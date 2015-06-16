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
Module contains CairoDrawableArea widget. You can draw onto it using 
Cairo, and listen to its mouse and keyboard events.
"""

from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Gdk

class CairoDrawableArea(Gtk.Widget):
    """
    A widget for creating custom components using Cairo canvas. 
    """

    def __init__(self, pref_width, pref_height, func_draw, use_widget_bg=False):
        # Init widget.
        GObject.GObject.__init__(self)

        # Preferred size. Parant container has an effect on actual size. 
        self._pref_width = pref_width
        self._pref_height = pref_height
        self._use_widget_bg = use_widget_bg

        # Set callback funcs
        # Draw, must be provided
        self._draw_func = func_draw

        # Mouse events, set default noops
        self.press_func = self._press
        self.release_func = self._release
        self.motion_notify_func = self._motion_notify
        self.leave_notify_func = self._leave
        self.enter_notify_func = self._enter
        self.mouse_scroll_func = None
        
        # Flag for grabbing focus
        self.grab_focus_on_press = True
        
    def do_realize(self):


        allocation = self.get_allocation()
        attr = Gdk.WindowAttr()
        attr.window_type = Gdk.WindowType.CHILD
        attr.x = allocation.x
        attr.y = allocation.y
        attr.width = allocation.width
        attr.height = allocation.height
        attr.visual = self.get_visual()
        attr.event_mask = self.get_events() \
                                 | Gdk.EventMask.EXPOSURE_MASK \
                                 | Gdk.EventMask.BUTTON_PRESS_MASK \
                                 | Gdk.EventMask.BUTTON_RELEASE_MASK \
                                 | Gdk.EventMask.BUTTON_MOTION_MASK \
                                 | Gdk.EventMask.POINTER_MOTION_HINT_MASK \
                                 | Gdk.EventMask.ENTER_NOTIFY_MASK \
                                 | Gdk.EventMask.LEAVE_NOTIFY_MASK \
                                 | Gdk.EventMask.KEY_PRESS_MASK \
                                 | Gdk.EventMask.SCROLL_MASK \
                                 
        WAT = Gdk.WindowAttributesType
        mask = WAT.X | WAT.Y | WAT.VISUAL
        window = Gdk.Window(self.get_parent_window(), attr, mask);
        
        """
        # Create GDK window
        self.window = Gdk.Window(self.get_parent_window(),
                                 width=self.allocation.width,
                                 height=self.allocation.height,
                                 window_type=Gdk.WINDOW_CHILD,
                                 wclass=Gdk.INPUT_OUTPUT,
                                 event_mask=self.get_events() 
                                 | Gdk.EventMask.EXPOSURE_MASK 
                                 | Gdk.EventMask.BUTTON_PRESS_MASK
                                 | Gdk.EventMask.BUTTON_RELEASE_MASK
                                 | Gdk.EventMask.BUTTON_MOTION_MASK
                                 | Gdk.EventMask.POINTER_MOTION_HINT_MASK
                                 | Gdk.EventMask.ENTER_NOTIFY_MASK
                                 | Gdk.EventMask.LEAVE_NOTIFY_MASK
                                 | Gdk.EventMask.KEY_PRESS_MASK
                                 | Gdk.EventMask.SCROLL_MASK)
        """
        # Connect motion notify event
        self.connect('motion_notify_event', self._motion_notify_event)
        
        # Connect mouse scroll event
        self.connect("scroll-event", self._mouse_scroll_event)
        
        # Make widget capable of grabbing focus
        self.set_property("can-focus",  True)

        # Check that cairo context can be created
        #if not hasattr(self.window, "cairo_create"):
        #    print "no cairo"
        #    raise SystemExit

        # GTK+ stores the widget that owns a Gdk.Window as user data on it. 
        # Custom widgets should do this too
        #self.window.set_user_data(self)

        # Attach style
        #self.style.attach(self.window)

        # Set background color
        #if(self._use_widget_bg):
        #    self.style.set_background(self.window, Gtk.StateType.NORMAL)

        # Set size and place 
        #self.window.move_resize(self.allocation)
        #self.window.move_resize(self.allocation)
        # Set an internal flag telling that we're realized
        self.set_window(window)
        self.register_window(window)
        self.set_realized(True)
        window.set_background_pattern(None)
        
    def set_pref_size(self, pref_width, pref_height):
        self._pref_width = pref_width
        self._pref_height = pref_height
    
    # Gtk+ callback to ask widgets preferred size
    def do_size_request(self, requisition):        
        requisition.width = self._pref_width
        requisition.height = self._pref_height

    # Gtk+ callback to tell widget its allocated size
    def do_size_allocate(self, allocation):
        # This is called by when widget size is known
        # new size in tuple allocation
        self.allocation = allocation
        if self.get_realized():
            self.window.move_resize(*allocation)

    # Noop funcs for unhandled events
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
    
    # Event handlers
    # Expose event callback
    # Create cairo context and pass it on for custom widget drawing.
    def do_expose_event(self, event):
        self.chain(event)
        try:
            cr = self.window.cairo_create()
        except AttributeError:
            print "Cairo create failed"
            raise SystemExit

        return self._draw_func(event, cr, self.allocation)

    # Mouse press / release events
    def do_button_press_event(self, event):
        if self.grab_focus_on_press:
            self.grab_focus()
        self.press_func(event)
        return True

    def do_button_release_event(self, event):
        self.release_func(event)
        return True

    def _mouse_scroll_event(self, widget, event):
        if self.mouse_scroll_func == None:
            return
        self.mouse_scroll_func(event)

    # Mouse drag event
    def _motion_notify_event(self, widget, event):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.get_state()

        self.motion_notify_func(x, y, state)

    # Enter / leave events
    def do_enter_notify_event(self, event):
        self.enter_notify_func(event)
        
    def do_leave_notify_event(self, event):
        self.leave_notify_func(event)
