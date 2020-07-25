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

from gi.repository import Gtk

class ReadyMadeItemSelectpanel:

    def __init__(self, ready_made_item, selected_callback):
        self.ready_made_item = ready_made_item
        self.selected_callback = selected_callback
        
        self.widget = Gtk.EventBox()
        widget.connect("button-press-event", lambda w,e:self.pressed())
        widget.set_can_focus(True)
        widget.add_events(Gdk.EventMask.KEY_PRESS_MASK)

    def pressed(self):
        self.selected_callback(self.ready_made_item)


