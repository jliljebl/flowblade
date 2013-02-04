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

# Monitor
pos_bar = None
tc = None
mark_in_display = None
mark_out_display = None
length_display = None

# Timeline
tline_display = None
tline_scale = None
tline_canvas = None
tline_scroll = None
tline_info = None
tline_column = None
big_tc = None

# indexes match editmode values in editorstate.py
mode_buttons = None
notebook_buttons = None

play_b = None
clip_editor_b = None
sequence_editor_b = None

# Theme colors
note_bg_color = None
fg_color = None
fg_color_tuple = None
bg_color_tuple = None
    

def capture_references(new_editor_window):
    """
    Create shorter names for some of the frequently used GUI objects.
    """
    global editor_window, media_list_view, bin_list_view, sequence_list_view, pos_bar, \
    tc, mark_in_display, mark_out_display, length_display, tline_display, \
    tline_scale, tline_canvas, tline_scroll, tline_v_scroll, tline_info, \
    tline_column, mode_buttons, play_b, clip_editor_b, sequence_editor_b, note_bg_color, fg_color, fg_color_tuple, bg_color_tuple, \
    effect_select_list_view, effect_select_combo_box, project_info_vbox, middle_notebook, big_tc, editmenu, notebook_buttons

    # Get references
    editor_window = new_editor_window

    media_list_view = editor_window.media_list_view
    bin_list_view = editor_window.bin_list_view
    sequence_list_view = editor_window.sequence_list_view
    
    project_info_vbox = editor_window.project_info_vbox
    middle_notebook = editor_window.notebook
    
    effect_select_list_view = editor_window.effect_select_list_view
    effect_select_combo_box = editor_window.effect_select_combo_box

    pos_bar = editor_window.pos_bar
    tc = editor_window.tc
    mark_in_display = editor_window.mark_in_entry
    mark_out_display = editor_window.mark_out_entry
    length_display = editor_window.length_entry

    tline_display = editor_window.tline_display
    tline_scale = editor_window.tline_scale
    tline_canvas = editor_window.tline_canvas
    tline_scroll = editor_window.tline_scroller
    tline_info = editor_window.tline_info
    tline_column = editor_window.tline_column

    mode_buttons = [editor_window.insert_move_b,
                    editor_window.overwrite_move_b,
                    editor_window.one_roll_trim_b,
                    editor_window.tworoll_trim_b]
    play_b = editor_window.play_b
    clip_editor_b = editor_window.clip_editor_b
    sequence_editor_b = editor_window.sequence_editor_b

    """ 
    Feature postponed, but may still be introduced 
    notebook_buttons = [editor_window.show_media_panel_b, 
                        editor_window.show_filters_panel_b,
                        editor_window.show_compositors_panel_b,
                        editor_window.show_sequences_panel_b,
                        editor_window.show_render_panel_b]
    """

    big_tc = editor_window.big_TC

    editmenu = editor_window.uimanager.get_widget('/MenuBar/EditMenu')

    style = editor_window.notebook.get_style()
    note_bg_color = style.bg[gtk.STATE_NORMAL]
    fg_color = style.fg[gtk.STATE_NORMAL]
    
    # Get cairo color tuple from gtk.gdk.Color
    raw_r, raw_g, raw_b = hex_to_rgb(fg_color.to_string())
    fg_color_tuple = (float(raw_r)/65535.0, float(raw_g)/65535.0, float(raw_b)/65535)

    raw_r, raw_g, raw_b = hex_to_rgb(note_bg_color.to_string())
    bg_color_tuple = (float(raw_r)/65535.0, float(raw_g)/65535.0, float(raw_b)/65535)

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

