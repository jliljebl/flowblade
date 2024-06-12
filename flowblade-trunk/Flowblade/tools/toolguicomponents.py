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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""
"""
Gui bilding utils for tool applications with no dependencies on 
main application modules.
"""


import gi
gi.require_version('PangoCairo', '1.0')

from gi.repository import Gio, Gdk
from gi.repository import Pango
from gi.repository import PangoCairo

import cairo
import math
M_PI = math.pi

import cairoarea
import utils

BIG_TC_FRAME_GRAD_STOPS = [ (1, 0.7, 0.7, 0.7, 1),
                            (0.95, 0.7, 0.7, 0.7, 1),
                            (0.75, 0.1, 0.1, 0.1, 1),
                            (0, 0.14, 0.14, 0.14, 1)]


class PressLaunch:
    def __init__(self, callback, w=22, h=22):
        self.widget = cairoarea.CairoDrawableArea2( w, 
                                                    h, 
                                                    self._draw)
        self.widget.press_func = self._press_event
        self.callback = callback
        self.sensitive = True

    def set_sensitive(self, value):
        self.sensitive = value
        
    def _draw(self, event, cr, allocation):      
        cr.move_to(7, 13)
        cr.line_to(12, 18)
        cr.line_to(17, 13)
        cr.close_path()
        cr.set_source_rgb(0.66, 0.66, 0.66)
        cr.fill()
        
    def _press_event(self, event):
        if self.sensitive == False:
           return 

        self.callback(self.widget, event)

class PressLaunchSurface:
    def __init__(self, callback, surface, w=22, h=22, show_mouse_prelight=True):
        self.widget = cairoarea.CairoDrawableArea2( w,
                                                    h,
                                                    self._draw)
        self.widget.press_func = self._press_event
        self.callback = callback
        self.surface = surface
        self.surface_x = 6
        self.surface_y = 6
        
        self.draw_triangle = False # set True at creation site if needed

        self.prelight_on = False 
        self.ignore_next_leave = False
        
        if show_mouse_prelight:
            self._prepare_mouse_prelight()
        else:
            self.surface_prelight = None

    def connect_launched_menu(self, launch_menu):
        # We need to leave prelight icon when menu closed
        launch_menu.connect("hide", lambda w : self.leave_notify_listener(None))
    
    def _prepare_mouse_prelight(self):
        self.surface_prelight = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.surface.get_width(), self.surface.get_height())
        cr = cairo.Context(self.surface_prelight)
        cr.set_source_surface(self.surface, 0, 0)
        cr.rectangle(0,0,self.surface.get_width(), self.surface.get_height())
        cr.fill()
        
        cr.set_operator(cairo.Operator.ATOP)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.5)
        cr.rectangle(0,0,self.surface.get_width(), self.surface.get_height())
        cr.fill()
        
        self.widget.leave_notify_func = self.leave_notify_listener
        self.widget.enter_notify_func = self.enter_notify_listener

    def leave_notify_listener(self, event):
        if self.ignore_next_leave == True:
            self.ignore_next_leave = False
            return
            
        self.prelight_on = False
        self.widget.queue_draw()

    def shut_prelight(self):
        self.prelight_on = False
        self.widget.queue_draw()

    def enter_notify_listener(self, event):
        self.prelight_on = True 
        self.widget.queue_draw()

    def _draw(self, event, cr, allocation):
        if self.draw_triangle == False:
            if self.prelight_on == False or self.surface_prelight == None:
                cr.set_source_surface(self.surface, self.surface_x, self.surface_y)
            else:
                cr.set_source_surface(self.surface_prelight, self.surface_x, self.surface_y)
            cr.paint()
        else:
            self._draw_triangle(event, cr, allocation)  

    def _draw_triangle(self, event, cr, allocation):      
        cr.move_to(7, 13)
        cr.line_to(12, 18)
        cr.line_to(17, 13)
        cr.close_path()
        cr.set_source_rgb(0.66, 0.66, 0.66)
        cr.fill()
        
    def _press_event(self, event):
        self.ignore_next_leave = True
        self.prelight_on = True 
        self.callback(self.widget, event)
        

class MonitorTCDisplay:
    """
    Mostly copy-pasted from BigTCDisplay, just enough different to make common inheritance
    annoying.
    """
    def __init__(self, widget_width=94):
        self.widget = cairoarea.CairoDrawableArea2( widget_width,
                                                    20,
                                                    self._draw)
        self.font_desc = Pango.FontDescription("Bitstream Vera Sans Mono Condensed 9")

        # Draw consts
        x = 2
        y = 2
        width = widget_width - 4
        height = 16
        aspect = 1.0
        corner_radius = height / 3.5
        radius = corner_radius / aspect
        degrees = M_PI / 180.0

        self._draw_consts = (x, y, width, height, aspect, corner_radius, radius, degrees)

        self.FPS_NOT_SET = -99.0

        self._frame = 0
        self.use_internal_frame = False

        self.use_internal_fps = False # if False, fps value for calculating tc comes from utils.fps(),
                                       # if True, fps value from self.fps that will have to be set from user site
        self.display_tc = True # if this is False the frame number is displayed instead of timecode
        self.fps = self.FPS_NOT_SET # this will have to be set from user site

    def set_frame(self, frame):
        self._frame = frame # this is used in tools, editor window uses PLAYER frame
        self.widget.queue_draw()

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo context and allocation.
        """
        x, y, w, h = allocation

        # Draw round rect with gradient and stroke around for thin bezel
        self._round_rect_path(cr)
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.fill_preserve()

        grad = cairo.LinearGradient (0, 0, 0, h)
        for stop in BIG_TC_FRAME_GRAD_STOPS:
            grad.add_color_stop_rgba(*stop)
        cr.set_source(grad)
        cr.set_line_width(1)
        cr.stroke()

        # Get current TIMELINE frame str
        if self.use_internal_frame:
            frame = self._frame
        else:
            frame = PLAYER().tracktor_producer.frame() # is this used actually?

        if self.display_tc == True:
            if self.use_internal_fps == False:
                frame_str = utils.get_tc_string(frame)
            else:
                if  self.fps != self.FPS_NOT_SET:
                    frame_str = utils.get_tc_string_with_fps(frame, self.fps)
                else:
                    frame_str = ""
        else:
            frame_str = str(self._frame).rjust(6)
    
        # Text
        layout = PangoCairo.create_layout(cr)
        layout.set_text(frame_str, -1)
        layout.set_font_description(self.font_desc)

        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.move_to(8, 2)
        PangoCairo.update_layout(cr, layout)
        PangoCairo.show_layout(cr, layout)

    def _round_rect_path(self, cr):
        x, y, width, height, aspect, corner_radius, radius, degrees = self._draw_consts

        cr.new_sub_path()
        cr.arc (x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc (x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc (x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc (x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path ()
        
# ------------------------------------------------------ menu building
def menu_clear_or_create(menu):
    if menu != None:
        menu.remove_all()
    else:
        menu = Gio.Menu.new()
    
    return menu

def add_menu_action(application, menu, label, item_id, data, callback, active=True):
    if active == True:
        menu.append(label, "app." + item_id) 
    else:
        menu.append(label, "noaction") 
    action = Gio.SimpleAction(name=item_id)
    action.connect("activate", callback, data)
    application.add_action(action)

def create_rect(x, y):
    rect = Gdk.Rectangle()
    rect.x = x
    rect.y = y
    rect.width = 2
    rect.height = 2
    
    return rect
