"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2022 Janne Liljeblad and contributors.

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

"""
High-level functions that can be used as targets of key presses, jog/shuttle
actions, or other events.

This module provides a bunch of simple, centralized functions that can be
called from elsewhere in the program, which then take the current context into
account, and dispatch to the various other parts of the program that actually
do the work.

The idea is that you can have a lot of random far-flung code calling these
functions, which are centralized, instead of a bunch of point to point
connections from random things that want to control things connecting
directly to the various parts of the program they want to control.

"""

# TODO: The target actions and functions in this module are a strict superset
# TODO: of the named target actions available in keyevent. It would probably
# TODO: be a good idea to make more of the keyevent actions eventually
# TODO: execute these functions, to avoid code duplication. Additionally,
# TODO: the new target actions here could then be added as supported targets
# TODO: for keyboard events.
# TODO:
# TODO: See keyevents.py for more details.

import editorstate
from editorstate import current_sequence
from editorstate import PLAYER

import compositormodes
import editorpersistance
import gui
import kftoolmode
import medialog
import modesetting
import monitorevent
import movemodes
import projectaction
import tlineaction
import tlinewidgets
import trimmodes
import updater

##############################################################################
# CONTROL FUNCTIONS WITH MORE THAN ZERO ARGUMENTS                            #
##############################################################################

# These functions can not be used in the same manner as the zero-argument
# handler functions in this module, and have no unified contract between them.
# As such, they are not good candidates for mapping directly to key events.

def move_player_position(delta):
    """
    Move the current monitor timeline by the specified number of frames.

    Accepts delta, a signed integeger, which represents the number of frames
    to move the timeline.

    Returns True if the player position was moved in some way,
    or False otherwise.

    Positive numbers move the timeline forward by the specified number of
    frames. Negative numbers move it backwards. Zero is a no-op.

    """

    # handle trim mode differently
    if editorstate.current_is_active_trim_mode() == True:
        trimmodes.move_delta(delta)
        return True
    else:
        PLAYER().seek_delta(delta)
        return True

    return False

def variable_speed_playback(speed):
    """
    Start variable speed playback at the specified speed.

    Speed is a signed floating point number representing the speed (and
    direction) to move the timeline.

    Positive numbers move the timeline forward, at the given speed.
    Negative numbers move the timeline backward, at the given speed.

    Returns True if variable playback was controlled in some way, or
    False if variable playback was not attempted.

    Note that MLT can not currently support playback of speeds slower than
    the normal speed of play. For example, -1.0 is OK, and 1.0 is OK. But
    0.99 will just never advance to the next frame. Apparently slower than
    1x playback speeds are on the roadmap for MLT, so it may work someday.
    Passing in a speed of 0 effectively stops playback.

    """

    # don't perform variable speed playback in trim mode
    if editorstate.current_is_active_trim_mode() == True:
        return False

    if editorstate.timeline_visible():
        trimmodes.set_no_edit_trim_mode()

    PLAYER().start_variable_speed_playback(speed)

    return True

##############################################################################
# ZERO ARGUMENT HANDLER FUNCTIONS                                            #
##############################################################################

# The contract for each of these zero-argument handler functions is the same:
# - They each accept no arguments
# - They each control some aspect of the program
# - They each try to figure out the context they're operating in, so they
#   can be assigned directly to key presses from a keyboard or other device
# - They each return True if they did something, or False if they didn't

def three_point_overwrite():
    # Key bindings for MOVE MODES and _NO_EDIT modes
    if editorstate.current_is_move_mode() or editorstate.current_is_active_trim_mode() == False:
        tlineaction.three_point_overwrite_pressed()
        return True

    return False

def add_marker():
    if editorstate.timeline_visible():
        tlineaction.add_marker()
        return True

    return False

def append():
    # Key bindings for MOVE MODES and _NO_EDIT modes
    if editorstate.current_is_move_mode() or editorstate.current_is_active_trim_mode() == False:
        tlineaction.append_button_pressed()
        return True

    return False

def append_from_bin():
    # Key bindings for MOVE MODES and _NO_EDIT modes
    if editorstate.current_is_move_mode() or editorstate.current_is_active_trim_mode() == False:
        projectaction.append_selected_media_clips_into_timeline()
        return True

    return False

def clear_io_marks():
    monitorevent.marks_clear_pressed()
    return True

def clear_mark_in():
    monitorevent.mark_in_clear_pressed()
    return True

def clear_mark_out():
    monitorevent.mark_out_clear_pressed()
    return True

def cut():
    tlineaction.cut_pressed()
    return True

def cut_all():
    tlineaction.cut_all_pressed()
    return True

def display_clip_in_monitor():
    if editorstate.timeline_visible():
        updater.display_clip_in_monitor()
        return True

    return False

def display_sequence_in_monitor():
    if not editorstate.timeline_visible():
        updater.display_sequence_in_monitor()
        return True

    return False

def delete():
    # Key bindings for MOVE MODES and _NO_EDIT modes
    if editorstate.current_is_move_mode() or editorstate.current_is_active_trim_mode() == False:
        if editorstate.EDIT_MODE() == editorstate.KF_TOOL:
            kftoolmode.delete_active_keyframe()
            return True
        else:
            # Clip selection and compositor selection are mutually exclusive, 
            # so max one of these will actually delete something
            tlineaction.splice_out_button_pressed()
            compositormodes.delete_current_selection()
            return True

    return False

def enter_edit():
    # Key bindings for keyboard trimming
    if editorstate.current_is_active_trim_mode() == True:
        trimmodes.enter_pressed()
        return True

    return False

def faster():
    monitorevent.l_pressed()
    return True

def insert():
    tlineaction.insert_button_pressed()
    return True

def lift():
    tlineaction.lift_button_pressed()
    return True

def log_range():
    if editorstate.timeline_visible() == False:
        medialog.log_range_clicked()
        return True

    return True

def mark_in():
    monitorevent.mark_in_pressed()
    return True

def mark_out():
    monitorevent.mark_out_pressed()
    return True

def next_cut():
    # Key bindings for MOVE MODES and _NO_EDIT modes
    if editorstate.current_is_move_mode() or editorstate.current_is_active_trim_mode() == False:
        if editorstate.timeline_visible():
            tline_frame = PLAYER().tracktor_producer.frame()
            frame = current_sequence().find_next_cut_frame(tline_frame)
            if frame != -1:
                PLAYER().seek_frame(frame)
                if editorpersistance.prefs.center_on_arrow_move == True:
                    updater.center_tline_to_current_frame()
                return True
        else:
            monitorevent.up_arrow_seek_on_monitor_clip()
            return True

    return False

def next_frame():
    return move_player_position(1)

def nudge_back():
    movemodes.nudge_selection(-1)
    return True

def nudge_back_10():
    movemodes.nudge_selection(-10)
    return True

def nudge_forward():
    movemodes.nudge_selection(1)
    return True

def nudge_forward_10():
    movemodes.nudge_selection(10)
    return True

def open_next():
    projectaction.open_next_media_item_in_monitor()
    return True

def open_prev():
    projectaction.open_prev_media_item_in_monitor()
    return True

def overwrite_range():
    tlineaction.range_overwrite_pressed()
    return True

def play():
    monitorevent.play_pressed()
    return True

def play_pause():
    if PLAYER().is_playing():
        stop()
        return True
    else:
        play()
        return True

    return False

def play_pause_loop_marks():
    if PLAYER().is_playing():
        monitorevent.stop_pressed()
        return True
    else:
        monitorevent.start_marks_looping()
        return True

    return False

def prev_cut():
    # Key bindings for MOVE MODES and _NO_EDIT modes
    if editorstate.current_is_move_mode() or editorstate.current_is_active_trim_mode() == False:
        if editorstate.timeline_visible():
            tline_frame = PLAYER().tracktor_producer.frame()
            frame = current_sequence().find_prev_cut_frame(tline_frame)
            if frame != -1:
                PLAYER().seek_frame(frame)
                if editorpersistance.prefs.center_on_arrow_move == True:
                    updater.center_tline_to_current_frame()  
                return True
        else:
            monitorevent.down_arrow_seek_on_monitor_clip()
            return True

    return False

def prev_frame():
    return move_player_position(-1)

def resync():
    if editorstate.timeline_visible():
        tlineaction.resync_button_pressed()
        return True

    return False

def select_next():
    monitorevent.select_next_clip_for_filter_edit()
    return True

def select_prev():
    monitorevent.select_prev_clip_for_filter_edit()
    return True

def sequence_split():
    if editorstate.timeline_visible():
        tlineaction.sequence_split_pressed()
        return True

    return False

def slower():
    monitorevent.j_pressed()
    return True

def stop():
    monitorevent.stop_pressed()
    return True

def switch_monitor():
    if editorstate.timeline_visible():
        display_clip_in_monitor()
        return True
    else:
        display_sequence_in_monitor()
        return True

    return False

def to_end():
    # Key bindings for MOVE MODES and _NO_EDIT modes
    if editorstate.current_is_move_mode() or editorstate.current_is_active_trim_mode() == False:
        if PLAYER().is_playing():
            monitorevent.stop_pressed()
        PLAYER().seek_end()
        updater.repaint_tline()
        updater.update_tline_scrollbar()
        return True
    else:
        if PLAYER().is_playing():
            monitorevent.stop_pressed()
        gui.editor_window.set_default_edit_tool()
        PLAYER().seek_end()
        updater.repaint_tline()
        updater.update_tline_scrollbar()
        return True

    return False

def toggle_ripple():
    gui.editor_window.toggle_trim_ripple_mode()
    return True

def to_mark_in():
    monitorevent.to_mark_in_pressed()
    return True

def to_mark_out():
    monitorevent.to_mark_out_pressed()
    return True

def to_start():
    # Key bindings for MOVE MODES and _NO_EDIT modes
    if editorstate.current_is_move_mode() or editorstate.current_is_active_trim_mode() == False:
        if PLAYER().is_playing():
            monitorevent.stop_pressed()
        PLAYER().seek_frame(0)
        tlinewidgets.pos = 0
        updater.repaint_tline()
        updater.update_tline_scrollbar()
        return True
    else:
        if PLAYER().is_playing():
            monitorevent.stop_pressed()
        gui.editor_window.set_default_edit_tool()
        PLAYER().seek_frame(0)
        tlinewidgets.pos = 0
        updater.repaint_tline()
        updater.update_tline_scrollbar()
        return True

    return False

def trim_end():
    if editorstate.timeline_visible():
        tlineaction.trim_end_pressed()
        return True

    return False

def trim_start():
    if editorstate.timeline_visible():
        tlineaction.trim_start_pressed()
        return True

    return False

def zoom_in():
    updater.zoom_in()
    return True

def zoom_out():
    updater.zoom_out()
    return True

##############################################################################
# HANDLER LOOKUP BY NAME                                                     #
##############################################################################

def get_handler_by_name(name):
    """
    Get a reference to a zero-argument handler function by name,
    or None if not found.

    Example usage:

    handler = targetactions.get_handler_by_name("play")
    if handler is not None:
        # executes targetactions.play(), by way of function reference
        handler()

    """

    if name in __HANDLER_MAP:
        return __HANDLER_MAP[name]

    return None

# map of target action string -> function reference
__HANDLER_MAP = {
    "3_point_overwrite": three_point_overwrite,
    "add_marker": add_marker,
    "append": append,
    "append_from_bin": append_from_bin,
    "clear_io_marks": clear_io_marks,
    "clear_mark_in": clear_mark_in,
    "clear_mark_out": clear_mark_out,
    "cut": cut,
    "cut_all": cut_all,
    "delete": delete,
    "display_clip_in_monitor": display_clip_in_monitor,
    "display_sequence_in_monitor": display_sequence_in_monitor,
    "enter_edit": enter_edit,
    "faster": faster,
    "insert": insert,
    "lift": lift,
    "log_range": log_range,
    "mark_in": mark_in,
    "mark_out": mark_out,
    "next_cut": next_cut,
    "next_frame": next_frame,
    "nudge_back": nudge_back,
    "nudge_back_10": nudge_back_10,
    "nudge_forward": nudge_forward,
    "nudge_forward_10": nudge_forward_10,
    "open_next": open_next,
    "open_prev": open_prev,
    "overwrite_range": overwrite_range,
    "play": play,
    "play_pause": play_pause,
    "play_pause_loop_marks": play_pause_loop_marks,
    "prev_cut": prev_cut,
    "prev_frame": prev_frame,
    "resync": resync,
    "select_next": select_next,
    "select_prev": select_prev,
    "sequence_split": sequence_split,
    "slower": slower,
    "stop": stop,
    "switch_monitor": switch_monitor,
    "to_end": to_end,
    "toggle_ripple": toggle_ripple,
    "to_mark_in": to_mark_in,
    "to_mark_out": to_mark_out,
    "to_start": to_start,
    "trim_end": trim_end,
    "trim_start": trim_start,
    "zoom_in": zoom_in,
    "zoom_out": zoom_out,
}

