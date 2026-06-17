"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2022 Janne Liljeblad.

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
This module handles creating single track rendered transitions.
"""

from gi.repository import Gtk, GLib

import hashlib
import os
import time

import appconsts
import dialogs
import dialogutils
import edit
import editorstate
from editorstate import current_sequence
from editorstate import get_track
from editorstate import PROJECT
import gui
import mlttransitions
import movemodes
import renderconsumer
import render
import respaths
import singletracktransitiondialogs
import userfolders

# Used to store transition render data needed at render complete callback.
transition_render_data = None

#    NOTE: rendered transitions require 1 frame extra on both ends: to in, from out
#
#
#                to clip req            cut        from clip req
#                (length + 2) // 2                 (length + 2) // 2 (+1 if length odd)
#           |                            |                            | 
#----------------------------------------|----------------------------------------
#            |                           |                           |
#                   to clip part                    from clip part
#                     to clip req - 1               from clip req - 1
#
#
#  from clip |              rendered transition clip on tline        | to clip
#  out = orig out - to clip part                                       in = orig in + from clip part  
#
#
#           |              rendered transition clip                   |
#                          length + 2 = to clip reg + from clip req
#           from in = from out orig - to clip req, from out = from in + length + 2 
#           to in = to in orig - to clip req, to out = to in + length + 2  
#
#            |              rendered transition clip on tline        |
#                           length, in = 1, out = media length - 1 (-1 out incl.)



# ------------------------------------------------------------- parts computation funcs
def get_parts_and_reqs_for_length(length):
    real_length = length + 2
    to_req = real_length // 2
    from_req = to_req
    if length % 2 == 1:
        from_req = from_req + 1
    to_part = to_req - 1
    from_part = from_req - 1
    
    return (from_req, to_req, from_part, to_part)

def _get_available_handles(from_clip, to_clip):
    from_handle = from_clip.get_length() - from_clip.clip_out - 1 # -1 out incl.
    to_handle = to_clip.clip_in
    
    # Images have limitless handles, but we simulate that with big value
    IMAGE_MEDIA_HANDLE_LENGTH = 1000
    if from_clip.media_type == appconsts.IMAGE:
        from_handle = IMAGE_MEDIA_HANDLE_LENGTH
    if to_clip.media_type == appconsts.IMAGE:
        to_handle = IMAGE_MEDIA_HANDLE_LENGTH
        
    return (from_handle -1, to_handle -1) # -1,-1 at least one unused frame outside of trnasition value required 

def get_transition_data_for_clips(track, from_clip, to_clip):
    from_handle, to_handle = _get_available_handles(from_clip, to_clip)
    max_handle = from_handle
    if to_handle < from_handle:
        max_handle = to_handle    

    max_length = max_handle * 2
    
    transition_data = {"track":track,
                       "from_clip":from_clip,
                       "to_clip":to_clip,
                       "from_handle":from_handle,
                       "to_handle":to_handle,
                       "max_length":max_length}
    return transition_data

def _get_clips_overlapping_ranges(length, from_clip_out, to_clip_in, from_part, to_part):
    # Get from in and out frames
    from_in = from_clip_out - to_part
    from_out = from_in + length - 1 # -1 out incl.
    
    # Get to in and out frames
    to_in = to_clip_in - from_part
    to_out = to_in + length - 1 # -1 out incl.

    return (from_in, from_out, to_in, to_out)


# ------------------------------------------------------------- external interface
def add_transition_menu_item_selected():
    add_transition_pressed()

def add_transition_pressed(retry_from_render_folder_select=False):
    if movemodes.selected_track == -1:
        print("no selection track")
        # TODO:  info?
        return

    track = get_track(movemodes.selected_track)
    clip_count = movemodes.selected_range_out - movemodes.selected_range_in + 1 # +1 out incl.

    if not (clip_count == 2):
        return

    from_clip = track.clips[movemodes.selected_range_in]
    to_clip = track.clips[movemodes.selected_range_out]
    
    transition_data = get_transition_data_for_clips(track, from_clip, to_clip)
    
    if transition_data["max_length"] < 2:
        # INFOWINDOW
        return 

    if track.id >= current_sequence().first_video_index:
        singletracktransitiondialogs.transition_edit_dialog(_add_transition_dialog_callback, 
                                                            transition_data)
    else:
        singletracktransitiondialogs.no_audio_tracks_mixing_info()

def get_transition_drag_data(track, index):
    transition_data = {}
    try:
        current_transition_clip = track.clips[index]
        from_clip = track.clips[index - 1]
        to_clip = track.clips[index + 1]
        transition_data["from_clip"] = from_clip
        transition_data["to_clip"] = to_clip
    except:
         transition_data["legal"] = False
         return 

    from_req, to_req, from_part, to_part = get_parts_and_reqs_for_length(current_transition_clip.clip_length())

    transition_data["from_handle_from_center"] = abs(from_clip.get_length() - from_clip.clip_out - from_part)
    transition_data["to_handle_from_center"] = abs(to_clip.clip_in - to_part)
    transition_data["center_frame"] = track.clip_start(index) + from_part
    if transition_data["to_handle_from_center"]  > transition_data["from_handle_from_center"]:
        transition_data["max_handle_from_center"] = transition_data["from_handle_from_center"]
    else:
        transition_data["max_handle_from_center"] = transition_data["to_handle_from_center"]

    return transition_data

def add_transition_from_dnd(track, from_clip, to_clip, from_clip_index, is_dissolve, wipe_mame):
    transition_data = get_transition_data_for_clips(track, from_clip, to_clip)
    transition_data["dnd_wipe_name"] = wipe_mame
    transition_data["dnd_is_dissolve"] = is_dissolve
    transition_data["dnd_from_clip_index"] = from_clip_index

    from_clip_index = movemodes.selected_range_in
    
    # We're piggypacking existing dialog callback method and will use some default values for rendering. 
    _add_transition_dialog_callback(None, None, None, transition_data)

def _add_transition_dialog_callback(dialog, response_id, selection_widgets, transition_data):
    # This is now baing used to create transitions from dnd and then no creation dialog exists. 
    if dialog != None:

        if response_id != Gtk.ResponseType.ACCEPT:
            dialog.destroy()
            return

        # Get input data
        type_combo, length_entry, enc_combo, quality_combo, wipe_luma_combo_box, encodings = selection_widgets
        transition_type_selection_index = type_combo.get_active()

        quality_option_index = quality_combo.get_active()
        
        # 'encodings' is subset of 'renderconsumer.encoding_options' because libx264 was always buggy for this 
        # use. We find out right 'renderconsumer.encoding_options' index for rendering.
        selected_encoding_option_index = enc_combo.get_active()
        enc = encodings[selected_encoding_option_index]
        encoding_option_index = renderconsumer.encoding_options.index(enc)
        
        extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension
        sorted_wipe_luma_index = wipe_luma_combo_box.get_active()

        try:
            length = int(length_entry.get_text())
        except Exception as e:
            # INFOWINDOW, bad input
            dialog.destroy()
            return

        dialog.destroy()
        
        from_clip_index = movemodes.selected_range_in    
    else:
        # Create data to match what we get from dialog when we caome here from 
        length = 30
        transition_type_selection_index = 0
        sorted_wipe_luma_index = 0
        if transition_data["dnd_is_dissolve"] == False:
            transition_type_selection_index = 1
            sorted_wipe_luma_index = mlttransitions.get_sorted_wipe_luma_index_for_name(transition_data["dnd_wipe_name"])

        # 'encodings' is subset of 'renderconsumer.encoding_options' because libx264 was always buggy for this 
        # use. We find out right 'renderconsumer.encoding_options' index for rendering.
        # TODO: See panels.py also, this needs to be killed somehow.
        encodings = []
        for encoding in renderconsumer.encoding_options:
            if encoding.vcodec != "libx264":
                encodings.append(encoding)

        try:
            encoding_option_index, quality_option_index = PROJECT().get_project_property(appconsts.P_PROP_TRANSITION_ENCODING)
        except:
            encoding_option_index = 0
            quality_option_index = 0

        extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension

        from_clip_index = transition_data["dnd_from_clip_index"] 

    from_clip = transition_data["from_clip"]
    to_clip = transition_data["to_clip"]
    
    from_handle = transition_data["from_handle"]
    to_hjandle = transition_data["to_handle"]


    # Get required lengths and parts
    from_req, to_req, from_part, to_part =  get_parts_and_reqs_for_length(length)

    # Check that we have enough handles
    if from_req > transition_data["from_handle"] or to_req >  transition_data["to_handle"]:
        singletracktransitiondialogs.show_no_handles_dialog( from_req,
                                     from_handle, 
                                     to_req,
                                     to_handle,
                                     length)
        return

    editorstate.transition_length = length # Saved for user so that last length becomes default for next invocation.

    from_in, from_out, to_in, to_out = _get_clips_overlapping_ranges(length, from_clip.clip_out, to_clip.clip_in, from_part, to_part)

    # Edit clears selection, get transition index before selection is cleared
    trans_index = from_clip_index + 1
    movemodes.clear_selected_clips()

    # Save encoding
    PROJECT().set_project_property(appconsts.P_PROP_TRANSITION_ENCODING, (encoding_option_index, quality_option_index))

    producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                        from_clip,
                                                                        to_clip,
                                                                        from_out,
                                                                        from_in,
                                                                        to_out,
                                                                        to_in,
                                                                        transition_type_selection_index,
                                                                        sorted_wipe_luma_index)

    creation_data = (   from_clip.id,
                        to_clip.id,
                        from_out,
                        from_in,
                        to_out,
                        to_in,
                        transition_type_selection_index,
                        sorted_wipe_luma_index)
                                                
    # Save transition data into global variable to be available at render complete callback
    global transition_render_data
    transition_render_data = (trans_index, from_clip, to_clip, transition_data["track"], from_in, to_out, transition_type_selection_index, creation_data)
    window_text, type_id = mlttransitions.rendered_transitions[transition_type_selection_index]
    window_text = _("Rendering ") + window_text

    render.render_single_track_transition_clip( producer_tractor,
                                                encoding_option_index,
                                                quality_option_index, 
                                                str(extension_text), 
                                                _transition_render_complete,
                                                window_text)

def _transition_render_complete(clip_path):

    global transition_render_data
    transition_index, from_clip, to_clip, track, from_in, to_out, transition_type, creation_data = transition_render_data

    transition_clip = current_sequence().create_rendered_transition_clip(clip_path, transition_type)
    transition_clip.creation_data = creation_data

    data = {"transition_clip":transition_clip,
            "transition_index":transition_index,
            "from_clip":from_clip,
            "to_clip":to_clip,
            "track":track,
            "from_in":from_in,
            "to_out":to_out}

    action = edit.add_centered_transition_action(data)
    action.do_edit()

def re_render_transition(data):
    clip, track, msg, x = data
    if not hasattr(clip, "creation_data"):
        singletracktransitiondialogs.no_creation_data_dialog()
        return
    
    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_selection_index, \
    sorted_wipe_luma_index = clip.creation_data
    
    from_clip = editorstate.current_sequence().get_clip_for_id(from_clip_id)
    to_clip = editorstate.current_sequence().get_clip_for_id(to_clip_id)
    if from_clip == None or to_clip == None:
        singletracktransitiondialogs.source_clips_not_found_dialog()
        return

    transition_data = {"track":track,
                        "clip":clip,
                        "from_clip":from_clip,
                        "to_clip":to_clip}

    dialogs.transition_re_render_dialog(_transition_RE_render_dialog_callback, transition_data)

def _transition_RE_render_dialog_callback(dialog, response_id, selection_widgets, transition_data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    enc_combo, quality_combo, encodings = selection_widgets
    quality_option_index = quality_combo.get_active()

    # 'encodings' is subset of 'renderconsumer.encoding_options' because libx264 was always buggy for this 
    # use. We find out right 'renderconsumer.encoding_options' index for rendering.
    selected_encoding_option_index = enc_combo.get_active()
    enc = encodings[selected_encoding_option_index]
    encoding_option_index = renderconsumer.encoding_options.index(enc)
    
    dialog.destroy()
        
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension

    clip = transition_data["clip"]
    track =  transition_data["track"]
    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_selection_index, \
    sorted_wipe_luma_index = clip.creation_data
    
    trans_index = track.clips.index(clip)

    producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                        transition_data["from_clip"],
                                                                        transition_data["to_clip"],
                                                                        from_out,
                                                                        from_in,
                                                                        to_out,
                                                                        to_in,
                                                                        transition_type_selection_index,
                                                                        sorted_wipe_luma_index)
    

    # Save transition data into global variable to be available at render complete callback
    global transition_render_data
    transition_render_data = (trans_index, track, clip, transition_type_selection_index, clip.creation_data)
    window_text, type_id = mlttransitions.rendered_transitions[transition_type_selection_index]
    window_text = _("Rerendering ") + window_text

    render.render_single_track_transition_clip( producer_tractor,
                                                encoding_option_index,
                                                quality_option_index, 
                                                str(extension_text), 
                                                _transition_RE_render_complete,
                                                window_text)

def _transition_RE_render_complete(clip_path):
    global transition_render_data
    transition_index, track, orig_clip, transition_type, creation_data = transition_render_data

    transition_clip = current_sequence().create_rendered_transition_clip(clip_path, transition_type)
    transition_clip.creation_data = creation_data
    transition_clip.clip_in = orig_clip.clip_in
    transition_clip.clip_out = orig_clip.clip_out

    data = {"track":track,
            "transition_clip":transition_clip,
            "transition_index":transition_index}

    action = edit.replace_centered_transition_action(data)
    action.do_edit()

def create_length_changed_transition(track, index, new_length):
    # Get old transition data.
    old_transition_clip = track.clips[index]
    # We need transition type and possible wipe luma from old transition.
    old_from_clip_id, old_to_clip_id, old_from_out, old_from_in, old_to_out, old_to_in, transition_type_selection_index, \
    sorted_wipe_luma_index = old_transition_clip.creation_data

    old_from_req, old_to_req, old_from_part, old_to_part = get_parts_and_reqs_for_length(old_transition_clip.clip_length())

    # Get current from_to_clips.
    try:
        from_clip = track.clips[index - 1]
        to_clip = track.clips[index + 1]
    except:
        print("clips not available")
        # TODO: Info?
        return

    # Get new parts and reqs.
    from_req, to_req, from_part, to_part = get_parts_and_reqs_for_length(new_length)

    # Get from clip out and to clip in as if the currently exiting transition wasn't there.
    from_clip_out = from_clip.clip_out + old_from_part
    to_clip_in = to_clip.clip_in - old_to_part

    # Get new transition clip ranges.
    from_in, from_out, to_in, to_out = _get_clips_overlapping_ranges(new_length, from_clip_out, to_clip_in, from_part, to_part)

    producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                        from_clip,
                                                                        to_clip,
                                                                        from_out,
                                                                        from_in,
                                                                        to_out,
                                                                        to_in,
                                                                        transition_type_selection_index,
                                                                        sorted_wipe_luma_index)

    creation_data = (   from_clip.id,
                        to_clip.id,
                        from_out,
                        from_in,
                        to_out,
                        to_in,
                        transition_type_selection_index,
                        sorted_wipe_luma_index)

    encoding_option_index, quality_option_index = PROJECT().get_project_property(appconsts.P_PROP_TRANSITION_ENCODING)
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension

    # Save transition data into global variable to be available at render complete callback
    global transition_render_data
    transition_render_data = (index, from_clip, to_clip, track, from_in, to_out, transition_type_selection_index, creation_data)
    
    window_text, type_id = mlttransitions.rendered_transitions[transition_type_selection_index]
    window_text = _("Rendering ") + window_text

    render.render_single_track_transition_clip( producer_tractor,
                                                encoding_option_index,
                                                quality_option_index, 
                                                str(extension_text), 
                                                _length_changed_transition_rendered_callback,
                                                window_text)

def _length_changed_transition_rendered_callback(clip_path):

    global transition_render_data
    transition_index, from_clip, to_clip, track, from_in, to_out, transition_type, creation_data = transition_render_data

    transition_clip = current_sequence().create_rendered_transition_clip(clip_path, transition_type)
    transition_clip.creation_data = creation_data

    data = {"transition_clip":transition_clip,
            "transition_index":transition_index,
            "from_clip":from_clip,
            "to_clip":to_clip,
            "track":track,
            "from_in":from_in,
            "to_out":to_out}

    action = edit.replace_length_changed_transition_action(data)
    action.do_edit()

# ----------------------------------------------------------- re-redering
def rerender_all_rendered_transitions():
    seq = editorstate.current_sequence()
    
    # Get list of rerendered transitions and unrenderable count
    rerender_list = []
    unrenderable = 0
    for i in range(1, len(seq.tracks)):
        track = seq.tracks[i]
        for j in range(0, len(track.clips)):
            clip = track.clips[j]
            if hasattr(clip, "rendered_type"):
                if hasattr(clip, "creation_data"):
                    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, \
                    transition_type_selection_index, sorted_wipe_luma_index = clip.creation_data
                    from_clip = editorstate.current_sequence().get_clip_for_id(from_clip_id)
                    to_clip = editorstate.current_sequence().get_clip_for_id(to_clip_id)
                    # transition
                    if from_clip == None or to_clip == None:
                         unrenderable += 1
                    else:
                        rerender_list.append((clip, track))
            
                else:
                    unrenderable += 1
    
    # Show dialog and pass data
    dialogs.re_render_all_dialog(_RE_render_all_dialog_callback, rerender_list, unrenderable)

def _RE_render_all_dialog_callback(dialog, response_id, selection_widgets, rerender_list):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    # Get input data
    enc_combo, quality_combo, encodings = selection_widgets
    quality_option_index = quality_combo.get_active()
    
    # 'encodings' is subset of 'renderconsumer.encoding_options' because libx264 was always buggy for this 
    # use. We find out right 'renderconsumer.encoding_options' index for rendering.
    selected_encoding_option_index = enc_combo.get_active()
    enc = encodings[selected_encoding_option_index]
    encoding_option_index = renderconsumer.encoding_options.index(enc)
    
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension

    dialog.destroy()
    
    renrender_window = singletracktransitiondialogs.ReRenderderAllWindow((encoding_option_index, quality_option_index, extension_text), rerender_list)
    renrender_window.create_gui()
    renrender_window.start_render()

