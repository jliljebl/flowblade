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

edit_data = None

# ---------------------------------------------- mouse events
def mouse_press(event, frame):

    x = event.x
    y = event.y

    global edit_data#, pressed_on_selected, drag_disabled

    # Clear edit data in gui module
    edit_data = None
    tlinewidgets.set_edit_mode_data(edit_data)
    
    # Get pressed track
    track = tlinewidgets.get_track(y)  

    # Selecting empty clears selection
    if track == None:
        #clear_selected_clips()
        #pressed_on_selected = False
        updater.repaint_tline()
        return    
    
    # Get pressed clip index
    clip_index = current_sequence().get_clip_index(track, frame)

    # Selecting empty clears selection
    if clip_index == -1:
        #clear_selected_clips()
        #pressed_on_selected = False
        updater.repaint_tline()
        return
        
    edit_data = {"draw_function":_tline_overlay,
                 "clip_index":track.id,
                 "track":track,
                 "mouse_start_x":x,
                 "mouse_start_y":y}
                 
    tlinewidgets.set_edit_mode_data(edit_data)
    updater.repaint_tline()
    
        
def mouse_move(x, y, frame, state):
    pass
    
def mouse_release(x, y, frame, state):
    global edit_data#, pressed_on_selected, drag_disabled
    edit_data = None
    

# ----------------------------------------------------------------------- Edit overlay
def _tline_overlay(cr, pos):
    print "tline overlay:", pos
