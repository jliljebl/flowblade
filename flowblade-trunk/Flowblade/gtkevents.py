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

def connect(connect_widget, event_type, callback_func, data=None):
    connect_widget.gesture = Gtk.GestureMultiPress(widget=connect_widget)
    #connect_widget.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    connect_widget.gesture.connect("pressed", on_gesture_pressed, None)
    #connect_widget.gesture.set_propagation_phase(Gtk.PropagationPhase.BUBBLE)
    #connect_widget.gesture.set_button(0)


def on_gesture_pressed(gesture, n_press, x, y, user_data):
    print("fff", x, y)
                        

class SimpleStateEvent:
    
    def __init__(self):
        event = Gtk.get_current_event()
        unknow_val, self.state = event.get_state()
        
    def get_state(self):
        return self.state


class ScrollEvent:
    
    def __init__(self, dx, dy):
        if dy == 1.0:
            self.direction = Gdk.ScrollDirection.UP
        elif dy == -1.0:
            self.direction = Gdk.ScrollDirection.DOWN
        elif dx == 1.0:
            self.direction = Gdk.ScrollDirection.RIGHT
        else:
            self.direction = Gdk.ScrollDirection.LEFT

        event = Gtk.get_current_event()
        unknow_val, self.state = event.get_state()
        
    def get_state(self):
        return self.state
