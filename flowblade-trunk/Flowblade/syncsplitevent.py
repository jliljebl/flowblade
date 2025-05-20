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

"""
Module handles events related to audiosplits and setting clip sync relationships.
"""

from gi.repository import Gdk, GLib, Gtk

import appconsts
import dialogs
import dialogutils
import edit
import editorstate
from editorstate import current_sequence
from editorstate import get_track
import editorpersistance
import gui
import guipopover
import movemodes
import resync
import tlinewidgets
import updater
import utils


parent_selection_data = None

CHILD_SELECTION_SINGLE = 1
CHILD_SELECTION_MULTIPLE = 2


# ----------------------------------- split audio
def split_audio_synched(popup_data):
    """
    We have do two separate edits to do this, because we need to have a clip on timeline 
    to be able to sync it. So if user undoes this he'll need
    to two undos, which may not be to user expectation as doing this is only one edit. 
    """
    clip, track, item_id, x = popup_data
    
    # We can only split audio from unmuted clips because splitting mutes audio
    # and we want to avoid splitting audio twice.
    if clip.mute_filter != None:
        return
        
    split_action, parent_clip, child_clip, child_clip_track = _get_split_audio_edit_action(popup_data)
    split_action.do_edit()
    sync_action = _get_set_sync_action(child_clip_track, child_clip, parent_clip, track)
    sync_action.do_edit()

def split_audio_synched_from_clips_list(clips, track):
    item_id = "not actually used"
    split_actions_data = []
    split_actions = []
    for clip in clips:
        # We're using the existing function to do this need x for clip frame to use it
        index = track.clips.index(clip)
        frame = track.clip_start(index)
        x = tlinewidgets._get_frame_x(frame)

        popup_data = (clip, track, item_id, x)

        # We can only split audio from unmuted clips because splitting mutes audio
        # and we want to avoid splitting audio twice.
        if clip.mute_filter == None:
            split_action, parent_clip, child_clip, child_clip_track = _get_split_audio_edit_action(popup_data)
            split_actions.append(split_action)
            split_actions_data.append((parent_clip, child_clip, child_clip_track))
    
    # We need to do split action before creating set sync actio0ns because we need a clip on timeline 
    # to actually sync with.
    split_consolidated_action = edit.ConsolidatedEditAction(split_actions)
    split_consolidated_action.do_consolidated_edit()

    set_sync_actions = []
    for split_data in split_actions_data:
        parent_clip, child_clip, child_clip_track = split_data
        
        sync_action = _get_set_sync_action(child_clip_track, child_clip, parent_clip, track)
        set_sync_actions.append(sync_action)

    sync_consolidated_action = edit.ConsolidatedEditAction(set_sync_actions)
    sync_consolidated_action.do_consolidated_edit()

def sync_menu_launch_pressed(launcher, widget, event):
    guipopover.sync_menu_show(launcher, widget, _sync_property_item_activated, _sync_split_property_activated, _auto_sync_split_menu_item_item_activated)

def _sync_property_item_activated(action, event, msg):
    new_state = not(action.get_state().get_boolean())

    if msg == "autosplit":
        editorpersistance.prefs.sync_autosplit = new_state
    elif msg == "dualtrim":
        editorpersistance.prefs.sync_dualtrim = new_state
    elif msg == "showsync":
        editorpersistance.prefs.show_sync = new_state
        
    action.set_state(GLib.Variant.new_boolean(new_state))

def _sync_split_property_activated(action, variant):
    if variant.get_string() == "splitmirror":
        editorpersistance.prefs.sync_mirror = True
    else:
        editorpersistance.prefs.sync_mirror = False

    action.set_state(variant)
    editorpersistance.save()
    #guipopover._tline_properties_popover.hide()

def _auto_sync_split_menu_item_item_activated(action, new_value_variant):
    msg = int(new_value_variant.get_string())
    editorpersistance.prefs.sync_autosplit = msg
    editorpersistance.save()
    action.set_state(new_value_variant)

def _get_set_sync_action(child_clip_track, child_clip, parent_clip, parent_track):
    child_index = child_clip_track.clips.index(child_clip)
    parent_clip_index = parent_track.clips.index(parent_clip)
    
    data = {"child_index":child_index,
            "child_track":child_clip_track,
            "parent_index":parent_clip_index,
            "parent_track":parent_track}
    action = edit.set_sync_action(data)
    return action
    #action.do_edit()
    
def split_audio(popup_data):
    clip, track, item_id, x = popup_data
    
    # We can only split audio from unmuted clips because splitting mutes audio
    # and we want to avoid splitting audio twice.
    if clip.mute_filter != None:
        return
        
    action, clip, audio_clip, to_track = _get_split_audio_edit_action(popup_data)

    action.do_edit()

def split_audio_from_clips_list(clips, track):
    item_id = "not actually used"
    actions_list = []
    for clip in clips:
        # We're using the existing function to do this need x for clip frame to use it
        index = track.clips.index(clip)
        frame = track.clip_start(index)
        x = tlinewidgets._get_frame_x(frame)

        popup_data = (clip, track, item_id, x)

        # We can only split audio from unmuted clips because splitting mutes audio
        # and we want to avoid splitting audio twice.
        if clip.mute_filter == None:
            action, clip, audio_clip, to_track = _get_split_audio_edit_action(popup_data)
            actions_list.append(action)
    
    consolidated_action = edit.ConsolidatedEditAction(actions_list)
    consolidated_action.do_consolidated_edit()

def _do_split_audio_edit(popup_data):
    return _get_split_audio_edit_action(popup_data)

def _get_split_audio_edit_action(popup_data):
    clip, track, item_id, x = popup_data

    if editorpersistance.prefs.sync_mirror == False:
        to_track = current_sequence().tracks[current_sequence().first_video_index - 1]
    else:
        to_track_id = (current_sequence().first_video_index - 1) - (track.id - current_sequence().first_video_index)
        if to_track_id < 1:
            to_track_id = 1
        to_track = current_sequence().tracks[to_track_id]
        
    press_frame = tlinewidgets.get_frame(x)
    index = current_sequence().get_clip_index(track, press_frame)
    frame = track.clip_start(index)

    audio_clip = current_sequence().create_file_producer_clip(clip.path, None, False, clip.ttl)
    audio_clip.media_type = appconsts.AUDIO
    split_length = clip.clip_out - clip.clip_in + 1 # +1 out is inclusive and we're looking for length
    data = { "parent_clip":clip,
             "audio_clip":audio_clip,
             "over_in":frame,
             "over_out":frame + split_length,
             "to_track":to_track}

    action = edit.audio_splice_action(data)
    
    return (action, clip, audio_clip, to_track)

def get_synched_split_action_for_clip_and_track(clip, track):
    if editorpersistance.prefs.sync_mirror == False:
        to_track = current_sequence().tracks[current_sequence().first_video_index - 1]
    else:
        to_track_id = (current_sequence().first_video_index - 1) - (track.id - current_sequence().first_video_index)
        if to_track_id < 1:
            to_track_id = 1
        to_track = current_sequence().tracks[to_track_id]
        
    index = track.clips.index(clip)
    frame = track.clip_start(index)

    audio_clip = current_sequence().create_file_producer_clip(clip.path, None, False, clip.ttl)
    audio_clip.media_type = appconsts.AUDIO
    split_length = clip.clip_out - clip.clip_in + 1 # +1 out is inclusive and we're looking for length
    data = { "parent_clip":clip,
             "audio_clip":audio_clip,
             "over_in":frame,
             "over_out":frame + split_length,
             "to_track":to_track,
             "track":track}

    action = edit.audio_synched_splice_action(data)
    return action

def set_track_clips_sync(child_track):
    dialogs.set_parent_track_dialog(child_track, _parent_track_selected)
 
def _parent_track_selected(dialog, response_id, data):
    if response_id == Gtk.ResponseType.ACCEPT:
        child_track, selection_data, tracks_combo = data
        parent_track = selection_data[tracks_combo.get_active()]
        
        dialog.destroy()
        
        do_set_track_clips_sync(child_track, parent_track)
        child_track.parent_track = parent_track
    else:
        dialog.destroy()

def do_set_track_clips_sync(child_track, parent_track):
    if len(parent_track.clips) == 0:
        return
    if len(child_track.clips) == 0:
        return
        
    orig_sync_data, new_sync_data = resync.get_track_all_resync_action_data(child_track, parent_track)
    
    data = {"child_track":child_track,
            "orig_sync_data":orig_sync_data,
            "new_sync_data":new_sync_data}
    
    action = edit.set_track_sync_action(data)
    action.do_edit()

def clear_track_clips_sync(child_track):
    orig_sync_data = {}
    sync_data_exists = False
    for clip in child_track.clips:
        if clip.is_blanck_clip == True:
            continue
        if  clip.sync_data != None:
            sync_data_exists = True
        
        orig_sync_data[clip] = clip.sync_data
    
    # Let's not put noop edits in undo stack.
    if sync_data_exists == False:
        return

    data = {"child_track":child_track,
            "orig_sync_data":orig_sync_data}

    action = edit.clear_track_sync_action(data)
    action.do_edit()

def set_box_clips_sync(box_selection):
    parent_track, parent_track_selection = box_selection.get_center_most_sync_track()
    
    # Get parent clip. No edit actions for missing parent clip on parent track on blank clips.
    # TODO: Add info window.
    try:
        parent_clip = parent_track.clips[parent_track_selection.selected_range_in]
    except:
        return
    if parent_clip.is_blanck_clip == True:
        return

    parent_clip = parent_track.clips[parent_track_selection.selected_range_in]
    tracks_orig_sync_data, tracks_new_sync_data = resync.get_box_selection_resync_action_data(box_selection, parent_track, parent_clip)
    
    data = {"orig_sync_data":tracks_orig_sync_data,
            "new_sync_data":tracks_new_sync_data}
    
    action = edit.set_box_selection_sync_action(data)
    action.do_edit()

# ---------------------------------------------- sync parent clips
def init_select_master_clip(popup_data):

    global parent_selection_data
    try:
        clip, track, item_id, x = popup_data
        frame = tlinewidgets.get_frame(x)
        child_index = current_sequence().get_clip_index(track, frame)

        if not (track.clips[child_index] == clip):
            # This should never happen, but I think we've seen this print sometimes. 
            print("problem at _init_select_master_clip(...)")
            return

        parent_selection_data = (CHILD_SELECTION_SINGLE, clip, child_index, track)
    except TypeError:
        # This is from multi selection that does not provide same data as single selection.
        parent_selection_data = (CHILD_SELECTION_MULTIPLE, movemodes.selected_range_in, movemodes.selected_range_out, track)
        
    gdk_window = gui.tline_display.get_parent_window()
    gdk_window.set_cursor(Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.TCROSS))
    editorstate.edit_mode = editorstate.SELECT_PARENT_CLIP

def init_select_master_clip_from_keyevent():
    global parent_selection_data
    if movemodes.selected_track != -1:
        child_index = movemodes.selected_range_in
        track = current_sequence().tracks[movemodes.selected_track]
        clip = track.clips[child_index]

        parent_selection_data = (CHILD_SELECTION_MULTIPLE, movemodes.selected_range_in, movemodes.selected_range_out, track)
        gdk_window = gui.tline_display.get_parent_window()
        gdk_window.set_cursor(Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.TCROSS))
        editorstate.edit_mode = editorstate.SELECT_PARENT_CLIP
        gui.editor_window.tline_cursor_manager.tline_cursor_enter(None)

def select_sync_parent_mouse_pressed(event, frame):
   
    global parent_selection_data
    selection_type, data1, data2, data3 = parent_selection_data

    if selection_type == CHILD_SELECTION_SINGLE:
        _set_sync_parent_clip(event, frame)
    else:
        _set_sync_parent_clip_multi(event, frame)

    gdk_window = gui.tline_display.get_parent_window()
    gdk_window.set_cursor(Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.LEFT_PTR))

    parent_selection_data = None

    # Edit consumes selection
    movemodes.clear_selected_clips()

    updater.repaint_tline()

def _set_sync_parent_clip(event, frame):
    sel_type, child_clip, child_index, child_clip_track = parent_selection_data
    parent_track = tlinewidgets.get_track(event.y)
    
    # this can't have parent clip already
    if child_clip.sync_data != None:
        return

    if parent_track == None:
        return 
    parent_clip_index = current_sequence().get_clip_index(parent_track, frame)
    if parent_clip_index == -1:
        return

    # Parent and child can't be on the same track.
    if parent_track == child_clip_track:
        return
        
    parent_clip = parent_track.clips[parent_clip_index]
    
    # These cannot be chained.
    # Now that all parent clips must be on track V1 this is no longer should be possible.
    if parent_clip.sync_data != None:
        print("parent_clip.sync_data != None")
        return

    data = {"child_index":child_index,
            "child_track":child_clip_track,
            "parent_index":parent_clip_index,
            "parent_track":parent_track}
    action = edit.set_sync_action(data)
    action.do_edit()

def _set_sync_parent_clip_multi(event, frame):
    sel_type,  selected_range_in, selected_range_out, child_clip_track = parent_selection_data
    parent_track = tlinewidgets.get_track(event.y)
    if parent_track == None:
        return 
    
    child_clips = []
    for i in range(selected_range_in, selected_range_out + 1):
        child_clips.append(child_clip_track.clips[i])
    
    # these can't have parent clip already
    for clip in child_clips:
        if clip.sync_data != None:
            return

    parent_clip_index = current_sequence().get_clip_index(parent_track, frame)
    if parent_clip_index == -1:
        return

    # Parent and child can't be on the same track.
    if parent_track == child_clip_track:
        return
        
    parent_clip = parent_track.clips[parent_clip_index]
    
    # These cannot be chained.
    # Now that all parent clips must be on track V1 this is no longer should be possible.
    if parent_clip.sync_data != None:
        print("parent_clip.sync_data != None")
        return

    # Create edit actions.
    edit_actions = []
    for child_index in range(selected_range_in, selected_range_out + 1):
        if child_clip_track.clips[child_index].is_blank == True:
            continue
        data = {"child_index":child_index,
                "child_track":child_clip_track,
                "parent_index":parent_clip_index,
                "parent_track":parent_track}
        action = edit.set_sync_action(data)
        edit_actions.append(action)
        
    consolidated_action = edit.ConsolidatedEditAction(edit_actions)
    consolidated_action.do_consolidated_edit()


def resync_multi(popup_data):
    resync_clip_from_button()

def resync_clip_from_button():
    track = get_track(movemodes.selected_track)
    clip_list = [] 
    for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        clip_list.append(track.clips[i])

    resync_clips_data_list = []
    for clip in clip_list:
        if clip.sync_data != None:
            resync_clips_data_list.append((clip, track))

    if len(resync_clips_data_list) == 0:
        return # All in sync

    data = {"resync_clips_data_list":resync_clips_data_list}
    action = edit.resync_track_action(data)
    action.do_edit()

def resync_clip(popup_data):
    
    clip, track, item_id, x = popup_data
    _do_single_clip_resync(clip, track)

def _do_single_clip_resync(clip, track):
    clip_list = [(clip, track)]
    
    resync_data_list = resync.get_resync_data_list_for_clip_list(clip_list)

    if len(resync_data_list) == 0:
        return # Parent clip is gone.

    # Get sync data. If we're in sync, do nothing.
    clip, track, index, child_clip_start, pos_offset = resync_data_list[0]
    if pos_offset == clip.sync_data.pos_offset:
        return None
    
    # Do resync.
    data = {"clips":clip_list}
    action = edit.resync_clip_action(data)
    action.do_edit()
    
    updater.repaint_tline()

def resync_track():
    if movemodes.selected_track == -1:
        return

    selected_track = get_track(movemodes.selected_track)
    resync_selected_track(selected_track)

def resync_selected_track(selected_track):
    
    resync_clips_data_list = resync.get_track_resync_clips_data_list(selected_track)
    
    if len(resync_clips_data_list) == 0:
        return

    data = {"resync_clips_data_list":resync_clips_data_list}
    action = edit.resync_track_action(data)
    action.do_edit()

def clear_sync_relation(popup_data):
    clip, track, item_id, x = popup_data
    do_clear_sync_relation(clip, track)

def clear_sync_relation_from_keyevent():
    if movemodes.selected_track != -1:
        track = current_sequence().tracks[movemodes.selected_track]
        clip = track.clips[movemodes.selected_range_in]
        do_clear_sync_relation(clip, track)

def do_clear_sync_relation(clip, track):
    data = {"child_clip":clip,
            "child_track":track}
    action = edit.clear_sync_action(data)
    action.do_edit()

    # Edit consumes selection
    movemodes.clear_selected_clips()
    updater.repaint_tline()

def clear_sync_relation_multi(popup_data):
    child_clip_track = current_sequence().tracks[movemodes.selected_track]

    # Create edit actions.
    edit_actions = []
    for child_index in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        if child_clip_track.clips[child_index].is_blank == True:
            continue
        data = {"child_clip":child_clip_track.clips[child_index],
                "child_track":child_clip_track}
        action = edit.clear_sync_action(data)
        edit_actions.append(action)

    consolidated_action = edit.ConsolidatedEditAction(edit_actions)
    consolidated_action.do_consolidated_edit()

    # Edit consumes selection
    movemodes.clear_selected_clips()
    updater.repaint_tline()

