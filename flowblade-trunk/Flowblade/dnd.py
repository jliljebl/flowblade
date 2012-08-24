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

import gtk

import clipeffectseditor
from editorstate import current_bin
from editorstate import PROJECT
import gui
import mltfilters
import respaths
import updater

# GUI consts
MEDIA_ICON_WIDTH = 20
MEDIA_ICON_HEIGHT = 15

MEDIA_FILES_DND_TARGET = ('media_file', gtk.TARGET_SAME_APP, 0)
EFFECTS_DND_TARGET = ('effect', gtk.TARGET_SAME_APP, 0)
STRING_DATA_BITS = 8

drag_data = None # Temp. holding for data during drag.

# ----------------------------------------------- set gui components as drag sources and destinations
def connect_media_files_tree_view(tree_view):
    tree_view.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                                       [MEDIA_FILES_DND_TARGET], 
                                       gtk.gdk.ACTION_COPY)
    tree_view.connect_after('drag_begin', _media_files_drag_begin)
    tree_view.connect("drag_data_get", _media_files_drag_data_get)

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

def connect_stack_treeview(widget):
    widget.drag_dest_set(gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_DROP,
                         [EFFECTS_DND_TARGET], 
                         gtk.gdk.ACTION_COPY)
    widget.connect("drag_drop", _on_effect_stack_drop)

def connect_tline(widget, do_effect_drop_func, do_media_drop_func):
    widget.drag_dest_set(gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_DROP,
                         [MEDIA_FILES_DND_TARGET, EFFECTS_DND_TARGET], 
                         gtk.gdk.ACTION_COPY)
    widget.connect("drag_drop", _on_tline_drop, do_effect_drop_func, do_media_drop_func)
    

# ------------------------------------------------- handlers for drag events
def _media_files_drag_begin(treeview, context):
    _save_treeview_selection(treeview)
    media_file = _get_first_dragged_media_file()
    context.set_icon_pixbuf(media_file.icon, MEDIA_ICON_WIDTH, MEDIA_ICON_HEIGHT)

def _media_files_drag_data_get(treeview, context, selection, target_id, timestamp):
    _save_treeview_selection(treeview)

def _effects_drag_begin(widget, context):
    pass 
    # uncomment to use filter icon for drag
    #filter_info = clipeffectseditor.get_selected_filter_info()
    #icon = filter_info.get_icon()
    #context.set_icon_pixbuf(icon, icon.get_width() / 2, icon.get_height() / 2)

def _effects_drag_data_get(treeview, context, selection, target_id, timestamp):
    _save_treeview_selection(treeview)

def _on_monitor_drop(widget, context, x, y, timestamp):
    context.finish(True, False, timestamp)
    media_file = _get_first_dragged_media_file()
    updater.set_and_display_monitor_media_file(media_file)
    gui.pos_bar.widget.grab_focus()

def _on_effect_stack_drop(widget, context, x, y, timestamp):
    context.finish(True, False, timestamp)
    clipeffectseditor.add_currently_selected_effect()
    
def _bin_drag_data_received(treeview, context, x, y, selection, info, etime, move_files_to_bin_func):
    bin_path, drop_pos = treeview.get_dest_row_at_pos(x, y)
    file_row_tuples = drag_data
    moved_rows = []
    for row in file_row_tuples:
        moved_rows.append(max(row))
    move_files_to_bin_func(max(bin_path), moved_rows)
    
def _save_treeview_selection(treeview):
    treeselection = treeview.get_selection()
    (model, rows) = treeselection.get_selected_rows()
    global drag_data
    drag_data = rows

def _on_tline_drop(widget, context, x, y, timestamp, do_effect_drop_func, do_media_drop_func):
    if context.get_source_widget() == gui.effect_select_list_view.treeview:
        do_effect_drop_func(x, y)
        gui.tline_canvas.widget.grab_focus()
    elif context.get_source_widget() == gui.media_list_view.treeview:
        media_file = _get_first_dragged_media_file()
        do_media_drop_func(media_file, x, y)
        gui.tline_canvas.widget.grab_focus()

    context.finish(True, False, timestamp)

# ----------------------------------------------- 
def _get_first_dragged_media_file():
    rows = drag_data
    row = rows[0]
    row_index = max(row)
    file_id = current_bin().file_ids[row_index] 
    return PROJECT().media_files[file_id]
