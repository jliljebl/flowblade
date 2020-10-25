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

from gi.repository import Gtk, Gdk
from gi.repository import GLib, GObject

from editorstate import PLAYER
import editorstate
import gui
import guicomponents
import guiutils
import keyframeeditor
import propertyparse
import respaths
import utils
import vieweditor
import vieweditorlayer
import vieweditorshape

_rotomask = None

VIEW_EDITOR_WIDTH = 815
VIEW_EDITOR_HEIGHT = 620


# ------------------------------------------- module interface
def show_rotomask(mlt_filter, editable_properties, property_editor_widgets_create_func, value_labels):
    
    # Create custom keyframe editor for spline
    kf_json_prop = [ep for ep in editable_properties if ep.name == "spline"][0]
    kf_editor = keyframeeditor.RotoMaskKeyFrameEditor(kf_json_prop, propertyparse.rotomask_json_value_string_to_kf_array)

    # Use lambda to monkeypatch other editable properties to update rotomask on value write 
    invert_prop = [ep for ep in editable_properties if ep.name == "invert"][0]
    invert_prop.write_val_func = invert_prop.write_value
    invert_prop.write_value = lambda value_str: _write_val_and_update_editor(invert_prop, value_str)

    feather_prop = [ep for ep in editable_properties if ep.name == "feather"][0]
    feather_prop.write_val_func = feather_prop.write_value
    feather_prop.write_value = lambda value_str: _write_val_and_update_editor(feather_prop, value_str)
    
    feather_passes_prop = [ep for ep in editable_properties if ep.name == "feather_passes"][0]
    feather_passes_prop.write_val_func = feather_passes_prop.write_value
    feather_passes_prop.write_value = lambda value_str: _write_val_and_update_editor(feather_passes_prop, value_str)
    
    alpha_operation_prop = [ep for ep in editable_properties if ep.name == "alpha_operation"][0]
    alpha_operation_prop.write_val_func = alpha_operation_prop.write_value
    alpha_operation_prop.write_value = lambda value_str: _write_val_and_update_editor(alpha_operation_prop, value_str)

    mode_prop = [ep for ep in editable_properties if ep.name == "mode"][0]
    mode_prop.write_val_func = mode_prop.write_value
    mode_prop.write_value = lambda value_str: _write_val_and_update_editor(mode_prop, value_str)
    
    # Create editor window
    global _rotomask
    _rotomask = RotoMaskEditor(kf_editor, property_editor_widgets_create_func, value_labels)
    _rotomask.show_current_frame()

def close_rotomask():
    global _rotomask
    _rotomask.set_visible(False)
    GLib.idle_add(rotomask_destroy)

def rotomask_destroy():
    global _rotomask
    _rotomask.destroy()
    _rotomask = None
        
def _write_val_and_update_editor(ep, value_str):
    ep.write_val_func(value_str)    
    _rotomask.show_current_frame()
    
# ---------------------------------------------------------- editor
class RotoMaskEditor(Gtk.Window):
    def __init__(self, kf_editor, property_editor_widgets_create_func, value_labels): # kf_editor is keyframeeditor.RotoMaskKeyFrameEditor
        GObject.GObject.__init__(self)
        self.set_modal(True)
        self.set_transient_for(gui.editor_window.window)
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
        
        editor_widgets = property_editor_widgets_create_func()
        
        self.block_updates = False
        self.mask_create_freeze = False # We are not allowing user to change acrive kf when creating mask

        self.kf_editor = kf_editor
        self.kf_editor.set_parent_editor(self)

        # mask type param was added later, we need handle it not existing.
        if self.get_mask_type() == -1:
            self.set_mask_type(vieweditorshape.LINE_MASK)
            self.set_mask_type_on_init = False # but we don't want to destroy user's curve masks. THis is not complety back wards compatible stuff can get destroyed on second load.
        else:
            self.set_mask_type_on_init = True
            
        self.value_labels = value_labels
        
        self.view_editor = vieweditor.ViewEditor(PLAYER().profile, VIEW_EDITOR_WIDTH, VIEW_EDITOR_HEIGHT)
        self.view_editor.draw_safe_area = False

        self.tc_display = guicomponents.MonitorTCDisplay()
        self.tc_display.use_internal_frame = True
        self.tc_display.widget.set_valign(Gtk.Align.CENTER)

        kf_mode_img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "roto_kf_edit_mode.png")
        move_mode_img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "roto_move_mode.png")
        self.kf_mode_button = Gtk.ToggleButton()
        self.kf_mode_button.set_image(kf_mode_img)
        self.kf_mode_button.set_active(True) # we start with vieweditorlayer.ROTO_POINT_MODE edit mode
        self.kf_mode_button.connect("clicked", self._kf_mode_clicked)
        self.move_mode_button = Gtk.ToggleButton()
        self.move_mode_button.set_image(move_mode_img)
        self.move_mode_button.connect("clicked", self._move_mode_clicked)
        
        self.scale_selector = vieweditor.ScaleSelector(self)
        self.view_editor.scale_select = self.scale_selector

        timeline_box = Gtk.HBox()
        timeline_box.pack_start(self.tc_display.widget, False, False, 0)
        timeline_box.pack_start(Gtk.Label(), True, True, 0)
        timeline_box.pack_start(self.kf_mode_button, False, False, 0)
        timeline_box.pack_start(self.move_mode_button, False, False, 0)
        timeline_box.pack_start(Gtk.Label(), True, True, 0)
        timeline_box.pack_start(self.scale_selector, False, False, 0)
        timeline_box.set_margin_top(6)
        timeline_box.set_margin_bottom(6)

        mask_type_label = Gtk.Label(_("Mask Type:"))
        mask_type_combo_box = Gtk.ComboBoxText()
        mask_type_combo_box.append_text(_("Curve Mask"))
        mask_type_combo_box.append_text(_("Line Mask"))
        mask_type_combo_box.set_active(0)
        mask_type_combo_box.connect("changed", self.mask_type_selection_changed)  
        self.mask_type_combo_box = mask_type_combo_box
        
        allow_adding_check = Gtk.CheckButton()
        allow_adding_check.set_active(False) # This shows value of self.roto_mask_layer.allow_adding_points, False is default
        allow_adding_check.connect("toggled", self.allow_adding_toggled)
        allow_adding_label = Gtk.Label(_("Allow to add / delete points in closed masks"))
        
        save_rotodata_b = guiutils.get_sized_button(_("Close Tool"), 150, 32)
        save_rotodata_b.connect("clicked", lambda w:self._save_rotodata_pressed())
        
        prop_editor_row1 = Gtk.HBox()
        prop_editor_row1.pack_start(Gtk.Label(), True, True, 0)
        prop_editor_row1.pack_start(mask_type_label, False, False, 0)
        prop_editor_row1.pack_start(guiutils.pad_label(4, 4), False, False, 0)
        prop_editor_row1.pack_start(mask_type_combo_box, False, False, 0)
        prop_editor_row1.pack_start(guiutils.pad_label(24, 20), False, False, 0)
        prop_editor_row1.pack_start(editor_widgets[0], False, False, 0)
        prop_editor_row1.pack_start(guiutils.pad_label(24, 20), False, False, 0)
        prop_editor_row1.pack_start(editor_widgets[3], False, False, 0)
        prop_editor_row1.pack_start(guiutils.pad_label(24, 20), False, False, 0)
        prop_editor_row1.pack_start(editor_widgets[4], False, False, 0)
        prop_editor_row1.pack_start(Gtk.Label(), True, True, 0)
        
        prop_editor_row2 = Gtk.HBox()
        prop_editor_row2.pack_start(Gtk.Label(), True, True, 0)
        prop_editor_row2.pack_start(editor_widgets[1], False, False, 0)
        prop_editor_row2.pack_start(guiutils.pad_label(24, 20), False, False, 0)
        prop_editor_row2.pack_start(editor_widgets[2], False, False, 0)
        prop_editor_row2.pack_start(Gtk.Label(), True, True, 0)

        editor_buttons_row = Gtk.HBox()
        editor_buttons_row.pack_start(allow_adding_check, False, False, 0)
        editor_buttons_row.pack_start(guiutils.pad_label(4, 2), False, False, 0)
        editor_buttons_row.pack_start(allow_adding_label, False, False, 0)
        editor_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        editor_buttons_row.pack_start(save_rotodata_b, False, False, 0)
        
        editor_panel = Gtk.VBox()
        editor_panel.pack_start(self.view_editor, True, True, 0)
        editor_panel.pack_start(timeline_box, False, False, 0)
        editor_panel.pack_start(kf_editor, False, False, 0)
        editor_panel.pack_start(guiutils.pad_label(2, 12), False, False, 0)
        editor_panel.pack_start(prop_editor_row1, False, False, 0)
        editor_panel.pack_start(guiutils.pad_label(2, 12), False, False, 0)
        editor_panel.pack_start(prop_editor_row2, False, False, 0)
        editor_panel.pack_start(guiutils.pad_label(2, 12), False, False, 0)
        editor_panel.pack_start(editor_buttons_row, False, False, 0)

        editor_row = Gtk.HBox()
        editor_row.pack_start(editor_panel, True, True, 0)

        alignment = guiutils.set_margins(editor_row, 8,8,8,8)

        self.add(alignment)

        self.view_editor.clear_layers()
        # NOTE: we start with vieweditorlayer.ROTO_POINT_MODE edit mode, see __init()__
        self.roto_mask_layer = vieweditorlayer.RotoMaskEditLayer(self.view_editor, self.kf_editor.clip_editor, kf_editor.editable_property, self)
        self.view_editor.add_layer(self.roto_mask_layer)
        self.view_editor.activate_layer(0)

        self.show_all()
        
        self.kf_editor.active_keyframe_changed()

        self.connect("size-allocate", lambda w, e:self.window_resized())
        self.connect("window-state-event", lambda w, e:self.window_resized())
        self.connect("key-press-event", self.key_down)
        self.window_resized()

        self.kf_editor.clip_editor.maybe_set_first_kf_in_clip_area_active()

        self.update_mask_create_freeze_gui()

    def mask_type_selection_changed(self, combo_box):
        if combo_box.get_active() == 0:
            self.roto_mask_layer.edit_point_shape.set_mask_type(vieweditorshape.CURVE_MASK)
            self.set_mask_type(vieweditorshape.CURVE_MASK)
        else:
            self.roto_mask_layer.edit_point_shape.set_mask_type(vieweditorshape.LINE_MASK)
            self.set_mask_type(vieweditorshape.LINE_MASK)

        self.roto_mask_layer.edit_point_shape.convert_shape_coords_and_update_clip_editor_keyframes()
        self.roto_mask_layer.editable_property.write_out_keyframes(self.roto_mask_layer.edit_point_shape.clip_editor.keyframes)
        
        self.show_current_frame()

    def allow_adding_toggled(self, check_box):
        self.roto_mask_layer.allow_adding_points = check_box.get_active()

    def get_mask_type(self):
        try:
            rotomask_filter = self.kf_editor.editable_property._get_filter_object()
            name, val, param_type = rotomask_filter.non_mlt_properties[0]
            return int(val)
        except:
            return -1

    def set_mask_type(self, mask_type):
        rotomask_filter = self.kf_editor.editable_property._get_filter_object()
        if self.get_mask_type() != -1: # for older project types, this param was added later and we need to handle case that is does not exist.
            rotomask_filter.non_mlt_properties.pop(0)
        rotomask_filter.non_mlt_properties.append(("mask_type", mask_type, 0))
        
    def update_view(self):
        # Callback from kf_editor
        self.show_current_frame()

    def show_current_frame(self):
        tline_frame = PLAYER().current_frame()
        length = PLAYER().producer.get_length()
        rgbdata = PLAYER().seek_and_get_rgb_frame(tline_frame)
        self.view_editor.set_screen_rgb_data(rgbdata)
        self.view_editor.update_layers_for_frame(tline_frame)
        self.tc_display.set_frame(tline_frame)
        self.view_editor.edit_area.queue_draw()

    def window_resized(self):
        scale = self.scale_selector.get_current_scale()
        self.scale_changed(scale)

    def scale_changed(self, new_scale):
        self.view_editor.set_scale_and_update(new_scale)
        self.roto_mask_layer.edit_point_shape.update_shape()
        
        tline_frame = PLAYER().current_frame()
        self.view_editor.update_layers_for_frame(tline_frame)
        self.view_editor.edit_area.queue_draw()

    def update_effects_editor_value_labels(self):
        self.value_labels[0].set_text(str(len(self.kf_editor.clip_editor.keyframes)))
        kf, curve_points = self.kf_editor.clip_editor.keyframes[0] # We always have one
        self.value_labels[1].set_text(str(len(curve_points)))
    
    def _kf_mode_clicked(self, kf_button):
        if self.roto_mask_layer.edit_mode == vieweditorlayer.ROTO_POINT_MODE and kf_button.get_active() == False:
            kf_button.set_active(True) # we untoggled by clicking which is not allowed, untoggle happens whenthe other mode is selected. We set the untoggled button back to being active.
        elif  kf_button.get_active() == False:
            pass # this event is redundant, we always get two events when changing modes
        elif self.roto_mask_layer.edit_mode != vieweditorlayer.ROTO_POINT_MODE:
            self.roto_mask_layer.edit_mode = vieweditorlayer.ROTO_POINT_MODE
            self.move_mode_button.set_active(False)
    
    def _move_mode_clicked(self, move_button):
        if self.roto_mask_layer.edit_mode == vieweditorlayer.ROTO_MOVE_MODE and move_button.get_active() == False:
            move_button.set_active(True)  # we untoggled by clicking which is not allowed, untoggle happens whenthe other mode is selected. We set the untoggled button back to being active. 
        elif move_button.get_active() == False:
            pass # this event is redundant, we always get two events when changing modes
        elif self.roto_mask_layer.edit_mode != vieweditorlayer.ROTO_MOVE_MODE:
            self.roto_mask_layer.edit_mode = vieweditorlayer.ROTO_MOVE_MODE
            self.kf_mode_button.set_active(False)

    def position_listener(self, normalized_pos, length):
        frame = normalized_pos * length
        self.tc_display.set_frame(int(frame))

    def _save_rotodata_pressed(self):
        close_rotomask()

    def _prev_frame_pressed(self):
        PLAYER().seek_delta(-1)
        self.show_current_frame()

    def _next_frame_pressed(self):
        PLAYER().seek_delta(1)
        self.show_current_frame()

    def key_down(self, widget, event):
        #  Handle non-timeline delete 
        if event.keyval == Gdk.KEY_Delete:
            if self.roto_mask_layer.allow_adding_points == True: # allow_adding_points controls deleting too
                self.roto_mask_layer.delete_selected_point()
                return True
            
        if event.keyval == Gdk.KEY_Left:
            PLAYER().seek_delta(-1)
            tline_frame = PLAYER().current_frame()
            self.kf_editor.display_tline_frame(tline_frame)
            self.show_current_frame()
            return True

        if event.keyval == Gdk.KEY_Right:
            PLAYER().seek_delta(1)
            tline_frame = PLAYER().current_frame()
            self.kf_editor.display_tline_frame(tline_frame)
            self.show_current_frame()
            return True
            
        # Key event was not handled here.
        return False

    def update_mask_create_freeze_gui(self):
        if self.roto_mask_layer.edit_point_shape.closed == True:
            self.mask_create_freeze = False
            if self.set_mask_type_on_init == True:
                self.mask_type_combo_box.set_active(self.get_mask_type())
        else:
            self.mask_create_freeze = True

        self.kf_editor.set_editor_sensitive(not self.mask_create_freeze)
                
