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

"""
Module handles user edit events for trim, roll and slip trim modes. 
"""

import appconsts
import dialogutils
import edit
import editorpersistance
import editorstate
from editorstate import current_sequence
from editorstate import PLAYER
from editorstate import EDIT_MODE
import gui
import tlinewidgets
import updater


# Default value for pre- and post roll in loop playback
DEFAULT_LOOP_HALF_LENGTH = 25

# Pre- and post roll in loop playback
loop_half_length = DEFAULT_LOOP_HALF_LENGTH

# Data/state for ongoing edit.
edit_data = None
ripple_data = None

# Flag for disabling mouse event
mouse_disabled = False

# Flag for temporary blank needed for one roll trim editing track's last clip's out
last_from_trimmed = False

# Function that sets edit mode when exiting with click on empty
set_exit_mode_func = None

# Function that sets <X>_NO_EDIT mode that displays trim cursor but no edit is under way.
#
# This is used e.g. when user clicks empty and preference is to stay in trim mode, 
# so active edit is exited to <X>_NO_EDIT mode.
#
# This function is set when trim modes are entered to be to the "edit init func for" the entered trim mode.
set_no_edit_mode_func = None

# Sub modes for handling mouse vs. keyboard edits
NOTHING_ON = 0
MOUSE_EDIT_ON = 1
KEYB_EDIT_ON = 2

submode = NOTHING_ON

MAX_DELTA = 100000000

# ------------------------------------ module functions       
def _get_trim_edit(track, frame):
    """
    Return a trim edit for a frame on a track.
    """
    # Trying to trim from frame after last clip will init from-side trim
    # for frame where last clip ends.
    if ((frame >= track.get_length()) 
        and (track.get_length() > 1)):
        cut_frame = track.get_length()
        edit_to_side = False
        return(cut_frame, edit_to_side)

    # Get cut frame for trim
    cut_frame = current_sequence().get_closest_cut_frame(track.id, frame)
    if cut_frame == -1:
        return(-1, None)
    edit_to_side = False
    if frame >= cut_frame:
        edit_to_side = True
    return(cut_frame, edit_to_side)

def _get_trim_limits(cut_frame, from_clip, to_clip):
    """
    NOTE: trim_limits frames here are TIMELINE frames, not CLIP frames
    Returns relevant clip boundaries when doing trim edits.
    - clip handles on both sides of cut
    - clip ends on both sides of cut
    """
    # This is too complex now that roll is handled separately, could be reworked.
    # "both_start", and "both_end" are no longer correct names for range variables since only one clip is
    # needed taken into account when calculating legel trim range.
    trim_limits = {}

    if from_clip == None:
        trim_limits["from_start"] = -1
        trim_limits["from_end"] = -1
        trim_limits["both_start"] = -1
    else:
        trim_limits["from_start"] = cut_frame - from_clip.clip_out
        from_length = from_clip.get_length() # This is available media length, not current clip length
        trim_limits["from_end"] = cut_frame - from_clip.clip_out + from_length - 1
        trim_limits["both_start"] = cut_frame - (from_clip.clip_out - from_clip.clip_in)
    if to_clip == None:
        trim_limits["to_start"] = -1
        trim_limits["to_end"] = -1
        trim_limits["both_end"] = -1
    else:
        trim_limits["to_start"] = cut_frame - to_clip.clip_in
        to_length = to_clip.get_length() # This is available media length, not current clip length
        trim_limits["to_end"] = cut_frame - to_clip.clip_in + to_length
        trim_limits["both_end"] = cut_frame + (to_clip.clip_out - to_clip.clip_in)
    
    return trim_limits

def _get_roll_limits(cut_frame, from_clip, to_clip):
    # Trim_limits frames here are TIMELINE frames, not CLIP frames
    trim_limits = {}

    trim_limits["from_start"] = cut_frame - (from_clip.clip_out - from_clip.clip_in)
    from_length = from_clip.get_length()
    trim_limits["from_end"] = cut_frame - from_clip.clip_out + from_length - 2 # -1 incl, -1 leave one frame, == -2

    if from_clip.is_blanck_clip:
        trim_limits["from_end"]  = 10000000

    trim_limits["to_start"] = cut_frame - to_clip.clip_in
    to_length = to_clip.get_length()
    trim_limits["to_end"] = cut_frame + (to_clip.clip_out - to_clip.clip_in) #- to_clip.clip_in + to_length - 1 # - 1, leave one frame
    if to_clip.is_blanck_clip:
        trim_limits["to_start"] = 0

    if trim_limits["from_start"] > trim_limits["to_start"]:
        trim_limits["both_start"] = trim_limits["from_start"]
    else:
        trim_limits["both_start"] = trim_limits["to_start"]
        
    if trim_limits["to_end"] < trim_limits["from_end"]:
        trim_limits["both_end"] = trim_limits["to_end"]
    else:
        trim_limits["both_end"] = trim_limits["from_end"]

    return trim_limits
    
def _set_edit_data(track, edit_frame, is_one_roll_trim):
    """
    Sets edit mode data used by both trim modes
    """
    # Find index of to-clip of edit
    index = current_sequence().get_clip_index(track, edit_frame)
    
    to_clip = track.clips[index]
    if index > 0:
        from_clip = track.clips[index -1]
    else:
        from_clip = None

    # Trimming last clip on track can only be edited from side
    # but code so farproduces to_clip == last clip, from_clip == None,
    # fix this by setting new values for from_clip and_to clip.
    #
    # we're also getting wrong index from mlt as edit frame == track.get_length()
    if edit_frame == track.get_length():
        global last_from_trimmed
        index = current_sequence().get_clip_index(track, edit_frame - 1)
        last_from_trimmed = True
        from_clip = to_clip
        to_clip = None
    else:
        last_from_trimmed = False

    # Get trimlimits
    if is_one_roll_trim:
        trim_limits = _get_trim_limits(edit_frame, from_clip, to_clip)
    else:
        trim_limits = _get_roll_limits(edit_frame, from_clip, to_clip)
        
    global edit_data
    edit_data = {"track":track.id,
                 "track_object":track,
                 "index":index,
                 "edit_frame":edit_frame,
                 "selected_frame":edit_frame,
                 "trim_limits":trim_limits,
                 "from_clip":from_clip,
                 "to_clip":to_clip}

def _pressed_on_edited_track(y):
    pressed_track = tlinewidgets.get_track(y)
    if ((pressed_track == None) 
        or(pressed_track.id != edit_data["track"])):
        return False
    return True

def _trimmed_clip_is_blank():
    if edit_data["to_side_being_edited"]:
        if edit_data["to_clip"].is_blanck_clip:
            return True
    else:
        if edit_data["from_clip"].is_blanck_clip:
            return True

    return False

def trim_looping_stopped():
    # Reinits current trim mode
    if editorstate.edit_mode == editorstate.ONE_ROLL_TRIM: 
        set_oneroll_mode(edit_data["track_object"], 
                         edit_data["edit_frame"],
                         edit_data["to_side_being_edited"])
    if editorstate.edit_mode == editorstate.TWO_ROLL_TRIM:
        set_tworoll_mode(edit_data["track_object"], 
                         edit_data["edit_frame"])
    if editorstate.edit_mode == editorstate.SLIDE_TRIM:
        set_slide_mode(edit_data["track_object"], 
                         edit_data["reinit_frame"])

def update_cursor_to_mode():
    gui.editor_window.set_cursor_to_mode()

def set_no_edit_trim_mode():
    if editorstate.edit_mode == editorstate.ONE_ROLL_TRIM or \
    editorstate.edit_mode == editorstate.TWO_ROLL_TRIM or \
    editorstate.edit_mode == editorstate.SLIDE_TRIM:
        set_no_edit_mode_func()


#----------------------------------------------------- keyboard events
def left_arrow_pressed(ctrl_pressed):
    global submode
    if submode == MOUSE_EDIT_ON:
        return
        
    submode = KEYB_EDIT_ON
    delta = 1
    if ctrl_pressed:
        delta = 10
        
    if EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        _one_roll_trim_left(delta)
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        _tworoll_trim_left(delta)
    elif EDIT_MODE() == editorstate.SLIDE_TRIM:
        _slide_trim_left(delta)
        
def right_arrow_pressed(ctrl_pressed):
    global submode
    if submode == MOUSE_EDIT_ON:
        return
        
    submode = KEYB_EDIT_ON
    delta = 1
    if ctrl_pressed:
        delta = 10
        
    if EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        _one_roll_trim_right(delta)
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        _tworoll_trim_right(delta)
    elif EDIT_MODE() == editorstate.SLIDE_TRIM:
        _slide_trim_right(delta)

def enter_pressed():
    global submode
    if submode != KEYB_EDIT_ON:
        return

    if EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        _one_roll_enter_edit()
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        _tworoll_enter_edit()
    elif EDIT_MODE() == editorstate.SLIDE_TRIM:
        _slide_enter_edit()

    submode = NOTHING_ON

def _one_roll_trim_left(delta):
    # Get legal edit frame for overlay display
    global edit_data
    frame = edit_data["selected_frame"] - delta
    frame = _legalize_one_roll_trim(frame, edit_data["trim_limits"])
    edit_data["selected_frame"] = frame
    gui.monitor_widget.set_edit_tline_frame(frame, frame - edit_data["edit_frame"])
    
    PLAYER().seek_frame(frame)
    
def _one_roll_trim_right(delta):
    # Get legal edit frame for overlay display
    global edit_data
    frame = edit_data["selected_frame"] + delta
    frame = _legalize_one_roll_trim(frame, edit_data["trim_limits"])
    edit_data["selected_frame"] = frame
    gui.monitor_widget.set_edit_tline_frame(frame, frame - edit_data["edit_frame"])
    
    PLAYER().seek_frame(frame)
    
def _one_roll_enter_edit():
    frame = edit_data["selected_frame"]
    _do_one_roll_trim_edit(frame)

def _tworoll_trim_left(delta):
    global edit_data
    frame = edit_data["selected_frame"] - delta
    frame = _legalize_two_roll_trim(frame, edit_data["trim_limits"])
    edit_data["selected_frame"] = frame

    gui.monitor_widget.set_edit_tline_frame(frame, frame - edit_data["edit_frame"])
    gui.monitor_widget.update_roll_match_frame()
    
    PLAYER().seek_frame(frame)

def _tworoll_trim_right(delta):
    global edit_data
    frame = edit_data["selected_frame"] + delta
    frame = _legalize_two_roll_trim(frame, edit_data["trim_limits"])
    edit_data["selected_frame"] = frame

    gui.monitor_widget.set_edit_tline_frame(frame, frame - edit_data["edit_frame"])
    gui.monitor_widget.update_roll_match_frame()
    
    PLAYER().seek_frame(frame)

def _tworoll_enter_edit():
    _do_two_roll_edit(edit_data["selected_frame"])

def _slide_trim_left(delta):
    global edit_data
    try:
        frame = edit_data["keyboard_selected_frame"]
        edit_data["keyboard_selected_frame"] = frame - delta
    except:
        try:
            edit_data["keyboard_selected_frame"] = edit_data["press_start"] - delta
        except:
            trim_limits = edit_data["trim_limits"]
            edit_data["press_start"] = trim_limits["clip_start"] + 1 # this can be anything the relevant thing here is mouse delta
            edit_data["keyboard_selected_frame"] = edit_data["press_start"] - delta
    
    total_delta = edit_data["press_start"] - edit_data["keyboard_selected_frame"]
    gui.monitor_widget.set_slip_edit_tline_frame(edit_data["clip"], total_delta)
        
    display_frame = _update_slide_trim_for_mouse_frame(edit_data["keyboard_selected_frame"])
    PLAYER().seek_frame(display_frame)

def _slide_trim_right(delta):
    global edit_data
    try:
        frame = edit_data["keyboard_selected_frame"]
        edit_data["keyboard_selected_frame"] = frame + delta
    except:
        try:
            edit_data["keyboard_selected_frame"] = edit_data["press_start"] + delta
        except:
            trim_limits = edit_data["trim_limits"]
            edit_data["press_start"] = trim_limits["clip_start"] + 1 # this can be anything the relevant thing here is mouse delta
            edit_data["keyboard_selected_frame"] = edit_data["press_start"] + delta

    total_delta = edit_data["press_start"] - edit_data["keyboard_selected_frame"]
    gui.monitor_widget.set_slip_edit_tline_frame(edit_data["clip"], total_delta)

    display_frame = _update_slide_trim_for_mouse_frame(edit_data["keyboard_selected_frame"])
    PLAYER().seek_frame(display_frame)

def _slide_enter_edit():
    _do_slide_edit()
    
# ------------------------------------- ONE ROLL TRIM EVENTS
def set_oneroll_mode(track, current_frame=-1, editing_to_clip=None):
    """
    Sets one roll mode
    """
    if track == None:
        return False

    if track.id < 1 or (track.id >= len(current_sequence().tracks) - 1):
        return False

    if current_frame == -1: # from button, ctrl + mouse calls with frame
        current_frame = PLAYER().producer.frame() + 1 # +1 because cut frame selects previous clip

    if current_frame >= track.get_length():
        return False

    edit_frame, to_side_being_edited = _get_trim_edit(track, current_frame)
    
    if edit_frame == -1:
        return False

    # hack fix for last clip out trim. If frame pointer not at very end of clip
    # the other functions for getting trim frame given +1 too much 
    if edit_frame > track.get_length():
        edit_frame = track.get_length()

    if editing_to_clip != None: # This is set when mode reset after edit or after undo or redo
                                # _get_trim_edit() might give different(wrong) clip being edited
                                # because cut is now at a different place.
        to_side_being_edited = editing_to_clip

    _set_edit_data(track, edit_frame, True)

    # Init ripple data if needed
    global ripple_data
    ripple_data = None
    if editorstate.trim_mode_ripple == True:
        ripple_data = RippleData(track, edit_frame)

    global edit_data
    # Add ripple data 
    edit_data["ripple_data"] = ripple_data
    
    # Set side being edited to default to-side
    edit_data["to_side_being_edited"] = to_side_being_edited

    # Set start frame bound for ripple mode edits
    if editorstate.trim_mode_ripple == True:
        ripple_start_bound = edit_frame - ripple_data.max_backwards

        # Case: editing to-clip
        if edit_data["to_side_being_edited"]:
            ripple_end_bound = edit_frame + ripple_data.max_backwards
            edit_data["trim_limits"]["ripple_display_end"] = edit_data["trim_limits"]["both_end"] 
            if edit_data["trim_limits"]["both_end"] > ripple_end_bound:
                edit_data["trim_limits"]["both_end"] = ripple_end_bound
        # Case: editing from-clip
        else:
            ripple_start_bound = edit_frame - ripple_data.max_backwards
            edit_data["trim_limits"]["ripple_display_start"] = edit_data["trim_limits"]["both_start"] 
            if edit_data["trim_limits"]["both_start"] < ripple_start_bound: # name "both_start"] is artifact fromearlier when trimlimits were used for both "trim and "roll" edits
                edit_data["trim_limits"]["both_start"] = ripple_start_bound
    else:
        edit_data["trim_limits"]["ripple_display_end"] = -1
        edit_data["trim_limits"]["ripple_display_start"] = -1
            
    current_sequence().clear_hidden_track()

    # Cant't trim a blank clip. Blank clips are special in MLT and can't be
    # made to do things that are needed in trim.
    if _trimmed_clip_is_blank():
        set_exit_mode_func()
        primary_txt = _("Can't ONE ROLL TRIM blank clips.")
        secondary_txt = _("You can use MOVE OVERWRITE or TWO ROLL TRIM edits instead\nto get the desired change.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return False
        
    # Give timeline widget needed data
    if editorstate.trim_mode_ripple == False:
        tlinewidgets.set_edit_mode(edit_data,
                                   tlinewidgets.draw_one_roll_overlay)
    else:
        tlinewidgets.set_edit_mode(edit_data,
                                   tlinewidgets.draw_one_roll_overlay_ripple)

    # Set clip as special producer on hidden track and display current frame 
    # from it.
    trim_limits = edit_data["trim_limits"]
    if edit_data["to_side_being_edited"]:
        clip = edit_data["to_clip"]
        clip_start = trim_limits["to_start"]
    else:
        clip = edit_data["from_clip"]
        clip_start = trim_limits["from_start"]

    # Init trim view layout
    if track.type == appconsts.VIDEO and clip.media_type != appconsts.PATTERN_PRODUCER:
        if edit_data["to_side_being_edited"]:
            gui.monitor_widget.set_start_trim_view(edit_data["from_clip"], clip_start)
        else:
            gui.monitor_widget.set_end_trim_view(edit_data["to_clip"], clip_start)
        gui.monitor_widget.set_edit_tline_frame(current_frame, current_frame - edit_frame)
    else:
        gui.monitor_widget.set_default_view()
   
    # Set interactive trimview on hidden track
    if clip.media_type != appconsts.PATTERN_PRODUCER:
        current_sequence().display_trim_clip(clip.path, clip_start, None, clip.ttl) # file producer
    else:
        current_sequence().display_trim_clip(None, clip_start, clip.create_data, None) # pattern producer

    PLAYER().seek_frame(edit_frame)
    return True

def oneroll_trim_press(event, frame):
    """
    User presses mouse when in one roll mode.
    """
    global mouse_disabled, submode

    if not _pressed_on_edited_track(event.y):
        track = tlinewidgets.get_track(event.y)
        success = set_oneroll_mode(track, frame)
        if not success:
            if editorpersistance.prefs.empty_click_exits_trims == True:
                set_exit_mode_func(True) # further mouse events are handled at editevent.py
            else:
                set_no_edit_mode_func() # further mouse events are handled at editevent.py
        else:
            submode = MOUSE_EDIT_ON # to stop entering keyboard edits until mouse released
            if not editorpersistance.prefs.quick_enter_trims:
                # new trim inited, editing non-active until release
                tlinewidgets.trim_mode_in_non_active_state = True
                gui.tline_canvas.widget.queue_draw()
                gui.editor_window.set_tline_cursor(editorstate.ONE_ROLL_TRIM_NO_EDIT)
                mouse_disabled = True
            else:
                # new trim inited, active immediately
                oneroll_trim_move(event.x, event.y, frame, None)
                gui.tline_canvas.widget.queue_draw()
        return
        
    if not _pressed_on_one_roll_active_area(frame):
        track = tlinewidgets.get_track(event.y)
        success = set_oneroll_mode(track, frame)
        if not success:
            if editorpersistance.prefs.empty_click_exits_trims == True:
                set_exit_mode_func(True) # further mouse events are handled at editevent.py
            else:
                set_no_edit_mode_func() # no furter mouse events will come here
        else:
            submode = MOUSE_EDIT_ON # to stop entering keyboard edits until mouse released
            if not editorpersistance.prefs.quick_enter_trims:
                # new trim inited, editing non-active until release
                tlinewidgets.trim_mode_in_non_active_state = True
                gui.tline_canvas.widget.queue_draw()
                gui.editor_window.set_tline_cursor(editorstate.ONE_ROLL_TRIM_NO_EDIT)
                mouse_disabled = True
            else:
                # new trim inited, active immediately
                oneroll_trim_move(event.x, event.y, frame, None)
                gui.tline_canvas.widget.queue_draw()
        return

    # Get legal edit delta and set to edit mode data for overlay draw
    global edit_data
    frame = _legalize_one_roll_trim(frame, edit_data["trim_limits"])
    edit_data["selected_frame"] = frame

    PLAYER().seek_frame(frame)

def oneroll_trim_move(x, y, frame, state):
    """
    User moves mouse when in one roll mode.
    """
    if mouse_disabled:
        return

    # Get legal edit frame for overlay display
    global edit_data
    frame = _legalize_one_roll_trim(frame, edit_data["trim_limits"])
    edit_data["selected_frame"] = frame
    gui.monitor_widget.set_edit_tline_frame(frame, frame - edit_data["edit_frame"])

    PLAYER().seek_frame(frame)
    
def oneroll_trim_release(x, y, frame, state):
    """
    User releases mouse when in one roll mode.
    """
    global mouse_disabled, submode
    submode = NOTHING_ON # we can now enter keyboard edits 
    if mouse_disabled:
        mouse_disabled = False
        # we may have been in non active state because the clip being edited was changed
        gui.editor_window.set_cursor_to_mode()
        tlinewidgets.trim_mode_in_non_active_state = False 
        gui.tline_canvas.widget.queue_draw()
        return
    
    gui.monitor_widget.one_roll_mouse_release(edit_data["edit_frame"], frame - edit_data["edit_frame"])
    tlinewidgets.pointer_context = appconsts.POINTER_CONTEXT_NONE

    _do_one_roll_trim_edit(frame)

def _do_one_roll_trim_edit(frame):
    # Get legal edit delta and set to edit mode data for overlay draw
    global edit_data
    frame = _legalize_one_roll_trim(frame, edit_data["trim_limits"])
    delta = frame - edit_data["edit_frame"]

    # case: editing from-side of last clip
    global last_from_trimmed
    if last_from_trimmed:
        last_from_trimmed = False
        if editorstate.trim_mode_ripple == False:
            data = {"track":edit_data["track_object"],
                    "index":edit_data["index"],
                    "clip":edit_data["from_clip"],
                    "delta":delta,
                    "undo_done_callback":clip_end_first_do_done,
                    "first_do":True}
            action = edit.trim_last_clip_end_action(data)
            last_from_trimmed = False
            action.do_edit()
        else:
            data = {"track":edit_data["track_object"],
                    "index":edit_data["index"],
                    "clip":edit_data["from_clip"],
                    "edit_delta":delta,
                    "undo_done_callback":clip_end_first_do_done,
                    "first_do":True,
                    "multi_data":ripple_data}
            action = edit.ripple_trim_last_clip_end_action(data)
            action.do_edit()
        # Edit is reinitialized in callback from edit action one_roll_trim_undo_done
    # case: editing to-side of cut
    elif edit_data["to_side_being_edited"]:
        if editorstate.trim_mode_ripple == False:
            data = {"track":edit_data["track_object"],
                    "index":edit_data["index"],
                    "clip":edit_data["to_clip"],
                    "delta":delta,
                    "undo_done_callback":one_roll_trim_undo_done,
                    "first_do":True}
            action = edit.trim_start_action(data)
            action.do_edit()
            # Edit is reinitialized in callback from edit action one_roll_trim_undo_done
        else:
            data = {"track":edit_data["track_object"],
                    "index":edit_data["index"],
                    "clip":edit_data["to_clip"],
                    "edit_delta":delta,
                    "undo_done_callback":one_roll_trim_undo_done,
                    "first_do":True,
                    "multi_data":ripple_data}
            action = edit.ripple_trim_start_action(data)
            action.do_edit()
    # case: editing from-side of cut
    else:
        if editorstate.trim_mode_ripple == False:
            data = {"track":edit_data["track_object"],
                    "index":edit_data["index"] - 1,
                    "clip":edit_data["from_clip"],
                    "delta":delta,
                    "undo_done_callback":one_roll_trim_undo_done,
                    "first_do":True}
            action = edit.trim_end_action(data)
            action.do_edit()
            # Edit is reinitialized in callback from edit action one_roll_trim_undo_done
        else:
            data = {"track":edit_data["track_object"],
                    "index":edit_data["index"] - 1,
                    "clip":edit_data["from_clip"],
                    "edit_delta":delta,
                    "undo_done_callback":one_roll_trim_undo_done,
                    "first_do":True,
                    "multi_data":ripple_data}
            action = edit.ripple_trim_end_action(data)
            action.do_edit()
            
def oneroll_play_pressed():
    # Start trim preview playback loop
    current_sequence().hide_hidden_clips()
    PLAYER().start_loop_playback(edit_data["edit_frame"], loop_half_length, edit_data["track_object"].get_length())

def oneroll_stop_pressed():
    # Stop trim preview playback loop
    PLAYER().stop_loop_playback(trim_looping_stopped)

def oneroll_prev_pressed():
    _do_one_roll_trim_edit(edit_data["edit_frame"] - 1)
    
def oneroll_next_pressed():
    _do_one_roll_trim_edit(edit_data["edit_frame"] + 1)

def one_roll_trim_undo_done(track, index, is_to_side_edit):
    """
    WRONG NAME FOR FUNCTION
    Callback if initial edit done. Undo and redo do not cause this to be called
    """
    # reinit edit mode to correct side
    frame = track.clip_start(index)
    success = set_oneroll_mode(track, frame, is_to_side_edit)
    if not success:
        set_no_edit_mode_func()

def clip_end_first_do_done(track):
    frame = track.get_length() - 1
    set_oneroll_mode(track, frame, False)

def _legalize_one_roll_trim(frame, trim_limits):
    """
    Keeps one roll trim selection in legal edit area.
    """
    # Case: editing to-clip
    if edit_data["to_side_being_edited"]:
        first = trim_limits["to_start"]
        last = trim_limits["both_end"] 
    # Case: editing from-clip
    else:
        first = trim_limits["both_start"]
        last = trim_limits["from_end"] 
        
    if frame <= first:
        frame = first
        tlinewidgets.trim_status = appconsts.ON_FIRST_FRAME
    elif frame >= last:
        frame = last
        tlinewidgets.trim_status = appconsts.ON_LAST_FRAME
    else:
        tlinewidgets.trim_status = appconsts.ON_BETWEEN_FRAME

    return frame

def _pressed_on_one_roll_active_area(frame):
    trim_limits = edit_data["trim_limits"]
    if edit_data["to_side_being_edited"]:
        if frame < trim_limits["to_start"]:
            return False
        if frame > trim_limits["both_end"]:
            return False
        if frame < edit_data["edit_frame"]:
            return False
    else:
        if frame < trim_limits["both_start"]:
            return False
        if frame > trim_limits["from_end"]:
            return False
        if frame > edit_data["edit_frame"]:
            return False
    
    return True



class RippleData:
    """
    This class collects and saves data needed for ripple mode trims.
    """
    def __init__(self, pressed_track, trim_frame):
        
        self.trim_frame = trim_frame
        self.pressed_track_id = pressed_track.id
        self.max_backwards = 0
        self.trim_blank_indexes = []
        self.track_edit_ops = []
        self.track_affected = []
        self.track_blank_end_offset = []
        self.moved_compositors_destroy_ids = [] # we cannot rely on object identies with compositors because they get destroyd and recreated in undo/redo actions
        self.legal_edit = True
        self._build_ripple_data()

    def _build_ripple_data(self):
        tracks = current_sequence().tracks

        # Look at all tracks exept hidden and black
        # Get per track:
        # * maximum length trim can be done backwards or forwards before an overwrite happens
        # * indexes of blanks that are trimmed and/or added/removed,
        #   -1 when no blanks are altered on that track
        #
        # Method for setting moved clips and max deltas:
        # * if track has 0 or 1 clip(s) and no blanks, track is ignored
        # * if track length < first_moved_frame, track is ignored
        # * if track has no blanks but track length > first_moved_frame, max delta is 0
        # * if track has blanks, max delta is closest blank length
        
        track_max_deltas = []
        trim_blank_indexes = []
        for i in range(1, len(tracks) - 1):
            track = tracks[i]
            # Case: 0 or 1 clips
            if len(track.clips) < 2:
                track_max_deltas.append(MAX_DELTA)
                trim_blank_indexes.append(-1)
                self.track_blank_end_offset.append(None)
            else:
                # Case: 2 - n clips
                clip_index = current_sequence().get_clip_index(track, self.trim_frame)
                first_frame_clip = track.clips[clip_index]
                
                # Case: frame after track last clip
                if clip_index == -1:
                    track_max_deltas.append(MAX_DELTA)
                    trim_blank_indexes.append(-1)
                    self.track_blank_end_offset.append(None)
                    continue

                # Case: frame is on blank 
                if first_frame_clip.is_blanck_clip:
                    track_max_deltas.append(track.clips[clip_index].clip_length())
                    trim_blank_indexes.append(clip_index)
                    self.track_blank_end_offset.append(self.get_track_blank_end_offset(track, clip_index))
                else:
                    # Case: frame is on media clip
                    
                    # Get closest blank clip index
                    closest_blank_index = -1
                    closest_blank_distance = MAX_DELTA
                    for i in range(0, len(track.clips)):
                        blank =  track.clips[i]
                        if blank.is_blanck_clip == False:
                            continue #  Clip is media clip, we're looking for closest blank
                        
                        blank_first_frame = track.clip_start(i)
                        blank_last_frame = blank_first_frame + blank.clip_length()
                        
                        # Clip before trimmed timeline frame, distance is from blank last frame
                        if blank_last_frame <= self.trim_frame:
                            if self.trim_frame - blank_last_frame < closest_blank_distance:
                                closest_blank_distance = self.trim_frame - blank_last_frame
                                closest_blank_index = i

                        # Clip after trimmed timeline frame, distance is from blank first frame
                        elif blank_first_frame >= self.trim_frame: 
                            if blank_last_frame - self.trim_frame < closest_blank_distance:
                                closest_blank_distance = blank_last_frame - self.trim_frame 
                                closest_blank_index = i
                        else:
                            print "_build_ripple_data(): supposedly unreachable case hit"
                        
                    
                    # Case: no blanks found on track
                    if closest_blank_index == -1:
                        track_max_deltas.append(0)
                        trim_blank_indexes.append(clip_index)
                        self.track_blank_end_offset.append(self.get_track_blank_end_offset(track, clip_index - 1))
                    # Case closest blank found
                    else:
                        track_max_deltas.append(track.clips[closest_blank_index].clip_length())
                        trim_blank_indexes.append(closest_blank_index)
                        self.track_blank_end_offset.append(self.get_track_blank_end_offset(track, closest_blank_index))

        self.trim_blank_indexes = trim_blank_indexes

        # Pressed track does not ripple, pressed track trim edit defines ripple direction and amount
        track_max_deltas[self.pressed_track_id - 1] = MAX_DELTA
        self.trim_blank_indexes[self.pressed_track_id - 1] = -1
    
        # Smallest track delta is the max number of frames 
        # the edit can be done backwards
        smallest_max_delta = MAX_DELTA
        for i in range(1, len(tracks) - 1):
            d = track_max_deltas[i - 1]
            if d < smallest_max_delta:
                smallest_max_delta = d
        self.max_backwards = smallest_max_delta

        # Track have different ways the edit will need to be applied
        # make a list of those
        track_edit_ops = []
        for i in range(1, len(tracks) - 1):
            track = tracks[i]
            track_delta = track_max_deltas[i - 1]
            if track_delta == 0:
                track_edit_ops.append(appconsts.MULTI_ADD_TRIM)
            elif track_delta == MAX_DELTA:
                track_edit_ops.append(appconsts.MULTI_NOOP)
            elif self.max_backwards > 0 and track_delta == self.max_backwards:
                track_edit_ops.append(appconsts.MULTI_TRIM_REMOVE)
            else:
                track_edit_ops.append(appconsts.MULTI_TRIM)
        self.track_edit_ops = track_edit_ops

        # Make list of boolean values of tracks affected by the edit
        for i in range(1, len(tracks) - 1):
            self.track_affected.append(True)
        self.track_affected[self.pressed_track_id - 1] = True

        # Make list compositors that are moved with ripple edit
        tracks_compositors = self.get_tracks_compositors_list()
        affected_compositors_destroy_ids = []
        for i in range(1, len(tracks) - 1):
            if self.trim_blank_indexes[i - 1] == -1:
                continue # This track is not affected by edit
            
            # Get affect compositors on this track
            track = tracks[i]
            compositors = tracks_compositors[i - 1]
            for j in range(0, len(compositors)):
                comp = compositors[j]
                first_affected_blank_index = self.trim_blank_indexes[i - 1]
                first_affected_frame = tracks[i].clip_start(first_affected_blank_index + 1)
                if comp.clip_in >= first_affected_frame:
                    affected_compositors_destroy_ids.append(comp.destroy_id)
        
        self.moved_compositors_destroy_ids = affected_compositors_destroy_ids
        

    def get_track_blank_end_offset(self, track, blank_index):
        blank_end_frame = track.clip_start(blank_index + 1)
        return blank_end_frame - self.trim_frame

    def get_tracks_compositors_list(self):
        tracks_compositors_list = []
        for track_index in range(1, len(current_sequence().tracks) - 1):
            tracks_compositors_list.append(current_sequence().get_track_compositors(track_index))
        
        return tracks_compositors_list
    
#---------------------------------------- TWO ROLL TRIM EVENTS
def set_tworoll_mode(track, current_frame = -1):
    """
    Sets two roll mode
    """     
    if track == None:
        return False
    
    current_frame_trim_view_fix = 0
    if current_frame == -1:
        current_frame = PLAYER().producer.frame() + 1 # +1 because cut frame selects previous clip
        current_frame_trim_view_fix = -1 # when initing trim view the +1 for current frame needs to be undone

    if current_frame >= track.get_length():
        return False
        
    current_sequence().clear_hidden_track()
    
    edit_frame, to_side_being_edited = _get_trim_edit(track, current_frame)
    
    # Trying to two roll edit last clip's out frame inits one roll trim mode
    # via programmed click.
    if edit_frame >= track.get_length():
        return False

    try:
        _set_edit_data(track, edit_frame, False)
    except: # fails for last clip
        return False

    if edit_frame == 0:
        _tworoll_init_failed_window()
        return False

    global edit_data
    if edit_data["from_clip"] == None:
        _tworoll_init_failed_window()
        return False

    # Force edit side to be on non-blanck side
    if to_side_being_edited and edit_data["to_clip"].is_blanck_clip:
        to_side_being_edited = False
    if ((to_side_being_edited == False)
        and edit_data["from_clip"].is_blanck_clip):
        to_side_being_edited = True

    edit_data["to_side_being_edited"] = to_side_being_edited
    
    # Find out if non edit side is blank
    non_edit_side_blank = False
    if to_side_being_edited and edit_data["from_clip"].is_blanck_clip:
        non_edit_side_blank = True
    if ((to_side_being_edited == False) and edit_data["to_clip"].is_blanck_clip):
        non_edit_side_blank = True        
    edit_data["non_edit_side_blank"] = non_edit_side_blank
        
    # Give timeline widget needed data
    tlinewidgets.set_edit_mode(edit_data, tlinewidgets.draw_two_roll_overlay)

    # Set clip as producer on hidden track and display current frame 
    # from it.
    trim_limits = edit_data["trim_limits"]
    if edit_data["to_side_being_edited"]:
        clip = edit_data["to_clip"]
        clip_start = trim_limits["to_start"]
    else:
        clip = edit_data["from_clip"]
        clip_start = trim_limits["from_start"]

    # Init two roll trim view layout
    if track.type == appconsts.VIDEO and clip.media_type != appconsts.PATTERN_PRODUCER and editorstate.show_trim_view == appconsts.TRIM_VIEW_ON:
        if edit_data["to_side_being_edited"]:
            gui.monitor_widget.set_roll_trim_right_active_view(edit_data["from_clip"], clip_start)
        else:
            gui.monitor_widget.set_roll_trim_left_active_view(edit_data["to_clip"], clip_start)
        gui.monitor_widget.set_edit_tline_frame(current_frame + current_frame_trim_view_fix, 
                                                current_frame + current_frame_trim_view_fix - edit_frame)
    else:
        gui.monitor_widget.set_default_view()

    # Set interactive trim view clip on hidden track
    if clip.media_type != appconsts.PATTERN_PRODUCER:
        current_sequence().display_trim_clip(clip.path, clip_start, None, clip.ttl) # File producer
    else:
        current_sequence().display_trim_clip(None, clip_start, clip.create_data, None) # pattern producer
        
    PLAYER().seek_frame(edit_frame)
    updater.repaint_tline()

    return True

def _tworoll_init_failed_window():
    primary_txt = _("Initializing TWO ROLL TRIM failed")
    secondary_txt = _("You are attempting TWO ROLL TRIM at a position in the timeline\nwhere it can't be performed.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

def tworoll_trim_press(event, frame):
    """
    User presses mouse when in two roll mode.
    """   
    if not _pressed_on_edited_track(event.y):
        _attempt_reinit_tworoll(event, frame)
        return

    if not _pressed_on_two_roll_active_area(frame):
        _attempt_reinit_tworoll(event, frame)
        return

    global edit_data, submode
    submode = MOUSE_EDIT_ON

    frame = _legalize_two_roll_trim(frame, edit_data["trim_limits"])
    edit_data["selected_frame"] = frame
    PLAYER().seek_frame(frame)

def _attempt_reinit_tworoll(event, frame):
        track = tlinewidgets.get_track(event.y)
        success = set_tworoll_mode(track, frame)
        if not success:
            if editorpersistance.prefs.empty_click_exits_trims == True:
                set_exit_mode_func(True) # further mouse events are handled at editevent.py
            else:
                set_no_edit_mode_func() # further mouse events are handled at editevent.py
        else:
            if not editorpersistance.prefs.quick_enter_trims:
                # new trim inited, editing non-active until release
                global mouse_disabled
                tlinewidgets.trim_mode_in_non_active_state = True
                gui.tline_canvas.widget.queue_draw()
                gui.editor_window.set_tline_cursor(editorstate.TWO_ROLL_TRIM_NO_EDIT)
                mouse_disabled = True
            else:
                # new trim inited, active immediately
                tworoll_trim_move(event.x, event.y, frame, None)
                gui.tline_canvas.widget.queue_draw()
                
def tworoll_trim_move(x, y, frame, state):
    """
    User moves mouse when in two roll mode.
    """
    if mouse_disabled:
        return

    global edit_data
    frame = _legalize_two_roll_trim(frame, edit_data["trim_limits"])
    edit_data["selected_frame"] = frame

    gui.monitor_widget.set_edit_tline_frame(frame, frame - edit_data["edit_frame"])
    gui.monitor_widget.update_roll_match_frame()

    PLAYER().seek_frame(frame)
    
def tworoll_trim_release(x, y, frame, state):
    """
    User releases mouse when in two roll mode.
    """
    global mouse_disabled
    if mouse_disabled == True:
        # we may have been in non active state because the clip being edited was changed
        gui.editor_window.set_cursor_to_mode()
        tlinewidgets.trim_mode_in_non_active_state = False 
        gui.tline_canvas.widget.queue_draw()
        mouse_disabled = False
        return

    global edit_data, submode
    submode = NOTHING_ON # we can now enter keyboard edits
     
    frame = _legalize_two_roll_trim(frame, edit_data["trim_limits"])
    edit_data["selected_frame"] = frame

    gui.monitor_widget.set_edit_tline_frame(frame, frame - edit_data["edit_frame"])
    gui.monitor_widget.update_roll_match_frame()
    
    _do_two_roll_edit(frame)

def tworoll_play_pressed():
    current_sequence().hide_hidden_clips()
    PLAYER().start_loop_playback(edit_data["edit_frame"], loop_half_length, edit_data["track_object"].get_length())

def tworoll_stop_pressed():
    PLAYER().stop_loop_playback(trim_looping_stopped)

def tworoll_prev_pressed():    
    new_cut_frame = _legalize_two_roll_trim(edit_data["edit_frame"] - 1, \
                                            edit_data["trim_limits"])
    _do_two_roll_edit(new_cut_frame)
    
def tworoll_next_pressed():
    new_cut_frame = _legalize_two_roll_trim(edit_data["edit_frame"] + 1, \
                                            edit_data["trim_limits"])
    _do_two_roll_edit(new_cut_frame)

def _do_two_roll_edit(new_cut_frame):
    """
    Called from drag-release and next, prev button presses.
    """
    # Only do two roll edit if both clips exist
    if ((edit_data["from_clip"] != None) and 
            (edit_data["to_clip"] != None)):
        # Get edit data
        delta = new_cut_frame - edit_data["edit_frame"]
        data = {"track":edit_data["track_object"],
                "index":edit_data["index"],
                "from_clip":edit_data["from_clip"],
                "to_clip":edit_data["to_clip"],
                "delta":delta,
                "edit_done_callback":two_rolledit_done,
                "cut_frame":edit_data["edit_frame"],
                "to_side_being_edited":edit_data["to_side_being_edited"],
                "non_edit_side_blank":edit_data["non_edit_side_blank"],
                "first_do":True}
                
        action = edit.tworoll_trim_action(data)
        edit.do_gui_update = True
        action.do_edit()

def two_rolledit_done(was_redo, cut_frame, delta, track, to_side_being_edited):
    """
    Set two roll playback to correct place after edit or redo or undo.
    Callback from edit action.
    """
    # This is done because cut_frame is the frame where cut was before original edit.
    if was_redo:
        frame = cut_frame + delta
    else:
        frame = cut_frame

    # Calculated frame always reinits in to side, so we need to 
    # step one back to reinit on from side if we did the edit from that side
    if to_side_being_edited != True:
        frame = frame - 2
        if frame < 0:
            frame = 0

    # seek and reinit
    PLAYER().seek_frame(frame)
    set_tworoll_mode(track)

def two_roll_audio_sync_edit_done(cut_frame, delta, track, to_side_being_edited):
    """
    Set two roll playback to correct place after edit or redo or undo.
    Callback from edit action.
    """
    frame = cut_frame + delta

    # Calculated frame always reinits on to side, so we need to 
    # step one back to reinit on from side if we did the edit from that side
    if to_side_being_edited != True:
        frame = frame - 1
        if frame < 0:
            frame = 0

    # seek and reinit
    PLAYER().seek_frame(frame)
    set_tworoll_mode(track)

def _legalize_two_roll_trim(frame, trim_limits):
    """
    Keeps two roll trim selection in legal edit area.
    """
    first = trim_limits["both_start"]
    last = trim_limits["both_end"]

    if frame <= first:
        frame = first
        tlinewidgets.trim_status = appconsts.ON_FIRST_FRAME
    elif frame >= last:
        frame = last
        tlinewidgets.trim_status = appconsts.ON_LAST_FRAME
    else:
        tlinewidgets.trim_status = appconsts.ON_BETWEEN_FRAME
        
    return frame

def _pressed_on_two_roll_active_area(frame):
    first, last = _get_two_roll_first_and_last()
    if frame < first:
        return False
    if frame > last:
        return False

    return True

def _get_two_roll_first_and_last():
    first = -1
    last = -1
    
    index = edit_data["index"]
    track = edit_data["track_object"]
    first = track.clip_start(index - 1) + 1
    end_clip = track.clips[index]
    last = track.clip_start(index) + end_clip.clip_out - end_clip.clip_in
                 
    return (first, last)

#---------------------------------------- SLIP ROLL TRIM EVENTS
def set_slide_mode(track, current_frame):
    """
    Sets SLIP tool mode
    """
    if track == None:
        return None

    if current_frame > track.get_length() - 1:
        return False

    current_sequence().clear_hidden_track()
    
    view_frame, start_frame_being_viewed = _get_trim_edit(track, current_frame)

    # _get_trim_edit() gives first frame belonging to next clip if press closer to end frame of clip
    if not start_frame_being_viewed:
        view_frame = view_frame -1

    try:
        _set_slide_mode_edit_data(track, view_frame)
    except:
        return False

    if edit_data["clip"].is_blanck_clip:
        return False

    clip = edit_data["clip"]
    clip_start = edit_data["trim_limits"]["clip_start"]
    edit_data["start_frame_being_viewed"] = start_frame_being_viewed
    fake_current_frame = clip_start
    if not start_frame_being_viewed:
        fake_current_frame = clip_start + clip.clip_out - clip.clip_in
        
    # Give timeline widget needed data
    tlinewidgets.set_edit_mode(edit_data, tlinewidgets.draw_slide_overlay)
    tlinewidgets.fake_current_frame = fake_current_frame

    # Set clip as producer on hidden track and display current frame from it.
    clip = edit_data["clip"]
    clip_start = 0 # we'll calculate the offset from actual position of clip on timeline to display the frame displayed after sliding

    # Init two roll trim view layout
    if track.type == appconsts.VIDEO and clip.media_type != appconsts.PATTERN_PRODUCER and editorstate.show_trim_view == appconsts.TRIM_VIEW_ON:
        if not start_frame_being_viewed:
            gui.monitor_widget.set_slip_trim_right_active_view(edit_data["clip"])
            gui.monitor_widget.set_edit_tline_frame(clip.clip_out, 0)
        else:
            gui.monitor_widget.set_slip_trim_left_active_view(edit_data["clip"])
            gui.monitor_widget.set_edit_tline_frame(clip.clip_in, 0)
    else:
        gui.monitor_widget.set_default_view()

    # Set interactive trim view clip on hidden track
    if clip.media_type != appconsts.PATTERN_PRODUCER:
        current_sequence().display_trim_clip(clip.path, clip_start, None, clip.ttl) # File producer
    else:
        current_sequence().display_trim_clip(None, clip_start, clip.create_data, None) # pattern producer
        
    if start_frame_being_viewed:
        PLAYER().seek_frame(clip.clip_in)
    else:
        PLAYER().seek_frame(clip.clip_out)

    updater.repaint_tline()

    return True

def _set_slide_mode_edit_data(track, edit_frame):
    """
    Sets edit mode data used by both trim modes
    """
    index = current_sequence().get_clip_index(track, edit_frame)
    if index == -1:
        index = len(track.clips) - 1

    clip = track.clips[index]

    trim_limits = {}
    trim_limits["start_handle"] = clip.clip_in
    trim_limits["end_handle"] = clip.get_length() - clip.clip_out
    trim_limits["clip_start"] = track.clip_start(index)
    trim_limits["media_length"] = clip.get_length()

    global edit_data
    edit_data = {"track":track.id, # tlinewidgets.py uses this to get draw y  
                 "track_object":track,
                 "index":index,
                 "trim_limits":trim_limits,
                 "mouse_delta":0,
                 "clip":clip}

def _attempt_reinit_slide(event, frame):
    track = tlinewidgets.get_track(event.y)
    success = set_slide_mode(track, frame)
    if not success:
        if editorpersistance.prefs.empty_click_exits_trims == True:
            set_exit_mode_func(True) # further mouse events are handled at editevent.py
        else:
            set_no_edit_mode_func() # further mouse events are handled at editevent.py
    else:
        if not editorpersistance.prefs.quick_enter_trims:
            gui.tline_canvas.widget.queue_draw()
            gui.editor_window.set_tline_cursor(editorstate.SLIDE_TRIM_NO_EDIT)
            tlinewidgets.trim_mode_in_non_active_state = True
            global mouse_disabled
            mouse_disabled = True
        else:
            # new trim inited, active immediately
            global edit_data
            edit_data["press_start"] = frame
            slide_trim_move(event.x, event.y, frame, None)
            gui.tline_canvas.widget.queue_draw()

def slide_trim_press(event, frame):
    global edit_data
    edit_data["press_start"] = frame

    if not _pressed_on_edited_track(event.y):
        _attempt_reinit_slide(event, frame)
        return
    
    if frame > tlinewidgets.get_track(event.y).get_length():
        if editorpersistance.prefs.empty_click_exits_trims == True:
            set_exit_mode_func(True) # further mouse events are handled at editevent.py
        else:
            set_no_edit_mode_func() # further mouse events are handled at editevent.py
        return

    if not _pressed_on_slide_active_area(frame):
        _attempt_reinit_slide(event, frame)
        return

    global submode
    submode = MOUSE_EDIT_ON
    
    display_frame = _update_slide_trim_for_mouse_frame(frame)
    PLAYER().seek_frame(display_frame)

def slide_trim_move(x, y, frame, state):
    if mouse_disabled:
        return

    mouse_delta = edit_data["press_start"] - frame
    gui.monitor_widget.set_slip_edit_tline_frame(edit_data["clip"], mouse_delta)
        
    display_frame = _update_slide_trim_for_mouse_frame(frame)
    PLAYER().seek_frame(display_frame)

def slide_trim_release(x, y, frame, state):
    global mouse_disabled
    if mouse_disabled == True:
        # we may have been in non active state because the clip being edited was changed
        gui.editor_window.set_cursor_to_mode()
        tlinewidgets.trim_mode_in_non_active_state = False 
        gui.tline_canvas.widget.queue_draw()
        mouse_disabled = False
        return
    
    display_frame = _update_slide_trim_for_mouse_frame(frame)
    PLAYER().seek_frame(display_frame)

    global edit_data, submode
    submode = NOTHING_ON # we can now enter keyboard edits
    display_frame = _update_slide_trim_for_mouse_frame(frame)
    PLAYER().seek_frame(display_frame)
    _do_slide_edit()
    
def _update_slide_trim_for_mouse_frame(frame):
    global edit_data
    clip = edit_data["clip"]
    mouse_delta = edit_data["press_start"] - frame

    # make sure slided clip area stays inside available media
    # fix_diff, herp, derp ... jeessus
    fix_diff_in = _legalize_slide(clip.clip_in + mouse_delta, clip)
    fix_diff_out = _legalize_slide(clip.clip_out + mouse_delta, clip)

    if fix_diff_in == 0 and fix_diff_out != 0:
        fix_diff = fix_diff_out
    elif  fix_diff_in != 0 and fix_diff_out == 0:
        fix_diff = fix_diff_in
    elif  fix_diff_in != 0 and fix_diff_out != 0:
        if abs(fix_diff_in) > abs(fix_diff_out):
            fix_diff = fix_diff_in
        else:
            fix_diff = fix_diff_out
    else:
        fix_diff = 0

    edit_data["mouse_delta"] = mouse_delta - fix_diff
    
    # Get display frame on hidden track
    if edit_data["start_frame_being_viewed"]:
        display_frame = clip.clip_in + mouse_delta - fix_diff
    else:
        display_frame = clip.clip_out + mouse_delta - fix_diff

    return display_frame

def _pressed_on_slide_active_area(frame):
    trim_limits = edit_data["trim_limits"]
    clip_start = trim_limits["clip_start"]
    clip = edit_data["clip"]
    clip_end = clip_start + clip.clip_out - clip.clip_in
    
    if frame >= clip_start and frame < clip_end:
        return True
    else:
        return False

def _legalize_slide(media_frame, clip):
    if media_frame < 0:
        return media_frame
    if media_frame >= clip.get_length():
        return media_frame - clip.get_length() - 1 # -1 out inclusive.
    return 0

def _do_slide_edit():
    """
    Called from drag-release and next, prev button presses.
    """
    # "track","clip","delta","index","first_do","first_do_callback"
    data = {"track":edit_data["track_object"],
            "index":edit_data["index"],
            "clip":edit_data["clip"],
            "delta":edit_data["mouse_delta"],
            "first_do_callback":_slide_trim_first_do_callback,
            "start_frame_being_viewed":edit_data["start_frame_being_viewed"],
            "first_do":True}

    action = edit.slide_trim_action(data)
    edit.do_gui_update = True
    action.do_edit()

def _slide_trim_first_do_callback(track, clip, index, start_frame_being_viewed):
    # If in one roll mode, reinit edit mode to correct side
    if start_frame_being_viewed:
        frame = track.clip_start(index) + 1 # +1 because cut frame selects previous clip
    else:
        frame = track.clip_start(index) + clip.clip_out - clip.clip_in - 1
    set_slide_mode(track, frame)

def slide_play_pressed():
    current_sequence().hide_hidden_clips()

    clip_start = edit_data["trim_limits"]["clip_start"]
    clip = edit_data["clip"]
            
    if edit_data["start_frame_being_viewed"]:
        frame = clip_start + 1 # +1 because cut frame selects previous clip
    else:
        frame = clip_start + clip.clip_out - clip.clip_in - 1
    edit_data["reinit_frame"] = frame
    PLAYER().start_loop_playback(frame, loop_half_length, edit_data["track_object"].get_length())

def slide_stop_pressed():
    PLAYER().stop_loop_playback(trim_looping_stopped)

def slide_prev_pressed():    
    global edit_data
    edit_data["mouse_delta"] = -1
    _do_slide_edit()
    
def slide_next_pressed():
    global edit_data
    edit_data["mouse_delta"] = 1
    _do_slide_edit()
