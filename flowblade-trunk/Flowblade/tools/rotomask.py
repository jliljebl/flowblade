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
import keyframeeditor
import projectaction
import propertyparse
import respaths
import positionbar
import utils
import vieweditor
import vieweditorlayer

_rotomask = None

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

def show_rotomask(mlt_filter, editable_properties):
    
    kf_json_prop = filter(lambda ep: ep.name == "spline", editable_properties)[0]
    kf_editor = keyframeeditor.RotoMaskKeyFrameEditor(kf_json_prop, propertyparse.rotomask_json_value_string_to_kf_array)
        
    global _rotomask
    _rotomask = RotoMaskEditor(kf_editor)
    #_rotomask.load_titler_data()
    _rotomask.show_current_frame()

def close_rotomask():
    global _rotomask
    _rotomask.set_visible(False)
    GLib.idle_add(rotomask_destroy)

def rotomask_destroy():
    global _rotomask
    _rotomask.destroy()
    _rotomask = None
        
            
# ---------------------------------------------------------- editor
class RotoMaskEditor(Gtk.Window):
    def __init__(self, kf_editor):
        GObject.GObject.__init__(self)
        self.set_title(_("RotoMaskEditor"))
        self.connect("delete-event", lambda w, e:close_rotomask())
        
        if editorstate.screen_size_small_height() == True:
            global TEXT_LAYER_LIST_HEIGHT, TEXT_VIEW_HEIGHT, VIEW_EDITOR_HEIGHT
            TEXT_LAYER_LIST_HEIGHT = 150
            TEXT_VIEW_HEIGHT = 180
            VIEW_EDITOR_HEIGHT = 450

        if editorstate.screen_size_small_height() == True:
            global VIEW_EDITOR_WIDTH
            VIEW_EDITOR_WIDTH = 680
            
        self.block_updates = False
        
        self.kf_editor = kf_editor
        self.kf_editor.set_parent_editor(self)
        
        self.view_editor = vieweditor.ViewEditor(PLAYER().profile, VIEW_EDITOR_WIDTH, VIEW_EDITOR_HEIGHT)
        #self.view_editor.active_layer_changed_listener = self.active_layer_changed
        
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

        self.tc_display = guicomponents.MonitorTCDisplay()
        self.tc_display.use_internal_frame = True
        self.tc_display.widget.set_valign(Gtk.Align.CENTER)


        self.scale_selector = vieweditor.ScaleSelector(self)

        timeline_box = Gtk.HBox()
        timeline_box.pack_start(self.tc_display.widget, False, False, 0)
        timeline_box.pack_start(Gtk.Label(), True, True, 0)
        timeline_box.pack_start(self.scale_selector, False, False, 0)
        timeline_box.set_margin_top(6)
        timeline_box.set_margin_bottom(6)

        exit_b = guiutils.get_sized_button(_("Cancel Edit"), 150, 32)
        exit_b.connect("clicked", lambda w:close_rotomask())
        save_rotodata_b = guiutils.get_sized_button(_("Save Rotomask Data"), 150, 32)
        save_rotodata_b.connect("clicked", lambda w:self._save_rotodata_pressed())
        
        editor_buttons_row = Gtk.HBox()
        editor_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        editor_buttons_row.pack_start(guiutils.pad_label(24, 2), False, False, 0)
        editor_buttons_row.pack_start(guiutils.pad_label(24, 2), False, False, 0)
        editor_buttons_row.pack_start(exit_b, False, False, 0)
        editor_buttons_row.pack_start(save_rotodata_b, False, False, 0)
        
        editor_panel = Gtk.VBox()
        editor_panel.pack_start(self.view_editor, True, True, 0)
        editor_panel.pack_start(kf_editor, False, False, 0)
        editor_panel.pack_start(timeline_box, False, False, 0)
        editor_panel.pack_start(guiutils.pad_label(2, 24), True, True, 0)
        editor_panel.pack_start(editor_buttons_row, False, False, 0)

        editor_row = Gtk.HBox()
        editor_row.pack_start(editor_panel, True, True, 0)

        alignment = guiutils.set_margins(editor_row, 8,8,8,8)

        self.add(alignment)

        self.view_editor.clear_layers()
        self.roto_mask_layer = vieweditorlayer.RotoMaskEditLayer(self.view_editor, self.kf_editor.clip_editor)
        self.view_editor.add_layer(self.roto_mask_layer)
        self.view_editor.activate_layer(0)

        self.show_all()
        
        self.kf_editor.active_keyframe_changed()

        self.connect("size-allocate", lambda w, e:self.window_resized())
        self.connect("window-state-event", lambda w, e:self.window_resized())

        self.window_resized()
                
    def update_view(self):
        # Callback from kf_editor
        self.show_current_frame()

    def show_current_frame(self):
        frame = PLAYER().current_frame()
        length = PLAYER().producer.get_length()
        rgbdata = PLAYER().seek_and_get_rgb_frame(frame)
        self.view_editor.set_screen_rgb_data(rgbdata)
        self.view_editor.update_layers_for_frame(frame)
        self.tc_display.set_frame(frame)
        self._update_active_layout()

    def window_resized(self):
        scale = self.scale_selector.get_current_scale()
        self.scale_changed(scale)

    def scale_changed(self, new_scale):
        self.view_editor.set_scale_and_update(new_scale)
        frame = PLAYER().current_frame()
        self.view_editor.update_layers_for_frame(frame)
        self.view_editor.edit_area.queue_draw()


        
    """ REMOVE
    def write_current_frame(self):
        self.view_editor.write_out_layers = True
        self.show_current_frame()
    """
    def position_listener(self, normalized_pos, length):
        frame = normalized_pos * length
        self.tc_display.set_frame(int(frame))

    def _save_rotodata_pressed(self):
        pass
        # pasas



    def _clear_layers_pressed(self):
        # INFOWINDOW
        # CONFIRM WINDOW HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        global _titler_data
        _titler_data = TitlerData()
        self.load_titler_data()


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

    """
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
    """

    def _prev_frame_pressed(self):
        PLAYER().seek_delta(-1)
        self.show_current_frame()

    def _next_frame_pressed(self):
        PLAYER().seek_delta(1)
        self.show_current_frame()


    def _editor_layer_mouse_released(self):
        p = self.view_editor.active_layer.edit_point_shape.edit_points[0]
        
        """
        self.block_updates = True

        self.x_pos_spin.set_value(p.x)
        self.y_pos_spin.set_value(p.y)
        
        _titler_data.active_layer.x = p.x
        _titler_data.active_layer.y = p.y

        self.block_updates = False
        """


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
        self.view_editor.edit_area.queue_draw()
        pass
        """
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
        """

