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
Handles Overwrite Box tool functionality.
"""

import editorstate
import tlinewidgets
import updater

box_selection_data = None
edit_data = None

def clear_data():
    # these need to cleared when box move tool is activated
    global box_selection_data, edit_data
    box_selection_data = None
    edit_data = None
     
def mouse_press(event, frame):
    global edit_data, box_selection_data
    if box_selection_data == None: # mouse action to select
        press_point = (event.x, event.y)
        
        edit_data = {"action_on":True,
                     "press_point":press_point,
                     "mouse_point":press_point,
                     "box_selection_data":None}
    else: # mouse action to move
        if box_selection_data.is_hit(event.x, event.y) == False:
            # Back to start state
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
    if box_selection_data == None: # mouse action to select
        edit_data["mouse_point"] = (x, y)
       
    else: # mouse move to move
        print "moooooooooooove"
        delta = frame - edit_data["press_frame"]
        edit_data["delta"] = delta

    tlinewidgets.set_edit_mode_data(edit_data)
    updater.repaint_tline()
    
def mouse_release(x, y, frame):
    global box_selection_data, edit_data
    if edit_data == None:
        return
        
    if box_selection_data == None: # mouse action to select
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
    else: # mouse action to move
        delta = frame - edit_data["press_frame"]
        edit_data["delta"] = delta
        # Back to start state
        edit_data = None
        box_selection_data = None
    
    tlinewidgets.set_edit_mode_data(edit_data)
    updater.repaint_tline()


class BoxMoveData:
    """
    This class collects and data needed for boxovewrite moves.
    """
    def __init__(self, p1, p2):
        self.topleft_frame = -1
        self.topleft_track = -1
        self.width_frames = -1
        self.height_tracks = -1
        self.track_selections = []
        self.selected_compositors = []
        
        self._get_selection_data(p1, p2)
    
        print self.__dict__
        
    def _get_selection_data(self,  p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        start_frame = tlinewidgets.get_frame(x1)
        end_frame = tlinewidgets.get_frame(x2) 
        
        track_top = tlinewidgets.get_track(y1).id
        track_bottom = tlinewidgets.get_track(y2).id

        self.topleft_track = track_top
        self.height_tracks = track_top - track_bottom + 1
 
        for i in range(track_bottom, track_top + 1):
            self.track_selections.append(BoxTrackSelection(i, start_frame, end_frame))

        # Get selection bounding box
        self.topleft_frame = 1000000000000
        for track_selection in self.track_selections:
            if track_selection.range_frame_in < self.topleft_frame:
                self.topleft_frame = track_selection.range_frame_in
                
        last_frame = 0
        for track_selection in self.track_selections:
            if track_selection.range_frame_out > last_frame:
                last_frame = track_selection.range_frame_out
        
        self.width_frames = last_frame - self.topleft_frame

    def is_empty(self):
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
    This class collects data on track's box selected clips.
    """
    def __init__(self, i, start_frame, end_frame):
        self.track_id = i
        self.selected_range_in  = -1
        self.selected_range_out = -1
        self.range_frame_in  = -1
        self.range_frame_out = -1
        self.clip_lengths = []
        
        track = editorstate.current_sequence().tracks[i]
        
        # Get range indexes
        self.selected_range_in = editorstate.current_sequence().get_clip_index(track, start_frame)
        
        index_range_out = editorstate.current_sequence().get_clip_index(track, end_frame)
        if index_range_out != -1:
            self.selected_range_out = index_range_out
        else:
            if self.selected_range_in == -1:
                return # track is empty
            # Range ends on last clip
            self.selected_range_out = len(track.clips) - 1
            
        # Get clip lengths
        for i in range(self.selected_range_in, self.selected_range_out + 1):
            clip = track.clips[i]
            self.clip_lengths.append(clip.clip_out - clip.clip_in + 1)
        
        # Get bounding frames
        self.range_frame_in  = track.clip_start(self.selected_range_in)
        self.range_frame_out =  track.clip_start(self.selected_range_out) + self.clip_lengths[-1]
        
        
        
        
