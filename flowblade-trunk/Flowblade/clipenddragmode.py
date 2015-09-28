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

from editorstate import current_sequence
import editorstate
import tlinewidgets

# Edit mode that was active when mode was entered 
_enter_mode = None

def maybe_init_for_mouse_press(event, frame):
    print "maybe"
    # See if we actually hit a clip
    track = tlinewidgets.get_track(event.y)
    if track == None:
        return
    clip_index = current_sequence().get_clip_index(track, frame)
    if clip_index == -1:
        return
    
    print "CLIP_END_DRAG active"
    global _enter_mode
    _enter_mode = editorstate.edit_mode
    editorstate.edit_mode = editorstate.CLIP_END_DRAG

def mouse_press(event, frame):
    print "press"

def mouse_move(x, y, frame, state):
    print "move"

def mouse_release(x, y, frame, state):
    print "release"
    editorstate.edit_mode = _enter_mode
    
