"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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
import math
import time

import gi
gi.require_version('PangoCairo', '1.0')

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
import gtkbuilder
import gui
import guiutils
import mltprofiles
import respaths
import renderconsumer
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
TC_ZEROS_COLOR = (0.4, 0.4, 0.4)

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
generator_icon = None
gmic_icon = None
selection_icon = None
title_icon = None

add_compositors_is_multi_selection = False 
 
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

        # View
        self.treeview = Gtk.TreeView(model=self.storemodel)
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
class TextTextListView(Gtk.VBox):
    """
    GUI component displaying list with columns: text, text
    Middle column expands.
    """

    def __init__(self,  headers_visible=False, header1="text", header2="text2"):
        GObject.GObject.__init__(self)

       # Datamodel: icon, text, text
        self.storemodel = Gtk.ListStore(str, str)

        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # View
        self.treeview = Gtk.TreeView(model=self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(headers_visible)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.SINGLE)

        # Column views
        self.text_col_1 = Gtk.TreeViewColumn(header1)
        self.text_col_2 = Gtk.TreeViewColumn(header2)

        # Cell renderers
        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", Pango.EllipsizeMode.END)
        self.text_rend_1.set_property("font", "Bold Sans 12")

        self.text_rend_2 = Gtk.CellRendererText()
        self.text_rend_2.set_property("yalign", 0.0)

        # Build column views
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1, True)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 0)

        self.text_col_2.set_expand(False)
        self.text_col_2.set_min_width(100)
        self.text_col_2.pack_start(self.text_rend_2, True)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 1)

        # Add column views to view
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()

    def connect_selection_changed(self, selection_cb):
        # Connect selection 'changed' signal
        tree_sel = self.treeview.get_selection()
        tree_sel.connect("changed", selection_cb)
        
    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows

    def get_selected_row_index(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return int(rows[0].to_string())


class MultiTextColumnListView(Gtk.VBox):
    """
    GUI component displaying list with columns: img, text, text
    Middle column expands.
    """

    def __init__(self, columns_number):
        GObject.GObject.__init__(self)

        self.columns_number = columns_number

        type_list = []
        for i in range(0, columns_number):
            type_list.append(str)

        self.storemodel = Gtk.ListStore.new(type_list)

        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # View
        self.treeview = Gtk.TreeView(model=self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(True)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.SINGLE)

        # Column views
        self.columns = []
        self.renderers = []
        for i in range(0, columns_number):
            text_col = Gtk.TreeViewColumn.new()#("text1")
            text_rend = Gtk.CellRendererText()
            
            text_col.set_expand(True)
            text_col.set_spacing(5)
            text_col.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
            text_col.set_min_width(50)
            text_col.pack_start(text_rend, True)
            text_col.add_attribute(text_rend, "text", i)
        
            self.columns.append(text_col)
            self.renderers.append(text_rend)
        
            self.treeview.append_column(text_col)
        
        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()

    def set_column_titles(self, titles):
        for i in range(0, len(titles)):
            self.columns[i].set_title(titles[i])
            
    def connect_selection_changed(self, selection_cb):
        # Connect selection 'changed' signal
        tree_sel = self.treeview.get_selection()
        tree_sel.connect("changed", selection_cb)
        
    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows

    def get_selected_row(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows[0]

    def get_selected_row_index(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return int(rows[0].to_string())
        
    def fill_data_model(self, data_rows):
        self.storemodel.clear()
        for row in data_rows:
            row_data = []
            for i in range(0, self.columns_number):
                row_data.append(row[i])
            self.storemodel.append(row_data)
        
        self.scroll.queue_draw()
        
# ------------------------------------------------- item lists
class BinTreeView(Gtk.VBox):
    """
    GUI component displaying list with columns: img, text, text
    Middle column expands.
    """

    def __init__(self, bin_selection_cb, bin_name_edit_cb, bins_popup_cb, button_press_cb):
        GObject.GObject.__init__(self)

        self.bins_popup_cb = bins_popup_cb
        self.button_press_cb = button_press_cb

       # Datamodel: icon, text, text (folder, name, item count)
        self.storemodel = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str)

        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # TreeView
        self.treeview = Gtk.TreeView(model=self.storemodel)
        self.treeview.connect('button-press-event', self._button_press_event)
        self.treeview.set_headers_visible(False)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.SINGLE)
        tree_sel.connect("changed", bin_selection_cb)
        
        # Cell renderers
        self.icon_rend = Gtk.CellRendererPixbuf()
        self.icon_rend.set_padding(3, 0)
        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.set_property("editable", True)
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
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "bin_5.png")
                row_data = [pixbuf,
                            media_bin.name,
                            str(len(media_bin.file_ids))]
                self.storemodel.append(row_data)
                
            except GObject.GError as exc:
                print("can't load icon", exc)
        
        self.scroll.queue_draw()
        
    def _button_press_event(self, widget, event):
        if event.button == 3:
            self.bins_popup_cb(widget, event)
        elif event.button == 1:
            self.button_press_cb()

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

        # View
        self.treeview = Gtk.TreeView(model=self.storemodel)
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

        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows


class SequenceListView(ImageTextImageListView):
    """
    GUI component displaying list of sequences in project
    """

    def __init__(self, seq_name_edited_cb, sequence_popup_cb, double_click_cb):
        ImageTextImageListView.__init__(self)
        self.sequence_popup_cb = sequence_popup_cb
        self.treeview.connect('button-press-event', self._button_press_event)

        self.double_click_cb = double_click_cb
        self.double_click_counter = 0 # We get 2 events for double click, we use this to only do one callback
        
        # Icon path
        self.icon_path = respaths.IMAGE_PATH + "sequence.png"
        self.arrow_path = respaths.IMAGE_PATH + "filter_save.png"
        
        # Set sequence name editable and connect 'edited' signal
        self.icon_rend_1.props.xpad = 3
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
            arrow = GdkPixbuf.Pixbuf.new_from_file(self.arrow_path )
            if seq != current_sequence():
                arrow = None
            row_data = [icon,
                        seq.name,
                        arrow]
            self.storemodel.append(row_data)
            self.scroll.queue_draw()

    def _button_press_event(self, widget, event):
        if event.button == 3:
            self.sequence_popup_cb(widget, event)
        # Double click handled separately
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            self.double_click_counter += 1
            if self.double_click_counter == 2:
                self.double_click_counter = 0
                self.double_click_cb()

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

        # View
        self.treeview = Gtk.TreeView(model=self.storemodel)
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

        # View
        self.treeview = Gtk.TreeView(model=self.storemodel)
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
        self.name_value.set_max_width_chars(30)

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
        pass # Seek and destroy callsites

# -------------------------------------------- compositor info
class PluginInfoPanel(Gtk.HBox):
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

        info_row_5 = Gtk.HBox()
        info_row_5.pack_start(self.length, False, False, 0)
        info_row_5.pack_start(self.length_value, False, False, 0)
        info_row_5.pack_start(Gtk.Label(), True, True, 0)

        self.pack_start(info_row_2, False, False, 0)
        self.pack_start(info_row_5, False, False, 0)

        self.set_spacing(4)
        self._set_use_mark_up()

    def display_plugin_info(self, clip, track_name):
        self.source_track.set_text(_("<b>Generator Clip on Track:</b>") + " ")
        self.length.set_text(_("<b>Length:</b>") + " ")

        self.source_track_value.set_text("<b>" + track_name + "</b>")

        length = utils.get_tc_string(clip.get_length())
        self.length_value.set_text("<b>" + length + "</b>")

        self._set_use_mark_up()
    """    
    def set_no_compositor_info(self):
        self.source_track.set_text("")
        self.source_track_value.set_text("")

        self.length.set_text("")
        self.length_value.set_text("")

        self._set_use_mark_up()
    """
    
    def _set_use_mark_up(self):
        self.source_track.set_use_markup(True)
        self.length.set_use_markup(True)
        self.length_value.set_use_markup(True)
        self.source_track_value.set_use_markup(True)

        
# -------------------------------------------- compositor info
class BinInfoPanel(Gtk.HBox):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.set_homogeneous(False)

        if editorstate.screen_size_small_height() == True:
            font_desc = "sans bold 8"
        else:
            font_desc = "sans bold 9"
            
        self.bin_name = Gtk.Label()

        self.bin_name.override_font(Pango.FontDescription(font_desc))
        self.bin_name.set_sensitive(False)
                       
        self.items = Gtk.Label()
        self.items_value = Gtk.Label()

        self.items.modify_font(Pango.FontDescription(font_desc))
        self.items_value.modify_font(Pango.FontDescription(font_desc))
        self.items.set_sensitive(False)
        self.items_value.set_sensitive(False)
        
        info_col_2 = Gtk.HBox()
        info_col_2.pack_start(self.bin_name, False, True, 0)
        info_col_2.pack_start(Gtk.Label(), True, True, 0)

        info_col_3 = Gtk.HBox()
        info_col_3.pack_start(self.items, False, False, 0)
        info_col_3.pack_start(self.items_value, False, False, 0)
        info_col_3.pack_start(Gtk.Label(), True, True, 0)

        self.ratings_filtering_info = Gtk.Label()
        self.ratings_filtering_info.set_sensitive(False)

        all_image = guiutils.get_image("show_all_ratings")
        all_image.set_tooltip_text(_("Show All Ratings"))
        favorites_image = guiutils.get_image("show_favorites")
        favorites_image.set_tooltip_text(_("Show Favorites"))
        bad_image = guiutils.get_image("hide_bad")
        bad_image.set_tooltip_text(_("Hide Bad"))
        self.image_box = Gtk.Stack.new() 	
        self.image_box.add_named (all_image, "show_all_ratings")
        self.image_box.add_named (favorites_image, "show_favorites")
        self.image_box.add_named (bad_image, "hide_bad")
        self.image_box.set_visible_child_name("show_all_ratings")

        self.pack_start(guiutils.pad_label(24, 4), False, False, 0)
        self.pack_start(info_col_2, False, False, 0)
        self.pack_start(guiutils.pad_label(12, 4), False, False, 0)
        self.pack_start(info_col_3, False, False, 0)
        self.pack_start(guiutils.pad_label(12, 4), False, False, 0)
        self.pack_start(self.image_box, False, False, 0)
        self.pack_start(Gtk.Label(), True, True, 0)
        
        self.set_spacing(4)

    def display_bin_info(self):        
        self.bin_name.set_text("<b>" + editorstate.PROJECT().c_bin.name + "</b>")
        self.items.set_text(_("<b>Items:</b>") + " ")
        self.items_value.set_text(str(len(editorstate.PROJECT().c_bin.file_ids)))

        if editorstate.media_view_ratings_filter == appconsts.MEDIA_RATINGS_SHOW_ALL:
            self.image_box.set_visible_child_name("show_all_ratings")
        elif editorstate.media_view_ratings_filter == appconsts.MEDIA_RATINGS_SHOW_FAVORITES:
            self.image_box.set_visible_child_name("show_favorites")
        else:
            self.image_box.set_visible_child_name("hide_bad")

        self._set_use_mark_up()

    def _set_use_mark_up(self):
        self.bin_name.set_use_markup(True)
        self.items.set_use_markup(True)
        self.items_value.set_use_markup(True)
        self.ratings_filtering_info.set_use_markup(True) 

        
# -------------------------------------------- media select panel
class MediaPanel():
    
    NORMAL_MODE = 0
    MOVE_MODE = 1
    
    def __init__(self, media_file_popup_cb, double_click_cb, panel_menu_cb):
        self.widget = Gtk.VBox()
        self.widget.set_name("darker-bg-widget")
        self.row_widgets = []
        self.selected_objects = []
        self.columns = editorpersistance.prefs.media_columns
        self.media_file_popup_cb = media_file_popup_cb
        self.panel_menu_cb = panel_menu_cb
        self.double_click_cb = double_click_cb
        self.monitor_indicator = guiutils.get_cairo_image("monitor_indicator", force=False) # Aug-2019 - SvdB - BB - We want to keep the small icon for this
        self.last_event_time = 0.0
        self.last_ctrl_selected_media_object = None
        self.last_pressed = None
        self.double_click_release = False # needed to get focus over to pos bar after double click, usually media object grabs focus
        
        self.mode = MediaPanel.NORMAL_MODE
        self.ignore_relese_for_move = False
            
        global has_proxy_icon, is_proxy_icon, graphics_icon, imgseq_icon, audio_icon, \
        pattern_icon, profile_warning_icon, unused_icon, generator_icon, gmic_icon, \
        selection_icon, title_icon

        has_proxy_icon = guiutils.get_cairo_image("has_proxy_indicator")
        is_proxy_icon = guiutils.get_cairo_image("is_proxy_indicator")
        graphics_icon = guiutils.get_cairo_image("graphics_indicator")
        imgseq_icon = guiutils.get_cairo_image("imgseq_indicator")
        audio_icon = guiutils.get_cairo_image("audio_indicator")
        pattern_icon = guiutils.get_cairo_image("pattern_producer_indicator")
        profile_warning_icon = guiutils.get_cairo_image("profile_warning")
        unused_icon = guiutils.get_cairo_image("unused_indicator")
        generator_icon = guiutils.get_cairo_image("generator_indicator")
        gmic_icon = guiutils.get_cairo_image("gmic_indicator")
        selection_icon = guiutils.get_cairo_image("selection_indicator")
        title_icon = guiutils.get_cairo_image("open_titler")
        
    def get_selected_media_objects(self):
        return self.selected_objects

    def get_selected_media_objects_for_drag(self):
        last_pressed = self.selected_objects[-1]
        return [last_pressed]
 
    def media_object_selected_test(self, media_object):
        if media_object in self.selected_objects:
            return True
        else:
            return False
 
    def init_move(self):
        self.mode = MediaPanel.MOVE_MODE
        self.widget.queue_draw()
        
    def media_object_selected(self, media_object, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.double_click_release = True
            self.clear_selection()
            self.selected_objects.append(media_object)
            self.widget.queue_draw()
            gui.pos_bar.widget.grab_focus()
            GLib.idle_add(self.double_click_cb, media_object.media_file)
            return

        # HACK! We're using event times to exclude double events when icon is pressed
        now = time.time()
        if (now - self.last_event_time) < 0.05:
            self.last_event_time = now
            return
        self.last_event_time = now

        if self.mode == MediaPanel.MOVE_MODE:
            self.mode = MediaPanel.NORMAL_MODE
            self.last_pressed = media_object
            self.do_clicked_move()
            return

        widget.grab_focus()

        self.last_pressed = media_object # We need this data because self.selected_objects holds 
                                         # no information on which media object was pressed last 
                                         # when dragging onto timeline.

        if event.button == 1:
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                
                # add to selected if not there
                try:
                    index = self.selected_objects.index(media_object)
                except:
                    self.selected_objects.append(media_object)
                    self.widget.queue_draw()
                    self.last_ctrl_selected_media_object = media_object
                    return
            elif (event.get_state() & Gdk.ModifierType.SHIFT_MASK) and len(self.selected_objects) > 0:
                # Get data on current selection and pressed media object
                first_selected = -1
                last_selected = -1
                pressed_widget = -1
                for i in range(0, len(current_bin().file_ids)):
                    file_id = current_bin().file_ids[i]
                    m_file = PROJECT().media_files[file_id]
                    m_obj = self.widget_for_mediafile[m_file]
                    if m_obj in self.selected_objects:
                        selected = True
                    else:
                        selected = False
                    
                    if selected and first_selected == -1:
                        first_selected = i
                    if selected:
                        last_selected = i
                    if media_object == m_obj:
                        pressed_widget = i
                
                # Get new selection range
                if pressed_widget < first_selected:
                    sel_range = (pressed_widget, first_selected)
                elif pressed_widget > last_selected:
                    sel_range = (last_selected, pressed_widget)
                else:
                    sel_range = (pressed_widget, pressed_widget)
                    
                self.clear_selection()
                
                # Select new range
                start, end = sel_range
                for i in range(start, end + 1):
                    file_id = current_bin().file_ids[i]
                    m_file = PROJECT().media_files[file_id]
                    m_obj = self.widget_for_mediafile[m_file]
                    
                    self.selected_objects.append(m_obj)
            else:
                if not(media_object in self.selected_objects):
                    self.selected_objects.append(media_object)

        elif event.button == 3:
            if self.media_object_selected_test(media_object) == False:
                self.clear_selection()
            self.media_file_popup_cb(media_object.widget,
                                     media_object.media_file,
                                     event)

        self.widget.queue_draw()

    def release_on_media_object(self, media_object, widget, event):
        if self.ignore_relese_for_move == True:
            self.ignore_relese_for_move = False
            return
        
        if self.last_ctrl_selected_media_object == media_object:
            self.last_ctrl_selected_media_object = None
            return
        
        if not self.double_click_release:
            widget.grab_focus()
        else:
            self.double_click_release = False # after double click we want bos bar to have focus
            
        if event.button == 1:
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                # remove from selected if already there
                try:
                    index = self.selected_objects.index(media_object)
                    self.selected_objects.remove(media_object)
                except:
                    pass
            elif (event.get_state() & Gdk.ModifierType.SHIFT_MASK):
                pass
            else:
                self.clear_selection()
                self.selected_objects.append(media_object)

            self.widget.queue_draw()

    def select_media_file(self, media_file):
        self.clear_selection()
        self.selected_objects.append(self.widget_for_mediafile[media_file])

    def select_media_file_list(self, media_files):
        self.clear_selection()
        for media_file in media_files:
            self.selected_objects.append(self.widget_for_mediafile[media_file])

    def update_selected_bg_colors(self):
        self.widget.queue_draw()

    def empty_pressed(self, widget, event):
        self.clear_selection()
        if event.button == 3:
            self.panel_menu_cb(widget, event)

    def select_all(self):
        self.clear_selection()
        bg_color = gui.get_selected_bg_color()

        for media_file, media_object in self.widget_for_mediafile.items():
            self.selected_objects.append(media_object)

        self.widget.queue_draw()

    def clear_selection(self):
        self.selected_objects = []

        # Clear CTRL+X selection too.
        paste_data = editorstate.get_copy_paste_objects()
        if paste_data != None:
            data_type, objs = paste_data
            if data_type == appconsts.CUT_PASTE_MEDIA_ITEMS:
                editorstate.clear_copy_paste_objects()

        self.widget.queue_draw()

    def do_clicked_move(self):
        # We need this savad because fill_data_model() clears selection.
        selected_length = len(self.selected_objects)
        first_item_id = self.selected_objects[0].media_file.id
        
        # Remove from list
        for move_file_widget in self.selected_objects:
            pop_index = current_bin().file_ids.index(move_file_widget.media_file.id)
            current_bin().file_ids.pop(pop_index)

        # Put back
        insert_index = current_bin().file_ids.index(self.last_pressed.media_file.id)
        for move_file_widget in self.selected_objects:
            current_bin().file_ids.insert(insert_index, move_file_widget.media_file.id)
            insert_index += 1

        self.fill_data_model() # This also clears selections.

        # Select new range
        start = current_bin().file_ids.index(first_item_id)
        end = start + selected_length
        for i in range(start, end):
            file_id = current_bin().file_ids[i]
            m_file = PROJECT().media_files[file_id]
            m_obj = self.widget_for_mediafile[m_file]

            self.selected_objects.append(m_obj)

        self.ignore_relese_for_move = True
        self.widget.queue_draw()
        
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
            
            image = guiutils.get_image("media_panel_empty")
            image.set_sensitive(False)
            dnd.connect_media_drop_widget(image)
            filler = self._get_empty_filler(image)
            self.widget.pack_start(filler, False, False, 0)
            self.row_widgets.append(filler)
            
            self.add_info_text_row(_("Right Click to Add Media."))
            self.add_info_text_row(_("\nRight Click on Timeline Clips, Media Items or"))
            self.add_info_text_row(_("Tracks Column to access related features."))

            filler = self._get_empty_filler()
            dnd.connect_media_drop_widget(filler)
            self.row_widgets.append(filler)
            self.widget.pack_start(filler, True, True, 0)
            self.widget.show_all()
            return

        column = 0
        row_box = Gtk.HBox()
        dnd.connect_media_drop_widget(row_box)
        row_box.set_size_request(MEDIA_OBJECT_WIDGET_WIDTH * self.columns, MEDIA_OBJECT_WIDGET_HEIGHT)

        unused_list = PROJECT().get_unused_media()

        for file_id in current_bin().file_ids:
            media_file = PROJECT().media_files[file_id]

            # Filter view file type.
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
            if ((editorstate.media_view_filter == appconsts.SHOW_CONTAINERS)
                and (media_file.container_data == None)):
                continue
            if ((editorstate.media_view_filter == appconsts.SHOW_UNUSED_FILES)
                and (media_file not in unused_list)):
                continue
            # Filter view ratings.
            if ((editorstate.media_view_ratings_filter == appconsts.MEDIA_RATINGS_HIDE_BAD)
                and (media_file.rating == appconsts.MEDIA_FILE_BAD)):
                continue
            if ((editorstate.media_view_ratings_filter == appconsts.MEDIA_RATINGS_SHOW_FAVORITES)
                and (media_file.rating != appconsts.MEDIA_FILE_FAVORITE)):
                continue
                
            media_object = MediaObjectWidget(media_file,
                                            self, 
                                            self.media_object_selected, 
                                            self.release_on_media_object, 
                                            self.monitor_indicator,
                                            self.media_object_selected_test)
                                            
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
        if widget == None:
            filler = gtkbuilder.EventBox(Gtk.Label(), "button-press-event", self.empty_pressed)
        else:
            filler = gtkbuilder.EventBox(widget, "button-press-event", self.empty_pressed)
        return filler

    def add_info_text_row(self, txt):
        info = Gtk.Label(label=txt)
        info.set_sensitive(False)
        dnd.connect_media_drop_widget(info)
        filler = self._get_empty_filler(info)
        self.widget.pack_start(filler, False, False, 0)
        self.row_widgets.append(filler)
            
class MediaObjectWidget:

    def __init__(self, media_file, panel, selected_callback, release_callback, indicator_icon, is_selected_test):
        self.media_file = media_file
        self.panel = panel
        self.selected_callback = selected_callback
        self.is_selected_test = is_selected_test
        self.indicator_icon = indicator_icon
        self.matches_project_profile = media_file.matches_project_profile()

        r, g, b = utils.cairo_color_from_gdk_color(gui.get_selected_bg_color())
        self.selected_color = (r, g, b, 1.0)
        self.move_color  = (0.5, 0.5, 0.5, 1.0)

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

        self.create_round_rect_path(cr, 0, 0, w - 5, h - 5, 6.0)
        cr.clip()
        
        cr.set_source_surface(self.media_file.icon, 0, 0)
        cr.paint()

        # Draw rating indicator if needed.
        if self.media_file.rating == appconsts.MEDIA_FILE_FAVORITE:
            info_color = (0.2, 0.8, 0.2)
        elif self.media_file.rating == appconsts.MEDIA_FILE_BAD:
            info_color = (0.85, 0.25, 0.25)
        if self.media_file.rating != appconsts.MEDIA_FILE_UNRATED:
            cr.set_line_width(9.5)
            cr.set_source_rgb(*info_color)
            cr.move_to(0, h - 9.5)
            cr.line_to(w, h - 9.5)
            cr.stroke()
            
        cr.reset_clip()
        cr.set_source_rgba(0,0,0,0.3)
        
        # Draw blue outline if selected.
        if self.is_selected_test(self):
            cr.set_source_rgba(*self.selected_color)

            if self.panel.mode == MediaPanel.MOVE_MODE:
                cr.set_source_rgba(*self.move_color)

        # Indicate CTRL+X cut items that have not been pasted yet
        # with red outline.
        copy_paste_data = editorstate.get_copy_paste_objects()
        if copy_paste_data != None:
            object_type, file_ids = copy_paste_data
            if object_type == appconsts.CUT_PASTE_MEDIA_ITEMS:
                if self.media_file.id in file_ids:
                    cr.set_source_rgba(1,0,0,0.3)
        cr.set_line_width(3.0)
        self.create_round_rect_path(cr, 0, 0, w - 5, h - 5, 6.0)
        cr.stroke()
        
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
        cr.rectangle(28,71,62,12)
        cr.fill()
            
        cr.move_to(30, 79)
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

        if hasattr(self.media_file, "container_data") and self.media_file.container_data != None:
            if self.media_file.container_data.container_type == appconsts.CONTAINER_CLIP_FLUXITY:
                cr.set_source_surface(generator_icon, 6, 6)
                cr.paint()
            elif self.media_file.container_data.container_type == appconsts.CONTAINER_CLIP_GMIC:
                cr.set_source_surface(gmic_icon, 6, 6)
                cr.paint()
            elif self.media_file.container_data.container_type == appconsts.CONTAINER_CLIP_MLT_XML:
                cr.set_source_surface(selection_icon, 6, 6)
                cr.paint()
        else:
            if self.media_file.type == appconsts.IMAGE:
                if hasattr(self.media_file, "titler_data") and self.media_file.titler_data != None:
                    cr.set_source_surface(title_icon, 6, 6)
                    cr.paint()
                else:
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

        if self.is_selected_test(self):
            if self.panel.mode == MediaPanel.MOVE_MODE:          
                cr.set_source_rgba(0.5, 0.5, 0.5, 0.5)
            else:
                r, g, b, a = self.selected_color                     
                cr.set_source_rgba(r, g, b, 0.3)     
                                    
            self.create_round_rect_path(cr, 0, 0, w - 5, h - 5, 6.0)
            cr.fill()
                
    def create_round_rect_path(self, cr, x, y, width, height, radius=4.0):
        degrees = math.pi / 180.0

        cr.new_sub_path()
        cr.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path()


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
        We get cairo context and allocation.
        """
        x, y, w, h = allocation

        # Draw separator
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.5,0.5,0.5,0.2)
        cr.move_to(8.5, 2.5)
        cr.line_to(w - 8.5, 2.5)
        cr.stroke()

# ---------------------------------------------- MISC WIDGETS
def get_monitor_view_select_launcher(callback):
    prefs = editorpersistance.prefs
    surface = guiutils.get_cairo_image("program_view_2")
    menu_launch = PressLaunchPopover(callback, surface, w=24, h=16)
    menu_launch.surface_y = 3
    
    menu_launch.widget.set_margin_top(2)
    return menu_launch

def get_trim_view_select_launcher(callback):
    prefs = editorpersistance.prefs
    surface = guiutils.get_cairo_image("trim_view")
    menu_launch = PressLaunchPopover(callback, surface, w=24, h=16)
    menu_launch.surface_y = 3

    menu_launch.widget.set_margin_top(2)
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

def get_profile_info_reduced_small_box(profile):
    text = get_profile_reduced_info_text(profile)
    label = Gtk.Label(label=text)

    if editorstate.screen_size_small_height() == True:
        font_desc = "sans bold 8"
    else:
        font_desc = "sans bold 9"
    label.modify_font(Pango.FontDescription(font_desc))
    label.set_sensitive(False)
        
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
    
    fps_str = utils.get_fps_str_with_two_decimals(str(profile.fps()))
    str_list.append(_("Fps: ") + fps_str)
    pix_asp = float(profile.sample_aspect_num()) / profile.sample_aspect_den()
    pa_str =  "%.2f" % pix_asp
    str_list.append(", " + _("Pixel Aspect: ") + pa_str)

    return ''.join(str_list)
    
def get_profile_reduced_info_text(profile):
    str_list = []
    fps_str = utils.get_fps_str_with_two_decimals(str(profile.fps()))
    str_list.append(_("Fps: ") + fps_str + ", ")
    str_list.append(str(profile.width()))
    str_list.append(" x ")
    str_list.append(str(profile.height()))
    str_list.append(", " + str(profile.display_aspect_num()))
    str_list.append(":")
    str_list.append(str(profile.display_aspect_den()))
    #str_list.append("\n")

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

def get_full_profile_info_text(profile):
    str_list = []
    str_list.append(_("Description: ") + profile.description())
    str_list.append("\n")
    str_list.append(_("Dimensions: ") + str(profile.display_aspect_num()) + ":" + str(profile.display_aspect_den()))
    str_list.append("\n")
    # round fractional frame rates to something easier to read
    fps = profile.fps()
    display_fps = str(round(fps))
    if 0 != (fps % 1):
        display_fps = str(round((float(fps)), 2))
    str_list.append(_("Frames per second: ") + display_fps)
    str_list.append("\n")
    str_list.append(_("Size: ") + str(profile.width()) + " x " + str(profile.height()))
    str_list.append("\n")
    pix_asp = float(profile.sample_aspect_num()) / profile.sample_aspect_den()
    pa_str =  "%.2f" % pix_asp
    str_list.append(_("Pixel aspect ratio: ") + pa_str)
    str_list.append("\n")
    if profile.progressive() == True:
        prog = _("Yes")
    else:
        prog = _("No")
    str_list.append(_("Progressive: ") + prog)
    str_list.append("\n")
    str_list.append(_("Color space: ") + "ITU-R " + str(profile.colorspace()))
    return ''.join(str_list)

def set_profile_info_values_text(profile, label, show_description):
    str_list = []

    # round fractional frame rates to something easier to read
    fps = profile.fps()
    display_fps = str(round(fps))
    if 0 != (fps % 1):
        display_fps = str(round((float(fps)), 2))

    if show_description:
        str_list.append(profile.description())
        str_list.append("\n")
    str_list.append(str(profile.display_aspect_num()))
    str_list.append(":")
    str_list.append(str(profile.display_aspect_den()))
    str_list.append("\n")
    str_list.append(display_fps)
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
        # Aug-2019 - SvdB -BB
        prefs = editorpersistance.prefs

        self.widget = cairoarea.CairoDrawableArea2( 140,
                                                    22,
                                                    self._draw)
        self.font_desc = Pango.FontDescription("Bitstream Vera Sans Mono Condensed " + str(15))
        
        # Draw consts
        x = 2
        y = 2
        width = 140
        height = 22
        aspect = 1.0
        corner_radius = height / 3.5
        radius = corner_radius / aspect
        degrees = M_PI / 180.0

        self._draw_consts = (x, y, width, height, aspect, corner_radius, radius, degrees)

        self.TEXT_X = 18
        self.TEXT_Y = 1

        self.widget.connect("button-press-event", self._button_press)
        self.widget.set_margin_top(1)

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo context and allocation.
        """
        x, y, w, h = allocation

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
        
        try:
            frame = PLAYER().tracktor_producer.frame()
            frame_str = utils.get_tc_zeros_overlay_fine_grained(frame)
        except:
            print("except")
            frame_str = "00:00:00:00"
            
        layout = PangoCairo.create_layout(cr)
        layout.set_text(frame_str, -1)
        layout.set_font_description(self.font_desc)

        cr.set_source_rgb(*TC_ZEROS_COLOR)
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
    def __init__(self, widget_width=94):
        self.widget = cairoarea.CairoDrawableArea2( widget_width,
                                                    20,
                                                    self._draw)
        self.font_desc = Pango.FontDescription("Bitstream Vera Sans Mono Condensed 9")

        # Draw consts
        x = 2
        y = 2
        width = widget_width - 4
        height = 16
        aspect = 1.0
        corner_radius = height / 3.5
        radius = corner_radius / aspect
        degrees = M_PI / 180.0

        self._draw_consts = (x, y, width, height, aspect, corner_radius, radius, degrees)

        self.FPS_NOT_SET = -99.0

        self._frame = 0
        self.use_internal_frame = False

        self.use_internal_fps = False # if False, fps value for calculating tc comes from utils.fps(),
                                       # if True, fps value from self.fps that will have to be set from user site
        self.display_tc = True # if this is False the frame number is displayed instead of timecode
        self.fps = self.FPS_NOT_SET # this will have to be set from user site

    def set_frame(self, frame):
        self._frame = frame # this is used in tools, editor window uses PLAYER frame
        self.widget.queue_draw()

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo context and allocation.
        """
        x, y, w, h = allocation

        # Draw round rect with gradient and stroke around for thin bezel
        self._round_rect_path(cr)
        cr.set_source_rgb(0.1, 0.1, 0.1)
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

        if self.display_tc == True:
            if self.use_internal_fps == False:
                frame_str = utils.get_tc_string(frame)
            else:
                if  self.fps != self.FPS_NOT_SET:
                    frame_str = utils.get_tc_string_with_fps(frame, self.fps)
                else:
                    frame_str = ""
        else:
            frame_str = str(self._frame).rjust(6)
    
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


class MonitorMarksTCInfo:
    def __init__(self):
        if editorstate.screen_size_small_height() == True:
            font_desc = "sans bold 8"
        else:
            font_desc = "sans bold 9"

        self.monitor_source = Gtk.Label()
        self.monitor_source.modify_font(Pango.FontDescription(font_desc))
        self.monitor_source.set_ellipsize(Pango.EllipsizeMode.END)
        #self.monitor_source.set_sensitive(False)
        
        self.monitor_tc = Gtk.Label()
        self.monitor_tc.modify_font(Pango.FontDescription(font_desc))

        self.marks_tc_display = MonitorInfoDisplay()

        self.widget = self.marks_tc_display.widget # Gtk.HBox()
        #self.widget.pack_start(self.marks_tc_display.widget, False, False, 0)

    def set_source_name(self, source_name):
        self.monitor_source.set_text(source_name)
        
    def set_source_tc(self, tc_str):
        self.monitor_tc.set_text(tc_str)
    
    def set_range_info(self, mark_in, mark_out):
        self.marks_tc_display.set_marks_range_info(mark_in, mark_out)
        self.marks_tc_display.widget.queue_draw()



class MonitorInfoDisplay:

    def __init__(self, widget_width=299):
        self.widget = cairoarea.CairoDrawableArea2( widget_width,
                                                    18,
                                                    self._draw)
        self.font_desc = Pango.FontDescription("sans bold 9")
        self.mark_in_img = guiutils.get_cairo_image("mark_in_tc", force=False) 
        self.mark_out_img = guiutils.get_cairo_image("mark_out_tc", force=False)
        self.marks_length_img = guiutils.get_cairo_image("marks_length_tc", force=False)

        self.in_str = ""
        self.out_str = ""
        self.len_str = ""

        self.in_zeros_overlay = ""
        self.out_zeros_overlay = ""
        self.len_zeros_overlay = ""

        self.mark_in_empty = True
        self.mark_out_empty = True
        self.len_empty = True
        
        # Draw consts
        x = 2
        y = 2
        width = widget_width - 4
        height = 16
        aspect = 1.0
        corner_radius = height / 3.5
        radius = corner_radius / aspect
        degrees = M_PI / 180.0

        self._draw_consts = (x, y, width, height, aspect, corner_radius, radius, degrees)

        self.FPS_NOT_SET = -99.0

        self._frame = 0
        self.use_internal_frame = False

        self.use_internal_fps = False # if False, fps value for calculating tc comes from utils.fps(),
                                       # if True, fps value from self.fps that will have to be set from user site
        self.display_tc = True # if this is False the frame number is displayed instead of timecode
        self.fps = self.FPS_NOT_SET # this will have to be set from user site

    def set_frame(self, frame):
        self._frame = frame # this is used in tools, editor window uses PLAYER frame
        self.widget.queue_draw()

    def set_marks_range_info(self, mark_in, mark_out):
        self.in_zeros_overlay = ""
        self.out_zeros_overlay = ""
        self.len_zeros_overlay = ""
        
        if mark_in != -1:
            mark_in_info = utils.get_tc_string(mark_in)
            self.in_zeros_overlay = utils.get_tc_zeros_overlay_fine_grained(mark_in)
            self.mark_in_empty = False
        else:
            mark_in_info = " - - : - - : - - : - -"
            self.mark_in_empty = True
        self.in_str = mark_in_info
        
        if mark_out != -1:
            mark_out_info = utils.get_tc_string(mark_out)
            self.out_zeros_overlay = utils.get_tc_zeros_overlay_fine_grained(mark_out)
            self.mark_out_empty = False
        else:
            mark_out_info =  " - - : - - : - - : - - "
            self.mark_out_empty = True
        self.out_str = mark_out_info

        range_len = mark_out - mark_in + 1 # +1, out incl.
        if mark_in != -1 and mark_out != -1:
            range_info = utils.get_tc_string(range_len)
            self.len_zeros_overlay = utils.get_tc_zeros_overlay_fine_grained(range_len)
            self.len_empty = False
        else:
            range_info =  " - - : - - : - - : - - "
            self.len_empty = True
        self.len_str = range_info

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo context and allocation.
        """
        x, y, w, h = allocation

        # Draw round rect with gradient and stroke around for thin bezel        
        cr.set_source_surface(self.mark_in_img, 12, 5)
        cr.paint()
        cr.set_source_surface(self.mark_out_img, 110, 5)
        cr.paint()
        cr.set_source_surface(self.marks_length_img, 205, 5)
        cr.paint()
        
        is_tc = True
        # Tc Texts
        self.draw_tc(cr, self.in_str, 21, 2, not self.mark_in_empty)
        self.draw_tc(cr, self.in_zeros_overlay, 21, 2, False)
        self.draw_tc(cr, self.out_str, 118, 2, not self.mark_out_empty)
        self.draw_tc(cr, self.out_zeros_overlay, 118, 2, False)
        self.draw_tc(cr, self.len_str, 218, 2, not self.len_empty)
        self.draw_tc(cr, self.len_zeros_overlay, 218, 2, False)

    def draw_tc(self, cr, tc_text, x, y, is_tc):
        layout = PangoCairo.create_layout(cr)
        layout.set_text(tc_text) #+ "     " + self.out_str + "      " + self.len_str, -1)
        layout.set_font_description(self.font_desc)
        if is_tc == True:
            cr.set_source_rgb(0.7, 0.7, 0.7)
        else:
            cr.set_source_rgb(0.4, 0.4, 0.4)
        cr.move_to(x, y)
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
    def __init__(self, comp_mode_launch, tline_render_mode_launcher):
        self.widget = Gtk.HBox()
        self.comp_mode_launch = comp_mode_launch
        self.tline_render_mode_launcher = tline_render_mode_launcher
        self.update_gui()

    def update_gui(self):
        for child in self.widget.get_children():
            self.widget.remove(child)
        
        self.widget.pack_start(Gtk.Label(), True, True, 0)

        if PROJECT().proxy_data.proxy_mode == appconsts.USE_PROXY_MEDIA:
            proxy_img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "project_proxy.png")
            proxy_img.set_tooltip_text(_("Sequence uses proxy media if available."))
            self.widget.pack_start(proxy_img, False, False, 0)
            self.widget.pack_start(guiutils.pad_label(16,4), False, False, 0)
        
        #self.widget.pack_start(self.tline_render_mode_launcher.widget, False, False, 0)
        #self.widget.pack_start(guiutils.pad_label(8,4), False, False, 0)
        
        self.widget.pack_start(self.comp_mode_launch.widget, False, False, 0)
        self.widget.pack_start(guiutils.pad_label(4,4), False, False, 0)
            
        self.widget.show_all()
        self.widget.queue_draw()


class TracksNumbersSelect:
    def __init__(self, v_tracks, a_tracks):
        
        self.MAX_TRACKS = appconsts.MAX_TRACKS
        
        self.widget = Gtk.HBox()
        
        self.video_label = Gtk.Label(label=_("Video:"))
        self.video_tracks = Gtk.SpinButton.new_with_range(1, self.MAX_TRACKS, 1)
        self.video_tracks.set_value(v_tracks)
        self.video_tracks.connect("value-changed", self.video_tracks_changed)
        
        self.audio_label = Gtk.Label(label=_("Audio:"))
        self.audio_tracks = Gtk.SpinButton.new_with_range(0, self.MAX_TRACKS-1, 1)
        self.audio_tracks.set_value(a_tracks)
        self.audio_tracks.connect("value-changed", self.audio_tracks_changed)
        
        self.label = Gtk.Label(label=_("Number of Tracks:"))
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

        self.frames_label = Gtk.Label(label=_("Frames:"))
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

    return get_scroll_widget(size, license_text)

def get_scroll_widget(size, text):
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




class PressLaunch:
    def __init__(self, callback, surface, w=22, h=22, show_mouse_prelight=True):
        self.widget = cairoarea.CairoDrawableArea2( w,
                                                    h,
                                                    self._draw)
        self.widget.press_func = self._press_event
        self.callback = callback
        self.surface = surface
        self.surface_x = 6
        self.surface_y = 6
        
        self.draw_triangle = False # set True at creation site if needed

        self.prelight_on = False 
        self.ignore_next_leave = False
        
        if show_mouse_prelight:
            self._prepare_mouse_prelight()
        else:
            self.surface_prelight = None

    def connect_launched_menu(self, launch_menu):
        # We need to leave prelight icon when menu closed
        launch_menu.connect("hide", lambda w : self.leave_notify_listener(None))
    
    def _prepare_mouse_prelight(self):
        self.surface_prelight = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.surface.get_width(), self.surface.get_height())
        cr = cairo.Context(self.surface_prelight)
        cr.set_source_surface(self.surface, 0, 0)
        cr.rectangle(0,0,self.surface.get_width(), self.surface.get_height())
        cr.fill()
        
        cr.set_operator(cairo.Operator.ATOP)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.5)
        cr.rectangle(0,0,self.surface.get_width(), self.surface.get_height())
        cr.fill()
        
        self.widget.leave_notify_func = self.leave_notify_listener
        self.widget.enter_notify_func = self.enter_notify_listener

    def leave_notify_listener(self, event):
        if self.ignore_next_leave == True:
            self.ignore_next_leave = False
            return
            
        self.prelight_on = False
        self.widget.queue_draw()

    def shut_prelight(self):
        self.prelight_on = False
        self.widget.queue_draw()

    def enter_notify_listener(self, event):
        self.prelight_on = True 
        self.widget.queue_draw()

    def _draw(self, event, cr, allocation):
        if self.draw_triangle == False:
            if self.prelight_on == False or self.surface_prelight == None:
                cr.set_source_surface(self.surface, self.surface_x, self.surface_y)
            else:
                cr.set_source_surface(self.surface_prelight, self.surface_x, self.surface_y)
            cr.paint()
        else:
            self._draw_triangle(event, cr, allocation)  

    def _draw_triangle(self, event, cr, allocation):      
        cr.move_to(7, 13)
        cr.line_to(12, 18)
        cr.line_to(17, 13)
        cr.close_path()
        cr.set_source_rgb(0.66, 0.66, 0.66)
        cr.fill()
        
    def _press_event(self, event):
        self.ignore_next_leave = True
        self.prelight_on = True 
        self.callback(self.widget, event)

class PressLaunchPopover(PressLaunch):
    def __init__(self, callback, surface, w=22, h=22):

        # Popovers need access to launcher object from callback.

        PressLaunch.__init__(self, callback, surface, w, h)

    def _press_event(self, event):
        self.ignore_next_leave = True
        self.prelight_on = True 
        self.callback(self, self.widget, event)
        

class ImageMenuLaunch(PressLaunch):
    def __init__(self, callback, surface_list, w=22, h=22):
        self.surface_list = surface_list
        PressLaunch.__init__(self, callback, surface_list[0], w, h)

    def _prepare_mouse_prelight(self):
        self.surface_prelight_list = []
        for icon in self.surface_list:
            surface_prelight = cairo.ImageSurface(cairo.FORMAT_ARGB32, icon.get_width(), icon.get_height())
            cr = cairo.Context(surface_prelight)
            cr.set_source_surface(icon, 0, 0)
            cr.rectangle(0, 0, icon.get_width(), icon.get_height())
            cr.fill()
            
            cr.set_operator(cairo.Operator.ATOP)
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.5)
            cr.rectangle(0, 0, icon.get_width(), icon.get_height())
            cr.fill()
            
            self.surface_prelight_list.append(surface_prelight)

        self.widget.leave_notify_func = self.leave_notify_listener
        self.widget.enter_notify_func = self.enter_notify_listener
        
    def set_pixbuf(self, surface_index):
        self.surface = self.surface_list[surface_index]
        self.surface_prelight = self.surface_prelight_list[surface_index]
            
        self.widget.queue_draw()


class ImageMenuLaunchPopover(PressLaunchPopover):
    def __init__(self, callback, surface_list, w=22, h=22):
        self.surface_list = surface_list
        PressLaunchPopover.__init__(self, callback, surface_list[0], w, h)

    def _prepare_mouse_prelight(self):
        self.surface_prelight_list = []
        for icon in self.surface_list:
            surface_prelight = cairo.ImageSurface(cairo.FORMAT_ARGB32, icon.get_width(), icon.get_height())
            cr = cairo.Context(surface_prelight)
            cr.set_source_surface(icon, 0, 0)
            cr.rectangle(0, 0, icon.get_width(), icon.get_height())
            cr.fill()
            
            cr.set_operator(cairo.Operator.ATOP)
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.5)
            cr.rectangle(0, 0, icon.get_width(), icon.get_height())
            cr.fill()
            
            self.surface_prelight_list.append(surface_prelight)

        self.widget.leave_notify_func = self.leave_notify_listener
        self.widget.enter_notify_func = self.enter_notify_listener
        
    def set_pixbuf(self, surface_index):
        self.surface = self.surface_list[surface_index]
        self.surface_prelight = self.surface_prelight_list[surface_index]
            
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
                                            appconsts.TLINE_TOOL_KFTOOL: 9,
                                            appconsts.TLINE_TOOL_MULTI_TRIM: 10
                                     }

    def set_tool_pixbuf(self, tool_id):
        surface_index = self.TOOL_ID_TO_SURFACE_INDEX[tool_id]
        self.set_pixbuf(surface_index)
        
    def _draw(self, event, cr, allocation):
        PressLaunch._draw(self, event, cr, allocation)

        x_pos = [27,32,37]
        y_pos = [13,18,13]
        cr.move_to(x_pos[0], y_pos[0])
        cr.line_to(x_pos[1], y_pos[1])
        cr.line_to(x_pos[2], y_pos[2])
        cr.close_path()
        cr.set_source_rgb(0.66, 0.66, 0.66)
        cr.fill()

    
class HamburgerPressLaunch:
    def __init__(self, callback, surfaces=None, width=-1, data=None):
        # Aug-2019 - SvdB - BB
        prefs = editorpersistance.prefs
        size_adj = 1
        y_adj = 0

        
        if width == -1:
            x_size = 18
        else:
            x_size = width

        self.x_size_pref = x_size 
        self.y_size_pref = 18
        self.widget = cairoarea.CairoDrawableArea2( self.x_size_pref,
                                                    self.y_size_pref,
                                                    self._draw)
        self.widget.press_func = self._press_event
        self.sensitive = True
        self.callback = callback
        self.data = data
        self.do_popover_callback = False # These need more data.

        if surfaces == None:
            self.surface_active = guiutils.get_cairo_image("hamburger")
            self.surface_not_active = guiutils.get_cairo_image("hamburger_not_active")
        else:
            self.surface_active = surfaces[0]
            self.surface_not_active = surfaces[1]

        self.surface_x  = 0
        self.surface_y  = y_adj

        self.prelight_on = False 
        self.ignore_next_leave = False
        self._prepare_mouse_prelight()

    def connect_launched_menu(self, launch_menu):
        # We need to leave prelight icon when menu closed
        launch_menu.connect("hide", lambda w : self.leave_notify_listener(None))
    
    def _prepare_mouse_prelight(self):
        self.surface_prelight = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.surface_active.get_width(), self.surface_active.get_height())
        cr = cairo.Context(self.surface_prelight)
        cr.set_source_surface(self.surface_active, 0, 0)
        cr.rectangle(0, 0, self.surface_active.get_width(), self.surface_active.get_height())
        cr.fill()
        
        cr.set_operator(cairo.Operator.ATOP)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.5)
        cr.rectangle(0,0,self.surface_active.get_width(), self.surface_active.get_height())
        cr.fill()
        
        self.widget.leave_notify_func = self.leave_notify_listener
        self.widget.enter_notify_func = self.enter_notify_listener
        
    def set_sensitive(self, sensitive):
        self.sensitive = sensitive
        self.widget.queue_draw()

    def _draw(self, event, cr, allocation):
        if self.sensitive == True:
            surface = self.surface_active
            if self.prelight_on == True:
                surface = self.surface_prelight
        else:
            surface = self.surface_not_active
            
        cr.set_source_surface(surface, self.surface_x, self.surface_y)
        cr.paint()

    def _press_event(self, event):
        if self.sensitive == True:
            self.ignore_next_leave = True
            self.prelight_on = True
            if self.do_popover_callback == True:
                self.callback(self, self.widget, event, self.data)
            else:
                if self.data == None:
                    self.callback(self.widget, event)
                else:
                    self.callback(self.widget, event, self.data)

    def leave_notify_listener(self, event):
        if self.ignore_next_leave == True:
            self.ignore_next_leave = False
            return
            
        self.prelight_on = False
        self.widget.queue_draw()
    
    def enter_notify_listener(self, event):
        self.prelight_on = True 
        self.widget.queue_draw()
        

class MonitorSwitch:
    def __init__(self, callback):
        self.WIDTH = 94
        self.HEIGHT = 10
        
        self.press_fix = 6 # we don't get want to divide press exactly half, timeline gets more
        
        # Aug-2019 - SvdB - BB - Set the appropriate values based on button size. Use guiutils functions
        prefs = editorpersistance.prefs

        self.widget = cairoarea.CairoDrawableArea2( self.WIDTH ,
                                                    self.HEIGHT,
                                                    self._draw)
        self.widget.set_tooltip_text(_("Display Timeline / Clip on Monitor"))
        self.widget.press_func = self._press_event

        self.tline_surface = guiutils.get_cairo_image("timeline_button")
        self.tline_active_surface = guiutils.get_cairo_image("timeline_button_active")
        self.clip_surface = guiutils.get_cairo_image("clip_button")
        self.clip_active_surface = guiutils.get_cairo_image("clip_button_active")
        
        self.callback = callback

    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation

        if editorstate.timeline_visible():
            tline_draw_surface = self.tline_active_surface 
            clip_draw_surface = self.clip_surface
        else:
            tline_draw_surface = self.tline_surface 
            clip_draw_surface = self.clip_active_surface
            
        def_off = 14
        y_off_tline = 3
        y_off_clip = 4
        mid_gap = 10
        y_off_tline = -1
        y_off_clip = 0

        cr.set_source_rgb(0.063, 0.341, 0.659)
        self.create_round_rect_path(cr, 0, 0, 84, 20, 10.0)
        cr.fill()

        cr.set_source_surface(tline_draw_surface, def_off, y_off_tline)
        cr.paint()

        # Aug-2019 - SvdB - BB - Calculate offset for displaying the next button
        base_off = tline_draw_surface.get_width()

        cr.set_source_surface(clip_draw_surface, def_off + base_off + mid_gap, y_off_clip)
        cr.paint()

    def create_round_rect_path(self, cr, x, y, width, height, radius=4.0):
        degrees = M_PI / 180.0
        #cr.new_sub_path()
        cr.arc(x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc(x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc(x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc(x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path()
        
    def _press_event(self, event):
        if event.x < (self.WIDTH / 2 + self.press_fix) and editorstate.timeline_visible() == False:
            self.callback(appconsts.MONITOR_TLINE_BUTTON_PRESSED)
        elif editorstate.timeline_visible() == True:
            self.callback(appconsts.MONITOR_CLIP_BUTTON_PRESSED)

    def toggle(self):
        """
        Toggle the monitor between the media clip and the timeline.

        """

        # if there is no media clip, there is nothing to toggle
        if editorstate.MONITOR_MEDIA_FILE() == None:
            return

        # if a media clip is displayed, toggle to the timeline, or vice versa
        if editorstate.timeline_visible() == False:
            self.callback(appconsts.MONITOR_TLINE_BUTTON_PRESSED)
        else:
            self.callback(appconsts.MONITOR_CLIP_BUTTON_PRESSED)


class MonitorClipType:
    def __init__(self):
        self.WIDTH = 47
        self.HEIGHT = 12
        
        self.widget = cairoarea.CairoDrawableArea2( self.WIDTH,
                                                    self.HEIGHT,
                                                    self._draw)
        self.widget.set_tooltip_text(_("Clip Media Type"))

        self.image_surface = guiutils.get_cairo_image("graphics_indicator")
        self.icons_data = {}
        self.icons_data[appconsts.IMAGE] = (guiutils.get_cairo_image("graphics_indicator"), 24, 4)
        self.icons_data[appconsts.IMAGE_SEQUENCE] = (guiutils.get_cairo_image("imgseq_indicator"), 24, 4)
        self.icons_data[appconsts.VIDEO] = (guiutils.get_cairo_image("show_video_files"), 24, 4)
        self.icons_data[appconsts.AUDIO] = (guiutils.get_cairo_image("audio_indicator"), 24, 4)
 
    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation

        if not editorstate.timeline_visible():
            image_surface, x, y = self.icons_data[editorstate.MONITOR_MEDIA_FILE().type]
            cr.set_source_surface(image_surface, x, y)
            cr.paint()




# ------------------------------------------------------- combo boxes with categories
def get_profiles_combo():
    return CategoriesModelComboBox(mltprofiles._categorized_profiles)

class CategoriesModelComboBox:
    
    def __init__(self, categories_list):
        self.categories_list = categories_list # categories_list is list of form [("category_name", [category_items]), ...]
                                               # with category_items list of form ["item_name", ...]

        self.model = Gtk.TreeStore.new([str])
        
        for i in range(0, len(categories_list)):
            name, items = categories_list[i]
            self.model.append(None, [name])
            for item_name in items:
                category_iter = self.model.get_iter_from_string(str(i))
                self.model.append(category_iter, [item_name])

        self.widget = Gtk.ComboBox.new_with_model(self.model)
        renderer_text = Gtk.CellRendererText()
        self.widget.pack_start(renderer_text, True)
        self.widget.add_attribute(renderer_text, "text", 0)

    def set_changed_callback(self, callback):
        self.widget.connect("changed", callback)

    def set_selected(self, active_item_name):
        for i in range(0, len(self.categories_list)):
            name, items = self.categories_list[i]
            for j in range(0, len(items)):
                if items[j] == active_item_name:
                    iter = self.model.get_iter_from_string(str(i) + ":" + str(j))
                    self.widget.set_active_iter(iter)

    def get_selected(self):        
        indices = self.model.get_path(self.widget.get_active_iter()).get_indices()
        name, items = self.categories_list[indices[0]]
        return items[indices[1]]

    def refill(self, categories_list):
        self.categories_list = categories_list
        self.model.clear()
    
        for i in range(0, len(categories_list)):
            name, items = categories_list[i]
            self.model.append(None, [name])
            for item_name in items:
                category_iter = self.model.get_iter_from_string(str(i))
                self.model.append(category_iter, [item_name])
                
def get_encodings_combo():
    return CategoriesModelComboBoxWithData(renderconsumer.categorized_encoding_options)


class CategoriesModelComboBoxWithData:
    
    def __init__(self, categories_list):
        self.categories_list = categories_list # categories_list is list of form [("category_name", [category_items]), ...]
                                               # with category_items list of form [("item_name", data_object), ...]
        self.model = Gtk.TreeStore.new([str])
        
        for i in range(0, len(categories_list)):
            name, items = categories_list[i]
            self.model.append(None, [name])
            for item in items:
                item_name, item_data = item
                category_iter = self.model.get_iter_from_string(str(i))
                self.model.append(category_iter, [item_name])

        self.widget = Gtk.ComboBox.new_with_model(self.model)
        renderer_text = Gtk.CellRendererText()
        self.widget.pack_start(renderer_text, True)
        self.widget.add_attribute(renderer_text, "text", 0)

    def set_changed_callback(self, callback):
        self.widget.connect("changed", callback)
        
    def set_selected(self, active_item_name):
        for i in range(0, len(self.categories_list)):
            name, items = self.categories_list[i]
            for j in range(0, len(items)):
                item_name, item_data = items[j]
                if item_name == active_item_name:
                    iter = self.model.get_iter_from_string(str(i) + ":" + str(j))
                    self.widget.set_active_iter(iter)
                    
    def get_selected(self):        
        indices = self.model.get_path(self.widget.get_active_iter()).get_indices()
        name, items = self.categories_list[indices[0]]
        return items[indices[1]]

    def get_selected_name(self):        
        indices = self.model.get_path(self.widget.get_active_iter()).get_indices()
        name, items = self.categories_list[indices[0]]
        name, item = items[indices[1]]
        return name

    def refill(self, categories_list):
        self.categories_list = categories_list
        self.model.clear()

        for i in range(0, len(categories_list)):
            name, items = categories_list[i]
            self.model.append(None, [name])
            for item in items:
                item_name, item_data = item
                category_iter = self.model.get_iter_from_string(str(i))
                self.model.append(category_iter, [item_name])


class EditMultiStack:
    def __init__(self):
        self.widget = Gtk.Stack()
        self.panels = {}

    def add_named(self, panel, name):
        self.panels[name] = panel
        self.widget.add_named(panel, name)

    def set_visible_child_name(self, name):
        self.widget.set_visible_child_name(name)
        self.panels[name].show_all()

    def get_visible_child_name(self):
        return self.widget.get_visible_child_name()


def create_jobs_list_view():
    global _jobs_list_view
    _jobs_list_view = JobsQueueView()
    return _jobs_list_view

class JobsQueueView(Gtk.VBox):

    def __init__(self):
        GObject.GObject.__init__(self)
        
        self.storemodel = Gtk.ListStore(str, str, str)
        
        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # View
        self.treeview = Gtk.TreeView(model=self.storemodel)
        self.treeview.set_headers_visible(True)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.text_rend_2 = Gtk.CellRendererText()
        self.text_rend_2.set_property("yalign", 0.0)
        self.text_rend_2.set_property("ellipsize", Pango.EllipsizeMode.END)
        
        self.text_rend_3 = Gtk.CellRendererText()
        self.text_rend_3.set_property("yalign", 0.0)
        
        self.text_rend_4 = Gtk.CellRendererText()
        self.text_rend_4.set_property("yalign", 0.0)

        # Column views
        self.text_col_2 = Gtk.TreeViewColumn(_("Job Info"))
        self.text_col_3 = Gtk.TreeViewColumn(_("Render Time"))
        self.text_col_4 = Gtk.TreeViewColumn(_("Progress"))

        self.text_col_2.set_expand(True)
        self.text_col_2.pack_start(self.text_rend_2, True)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 0)
        self.text_col_2.set_min_width(90)

        self.text_col_3.set_expand(False)
        self.text_col_3.pack_start(self.text_rend_3, True)
        self.text_col_3.add_attribute(self.text_rend_3, "text", 1)

        self.text_col_4.set_expand(False)
        self.text_col_4.pack_start(self.text_rend_4, True)
        self.text_col_4.add_attribute(self.text_rend_4, "text", 2)

        # Add column views to view
        self.treeview.append_column(self.text_col_2)
        self.treeview.append_column(self.text_col_3)
        self.treeview.append_column(self.text_col_4)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        frame = Gtk.Frame()
        frame.add(self.scroll)
        self.pack_start(frame, True, True, 0)
        self.scroll.show_all()
        frame.show_all()
        self.show_all()

    def get_selected_row_index(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return int(rows[0].to_string ())
        
    def fill_data_model(self, jobs_list):
        self.storemodel.clear()        
        
        for job in jobs_list:
            row_data = [job.text,
                        job.get_elapsed_str(),
                        job.get_progress_str()]
            self.storemodel.append(row_data)
        
        self.scroll.queue_draw()

    def update_row(self, row, jobs_list):
        tree_path = Gtk.TreePath.new_from_string(str(row))
        store_iter = self.storemodel.get_iter(tree_path)

        self.storemodel.set_value(store_iter, 0, jobs_list[row].text)
        self.storemodel.set_value(store_iter, 1, jobs_list[row].get_elapsed_str())
        self.storemodel.set_value(store_iter, 2, jobs_list[row].get_progress_str())

        self.scroll.queue_draw()
    