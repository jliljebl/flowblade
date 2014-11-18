"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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

import pygtk
pygtk.require('2.0');
import gtk


import appconsts
import edit
from editorstate import current_sequence
import tlinewidgets
import updater

MAX_DELTA = 100000000
        
edit_data = None
mouse_disabled = True

class MultimoveData:
    """
    This class collects and saves data that enables a "Multi" tool edit to be performed.
    """
    def __init__(self, pressed_track, first_moved_frame, move_all_tracks):
        
        self.first_moved_frame = first_moved_frame
        self.pressed_track_id = pressed_track.id
        self.max_backwards = 0
        self.move_all_tracks = move_all_tracks
        self.trim_blank_indexes = []
        self.track_edit_ops = []
        self.track_affected = []
        self.legal_edit = True
        self._build_move_data()

    def _build_move_data(self):
        # Look at all tracks exept
        tracks = current_sequence().tracks

        # Get per track:
        # * maximum length edit can be done backwards before an overwrite happens
        # * indexes of blanks that are trimmed and/or added/removed,
        #   -1 when no blanks are altered on that track
        track_max_deltas = []
        trim_blank_indexes = []
        for i in range(1, len(tracks) - 1):
            track = tracks[i]
            if len(track.clips) == 0:
                track_max_deltas.append(MAX_DELTA)
                trim_blank_indexes.append(-1)
            else:
                clip_index = current_sequence().get_clip_index(track, self.first_moved_frame)
                first_frame_clip = track.clips[clip_index]
                clip_first_frame = track.clip_start(clip_index)

                # Case: frame after track last clip, no clips are moved
                if clip_index == -1:
                    track_max_deltas.append(MAX_DELTA)
                    trim_blank_indexes.append(-1)
                    continue
        
                # Case: Clip start in same frame as moved clip start 
                if (clip_first_frame == self.first_moved_frame) and (not first_frame_clip.is_blanck_clip):
                    if clip_index  == 0: # First clip on track
                        track_max_deltas.append(0)
                        trim_blank_indexes.append(0)
                    else:
                        # not first/last clip on track
                        prev_clip = track.clips[clip_index - 1]
                        if not prev_clip.is_blanck_clip:
                            # first clip to be moved is tight after clip on first move frame
                            track_max_deltas.append(0)
                            trim_blank_indexes.append(clip_index)
                        else:
                            blank_clip_start_frame = track.clip_start(clip_index + 1)
                            moved_clip_start_frame = track.clip_start(clip_index + 2)
                            track_max_deltas.append(moved_clip_start_frame - blank_clip_start_frame)
                            trim_blank_indexes.append(clip_index - 1) 
                    continue
                    
                # Case: frame on clip 
                if not first_frame_clip.is_blanck_clip:
                    if clip_index  == 0: # First clip on track
                        track_max_deltas.append(0)
                        trim_blank_indexes.append(0)
                    elif clip_index == len(track.clips) - 1: # last clip on track, no clips are moved
                        track_max_deltas.append(MAX_DELTA)
                        trim_blank_indexes.append(-1)
                    else:
                        # not first/last clip on track
                        next_clip = track.clips[clip_index + 1]
                        if not next_clip.is_blanck_clip:
                            # first clip to be moved is tight after clip on first move frame
                            track_max_deltas.append(0)
                            trim_blank_indexes.append(clip_index + 1)
                        else:
                            blank_clip_start_frame = track.clip_start(clip_index + 1)
                            moved_clip_start_frame = track.clip_start(clip_index + 2)
                            track_max_deltas.append(moved_clip_start_frame - blank_clip_start_frame)
                            trim_blank_indexes.append(clip_index + 1) 
                # Case: frame on blank
                else:
                    track_max_deltas.append(track.clips[clip_index].clip_length())
                    trim_blank_indexes.append(clip_index)

        self.trim_blank_indexes = trim_blank_indexes

        # Pressed track max delta trim blank index is calculated differently 
        # (because on pressed track to the hit clip is moved)
        # and existing values overwritten
        track = tracks[self.pressed_track_id]
        clip_index = current_sequence().get_clip_index(track, self.first_moved_frame)
        first_frame_clip = track.clips[clip_index]
        
        if first_frame_clip.is_blanck_clip:
            self.legal_edit = False
            return

        if clip_index == 0:
            max_d = 0
            trim_index = 0
        else:
            prev_clip = track.clips[clip_index - 1]
            if prev_clip.is_blanck_clip == True:
                max_d = prev_clip.clip_length()
                trim_index = clip_index - 1
            else:
                max_d = 0
                trim_index = clip_index
        
        track_max_deltas[self.pressed_track_id - 1] = max_d
        self.trim_blank_indexes[self.pressed_track_id - 1] = trim_index
        
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
        if self.move_all_tracks:
            for i in range(1, len(tracks) - 1):
                self.track_affected.append(True)
        else:
            for i in range(1, len(tracks) - 1):
                self.track_affected.append(False)
            self.track_affected[self.pressed_track_id - 1] = True
                
def mouse_press(event, frame):
    x = event.x
    y = event.y

    global edit_data, mouse_disabled

    # Clear edit data in gui module
    edit_data = None
    mouse_disabled = False
    tlinewidgets.set_edit_mode_data(edit_data)

    # Get pressed track
    track = tlinewidgets.get_track(y)  
    if track == None:
        mouse_disabled = True
        return

    # Get pressed clip index
    clip_index = current_sequence().get_clip_index(track, frame)

    # Selecting empty or blank clip does not define edit
    if clip_index == -1:
        mouse_disabled = True
        return
    pressed_clip = track.clips[clip_index]
    if pressed_clip.is_blanck_clip:
        mouse_disabled = True
        return

    if (event.state & gtk.gdk.CONTROL_MASK):
        move_all = False
    else:
        move_all = True

    first_moved_frame = track.clip_start(clip_index)
    multi_data = MultimoveData(track, first_moved_frame, move_all)
    
    edit_data = {"track_id":track.id,
                 "press_frame":frame,
                 "current_frame":frame,
                 "first_moved_frame":first_moved_frame,
                 "mouse_start_x":x,
                 "mouse_start_y":y,
                 "multi_data":multi_data}

    tlinewidgets.set_edit_mode_data(edit_data)
    updater.repaint_tline()

def mouse_move(x, y, frame, state):
    if mouse_disabled:
        return

    global edit_data
    edit_data["current_frame"] = frame

    updater.repaint_tline()
    
def mouse_release(x, y, frame, state):
    if mouse_disabled:
        return

    global edit_data

    press_frame = edit_data["press_frame"]
    min_allowed_delta = - edit_data["multi_data"].max_backwards
    
    delta = frame - press_frame
    if delta < min_allowed_delta:
        delta = min_allowed_delta
    
    if delta != 0:
        data = {"edit_delta":delta,
                "multi_data":edit_data["multi_data"]}
        action = edit.multi_move_action(data)
        action.do_edit()
    
    edit_data = None
    tlinewidgets.set_edit_mode_data(edit_data)
    
    updater.repaint_tline()

