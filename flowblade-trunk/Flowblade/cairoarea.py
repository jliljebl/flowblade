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

"""
Module contains CairoDrawableArea2 widget. You can draw onto it using 
Cairo by setting the raw function on ceation, and listen to its mouse and keyboard events.
"""

from gi.repository import Gtk
from gi.repository import Gdk

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
        self.add_events(Gdk.EventMask.POINTER_MOTION_HINT_MASK)
    
        self.set_size_request(pref_width, pref_height)
        self._use_widget_bg = use_widget_bg

        # Connect signal listeners
        self._draw_func = func_draw
        self.connect('draw', self._draw_event)

        self.connect('button-press-event', self._button_press_event)
        self.connect('button-release-event', self._button_release_event)
        self.connect('motion-notify-event', self._motion_notify_event)
        self.connect('enter-notify-event', self._enter_notify_event)
        self.connect('leave-notify-event', self._leave_notify_event)
        self.connect("scroll-event", self._mouse_scroll_event)

        # Signal handler funcs. These are monkeypatched as needed on codes sites
        # that create the objects.
        self.press_func = self._press
        self.release_func = self._release
        self.motion_notify_func = self._motion_notify
        self.leave_notify_func = self._leave
        self.enter_notify_func = self._enter
        self.mouse_scroll_func = None

        # Flag for grabbing focus
        self.set_property("can-focus",  True)
        self.grab_focus_on_press = True

    def add_pointer_motion_mask(self):
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        #self.connect('pointer-motion-event', listener)

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
    # are by default the noop functions here, but are monkeypathed 
    # at creation sites as needed. 
    def _button_press_event(self, widget, event):
        if self.grab_focus_on_press:
            self.grab_focus()
        self.press_func(event)

        return False

    def _button_release_event(self,  widget, event):
        self.release_func(event)

        return False

    def _motion_notify_event(self, widget, event):
        if event.is_hint:
            winbdow, x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.get_state()

        self.motion_notify_func(x, y, state)

    def _enter_notify_event(self, widget, event):
        self.enter_notify_func(event)
        
    def _leave_notify_event(self, widget, event):
        self.leave_notify_func(event)
        
    def _mouse_scroll_event(self, widget, event):
        if self.mouse_scroll_func == None:
            return
        self.mouse_scroll_func(event)

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

