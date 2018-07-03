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
Module handles Keyframe tool functionality
"""

from editorstate import current_sequence
import tlinewidgets
import updater

OVERLAY_BG = (0.0, 0.0, 0.0, 0.8)
OVERLAY_DRAW_COLOR = (0.0, 0.0, 0.0, 0.8)
EDIT_AREA_HEIGHT = 200

edit_data = None

# ---------------------------------------------- mouse events
def mouse_press(event, frame):

    print "gggg"
    x = event.x
    y = event.y

    # If we have clip being edited and its edit area is hit, we do not need to init data.
    if _clip_is_being_edited() and _clip_edit_area_hit(x, y):
        print "ooooooooooooooooooo"
        return
    
    # Get pressed track
    track = tlinewidgets.get_track(y)  

    # Selecting empty clears selection
    if track == None:
        #clear_selected_clips()
        #pressed_on_selected = False
        _set_no_clip_edit_data()
        updater.repaint_tline()
        return    
    
    # Get pressed clip index
    clip_index = current_sequence().get_clip_index(track, frame)

    # Selecting empty clears selection
    if clip_index == -1:
        #clear_selected_clips()
        #pressed_on_selected = False
        _set_no_clip_edit_data()
        updater.repaint_tline()
        return
    
    print "kkkkkk"

    global edit_data #, pressed_on_selected, drag_disabled
    edit_data = {"draw_function":_tline_overlay,
                 "clip_index":clip_index,
                 "track":track,
                 "mouse_start_x":x,
                 "mouse_start_y":y}
                 
    tlinewidgets.set_edit_mode_data(edit_data)
    updater.repaint_tline()
    
        
def mouse_move(x, y, frame, state):
    pass
    
def mouse_release(x, y, frame, state):
    #global edit_data#, pressed_on_selected, drag_disabled
    #edit_data = None
    pass

# -------------------------------------------- EDIT FUNCTIONS
def _clip_is_being_edited():
    if edit_data == None:
        return False
    if edit_data["clip_index"] == -1:
        return False
    
    return True

def _clip_edit_area_hit(x, y):
    return False

def _set_no_clip_edit_data():
    # set edit data to reflect that no clip is being edited currently.
    global edit_data 
    edit_data = {"draw_function":_tline_overlay,
                 "clip_index":-1,
                 "track":None,
                 "mouse_start_x":-1,
                 "mouse_start_y":-1}

    tlinewidgets.set_edit_mode_data(edit_data)
    
# ----------------------------------------------------------------------- Edit overlay
def _tline_overlay(cr, pos):
    if _clip_is_being_edited() == False:
        return
        
    track = edit_data["track"]
    ty = tlinewidgets._get_track_y(track.id)
    cx_start = tlinewidgets._get_frame_x(track.clip_start(edit_data["clip_index"]))
    clip = track.clips[edit_data["clip_index"]]
    cx_end = tlinewidgets._get_frame_x(track.clip_start(edit_data["clip_index"]) + clip.clip_out - clip.clip_in + 1)  # +1 because out inclusive

    height = EDIT_AREA_HEIGHT

    cr.set_source_rgba(*OVERLAY_BG)
    cr.rectangle(cx_start, ty - height/2, cx_end - cx_start, height)
    cr.fill()
