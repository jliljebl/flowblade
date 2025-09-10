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

import appconsts
import resync

def set_child_clip_trim_data(edit_data, edit_tool):
    if edit_data["to_side_being_edited"] == True:
        parent_clip = edit_data["to_clip"]
    else:
        parent_clip = edit_data["from_clip"]
    
    _set_child_clip_data(edit_data, parent_clip)

def set_child_clip_end_drag_data(edit_data, parent_clip):
    _set_child_clip_data(edit_data, parent_clip)
    
def _set_child_clip_data(edit_data, parent_clip):
    child_clip_sync_items = resync.get_child_clips(parent_clip)
    
    if child_clip_sync_items == None:
        edit_data["child_clip_trim_data"] = None
        return
    
    if len(child_clip_sync_items) > 1:
        edit_data["child_clip_trim_data"] = None
        # TODO: We dont dual trim when clip has multiple children. Set flag for info window.
        return

    edit_data["child_clip_trim_data"] = child_clip_sync_items[0]

def get_clip_end_dual_sync_edit_data(edit_data):
    if edit_data["child_clip_trim_data"] == None:
        return None 
    
    child_clip, child_track = edit_data["child_clip_trim_data"] 
    
    data = {"track":child_track,
            "clip":child_clip,
            "index":child_track.clips.index(child_clip)}
    
    return data
    
