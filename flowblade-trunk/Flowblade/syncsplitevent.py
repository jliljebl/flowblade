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
Module handles events related to audiosplits and setting clip sync relationships.
"""
import pygtk
pygtk.require('2.0');
import gtk


import appconsts
import dialogutils
import edit
import editorstate
from editorstate import current_sequence
from editorstate import get_track
import gui
import movemodes
import tlinewidgets
import updater
import utils

# NOTE: THIS AND resync.py SHOULD PROBABLY BE THE SAME MODULE

parent_selection_data = None

# ----------------------------------- split audio
def split_audio_synched(popup_data):
    """
    We do two separate edits to do this, so if user undoes this he'll need
    to two undos, which may not be to user expectation as doing this is only one edit 
    """
    (parent_clip, child_clip, child_clip_track) = _do_split_audio_edit(popup_data)

    # This is quarenteed because GUI option to do this is only available on this track
    parent_track = current_sequence().tracks[current_sequence().first_video_index]
    child_index = child_clip_track.clips.index(child_clip)
    parent_clip_index = parent_track.clips.index(parent_clip)
    
    data = {"child_index":child_index,
            "child_track":child_clip_track,
            "parent_index":parent_clip_index,
            "parent_track":parent_track}
    action = edit.set_sync_action(data)
    action.do_edit()

def split_audio(popup_data):
    _do_split_audio_edit(popup_data)

def _do_split_audio_edit(popup_data):
    # NOTE: THIS HARD CODES ALL SPLITS TO HAPPEN ON TRACK A1, THIS MAY CHANGE
    to_track = current_sequence().tracks[current_sequence().first_video_index - 1]

    clip, track, item_id, x = popup_data
    press_frame = tlinewidgets.get_frame(x)
    index = current_sequence().get_clip_index(track, press_frame)
    frame = track.clip_start(index)

    audio_clip = current_sequence().create_file_producer_clip(clip.path)
    audio_clip.media_type = appconsts.AUDIO
    split_length = clip.clip_out - clip.clip_in + 1 # +1 out is inclusive and we're looking for length
    data = { "parent_clip":clip,
             "audio_clip":audio_clip,
             "over_in":frame,
             "over_out":frame + split_length,
             "to_track":to_track}

    action = edit.audio_splice_action(data)
    action.do_edit()
    
    return (clip, audio_clip, to_track)

# ---------------------------------------------- sync parent clips
def init_select_master_clip(popup_data):
    clip, track, item_id, x = popup_data
    frame = tlinewidgets.get_frame(x)
    child_index = current_sequence().get_clip_index(track, frame)

    if not (track.clips[child_index] == clip):
        # This should never happen 
        print "big fu at _init_select_master_clip(...)"
        return

    gdk_window = gui.tline_display.get_parent_window();
    gdk_window.set_cursor(gtk.gdk.Cursor(gtk.gdk.TCROSS))
    editorstate.edit_mode = editorstate.SELECT_PARENT_CLIP
    global parent_selection_data
    parent_selection_data = (clip, child_index, track)

def select_sync_parent_mouse_pressed(event, frame):
    _set_sync_parent_clip(event, frame)
    
    gdk_window = gui.tline_display.get_parent_window();
    gdk_window.set_cursor(gtk.gdk.Cursor(gtk.gdk.LEFT_PTR))
   
    global parent_selection_data
    parent_selection_data = None

    # Edit consumes selection
    movemodes.clear_selected_clips()

    updater.repaint_tline()

def _set_sync_parent_clip(event, frame):
    child_clip, child_index, child_clip_track = parent_selection_data
    parent_track = tlinewidgets.get_track(event.y)
    
    if parent_track != current_sequence().tracks[current_sequence().first_video_index]:
        dialogutils.warning_message(_("Sync parent clips must be on track V1"), 
                                _("Selected sync parent clip is on track ")+ utils.get_track_name(parent_track, current_sequence()) + _(".\nYou can only sync to clips that are on track V1."),
                                gui.editor_window.window,
                                True)
        return
    
    # this can't have parent clip already
    if child_clip.sync_data != None:
        return

    if parent_track == None:
        return 
    parent_clip_index = current_sequence().get_clip_index(parent_track, frame)
    if parent_clip_index == -1:
        return

    # Parent and child can't be on the same track.
    # Now that all parent clips must be on track V1 this is no longer shoild be possible.
    if parent_track == child_clip_track:
        print "parent_track == child_clip_track"
        return
        
    parent_clip = parent_track.clips[parent_clip_index]
    
    # These cannot be chained.
    # Now that all parent clips must be on track V1 this is no longer shoild be possible.
    if parent_clip.sync_data != None:
        print "parent_clip.sync_data != None"
        return

    data = {"child_index":child_index,
            "child_track":child_clip_track,
            "parent_index":parent_clip_index,
            "parent_track":parent_track}
    action = edit.set_sync_action(data)
    action.do_edit()

def resync_clip(popup_data):
    clip, track, item_id, x = popup_data
    clip_list=[(clip, track)]
    
    data = {"clips":clip_list}
    action = edit.resync_some_clips_action(data)
    action.do_edit()
    
    updater.repaint_tline()

def resync_everything():
    # Selection not valid after resync action
    if movemodes.selected_track == -1:
        movemodes.clear_selected_clips()
    
    action = edit.resync_all_action({})
    action.do_edit()
    
    updater.repaint_tline()

def resync_selected():
    if movemodes.selected_track == -1:
        return

    track = get_track(movemodes.selected_track)
    clip_list = []
    for index in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        clip_list.append((track.clips[index], track))

    # Selection not valid after resync action
    movemodes.clear_selected_clips()

    # Chack if synced clips have same or consecutive parent clips
    all_same_or_consecutive = True
    master_id = -1
    current_master_clip = -1
    current_master_index = -1
    master_track = current_sequence().first_video_track()
    for t in clip_list:
        clip, track = t
        try:
            if master_id == -1:
                master_id = clip.sync_data.master_clip.id
                current_master_clip = clip.sync_data.master_clip
                current_master_index = master_track.clips.index(current_master_clip)
            else:
                if clip.sync_data.master_clip.id != master_id:
                    next_master_index = master_track.clips.index(clip.sync_data.master_clip)
                    if current_master_index + 1 == next_master_index:
                        # Masters are consecutive, save data to test next
                        master_id = clip.sync_data.master_clip.id
                        current_master_index = master_track.clips.index(current_master_clip)
                    else:
                        all_same_or_consecutive = False
        except:
            all_same_or_consecutive = False

    # If clips are all for same or consecutive sync parent clips, sync them as a unit.
    if len(clip_list) > 1 and all_same_or_consecutive == True:
        data = {"clips":clip_list}
        action = edit.resync_clips_sequence_action(data)
        action.do_edit()
    else: # Single or non-consecutive clips are synched separately
        data = {"clips":clip_list}
        action = edit.resync_some_clips_action(data)
        action.do_edit()

    updater.repaint_tline()

def clear_sync_relation(popup_data):
    clip, track, item_id, x = popup_data

    data = {"child_clip":clip,
            "child_track":track}
    action = edit.clear_sync_action(data)
    action.do_edit()

    # Edit consumes selection
    movemodes.clear_selected_clips()
    
    updater.repaint_tline()

