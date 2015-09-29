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
Module handles clip effects editing logic and gui
"""

import gui
from editorstate import current_sequence
import editorstate
import tlinewidgets
import updater

# Edit mode that was active when mode was entered 
_enter_mode = None
_enter_draw_func = None


def maybe_init_for_mouse_press(event, frame):
    print "maybe"
    
    # See if we actually hit a clip
    track = tlinewidgets.get_track(event.y)
    if track == None:
        return
    if track.id < 1 or (track.id >= len(current_sequence().tracks) - 1):
        return False
    clip_index = current_sequence().get_clip_index(track, frame)
    if clip_index == -1:
        return

    clip = track.clips[clip_index]
    
    # See if we're dragging clip end or start
    cut_frame = current_sequence().get_closest_cut_frame(track.id, frame)
    editing_clip_end = True
    if frame >= cut_frame:
        editing_clip_end = False
    else:
        cut_frame = cut_frame - (clip.clip_out - clip.clip_in)

    if editing_clip_end == True:
        bound_end = cut_frame - clip.clip_in + clip.get_length() # get_length() is available media length, not current clip length
        bound_start = cut_frame
    else:
        bound_start = cut_frame - clip.clip_in 
        bound_end =  cut_frame + (clip.clip_out - clip.clip_in)
    
    global _enter_mode, _enter_draw_func, _edit_data

    _enter_mode = editorstate.edit_mode
    editorstate.edit_mode = editorstate.CLIP_END_DRAG
    
    _enter_draw_func = tlinewidgets.canvas_widget.edit_mode_overlay_draw_func

    _edit_data = {}
    _edit_data["track"] = track
    _edit_data["clip_index"] = clip_index
    _edit_data["frame"] = frame
    _edit_data["editing_clip_end"] = editing_clip_end
    _edit_data["bound_end"] = bound_end
    _edit_data["bound_start"] = bound_start
    _edit_data["track_height"] = track.height

    tlinewidgets.set_edit_mode(_edit_data, tlinewidgets.draw_clip_end_drag_overlay)

    gui.editor_window.set_cursor_to_mode()

def mouse_press(event, frame):
    print "press"
    frame = _legalize_frame(frame)
    _edit_data["frame"] = frame
    print frame
    updater.repaint_tline()

def mouse_move(x, y, frame, state):
    print "move"
    frame = _legalize_frame(frame)
    _edit_data["frame"] = frame
    print frame
    updater.repaint_tline()

def mouse_release(x, y, frame, state):
    print "release"

    frame = _legalize_frame(frame)
    _edit_data["frame"] = frame
    
    # do edit
    
    # Go back to enter mode
    editorstate.edit_mode = _enter_mode
    tlinewidgets.set_edit_mode(None, _enter_draw_func)
        
    gui.editor_window.set_cursor_to_mode()
    updater.repaint_tline()

def _legalize_frame(frame):
    start = _edit_data["bound_start"]
    end = _edit_data["bound_end"]

    if _edit_data["editing_clip_end"] == True:
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
    
    

    
