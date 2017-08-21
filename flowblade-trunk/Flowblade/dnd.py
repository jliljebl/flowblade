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
Module handles drag and drop between widgets.
"""

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import GLib

import os

import editorstate
import gui
import utils
import respaths

# Source identifiers
SOURCE_MEDIA_FILE = "media_file"
SOURCE_MONITOR_WIDGET = "monitor"
SOURCE_EFFECTS_TREE = "effects"
SOURCE_RANGE_LOG = "range log"

# GUI consts
MEDIA_ICON_WIDTH = 20
MEDIA_ICON_HEIGHT = 15

MEDIA_FILES_DND_TARGET = Gtk.TargetEntry.new('media_file', Gtk.TargetFlags.SAME_APP, 0)
EFFECTS_DND_TARGET = Gtk.TargetEntry.new('effect', Gtk.TargetFlags.SAME_APP, 0)
#EFFECTS_STACK_DND_TARGET = Gtk.TargetEntry.new('effectstack', Gtk.TargetFlags.SAME_APP, 0)
CLIPS_DND_TARGET = Gtk.TargetEntry.new('clip', Gtk.TargetFlags.SAME_APP, 0)
RANGE_DND_TARGET = Gtk.TargetEntry.new('range', Gtk.TargetFlags.SAME_APP, 0)

URI_DND_TARGET = Gtk.TargetEntry.new('text/uri-list', 0, 0)


# These used to hold data needed on drag drop instead of the API provided GtkSelectionData.
drag_data = None 
drag_source = None

# Drag icons
clip_icon = None
empty_icon = None

# Callback functions
add_current_effect = None
display_monitor_media_file = None
range_log_items_tline_drop = None
range_log_items_log_drop = None
open_dropped_files = None

def init():
    global clip_icon, empty_icon
    clip_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "clip_dnd.png")
    empty_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "empty.png")


# ----------------------------------------------- set gui components as drag sources and destinations
def connect_media_files_object_widget(widget):
    widget.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,
                           [MEDIA_FILES_DND_TARGET], 
                           Gdk.DragAction.COPY)
    widget.connect("drag_data_get", _media_files_drag_data_get)
    widget.drag_source_set_icon_pixbuf(clip_icon)
    
    connect_media_drop_widget(widget)
    
def connect_media_files_object_cairo_widget(widget):
    widget.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,
                           [MEDIA_FILES_DND_TARGET], 
                           Gdk.DragAction.COPY)
    widget.connect("drag_data_get", _media_files_drag_data_get)
    widget.drag_source_set_icon_pixbuf(clip_icon)

    connect_media_drop_widget(widget)

def connect_media_drop_widget(widget):
    widget.drag_dest_set(Gtk.DestDefaults.ALL, [URI_DND_TARGET], Gdk.DragAction.COPY)
    widget.drag_dest_add_uri_targets()
    widget.connect("drag_data_received", _media_files_drag_received)
    
def connect_bin_tree_view(treeview, move_files_to_bin_func):
    treeview.enable_model_drag_dest([MEDIA_FILES_DND_TARGET],
                                    Gdk.DragAction.DEFAULT)
                                         
    treeview.connect("drag_data_received", _bin_drag_data_received, move_files_to_bin_func)

def connect_effects_select_tree_view(tree_view):
    tree_view.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK,
                                       [EFFECTS_DND_TARGET], 
                                       Gdk.DragAction.COPY)
    tree_view.connect("drag_data_get", _effects_drag_data_get)
  
def connect_video_monitor(widget):
    widget.drag_dest_set(Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP,
                         [MEDIA_FILES_DND_TARGET], 
                         Gdk.DragAction.COPY)

    widget.connect("drag_drop", _on_monitor_drop)
    widget.connect("drag_data_get", _save_monitor_media)
    
    widget.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,
                           [MEDIA_FILES_DND_TARGET], 
                           Gdk.DragAction.COPY)
    widget.drag_source_set_icon_pixbuf(clip_icon)

def connect_tline(widget, do_effect_drop_func, do_media_drop_func):
    widget.drag_dest_set(Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP,
                         [MEDIA_FILES_DND_TARGET, EFFECTS_DND_TARGET, CLIPS_DND_TARGET], 
                         Gdk.DragAction.COPY)
    widget.connect("drag_drop", _on_tline_drop, do_effect_drop_func, do_media_drop_func)
    
def connect_range_log(treeview):
    treeview.drag_source_set(Gdk.ModifierType.BUTTON1_MASK,
                           [CLIPS_DND_TARGET], 
                           Gdk.DragAction.COPY)
    treeview.connect("drag_data_get", _range_log_drag_data_get)
    treeview.drag_dest_set(Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP,
                             [RANGE_DND_TARGET], 
                             Gdk.DragAction.COPY)
    treeview.connect("drag_drop", _on_range_drop)
    treeview.drag_source_set_icon_pixbuf(clip_icon)
    
def start_tline_clips_out_drag(event, clips, widget):
    global drag_data
    drag_data = clips
    target_list = Gtk.TargetList.new([RANGE_DND_TARGET])
    context = widget.drag_begin(target_list, Gdk.DragAction.COPY, 1, event)


# ------------------------------------------------- handlers for drag events
def _media_files_drag_data_get(widget, context, selection, target_id, timestamp):
    _save_media_panel_selection()

def _media_files_drag_received(widget, context, x, y, data, info, timestamp):
    uris = data.get_uris()
    files = []
    for uri in uris:
        try:
            uri_tuple = GLib.filename_from_uri(uri)
        except:
            continue
        uri, unused = uri_tuple
        if os.path.exists(uri) == True:
            if utils.is_media_file(uri) == True:
                files.append(uri)

    if len(files) == 0:
        return

    open_dropped_files(files)
    
def _range_log_drag_data_get(treeview, context, selection, target_id, timestamp):
    _save_treeview_selection(treeview)
    global drag_source
    drag_source = SOURCE_RANGE_LOG

def _effects_drag_data_get(treeview, context, selection, target_id, timestamp):
    _save_treeview_selection(treeview)
    global drag_source
    drag_source = SOURCE_EFFECTS_TREE

def _on_monitor_drop(widget, context, x, y, timestamp):
    context.finish(True, False, timestamp)
    if drag_data == None: # A user error drag from monitor to monitor
        return
    media_file = drag_data[0].media_file
    display_monitor_media_file(media_file)
    gui.pos_bar.widget.grab_focus()

def _on_effect_stack_drop(widget, context, x, y, timestamp):
    context.finish(True, False, timestamp)
    add_current_effect()
    
def _bin_drag_data_received(treeview, context, x, y, selection, info, etime, move_files_to_bin_func):
    bin_path, drop_pos = treeview.get_dest_row_at_pos(x, y)
    moved_rows = []
    for media_object in drag_data:
        moved_rows.append(media_object.bin_index)
    move_files_to_bin_func(max(bin_path), moved_rows)

def _save_treeview_selection(treeview):
    treeselection = treeview.get_selection()
    (model, rows) = treeselection.get_selected_rows()
    global drag_data
    drag_data = rows

def _save_media_panel_selection():
    global drag_data, drag_source
    drag_data = gui.media_list_view.get_selected_media_objects()
    drag_source = SOURCE_MEDIA_FILE

def _save_monitor_media(widget, context, selection, target_id, timestamp):
    media_file = editorstate.MONITOR_MEDIA_FILE()
    global drag_data, drag_source
    drag_data = media_file
    drag_source = SOURCE_MONITOR_WIDGET
    if media_file == None:
        return False

    return True
    
def _on_tline_drop(widget, context, x, y, timestamp, do_effect_drop_func, do_media_drop_func):
    if drag_data == None:
        context.finish(True, False, timestamp)
        return
    
    if drag_source == SOURCE_EFFECTS_TREE:
        do_effect_drop_func(x, y)
        gui.tline_canvas.widget.grab_focus()
    elif drag_source == SOURCE_MEDIA_FILE:
        media_file = drag_data[0].media_file
        do_media_drop_func(media_file, x, y, True)
        gui.tline_canvas.widget.grab_focus()
    elif drag_source == SOURCE_MONITOR_WIDGET:
        if drag_data != None:
            do_media_drop_func(drag_data, x, y, True)
            gui.tline_canvas.widget.grab_focus()
        else:
            print "monitor_drop fail"
    elif drag_source == SOURCE_RANGE_LOG:
        range_log_items_tline_drop(drag_data, x, y)
    else:
        print "_on_tline_drop failed to do anything"
    
    context.finish(True, False, timestamp)

def _on_range_drop(widget, context, x, y, timestamp):
    range_log_items_log_drop(drag_data)

    context.finish(True, False, timestamp)
