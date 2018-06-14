"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <http://code.google.com/p/flowblade>.

    Flowblade Movie Editor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Flowblade Movie Editor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Module contains classes and build methods to create GUI objects.
"""

import cairo
import copy
import math
import time

from gi.repository import GObject
from gi.repository import GdkPixbuf
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import PangoCairo
from gi.repository import GLib

import appconsts
import cairoarea
import dnd
import editorpersistance
import editorstate
from editorstate import current_sequence
from editorstate import current_bin
from editorstate import PROJECT
from editorstate import PLAYER
import gui
import guiutils
import mltfilters
import mltprofiles
import mlttransitions
import monitorwidget
import respaths
import shortcuts
import snapping
import toolsintegration
import translations
import utils

SEPARATOR_HEIGHT = 5
SEPARATOR_WIDTH = 250

MONITOR_COMBO_WIDTH = 32
MONITOR_COMBO_HEIGHT = 12

MEDIA_OBJECT_WIDGET_WIDTH = 120
MEDIA_OBJECT_WIDGET_HEIGHT = 105

CLIP_EDITOR_LEFT_WIDTH = 200

TC_COLOR = (0.7, 0.7, 0.7)

BIG_TC_GRAD_STOPS = [   (1, 1, 1, 1, 0.2),
                        (0.8, 1, 1, 1, 0),
                        (0.51, 1, 1, 1, 0),
                        (0.50, 1, 1, 1, 0.25),
                        (0, 1, 1, 1, 0.4)]

BIG_TC_FRAME_GRAD_STOPS = [ (1, 0.7, 0.7, 0.7, 1),
                            (0.95, 0.7, 0.7, 0.7, 1),
                            (0.75, 0.1, 0.1, 0.1, 1),
                            (0, 0.14, 0.14, 0.14, 1)]
M_PI = math.pi

has_proxy_icon = None
is_proxy_icon = None
graphics_icon = None
imgseq_icon = None
audio_icon = None
pattern_icon = None
profile_warning_icon = None

# GTK3 requires these to be created outside of callback
markers_menu = Gtk.Menu.new()
tracks_menu = Gtk.Menu.new()
monitor_menu = Gtk.Menu.new()
trim_view_menu = Gtk.Menu.new()
tools_menu = Gtk.Menu.new()
file_filter_menu = Gtk.Menu()
column_count_menu = Gtk.Menu()
clip_popup_menu = Gtk.Menu()
tracks_pop_menu = Gtk.Menu()
transition_clip_menu = Gtk.Menu()
blank_clip_menu = Gtk.Menu()
audio_clip_menu = Gtk.Menu()
compositor_popup_menu = Gtk.Menu()
media_file_popup_menu = Gtk.Menu()
filter_stack_menu_popup_menu = Gtk.Menu()
media_linker_popup_menu = Gtk.Menu()
log_event_popup_menu = Gtk.Menu()
levels_menu = Gtk.Menu()
clip_effects_hamburger_menu = Gtk.Menu()
bin_popup_menu = Gtk.Menu()


# ------------------------------------------------- item lists
class ImageTextTextListView(Gtk.VBox):
    """
    GUI component displaying list with columns: img, text, text
    Middle column expands.
    """

    def __init__(self):
        GObject.GObject.__init__(self)

       # Datamodel: icon, text, text
        self.storemodel = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str)

        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

        # View
        self.treeview = Gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(False)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.SINGLE)

        # Column views
        self.icon_col = Gtk.TreeViewColumn("Icon")
        self.text_col_1 = Gtk.TreeViewColumn("text1")
        self.text_col_2 = Gtk.TreeViewColumn("text2")

        # Cell renderers
        self.icon_rend = Gtk.CellRendererPixbuf()
        self.icon_rend.props.xpad = 6

        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", Pango.EllipsizeMode.END)

        self.text_rend_2 = Gtk.CellRendererText()
        self.text_rend_2.set_property("yalign", 0.0)

        # Build column views
        self.icon_col.set_expand(False)
        self.icon_col.set_spacing(5)
        self.icon_col.pack_start(self.icon_rend, False)
        self.icon_col.add_attribute(self.icon_rend, 'pixbuf', 0)

        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1, True)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 1)

        self.text_col_2.set_expand(False)
        self.text_col_2.pack_start(self.text_rend_2, True)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 2)

        # Add column views to view
        self.treeview.append_column(self.icon_col)
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows

# ------------------------------------------------- item lists
class BinTreeView(Gtk.VBox):
    """
    GUI component displaying list with columns: img, text, text
    Middle column expands.
    """

    def __init__(self, bin_selection_cb, bin_name_edit_cb, bins_popup_cb):
        GObject.GObject.__init__(self)

        self.bins_popup_cb = bins_popup_cb

       # Datamodel: icon, text, text (folder, name, item count)
        self.storemodel = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str)

        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.NONE)

        # TreeView
        self.treeview = Gtk.TreeView(self.storemodel)
        self.treeview.connect('button-press-event', self._button_press_event)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(False)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.SINGLE)
        tree_sel.connect("changed", bin_selection_cb)
        
        # Cell renderers
        self.icon_rend = Gtk.CellRendererPixbuf()
        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.connect("edited",
                                 bin_name_edit_cb,
                                 (self.storemodel, 1))
        self.text_rend_1.set_property("ellipsize", Pango.EllipsizeMode.END)
        self.text_rend_2 = Gtk.CellRendererText()

        # Column views
        self.bin_col = Gtk.TreeViewColumn("")
        self.bin_col.set_expand(True)
        self.bin_col.pack_start(self.icon_rend, False)
        self.bin_col.add_attribute(self.icon_rend, 'pixbuf', 0)
        self.bin_col.pack_start(self.text_rend_1, True)
        self.bin_col.add_attribute(self.text_rend_1, 'text', 1)

        self.item_count_col = Gtk.TreeViewColumn("", self.text_rend_2, text=2)
        self.item_count_col.set_expand(False)

        # Add column views to view
        self.treeview.append_column(self.bin_col)
        self.treeview.append_column(self.item_count_col)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()

        self.scroll.connect('button-press-event', self._button_press_event)

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows

    def fill_data_model(self):
        self.storemodel.clear()

        for media_bin in PROJECT().bins:
            try:
                #Gtk.Image.new_from_stock(Gtk.STOCK_OPEN, Gtk.IconSize.MENU)
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "bin_5.png")
                row_data = [pixbuf,
                            media_bin.name,
                            str(len(media_bin.file_ids))]
                self.storemodel.append(row_data)
                
            except GObject.GError, exc:
                print "can't load icon", exc
        
        self.scroll.queue_draw()
        
    def _button_press_event(self, widget, event):
        if event.button == 3:
            self.bins_popup_cb(event)



# ------------------------------------------------- item lists
class ImageTextImageListView(Gtk.VBox):
    """
    GUI component displaying list with columns: img, text, img
    Middle column expands.
    """

    def __init__(self):
        GObject.GObject.__init__(self)

       # Datamodel: icon, text, icon
        self.storemodel = Gtk.ListStore(GdkPixbuf.Pixbuf, str, GdkPixbuf.Pixbuf)

        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

        # View
        self.treeview = Gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(False)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.SINGLE)

        # Column views
        self.icon_col_1 = Gtk.TreeViewColumn("icon1")
        self.text_col_1 = Gtk.TreeViewColumn("text1")
        self.icon_col_2 = Gtk.TreeViewColumn("icon2")

        # Cell renderers
        self.icon_rend_1 = Gtk.CellRendererPixbuf()
        self.icon_rend_1.props.xpad = 6

        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", Pango.EllipsizeMode.END)

        self.icon_rend_2 = Gtk.CellRendererPixbuf()
        self.icon_rend_2.props.xpad = 6

        # Build column views
        self.icon_col_1.set_expand(False)
        self.icon_col_1.set_spacing(5)
        self.icon_col_1.pack_start(self.icon_rend_1, False)
        self.icon_col_1.add_attribute(self.icon_rend_1, 'pixbuf', 0)

        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1, True)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 1)

        self.icon_col_2.set_expand(False)
        self.icon_col_2.set_spacing(5)
        self.icon_col_2.pack_start(self.icon_rend_2, False)
        self.icon_col_2.add_attribute(self.icon_rend_2, 'pixbuf', 2)

        # Add column views to view
        self.treeview.append_column(self.icon_col_1)
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.icon_col_2)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows


class SequenceListView(ImageTextTextListView):
    """
    GUI component displaying list of sequences in project
    """

    def __init__(self, seq_name_edited_cb, sequence_popup_cb):
        ImageTextTextListView.__init__(self)
        self.sequence_popup_cb = sequence_popup_cb
        self.treeview.connect('button-press-event', self._button_press_event)
        self.scroll.set_shadow_type(Gtk.ShadowType.NONE)

        # Icon path
        self.icon_path = respaths.IMAGE_PATH + "sequence.png"

        # Set sequence name editable and connect 'edited' signal
        self.text_rend_1.set_property("editable", True)
        self.text_rend_1.connect("edited",
                                 seq_name_edited_cb,
                                 (self.storemodel, 1))

        self.scroll.connect('button-press-event', self._button_press_event)
        
    def fill_data_model(self):
        """
        Creates displayed data.
        Displays icon, sequence name and sequence length
        """
        self.storemodel.clear()
        for seq in PROJECT().sequences:
            icon = GdkPixbuf.Pixbuf.new_from_file(self.icon_path)
            active = ""
            if seq == current_sequence():
                active = _("active") + " "
            row_data = [icon,
                        seq.name,
                        active]
            self.storemodel.append(row_data)
            self.scroll.queue_draw()

    def _button_press_event(self, widget, event):
        if event.button == 3:
            self.sequence_popup_cb(event)


class MediaListView(ImageTextTextListView):
    """
    GUI component displaying list of media files.
    """

    def __init__(self, row_activated_cb, file_name_edited_cb):
        ImageTextTextListView.__init__(self)

        # Connect double-click listener and allow multiple selection
        self.treeview.connect("row-activated",
                              row_activated_cb)

        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.MULTIPLE)
        self.text_rend_1.set_property("editable", True)
        self.text_rend_1.set_property("font-desc", Pango.FontDescription("sans bold 9"))
        self.text_rend_1.connect("edited",
                                 file_name_edited_cb,
                                 (self.storemodel, 1))

        self.text_rend_2.set_property("font-desc", Pango.FontDescription("sans 8"))
        self.text_rend_2.set_property("yalign", 0.5)

    def fill_data_model(self):
        """
        Creates displayed data.
        Displays thumbnail icon, file name and length
        """
        self.storemodel.clear()
        for file_id in current_bin().file_ids:
            media_file = PROJECT().media_files[file_id]
            row_data = [media_file.icon,
                        media_file.name,
                        utils.clip_length_string(media_file.length)]
            self.storemodel.append(row_data)
            self.scroll.queue_draw()


class BinListView(ImageTextTextListView):
    """
    GUI component displaying list of media files.
    """

    def __init__(self, bin_selection_cb, bin_name_edit_cb):
        ImageTextTextListView.__init__(self)

        self.text_col_1.set_min_width(10)

        # Connect selection 'changed' signal
        tree_sel = self.treeview.get_selection()
        tree_sel.connect("changed", bin_selection_cb)

        # Set bin name editable and connect 'edited' signal
        self.text_rend_1.set_property("editable", True)
        self.text_rend_1.connect("edited",
                                 bin_name_edit_cb,
                                 (self.storemodel, 1))

    def fill_data_model(self):
        self.storemodel.clear()

        for media_bin in PROJECT().bins:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "bin_5.png")
                row_data = [pixbuf,
                            media_bin.name,
                            str(len(media_bin.file_ids))]
                self.storemodel.append(row_data)
                self.scroll.queue_draw()
            except GObject.GError, exc:
                print "can't load icon", exc


class FilterListView(ImageTextImageListView):
    """
    GUI component displaying list of available filters.
    """
    def __init__(self, selection_cb=None):
        ImageTextImageListView.__init__(self)

        # Connect selection 'changed' signal
        if not(selection_cb == None):
            tree_sel = self.treeview.get_selection()
            tree_sel.connect("changed", selection_cb)

    def fill_data_model(self, filter_group):
        self.storemodel.clear()
        for i in range(0, len(filter_group)):
            f = filter_group[i]
            row_data = [f.get_icon(),
                        translations.get_filter_name(f.name),
                        None] # None is historical on/off icon thingy, not used anymore
            self.storemodel.append(row_data)
            self.scroll.queue_draw()


class FilterSwitchListView(Gtk.VBox):
    """
    GUI component displaying list of filters applied to a clip.
    """

    def __init__(self, selection_cb, toggle_cb, row_deleted, row_inserted):
        GObject.GObject.__init__(self)

        # Datamodel: icon, text, icon
        self.storemodel = Gtk.ListStore(GdkPixbuf.Pixbuf, str, bool)
        self.storemodel.connect("row-deleted", row_deleted)
        self.storemodel.connect("row-inserted", row_inserted)
        
        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

        # View
        self.treeview = Gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(False)
        self.treeview.set_reorderable(True)

        
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.SINGLE)

        # Column views
        self.icon_col_1 = Gtk.TreeViewColumn("icon1")
        self.text_col_1 = Gtk.TreeViewColumn("text1")
        self.check_col_1 = Gtk.TreeViewColumn("switch")

        # Cell renderers
        self.icon_rend_1 = Gtk.CellRendererPixbuf()
        self.icon_rend_1.props.xpad = 6

        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", Pango.EllipsizeMode.END)

        self.toggle_rend = Gtk.CellRendererToggle()
        self.toggle_rend.set_property('activatable', True)
        self.toggle_rend.connect( 'toggled', self.toggled)

        # Build column views
        self.icon_col_1.set_expand(False)
        self.icon_col_1.set_spacing(5)
        self.icon_col_1.pack_start(self.icon_rend_1, False)
        self.icon_col_1.add_attribute(self.icon_rend_1, 'pixbuf', 0)

        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1, True)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 1)

        self.check_col_1.set_expand(False)
        self.check_col_1.set_spacing(5)
        self.check_col_1.pack_start(self.toggle_rend, False)
        self.check_col_1.add_attribute(self.toggle_rend, "active", 2)

        # Add column views to view
        self.treeview.append_column(self.icon_col_1)
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.check_col_1)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()

        # Connect selection 'changed' signal
        if not(selection_cb == None):
            tree_sel = self.treeview.get_selection()
            tree_sel.connect("changed", selection_cb)

        self.toggle_callback = toggle_cb

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows

    def fill_data_model(self, filter_group, filter_objects):
        """
        Creates displayed data.
        Displays thumbnail icon, file name and length
        filter_group is array of mltfilter.FilterInfo objects.
        filter_obejcts is array of mltfilter.FilterObject objects
        """
        self.storemodel.clear()
        for i in range(0, len(filter_group)):
            f = filter_group[i]
            row_data = [f.get_icon(),
                        translations.get_filter_name(f.name),
                        filter_objects[i].active]
            self.storemodel.append(row_data)
            self.scroll.queue_draw()

    def toggled(self, cell, path):
        self.toggle_callback(int(path))


class TextListView(Gtk.VBox):
    """
    GUI component displaying list with  single column text column.
    """
    def __init__(self, width, column_name=None):
        GObject.GObject.__init__(self)

       # Datamodel: icon, text, text
        self.storemodel = Gtk.ListStore(str)

        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

        # View
        self.treeview = Gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        if column_name == None:
            self.treeview.set_headers_visible(False)
            column_name = "text1"
        self.treeview.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        # Cell renderers
        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", Pango.EllipsizeMode.END)

        # Build column views
        self.text_col_1 = Gtk.TreeViewColumn(column_name)
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        self.text_col_1.set_min_width(width)
        self.text_col_1.pack_start(self.text_rend_1, False)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 0)

        # Add column views to view
        self.treeview.append_column(self.text_col_1)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows

    def get_selected_indexes_list(self):
        rows = self.get_selected_rows_list()
        indexes = []
        for row in rows:
            indexes.append(max(row))
        return indexes


class ProfileListView(TextListView):
    """
    GUI component displaying list with columns: img, text, text
    Middle column expands.
    """
    def __init__(self, column_name=None):
        TextListView.__init__(self, 100, column_name)

    def fill_data_model(self, profiles):
        self.storemodel.clear()
        default_profile = mltprofiles.get_default_profile()
        for profile in profiles:
            row_data = [profile[0]]
            if default_profile == profile[1]:
                row_data = [row_data[0] + " <" + _("default") + ">"]
            self.storemodel.append(row_data)

        self.scroll.queue_draw()


class AutoSavesListView(TextListView):
    def __init__(self, column_name=None):
        TextListView.__init__(self, 300, None)
        self.treeview.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

    def fill_data_model(self, autosaves):
        self.storemodel.clear()
        for autosave_object in autosaves:
            since_time_str = utils.get_time_str_for_sec_float(autosave_object.age)
            row_data = [_("Autosave created ") + since_time_str + _(" ago.")]
            self.storemodel.append(row_data)

        self.treeview.set_cursor("0")

        self.scroll.queue_draw()


# -------------------------------------------- clip info
class ClipInfoPanel(Gtk.HBox):

    def __init__(self):
        GObject.GObject.__init__(self)

        if editorstate.screen_size_small_height() == True:
            font_desc = "sans bold 8"
        else:
            font_desc = "sans bold 9"

        self.name_label = guiutils.bold_label(_("Clip:"))

        self.name_value = Gtk.Label()
        self.name_value.set_ellipsize(Pango.EllipsizeMode.END)
        self.name_value.set_max_width_chars(15)

        self.name_label.set_sensitive(False)
        self.name_value.set_sensitive(False)
        self.name_value.modify_font(Pango.FontDescription(font_desc))
        self.name_label.modify_font(Pango.FontDescription(font_desc))
        
        self.track = guiutils.bold_label(_("Track:"))
        self.track_value = Gtk.Label()
        
        self.track.set_sensitive(False)
        self.track_value.set_sensitive(False)
        self.track.modify_font(Pango.FontDescription(font_desc))
        self.track_value.modify_font(Pango.FontDescription(font_desc))
        
        info_row_1 = Gtk.HBox()
        info_row_1.pack_start(self.name_label, False, True, 0)
        info_row_1.pack_start(self.name_value, True, True, 0)

        info_row_2 = Gtk.HBox()
        info_row_2.pack_start(self.track, False, False, 0)
        info_row_2.pack_start(self.track_value, True, True, 0)

        self.pack_start(info_row_1, False, False, 0)
        self.pack_start(guiutils.pad_label(24,12), False, False, 0)
        self.pack_start(info_row_2, False, False, 0)
        
    def display_clip_info(self, clip, track, index):
        self.name_label.set_text(_("<b>Clip: </b>"))
        self.name_value.set_text("<b>" + clip.name + "</b>")
        self.track.set_text(_("<b>Track: </b>"))
        self.track_value.set_text("<b>" + track.get_name() + "</b>")
        self._set_use_mark_up()

    def set_no_clip_info(self):
        self.name_label.set_text("")
        self.name_value.set_text("")
        self.track.set_text("")
        self.track_value.set_text("")
        self._set_use_mark_up()

    def _set_use_mark_up(self):
        self.name_label.set_use_markup(True)
        self.track.set_use_markup(True)
        self.name_value.set_use_markup(True)
        self.track_value.set_use_markup(True)

    def set_enabled(self, value):
        pass


# -------------------------------------------- compositor info
class CompositorInfoPanel(Gtk.HBox):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.set_homogeneous(False)

        if editorstate.screen_size_small_height() == True:
            font_desc = "sans bold 8"
        else:
            font_desc = "sans bold 9"
            
        self.source_track = Gtk.Label()
        self.source_track_value = Gtk.Label()

        self.source_track.modify_font(Pango.FontDescription(font_desc))
        self.source_track_value.modify_font(Pango.FontDescription(font_desc))
        self.source_track.set_sensitive(False)
        self.source_track_value.set_sensitive(False)
                       
        self.destination_track = Gtk.Label()
        self.destination_track_value = Gtk.Label()

        self.destination_track.modify_font(Pango.FontDescription(font_desc))
        self.destination_track_value.modify_font(Pango.FontDescription(font_desc))
        self.destination_track.set_sensitive(False)
        self.destination_track_value.set_sensitive(False)
        
        self.length = Gtk.Label()
        self.length_value = Gtk.Label()

        self.length.modify_font(Pango.FontDescription(font_desc))
        self.length_value.modify_font(Pango.FontDescription(font_desc))
        self.length.set_sensitive(False)
        self.length_value.set_sensitive(False)
        
        info_row_2 = Gtk.HBox()
        info_row_2.pack_start(self.source_track, False, True, 0)
        info_row_2.pack_start(self.source_track_value, False, False, 0)
        info_row_2.pack_start(Gtk.Label(), True, True, 0)

        info_row_3 = Gtk.HBox()
        info_row_3.pack_start(self.destination_track, False, False, 0)
        info_row_3.pack_start(self.destination_track_value, False, False, 0)
        info_row_3.pack_start(Gtk.Label(), True, True, 0)

        info_row_5 = Gtk.HBox()
        info_row_5.pack_start(self.length, False, False, 0)
        info_row_5.pack_start(self.length_value, False, False, 0)
        info_row_5.pack_start(Gtk.Label(), True, True, 0)

        PAD_HEIGHT = 2
        self.pack_start(info_row_2, False, False, 0)
        self.pack_start(info_row_3, False, False, 0)
        self.pack_start(info_row_5, False, False, 0)

        self.set_spacing(4)
        self.set_no_compositor_info()
        self.set_enabled(False)

    def display_compositor_info(self, compositor):
        self.source_track.set_text(_("<b>Source:</b>") + " ")
        self.destination_track.set_text(_("<b>Destination:</b>") + " ")
        self.length.set_text(_("<b>Length:</b>") + " ")
        
        src_track = utils.get_track_name(current_sequence().tracks[compositor.transition.b_track],current_sequence())
        self.source_track_value.set_text("<b>" + src_track + "</b>")

        dest_track = utils.get_track_name(current_sequence().tracks[compositor.transition.a_track], current_sequence())
        self.destination_track_value.set_text("<b>" + dest_track + "</b>")

        length = utils.get_tc_string(compositor.clip_out - compositor.clip_in)
        self.length_value.set_text("<b>" + length + "</b>")

        self._set_use_mark_up()
        
    def set_no_compositor_info(self):
        self.source_track.set_text("")
        self.source_track_value.set_text("")

        self.destination_track.set_text("")
        self.destination_track_value.set_text("")

        self.length.set_text("")
        self.length_value.set_text("")

        self._set_use_mark_up()

    def _set_use_mark_up(self):
        self.source_track.set_use_markup(True)
        self.destination_track.set_use_markup(True)
        self.length.set_use_markup(True)
        self.length_value.set_use_markup(True)
        self.destination_track_value.set_use_markup(True)
        self.source_track_value.set_use_markup(True)

    def set_enabled(self, value):
        pass
        #self.source_track.set_sensitive(value)
        #self.destination_track.set_sensitive(value)
        #self.length.set_sensitive(value)


# -------------------------------------------- media select panel
class MediaPanel():

    def __init__(self, media_file_popup_cb, double_click_cb, panel_menu_cb):
        self.widget = Gtk.VBox()
        self.row_widgets = []
        self.selected_objects = []
        self.columns = editorpersistance.prefs.media_columns
        self.media_file_popup_cb = media_file_popup_cb
        self.panel_menu_cb = panel_menu_cb
        self.double_click_cb = double_click_cb
        self.monitor_indicator = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "monitor_indicator.png")
        self.last_event_time = 0.0
        self.last_ctrl_selected_media_object = None
        
        global has_proxy_icon, is_proxy_icon, graphics_icon, imgseq_icon, audio_icon, pattern_icon, profile_warning_icon
        has_proxy_icon = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "has_proxy_indicator.png")
        is_proxy_icon = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "is_proxy_indicator.png")
        graphics_icon = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "graphics_indicator.png")
        imgseq_icon = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "imgseq_indicator.png")
        audio_icon = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "audio_indicator.png")
        pattern_icon = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "pattern_producer_indicator.png")
        profile_warning_icon = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "profile_warning.png")

    def get_selected_media_objects(self):
        return self.selected_objects

    def media_object_selected(self, media_object, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            widget.grab_focus()
            self.clear_selection()
            media_object.widget.override_background_color(Gtk.StateType.NORMAL, gui.get_selected_bg_color())
            self.selected_objects.append(media_object)
            self.widget.queue_draw()
            GLib.idle_add(self.double_click_cb, media_object.media_file)
            return

        # HACK! We're using event times to exclude double events when icon is pressed
        now = time.time()
        if (now - self.last_event_time) < 0.05:
            self.last_event_time = now
            return
        self.last_event_time = now

        widget.grab_focus()
        if event.button == 1:
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                
                # add to selected if not there
                try:
                    index = self.selected_objects.index(media_object)
                except:
                    self.selected_objects.append(media_object)
                    media_object.widget.override_background_color(Gtk.StateType.NORMAL, gui.get_selected_bg_color())
                    self.last_ctrl_selected_media_object = media_object
                    return                
            else:
                self.clear_selection()
                media_object.widget.override_background_color(Gtk.StateType.NORMAL, gui.get_selected_bg_color())
                self.selected_objects.append(media_object)

        elif event.button == 3:
            self.clear_selection()
            display_media_file_popup_menu(media_object.media_file,
                                          self.media_file_popup_cb,
                                          event)

        self.widget.queue_draw()

    def release_on_media_object(self, media_object, widget, event):
        if self.last_ctrl_selected_media_object == media_object:
            self.last_ctrl_selected_media_object = None
            return
            
        widget.grab_focus()
        if event.button == 1:
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                # remove from selected if already there
                try:
                    index = self.selected_objects.index(media_object)
                    self.selected_objects.remove(media_object)
                    media_object.widget.override_background_color(Gtk.StateType.NORMAL, gui.get_bg_color())
                except:
                    pass
                    
    def select_media_file(self, media_file):
        self.clear_selection()
        self.selected_objects.append(self.widget_for_mediafile[media_file])

    def select_media_file_list(self, media_files):
        self.clear_selection()
        for media_file in media_files:
            self.selected_objects.append(self.widget_for_mediafile[media_file])

    def empty_pressed(self, widget, event):
        self.clear_selection()
        if event.button == 3:
            self.panel_menu_cb(event)

    def select_all(self):
        self.clear_selection()
        bg_color = gui.get_selected_bg_color()

        for media_file, media_object in self.widget_for_mediafile.iteritems():
            media_object.widget.override_background_color(Gtk.StateType.NORMAL, bg_color)
            self.selected_objects.append(media_object)

    def clear_selection(self):
        bg_color = gui.get_bg_color()
        for m_obj in self.selected_objects:
            m_obj.widget.override_background_color(Gtk.StateType.NORMAL, bg_color)
        self.selected_objects = []

    def columns_changed(self, columns):
        self.columns = columns
        editorpersistance.prefs.media_columns = self.columns
        editorpersistance.save()
        self.fill_data_model()

    def fill_data_model(self):
        for w in self.row_widgets:
            self.widget.remove(w)
        self.row_widgets = []
        self.widget_for_mediafile = {}
        self.selected_objects = []

        # info with text for empty panel
        if len(current_bin().file_ids) == 0:
            filler = self._get_empty_filler()
            dnd.connect_media_drop_widget(filler)
            self.row_widgets.append(filler)
            self.widget.pack_start(filler, True, True, 0)
            
            info = Gtk.Label(_("Right Click to Add Media."))
            info.set_sensitive(False)
            dnd.connect_media_drop_widget(info)
            filler = self._get_empty_filler(info)
            self.widget.pack_start(filler, False, False, 0)
            self.row_widgets.append(filler)
            
            filler = self._get_empty_filler()
            dnd.connect_media_drop_widget(filler)
            self.row_widgets.append(filler)
            self.widget.pack_start(filler, True, True, 0)
            self.widget.show_all()
            return

        column = 0
        bin_index = 0
        row_box = Gtk.HBox()
        dnd.connect_media_drop_widget(row_box)
        row_box.set_size_request(MEDIA_OBJECT_WIDGET_WIDTH * self.columns, MEDIA_OBJECT_WIDGET_HEIGHT)
        for file_id in current_bin().file_ids:
            media_file = PROJECT().media_files[file_id]

            # Filter view
            if ((editorstate.media_view_filter == appconsts.SHOW_VIDEO_FILES)
                and (media_file.type != appconsts.VIDEO)):
                continue
            if ((editorstate.media_view_filter == appconsts.SHOW_AUDIO_FILES)
                and (media_file.type != appconsts.AUDIO)):
                continue
            if ((editorstate.media_view_filter == appconsts.SHOW_GRAPHICS_FILES)
                and (media_file.type != appconsts.IMAGE)):
                continue
            if ((editorstate.media_view_filter == appconsts.SHOW_IMAGE_SEQUENCES)
                and (media_file.type != appconsts.IMAGE_SEQUENCE)):
                continue
            if ((editorstate.media_view_filter == appconsts.SHOW_PATTERN_PRODUCERS)
                and (media_file.type != appconsts.PATTERN_PRODUCER)):
                continue

            media_object = MediaObjectWidget(media_file, self.media_object_selected, self.release_on_media_object, bin_index, self.monitor_indicator)
            dnd.connect_media_files_object_widget(media_object.widget)
            dnd.connect_media_files_object_cairo_widget(media_object.img)
            self.widget_for_mediafile[media_file] = media_object
            row_box.pack_start(media_object.widget, False, False, 0)
            column += 1
            if column == self.columns:
                filler = self._get_empty_filler()
                row_box.pack_start(filler, True, True, 0)
                self.widget.pack_start(row_box, False, False, 0)
                self.row_widgets.append(row_box)
                row_box = Gtk.HBox()
                column = 0
            bin_index += 1

        if column != 0:
            filler = self._get_empty_filler()
            dnd.connect_media_drop_widget(filler)
            row_box.pack_start(filler, True, True, 0)
            self.widget.pack_start(row_box, False, False, 0)
            self.row_widgets.append(row_box)

        filler = self._get_empty_filler()
        dnd.connect_media_drop_widget(filler)
        self.row_widgets.append(filler)
        self.widget.pack_start(filler, True, True, 0)

        self.widget.show_all()

    def _get_empty_filler(self, widget=None):
        filler = Gtk.EventBox()
        filler.connect("button-press-event", lambda w,e: self.empty_pressed(w,e))
        if widget == None:
            filler.add(Gtk.Label())
        else:
            filler.add(widget)
        return filler


class MediaObjectWidget:

    def __init__(self, media_file, selected_callback, release_callback, bin_index, indicator_icon):
        self.media_file = media_file
        self.selected_callback = selected_callback
        self.bin_index = bin_index
        self.indicator_icon = indicator_icon
        self.selected_callback = selected_callback
        self.matches_project_profile = media_file.matches_project_profile()

        self.widget = Gtk.EventBox()
        self.widget.connect("button-press-event", lambda w,e: selected_callback(self, w, e))
        self.widget.connect("button-release-event", lambda w,e: release_callback(self, w, e))
        self.widget.dnd_media_widget_attr = True # this is used to identify widget at dnd drop
        self.widget.set_can_focus(True)
        self.widget.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.vbox = Gtk.VBox()

        self.img = cairoarea.CairoDrawableArea2(appconsts.THUMB_WIDTH, appconsts.THUMB_HEIGHT, self._draw_icon)
        self.img.press_func = self._press
        self.img.dnd_media_widget_attr = True # this is used to identify widget at dnd drop
        self.img.set_can_focus(True)
        self.img.set_tooltip_text(media_file.name)

        txt = Gtk.Label(label=media_file.name)
        txt.modify_font(Pango.FontDescription("sans 9"))
        txt.set_max_width_chars(13)
        # Feb-2017 - SvdB - For full file names. First part shows the original code for short file names        
        if editorpersistance.prefs.show_full_file_names == False:
            txt.set_ellipsize(Pango.EllipsizeMode.END)
        else:
            txt.set_line_wrap_mode(Pango.WrapMode.CHAR)
            txt.set_line_wrap(True)
        # end SvdB
        txt.set_tooltip_text(media_file.name)

        self.vbox.pack_start(self.img, True, True, 0)
        self.vbox.pack_start(txt, False, False, 0)

        self.align = guiutils.set_margins(self.vbox, 6, 6, 6, 6)

        self.widget.add(self.align)

    def _get_matches_profile(self):
        if (not hasattr(self.media_file, "info")): # to make really sure that old projects don't crash,
            return True                            # but probably is not needed as attr is added at load
        if self.media_file.info == None:
            return True

        is_match = True # this is true for audio and graphics and image sequences and is only
                        # set false for video that does not match profile

        if self.media_file.type == appconsts.VIDEO:
            best_media_profile_index = mltprofiles.get_closest_matching_profile_index(self.media_file.info)
            project_profile_index = mltprofiles.get_index_for_name(PROJECT().profile.description())
            if best_media_profile_index != project_profile_index:
                is_match = False

        return is_match

    def _press(self, event):
        self.selected_callback(self, self.widget, event)

    def _draw_icon(self, event, cr, allocation):
        x, y, w, h = allocation
        cr.set_source_surface(self.media_file.icon, 0, 0)
        cr.paint()
        if self.media_file == editorstate.MONITOR_MEDIA_FILE():
            cr.set_source_surface(self.indicator_icon, 29, 22)
            cr.paint()

        cr.select_font_face ("sans-serif",
                 cairo.FONT_SLANT_NORMAL,
                 cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(9)
        if self.media_file.mark_in != -1 and self.media_file.mark_out != -1:
            cr.set_source_rgba(0,0,0,0.5)
            cr.rectangle(21,1,72,12)
            cr.fill()
            
            cr.move_to(23, 10)
            clip_length = utils.get_tc_string(self.media_file.mark_out - self.media_file.mark_in + 1) #+1 out incl.
            cr.set_source_rgb(1, 1, 1)
            cr.show_text("][ " + str(clip_length))

        cr.set_source_rgba(0,0,0,0.5)
        cr.rectangle(28,75,62,12)
        cr.fill()
            
        cr.move_to(30, 84)
        cr.set_source_rgb(1, 1, 1)
        media_length = utils.get_tc_string(self.media_file.length)
        cr.show_text(str(media_length))
            
        if self.media_file.type != appconsts.PATTERN_PRODUCER:
            if self.media_file.is_proxy_file == True:
                cr.set_source_surface(is_proxy_icon, 96, 6)
                cr.paint()
            elif self.media_file.has_proxy_file == True:
                cr.set_source_surface(has_proxy_icon, 96, 6)
                cr.paint()

        if self.matches_project_profile == False:
            cr.set_source_surface(profile_warning_icon, 4, 70)
            cr.paint()

        if self.media_file.type == appconsts.IMAGE:
            cr.set_source_surface(graphics_icon, 6, 6)
            cr.paint()

        if self.media_file.type == appconsts.IMAGE_SEQUENCE:
            cr.set_source_surface(imgseq_icon, 6, 6)
            cr.paint()

        if self.media_file.type == appconsts.AUDIO:
            cr.set_source_surface(audio_icon, 6, 6)
            cr.paint()

        if self.media_file.type == appconsts.PATTERN_PRODUCER:
            cr.set_source_surface(pattern_icon, 6, 6)
            cr.paint()



# -------------------------------------------- context menus
class EditorSeparator:
    """
    GUI component used to add, move and remove keyframes to of
    inside a single clip. Does not a reference of the property being
    edited and needs a parent editor to write keyframe values.
    """

    def __init__(self):
        self.widget = cairoarea.CairoDrawableArea2( SEPARATOR_WIDTH,
                                                    SEPARATOR_HEIGHT,
                                                    self._draw)
    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation

        # Draw separator
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.5,0.5,0.5,0.2)
        cr.move_to(8.5, 2.5)
        cr.line_to(w - 8.5, 2.5)
        cr.stroke()

# ---------------------------------------------- MISC WIDGETS
def get_monitor_view_select_combo(callback):
    surface_list = [cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "program_view_2.png"),
                   cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "vectorscope.png"),
                   cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "rgbparade.png")]
    menu_launch = ImageMenuLaunch(callback, surface_list, w=24, h=20)
    menu_launch.surface_y = 10
    return menu_launch

def get_trim_view_select_combo(callback):
    surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "trim_view.png")
    menu_launch = PressLaunch(callback, surface, w=24, h=20)
    menu_launch.surface_y = 10
    return menu_launch
    
def get_compositor_track_select_combo(source_track, target_track, callback):
    tracks_combo = Gtk.ComboBoxText()
    active_index = -1
    cb_index = 0
    for track_index in range(source_track.id - 1, current_sequence().first_video_index - 1, -1):
        track = current_sequence().tracks[track_index]
        tracks_combo.append_text(utils.get_track_name(track, current_sequence()))
        if track == target_track:
            active_index = cb_index
        cb_index += 1
    if active_index == -1:
        tracks_combo.set_active(0)
    else:
        tracks_combo.set_active(active_index)
    tracks_combo.connect("changed", lambda w,e: callback(w), None)
    return tracks_combo

# -------------------------------------------- context menus
def display_tracks_popup_menu(event, track, callback):
    track_obj = current_sequence().tracks[track]
    track_menu = tracks_pop_menu
    guiutils.remove_children(track_menu)

    if track_obj.edit_freedom != appconsts.FREE:
        track_menu.append(_get_menu_item(_("Lock Track"), callback, (track,"lock", None), False))
        track_menu.append(_get_menu_item(_("Unlock Track"), callback, (track,"unlock", None), True))

    else:
        track_menu.append(_get_menu_item(_("Lock Track"), callback, (track,"lock", None), True))
        track_menu.append(_get_menu_item(_("Unlock Track"), callback, (track,"unlock", None), False))

    _add_separetor(track_menu)

    normal_size_item = Gtk.RadioMenuItem()
    normal_size_item.set_label(_("Large Height"))
    normal_size_item.set_active(track_obj.height == appconsts.TRACK_HEIGHT_NORMAL)
    normal_size_item.connect("activate", callback, (track, "normal_height", None))
    track_menu.append(normal_size_item)

    small_size_item = Gtk.RadioMenuItem.new_with_label([normal_size_item], _("Normal Height"))
    small_size_item.set_active(track_obj.height != appconsts.TRACK_HEIGHT_NORMAL)
    small_size_item.connect("activate", callback, (track, "small_height", None))
    track_menu.append(small_size_item)

    _add_separetor(track_menu)

    track_menu.append(_get_track_mute_menu_item(event, track_obj, callback))

    track_menu.show_all()

    track_menu.popup(None, None, None, None, event.button, event.time)

def display_clip_popup_menu(event, clip, track, callback):
    if clip.is_blanck_clip:
        display_blank_clip_popup_menu(event, clip, track, callback)
        return

    if hasattr(clip, "rendered_type"):
        display_transition_clip_popup_menu(event, clip, track, callback)
        return

    clip_menu = clip_popup_menu
    guiutils.remove_children(clip_menu)
    
    # Menu items    
    clip_menu.add(_get_menu_item(_("Open in Filters Editor"), callback, (clip, track, "open_in_editor", event.x)))
    # Only make opening in compositor editor for video tracks V2 and higher
    if track.id <= current_sequence().first_video_index:
        active = False
    else:
        active = True
    if clip.media_type != appconsts.PATTERN_PRODUCER:
        clip_menu.add(_get_menu_item(_("Open in Clip Monitor"), callback,\
                      (clip, track, "open_in_clip_monitor", event.x)))

    _add_separetor(clip_menu)

    if track.type == appconsts.VIDEO:
        clip_menu.add(_get_tool_integration_menu_item(event, clip, track, callback))
        _add_separetor(clip_menu)
        
    if track.type == appconsts.VIDEO:
        active = True
        if clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER:
            active = False
        clip_menu.add(_get_menu_item(_("Split Audio"), callback,\
                      (clip, track, "split_audio", event.x), active))
        if track.id == current_sequence().first_video_index:
            active = True
        else:
            active = False
        if clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER:
            active = False
        clip_menu.add(_get_menu_item(_("Split Audio Synched"), callback,\
              (clip, track, "split_audio_synched", event.x), active))

    if editorstate.display_all_audio_levels == False:
        _add_separetor(clip_menu)

        if clip.waveform_data == None:
           clip_menu.add(_get_menu_item(_("Display Audio Level"), callback,\
                      (clip, track, "display_waveform", event.x), True))
        else:
           clip_menu.add(_get_menu_item(_("Clear Waveform"), callback,\
              (clip, track, "clear_waveform", event.x), True))

    audio_sync_item = _get_menu_item(_("Select Clip to Audio Sync With..."), callback, (clip, track, "set_audio_sync_clip", event.x))
    if utils.is_mlt_xml_file(clip.path) == True:
        audio_sync_item.set_sensitive(False)
    if clip.media_type == appconsts.IMAGE_SEQUENCE or clip.media_type == appconsts.IMAGE or clip.media_type == appconsts.PATTERN_PRODUCER:
        audio_sync_item.set_sensitive(False)
 
    clip_menu.add(audio_sync_item)
            
    _add_separetor(clip_menu)

    if track.id != current_sequence().first_video_index:
        if clip.sync_data != None:
            clip_menu.add(_get_menu_item(_("Resync"), callback, (clip, track, "resync", event.x)))
            clip_menu.add(_get_menu_item(_("Clear Sync Relation"), callback, (clip, track, "clear_sync_rel", event.x)))
        else:
            clip_menu.add(_get_menu_item(_("Select Sync Parent Clip..."), callback, (clip, track, "set_master", event.x)))

        _add_separetor(clip_menu)

    clip_menu.add(_get_mute_menu_item(event, clip, track, callback))

    _add_separetor(clip_menu)

    clip_menu.add(_get_filters_add_menu_item(event, clip, track, callback))

    # Only add compositors for video tracks V2 and higher
    if track.id <= current_sequence().first_video_index:
        active = False
    else:
        active = True
    clip_menu.add(_get_compositors_add_menu_item(event, clip, track, callback, active))
    clip_menu.add(_get_auto_fade_compositors_add_menu_item(event, clip, track, callback, active))
    #clip_menu.add(_get_blenders_add_menu_item(event, clip, track, callback, active))

    _add_separetor(clip_menu)
    clip_menu.add(_get_clone_filters_menu_item(event, clip, track, callback))
    clip_menu.add(_get_menu_item(_("Clear Filters"), callback, (clip, track, "clear_filters", event.x)))

    _add_separetor(clip_menu)
    clip_menu.add(_get_clip_properties_menu_item(event, clip, track, callback))
    clip_menu.add(_get_clip_markers_menu_item(event, clip, track, callback))
    clip_menu.add(_get_menu_item(_("Clip Info"), callback,\
                  (clip, track, "clip_info", event.x)))

    _add_separetor(clip_menu)
    clip_menu.add(_get_select_menu_item(event, clip, track, callback))
        
    if track.type == appconsts.VIDEO and clip.media_type != appconsts.PATTERN_PRODUCER:
        _add_separetor(clip_menu)
        clip_menu.add(_get_match_frame_menu_item(event, clip, track, callback))

    _add_separetor(clip_menu)
    
    clip_menu.add(_get_edit_menu_item(event, clip, track, callback))

    clip_menu.popup(None, None, None, None, event.button, event.time)

def display_transition_clip_popup_menu(event, clip, track, callback):
    clip_menu = transition_clip_menu
    guiutils.remove_children(clip_menu)

    clip_menu.add(_get_menu_item(_("Rerender"), callback, (clip, track, "re_render", event.x)))
    
    clip_menu.add(_get_menu_item(_("Open in Filters Editor"), callback, (clip, track, "open_in_editor", event.x)))

    _add_separetor(clip_menu)

    clip_menu.add(_get_mute_menu_item(event, clip, track, callback))

    _add_separetor(clip_menu)

    clip_menu.add(_get_filters_add_menu_item(event, clip, track, callback))

    # Only add compositors for video tracks V2 and higher
    if track.id <= current_sequence().first_video_index:
        active = False
    else:
        active = True
    clip_menu.add(_get_compositors_add_menu_item(event, clip, track, callback, active))
    clip_menu.add(_get_blenders_add_menu_item(event, clip, track, callback, active))

    _add_separetor(clip_menu)

    clip_menu.add(_get_clone_filters_menu_item(event, clip, track, callback))
    clip_menu.add(_get_menu_item(_("Clear Filters"), callback, (clip, track, "clear_filters", event.x)))
    clip_menu.popup(None, None, None, None, event.button, event.time)

def display_blank_clip_popup_menu(event, clip, track, callback):
    clip_menu = blank_clip_menu
    guiutils.remove_children(clip_menu)

    clip_menu.add(_get_menu_item(_("Strech Prev Clip to Cover"), callback, (clip, track, "cover_with_prev", event.x)))
    clip_menu.add(_get_menu_item(_("Strech Next Clip to Cover"), callback, (clip, track, "cover_with_next", event.x)))
    _add_separetor(clip_menu)
    clip_menu.add(_get_menu_item(_("Delete"), callback, (clip, track, "delete_blank", event.x)))
    clip_menu.popup(None, None, None, None, event.button, event.time)

def display_audio_clip_popup_menu(event, clip, track, callback):
    if clip.is_blanck_clip:
        display_blank_clip_popup_menu(event, clip, track, callback)
        return

    clip_menu = audio_clip_menu
    guiutils.remove_children(clip_menu)

    clip_menu.add(_get_menu_item(_("Open in Filters Editor"), callback, (clip, track, "open_in_editor", event.x)))
    if clip.media_type != appconsts.PATTERN_PRODUCER:
        clip_menu.add(_get_menu_item(_("Open in Clip Monitor"), callback,\
                      (clip, track, "open_in_clip_monitor", event.x)))

    _add_separetor(clip_menu)

    if clip.sync_data != None:
        clip_menu.add(_get_menu_item(_("Resync"), callback, (clip, track, "resync", event.x)))
        clip_menu.add(_get_menu_item(_("Clear Sync Relation"), callback, (clip, track, "clear_sync_rel", event.x)))
    else:
        clip_menu.add(_get_menu_item(_("Select Sync Parent Clip..."), callback, (clip, track, "set_master", event.x)))

    _add_separetor(clip_menu)

    if clip.waveform_data == None:
       clip_menu.add(_get_menu_item(_("Display Audio Level"), callback,\
                  (clip, track, "display_waveform", event.x), True))
    else:
       clip_menu.add(_get_menu_item(_("Clear Waveform"), callback,\
          (clip, track, "clear_waveform", event.x), True))

    _add_separetor(clip_menu)

    clip_menu.add(_get_mute_menu_item(event, clip, track, callback))

    _add_separetor(clip_menu)

    clip_menu.add(_get_audio_filters_add_menu_item(event, clip, track, callback))

    _add_separetor(clip_menu)

    clip_menu.add(_get_menu_item(_("Rename Clip"), callback,\
                      (clip, track, "rename_clip", event.x)))
    clip_menu.add(_get_color_menu_item(clip, track, callback))
    clip_menu.add(_get_menu_item(_("Clip Info"), callback,\
                  (clip, track, "clip_info", event.x)))

    _add_separetor(clip_menu)
    clip_menu.add(_get_select_menu_item(event, clip, track, callback))

    _add_separetor(clip_menu)
    
    clip_menu.add(_get_edit_menu_item(event, clip, track, callback))

    clip_menu.popup(None, None, None, None, event.button, event.time)

def display_compositor_popup_menu(event, compositor, callback):
    compositor_menu = compositor_popup_menu
    guiutils.remove_children(compositor_menu)

    compositor_menu.add(_get_menu_item(_("Open In Compositor Editor"), callback, ("open in editor",compositor)))
    _add_separetor(compositor_menu)
    compositor_menu.add(_get_menu_item(_("Sync with Origin Clip"), callback, ("sync with origin",compositor)))

    autofollow_item = Gtk.CheckMenuItem()
    autofollow_item.set_label(_("Obey Auto Follow"))
    autofollow_item.set_active(compositor.obey_autofollow)
    autofollow_item.connect("activate", callback, ("set auto follow", compositor))
    autofollow_item.set_sensitive(editorstate.auto_follow_active())
    autofollow_item.show()

    compositor_menu.append(autofollow_item)
    
    _add_separetor(compositor_menu)
    compositor_menu.add(_get_menu_item(_("Delete"), callback, ("delete",compositor)))
    compositor_menu.popup(None, None, None, None, event.button, event.time)

def _get_filters_add_menu_item(event, clip, track, callback):
    menu_item = Gtk.MenuItem(_("Add Filter"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    for group in mltfilters.groups:
        group_name, filters_array = group
        group_item = Gtk.MenuItem(group_name)
        sub_menu.append(group_item)
        sub_sub_menu = Gtk.Menu()
        group_item.set_submenu(sub_sub_menu)
        for filter_info in filters_array:
            filter_item = Gtk.MenuItem(translations.get_filter_name(filter_info.name))
            sub_sub_menu.append(filter_item)
            filter_item.connect("activate", callback, (clip, track, "add_filter", (event.x, filter_info)))
            filter_item.show()
        group_item.show()

    menu_item.show()
    return menu_item

def _get_audio_filters_add_menu_item(event, clip, track, callback):
    menu_item = Gtk.MenuItem(_("Add Filter"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    audio_groups = mltfilters.get_audio_filters_groups()
    for group in audio_groups:
        group_name, filters_array = group
        group_item = Gtk.MenuItem(group_name)
        sub_menu.append(group_item)
        sub_sub_menu = Gtk.Menu()
        group_item.set_submenu(sub_sub_menu)
        for filter_info in filters_array:
            filter_item = Gtk.MenuItem(translations.get_filter_name(filter_info.name))
            sub_sub_menu.append(filter_item)
            filter_item.connect("activate", callback, (clip, track, "add_filter", (event.x, filter_info)))
            filter_item.show()
        group_item.show()

    menu_item.show()
    return menu_item

def _get_compositors_add_menu_item(event, clip, track, callback, sensitive):
    menu_item = Gtk.MenuItem(_("Add Compositor"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    for i in range(0, len(mlttransitions.compositors)):
        compositor = mlttransitions.compositors[i]
        name, compositor_type = compositor
        #if compositor_type == "##affine":
        #    continue
        # Continue if compositor_type not present in system
        try:
            info = mlttransitions.mlt_compositor_transition_infos[compositor_type]
        except:
            continue
        compositor_item = Gtk.MenuItem(name)
        sub_menu.append(compositor_item)
        compositor_item.connect("activate", callback, (clip, track, "add_compositor", (event.x, compositor_type)))
        compositor_item.show()
 
    _add_separetor(sub_menu)
     
    alpha_combiners_menu_item = _get_alpha_combiners_add_menu_item(event, clip, track, callback, sensitive)
    sub_menu.append(alpha_combiners_menu_item)
    blenders_menu_item  = _get_blenders_add_menu_item(event, clip, track, callback, sensitive)
    sub_menu.append(blenders_menu_item)
    
    menu_item.set_sensitive(sensitive)
    menu_item.show()
    return menu_item

def _get_blenders_add_menu_item(event, clip, track, callback, sensitive):
    menu_item = Gtk.MenuItem(_("Blenders"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    for i in range(0, len(mlttransitions.blenders)):
        blend = mlttransitions.blenders[i]
        name, compositor_type = blend
        blender_item = Gtk.MenuItem(name)
        sub_menu.append(blender_item)
        blender_item.connect("activate", callback, (clip, track, "add_compositor", (event.x, compositor_type)))
        blender_item.show()
    menu_item.set_sensitive(sensitive)
    menu_item.show()
    return menu_item

def _get_alpha_combiners_add_menu_item(event, clip, track, callback, sensitive):
    menu_item = Gtk.MenuItem(_("Alpha Combiners"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    for i in range(0, len(mlttransitions.alpha_combiners)):
        alpha_combiner = mlttransitions.alpha_combiners[i]
        name, compositor_type = alpha_combiner
        alpha_combiner_item = Gtk.MenuItem(name)
        sub_menu.append(alpha_combiner_item)
        alpha_combiner_item.connect("activate", callback, (clip, track, "add_compositor", (event.x, compositor_type)))
        alpha_combiner_item.show()
    menu_item.set_sensitive(sensitive)
    menu_item.show()
    return menu_item
    
def _get_auto_fade_compositors_add_menu_item(event, clip, track, callback, sensitive):
    menu_item = Gtk.MenuItem(_("Add Fade"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    for i in range(0, len(mlttransitions.autofades)):
        auto_fade_compositor = mlttransitions.autofades[i]
        name, compositor_type = auto_fade_compositor
        try:
            info = mlttransitions.mlt_compositor_transition_infos[compositor_type]
        except:
            continue
        compositor_item = Gtk.MenuItem(name)
        sub_menu.append(compositor_item)
        compositor_item.connect("activate", callback, (clip, track, "add_autofade", (event.x, compositor_type)))
        compositor_item.show()
    menu_item.set_sensitive(sensitive)
    menu_item.show()
    return menu_item
    
def _get_match_frame_menu_item(event, clip, track, callback):
    menu_item = Gtk.MenuItem(_("Show Match Frame"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    start_item_monitor = Gtk.MenuItem(_("First Frame in Monitor"))
    sub_menu.append(start_item_monitor)
    start_item_monitor.connect("activate", callback, (clip, track, "match_frame_start_monitor", None))
    start_item_monitor.show()

    end_item_monitor = Gtk.MenuItem(_("Last Frame in Monitor"))
    sub_menu.append(end_item_monitor)
    end_item_monitor.connect("activate", callback, (clip, track, "match_frame_end_monitor", None))
    end_item_monitor.show()
    
    _add_separetor(sub_menu)
    
    start_item = Gtk.MenuItem(_("First Frame on Timeline"))
    sub_menu.append(start_item)
    start_item.connect("activate", callback, (clip, track, "match_frame_start", None))
    start_item.show()

    end_item = Gtk.MenuItem(_("Last Frame on Timeline"))
    sub_menu.append(end_item)
    end_item.connect("activate", callback, (clip, track, "match_frame_end", None))
    end_item.show()

    _add_separetor(sub_menu)
        
    clear_item = Gtk.MenuItem(_("Clear Match Frame"))
    sub_menu.append(clear_item)
    clear_item.connect("activate", callback, (clip, track, "match_frame_close", None))
    clear_item.show()
    
    menu_item.set_sensitive(True)
    menu_item.show()
    return menu_item

def _get_select_menu_item(event, clip, track, callback):
    menu_item = Gtk.MenuItem(_("Select"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    all_after = Gtk.MenuItem(_("All Clips After"))
    sub_menu.append(all_after)
    all_after.connect("activate", callback, (clip, track, "select_all_after", None))
    all_after.show()

    all_before = Gtk.MenuItem(_("All Clips Before"))
    sub_menu.append(all_before)
    all_before.connect("activate", callback, (clip, track, "select_all_before", None))
    all_before.show()

    menu_item.set_sensitive(True)
    menu_item.show()
    return menu_item
    
def _get_tool_integration_menu_item(event, clip, track, callback):
    menu_item = Gtk.MenuItem(_("Export To Tool"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    export_tools = toolsintegration.get_export_integrators()
    for integrator in export_tools:
        export_item = Gtk.MenuItem(copy.copy(integrator.tool_name))
        sub_menu.append(export_item)
        export_item.connect("activate", integrator.export_callback, (clip, track))
        if integrator.supports_clip_media(clip) == False:
            export_item.set_sensitive(False)
        export_item.show()

    menu_item.show()
    return menu_item

def _get_edit_menu_item(event, clip, track, callback):
    menu_item = Gtk.MenuItem(_("Edit"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    del_item = _get_menu_item(_("Delete"), callback, (clip, track, "delete", event.x))
    sub_menu.append(del_item)

    lift_item = _get_menu_item(_("Lift"), callback, (clip, track, "lift", event.x))
    sub_menu.append(lift_item)
    
    _add_separetor(sub_menu)
    
    length_item = _get_menu_item(_("Set Clip Length..."), callback, (clip, track, "length", event.x))
    sub_menu.append(length_item)

    stretch_next_item = _get_menu_item(_("Stretch Over Next Blank"), callback, (clip, track, "stretch_next", event.x))
    sub_menu.append(stretch_next_item)

    stretch_prev_item = _get_menu_item(_("Stretch Over Prev Blank"), callback, (clip, track, "stretch_prev", event.x))
    sub_menu.append(stretch_prev_item)
    
    menu_item.show()
    return menu_item
    
def _get_clone_filters_menu_item(event, clip, track, callback):
    menu_item = Gtk.MenuItem(_("Clone Filters"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    clone_item = Gtk.MenuItem(_("From Next Clip"))
    sub_menu.append(clone_item)
    clone_item.connect("activate", callback, (clip, track, "clone_filters_from_next", None))
    clone_item.show()

    clone_item = Gtk.MenuItem(_("From Previous Clip"))
    sub_menu.append(clone_item)
    clone_item.connect("activate", callback, (clip, track, "clone_filters_from_prev", None))
    clone_item.show()

    menu_item.show()
    return menu_item

def _get_mute_menu_item(event, clip, track, callback):
    menu_item = Gtk.MenuItem(_("Mute"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    item = Gtk.MenuItem(_("Unmute"))
    sub_menu.append(item)
    item.connect("activate", callback, (clip, track, "mute_clip", (False)))
    item.show()
    item.set_sensitive(not(clip.mute_filter==None))

    item = Gtk.MenuItem(_("Mute Audio"))
    sub_menu.append(item)
    item.connect("activate", callback, (clip, track, "mute_clip", (True)))
    item.show()
    item.set_sensitive(clip.mute_filter==None)

    menu_item.show()
    return menu_item

def _get_track_mute_menu_item(event, track, callback):
    menu_item = Gtk.MenuItem(_("Mute"))
    sub_menu = Gtk.Menu()
    menu_item.set_submenu(sub_menu)

    item = Gtk.MenuItem(_("Unmute"))
    sub_menu.append(item)
    if track.type == appconsts.VIDEO:
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_NOTHING))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_NOTHING)
    else:
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_VIDEO))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_VIDEO)
    item.show()

    if track.type == appconsts.VIDEO:
        item = Gtk.MenuItem(_("Mute Video"))
        sub_menu.append(item)
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_VIDEO))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_VIDEO)
        item.show()

    item = Gtk.MenuItem(_("Mute Audio"))
    sub_menu.append(item)
    if track.type == appconsts.VIDEO:
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_AUDIO))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_AUDIO)
    else:
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_ALL))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_ALL)
    item.show()

    if track.type == appconsts.VIDEO:
        item = Gtk.MenuItem(_("Mute All"))
        sub_menu.append(item)
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_ALL))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_ALL)
        item.show()

    menu_item.show()
    return menu_item

def _get_clip_properties_menu_item(event, clip, track, callback):
    properties_menu_item = Gtk.MenuItem(_("Properties"))
    properties_menu =  Gtk.Menu()
    properties_menu.add(_get_menu_item(_("Rename Clip"), callback,\
                      (clip, track, "rename_clip", event.x)))
    properties_menu.add(_get_color_menu_item(clip, track, callback))
    properties_menu_item.set_submenu(properties_menu)
    properties_menu_item.show_all()
    return properties_menu_item

def _get_color_menu_item(clip, track, callback):
    color_menu_item = Gtk.MenuItem(_("Clip Color"))
    color_menu =  Gtk.Menu()
    color_menu.add(_get_menu_item(_("Default"), callback, (clip, track, "clip_color", "default")))
    color_menu.add(_get_menu_item(_("Red"), callback, (clip, track, "clip_color", "red")))
    color_menu.add(_get_menu_item(_("Green"), callback, (clip, track, "clip_color", "green")))
    color_menu.add(_get_menu_item(_("Blue"), callback, (clip, track, "clip_color", "blue")))
    color_menu.add(_get_menu_item(_("Orange"), callback, (clip, track, "clip_color", "orange")))
    color_menu.add(_get_menu_item(_("Brown"), callback, (clip, track, "clip_color", "brown")))
    color_menu.add(_get_menu_item(_("Olive"), callback, (clip, track, "clip_color", "olive")))
    color_menu_item.set_submenu(color_menu)
    color_menu_item.show_all()
    return color_menu_item

def _get_clip_markers_menu_item(event, clip, track, callback):
    markers_menu_item = Gtk.MenuItem(_("Markers"))
    markers_menu =  Gtk.Menu()
    markers_exist = len(clip.markers) != 0
    #menu = markers_menu
    #guiutils.remove_children(menu)
    if markers_exist:
        for i in range(0, len(clip.markers)):
            marker = clip.markers[i]
            name, frame = marker
            item_str = utils.get_tc_string(frame) + " " + name
            markers_menu.add(_get_menu_item(item_str, callback, (clip, track, "go_to_clip_marker", str(i))))
        _add_separetor(markers_menu)
    else:
        no_markers_item = _get_menu_item(_("No Clip Markers"), callback, "dummy", False)
        markers_menu.add(no_markers_item)
        _add_separetor(markers_menu)
        
    markers_menu.add(_get_menu_item(_("Add Clip Marker At Playhead Position"), callback, (clip, track, "add_clip_marker", None)))
    del_item = _get_menu_item(_("Delete Clip Marker At Playhead Position"), callback, (clip, track, "delete_clip_marker", None), markers_exist==True)
    markers_menu.add(del_item)
    del_all_item = _get_menu_item(_("Delete All Clip Markers"), callback, (clip, track, "deleteall_clip_markers", None), markers_exist==True)
    markers_menu.add(del_all_item)
    markers_menu_item.set_submenu(markers_menu)
    markers_menu_item.show_all()
    return markers_menu_item

def _set_non_sensitive_if_state_matches(mutable, item, state):
    if mutable.mute_state == state:
        item.set_sensitive(False)

def display_media_file_popup_menu(media_file, callback, event):
    media_file_menu = media_file_popup_menu
    guiutils.remove_children(media_file_menu)

    # "Open in Clip Monitor" is sent as event id, same for all below
    media_file_menu.add(_get_menu_item(_("Rename"), callback,("Rename", media_file, event)))
    media_file_menu.add(_get_menu_item(_("Delete"), callback,("Delete", media_file, event)))
    _add_separetor(media_file_menu)
    media_file_menu.add(_get_menu_item(_("Open in Clip Monitor"), callback,("Open in Clip Monitor", media_file, event)))
    if media_file.type != appconsts.PATTERN_PRODUCER:
        media_file_menu.add(_get_menu_item(_("File Properties"), callback, ("File Properties", media_file, event)))

    if media_file.type != appconsts.IMAGE and media_file.type != appconsts.AUDIO and media_file.type != appconsts.PATTERN_PRODUCER:
        _add_separetor(media_file_menu)
        if media_file.type != appconsts.IMAGE_SEQUENCE:
            media_file_menu.add(_get_menu_item(_("Render Slow/Fast Motion File"), callback, ("Render Slow/Fast Motion File", media_file, event)))
        if media_file.type != appconsts.IMAGE_SEQUENCE:
            media_file_menu.add(_get_menu_item(_("Render Reverse Motion File"), callback, ("Render Reverse Motion File", media_file, event)))
    if media_file.type == appconsts.VIDEO or media_file.type == appconsts.IMAGE_SEQUENCE:
        item = _get_menu_item(_("Render Proxy File"), callback, ("Render Proxy File", media_file, event))
        media_file_menu.add(item)

    """
    if media_file.type == appconsts.VIDEO:
        if media_file.info != None:

            best_media_profile_index = mltprofiles.get_closest_matching_profile_index(media_file.info)
            project_profile_index = mltprofiles.get_index_for_name(PROJECT().profile.description())

            # Add this item if best profile does not match project profile
            if best_media_profile_index != project_profile_index:
                _add_separetor(media_file_menu)
                item = _get_menu_item(_("Change Project Profile To Match..."), callback, ("Project Profile", media_file, event))
                media_file_menu.add(item)
    """
    
    media_file_menu.popup(None, None, None, None, event.button, event.time)

def display_filter_stack_popup_menu(row, treeview, callback, event):
    filter_stack_menu = filter_stack_menu_popup_menu
    guiutils.remove_children(filter_stack_menu)

    filter_stack_menu.add(_get_menu_item(_("Toggle Active"), callback, ("toggle", row, treeview)))
    filter_stack_menu.add(_get_menu_item(_("Reset Values"), callback, ("reset", row, treeview)))
    _add_separetor(filter_stack_menu)
    filter_stack_menu.add(_get_menu_item(_("Move Up"), callback, ("moveup", row, treeview)))
    filter_stack_menu.add(_get_menu_item(_("Move Down"), callback, ("movedown", row, treeview)))
    
    filter_stack_menu.popup(None, None, None, None, event.button, event.time)

def display_media_log_event_popup_menu(row, treeview, callback, event):
    log_event_menu = log_event_popup_menu
    guiutils.remove_children(log_event_menu)

    log_event_menu.add(_get_menu_item(_("Display In Clip Monitor"), callback, ("display", row, treeview)))
    log_event_menu.add(_get_menu_item(_("Render Slow/Fast Motion File"), callback, ("renderslowmo",  row, treeview)))
    log_event_menu.add(_get_menu_item(_("Toggle Star"), callback, ("toggle", row, treeview)))
    log_event_menu.add(_get_menu_item(_("Delete"), callback, ("delete", row, treeview)))
    log_event_menu.popup(None, None, None, None, event.button, event.time)

def display_media_linker_popup_menu(row, treeview, callback, event):
    media_linker_menu = media_linker_popup_menu
    guiutils.remove_children(media_linker_menu)

    media_linker_menu.add(_get_menu_item(_("Set File Relink Path"), callback, ("set relink", row)))
    media_linker_menu.add(_get_menu_item(_("Delete File Relink Path"), callback, ("delete relink", row)))
    _add_separetor(media_linker_menu)
    media_linker_menu.add(_get_menu_item(_("Show Full Paths"), callback, ("show path", row)))
    media_linker_menu.popup(None, None, None, None, event.button, event.time)

def _add_separetor(menu):
    sep = Gtk.SeparatorMenuItem()
    sep.show()
    menu.add(sep)

def _get_menu_item(text, callback, data, sensitive=True):
    item = Gtk.MenuItem.new_with_label(text)
    item.connect("activate", callback, data)
    item.show()
    item.set_sensitive(sensitive)
    return item

def _get_radio_menu_item(text, callback, group):
    item = Gtk.RadioMenuItem(group, text, False)
    item.show()
    return item

def _get_image_menu_item(img, text, callback, data):
    item = Gtk.ImageMenuItem()
    item.set_image(img)
    item.connect("activate", callback, data)
    item.set_always_show_image(True)
    item.set_use_stock(False)
    item.set_label(text)
    item.show()
    return item

# --------------------------------------------------- profile info gui
def get_profile_info_box(profile, show_description=True):
    # Labels text
    label_label = Gtk.Label()
    set_profile_info_labels_text(label_label, show_description)

    # Values text
    value_label = Gtk.Label()
    set_profile_info_values_text(profile, value_label, show_description)

    # Create box
    hbox = Gtk.HBox()
    hbox.pack_start(label_label, False, False, 0)
    hbox.pack_start(value_label, True, True, 0)

    return hbox

def get_profile_info_small_box(profile):
    text = get_profile_info_text(profile)
    label = Gtk.Label(label=text)

    hbox = Gtk.HBox()
    hbox.pack_start(label, False, False, 0)

    return hbox

def get_profile_info_text(profile):
    str_list = []
    str_list.append(str(profile.width()))
    str_list.append(" x ")
    str_list.append(str(profile.height()))
    str_list.append(", " + str(profile.display_aspect_num()))
    str_list.append(":")
    str_list.append(str(profile.display_aspect_den()))
    str_list.append(", ")
    if profile.progressive() == True:
        str_list.append(_("Progressive"))
    else:
        str_list.append(_("Interlaced"))

    str_list.append("\n")
    str_list.append(_("Fps: ") + str(profile.fps()))
    pix_asp = float(profile.sample_aspect_num()) / profile.sample_aspect_den()
    pa_str =  "%.2f" % pix_asp
    str_list.append(", " + _("Pixel Aspect: ") + pa_str)

    return ''.join(str_list)

def set_profile_info_labels_text(label, show_description):
    str_list = []
    if show_description:
        str_list.append(_("Description:"))
        str_list.append("\n")
    str_list.append(_("Dimensions:"))
    str_list.append("\n")
    str_list.append(_("Frames per second:"))
    str_list.append("\n")
    str_list.append(_("Size:"))
    str_list.append("\n")
    str_list.append(_("Pixel aspect ratio: "))
    str_list.append("\n")
    str_list.append(_("Progressive:"))

    label_label_text = ''.join(str_list)
    label.set_text(label_label_text)
    label.set_justify(Gtk.Justification.LEFT)

def set_profile_info_values_text(profile, label, show_description):
    str_list = []
    if show_description:
        str_list.append(profile.description())
        str_list.append("\n")
    str_list.append(str(profile.display_aspect_num()))
    str_list.append(":")
    str_list.append(str(profile.display_aspect_den()))
    str_list.append("\n")
    str_list.append(str(profile.fps()))
    str_list.append("\n")
    str_list.append(str(profile.width()))
    str_list.append(" x ")
    str_list.append(str(profile.height()))
    str_list.append("\n")
    pix_asp = float(profile.sample_aspect_num()) / profile.sample_aspect_den()
    pa_str =  "%.2f" % pix_asp
    str_list.append(pa_str)
    str_list.append("\n")
    if profile.progressive() == True:
        prog = _("Yes")
    else:
        prog = _("No")
    str_list.append(prog)
    value_label_text = ''.join(str_list)
    label.set_text(value_label_text)
    label.set_justify(Gtk.Justification.LEFT)


class BigTCDisplay:

    def __init__(self):
        self.widget = cairoarea.CairoDrawableArea2( 170,
                                                    22,
                                                    self._draw)
        self.font_desc = Pango.FontDescription("Bitstream Vera Sans Mono Condensed 15")
        
        # Draw consts
        x = 2
        y = 2
        width = 166
        height = 24
        aspect = 1.0
        corner_radius = height / 3.5
        radius = corner_radius / aspect
        degrees = M_PI / 180.0

        self._draw_consts = (x, y, width, height, aspect, corner_radius, radius, degrees)

        self.TEXT_X = 18
        self.TEXT_Y = 1

        self.widget.connect("button-press-event", self._button_press)

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation

        # Draw round rect with gradient and stroke around for thin bezel
        self._round_rect_path(cr)
        if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
            cr.set_source_rgb(0.2, 0.2, 0.2)
        else:
            cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.fill_preserve()

        if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
            grad = cairo.LinearGradient (0, 0, 0, h)
            for stop in BIG_TC_GRAD_STOPS:
                grad.add_color_stop_rgba(*stop)
            cr.set_source(grad)
            cr.fill_preserve()

        grad = cairo.LinearGradient (0, 0, 0, h)
        for stop in BIG_TC_FRAME_GRAD_STOPS:
            grad.add_color_stop_rgba(*stop)
        cr.set_source(grad)
        cr.set_line_width(1)
        cr.stroke()

        # Get current TIMELINE frame str
        try:
            frame = PLAYER().tracktor_producer.frame()
            frame_str = utils.get_tc_string(frame)
        except:
            frame_str = "00:00:00:00"

        # Text
        layout = PangoCairo.create_layout(cr)
        layout.set_text(frame_str, -1)
        layout.set_font_description(self.font_desc)

        cr.set_source_rgb(*TC_COLOR)
        cr.move_to(self.TEXT_X, self.TEXT_Y)

        PangoCairo.update_layout(cr, layout)
        PangoCairo.show_layout(cr, layout)
                
    def _round_rect_path(self, cr):
        x, y, width, height, aspect, corner_radius, radius, degrees = self._draw_consts

        cr.new_sub_path()
        cr.arc (x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc (x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc (x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc (x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path ()

    def _button_press(self, widget, event):
        gui.big_tc.set_visible_child_name("BigTCEntry")
        entry = gui.big_tc.get_visible_child()
        entry.set_text(BigTCEntry().get_current_frame_text())
        entry.grab_focus()

    def _seek_frame(self, frame):
        PLAYER().seek_frame(frame)


class BigTCEntry:
    """
    Test class for replacement of BigTCDisplay, when Editing time position
    """

    def __init__(self):
        self.widget = Gtk.Entry()
        frame_str = self.get_current_frame_text()
        self.widget.set_text(frame_str)
        self.visible = False
        self.widget.connect("activate", self._enter_pressed)
        self.widget.connect("focus-out-event", self._focus_lost)
        
    def get_current_frame_text(self):
        try:
            frame = PLAYER().tracktor_producer.frame()
            frame_str = utils.get_tc_string(frame)
        except:
            frame_str = "00:00:00:00"
        return frame_str

    def _handle_set_time(self):
        frame_str = gui.big_tc.get_visible_child().get_text()
        frame = utils.get_tc_frame(frame_str)
        gui.big_tc.set_visible_child_name("BigTCDisplay")
        PLAYER().seek_frame(int(frame))

    def _enter_pressed(self, event):
        self._handle_set_time()
        gui.pos_bar.widget.grab_focus()

    def _focus_lost(self, widget, event):
        if gui.big_tc.get_visible_child_name() == "BigTCEntry":
            self._handle_set_time()


class MonitorTCDisplay:
    """
    Mostly copy-pasted from BigTCDisplay, just enough different to make common inheritance
    annoying.
    """
    def __init__(self):
        self.widget = cairoarea.CairoDrawableArea2( 94,
                                                    20,
                                                    self._draw)
        self.font_desc = Pango.FontDescription("Bitstream Vera Sans Mono Condensed 9")

        # Draw consts
        x = 2
        y = 2
        width = 90
        height = 16
        aspect = 1.0
        corner_radius = height / 3.5
        radius = corner_radius / aspect
        degrees = M_PI / 180.0

        self._draw_consts = (x, y, width, height, aspect, corner_radius, radius, degrees)

        self.FPS_NOT_SET = -99.0

        self._frame = 0
        self.use_internal_frame = False

        self.use_internal_fps = False # if False, fps value for calulating tc comes from utils.fps(),
                                       # if True, fps value from self.fps that will have to be set from user site
        self.fps = self.FPS_NOT_SET # this will have to be set from user site

    def set_frame(self, frame):
        self._frame = frame # this is used in tools, editor window uses PLAYER frame
        self.widget.queue_draw()

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation

        # Draw bg
        #cr.set_source_rgb(*guiutils.get_theme_bg_color())
        #cr.rectangle(0, 0, w, h)
        #cr.fill()

        # Draw round rect with gradient and stroke around for thin bezel
        self._round_rect_path(cr)
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.fill_preserve()

        if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
            grad = cairo.LinearGradient (0, 0, 0, h)
            for stop in BIG_TC_GRAD_STOPS:
                grad.add_color_stop_rgba(*stop)
            cr.set_source(grad)
            cr.fill_preserve()

        grad = cairo.LinearGradient (0, 0, 0, h)
        for stop in BIG_TC_FRAME_GRAD_STOPS:
            grad.add_color_stop_rgba(*stop)
        cr.set_source(grad)
        cr.set_line_width(1)
        cr.stroke()

        # Get current TIMELINE frame str
        if self.use_internal_frame:
            frame = self._frame
        else:
            frame = PLAYER().tracktor_producer.frame() # is this used actually?

        if self.use_internal_fps == False:
            frame_str = utils.get_tc_string(frame)
        else:
            if  self.fps != self.FPS_NOT_SET:
                frame_str = utils.get_tc_string_with_fps(frame, self.fps)
            else:
                frame_str = ""

        # Text
        layout = PangoCairo.create_layout(cr)
        layout.set_text(frame_str, -1)
        layout.set_font_description(self.font_desc)

        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.move_to(8, 2)
        PangoCairo.update_layout(cr, layout)
        PangoCairo.show_layout(cr, layout)

    def _round_rect_path(self, cr):
        x, y, width, height, aspect, corner_radius, radius, degrees = self._draw_consts

        cr.new_sub_path()
        cr.arc (x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc (x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc (x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc (x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path ()


class TimeLineLeftBottom:
    def __init__(self):
        self.widget = Gtk.HBox()
        self.update_gui()

    def update_gui(self):
        for child in self.widget.get_children():
            self.widget.remove(child)
        self.widget.pack_start(Gtk.Label(), True, True, 0)
        if PROJECT().proxy_data.proxy_mode == appconsts.USE_PROXY_MEDIA:
            proxy_img =  Gtk.Image.new_from_file(respaths.IMAGE_PATH + "project_proxy.png")
            self.widget.pack_start(proxy_img, False, False, 0)

        self.widget.show_all()
        self.widget.queue_draw()


class TracksNumbersSelect:
    def __init__(self, v_tracks, a_tracks):
        
        self.MAX_TRACKS = appconsts.MAX_TRACKS
        
        self.widget = Gtk.HBox()
        
        self.video_label = Gtk.Label(_("Video:"))
        self.video_tracks = Gtk.SpinButton.new_with_range(1, self.MAX_TRACKS, 1)
        self.video_tracks.set_value(v_tracks)
        self.video_tracks.connect("value-changed", self.video_tracks_changed)
        
        self.audio_label = Gtk.Label(_("Audio:"))
        self.audio_tracks = Gtk.SpinButton.new_with_range(0, self.MAX_TRACKS-1, 1)
        self.audio_tracks.set_value(a_tracks)
        self.audio_tracks.connect("value-changed", self.audio_tracks_changed)
        
        self.label = Gtk.Label(_("Number of Tracks:"))
        self.tracks_amount_info = Gtk.Label()
        self.set_total_tracks_info()

        self.widget.pack_start(self.label, False, False, 0)
        self.widget.pack_start(guiutils.pad_label(22,2), False, False, 0)
        self.widget.pack_start(self.video_label, False, False, 0)
        self.widget.pack_start(self.video_tracks, False, False, 0)
        self.widget.pack_start(guiutils.pad_label(22,2), False, False, 0)
        self.widget.pack_start(self.audio_label, False, False, 0)
        self.widget.pack_start(self.audio_tracks, False, False, 0)
        self.widget.pack_start(guiutils.pad_label(22,2), False, False, 0)
        self.widget.pack_start(self.tracks_amount_info, False, False, 0)
        self.widget.pack_start(Gtk.Label(), True, True, 0)

    def video_tracks_changed(self, adjustment):
        if self.video_tracks.get_value() + self.audio_tracks.get_value() > self.MAX_TRACKS:
            self.audio_tracks.set_value(self.MAX_TRACKS - self.video_tracks.get_value())
        self.set_total_tracks_info()

    def audio_tracks_changed(self, adjustment):
        if self.video_tracks.get_value() + self.audio_tracks.get_value() > self.MAX_TRACKS:
            self.video_tracks.set_value(self.MAX_TRACKS - self.audio_tracks.get_value())
        self.set_total_tracks_info()
        
    def set_total_tracks_info(self):
        self.tracks_amount_info.set_text(str(int(self.video_tracks.get_value() + self.audio_tracks.get_value())) + " / " + str(self.MAX_TRACKS))
        self.tracks_amount_info.queue_draw ()

    def get_tracks(self):
        return (int(self.video_tracks.get_value()), int(self.audio_tracks.get_value()))


class ClipLengthChanger:
    def __init__(self, clip):
        
        self.clip = clip
        
        self.widget = Gtk.HBox()
        
        frames = clip.clip_length()
        self.max_len = clip.get_length()

        self.frames_label = Gtk.Label(_("Frames:"))
        self.frames_spin = Gtk.SpinButton.new_with_range(1, self.max_len, 1)
        self.frames_spin.set_value(frames)
        self.frames_spin.connect("value-changed", self._length_changed)
        
        self.tc_length = Gtk.Entry()
        self.tc_length.set_text(utils.get_tc_string(frames))
        self.tc_length.connect("activate", self._enter_pressed)

        self.widget.pack_start(self.frames_label, False, False, 0)
        self.widget.pack_start(self.frames_spin, False, False, 0)
        self.widget.pack_start(guiutils.pad_label(22,2), False, False, 0)
        self.widget.pack_start(self.tc_length, False, False, 0)
        self.widget.pack_start(Gtk.Label(), True, True, 0)

    def _length_changed(self, adjustment):
        self.tc_length.set_text(utils.get_tc_string(self.frames_spin.get_value()))

    def _enter_pressed(self, event):
        frame_str = self.tc_length.get_text()
        frame = utils.get_tc_frame(frame_str)
        
        if frame > self.max_len:
            frame = self.max_len
            self.tc_length.set_text(utils.get_tc_string(frame))
        if frame < 0:
            frame = 0
            self.tc_length.set_text(utils.get_tc_string(frame))
        
        self.frames_spin.set_value(frame)
        
    def get_length(self):
        return int(self.frames_spin.get_value())

def get_gpl3_scroll_widget(size):
    license_file = open(respaths.GPL_3_DOC)
    license_text = license_file.read()

    view = Gtk.TextView()
    view.set_editable(False)
    view.set_pixels_above_lines(2)
    view.set_left_margin(2)
    view.set_wrap_mode(Gtk.WrapMode.WORD)
    view.get_buffer().set_text(license_text)

    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    sw.add(view)
    sw.set_size_request(*size)

    return sw

def get_translations_scroll_widget(size):
    trans_file = open(respaths.TRANSLATIONS_DOC)
    trans_text = trans_file.read()

    return get_text_scroll_widget(trans_text, size)
    
def get_text_scroll_widget(text, size):
    view = Gtk.TextView()
    view.set_editable(False)
    view.set_pixels_above_lines(2)
    view.set_left_margin(2)
    view.set_wrap_mode(Gtk.WrapMode.WORD)
    view.get_buffer().set_text(text)

    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    sw.add(view)
    sw.set_size_request(*size)

    return sw

def get_markers_menu_launcher(callback, pixbuf):
    m_launch = PressLaunch(callback, pixbuf)
    return m_launch

def get_markers_popup_menu(event, callback):
    seq = current_sequence()
    markers_exist = len(seq.markers) != 0
    menu = markers_menu
    guiutils.remove_children(menu)
    if markers_exist:
        for i in range(0, len(seq.markers)):
            marker = seq.markers[i]
            name, frame = marker
            item_str  = utils.get_tc_string(frame) + " " + name
            menu.add(_get_menu_item(item_str, callback, str(i) ))
        _add_separetor(menu)
    else:
        no_markers_item = _get_menu_item(_("No Markers"), callback, "dummy", False)
        menu.add(no_markers_item)
        _add_separetor(menu)
    menu.add(_get_menu_item(_("Add Marker"), callback, "add" ))
    del_item = _get_menu_item(_("Delete Marker"), callback, "delete", markers_exist==True)
    menu.add(del_item)
    del_all_item = _get_menu_item(_("Delete All Markers"), callback, "deleteall", markers_exist==True)
    menu.add(del_all_item)
    menu.show_all()
    menu.popup(None, None, None, None, event.button, event.time)

def get_all_tracks_popup_menu(event, callback):
    menu = tracks_menu
    guiutils.remove_children(menu)
    menu.add(_get_menu_item(_("Maximize Tracks"), callback, "max" ))
    menu.add(_get_menu_item(_("Maximize Video Tracks"), callback, "maxvideo" ))
    menu.add(_get_menu_item(_("Maximize Audio Tracks"), callback, "maxaudio" ))
    _add_separetor(menu)
    menu.add(_get_menu_item(_("Minimize Tracks"), callback, "min" ))
    _add_separetor(menu)
    menu.add(_get_menu_item(_("Activate All Tracks"), callback, "allactive" ))
    menu.add(_get_menu_item(_("Activate Only Current Top Active Track"), callback, "topactiveonly" ))
    _add_separetor(menu)
    shrink_tline_item = Gtk.CheckMenuItem(_("Vertical Shrink Timeline").encode('utf-8'))
    shrink_tline_item.set_active(PROJECT().get_project_property(appconsts.P_PROP_TLINE_SHRINK_VERTICAL))
    shrink_tline_item.show()
    shrink_tline_item.connect("toggled", callback, "shrink" )
    if len(current_sequence().tracks) == 11:
        shrink_tline_item.set_sensitive(False) # This can't do anything if 9 editable tracks in sequence
    menu.append(shrink_tline_item)
        
    menu.popup(None, None, None, None, event.button, event.time)

def get_audio_levels_popup_menu(event, callback):
    # needs renaming
    menu = levels_menu
    guiutils.remove_children(menu)


    """
    ponter_sensitive_item = Gtk.CheckMenuItem()
    ponter_sensitive_item.set_label(_("Tool Cursor Context Sensitive"))
    ponter_sensitive_item.set_active(editorstate.cursor_is_tline_sensitive)
    ponter_sensitive_item.connect("activate", callback, "pointer_sensitive_item")

    menu.append(ponter_sensitive_item) 
    
    _add_separetor(menu)
    """

    thumbs_item = Gtk.CheckMenuItem()
    thumbs_item.set_label(_("Display Clip Media Thumbnails"))
    thumbs_item.set_active(editorstate.display_clip_media_thumbnails)
    thumbs_item.connect("activate", callback, "thumbs")

    menu.append(thumbs_item)
    
    _add_separetor(menu)

    snapping_item = Gtk.CheckMenuItem()
    snapping_item.set_label(_("Snapping On"))
    snapping_item.set_active(snapping.snapping_on)
    snapping_item.connect("activate", callback, "snapping")

    menu.append(snapping_item)
    
    _add_separetor(menu)

    allways_item = Gtk.RadioMenuItem()
    allways_item.set_label(_("Display All Audio Levels"))
    menu.append(allways_item)

    on_request_item = Gtk.RadioMenuItem.new_with_label([allways_item], _("Display Audio Levels On Request"))

    menu.append(on_request_item)

    if editorstate.display_all_audio_levels == True:
        on_request_item.connect("activate", callback, "on request")
        allways_item.set_active(True)
        on_request_item.set_active(False)
    else:
        allways_item.connect("activate", callback, "all")
        allways_item.set_active(False)
        on_request_item.set_active(True)

    menu.show_all()
    menu.popup(None, None, None, None, event.button, event.time)

def get_clip_effects_editor_hamburger_menu(event, callback):
    # needs renaming
    menu = clip_effects_hamburger_menu
    guiutils.remove_children(menu)

    menu.add(_get_menu_item(_("Save Effect Values"), callback, "save"))
    menu.add(_get_menu_item(_("Load Effect Values"), callback, "load"))
    menu.add(_get_menu_item(_("Reset Effect Values"), callback, "reset"))
    
    _add_separetor(menu)
    
    menu.add(_get_menu_item(_("Delete Effect"), callback, "delete"))

    menu.show_all()
    menu.popup(None, None, None, None, event.button, event.time)

def get_compositor_editor_hamburger_menu(event, callback):
    # needs renaming
    menu = clip_effects_hamburger_menu
    guiutils.remove_children(menu)

    menu.add(_get_menu_item(_("Save Compositor Values"), callback, "save"))
    menu.add(_get_menu_item(_("Load Compositor Values"), callback, "load"))
    menu.add(_get_menu_item(_("Reset Compositor Values"), callback, "reset"))
    
    _add_separetor(menu)
    
    menu.add(_get_menu_item(_("Delete Compositor"), callback, "delete"))

    menu.show_all()
    menu.popup(None, None, None, None, event.button, event.time)
    
def get_monitor_view_popupmenu(launcher, event, callback):
    menu = monitor_menu
    guiutils.remove_children(menu)
    menu.add(_get_image_menu_item(Gtk.Image.new_from_file(
        respaths.IMAGE_PATH + "program_view_2.png"), _("Image"), callback, 0))
    menu.add(_get_image_menu_item(Gtk.Image.new_from_file(
        respaths.IMAGE_PATH + "vectorscope.png"), _("Vectorscope"), callback, 1))
    menu.add(_get_image_menu_item(Gtk.Image.new_from_file(
        respaths.IMAGE_PATH + "rgbparade.png"), _("RGB Parade"), callback, 2))

    _add_separetor(menu)

    overlay_menu_item = Gtk.MenuItem(_("Overlay Opacity").encode('utf-8'))
    overlay_menu_item.show()
    overlay_menu = Gtk.Menu()

    op_100 = Gtk.RadioMenuItem()
    op_100.set_label(_("100%").encode('utf-8'))
    op_100.connect("activate", callback, 3)
    op_100.show()
    overlay_menu.append(op_100)

    op_80 = Gtk.RadioMenuItem.new_with_label([op_100], _("80%").encode('utf-8'))
    op_80.connect("activate", callback, 4)
    op_80.show()
    overlay_menu.append(op_80)

    op_50 = Gtk.RadioMenuItem.new_with_label([op_100], _("50%").encode('utf-8'))
    op_50.connect("activate", callback, 5)
    op_50.show()
    overlay_menu.append(op_50)

    op_20 = Gtk.RadioMenuItem.new_with_label([op_100], _("20%").encode('utf-8'))
    op_20.connect("activate", callback, 6)
    op_20.show()
    overlay_menu.append(op_20)

    op_0 = Gtk.RadioMenuItem.new_with_label([op_100], _("0%").encode('utf-8'))
    op_0.connect("activate", callback, 7)
    op_0.show()
    overlay_menu.append(op_0)

    active_index = current_sequence().get_mix_index()
    items = [op_100, op_80, op_50, op_20, op_0]
    active_item = items[active_index]
    active_item.set_active(True)

    overlay_menu_item.set_submenu(overlay_menu)
    menu.append(overlay_menu_item)

    menu.popup(None, None, None, None, event.button, event.time)

def get_trim_view_popupmenu(launcher, event, callback):
    menu = trim_view_menu
    guiutils.remove_children(menu)

    trim_view_all = Gtk.RadioMenuItem()
    trim_view_all.set_label(_("Trim View On").encode('utf-8'))

    trim_view_all.show()
    menu.append(trim_view_all)
    
    trim_view_single = Gtk.RadioMenuItem.new_with_label([trim_view_all], _("Trim View Single Side Edits Only").encode('utf-8'))

    trim_view_single.show()
    menu.append(trim_view_single)

    no_trim_view = Gtk.RadioMenuItem.new_with_label([trim_view_all], _("Trim View Off").encode('utf-8'))

    no_trim_view.show()
    menu.append(no_trim_view)

    active_index = editorstate.show_trim_view # The values for this as defines in appconsts.py correspond to indexes here
    items = [trim_view_all, trim_view_single, no_trim_view]
    active_item = items[active_index]
    active_item.set_active(True)

    trim_view_all.connect("activate", callback, "trimon")
    trim_view_single.connect("activate", callback, "trimsingle")
    no_trim_view.connect("activate", callback, "trimoff")
    
    _add_separetor(menu)

    menu_item = _get_menu_item(_("Set Current Clip Frame Match Frame"), callback, "clipframematch" )
    if editorstate.timeline_visible() == True:
        menu_item.set_sensitive(False)
    menu.add(menu_item)
    
    menu_item = _get_menu_item(_("Clear Match Frame"), callback, "matchclear" )
    if gui.monitor_widget.view != monitorwidget.FRAME_MATCH_VIEW:
        menu_item.set_sensitive(False)
    menu.add(menu_item)

    menu.popup(None, None, None, None, event.button, event.time)

def get_file_filter_popup_menu(launcher, event, callback):
    menu = file_filter_menu
    guiutils.remove_children(menu)
    menu.set_accel_group(gui.editor_window.accel_group)

    menu_item = _get_image_menu_item(Gtk.Image.new_from_file(
        respaths.IMAGE_PATH + "show_all_files.png"), _("All Files"), callback, 0)
    menu.add(menu_item)

    menu_item = _get_image_menu_item(Gtk.Image.new_from_file(
        respaths.IMAGE_PATH + "show_video_files.png"),   _("Video Files"), callback, 1)
    menu.add(menu_item)

    menu_item = _get_image_menu_item(Gtk.Image.new_from_file(
        respaths.IMAGE_PATH + "show_audio_files.png"), _("Audio Files"), callback, 2)
    menu.add(menu_item)

    menu_item = _get_image_menu_item(Gtk.Image.new_from_file(
        respaths.IMAGE_PATH + "show_graphics_files.png"), _("Graphics Files"), callback, 3)
    menu.add(menu_item)

    menu_item = _get_image_menu_item(Gtk.Image.new_from_file(
        respaths.IMAGE_PATH + "show_imgseq_files.png"), _("Image Sequences"), callback, 4)
    menu.add(menu_item)

    menu_item = _get_image_menu_item(Gtk.Image.new_from_file(
        respaths.IMAGE_PATH + "show_pattern_producers.png"), _("Pattern Producers"), callback, 5)
    menu.add(menu_item)
    menu.show_all()
    menu.popup(None, None, None, None, event.button, event.time)

def get_columns_count_popup_menu(event, callback):
    menu = column_count_menu
    guiutils.remove_children(menu)
    menu.set_accel_group(gui.editor_window.accel_group)

    columns = gui.editor_window.media_list_view.columns

    menu_item_2 = Gtk.RadioMenuItem()
    menu_item_2.set_label(_("2 Columns"))
    menu_item_2.set_active(columns==2)
    menu_item_2.connect("activate", callback, 2)
    menu.append(menu_item_2)

    menu_item_3 = Gtk.RadioMenuItem.new_with_label([menu_item_2], _("3 Columns"))
    menu_item_3.connect("activate", callback, 3)
    menu_item_3.set_active(columns==3)
    menu.append(menu_item_3)

    menu_item_4 = Gtk.RadioMenuItem.new_with_label([menu_item_2], _("4 Columns"))
    menu_item_4.connect("activate", callback, 4)
    menu_item_4.set_active(columns==4)
    menu.append(menu_item_4)

    menu_item_5 = Gtk.RadioMenuItem.new_with_label([menu_item_2], _("5 Columns"))
    menu_item_5.connect("activate", callback, 5)
    menu_item_5.set_active(columns==5)
    menu.append(menu_item_5)

    menu_item_6 = Gtk.RadioMenuItem.new_with_label([menu_item_2], _("6 Columns"))
    menu_item_6.connect("activate", callback, 6)
    menu_item_6.set_active(columns==6)
    menu.append(menu_item_6)

    menu_item_7 = Gtk.RadioMenuItem.new_with_label([menu_item_2], _("7 Columns"))
    menu_item_7.connect("activate", callback, 7)
    menu_item_7.set_active(columns==7)
    menu.append(menu_item_7)

    menu.show_all()
    menu.popup(None, None, None, None, event.button, event.time)

def get_shorcuts_selector():
    shortcuts_combo = Gtk.ComboBoxText()
    current_pref_index = -1
    
    for i in range(0, len(shortcuts.shortcut_files)):
        shortcut_file = shortcuts.shortcut_files[i]
        shortcuts_combo.append_text(shortcuts.shortcut_files_display_names[i])
        if editorpersistance.prefs.shortcuts == shortcut_file:
            current_pref_index = i
    
    # Set current selection active
    if current_pref_index != -1:
        shortcuts_combo.set_active(current_pref_index)
    else:
        # Something is wrong, the pref shortcut file is not preset in the system.
        print "Shortcut file in editprpersistance.pref.shortcuts not found!"
        shortcuts_combo.set_active(0)

    return shortcuts_combo

class PressLaunch:
    def __init__(self, callback, surface, w=22, h=22):
        self.widget = cairoarea.CairoDrawableArea2( w,
                                                    h,
                                                    self._draw)
        self.widget.press_func = self._press_event

        self.callback = callback
        self.surface = surface
        self.surface_x  = 6
        self.surface_y  = 6

    def _draw(self, event, cr, allocation):
        cr.set_source_surface(self.surface, self.surface_x, self.surface_y)
        cr.paint()

    def _press_event(self, event):
        self.callback(self.widget, event)


class ImageMenuLaunch(PressLaunch):
    def __init__(self, callback, surface_list, w=22, h=22):
        PressLaunch.__init__(self, callback, surface_list[0], w, h)
        self.surface_list = surface_list

    def set_pixbuf(self, surface_index):
        self.surface = self.surface_list[surface_index]
        self.widget.queue_draw()


class ToolSelector(ImageMenuLaunch):
    def __init__(self, callback, surface_list, w, h):
        ImageMenuLaunch.__init__(self, callback, surface_list, w, h)
        # surface_list indexes and tool ids need hardcoded mapping, tool_ids and surface indexes cannot easily be made to correspond 
        self.TOOL_ID_TO_SURFACE_INDEX = {   appconsts.TLINE_TOOL_INSERT: 0,
                                            appconsts.TLINE_TOOL_OVERWRITE: 1,
                                            appconsts.TLINE_TOOL_TRIM: 2,
                                            appconsts.TLINE_TOOL_ROLL: 4,
                                            appconsts.TLINE_TOOL_SLIP: 5,
                                            appconsts.TLINE_TOOL_SPACER: 6,
                                            appconsts.TLINE_TOOL_BOX: 7,
                                            appconsts.TLINE_TOOL_RIPPLE_TRIM: 3,
                                            appconsts.TLINE_TOOL_CUT: 8,
                                            appconsts.TLINE_TOOL_KFTOOL: 9
                                     }
   
    def set_tool_pixbuf(self, tool_id):
        surface_index = self.TOOL_ID_TO_SURFACE_INDEX[tool_id]
        self.set_pixbuf(surface_index)
        
    def _draw(self, event, cr, allocation):
        PressLaunch._draw(self, event, cr, allocation)

        cr.move_to(27, 13)
        cr.line_to(32, 18)
        cr.line_to(37, 13)
        cr.close_path()
        if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
            cr.set_source_rgb(0, 0, 0)
        else:
            cr.set_source_rgb(0.66, 0.66, 0.66)
        cr.fill()


class HamburgerPressLaunch:
    def __init__(self, callback):
        self.widget = cairoarea.CairoDrawableArea2( 18,
                                                    18,
                                                    self._draw)
        self.widget.press_func = self._press_event
        self.sensitive = True
        self.callback = callback
        
        self.surface_active = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "hamburger.png")
        self.surface_not_active = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "hamburger_not_active.png")
        self.surface_x  = 0
        self.surface_y  = 0
    
    def set_sensitive(self, sensitive):
        self.sensitive = sensitive
        self.widget.queue_draw()

    def _draw(self, event, cr, allocation):
        if self.sensitive == True:
            surface = self.surface_active
        else:
            surface = self.surface_not_active
            
        cr.set_source_surface(surface, self.surface_x, self.surface_y)
        cr.paint()

    def _press_event(self, event):
        if self.sensitive == True:
            self.callback(self.widget, event)


class MonitorSwitch:
    def __init__(self, callback):
        self.WIDTH = 84
        self.HEIGHT = 22
        self.widget = cairoarea.CairoDrawableArea2( self.WIDTH ,
                                                    self.HEIGHT,
                                                    self._draw)
        self.widget.press_func = self._press_event

        self.tline_surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "timeline_button.png")
        self.tline_active_surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "timeline_button_active.png")
        self.clip_surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "clip_button.png")
        self.clip_active_surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "clip_button_active.png")
        
        self.callback = callback
        self.surface_x  = 6
        self.surface_y  = 6

    def _draw(self, event, cr, allocation):
        if editorstate.timeline_visible():
            tline_draw_surface = self.tline_active_surface 
            clip_draw_surface = self.clip_surface
        else:
            tline_draw_surface = self.tline_surface 
            clip_draw_surface = self.clip_active_surface
            
        cr.set_source_surface(tline_draw_surface, 10, 5)
        cr.paint()

        cr.set_source_surface(clip_draw_surface, 60, 7)
        cr.paint()
        
    def _press_event(self, event):
        if event.x < self.WIDTH / 2 and editorstate.timeline_visible() == False:
            self.callback(appconsts.MONITOR_TLINE_BUTTON_PRESSED)
        elif editorstate.timeline_visible() == True:
            self.callback(appconsts.MONITOR_CLIP_BUTTON_PRESSED)
        
