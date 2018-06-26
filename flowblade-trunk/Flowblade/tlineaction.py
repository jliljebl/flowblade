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



from gi.repository import Gtk
from gi.repository import Gdk

import md5
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
import render
import renderconsumer
import respaths
import sequence
import syncsplitevent
import updater
import utils


# values for differentiating copy paste data
COPY_PASTA_DATA_CLIPS = 1
COPY_PASTA_DATA_COMPOSITOR_PROPERTIES = 2

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
        return None
    
    if MONITOR_MEDIA_FILE().type != appconsts.PATTERN_PRODUCER:
        new_clip = current_sequence().create_file_producer_clip(MONITOR_MEDIA_FILE().path, None, False, MONITOR_MEDIA_FILE().ttl)
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

    # Disable whencut action when it cut clash with ongoing edits
    if EDIT_MODE() == editorstate.ONE_ROLL_TRIM or EDIT_MODE() == editorstate.TWO_ROLL_TRIM or EDIT_MODE() == editorstate.SLIDE_TRIM:
        return

    if EDIT_MODE() == editorstate.MULTI_MOVE and multimovemode.edit_data != None:
        return

    if EDIT_MODE() == editorstate.MULTI_MOVE and multimovemode.edit_data != None:
        return
        
    if boxmove.box_selection_data != None:
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
    heading = _("Split to new Sequence at Playhead Position")
    info = _("Do you realy want to split this sequence into two?\nThis will create a new sequence receiving righthand content of your currently active sequence. Also the same content will be removed from your currently active sequence.\nThe newly created sequence will be opened.\n\n Continue?")
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
    compositors_to_move = _collect_compositors_for_split(tline_frame)

    # now we iterate over all tracks and collect the ones that provide content
    # after the cut position
    for i in range(1, len(current_sequence().tracks)):
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

    # and now, we nee to iterate over the collected clips and add them to
    # our newly created sequence
    for i in range(0, len(clips_to_move) - 1):
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
    
    # also, we need to add the compositors from our collection
    _add_compositors_to_split(compositors_to_move)
    
    # update time line to show whole range of new sequence
    updater.zoom_project_length()

def _collect_compositors_for_split(playhead):
    # there are basically three cases we need to take into consideration
    # when dealing with compositors.
    # first: the compositor lies completely before the playhead position
    # we do not have to deal with those and leave them untouched
    # compositor.clip_out < playhead position
    # second: the compositor lies completly behind the playhead position
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
    # now we remove the compositors that are completly after playhead positions
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

    # Edit consumes selection, so clear selected from clips
    movemodes.set_range_selection(movemodes.selected_track,
                                  movemodes.selected_range_in,
                                  movemodes.selected_range_out,
                                  False)
    
    track = get_track(movemodes.selected_track)

    if editevent.track_lock_check_and_user_info(track, splice_out_button_pressed, "splice out"):
        movemodes.clear_selection_values()
        return

    # A single clip delete can trigger a special clip cover delete
    # See if such delete should be attempted.
    # Exit if done succesfully, do normal splice out and report if failed
    cover_delete_failed = False
    if editorpersistance.prefs.trans_cover_delete == True:
        if movemodes.selected_range_out == movemodes.selected_range_in:
            clip = track.clips[movemodes.selected_range_in]
            if hasattr(clip, "rendered_type") and (track.id >= current_sequence().first_video_index):
                cover_delete_success =  _attempt_clip_cover_delete(clip, track, movemodes.selected_range_in)
                if cover_delete_success:
                    return # A successful cover delete happened
                else:
                    cover_delete_failed = True # A successful cover delete failed, do normal delete and gove info

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
        
        real_length = clip.get_length()
        to_part = real_length / 2
        from_part = real_length - to_part
    
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

    # Edit consumes selection, set clips seletion attr to False
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


def ripple_delete_button_pressed():
    print "Ripple delete"

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

    if not editorstate.timeline_visible():
        updater.display_sequence_in_monitor()
    
    updater.display_tline_cut_frame(track, range_in)

def range_overwrite_pressed():
    # Get data
    track = current_sequence().get_first_active_track()
    if editevent.track_lock_check_and_user_info(track, range_overwrite_pressed, "range overwrite"):
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
            # This actually never hit because mark in and mark out seem to first and last frame if nothing set
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
        
        if mark_in_frame == -1:
            show_three_point_edit_not_defined()
            return

        over_length = track.get_length() - mark_in_frame + 1 # + 1 out incl
        if over_length < range_length:
            monitor_clip_too_short(gui.editor_window.window)
            return
            
        over_clip_out = over_clip.mark_out
        mark_out_frame = mark_in_frame + range_length - 1 # -1 because it gets readded later
        
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
    range_length = mark_out_frame - mark_in_frame + 1 # end is incl.
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
    
def resync_button_pressed():
    if movemodes.selected_track != -1:
        syncsplitevent.resync_selected()
    else:
        if compositormodes.compositor != None:
            sync_compositor(compositormodes.compositor)

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
    
    # Auto fades need to go to start or end of clips and maintain their lengths
    if compositor.transition.info.auto_fade_compositor == True:
        if compositor.transition.info.name == "##auto_fade_in":
            clip_end = clip_start + compositor.get_length() - 1
        else:
            clip_start = clip_end - compositor.get_length() + 1
            
    data = {"compositor":compositor,"clip_in":clip_start,"clip_out":clip_end}
    action = edit.move_compositor_action(data)
    action.do_edit()
        
def set_compositors_fades_defaults():
    dialogs.set_fades_defaults_dialog(_compositors_fades_defaults_callback)

def _compositors_fades_defaults_callback(dialog, response_id, widgets):
    group_select, fade_in_check, fade_in_spin, fade_out_check, fade_out_spin, fade_in_length_label, fade_out_length_label = widgets
    
    group = group_select.get_active()
    fade_in_on = fade_in_check.get_active()
    fade_in_length = int(fade_in_spin.get_value())
    fade_out_on = fade_out_check.get_active()
    fade_out_length = int(fade_out_spin.get_value())

    dialog.destroy()
    
    if group == 0:
        fade_in_key = appconsts.P_PROP_DISSOLVE_GROUP_FADE_IN
        fade_out_key = appconsts.P_PROP_DISSOLVE_GROUP_FADE_OUT
    else:
        fade_in_key = appconsts.P_PROP_ANIM_GROUP_FADE_IN
        fade_out_key = appconsts.P_PROP_ANIM_GROUP_FADE_OUT

    if fade_in_on == False or fade_in_length == 0:
        PROJECT().set_project_property(fade_in_key, -1)
    else:
        PROJECT().set_project_property(fade_in_key, fade_in_length)
        
    if fade_out_on == False or fade_out_length == 0:
        PROJECT().set_project_property(fade_out_key, -1)
    else:
        PROJECT().set_project_property(fade_out_key, fade_out_length)


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

def sync_all_compositors():
    full_sync_data = edit.get_full_compositor_sync_data()
    
    for sync_item in full_sync_data:
        destroy_id, orig_in, orig_out, clip_start, clip_end = sync_item
        compositor = current_sequence().get_compositor_for_destroy_id(destroy_id)
        data = {"compositor":compositor,"clip_in":clip_start,"clip_out":clip_end}
        action = edit.move_compositor_action(data)
        action.do_edit()

    """
    # Pair all compositors with their origin clips ids
    comp_clip_pairings = {}
    for compositor in current_sequence().compositors:
        if compositor.origin_clip_id in comp_clip_pairings:
            comp_clip_pairings[compositor.origin_clip_id].append(compositor)
        else:
            comp_clip_pairings[compositor.origin_clip_id] = [compositor]
    
    # Create resync list
    resync_list = []
    for i in range(current_sequence().first_video_index, len(current_sequence().tracks) - 1): # -1, there is a topmost hidden track 
        track = current_sequence().tracks[i] # b_track is source track where origin clip is
        for j in range(0, len(track.clips)):
            clip = track.clips[j]
            if clip.id in comp_clip_pairings:
                compositor_list = comp_clip_pairings[clip.id]
                for compositor in compositor_list:
                    resync_list.append((clip, track, j, compositor))
                    
    # Do sync
    for resync_item in resync_list:
        try:
            clip, track, clip_index, compositor = resync_item
            clip_start = track.clip_start(clip_index)
            clip_end = clip_start + clip.clip_out - clip.clip_in
            
            # Auto fades need to go to start or end of clips and maintain their lengths
            if compositor.transition.info.auto_fade_compositor == True:
                if compositor.transition.info.name == "##auto_fade_in":
                    clip_end = clip_start + compositor.get_length() - 1
                else:
                    clip_start = clip_end - compositor.get_length() + 1
            
            data = {"compositor":compositor,"clip_in":clip_start,"clip_out":clip_end}
            action = edit.move_compositor_action(data)
            action.do_edit()
        except:
            # Clip is probably deleted
            pass
    """
    
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
    
    transition_data = get_transition_data_for_clips(track, from_clip, to_clip)
    
    if track.id >= current_sequence().first_video_index:
        dialogs.transition_edit_dialog(_add_transition_dialog_callback, 
                                       transition_data)
    else:
        _no_audio_tracks_mixing_info()

def get_transition_data_for_clips(track, from_clip, to_clip):
    
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
    return transition_data

def _add_transition_render_folder_select_callback(dialog, response_id, file_select):
    try:
        folder = file_select.get_filenames()[0]
    except:
        dialog.destroy()
        return

    dialog.destroy()
    if response_id == Gtk.ResponseType.YES:
        if folder ==  os.path.expanduser("~"):
            dialogs.rendered_clips_no_home_folder_dialog()
        else:
            editorpersistance.prefs.render_folder = folder
            editorpersistance.save()
            add_transition_pressed(True)

def _add_transition_dialog_callback(dialog, response_id, selection_widgets, transition_data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    # Get input data
    type_combo, length_entry, enc_combo, quality_combo, wipe_luma_combo_box, color_button = selection_widgets
    transition_type_selection_index = type_combo.get_active()
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

    # Save encoding
    PROJECT().set_project_property(appconsts.P_PROP_TRANSITION_ENCODING,(encoding_option_index,quality_option_index))

    from_clip = transition_data["from_clip"]
    to_clip = transition_data["to_clip"]

    # Get values to build transition render sequence
    # Divide transition lenght between clips, odd frame goes to from_clip 
    real_length = length + 1 # first frame is 100% from clip frame so we are going to have to drop that
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
                                 transition_data["to_handle"],
                                 length) == False:
        return
    
    editorstate.transition_length = length
    
    # Get from in and out frames
    from_in = from_clip.clip_out - from_part + add_thingy
    from_out = from_in + length # or transition will include one frame too many
    
    # Get to in and out frames
    to_in = to_clip.clip_in - to_part - 1 
    to_out = to_in + length # or transition will include one frame too many

    # Edit clears selection, get track index before selection is cleared
    trans_index = movemodes.selected_range_out
    movemodes.clear_selected_clips()

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

    creation_data = (   from_clip.id,
                        to_clip.id,
                        from_out,
                        from_in,
                        to_out,
                        to_in,
                        transition_type_selection_index,
                        sorted_wipe_luma_index,
                        color_str)
                                                
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
    print "Render complete"

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
        _no_creation_data_dialog()
        return
    
    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_selection_index, \
    sorted_wipe_luma_index, color_str = clip.creation_data
    
    from_clip = editorstate.current_sequence().get_clip_for_id(from_clip_id)
    to_clip = editorstate.current_sequence().get_clip_for_id(to_clip_id)
    if from_clip == None or to_clip == None:
        _source_clips_not_found_dialog()
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
    
    dialog.destroy()
    
    enc_combo, quality_combo = selection_widgets
    encoding_option_index = enc_combo.get_active()
    quality_option_index = quality_combo.get_active()
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension

    clip = transition_data["clip"]
    track =  transition_data["track"]
    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_selection_index, \
    sorted_wipe_luma_index, color_str = clip.creation_data
    
    trans_index = track.clips.index(clip)

    producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                        transition_data["from_clip"],
                                                                        transition_data["to_clip"],
                                                                        from_out,
                                                                        from_in,
                                                                        to_out,
                                                                        to_in,
                                                                        transition_type_selection_index,
                                                                        sorted_wipe_luma_index,
                                                                        color_str)
    

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

def _check_transition_handles(from_req, from_handle, to_req, to_handle, length):

    if from_req > from_handle or to_req  > to_handle:
        SPACE_TAB = "    "
        info_text = _("To create a rendered transition you need enough media overlap from both clips!\n\n")
        first_clip_info = None
        if from_req > from_handle:
        
            first_clip_info = \
                        _("<b>FIRST CLIP MEDIA OVERLAP:</b>  ") + \
                        SPACE_TAB + _("Available <b>") + str(from_handle) + _("</b> frame(s), " ) + \
                        SPACE_TAB + _("Required <b>") + str(from_req) + _("</b> frame(s)")


        second_clip_info = None
        if to_req  > to_handle:
            second_clip_info = \
                            _("<b>SECOND CLIP MEDIA OVERLAP:</b> ") + \
                            SPACE_TAB + _("Available <b>") + str(to_handle) + _("</b> frame(s), ") + \
                            SPACE_TAB + _("Required <b>") + str(to_req) + _("</b> frame(s) ")

        
        img = Gtk.Image.new_from_file ((respaths.IMAGE_PATH + "transition_wrong.png"))
        img2 = Gtk.Image.new_from_file ((respaths.IMAGE_PATH + "transition_right.png"))
        img2.set_margin_bottom(24)

        label1 = Gtk.Label(_("Current situation, not enought media overlap:"))
        label1.set_margin_bottom(12)
        label2 = Gtk.Label(_("You need more media overlap:"))
        label2.set_margin_bottom(12)
        label2.set_margin_top(24)
        label3 = Gtk.Label(info_text)
        label3.set_use_markup(True)
        if first_clip_info != None:
            label4 = Gtk.Label(first_clip_info)
            label4.set_use_markup(True)
        if second_clip_info != None:
            label5 = Gtk.Label(second_clip_info)
            label5.set_use_markup(True)
        
        row1 = guiutils.get_centered_box([label1])
        row2 = guiutils.get_centered_box([img])
        row3 = guiutils.get_centered_box([label2])
        row4 = guiutils.get_centered_box([img2])
        row5 = guiutils.get_centered_box([label3])
        
        rows = [row1, row2, row3, row4]

        
        if first_clip_info != None:
            row6 = guiutils.get_left_justified_box([label4])
            rows.append(row6)
        if second_clip_info != None:
            row7 = guiutils.get_left_justified_box([label5])
            rows.append(row7)
        

        dialogutils.warning_message_with_panels(_("More media overlap needed to create transition!"), 
                                                "", gui.editor_window.window, True, dialogutils.dialog_destroy, rows)
                
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
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    # Get input data
    type_combo, length_entry, enc_combo, quality_combo, color_button = selection_widgets

    transition_type_selection_index = type_combo.get_active() + 3 # +3 because mlttransitions.RENDERED_FADE_IN = 3 and mlttransitions.RENDERED_FADE_OUT = 4
                                                                  # and fade in/out selection indexes are 0 and 1
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

    # Save encoding
    PROJECT().set_project_property(appconsts.P_PROP_TRANSITION_ENCODING,(encoding_option_index,quality_option_index))
    
    clip = transition_data["clip"]
    
    if length > clip.clip_length():
        info_text = _("Clip is too short for the requested fade:\n\n") + \
                    _("<b>Clip Length:</b> ") + str(clip.clip_length()) + _(" frame(s)\n") + \
                    _("<b>Fade Length:</b> ") + str(length) + _(" frame(s)\n")
        dialogutils.info_message(_("Clip is too short!"),
                                 info_text,
                                 gui.editor_window.window)
        return

    # Remember fade and transition lengths for next invocation, users prefer this over one default value
    editorstate.fade_length = length

    # Edit clears selection, get track index before selection is cleared
    clip_index = movemodes.selected_range_in
    movemodes.clear_selected_clips()

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

    # Creation data struct needs to have same members for transitions and fades, hence a lot of None here.
    # Used for rerender functionality.
    creation_data = (   clip.id,
                        None,
                        length,
                        None,
                        None,
                        None,
                        transition_type_selection_index,
                        None,
                        color_str)
                        
    # Save transition data into global variable to be available at render complete callback
    global transition_render_data
    transition_render_data = (clip_index, transition_type_selection_index, clip, transition_data["track"], length, creation_data)
    window_text, type_id = mlttransitions.rendered_transitions[transition_type_selection_index]
    window_text = _("Rendering ") + window_text
    render.render_single_track_transition_clip(producer_tractor,
                                        encoding_option_index,
                                        quality_option_index, 
                                        str(extension_text), 
                                        _fade_render_complete,
                                        window_text)

def _fade_render_complete(clip_path):
    global transition_render_data
    clip_index, fade_type, clip, track, length, creation_data = transition_render_data

    fade_clip = current_sequence().create_rendered_transition_clip(clip_path, fade_type)
    fade_clip.creation_data = creation_data

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

def re_render_fade(data):
    clip, track, msg, x = data
    if not hasattr(clip, "creation_data"):
        _no_creation_data_dialog()
        return
    
    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_selection_index, \
    sorted_wipe_luma_index, color_str = clip.creation_data
    
    from_clip = editorstate.current_sequence().get_clip_for_id(from_clip_id)
    if from_clip == None:
        _source_clips_not_found_dialog()
        return

    fade_data = {   "track":track,
                    "clip":clip,
                    "from_clip":from_clip}

    dialogs.fade_re_render_dialog(_fade_RE_render_dialog_callback, fade_data)

def _fade_RE_render_dialog_callback(dialog, response_id, selection_widgets, fade_data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return
    
    # Get input data
    enc_combo, quality_combo = selection_widgets
    encoding_option_index = enc_combo.get_active()
    quality_option_index = quality_combo.get_active()
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension

    dialog.destroy()
        
    track = fade_data["track"]
    orig_fade_clip = fade_data["clip"]
    from_clip = fade_data["from_clip"]
    length = orig_fade_clip.clip_out - orig_fade_clip.clip_in + 1
    
    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_index, \
    sorted_wipe_luma_index, color_str = orig_fade_clip.creation_data

    # We need to change fade source clip in or out point and source clip is in timeline currently
    from_clone = editorstate.current_sequence().create_clone_clip(from_clip)
    if transition_type_index == appconsts.RENDERED_FADE_IN:
        from_clone.clip_in = from_clone.clip_in - length
    else:
        from_clone.clip_out = from_clone.clip_out + length
    
    # Save encoding
    PROJECT().set_project_property(appconsts.P_PROP_TRANSITION_ENCODING,(encoding_option_index, quality_option_index))

    # Remember fade and transition lengths for next invocation, users prefer this over one default value.
    editorstate.fade_length = length

    producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                        from_clone,
                                                                        None,
                                                                        length,
                                                                        None,
                                                                        None,
                                                                        None,
                                                                        transition_type_index,
                                                                        None,
                                                                        color_str)
    print "producer_tractor length:" + str(producer_tractor.get_length())

    fade_clip_index = track.clips.index(orig_fade_clip)
    
    # Save transition data into global variable to be available at render complete callback
    global transition_render_data
    transition_render_data = (fade_clip_index, transition_type_index, from_clone, track, length, orig_fade_clip.creation_data)
    window_text, type_id = mlttransitions.rendered_transitions[transition_type_index]
    window_text = _("Rendering ") + window_text
    render.render_single_track_transition_clip( producer_tractor,
                                                encoding_option_index,
                                                quality_option_index, 
                                                str(extension_text), 
                                                _fade_RE_render_complete,
                                                window_text)

def _fade_RE_render_complete(clip_path):    
    global transition_render_data
    clip_index, fade_type, from_clone, track, length, creation_data = transition_render_data

    new_fade_clip = current_sequence().create_rendered_transition_clip(clip_path, fade_type)
    new_fade_clip.creation_data = creation_data

    data = {"fade_clip":new_fade_clip,
            "index":clip_index,
            "track":track,
            "length":length}

    action = edit.replace_rendered_fade_action(data)
    action.do_edit()

def rerender_all_rendered_transitions_and_fades():
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
                    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_selection_index, \
                        sorted_wipe_luma_index, color_str = clip.creation_data
                    from_clip = editorstate.current_sequence().get_clip_for_id(from_clip_id)
                    to_clip = editorstate.current_sequence().get_clip_for_id(to_clip_id)
                    if clip.rendered_type < appconsts.RENDERED_FADE_IN:
                        # transition
                        if from_clip == None or to_clip == None:
                             unrenderable += 1
                        else:
                            rerender_list.append((clip, track))
                    else:
                        # fade
                        if from_clip == None:
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
    enc_combo, quality_combo = selection_widgets
    encoding_option_index = enc_combo.get_active()
    quality_option_index = quality_combo.get_active()
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension

    dialog.destroy()
    
    renrender_window = ReRenderderAllWindow((encoding_option_index, quality_option_index, extension_text), rerender_list)
    renrender_window.create_gui()
    renrender_window.start_render()


class ReRenderderAllWindow:
    
    def __init__(self, encoding_selections, rerender_list):
        self.rerender_list = rerender_list
        self.rendered_items = []
        self.encoding_selections = encoding_selections
        self.dialog = Gtk.Dialog("Rerender all Rendered Transitions / Fades",
                         gui.editor_window.window,
                         Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                         (_("Cancel").encode('utf-8'), Gtk.ResponseType.REJECT))
        self.current_item = 0
        self.runner_thread = None
        self.renderer = None
    
    def create_gui(self):
        text = ""
        self.text_label = Gtk.Label(label=text)
        self.text_label.set_use_markup(True)
        
        text_box = Gtk.HBox(False, 2)
        text_box.pack_start(self.text_label,False, False, 0)
        text_box.pack_start(Gtk.Label(), True, True, 0)

        status_box = Gtk.HBox(False, 2)
        status_box.pack_start(text_box, False, False, 0)
        status_box.pack_start(Gtk.Label(), True, True, 0)

        self.progress_bar = Gtk.ProgressBar()
    
        progress_vbox = Gtk.VBox(False, 2)
        progress_vbox.pack_start(status_box, False, False, 0)
        progress_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
        progress_vbox.pack_start(self.progress_bar, False, False, 0)

        alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)

        self.dialog.vbox.pack_start(alignment, True, True, 0)
        dialogutils.set_outer_margins(self.dialog.vbox)
        self.dialog.set_default_size(500, 125)
        alignment.show_all()
        self.dialog.connect('response', self._cancel_pressed)
        self.dialog.show()


    def start_render(self):
        self.runner_thread = ReRenderRunnerThread(self)
        self.runner_thread.start()

    def render_next(self):
        # Update item text          
        info_text = _("Rendering item ") + str(self.current_item + 1) + "/" + str(len(self.rerender_list))
        Gdk.threads_enter()
        self.text_label.set_text(info_text)
        Gdk.threads_leave()
        
        # Get render data
        clip, track = self.rerender_list[self.current_item]
        encoding_option_index, quality_option_index, file_ext = self.encoding_selections 

        # Dreate render consumer
        profile = PROJECT().profile
        folder = editorpersistance.prefs.render_folder
        file_name = md5.new(str(os.urandom(32))).hexdigest()
        self.write_file = folder + "/"+ file_name + file_ext
        consumer = renderconsumer.get_render_consumer_for_encoding_and_quality(self.write_file, profile, encoding_option_index, quality_option_index)
        
        if clip.rendered_type > appconsts.RENDERED_COLOR_DIP:
            self._render_fade(clip, track, consumer, self.write_file)
        else:
            self._render_transition(clip, track, consumer, self.write_file)

    def _render_fade(self, orig_fade_clip, track, consumer, write_file):
        from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_index, \
        sorted_wipe_luma_index, color_str = orig_fade_clip.creation_data
        length = orig_fade_clip.clip_out - orig_fade_clip.clip_in + 1
        
        # We need to change fade source clip in or out point and source clip is in timeline currently
        from_clip = editorstate.current_sequence().get_clip_for_id(from_clip_id)
        from_clone = editorstate.current_sequence().create_clone_clip(from_clip)
        if transition_type_index == appconsts.RENDERED_FADE_IN:
            from_clone.clip_in = from_clone.clip_in - length
        else:
            from_clone.clip_out = from_clone.clip_out + length

        producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                            from_clone,
                                                                            None,
                                                                            length,
                                                                            None,
                                                                            None,
                                                                            None,
                                                                            transition_type_index,
                                                                            None,
                                                                            color_str)

        # start and end frames
        start_frame = 0
        end_frame = producer_tractor.get_length() - 1
            
        # Launch render
        self.renderer = renderconsumer.FileRenderPlayer(write_file, producer_tractor, consumer, start_frame, end_frame)
        self.renderer.start()


    def _render_transition(self, clip, track, consumer, write_file):
        from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_selection_index, \
        sorted_wipe_luma_index, color_str = clip.creation_data

        from_clip = editorstate.current_sequence().get_clip_for_id(from_clip_id)
        to_clip = editorstate.current_sequence().get_clip_for_id(to_clip_id)
                    
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
        
        # start and end frames
        start_frame = 0
        end_frame = producer_tractor.get_length() - 1
        
        # Launch render
        self.renderer = renderconsumer.FileRenderPlayer(write_file, producer_tractor, consumer, start_frame, end_frame)
        self.renderer.start()
        
    def update_fraction(self):
        if self.renderer == None:
            return
        
        render_fraction = self.renderer.get_render_fraction()
        
        Gdk.threads_enter()
        self.progress_bar.set_fraction(render_fraction)
        pros = int(render_fraction * 100)
        self.progress_bar.set_text(str(pros) + "%")
        Gdk.threads_leave()

    def show_full_fraction(self):
        Gdk.threads_enter()
        self.progress_bar.set_fraction(1.0)
        pros = int(1.0 * 100)
        self.progress_bar.set_text(str(pros) + "%")
        Gdk.threads_leave()
        
    def item_render_complete(self):
        clip, track = self.rerender_list[self.current_item]
        self.rendered_items.append((clip, track, str(self.write_file)))
        self.current_item += 1

    def all_items_done(self):
        return self.current_item == len(self.rerender_list)

    def _cancel_pressed(self, dialog, response_id):
        self.dialog.destroy()

    def exit_shutdown(self):       
        for render_item in self.rendered_items:
            orig_clip, track, new_clip_path = render_item
            
            from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_index, \
            sorted_wipe_luma_index, color_str = orig_clip.creation_data
        
            clip_index = track.clips.index(orig_clip)
                        
            if orig_clip.rendered_type > appconsts.RENDERED_COLOR_DIP:
                new_fade_clip = current_sequence().create_rendered_transition_clip(new_clip_path, transition_type_index)
                new_fade_clip.creation_data = orig_clip.creation_data

                length = orig_clip.clip_out - orig_clip.clip_in + 1
        
                data = {"fade_clip":new_fade_clip,
                        "index":clip_index,
                        "track":track,
                        "length":length}
                
                Gdk.threads_enter()
                action = edit.replace_rendered_fade_action(data)
                action.do_edit()
                Gdk.threads_leave()
            else:
                transition_clip = current_sequence().create_rendered_transition_clip(new_clip_path, transition_type_index)
                transition_clip.creation_data = orig_clip.creation_data
                transition_clip.clip_in = orig_clip.clip_in
                transition_clip.clip_out = orig_clip.clip_out

                data = {"track":track,
                        "transition_clip":transition_clip,
                        "transition_index":clip_index}
                        
                Gdk.threads_enter()
                action = edit.replace_centered_transition_action(data)
                action.do_edit()
                Gdk.threads_leave()

        Gdk.threads_enter()
        self.dialog.destroy()
        Gdk.threads_leave()


class ReRenderRunnerThread(threading.Thread):
    
    def __init__(self, rerender_window):
        self.rerender_window = rerender_window
        
        threading.Thread.__init__(self)

    def run(self):
        self.running = True
        while self.running:
            self.rerender_window.render_next()
            
            item_render_ongoing = True
            while item_render_ongoing:
                time.sleep(0.33)
                
                self.rerender_window.update_fraction()
                
                if self.rerender_window.renderer.stopped == True:
                    item_render_ongoing = False
                
            self.rerender_window.show_full_fraction()
            
            self.rerender_window.item_render_complete()
            if self.rerender_window.all_items_done() == True:
                self.running = False
            else:
                time.sleep(0.33)

        self.rerender_window.exit_shutdown()


def _no_creation_data_dialog():
    primary_txt = _("Can't rerender this fade / transition.")
    secondary_txt = _("This fade / transition was created with Flowblade <= 1.14 and does not have the necessary data embedded.\nRerendering works with fades/transitions created with Flowblade >= 1.16.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

def _source_clips_not_found_dialog():
    primary_txt = _("Can't rerender this fade / transition.")
    secondary_txt = _("The clip/s used to create this fade / transition are no longer available on the timeline.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
    
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
def do_timeline_objects_copy():
    if _timeline_has_focus() == False:
        # try to extract text to clipboard because user pressed CTRL + C
        copy_source = gui.editor_window.window.get_focus()
        try:
            copy_source.copy_clipboard()
        except:# selected widget was not a Gtk.Editable that can provide text to clipboard
            pass

        return 

    if compositormodes.compositor != None and compositormodes.compositor.selected == True:
        editorstate.set_copy_paste_objects((COPY_PASTA_DATA_COMPOSITOR_PROPERTIES, compositormodes.compositor.get_copy_paste_objects()))
        return
        
    if movemodes.selected_track != -1:
        # copying clips
        track = current_sequence().tracks[movemodes.selected_track]
        clone_clips = []
        for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
            clone_clip = current_sequence().clone_track_clip(track, i)
            clone_clips.append(clone_clip)
        editorstate.set_copy_paste_objects((COPY_PASTA_DATA_CLIPS, clone_clips))
        return

def do_timeline_objects_paste():
    if _timeline_has_focus() == False:
        return 
        
    track = current_sequence().get_first_active_track()
    if track == None:
        return 
    paste_objs = editorstate.get_copy_paste_objects()
    if paste_objs == None:
        return 
    
    data_type, paste_clips = paste_objs
    if data_type != COPY_PASTA_DATA_CLIPS:
        do_compositor_data_paste(paste_objs)
        return

    tline_pos = editorstate.current_tline_frame()

    new_clips = []
    for clip in paste_clips:
        new_clip = current_sequence().create_clone_clip(clip)
        new_clips.append(new_clip)
    editorstate.set_copy_paste_objects((COPY_PASTA_DATA_CLIPS, new_clips))

    # Paste clips
    editevent.do_multiple_clip_insert(track, paste_clips, tline_pos)

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
    if data_type != COPY_PASTA_DATA_CLIPS:
        do_compositor_data_paste(paste_objs)
        return
        
    if movemodes.selected_track == -1:
        return
        
    target_clips = []
    track = current_sequence().tracks[movemodes.selected_track]
    for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        target_clips.append(track.clips[i])

    # First clip of selection is used as filters source
    source_clip = paste_clips[0]

    # Currently selected clips are target clips
    target_clips = []
    track = current_sequence().tracks[movemodes.selected_track]
    for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1):
        target_clips.append(track.clips[i])
        
    for target_clip in target_clips:
        data = {"clip":target_clip,"clone_source_clip":source_clip}
        action = edit.paste_filters_action(data)
        action.do_edit()

def do_compositor_data_paste(paste_objs):
    data_type, paste_data = paste_objs
    if data_type != COPY_PASTA_DATA_COMPOSITOR_PROPERTIES:
        print "supposed unreahcable if in do_compositor_data_paste"
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

