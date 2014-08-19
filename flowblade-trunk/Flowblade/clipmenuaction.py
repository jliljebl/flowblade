"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

"""
This module handles actions initiated from clip and compositor popup menus.
"""

import audiowaveform
import appconsts
import clipeffectseditor
import compositeeditor
import dialogs
import dialogutils
import gtk
import gui
import guicomponents
import edit
import editevent
from editorstate import current_sequence
from editorstate import get_track
from editorstate import PROJECT
import movemodes
import syncsplitevent
import tlinewidgets
import updater
import utils

# ---------------------------------- clip menu
def display_clip_menu(y, event, frame):
    # See if we actually hit a clip
    track = tlinewidgets.get_track(y)
    if track == None:
        return False
    clip_index = current_sequence().get_clip_index(track, frame)
    if clip_index == -1:
        return False
    # Can't do anything to clips in locked tracks
    if editevent.track_lock_check_and_user_info(track, display_clip_menu, "clip context menu"):
        return False
    
    # Display popup
    pressed_clip = track.clips[clip_index]
    if pressed_clip.is_blanck_clip == False:
        movemodes.select_clip(track.id, clip_index)
    else:
        movemodes.select_blank_range(track, pressed_clip)

    if track.type == appconsts.VIDEO:
        guicomponents.display_clip_popup_menu(event, pressed_clip, \
                                              track, _clip_menu_item_activated)
    elif track.type == appconsts.AUDIO:
        guicomponents.display_audio_clip_popup_menu(event, pressed_clip, \
                                                    track, _clip_menu_item_activated)

    return True

def _clip_menu_item_activated(widget, data):
    # Callback from selected clipmenu item
    clip, track, item_id, item_data = data
    handler = POPUP_HANDLERS[item_id]
    handler(data)

def _compositor_menu_item_activated(widget, data):
    action_id, compositor = data
    if action_id == "open in editor":
        compositeeditor.set_compositor(compositor)
    elif action_id == "delete":
        compositor.selected = False
        data = {"compositor":compositor}
        action = edit.delete_compositor_action(data)
        action.do_edit()
    elif action_id == "sync with origin":
        track = current_sequence().tracks[compositor.transition.b_track] # b_track is source track where origin clip is
        origin_clip = None
        for clip in track.clips:
            if clip.id == compositor.origin_clip_id:
                origin_clip = clip
        if origin_clip == None:
            dialogutils.info_message(_("Origin clip not found!"), 
                                 _("Clip used to create this Compositor has been removed\nor moved to different track."), 
                                 gui.editor_window.window)
            return
        clip_index = track.clips.index(origin_clip)
        clip_start = track.clip_start(clip_index)
        clip_end = clip_start + origin_clip.clip_out - origin_clip.clip_in
        data = {"compositor":compositor,"clip_in":clip_start,"clip_out":clip_end}
        action = edit.move_compositor_action(data)
        action.do_edit()

def _open_clip_in_effects_editor(data):
    updater.open_clip_in_effects_editor(data)
    
def _open_clip_in_clip_monitor(data):
    clip, track, item_id, x = data
    
    media_file = PROJECT().get_media_file_for_path(clip.path)
    media_file.mark_in = clip.clip_in
    media_file.mark_out = clip.clip_out
    updater.set_and_display_monitor_media_file(media_file)
    gui.pos_bar.widget.grab_focus()

def _show_clip_info(data):
    clip, track, item_id, x = data
    
    width = clip.get("width")
    height = clip.get("height")
    size = str(width) + " x " + str(height)
    l_frames = clip.clip_out - clip.clip_in + 1 # +1 out inclusive
    length = utils.get_tc_string(l_frames)

    video_index = clip.get_int("video_index")
    audio_index = clip.get_int("audio_index")
    long_video_property = "meta.media." + str(video_index) + ".codec.long_name"
    long_audio_property = "meta.media." + str(audio_index) + ".codec.long_name"
    vcodec = clip.get(str(long_video_property))
    acodec = clip.get(str(long_audio_property))

    dialogs.clip_properties_dialog((length, size, clip.path, vcodec, acodec))

def _rename_clip(data):
    clip, track, item_id, x = data
    dialogs.new_clip_name_dialog(_rename_clip_edited, clip)

def _rename_clip_edited(dialog, response_id, data):
    """
    Sets edited value to liststore and project data.
    """
    name_entry, clip = data
    new_text = name_entry.get_text()
    dialog.destroy()

    if response_id != gtk.RESPONSE_ACCEPT:
        return      
    if len(new_text) == 0:
        return

    clip.name = new_text
    updater.repaint_tline()

def _clip_color(data):
    clip, track, item_id, clip_color = data
    if clip_color == "default":
        clip.color = None
    elif clip_color == "red":
         clip.color = (1, 0, 0)
    elif clip_color == "green":
         clip.color = (0, 1, 0)
    elif clip_color == "blue":
         clip.color = (0.2, 0.2, 0.9)
    elif clip_color == "orange":
        clip.color =(0.929, 0.545, 0.376)
    elif clip_color == "brown":
        clip.color = (0.521, 0.352, 0.317)
    elif clip_color == "olive":
        clip.color = (0.5, 0.55, 0.5)

    updater.repaint_tline()

def open_selection_in_effects():
    if movemodes.selected_range_in == -1:
        return
    
    track = get_track(movemodes.selected_track)
    clip = track.clips[movemodes.selected_range_in]    
    clipeffectseditor.set_clip(clip, track, movemodes.selected_range_in)
    
def _add_filter(data):
    clip, track, item_id, item_data = data
    x, filter_info = item_data
    action = clipeffectseditor.get_filter_add_action(filter_info, clip)
    action.do_edit()
    
    # (re)open clip in editor
    frame = tlinewidgets.get_frame(x)
    index = track.get_clip_index_at(frame)
    clipeffectseditor.set_clip(clip, track, index)

def _add_compositor(data):
    clip, track, item_id, item_data = data
    x, compositor_type = item_data

    frame = tlinewidgets.get_frame(x)
    clip_index = track.get_clip_index_at(frame)

    target_track_index = track.id - 1

    compositor_in = current_sequence().tracks[track.id].clip_start(clip_index)
    clip_length = clip.clip_out - clip.clip_in
    compositor_out = compositor_in + clip_length

    edit_data = {"origin_clip_id":clip.id,
                "in_frame":compositor_in,
                "out_frame":compositor_out,
                "a_track":target_track_index,
                "b_track":track.id,
                "compositor_type":compositor_type}
    action = edit.add_compositor_action(edit_data)
    action.do_edit()
    
    updater.repaint_tline()

def _mute_clip(data):
    clip, track, item_id, item_data = data
    set_clip_muted = item_data

    if set_clip_muted == True:
        data = {"clip":clip}
        action = edit.mute_clip(data)
        action.do_edit()
    else:# then we're stting clip unmuted
        data = {"clip":clip}
        action = edit.unmute_clip(data)
        action.do_edit()

def _delete_blank(data):
    clip, track, item_id, x = data
    movemodes.select_blank_range(track, clip)
    from_index = movemodes.selected_range_in
    to_index = movemodes.selected_range_out  
    movemodes.clear_selected_clips()
    data = {"track":track,"from_index":from_index,"to_index":to_index}
    action = edit.remove_multiple_action(data)
    action.do_edit()

def _cover_blank_from_prev(data):
    clip, track, item_id, item_data = data
    clip_index = movemodes.selected_range_in - 1
    if clip_index < 0: # we're not getting legal clip index
        return 
    cover_clip = track.clips[clip_index]

    # Check that clip covers blank area
    total_length = 0
    for i in range(movemodes.selected_range_in,  movemodes.selected_range_out + 1):
        total_length += track.clips[i].clip_length()
    clip_handle = cover_clip.get_length() - cover_clip.clip_out - 1
    if total_length > clip_handle: # handle not long enough to cover blanks
        primary_txt = _("Previous clip does not have enough material to cover blank area")
        secondary_txt = _("Requested edit can't be done.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return
    
    # Do edit
    movemodes.clear_selected_clips()
    data = {"track":track, "clip":cover_clip, "clip_index":clip_index}
    action = edit.trim_end_over_blanks(data)
    action.do_edit()

def _cover_blank_from_next(data):
    clip, track, item_id, item_data = data
    clip_index = movemodes.selected_range_out + 1
    blank_index = movemodes.selected_range_in
    if clip_index < 0: # we're not getting legal clip index
        return
    cover_clip = track.clips[clip_index]
    
    # Check that clip covers blank area
    total_length = 0
    for i in range(movemodes.selected_range_in,  movemodes.selected_range_out + 1):
        total_length += track.clips[i].clip_length()
    if total_length > cover_clip.clip_in: # handle not long enough to cover blanks
        primary_txt = _("Next clip does not have enough material to cover blank area")
        secondary_txt = _("Requested edit can't be done.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return 

    # Do edit
    movemodes.clear_selected_clips()
    data = {"track":track, "clip":cover_clip, "blank_index":blank_index}
    action = edit.trim_start_over_blanks(data)
    action.do_edit()

def clear_filters():
    if movemodes.selected_track == -1:
        return

    track = get_track(movemodes.selected_track)
    clips = []
    for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        clips.append(track.clips[i])

    data = {"clips":clips}
    action = edit.remove_multiple_filters_action(data)
    action.do_edit()
    
    movemodes.clear_selected_clips()
    updater.repaint_tline()

def _display_wavefrom(data):
    audiowaveform.set_waveform_displayer_clip_from_popup(data)

def _clear_waveform(data):
    audiowaveform.clear_waveform(data)

def  _clone_filters_from_next(data):
    clip, track, item_id, item_data = data
    index = track.clips.index(clip)
    if index == len(track.clips) - 1:
        return # clip is last clip
    clone_clip = track.clips[index + 1]
    _do_filter_clone(clip, clone_clip)

def _clone_filters_from_prev(data):
    clip, track, item_id, item_data = data
    index = track.clips.index(clip)
    if index == 0:
        return # clip is first clip
    clone_clip = track.clips[index - 1]
    _do_filter_clone(clip, clone_clip)

def _do_filter_clone(clip, clone_clip):
    if clone_clip.is_blanck_clip:
        return
    data = {"clip":clip,"clone_source_clip":clone_clip}
    action = edit.clone_filters_action(data)
    action.do_edit()




# Functions to handle popup menu selections for strings 
# set as activation messages in guicomponents.py
# activation_message -> _handler_func
POPUP_HANDLERS = {"set_master":syncsplitevent.init_select_master_clip,
                  "open_in_editor":_open_clip_in_effects_editor,
                  "clip_info":_show_clip_info,
                  "open_in_clip_monitor":_open_clip_in_clip_monitor,
                  "rename_clip":_rename_clip,
                  "clip_color":_clip_color,
                  "split_audio":syncsplitevent.split_audio,
                  "split_audio_synched":syncsplitevent.split_audio_synched,
                  "resync":syncsplitevent.resync_clip,
                  "add_filter":_add_filter,
                  "add_compositor":_add_compositor,
                  "clear_sync_rel":syncsplitevent.clear_sync_relation,
                  "mute_clip":_mute_clip,
                  "display_waveform":_display_wavefrom,
                  "clear_waveform":_clear_waveform,
                  "delete_blank":_delete_blank,
                  "cover_with_prev": _cover_blank_from_prev,
                  "cover_with_next": _cover_blank_from_next,
                  "clone_filters_from_next": _clone_filters_from_next,
                  "clone_filters_from_prev": _clone_filters_from_prev}
