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

import pygtk
pygtk.require('2.0');
import gtk

import numpy as np

import cairoarea
import cairo
import respaths

MIN_PAD = 20
GUIDES_COLOR = (0.5, 0.5, 0.5, 1.0)


class ViewEditor(gtk.Frame):

    def __init__(self, profile, scroll_width, scroll_height):
        gtk.Frame.__init__(self)
        self.scale = 1.0
        self.draw_overlays = True
        self.draw_safe_area = True
        self.has_safe_area = True
        self.profile_w = profile.width()
        self.profile_h = profile.height()
        self.aspect_ratio = float(profile.sample_aspect_num()) / profile.sample_aspect_den()
        self.scaled_screen_width = self.profile_w * self.aspect_ratio # scale is gonna be 1.0 here
        self.scaled_screen_height = self.profile_h
        self.origo = (MIN_PAD, MIN_PAD)

        self.bg_buf = None
        self.write_out_layers = False
        self.write_file_path = None

        self.edit_area = cairoarea.CairoDrawableArea(int(self.scaled_screen_width + MIN_PAD * 2), self.profile_h + MIN_PAD * 2, self._draw)
        self.edit_area.press_func = self._press_event
        self.edit_area.motion_notify_func = self._motion_notify_event
        self.edit_area.release_func = self._release_event
        
        self.scroll_window = gtk.ScrolledWindow()
        self.scroll_window.add_with_viewport(self.edit_area)
        self.scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll_window.show_all()
        self.scroll_window.set_size_request(scroll_width, scroll_height)  # +2 to not show scrollbars
        self.add(self.scroll_window)

        self.edit_layers = []
        self.active_layer = None
        self.edit_target_layer = None
        
        self.change_active_layer_for_hit = True
        self.active_layer_changed_listener = None # interface: listener(new_active_index)
                                                  # note: vieweditor calls activate_layer( ) when non-active layer hit
                                                  # here so listener needs only to change its active layer, not call activate_layer(  ) here

        self.set_scale_and_update(1.0)

    def write_layers_to_png(self, save_path):
        self.write_out_layers = True
        self.write_file_path = save_path
        self.edit_area.queue_draw()

    def activate_layer(self, layer_index):
        if self.active_layer != None:
            self.active_layer.active = False
        self.active_layer = self.edit_layers[layer_index]
        self.active_layer.active = True 

    def clear_layers(self):
        self.edit_layers = []
        self.active_layer = None
        self.edit_target_layer = None
    
    def add_layer(self, layer):
        self.edit_layers.append(layer)

    def set_scale_and_update(self, new_scale):
        self.scale = new_scale
        self.set_scaled_screen_size()
        self.set_edit_area_size_and_origo()

    def set_scaled_screen_size(self):
        self.scaled_screen_width = self.scale * self.profile_w * self.aspect_ratio
        self.scaled_screen_height = self.scale * self.profile_h

    def set_edit_area_size_and_origo(self):
        x, y, scroll_w, scroll_h = self.scroll_window.get_allocation()

        # If scaled screen smaller then scroll window size center it and set origo
        if ((self.scaled_screen_width < scroll_w) and (self.scaled_screen_height < scroll_h)):
            origo_x = (scroll_w - self.scaled_screen_width) / 2
            origo_y = (scroll_h - self.scaled_screen_height ) / 2
            self.origo = (int(origo_x), int(origo_y))
            self.edit_area.set_size_request(self.profile_w + MIN_PAD * 2, 
                                            self.profile_h + MIN_PAD * 2)
        else:
            if self.scaled_screen_width > scroll_w:
                new_w = self.scaled_screen_width + MIN_PAD * 2
                origo_x = MIN_PAD
            else:
                new_w = scroll_w
                origo_x = (scroll_w - self.scaled_screen_width) / 2
                
            if self.scaled_screen_height > scroll_h:
                new_h = self.scaled_screen_height + MIN_PAD * 2
                origo_y = MIN_PAD
            else:
                new_h = scroll_h
                origo_y = (scroll_h - self.scaled_screen_height) / 2
            
            self.origo = (int(origo_x), int(origo_y))
            self.edit_area.set_size_request(int(new_w), int(new_h))

    # ----------------------------------------------------- mouse events
    def _press_event(self, event):
        """
        Mouse press callback
        """
        self.edit_target_layer = None
        p = self.panel_coord_to_movie_coord((event.x, event.y))
        if self.active_layer.hit(p):
            self.edit_area.queue_draw()
            self.edit_target_layer = self.active_layer
            self.edit_target_layer.handle_mouse_press(p)
        else:
            if not self.change_active_layer_for_hit:
                return
            for i in range(len(self.edit_layers)):
                layer = self.edit_layers[i]
                if layer.hit(p):
                    self.active_layer_changed_listener(i)
                    self.activate_layer(i)
                    self.edit_area.queue_draw()
                    self.edit_target_layer = self.active_layer
                    self.edit_target_layer.handle_mouse_press(p)
            
    def _motion_notify_event(self, x, y, state):
        """
        Mouse drag callback
        """
        p = self.panel_coord_to_movie_coord((x, y))
        if self.edit_target_layer != None:
            self.edit_target_layer.handle_mouse_drag(p)
            self.edit_area.queue_draw()
        
    def _release_event(self, event):
        """
        Mouse release
        """
        p = self.panel_coord_to_movie_coord((event.x, event.y))
        if self.edit_target_layer != None:
            self.edit_target_layer.handle_mouse_release(p)
            self.edit_area.queue_draw()
        self.edit_target_layer = None
    
    # -------------------------------------------- coord conversions
    def panel_coord_to_movie_coord(self, panel_point):
        panel_x, panel_y = panel_point
        origo_x, origo_y = self.origo
        
        panel_o_x = panel_x - origo_x
        panel_o_y = panel_y - origo_y

        movie_x =  (1.0 / (self.scale * self.aspect_ratio)) * panel_o_x
        movie_y =  (1.0 / self.scale) * panel_o_y
        return (movie_x, movie_y)
    
    def movie_coord_to_panel_coord(self, movie_point):
        movie_x, movie_y = movie_point
        origo_x, origo_y = self.origo
        
        panel_x = movie_x * self.scale * self.aspect_ratio + origo_x
        panel_y = movie_y * self.scale + origo_y
        return (panel_x, panel_y)

    # --------------------------------------------------- drawing
    def set_screen_rgb_data(self, screen_rgb_data):
        buf = np.fromstring(screen_rgb_data, dtype=np.uint8)
        buf.shape = (self.profile_h + 1, self.profile_w, 4) # +1 in h, seemeed to need it
        out = np.copy(buf)
        r = np.index_exp[:, :, 0]
        b = np.index_exp[:, :, 2]
        out[r] = buf[b]
        out[b] = buf[r]
        self.bg_buf = out

    def _draw(self, event, cr, allocation):
        if self.bg_buf != None:
            # MLT Provides images in which R <-> B are swiched from what Cairo wants them,
            # so use numpy to switch them and to create a modifiable buffer for Cairo
            
            # Create cairo surface
            stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_RGB24, self.profile_w)
            surface = cairo.ImageSurface.create_for_data(self.bg_buf, cairo.FORMAT_RGB24, self.profile_w, self.profile_h, stride)
        
            # Display it
            ox, oy = self.origo
            cr.save()
            cr.translate(ox, oy)
            cr.scale(self.scale * self.aspect_ratio, self.scale)
            cr.set_source_surface(surface, 0, 0)
            cr.paint()
            cr.restore()
        
        if self.write_out_layers == True:
            # We need to go to 1.0 scale, 0,0 origo draw for out the file 
            current_scale = self.scale
            self.scale = 1.0
            self.origo = (0.0, 0.0)
            img_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.profile_w, self.profile_h)
            cr = cairo.Context(img_surface)

        for editorlayer in self.edit_layers:
            if editorlayer.visible:
                editorlayer.draw(cr, self.write_out_layers, self.draw_overlays)
        
        if self.write_out_layers == True:
            img_surface.write_to_png(self.write_file_path)
            self.write_file_path = None # to make sure user components set this every time
            self.write_out_layers = False
            self.set_scale_and_update(current_scale) # return to user set scale
        
        self._draw_guidelines(cr)
        
    def _draw_guidelines(self, cr):
        ox, oy = self.origo
        ox += 0.5
        oy += 0.5
        w = self.scaled_screen_width + ox
        h = self.scaled_screen_height + oy
        cr.move_to(ox, oy)
        cr.line_to(w, oy)
        cr.line_to(w, h)
        cr.line_to(ox, h)
        cr.close_path()
        cr.set_line_width(1.0)
        cr.set_source_rgba(*GUIDES_COLOR)
        cr.stroke()

        # Draw "safe" area, this is not based on any real specification
        if self.draw_safe_area == True and self.has_safe_area == True:
            dimensions_safe_mult = 0.9
            xin = ((w - ox) - ((w - ox) * dimensions_safe_mult)) / 2.0
            yin = ((h - oy) - ((h - oy) * dimensions_safe_mult)) / 2.0
            cr.move_to(ox + xin, oy + yin)
            cr.line_to(w - xin, oy + yin)
            cr.line_to(w - xin, h - yin)
            cr.line_to(ox + xin, h - yin)
            cr.close_path()
            cr.stroke()


class ScaleSelector(gtk.VBox):
    
    def __init__(self, listener):
        gtk.VBox.__init__(self)
        self.listener = listener # listerner needs to implement scale_changed(scale) interface
        self.scales = [0.25, 0.33, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0]
        combo = gtk.combo_box_new_text()
        for scale in self.scales:
            scale_str = str(int(100 * scale)) + "%"
            combo.append_text(scale_str)
        combo.set_active(2)
        combo.connect("changed", 
                      lambda w,e: self._scale_changed(w.get_active()), 
                      None)    
        self.add(combo)
        self.combo = combo

    def get_current_scale(self):
        return self.scales[self.combo.get_active()]

    def _scale_changed(self, scale_index):
        self.listener.scale_changed(self.scales[scale_index])


class GuidesViewToggle(gtk.ToggleButton):
    
    def __init__(self, view_editor):
        gtk.ToggleButton.__init__(self)
        icon = gtk.image_new_from_file(respaths.IMAGE_PATH + "guides_view_switch.png")
        self.set_image(icon)
        self.view_editor = view_editor
        
        self.set_active(True)
        self.connect("clicked",  lambda w:self._clicked())
 
    def _clicked(self):
        self.view_editor.draw_overlays = self.get_active()
        self.view_editor.draw_safe_area = self.get_active()
        self.view_editor.edit_area.queue_draw()
