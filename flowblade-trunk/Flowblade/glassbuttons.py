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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

import cairo
import pygtk
pygtk.require('2.0');
import gtk

import math

from cairoarea import CairoDrawableArea
import editorpersistance
import gui
import respaths

BUTTONS_GRAD_STOPS = [   (1, 1, 1, 1, 0.2),
                        (0.8, 1, 1, 1, 0),
                        (0.51, 1, 1, 1, 0),
                        (0.50, 1, 1, 1, 0.25),
                        (0, 1, 1, 1, 0.4)]

BUTTONS_PRESSED_GRAD_STOPS = [(1, 0.7, 0.7, 0.7, 1),
                             (0, 0.5, 0.5, 0.5, 1)]
                             
LINE_GRAD_STOPS = [ (1, 0.66, 0.66, 0.66, 1),
                            (0.95, 0.7, 0.7, 0.7, 1),
                            (0.65, 0.3, 0.3, 0.3, 1),
                            (0, 0.64, 0.64, 0.64, 1)]

BUTTON_NOT_SENSITIVE_GRAD_STOPS = [(1, 0.9, 0.9, 0.9, 0.7),
                                    (0, 0.9, 0.9, 0.9, 0.7)]

CORNER_DIVIDER = 5

MB_BUTTONS_WIDTH = 317
MB_BUTTONS_HEIGHT = 30
MB_BUTTON_HEIGHT = 22
MB_BUTTON_WIDTH = 35
MB_BUTTON_Y = 4
MB_BUTTON_IMAGE_Y = 6

M_PI = math.pi

NO_HIT = -1

# Focus groups are used to test if one widget in the group of buttons widgets has keyboard focus
DEFAULT_FOCUS_GROUP = "default_focus_group"
focus_groups = {DEFAULT_FOCUS_GROUP:[]}


class AbstractGlassButtons:

    def __init__(self, button_width, button_height, button_y, widget_width, widget_height):
        # Create widget and connect listeners
        self.widget = CairoDrawableArea(widget_width, 
                                        widget_height, 
                                        self._draw)
        self.widget.press_func = self._press_event
        self.widget.motion_notify_func = self._motion_notify_event
        self.widget.release_func = self._release_event

        self.pressed_callback_funcs = None # set later
        self.released_callback_funcs = None # set later

        self.pressed_button = -1

        self.degrees = M_PI / 180.0

        self.button_width = button_width
        self.button_height = button_height
        self.button_y = button_y
        self.button_x = 0 # set when first allocation known by extending class

        self.icons = []
        self.image_x = []
        self.image_y = []
        self.sensitive = []
        
        if editorpersistance.prefs.buttons_style == editorpersistance.GLASS_STYLE:
            self.glass_style = True
        else:
            self.glass_style = False
        
        # Dark theme comes with flat buttons
        self.dark_theme = False
        if editorpersistance.prefs.dark_theme == True:
            self.glass_style = False
            self.dark_theme = True

        self.draw_button_gradients = True # set False at object creation site to kill all gradients

    def _set_button_draw_consts(self, x, y, width, height):
        aspect = 1.0
        corner_radius = height / CORNER_DIVIDER
        radius = corner_radius / aspect

        self._draw_consts = (x, y, width, height, aspect, corner_radius, radius)
    
    def set_sensitive(self, value):
        self.sensitive = []
        for i in self.icons:
            self.sensitive.append(value)

    def _round_rect_path(self, cr):
        x, y, width, height, aspect, corner_radius, radius = self._draw_consts
        degrees = self.degrees

        cr.new_sub_path()
        cr.arc (x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc (x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc (x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc (x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path ()

    def _press_event(self, event):
        print "_press_event not impl"

    def _motion_notify_event(self, x, y, state):
        print "_motion_notify_event not impl"

    def _release_event(self, event):
        print "_release_event not impl"

    def _draw(self, event, cr, allocation):
        print "_draw not impl"

    def _get_hit_code(self, x, y):
        button_x = self.button_x
        for i in range(0, len(self.icons)):
            if ((x >= button_x) and (x <= button_x + self.button_width)
                and (y >= self.button_y) and (y <= self.button_y + self.button_height)):
                    if self.sensitive[i] == True:
                        return i 
            button_x += self.button_width

        return NO_HIT
        
    def _draw_buttons(self, cr, w, h):
        # Width of buttons group
        buttons_width = self.button_width * len(self.icons)

        # Draw bg
        cr.set_source_rgb(*gui.bg_color_tuple)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # Line width for all strokes
        cr.set_line_width(1.0)

        # bg 
        self._set_button_draw_consts(self.button_x + 0.5, self.button_y + 0.5, buttons_width, self.button_height + 1.0)
        self._round_rect_path(cr)
        r, g, b = gui.bg_color_tuple
        if self.draw_button_gradients:
            if self.glass_style == True:
                cr.set_source_rgb(0.75, 0.75, 0.75)#*gui.bg_color_tuple)#0.75, 0.75, 0.75)
                cr.fill_preserve()
            else:
                grad = cairo.LinearGradient (self.button_x, self.button_y, self.button_x, self.button_y + self.button_height)
                if self.dark_theme == False:
                    grad.add_color_stop_rgba(1, r - 0.1, g - 0.1, b - 0.1, 1)
                    grad.add_color_stop_rgba(0, r + 0.1, g + 0.1, b + 0.1, 1)
                else:
                    grad.add_color_stop_rgba(1, r + 0.04, g + 0.04, b + 0.04, 1)
                    grad.add_color_stop_rgba(0, r + 0.07, g + 0.07, b + 0.07, 1)

                cr.set_source(grad)
                cr.fill_preserve()

        # Pressed button gradient
        if self.pressed_button > -1:
            if self.draw_button_gradients:
                grad = cairo.LinearGradient (self.button_x, self.button_y, self.button_x, self.button_y + self.button_height)
                if self.glass_style == True:
                    for stop in BUTTONS_PRESSED_GRAD_STOPS:
                        grad.add_color_stop_rgba(*stop)
                else:
                    grad = cairo.LinearGradient (self.button_x, self.button_y, self.button_x, self.button_y + self.button_height)
                    grad.add_color_stop_rgba(1, r - 0.3, g - 0.3, b - 0.3, 1)
                    grad.add_color_stop_rgba(0, r - 0.1, g - 0.1, b - 0.1, 1)
            else:
                    grad = cairo.LinearGradient (self.button_x, self.button_y, self.button_x, self.button_y + self.button_height)
                    grad.add_color_stop_rgba(1, r - 0.3, g - 0.3, b - 0.3, 1)
                    grad.add_color_stop_rgba(0, r - 0.3, g - 0.3, b - 0.3, 1)
            cr.save()
            cr.set_source(grad)
            cr.clip()
            cr.rectangle(self.button_x + self.pressed_button * self.button_width, self.button_y, self.button_width, self.button_height)
            cr.fill()
            cr.restore()

        # Icons and sensitive gradient
        grad = cairo.LinearGradient (self.button_x, self.button_y, self.button_x, self.button_y + self.button_height)
        for stop in BUTTON_NOT_SENSITIVE_GRAD_STOPS:
            grad.add_color_stop_rgba(*stop)
        x = self.button_x
        for i in range(0, len(self.icons)):
            icon = self.icons[i]
            cr.set_source_pixbuf(icon, x + self.image_x[i], self.image_y[i])
            cr.paint()
            if self.sensitive[i] == False:
                cr.save()
                self._round_rect_path(cr)
                cr.set_source(grad)
                cr.clip()
                cr.rectangle(x, self.button_y, self.button_width, self.button_height)
                cr.fill()
                cr.restore()
            x += self.button_width

        if self.glass_style == True and self.draw_button_gradients:
            # Glass gradient
            self._round_rect_path(cr)
            grad = cairo.LinearGradient (self.button_x, self.button_y, self.button_x, self.button_y + self.button_height)
            for stop in BUTTONS_GRAD_STOPS:
                grad.add_color_stop_rgba(*stop)
            cr.set_source(grad)
            cr.fill()
        else:
            pass

        if self.dark_theme != True:
            # Round line
            grad = cairo.LinearGradient (self.button_x, self.button_y, self.button_x, self.button_y + self.button_height)
            for stop in LINE_GRAD_STOPS:
                grad.add_color_stop_rgba(*stop)
            cr.set_source(grad)
            self._set_button_draw_consts(self.button_x + 0.5, self.button_y + 0.5, buttons_width, self.button_height)
            self._round_rect_path(cr)
            cr.stroke()

        if self.dark_theme == True:
            cr.set_source_rgb(*gui.bg_color_tuple)

        # Vert lines
        x = self.button_x
        for i in range(0, len(self.icons)):
            if (i > 0) and (i < len(self.icons)):
                cr.move_to(x + 0.5, self.button_y)
                cr.line_to(x + 0.5, self.button_y + self.button_height)
                cr.stroke()
            x += self.button_width

        
class PlayerButtons(AbstractGlassButtons):

    def __init__(self):

        AbstractGlassButtons.__init__(self, MB_BUTTON_WIDTH, MB_BUTTON_HEIGHT, MB_BUTTON_Y, MB_BUTTONS_WIDTH, MB_BUTTONS_HEIGHT)

        IMG_PATH = respaths.IMAGE_PATH
        play_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "play_2_s.png")
        stop_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "stop_s.png")
        next_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "next_frame_s.png")
        prev_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "prev_frame_s.png")
        mark_in_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "mark_in_s.png")
        mark_out_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "mark_out_s.png")
        marks_clear_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "marks_clear_s.png") 
        to_mark_in_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "to_mark_in_s.png")        
        to_mark_out_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "to_mark_out_s.png") 

        self.icons = [prev_icon, next_icon, play_icon, stop_icon, 
                      mark_in_icon, mark_out_icon, 
                      marks_clear_icon, to_mark_in_icon, to_mark_out_icon]
        self.image_x = [8, 10, 13, 13, 6, 14, 5, 10, 9]

        for i in range(0, len(self.icons)):
            self.image_y.append(MB_BUTTON_IMAGE_Y)

        self.pressed_callback_funcs = None # set using set_callbacks()

        self.set_sensitive(True)
        
        focus_groups[DEFAULT_FOCUS_GROUP].append(self.widget)

    def set_trim_sensitive_pattern(self):
        self.sensitive = [True, True, True, True, False, False, False, False, False]
        self.widget.queue_draw()

    def set_normal_sensitive_pattern(self):
        self.set_sensitive(True)
        self.widget.queue_draw()

    # ------------------------------------------------------------- mouse events
    def _press_event(self, event):
        """
        Mouse button callback
        """
        self.pressed_button = self._get_hit_code(event.x, event.y)
        if self.pressed_button >= 0 and self.pressed_button < len(self.icons):
            callback_func = self.pressed_callback_funcs[self.pressed_button] # index is set to match at editorwindow.py where callback func list is created
            callback_func()
        self.widget.queue_draw()

    def _motion_notify_event(self, x, y, state):
        """
        Mouse move callback
        """
        button_under = self._get_hit_code(x, y)
        if self.pressed_button != button_under: # pressed button is released
            self.pressed_button = NO_HIT
        self.widget.queue_draw()

    def _release_event(self, event):
        """
        Mouse release callback
        """
        self.pressed_button = -1
        self.widget.queue_draw()

    def set_callbacks(self, pressed_callback_funcs):
        self.pressed_callback_funcs = pressed_callback_funcs 

    # ---------------------------------------------------------------- painting
    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation
        self.allocation = allocation

        mid_x = w / 2
        buttons_width = self.button_width * len(self.icons)
        self.button_x = mid_x - (buttons_width / 2)
        self._draw_buttons(cr, w, h)


class GlassButtonsGroup(AbstractGlassButtons):

    def __init__(self, button_width, button_height, button_y, image_x_default, image_y_default, focus_group=DEFAULT_FOCUS_GROUP):
        AbstractGlassButtons.__init__(self, button_width, button_height, button_y, button_width, button_height)
        self.released_callback_funcs = []
        self.image_x_default = image_x_default
        self.image_y_default = image_y_default
        focus_groups[focus_group].append(self.widget)

    def add_button(self, pix_buf, release_callback):
        self.icons.append(pix_buf)
        self.released_callback_funcs.append(release_callback)
        self.image_x.append(self.image_x_default)
        self.image_y.append(self.image_y_default)
        self.sensitive.append(True)
        self.widget.set_pref_size(len(self.icons) * self.button_width + 2, self.button_height + 2)

    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation
        self.allocation = allocation
        self.button_x = 0
        self._draw_buttons(cr, w, h)

    def _press_event(self, event):
        self.pressed_button = self._get_hit_code(event.x, event.y)
        self.widget.queue_draw()

    def _motion_notify_event(self, x, y, state):
        button_under = self._get_hit_code(x, y)
        if self.pressed_button != button_under: # pressed button is released if mouse moves from over it
            if self.pressed_button > 0 and self.pressed_button < len(self.icons):
                release_func = self.released_callback_funcs[self.pressed_button]
                release_func()
            self.pressed_button = NO_HIT
        self.widget.queue_draw()

    def _release_event(self, event):
        if self.pressed_button >= 0 and self.pressed_button < len(self.icons):
            release_func = self.released_callback_funcs[self.pressed_button]
            release_func()
        self.pressed_button = -1
        self.widget.queue_draw()


class GlassButtonsToggleGroup(GlassButtonsGroup):    
    def set_pressed_button(self, pressed_button_index, fire_clicked_cb=False):
        self.pressed_button = pressed_button_index
        if fire_clicked_cb == True:
            self._fire_pressed_button()
        self.widget.queue_draw()

    def _fire_pressed_button(self):
        release_func = self.released_callback_funcs[self.pressed_button]
        release_func()

    def _press_event(self, event):
        new_pressed_button = self._get_hit_code(event.x, event.y)
        if new_pressed_button == NO_HIT:
            return
        if new_pressed_button != self.pressed_button:
            self.pressed_button = new_pressed_button
            self._fire_pressed_button()
            self.widget.queue_draw()

    def _motion_notify_event(self, x, y, state):
        pass

    def _release_event(self, event):
        pass


def focus_group_has_focus(focus_group):
    group = focus_groups[focus_group]
    for widget in group:
        if widget.is_focus():
            return True
    
    return False
