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

import pygtk
pygtk.require('2.0');
import gtk
import os
import time

import appconsts
import clipeffectseditor
import compositeeditor
import compositormodes
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
import medialog
import movemodes
import multimovemode
import syncsplitevent
import tlinewidgets
import trimmodes
import undo
import updater
import utils


# module state
mouse_disabled = False # Used to ignore drag and release events when press doesn't start an action that can handle those events.
repeat_event = None
parent_selection_data = None # Held here until user presses tline again

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

# ------------------------------------- edit mode setting
def set_default_edit_mode(disable_mouse=False):
    """
    This is used as global 'go to start position' exit door from
    situations where for example user is in trim and exits it
    without specifying which edit mode to go to.
    
    NOTE: As this uses 'programmed click', this method does nothing if insert mode button
    is already down.
    """
    gui.editor_window.handle_insert_move_mode_button_press()
    gui.editor_window.set_mode_selector_to_mode()
    if disable_mouse:
        global mouse_disabled
        mouse_disabled = True

def set_clip_monitor_edit_mode():
    """
    Going to clip monitor exits active trimodes into non active trimmodes.
    """
    if EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        oneroll_trim_no_edit_init()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM_NO_EDIT:
        pass
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        tworoll_trim_no_edit_init()
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM_NO_EDIT:
        pass
    else:
        gui.editor_window.handle_insert_move_mode_button_press()
        
    gui.editor_window.set_mode_selector_to_mode()

def set_post_undo_redo_edit_mode():
    if EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        oneroll_trim_no_edit_init()
    if EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        tworoll_trim_no_edit_init()

def stop_looping():
    # Stop trim mode looping using trimmodes.py methods for it
    # Called when entering move modes.
    if PLAYER().looping():
        if EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
            trimmodes.oneroll_stop_pressed()
        if EDIT_MODE() == editorstate.TWO_ROLL_TRIM: 
            trimmodes.tworoll_stop_pressed()

# -------------------------------------------------------------- move modes
def insert_move_mode_pressed():
    """
    User selects insert move mode.
    """
    stop_looping()
    current_sequence().clear_hidden_track()

    editorstate.edit_mode = editorstate.INSERT_MOVE
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_insert_overlay)

    _set_move_mode()

def overwrite_move_mode_pressed():
    """
    User selects overwrite move mode.
    """
    stop_looping()
    current_sequence().clear_hidden_track()

    editorstate.edit_mode = editorstate.OVERWRITE_MOVE
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_overwrite_overlay)

    _set_move_mode()

def multi_mode_pressed():
    stop_looping()
    current_sequence().clear_hidden_track()

    editorstate.edit_mode = editorstate.MULTI_MOVE
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_multi_overlay)
    
    updater.set_move_mode_gui()
    updater.repaint_tline()

def _set_move_mode():
    updater.set_move_mode_gui()
    updater.set_transition_render_edit_menu_items_sensitive(movemodes.selected_range_in, movemodes.selected_range_out)
    updater.repaint_tline()

# -------------------------------------------------------------- one roll trim
def oneroll_trim_no_edit_init():
    """
    This mode is entered and this method is called when:
    - user first selects trim tool
    - user does cut(X) action while in trim mode
    - user clicks empty and preference is to keep using trim tool (to not exit to INSERT_MOVE)
    """
    stop_looping()
    editorstate.edit_mode = editorstate.ONE_ROLL_TRIM_NO_EDIT
    gui.editor_window.set_cursor_to_mode()
    tlinewidgets.set_edit_mode(None, None) # No overlays are drawn in this edit mode
    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

def oneroll_trim_no_edit_press(event, frame):
    """
    Mouse press while in ONE_ROLL_TRIM_NO_EDIT attempts to init edit and 
    move to ONE_ROLL_TRIM mode.
    """
    success = oneroll_trim_mode_init(event.x, event.y)
    if success:
        # If not quick enter, disable edit until mouse released
        if not editorpersistance.prefs.quick_enter_trims:
            global mouse_disabled
            tlinewidgets.trim_mode_in_non_active_state = True
            mouse_disabled = True
         # If preference is quick enter, call mouse move handler immediately 
         # to move edit point to where mouse is
        else:
            trimmodes.oneroll_trim_move(event.x, event.y, frame, None)
    else:
        if editorpersistance.prefs.empty_click_exits_trims == True:
            set_default_edit_mode(True)
        else:
            editorstate.edit_mode = editorstate.ONE_ROLL_TRIM_NO_EDIT

def oneroll_trim_no_edit_move(x, y, frame, state):
    # Only presses are handled in ONE_ROLL_TRIM_NO_EDIT mode
    pass

def oneroll_trim_no_edit_release(x, y, frame, state):
    # Only presses are handled in ONE_ROLL_TRIM_NO_EDIT mode
    pass

def oneroll_trim_mode_init(x, y):
    """
    User enters ONE_ROLL_TRIM mode from ONE_ROLL_TRIM_NO_EDIT 
    """
    track = tlinewidgets.get_track(y)
    if track == None:
        return False

    if track_lock_check_and_user_info(track, oneroll_trim_mode_init, "one roll trim mode"):
        set_default_edit_mode()
        return False

    stop_looping() 
    editorstate.edit_mode = editorstate.ONE_ROLL_TRIM

    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

    # init mode
    press_frame = tlinewidgets.get_frame(x)
    trimmodes.set_exit_mode_func = set_default_edit_mode
    trimmodes.set_no_edit_mode_func = oneroll_trim_no_edit_init
    success = trimmodes.set_oneroll_mode(track, press_frame)
    return success

# --------------------------------------------------------- two roll trim
def tworoll_trim_no_edit_init():
    stop_looping()
    editorstate.edit_mode = editorstate.TWO_ROLL_TRIM_NO_EDIT
    gui.editor_window.set_cursor_to_mode()
    tlinewidgets.set_edit_mode(None, None) # No overlays are drawn in this edit mode
    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

def tworoll_trim_no_edit_press(event, frame):
    success = tworoll_trim_mode_init(event.x, event.y)
    if success:
        if not editorpersistance.prefs.quick_enter_trims:
            global mouse_disabled
            tlinewidgets.trim_mode_in_non_active_state = True
            mouse_disabled = True
        else:
            trimmodes.tworoll_trim_move(event.x, event.y, frame, None)
    else:
        if editorpersistance.prefs.empty_click_exits_trims == True:
            set_default_edit_mode(True)
        else:
            editorstate.edit_mode = editorstate.TWO_ROLL_TRIM_NO_EDIT

def tworoll_trim_no_edit_move(x, y, frame, state):
    pass

def tworoll_trim_no_edit_release(x, y, frame, state):
    pass
    
def tworoll_trim_mode_init(x, y):
    """
    User selects two roll mode
    """
    track = tlinewidgets.get_track(y)
    if track == None:
        return False
    
    if track_lock_check_and_user_info(track, tworoll_trim_mode_init, "two roll trim mode",):
        set_default_edit_mode()
        return False

    stop_looping()
    editorstate.edit_mode = editorstate.TWO_ROLL_TRIM

    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

    press_frame = tlinewidgets.get_frame(x)
    trimmodes.set_exit_mode_func = set_default_edit_mode
    trimmodes.set_no_edit_mode_func = tworoll_trim_no_edit_init
    success = trimmodes.set_tworoll_mode(track, press_frame)
    return success

# ----------------------------------------------------- slide trim
def slide_trim_no_edit_init():
    stop_looping() # Stops looping 
    editorstate.edit_mode = editorstate.SLIDE_TRIM_NO_EDIT
    gui.editor_window.set_cursor_to_mode()
    tlinewidgets.set_edit_mode(None, None) # No overlays are drawn in this edit mode
    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

def slide_trim_no_edit_press(event, frame):
    success = slide_trim_mode_init(event.x, event.y)
    if success:
        if not editorpersistance.prefs.quick_enter_trims:
            global mouse_disabled
            tlinewidgets.trim_mode_in_non_active_state = True
            mouse_disabled = True
        else:
            trimmodes.edit_data["press_start"] = frame
            trimmodes.slide_trim_move(event.x, event.y, frame, None)
    else:
        if editorpersistance.prefs.empty_click_exits_trims == True:
            set_default_edit_mode(True)
        else:
            editorstate.edit_mode = editorstate.SLIDE_TRIM_NO_EDIT
    
def slide_trim_no_edit_move(x, y, frame, state):
    pass
    
def slide_trim_no_edit_release(x, y, frame, state):
    pass

def slide_trim_mode_init(x, y):
    """
    User selects two roll mode
    """
    track = tlinewidgets.get_track(y)
    if track == None:
        return False
    
    if track_lock_check_and_user_info(track, tworoll_trim_mode_init, "two roll trim mode"):
        set_default_edit_mode()
        return False

    stop_looping()
    editorstate.edit_mode = editorstate.SLIDE_TRIM

    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

    press_frame = tlinewidgets.get_frame(x)
    trimmodes.set_exit_mode_func = set_default_edit_mode
    trimmodes.set_no_edit_mode_func = slide_trim_no_edit_init
    success = trimmodes.set_slide_mode(track, press_frame)
    return success


# ------------------------------------ timeline mouse events
def tline_canvas_mouse_pressed(event, frame):
    """
    Mouse event callback from timeline canvas widget
    """
    global mouse_disabled

    if PLAYER().looping():
        return
    elif PLAYER().is_playing():
        PLAYER().stop_playback()
    
    # Double click handled separately
    if event.type == gtk.gdk._2BUTTON_PRESS:
        return

    # Handle and exit parent clip selecting
    if EDIT_MODE() == editorstate.SELECT_PARENT_CLIP:
        syncsplitevent.select_sync_parent_mouse_pressed(event, frame)
        mouse_disabled = True
        # Set INSERT_MODE
        set_default_edit_mode()  
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
            mouse_disabled == True
            # Right mouse + CTRL displays clip menu if we hit clip
            if (event.state & gtk.gdk.CONTROL_MASK):
                PLAYER().seek_frame(frame)
            # Right mouse on timeline seeks frame
            else:
                success = display_clip_menu_pop_up(event.y, event, frame)
                if not success:
                    PLAYER().seek_frame(frame)
        return

    #  Check if compositor is hit and if so handle compositor editing
    if editorstate.current_is_move_mode() and timeline_visible():
        hit_compositor = tlinewidgets.compositor_hit(frame, event.y, current_sequence().compositors)
        if hit_compositor != None:
            movemodes.clear_selected_clips()
            if event.button == 1:
                compositormodes.set_compositor_mode(hit_compositor)
                mode_funcs = EDIT_MODE_FUNCS[editorstate.COMPOSITOR_EDIT]
                press_func = mode_funcs[TL_MOUSE_PRESS]
                press_func(event, frame)
            elif event.button == 3:
                mouse_disabled == True
                compositormodes.set_compositor_selected(hit_compositor)
                guicomponents.display_compositor_popup_menu(event, hit_compositor,
                                                            compositor_menu_item_activated)
            elif event.button == 2:
                updater.zoom_project_length()
            return

    compositormodes.clear_compositor_selection()

    # Handle mouse button presses depending which button was pressed and
    # editor state.
    # RIGHT BUTTON: seek frame or display clip menu
    if (event.button == 3):
        if ((not editorstate.current_is_active_trim_mode()) and timeline_visible()):
            if not(event.state & gtk.gdk.CONTROL_MASK):
                success = display_clip_menu_pop_up(event.y, event, frame)
                if not success:
                    PLAYER().seek_frame(frame)
            else:
                PLAYER().seek_frame(frame) 
        else:
            # For trim modes set <X>_NO_EDIT edit mode and seek frame. and seek frame
            trimmodes.set_no_edit_trim_mode()
            PLAYER().seek_frame(frame)
        return
    # LEFT BUTTON + CTRL: Select new trimmed clip in one roll trim mode
    elif (event.button == 1 
          and (event.state & gtk.gdk.CONTROL_MASK)
          and EDIT_MODE() == editorstate.ONE_ROLL_TRIM):
        track = tlinewidgets.get_track(event.y)
        if track == None:
            if editorpersistance.prefs.empty_click_exits_trims == True:
                set_default_edit_mode(True)
            return
        success = trimmodes.set_oneroll_mode(track, frame)
        if (not success) and editorpersistance.prefs.empty_click_exits_trims == True:
            set_default_edit_mode(True)
            return
        gui.editor_window.set_cursor_to_mode()
        gui.editor_window.set_mode_selector_to_mode()
        if not editorpersistance.prefs.quick_enter_trims:
            mouse_disabled = True
        else:
            trimmodes.oneroll_trim_move(event.x, event.y, frame, None)
    # LEFT BUTTON + CTRL: Select new trimmed clip in two roll trim mode
    elif (event.button == 1 
          and (event.state & gtk.gdk.CONTROL_MASK)
          and EDIT_MODE() == editorstate.TWO_ROLL_TRIM):
        track = tlinewidgets.get_track(event.y)
        if track == None:
            if editorpersistance.prefs.empty_click_exits_trims == True:
                set_default_edit_mode(True)
            return
        success = trimmodes.set_tworoll_mode(track, frame)
        if (not success) and  editorpersistance.prefs.empty_click_exits_trims == True:
            set_default_edit_mode(True)
            return
        if not editorpersistance.prefs.quick_enter_trims:
            mouse_disabled = True
        else:
            trimmodes.tworoll_trim_move(event.x, event.y, frame, None)
    # LEFT BUTTON: Handle left mouse button edits by passing event to current edit mode
    # handler func
    elif event.button == 1:
        mode_funcs = EDIT_MODE_FUNCS[EDIT_MODE()]
        press_func = mode_funcs[TL_MOUSE_PRESS]
        press_func(event, frame)
    elif event.button == 2:
        updater.zoom_project_length()

def tline_canvas_mouse_moved(x, y, frame, button, state):
    """
    Mouse event callback from timeline canvas widget
    """
    # Refuse mouse events for some editor states.
    if PLAYER().looping():
        return        
    if mouse_disabled == True:
        return
    if not timeline_visible():
        return

    # Handle timeline position setting with right mouse button
    if button == 3:
        if not timeline_visible():
            return
        PLAYER().seek_frame(frame)
    # Handle left mouse button edits
    elif button == 1:
        mode_funcs = EDIT_MODE_FUNCS[EDIT_MODE()]
        move_func = mode_funcs[TL_MOUSE_MOVE]
        move_func(x, y, frame, state)

def tline_canvas_mouse_released(x, y, frame, button, state):
    """
    Mouse event callback from timeline canvas widget
    """
    gui.editor_window.set_cursor_to_mode()
     
    global mouse_disabled
    if mouse_disabled == True:
        gui.editor_window.set_cursor_to_mode() # we only need this update when mode change (to active trim mode) disables mouse, so we'll only do this then
        tlinewidgets.trim_mode_in_non_active_state = False # we only need this update when mode change (to active trim mode) disables mouse, so we'll only do this then
        gui.tline_canvas.widget.queue_draw()
        mouse_disabled = False
        return

    if not timeline_visible():
        return
        
    if PLAYER().looping():
        PLAYER().stop_loop_playback(trimmodes.trim_looping_stopped)
        return

    # Handle timeline position setting with right mouse button
    if button == 3:
        #if not editorstate.current_is_move_mode():
        #    return
        if not timeline_visible():
            return
        PLAYER().seek_frame(frame) 
    # Handle left mouse button edits
    elif button == 1:
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
        set_default_edit_mode()
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
        set_default_edit_mode()
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
        set_default_edit_mode()
        return

    set_default_edit_mode()

    frame = tlinewidgets.get_frame(x)
    
    # Create new clip.
    if media_file.type != appconsts.PATTERN_PRODUCER:
        new_clip = current_sequence().create_file_producer_clip(media_file.path, media_file.name)
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
            
    do_clip_insert(track, new_clip, frame)

def tline_range_item_drop(rows, x, y):
    track = tlinewidgets.get_track(y)
    if track == None:
        return
    if track.id < 1 or track.id >= (len(current_sequence().tracks) - 1):
        return 
    if track_lock_check_and_user_info(track):
        set_default_edit_mode()
        return
        
    frame = tlinewidgets.get_frame(x)
    clips = medialog.get_clips_for_rows(rows)
    set_default_edit_mode()
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
ONE_ROLL_TRIM_NO_EDIT_FUNCS = [oneroll_trim_no_edit_press, 
                               oneroll_trim_no_edit_move,
                               oneroll_trim_no_edit_release]
TWO_ROLL_TRIM_FUNCS = [trimmodes.tworoll_trim_press,
                       trimmodes.tworoll_trim_move,
                       trimmodes.tworoll_trim_release]
TWO_ROLL_TRIM_NO_EDIT_FUNCS = [tworoll_trim_no_edit_press,
                               tworoll_trim_no_edit_move,
                               tworoll_trim_no_edit_release]
COMPOSITOR_EDIT_FUNCS = [compositormodes.mouse_press,
                         compositormodes.mouse_move,
                         compositormodes.mouse_release]
SLIDE_TRIM_FUNCS = [trimmodes.slide_trim_press,
                    trimmodes.slide_trim_move,
                    trimmodes.slide_trim_release]
SLIDE_TRIM_NO_EDIT_FUNCS = [slide_trim_no_edit_press,
                            slide_trim_no_edit_move,
                            slide_trim_no_edit_release]
MULTI_MOVE_FUNCS = [multimovemode.mouse_press,
                    multimovemode.mouse_move,
                    multimovemode.mouse_release]
                        
# (mode - mouse handler function list) table
EDIT_MODE_FUNCS = {editorstate.INSERT_MOVE:INSERT_MOVE_FUNCS,
                   editorstate.OVERWRITE_MOVE:OVERWRITE_MOVE_FUNCS,
                   editorstate.ONE_ROLL_TRIM:ONE_ROLL_TRIM_FUNCS,
                   editorstate.TWO_ROLL_TRIM:TWO_ROLL_TRIM_FUNCS,
                   editorstate.COMPOSITOR_EDIT:COMPOSITOR_EDIT_FUNCS,
                   editorstate.ONE_ROLL_TRIM_NO_EDIT:ONE_ROLL_TRIM_NO_EDIT_FUNCS,
                   editorstate.TWO_ROLL_TRIM_NO_EDIT:TWO_ROLL_TRIM_NO_EDIT_FUNCS,
                   editorstate.SLIDE_TRIM:SLIDE_TRIM_FUNCS,
                   editorstate.SLIDE_TRIM_NO_EDIT:SLIDE_TRIM_NO_EDIT_FUNCS,
                   editorstate.MULTI_MOVE:MULTI_MOVE_FUNCS}

