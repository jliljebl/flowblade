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

import copy
import os
import pickle
import threading

import time

from gi.repository import Gtk, Gdk, GdkPixbuf
from gi.repository import GLib, GObject
from gi.repository import Pango
from gi.repository import PangoCairo

import toolsdialogs
from editorstate import PLAYER
import editorstate
import gui
import guicomponents
import guiutils
import dialogutils
import projectaction
import respaths
import positionbar
import utils
import vieweditor
import vieweditorlayer

_titler = None
_titler_data = None
_titler_lastdir = None

_keep_titler_data = True
_open_saved_in_bin = True

_filling_layer_list = False

VIEW_EDITOR_WIDTH = 815
VIEW_EDITOR_HEIGHT = 620

TEXT_LAYER_LIST_WIDTH = 300
TEXT_LAYER_LIST_HEIGHT = 150

TEXT_VIEW_WIDTH = 300
TEXT_VIEW_HEIGHT = 275

DEFAULT_FONT_SIZE = 25

FACE_REGULAR = "Regular"
FACE_BOLD = "Bold"
FACE_ITALIC = "Italic"
FACE_BOLD_ITALIC = "Bold Italic"

ALIGN_LEFT = 0
ALIGN_CENTER = 1
ALIGN_RIGHT = 2

def show_titler():
    global _titler_data
    if _titler_data == None:
        _titler_data = TitlerData()
    
    global _titler
    if _titler != None:
        primary_txt = _("Titler is already open")
        secondary_txt =  _("Only single instance of Titler can be opened.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    _titler = Titler()
    _titler.load_titler_data()
    _titler.show_current_frame()

def close_titler():
    global _titler, _titler_data
    
    _titler.set_visible(False)

    GLib.idle_add(titler_destroy)

def titler_destroy():
    global _titler, _titler_data
    _titler.destroy()
    _titler = None

    if not _keep_titler_data:
        _titler_data = None

def reset_titler():
    global _titler_data
    _titler_data = None
        
# ------------------------------------------------------------- data
class TextLayer:
    """
    Data needed to create a pango text layout.
    """
    def __init__(self):
        self.text = "Text"
        self.x = 0.0
        self.y = 0.0
        self.angle = 0.0 # future feature
        self.font_family = "Times New Roman"
        self.font_face = FACE_REGULAR
        self.font_size = 15
        self.fill_on = True
        self.color_rgba = (1.0, 1.0, 1.0, 1.0) 
        self.alignment = ALIGN_LEFT
        self.pixel_size = (100, 100)
        self.spacing = 5
        
        self.outline_on = False
        self.outline_color_rgba = (0.3, 0.3, 0.3, 1.0) 
        self.outline_width = 2

        self.shadow_on = False
        self.shadow_color_rgb = (0.0, 0.0, 0.0) 
        self.shadow_opacity = 100
        self.shadow_xoff = 3
        self.shadow_yoff = 3
        self.shadow_blur = 0.0 # not impl yet, for future so that we don't need to break save format again
        
        self.pango_layout = None # PangoTextLayout(self)

        self.layer_attributes = None # future feature 
        self.visible = True

    def get_font_desc_str(self):
        return self.font_family + " " + self.font_face + " " + str(self.font_size)

    def update_pango_layout(self):
        self.pango_layout.load_layer_data(self)


class TitlerData:
    """
    Data edited in titler editor
    """
    def __init__(self):
        self.layers = []
        self.active_layer = None
        self.add_layer()
        self.scroll_params = None # future feature
        
    def add_layer(self):
        # adding layer makes new layer active
        self.active_layer = TextLayer()
        self.active_layer.pango_layout = PangoTextLayout(self.active_layer)
        self.layers.append(self.active_layer)

    def get_active_layer_index(self):
        return self.layers.index(self.active_layer)
    
    def save(self, save_file_path):
        save_data = copy.deepcopy(self)
        for layer in save_data.layers:
            layer.pango_layout = None
        write_file = file(save_file_path, "wb")
        pickle.dump(save_data, write_file)
   
    def create_pango_layouts(self):
        for layer in self.layers:
            layer.pango_layout = PangoTextLayout(layer)
            
# ---------------------------------------------------------- editor
class Titler(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.set_title(_("Titler"))
        self.connect("delete-event", lambda w, e:close_titler())
        
        if editorstate.screen_size_small_height() == True:
            global TEXT_LAYER_LIST_HEIGHT, TEXT_VIEW_HEIGHT, VIEW_EDITOR_HEIGHT
            TEXT_LAYER_LIST_HEIGHT = 150
            TEXT_VIEW_HEIGHT = 180
            VIEW_EDITOR_HEIGHT = 450

        if editorstate.screen_size_small_height() == True:
            global VIEW_EDITOR_WIDTH
            VIEW_EDITOR_WIDTH = 680
            
        self.block_updates = False
        
        self.view_editor = vieweditor.ViewEditor(PLAYER().profile, VIEW_EDITOR_WIDTH, VIEW_EDITOR_HEIGHT)
        self.view_editor.active_layer_changed_listener = self.active_layer_changed
        
        self.guides_toggle = vieweditor.GuidesViewToggle(self.view_editor)
        
        add_b = Gtk.Button(_("Add"))
        del_b = Gtk.Button(_("Delete"))
        add_b.connect("clicked", lambda w:self._add_layer_pressed())
        del_b.connect("clicked", lambda w:self._del_layer_pressed())
        add_del_box = Gtk.HBox()
        add_del_box = Gtk.HBox(True,1)
        add_del_box.pack_start(add_b, True, True, 0)
        add_del_box.pack_start(del_b, True, True, 0)

        center_h_icon = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "center_horizontal.png")
        center_v_icon = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "center_vertical.png")
        center_h = Gtk.Button()
        center_h.set_image(center_h_icon)
        center_h.connect("clicked", lambda w:self._center_h_pressed())
        center_v = Gtk.Button()
        center_v.set_image(center_v_icon)
        center_v.connect("clicked", lambda w:self._center_v_pressed())

        self.layer_list = TextLayerListView(self._layer_selection_changed, self._layer_visibility_toggled)
        self.layer_list.set_size_request(TEXT_LAYER_LIST_WIDTH, TEXT_LAYER_LIST_HEIGHT)
    
        self.text_view = Gtk.TextView()
        self.text_view.set_pixels_above_lines(2)
        self.text_view.set_left_margin(2)
        self.text_view.get_buffer().connect("changed", self._text_changed)

        self.sw = Gtk.ScrolledWindow()
        self.sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
        self.sw.add(self.text_view)
        self.sw.set_size_request(TEXT_VIEW_WIDTH, TEXT_VIEW_HEIGHT)

        scroll_frame = Gtk.Frame()
        scroll_frame.add(self.sw)
        
        self.tc_display = guicomponents.MonitorTCDisplay()
        self.tc_display.use_internal_frame = True
        self.tc_display.widget.set_valign(Gtk.Align.CENTER)
        
        self.pos_bar = positionbar.PositionBar()
        self.pos_bar.set_listener(self.position_listener)
        self.pos_bar.update_display_from_producer(PLAYER().producer)
        self.pos_bar.mouse_release_listener = self.pos_bar_mouse_released

        pos_bar_frame = Gtk.Frame()
        pos_bar_frame.add(self.pos_bar.widget)
        pos_bar_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        pos_bar_frame.set_valign(Gtk.Align.CENTER)
                
        font_map = PangoCairo.font_map_get_default()
        unsorted_families = font_map.list_families()
        if len(unsorted_families) == 0:
            print "No font families found in system! Titler will not work."
        self.font_families = sorted(unsorted_families, key=lambda family: family.get_name())
        self.font_family_indexes_for_name = {}
        combo = Gtk.ComboBoxText()
        indx = 0
        for family in self.font_families:
            combo.append_text(family.get_name())
            self.font_family_indexes_for_name[family.get_name()] = indx
            indx += 1
        combo.set_active(0)
        self.font_select = combo
        self.font_select.connect("changed", self._edit_value_changed)
    
        adj = Gtk.Adjustment(float(DEFAULT_FONT_SIZE), float(1), float(300), float(1))
        self.size_spin = Gtk.SpinButton()
        self.size_spin.set_adjustment(adj)
        self.size_spin.connect("changed", self._edit_value_changed)
        self.size_spin.connect("key-press-event", self._key_pressed_on_widget)

        font_main_row = Gtk.HBox()
        font_main_row.pack_start(self.font_select, True, True, 0)
        font_main_row.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        font_main_row.pack_start(self.size_spin, False, False, 0)

        self.bold_font = Gtk.ToggleButton()
        self.italic_font = Gtk.ToggleButton()
        bold_icon = Gtk.Image.new_from_stock(Gtk.STOCK_BOLD, 
                                       Gtk.IconSize.BUTTON)
        italic_icon = Gtk.Image.new_from_stock(Gtk.STOCK_ITALIC, 
                                       Gtk.IconSize.BUTTON)
        self.bold_font.set_image(bold_icon)
        self.italic_font.set_image(italic_icon)
        self.bold_font.connect("clicked", self._edit_value_changed)
        self.italic_font.connect("clicked", self._edit_value_changed)
        
        self.left_align = Gtk.RadioButton(None)
        self.center_align = Gtk.RadioButton.new_from_widget(self.left_align)
        self.right_align = Gtk.RadioButton.new_from_widget(self.left_align)
        left_icon = Gtk.Image.new_from_stock(Gtk.STOCK_JUSTIFY_LEFT, 
                                       Gtk.IconSize.BUTTON)
        center_icon = Gtk.Image.new_from_stock(Gtk.STOCK_JUSTIFY_CENTER, 
                                       Gtk.IconSize.BUTTON)
        right_icon = Gtk.Image.new_from_stock(Gtk.STOCK_JUSTIFY_RIGHT, 
                                       Gtk.IconSize.BUTTON)
        self.left_align.set_image(left_icon)
        self.center_align.set_image(center_icon)
        self.right_align.set_image(right_icon)
        self.left_align.set_mode(False)
        self.center_align.set_mode(False)
        self.right_align.set_mode(False)
        self.left_align.connect("clicked", self._edit_value_changed)
        self.center_align.connect("clicked", self._edit_value_changed)
        self.right_align.connect("clicked", self._edit_value_changed)
        
        self.color_button = Gtk.ColorButton.new_with_rgba(Gdk.RGBA(red=1.0, green=1.0, blue=1.0, alpha=1.0))
        self.color_button.connect("color-set", self._edit_value_changed)
        self.fill_on = Gtk.CheckButton()
        self.fill_on.set_active(True)
        self.fill_on.connect("toggled", self._edit_value_changed)

        buttons_box = Gtk.HBox()
        buttons_box.pack_start(Gtk.Label(), True, True, 0)
        buttons_box.pack_start(self.bold_font, False, False, 0)
        buttons_box.pack_start(self.italic_font, False, False, 0)
        buttons_box.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        buttons_box.pack_start(self.left_align, False, False, 0)
        buttons_box.pack_start(self.center_align, False, False, 0)
        buttons_box.pack_start(self.right_align, False, False, 0)
        buttons_box.pack_start(guiutils.pad_label(15, 5), False, False, 0)
        buttons_box.pack_start(self.color_button, False, False, 0)
        buttons_box.pack_start(guiutils.pad_label(2, 1), False, False, 0)
        buttons_box.pack_start(self.fill_on, False, False, 0)
        buttons_box.pack_start(Gtk.Label(), True, True, 0)

        outline_label = Gtk.Label(_("<b>Outline</b>"))
        outline_label.set_use_markup(True)
        outline_size = Gtk.Label(_("Size:"))
        
        self.out_line_color_button = Gtk.ColorButton.new_with_rgba(Gdk.RGBA(red=0.3, green=0.3, blue=0.3, alpha=1.0))
        self.out_line_color_button.connect("color-set", self._edit_value_changed)
        
        adj2 = Gtk.Adjustment(float(3), float(1), float(50), float(1))
        self.out_line_size_spin = Gtk.SpinButton()
        self.out_line_size_spin.set_adjustment(adj2)
        self.out_line_size_spin.connect("changed", self._edit_value_changed)
        self.out_line_size_spin.connect("key-press-event", self._key_pressed_on_widget)

        self.outline_on = Gtk.CheckButton()
        self.outline_on.set_active(False)
        self.outline_on.connect("toggled", self._edit_value_changed)
        
        outline_box = Gtk.HBox()
        outline_box.pack_start(outline_label, False, False, 0)
        outline_box.pack_start(guiutils.pad_label(15, 1), False, False, 0)
        outline_box.pack_start(outline_size, False, False, 0)
        outline_box.pack_start(guiutils.pad_label(2, 1), False, False, 0)
        outline_box.pack_start(self.out_line_size_spin, False, False, 0)
        outline_box.pack_start(guiutils.pad_label(15, 1), False, False, 0)
        outline_box.pack_start(self.out_line_color_button, False, False, 0)
        outline_box.pack_start(guiutils.pad_label(2, 1), False, False, 0)
        outline_box.pack_start(self.outline_on, False, False, 0)
        outline_box.pack_start(Gtk.Label(), True, True, 0)

        shadow_label = Gtk.Label(_("<b>Shadow</b>"))
        shadow_label.set_use_markup(True)
        shadow_opacity_label = Gtk.Label(_("Opacity:"))
        shadow_xoff = Gtk.Label(_("X Off:"))
        shadow_yoff = Gtk.Label(_("Y Off:"))
        
        self.shadow_opa_spin = Gtk.SpinButton()
        adj3 = Gtk.Adjustment(float(100), float(1), float(100), float(1))
        self.shadow_opa_spin.set_adjustment(adj3)
        self.shadow_opa_spin.connect("changed", self._edit_value_changed)
        self.shadow_opa_spin.connect("key-press-event", self._key_pressed_on_widget)

        self.shadow_xoff_spin = Gtk.SpinButton()
        adj4 = Gtk.Adjustment(float(3), float(1), float(100), float(1))
        self.shadow_xoff_spin.set_adjustment(adj4)
        self.shadow_xoff_spin.connect("changed", self._edit_value_changed)
        self.shadow_xoff_spin.connect("key-press-event", self._key_pressed_on_widget)

        self.shadow_yoff_spin = Gtk.SpinButton()
        adj5 = Gtk.Adjustment(float(3), float(1), float(100), float(1))
        self.shadow_yoff_spin.set_adjustment(adj5)
        self.shadow_yoff_spin.connect("changed", self._edit_value_changed)
        self.shadow_yoff_spin.connect("key-press-event", self._key_pressed_on_widget)

        self.shadow_on = Gtk.CheckButton()
        self.shadow_on.set_active(False)
        self.shadow_on.connect("toggled", self._edit_value_changed)
        
        self.shadow_color_button = Gtk.ColorButton.new_with_rgba(Gdk.RGBA(red=0.3, green=0.3, blue=0.3, alpha=1.0))
        self.shadow_color_button.connect("color-set", self._edit_value_changed)

        shadow_box_1 = Gtk.HBox()
        shadow_box_1.pack_start(shadow_label, False, False, 0)
        shadow_box_1.pack_start(guiutils.pad_label(15, 1), False, False, 0)
        shadow_box_1.pack_start(shadow_opacity_label, False, False, 0)
        shadow_box_1.pack_start(self.shadow_opa_spin, False, False, 0)
        shadow_box_1.pack_start(guiutils.pad_label(15, 1), False, False, 0)
        shadow_box_1.pack_start(self.shadow_color_button, False, False, 0)
        shadow_box_1.pack_start(guiutils.pad_label(2, 1), False, False, 0)
        shadow_box_1.pack_start(self.shadow_on, False, False, 0)
        shadow_box_1.pack_start(Gtk.Label(), True, True, 0)

        shadow_box_2 = Gtk.HBox()
        shadow_box_2.pack_start(shadow_xoff, False, False, 0)
        shadow_box_2.pack_start(self.shadow_xoff_spin, False, False, 0)
        shadow_box_2.pack_start(guiutils.pad_label(15, 1), False, False, 0)
        shadow_box_2.pack_start(shadow_yoff, False, False, 0)
        shadow_box_2.pack_start(self.shadow_yoff_spin, False, False, 0)
        shadow_box_2.pack_start(Gtk.Label(), True, True, 0)
        
        load_layers = Gtk.Button(_("Load Layers"))
        load_layers.connect("clicked", lambda w:self._load_layers_pressed())
        save_layers = Gtk.Button(_("Save Layers"))
        save_layers.connect("clicked", lambda w:self._save_layers_pressed())
        clear_layers = Gtk.Button(_("Clear All"))
        clear_layers.connect("clicked", lambda w:self._clear_layers_pressed())

        layers_save_buttons_row = Gtk.HBox()
        layers_save_buttons_row.pack_start(save_layers, False, False, 0)
        layers_save_buttons_row.pack_start(load_layers, False, False, 0)
        layers_save_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        
        adj = Gtk.Adjustment(float(0), float(0), float(3000), float(1))
        self.x_pos_spin = Gtk.SpinButton()
        self.x_pos_spin.set_adjustment(adj)
        self.x_pos_spin.connect("changed", self._position_value_changed)
        self.x_pos_spin.connect("key-press-event", self._key_pressed_on_widget)
        adj = Gtk.Adjustment(float(0), float(0), float(3000), float(1))
        self.y_pos_spin = Gtk.SpinButton()
        self.y_pos_spin.set_adjustment(adj)
        self.y_pos_spin.connect("changed", self._position_value_changed)
        self.y_pos_spin.connect("key-press-event", self._key_pressed_on_widget)
        adj = Gtk.Adjustment(float(0), float(0), float(3000), float(1))
        self.rotation_spin = Gtk.SpinButton()
        self.rotation_spin.set_adjustment(adj)
        self.rotation_spin.connect("changed", self._position_value_changed)
        self.rotation_spin.connect("key-press-event", self._key_pressed_on_widget)
        
        undo_pos = Gtk.Button()
        undo_icon = Gtk.Image.new_from_stock(Gtk.STOCK_UNDO, 
                                       Gtk.IconSize.BUTTON)
        undo_pos.set_image(undo_icon)

        next_icon = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "next_frame_s.png")
        prev_icon = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "prev_frame_s.png")
        prev_frame = Gtk.Button()
        prev_frame.set_image(prev_icon)
        prev_frame.connect("clicked", lambda w:self._prev_frame_pressed())
        next_frame = Gtk.Button()
        next_frame.set_image(next_icon)
        next_frame.connect("clicked", lambda w:self._next_frame_pressed())

        self.scale_selector = vieweditor.ScaleSelector(self)

        timeline_box = Gtk.HBox()
        timeline_box.pack_start(self.tc_display.widget, False, False, 0)
        timeline_box.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        timeline_box.pack_start(pos_bar_frame, True, True, 0)
        timeline_box.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        timeline_box.pack_start(prev_frame, False, False, 0)
        timeline_box.pack_start(next_frame, False, False, 0)
        timeline_box.pack_start(self.guides_toggle, False, False, 0)
        timeline_box.pack_start(self.scale_selector, False, False, 0)
        timeline_box.set_margin_top(6)
        timeline_box.set_margin_bottom(6)
        
        positions_box = Gtk.HBox()
        positions_box.pack_start(Gtk.Label(), True, True, 0)
        positions_box.pack_start(Gtk.Label(label="X:"), False, False, 0)
        positions_box.pack_start(self.x_pos_spin, False, False, 0)
        positions_box.pack_start(guiutils.pad_label(40, 5), False, False, 0)
        positions_box.pack_start(Gtk.Label(label="Y:"), False, False, 0)
        positions_box.pack_start(self.y_pos_spin, False, False, 0)
        #positions_box.pack_start(Gtk.Label(label=_("Angle")), False, False, 0)
        #positions_box.pack_start(self.rotation_spin, False, False, 0)
        positions_box.pack_start(guiutils.pad_label(40, 5), False, False, 0)
        positions_box.pack_start(center_h, False, False, 0)
        positions_box.pack_start(center_v, False, False, 0)
        positions_box.pack_start(Gtk.Label(), True, True, 0)

        controls_panel_1 = Gtk.VBox()
        controls_panel_1.pack_start(add_del_box, False, False, 0)
        controls_panel_1.pack_start(self.layer_list, False, False, 0)
        controls_panel_1.pack_start(layers_save_buttons_row, False, False, 0)

        controls_panel_2 = Gtk.VBox()
        controls_panel_2.pack_start(scroll_frame, True, True, 0)
        controls_panel_2.pack_start(font_main_row, False, False, 0)
        controls_panel_2.pack_start(buttons_box, False, False, 0)
        controls_panel_2.pack_start(guiutils.pad_label(40, 1), False, False, 0)
        controls_panel_2.pack_start(outline_box, False, False, 0)
        controls_panel_2.pack_start(guiutils.pad_label(40, 1), False, False, 0)
        controls_panel_2.pack_start(shadow_box_1, False, False, 0)
        controls_panel_2.pack_start(shadow_box_2, False, False, 0)
        
        controls_panel = Gtk.VBox()
        controls_panel.pack_start(guiutils.get_named_frame(_("Active Layer"),controls_panel_2), True, True, 0)
        controls_panel.pack_start(guiutils.get_named_frame(_("Layers"),controls_panel_1), False, False, 0)
 
        view_editor_editor_buttons_row = Gtk.HBox()
        view_editor_editor_buttons_row.pack_start(positions_box, False, False, 0)
        view_editor_editor_buttons_row.pack_start(Gtk.Label(), True, True, 0)

        keep_label = Gtk.Label(label=_("Keep Layers When Closed"))
        self.keep_layers_check = Gtk.CheckButton()
        self.keep_layers_check.set_active(_keep_titler_data)
        self.keep_layers_check.connect("toggled", self._keep_layers_toggled)
        
        open_label = Gtk.Label(label=_("Open Saved Title In Bin"))
        self.open_in_current_check = Gtk.CheckButton()
        self.open_in_current_check.set_active(_open_saved_in_bin)
        self.open_in_current_check.connect("toggled", self._open_saved_in_bin)

        exit_b = guiutils.get_sized_button(_("Close"), 150, 32)
        exit_b.connect("clicked", lambda w:close_titler())
        save_titles_b = guiutils.get_sized_button(_("Save Title Graphic"), 150, 32)
        save_titles_b.connect("clicked", lambda w:self._save_title_pressed())
        
        editor_buttons_row = Gtk.HBox()
        editor_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        editor_buttons_row.pack_start(keep_label, False, False, 0)
        editor_buttons_row.pack_start(self.keep_layers_check, False, False, 0)
        editor_buttons_row.pack_start(guiutils.pad_label(24, 2), False, False, 0)
        editor_buttons_row.pack_start(open_label, False, False, 0)
        editor_buttons_row.pack_start(self.open_in_current_check, False, False, 0)
        editor_buttons_row.pack_start(guiutils.pad_label(24, 2), False, False, 0)
        editor_buttons_row.pack_start(exit_b, False, False, 0)
        editor_buttons_row.pack_start(save_titles_b, False, False, 0)
        
        editor_panel = Gtk.VBox()
        editor_panel.pack_start(self.view_editor, True, True, 0)
        editor_panel.pack_start(timeline_box, False, False, 0)
        editor_panel.pack_start(guiutils.get_in_centering_alignment(view_editor_editor_buttons_row), False, False, 0)
        editor_panel.pack_start(guiutils.pad_label(2, 24), True, True, 0)
        editor_panel.pack_start(editor_buttons_row, False, False, 0)

        editor_row = Gtk.HBox()
        editor_row.pack_start(controls_panel, False, False, 0)
        editor_row.pack_start(editor_panel, True, True, 0)

        alignment = guiutils.set_margins(editor_row, 8,8,8,8)

        self.add(alignment)

        self.layer_list.fill_data_model()
        self._update_gui_with_active_layer_data()
        self.show_all()

        self.connect("size-allocate", lambda w, e:self.window_resized())
        self.connect("window-state-event", lambda w, e:self.window_resized())
    
    def load_titler_data(self):
        # clear and then load layers, and set layer 0 active
        self.view_editor.clear_layers()

        global _titler_data
        _titler_data.create_pango_layouts()

        for layer in _titler_data.layers:
            text_layer = vieweditorlayer.TextEditLayer(self.view_editor, layer.pango_layout)
            text_layer.mouse_released_listener  = self._editor_layer_mouse_released
            text_layer.set_rect_pos(layer.x, layer.y)
            text_layer.update_rect = True
            self.view_editor.add_layer(text_layer)

        self._activate_layer(0)
        self.layer_list.fill_data_model()
        self.view_editor.edit_area.queue_draw()

    def show_current_frame(self):
        frame = PLAYER().current_frame()
        length = PLAYER().producer.get_length()
        rgbdata = PLAYER().seek_and_get_rgb_frame(frame)
        self.view_editor.set_screen_rgb_data(rgbdata)
        self.pos_bar.set_normalized_pos(float(frame)/float(length))
        self.tc_display.set_frame(frame)
        self.pos_bar.widget.queue_draw()
        self._update_active_layout()

    def window_resized(self):
        scale = self.scale_selector.get_current_scale()
        self.scale_changed(scale)

    def scale_changed(self, new_scale):
        self.view_editor.set_scale_and_update(new_scale)
        self.view_editor.edit_area.queue_draw()

    def write_current_frame(self):
        self.view_editor.write_out_layers = True
        self.show_current_frame()

    def position_listener(self, normalized_pos, length):
        frame = normalized_pos * length
        self.tc_display.set_frame(int(frame))
        self.pos_bar.widget.queue_draw()

    def pos_bar_mouse_released(self, normalized_pos, length):
        frame = int(normalized_pos * length)
        PLAYER().seek_frame(frame)
        self.show_current_frame()

    def _save_title_pressed(self):
        toolsdialogs.save_titler_graphic_as_dialog(self._save_title_dialog_callback, "title.png", _titler_lastdir)

    def _save_title_dialog_callback(self, dialog, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            try:
                filenames = dialog.get_filenames()
                dialog.destroy()
                save_path = filenames[0]
                self.view_editor.write_layers_to_png(save_path)
                (dirname, filename) = os.path.split(save_path)
                global _titler_lastdir
                _titler_lastdir = dirname
        
                if _open_saved_in_bin:
                    open_file_thread = OpenFileThread(save_path, self.view_editor)
                    open_file_thread.start()
                # INFOWINDOW
            except:
                # INFOWINDOW
                dialog.destroy()
                return
        else:
            dialog.destroy()

    def _save_layers_pressed(self):
        toolsdialogs.save_titler_data_as_dialog(self._save_layers_dialog_callback, "titler_layers", None)

    def _save_layers_dialog_callback(self, dialog, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            filenames = dialog.get_filenames()
            save_path = filenames[0]
            _titler_data.save(save_path)
            dialog.destroy()
        else:
            dialog.destroy()
            
    def _load_layers_pressed(self):
        toolsdialogs.load_titler_data_dialog(self._load_layers_dialog_callback)
        
    def _load_layers_dialog_callback(self, dialog, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            try:
                filenames = dialog.get_filenames()
                load_path = filenames[0]
                f = open(load_path)
                new_data = pickle.load(f)
                global _titler_data
                _titler_data = new_data
                self.load_titler_data()
            except:
                dialog.destroy()
                # INFOWINDOW
                return
                
            dialog.destroy()
        else:
            dialog.destroy()

    def _clear_layers_pressed(self):
        # INFOWINDOW
        # CONFIRM WINDOW HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        global _titler_data
        _titler_data = TitlerData()
        self.load_titler_data()

    def _keep_layers_toggled(self, widget):
        global _keep_titler_data
        _keep_titler_data = widget.get_active()

    def _open_saved_in_bin(self, widget):
        global _open_saved_in_bin
        _open_saved_in_bin = widget.get_active()

    def _key_pressed_on_widget(self, widget, event):
        # update layer for enter on size spin
        if widget == self.size_spin and event.keyval == Gdk.KEY_Return:
            self.size_spin.update()
            self._update_active_layout()
            return True

            # update layer for enter on x, y, angle
        if ((event.keyval == Gdk.KEY_Return) and ((widget == self.x_pos_spin) or
            (widget == self.y_pos_spin) or (widget == self.rotation_spin))):
            self.x_pos_spin.update()
            self.y_pos_spin.update()
            self.rotation_spin.update()
            _titler_data.active_layer.x = self.x_pos_spin.get_value()
            _titler_data.active_layer.y = self.y_pos_spin.get_value()
            self._update_editor_layer_pos()
            self.view_editor.edit_area.queue_draw()
            return True

        return False

    def _update_editor_layer_pos(self):
        shape = self.view_editor.active_layer.edit_point_shape
        shape.translate_points_to_pos(_titler_data.active_layer.x, 
                                      _titler_data.active_layer.y, 0)

    def _add_layer_pressed(self):
        global _titler_data
        _titler_data.add_layer()
        
        view_editor_layer = vieweditorlayer.TextEditLayer(self.view_editor, _titler_data.active_layer.pango_layout)
        view_editor_layer.mouse_released_listener  = self._editor_layer_mouse_released
        self.view_editor.edit_layers.append(view_editor_layer)
        
        self.layer_list.fill_data_model()
        self._activate_layer(len(_titler_data.layers) - 1)
        
    def _del_layer_pressed(self):
        # we always need 1 layer
        if len(_titler_data.layers) < 2:
            return

        #active_index = _titler_data.get_active_layer_index()
        _titler_data.layers.remove(_titler_data.active_layer)
        self.view_editor.edit_layers.remove(self.view_editor.active_layer)
        self.layer_list.fill_data_model()
        self._activate_layer(0)

    def _layer_visibility_toggled(self, layer_index):
        toggled_visible = (self.view_editor.edit_layers[layer_index].visible == False)
        self.view_editor.edit_layers[layer_index].visible = toggled_visible
        _titler_data.layers[layer_index].visible = toggled_visible
        self.layer_list.fill_data_model()

        self.view_editor.edit_area.queue_draw()
        
    def _center_h_pressed(self):
        # calculate top left x pos for centering
        w, h = _titler_data.active_layer.pango_layout.pixel_size
        centered_x = self.view_editor.profile_w/2 - w/2
        
        # update data and view
        _titler_data.active_layer.x = centered_x
        self._update_editor_layer_pos()
        self.view_editor.edit_area.queue_draw()
        
        self.block_updates = True
        self.x_pos_spin.set_value(centered_x)
        self.block_updates = False

    def _center_v_pressed(self):
        # calculate top left x pos for centering
        w, h = _titler_data.active_layer.pango_layout.pixel_size
        centered_y = self.view_editor.profile_h/2 - h/2
        
        # update data and view
        _titler_data.active_layer.y = centered_y
        self._update_editor_layer_pos()
        self.view_editor.edit_area.queue_draw()
        
        self.block_updates = True
        self.y_pos_spin.set_value(centered_y)
        self.block_updates = False

    def _prev_frame_pressed(self):
        PLAYER().seek_delta(-1)
        self.show_current_frame()

    def _next_frame_pressed(self):
        PLAYER().seek_delta(1)
        self.show_current_frame()

    def _layer_selection_changed(self, treeview, path, column):
        selected_row = path.get_indices()[0]

        # we're listeneing to "changed" on treeview and get some events (text updated)
        # when layer selection was not changed.
        if selected_row == -1:
            return

        self._activate_layer(selected_row)

    def active_layer_changed(self, layer_index):
        global _titler_data
        _titler_data.active_layer = _titler_data.layers[layer_index]
        self._update_gui_with_active_layer_data()
        _titler_data.active_layer.update_pango_layout()

    def _activate_layer(self, layer_index):
        global _titler_data
        _titler_data.active_layer = _titler_data.layers[layer_index]
        
        self._update_gui_with_active_layer_data()
        _titler_data.active_layer.update_pango_layout()
        self.view_editor.activate_layer(layer_index)
        self.view_editor.active_layer.update_rect = True
        self.view_editor.edit_area.queue_draw()

    def _editor_layer_mouse_released(self):
        p = self.view_editor.active_layer.edit_point_shape.edit_points[0]
        
        self.block_updates = True

        self.x_pos_spin.set_value(p.x)
        self.y_pos_spin.set_value(p.y)
        
        _titler_data.active_layer.x = p.x
        _titler_data.active_layer.y = p.y

        self.block_updates = False

    def _text_changed(self, widget):
        self._update_active_layout()

    def _position_value_changed(self, widget):
        # mouse release when layer is moved causes this method to be called,
        # but we don't want to do any additinal updates here for that event
        # This is only used when user presses arrows in position spins.
        if self.block_updates:
            return

        _titler_data.active_layer.x = self.x_pos_spin.get_value()
        _titler_data.active_layer.y = self.y_pos_spin.get_value()
        self._update_editor_layer_pos()
        self.view_editor.edit_area.queue_draw()

    def _edit_value_changed(self, widget):
        self._update_active_layout()

    def _update_active_layout(self, fill_layers_data_if_needed=True):
        if self.block_updates:
            return

        global _titler_data
        buf = self.text_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), include_hidden_chars=True)
        if text != _titler_data.active_layer.text:
            update_layers_list = True
        else:
            update_layers_list = False

        _titler_data.active_layer.text = text
        
        family = self.font_families[self.font_select.get_active()]
        _titler_data.active_layer.font_family = family.get_name()

        _titler_data.active_layer.font_size = self.size_spin.get_value_as_int()
        
        face = FACE_REGULAR
        if self.bold_font.get_active() and self.italic_font.get_active():
            face = FACE_BOLD_ITALIC
        elif self.italic_font.get_active():
            face = FACE_ITALIC
        elif self.bold_font.get_active():
            face = FACE_BOLD
        _titler_data.active_layer.font_face = face
        
        align = ALIGN_LEFT
        if self.center_align.get_active():
            align = ALIGN_CENTER
        elif  self.right_align.get_active():
             align = ALIGN_RIGHT
        _titler_data.active_layer.alignment = align

        color = self.color_button.get_color()
        r, g, b = utils.hex_to_rgb(color.to_string())
        new_color = (r/65535.0, g/65535.0, b/65535.0, 1.0)        
        _titler_data.active_layer.color_rgba = new_color
        _titler_data.active_layer.fill_on = self.fill_on.get_active()
        
        # OUTLINE
        color = self.out_line_color_button.get_color()
        r, g, b = utils.hex_to_rgb(color.to_string())
        new_color2 = (r/65535.0, g/65535.0, b/65535.0, 1.0)    
        _titler_data.active_layer.outline_color_rgba = new_color2
        _titler_data.active_layer.outline_on = self.outline_on.get_active()
        _titler_data.active_layer.outline_width = self.out_line_size_spin.get_value()

        
        # SHADOW
        color = self.shadow_color_button.get_color()
        r, g, b = utils.hex_to_rgb(color.to_string())
        a = self.shadow_opa_spin.get_value() / 100.0
        new_color3 = (r/65535.0, g/65535.0, b/65535.0)  
        _titler_data.active_layer.shadow_color_rgb = new_color3
        _titler_data.active_layer.shadow_on = self.shadow_on.get_active()
        _titler_data.active_layer.shadow_opacity = self.shadow_opa_spin.get_value()
        _titler_data.active_layer.shadow_xoff = self.shadow_xoff_spin.get_value()
        _titler_data.active_layer.shadow_yoff = self.shadow_yoff_spin.get_value()
                
        self.view_editor.active_layer.update_rect = True
        _titler_data.active_layer.update_pango_layout()

        # We only wnat to update layer list data model when this called after user typing 
        if update_layers_list:
            self.layer_list.fill_data_model()

        self.view_editor.edit_area.queue_draw()

    def _update_gui_with_active_layer_data(self):
        if _filling_layer_list:
            return
        
        # This a bit hackish, but works. Finding a method that blocks all
        # gui events from being added to queue would be nice.
        self.block_updates = True
        
        # TEXT
        layer = _titler_data.active_layer
        self.text_view.get_buffer().set_text(layer.text)

        r, g, b, a = layer.color_rgba
        button_color = Gdk.RGBA(r, g, b, 1.0)
        self.color_button.set_rgba(button_color)

        if FACE_REGULAR == layer.font_face:
            self.bold_font.set_active(False)
            self.italic_font.set_active(False)
        elif FACE_BOLD == layer.font_face:
            self.bold_font.set_active(True)
            self.italic_font.set_active(False)
        elif FACE_ITALIC == layer.font_face:
            self.bold_font.set_active(False)
            self.italic_font.set_active(True) 
        else:#FACE_BOLD_ITALIC
            self.bold_font.set_active(True)
            self.italic_font.set_active(True)

        if layer.alignment == ALIGN_LEFT:
            self.left_align.set_active(True)
        elif layer.alignment == ALIGN_CENTER:
            self.center_align.set_active(True)
        else:#ALIGN_RIGHT
            self.right_align.set_active(True)

        self.size_spin.set_value(layer.font_size)
        
        try:
            combo_index = self.font_family_indexes_for_name[layer.font_family]
            self.font_select.set_active(combo_index)
        except:# if font family not found we'll use first. This happens e.g at start-up if "Times New Roman" not in system.
            family = self.font_families[0]
            layer.font_family = family.get_name()
            self.font_select.set_active(0)

        self.x_pos_spin.set_value(layer.x)
        self.y_pos_spin.set_value(layer.y)
        self.rotation_spin.set_value(layer.angle)
        
        self.fill_on.set_active(layer.fill_on)
                
        # OUTLINE
        r, g, b, a = layer.outline_color_rgba
        button_color = Gdk.RGBA(r, g, b, 1.0)
        self.out_line_color_button.set_rgba(button_color)
        self.out_line_size_spin.set_value(layer.outline_width)
        self.outline_on.set_active(layer.outline_on)
        
        # SHADOW
        r, g, b = layer.shadow_color_rgb
        button_color = Gdk.RGBA(r, g, b, 1.0)
        self.shadow_color_button.set_rgba(button_color)
        self.shadow_opa_spin.set_value(layer.shadow_opacity)
        self.shadow_xoff_spin.set_value(layer.shadow_xoff)
        self.shadow_yoff_spin.set_value(layer.shadow_yoff)
        self.shadow_on.set_active(layer.shadow_on)
        
        self.block_updates = False



# --------------------------------------------------------- layer/s representation
class PangoTextLayout:
    """
    Object for drawing current active layer with Pango.
    
    Pixel size of layer can only be obtained when cairo context is available
    for drawing, so pixel size of layer is saved here.
    """
    def __init__(self, layer):
        self.load_layer_data(layer)
        
    def load_layer_data(self, layer): 
        self.text = layer.text
        self.font_desc = Pango.FontDescription(layer.get_font_desc_str())
        self.color_rgba = layer.color_rgba
        self.alignment = self._get_pango_alignment_for_layer(layer)
        self.pixel_size = layer.pixel_size
        self.fill_on = layer.fill_on
        
        self.outline_color_rgba = layer.outline_color_rgba
        self.outline_on = layer.outline_on
        self.outline_width = layer.outline_width

        self.shadow_on = layer.shadow_on
        self.shadow_color_rgb = layer.shadow_color_rgb
        self.shadow_opacity = layer.shadow_opacity
        self.shadow_xoff = layer.shadow_xoff
        self.shadow_yoff = layer.shadow_yoff

    # called from vieweditor draw vieweditor-> editorlayer->here
    def draw_layout(self, cr, x, y, rotation, xscale, yscale):
        cr.save()
        
        layout = PangoCairo.create_layout(cr)
        layout.set_text(self.text, -1)
        layout.set_font_description(self.font_desc)
        layout.set_alignment(self.alignment)
    
        self.pixel_size = layout.get_pixel_size()

        # Shadow
        if self.shadow_on:
            cr.save()
            r, g, b = self.shadow_color_rgb
            a = self.shadow_opacity / 100.0
            cr.set_source_rgba(r, g, b, a)
            cr.move_to(x + self.shadow_xoff, y + self.shadow_yoff)
            cr.scale(xscale, yscale)
            cr.rotate(rotation)
            PangoCairo.update_layout(cr, layout)
            PangoCairo.show_layout(cr, layout)
            cr.restore()
        
        # Text
        if self.fill_on:
            cr.set_source_rgba(*self.color_rgba)
            cr.move_to(x, y)
            cr.scale(xscale, yscale)
            cr.rotate(rotation)
            
            PangoCairo.update_layout(cr, layout)
            PangoCairo.show_layout(cr, layout)
        
        # Outline
        if self.outline_on:
            if self.fill_on == False: # case when user only wants outline we need to transform here
                cr.move_to(x, y)
                cr.scale(xscale, yscale)
                cr.rotate(rotation)
            PangoCairo.layout_path(cr, layout)
            cr.set_source_rgba(*self.outline_color_rgba)
            cr.set_line_width(self.outline_width)
            cr.stroke()
        
        cr.restore()

    def _get_pango_alignment_for_layer(self, layer):
        if layer.alignment == ALIGN_LEFT:
            return Pango.Alignment.LEFT
        elif layer.alignment == ALIGN_CENTER:
            return Pango.Alignment.CENTER
        else:
            return Pango.Alignment.RIGHT


class TextLayerListView(Gtk.VBox):

    def __init__(self, selection_changed_cb, layer_visible_toggled_cb):
        GObject.GObject.__init__(self)
        self.layer_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "text_layer.png")
        self.eye_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "eye.png")

        self.layer_visible_toggled_cb = layer_visible_toggled_cb

       # Datamodel: str
        self.storemodel = Gtk.ListStore(GdkPixbuf.Pixbuf, str, GdkPixbuf.Pixbuf)
 
        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

        # View
        self.treeview = Gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(False)
        self.treeview.connect("button-press-event", self.button_press)
        self.treeview.set_activate_on_single_click(True)
        self.treeview.connect("row-activated", selection_changed_cb)
         
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.SINGLE)
        #tree_sel.connect("changed", selection_changed_cb)

        # Cell renderers
        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", Pango.EllipsizeMode.END)
        self.text_rend_1.set_property("font", "Sans Bold 10")
        self.text_rend_1.set_fixed_height_from_font(1)

        self.icon_rend_1 = Gtk.CellRendererPixbuf()
        self.icon_rend_1.props.xpad = 6
        self.icon_rend_1.set_fixed_size(40, 40)

        self.icon_rend_2 = Gtk.CellRendererPixbuf()
        self.icon_rend_2.props.xpad = 2
        self.icon_rend_2.set_fixed_size(20, 40)

        # Column view
        self.icon_col_1 = Gtk.TreeViewColumn("layer_icon")
        self.text_col_1 = Gtk.TreeViewColumn("layer_text")
        self.icon_col_2 = Gtk.TreeViewColumn("eye_icon")
        
        # Build column views
        self.icon_col_1.set_expand(False)
        self.icon_col_1.set_spacing(5)
        self.icon_col_1.pack_start(self.icon_rend_1, True)
        self.icon_col_1.add_attribute(self.icon_rend_1, 'pixbuf', 0)

        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1, True)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 1)

        self.icon_col_2.set_expand(False)
        self.icon_col_2.set_spacing(5)
        self.icon_col_2.pack_start(self.icon_rend_2, True)
        self.icon_col_2.add_attribute(self.icon_rend_2, 'pixbuf', 2)

        # Add column views to view
        self.treeview.append_column(self.icon_col_1)
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.icon_col_2)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()

    def button_press(self, tree_view, event):
        if self.icon_col_1.get_width() + self.text_col_1.get_width() < event.x:
            path = self.treeview.get_path_at_pos(int(event.x), int(event.y))
            if path != None:
                self.layer_visible_toggled_cb(max(path[0]))

    def get_selected_row(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        try: # This has at times been called too often, but try may not be needed here anymore.
            return max(rows)[0]
        except:
            return -1

    def fill_data_model(self):
        """
        Creates displayed data.
        Displays icon, sequence name and sequence length
        """
        global _filling_layer_list
        _filling_layer_list = True
        self.storemodel.clear()
        for layer in _titler_data.layers:
            if layer.visible:
                visible_icon = self.eye_icon
            else:
                visible_icon = None 
            row_data = [self.layer_icon, layer.text, visible_icon]
            self.storemodel.append(row_data)
        
        self.scroll.queue_draw()
        _filling_layer_list = False


class OpenFileThread(threading.Thread):
    
    def __init__(self, filename, view_editor):
        threading.Thread.__init__(self)
        self.filename = filename
        self.view_editor = view_editor

    def run(self):
        # This makes sure that the file has been written to disk
        while(self.view_editor.write_out_layers == True):
            time.sleep(0.1)
        
        open_in_bin_thread = projectaction.AddMediaFilesThread([self.filename])
        open_in_bin_thread.start()
