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

import gui
import medialog
import monitorevent
import shortcuts
import tlineaction
import updater

# Widget names
TLINE_CANVAS = "tlinecanvas"
TLINE_TRACK_COLUMN = "tlinetrackcolumn"
TLINE_SCALE = "tlinescale"
POS_BAR = "posbar"
TLINE_LEFT_CORNER = "tlineleftcorner"
TLINE_SCROLL = "tlinescroll"
TLINE_MONITOR_DISPLAY = "tlinemonitordisplay"
TLINE_ALL = [TLINE_CANVAS, TLINE_TRACK_COLUMN, TLINE_SCALE, TLINE_LEFT_CORNER, TLINE_SCROLL, TLINE_MONITOR_DISPLAY]
MONITOR_SWITCH = "monitorswitch"
MONITOR_WAVEFORM_DISPLAY = "monitorwaveformdisplay"
MONITOR_ALL = [MONITOR_SWITCH, MONITOR_WAVEFORM_DISPLAY, POS_BAR]
TLINE_MONITOR_ALL = TLINE_ALL +  MONITOR_ALL

# widget name -> widget object
_widgets = {}
# widget -> ShortCutController object
_controllers = {}


def init():
    # Build _widgets data struct with live objects.
    global _widgets
    _widgets = {TLINE_CANVAS: gui.tline_canvas.widget,
                TLINE_TRACK_COLUMN: gui.tline_column.widget,
                TLINE_SCALE: gui.tline_scale.widget,
                POS_BAR: gui.pos_bar.widget,
                TLINE_LEFT_CORNER: gui.tline_left_corner.widget,
                TLINE_SCROLL: gui.tline_scroll,
                TLINE_MONITOR_DISPLAY: gui.tline_display,
                MONITOR_SWITCH: gui.monitor_switch.widget,
                MONITOR_WAVEFORM_DISPLAY: gui.monitor_waveform_display.widget
                }

    #TODO: HANDLE 2 MONITORS!!!!!!!!!!!!!!

    # Create actions
    _create_action("mark_in", monitorevent.mark_in_pressed, TLINE_MONITOR_ALL) # TODO: no worky when clip in monitor
    _create_action("to_mark_in", monitorevent.to_mark_in_pressed, TLINE_MONITOR_ALL)
    _create_action("mark_out", monitorevent.mark_out_pressed, TLINE_MONITOR_ALL)
    _create_action("to_mark_out", monitorevent.to_mark_out_pressed, TLINE_MONITOR_ALL)
    _create_action("clear_io_marks", monitorevent.marks_clear_pressed, TLINE_MONITOR_ALL)
    _create_action("zoom_out", updater.zoom_out, TLINE_MONITOR_ALL)
    _create_action("zoom_in", updater.zoom_in, TLINE_MONITOR_ALL)
    _create_action("switch_monitor", updater.switch_monitor_display, TLINE_MONITOR_ALL) # does not work monitor -> tline
    _create_action("add_marker", tlineaction.add_marker, TLINE_MONITOR_ALL)
    _create_action("cut", tlineaction.cut_pressed, TLINE_ALL)
    _create_action("cut_all", tlineaction.cut_pressed, TLINE_ALL)
    _create_action("log_range", medialog.log_range_clicked, TLINE_MONITOR_ALL)
    _create_action("set_length", tlineaction.set_length_from_keyevent, TLINE_ALL)
        

def _create_action(action, press_func, widget_list):
    for widget_id in widget_list:
        widget = _widgets[widget_id]
        if widget in _controllers:
            _controllers[widget].add_shortcut(action, press_func)
        else:
            _controllers[widget] = ShortCutController(widget)
            _controllers[widget].add_shortcut(action, press_func)


class ShortCutController:
    def __init__(self, widget):
        self.shortcuts = {}
        self.widget = widget
        self.widget.connect("key-press-event", lambda w, e: self._short_cut_handler(e))
    
    def add_shortcut(self, action, press_func):
        self.shortcuts[action] = press_func
    
    def _short_cut_handler(self, event):
        action = shortcuts.get_shortcut_action(event)
        try:
            press_func = self.shortcuts[action]
            press_func()
            return True
        except KeyError:
            return False
            


    
        


