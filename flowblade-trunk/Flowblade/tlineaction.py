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
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Module handles button edit events from buttons in the middle bar and other non-tool edits targeting timeline.
"""



from gi.repository import Gtk
from gi.repository import Gdk

import copy
import hashlib
import os
from operator import itemgetter
import threading
import time

import app
import appconsts
import boxmove
import clipeffectseditor
import compositeeditor
import compositormodes
import cutmode
import dialogs
import dialogutils
import glassbuttons
import gui
import guicomponents
import guiutils
import edit
import editevent
import editorpersistance
import editorstate
from editorstate import get_track
from editorstate import current_sequence
from editorstate import PLAYER
from editorstate import PROJECT
from editorstate import timeline_visible
from editorstate import MONITOR_MEDIA_FILE
from editorstate import EDIT_MODE
import movemodes
import multimovemode
import mlttransitions
import projectaction
import render
import renderconsumer
import respaths
import sequence
import syncsplitevent
import updater
import userfolders
import utils


# values for differentiating copy paste data
COPY_PASTE_DATA_CLIPS = appconsts.COPY_PASTE_DATA_CLIPS
CUT_PASTE_DATA_CLIPS = appconsts.CUT_PASTE_DATA_CLIPS
COPY_PASTE_DATA_COMPOSITOR_PROPERTIES = appconsts.COPY_PASTE_DATA_COMPOSITOR_PROPERTIES


# --------------------------- module funcs
def _get_new_clip_from_clip_monitor():
    """
    Creates and returns new clip from current clip monitor clip
    with user set in and out points.
    """
    if MONITOR_MEDIA_FILE() == None:
        # Info window here
        return None
    
    if MONITOR_MEDIA_FILE().type != appconsts.PATTERN_PRODUCER:
        new_clip = current_sequence().create_file_producer_clip(MONITOR_MEDIA_FILE().path, None, False, MONITOR_MEDIA_FILE().ttl)
    else:
        new_clip = current_sequence().create_pattern_producer(MONITOR_MEDIA_FILE())
    
    if MONITOR_MEDIA_FILE().container_data != None:
        new_clip.container_data = copy.deepcopy(MONITOR_MEDIA_FILE().container_data)
        new_clip.container_data.container_data.generate_clip_id()
        
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

    # Disable cut action when it clashes with ongoing edits
    if _can_do_cut() == False:
        return
    
    # Get cut frame
    tline_frame = PLAYER().current_frame()

    movemodes.clear_selected_clips()

    # Iterate tracks and do cut on all active that have non-blanck
    # clips and frame is not on previous edits
    for i in range(1, len(current_sequence().tracks)):
        track = get_track(i)
        if track.active == False:
            continue
        
        if dialogutils.track_lock_check_and_user_info(track): # so the other tracks get cut...
           continue 

        # Get index and clip
        index = track.get_clip_index_at(int(tline_frame))
        try:
            clip = track.clips[index]            
            # don't cut blank clips
            if clip.is_blanck_clip:
                continue
        except Exception:
            continue # Frame is after last clip in track

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

def cut_all_pressed():
    # Disable cut action when it clashes with ongoing edits
    if _can_do_cut() == False:
        return
        
    tline_frame = PLAYER().current_frame()
    movemodes.clear_selected_clips()
    cutmode.cut_all_tracks(tline_frame)
    
def _can_do_cut():
    if EDIT_MODE() == editorstate.ONE_ROLL_TRIM or EDIT_MODE() == editorstate.TWO_ROLL_TRIM or EDIT_MODE() == editorstate.SLIDE_TRIM:
        return False
    if EDIT_MODE() == editorstate.MULTI_MOVE and multimovemode.edit_data != None:
        return False
    if EDIT_MODE() == editorstate.MULTI_MOVE and multimovemode.edit_data != None:
        return False
    if boxmove.box_selection_data != None:
        return False
    
    return True
        
def sequence_split_pressed():
    """
    Intention of this method is to split a sequence at the current position,
    reduce it to the the clips on the left side of the cut and move the remains
    on the right side of the cut to a newly created sequence that is then
    opened.
    """
    # before we start we will ask the user whether he really wants to do, what he
    # just asked for. The intention of this is to provide some more background
    # information
    heading = _("Confirm split to new Sequence at Playhead position")
    info = _("This will create a new sequence from the part after playhead. That part will be removed from\nyour current active sequence.\n\nThe newly created sequence will be opened as current sequence.\n\nUndo stack will also be cleared and this operation cannot be undone.")
    dialogutils.warning_confirmation(split_confirmed, heading, info, gui.editor_window.window)

def split_confirmed(dialog, response_id):
    # so, does the user really want to split the sequence?
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    # first we destroy the dialog and then we carry out our task
    dialog.destroy()

    # we determine the frame position
    tline_frame = PLAYER().current_frame()

    # We start with actually cutting the sequence
    # actually this poses performance loss, as we do the track loop twice
    # one in cut_pressed and one in this method
    # also other operations are repeated
    cutmode.cut_all_tracks(tline_frame)

    # prepare a data structure that will receive our clips we want to move to
    # another sequence plus all the information to actually put them at the same
    # relative position
    clips_to_move = []

    # we collect the compositors that need to be moved
    if current_sequence().compositing_mode != appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
        compositors_to_move = _collect_compositors_for_split(tline_frame)

    # now we iterate over all tracks and collect the ones that provide content
    # after the cut position
    for i in range(1, len(current_sequence().tracks) - 1):
        track = get_track(i)

        # Get index and clip - so basically this means, all clips in this
        # track with this index and above are left of the cut position,
        # so we gather required information for our new sequence
        index = track.get_clip_index_at(int(tline_frame))

        # we need to check whether the first clip at cut is a blank clip
        blank_length = 0
        if index < len(track.clips):
            first_clip = track.clips[index]
            if first_clip.is_blanck_clip == True:
                # yes, it is a blank clip, therefore we need to modify its length
                # but only if the clip_start lies before the current frame
                clip_start = track.clip_start(index)
                if tline_frame > clip_start:
                    blank_length = first_clip.clip_out - (tline_frame - clip_start) + 1
                else:
                    blank_length = first_clip.clip_out - clip_start + 1

        for j in range(index, len(track.clips)):
            clip = track.clips[j]
            data = {
                "track_index": i,
                "clip": clip,
                "clip_in": clip.clip_in,
                "clip_out": clip.clip_out,
                "blank_length": blank_length
            }

            clips_to_move.append(data)
            # okay, we processed this clip, go on to the next one

    # so we collected all the data for this sequence, now we need to remove
    # all the clips right hand of the current position
    data = {
        "tracks":current_sequence().tracks,
        "mark_in_frame":tline_frame,
        "mark_out_frame":PLAYER().get_active_length()
    }

    action = edit.range_delete_action(data)
    action.do_edit()

    # so we collected all the data for all tracks
    # now we create a new sequence and will open that very sequence
    name = _("sequence_") + str(PROJECT().next_seq_number)
    sequence.VIDEO_TRACKS_COUNT, sequence.AUDIO_TRACKS_COUNT = current_sequence().get_track_counts()
    PROJECT().add_named_sequence(name)
    app.change_current_sequence(len(PROJECT().sequences) - 1)
    # New sequence needs to have same compositing mode as current.
    projectaction.do_compositing_mode_change(current_sequence().compositing_mode)

    # and now, we nee to iterate over the collected clips and add them to
    # our newly created sequence
    for i in range(0, len(clips_to_move)):
        collected = clips_to_move[i]
        track_index = collected["track_index"]

        # determine the track we need to put the clip in
        clip = collected["clip"]
        if clip.is_blanck_clip == True:
            length = collected["blank_length"]
            if length == 0:
                length = clip.clip_length()
            current_sequence().append_blank(length, get_track(track_index))
            continue

        #prepare the date and append it to the sequence
        data = {
            "track": get_track(track_index),
            "clip": collected["clip"],
            "clip_in": collected["clip_in"],
            "clip_out": collected["clip_out"]
        }

        action = edit.append_action(data)
        action.do_edit()
    
    # also, we need to add the compositors from our collection.
    if current_sequence().compositing_mode != appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
        _add_compositors_to_split(compositors_to_move)

    # update time line to show whole range of new sequence
    updater.zoom_project_length()

def _collect_compositors_for_split(playhead):
    # there are basically three cases we need to take into consideration
    # when dealing with compositors.
    # first: the compositor lies completely before the playhead position
    # we do not have to deal with those and leave them untouched
    # compositor.clip_out < playhead position
    # second: the compositor lies completely behind the playhead position
    # the compositor needs to be removed from the split sequence and needs to
    # be moved to the newly created one. we need to create a duplicate and modify
    # its clip_in and clip_out properties. basically this formula should apply:
    # new_compositor.clip_in = old_compositor.clip_in - playhead position (same
    # for clip_out)
    # third: the playhead position is on a compositor. In this case we need to
    # split the compositor in two, move one part to the new sequence and leave
    # the first part in the old one. This can probably be done by simply
    # modifying the clip_out property of the old compositor.
    # the new compositor will have clip_in == 0 and
    # clip_out = oc.clip_out - playhead position.

    # result structure
    new_compositors = []
    compositors_to_remove = []

    #  we start with analyzing and collecting the compositors
    old_compositors = current_sequence().get_compositors()
    for index in range(0, len(old_compositors)):
        old_compositor = old_compositors[index]
        if old_compositor.clip_out < playhead:
            continue
        
        new_compositor = current_sequence().create_compositor(old_compositor.type_id)
        new_compositor.clone_properties(old_compositor)
        if old_compositor.clip_in < playhead:
            new_compositor.set_in_and_out(0, old_compositor.clip_out - playhead)
            old_compositor.set_in_and_out(old_compositor.clip_in, playhead)
        else:
            new_compositor.set_in_and_out(old_compositor.clip_in - playhead, old_compositor.clip_out - playhead)
            compositors_to_remove.append(old_compositor)

        new_compositor.transition.set_tracks(old_compositor.transition.a_track, old_compositor.transition.b_track)
        new_compositor.obey_autofollow = old_compositor.obey_autofollow
        new_compositors.append(new_compositor)
    
    # done with collecting all new necessary compositors
    # now we remove the compositors that are completely after playhead positions
    # cut compositors have already been reduces in length
    for index in range(0, len(compositors_to_remove)):
        old_compositor = compositors_to_remove[index]
        old_compositor.selected = False
        data = {"compositor":old_compositor}
        action = edit.delete_compositor_action(data)
        action.do_edit()
    
    return new_compositors

def _add_compositors_to_split(new_compositors):
    # now we basically just need to add the compositors in the list to the
    # right track
    for index in range(0, len(new_compositors)):
        new_compositor = new_compositors[index]
        current_sequence()._plant_compositor(new_compositor)
        current_sequence().compositors.append(new_compositor)
    current_sequence().restack_compositors()

def splice_out_button_pressed():
    """
    Removes 1 - n long continuous clip range from track and closes
    the created gap.
    """
    if movemodes.selected_track == -1:
        return

    # Edit consumes selection, so clear selected state from clips
    movemodes.set_range_selection(movemodes.selected_track,
                                  movemodes.selected_range_in,
                                  movemodes.selected_range_out,
                                  False)
    
    track = get_track(movemodes.selected_track)

    if dialogutils.track_lock_check_and_user_info(track):
        movemodes.clear_selection_values()
        return

    # A single clip delete can trigger a special clip cover delete
    # See if such delete should be attempted.
    # Exit if done successfully, do normal splice out and report if failed
    cover_delete_failed = False
    if editorpersistance.prefs.trans_cover_delete == True:
        if movemodes.selected_range_out == movemodes.selected_range_in:
            clip = track.clips[movemodes.selected_range_in]
            if hasattr(clip, "rendered_type") and (track.id >= current_sequence().first_video_index):
                cover_delete_success =  _attempt_clip_cover_delete(clip, track, movemodes.selected_range_in)
                if cover_delete_success:
                    return # A successful cover delete happened
                else:
                    cover_delete_failed = True # A cover delete failed, do normal delete and gove info

    # Do delete
    data = {"track":track,
            "from_index":movemodes.selected_range_in,
            "to_index":movemodes.selected_range_out}
    edit_action = edit.remove_multiple_action(data)
    edit_action.do_edit()

    _splice_out_done_update()
    
    if cover_delete_failed == True:
        dialogutils.info_message(_("Fade/Transition cover delete failed!"),
         _("There wasn't enough material available in adjacent clips.\nA normal Splice Out was done instead."),
         gui.editor_window.window)

def _attempt_clip_cover_delete(clip, track, index):
    if clip.rendered_type == appconsts.RENDERED_FADE_OUT:
        if index != 0:
            cover_clip = track.clips[movemodes.selected_range_in - 1]
            if clip.get_length() < (cover_clip.get_length() - cover_clip.clip_out + 1):
                # Do delete
                data = {"track":track,
                        "clip":clip,
                        "index":movemodes.selected_range_in}
                edit_action = edit.cover_delete_fade_out(data)
                edit_action.do_edit()
                _splice_out_done_update()
                return True
        return False
        
    elif clip.rendered_type == appconsts.RENDERED_FADE_IN:
        if index != len(track.clips) - 1:
            cover_clip = track.clips[movemodes.selected_range_in + 1]
            if clip.get_length() <= cover_clip.clip_in + 1:
                # Do delete
                data = {"track":track,
                        "clip":clip,
                        "index":movemodes.selected_range_in}
                edit_action = edit.cover_delete_fade_in(data)
                edit_action.do_edit()
                _splice_out_done_update()
                return True
        return False
        
    else:# RENDERED_DISSOLVE, RENDERED_WIPE, RENDERED_COLOR_DIP
        if index == 0:
            return False
        if index == len(track.clips) - 1:
            return False
        cover_form_clip = track.clips[movemodes.selected_range_in - 1]
        cover_to_clip = track.clips[movemodes.selected_range_in + 1]
        
        real_length = clip.get_length() # this the mlt finction giving media length, not length on timeline

        to_part = real_length // 2
        from_part = real_length - to_part

        # Fix lengths to match what existed before adding rendered transition
        clip_marks_length = clip.clip_out - clip.clip_in
        if clip_marks_length % 2 == 1:
            to_part += -1
        else:
            from_part += 1
            to_part += -1

        if to_part > cover_to_clip.clip_in:
            return False
        if from_part > cover_form_clip.get_length() - cover_form_clip.clip_out - 1:# -1, clip_out inclusive
            return False
            
        # Do delete
        data = {"track":track,
                "clip":clip,
                "index":movemodes.selected_range_in,
                "to_part": to_part,
                "from_part":from_part}
        edit_action = edit.cover_delete_transition(data)
        edit_action.do_edit()
        return True
  
    return False

def _splice_out_done_update():
    # Nothing is selected after edit
    movemodes.clear_selection_values()
    updater.repaint_tline()

def lift_button_pressed():
    """
    Removes 1 - n long continuous clip range from track and fills
    the created gap with a blank clip
    """
    if movemodes.selected_track == -1:
        return

    # Edit consumes selection, set clips selection attr to False
    movemodes.set_range_selection(movemodes.selected_track, 
                                  movemodes.selected_range_in,
                                  movemodes.selected_range_out, 
                                  False)
                         
    track = get_track(movemodes.selected_track)

    if dialogutils.track_lock_check_and_user_info(track):
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

def ripple_delete_button_pressed():
    if movemodes.selected_track == -1:
        return

    track = get_track(movemodes.selected_track)
    
    delete_range_in = track.clip_start(movemodes.selected_range_in)
    out_clip = track.clips[movemodes.selected_range_out]
    delete_range_out = track.clip_start(movemodes.selected_range_out) + out_clip.clip_out - out_clip.clip_in + 1 # +1 out incl
    delete_range_length = delete_range_out - delete_range_in
    
    ripple_data = multimovemode.MultimoveData(track, delete_range_out, True, False)
    ripple_data.build_ripple_data(track.id, delete_range_length, movemodes.selected_range_in)
    available_from_range_out = ripple_data.max_backwards

    ripple_data = multimovemode.MultimoveData(track, delete_range_in, True, False)
    ripple_data.build_ripple_data(track.id, delete_range_length, movemodes.selected_range_in)
    available_from_range_in = ripple_data.max_backwards

    if available_from_range_in < delete_range_length or available_from_range_out < delete_range_length:
        overwrite_track = ripple_data.get_overwrite_data(delete_range_length)
        primary_txt = _("Can't do Ripple Delete!")
        secondary_txt = _("Selected Ripple Delete would cause an overwrite and that is not permitted for this edit action.\n\nOverwrite would happen on at track <b>") + utils.get_track_name(overwrite_track, current_sequence()) + "</b>."
        parent_window = gui.editor_window.window
        dialogutils.info_message(primary_txt, secondary_txt, parent_window)
        return 

    # Do ripple delete
    data = {"track":track,
            "from_index":movemodes.selected_range_in,
            "to_index":movemodes.selected_range_out,
            "multi_data":ripple_data,
            "edit_delta":-delete_range_length}
    edit_action = edit.ripple_delete_action(data)
    edit_action.do_edit()
    
    _splice_out_done_update()
    
def insert_button_pressed():
    track = current_sequence().get_first_active_track()

    if dialogutils.track_lock_check_and_user_info(track):
        return

    tline_pos =_current_tline_frame()
    
    new_clip = _get_new_clip_from_clip_monitor()
    if new_clip == None:
        no_monitor_clip_info(gui.editor_window.window)
        return

    updater.save_monitor_frame = False # hack to not get wrong value saved in MediaFile.current_frame
    editevent.do_clip_insert(track, new_clip, tline_pos)

    editevent.maybe_autorender_plugin(new_clip)
    
def append_button_pressed():
    track = current_sequence().get_first_active_track()

    if dialogutils.track_lock_check_and_user_info(track):
        return

    tline_pos = track.get_length()
    
    new_clip = _get_new_clip_from_clip_monitor()
    if new_clip == None:
        no_monitor_clip_info(gui.editor_window.window)
        return

    updater.save_monitor_frame = False # hack to not get wrong value saved in MediaFile.current_frame
    editevent.do_clip_insert(track, new_clip, tline_pos)

    editevent.maybe_autorender_plugin(new_clip)
    
def three_point_overwrite_pressed():
    # Check that state is good for edit
    if movemodes.selected_track == -1:
        primary_txt = _("No Clips are selected!")
        secondary_txt = _("You need to select clips to overwrite to perform this edit.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    # Get data
    track = get_track(movemodes.selected_track)
    if dialogutils.track_lock_check_and_user_info(track):
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

    if not editorstate.timeline_visible():
        updater.display_sequence_in_monitor()
    
    updater.display_tline_cut_frame(track, range_in)

    editevent.maybe_autorender_plugin(over_clip)
    
def range_overwrite_pressed():
    # Get data
    track = current_sequence().get_first_active_track()
    if dialogutils.track_lock_check_and_user_info(track):
        return

    # Get over clip and check it overwrite range area
    over_clip = _get_new_clip_from_clip_monitor()
    if over_clip == None:
        no_monitor_clip_info(gui.editor_window.window)
        return

    # tractor is has mark in and mark
    mark_in_frame = current_sequence().tractor.mark_in
    mark_out_frame = current_sequence().tractor.mark_out
    
    # Case timeline marked
    if mark_in_frame != -1 and mark_out_frame != -1:
        range_length = mark_out_frame - mark_in_frame + 1 # end is incl.
        if over_clip.mark_in == -1:
            # This actually should never be hit because mark in and mark out seem to first and last frame if nothing set
            show_three_point_edit_not_defined()
            return

        over_length = over_clip.mark_out - over_clip.mark_in + 1 # + 1 out incl
        if over_length < range_length:
            monitor_clip_too_short(gui.editor_window.window)
            return

        over_clip_out = over_clip.mark_in + range_length - 1
        
    # Case clip marked
    elif over_clip.mark_out != -1 and over_clip.mark_in != -1:
        range_length = over_clip.mark_out - over_clip.mark_in + 1 # end is incl.

        over_clip_out = over_clip.mark_out
        if mark_out_frame == -1:
            # Mark in defined
            mark_out_frame = mark_in_frame + range_length - 1 # -1 because it gets read later
        else:
            # Mark out defined
            mark_in_frame = mark_out_frame - range_length + 1
            if mark_in_frame < 0:
                clip_shortning = -mark_in_frame
                mark_in_frame = 0
                over_clip.mark_in = over_clip.mark_in + clip_shortning # moving overclip in forward because in needs to hit timeline frame 0
    # case neither clip or timeline has both in and out points
    else:
        show_three_point_edit_not_defined()
        return
        
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

    editevent.maybe_autorender_plugin(over_clip)

def _show_three_poimt_edit_not_defined():
    primary_txt = _("3 point edit not defined!")
    secondary_txt = _("You need to set Timeline Range using Mark In and Mark Out buttons\nto perform this edit.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
            
def delete_range_button_pressed():
    # Get data
    #track = current_sequence().get_first_active_track()
    #if editevent.track_lock_check_and_user_info(track, range_overwrite_pressed, "range overwrite"):
    #    return
    tracks = []
    for i in range(1, len(current_sequence().tracks) - 1):
        track = current_sequence().tracks[i]
        if track.edit_freedom != appconsts.LOCKED:
            tracks.append(track)

    if len(tracks) == 0:
        # all tracks are locked!
        return
            
    # tractor is has mark in and mark
    mark_in_frame = current_sequence().tractor.mark_in
    mark_out_frame = current_sequence().tractor.mark_out

    if mark_in_frame == -1 or mark_out_frame == -1:
        primary_txt = _("Timeline Range not set!")
        secondary_txt = _("You need to set Timeline Range using Mark In and Mark Out buttons\nto perform this edit.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    movemodes.clear_selected_clips() # edit consumes selection

    updater.save_monitor_frame = False # hack to not get wrong value saved in MediaFile.current_frame

    data = {"tracks":tracks,
            "mark_in_frame":mark_in_frame,
            "mark_out_frame":mark_out_frame + 1} # +1 because mark is displayed and end of frame end this 
                                                 # confirms to user expectation of
                                                 # of how this should work
    action = edit.range_delete_action(data)
    action.do_edit()

    PLAYER().seek_frame(mark_in_frame)

def trim_start_pressed():
    clip, track, index = _get_kb_quick_trim_target_clip()
    if clip == None:
        return

    current_frame = PLAYER().current_frame()
    clip_start_in_tline = track.clip_start(index)
    delta = current_frame - clip_start_in_tline

    data = {"track":track,
            "clip":clip,
            "index":index,
            "delta":delta,
            "undo_done_callback":None, # we're not doing the callback because we are not in trim tool that needs it
            "first_do":False}
                            
    action = edit.trim_start_action(data)
    action.do_edit()

def trim_end_pressed():
    clip, track, index = _get_kb_quick_trim_target_clip()
    if clip == None:
        return

    current_frame = PLAYER().current_frame()
    clip_end_in_tline = track.clip_start(index) + clip.clip_out - clip.clip_in
    delta = current_frame - clip_end_in_tline

    data = {"track":track,
            "clip":clip,
            "index":index,
            "delta":delta,
            "undo_done_callback":None, # we're not doing the callback because we are not in trim tool that needs it
            "first_do":False}
                            
    action = edit.trim_end_action(data)
    action.do_edit()
    
def _get_kb_quick_trim_target_clip():
    current_frame = PLAYER().current_frame()
    if movemodes.selected_track != -1:
        track = current_sequence().tracks[movemodes.selected_track]
        clip_index = track.get_clip_index_at(current_frame)
        if clip_index >= movemodes.selected_range_in and clip_index >= movemodes.selected_range_out:
            return (track.clips[clip_index], track, clip_index)

    track = current_sequence().get_first_active_track()
    if track == None:
        return (None, None, None) # we have no way of determining which track is targeted.
    try:
        clip_index = track.get_clip_index_at(current_frame)
        clip = track.clips[clip_index]
        return (clip, track, clip_index)
    except:
        return (None, None, None)

def resync_button_pressed():
    if movemodes.selected_track != -1:
        syncsplitevent.resync_clip_from_button()
    else:
        if compositormodes.compositor != None:
            sync_compositor(compositormodes.compositor)

def resync_track_button_pressed():
    syncsplitevent.resync_track()

def sync_compositor(compositor):
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
        
def split_audio_button_pressed():
    if movemodes.selected_track == -1:
        return
    
    track = current_sequence().tracks[movemodes.selected_track]
    clips = []
    for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        
        clip = track.clips[i]
        if clip.is_blanck_clip == False:
            clips.append(clip)

    syncsplitevent.split_audio_from_clips_list(clips, track)

def split_audio_synched_button_pressed():
    if movemodes.selected_track == -1:
        return
    
    track = current_sequence().tracks[movemodes.selected_track]
    clips = []
    for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        
        clip = track.clips[i]
        if clip.is_blanck_clip == False:
            clips.append(clip)

    syncsplitevent.split_audio_synched_from_clips_list(clips, track)
    
def sync_all_compositors():
    full_sync_data, orphaned_compositors = edit.get_full_compositor_sync_data()
    
    for sync_item in full_sync_data:
        destroy_id, orig_in, orig_out, clip_start, clip_end, clip_track, orig_compositor_track = sync_item
        compositor = current_sequence().get_compositor_for_destroy_id(destroy_id)
        data = {"compositor":compositor,"clip_in":clip_start,"clip_out":clip_end}
        action = edit.move_compositor_action(data)
        action.do_edit()


# --------------------------------------------------------- view move setting
def view_mode_menu_lauched(launcher, event):
    guicomponents.get_monitor_view_popupmenu(launcher, event, _view_mode_menu_item_item_activated)
    
def _view_mode_menu_item_item_activated(widget, msg):
    if msg < 3:
        editorstate.current_sequence().set_output_mode(msg)
        gui.editor_window.view_mode_select.set_pixbuf(msg)
    else:
        mix_value_index = msg - 3 ## this just done in a bit hackish way, 
        # see guicomponents.get_monitor_view_popupmenu and sequence.SCOPE_MIX_VALUES
        editorstate.current_sequence().set_scope_overlay_mix(mix_value_index)


# ------------------------------------------------------- dialogs    
def no_monitor_clip_info(parent_window):
    primary_txt = _("No Clip loaded into Monitor")
    secondary_txt = _("Can't do the requested edit because there is no Clip in Monitor.")
    dialogutils.info_message(primary_txt, secondary_txt, parent_window)

def monitor_clip_too_short(parent_window):
    primary_txt = _("Defined range in Monitor Clip is too short")
    secondary_txt = _("Can't do the requested edit because Mark In -> Mark Out Range or Clip is too short.")
    dialogutils.info_message(primary_txt, secondary_txt, parent_window)

def show_three_point_edit_not_defined():
    primary_txt = _("3 point edit not defined!")
    secondary_txt = _("You need to set Mark In and Mark Out on Timeline or Clip and\nadditional Mark In on Timeline or Clip to perform this edit.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
            

# ------------------------------------------------- clip to range log d'n'd
def mouse_dragged_out(event):
    if movemodes.selected_range_in != -1:
        movemodes.clips_drag_out_started(event)

# --------------------------------------------------- copy/paste
def do_timeline_objects_copy(is_copy=True):
    if compositormodes.compositor != None and compositormodes.compositor.selected == True:
        editorstate.set_copy_paste_objects((COPY_PASTE_DATA_COMPOSITOR_PROPERTIES, compositormodes.compositor.get_copy_paste_data()))
        return
        
    if movemodes.selected_track != -1:
        # copying clips
        track = current_sequence().tracks[movemodes.selected_track]
        clone_clips = []
        for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
            clone_clip = current_sequence().clone_track_clip(track, i)
            clone_clips.append(clone_clip)
            source_clip = track.clips[i]
            for j in range(0, len(clone_clip.filters)):
                clone_clip.filters[j].active = source_clip.filters[j].active
        if is_copy:
            editorstate.set_copy_paste_objects((COPY_PASTE_DATA_CLIPS, clone_clips))
        else:
            data = {"track":track,
                    "from_index":movemodes.selected_range_in,
                    "to_index":movemodes.selected_range_out}
            edit_action = edit.lift_multiple_action(data)
            edit_action.do_edit()

            editorstate.set_copy_paste_objects((CUT_PASTE_DATA_CLIPS, clone_clips))

def do_timeline_objects_paste():
    track = current_sequence().get_first_active_track()
    if track == None:
        return 
    paste_objs = editorstate.get_copy_paste_objects()
    if paste_objs == None:
        return 
    
    data_type, paste_clips = paste_objs
    if data_type != COPY_PASTE_DATA_CLIPS and data_type != CUT_PASTE_DATA_CLIPS:
        do_compositor_data_paste(paste_objs)
        return

    tline_pos = editorstate.current_tline_frame()

    if data_type == COPY_PASTE_DATA_CLIPS:
        # So that multiple copies with CTRL+V can be made
        new_clips = []
        for clip in paste_clips:
            if isinstance(clip, int): # blanks, these represented as int's.
                new_clip = clip 
            else: # media clips
                new_clip = current_sequence().create_clone_clip(clip)
            new_clips.append(new_clip)
        editorstate.set_copy_paste_objects((COPY_PASTE_DATA_CLIPS, new_clips))

        # Paste clips
        editevent.do_multiple_clip_insert(track, paste_clips, tline_pos)
    else:
        # Paste clips
        editevent.do_multiple_clip_insert(track, paste_clips, tline_pos)
        editorstate.clear_copy_paste_objects() # Cut/paste only happens once

def do_timeline_filters_paste():
    if _timeline_has_focus() == False:
        return 
        
    track = current_sequence().get_first_active_track()
    if track == None:
        return 

    paste_objs = editorstate.get_copy_paste_objects()
    if paste_objs == None:
        return 

    data_type, paste_clips = paste_objs
    if data_type != COPY_PASTE_DATA_CLIPS:
        do_compositor_data_paste(paste_objs)
        return
        
    if movemodes.selected_track == -1:
        return

    # First clip of selection is used as filters source
    source_clip = paste_clips[0]

    # Currently selected clips are target clips
    target_clips = []
    track = current_sequence().tracks[movemodes.selected_track]
    for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        target_clips.append(track.clips[i])
    
    actions = []    
    for target_clip in target_clips:
        data = {"clip":target_clip,"clone_source_clip":source_clip}
        action = edit.paste_filters_action(data)
        actions.append(action)

    c_action = edit.ConsolidatedEditAction(actions)
    c_action.do_consolidated_edit()

def do_compositor_data_paste(paste_objs):
    data_type, paste_data = paste_objs
    if data_type != COPY_PASTE_DATA_COMPOSITOR_PROPERTIES:
        print("supposedly unreachable if in do_compositor_data_paste")
        return
        
    if compositormodes.compositor != None and compositormodes.compositor.selected == True:
        compositormodes.compositor.do_values_copy_paste(paste_data)
        compositeeditor.set_compositor(compositormodes.compositor)
        return

def _timeline_has_focus(): # copied from keyevents.by. maybe put in utils?
    if(gui.tline_canvas.widget.is_focus()
       or gui.tline_column.widget.is_focus()
       or gui.editor_window.tool_selector.widget.is_focus()
       or (gui.pos_bar.widget.is_focus() and timeline_visible())
       or gui.tline_scale.widget.is_focus()
       or glassbuttons.focus_group_has_focus(glassbuttons.DEFAULT_FOCUS_GROUP)):
        return True

    return False

#------------------------------------------- markers
def marker_menu_lauch_pressed(widget, event):
    guicomponents.get_markers_popup_menu(event, _marker_menu_item_activated)

def _marker_menu_item_activated(widget, msg):
    current_frame = PLAYER().current_frame()
    mrk_index = -1
    for i in range(0, len(current_sequence().markers)):
        name, frame = current_sequence().markers[i]
        if frame == current_frame:
            mrk_index = i
            
    if msg == "add":
        dialogs.marker_name_dialog(utils.get_tc_string(current_frame), _marker_add_dialog_callback)
    elif msg == "delete":
        if mrk_index != -1:
            current_sequence().markers.pop(mrk_index)
            updater.repaint_tline()
    elif msg == "deleteall":
        current_sequence().markers = []
        updater.repaint_tline()
    elif msg == "rename":
        if mrk_index != -1:
            current_sequence().markers.pop(mrk_index)
            dialogs.marker_name_dialog(utils.get_tc_string(current_frame), _marker_add_dialog_callback, True)
    else: # seek to marker
        name, frame = current_sequence().markers[int(msg)]
        PLAYER().seek_frame(frame)

def add_marker():
    current_frame = PLAYER().current_frame()
    if PLAYER().is_stopped() == False:
        _do_add_marker(_("Playback Marker"), current_frame)
    else:
        dialogs.marker_name_dialog(utils.get_tc_string(current_frame), _marker_add_dialog_callback)

def _marker_add_dialog_callback(dialog, response_id, name_entry):
    name = name_entry.get_text()
    dialog.destroy()
    if response_id != Gtk.ResponseType.ACCEPT:
        return
    current_frame = PLAYER().current_frame()
    _do_add_marker(name, current_frame)

def _do_add_marker(name, current_frame):
    dupl_index = -1
    for i in range(0, len(current_sequence().markers)):
        marker_name, frame = current_sequence().markers[i]
        if frame == current_frame:
            dupl_index = i
    if dupl_index != -1:
        current_sequence().markers.pop(dupl_index)

    current_sequence().markers.append((name, current_frame))
    current_sequence().markers = sorted(current_sequence().markers, key=itemgetter(1))

    updater.update_position_bar()
    updater.repaint_tline()
    

# ---------------------------------------- timeline edits
def all_filters_off():
    current_sequence().set_all_filters_active_state(False)
    clipeffectseditor.update_stack_view()

def all_filters_on():
    current_sequence().set_all_filters_active_state(True)
    clipeffectseditor.update_stack_view()

def set_track_small_height(track_index):
    track = get_track(track_index)
    track.height = appconsts.TRACK_HEIGHT_SMALL
    if editorstate.SCREEN_HEIGHT < 863:
        track.height = appconsts.TRACK_HEIGHT_SMALLEST



