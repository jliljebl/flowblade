
import ctypes
import gtk
import numpy as np
import struct
from PIL import Image

import cairoarea
import cairo

MIN_PAD = 20

class ViewEditor(gtk.Frame):

    def __init__(self, profile):
        gtk.Frame.__init__(self)
        self.scale = 1.0
        self.profile_w = profile.width()
        self.profile_h  = profile.height()
        self.scaled_screen_width = self.profile_w
        self.scales_screen_height = self.profile_h
        self.aspect_ratio = 1.0
        self.origo = (MIN_PAD, MIN_PAD)
        
        self.bg_buf = None
        self.write_out_layers = False

        self.edit_area = cairoarea.CairoDrawableArea(self.profile_w + MIN_PAD * 2, self.profile_h + MIN_PAD * 2, self._draw)
        self.edit_area.press_func = self._press_event
        self.edit_area.motion_notify_func = self._motion_notify_event
        self.edit_area.release_func = self._release_event
        
        self.scroll_window = gtk.ScrolledWindow()
        self.scroll_window.add_with_viewport(self.edit_area)
        self.scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll_window.show_all()
        self.scroll_window.set_size_request(self.profile_w + MIN_PAD * 2 + 2, self.profile_h + MIN_PAD * 2 + 2) # +2 to not show scrollbars
        self.add(self.scroll_window)

        self.edit_layers = []
        self.active_layer = None
        self.edit_target_layer = None

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
        if ((self.scaled_screen_width < scroll_w) and (self.scales_screen_height < scroll_h)):
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
        
        conv_mult = 1.0 / self.scale

        movie_x = conv_mult * panel_o_x
        movie_y = conv_mult * panel_o_y
        return (movie_x, movie_y)
    
    def movie_coord_to_panel_coord(self, movie_point):
        movie_x, movie_y = movie_point
        origo_x, origo_y = self.origo
        
        panel_x = movie_x * self.scale + origo_x
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
        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.rectangle(20, 20, 30, 10)
        cr.fill()

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
            x, y, w, h = allocation
            img_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
            cr = cairo.Context(img_surface)

        for editorlayer in self.edit_layers:
            editorlayer.draw(cr)
        
        if self.write_out_layers == True:
            img_surface.write_to_png("/home/janne/gfggfgf.png")
            self.write_out_layers = False
            
