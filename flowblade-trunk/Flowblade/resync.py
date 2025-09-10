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
from editorstate import current_sequence

# Syncing clips
#
# Sync is created by selecting a parent clip for the child clip. Parent clips
# must be on track V1.
#
# Setting sync means calculating and saving the position difference between where first frames of clips
# would be on the timeline.
#
# After every edit sync states of all child clips is calculated, and it 
# gets displayed to the user in the next timeline redraw using red, green and gray colors

# Maps clip -> track
sync_children = {}

# Maps parent -> child. Used to implement dual sync trim feature.
sync_parents = {}

# ----------------------------------------- sync display updating
def clip_added_to_timeline(clip, track):
    if clip.sync_data != None:
        sync_children[clip] = track
        if clip.sync_data.master_clip in sync_parents:
            sync_parents[clip.sync_data.master_clip].append(clip)
        else:
            sync_parents[clip.sync_data.master_clip] = [clip]

def clip_removed_from_timeline(clip):
    try:
        sync_children.pop(clip)
    except KeyError:
        pass

    try:
        sync_parents.pop(clip)
    except KeyError:
        pass

def clip_sync_cleared(clip):
    # This and the method above are called for different purposes, so we'll 
    # keep them separate even though they do the same thing. (???)
    try:
        sync_children.pop(clip)
    except KeyError:
        pass

def sequence_changed(new_sequence):
    global sync_children
    sync_children = {}
    for track in new_sequence.tracks:
        for clip in track.clips:
            clip_added_to_timeline(clip, track)
    calculate_and_set_child_clip_sync_states()

def calculate_and_set_child_clip_sync_states():
    for child_clip, track in sync_children.items():
        child_index = track.clips.index(child_clip)
        child_clip_start = track.clip_start(child_index) - child_clip.clip_in

        parent_clip = child_clip.sync_data.master_clip
        parent_track = child_clip.sync_data.master_clip_track 
        try:
            parent_index = parent_track.clips.index(parent_clip)
        except:
            child_clip.sync_data.sync_state = appconsts.SYNC_PARENT_GONE
            continue

        parent_clip_start = parent_track.clip_start(parent_index) - parent_clip.clip_in
        pos_offset = child_clip_start - parent_clip_start

        if pos_offset == child_clip.sync_data.pos_offset:
            child_clip.sync_data.sync_state = appconsts.SYNC_CORRECT
        else:
            child_clip.sync_data.sync_state = appconsts.SYNC_OFF
        
        child_clip.sync_diff = pos_offset - child_clip.sync_data.pos_offset

def get_resync_data_list_for_clip_list(clips_list):
    # Input is list of (clip, track) tuples
    # Returns list of tuples with data needed to do resync.
    # Return tuples are of type (clip, track, index, child_clip_start_on_timeline, pos_off)
    resync_data = []

    for clip_track_tuple in clips_list:
        child_clip, track = clip_track_tuple
        child_index = track.clips.index(child_clip)
        child_clip_pos_on_tline = track.clip_start(child_index)
        child_clip_start = child_clip_pos_on_tline - child_clip.clip_in

        parent_clip = child_clip.sync_data.master_clip
        parent_track = child_clip.sync_data.master_clip_track
        try:
            parent_index = parent_track.clips.index(parent_clip)
        except:
            # Parent clip no longer awailable
            continue
            
        parent_clip_start = parent_track.clip_start(parent_index) - parent_clip.clip_in
        pos_offset = child_clip_start - parent_clip_start

        resync_data.append((child_clip, track, child_index, child_clip_pos_on_tline, pos_offset))
    
    return resync_data

def get_track_resync_clips_data_list(track):
    # Return value is list of (clip, track) tuples
    clips_data = []
    for clip in track.clips:
        if clip.sync_data != None:
            clips_data.append((clip, track))
    
    return clips_data

def get_box_selection_resync_action_data(box_selection, parent_track, parent_clip):
    tracks_orig_sync_data = []
    tracks_new_sync_data = []
    for track_selection in box_selection.track_selections:

        if track_selection.track_id == parent_track.id:
            continue
            
        orig_sync_data, new_sync_data = _get_box_resync_action_data_for_track(track_selection, parent_track, parent_clip)

        tracks_orig_sync_data.append((track_selection, orig_sync_data))
        tracks_new_sync_data.append((track_selection, new_sync_data))

    return (tracks_orig_sync_data, tracks_new_sync_data)

def _get_box_resync_action_data_for_track(track_selection, parent_track, parent_clip):

    child_track = current_sequence().tracks[track_selection.track_id]
    
    orig_sync_data = {}
    for i in range(track_selection.selected_range_in, track_selection.selected_range_out + 1):
        clip = child_track.clips[i]
        if clip.is_blanck_clip == True:
            continue
        orig_sync_data[clip] = clip.sync_data

    new_sync_data = {}
    for i in range(track_selection.selected_range_in, track_selection.selected_range_out + 1):
        clip = child_track.clips[i]
        if clip.is_blanck_clip == True:
            continue
        clip_start_frame = child_track.clip_start(i)

        parent_index = parent_track.clips.index(parent_clip)

        # Get offset
        child_clip_start = clip_start_frame - clip.clip_in
        parent_clip_start = parent_track.clip_start(parent_index) - parent_clip.clip_in
        pos_offset = child_clip_start - parent_clip_start
        sync_data = (pos_offset, parent_clip, parent_track)

        new_sync_data[clip] = sync_data
    
    return (orig_sync_data, new_sync_data)
    
def get_track_all_resync_action_data(child_track, parent_track):
    orig_sync_data = {}
    for clip in child_track.clips:
        if clip.is_blanck_clip == True:
            continue
        orig_sync_data[clip] = clip.sync_data
    
    new_sync_data = {}
    for i in range(0, len(child_track.clips)):
        clip = child_track.clips[i]
        if clip.is_blanck_clip == True:
            continue
        clip_start_frame = child_track.clip_start(i)
        parent_clip = current_sequence().find_parent_clip_for_clip_start(parent_track, clip_start_frame)
        if parent_clip != None:
            parent_index = parent_track.clips.index(parent_clip)

            # Get offset
            child_clip_start = clip_start_frame - clip.clip_in
            parent_clip_start = parent_track.clip_start(parent_index) - parent_clip.clip_in
            pos_offset = child_clip_start - parent_clip_start
            sync_data = (pos_offset, parent_clip, parent_track)
        else:
            sync_data = (None, None, None)
            
        new_sync_data[clip] = sync_data
    
    return (orig_sync_data, new_sync_data)

def print_sync_children():
    for child_clip, track in sync_children.items():
        print(child_clip.id)
