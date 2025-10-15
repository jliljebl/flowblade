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
from gi.repository import Gdk

import editorpersistance
import editorstate
from editorstate import PLAYER
import gui
import medialog
import monitorevent
import movemodes
import shortcuts
import syncsplitevent
import tlineaction
import trackaction
import trimmodes
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
    _create_action("mark_in", monitorevent.mark_in_pressed, TLINE_MONITOR_ALL)
    _create_action("to_mark_in", monitorevent.to_mark_in_pressed, TLINE_MONITOR_ALL)
    _create_action("mark_out", monitorevent.mark_out_pressed, TLINE_MONITOR_ALL)
    _create_action("to_mark_out", monitorevent.to_mark_out_pressed, TLINE_MONITOR_ALL)
    _create_action("clear_io_marks", monitorevent.marks_clear_pressed, TLINE_MONITOR_ALL)
    _create_action("zoom_out", updater.zoom_out, TLINE_MONITOR_ALL)
    _create_action("zoom_in", updater.zoom_in, TLINE_MONITOR_ALL)
    _create_action("switch_monitor", updater.switch_monitor_display, TLINE_MONITOR_ALL)
    _create_action("add_marker", tlineaction.add_marker, TLINE_MONITOR_ALL)
    _create_action("cut", tlineaction.cut_pressed, TLINE_ALL)
    _create_action("cut_all", tlineaction.cut_pressed, TLINE_ALL)
    _create_action("log_range", medialog.log_range_clicked, TLINE_MONITOR_ALL)
    _create_action("set_length", tlineaction.set_length_from_keyevent, TLINE_ALL)
    _create_action("insert", tlineaction.insert_button_pressed, TLINE_MONITOR_ALL)
    _create_action("append", tlineaction.append_button_pressed, TLINE_MONITOR_ALL)
    _create_action("3_point_overwrite", tlineaction.three_point_overwrite_pressed, TLINE_MONITOR_ALL)
    _create_action("overwrite_range", tlineaction.range_overwrite_pressed, TLINE_MONITOR_ALL)
    _create_action("trim_start", tlineaction.trim_start_pressed, TLINE_ALL)
    _create_action("trim_end", tlineaction.trim_end_pressed, TLINE_ALL)
    _create_action("toggle_audio_mute", tlineaction.mute_clip_from_keyevent, TLINE_ALL)
    _create_action("nudge_back", lambda: movemodes.nudge_selection(-1), TLINE_ALL)
    _create_action("nudge_forward", lambda: movemodes.nudge_selection(1), TLINE_ALL)
    _create_action("nudge_back_10", lambda: movemodes.nudge_selection(-10), TLINE_ALL)
    _create_action("nudge_forward_10", lambda: movemodes.nudge_selection(10), TLINE_ALL)
    _create_action("select_next", monitorevent.select_next_clip_for_filter_edit, TLINE_MONITOR_ALL)
    _create_action("select_prev", monitorevent.select_prev_clip_for_filter_edit, TLINE_MONITOR_ALL)
    _create_action("toggle_track_output", trackaction.toggle_track_output, TLINE_ALL)
    _create_action("split_selected", tlineaction.split_audio_synched_button_pressed, TLINE_ALL)
    _create_action("set_sync_relation", syncsplitevent.init_select_master_clip_from_keyevent, TLINE_ALL)
    _create_action("clear_sync_relation", syncsplitevent.clear_sync_relation_from_keyevent, TLINE_ALL)
    _create_action("slower", monitorevent.j_pressed, TLINE_MONITOR_ALL)
    _create_action("stop", monitorevent.k_pressed, TLINE_MONITOR_ALL)
    _create_action("faster", monitorevent.l_pressed, TLINE_MONITOR_ALL)
    _create_action("play_pause", _play_pause_action, TLINE_MONITOR_ALL)
    _create_action("prev_frame", _prev_frame_action, TLINE_MONITOR_ALL, True)
    _create_action("next_frame", _next_frame_action, TLINE_MONITOR_ALL, True)

def _create_action(action, press_func, widget_list, pass_event=False):
    for widget_id in widget_list:
        widget = _widgets[widget_id]
        if widget in _controllers:
            _controllers[widget].add_shortcut(action, press_func, pass_event)
        else:
            _controllers[widget] = ShortCutController(widget)
            _controllers[widget].add_shortcut(action, press_func, pass_event)


class ShortCutController:
    def __init__(self, widget):
        self.shortcuts = {}
        self.widget = widget
        self.widget.connect("key-press-event", lambda w, e: self._short_cut_handler(e))
    
    def add_shortcut(self, action, press_func, pass_event):
        self.shortcuts[action] = (press_func, pass_event)
    
    def _short_cut_handler(self, event):
        action = shortcuts.get_shortcut_action(event)
        print("ShortCutController: ", action)
        try:
            press_func, pass_event = self.shortcuts[action]
            if pass_event == False:
                press_func()
            else:
                press_func(event)
            return True
        except KeyError:
            return False


# --------------------------------------------------------- local handler funcs
def _play_pause_action():
    if PLAYER().is_playing():
        monitorevent.stop_pressed()
    else:
        monitorevent.play_pressed()

def _prev_frame_action(event):
    if editorstate.current_is_active_trim_mode() == True:
        trimmodes.left_arrow_pressed((event.get_state() & Gdk.ModifierType.CONTROL_MASK))
    else:    
        _do_arrow_frame_action(-1, event)

def _next_frame_action(event):
    if editorstate.current_is_active_trim_mode() == True:
        trimmodes.right_arrow_pressed((event.get_state() & Gdk.ModifierType.CONTROL_MASK))
    else:    
        _do_arrow_frame_action(1, event)
        
def _do_arrow_frame_action(seek_amount, event):
    prefs = editorpersistance.prefs
    
    if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
        PLAYER().slowmo_seek_delta(seek_amount)
        return 

    if (event.get_state() & Gdk.ModifierType.SHIFT_MASK):
        seek_amount = seek_amount * prefs.ffwd_rev_shift
    if (event.get_state() & Gdk.ModifierType.LOCK_MASK):
        seek_amount = seek_amount * prefs.ffwd_rev_caps
    PLAYER().seek_delta(seek_amount)
