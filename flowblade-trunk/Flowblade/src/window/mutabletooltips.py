"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2026 Janne Liljeblad.

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
This module handles creating tooltips that might change because they contain info about
user settable keyboard shortcuts.
"""

import editorpersistance
import shortcuts

MIDDLEBAR_DELETE_BUTTONS = 0
MIDDLEBAR_MONITOR_INSERT_BUTTONS = 1

_root_node = None

_widgets_to_actioncodes = {}


def init():
    _set_rootnode()
    _apply_tooltips()

def add_widget(widget_id, widget, tooltip_runner):
    global _widgets_to_actioncodes
    _widgets_to_actioncodes[widget_id] = (widget, tooltip_runner)

def _set_rootnode():
    global _root_node
    _root_node = shortcuts.get_shortcuts_xml_root_node(editorpersistance.prefs.shortcuts)

def _kb_str(action_code):
    return shortcuts.get_shortcut_kb_str(_root_node, action_code)

def _apply_tooltips():
    for widget_id in _widgets_to_actioncodes:
        apply_func = _tooptip_apply_funcs[widget_id]
        widget, tooltip_runner = _widgets_to_actioncodes[widget_id]
        apply_func(widget, tooltip_runner)

def _middlebar_delete(widget, tooltip_runner):
    tooltips = [_("Splice Out - ") + _kb_str("delete"),  _("Lift - ") +  _kb_str("lift"), _("Ripple Delete"), _("Range Delete")]
    tooltip_runner.tooltips = tooltips

def _middlebar_monitor_insert(widget, tooltip_runner):
    tooltips = [_("Overwrite Range") + _kb_str("overwrite_range"), _("Overwrite Selected Clip/s"), _("Insert Clip - ")  + _kb_str("insert"), _("Append Clip - ") + _kb_str("append")]
    tooltip_runner.tooltips = tooltips

_tooptip_apply_funcs =  {
    MIDDLEBAR_DELETE_BUTTONS: _middlebar_delete,
    MIDDLEBAR_MONITOR_INSERT_BUTTONS: _middlebar_monitor_insert
}
