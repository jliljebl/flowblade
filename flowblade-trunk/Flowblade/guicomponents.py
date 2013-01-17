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
import gtk
import math
import pango
import pangocairo

import appconsts
from cairoarea import CairoDrawableArea
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

SEQUENCE_IMG_PATH = "/res/img/sequence.png" 
SEPARATOR_HEIGHT = 5
SEPARATOR_WIDTH = 250

MONITOR_COMBO_WIDTH = 47
MONITOR_COMBO_HEIGHT = 16

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

# ------------------------------------------------- item lists 
class ImageTextTextListView(gtk.VBox):
    """
    GUI component displaying list with columns: img, text, text
    Middle column expands.
    """

    def __init__(self):
        gtk.VBox.__init__(self)

        style = self.get_style()
        bg_col = style.bg[gtk.STATE_NORMAL]
        
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

class ImageTextImageListView(gtk.VBox):
    """
    GUI component displaying list with columns: img, text, img
    Middle column expands.
    """

    def __init__(self):
        gtk.VBox.__init__(self)

        style = self.get_style()
        bg_col = style.bg[gtk.STATE_NORMAL]
        
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
        self.icon_path = respaths.ROOT_PATH + SEQUENCE_IMG_PATH
        
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
 
        # No border for scroll container 
        #self.scroll.set_shadow_type(gtk.SHADOW_NONE)

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

        icon_theme = gtk.icon_theme_get_default()
        for bin in PROJECT().bins:
            try:
                #pixbuf = icon_theme.load_icon(gtk.STOCK_DIRECTORY, 24, 0)
                pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "bin_3.png")
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

        self.on_icon = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "filter_on.png")       
        self.off_icon = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "filter_off.png")
    
    def fill_data_model(self, filter_group, filter_objects=None):

        self.storemodel.clear()
        for i in range(0, len(filter_group)):
            f = filter_group[i]
            on_icon = None
            if not(filter_objects == None):
                if filter_objects[i].active == False:
                    on_icon = self.off_icon
                else:
                    on_icon = self.on_icon
            row_data = [f.get_icon(),
                        translations.get_filter_name(f.name), 
                        on_icon]
            self.storemodel.append(row_data)
            self.scroll.queue_draw()


class FilterSwitchListView(gtk.VBox):
    """
    GUI component displaying list of filters applied to a clip.
    """

    def __init__(self, selection_cb, toggle_cb):
        gtk.VBox.__init__(self)

        style = self.get_style()
        bg_col = style.bg[gtk.STATE_NORMAL]
        
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
        

class ProfileListView(gtk.VBox):
    """
    GUI component displaying list with columns: img, text, text
    Middle column expands.
    """
    def __init__(self, column_name=None):
        gtk.VBox.__init__(self)

        style = self.get_style()
        bg_col = style.bg[gtk.STATE_NORMAL]
        
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
        self.text_col_1.set_min_width(100)
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

    def fill_data_model(self, profiles):
        self.storemodel.clear()
        default_profile = mltprofiles.get_default_profile()
        for profile in profiles:
            row_data = [profile[0]]
            if default_profile == profile[1]:
                row_data = [row_data[0] + " <" + _("default") + ">"]
            self.storemodel.append(row_data)
        
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
        
        self.set_size_request(250, 56)

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

        self.name_label = gtk.Label()
        self.name_value = gtk.Label()
        self.name_value.set_ellipsize(pango.ELLIPSIZE_END)

        self.source_track = gtk.Label()
        self.source_track_value = gtk.Label()

        self.destination_track = gtk.Label()
        self.destination_track_value = gtk.Label()

        self.position = gtk.Label()
        self.position_value = gtk.Label()

        self.length = gtk.Label()
        self.length_value = gtk.Label()
        
        info_row_1 = gtk.HBox()
        info_row_1.pack_start(self.name_label, False, True, 0)
        info_row_1.pack_start(self.name_value, True, True, 0)

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
        filler1 = gtk.Label()
        filler1.set_size_request(5, PAD_HEIGHT)
        filler2 = gtk.Label()
        filler2.set_size_request(5, PAD_HEIGHT)
        filler3 = gtk.Label()
        filler3.set_size_request(5, PAD_HEIGHT)
        filler4 = gtk.Label()
        filler4.set_size_request(5, PAD_HEIGHT)

        self.pack_start(info_row_1, False, False, 0)
        self.pack_start(filler1, False, False, 0)        
        self.pack_start(info_row_2, False, False, 0)
        self.pack_start(filler2, False, False, 0) 
        self.pack_start(info_row_3, False, False, 0)
        self.pack_start(filler3, False, False, 0) 
        self.pack_start(info_row_4, False, False, 0)
        self.pack_start(filler4, False, False, 0) 
        self.pack_start(info_row_5, False, False, 0)
        
        self.set_no_compositor_info()
        self.set_enabled(False)
        self.set_size_request(250, 120)

    def display_compositor_info(self, compositor):
        if compositor.compositor_index < len(mlttransitions.compositors):
            comp_type = _("Compositor")
        else:
            comp_type = _("Blend")
        self.name_value.set_text(comp_type)
                
        src_track = utils.get_track_name(current_sequence().tracks[compositor.transition.b_track],current_sequence())
        self.source_track_value.set_text(src_track)
        
        dest_track = utils.get_track_name(current_sequence().tracks[compositor.transition.a_track], current_sequence())
        self.destination_track_value.set_text(dest_track)
        
        pos = utils.get_tc_string(compositor.clip_in)
        self.position_value.set_text(pos)
        
        length = utils.get_tc_string(compositor.clip_out - compositor.clip_in)
        self.length_value.set_text(length)

    def set_no_compositor_info(self):
        self.name_label.set_text(_("<b>Type:</b>"))
        self.name_value.set_text("")
        self.name_value.set_ellipsize(pango.ELLIPSIZE_END)

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
        self.name_label.set_use_markup(True)
        self.source_track.set_use_markup(True)
        self.destination_track.set_use_markup(True)
        self.position.set_use_markup(True)
        self.length.set_use_markup(True)

    def set_enabled(self, value):
        self.name_label.set_sensitive(value)
        self.source_track.set_sensitive(value)
        self.destination_track.set_sensitive(value)
        self.position.set_sensitive(value)
        self.length.set_sensitive(value)

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
def get_monitor_view_select_combo():
    combo_list = gtk.ListStore(gtk.gdk.Pixbuf)
    combo_list.append([gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "program_view_2.png")])
    combo_list.append([gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "vectorscope.png")])
    combo_list.append([gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "rgbparade.png")])

    px = gtk.CellRendererPixbuf()
    combobox = gtk.ComboBox(combo_list)
    combobox.pack_start(px, True)
    combobox.add_attribute(px, "pixbuf", 0)
    combobox.set_active(0)
    combobox.set_size_request(MONITOR_COMBO_WIDTH, MONITOR_COMBO_HEIGHT)
    return combobox

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
       clip_menu.add(_get_menu_item(_("Display Waveform"), callback,\
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

    clip_menu.add(_get_menu_item(_("Clip Info"), callback,\
                  (clip, track, "clip_info", event.x)))
    clip_menu.popup(None, None, None, event.button, event.time)

def display_blank_clip_popup_menu(event, clip, track, callback):
    clip_menu = gtk.Menu()
    clip_menu.add(_get_menu_item(_("Strech Prev Clip to Cover"), callback, (clip, track, "cover_with_prev", event.x)))
    clip_menu.add(_get_menu_item(_("Strech Next Clip to Cover"), callback, (clip, track, "cover_with_next", event.x)))
    _add_separetor(clip_menu)
    clip_menu.add(_get_menu_item(_("Consolidate"), callback, (clip, track, "comsolidate_blanks", event.x)))
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
       clip_menu.add(_get_menu_item(_("Display Waveform"), callback,\
                  (clip, track, "display_waveform", event.x), True))
    else:
       clip_menu.add(_get_menu_item(_("Clear Waveform"), callback,\
          (clip, track, "clear_waveform", event.x), True))
    
    _add_separetor(clip_menu)
    
    clip_menu.add(_get_mute_menu_item(event, clip, track, callback))
    
    _add_separetor(clip_menu)
    
    clip_menu.add(_get_audio_filters_add_menu_item(event, clip, track, callback))

    _add_separetor(clip_menu)

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
    menu_item = gtk.MenuItem(_("Add Audio Filter"))
    sub_menu = gtk.Menu()
    menu_item.set_submenu(sub_menu)
    
    filters_array = mltfilters.get_audio_filters_group()
    for filter_info in filters_array:
        filter_item = gtk.MenuItem(translations.get_filter_name(filter_info.name))
        sub_menu.append(filter_item)
        filter_item.connect("activate", callback, (clip, track, "add_filter", (event.x, filter_info)))
        filter_item.show()

    menu_item.show()
    return menu_item
    
def _get_compositors_add_menu_item(event, clip, track, callback, sensitive):
    menu_item = gtk.MenuItem(_("Add Compositor"))
    sub_menu = gtk.Menu()
    menu_item.set_submenu(sub_menu)
    
    for i in range(0, len(mlttransitions.compositors)):
        compositor = mlttransitions.compositors[i]
        name, creator_func = compositor
        compositor_item = gtk.MenuItem(name)
        sub_menu.append(compositor_item)
        compositor_item.connect("activate", callback, (clip, track, "add_compositor", (event.x, i)))
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
        name, id_str = blend
        blender_item = gtk.MenuItem(name)
        sub_menu.append(blender_item)
        blender_item.connect("activate", callback, (clip, track, "add_blender", (event.x, i)))
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
    item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_NOTHING))
    _set_non_sensite_if_state_matches(track, item, appconsts.TRACK_MUTE_NOTHING)
    if track.type == appconsts.AUDIO:
        _set_non_sensite_if_state_matches(track, item, appconsts.TRACK_MUTE_VIDEO)
    item.show()
    
    if track.type == appconsts.VIDEO:
        item = gtk.MenuItem(_("Mute Video"))
        sub_menu.append(item)
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_VIDEO))
        _set_non_sensite_if_state_matches(track, item, appconsts.TRACK_MUTE_VIDEO)
        item.show()

    item = gtk.MenuItem(_("Mute Audio"))
    sub_menu.append(item)
    item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_AUDIO))
    _set_non_sensite_if_state_matches(track, item, appconsts.TRACK_MUTE_AUDIO)
    item.show()

    if track.type == appconsts.VIDEO:
        item = gtk.MenuItem(_("Mute All"))
        sub_menu.append(item)
        item.connect("activate", callback, (track, "mute_track", appconsts.TRACK_MUTE_ALL))
        _set_non_sensite_if_state_matches(track, item, appconsts.TRACK_MUTE_ALL)
        item.show()

    
    menu_item.show()
    return menu_item

def _set_non_sensite_if_state_matches(mutable, item, state):
    if mutable.mute_state == state:
        item.set_sensitive(False)

def diplay_media_file_popup_menu(media_file, callback, event):
    media_file_menu = gtk.Menu()
    # "Open in Clip Monitor" is sent as event id, same for all below
    # See useraction._media_file_menu_item_selected(...)
    media_file_menu.add(_get_menu_item(_("Open in Clip Monitor"), callback,("Open in Clip Monitor", media_file, event))) 
    media_file_menu.add(_get_menu_item(_("File Properties"), callback, ("File Properties", media_file, event)))
    _add_separetor(media_file_menu)
    media_file_menu.add(_get_menu_item(_("Render Slow/Fast Motion File"), callback, ("Render Slow/Fast Motion File", media_file, event)))
    _add_separetor(media_file_menu)
    media_file_menu.add(_get_menu_item(_("Delete"), callback, ("Delete", media_file, event)))
    media_file_menu.popup(None, None, None, event.button, event.time)

def display_filter_stack_popup_menu(row, treeview, callback, event):
    filter_stack_menu = gtk.Menu()        
    filter_stack_menu.add(_get_menu_item(_("Toggle Active"), callback, ("toggle", row, treeview)))
    filter_stack_menu.add(_get_menu_item(_("Reset Values"), callback, ("reset", row, treeview)))
    filter_stack_menu.popup(None, None, None, event.button, event.time)
    
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

def set_profile_info_labels_text(label, show_description):
    # Labels text
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
    # Values text
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
                                        20,
                                        self._draw)
        self.font_desc = pango.FontDescription("Bitstream Vera Sans Mono Condensed 15")
        
        #Draw consts
        x = 2
        y = 2
        width = 166
        height = 30
        aspect = 1.0
        corner_radius = height / 3.5
        radius = corner_radius / aspect
        degrees = M_PI / 180.0
        
        self._draw_consts = (x, y, width, height, aspect, corner_radius, radius, degrees)
    
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
        frame = PLAYER().tracktor_producer.frame()
        frame_str = utils.get_tc_string(frame)

        # Text
        pango_context = pangocairo.CairoContext(cr)
        layout = pango_context.create_layout()
        layout.set_text(frame_str)
        layout.set_font_description(self.font_desc)

        pango_context.set_source_rgb(0.0, 0.0, 0)

        pango_context.set_source_rgb(0.7, 0.7, 0.7)
        pango_context.move_to(18, 5)
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
    menu.popup(None, None, None, event.button, event.time)

def get_all_tracks_popup_menu(event, callback):
    menu = gtk.Menu()
    menu.add(_get_menu_item(_("Maximize tracks Height"), callback, "max" ))
    menu.add(_get_menu_item(_("Minimize tracks Height"), callback, "min" ))
    menu.popup(None, None, None, event.button, event.time)


class PressLaunch:
    def __init__(self, callback, pixbuf):
        self.widget = CairoDrawableArea(22, 
                                        22, 
                                        self._draw)
        self.widget.press_func = self._press_event
        
        self.callback = callback
        self.pixbuf = pixbuf

    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation
        
        # Draw bg
        cr.set_source_rgb(*gui.bg_color_tuple)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        
        cr.set_source_pixbuf(self.pixbuf, 6, 6)
        cr.paint()

    def _press_event(self, event):
        self.callback(self.widget, event)
