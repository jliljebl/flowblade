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
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Module handles button edit events from buttons in the middle bar.
"""

import pygtk
pygtk.require('2.0');
import gtk

import os
from operator import itemgetter

import appconsts
import dialogs
import dialogutils
import gui
import guicomponents
import edit
import editevent
import editorpersistance
import editorstate
from editorstate import get_track
from editorstate import current_sequence
from editorstate import PLAYER
from editorstate import timeline_visible
from editorstate import MONITOR_MEDIA_FILE
from editorstate import EDIT_MODE
import movemodes
import mlttransitions
import render
import renderconsumer
import syncsplitevent
import updater
import utils

# Used to store transition render data to be used at render complete callback
transition_render_data = None


# --------------------------- module funcs
def _get_new_clip_from_clip_monitor():
    """
    Creates and returns new clip from current clip monitor clip
    with user set in and out points.
    """
    if MONITOR_MEDIA_FILE() == None:
        # Info window here
        return
    
    if MONITOR_MEDIA_FILE().type != appconsts.PATTERN_PRODUCER:
        new_clip = current_sequence().create_file_producer_clip(MONITOR_MEDIA_FILE().path)
    else:
        new_clip = current_sequence().create_pattern_producer(MONITOR_MEDIA_FILE())
        
    # Set clip in and out points
    new_clip.mark_in = MONITOR_MEDIA_FILE().mark_in
    new_clip.mark_out = MONITOR_MEDIA_FILE().mark_out
    new_clip.name = MONITOR_MEDIA_FILE().name

    if new_clip.mark_in == -1:
         new_clip.mark_in = 0
    if new_clip.mark_out == -1:
        new_clip.mark_out = new_clip.get_length() - 1 #-1 == out inclusive

    return new_clip

# How to get this depends on what is displayed on monitor
def _current_tline_frame():
    return editorstate.current_tline_frame()

# ---------------------------------- edit button events
def cut_pressed():
    if not timeline_visible():
        updater.display_sequence_in_monitor()

    if EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        editevent.oneroll_trim_no_edit_init()
        return

    if EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        editevent.tworoll_trim_no_edit_init()
        return
        
    tline_frame = PLAYER().current_frame()

    movemodes.clear_selected_clips()

    # Iterate tracks and do cut on all active that have non-blanck
    # clips and frame is not on previous edits
    for i in range(1, len(current_sequence().tracks)):
        track = get_track(i)
        if track.active == False:
            continue
        
        if editevent.track_lock_check_and_user_info(track, cut_pressed, "cut"): # so the other tracks get cut...
           continue 

        # Get index and clip
        index = track.get_clip_index_at(int(tline_frame))
        try:
            clip = track.clips[index]            
            # don't cut blanck clip
            if clip.is_blanck_clip:
                continue
        except Exception:
            continue # Frame after last clip in track

        # Get cut frame in clip frames
        clip_start_in_tline = track.clip_start(index)
        clip_frame = tline_frame - clip_start_in_tline + clip.clip_in

        # Dont edit if frame on cut.
        if clip_frame == clip.clip_in:
            continue

        # Do edit
        data = {"track":track,
                "index":index,
                "clip":clip,
                "clip_cut_frame":clip_frame}
        action = edit.cut_action(data)
        action.do_edit()
   
    updater.repaint_tline()

def splice_out_button_pressed():
    """
    Removes 1 - n long continuous clip range from track and closes
    the created gap.
    """
    if movemodes.selected_track == -1:
        return

    # Edit consumes selection, so clear selected from clips
    movemodes.set_range_selection(movemodes.selected_track,
                                  movemodes.selected_range_in,
                                  movemodes.selected_range_out,
                                  False)
    
    track = get_track(movemodes.selected_track)

    if editevent.track_lock_check_and_user_info(track, splice_out_button_pressed, "splice out"):
        movemodes.clear_selection_values()
        return

    data = {"track":track,
            "from_index":movemodes.selected_range_in,
            "to_index":movemodes.selected_range_out}
    edit_action = edit.remove_multiple_action(data)
    edit_action.do_edit()

    # Nothing is selected after edit
    movemodes.clear_selection_values()

    updater.repaint_tline()

def lift_button_pressed():
    """
    Removes 1 - n long continuous clip range from track and fills
    the created gap with a black clip
    """
    if movemodes.selected_track == -1:
        return

    # Edit consumes selection, set clips seletion attr to false
    movemodes.set_range_selection(movemodes.selected_track, 
                                  movemodes.selected_range_in,
                                  movemodes.selected_range_out, 
                                  False)
                         
    track = get_track(movemodes.selected_track)

    if editevent.track_lock_check_and_user_info(track, lift_button_pressed, "lift"):
        movemodes.clear_selection_values()
        return

    data = {"track":track,
            "from_index":movemodes.selected_range_in,
            "to_index":movemodes.selected_range_out}
    edit_action = edit.lift_multiple_action(data)
    edit_action.do_edit()

    # Nothing is left selected after edit
    movemodes.clear_selection_values()

    updater.repaint_tline()

def insert_button_pressed():
    track = current_sequence().get_first_active_track()

    if editevent.track_lock_check_and_user_info(track, insert_button_pressed, "insert"):
        return

    tline_pos =_current_tline_frame()
    
    new_clip = _get_new_clip_from_clip_monitor()
    if new_clip == None:
        no_monitor_clip_info(gui.editor_window.window)
        return

    updater.save_monitor_frame = False # hack to not get wrong value saved in MediaFile.current_frame
    editevent.do_clip_insert(track, new_clip, tline_pos)
    
def append_button_pressed():
    track = current_sequence().get_first_active_track()

    if editevent.track_lock_check_and_user_info(track, append_button_pressed, "insert"):
        return

    tline_pos = track.get_length()
    
    new_clip = _get_new_clip_from_clip_monitor()
    if new_clip == None:
        no_monitor_clip_info(gui.editor_window.window)
        return

    updater.save_monitor_frame = False # hack to not get wrong value saved in MediaFile.current_frame
    editevent.do_clip_insert(track, new_clip, tline_pos)

def three_point_overwrite_pressed():
    # Check that state is good for edit
    if movemodes.selected_track == -1:
        primary_txt = _("No Clips are selected!")
        secondary_txt = _("You need to select clips to overwrite to perform this edit.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    # Get data
    track = get_track(movemodes.selected_track)
    if editevent.track_lock_check_and_user_info(track, three_point_overwrite_pressed, "3 point overwrite"):
        return
    
    range_start_frame = track.clip_start(movemodes.selected_range_in)
    out_clip = track.clips[movemodes.selected_range_out]
    out_start = track.clip_start(movemodes.selected_range_out)
    range_end_frame = out_start + out_clip.clip_out - out_clip.clip_in
    range_length = range_end_frame - range_start_frame + 1 # calculated end is incl.

    over_clip = _get_new_clip_from_clip_monitor()
    if over_clip == None:
        no_monitor_clip_info(gui.editor_window.window)
        return
    over_length = over_clip.mark_out - over_clip.mark_in + 1 # + 1 out incl ?????????? what if over_clip.mark_out == -1  ?????????? 
    
    if over_length < range_length:
        monitor_clip_too_short(gui.editor_window.window)
        return
    
    over_clip_out = over_clip.mark_in + range_length - 1 # -1 out incl
    
    range_in = movemodes.selected_range_in
    range_out = movemodes.selected_range_out
    
    movemodes.clear_selected_clips() # edit consumes selection

    updater.save_monitor_frame = False # hack to not get wrong value saved in MediaFile.current_frame

    data = {"track":track,
            "clip":over_clip,
            "clip_in":over_clip.mark_in,
            "clip_out":over_clip_out,
            "in_index":range_in,
            "out_index":range_out}
    action = edit.three_point_overwrite_action(data)
    action.do_edit()

    updater.display_tline_cut_frame(track, range_in)

def range_overwrite_pressed():
    # Get data
    track = current_sequence().get_first_active_track()
    if editevent.track_lock_check_and_user_info(track, range_overwrite_pressed, "range overwrite"):
        return
    
    # tractor is has mark in and mark
    mark_in_frame = current_sequence().tractor.mark_in
    mark_out_frame = current_sequence().tractor.mark_out
    range_length = mark_out_frame - mark_in_frame + 1 # end is incl.
    if mark_in_frame == -1 or mark_out_frame == -1:
        primary_txt = _("Timeline Range not set!")
        secondary_txt = _("You need to set Timeline Range using Mark In and Mark Out buttons\nto perform this edit.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    # Get over clip and check it overwrite range area
    over_clip = _get_new_clip_from_clip_monitor()
    if over_clip == None:
        no_monitor_clip_info(gui.editor_window.window)
        return

    over_length = over_clip.mark_out - over_clip.mark_in + 1 # + 1 out incl
    if over_length < range_length:
        monitor_clip_too_short(gui.editor_window.window)
        return

    over_clip_out = over_clip.mark_in + range_length - 1

    movemodes.clear_selected_clips() # edit consumes selection

    updater.save_monitor_frame = False # hack to not get wrong value saved in MediaFile.current_frame

    data = {"track":track,
            "clip":over_clip,
            "clip_in":over_clip.mark_in,
            "clip_out":over_clip_out,
            "mark_in_frame":mark_in_frame,
            "mark_out_frame":mark_out_frame + 1} # +1 because mark is displayed and end of frame end this 
                                                 # confirms to user expectation of
                                                 # of how this should work
    action = edit.range_overwrite_action(data)
    action.do_edit()

    updater.display_tline_cut_frame(track, track.get_clip_index_at(mark_in_frame))

def resync_button_pressed():
    syncsplitevent.resync_selected()

def add_transition_menu_item_selected():
    if movemodes.selected_track == -1:
        # INFOWINDOW
        return

    clip_count = movemodes.selected_range_out - movemodes.selected_range_in + 1 # +1 out incl.
    if not (clip_count == 2):
        # INFOWINDOW
        return
    add_transition_pressed()
    
def add_fade_menu_item_selected():
    if movemodes.selected_track == -1:
        print "so selection track"
        # INFOWINDOW
        return

    clip_count = movemodes.selected_range_out - movemodes.selected_range_in + 1 # +1 out incl.
    if not (clip_count == 1):
        # INFOWINDOW
        return
    add_transition_pressed()

def add_transition_pressed(retry_from_render_folder_select=False):
    if movemodes.selected_track == -1:
        print "so selection track"
        # INFOWINDOW
        return

    track = get_track(movemodes.selected_track)
    clip_count = movemodes.selected_range_out - movemodes.selected_range_in + 1 # +1 out incl.

    if not ((clip_count == 2) or (clip_count == 1)):
        # INFOWINDOW
        print "clip count"
        return

    if track.id < current_sequence().first_video_index and clip_count == 1:
        _no_audio_tracks_mixing_info()
        return

    if editorpersistance.prefs.render_folder == None:
        if retry_from_render_folder_select == True:
            return
        dialogs.select_rendred_clips_dir(_add_transition_render_folder_select_callback,
                                         gui.editor_window.window,
                                         editorpersistance.prefs.render_folder)
        return

    if clip_count == 2:
        _do_rendered_transition(track)
    else:
        _do_rendered_fade(track)

def _do_rendered_transition(track):
    from_clip = track.clips[movemodes.selected_range_in]
    to_clip = track.clips[movemodes.selected_range_out]
    
    # Get available clip handles to do transition
    from_handle = from_clip.get_length() - from_clip.clip_out
    from_clip_length = from_clip.clip_out - from_clip.clip_in                                                 
    to_handle = to_clip.clip_in
    to_clip_length = to_clip.clip_out - to_clip.clip_in
    
    if to_clip_length < from_handle:
        from_handle = to_clip_length
    if from_clip_length < to_handle:
        to_handle = from_clip_length
        
    # Images have limitless handles, but we simulate that with big value
    IMAGE_MEDIA_HANDLE_LENGTH = 1000
    if from_clip.media_type == appconsts.IMAGE:
        from_handle = IMAGE_MEDIA_HANDLE_LENGTH
    if to_clip.media_type == appconsts.IMAGE:
        to_handle = IMAGE_MEDIA_HANDLE_LENGTH
     
    max_length = from_handle + to_handle
    
    transition_data = {"track":track,
                       "from_clip":from_clip,
                       "to_clip":to_clip,
                       "from_handle":from_handle,
                       "to_handle":to_handle,
                       "max_length":max_length}

    if track.id >= current_sequence().first_video_index:
        dialogs.transition_edit_dialog(_add_transition_dialog_callback, 
                                       transition_data)
    else:
        _no_audio_tracks_mixing_info()
        
def _add_transition_render_folder_select_callback(dialog, response_id, file_select):
    try:
        folder = file_select.get_filenames()[0]
    except:
        dialog.destroy()
        return

    dialog.destroy()
    if response_id == gtk.RESPONSE_YES:
        if folder ==  os.path.expanduser("~"):
            dialogs.rendered_clips_no_home_folder_dialog()
        else:
            editorpersistance.prefs.render_folder = folder
            editorpersistance.save()
            add_transition_pressed(True)

def _add_transition_dialog_callback(dialog, response_id, selection_widgets, transition_data):
    if response_id != gtk.RESPONSE_ACCEPT:
        dialog.destroy()
        return

    # Get input data
    type_combo, length_entry, enc_combo, quality_combo, wipe_luma_combo_box, color_button = selection_widgets
    encoding_option_index = enc_combo.get_active()
    quality_option_index = quality_combo.get_active()
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension
    sorted_wipe_luma_index = wipe_luma_combo_box.get_active()
    color_str = color_button.get_color().to_string()

    try:
        length = int(length_entry.get_text())
    except Exception, e:
        # INFOWINDOW, bad input
        print str(e)
        print "entry"
        return

    dialog.destroy()

    from_clip = transition_data["from_clip"]
    to_clip = transition_data["to_clip"]

    # Get values to build transition render sequence
    # Divide transition lenght between clips, odd frame goes to from_clip 
    real_length = length + 1 # first frame is full from clip frame so we are going to have to drop that
    to_part = real_length / 2
    from_part = real_length - to_part

    # HACKFIX, I just tested this till it worked, not entirely sure on math here
    if to_part == from_part:
        add_thingy = 0
    else:
        add_thingy = 1
    
    if _check_transition_handles((from_part - add_thingy),
                                 transition_data["from_handle"], 
                                 to_part - (1 - add_thingy), 
                                 transition_data["to_handle"]) == False:
        return
    
    # Get from in and out frames
    from_in = from_clip.clip_out - from_part + add_thingy
    from_out = from_in + length # or transition will include one frame too many
    
    # Get to in and out frames
    to_in = to_clip.clip_in - to_part - 1 
    to_out = to_in + length # or transition will include one frame too many

    # Edit clears selection, get track index before selection is cleared
    trans_index = movemodes.selected_range_out
    movemodes.clear_selected_clips()
    transition_type_selection_index = type_combo.get_active() # these corespond with ...
    producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                        from_clip,
                                                                        to_clip,
                                                                        from_out,
                                                                        from_in,
                                                                        to_out,
                                                                        to_in,
                                                                        transition_type_selection_index,
                                                                        sorted_wipe_luma_index,
                                                                        color_str)

    # Save transition data into global variable to be available at render complete callback
    global transition_render_data
    transition_render_data = (trans_index, from_clip, to_clip,  transition_data["track"], from_in, to_out, transition_type_selection_index)
    window_text, type_id = mlttransitions.rendered_transitions[transition_type_selection_index]
    window_text = _("Rendering ") + window_text

    render.render_single_track_transition_clip(producer_tractor,
                                        encoding_option_index,
                                        quality_option_index, 
                                        str(extension_text), 
                                        _transition_render_complete,
                                        window_text)

def _transition_render_complete(clip_path):
    print "render complete"

    global transition_render_data
    transition_index, from_clip, to_clip, track, from_in, to_out, transition_type = transition_render_data

    transition_clip = current_sequence().create_rendered_transition_clip(clip_path, transition_type)
    
    data = {"transition_clip":transition_clip,
            "transition_index":transition_index,
            "from_clip":from_clip,
            "to_clip":to_clip,
            "track":track,
            "from_in":from_in,
            "to_out":to_out}

    action = edit.add_centered_transition_action(data)
    action.do_edit()

def _check_transition_handles(from_req, from_handle, to_req, to_handle):

    if from_req > from_handle:
        info_text = _("There is not enough material available in the FROM clip after the cut") + \
                    _("\nto create the transition.\n\n") + \
                    _("<b>Available:</b> ") + str(from_handle) + _(" frame(s)\n") + \
                    _("<b>Required:</b> ") + str(from_req) + _(" frame(s)")
        dialogutils.info_message(_("FROM Clip Handle is too short!"),
                                 info_text,
                                 gui.editor_window.window)
        return False
    if to_req  > to_handle:
        info_text = _("There is not enough material available in the TO clip before the cut") + \
                    _("\nto create the transition.\n\n") + \
                    _("<b>Available:</b> ") + str(to_handle) + _(" frame(s)\n") + \
                    _("<b>Required:</b> ") + str(to_req) + _(" frame(s)")
        dialogutils.info_message(_("TO Clip Handle is too short!"),
                                 info_text,
                                 gui.editor_window.window)
        return False

    return True

def _do_rendered_fade(track):
    clip = track.clips[movemodes.selected_range_in]

    transition_data = {"track":track,
                       "clip":clip}

    if track.id >= current_sequence().first_video_index:
        dialogs.fade_edit_dialog(_add_fade_dialog_callback, transition_data)
    else:
        _no_audio_tracks_mixing_info()

def _no_audio_tracks_mixing_info():
    primary_txt = _("Only Video Track mix / fades available")
    secondary_txt = _("Unfortunately rendered mixes and fades can currently\nonly be applied on clips on Video Tracks.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

def _add_fade_dialog_callback(dialog, response_id, selection_widgets, transition_data):
    if response_id != gtk.RESPONSE_ACCEPT:
        dialog.destroy()
        return

    # Get input data
    type_combo, length_entry, enc_combo, quality_combo, color_button = selection_widgets
    encoding_option_index = enc_combo.get_active()
    quality_option_index = quality_combo.get_active()
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension
    color_str = color_button.get_color().to_string()

    try:
        length = int(length_entry.get_text())
    except Exception, e:
        # INFOWINDOW, bad input
        print str(e)
        print "entry"
        return

    dialog.destroy()

    if length == 0:
        return

    clip = transition_data["clip"]
    
    if length > clip.clip_length():
        info_text = _("Clip is too short for the requested fade:\n\n") + \
                    _("<b>Clip Length:</b> ") + str(clip.clip_length()) + _(" frame(s)\n") + \
                    _("<b>Fade Length:</b> ") + str(length) + _(" frame(s)\n")
        dialogutils.info_message(_("Clip is too short!"),
                                 info_text,
                                 gui.editor_window.window)
        return

    # Edit clears selection, get track index before selection is cleared
    clip_index = movemodes.selected_range_in
    movemodes.clear_selected_clips()
    transition_type_selection_index = type_combo.get_active() + 3 # +3 because mlttransitions.RENDERED_FADE_IN = 3 and mlttransitions.RENDERED_FADE_OUT = 4
                                                                  # and fade in/out selection indexes are 0 and 1
    producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                        clip,
                                                                        None,
                                                                        length,
                                                                        None,
                                                                        None,
                                                                        None,
                                                                        transition_type_selection_index,
                                                                        None,
                                                                        color_str)
    print "producer_tractor length:" + str(producer_tractor.get_length())

    # Save transition data into global variable to be available at render complete callback
    global transition_render_data
    transition_render_data = (clip_index, transition_type_selection_index, clip, transition_data["track"], length)
    window_text, type_id = mlttransitions.rendered_transitions[transition_type_selection_index]
    window_text = _("Rendering ") + window_text
    render.render_single_track_transition_clip(producer_tractor,
                                        encoding_option_index,
                                        quality_option_index, 
                                        str(extension_text), 
                                        _fade_render_complete,
                                        window_text)

def _fade_render_complete(clip_path):
    print "fade render complete"

    global transition_render_data
    clip_index, fade_type, clip, track, length = transition_render_data

    fade_clip = current_sequence().create_rendered_transition_clip(clip_path, fade_type)
    
    data = {"fade_clip":fade_clip,
            "index":clip_index,
            "track":track,
            "length":length}

    if fade_type == mlttransitions.RENDERED_FADE_IN:
        action = edit.add_rendered_fade_in_action(data)
        action.do_edit()
    else: # mlttransitions.RENDERED_FADE_OUT
        action = edit.add_rendered_fade_out_action(data)
        action.do_edit()
        
# --------------------------------------------------------- view move setting
def view_mode_menu_lauched(launcher, event):
    guicomponents.get_monitor_view_popupmenu(launcher, event, _view_mode_menu_item_item_activated)
    
def _view_mode_menu_item_item_activated(widget, msg):
    editorstate.current_sequence().set_output_mode(msg)
    gui.editor_window.view_mode_select.set_pixbuf(msg)

# ------------------------------------------------------- dialogs    
def no_monitor_clip_info(parent_window):
    primary_txt = _("No Clip loaded into Monitor")
    secondary_txt = _("Can't do the requested edit because there is no Clip in Monitor.")
    dialogutils.info_message(primary_txt, secondary_txt, parent_window)

def monitor_clip_too_short(parent_window):
    primary_txt = _("Defined range in Monitor Clip is too short")
    secondary_txt = _("Can't do the requested edit because Mark In -> Mark Out Range or Clip is too short.")
    dialogutils.info_message(primary_txt, secondary_txt, parent_window)


# ------------------------------------------------- clip to rang log d'n'd
def mouse_dragged_out(event):
    if movemodes.selected_range_in != -1:
        movemodes.clips_drag_out_started(event)

# --------------------------------------------------- copy/paste
def do_timeline_objects_copy():
    if movemodes.selected_track != -1:
        # copying clips
        track = current_sequence().tracks[movemodes.selected_track]
        clone_clips = []
        for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
            clone_clip = current_sequence().clone_track_clip(track, i)
            clone_clips.append(clone_clip)
        editorstate.set_copy_paste_objects(clone_clips)

def do_timeline_objects_paste():
    track = current_sequence().get_first_active_track()
    if track == None:
        return

    paste_objs = editorstate.get_copy_paste_objects()
    if paste_objs == None:
        return

    tline_pos = editorstate.current_tline_frame()

    new_clips = []
    for clip in paste_objs:
        new_clip = current_sequence().create_clone_clip(clip)
        new_clips.append(new_clip)
    editorstate.set_copy_paste_objects(new_clips)

    # Paste clips
    editevent.do_multiple_clip_insert(track, paste_objs, tline_pos)

#------------------------------------------- markers
def marker_menu_lauch_pressed(widget, event):
    guicomponents.get_markers_popup_menu(event, _marker_menu_item_activated)

def _marker_menu_item_activated(widget, msg):
    current_frame = PLAYER().current_frame()
    if msg == "add":
        dialogs.marker_name_dialog(utils.get_tc_string(current_frame), _marker_add_dialog_callback)
    elif msg == "delete":
        mrk_index = -1
        for i in range(0, len(current_sequence().markers)):
            name, frame = current_sequence().markers[i]
            if frame == current_frame:
                mrk_index = i
        if mrk_index != -1:
            current_sequence().markers.pop(mrk_index)
            updater.repaint_tline()
    elif msg == "deleteall":
        current_sequence().markers = []
        updater.repaint_tline()
    else: # seek to marker
        name, frame = current_sequence().markers[int(msg)]
        PLAYER().seek_frame(frame)

def add_marker():
    current_frame = PLAYER().current_frame()
    dialogs.marker_name_dialog(utils.get_tc_string(current_frame), _marker_add_dialog_callback)

def _marker_add_dialog_callback(dialog, response_id, name_entry):
    name = name_entry.get_text()
    dialog.destroy()
    current_frame = PLAYER().current_frame()
    dupl_index = -1
    for i in range(0, len(current_sequence().markers)):
        marker_name, frame = current_sequence().markers[i]
        if frame == current_frame:
            dupl_index = i
    if dupl_index != -1:
        current_sequence().markers.pop(dupl_index)

    current_sequence().markers.append((name, current_frame))
    current_sequence().markers = sorted(current_sequence().markers, key=itemgetter(1))
    updater.repaint_tline()
