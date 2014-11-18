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
Module handles drag and drop.
"""

import pygtk
pygtk.require('2.0');
import gtk


import editorstate
import gui
import respaths


# GUI consts
MEDIA_ICON_WIDTH = 20
MEDIA_ICON_HEIGHT = 15

MEDIA_FILES_DND_TARGET = ('media_file', gtk.TARGET_SAME_APP, 0)
EFFECTS_DND_TARGET = ('effect', gtk.TARGET_SAME_APP, 0)
CLIPS_DND_TARGET = ('clip', gtk.TARGET_SAME_APP, 0)
RANGE_DND_TARGET = ('range', gtk.TARGET_SAME_APP, 0)
STRING_DATA_BITS = 8

# Holds data during drag
drag_data = None 

# Drag icons
clip_icon = None
empty_icon = None

# Callback functions
add_current_effect = None
display_monitor_media_file = None
range_log_items_tline_drop = None
range_log_items_log_drop = None

def init():
    global clip_icon, empty_icon
    clip_icon = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "clip_dnd.png")
    empty_icon = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "empty.png")

# ----------------------------------------------- set gui components as drag sources and destinations
def connect_media_files_object_widget(widget):
    widget.drag_source_set(gtk.gdk.BUTTON1_MASK,
                           [MEDIA_FILES_DND_TARGET], 
                           gtk.gdk.ACTION_COPY)
    widget.connect_after('drag_begin', _media_files_drag_begin)
    widget.connect("drag_data_get", _media_files_drag_data_get)
    
def connect_media_files_object_cairo_widget(widget):
    widget.drag_source_set(gtk.gdk.BUTTON1_MASK,
                           [MEDIA_FILES_DND_TARGET], 
                           gtk.gdk.ACTION_COPY)
    widget.connect_after('drag_begin', _media_files_drag_begin)
    widget.connect("drag_data_get", _media_files_drag_data_get)
    
def connect_bin_tree_view(treeview, move_files_to_bin_func):
    treeview.enable_model_drag_dest([MEDIA_FILES_DND_TARGET],
                                    gtk.gdk.ACTION_DEFAULT)
                                         
    treeview.connect("drag_data_received", _bin_drag_data_received, move_files_to_bin_func)

    
def connect_effects_select_tree_view(tree_view):
    tree_view.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                                       [EFFECTS_DND_TARGET], 
                                       gtk.gdk.ACTION_COPY)
    tree_view.connect_after('drag_begin', _effects_drag_begin)
    tree_view.connect("drag_data_get", _effects_drag_data_get)

def connect_video_monitor(widget):
    widget.drag_dest_set(gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_DROP,
                         [MEDIA_FILES_DND_TARGET], 
                         gtk.gdk.ACTION_COPY)

    widget.connect("drag_drop", _on_monitor_drop)

    widget.drag_source_set(gtk.gdk.BUTTON1_MASK,
                           [MEDIA_FILES_DND_TARGET], 
                           gtk.gdk.ACTION_COPY)
    widget.connect_after('drag_begin', _monitor_media_drag_begin)
    widget.connect("drag_data_get", _monitor_media_drag_data_get)
    
def connect_stack_treeview(widget):
    widget.drag_dest_set(gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_DROP,
                         [EFFECTS_DND_TARGET], 
                         gtk.gdk.ACTION_COPY)
    widget.connect("drag_drop", _on_effect_stack_drop)

def connect_tline(widget, do_effect_drop_func, do_media_drop_func):
    widget.drag_dest_set(gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_DROP,
                         [MEDIA_FILES_DND_TARGET, EFFECTS_DND_TARGET, CLIPS_DND_TARGET], 
                         gtk.gdk.ACTION_COPY)
    widget.connect("drag_drop", _on_tline_drop, do_effect_drop_func, do_media_drop_func)
    
def connect_range_log(treeview):
    treeview.drag_source_set(gtk.gdk.BUTTON1_MASK,
                           [CLIPS_DND_TARGET], 
                           gtk.gdk.ACTION_COPY)
    treeview.connect_after('drag_begin', _range_log_drag_begin)
    treeview.connect("drag_data_get", _range_log_drag_data_get)
    treeview.drag_dest_set(gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_DROP,
                             [RANGE_DND_TARGET], 
                             gtk.gdk.ACTION_COPY)
    treeview.connect("drag_drop", _on_range_drop)
    
def start_tline_clips_out_drag(event, clips, widget):
    global drag_data
    drag_data = clips
    context = widget.drag_begin([RANGE_DND_TARGET], gtk.gdk.ACTION_COPY, 1, event)
    if context == None: # if something outside of the application is clicked we'll end here and cannot create a context
        return
    context.set_icon_pixbuf(clip_icon, 30, 15)


# ------------------------------------------------- handlers for drag events
def _media_files_drag_begin(treeview, context):
    _save_media_panel_selection()
    context.set_icon_pixbuf(clip_icon, 30, 15)

def _media_files_drag_data_get(widget, context, selection, target_id, timestamp):
    _save_media_panel_selection()

def  _monitor_media_drag_begin(widget, context):
    success = _save_monitor_media()
    if success:
        context.set_icon_pixbuf(clip_icon, 30, 15)
    else:
        context.set_icon_pixbuf(empty_icon, 30, 15)

def _monitor_media_drag_data_get(widget, context, selection, target_id, timestamp):
    pass
    #context.set_icon_pixbuf(clip_icon, 30, 15)

def _range_log_drag_begin(widget, context):
    context.set_icon_pixbuf(clip_icon, 30, 15)

def _range_log_drag_data_get(treeview, context, selection, target_id, timestamp):
    _save_treeview_selection(treeview)
        
def _effects_drag_begin(widget, context):
    pass 

def _effects_drag_data_get(treeview, context, selection, target_id, timestamp):
    _save_treeview_selection(treeview)

def _on_monitor_drop(widget, context, x, y, timestamp):
    context.finish(True, False, timestamp)
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
    global drag_data
    drag_data = gui.media_list_view.get_selected_media_objects()

def _save_monitor_media():
    media_file = editorstate.MONITOR_MEDIA_FILE()
    global drag_data
    drag_data = media_file

    if media_file == None:
        return False

    return True
    
def _on_tline_drop(widget, context, x, y, timestamp, do_effect_drop_func, do_media_drop_func):
    if context.get_source_widget() == gui.effect_select_list_view.treeview:
        do_effect_drop_func(x, y)
        gui.tline_canvas.widget.grab_focus()
    elif hasattr(context.get_source_widget(), "dnd_media_widget_attr") or hasattr(context.get_source_widget(), "dnd_media_widget_attr"):
        media_file = drag_data[0].media_file
        do_media_drop_func(media_file, x, y)
        gui.tline_canvas.widget.grab_focus()
    elif context.get_source_widget() == gui.tline_display:
        if drag_data != None:
            do_media_drop_func(drag_data, x, y, True)
            gui.tline_canvas.widget.grab_focus()
        else:
            print "monitor_drop fail"
    elif context.get_source_widget() == gui.editor_window.media_log_events_list_view.treeview:
        range_log_items_tline_drop(drag_data, x, y)
    else:
        print "_on_tline_drop failed to do anything"
    
    context.finish(True, False, timestamp)

def _on_range_drop(widget, context, x, y, timestamp):
    range_log_items_log_drop(drag_data)

    context.finish(True, False, timestamp)
