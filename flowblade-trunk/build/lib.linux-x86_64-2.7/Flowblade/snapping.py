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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

"""
This module handles snapping to clip ends while mouse dragging on timeline.
"""

import compositormodes
import editorstate
from editorstate import current_sequence
from editorstate import EDIT_MODE

# These are monkeypatched to have access to tlinewidgets.py state  
_get_frame_for_x_func = None
_get_x_for_frame_func = None

snapping_on = True

_snap_threshold = 6 # in pixels

_snap_happened = False
_last_snap_x = -1


#---------------------------------------------------- interface
def get_snapped_x(x, track, edit_data):
    if snapping_on == False:
        return x
    
    frame = _get_frame_for_x_func(x)

    # Do snaps for relevant edit modes.
    if EDIT_MODE() == editorstate.OVERWRITE_MOVE:
        if editorstate.overwrite_mode_box == True:
            return x
        return _overwrite_move_snap(x, track, frame, edit_data)
    elif EDIT_MODE() == editorstate.CLIP_END_DRAG:
        return _object_end_drag_snap(x, track, frame, edit_data)
    elif EDIT_MODE() == editorstate.COMPOSITOR_EDIT:
        track = current_sequence().tracks[compositormodes.compositor.transition.b_track - 1]
        if compositormodes.sub_mode == compositormodes.TRIM_EDIT:
            return _object_end_drag_snap(x, track, frame, edit_data)
        elif compositormodes.sub_mode == compositormodes.MOVE_EDIT:
            return _compositor_move_snap(x, track, frame, edit_data)
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM or  EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        return _trimming_snap(x, track, frame, edit_data)
    elif EDIT_MODE() ==  editorstate.MULTI_MOVE:
        return _spacer_move_snap(x, track, frame, edit_data)

    # Many edit modes do not have snapping even if snapping is on
    return x

def snap_active():
    return _snap_happened

def get_snap_x():
    return _last_snap_x

def mouse_edit_ended():
    global _snap_happened
    _snap_happened = False


#------------------------------------------- utils funcs
def _get_track_above(track):
    if track.id < len(current_sequence().tracks) - 2:
        return current_sequence().tracks[track.id  + 1]
    else:
        return None
        
def _get_track_below(track):
    if track.id > 1:
        return current_sequence().tracks[track.id  - 1]
    else:
        return None

def _get_track_snapped_x(track, x, frame, frame_x):
    closest_cut_frame = current_sequence().get_closest_cut_frame(track.id, frame)
    if closest_cut_frame == -1:
        return -1
    
    cut_frame_x = _get_x_for_frame_func(closest_cut_frame)
    
    if abs(cut_frame_x - frame_x) < _snap_threshold:
        global _last_snap_x
        _last_snap_x = cut_frame_x
        return x - (frame_x - cut_frame_x)
    else:
        return -1 # no snapping happened

def _three_track_snap(track, x, frame, frame_x):
    snapped_x = -1
    
    track_above = _get_track_above(track)
    track_below = _get_track_below(track)
    
    # Check snapping for mouse track and the tracks beside mouse track
    # Check order: track_above, track_below, track, last in order is preferred if multiple snapping happens
    if track_above != None:
        snapped_x = _get_track_snapped_x(track_above, x, frame, frame_x)
    if track_below != None:
        snapped_next_track_x = _get_track_snapped_x(track_below, x, frame, frame_x)
        if snapped_next_track_x != -1:
            snapped_x = snapped_next_track_x
    snapped_next_track_x = _get_track_snapped_x(track, x, frame, frame_x)
    if snapped_next_track_x != -1:
        snapped_x = snapped_next_track_x

    return snapped_x

def _all_tracks_snap(track, x, frame, frame_x):
    snapped_x = -1
    
    for i in range(1, len(current_sequence().tracks) - 1):
        track = current_sequence().tracks[i]
        snapped_x = _get_track_snapped_x(track, x, frame, frame_x)
        if snapped_x != -1:
            return snapped_x

    return snapped_x
    
def return_snapped_x_or_x(snapped_x, x):
    # Return either original or snapped x
    global _snap_happened
    if snapped_x == -1: # indicates no snap happened
        _snap_happened = False
        return x
    else:
        _snap_happened = True
        return snapped_x
        
#---------------------------------------------------- edit mode snapping funcsd
def _overwrite_move_snap(x, track, frame, edit_data):
    if edit_data == None:
        return x

    press_frame = edit_data["press_frame"]
    first_clip_start = edit_data["first_clip_start"]
    first_clip_frame = first_clip_start + (frame - press_frame)
    first_clip_x = _get_x_for_frame_func(first_clip_frame)

    snapped_x = -1 # if value stays same till end, no snapping has happened
    snapped_x = _three_track_snap(track, x, first_clip_frame, first_clip_x)
            
    # Return either original x or snapped x
    return return_snapped_x_or_x(snapped_x, x)

def _object_end_drag_snap(x, track, frame, edit_data):
    if edit_data == None:
        return x

    frame_x = _get_x_for_frame_func(frame)

    snapped_x = -1  # if value stays same till end, no snapping happened.
    snapped_x = _three_track_snap(track, x, frame, frame_x)
        
    # Return either original or snapped x
    return return_snapped_x_or_x(snapped_x, x)

def _compositor_move_snap(x, track, frame, edit_data):
    if edit_data == None:
        return x

    snapped_x = -1 # if value stays same till end, no snapping happened.

    comp_in_frame = edit_data["clip_in"] + (frame - edit_data["press_frame"])
    comp_in_x = _get_x_for_frame_func(comp_in_frame)

    snapped_x = -1 # if value stys same till end, no snapping has happened
    snapped_x = _three_track_snap(track, x, comp_in_frame, comp_in_x)

    if snapped_x == -1: # indicates no snap happened
        comp_out_frame = edit_data["clip_in"] + (frame - edit_data["press_frame"]) + edit_data["clip_length"] 
        comp_out_x = _get_x_for_frame_func(comp_out_frame)
        snapped_x = _three_track_snap(track, x, comp_out_frame, comp_out_x)
    
    # Return either original x or snapped x
    return return_snapped_x_or_x(snapped_x, x)

def _trimming_snap(x, track, frame, edit_data):
    if edit_data == None:
        return x

    selected_frame = _get_frame_for_x_func(x)
    selected_frame_x = _get_x_for_frame_func(selected_frame)

    snapped_x = -1 # if value stays same till end, no snapping has happened
    snapped_x = _three_track_snap(track, x, selected_frame, selected_frame_x)
    
    return_x = return_snapped_x_or_x(snapped_x, x)
    edit_data["selected_frame"] = _get_frame_for_x_func(return_x) # we need to put snapped frame back into edit data because that is what is used by code elsewhere

    # Return either original x or snapped x
    return return_x

def _spacer_move_snap(x, track, frame, edit_data):
    if edit_data == None:
        return x

    press_frame = edit_data["press_frame"]
    delta = frame - press_frame
    first_moved_frame = edit_data["first_moved_frame"]
    
    move_frame = first_moved_frame + delta
    move_frame_x = _get_x_for_frame_func(move_frame)

    snapped_x = -1 # if value stays same till end, no snapping has happened
    snapped_x = _all_tracks_snap(track, x, move_frame, move_frame_x)
    
    # Return either original or snapped x
    return return_snapped_x_or_x(snapped_x, x)
    
