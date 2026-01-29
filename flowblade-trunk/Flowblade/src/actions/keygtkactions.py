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

import appconsts
import clipeffectseditor
import compositeeditor
import compositormodes
import editorpersistance
import editorstate
from editorstate import PLAYER
from editorstate import current_sequence
import gui
import keyframeeditor
import kftoolmode
import medialog
import menuactions
import modesetting
import monitorevent
import movemodes
import multitrimmode
import projectaction
import shortcuts
import shortcutsquickeffects
import syncsplitevent
import tlineaction
import tlinewidgets
import tlineypage
import trackaction
import trimmodes
import updater
import workflow

# This module handles creating keyboard shortcuts using data in shortcuts.py and executing related actions.

# Widget names for action target setting and look up.
APP_WINDOW = "appwindow"
APP_WINDOW_2 = "appwindow2"
SEQUENCE_LIST_VIEW = "sequencelistview"
BIN_LIST_VIEW = "binlistview"
LOG_LIST_VIEW = "loglistview"
TLINE_CANVAS = "tlinecanvas"
TLINE_TRACK_COLUMN = "tlinetrackcolumn"
TLINE_SCALE = "tlinescale"
POS_BAR = "posbar"
TLINE_LEFT_CORNER = "tlineleftcorner"
TLINE_SCROLL = "tlinescroll"
TLINE_MONITOR_DISPLAY = "tlinemonitordisplay"
TLINE_ALL = [TLINE_CANVAS, TLINE_TRACK_COLUMN, TLINE_SCALE, TLINE_LEFT_CORNER, TLINE_SCROLL, TLINE_MONITOR_DISPLAY]
MONITOR_SWITCH = "monitorswitch"
MONITOR_ALL = [MONITOR_SWITCH, POS_BAR]
MIDDLE_BUTTONS_1 = "midbar_b_1"
MIDDLE_BUTTONS_2 = "midbar_b_2"
MIDDLE_BUTTONS_3 = "midbar_b_3"
MIDDLE_BUTTONS_4 = "midbar_b_4"
MIDDLE_BUTTONS_5 = "midbar_b_5"
MIDDLE_BUTTONS_6 = "midbar_b_6"
MIDDLEBAR_BUTTONS = [MIDDLE_BUTTONS_1, MIDDLE_BUTTONS_2, MIDDLE_BUTTONS_3, MIDDLE_BUTTONS_4, MIDDLE_BUTTONS_5, MIDDLE_BUTTONS_6]
TLINE_MONITOR_ALL = TLINE_ALL + MONITOR_ALL + MIDDLEBAR_BUTTONS

# widget name -> widget object
_widgets = {}
# widget -> ShortCutController object
_controllers = {}


class FocusError(Exception):
    pass
    
def init():
    # Build _widgets data struct with live objects.
    global _widgets
    _widgets = {APP_WINDOW: gui.editor_window.window,
                TLINE_CANVAS: gui.tline_canvas.widget,
                TLINE_TRACK_COLUMN: gui.tline_column.widget,
                TLINE_SCALE: gui.tline_scale.widget,
                POS_BAR: gui.pos_bar.widget,
                TLINE_LEFT_CORNER: gui.tline_left_corner.widget,
                TLINE_SCROLL: gui.tline_scroll,
                TLINE_MONITOR_DISPLAY: gui.tline_display,
                MONITOR_SWITCH: gui.monitor_switch.widget,
                SEQUENCE_LIST_VIEW: gui.sequence_list_view,
                BIN_LIST_VIEW: gui.bin_list_view, 
                LOG_LIST_VIEW: gui.editor_window.media_log_events_list_view,
                MIDDLE_BUTTONS_1: gui.editor_window.zoom_buttons.widget,
                MIDDLE_BUTTONS_2: gui.editor_window.edit_buttons.widget,
                MIDDLE_BUTTONS_3: gui.editor_window.edit_buttons_3.widget, 
                MIDDLE_BUTTONS_4: gui.editor_window.edit_buttons_2.widget, 
                MIDDLE_BUTTONS_5: gui.editor_window.monitor_insert_buttons.widget, 
                MIDDLE_BUTTONS_6: gui.editor_window.undo_redo.widget}

    # HANDLE TWO WINDOWS
    if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
        APP_WINDOWS = [APP_WINDOW]
    else:
        APP_WINDOWS = [APP_WINDOW, APP_WINDOW_2]
        _widgets[APP_WINDOW_2] = gui.editor_window.window2
    
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
    _create_action("cut_all", tlineaction.cut_all_pressed, TLINE_ALL)
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
    _create_action("next_cut", _next_cut_action, TLINE_MONITOR_ALL)
    _create_action("prev_cut", _prev_cut_action, TLINE_MONITOR_ALL)
    _create_action("enter_edit", _enter_edit_action, TLINE_ALL)
    _create_action("delete", _tline_delete_action, TLINE_ALL)
    _create_action("lift", tlineaction.lift_button_pressed, TLINE_ALL) 
    _create_action("play_pause_loop_marks", _play_pause_loop_marks_action, TLINE_MONITOR_ALL)
    _create_action("to_start", _to_start_action, TLINE_MONITOR_ALL)
    _create_action("to_end", _to_end_action, TLINE_MONITOR_ALL)
    _create_action("delete", _delete_sequence_action, [SEQUENCE_LIST_VIEW])
    _create_action("delete", _delete_bin_action, [BIN_LIST_VIEW])
    _create_action("delete", _delete_log_action, [LOG_LIST_VIEW])
    _create_action("append_from_bin", projectaction.append_selected_media_clips_into_timeline, TLINE_MONITOR_ALL)
    _create_action("resync", tlineaction.resync_track_button_pressed, TLINE_MONITOR_ALL) # Currently menu global gets to this firsts.
    _create_action("monitor_show_video", lambda: tlineaction.set_monitor_display_mode(appconsts.PROGRAM_OUT_MODE), TLINE_MONITOR_ALL)
    _create_action("monitor_show_scope", lambda: tlineaction.set_monitor_display_mode(appconsts.VECTORSCOPE_MODE), TLINE_MONITOR_ALL)
    _create_action("monitor_show_rgb", lambda: tlineaction.set_monitor_display_mode(appconsts.RGB_PARADE_MODE), TLINE_MONITOR_ALL)
    _create_action("mark_selection_range", monitorevent.mark_selection_range_pressed, TLINE_MONITOR_ALL)
    _create_action("edittool_move", lambda: _editool(1), TLINE_MONITOR_ALL)
    _create_action("edittool_multitrim", lambda: _editool(2), TLINE_MONITOR_ALL)
    _create_action("edittool_spacer", lambda: _editool(3), TLINE_MONITOR_ALL)
    _create_action("edittool_insert", lambda: _editool(4), TLINE_MONITOR_ALL)
    _create_action("edittool_cut", lambda: _editool(5), TLINE_MONITOR_ALL)
    _create_action("edittool_keyframe", lambda: _editool(6), TLINE_MONITOR_ALL)
    _create_action("kp_edittool_move", lambda: _editool(1), TLINE_MONITOR_ALL)
    _create_action("kpstr_edittool_move", lambda: _editool(1), TLINE_MONITOR_ALL)
    _create_action("kp_edittool_move", lambda: _editool(1), TLINE_MONITOR_ALL)
    _create_action("kpstr_edittool_move",  lambda: _editool(1), TLINE_MONITOR_ALL)
    _create_action("kp_edittool_multitrim",  lambda: _editool(2), TLINE_MONITOR_ALL)
    _create_action("kpstr_edittool_multitrim",  lambda: _editool(2), TLINE_MONITOR_ALL)
    _create_action("kp_edittool_spacer",  lambda: _editool(3), TLINE_MONITOR_ALL)
    _create_action("kp_str_edittool_spacer",  lambda: _editool(3), TLINE_MONITOR_ALL)
    _create_action("kp_edittool_insert",  lambda: _editool(4), TLINE_MONITOR_ALL)
    _create_action("kpstr_edittool_insert",  lambda: _editool(4), TLINE_MONITOR_ALL)
    _create_action("kp_edittool_cut", lambda: _editool(5), TLINE_MONITOR_ALL)
    _create_action("kpstr_edittool_cut",  lambda: _editool(5), TLINE_MONITOR_ALL)
    _create_action("kp_edittool_keyframe",  lambda: _editool(6), TLINE_MONITOR_ALL)
    _create_action("kpstr_edittool_keyframe",  lambda: _editool(6), TLINE_MONITOR_ALL)
    _create_action("quickeffect_1", lambda: _quickeffect("f1"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_2", lambda: _quickeffect("f2"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_3", lambda: _quickeffect("f3"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_4", lambda: _quickeffect("f4"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_5", lambda: _quickeffect("f5"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_6", lambda: _quickeffect("f6"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_7", lambda: _quickeffect("f7"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_8", lambda: _quickeffect("f8"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_9", lambda: _quickeffect("f9"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_10", lambda: _quickeffect("f10"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_11", lambda: _quickeffect("f11"), TLINE_MONITOR_ALL)
    _create_action("quickeffect_12", lambda: _quickeffect("f12"), TLINE_MONITOR_ALL)
    _create_action("tline_page_down", tlineypage.page_down_key, APP_WINDOWS)
    _create_action("tline_page_up", tlineypage.page_up_key, APP_WINDOWS)
    _create_action("open_next", projectaction.open_next_media_item_in_monitor, APP_WINDOWS)
    _create_action("open_prev", projectaction.open_prev_media_item_in_monitor, APP_WINDOWS)
    _create_action("append_from_bin", _append_bin, APP_WINDOWS)
    _create_action("move_media", _init_media_list_move, APP_WINDOWS)
    _create_action("monitor_show_video",lambda: tlineaction.set_monitor_display_mode(appconsts.PROGRAM_OUT_MODE), APP_WINDOWS)
    _create_action("monitor_show_scope", lambda: tlineaction.set_monitor_display_mode(appconsts.VECTORSCOPE_MODE), APP_WINDOWS)
    _create_action("monitor_show_rgb", lambda: tlineaction.set_monitor_display_mode(appconsts.RGB_PARADE_MODE), APP_WINDOWS)
    _create_action("delete", _global_delete, APP_WINDOWS)
    _create_action("fullscreen",  menuactions.toggle_fullscreen, APP_WINDOWS)
    _create_action("global_escape", _global_escape, APP_WINDOWS)
    _create_action("global_control_a", _global_control_A, APP_WINDOWS)

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
        try:
            press_func, pass_event = self.shortcuts[action]
            if pass_event == False:
                press_func()
            else:
                press_func(event)
            return True
        except(KeyError, FocusError) as e:
            return False

        
# --------------------------------------------------------- effect editors
def connect_filter_widget(widget):
    widget.connect("key-press-event", _filter_widget_keypress_handler)
    children = widget.get_children()
    for child in children:
        child.connect("key-press-event", _filter_widget_keypress_handler)
            
def _filter_widget_keypress_handler(widget, event):
    action = shortcuts.get_shortcut_action(event)
    focus_editor = _get_focus_keyframe_editor(clipeffectseditor.keyframe_editor_widgets)

    if focus_editor != None:
        if focus_editor.get_focus_child() != None:
            if focus_editor.__class__ == keyframeeditor.FilterRectGeometryEditor or \
                focus_editor.__class__ == keyframeeditor.FilterRotatingGeometryEditor or \
                focus_editor.__class__ == keyframeeditor.GeometryNoKeyframes:
                if ((event.keyval == Gdk.KEY_Left) 
                    or (event.keyval == Gdk.KEY_Right)
                    or (event.keyval == Gdk.KEY_Up)
                    or (event.keyval == Gdk.KEY_Down)):
                    focus_editor.arrow_edit(event.keyval, (event.get_state() & Gdk.ModifierType.CONTROL_MASK), (event.get_state() & Gdk.ModifierType.SHIFT_MASK))
                    return True
        if action == 'play_pause':
            _play_pause_action()
            return True
        if action == 'play_pause_loop_marks':
            _play_pause_loop_marks_action()
            return True
        if action == 'prev_frame' or action == 'next_frame':
            if action == 'prev_frame':
                _prev_frame_action(event)
            else:
                _next_frame_action(event)
            return True
        if action == "delete":
            focus_editor.delete_pressed()
            return True
    
    return False


def _get_focus_keyframe_editor(keyframe_editor_widgets):
    if keyframe_editor_widgets == None:
        return None
    for kfeditor in keyframe_editor_widgets:
        if kfeditor.get_focus_child() != None:
           return kfeditor
    return None

# --------------------------------------------------------- compositor editors
def connect_compositor_widget(widget):
    widget.connect("key-press-event", _compositor_widget_keypress_handler)
    children = widget.get_children()
    for child in children:
        child.connect("key-press-event", _compositor_widget_keypress_handler)
        
def _compositor_widget_keypress_handler(widget, event):
    if compositeeditor.keyframe_editor_widgets != None:
        for kfeditor in compositeeditor.keyframe_editor_widgets:
            if kfeditor.get_focus_child() != None:
                if kfeditor.__class__ == keyframeeditor.GeometryEditor or \
                kfeditor.__class__ == keyframeeditor.RotatingGeometryEditor:
                    action = shortcuts.get_shortcut_action(event)
                    if ((event.keyval == Gdk.KEY_Left) 
                        or (event.keyval == Gdk.KEY_Right)
                        or (event.keyval == Gdk.KEY_Up)
                        or (event.keyval == Gdk.KEY_Down)):
                        kfeditor.arrow_edit(event.keyval, (event.get_state() & Gdk.ModifierType.CONTROL_MASK), (event.get_state() & Gdk.ModifierType.SHIFT_MASK))
                        return True
                    if action == 'play_pause':
                        _play_pause_action()
                        return True
                    if action == 'play_pause_loop_marks':
                        _play_pause_loop_marks_action()
                        return True
                    if action == 'prev_frame' or action == 'next_frame':
                        if action == 'prev_frame':
                            _prev_frame_action(event)
                        else:
                            _next_frame_action(event)
                        return True
                    if action == "delete":
                        kfeditor.delete_pressed()
                        return True
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

def _next_cut_action():
    if editorstate.current_is_active_trim_mode() == True:
        return

    if editorstate.timeline_visible():
        tline_frame = PLAYER().tracktor_producer.frame()
        cut_frame = current_sequence().find_next_cut_frame(tline_frame) # returns-1 if nor found
        mark_frame = current_sequence().find_next_mark_or_marker(tline_frame) # returns-1 if nor found

        frame = cut_frame
        if mark_frame != -1 and mark_frame < frame:
            frame = mark_frame

        if frame != -1:
            PLAYER().seek_frame(frame)
            if editorpersistance.prefs.center_on_arrow_move == True:
                updater.center_tline_to_current_frame()
    else:
         monitorevent.up_arrow_seek_on_monitor_clip()
     
def _prev_cut_action():
    if editorstate.current_is_active_trim_mode() == True:
        return
     
    if editorstate.timeline_visible():
        tline_frame = PLAYER().tracktor_producer.frame()
        cut_frame = current_sequence().find_prev_cut_frame(tline_frame)
        mark_frame = current_sequence().find_prev_mark_or_marker(tline_frame) # returns-1 if nor found
        
        frame = cut_frame
        if mark_frame != -1 and mark_frame > frame:
            frame = mark_frame

        if frame != -1:
            PLAYER().seek_frame(frame)
            if editorpersistance.prefs.center_on_arrow_move == True:
                updater.center_tline_to_current_frame()  
    else:
         monitorevent.down_arrow_seek_on_monitor_clip()

def _enter_edit_action():
    # We are currently always calling both of these.
    # Check exit of this, e.g. we go from two roll to one roll.
    if editorstate.current_is_active_trim_mode() == True:
        trimmodes.enter_pressed()
            
    if editorstate.EDIT_MODE() == editorstate.MULTI_TRIM:
        multitrimmode.enter_pressed()

def _tline_delete_action():
    if editorstate.EDIT_MODE() == editorstate.KF_TOOL:
        kftoolmode.delete_active_keyframe()
    else:
        # Clip selection and compositor selection are mutually exclusive, 
        # so max one one these will actually delete something.
        tlineaction.splice_out_button_pressed()
        compositormodes.delete_current_selection()

def _play_pause_loop_marks_action():
    if editorstate.current_is_move_mode():
        if PLAYER().is_playing():
            monitorevent.stop_pressed()
        else:
            monitorevent.start_marks_looping()

def _to_start_action():
    if PLAYER().is_playing():
        monitorevent.stop_pressed()
    gui.editor_window.tline_cursor_manager.set_default_edit_tool()
    PLAYER().seek_frame(0)

    if editorstate.timeline_visible():
        tlinewidgets.pos = 0
        updater.repaint_tline()
        updater.update_tline_scrollbar()

def _to_end_action():
    if PLAYER().is_playing():
        monitorevent.stop_pressed()
    gui.editor_window.tline_cursor_manager.set_default_edit_tool()
    PLAYER().seek_end()

    if editorstate.timeline_visible():
        pos = current_sequence().get_length() - 1 - int(float(gui.tline_canvas.widget.get_allocation().width) / float(tlinewidgets.pix_per_frame) * 0.75)
        if pos < 0:
            pos = 0
        tlinewidgets.pos = pos
        updater.repaint_tline()
        updater.update_tline_scrollbar()

def _delete_sequence_action():
    if gui.sequence_list_view.text_rend_1.get_property("editing") == True:
        return
    projectaction.delete_selected_sequence()

def _delete_bin_action():
    if gui.bin_list_view.text_rend_1.get_property("editing") == True:
        return
    projectaction.delete_selected_bin()

def _delete_log_action():
    # Delete media log event
    if gui.editor_window.media_log_events_list_view.get_focus_child() != None:
        medialog.delete_selected()

def _append_bin():
    if gui.media_list_view.widget.has_focus() or gui.media_list_view.widget.get_focus_child() != None: 
        projectaction.append_selected_media_clips_into_timeline()
        return
    
    raise FocusError("Wrong focus for global event")

def _init_media_list_move():
    gui.media_list_view.init_move()

def _global_delete():
    # Delete media file
    if gui.media_list_view.widget.get_focus_child() != None:
        projectaction.delete_media_files()
        return

    raise FocusError("Wrong focus for global event")

def _global_escape():
    if editorstate.current_is_move_mode() == False:
        modesetting.set_default_edit_mode()
        return
    elif gui.big_tc.get_visible_child_name() == "BigTCEntry":
        gui.big_tc.set_visible_child_name("BigTCDisplay")
        return

    raise FocusError("Wrong focus for global event")

def _global_control_A():
    if gui.media_list_view.widget.has_focus() or gui.media_list_view.widget.get_focus_child() != None: 
        gui.media_list_view.select_all()
        return

    raise FocusError("Wrong focus for global event")

# ------------------------------------------------- edit tools
def _editool(keyboard_number): 
    workflow.tline_tool_keyboard_selected_for_number(keyboard_number)

# ------------------------------------------------- quickeffects
def _quickeffect(key_name):
    shortcutsquickeffects.do_quick_shortcut_filter_add(key_name)


# TODO: See if integration can be done and remove this comment.
#
# TODO: We should consider integrating some parts of this with targetactions.py
# TODO:
# TODO: As of this writing, targetactions.py has a superset of targetable
# TODO: actions, as compared to keygtkevents.py, totally separate from any keyboard
# TODO: event handling. There are a few new named target actions in there that
# TODO: aren't available in here. There is also currently a lot code duplication
# TODO: between the two modules. See targetactions.py for more details.
# TODO:
# TODO: At a minimum, if you add or modify any of the key actions in here,
# TODO: please consider updating targetactions.py as well. Right now there
# TODO: is a lot of duplication between these modules, and often a change
# TODO: in one would warrant a change in the other.
# TODO:
# TODO: keygtkevents.py is all about handling key presses from the keyboard, and
# TODO: routing those events to trigger actions in various parts of the program.
# TODO:
# TODO: targetactions.py is basically a bunch of zero-argument functions with
# TODO: names based on the shortcut key names found here. It was created as part
# TODO: of the USB HID work, so that USB jog/shuttle devices could have their
# TODO: buttons target various actions within the program, without requiring
# TODO: each USB driver to directly make connections to a dozen different parts
# TODO: of the program to control it.
# TODO:
# TODO: So now we have two collections of shortcut key names which map to
# TODO: basically the same actions, but in a different way. I originally wanted
# TODO: to just use keygtkevents.py as the target for the USB driver actions, but
# TODO: couldn't use it directly since this module is intertwined with the
# TODO: main computer keyboard and its events.
# TODO:
# TODO: For now, I have integrated the new command targets from
# TODO: targetactions.py into keygtkevents.py, both for completeness, and also as
# TODO: a proof of concept as to how we might migrate some of the other code
# TODO: in here over to call targetactions.py
# TODO:
# TODO:   -- Nathan Rosenquist (@ratherlargerobot)
# TODO:      Feb 2022