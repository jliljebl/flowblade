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
from gi.repository import Gdk
from gi.repository import Gtk

import cairoarea
import editorstate
from editorstate import PLAYER

DEFAULT_VIEW = 0
START_TRIM_VIEW = 1


class MonitorWidget:
    
    def __init__(self):
        self.widget = Gtk.VBox()
        
        self.view = DEFAULT_VIEW
        
        # top row
        self.top_row = Gtk.HBox()
        
        top = cairoarea.CairoDrawableArea2(1, 1, self._draw_black, use_widget_bg=False)
        self.top_row.pack_start(top, True, True,0)
        
        # mid row
        self.mid_row = Gtk.HBox()

        self.left_display = cairoarea.CairoDrawableArea2(1, 1, self._draw_black, use_widget_bg=False)

        black_box = Gtk.EventBox()
        black_box.add(Gtk.Label())
        bg_color = Gdk.Color(red=0.0, green=0.0, blue=0.0)
        black_box.modify_bg(Gtk.StateType.NORMAL, bg_color)
        self.monitor = black_box

        self.right_display = cairoarea.CairoDrawableArea2(1, 1, self._draw_black, use_widget_bg=False)
        
        self.mid_row.pack_start(self.left_display, False, False,0)
        self.mid_row.pack_start(self.monitor, True, True,0)
        self.mid_row.pack_start(self.right_display, False, False,0)
        
        # bottom row
        self.bottom_row = Gtk.HBox()
        bottom = cairoarea.CairoDrawableArea2(1, 1, self._draw_black, use_widget_bg=False)
        self.bottom_row.pack_start(bottom, True, True,0)
        
        # build pane
        self.widget.pack_start(self.top_row, False, False,0)
        self.widget.pack_start(self.mid_row , True, True,0)
        self.widget.pack_start(self.bottom_row, False, False,0)
        
    def get_monitor(self):
        return self.monitor

    def set_default_view(self):
        if self.view == DEFAULT_VIEW:
            return
        
        # Refreshing while rendering overwrites file on disk and loses 
        # previous rendered data. 
        if PLAYER().is_rendering:
            return
        
        self.view = DEFAULT_VIEW
        self.left_display.set_pref_size(1, 1)
        self.widget.queue_draw()
        PLAYER().refresh()
        
    def set_start_trim_view(self):
        if editorstate.show_trim_view == False:
            return

        if self.view == START_TRIM_VIEW:
            return

        # Refreshing while rendering overwrites file on disk and loses 
        # previous rendered data. 
        if PLAYER().is_rendering:
            return
        
        self.view = START_TRIM_VIEW
        
        print "jjajaj"
        self.left_display.set_pref_size(500, 500)
        self.widget.queue_draw()
        PLAYER().refresh()

    def _draw_black(self, event, cr, allocation):
        x, y, w, h = allocation

        # Draw bg
        cr.set_source_rgb(0.0, 0.0, 0.0)
        cr.rectangle(0, 0, w, h)
        cr.fill()

    def _draw_red(self, event, cr, allocation):
        # testing
        x, y, w, h = allocation

        # Draw bg
        cr.set_source_rgb(1.0, 0.0, 0.0)
        cr.rectangle(0, 0, w, h)
        cr.fill()
