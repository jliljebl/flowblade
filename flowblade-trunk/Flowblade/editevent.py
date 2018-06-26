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
Handles or passes on mouse edit events from timeline.

Handles edit mode setting.
"""

import os

from gi.repository import Gdk

import appconsts
import audiosync
import clipeffectseditor
import clipenddragmode
import compositeeditor
import compositormodes
import cutmode
import dialogutils
import edit
import editorstate
from editorstate import current_sequence
from editorstate import PLAYER
from editorstate import timeline_visible
from editorstate import EDIT_MODE
import editorpersistance
import gui
import guicomponents
import kftoolmode
import medialog
import modesetting
import movemodes
import multimovemode
import syncsplitevent
import tlinewidgets
import trimmodes
import updater
import utils


# functions are monkeypatched in at app.py 
display_clip_menu_pop_up = None
compositor_menu_item_activated = None


# ----------------------------- module funcs
def do_clip_insert(track, new_clip, tline_pos):
    index = _get_insert_index(track, tline_pos)

    # Can't put audio media on video track 
    if ((new_clip.media_type == appconsts.AUDIO)
       and (track.type == appconsts.VIDEO)):        
        _display_no_audio_on_video_msg(track)
        return

    movemodes.clear_selected_clips()
    
    # Do edit
    data = {"track":track,
            "clip":new_clip,
            "index":index,
            "clip_in":new_clip.mark_in,
            "clip_out":new_clip.mark_out}
    action = edit.insert_action(data)
    action.do_edit()
    
    updater.display_tline_cut_frame(track, index)

def do_multiple_clip_insert(track, clips, tline_pos):
    index = _get_insert_index(track, tline_pos)
    
    # Can't put audio media on video track
    for new_clip in clips:
        if ((new_clip.media_type == appconsts.AUDIO)
           and (track.type == appconsts.VIDEO)):        
            _display_no_audio_on_video_msg(track)
            return

    movemodes.clear_selected_clips()

    # Do edit
    data = {"track":track,
            "clips":clips,
            "index":index}
    action = edit.insert_multiple_action(data)
    action.do_edit()

    updater.display_tline_cut_frame(track, index)

def  _attempt_dnd_overwrite(track, clip, frame):
    # Can't put audio media on video track 
    if ((clip.media_type == appconsts.AUDIO)
       and (track.type == appconsts.VIDEO)):        
        return

    # Dropping on first available frame after last clip is append 
    # and is handled by insert code
    if track.get_length() == frame:
        return False

    # Clip dropped after last clip on track
    if track.get_length() < frame:
        index = _get_insert_index(track, track.get_length())

        movemodes.clear_selected_clips()
    
        data = {"track":track,
                "clip":clip,
                "blank_length":frame - track.get_length(),
                "index":index,
                "clip_in":clip.mark_in,
                "clip_out":clip.mark_out}
        action = edit.dnd_after_track_end_action(data)
        action.do_edit()

        updater.display_tline_cut_frame(track, index + 1)
        return True
    else: # Clip dropped before end of last clip on track
        index = track.get_clip_index_at(frame)
        overwritten_clip = track.clips[index]
        
        # dnd overwrites can only done on blank clips
        # Drops on clips are considered inserts
        if overwritten_clip.is_blanck_clip == False:
            return False

        drop_length = clip.mark_out - clip.mark_in + 1 # +1 , mark out incl.
        blank_start = track.clip_start(index)
        blank_end = track.clip_start(index + 1)
        
        movemodes.clear_selected_clips()
  
        # Clip dropped on first frame of blank
        if blank_start == frame:
            # If dropped clip longer then blank, replace blank
            if frame + drop_length >= blank_end:
                data = {"track":track,
                        "clip":clip,
                        "blank_length":blank_end - blank_start,
                        "index":index,
                        "clip_in":clip.mark_in}
                action = edit.dnd_on_blank_replace_action(data)
                action.do_edit()
            else: # If dropped clip shorter then blank, replace start part of blank
                data = {"track":track,
                        "clip":clip,
                        "blank_length":blank_end - blank_start,
                        "index":index,
                        "clip_in":clip.mark_in,
                        "clip_out":clip.mark_out}
                action = edit.dnd_on_blank_start_action(data)
                action.do_edit()

            updater.display_tline_cut_frame(track, index)
            return True

        # Clip dropped after first frame of blank        
        if frame + drop_length >= blank_end:
            # Overwrite end half of blank
            data = {"track":track,
                    "clip":clip,
                    "overwritten_blank_length":frame - blank_start,
                    "blank_length":blank_end - blank_start,
                    "index":index,
                    "clip_in":clip.mark_in,
                    "clip_out":clip.mark_out}
            action = edit.dnd_on_blank_end_action(data)
            action.do_edit()
        else: # Overwrite part of blank ei toimi
            data = {"track":track,
                    "clip":clip,
                    "overwritten_start_frame":frame - blank_start,
                    "blank_length":blank_end - blank_start,
                    "index":index,
                    "clip_in":clip.mark_in,
                    "clip_out":clip.mark_out}
            action = edit.dnd_on_blank_middle_action(data)
            action.do_edit()
            
        updater.display_tline_cut_frame(track, index + 1)
        return True

    return False # this won't be hit
    
def _get_insert_index(track, tline_pos):
    cut_frame = current_sequence().get_closest_cut_frame(track.id, tline_pos)
    index = current_sequence().get_clip_index(track, cut_frame)
    if index == -1:
        # Fix for case when inserting on empty track, which causes exception in
        # editorstate.current_sequence().get_clip_index(...) which returns -1
        index = track.count()
    elif ((cut_frame == -1) and (index == 0)
        and (tline_pos > 0) and (tline_pos >= track.get_length())):
        # Fix for case in which we get -1 for cut_frame because
        # tline_pos after last frame of the sequence, and
        # then get 0 for index which places clip in beginning, but we 
        # want it appended in the end of sequence.
        index = track.count()
    return index

def _display_no_audio_on_video_msg(track):
    dialogutils.warning_message(_("Can't put an audio clip on a video track."), 
                            _("Track ")+ utils.get_track_name(track, current_sequence()) + _(" is a video track and can't display audio only material."),
                            gui.editor_window.window)


# ------------------------------------ timeline mouse events
def tline_canvas_mouse_pressed(event, frame):
    """
    Mouse event callback from timeline canvas widget
    """
    
    if PLAYER().looping():
        return
    elif PLAYER().is_playing():
        PLAYER().stop_playback()
    
    # Double click handled separately
    if event.type == Gdk.EventType._2BUTTON_PRESS:
        return

    # Handle and exit parent clip selecting
    if EDIT_MODE() == editorstate.SELECT_PARENT_CLIP:
        syncsplitevent.select_sync_parent_mouse_pressed(event, frame)
        editorstate.timeline_mouse_disabled = True
        # Set INSERT_MODE
        modesetting.set_default_edit_mode()  
        return

    # Handle and exit tline sync clip selecting
    if EDIT_MODE() == editorstate.SELECT_TLINE_SYNC_CLIP:
        audiosync.select_sync_clip_mouse_pressed(event, frame)
        editorstate.timeline_mouse_disabled = True
        # Set INSERT_MODE
        modesetting.set_default_edit_mode()
        return
        
    # Hitting timeline in clip display mode displays timeline in
    # default mode.
    if not timeline_visible():
        updater.display_sequence_in_monitor()
        if (event.button == 1):
            # Now that we have correct edit mode we'll reenter
            # this method to get e.g. a select action
            tline_canvas_mouse_pressed(event, frame)
            return
        if (event.button == 3):
            # Right mouse + CTRL displays clip menu if we hit clip
            if (event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                PLAYER().seek_frame(frame)
            # Right mouse on timeline seeks frame
            else:
                success = display_clip_menu_pop_up(event.y, event, frame)
                if not success:
                    PLAYER().seek_frame(frame)
        return

    # If clip end drag mode is for some reason still active, exit to default edit mode
    if EDIT_MODE() == editorstate.CLIP_END_DRAG:
        modesetting.set_default_edit_mode()
        # This shouldn't happen unless for some reason mouse release didn't hit clipenddragmode listener.
        print "EDIT_MODE() == editorstate.CLIP_END_DRAG at mouse press!"

    #  Check if match frame close is hit
    if editorstate.current_is_move_mode() and timeline_visible():
        if tlinewidgets.match_frame_close_hit(event.x, event.y) == True:
            tlinewidgets.set_match_frame(-1, -1, True)
            updater.repaint_tline()
            return

    #  Check if compositor is hit and if so, handle compositor editing
    if editorstate.current_is_move_mode() and timeline_visible():
        hit_compositor = tlinewidgets.compositor_hit(frame, event.y, current_sequence().compositors)
        if hit_compositor != None:         
            if editorstate.auto_follow == False or hit_compositor.obey_autofollow == False:
                movemodes.clear_selected_clips()
                if event.button == 1 or (event.button == 3 and event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                    compositormodes.set_compositor_mode(hit_compositor)
                    mode_funcs = EDIT_MODE_FUNCS[editorstate.COMPOSITOR_EDIT]
                    press_func = mode_funcs[TL_MOUSE_PRESS]
                    press_func(event, frame)
                    return
            if event.button == 3:
                compositormodes.set_compositor_selected(hit_compositor)
                guicomponents.display_compositor_popup_menu(event, hit_compositor,
                                                            compositor_menu_item_activated)
                return
            elif event.button == 2:
                updater.zoom_project_length()
                return

    compositormodes.clear_compositor_selection()

    # Check if we should enter clip end drag mode
    if (event.button == 3 and editorstate.current_is_move_mode()
        and timeline_visible() and (event.get_state() & Gdk.ModifierType.CONTROL_MASK)):
        # with CTRL right mouse
        clipenddragmode.maybe_init_for_mouse_press(event, frame)
    elif (timeline_visible() and (EDIT_MODE() == editorstate.INSERT_MOVE or EDIT_MODE() == editorstate.OVERWRITE_MOVE)
        and (tlinewidgets.pointer_context == appconsts.POINTER_CONTEXT_END_DRAG_LEFT or tlinewidgets.pointer_context == appconsts.POINTER_CONTEXT_END_DRAG_RIGHT)):
        # with pointer context
        clipenddragmode.maybe_init_for_mouse_press(event, frame)

    # Handle mouse button presses depending which button was pressed and
    # editor state.
    # RIGHT BUTTON: seek frame or display clip menu if not dragging clip end
    if (event.button == 3 and EDIT_MODE() != editorstate.CLIP_END_DRAG):
        if ((not editorstate.current_is_active_trim_mode()) and timeline_visible()):
            if not(event.get_state() & Gdk.ModifierType.CONTROL_MASK):
                success = display_clip_menu_pop_up(event.y, event, frame)
                if not success:
                    PLAYER().seek_frame(frame)
        else:
            # For trim modes set <X>_NO_EDIT edit mode and seek frame. and seek frame
            trimmodes.set_no_edit_trim_mode()
            PLAYER().seek_frame(frame)
        return
    # LEFT BUTTON + CTRL: Select new trimmed clip in one roll trim mode
    #  This is not that relevant anymore with context sensitive cursor, look to remove.
    elif ((event.button == 1 
          and (event.get_state() & Gdk.ModifierType.CONTROL_MASK)
          and EDIT_MODE() == editorstate.ONE_ROLL_TRIM) or 
        (event.button == 1 and editorstate.cursor_is_tline_sensitive == True and EDIT_MODE() == editorstate.ONE_ROLL_TRIM)):
        track = tlinewidgets.get_track(event.y)
        if track == None:
            if editorpersistance.prefs.empty_click_exits_trims == True:
                modesetting.set_default_edit_mode(True)
            return
        success = trimmodes.set_oneroll_mode(track, frame)
        if (not success) and editorpersistance.prefs.empty_click_exits_trims == True:
            modesetting.set_default_edit_mode(True)
            return
            
        if trimmodes.edit_data["to_side_being_edited"] == True:
            pointer_context = appconsts.POINTER_CONTEXT_TRIM_LEFT
        else:
            pointer_context = appconsts.POINTER_CONTEXT_TRIM_RIGHT
        gui.editor_window.set_tline_cursor_to_context(pointer_context)
        gui.editor_window.set_tool_selector_to_mode()
        if not editorpersistance.prefs.quick_enter_trims:
            editorstate.timeline_mouse_disabled = True
        else:
            trimmodes.oneroll_trim_move(event.x, event.y, frame, None)
    # LEFT BUTTON + CTRL: Select new trimmed clip in two roll trim mode
    # This is not that relevant anymore with context sensitive cursor, look to remove.
    elif (event.button == 1 
          and (event.get_state() & Gdk.ModifierType.CONTROL_MASK)
          and EDIT_MODE() == editorstate.TWO_ROLL_TRIM):
        track = tlinewidgets.get_track(event.y)
        if track == None:
            if editorpersistance.prefs.empty_click_exits_trims == True:
                modesetting.set_default_edit_mode(True)
            return
        success = trimmodes.set_tworoll_mode(track, frame)
        if (not success) and  editorpersistance.prefs.empty_click_exits_trims == True:
            modesetting.set_default_edit_mode(True)
            return
        if not editorpersistance.prefs.quick_enter_trims:
            editorstate.timeline_mouse_disabled = True
        else:
            trimmodes.tworoll_trim_move(event.x, event.y, frame, None)
    elif event.button == 2:
        updater.zoom_project_length()
    # LEFT BUTTON: Handle left mouse button edits by passing event to current edit mode
    # handler func
    elif event.button == 1 or event.button == 3:
        mode_funcs = EDIT_MODE_FUNCS[EDIT_MODE()]
        press_func = mode_funcs[TL_MOUSE_PRESS]
        press_func(event, frame)

def tline_canvas_mouse_moved(x, y, frame, button, state):
    """
    Mouse event callback from timeline canvas widget
    """
    # Refuse mouse events for some editor states.
    if PLAYER().looping():
        return        
    if editorstate.timeline_mouse_disabled == True:
        return
    if not timeline_visible():
        return

    # Handle timeline position setting with right mouse button
    if button == 3 and EDIT_MODE() != editorstate.CLIP_END_DRAG and EDIT_MODE() != editorstate.COMPOSITOR_EDIT:
        if not timeline_visible():
            return
        PLAYER().seek_frame(frame)
    # Handle mouse button edits
    elif button == 1 or button == 3:
        mode_funcs = EDIT_MODE_FUNCS[EDIT_MODE()]
        move_func = mode_funcs[TL_MOUSE_MOVE]
        move_func(x, y, frame, state)

def tline_canvas_mouse_released(x, y, frame, button, state):
    """
    Mouse event callback from timeline canvas widget
    """
    gui.editor_window.set_cursor_to_mode()
     
    if editorstate.timeline_mouse_disabled == True:
        gui.editor_window.set_cursor_to_mode() # we only need this update when mode change (to active trim mode) disables mouse, so we'll only do this then
        tlinewidgets.trim_mode_in_non_active_state = False # we only need this update when mode change (to active trim mode) disables mouse, so we'll only do this then
        gui.tline_canvas.widget.queue_draw()
        editorstate.timeline_mouse_disabled = False
        return

    if not timeline_visible():
        return
        
    if PLAYER().looping():
        PLAYER().stop_loop_playback(trimmodes.trim_looping_stopped)
        return

    # Handle timeline position setting with right mouse button
    if button == 3 and EDIT_MODE() != editorstate.CLIP_END_DRAG and EDIT_MODE() != editorstate.COMPOSITOR_EDIT:
        if not timeline_visible():
            return
        PLAYER().seek_frame(frame) 
    # Handle mouse button edits
    elif button == 1 or button == 3:
        mode_funcs = EDIT_MODE_FUNCS[EDIT_MODE()]
        release_func = mode_funcs[TL_MOUSE_RELEASE]
        release_func(x, y, frame, state)

def tline_canvas_double_click(frame, x, y):
    if PLAYER().looping():
        return
    elif PLAYER().is_playing():
        PLAYER().stop_playback()

    if not timeline_visible():
        updater.display_sequence_in_monitor()
        modesetting.set_default_edit_mode()
        return

    hit_compositor = tlinewidgets.compositor_hit(frame, y, current_sequence().compositors)
    if hit_compositor != None:
        compositeeditor.set_compositor(hit_compositor)
        return

    track = tlinewidgets.get_track(y)
    if track == None:
        return
    clip_index = current_sequence().get_clip_index(track, frame)
    if clip_index == -1:
        return

    clip = track.clips[clip_index]
    if clip.is_blanck_clip == True:
        return
        
    data = (clip, track, None, x)
    updater.open_clip_in_effects_editor(data)


# -------------------------------------------------- DND release event callbacks
def tline_effect_drop(x, y):
    clip, track, index = tlinewidgets.get_clip_track_and_index_for_pos(x, y)
    if clip == None:
        return
    if track == None:
        return
    if track.id < 1 or track.id >= (len(current_sequence().tracks) - 1):
        return 
    if track_lock_check_and_user_info(track):
        modesetting.set_default_edit_mode()
        return
        
    if clip != clipeffectseditor.clip:
        clipeffectseditor.set_clip(clip, track, index)
    
    clipeffectseditor.add_currently_selected_effect() # drag start selects the dragged effect

def tline_media_drop(media_file, x, y, use_marks=False):
    track = tlinewidgets.get_track(y)
    if track == None:
        return
    if track.id < 1 or track.id >= (len(current_sequence().tracks) - 1):
        return 
    if track_lock_check_and_user_info(track):
        modesetting.set_default_edit_mode()
        return

    modesetting.set_default_edit_mode()

    frame = tlinewidgets.get_frame(x)
    
    # Create new clip.
    if media_file.type != appconsts.PATTERN_PRODUCER:
        new_clip = current_sequence().create_file_producer_clip(media_file.path, media_file.name, False, media_file.ttl)
    else:
        new_clip = current_sequence().create_pattern_producer(media_file)

    # Set clip in and out
    if use_marks == False:
        new_clip.mark_in = 0
        new_clip.mark_out = new_clip.get_length() - 1 # - 1 because out is mark_out inclusive

        if media_file.type == appconsts.IMAGE_SEQUENCE:
            new_clip.mark_out = media_file.length
    else:
        new_clip.mark_in = media_file.mark_in
        new_clip.mark_out =  media_file.mark_out

        if new_clip.mark_in == -1:
            new_clip.mark_in = 0
        if new_clip.mark_out == -1:
            new_clip.mark_out = new_clip.get_length() - 1 # - 1 because out is mark_out inclusive
            if media_file.type == appconsts.IMAGE_SEQUENCE:
                new_clip.mark_out = media_file.length

    # Graphics files get added with their default lengths
    f_name, ext = os.path.splitext(media_file.name)
    if utils.file_extension_is_graphics_file(ext) and media_file.type != appconsts.IMAGE_SEQUENCE: # image sequences are graphics files but have own length
        in_fr, out_fr, l = editorpersistance.get_graphics_default_in_out_length()
        new_clip.mark_in = in_fr
        new_clip.mark_out = out_fr

    # Non-insert DND actions
    if editorpersistance.prefs.dnd_action == appconsts.DND_OVERWRITE_NON_V1:
        if track.id != current_sequence().first_video_track().id:
            drop_done = _attempt_dnd_overwrite(track, new_clip, frame)
            if drop_done == True:
                return
    elif editorpersistance.prefs.dnd_action == appconsts.DND_ALWAYS_OVERWRITE:
        drop_done = _attempt_dnd_overwrite(track, new_clip, frame)
        if drop_done == True:
            return
            
    do_clip_insert(track, new_clip, frame)

def tline_range_item_drop(rows, x, y):
    track = tlinewidgets.get_track(y)
    if track == None:
        return
    if track.id < 1 or track.id >= (len(current_sequence().tracks) - 1):
        return 
    if track_lock_check_and_user_info(track):
        modesetting.set_default_edit_mode()
        return
        
    frame = tlinewidgets.get_frame(x)
    clips = medialog.get_clips_for_rows(rows)
    modesetting.set_default_edit_mode()
    do_multiple_clip_insert(track, clips, frame)

# ------------------------------------ track locks handling
def track_lock_check_and_user_info(track, calling_function="this ain't used anymore", actionname="this ain't used anymore"):
    if track.edit_freedom == appconsts.LOCKED:
        track_name = utils.get_track_name(track, current_sequence())

        # No edits on locked tracks.
        primary_txt = _("Can't edit a locked track")
        secondary_txt = _("Track ") + track_name + _(" is locked. Unlock track to edit it.")
        dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window)
        return True

    return False


# ------------------------------------ function tables
# mouse event indexes
TL_MOUSE_PRESS = 0
TL_MOUSE_MOVE = 1
TL_MOUSE_RELEASE = 2

# mouse event handler function lists for mode
INSERT_MOVE_FUNCS = [movemodes.insert_move_press, 
                     movemodes.insert_move_move,
                     movemodes.insert_move_release]
OVERWRITE_MOVE_FUNCS = [movemodes.overwrite_move_press,
                        movemodes.overwrite_move_move,
                        movemodes.overwrite_move_release]
ONE_ROLL_TRIM_FUNCS = [trimmodes.oneroll_trim_press, 
                       trimmodes.oneroll_trim_move,
                       trimmodes.oneroll_trim_release]
ONE_ROLL_TRIM_NO_EDIT_FUNCS = [modesetting.oneroll_trim_no_edit_press, 
                               modesetting.oneroll_trim_no_edit_move,
                               modesetting.oneroll_trim_no_edit_release]
TWO_ROLL_TRIM_FUNCS = [trimmodes.tworoll_trim_press,
                       trimmodes.tworoll_trim_move,
                       trimmodes.tworoll_trim_release]
TWO_ROLL_TRIM_NO_EDIT_FUNCS = [modesetting.tworoll_trim_no_edit_press,
                               modesetting.tworoll_trim_no_edit_move,
                               modesetting.tworoll_trim_no_edit_release]
COMPOSITOR_EDIT_FUNCS = [compositormodes.mouse_press,
                         compositormodes.mouse_move,
                         compositormodes.mouse_release]
SLIDE_TRIM_FUNCS = [trimmodes.slide_trim_press,
                    trimmodes.slide_trim_move,
                    trimmodes.slide_trim_release]
SLIDE_TRIM_NO_EDIT_FUNCS = [modesetting.slide_trim_no_edit_press,
                            modesetting.slide_trim_no_edit_move,
                            modesetting.slide_trim_no_edit_release]
MULTI_MOVE_FUNCS = [multimovemode.mouse_press,
                    multimovemode.mouse_move,
                    multimovemode.mouse_release]
CLIP_END_DRAG_FUNCS = [clipenddragmode.mouse_press,
                       clipenddragmode.mouse_move,
                       clipenddragmode.mouse_release]
CUT_FUNCS = [cutmode.mouse_press,
             cutmode.mouse_move,
             cutmode.mouse_release]
KFTOOL_FUNCS = [kftoolmode.mouse_press,
                kftoolmode.mouse_move,
                kftoolmode.mouse_release]

# (mode -> mouse handler function list) table
EDIT_MODE_FUNCS = {editorstate.INSERT_MOVE:INSERT_MOVE_FUNCS,
                   editorstate.OVERWRITE_MOVE:OVERWRITE_MOVE_FUNCS,
                   editorstate.ONE_ROLL_TRIM:ONE_ROLL_TRIM_FUNCS,
                   editorstate.TWO_ROLL_TRIM:TWO_ROLL_TRIM_FUNCS,
                   editorstate.COMPOSITOR_EDIT:COMPOSITOR_EDIT_FUNCS,
                   editorstate.ONE_ROLL_TRIM_NO_EDIT:ONE_ROLL_TRIM_NO_EDIT_FUNCS,
                   editorstate.TWO_ROLL_TRIM_NO_EDIT:TWO_ROLL_TRIM_NO_EDIT_FUNCS,
                   editorstate.SLIDE_TRIM:SLIDE_TRIM_FUNCS,
                   editorstate.SLIDE_TRIM_NO_EDIT:SLIDE_TRIM_NO_EDIT_FUNCS,
                   editorstate.MULTI_MOVE:MULTI_MOVE_FUNCS,
                   editorstate.CLIP_END_DRAG:CLIP_END_DRAG_FUNCS,
                   editorstate.CUT:CUT_FUNCS,
                   editorstate.KF_TOOL:KFTOOL_FUNCS}

