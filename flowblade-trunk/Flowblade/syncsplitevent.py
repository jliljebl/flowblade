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
    sync_action = _get_set_sync_action(child_clip_track, child_clip, parent_clip)
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
        
        sync_action = _get_set_sync_action(child_clip_track, child_clip, parent_clip)
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

def _get_set_sync_action(child_clip_track, child_clip, parent_clip):
    # This is quarenteed because GUI option to do this is only available on this track
    parent_track = current_sequence().tracks[current_sequence().first_video_index]
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
    # NOTE: THIS HARD CODES ALL SPLITS TO HAPPEN TO TRACK A1, THIS MAY CHANGE
    to_track = current_sequence().tracks[current_sequence().first_video_index - 1]

    clip, track, item_id, x = popup_data
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


# ---------------------------------------------- sync parent clips
def init_select_master_clip(popup_data):
    clip, track, item_id, x = popup_data
    frame = tlinewidgets.get_frame(x)
    child_index = current_sequence().get_clip_index(track, frame)

    if not (track.clips[child_index] == clip):
        # This should never happen 
        print("big fu at _init_select_master_clip(...)")
        return

    gdk_window = gui.tline_display.get_parent_window()
    gdk_window.set_cursor(Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.TCROSS))
    editorstate.edit_mode = editorstate.SELECT_PARENT_CLIP
    global parent_selection_data
    parent_selection_data = (clip, child_index, track)

def select_sync_parent_mouse_pressed(event, frame):
    _set_sync_parent_clip(event, frame)
    
    gdk_window = gui.tline_display.get_parent_window()
    gdk_window.set_cursor(Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.LEFT_PTR))
   
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
    # Now that all parent clips must be on track V1 this is no longer should be possible.
    if parent_track == child_clip_track:
        print("parent_track == child_clip_track")
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

def resync_clip_from_button():
    track = get_track(movemodes.selected_track)
    clip = track.clips[movemodes.selected_range_in]
    _do_single_clip_resync(clip, track)

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

    data = {"child_clip":clip,
            "child_track":track}
    action = edit.clear_sync_action(data)
    action.do_edit()

    # Edit consumes selection
    movemodes.clear_selected_clips()

    updater.repaint_tline()

