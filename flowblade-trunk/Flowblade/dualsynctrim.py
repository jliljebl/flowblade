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
import edit
import resync


ONE_ROLL_TRIM_LAST_END = 0
ONE_ROLL_TRIM_START = 1
ONE_ROLL_TRIM_END = 2

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

def get_one_roll_sync_edit(edit_data, delta, trim_type):
    if edit_data["child_clip_trim_data"] == None:
        return None

    child_clip, child_track = edit_data["child_clip_trim_data"]

    if trim_type == ONE_ROLL_TRIM_LAST_END:
        if delta > 0 and child_clip.get_length() - child_clip.clip_out < delta:
            return None
        if delta < 0 and child_clip.clip_out - child_clip.clip_in < abs(delta):
            return None
        if delta == 0:
            return None

        data = {"track":child_track,
                "index":child_track.clips.index(child_clip),
                "clip":child_clip,
                "delta":delta,
                "undo_done_callback":None,
                "first_do":False}
        action = edit.trim_last_clip_end_action(data)
        return action

    elif trim_type == ONE_ROLL_TRIM_START:
        if delta > 0 and child_clip.clip_out - child_clip.clip_in < delta:
            return None
        if delta < 0 and child_clip.clip_in < abs(delta):
            return None
        if delta == 0:
            return None
        data = {"track":child_track,
                "index":child_track.clips.index(child_clip),
                "clip":child_clip,
                "delta":delta,
                "undo_done_callback":None,
                "first_do":False}
        action = edit.trim_start_action(data)
        return action

    elif trim_type == ONE_ROLL_TRIM_END:
        if delta > 0 and child_clip.get_length() - child_clip.clip_out < delta:
            return None
        if delta < 0 and child_clip.clip_out - child_clip.clip_in < abs(delta):
            return None
        if delta == 0:
            return None
        data = {"track":child_track,
                "index":child_track.clips.index(child_clip),
                "clip":child_clip,
                "delta":delta,
                "undo_done_callback":None,
                "first_do":False}
        action = edit.trim_end_action(data)
        return action
    return None

"""
def get_clip_end_dual_sync_edit_data(edit_data):
    if edit_data["child_clip_trim_data"] == None:
        return None 
    
    child_clip, child_track = edit_data["child_clip_trim_data"] 
    
    data = {"track":child_track,
            "clip":child_clip,
            "index":child_track.clips.index(child_clip)}
    
    return data
"""

def get_two_roll_sync_edits(edit_data):
    delta = edit_data["delta"]
    from_clip_sync_items = resync.get_child_clips(edit_data["from_clip"])

    if from_clip_sync_items == None or len(from_clip_sync_items) > 1:
        from_clip = from_track = None
    else:
        from_clip, from_track = from_clip_sync_items[0]
        from_index = from_track.clips.index(from_clip) 

    to_clip_sync_items = resync.get_child_clips(edit_data["to_clip"])

    if to_clip_sync_items == None or len(to_clip_sync_items) > 1:
        to_clip = to_track = None
    else:
        to_clip, to_track = to_clip_sync_items[0]
        to_index = to_track.clips.index(to_clip)
        
    
    # CASE: to and from clip on same track immediately one after another
    if to_track != None and from_track != None and to_track == from_track and to_index == from_index + 1:
        data = {"track":to_track,
                "index":to_index,
                "from_clip":from_clip,
                "to_clip":to_clip,
                "delta":edit_data["delta"],
                "edit_done_callback": None, # we don't do callback needing this
                "cut_frame": edit_data["cut_frame"],
                "to_side_being_edited":None, # we don't do callback needing this
                "non_edit_side_blank":False,
                "first_do":False}  # no callback

        sync_trim_legal = check_two_roll_trim_lagality(data)
        if sync_trim_legal == False:
            return None

        action = edit.tworoll_trim_action(data)
        return [action]
    
    actions = []
    
    if from_clip != None:
        if from_index + 1 < len(from_track.clips):
            to_clip_one = from_track.clips[from_index + 1]
            non_edit_side_blank = (to_clip_one.is_blank == True)
            data = {"track":from_track,
                    "index":from_index + 1,
                    "from_clip":from_clip,
                    "to_clip":to_clip_one,
                    "delta":edit_data["delta"],
                    "edit_done_callback": None, # we don't do the callback needing this
                    "cut_frame": edit_data["cut_frame"],
                    "to_side_being_edited":None, # we don't do the callback needing this
                    "non_edit_side_blank":non_edit_side_blank,
                    "first_do":False}  # no callback
            
            if check_two_roll_trim_lagality(data) == True:
                action = edit.tworoll_trim_action(data)
                actions.append(action)
        else:
            do_edit = True
            if delta > 0 and from_clip.get_length() - from_clip.clip_out < delta:
                do_edit = False
            if delta < 0 and from_clip.clip_out - from_clip.clip_in < abs(delta):
                do_edit = False
            if delta == 0:
                do_edit = False
            
            if do_edit == True:
                data = {"track":from_track,
                        "index":from_index,
                        "clip":from_clip,
                        "delta":delta,
                        "undo_done_callback":None,
                        "first_do":False}
                action = edit.trim_last_clip_end_action(data)
                actions.append(action)
                
    if to_clip != None and to_index > 0:
        from_clip_here = to_track.clips[to_index - 1]
        non_edit_side_blank = (from_clip_here.is_blank == True)
        data = {"track":to_track,
                "index":to_index,
                "from_clip":from_clip_here,
                "to_clip":to_clip,
                "delta":edit_data["delta"],
                "edit_done_callback": None, # we don't do the callback needing this
                "cut_frame": edit_data["cut_frame"],
                "to_side_being_edited":None, # we don't do the callback needing this
                "non_edit_side_blank":non_edit_side_blank,
                "first_do":False}  # no callback
        
        if check_two_roll_trim_lagality(data) == True:
            action = edit.tworoll_trim_action(data)
            actions.append(action)
            
    if len(actions) == 0:
        return None
    else:
        return actions

def check_two_roll_trim_lagality(edit_data):
    cut_frame = edit_data["cut_frame"]
    from_clip = edit_data["from_clip"]
    to_clip = edit_data["to_clip"]
    delta = edit_data["delta"]
    
    # Trim_limits frames here are TIMELINE frames, not CLIP frames
    trim_limits = {}

    trim_limits["from_start"] = cut_frame - (from_clip.clip_out - from_clip.clip_in)
    from_length = from_clip.get_length()
    trim_limits["from_end"] = cut_frame - from_clip.clip_out + from_length - 2 # -1 incl, -1 leave one frame, == -2

    if from_clip.is_blanck_clip:
        trim_limits["from_end"]  = 10000000

    trim_limits["to_start"] = cut_frame - to_clip.clip_in
    to_length = to_clip.get_length()
    trim_limits["to_end"] = cut_frame + (to_clip.clip_out - to_clip.clip_in) #- to_clip.clip_in + to_length - 1 # - 1, leave one frame
    if to_clip.is_blanck_clip:
        trim_limits["to_start"] = 0

    if trim_limits["from_start"] > trim_limits["to_start"]:
        trim_limits["both_start"] = trim_limits["from_start"]
    else:
        trim_limits["both_start"] = trim_limits["to_start"]
        
    if trim_limits["to_end"] < trim_limits["from_end"]:
        trim_limits["both_end"] = trim_limits["to_end"]
    else:
        trim_limits["both_end"] = trim_limits["from_end"]

    start_available_range_length = abs(cut_frame - trim_limits["both_start"])
    end_available_range_length = abs(cut_frame - trim_limits["both_end"])

    if start_available_range_length < abs(delta):
        return False
    if end_available_range_length < abs(delta):
        return False

    return True
"""

        from_clip_edit_data = { "track":track,
                                "index":track.clips.index(clip),
                                "clip":clip,
                                "delta":edit_data["delta"],
                                "undo_done_callback":None,
                                "first_do":False}
            
    to_clip_sync_items = resync.get_child_clips(edit_data["to_clip"])
    if to_clip_sync_items == None or len(to_clip_sync_items) > 1:
        to_clip_edit_data = None
    else:
        clip, track = to_clip_sync_items[0]
        to_clip_edit_data = {   "track":track,
                                "index":track.clips.index(clip),
                                "clip":clip,
                                "delta":edit_data["delta"],
                                "undo_done_callback":None,
                                "first_do":False}

    return (from_clip_edit_data, to_clip_edit_data)

"""