"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

"""
This module handles actions initiated from clip and compositor popup menus.
"""

from PIL import Image

from gi.repository import GLib
from gi.repository import Gtk

try:
    import mlt7 as mlt
except:
    import mlt
from operator import itemgetter
import os
import shutil
import time

import audiosync
import appconsts
import clipeffectseditor
import compositeeditor
import containerclip
import dialogs
import dialogutils
import gui
import guipopoverclip
import edit
from editorstate import current_sequence
from editorstate import get_track
from editorstate import PROJECT
from editorstate import PLAYER
import kftoolmode
import mediaplugin
import mlttransitions
import modesetting
import movemodes
import projectaction
import singletracktransition
import syncsplitevent
import titler
import tlinewidgets
import tlineaction
import updater
import userfolders
import utils

# --------------------------------------------- menu data for each invocation.
_popover_clip_data = None # clip, track and press x cannot passed through using Gio.MenuItems and Gio.SimpleAction objects
                          # so they saved here before each menu invocation.
_compositor_data = None # clip, track and press x cannot passed through using Gio.MenuItems and Gio.SimpleAction objects
                          # so they saved here before each menu invocation.

# toolsintegrator.py needs this to launch tools
def get_popover_clip_data():
    return _popover_clip_data

# Edit event sets this because we cannot pass data through menu with Gio.Menu anymore.
def set_compositor_data(compositor):
    global _compositor_data
    _compositor_data = compositor

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
    if dialogutils.track_lock_check_and_user_info(track):
        return False
    
    # Display popup
    not_multi_selection = (movemodes.selected_range_in == -1 or (movemodes.selected_range_out - movemodes.selected_range_in) == 0)
    gui.tline_canvas.drag_on = False
    pressed_clip = track.clips[clip_index]
    if pressed_clip.is_blanck_clip == False:
        if not_multi_selection == True:
            movemodes.select_clip(track.id, clip_index)
    else:
        movemodes.select_blank_range(track, pressed_clip)

    global _popover_clip_data
    _popover_clip_data = (pressed_clip, track,  event.x)
            
    if track.type == appconsts.VIDEO:
        if not_multi_selection == True:
            guipopoverclip.clip_popover_menu_show(gui.tline_canvas.widget, pressed_clip, track, event.x, event.y, _clip_popover_menu_item_activated)
        else:
            guipopoverclip.multi_clip_popover_menu_show(gui.tline_canvas.widget, pressed_clip, track, event.x, event.y, _clip_popover_menu_item_activated)

    elif track.type == appconsts.AUDIO:
        guipopoverclip.audio_clip_popover_menu_show(gui.tline_canvas.widget, pressed_clip, track, event.x, event.y, _clip_popover_menu_item_activated)

    return True

def _clip_menu_item_activated(widget, data):
    # Callback from selected clipmenu item
    clip, track, item_id, item_data = data
    handler = POPUP_HANDLERS[item_id]
    handler(data)

def _clip_popover_menu_item_activated(action, variant, data):
    # Callback from selected clipmenu item
    item_id, item_data = data
    global _popover_clip_data
    clip, track, x = _popover_clip_data
    handler = POPUP_HANDLERS[item_id]
    handler_data = (clip, track, item_id, item_data)
    handler(handler_data)

def compositor_menu_item_activated(action, variant, action_id):
    compositor = _compositor_data
    if action_id == "open in editor":
        compositeeditor.set_compositor(compositor)
    elif action_id == "delete":
        compositor.selected = False
        data = {"compositor":compositor}
        action = edit.delete_compositor_action(data)
        action.do_edit()
    elif action_id == "sync with origin":
        tlineaction.sync_compositor(compositor)
    elif action_id == "set auto follow":
        compositor.obey_autofollow = widget.get_active()
        updater.repaint_tline()

def _delete_compositors(data):
    clip, track, item_id, x = data
    compositors = current_sequence().get_clip_compositors(clip)
    for compositor in compositors:
        data = {"compositor":compositor}
        action = edit.delete_compositor_action(data)
        action.do_edit()
        
def _multi_delete_compositors(data):
    clip, track, item_id, x = data
    for clip_index in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        composited_clip = track.clips[clip_index]
        if composited_clip.is_blanck_clip == True:
            continue
        compositors = current_sequence().get_clip_compositors(composited_clip)
        for compositor in compositors:
            data = {"compositor":compositor}
            action = edit.delete_compositor_action(data)
            action.do_edit()

def _open_clip_in_effects_editor(data):
    updater.open_clip_in_effects_editor(_get_data_with_xpos(data))
    
def _open_clip_in_clip_monitor(data):
    clip, track, item_id, x = data

    media_file = PROJECT().get_media_file_for_path(clip.path)
    if media_file == None and clip.container_data != None:
        media_file = PROJECT().get_media_file_for_container_data(clip.container_data)

    media_file.mark_in = clip.clip_in
    media_file.mark_out = clip.clip_out
    updater.set_and_display_monitor_media_file(media_file)
    gui.pos_bar.widget.grab_focus()

def _show_clip_info(data):
    clip, track, item_id, x = data

    width = clip.get("width")
    height = clip.get("height")
    if clip.media_type == appconsts.IMAGE:
        graphic_img = Image.open(clip.path)
        width, height = graphic_img.size
    size = str(width) + " x " + str(height)
    l_frames = clip.clip_out - clip.clip_in + 1 # +1 out inclusive
    length = utils.get_tc_string(l_frames)
    mark_in = utils.get_tc_string(clip.clip_in)
    mark_out = utils.get_tc_string(clip.clip_out + 1) # +1 out inclusive

    video_index = clip.get_int("video_index")
    audio_index = clip.get_int("audio_index")
    long_video_property = "meta.media." + str(video_index) + ".codec.long_name"
    long_audio_property = "meta.media." + str(audio_index) + ".codec.long_name"
    vcodec = clip.get(str(long_video_property))
    acodec = clip.get(str(long_audio_property))    
    if vcodec == None:
        vcodec = _("N/A")
    if acodec == None:
        acodec = _("N/A")

    dialogs.clip_properties_dialog((mark_in, mark_out, length, size, clip.path, vcodec, acodec))

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

    if response_id != Gtk.ResponseType.ACCEPT:
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
         clip.color = (0.8, 0.2, 0.2)
    elif clip_color == "green":
         clip.color = (0.2 * 0.6, 0.8 * 0.6, 0.2 * 0.6)
    elif clip_color == "blue":
         clip.color = (0.2 * 0.6, 0.2 * 0.6, 0.9 * 0.6)
    elif clip_color == "orange":
        clip.color =(0.929 * 0.6, 0.545 * 0.6, 0.376 * 0.6)
    elif clip_color == "brown":
        clip.color = (0.521, 0.352, 0.317)
    elif clip_color == "olive":
        clip.color = (0.4 * 0.8, 0.45 * 0.8, 0.4 * 0.8)

    updater.repaint_tline()

def open_selection_in_effects():
    if movemodes.selected_range_in == -1:
        return
    
    track = get_track(movemodes.selected_track)
    clip = track.clips[movemodes.selected_range_in]    
    clipeffectseditor.set_clip(clip, track, movemodes.selected_range_in)
    
def _add_filter(data):
    clip, track, item_id, filter_info = data
    clip, track, x = _popover_clip_data 

    action = clipeffectseditor.get_filter_add_action(filter_info, clip)
    clipeffectseditor.set_stack_update_blocked() # We update stack on set_clip below
    action.do_edit()
    clipeffectseditor.set_stack_update_unblocked()

    # (re)open clip in editor
    frame = tlinewidgets.get_frame(x)
    index = track.get_clip_index_at(frame)
    clipeffectseditor.set_clip(clip, track, index)
    clipeffectseditor.set_filter_item_expanded(len(clip.filters) - 1)

def _add_filter_multi(data):
    clip, track, item_id, item_data = data
    x, filter_info = item_data
    
    clipeffectseditor.set_stack_update_blocked() # We update stack on set_clip below
    
    range_in = movemodes.selected_range_in
    range_out = movemodes.selected_range_out
    clips = track.clips[range_in:range_out +1]
    data = {"clips":clips, 
            "filter_info":filter_info,
            "filter_edit_done_func":clipeffectseditor.filter_edit_multi_done_stack_update}
    action = edit.add_filter_multi_action(data)
    action.do_edit()
    
    clipeffectseditor.set_stack_update_unblocked()

    # (re)open clip in editor
    frame = tlinewidgets.get_frame(x)
    index = track.get_clip_index_at(frame)
    clipeffectseditor.set_clip(clip, track, index)
    clipeffectseditor.set_filter_item_expanded(len(clip.filters) - 1)

def _add_compositor(data):
    # Get the currently available compositors. 
    compositors = []
    for i in range(0, len(mlttransitions.compositors)):
        compositor = mlttransitions.compositors[i]
        name, compositor_type = compositor
        if compositor_type in mlttransitions.dropped_compositors:
            continue
        compositors.append(compositor)
    
    for i in range(0, len(mlttransitions.wipe_compositors)):
        alpha_combiner = mlttransitions.wipe_compositors[i]
        name, compositor_type = alpha_combiner
        if compositor_type in mlttransitions.dropped_compositors:
            continue
        compositors.append(alpha_combiner)
    
    dialogs.add_compositor_dialog(compositors, _add_compositor_dialog_callback)

def _add_compositor_dialog_callback(dialog, response_id, compositors, combo):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return
    
    name, compositor_type = compositors[combo.get_active()]
    dialog.destroy()

    clip, track, x = _popover_clip_data
    add_compositors_is_multi_selection = False

    target_track_index = track.id - 1

    a_track = target_track_index
    b_track = track.id

    frame = tlinewidgets.get_frame(x)
    clip_index = track.get_clip_index_at(frame)
    
    compositor_in = current_sequence().tracks[track.id].clip_start(clip_index)
    clip_length = clip.clip_out - clip.clip_in
    compositor_out = compositor_in + clip_length
    
    edit_data = {"origin_clip_id":clip.id,
                "in_frame":compositor_in,
                "out_frame":compositor_out,
                "a_track":a_track,
                "b_track":b_track,
                "compositor_type":compositor_type,
                "clip":clip}
    action = edit.add_compositor_action(edit_data)
    action.do_edit()
        
    updater.repaint_tline()

def _add_autofade(data):
    # NOTE: These stay synhced only in "Top Down Auto Follow" mode, see: edit.get_full_compositor_sync_data()
    
    clip, track, item_id, item_data = data
    x, compositor_type, add_compositors_is_multi_selection = item_data

    frame = tlinewidgets.get_frame(x)
    clip_index = track.get_clip_index_at(frame)

    target_track_index = track.id - 1

    if add_compositors_is_multi_selection == True:
        for clip_index in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
            composited_clip = track.clips[clip_index]
            if composited_clip.is_blanck_clip == True:
                continue
                
            clip_length = composited_clip.clip_out - composited_clip.clip_in
            if compositor_type == "##auto_fade_in":
                compositor_in = current_sequence().tracks[track.id].clip_start(clip_index)
                compositor_out = compositor_in + int(utils.fps()) - 1
            else: # fade out
                clip_start = current_sequence().tracks[track.id].clip_start(clip_index)
                compositor_out = clip_start + clip_length
                compositor_in = compositor_out - int(utils.fps()) + 1

            edit_data = {"origin_clip_id":composited_clip.id,
                        "in_frame":compositor_in,
                        "out_frame":compositor_out,
                        "a_track":target_track_index,
                        "b_track":track.id,
                        "compositor_type":compositor_type,
                        "clip":composited_clip}
            action = edit.add_compositor_action(edit_data)
            action.do_edit()
        
        updater.repaint_tline()
        return

    clip_length = clip.clip_out - clip.clip_in
    if compositor_type == "##auto_fade_in":
        compositor_in = current_sequence().tracks[track.id].clip_start(clip_index)
        compositor_out = compositor_in + int(utils.fps()) - 1
    else: # fade out
        clip_start = current_sequence().tracks[track.id].clip_start(clip_index)
        compositor_out = clip_start + clip_length
        compositor_in = compositor_out - int(utils.fps()) + 1

    edit_data = {"origin_clip_id":clip.id,
                "in_frame":compositor_in,
                "out_frame":compositor_out,
                "a_track":target_track_index,
                "b_track":track.id,
                "compositor_type":compositor_type,
                "clip":clip}

    action = edit.add_compositor_action(edit_data)
    action.do_edit()
    
    updater.repaint_tline()

def _edit_title(data):
    clip, track, item_id, item_data = data
    titler.edit_tline_title(clip, track, _title_edit_callback)

def _title_edit_callback(clip, track, new_title_path, new_titler_data):

    clip_index = track.clips.index(clip)
    
    while os.path.exists(new_title_path) == False:
        print(new_title_path, "not yet updated")
        time.sleep(0.3)
    
    new_clip = current_sequence().create_file_producer_clip(new_title_path, None, False, clip.ttl) # file producer
    new_clip.name = clip.name

    current_sequence().clone_clip_and_filters(clip, new_clip)
    new_titler_data.destroy_pango_layouts()
    new_clip.titler_data = new_titler_data

    data = {"old_clip":clip,
            "new_clip":new_clip,
            "track":track,
            "index":clip_index}
    action = edit.reload_replace(data)
    action.do_edit()

    titler.clean_titler_instance()

def _re_render_transition_or_fade(data):
    clip, track, item_id, item_data = data

    # Fix for changed number of creation data params
    try:
        from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_index, sorted_wipe_luma_index, color_str = clip.creation_data
    except:
        print("except")
        from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_index, sorted_wipe_luma_index = clip.creation_data

    clip.creation_data = (from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_index, sorted_wipe_luma_index)

    name, type_id = mlttransitions.rendered_transitions[transition_type_index]
    if type_id < appconsts.RENDERED_FADE_IN:
        singletracktransition.re_render_transition(data)
    else:
        tlineaction.re_render_fade(data)
        
def _mute_clip(data):
    clip, track, item_id, item_data = data
    set_clip_muted = item_data

    if set_clip_muted == True:
        data = {"clip":clip}
        action = edit.mute_clip(data)
        action.do_edit()
    else:# then we're sitting clip unmuted
        data = {"clip":clip}
        action = edit.unmute_clip(data)
        action.do_edit()

def _delete_clip(data):
    tlineaction.splice_out_button_pressed()

def _lift(data):
    tlineaction.lift_button_pressed()
    
def _set_length(data):
    clip, track, item_id, item_data = data
    dialogs.clip_length_change_dialog(_change_clip_length_dialog_callback, clip, track)

def _change_clip_length_dialog_callback(dialog, response_id, clip, track, length_changer):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    length = length_changer.get_length()
    index = track.clips.index(clip)
    
    dialog.destroy()
    
    data = {"track":track,
            "clip":clip,
            "index":index,
            "length":length}
            
    action = edit.set_clip_length_action(data)
    action.do_edit()
                
def _stretch_next(data):
    clip, track, item_id, item_data = data
    try:
        next_index = track.clips.index(clip) + 1
        if next_index >= len( track.clips):
            return # clip is last clip
        if track.clips[next_index].is_blanck_clip == True:
            # Next clip is blank so we can do this.
            clip = track.clips[next_index]
            data = (clip, track, item_id, item_data)
            _cover_blank_from_prev(data, True)
    except:
        pass # any error means that this can't be done
        
def _stretch_prev(data):
    clip, track, item_id, item_data = data
    try:
        prev_index = track.clips.index(clip) - 1
        if prev_index < 0:
            return # clip is first clip
        if track.clips[prev_index].is_blanck_clip == True:
            # Next clip is blank so we can do this.
            clip = track.clips[prev_index]
            data = (clip, track, item_id, item_data)
            _cover_blank_from_next(data, True)
    except:
        pass # any error means that this can't be done
        
def _delete_blank(data):
    clip, track, item_id, x = data
    movemodes.select_blank_range(track, clip)
    from_index = movemodes.selected_range_in
    to_index = movemodes.selected_range_out  
    movemodes.clear_selected_clips()
    data = {"track":track,"from_index":from_index,"to_index":to_index}
    action = edit.remove_multiple_action(data)
    action.do_edit()

def _cover_blank_from_prev(data, called_from_prev_clip=False):
    clip, track, item_id, item_data = data
    if not called_from_prev_clip:
        clip_index = movemodes.selected_range_in - 1
        if clip_index < 0: # we're not getting legal clip index
            return 
        cover_clip = track.clips[clip_index]
    else:
        clip_index = track.clips.index(clip) - 1
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

def _cover_blank_from_next(data, called_from_next_clip=False):
    clip, track, item_id, item_data = data
    if not called_from_next_clip:
        clip_index = movemodes.selected_range_out + 1
        blank_index = movemodes.selected_range_in
        if clip_index < 0: # we are not getting a legal clip index
            return
        cover_clip = track.clips[clip_index]
    else:
        clip_index = track.clips.index(clip) + 1
        blank_index = clip_index - 1
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
        if track.clips[i].is_blanck_clip == False:
            clips.append(track.clips[i])

    data = {"clips":clips}
    action = edit.remove_multiple_filters_action(data)
    action.do_edit()
    
    movemodes.clear_selected_clips()
    updater.repaint_tline()

def  _clone_filters_from_next(data):
    clip, track, item_id, is_multi = data
    if is_multi == True:
        end_index = movemodes.selected_range_out
        if end_index == len(track.clips) - 1:
            return # clip is last clip
        clone_index = end_index + 1
        while track.clips[clone_index].is_blanck_clip == True:
            clone_index += 1
            if clone_index == len(track.clips):
                return # We auto delete blanks after clips so we should not hit this

        clone_clip = track.clips[clone_index]
                    
        for clip_index in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
            target_clip = track.clips[clip_index]
            if target_clip.is_blanck_clip == True:
                continue

            _do_filter_clone(target_clip, clone_clip)
            
        return
        
    index = track.clips.index(clip)
    if index == len(track.clips) - 1:
        return # clip is last clip
    clone_index = index + 1
    while track.clips[clone_index].is_blanck_clip == True:
        clone_index += 1
        if clone_index == len(track.clips):
            return # We auto delete blanks after clips so we should not hit this
    clone_clip = track.clips[clone_index]
    _do_filter_clone(clip, clone_clip)

def _clone_filters_from_prev(data):
    clip, track, item_id, is_multi = data
    
    if is_multi == True:
        start_index = movemodes.selected_range_in
        if start_index == 0:
            return  # clip is first clip
            
        clone_index = start_index - 1
        while track.clips[clone_index].is_blanck_clip == True:
            clone_index -= 1
            if clone_index == 0:
                return

        clone_clip = track.clips[clone_index]
                    
        for clip_index in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
            target_clip = track.clips[clip_index]
            if target_clip.is_blanck_clip == True:
                continue

            _do_filter_clone(target_clip, clone_clip)
            
        return
        
    index = track.clips.index(clip)
    if index == 0:
        return # clip is first clip
    clone_index = index - 1
    while track.clips[clone_index].is_blanck_clip == True:
        clone_index -= 1
        if clone_index == 0:
            return 
    clone_clip = track.clips[clone_index]
    _do_filter_clone(clip, clone_clip)
    
def _do_filter_clone(clip, clone_clip):
    if clone_clip.is_blanck_clip:
        return
    data = {"clip":clip,"clone_source_clip":clone_clip}
    action = edit.clone_filters_action(data)
    action.do_edit()

def _clear_filters(data):
    clip, track, item_id, item_data = data
    clear_filters()

def _multi_split_audio(data):
    clip, track, item_id, item_data = data
    clips = _get_non_blank_selected_clips(track)
    
    syncsplitevent.split_audio_from_clips_list(clips, track)

def _multi_split_audio_synched(data):
    clip, track, item_id, item_data = data
    clips = _get_non_blank_selected_clips(track)
    
    syncsplitevent.split_audio_synched_from_clips_list(clips, track)

def _get_non_blank_selected_clips(track):
    clips = []
    for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        if track.clips[i].is_blanck_clip == False:
            clips.append(track.clips[i])
    return clips

def _select_all_after(data):
    clip, track, item_id, item_data = data
    movemodes._select_multiple_clips(track.id, track.clips.index(clip), len(track.clips) - 1)
    updater.repaint_tline()

def _select_all_before(data):
    clip, track, item_id, item_data = data
    movemodes._select_multiple_clips(track.id, 0, track.clips.index(clip))
    updater.repaint_tline()

def _add_clip_marker(data):
    clip, track, item_id, item_data = data
    current_frame = PLAYER().current_frame()

    try:
        current_frame_clip_index = track.get_clip_index_at(current_frame)
        current_frame_clip = track.clips[current_frame_clip_index]
    except:
        current_frame_clip = None
    
    if current_frame_clip != clip:
        # Playhead is not on popup clip
        return

    clip_start_in_tline = track.clip_start(current_frame_clip_index)
    clip_frame = current_frame - clip_start_in_tline + clip.clip_in
    
    dialogs.clip_marker_name_dialog(utils.get_tc_string(clip_frame), utils.get_tc_string(current_frame), _clip_marker_add_dialog_callback, (clip, track, clip_frame))

def _clip_marker_add_dialog_callback(dialog, response_id, name_entry, data):
    clip, track, clip_frame = data
    name = name_entry.get_text()
    dialog.destroy()
    
    # remove older on same frame
    dupl_index = -1
    for i in range(0, len(clip.markers)):
        marker_name, frame = clip.markers[i]
        if frame == clip_frame:
            dupl_index = i
    if dupl_index != -1:
        current_sequence().markers.pop(dupl_index)

    clip.markers.append((name, clip_frame))
    clip.markers = sorted(clip.markers, key=itemgetter(1))
    updater.repaint_tline()

def _go_to_clip_marker(data):
    clip, track, item_id, item_data = data
    marker = clip.markers[int(item_data)]
    name, clip_frame = marker
    
    clip_start_in_tline = track.clip_start(track.clips.index(clip))
    marker_frame = clip_start_in_tline + clip_frame - clip.clip_in

    PLAYER().seek_frame(marker_frame)

def _delete_clip_marker(data):
    clip, track, item_id, item_data = data

    clip_start_in_tline = track.clip_start(track.clips.index(clip))
    current_frame = PLAYER().current_frame()

    mrk_index = -1
    for i in range(0, len(clip.markers)):
        name, marker_clip_frame = clip.markers[i]
        marker_tline_frame = clip_start_in_tline + marker_clip_frame - clip.clip_in
        if marker_tline_frame == current_frame:
            mrk_index = i
    if mrk_index != -1:
        clip.markers.pop(mrk_index)
        updater.repaint_tline()

def _delete_all_clip_markers(data):
    clip, track, item_id, item_data = data
    clip.markers = []
    updater.repaint_tline()

def _volume_keyframes(data):
    clip, track, item_id, item_data = data
    modesetting.kftool_mode_from_popup_menu(clip, track, kftoolmode.VOLUME_KF_EDIT)
    
def _brightness_keyframes(data):
    clip, track, item_id, item_data = data
    modesetting.kftool_mode_from_popup_menu(clip, track, kftoolmode.BRIGHTNESS_KF_EDIT)

def _reload_clip_media(data):
    clip, track, item_id, item_data = data
    
    # TODO: This ain't doing the clip icon update as wished.
    media_item = PROJECT().get_media_file_for_path(clip.path)
    media_item.create_icon()
    
    clip_index = track.clips.index(clip)
    new_clip = current_sequence().create_clone_clip(clip)
    
    data = {"old_clip":clip,
            "new_clip":new_clip,
            "track":track,
            "index":clip_index}
    action = edit.reload_replace(data)
    action.do_edit()

def _create_container_clip_from_selection(data):
    GLib.idle_add(projectaction.create_selection_compound_clip)

def _get_data_with_xpos(data):
    clip, track, item_id, item_data = data
    clip, track, x = _popover_clip_data
    return (clip, track, item_id, x)
    
def _split_audio(data):
    syncsplitevent.split_audio(_get_data_with_xpos(data))

def _split_audio_synched(data):
    syncsplitevent.split_audio_synched(_get_data_with_xpos(data))

def _set_audio_sync_clip(data):
    audiosync.init_select_tline_sync_clip(_get_data_with_xpos(data))

def _render_tline_generator(data):
    clip, track, item_id, item_data = data
    clip, track, x = _popover_clip_data
    containerclip.render_tline_generator_clip(clip, _render_tline_generator_callback)

def _render_tline_generator_callback(combo):
    clip, track, x = _popover_clip_data
    render_data = (clip, None, None, None) # We keep old data package format for now.
    if combo.get_active() == 0: # 0 is render full media, see containeractions.set_video_endoding()
        containerclip.render_full_media(render_data)
    else:
        containerclip.render_clip_length(render_data)

    """
    TODO: see if "cc_render_full_media", "cc_render_settings" ca be deleted below.
    """

# Functions to handle popup menu selections for strings 
# set as activation messages in guipopoverclip.py
# activation_message -> _handler_func
POPUP_HANDLERS = {"set_master":syncsplitevent.init_select_master_clip,
                  "open_in_editor":_open_clip_in_effects_editor,
                  "clip_info":_show_clip_info,
                  "open_in_clip_monitor":_open_clip_in_clip_monitor,
                  "rename_clip":_rename_clip,
                  "clip_color":_clip_color,
                  "split_audio":_split_audio,
                  "split_audio_synched":_split_audio_synched,
                  "resync":syncsplitevent.resync_clip,
                  "add_filter":_add_filter,
                  "add_filter_multi":_add_filter_multi,
                  "add_compositor":_add_compositor,
                  "clear_sync_rel":syncsplitevent.clear_sync_relation,
                  "mute_clip":_mute_clip,
                  "delete_blank":_delete_blank,
                  "cover_with_prev": _cover_blank_from_prev,
                  "cover_with_next": _cover_blank_from_next,
                  "clone_filters_from_next": _clone_filters_from_next,
                  "clone_filters_from_prev": _clone_filters_from_prev,
                  "clear_filters": _clear_filters,
                  "select_all_after": _select_all_after,
                  "select_all_before":_select_all_before,
                  "delete":_delete_clip,
                  "lift":_lift, 
                  "length":_set_length,
                  "stretch_next":_stretch_next, 
                  "stretch_prev":_stretch_prev,
                  "add_autofade":_add_autofade,
                  "set_audio_sync_clip":_set_audio_sync_clip,
                  "re_render":_re_render_transition_or_fade,
                  "add_clip_marker":_add_clip_marker,
                  "go_to_clip_marker":_go_to_clip_marker,
                  "delete_clip_marker":_delete_clip_marker,
                  "deleteall_clip_markers":_delete_all_clip_markers,
                  "volumekf":_volume_keyframes,
                  "brightnesskf":_brightness_keyframes,
                  "delete_compositors":_delete_compositors,
                  "multi_delete_compositors": _multi_delete_compositors,
                  "reload_media":_reload_clip_media,
                  "create_multi_compound":_create_container_clip_from_selection,
                  "multi_split_audio":_multi_split_audio,
                  "multi_split_audio_synched":_multi_split_audio_synched,
                  "cc_render_full_media":containerclip.render_full_media,
                  "cc_render_clip":_render_tline_generator,
                  "cc_go_to_underdered":containerclip.switch_to_unrendered_media,
                  "cc_render_settings":containerclip.set_render_settings,
                  "cc_edit_program":containerclip.edit_program,
                  "cc_clone_generator":mediaplugin.add_media_plugin_clone,
                  "edit_title":_edit_title}
