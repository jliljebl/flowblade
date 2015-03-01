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
import gobject
import pygtk
pygtk.require('2.0');
import gtk

import math
import pango
import pangocairo

import appconsts
from cairoarea import CairoDrawableArea
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
import respaths
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

# ------------------------------------------------- item lists 
class ImageTextTextListView(gtk.VBox):
    """
    GUI component displaying list with columns: img, text, text
    Middle column expands.
    """

    def __init__(self):
        gtk.VBox.__init__(self)
       
       # Datamodel: icon, text, text
        self.storemodel = gtk.ListStore(gtk.gdk.Pixbuf, str, str)
 
        # Scroll container
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # View
        self.treeview = gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(False)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(gtk.SELECTION_SINGLE)

        # Column views
        self.icon_col = gtk.TreeViewColumn("Icon")
        self.text_col_1 = gtk.TreeViewColumn("text1")
        self.text_col_2 = gtk.TreeViewColumn("text2")
        
        # Cell renderers
        self.icon_rend = gtk.CellRendererPixbuf()
        self.icon_rend.props.xpad = 6

        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_END)

        self.text_rend_2 = gtk.CellRendererText()
        self.text_rend_2.set_property("yalign", 0.0)

        # Build column views
        self.icon_col.set_expand(False)
        self.icon_col.set_spacing(5)
        self.icon_col.pack_start(self.icon_rend)
        self.icon_col.add_attribute(self.icon_rend, 'pixbuf', 0)
        
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 1)

        self.text_col_2.set_expand(False)
        self.text_col_2.pack_start(self.text_rend_2)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 2)
        
        # Add column views to view
        self.treeview.append_column(self.icon_col)
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
        self.scroll.show_all()

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows


# ------------------------------------------------- item lists 
class ImageTextImageListView(gtk.VBox):
    """
    GUI component displaying list with columns: img, text, img
    Middle column expands.
    """

    def __init__(self):
        gtk.VBox.__init__(self)
        
       # Datamodel: icon, text, icon
        self.storemodel = gtk.ListStore(gtk.gdk.Pixbuf, str, gtk.gdk.Pixbuf)
 
        # Scroll container
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # View
        self.treeview = gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(False)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(gtk.SELECTION_SINGLE)

        # Column views
        self.icon_col_1 = gtk.TreeViewColumn("icon1")
        self.text_col_1 = gtk.TreeViewColumn("text1")
        self.icon_col_2 = gtk.TreeViewColumn("icon2")
        
        # Cell renderers
        self.icon_rend_1 = gtk.CellRendererPixbuf()
        self.icon_rend_1.props.xpad = 6

        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_END)

        self.icon_rend_2 = gtk.CellRendererPixbuf()
        self.icon_rend_2.props.xpad = 6

        # Build column views
        self.icon_col_1.set_expand(False)
        self.icon_col_1.set_spacing(5)
        self.icon_col_1.pack_start(self.icon_rend_1)
        self.icon_col_1.add_attribute(self.icon_rend_1, 'pixbuf', 0)
        
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 1)

        self.icon_col_2.set_expand(False)
        self.icon_col_2.set_spacing(5)
        self.icon_col_2.pack_start(self.icon_rend_2)
        self.icon_col_2.add_attribute(self.icon_rend_2, 'pixbuf', 2)
        
        # Add column views to view
        self.treeview.append_column(self.icon_col_1)
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.icon_col_2)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
        self.scroll.show_all()

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows


class SequenceListView(ImageTextTextListView):
    """
    GUI component displaying list of sequences in project
    """

    def __init__(self, seq_name_edited_cb):
        ImageTextTextListView.__init__(self)
        
        # Icon path
        self.icon_path = respaths.IMAGE_PATH + "sequence.png" 
        
        # Set sequence name editable and connect 'edited' signal
        self.text_rend_1.set_property("editable", True)
        self.text_rend_1.connect("edited", 
                                 seq_name_edited_cb, 
                                 (self.storemodel, 1))

    def fill_data_model(self):
        """
        Creates displayed data.
        Displays icon, sequence name and sequence length
        """
        self.storemodel.clear()
        for seq in PROJECT().sequences:
            icon = gtk.gdk.pixbuf_new_from_file(self.icon_path)
            active = ""
            if seq == current_sequence():
                active = "<edit>"
            row_data = [icon,
                        seq.name, 
                        active]
            self.storemodel.append(row_data)
            self.scroll.queue_draw()

       
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
        tree_sel.set_mode(gtk.SELECTION_MULTIPLE)
        self.text_rend_1.set_property("editable", True)
        self.text_rend_1.set_property("font-desc", pango.FontDescription("sans bold 9"))
        self.text_rend_1.connect("edited", 
                                 file_name_edited_cb, 
                                 (self.storemodel, 1))
                                 
        self.text_rend_2.set_property("font-desc", pango.FontDescription("sans 8"))
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

        for bin in PROJECT().bins:
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "bin_5.png")
                row_data = [pixbuf,
                            bin.name, 
                            str(len(bin.file_ids))]
                self.storemodel.append(row_data)
                self.scroll.queue_draw()
            except gobject.GError, exc:
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


class FilterSwitchListView(gtk.VBox):
    """
    GUI component displaying list of filters applied to a clip.
    """

    def __init__(self, selection_cb, toggle_cb):
        gtk.VBox.__init__(self)
        
       # Datamodel: icon, text, icon
        self.storemodel = gtk.ListStore(gtk.gdk.Pixbuf, str, bool)
 
        # Scroll container
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # View
        self.treeview = gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(False)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(gtk.SELECTION_SINGLE)

        # Column views
        self.icon_col_1 = gtk.TreeViewColumn("icon1")
        self.text_col_1 = gtk.TreeViewColumn("text1")
        self.check_col_1 = gtk.TreeViewColumn("switch")
        
        # Cell renderers
        self.icon_rend_1 = gtk.CellRendererPixbuf()
        self.icon_rend_1.props.xpad = 6

        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_END)

        self.toggle_rend = gtk.CellRendererToggle()
        self.toggle_rend.set_property('activatable', True)
        self.toggle_rend.connect( 'toggled', self.toggled)

        # Build column views
        self.icon_col_1.set_expand(False)
        self.icon_col_1.set_spacing(5)
        self.icon_col_1.pack_start(self.icon_rend_1)
        self.icon_col_1.add_attribute(self.icon_rend_1, 'pixbuf', 0)
        
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 1)

        self.check_col_1.set_expand(False)
        self.check_col_1.set_spacing(5)
        self.check_col_1.pack_start(self.toggle_rend)
        self.check_col_1.add_attribute(self.toggle_rend, "active", 2)
        
        # Add column views to view
        self.treeview.append_column(self.icon_col_1)
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.check_col_1)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
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
        

class TextListView(gtk.VBox):
    """
    GUI component displaying list with  single column text column.
    """
    def __init__(self, width, column_name=None):
        gtk.VBox.__init__(self)
        
       # Datamodel: icon, text, text
        self.storemodel = gtk.ListStore(str)
 
        # Scroll container
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # View
        self.treeview = gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        if column_name == None:
            self.treeview.set_headers_visible(False)
            column_name = "text1"
        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        # Cell renderers
        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_END)

        # Build column views
        self.text_col_1 = gtk.TreeViewColumn(column_name)
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.text_col_1.set_min_width(width)
        self.text_col_1.pack_start(self.text_rend_1)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 0)

        # Add column views to view
        self.treeview.append_column(self.text_col_1)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
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
        self.treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)

    def fill_data_model(self, autosaves):
        self.storemodel.clear()
        for autosave_object in autosaves:
            since_time_str = utils.get_time_str_for_sec_float(autosave_object.age)
            row_data = ["Autosave created " + since_time_str + " ago."]
            self.storemodel.append(row_data)
        
        self.treeview.set_cursor("0") 
        
        self.scroll.queue_draw()


# -------------------------------------------- clip info
class ClipInfoPanel(gtk.VBox):
    
    def __init__(self):
        gtk.VBox.__init__(self, False, 2)

        self.name_label = guiutils.bold_label(_("Clip:"))
        self.name_value = gtk.Label()
        self.name_value.set_ellipsize(pango.ELLIPSIZE_END)

        self.track = guiutils.bold_label(_("Track:"))
        self.track_value = gtk.Label()

        self.position = guiutils.bold_label(_("Pos:"))
        self.position_value = gtk.Label()
        
        info_row_1 = gtk.HBox()
        info_row_1.pack_start(self.name_label, False, True, 0)
        info_row_1.pack_start(self.name_value, True, True, 0)

        info_row_2 = gtk.HBox()
        info_row_2.pack_start(self.track, False, False, 0)
        info_row_2.pack_start(self.track_value, True, True, 0)

        info_row_3 = gtk.HBox()
        info_row_3.pack_start(self.position, False, False, 0)
        info_row_3.pack_start(self.position_value, True, True, 0)

        self.pack_start(info_row_1, False, False, 0)
        self.pack_start(info_row_2, False, False, 0)
        self.pack_start(info_row_3, False, False, 0)
        
        self.set_size_request(CLIP_EDITOR_LEFT_WIDTH, 56)

    def display_clip_info(self, clip, track, index):
        self.name_label.set_text(_("<b>Clip: </b>"))
        self.name_value.set_text(clip.name)
        self.track.set_text(_("<b>Track: </b>"))
        self.track_value.set_text(track.get_name())
        self.position.set_text(_("<b>Position:</b>"))
        clip_start_in_tline = track.clip_start(index)
        tc_str = utils.get_tc_string(clip_start_in_tline)
        self.position_value.set_text(tc_str)
        self._set_use_mark_up()

    def set_no_clip_info(self):
        self.name_label.set_text(_("<b>Clip:</b>"))
        self.name_value.set_text("")
        self.track.set_text(_("<b>Track:</b>"))
        self.track_value.set_text("")
        self.position.set_text(_("<b>Position:</b>"))
        self.position_value.set_text("")
        self._set_use_mark_up()

    def _set_use_mark_up(self):
        self.name_label.set_use_markup(True)
        self.track.set_use_markup(True)
        self.position.set_use_markup(True)

    def set_enabled(self, value):
        self.name_label.set_sensitive(value)
        self.track.set_sensitive(value)
        self.position.set_sensitive(value)


class CompositorInfoPanel(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self, False, 2)

        self.source_track = gtk.Label()
        self.source_track_value = gtk.Label()

        self.destination_track = gtk.Label()
        self.destination_track_value = gtk.Label()

        self.position = gtk.Label()
        self.position_value = gtk.Label()

        self.length = gtk.Label()
        self.length_value = gtk.Label()

        info_row_2 = gtk.HBox()
        info_row_2.pack_start(self.source_track, False, True, 0)
        info_row_2.pack_start(self.source_track_value, True, True, 0)

        info_row_3 = gtk.HBox()
        info_row_3.pack_start(self.destination_track, False, True, 0)
        info_row_3.pack_start(self.destination_track_value, True, True, 0)
    
        info_row_4 = gtk.HBox()
        info_row_4.pack_start(self.position, False, True, 0)
        info_row_4.pack_start(self.position_value, True, True, 0)

        info_row_5 = gtk.HBox()
        info_row_5.pack_start(self.length, False, False, 0)
        info_row_5.pack_start(self.length_value, True, True, 0)

        PAD_HEIGHT = 2
        self.pack_start(info_row_2, False, False, 0)
        self.pack_start(guiutils.get_pad_label(5, PAD_HEIGHT), False, False, 0) 
        self.pack_start(info_row_3, False, False, 0)
        self.pack_start(guiutils.get_pad_label(5, PAD_HEIGHT), False, False, 0) 
        self.pack_start(info_row_4, False, False, 0)
        self.pack_start(guiutils.get_pad_label(5, PAD_HEIGHT), False, False, 0) 
        self.pack_start(info_row_5, False, False, 0)
        
        self.set_no_compositor_info()
        self.set_enabled(False)

    def display_compositor_info(self, compositor):
        src_track = utils.get_track_name(current_sequence().tracks[compositor.transition.b_track],current_sequence())
        self.source_track_value.set_text(src_track)
        
        dest_track = utils.get_track_name(current_sequence().tracks[compositor.transition.a_track], current_sequence())
        self.destination_track_value.set_text(dest_track)
        
        pos = utils.get_tc_string(compositor.clip_in)
        self.position_value.set_text(pos)
        
        length = utils.get_tc_string(compositor.clip_out - compositor.clip_in)
        self.length_value.set_text(length)

    def set_no_compositor_info(self):
        self.source_track.set_text(_("<b>Source Track:</b>"))
        self.source_track_value.set_text("")

        self.destination_track.set_text(_("<b>Destination Track:</b>"))
        self.destination_track_value.set_text("")

        self.position.set_text(_("<b>Position:</b>"))
        self.position_value.set_text("")

        self.length.set_text(_("<b>Length:</b>"))
        self.length_value.set_text("")

        self._set_use_mark_up()
        
    def _set_use_mark_up(self):
        self.source_track.set_use_markup(True)
        self.destination_track.set_use_markup(True)
        self.position.set_use_markup(True)
        self.length.set_use_markup(True)

    def set_enabled(self, value):
        self.source_track.set_sensitive(value)
        self.destination_track.set_sensitive(value)
        self.position.set_sensitive(value)
        self.length.set_sensitive(value)


# -------------------------------------------- media select panel
class MediaPanel():
    
    def __init__(self, media_file_popup_cb, double_click_cb):
        self.widget = gtk.VBox()
        self.row_widgets = []
        self.selected_objects = []
        self.columns = editorpersistance.prefs.media_columns
        self.media_file_popup_cb = media_file_popup_cb
        self.double_click_cb = double_click_cb
        self.monitor_indicator = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "monitor_indicator.png")
        
        global has_proxy_icon, is_proxy_icon, graphics_icon, imgseq_icon, audio_icon, pattern_icon
        has_proxy_icon = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "has_proxy_indicator.png")
        is_proxy_icon = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "is_proxy_indicator.png")
        graphics_icon = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "graphics_indicator.png")
        imgseq_icon =  gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "imgseq_indicator.png")
        audio_icon =  gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "audio_indicator.png")
        pattern_icon =  gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "pattern_producer_indicator.png")
        
    def get_selected_media_objects(self):
        return self.selected_objects
        
    def media_object_selected(self, media_object, widget, event):
        widget.grab_focus()
        if event.type == gtk.gdk._2BUTTON_PRESS:
             self.double_click_cb(media_object.media_file)
        elif event.button == 1:
            if (event.state & gtk.gdk.CONTROL_MASK):
                widget.modify_bg(gtk.STATE_NORMAL, gui.selected_bg_color)
                # only add to selected if not already there
                try:
                    self.selected_objects.index(media_object)
                except:
                    self.selected_objects.append(media_object)
            else:
                self.clear_selection()
                widget.modify_bg(gtk.STATE_NORMAL, gui.selected_bg_color)
                self.selected_objects.append(media_object)
        elif event.button == 3:
            self.clear_selection()
            display_media_file_popup_menu(media_object.media_file,
                                          self.media_file_popup_cb,
                                          event)
        elif event.type == gtk.gdk._2BUTTON_PRESS:
             print "double click"
        self.widget.queue_draw()

    def select_media_file(self, media_file):
        self.clear_selection()
        self.selected_objects.append(self.widget_for_mediafile[media_file])
    
    def select_media_file_list(self, media_files):
        self.clear_selection()
        for media_file in media_files:
            self.selected_objects.append(self.widget_for_mediafile[media_file])        

    def empty_pressed(self, widget, event):
        self.clear_selection()

    def select_all(self):
        self.clear_selection()
        for media_file, media_object in self.widget_for_mediafile.iteritems():
            media_object.widget.modify_bg(gtk.STATE_NORMAL, gui.selected_bg_color)
            self.selected_objects.append(media_object)

    def clear_selection(self):
        for m_obj in self.selected_objects:
            m_obj.widget.modify_bg(gtk.STATE_NORMAL, gui.note_bg_color)
        self.selected_objects = []

    def columns_changed(self, adjustment):
        self.columns = int(adjustment.get_value())
        editorpersistance.prefs.media_columns = self.columns
        editorpersistance.save()
        self.fill_data_model()

    def fill_data_model(self):
        for w in self.row_widgets:
            self.widget.remove(w)
        self.row_widgets = []
        self.widget_for_mediafile = {}
        self.selected_objects = []

        column = 0
        bin_index = 0
        row_box = gtk.HBox()
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
                
            media_object = MediaObjectWidget(media_file, self.media_object_selected, bin_index, self.monitor_indicator)
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
                row_box = gtk.HBox()
                column = 0
            bin_index += 1

        if column != 0:
            filler = self._get_empty_filler()
            row_box.pack_start(filler, True, True, 0)
            self.widget.pack_start(row_box, False, False, 0)
            self.row_widgets.append(row_box)

        filler = self._get_empty_filler()
        self.row_widgets.append(filler)
        self.widget.pack_start(filler, True, True, 0)

        self.widget.show_all()

    def _get_empty_filler(self):
        filler = gtk.EventBox()
        filler.connect("button-press-event", lambda w,e: self.empty_pressed(w,e))
        filler.add(gtk.Label())
        return filler


class MediaObjectWidget:
    
    def __init__(self, media_file, selected_callback, bin_index, indicator_icon):
        self.media_file = media_file
        self.selected_callback = selected_callback
        self.bin_index = bin_index
        self.indicator_icon = indicator_icon
        self.selected_callback = selected_callback
        self.widget = gtk.EventBox()
        self.widget.connect("button-press-event", lambda w,e: selected_callback(self, w, e))
        self.widget.dnd_media_widget_attr = True # this is used to identify widget at dnd drop
        self.widget.set_can_focus(True)
 
        self.align = gtk.Alignment()
        self.align.set_padding(3, 2, 3, 2)
        self.align.set_size_request(MEDIA_OBJECT_WIDGET_WIDTH, MEDIA_OBJECT_WIDGET_HEIGHT)
        
        self.vbox = gtk.VBox()

        self.img = CairoDrawableArea(appconsts.THUMB_WIDTH, appconsts.THUMB_HEIGHT, self._draw_icon)
        self.img.press_func = self._press
        self.img.dnd_media_widget_attr = True # this is used to identify widget at dnd drop

        txt = gtk.Label(media_file.name)
        txt.modify_font(pango.FontDescription("sans 9"))
        txt.set_ellipsize(pango.ELLIPSIZE_END)

        self.vbox.pack_start(self.img, True, True, 0)
        self.vbox.pack_start(txt, False, False, 0)
        
        self.align.add(self.vbox)
        
        self.widget.add(self.align)

    def _press(self, event):
        self.selected_callback(self, self.widget, event)
        
    def _draw_icon(self, event, cr, allocation):
        x, y, w, h = allocation
        cr.set_source_pixbuf(self.media_file.icon, 0, 0)
        cr.paint()
        if self.media_file == editorstate.MONITOR_MEDIA_FILE():
            cr.set_source_pixbuf(self.indicator_icon, 29, 22)
            cr.paint()     
        if self.media_file.mark_in != -1 and self.media_file.mark_out != -1:
            cr.set_source_rgb(1, 1, 1)
            cr.select_font_face ("sans-serif",
                     cairo.FONT_SLANT_NORMAL,
                     cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(9)
            cr.move_to(23, 80)
            clip_length = utils.get_tc_string(self.media_file.mark_out - self.media_file.mark_in + 1) #+1 out incl.
            cr.show_text("][ " + str(clip_length))
        
        if self.media_file.type != appconsts.PATTERN_PRODUCER:
            if self.media_file.is_proxy_file == True:
                cr.set_source_pixbuf(is_proxy_icon, 96, 6)
                cr.paint()
            elif self.media_file.has_proxy_file == True:
                cr.set_source_pixbuf(has_proxy_icon, 96, 6)
                cr.paint()

        if self.media_file.type == appconsts.IMAGE:
            cr.set_source_pixbuf(graphics_icon, 6, 6)
            cr.paint()

        if self.media_file.type == appconsts.IMAGE_SEQUENCE:
            cr.set_source_pixbuf(imgseq_icon, 6, 6)
            cr.paint()

        if self.media_file.type == appconsts.AUDIO:
            cr.set_source_pixbuf(audio_icon, 6, 6)
            cr.paint()

        if self.media_file.type == appconsts.PATTERN_PRODUCER:
            cr.set_source_pixbuf(pattern_icon, 6, 6)
            cr.paint()
        
        
            
# -------------------------------------------- context menus
class EditorSeparator:
    """
    GUI component used to add, move and remove keyframes to of 
    inside a single clip. Does not a reference of the property being
    edited and needs a parent editor to write keyframe values.
    """

    def __init__(self):
        self.widget = CairoDrawableArea(SEPARATOR_WIDTH, 
                                        SEPARATOR_HEIGHT,
                                        self._draw)
    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation
        
        # Draw bg
        cr.set_source_rgb(*(gui.bg_color_tuple))
        cr.rectangle(0, 0, w, h)
        cr.fill()
        
        # Draw separator
        cr.set_line_width(1.0)
        r,g,b = gui.fg_color_tuple
        cr.set_source_rgba(r,g,b,0.2)
        cr.move_to(8.5, 2.5)
        cr.line_to(w - 8.5, 2.5)
        cr.stroke()

# ---------------------------------------------- MISC WIDGETS
def get_monitor_view_select_combo(callback):
    pixbuf_list = [gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "program_view_2.png"), 
                   gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "vectorscope.png"),
                   gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "rgbparade.png")]
    menu_launch = ImageMenuLaunch(callback, pixbuf_list, w=24, h=20)
    menu_launch.pixbuf_y = 10
    return menu_launch

def get_compositor_track_select_combo(source_track, target_track, callback):
    tracks_combo = gtk.combo_box_new_text()
    #tracks_combo.append_text("Auto Track Below")
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
    track_menu = gtk.Menu()

    if track_obj.edit_freedom != appconsts.FREE:
        track_menu.append(_get_menu_item(_("Lock Track"), callback, (track,"lock", None), False))
        track_menu.append(_get_menu_item(_("Unlock Track"), callback, (track,"unlock", None), True))

    else:
        track_menu.append(_get_menu_item(_("Lock Track"), callback, (track,"lock", None), True))
        track_menu.append(_get_menu_item(_("Unlock Track"), callback, (track,"unlock", None), False))

    _add_separetor(track_menu)

    normal_size_item = _get_radio_menu_item(_("Large Height"), callback, None)
    normal_size_item.set_active(track_obj.height == appconsts.TRACK_HEIGHT_NORMAL)
    normal_size_item.connect("activate", callback, (track, "normal_height", None))
    track_menu.append(normal_size_item)
    small_size_item = _get_radio_menu_item(_("Normal Height"), callback, normal_size_item)
    small_size_item.set_active(track_obj.height != appconsts.TRACK_HEIGHT_NORMAL)
    small_size_item.connect("activate", callback, (track, "small_height", None))
    track_menu.append(small_size_item)

    _add_separetor(track_menu)
    
    track_menu.append(_get_track_mute_menu_item(event, track_obj, callback))

    track_menu.popup(None, None, None, event.button, event.time)

def display_clip_popup_menu(event, clip, track, callback):
    if clip.is_blanck_clip:
        display_blank_clip_popup_menu(event, clip, track, callback)
        return

    if hasattr(clip, "rendered_type"):
        display_transition_clip_popup_menu(event, clip, track, callback)
        return

    clip_menu = gtk.Menu()
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

        clip_menu.add(_get_menu_item(_("Split Audio"), callback,\
                      (clip, track, "split_audio", event.x), True))
        if track.id == current_sequence().first_video_index:
            active = True
        else:
            active = False
        clip_menu.add(_get_menu_item(_("Split Audio Synched"), callback,\
              (clip, track, "split_audio_synched", event.x), active))

    _add_separetor(clip_menu)

    if clip.waveform_data == None:
       clip_menu.add(_get_menu_item(_("Display Audio Level"), callback,\
                  (clip, track, "display_waveform", event.x), True))
    else:
       clip_menu.add(_get_menu_item(_("Clear Waveform"), callback,\
          (clip, track, "clear_waveform", event.x), True))
    
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
    clip_menu.add(_get_blenders_add_menu_item(event, clip, track, callback, active))
    
    _add_separetor(clip_menu)
    clip_menu.add(_get_clone_filters_menu_item(event, clip, track, callback))

    _add_separetor(clip_menu)
    
    clip_menu.add(_get_menu_item(_("Rename Clip"), callback,\
                      (clip, track, "rename_clip", event.x)))
    clip_menu.add(_get_color_menu_item(clip, track, callback))  
    clip_menu.add(_get_menu_item(_("Clip Info"), callback,\
                  (clip, track, "clip_info", event.x)))

    clip_menu.popup(None, None, None, event.button, event.time)

def display_transition_clip_popup_menu(event, clip, track, callback):
    clip_menu = gtk.Menu()
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
    clip_menu.popup(None, None, None, event.button, event.time)
    
def display_blank_clip_popup_menu(event, clip, track, callback):
    clip_menu = gtk.Menu()
    clip_menu.add(_get_menu_item(_("Strech Prev Clip to Cover"), callback, (clip, track, "cover_with_prev", event.x)))
    clip_menu.add(_get_menu_item(_("Strech Next Clip to Cover"), callback, (clip, track, "cover_with_next", event.x)))
    _add_separetor(clip_menu)
    clip_menu.add(_get_menu_item(_("Delete"), callback, (clip, track, "delete_blank", event.x)))
    clip_menu.popup(None, None, None, event.button, event.time)
    
def display_audio_clip_popup_menu(event, clip, track, callback):
    if clip.is_blanck_clip:
        display_blank_clip_popup_menu(event, clip, track, callback)
        return

    clip_menu = gtk.Menu()
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

    clip_menu.popup(None, None, None, event.button, event.time)

def display_compositor_popup_menu(event, compositor, callback):
    compositor_menu = gtk.Menu()
    compositor_menu.add(_get_menu_item(_("Open In Compositor Editor"), callback, ("open in editor",compositor)))
    _add_separetor(compositor_menu)
    compositor_menu.add(_get_menu_item(_("Sync with Origin Clip"), callback, ("sync with origin",compositor)))
    _add_separetor(compositor_menu)
    compositor_menu.add(_get_menu_item(_("Delete"), callback, ("delete",compositor)))
    compositor_menu.popup(None, None, None, event.button, event.time)

def _get_filters_add_menu_item(event, clip, track, callback):
    menu_item = gtk.MenuItem(_("Add Filter"))
    sub_menu = gtk.Menu()
    menu_item.set_submenu(sub_menu)
    
    for group in mltfilters.groups:
        group_name, filters_array = group
        group_item = gtk.MenuItem(group_name)
        sub_menu.append(group_item)
        sub_sub_menu = gtk.Menu()
        group_item.set_submenu(sub_sub_menu)
        for filter_info in filters_array:
            filter_item = gtk.MenuItem(translations.get_filter_name(filter_info.name))
            sub_sub_menu.append(filter_item)
            filter_item.connect("activate", callback, (clip, track, "add_filter", (event.x, filter_info)))
            filter_item.show()
        group_item.show()

    menu_item.show()
    return menu_item

def _get_audio_filters_add_menu_item(event, clip, track, callback):
    menu_item = gtk.MenuItem(_("Add Filter"))
    sub_menu = gtk.Menu()
    menu_item.set_submenu(sub_menu)
    
    audio_groups = mltfilters.get_audio_filters_groups()
    for group in audio_groups:
        group_name, filters_array = group
        group_item = gtk.MenuItem(group_name)
        sub_menu.append(group_item)
        sub_sub_menu = gtk.Menu()
        group_item.set_submenu(sub_sub_menu)
        for filter_info in filters_array:
            filter_item = gtk.MenuItem(translations.get_filter_name(filter_info.name))
            sub_sub_menu.append(filter_item)
            filter_item.connect("activate", callback, (clip, track, "add_filter", (event.x, filter_info)))
            filter_item.show()
        group_item.show()

    menu_item.show()
    return menu_item
    
def _get_compositors_add_menu_item(event, clip, track, callback, sensitive):
    menu_item = gtk.MenuItem(_("Add Compositor"))
    sub_menu = gtk.Menu()
    menu_item.set_submenu(sub_menu)
       
    for i in range(0, len(mlttransitions.compositors)):
        compositor = mlttransitions.compositors[i]
        name, compositor_type = compositor
        # Continue if compositor_type not present in system
        try:
            info = mlttransitions.mlt_compositor_transition_infos[compositor_type]
        except:
            continue
        compositor_item = gtk.MenuItem(name)
        sub_menu.append(compositor_item)
        compositor_item.connect("activate", callback, (clip, track, "add_compositor", (event.x, compositor_type)))
        compositor_item.show()
    menu_item.set_sensitive(sensitive)
    menu_item.show()
    return menu_item

def _get_blenders_add_menu_item(event, clip, track, callback, sensitive):
    menu_item = gtk.MenuItem(_("Add Blend"))
    sub_menu = gtk.Menu()
    menu_item.set_submenu(sub_menu)
    
    for i in range(0, len(mlttransitions.blenders)):
        blend = mlttransitions.blenders[i]
        name, compositor_type = blend
        blender_item = gtk.MenuItem(name)
        sub_menu.append(blender_item)
        blender_item.connect("activate", callback, (clip, track, "add_compositor", (event.x, compositor_type)))
        blender_item.show()
    menu_item.set_sensitive(sensitive)
    menu_item.show()
    return menu_item

def _get_clone_filters_menu_item(event, clip, track, callback):
    menu_item = gtk.MenuItem(_("Clone Filters"))
    sub_menu = gtk.Menu()
    menu_item.set_submenu(sub_menu)
    
    clone_item = gtk.MenuItem(_("From Next Clip"))
    sub_menu.append(clone_item)
    clone_item.connect("activate", callback, (clip, track, "clone_filters_from_next", None))
    clone_item.show()

    clone_item = gtk.MenuItem(_("From Previous Clip"))
    sub_menu.append(clone_item)
    clone_item.connect("activate", callback, (clip, track, "clone_filters_from_prev", None))
    clone_item.show()

    menu_item.show()
    return menu_item

def _get_mute_menu_item(event, clip, track, callback):
    menu_item = gtk.MenuItem(_("Mute"))
    sub_menu = gtk.Menu()
    menu_item.set_submenu(sub_menu)

    item = gtk.MenuItem(_("Unmute"))
    sub_menu.append(item)
    item.connect("activate", callback, (clip, track, "mute_clip", (False)))
    item.show()
    item.set_sensitive(not(clip.mute_filter==None))

    item = gtk.MenuItem(_("Mute Audio"))
    sub_menu.append(item)
    item.connect("activate", callback, (clip, track, "mute_clip", (True)))
    item.show()
    item.set_sensitive(clip.mute_filter==None)
    
    menu_item.show()
    return menu_item

def _get_track_mute_menu_item(event, track, callback):
    menu_item = gtk.MenuItem(_("Mute"))
    sub_menu = gtk.Menu()
    menu_item.set_submenu(sub_menu)

    item = gtk.MenuItem(_("Unmute"))
    sub_menu.append(item)
    if track.type == appconsts.VIDEO:
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_NOTHING))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_NOTHING)
    else:
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_VIDEO))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_VIDEO)
    item.show()
    
    if track.type == appconsts.VIDEO:
        item = gtk.MenuItem(_("Mute Video"))
        sub_menu.append(item)
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_VIDEO))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_VIDEO)
        item.show()

    item = gtk.MenuItem(_("Mute Audio"))
    sub_menu.append(item)
    if track.type == appconsts.VIDEO:
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_AUDIO))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_AUDIO)
    else:
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_ALL))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_ALL)
    item.show()

    if track.type == appconsts.VIDEO:
        item = gtk.MenuItem(_("Mute All"))
        sub_menu.append(item)
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_ALL))
        _set_non_sensitive_if_state_matches(track, item, appconsts.TRACK_MUTE_ALL)
        item.show()

    menu_item.show()
    return menu_item

def _get_color_menu_item(clip, track, callback):
    color_menu_item = gtk.MenuItem(_("Clip Color"))
    color_menu =  gtk.Menu()
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

def _set_non_sensitive_if_state_matches(mutable, item, state):
    if mutable.mute_state == state:
        item.set_sensitive(False)

def display_media_file_popup_menu(media_file, callback, event):
    media_file_menu = gtk.Menu()
    # "Open in Clip Monitor" is sent as event id, same for all below
    media_file_menu.add(_get_menu_item(_("Rename"), callback,("Rename", media_file, event)))
    media_file_menu.add(_get_menu_item(_("Delete"), callback,("Delete", media_file, event))) 
    _add_separetor(media_file_menu)
    media_file_menu.add(_get_menu_item(_("Open in Clip Monitor"), callback,("Open in Clip Monitor", media_file, event))) 
    media_file_menu.add(_get_menu_item(_("File Properties"), callback, ("File Properties", media_file, event)))
    _add_separetor(media_file_menu)
    media_file_menu.add(_get_menu_item(_("Render Slow/Fast Motion File"), callback, ("Render Slow/Fast Motion File", media_file, event)))
    item = _get_menu_item(_("Render Proxy File"), callback, ("Render Proxy File", media_file, event))
    media_file_menu.add(item)
    
    media_file_menu.popup(None, None, None, event.button, event.time)

def display_filter_stack_popup_menu(row, treeview, callback, event):
    filter_stack_menu = gtk.Menu()        
    filter_stack_menu.add(_get_menu_item(_("Toggle Active"), callback, ("toggle", row, treeview)))
    filter_stack_menu.add(_get_menu_item(_("Reset Values"), callback, ("reset", row, treeview)))
    filter_stack_menu.popup(None, None, None, event.button, event.time)

def display_media_log_event_popup_menu(row, treeview, callback, event):
    log_event_menu = gtk.Menu()        
    log_event_menu.add(_get_menu_item(_("Display In Clip Monitor"), callback, ("display", row, treeview)))
    log_event_menu.add(_get_menu_item(_("Toggle Star"), callback, ("toggle", row, treeview)))
    log_event_menu.add(_get_menu_item(_("Delete"), callback, ("delete", row, treeview)))
    log_event_menu.popup(None, None, None, event.button, event.time)

def display_media_linker_popup_menu(row, treeview, callback, event):
    media_linker_menu = gtk.Menu()        
    media_linker_menu.add(_get_menu_item(_("Set File Relink Path"), callback, ("set relink", row)))
    media_linker_menu.add(_get_menu_item(_("Delete File Relink Path"), callback, ("delete relink", row)))
    _add_separetor(media_linker_menu)
    media_linker_menu.add(_get_menu_item(_("Show Full Paths"), callback, ("show path", row)))
    media_linker_menu.popup(None, None, None, event.button, event.time)

def _add_separetor(menu):
    sep = gtk.SeparatorMenuItem()
    sep.show()
    menu.add(sep)
    
def _get_menu_item(text, callback, data, sensitive=True):
    item = gtk.MenuItem(text)
    item.connect("activate", callback, data)
    item.show()
    item.set_sensitive(sensitive)
    return item

def _get_radio_menu_item(text, callback, group):
    item = gtk.RadioMenuItem(group, text, False)
    item.show()
    return item

def _get_image_menu_item(img, text, callback, data):
    item = gtk.ImageMenuItem()
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
    label_label = gtk.Label()
    set_profile_info_labels_text(label_label, show_description)
    
    # Values text
    value_label = gtk.Label()
    set_profile_info_values_text(profile, value_label, show_description) 
    
    # Create box
    hbox = gtk.HBox()
    hbox.pack_start(label_label, False, False, 0)
    hbox.pack_start(value_label, True, True, 0)
    
    return hbox

def get_profile_info_small_box(profile):
    text = get_profile_info_text(profile)
    label = gtk.Label(text)

    hbox = gtk.HBox()
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
    label.set_justify(gtk.JUSTIFY_LEFT)

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
    label.set_justify(gtk.JUSTIFY_LEFT)


class BigTCDisplay:
    
    def __init__(self):
        self.widget = CairoDrawableArea(170, 
                                        22,
                                        self._draw)
        self.font_desc = pango.FontDescription("Bitstream Vera Sans Mono Condensed 15")
        
        #Draw consts
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

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation

        # Draw bg
        cr.set_source_rgba(*gui.bg_color_tuple) 
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # Draw round rect with gradient and stroke around for thin bezel
        self._round_rect_path(cr)        
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.fill_preserve()

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
        frame = PLAYER().tracktor_producer.frame()
        frame_str = utils.get_tc_string(frame)

        # Text
        pango_context = pangocairo.CairoContext(cr)
        layout = pango_context.create_layout()
        layout.set_text(frame_str)
        layout.set_font_description(self.font_desc)

        pango_context.set_source_rgb(*TC_COLOR)#0.7, 0.7, 0.7)
        pango_context.move_to(self.TEXT_X, self.TEXT_Y)
        pango_context.update_layout(layout)
        pango_context.show_layout(layout)

    def _round_rect_path(self, cr):
        x, y, width, height, aspect, corner_radius, radius, degrees = self._draw_consts

        cr.new_sub_path()
        cr.arc (x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc (x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc (x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc (x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path ()

class MonitorTCDisplay:
    """
    Mostly copy-pasted from BigTCDisplay, just enough different to make common inheritance 
    annoying.
    """
    def __init__(self):
        self.widget = CairoDrawableArea(94, 
                                        20,
                                        self._draw)
        self.font_desc = pango.FontDescription("Bitstream Vera Sans Mono Condensed 9")
        
        #Draw consts
        x = 2
        y = 2
        width = 90
        height = 16
        aspect = 1.0
        corner_radius = height / 3.5
        radius = corner_radius / aspect
        degrees = M_PI / 180.0
        
        self._draw_consts = (x, y, width, height, aspect, corner_radius, radius, degrees)
        
        self._frame = 0
        self.use_internal_frame = False

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
        cr.set_source_rgb(*(gui.bg_color_tuple))
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # Draw round rect with gradient and stroke around for thin bezel
        self._round_rect_path(cr)        
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.fill_preserve()

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
            frame = PLAYER().tracktor_producer.frame()
        frame_str = utils.get_tc_string(frame)

        # Text
        pango_context = pangocairo.CairoContext(cr)
        layout = pango_context.create_layout()
        layout.set_text(frame_str)
        layout.set_font_description(self.font_desc)

        pango_context.set_source_rgb(0.7, 0.7, 0.7)
        pango_context.move_to(8, 2)
        pango_context.update_layout(layout)
        pango_context.show_layout(layout)

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
        self.widget = gtk.HBox()        
        self.update_gui()

    def update_gui(self):
        for child in self.widget.get_children():
            self.widget.remove(child)
        self.widget.pack_start(gtk.Label(), True, True)
        if PROJECT().proxy_data.proxy_mode == appconsts.USE_PROXY_MEDIA:
            proxy_img =  gtk.image_new_from_file(respaths.IMAGE_PATH + "project_proxy.png")
            self.widget.pack_start(proxy_img, False, False)

        self.widget.show_all()
        self.widget.queue_draw()

        
def get_gpl3_scroll_widget(size):
    license_file = open(respaths.GPL_3_DOC)
    license_text = license_file.read()
    
    view = gtk.TextView()
    view.set_sensitive(False)
    view.set_pixels_above_lines(2)
    view.set_left_margin(2)
    view.set_wrap_mode(gtk.WRAP_WORD)
    view.get_buffer().set_text(license_text)

    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
    sw.add(view)
    sw.set_size_request(*size)
    
    return sw

def get_translations_scroll_widget(size):
    trans_file = open(respaths.TRANSLATIONS_DOC)
    trans_text = trans_file.read()
    
    view = gtk.TextView()
    view.set_sensitive(False)
    view.set_pixels_above_lines(2)
    view.set_left_margin(2)
    view.set_wrap_mode(gtk.WRAP_WORD)
    view.get_buffer().set_text(trans_text)

    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
    sw.add(view)
    sw.set_size_request(*size)
    
    return sw
    
def get_track_counts_combo_and_values_list():
    tracks_combo = gtk.combo_box_new_text()
    tracks_combo.append_text(_("5 video, 4 audio"))
    tracks_combo.append_text(_("4 video, 3 audio"))
    tracks_combo.append_text(_("3 video, 2 audio"))
    tracks_combo.append_text(_("2 video, 1 audio"))
    tracks_combo.append_text(_("8 video, 1 audio"))
    tracks_combo.append_text(_("1 video, 8 audio"))
    tracks_combo.set_active(0)
    tracks_combo_values_list = appconsts.TRACK_CONFIGURATIONS
    return (tracks_combo, tracks_combo_values_list)
    
def get_markers_menu_launcher(callback, pixbuf):
    m_launch = PressLaunch(callback, pixbuf)
    return m_launch

def get_markers_popup_menu(event, callback):
    seq = current_sequence()
    markers_exist = len(seq.markers) != 0
    menu = gtk.Menu()
    if markers_exist:
        for i in range(0, len(seq.markers)):
            marker = seq.markers[i]
            name, frame = marker
            item_str  = utils.get_tc_string(frame) + " " + name
            menu.add(_get_menu_item(_(item_str), callback, str(i) ))
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
    menu.popup(None, None, None, event.button, event.time)

def get_all_tracks_popup_menu(event, callback):
    menu = gtk.Menu()
    menu.add(_get_menu_item(_("Maximize Tracks"), callback, "max" ))
    menu.add(_get_menu_item(_("Maximize Video Tracks"), callback, "maxvideo" ))
    menu.add(_get_menu_item(_("Maximize Audio Tracks"), callback, "maxaudio" ))
    _add_separetor(menu)
    menu.add(_get_menu_item(_("Minimize Tracks"), callback, "min" ))
    menu.popup(None, None, None, event.button, event.time)

def get_monitor_view_popupmenu(launcher, event, callback):
    menu = gtk.Menu()
    menu.add(_get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "program_view_2.png"), _("Image"), callback, 0))
    menu.add(_get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "vectorscope.png"), _("Vectorscope"), callback, 1))
    menu.add(_get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "rgbparade.png"), _("RGB Parade"), callback, 2))
    menu.popup(None, None, None, event.button, event.time)

def get_mode_selector_popup_menu(launcher, event, callback):
    menu = gtk.Menu()
    menu.set_accel_group(gui.editor_window.accel_group)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "insertmove_cursor.png"), _("Insert"), callback, 0)
    menu_item.set_accel_path("<Actions>/WindowActions/InsertMode")
    menu.add(menu_item)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "overwrite_cursor.png"),    _("Overwrite"), callback, 1)
    menu_item.set_accel_path("<Actions>/WindowActions/OverMode")
    menu.add(menu_item)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "oneroll_cursor.png"), _("Trim"), callback, 2)
    menu_item.set_accel_path("<Actions>/WindowActions/OneRollMode")        
    menu.add(menu_item)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "tworoll_cursor.png"), _("Roll"), callback, 3)
    menu_item.set_accel_path("<Actions>/WindowActions/TwoRollMode") 
    menu.add(menu_item)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "slide_cursor.png"), _("Slip"), callback, 4)
    menu_item.set_accel_path("<Actions>/WindowActions/SlideMode") 
    menu.add(menu_item)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "multimove_cursor.png"), _("Spacer"), callback, 5)
    menu_item.set_accel_path("<Actions>/WindowActions/MultiMode") 
    menu.add(menu_item)
    
    menu.popup(None, None, None, event.button, event.time)

def get_file_filter_popup_menu(launcher, event, callback):
    menu = gtk.Menu()
    menu.set_accel_group(gui.editor_window.accel_group)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "show_all_files.png"), _("All Files"), callback, 0)
    menu.add(menu_item)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "show_video_files.png"),   _("Video Files"), callback, 1)
    menu.add(menu_item)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "show_audio_files.png"), _("Audio Files"), callback, 2)
    menu.add(menu_item)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "show_graphics_files.png"), _("Graphics Files"), callback, 3)
    menu.add(menu_item)
    
    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "show_imgseq_files.png"), _("Image Sequences"), callback, 4)
    menu.add(menu_item)

    menu_item = _get_image_menu_item(gtk.image_new_from_file(
        respaths.IMAGE_PATH + "show_pattern_producers.png"), _("Pattern Producers"), callback, 5)
    menu.add(menu_item)

    menu.popup(None, None, None, event.button, event.time)
    
class PressLaunch:
    def __init__(self, callback, pixbuf, w=22, h=22):
        self.widget = CairoDrawableArea(w, 
                                        h, 
                                        self._draw)
        self.widget.press_func = self._press_event

        self.callback = callback
        self.pixbuf = pixbuf
        self.pixbuf_x  = 6
        self.pixbuf_y  = 6

    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation
        
        # Draw bg
        cr.set_source_rgb(*gui.bg_color_tuple)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        
        cr.set_source_pixbuf(self.pixbuf, self.pixbuf_x, self.pixbuf_y)
        cr.paint()

    def _press_event(self, event):
        self.callback(self.widget, event)


class ImageMenuLaunch(PressLaunch):
    def __init__(self, callback, pixbuf_list, w=22, h=22):
        PressLaunch.__init__(self, callback, pixbuf_list[0], w, h)
        self.pixbuf_list = pixbuf_list

    def set_pixbuf(self, pixbuf_index):
        self.pixbuf = self.pixbuf_list[pixbuf_index]
        self.widget.queue_draw()
        

class ToolSelector(ImageMenuLaunch):
    def _draw(self, event, cr, allocation):
        PressLaunch._draw(self, event, cr, allocation)
        
        cr.move_to(27, 13)
        cr.line_to(32, 18)
        cr.line_to(37, 13)
        cr.close_path()
        cr.set_source_rgb(0, 0, 0)
        cr.fill()
