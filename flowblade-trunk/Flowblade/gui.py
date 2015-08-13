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

from gi.repository import Gtk, Gdk

import editorpersistance


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
# Theme colors are given as tuple three RGB tuples, ((LIGHT_BG), (DARK_BG), (SELECTED_BG), (BUTTON_C0LORS))
_UBUNTU_COLORS = ((-1, -1, -1), (-1, -1, -1), (0.941, 0.466, 0.274, 0.9),(-1, -1, -1))
_GNOME_COLORS = ((-1, -1, -1), (0.172, 0.172, 0.172), (0.192, 0.361, 0.608), (-1, -1, -1))
_MINT_COLORS = ((-1, -1, -1), (-1, -1, -1), (0.941, 0.466, 0.274, 0.9), (-1, -1, -1))
 
_THEME_COLORS = (_UBUNTU_COLORS, _GNOME_COLORS, _MINT_COLORS)

_selected_bg_color = None
_bg_color = None
_button_colors = None

_colors_set = False 


_not_dark_fixed = ["GtkButton","cairoarea+CairoDrawableArea2", "GtkTreeView"]

#note_bg_color = None
#fg_color = None
#fg_color_tuple = None
#bg_color_tuple = None
#_selected_bg_color = None
#_selected_bg_color_exists = False  # _selected_bg_color cannot be tested == None because cracy Gdk.py 

#label = None

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

    style = editor_window.edit_buttons_row.get_style_context ()
    note_bg_color = style.get_background_color(Gtk.StateFlags.NORMAL)
    #print note_bg_color

    #fg_color = style.get_color(Gtk.StateFlags.NORMAL)
    #

    #style = editor_window.edit_buttons_row.get_style_context ()
    #selected_bg_color = style.get_background_color(Gtk.StateFlags.SELECTED)
    
    # Get cairo color tuple from Gdk.Color
    #raw_r, raw_g, raw_b = fg_color.red,  fg_color.green, fg_color.blue
    #fg_color_tuple = (float(raw_r)/65535.0, float(raw_g)/65535.0, float(raw_b)/65535)

    #raw_r, raw_g, raw_b = note_bg_color.red, note_bg_color.green ,note_bg_color.blue
    #bg_color_tuple = (float(raw_r)/65535.0, float(raw_g)/65535.0, float(raw_b)/65535)

def enable_save():
    editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(True)

# returns Gdk.RGBA color
def get_bg_color():
    return _bg_color

# returns Gdk.RGBA color
def get_selected_bg_color():
    return _selected_bg_color

# returns Gdk.RGBA color
def get_buttons_color():
    return _button_colors
    
def set_theme_colors():
    # Find out if theme color discovery works and set selected bg color apppropiately when 
    # this is first called.
    global _selected_bg_color, _bg_color, _button_colors, _colors_set

    fallback_theme_colors = 1
    theme_colors = _THEME_COLORS[fallback_theme_colors]
    
    style = editor_window.bin_list_view.get_style_context()
    sel_bg_color = style.get_background_color(Gtk.StateFlags.SELECTED)

    r, g, b, a = unpack_gdk_color(sel_bg_color)
    if r == 0.0 and g == 0.0 and b == 0.0:
        print "sel color NOT detected"
        _selected_bg_color = Gdk.RGBA(*theme_colors[2])
    else:
        print "sel color detected"
        _selected_bg_color = sel_bg_color

    style = editor_window.window.get_style_context()
    bg_color = style.get_background_color(Gtk.StateFlags.NORMAL)
    r, g, b, a = unpack_gdk_color(bg_color)

    if r == 0.0 and g == 0.0 and b == 0.0:
        print "bg color NOT detected"
        _bg_color = Gdk.RGBA(*theme_colors[0])
        _button_colors = Gdk.RGBA(*theme_colors[3])
    else:
        print "bg color detected"
        _bg_color = bg_color
        _button_colors = bg_color

    # Adwaita and some others show big area of black without this, does not bother ubuntu
    editor_window.tline_pane.override_background_color(Gtk.StateFlags.NORMAL, get_bg_color())
    editor_window.media_panel.override_background_color(Gtk.StateFlags.NORMAL, get_bg_color())
    editor_window.mm_paned.override_background_color(Gtk.StateFlags.NORMAL, get_bg_color())
    
def unpack_gdk_color(gdk_color):
    return (gdk_color.red, gdk_color.green, gdk_color.blue, gdk_color.alpha)

def _print_widget(widget): # debug
    path_str = widget.get_path().to_string()
    path_str = path_str.replace("GtkWindow:dir-ltr.background","")
    path_str = path_str.replace("dir-ltr","")
    path_str = path_str.replace("vertical","")
    path_str = path_str.replace("horizontal","")
    path_str = path_str.replace("[1/2]","")
    path_str = path_str.replace("GtkVBox:. GtkVPaned:[2/2]. GtkHBox:. GtkHPaned:. GtkVBox:. GtkNotebook:[1/1]","notebook:")
    print path_str

