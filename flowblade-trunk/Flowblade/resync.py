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
# gets displayd to the user in the next timeline redraw using red, green and gray colors

# Maps clip -> track
sync_children = {}

# ----------------------------------------- sync display updating
def clip_added_to_timeline(clip, track):
    if clip.sync_data != None:
        sync_children[clip] = track

def clip_removed_from_timeline(clip):
    try:
        sync_children.pop(clip)
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
    parent_track = current_sequence().first_video_track()
    for child_clip, track in sync_children.iteritems():
        child_index = track.clips.index(child_clip)
        child_clip_start = track.clip_start(child_index) - child_clip.clip_in

        #print child_clip.id
        parent_clip = child_clip.sync_data.master_clip
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

def get_resync_data_list():
    # Returns list of tuples with data needed to do resync
    # Return tuples (clip, track, index, pos_off)
    resync_data = []
    parent_track = current_sequence().first_video_track()
    for child_clip, track in sync_children.iteritems():
        child_index = track.clips.index(child_clip)
        child_clip_start = track.clip_start(child_index) - child_clip.clip_in

        parent_clip = child_clip.sync_data.master_clip
        try:
            parent_index = parent_track.clips.index(parent_clip)
        except:
            # Parent clip no longer awailable
            continue
        parent_clip_start = parent_track.clip_start(parent_index) - parent_clip.clip_in

        pos_offset = child_clip_start - parent_clip_start

        resync_data.append((child_clip, track, child_index, pos_offset))
    
    return resync_data

def get_resync_data_list_for_clip_list(clips_list):
    # Input is list of (clip, track) tuples
    # Returns list of tuples with data needed to do resync
    # Return tuples (clip, track, index, pos_off)
    resync_data = []
    parent_track = current_sequence().first_video_track()
    for clip_track_tuple in clips_list:
        child_clip, track = clip_track_tuple
        child_index = track.clips.index(child_clip)
        child_clip_start = track.clip_start(child_index) - child_clip.clip_in

        parent_clip = child_clip.sync_data.master_clip
        try:
            parent_index = parent_track.clips.index(parent_clip)
        except:
            # Parent clip no longer awailable
            continue
        parent_clip_start = parent_track.clip_start(parent_index) - parent_clip.clip_in

        pos_offset = child_clip_start - parent_clip_start

        resync_data.append((child_clip, track, child_index, pos_offset))
    
    return resync_data
    
def print_sync_children():
    for child_clip, track in sync_children.iteritems():
        print child_clip.id
        
        
        
        
