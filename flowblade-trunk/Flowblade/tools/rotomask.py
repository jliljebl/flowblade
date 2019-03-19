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


# ------------------------------------------- module interface
def show_rotomask(mlt_filter, editable_properties):
    
    kf_json_prop = filter(lambda ep: ep.name == "spline", editable_properties)[0]
    kf_editor = keyframeeditor.RotoMaskKeyFrameEditor(kf_json_prop, propertyparse.rotomask_json_value_string_to_kf_array)
        
    global _rotomask
    _rotomask = RotoMaskEditor(kf_editor)
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
    def __init__(self, kf_editor): # kf_editor is keyframeeditor.RotoMaskKeyFrameEditor
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
        
        self.guides_toggle = vieweditor.GuidesViewToggle(self.view_editor)
        
        add_b = Gtk.Button(_("Add"))
        del_b = Gtk.Button(_("Delete"))
        add_b.connect("clicked", lambda w:self._add_layer_pressed())
        del_b.connect("clicked", lambda w:self._del_layer_pressed())
        add_del_box = Gtk.HBox()
        add_del_box = Gtk.HBox(True,1)
        add_del_box.pack_start(add_b, True, True, 0)
        add_del_box.pack_start(del_b, True, True, 0)

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

        timeline_box = Gtk.HBox()
        timeline_box.pack_start(self.tc_display.widget, False, False, 0)
        timeline_box.pack_start(Gtk.Label(), True, True, 0)
        timeline_box.pack_start(self.kf_mode_button, False, False, 0)
        timeline_box.pack_start(self.move_mode_button, False, False, 0)
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
        editor_panel.pack_start(timeline_box, False, False, 0)
        editor_panel.pack_start(kf_editor, False, False, 0)
        editor_panel.pack_start(guiutils.pad_label(2, 12), True, True, 0)
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
        tline_frame = PLAYER().current_frame()
        self.view_editor.update_layers_for_frame(tline_frame)
        self.view_editor.edit_area.queue_draw()


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
        pass

    def _prev_frame_pressed(self):
        PLAYER().seek_delta(-1)
        self.show_current_frame()

    def _next_frame_pressed(self):
        PLAYER().seek_delta(1)
        self.show_current_frame()

    def key_down(self, widget, event):
        #  Handle non-timeline delete 
        if event.keyval == Gdk.KEY_Delete:
            self.roto_mask_layer.delete_selected_point()
            return True

        # Key event was not handled here.
        return False
