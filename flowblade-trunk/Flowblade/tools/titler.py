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
import pygtk
pygtk.require('2.0');
import gtk
import glib

import os
import pango
import pangocairo
import pickle
import threading
import time

import toolsdialogs
from editorstate import PLAYER
from editorstate import PROJECT
import editorstate
import editorpersistance
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

_keep_titler_data = True
_open_saved_in_bin = True

VIEW_EDITOR_WIDTH = 815
VIEW_EDITOR_HEIGHT = 620

TEXT_LAYER_LIST_WIDTH = 300
TEXT_LAYER_LIST_HEIGHT = 250

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

    glib.idle_add(titler_destroy)

def titler_destroy():
    global _titler, _titler_data
    _titler.destroy()
    _titler = None

    if not _keep_titler_data:
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
        self.color_rgba = (1.0, 1.0, 1.0, 1.0) 
        self.alignment = ALIGN_LEFT
        self.pixel_size = (100, 100)
        self.spacing = 5
        self.pango_layout = None # PangoTextLayout(self)

        self.drop_shadow = None # future feature, here to keep file compat once added
        self.animation = None # future feature
        self.layer_attributes = None # future feature (kerning etc. go here, we're not using all pango features)
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
class Titler(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_title(_("Titler"))
        self.connect("delete-event", lambda w, e:close_titler())
        
        if editorstate.SCREEN_HEIGHT < 800:
            global TEXT_LAYER_LIST_HEIGHT, TEXT_VIEW_HEIGHT, VIEW_EDITOR_HEIGHT
            TEXT_LAYER_LIST_HEIGHT = 200
            TEXT_VIEW_HEIGHT = 225
            VIEW_EDITOR_HEIGHT = 550

        self.block_updates = False
        
        self.view_editor = vieweditor.ViewEditor(PLAYER().profile, VIEW_EDITOR_WIDTH, VIEW_EDITOR_HEIGHT)
        self.view_editor.active_layer_changed_listener = self.active_layer_changed
        
        self.guides_toggle = vieweditor.GuidesViewToggle(self.view_editor)
        
        add_b = gtk.Button(_("Add"))
        del_b = gtk.Button(_("Delete"))
        add_b.connect("clicked", lambda w:self._add_layer_pressed())
        del_b.connect("clicked", lambda w:self._del_layer_pressed())
        add_del_box = gtk.HBox()
        add_del_box = gtk.HBox(True,1)
        add_del_box.pack_start(add_b)
        add_del_box.pack_start(del_b)

        center_h_icon = gtk.image_new_from_file(respaths.IMAGE_PATH + "center_horizontal.png")
        center_v_icon = gtk.image_new_from_file(respaths.IMAGE_PATH + "center_vertical.png")
        center_h = gtk.Button()
        center_h.set_image(center_h_icon)
        center_h.connect("clicked", lambda w:self._center_h_pressed())
        center_v = gtk.Button()
        center_v.set_image(center_v_icon)
        center_v.connect("clicked", lambda w:self._center_v_pressed())

        self.layer_list = TextLayerListView(self._layer_selection_changed, self._layer_visibility_toggled)
        self.layer_list.set_size_request(TEXT_LAYER_LIST_WIDTH, TEXT_LAYER_LIST_HEIGHT)
    
        self.text_view = gtk.TextView()
        self.text_view.set_pixels_above_lines(2)
        self.text_view.set_left_margin(2)
        self.text_view.get_buffer().connect("changed", self._text_changed)

        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.sw.add(self.text_view)
        self.sw.set_size_request(TEXT_VIEW_WIDTH, TEXT_VIEW_HEIGHT)

        scroll_frame = gtk.Frame()
        scroll_frame.add(self.sw)
        
        self.tc_display = guicomponents.MonitorTCDisplay()
        self.tc_display.use_internal_frame = True
        
        self.pos_bar = positionbar.PositionBar()
        self.pos_bar.set_listener(self.position_listener)
        self.pos_bar.update_display_from_producer(PLAYER().producer)
        self.pos_bar.mouse_release_listener = self.pos_bar_mouse_released
        pos_bar_frame = gtk.Frame()
        pos_bar_frame.add(self.pos_bar.widget)
        pos_bar_frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        
        font_map = pangocairo.cairo_font_map_get_default()
        unsorted_families = font_map.list_families()
        if len(unsorted_families) == 0:
            print "No font families found in system! Titler will not work."
        self.font_families = sorted(unsorted_families, key=lambda family: family.get_name())
        self.font_family_indexes_for_name = {}
        combo = gtk.combo_box_new_text()
        indx = 0
        for family in self.font_families:
            combo.append_text(family.get_name())
            self.font_family_indexes_for_name[family.get_name()] = indx
            indx += 1
        combo.set_active(0)
        self.font_select = combo
        self.font_select.connect("changed", self._edit_value_changed)
    
        adj = gtk.Adjustment(float(DEFAULT_FONT_SIZE), float(1), float(300), float(1))
        self.size_spin = gtk.SpinButton(adj)
        self.size_spin.connect("changed", self._edit_value_changed)
        self.size_spin.connect("key-press-event", self._key_pressed_on_widget)

        font_main_row = gtk.HBox()
        font_main_row.pack_start(self.font_select, True, True, 0)
        font_main_row.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        font_main_row.pack_start(self.size_spin, False, False, 0)

        self.bold_font = gtk.ToggleButton()
        self.italic_font = gtk.ToggleButton()
        bold_icon = gtk.image_new_from_stock(gtk.STOCK_BOLD, 
                                       gtk.ICON_SIZE_BUTTON)
        italic_icon = gtk.image_new_from_stock(gtk.STOCK_ITALIC, 
                                       gtk.ICON_SIZE_BUTTON)
        self.bold_font.set_image(bold_icon)
        self.italic_font.set_image(italic_icon)
        self.bold_font.connect("clicked", self._edit_value_changed)
        self.italic_font.connect("clicked", self._edit_value_changed)
        
        self.left_align = gtk.RadioButton()
        self.center_align = gtk.RadioButton(self.left_align)
        self.right_align = gtk.RadioButton(self.left_align)
        left_icon = gtk.image_new_from_stock(gtk.STOCK_JUSTIFY_LEFT, 
                                       gtk.ICON_SIZE_BUTTON)
        center_icon = gtk.image_new_from_stock(gtk.STOCK_JUSTIFY_CENTER, 
                                       gtk.ICON_SIZE_BUTTON)
        right_icon = gtk.image_new_from_stock(gtk.STOCK_JUSTIFY_RIGHT, 
                                       gtk.ICON_SIZE_BUTTON)
        self.left_align.set_image(left_icon)
        self.center_align.set_image(center_icon)
        self.right_align.set_image(right_icon)
        self.left_align.set_mode(False)
        self.center_align.set_mode(False)
        self.right_align.set_mode(False)
        self.left_align.connect("clicked", self._edit_value_changed)
        self.center_align.connect("clicked", self._edit_value_changed)
        self.right_align.connect("clicked", self._edit_value_changed)
        
        self.color_button = gtk.ColorButton()
        self.color_button.connect("color-set", self._edit_value_changed)

        buttons_box = gtk.HBox()
        buttons_box.pack_start(gtk.Label(), True, True, 0)
        buttons_box.pack_start(self.bold_font, False, False, 0)
        buttons_box.pack_start(self.italic_font, False, False, 0)
        buttons_box.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        buttons_box.pack_start(self.left_align, False, False, 0)
        buttons_box.pack_start(self.center_align, False, False, 0)
        buttons_box.pack_start(self.right_align, False, False, 0)
        buttons_box.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        buttons_box.pack_start(self.color_button, False, False, 0)
        buttons_box.pack_start(gtk.Label(), True, True, 0)

        load_layers = gtk.Button(_("Load Layers"))
        load_layers.connect("clicked", lambda w:self._load_layers_pressed())
        save_layers = gtk.Button(_("Save Layers"))
        save_layers.connect("clicked", lambda w:self._save_layers_pressed())
        clear_layers = gtk.Button(_("Clear All"))
        clear_layers.connect("clicked", lambda w:self._clear_layers_pressed())

        layers_save_buttons_row = gtk.HBox()
        layers_save_buttons_row.pack_start(save_layers, False, False, 0)
        layers_save_buttons_row.pack_start(load_layers, False, False, 0)
        layers_save_buttons_row.pack_start(gtk.Label(), True, True, 0)
        #layers_save_buttons_row.pack_start(clear_layers, False, False, 0)
        
        adj = gtk.Adjustment(float(0), float(0), float(3000), float(1))
        self.x_pos_spin = gtk.SpinButton(adj)
        self.x_pos_spin.connect("changed", self._position_value_changed)
        self.x_pos_spin.connect("key-press-event", self._key_pressed_on_widget)
        adj = gtk.Adjustment(float(0), float(0), float(3000), float(1))
        self.y_pos_spin = gtk.SpinButton(adj)
        self.y_pos_spin.connect("changed", self._position_value_changed)
        self.y_pos_spin.connect("key-press-event", self._key_pressed_on_widget)
        adj = gtk.Adjustment(float(0), float(0), float(3000), float(1))
        self.rotation_spin = gtk.SpinButton(adj)
        self.rotation_spin.connect("changed", self._position_value_changed)
        self.rotation_spin.connect("key-press-event", self._key_pressed_on_widget)
        
        undo_pos = gtk.Button()
        undo_icon = gtk.image_new_from_stock(gtk.STOCK_UNDO, 
                                       gtk.ICON_SIZE_BUTTON)
        undo_pos.set_image(undo_icon)

        next_icon = gtk.image_new_from_file(respaths.IMAGE_PATH + "next_frame_s.png")
        prev_icon = gtk.image_new_from_file(respaths.IMAGE_PATH + "prev_frame_s.png")
        prev_frame = gtk.Button()
        prev_frame.set_image(prev_icon)
        prev_frame.connect("clicked", lambda w:self._prev_frame_pressed())
        next_frame = gtk.Button()
        next_frame.set_image(next_icon)
        next_frame.connect("clicked", lambda w:self._next_frame_pressed())

        self.scale_selector = vieweditor.ScaleSelector(self)

        timeline_box = gtk.HBox()
        timeline_box.pack_start(guiutils.get_in_centering_alignment(self.tc_display.widget), False, False, 0)
        timeline_box.pack_start(guiutils.get_in_centering_alignment(pos_bar_frame, 1.0), True, True, 0)
        timeline_box.pack_start(prev_frame, False, False, 0)
        timeline_box.pack_start(next_frame, False, False, 0)
        timeline_box.pack_start(self.guides_toggle, False, False, 0)
        timeline_box.pack_start(self.scale_selector, False, False, 0)
        
        positions_box = gtk.HBox()
        positions_box.pack_start(gtk.Label(), True, True, 0)
        positions_box.pack_start(gtk.Label("X:"), False, False, 0)
        positions_box.pack_start(self.x_pos_spin, False, False, 0)
        positions_box.pack_start(guiutils.pad_label(10, 5), False, False, 0)
        positions_box.pack_start(gtk.Label("Y:"), False, False, 0)
        positions_box.pack_start(self.y_pos_spin, False, False, 0)
        positions_box.pack_start(guiutils.pad_label(10, 5), False, False, 0)
        #positions_box.pack_start(gtk.Label(_("Angle")), False, False, 0)
        #positions_box.pack_start(self.rotation_spin, False, False, 0)
        positions_box.pack_start(guiutils.pad_label(10, 5), False, False, 0)
        positions_box.pack_start(center_h, False, False, 0)
        positions_box.pack_start(center_v, False, False, 0)
        positions_box.pack_start(gtk.Label(), True, True, 0)

        controls_panel_1 = gtk.VBox()
        controls_panel_1.pack_start(add_del_box, False, False, 0)
        controls_panel_1.pack_start(self.layer_list, False, False, 0)
        controls_panel_1.pack_start(layers_save_buttons_row, False, False, 0)

        controls_panel_2 = gtk.VBox()
        controls_panel_2.pack_start(scroll_frame, True, True, 0)
        controls_panel_2.pack_start(font_main_row, False, False, 0)
        controls_panel_2.pack_start(buttons_box, False, False, 0)
        
        controls_panel = gtk.VBox()
        controls_panel.pack_start(guiutils.get_named_frame(_("Active Layer"),controls_panel_2), True, True, 0)
        controls_panel.pack_start(guiutils.get_named_frame(_("Layers"),controls_panel_1), False, False, 0)
 
        view_editor_editor_buttons_row = gtk.HBox()
        view_editor_editor_buttons_row.pack_start(positions_box, False, False, 0)
        view_editor_editor_buttons_row.pack_start(gtk.Label(), True, True, 0)

        keep_label = gtk.Label(_("Keep Layers When Closed"))
        self.keep_layers_check = gtk.CheckButton()
        self.keep_layers_check.set_active(_keep_titler_data)
        self.keep_layers_check.connect("toggled", self._keep_layers_toggled)
        
        open_label = gtk.Label(_("Open Saved Title In Bin"))
        self.open_in_current_check = gtk.CheckButton()
        self.open_in_current_check.set_active(_open_saved_in_bin)
        self.open_in_current_check.connect("toggled", self._open_saved_in_bin)

        exit_b = guiutils.get_sized_button(_("Close"), 150, 32)
        exit_b.connect("clicked", lambda w:close_titler())
        save_titles_b = guiutils.get_sized_button(_("Save Title Graphic"), 150, 32)
        save_titles_b.connect("clicked", lambda w:self._save_title_pressed())
        
        editor_buttons_row = gtk.HBox()
        editor_buttons_row.pack_start(gtk.Label(), True, True, 0)
        editor_buttons_row.pack_start(keep_label, False, False, 0)
        editor_buttons_row.pack_start(self.keep_layers_check, False, False, 0)
        editor_buttons_row.pack_start(guiutils.pad_label(24, 2), False, False, 0)
        editor_buttons_row.pack_start(open_label, False, False, 0)
        editor_buttons_row.pack_start(self.open_in_current_check, False, False, 0)
        editor_buttons_row.pack_start(guiutils.pad_label(24, 2), False, False, 0)
        editor_buttons_row.pack_start(exit_b, False, False, 0)
        editor_buttons_row.pack_start(save_titles_b, False, False, 0)
        
        editor_panel = gtk.VBox()
        editor_panel.pack_start(self.view_editor, True, True, 0)
        editor_panel.pack_start(timeline_box, False, False, 0)
        editor_panel.pack_start(guiutils.get_in_centering_alignment(view_editor_editor_buttons_row), False, False, 0)
        editor_panel.pack_start(guiutils.pad_label(2, 24), False, False, 0)
        editor_panel.pack_start(editor_buttons_row, False, False, 0)

        editor_row = gtk.HBox()
        editor_row.pack_start(controls_panel, False, False, 0)
        editor_row.pack_start(editor_panel, True, True, 0)

        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(8,8,8,8)
        alignment.add(editor_row)
    
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
        toolsdialogs.save_titler_graphic_as_dialog(self._save_title_dialog_callback, "title.png", None)

    def _save_title_dialog_callback(self, dialog, response_id):
        if response_id == gtk.RESPONSE_ACCEPT:
            try:
                filenames = dialog.get_filenames()
                dialog.destroy()
                save_path = filenames[0]
                self.view_editor.write_layers_to_png(save_path)
        
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
        if response_id == gtk.RESPONSE_ACCEPT:
            filenames = dialog.get_filenames()
            save_path = filenames[0]
            _titler_data.save(save_path)
            dialog.destroy()
        else:
            dialog.destroy()
            
    def _load_layers_pressed(self):
        toolsdialogs.load_titler_data_dialog(self._load_layers_dialog_callback)
        
    def _load_layers_dialog_callback(self, dialog, response_id):
        if response_id == gtk.RESPONSE_ACCEPT:
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
        if widget == self.size_spin and event.keyval == gtk.keysyms.Return:
            self.size_spin.update()
            self._update_active_layout()
            return True

            # update layer for enter on x, y, angle
        if ((event.keyval == gtk.keysyms.Return) and ((widget == self.x_pos_spin) or
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

    def _layer_selection_changed(self, selection):
        selected_row = self.layer_list.get_selected_row()
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
        #self.rotation_spin = gtk.SpinButton(adj)
        
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

        self.view_editor.active_layer.update_rect = True
        _titler_data.active_layer.update_pango_layout()

        # We only wnat to update layer list data model when this called after user typing 
        if update_layers_list:
            self.layer_list.fill_data_model()

        self.view_editor.edit_area.queue_draw()

    def _update_gui_with_active_layer_data(self):
        # This a bit hackish, but works. Finding a method that blocks all
        # gui events from being added to queue would be nice.
        self.block_updates = True
        
        layer = _titler_data.active_layer
        
        self.text_view.get_buffer().set_text(layer.text)
        
        r, g, b, a = layer.color_rgba
        button_color = gtk.gdk.Color(red=r,
                                     green=g,
                                     blue=b)
        self.color_button.set_color(button_color)

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
        self.font_desc = pango.FontDescription(layer.get_font_desc_str())
        self.color_rgba = layer.color_rgba
        self.alignment = self._get_pango_alignment_for_layer(layer)
        self.pixel_size = layer.pixel_size
    
    # called from vieweditor draw vieweditor-> editorlayer->here
    def draw_layout(self, cr, x, y, rotation, xscale, yscale):
        cr.save()
        
        pango_context = pangocairo.CairoContext(cr)
        layout = pango_context.create_layout()
        layout.set_text(self.text)
        layout.set_font_description(self.font_desc)
        layout.set_alignment(self.alignment)
        self.pixel_size = layout.get_pixel_size()
        pango_context.set_source_rgba(*self.color_rgba)
        pango_context.move_to(x, y)
        pango_context.scale( xscale, yscale)
        pango_context.rotate(rotation)
        pango_context.update_layout(layout)
        pango_context.show_layout(layout)

        cr.restore()

    def _get_pango_alignment_for_layer(self, layer):
        if layer.alignment == ALIGN_LEFT:
            return pango.ALIGN_LEFT
        elif layer.alignment == ALIGN_CENTER:
            return pango.ALIGN_CENTER
        else:
            return pango.ALIGN_RIGHT


class TextLayerListView(gtk.VBox):

    def __init__(self, selection_changed_cb, layer_visible_toggled_cb):
        gtk.VBox.__init__(self)
        self.layer_icon = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "text_layer.png")
        self.eye_icon = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "eye.png")

        self.layer_visible_toggled_cb = layer_visible_toggled_cb

       # Datamodel: str
        self.storemodel = gtk.ListStore(gtk.gdk.Pixbuf, str, gtk.gdk.Pixbuf)
 
        # Scroll container
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # View
        self.treeview = gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(False)
        self.treeview.connect("button-press-event", self.button_press)
        
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(gtk.SELECTION_SINGLE)
        tree_sel.connect("changed", selection_changed_cb)

        # Cell renderers
        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.text_rend_1.set_property("font", "Sans Bold 10")
        self.text_rend_1.set_fixed_height_from_font(1)

        self.icon_rend_1 = gtk.CellRendererPixbuf()
        self.icon_rend_1.props.xpad = 6
        self.icon_rend_1.set_fixed_size(40, 40)

        self.icon_rend_2 = gtk.CellRendererPixbuf()
        self.icon_rend_2.props.xpad = 2
        self.icon_rend_2.set_fixed_size(20, 40)

        # Column view
        self.icon_col_1 = gtk.TreeViewColumn("layer_icon")
        self.text_col_1 = gtk.TreeViewColumn("layer_text")
        self.icon_col_2 = gtk.TreeViewColumn("eye_icon")
        
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

    def button_press(self, tree_view, event):
        if self.icon_col_1.get_width() + self.text_col_1.get_width() < event.x:
            path = self.treeview.get_path_at_pos(int(event.x), int(event.y))
            if path != None:
                self.layer_visible_toggled_cb(max(path[0]))

    def get_selected_row(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        # When listening to "changed" this gets called too often for our needs (namely when user types),
        # but "row-activated" would activate layer changes only with double clicks, do we'll send -1 when this
        # is called and active layer is not actually changed. 
        try:
            return max(rows)[0]
        except:
            return -1

    def fill_data_model(self):
        """
        Creates displayed data.
        Displays icon, sequence name and sequence length
        """
        self.storemodel.clear()
        for layer in _titler_data.layers:
            if layer.visible:
                visible_icon = self.eye_icon
            else:
                visible_icon = None 
            row_data = [self.layer_icon, layer.text, visible_icon]
            self.storemodel.append(row_data)
        
        self.scroll.queue_draw()


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
