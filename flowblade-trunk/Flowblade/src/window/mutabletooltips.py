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
MIDDLEBAR_EDIT_BUTTONS = 3
MIDDLEBAR_SPLIT_SYNC_BUTTONS = 4


_root_node = None

_widgetid_to_widgetdata = {}


def init():
    _set_rootnode()
    _apply_tooltips()

def add_widget(widget_id, widget, tooltip_runner):
    global _widgetid_to_widgetdata
    _widgetid_to_widgetdata[widget_id] = (widget, tooltip_runner)

def _set_rootnode():
    global _root_node
    _root_node = shortcuts.get_shortcuts_xml_root_node(editorpersistance.prefs.shortcuts)

def _kb_str(action_code):
    return "<b>" + shortcuts.get_shortcut_kb_str(_root_node, action_code) + "</b>" 

def _apply_tooltips():
    for widget_id in _widgetid_to_widgetdata:
        apply_func = _tooptip_apply_funcs[widget_id]
        widget, tooltip_runner = _widgetid_to_widgetdata[widget_id]
        apply_func(widget, tooltip_runner)

def _middlebar_delete(widget, tooltip_runner):
    tooltips = [_("Splice Out - ") + _kb_str("delete"),  _("Lift - ") +  _kb_str("lift"), _("Ripple Delete"), _("Range Delete")]
    tooltip_runner.tooltips = tooltips

def _middlebar_monitor_insert(widget, tooltip_runner):
    tooltips = [_("Overwrite Range - ") + _kb_str("overwrite_range"), _("Overwrite Selected Clip/s"), _("Insert Clip - ")  + _kb_str("insert"), _("Append Clip - ") + _kb_str("append")]
    tooltip_runner.tooltips = tooltips

def _middlebar_edit(widget, tooltip_runner):
    tooltips = [_("Add Rendered Transition - 2 clips selected"), _("Cut Active Tracks - ") +  _kb_str("cut") + _("\nCut All Tracks - ") + _kb_str("cut_all")]
    tooltip_runner.tooltips = tooltips

def _middlebar_split_sync(widget, tooltip_runner):
    tooltips = [_("Split Audio Synched - ") + _kb_str("split_selected"), _("If <b>single</b> or <b>multi</b> selection set Sync for all Clips on Track Containing Selected Clip/s.\n\nIf <b>box selection</b> set Sync for all selected Clips to first Clip on center most Track."), _("Resync Track Containing Selected Clip/s - ")  +  _kb_str("resync"), _("Resync Selected Clips")]
    tooltip_runner.tooltips = tooltips

_tooptip_apply_funcs =  {
    MIDDLEBAR_DELETE_BUTTONS: _middlebar_delete,
    MIDDLEBAR_MONITOR_INSERT_BUTTONS: _middlebar_monitor_insert,
    MIDDLEBAR_EDIT_BUTTONS: _middlebar_edit, 
    MIDDLEBAR_SPLIT_SYNC_BUTTONS: _middlebar_split_sync
}
