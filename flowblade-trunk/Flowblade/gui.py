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
Module holds references to GUI widgets.
"""

import pygtk
pygtk.require('2.0');
import gtk



# Editor window
editor_window = None

# Menu
editmenu = None

# Project data lists
media_list_view = None
bin_list_view = None
sequence_list_view = None
effect_stack_list_view = None

middle_notebook = None # This is now the only notebook, update name sometime
project_info_vbox = None

effect_select_list_view = None
effect_select_combo_box = None

render_out_folder = None

# Media tab
media_view_filter_selector = None
proxy_button = None

# Monitor
pos_bar = None
tc = None

# Timeline
tline_display = None
tline_scale = None
tline_canvas = None
tline_scroll = None
tline_info = None
tline_column = None
tline_left_corner = None
big_tc = None

# indexes match editmode values in editorstate.py
notebook_buttons = None

play_b = None
clip_editor_b = None
sequence_editor_b = None

# Theme colors
note_bg_color = None
fg_color = None
fg_color_tuple = None
bg_color_tuple = None
selected_bg_color = None

def capture_references(new_editor_window):
    """
    Create shorter names for some of the frequently used GUI objects.
    """
    global editor_window, media_list_view, bin_list_view, sequence_list_view, pos_bar, \
    tc, tline_display, tline_scale, tline_canvas, tline_scroll, tline_v_scroll, tline_info, \
    tline_column, play_b, clip_editor_b, sequence_editor_b, note_bg_color, fg_color, fg_color_tuple, bg_color_tuple, selected_bg_color, \
    effect_select_list_view, effect_select_combo_box, project_info_vbox, middle_notebook, big_tc, editmenu, notebook_buttons, tline_left_corner

    editor_window = new_editor_window

    media_list_view = editor_window.media_list_view
    bin_list_view = editor_window.bin_list_view
    sequence_list_view = editor_window.sequence_list_view

    middle_notebook = editor_window.notebook
    
    effect_select_list_view = editor_window.effect_select_list_view
    effect_select_combo_box = editor_window.effect_select_combo_box

    pos_bar = editor_window.pos_bar
    tc = editor_window.tc

    tline_display = editor_window.tline_display
    tline_scale = editor_window.tline_scale
    tline_canvas = editor_window.tline_canvas
    tline_scroll = editor_window.tline_scroller
    tline_info = editor_window.tline_info
    tline_column = editor_window.tline_column
    tline_left_corner = editor_window.left_corner

    clip_editor_b = editor_window.clip_editor_b
    sequence_editor_b = editor_window.sequence_editor_b

    big_tc = editor_window.big_TC

    editmenu = editor_window.uimanager.get_widget('/MenuBar/EditMenu')

    style = editor_window.edit_buttons_row.get_style()
    note_bg_color = style.bg[gtk.STATE_NORMAL]
    fg_color = style.fg[gtk.STATE_NORMAL]
    selected_bg_color = style.bg[gtk.STATE_SELECTED]
    
    # Get cairo color tuple from gtk.gdk.Color
    raw_r, raw_g, raw_b = hex_to_rgb(fg_color.to_string())
    fg_color_tuple = (float(raw_r)/65535.0, float(raw_g)/65535.0, float(raw_b)/65535)

    raw_r, raw_g, raw_b = hex_to_rgb(note_bg_color.to_string())
    bg_color_tuple = (float(raw_r)/65535.0, float(raw_g)/65535.0, float(raw_b)/65535)

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

def enable_save():
    editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(True)
