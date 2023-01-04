"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2022 Janne Liljeblad.

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


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib


class GtkTicker:
    """
    Calls function repeatedly with given delay between calls.
    This cannot be restarted, that would cause unknow behaviour,
    instead create a new when needed
    """
    def __init__(self, action, delay, data=None):
        self.action = action # callback function
        self.delay = delay # in milliseconds
        self.data = data
        self.running = False
        self.exited = False
    
    def start_ticker(self, delay=None):
        self.running = True
        # Poll rendering from GDK with timeout events to get access to GDK lock on updates 
        # to be able to draw immediately.
        Gdk.threads_add_timeout(GLib.PRIORITY_HIGH_IDLE, self.delay, self._update)
    
    def destroy_ticker(self):
        self.running = False

    def _update(self):
        if not self.running:
            self.exited = True
            return False
        self.action(self.data)
        if not self.running:
            self.exited = True
            return False
        else:
            return True


def get_display_monitors_size_data():
    monitors_size_data = []
    
    display = Gdk.Display.get_default()
    scr_w = Gdk.Screen.width()
    scr_h = Gdk.Screen.height()
    monitors_size_data.append((scr_w, scr_h))
        
    num_monitors = display.get_n_monitors() # Get number of monitors.
    if num_monitors == 1:
        return monitors_size_data
    else:
        for monitor_index in range(0, num_monitors):
            monitor = display.get_monitor(monitor_index)
            geom = monitor.get_geometry()
            monitors_size_data.append((geom.width, geom.height))
        
        return monitors_size_data