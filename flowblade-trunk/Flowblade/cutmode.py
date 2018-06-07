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
Module handles cut tool funcktionality
"""

import edit
import tlinewidgets
import updater

def mouse_press(event, frame):
    track = tlinewidgets.get_track(event.y)

    # Get index and clip
    index = track.get_clip_index_at(int(frame))
    try:
        clip = track.clips[index]            
        # don't cut blanck clip
        if clip.is_blanck_clip:
            return
    except Exception:
        return # Frame after last clip in track, 

    # Get cut frame in clip frames
    clip_start_in_tline = track.clip_start(index)
    clip_frame = frame - clip_start_in_tline + clip.clip_in

    # Dont edit if frame on cut.
    if clip_frame == clip.clip_in:
        return

    # Do edit
    data = {"track":track,
            "index":index,
            "clip":clip,
            "clip_cut_frame":clip_frame}
    action = edit.cut_action(data)
    action.do_edit()

    updater.repaint_tline()
    
def mouse_move(x, y, frame, state):
    pass
    
def mouse_release(x, y, frame, state):
    pass

