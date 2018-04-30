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
Handles Box tool functionality.
"""

import edit
import editorstate
from editorstate import current_sequence
import tlinewidgets
import updater

box_selection_data = None
edit_data = None

def clear_data():
    # These need to cleared when box tool is activated
    global box_selection_data, edit_data
    box_selection_data = None
    edit_data = None
     
def mouse_press(event, frame):
    global edit_data, box_selection_data
    if box_selection_data == None: # mouse action is to select
        press_point = (event.x, event.y)
        
        edit_data = {"action_on":True,
                     "press_point":press_point,
                     "mouse_point":press_point,
                     "box_selection_data":None}
    else: # mouse action is to move
        if box_selection_data.is_hit(event.x, event.y) == False:
            # Back to start state if selection box missed
            edit_data = None
            box_selection_data = None
        else:
            edit_data = {"action_on":True,
                         "press_frame":frame,
                         "delta":0,
                         "box_selection_data":box_selection_data}
    
    tlinewidgets.set_edit_mode(edit_data, tlinewidgets.draw_overwrite_box_overlay)
    updater.repaint_tline()
    
def mouse_move(x, y, frame):
    global edit_data
    if edit_data == None:
        return
    if box_selection_data == None: # mouse action is to select
        edit_data["mouse_point"] = (x, y)
       
    else: # mouse action is to move
        delta = frame - edit_data["press_frame"]
        edit_data["delta"] = delta

    tlinewidgets.set_edit_mode_data(edit_data)
    updater.repaint_tline()
    
def mouse_release(x, y, frame):
    global box_selection_data, edit_data
    if edit_data == None:
        return
        
    if box_selection_data == None: # mouse action is to select
        box_selection_data = BoxMoveData(edit_data["press_point"], (x, y))
        if box_selection_data.is_empty() == False:
            edit_data = {"action_on":True,
                         "press_frame":frame,
                         "delta":0,
                         "box_selection_data":box_selection_data}
        else:
            box_selection_data = None
            edit_data = {"action_on":False,
                         "press_frame":-1,
                         "delta":0,
                         "box_selection_data":box_selection_data}
    else: # mouse action is to move
        delta = frame - edit_data["press_frame"]
        edit_data["delta"] = delta

        # Do edit
        data = {"box_selection_data":box_selection_data,
                "delta":delta}
        action = edit.box_overwrite_move_action(data)
        action.do_edit()
        
        # Back to start state
        edit_data = None
        box_selection_data = None
    
    tlinewidgets.set_edit_mode_data(edit_data)
    updater.repaint_tline()


class BoxMoveData:
    """
    This class collects data needed for Box tool edits.
    """
    def __init__(self, p1, p2):
        self.topleft_frame = -1
        self.topleft_track = -1
        self.width_frames = -1
        self.height_tracks = -1
        self.track_selections = []
        self.selected_compositors = []
        
        self._get_selection_data(p1, p2)

    def _get_selection_data(self,  p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        start_frame = tlinewidgets.get_frame(x1)
        end_frame = tlinewidgets.get_frame(x2) 
        
        track_top_index = self.get_bounding_track_index(y1, tlinewidgets.get_track(y1))
        track_bottom_index = self.get_bounding_track_index(y2, tlinewidgets.get_track(y2))

        self.topleft_track = track_top_index - 1

        # Get compositors
        for i in range(track_bottom_index + 1, track_top_index):
            track_compositors = current_sequence().get_track_compositors(i)
            for comp in track_compositors:
                if comp.clip_in >= start_frame and comp.clip_out < end_frame:
                    self.selected_compositors.append(comp)
        
        # Get BoxTrackSelection objects
        for i in range(track_bottom_index + 1, track_top_index):
            self.track_selections.append(BoxTrackSelection(i, start_frame, end_frame))

        # Drop empty tracks from bottom up
        while len(self.track_selections) > 0:
            if self.track_selections[0].is_empty() == True:
                self.track_selections.pop(0)
            else:
                track_bottom_index = self.track_selections[0].track_id
                break
                
        # Drop empty tracks from top down
        while len(self.track_selections) > 0:
            if self.track_selections[-1].is_empty() == True:
                self.track_selections.pop(-1)
            else:
                self.topleft_track = self.track_selections[-1].track_id
                break

        self.height_tracks = self.topleft_track - track_bottom_index + 1# self.topleft_track is inclusive to height, track_bottom_index is eclusive to height
        
        # Get selection bounding box
        self.topleft_frame = 1000000000000
        for track_selection in self.track_selections:
            if track_selection.range_frame_in != -1:
                if track_selection.range_frame_in < self.topleft_frame:
                    self.topleft_frame = track_selection.range_frame_in
                
        last_frame = 0
        for track_selection in self.track_selections:
            if track_selection.range_frame_out != -1:
                if track_selection.range_frame_out > last_frame:
                    last_frame = track_selection.range_frame_out
        
        self.width_frames = last_frame - self.topleft_frame
                   
    def get_bounding_track_index(self, mouse_y, tline_track):
        if tline_track == None:
            if mouse_y < tlinewidgets.REF_LINE_Y:
                return len(current_sequence().tracks) # mouse pressed above all tracks
            else:
                return 0 # mouse pressed below all tracks
        else:
            return tline_track.id

    def is_empty(self):
        if len(self.track_selections) == 0:
            return True
        
        return False

    def is_hit(self, x, y):
        hit_frame = tlinewidgets.get_frame(x)
        hit_track = tlinewidgets.get_track(y).id

        if ((hit_frame >= self.topleft_frame and hit_frame < self.topleft_frame + self.width_frames) and
            (hit_track <= self.topleft_track and hit_track > self.topleft_track - self.height_tracks)):
                return True
                
        return False


class BoxTrackSelection:
    """
    This class collects data on track's Box selected clips.
    """
    def __init__(self, i, start_frame, end_frame):
        self.track_id = i
        self.selected_range_in  = -1
        self.selected_range_out = -1
        self.range_frame_in  = -1
        self.range_frame_out = -1
        self.clip_lengths = []
        self.clip_is_media = []
        
        track = editorstate.current_sequence().tracks[i]
        
        # Get start range index, outer selection required
        start_bound_index = editorstate.current_sequence().get_clip_index(track, start_frame)
        
        if start_bound_index == -1:
            return # Selection starts after end of track contents, selection is empty

        if start_bound_index != 0:
            self.selected_range_in = start_bound_index + 1
            if self.selected_range_in == len(current_sequence().tracks):
                return # box selection was on last clip, nothing is elected
        else:
            if start_frame == 0:
                self.selected_range_in = 0 # first clip on timeline can be selected by selecting frame 0, no outer selection required here
            else:
                self.selected_range_in = start_bound_index + 1
                if self.selected_range_in == len(current_sequence().tracks):
                    return # box selection was on last clip, nothing is elected
        
        # Get end range index, outer selection required
        end_bound_index = editorstate.current_sequence().get_clip_index(track, end_frame)
        if end_bound_index != -1:
            self.selected_range_out = end_bound_index - 1
            if self.selected_range_out  < 0:
                return # range end was on first clip, nothing was selected
        else:
            if self.selected_range_in == -1:
                return # track is empty
            # Range ends on last clip
            self.selected_range_out = len(track.clips) - 1

        # Drop blanks from start
        blanks_stripped_start = self.selected_range_in
        for i in range(self.selected_range_in, self.selected_range_out + 1):
            if track.clips[i].is_blanck_clip == True:
                blanks_stripped_start = i + 1
            else:
                break
        self.selected_range_in = blanks_stripped_start
        if self.selected_range_in > self.selected_range_out:
            return # the 1 cli in selection range is blank

        # Drop blanks from end
        blanks_stripped_end = self.selected_range_out
        for i in range(self.selected_range_out, self.selected_range_in - 1, - 1):
            if track.clips[i].is_blanck_clip == True:
                blanks_stripped_end = i - 1
            else:
                break
        self.selected_range_out = blanks_stripped_end
            
        # Get clip lengths
        for i in range(self.selected_range_in, self.selected_range_out + 1):
            clip = track.clips[i]
            self.clip_lengths.append(clip.clip_out - clip.clip_in + 1)
            self.clip_is_media.append(clip.is_blanck_clip == False)

        # Get bounding frames
        self.range_frame_in  = track.clip_start(self.selected_range_in)
        self.range_frame_out =  track.clip_start(self.selected_range_out) + self.clip_lengths[-1]

    def is_empty(self):
        if len(self.clip_lengths) == 0:
            return True

        return False


