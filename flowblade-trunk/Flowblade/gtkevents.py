"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2025 Janne Liljeblad.

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

from gi.repository import Gtk, Gdk
                        

class SimpleStateEvent:
    
    def __init__(self):
        event = Gtk.get_current_event()
        unknow_val, self.state = event.get_state()
        
    def get_state(self):
        return self.state


class ScrollEvent:
    
    def __init__(self, dx, dy):
        if dy == -1.0:
            self.direction = Gdk.ScrollDirection.UP
        elif dy == 1.0:
            self.direction = Gdk.ScrollDirection.DOWN
        elif dx == 1.0:
            self.direction = Gdk.ScrollDirection.RIGHT
        else:
            self.direction = Gdk.ScrollDirection.LEFT

        event = Gtk.get_current_event()
        unknow_val, self.state = event.get_state()
        
    def get_state(self):
        return self.state


class ButtonEvent:
    
    def __init__(self, n_press, x, y):
    
        self.x = x
        self.y = y 
        self.n_press = n_press

        event = Gtk.get_current_event()
        unknown_val, self.state = event.get_state()
    
        self.type = event.type
        self.button = event.button.button

    def get_state(self):
        return self.state

class KeyPressEvent:

    def __init__(self, event, keyval, keycode, state):
        #event
        self.keyval = keyval
        self.keycode = keycode
        self.state = state
 

class KeyPressEventAdapter:
    
    def __init__(self, widget, callback, user_data=None):
        self.controller = Gtk.EventControllerKey.new(widget)
        self.controller.connect("key-pressed", self.pressed_event)
        self.widget = widget
        self.callback = callback
        self.user_data = user_data 
    
    def pressed_event(self, event, keyval, keycode, state):
        print("pressed event")
        gdk_event = KeyPressEvent(event, keyval, keycode, state)
        if self.user_data == None:
            self.callback(self.widget, gdk_event)
        else:
            self.callback(self.widget, gdk_event, *user_data)
