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
Module contains CairoDrawableArea2 widget. You can draw onto it using 
Cairo by setting the draw function on creation, and listen to its mouse and keyboard events.
"""

from gi.repository import Gtk
from gi.repository import Gdk

import gtkevents

bg_color = None


class CairoDrawableArea2(Gtk.DrawingArea):

    def __init__(self, pref_width, pref_height, func_draw, use_widget_bg=False):
        Gtk.DrawingArea.__init__(self)
        
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.add_events(Gdk.EventMask.BUTTON_MOTION_MASK)
        self.add_events(Gdk.EventMask.SCROLL_MASK)
        self.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK)
        self.add_events(Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
    
        self.set_size_request(pref_width, pref_height)
        self._use_widget_bg = use_widget_bg

        # Connect signal listeners
        self._draw_func = func_draw
        self.connect('draw', self._draw_event)

        #self.connect('button-press-event', self._button_press_event)
        self.press_controller = Gtk.GestureMultiPress(widget=self)
        self.press_controller.set_button(0)
        self.press_controller.connect("pressed", self._button_press_event)
        
        #self.connect('button-release-event', self._button_release_event)
        self.release_controller = Gtk.GestureMultiPress(widget=self)
        self.release_controller.connect("released", self._button_release_event)

        #self.connect('motion-notify-event', self._motion_notify_event)
        self.motion_controller = Gtk.EventControllerMotion(widget=self)
        self.motion_controller.connect("motion", self._motion_notify_event)

        #self.connect('enter-notify-event', self._enter_notify_event)
        self.enter_controller = Gtk.EventControllerMotion(widget=self)
        self.enter_controller.connect("enter", self._enter_notify_event)
        
        #self.connect('leave-notify-event', self._leave_notify_event)
        self.leave_controller = Gtk.EventControllerMotion(widget=self)
        self.leave_controller.connect("leave", self._leave_notify_event)
         
        #self.connect("scroll-event", self._mouse_scroll_event)
        self.scroll_controller = Gtk.EventControllerScroll(widget=self)
        self.scroll_controller.set_flags(Gtk.EventControllerScrollFlags.BOTH_AXES)
        self.scroll_controller.connect("scroll", self._mouse_scroll_event)
 
        # Signal handler funcs. These are monkeypatched as needed on codes sites
        # that create the objects.
        self.press_func = self._press
        self.release_func = self._release
        self.motion_notify_func = self._motion_notify
        self.leave_notify_func = self._leave
        self.enter_notify_func = self._enter
        self.mouse_scroll_func = None

        self.set_property("can-focus",  True)
        self.grab_focus_on_press = True

    def add_pointer_motion_mask(self):
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)

    def set_pref_size(self, pref_width, pref_height):
        self.set_size_request(pref_width, pref_height)

    def _draw_event(self, widget, cr):
        a = self.get_allocation()       
        self._draw_func(None, cr, (a.x, a.y, a.width, a.height)) # 'None' is event object that was used to pass through here.
                                                                  # GTK2 used a tuple for allocation and all draw funcs expect it, so we provide
                                                                  # allocation as tuple.
        return False

    # ------------------------------------------------------------ Signal listeners 
    # These pass on events to handler functions that 
    # are by default the noop functions here, but are monkeypatched 
    # at creation sites as needed. 
    def _button_press_event(self, event, n_press, x, y):    
        gdk_event = gtkevents.ButtonEvent(n_press, x, y)
        
        if self.grab_focus_on_press:
            self.grab_focus()
        self.press_func(gdk_event)
        
        return False

    def _button_release_event(self, event, n_press, x, y):
        gdk_event = gtkevents.ButtonEvent(n_press, x, y)
        self.release_func(gdk_event)

        return False

    def _motion_notify_event(self, event, x, y):
        gdk_event = gtkevents.SimpleStateEvent()
        state = gdk_event.get_state()
        self.motion_notify_func(x, y, state)

    def _enter_notify_event(self, event, a, b):
        gdk_event = gtkevents.SimpleStateEvent()
        self.enter_notify_func(gdk_event)
        
    def _leave_notify_event(self, event):
        gdk_event = gtkevents.SimpleStateEvent()
        self.leave_notify_func(gdk_event)
        
    def _mouse_scroll_event(self, scroll_event, dx, dy):
        if self.mouse_scroll_func == None:
            return

        gdk_event = gtkevents.ScrollEvent(dx, dy) # This wont be needed as such for Gtk4 which has get_current_event_state()

        self.mouse_scroll_func(gdk_event)

    # ------------------------------------------------------- Noop funcs for unhandled events
    def _press(self, event):
        pass

    def _release(self, event):
        pass

    def _motion_notify(self, x, y, state):
        pass

    def _enter(self, event):
        pass

    def _leave(self, event):
        pass

