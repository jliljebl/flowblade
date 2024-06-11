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
Module holds references to GUI widgets and offers some helper functions used in GUI creation.
"""

from gi.repository import Gtk, Gdk, GdkPixbuf

import respaths


# Editor window
editor_window = None

# Menu
editmenu = None

# Project data lists and related views.
media_list_view = None # This is guicomponents.MediaPanel (not a treeview)
bin_list_view = None
bin_panel = None
sequence_list_view = None

project_info_vbox = None

effect_select_list_view = None
effect_select_combo_box = None

render_out_folder = None

# Media tab
media_view_filter_selector = None

# Monitor
pos_bar = None

# Timeline
tline_display = None
tline_scale = None
tline_canvas = None
tline_render_strip = None
tline_scroll = None
tline_info = None # Shows save icon
tline_column = None
tline_left_corner = None
big_tc = None
comp_mode_launcher = None
monitor_widget = None
monitor_switch = None
# indexes match editmode values in editorstate.py
notebook_buttons = None

sequence_editor_b = None

tline_cursor_manager = None


# Theme colors
# Theme colors are given as 4 RGB tuples and string, ((LIGHT_BG), (DARK_BG), (SELECTED_BG), (DARK_SELECTED_BG), name)
_FLOWBLADE_COLORS = ((0.960784, 0.964706, 0.968627), (0.266667, 0.282353, 0.321569), (0.065, 0.342, 0.66), (0.065, 0.342, 0.66), "Flowblade Theme")

MID_NEUTRAL_THEME_NEUTRAL= ((54.0/255.0), (54.0/255.0), (54.0/255.0), 1.0)

_selected_bg_color = None
_bg_color = None
_bg_unmodified_normal = None
_button_colors = None

def capture_references(new_editor_window):
    """
    Create shorter names for some of the frequently used GUI objects.
    """
    global editor_window, media_list_view, bin_list_view, sequence_list_view, pos_bar, \
    tline_display, tline_scale, tline_canvas, tline_scroll, tline_v_scroll, tline_info, \
    tline_column, play_b, effect_select_list_view, effect_select_combo_box, \
    project_info_vbox, big_tc, editmenu, notebook_buttons, tline_left_corner, \
    monitor_widget, bin_panel, monitor_switch, comp_mode_launcher, tline_render_strip, \
    tline_cursor_manager

    editor_window = new_editor_window

    media_list_view = editor_window.media_list_view
    bin_list_view = editor_window.bin_list_view
    bin_panel = editor_window.bins_panel
    sequence_list_view = editor_window.sequence_list_view

    effect_select_list_view = editor_window.effect_select_list_view
    effect_select_combo_box = editor_window.effect_select_combo_box

    pos_bar = editor_window.pos_bar

    monitor_widget = editor_window.monitor_widget
    monitor_switch = editor_window.monitor_switch
    
    tline_display = editor_window.tline_display
    tline_scale = editor_window.tline_scale
    tline_canvas = editor_window.tline_canvas
    tline_scroll = editor_window.tline_scroller
    tline_info = editor_window.tline_info
    tline_column = editor_window.tline_column
    tline_left_corner = editor_window.left_corner
    comp_mode_launcher = editor_window.comp_mode_launcher

    big_tc = editor_window.big_TC

    editmenu = editor_window.uimanager.get_widget('/MenuBar/EditMenu')

    tline_cursor_manager = editor_window.tline_cursor_manager

def enable_save(project):
    if project.last_save_path != None:
        editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(True)

# returns Gdk.RGBA color
def get_bg_color():
    return _bg_color

# returns Gdk.RGBA color
def get_selected_bg_color():
    return _selected_bg_color

def get_mid_neutral_color():
    return Gdk.RGBA(*MID_NEUTRAL_THEME_NEUTRAL)

def set_theme_colors():
    # Find out if theme color discovery works and set selected bg color apppropiately when
    # this is first called.
    global _selected_bg_color, _bg_color, _button_colors, _bg_unmodified_normal

    # THEMECOLORS

    theme_colors = _FLOWBLADE_COLORS
    c = theme_colors[3]
    _selected_bg_color = Gdk.RGBA(*c)
    c = theme_colors[1]
    _bg_color = Gdk.RGBA(*c)
    _button_colors = Gdk.RGBA(*c)

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
    print(path_str)

def apply_theme():
    Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)
    apply_gtk_css()
            
def apply_gtk_css():        
    provider = Gtk.CssProvider.new()
    display = Gdk.Display.get_default()
    screen = display.get_default_screen()
    Gtk.StyleContext.add_provider_for_screen (screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    css_path = "/res/css3/gtk-flowblade-dark.css"

    provider.load_from_path(respaths.ROOT_PATH + css_path)

    return True

def get_default_filter_icon():
    return GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "filter.png")
    
def get_filter_group_icons(default_icon):
    group_icons = {}
    group_icons["Color"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "color.png")
    group_icons["Color Effect"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "color_filter.png")
    group_icons["Audio"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "audio_filter.png")
    group_icons["Audio Filter"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "audio_filter_sin.png")
    group_icons["Blur"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "blur_filter.png")
    group_icons["Distort"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "distort_filter.png")
    group_icons["Alpha"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "alpha_filter.png")
    group_icons["Movement"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "movement_filter.png")
    group_icons["Transform"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "transform.png")
    group_icons["Edge"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "edge.png")
    group_icons["Fix"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "fix.png")
    group_icons["Fade"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "fade_filter.png")
    group_icons["Artistic"] = default_icon
    group_icons["FILTER_MASK"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "filter_mask.png")
    group_icons["Blend"] = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "blend_filter.png")

    return group_icons
