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
Module handles button edit events from buttons above timeline.
"""
import gtk
import time #added for testing

import appconsts
import dialogutils
import gui
import edit
import editevent
import editorstate
from editorstate import get_track
from editorstate import current_sequence
from editorstate import PLAYER
from editorstate import timeline_visible
from editorstate import MONITOR_MEDIA_FILE
import movemodes
import mlttransitions
import syncsplitevent
import tlinewidgets
import updater

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
    if timeline_visible():
        return PLAYER().current_frame()
    else:
        return tlinewidgets.shadow_frame

# ---------------------------------- edit button events
def cut_pressed():
    if not timeline_visible():
        updater.display_sequence_in_monitor()

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

    editevent.do_clip_insert(track, new_clip, tline_pos)

def append_button_pressed():
    track = current_sequence().get_first_active_track()

    if editevent.track_lock_check_and_user_info(track, insert_button_pressed, "insert"):
        return

    tline_pos = track.get_length()
    
    new_clip = _get_new_clip_from_clip_monitor()
    if new_clip == None:
        no_monitor_clip_info(gui.editor_window.window)
        return

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

def view_mode_changed(combobox):
    editorstate.current_sequence().set_output_mode(combobox.get_active())
    
    
# ------------------------------------------------------- dialogs    
def no_monitor_clip_info(parent_window):
    primary_txt = _("No Clip loaded into Monitor")
    secondary_txt = _("Can't do the requested edit because there is no Clip in Monitor.")
    dialogutils.info_message(primary_txt, secondary_txt, parent_window)

def monitor_clip_too_short(parent_window):
    primary_txt = _("Defined range in Monitor Clip is too short")
    secondary_txt = _("Can't do the requested edit because Mark In -> Mark Out Range or Clip is too short.")
    dialogutils.info_message(primary_txt, secondary_txt, parent_window)

