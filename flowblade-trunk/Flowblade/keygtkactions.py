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

import gui
import monitorevent
import shortcuts

# Widget names
TLINE_CANVAS = "tlinecanvas"
TLINE_TRACK_COLUMN = "tlinetrackcolumn"
TLINE_ALL = [TLINE_CANVAS, TLINE_TRACK_COLUMN]

# action name -> widget list
_actions_to_widgets = { "mark_in": TLINE_ALL,
                        "to_mark_in":TLINE_ALL}
# widget objects
_widgets = {}
# widget -> ShortCutController object
_controllers = {}


def init():
    # Build _widgets data struct with live objects.
    global _widgets
    _widgets = {TLINE_CANVAS: gui.tline_canvas.widget,
                TLINE_TRACK_COLUMN: gui.tline_column.widget,
                }

    # Create actions
    _create_action("mark_in", monitorevent.mark_in_pressed)
    _create_action("to_mark_in", monitorevent.to_mark_in_pressed)
    
def _create_action(action, press_func):
    #key, modifier = _actions[action]
    widget_list = _actions_to_widgets[action]
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
        except KeyError:
            pass
            


    
        


