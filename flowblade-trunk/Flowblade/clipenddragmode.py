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

"""
Module handles clip end dragging edits.
"""

from gi.repository import Gdk

import appconsts
import dualsynctrim
import gui
import edit
from editorstate import current_sequence
import editorstate
import tlinewidgets
import updater

# Edit mode that was active when mode was entered 
_enter_mode = None
_enter_draw_func = None

# we are handling difference between insert on overwrite drags internally in
# this module.
INSERT_DRAG = 0
OVERWRITE_DRAG = 1
_submode = INSERT_DRAG

def get_submode():
    return _sub_mode

def maybe_init_for_mouse_press(event, frame):
    # See if we actually hit a clip
    track = tlinewidgets.get_track(event.y)
    if track == None:
        return
    if track.id < 1 or (track.id >= len(current_sequence().tracks) - 1):
        return
    if track.edit_freedom == appconsts.LOCKED:
        return
    clip_index = current_sequence().get_clip_index(track, frame)
    if clip_index == -1:
        return

    clip = track.clips[clip_index]
    
    if clip.is_blanck_clip:
        return

    cut_frame = current_sequence().get_closest_cut_frame(track.id, frame)

    if (event.get_state() & Gdk.ModifierType.MOD1_MASK):
        _init_overwrite_drag(clip, clip_index, track, frame, cut_frame)
    else:
        _init_insert_drag(clip, clip_index, track, frame, cut_frame)

def _init_insert_drag(clip, clip_index, track, frame, cut_frame):
    global _submode
    _submode = INSERT_DRAG

    # Now we will in fact enter CLIP_END_DRAG edit mode
    # See if we're dragging clip end or start
    editing_clip_end = True
    if frame >= cut_frame:
        editing_clip_end = False
    else:
        cut_frame = cut_frame - (clip.clip_out - clip.clip_in)

    if editing_clip_end == True: # clip end drags
        bound_end = cut_frame - clip.clip_in + clip.get_length() - 1 # get_length() is available media length, not current clip length
        bound_start = cut_frame - 1
        if clip_index == len(track.clips) - 1: # last clip
            bound_end = bound_end - 1
    else: # clip beginning drags
        bound_start = cut_frame - clip.clip_in 
        bound_end = cut_frame + (clip.clip_out - clip.clip_in) + 1

    global _enter_mode, _enter_draw_func, _edit_data

    _enter_mode = editorstate.edit_mode
    editorstate.edit_mode = editorstate.CLIP_END_DRAG
    
    _enter_draw_func = tlinewidgets.canvas_widget.edit_mode_overlay_draw_func

    _edit_data = {}
    _edit_data["track"] = track
    _edit_data["clip_index"] = clip_index
    _edit_data["clip_media_type"] = clip.media_type
    _edit_data["frame"] = frame
    _edit_data["press_frame"] = frame
    _edit_data["editing_clip_end"] = editing_clip_end
    _edit_data["bound_end"] = bound_end
    _edit_data["bound_start"] = bound_start
    _edit_data["clip_end"] = bound_end
    _edit_data["clip_start"] = bound_start
    _edit_data["track_height"] = track.height
    _edit_data["orig_in"] = cut_frame - 1
    _edit_data["orig_out"] = cut_frame + (clip.clip_out - clip.clip_in)
    _edit_data["submode"] = _submode
    _edit_data["cut_frame"] = cut_frame

    dualsynctrim.set_child_clip_end_drag_data(_edit_data, clip)

    _enter_mouse_drag_edit(editing_clip_end)

def _init_overwrite_drag(clip, clip_index, track, frame, cut_frame):

    global _submode
    _submode = OVERWRITE_DRAG
    
    # Now we will in fact enter CLIP_END_DRAG edit mode
    # See if we're dragging clip end or start
    editing_clip_end = True
    edit_frame = cut_frame 
        
    if frame >= cut_frame:
        editing_clip_end = False

    # Can't do overwrite drag on track first clip start or last clip end. 
    if clip_index == 0 and editing_clip_end == False:
        _init_insert_drag(clip, clip_index, track, frame, cut_frame)
        return
    elif clip_index == (len(track.clips) - 1) and editing_clip_end == True:
        _init_insert_drag(clip, clip_index, track, frame, cut_frame)
        return

    from_clip, to_clip = _get_from_clip_and_to_clip(editing_clip_end, track, clip_index)

    # Get edit bounds and clip start/end on tline for draw func
    if editing_clip_end == True: # clip end drags

        clip_start = cut_frame - (clip.clip_out - clip.clip_in)
        clip_end = cut_frame

        to_clip_start = track.clip_start(clip_index + 1) - to_clip.clip_in
        to_clip_end = track.clip_start(clip_index + 1) + to_clip.clip_length() 
        from_clip_start = track.clip_start(clip_index) 
        from_clip_end = track.clip_start(clip_index) + from_clip.get_length() - from_clip.clip_in
    else: # clip beginning drags
        clip_start = cut_frame
        clip_end = cut_frame + (to_clip.clip_out - to_clip.clip_in) + 1
        
        to_clip_start = track.clip_start(clip_index) - to_clip.clip_in
        to_clip_end = track.clip_start(clip_index) + to_clip.clip_length()
        from_clip_start = track.clip_start(clip_index - 1)
        from_clip_end = track.clip_start(clip_index - 1) - from_clip.clip_in + from_clip.get_length() 
    
    if to_clip_start > from_clip_start and to_clip.is_blanck_clip == False:
        bound_start = to_clip_start
    else:        
        bound_start = from_clip_start

    if from_clip_end < to_clip_end:
        bound_end = from_clip_end
    else:
        bound_end = to_clip_end
    
    if editing_clip_end == True and bound_end > to_clip_end:
        bound_end = to_clip_end
        
    if editing_clip_end == False and bound_start < from_clip_start:
        bound_start = from_clip_start

    if to_clip_start > from_clip_start and from_clip.is_blanck_clip == True:
        bound_start = to_clip_start
        
    global _enter_mode, _enter_draw_func, _edit_data

    _enter_mode = editorstate.edit_mode
    editorstate.edit_mode = editorstate.CLIP_END_DRAG

    _enter_draw_func = tlinewidgets.canvas_widget.edit_mode_overlay_draw_func
    
    _edit_data = {}
    _edit_data["track"] = track
    _edit_data["clip_index"] = clip_index
    _edit_data["clip_media_type"] = clip.media_type
    _edit_data["frame"] = frame
    _edit_data["press_frame"] = frame
    _edit_data["edit_frame"] = edit_frame
    _edit_data["editing_clip_end"] = editing_clip_end
    _edit_data["bound_end"] = bound_end
    _edit_data["bound_start"] = bound_start
    _edit_data["clip_end"] = clip_end
    _edit_data["clip_start"] = clip_start
    _edit_data["track_height"] = track.height
    _edit_data["orig_in"] = clip_start - 1
    _edit_data["orig_out"] = clip_end
    _edit_data["submode"] = _submode

    _enter_mouse_drag_edit(editing_clip_end)

def _enter_mouse_drag_edit(editing_clip_end):
    tlinewidgets.set_edit_mode(_edit_data, tlinewidgets.draw_clip_end_drag_overlay)

    if tlinewidgets.pointer_context == appconsts.POINTER_CONTEXT_NONE:
        if editing_clip_end == True:
            tlinewidgets.pointer_context = appconsts.POINTER_CONTEXT_END_DRAG_RIGHT
        else:
            tlinewidgets.pointer_context = appconsts.POINTER_CONTEXT_END_DRAG_LEFT

    gui.editor_window.tline_cursor_manager.set_cursor_to_mode()
    
def _get_from_clip_and_to_clip(editing_clip_end, track, clip_index):
    if editing_clip_end == True:
        from_clip = track.clips[clip_index]
        to_clip = track.clips[clip_index + 1]
    else:
        from_clip = track.clips[clip_index - 1]
        to_clip = track.clips[clip_index]
    
    return (from_clip, to_clip)
    
def mouse_press(event, frame):
    frame = _legalize_frame(frame)
    _edit_data["frame"] = frame

    updater.repaint_tline()

def mouse_move(x, y, frame, state):
    frame = _legalize_frame(frame)
    _edit_data["frame"] = frame
    updater.repaint_tline()

def mouse_release(x, y, frame, state):
    if _submode == INSERT_DRAG:
        _do_insert_trim(x, y, frame, state)
    else:
        _do_overwrite_trim(x, y, frame, state)

def _do_insert_trim(x, y, frame, state):
    frame = _legalize_frame(frame)
    _edit_data["frame"] = frame
    updater.repaint_tline()

    track = _edit_data["track"]
    clip_index = _edit_data["clip_index"]
    clip = track.clips[clip_index]
    orig_in = _edit_data["orig_in"]
    orig_out = _edit_data["orig_out"]
    
    # do edit
    # Dragging clip end
    if _edit_data["editing_clip_end"] == True:
        delta = frame - orig_out
        # Image clip end can be dragged to create a clip of any length.
        if _edit_data["clip_media_type"] == appconsts.IMAGE:
            if clip.clip_in + delta > clip.get_length():
                # We have dragged clip end to create a producer longer 
                # then current producer length.
                #
                # For length changing drags we only do inserts,
                # no blank covering.
                data = {"track":track,
                        "index":clip_index,
                        "clip":clip,
                        "delta":delta}
                action = edit.trim_image_end_beyond_max_length_action(data)
                action.do_edit()

                _exit_clip_end_drag()

                updater.repaint_tline()
                return

        # clip end trim if next clip is not blank or next xlip is last clip
        if ((clip_index == len(track.clips) - 1) or 
            (track.clips[clip_index + 1].is_blanck_clip == False)):
            data = {"track":track,
                    "index":clip_index,
                    "clip":clip,
                    "delta":delta}
            action = edit.trim_last_clip_end_action(data)
            
            if _edit_data["child_clip_trim_data"] == None:
                action.do_edit()
            else:
                sync_trim_action = dualsynctrim.get_one_roll_sync_edit(_edit_data, delta, dualsynctrim.ONE_ROLL_TRIM_END)
                if sync_trim_action != None:
                    actions = [action, sync_trim_action]
                    consolidated_action = edit.ConsolidatedEditAction(actions)
                    consolidated_action.do_consolidated_edit()
                else:
                    action.do_edit()
    
        else: # clip end trim next clip is blank
            blank_clip = track.clips[clip_index + 1]
            blank_clip_length = blank_clip.clip_length()
            data = {"track":track,
                    "index":clip_index,
                    "clip":clip,
                    "blank_clip_length":blank_clip_length,
                    "delta":delta}
            if delta < blank_clip_length: # partial blank overwrite
                action = edit.clip_end_drag_on_blank_action(data)
            else: # full blank replace
                action = edit.clip_end_drag_replace_blank_action(data)

            if _edit_data["child_clip_trim_data"] == None:
                action.do_edit()
            else:
                sync_trim_action = dualsynctrim.get_one_roll_sync_edit(_edit_data, delta, dualsynctrim.ONE_ROLL_TRIM_END)
                if sync_trim_action != None:
                    actions = [action, sync_trim_action]
                    consolidated_action = edit.ConsolidatedEditAction(actions)
                    consolidated_action.do_consolidated_edit()
                else:
                    action.do_edit()
                
    else:# Dragging clip start
        delta = frame - orig_in  - 1 # -1 because..uhh..inclusive exclusive something something
        # prev clip is not blank or first clip
        if ((clip_index == 0) or
            (track.clips[clip_index - 1].is_blanck_clip == False)):
            data = {"track":track,
                    "index":clip_index,
                    "clip":clip,
                    "delta":delta}
            action = edit.trim_start_action(data)
            if _edit_data["child_clip_trim_data"] == None:
                action.do_edit()
            else:
                sync_trim_action = dualsynctrim.get_one_roll_sync_edit(_edit_data, delta, dualsynctrim.ONE_ROLL_TRIM_START)
                if sync_trim_action != None:
                    actions = [action, sync_trim_action]
                    consolidated_action = edit.ConsolidatedEditAction(actions)
                    consolidated_action.do_consolidated_edit()
                else:
                    action.do_edit()
        else: # prev clip is blank
            blank_clip = track.clips[clip_index - 1]
            blank_clip_length = blank_clip.clip_length()
            data = {"track":track,
                    "index":clip_index,
                    "clip":clip,
                    "blank_clip_length":blank_clip_length,
                    "delta":delta}
            if -delta < blank_clip_length: # partial blank overwrite
                action = edit.clip_start_drag_on_blank_action(data)
            else: # full blank replace
                action = edit.clip_start_drag_replace_blank_action(data)

            if _edit_data["child_clip_trim_data"] == None:
                action.do_edit()
            else:
                data = {"track":track,
                        "index":clip_index,
                        "from_clip":blank_clip,
                        "to_clip":clip,
                        "delta":delta,
                        "edit_done_callback": None, # we don't do callback needing this
                        "cut_frame": _edit_data["cut_frame"],
                        "to_side_being_edited":None, # we don't do callback needing this
                        "non_edit_side_blank":True,
                        "first_do":False}  # no callback

                sync_trim_action = dualsynctrim.get_two_roll_sync_edits(data)
                if sync_trim_action != None:
                    actions = [action, sync_trim_action[0]]
                    consolidated_action = edit.ConsolidatedEditAction(actions)
                    consolidated_action.do_consolidated_edit()
                else:
                    action.do_edit()

    _exit_clip_end_drag()

    updater.repaint_tline()

def _do_overwrite_trim(x, y, frame, state):
    frame = _legalize_frame(frame)
    updater.repaint_tline()

    track = _edit_data["track"]
    clip_index = _edit_data["clip_index"]
    editing_clip_end = _edit_data["editing_clip_end"] 
    
    from_clip, to_clip = _get_from_clip_and_to_clip(editing_clip_end, track, clip_index)
    non_edit_side_blank = False
    if (_edit_data["editing_clip_end"] == False) and (track.clips[clip_index - 1].is_blanck_clip == True):
        non_edit_side_blank = True
    elif (_edit_data["editing_clip_end"] == True) and (track.clips[clip_index + 1].is_blanck_clip == True):
        non_edit_side_blank = True

    # If drag covers adjacent clip fully we need to use different edit actions.
    from_clip_start = track.clip_start(track.clips.index(from_clip)) - from_clip.clip_in
    to_clip_end = track.clip_start(track.clips.index(to_clip)) + to_clip.clip_length()

    if editing_clip_end == True and frame == _edit_data["bound_end"] and frame == to_clip_end:
        
        data = {"track":track,
                "clip":to_clip,
                "index":clip_index + 1}
                
        action = edit.cover_delete_fade_out(data) # action was created for another edit but works here too.
        action.do_edit()
        
        _exit_clip_end_drag()
        updater.repaint_tline()
        return
    elif editing_clip_end == False and frame == _edit_data["bound_start"] and frame == from_clip_start:
        data = {"track":track,
                "clip":from_clip,
                "index":clip_index - 1}
                
        action = edit.cover_delete_fade_in(data) # action was created for another edit but works here too.
        action.do_edit()
        
        _exit_clip_end_drag()
        updater.repaint_tline()
        return
        
    # Code here thinks "clip_index" is always index of trimmed clip,
    # but we are using existing edit.tworoll_trim_action() code to do the edit, and 
    # that assumes index to be latter of the to clips.
    if editing_clip_end == True:
        clip_index += 1


    # Get edit data
    delta = frame - _edit_data["edit_frame"]
    data = {"track":track,
            "index":clip_index,
            "from_clip":from_clip,
            "to_clip":to_clip,
            "delta":delta,
            "edit_done_callback":_dummy_cb,
            "cut_frame": _edit_data["edit_frame"],
            "to_side_being_edited":not editing_clip_end,
            "non_edit_side_blank":non_edit_side_blank,
            "first_do":True}

    action = edit.tworoll_trim_action(data)
    action_list = [action]

    sync_actions_list = dualsynctrim.get_two_roll_sync_edits(data)
    if sync_actions_list != None:
        action_list = action_list + sync_actions_list

    edit.do_gui_update = True

    if len(action_list) == 1:
        action.do_edit() # No dual sync edits
    else:
        consolidated_action = edit.ConsolidatedEditAction(action_list)
        consolidated_action.do_consolidated_edit()
            
    _exit_clip_end_drag()

    updater.repaint_tline()

def _exit_clip_end_drag(): 
    # Go back to enter mode
    editorstate.edit_mode = _enter_mode
    tlinewidgets.set_edit_mode(None, _enter_draw_func)
    tlinewidgets.pointer_context = appconsts.POINTER_CONTEXT_NONE
    
    gui.editor_window.tline_cursor_manager.set_cursor_to_mode()
    updater.repaint_tline()

def _legalize_frame(frame):
    start = _edit_data["bound_start"]
    end = _edit_data["bound_end"]

    if _edit_data["editing_clip_end"] == True:
        # Images end can be dragged to be of any length.
        if _edit_data["clip_media_type"] != appconsts.IMAGE:
            if frame > end:
                frame = end
        if frame < (start + 1):
            frame = start + 1
    else:
        if frame > end - 1:
            frame = end - 1

        if frame < start:
            frame = start
    
    return frame

def _dummy_cb(was_redo, cut_frame, delta, track, to_side_being_edited):
    # Edit code we use was made for trim edits and need a callback, but we don't need one here.
    pass
