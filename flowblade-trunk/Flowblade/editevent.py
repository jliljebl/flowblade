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
Handles (most) events that are done to edit current sequence.

Module updates current sequence data and calls GUI updates after edits are complete.

Handles edit mode setting.

Module passes mouse edit events to other modules, depending on current edit mode.
"""
import gtk

import appconsts
import audiowaveform
import clipeffectseditor
import compositeeditor
import compositormodes
import dialogs
import edit
import editorstate
from editorstate import current_sequence
from editorstate import get_track
from editorstate import PROJECT
from editorstate import PLAYER
from editorstate import timeline_visible
from editorstate import EDIT_MODE
import gui
import guicomponents
import mltfilters
import mlttransitions
import movemodes
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


# ----------------------------- module funcs
def do_clip_insert(track, new_clip, tline_pos):
    """
    Called from buttonevent.insert_button_pressed() and tline_media_drop()
    """
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

    # Can't put audio media on video track 
    if ((new_clip.media_type == appconsts.AUDIO)
       and (track.type == appconsts.VIDEO)):        
        dialogs.warning_message(_("Can't put an audio clip on a video track."), 
                                _("Track ")+ utils.get_track_name(track, current_sequence()) + _(" is a video track and can't display audio only material."),
                                gui.editor_window.window)
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

# --------------------------------- undo, redo
def do_undo(widget=None, data=None):
    undo.do_undo()
    updater.repaint_tline()
    
def do_redo(widget=None, data=None):
    undo.do_redo()
    updater.repaint_tline()

# ------------------------------------- edit mode setting
def set_default_edit_mode():
    """
    This is used as global 'go to start position' exit door from
    situations where for example user is in trim and exits it
    without specifying which edit mode to go to.
    
    NOTE: As this uses 'programmed click', this method does nothing if insert mode button
    is already down.
    """
    updater.set_mode_button_active(editorstate.INSERT_MOVE)
    
def exit_trimmodes():
    # Stop trim mode looping using trimmodes.py methods for it
    # Called when entering move modes.
    if PLAYER().looping():
        if EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
            trimmodes.oneroll_stop_pressed()
        if EDIT_MODE() == editorstate.TWO_ROLL_TRIM: 
            trimmodes.tworoll_stop_pressed()

def insert_move_mode_pressed():
    """
    User selects insert move mode.
    """
    exit_trimmodes()
    current_sequence().clear_hidden_track()

    editorstate.edit_mode = editorstate.INSERT_MOVE
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_insert_overlay)

    _set_move_mode()

def overwrite_move_mode_pressed():
    """
    User selects overwrite move mode.
    """
    exit_trimmodes()
    current_sequence().clear_hidden_track()

    editorstate.edit_mode = editorstate.OVERWRITE_MOVE
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_overwrite_overlay)

    _set_move_mode()

def oneroll_trim_mode_pressed():
    """
    User selects one roll mode
    """
    track = current_sequence().get_first_active_track()
    if track == None:
        return

    if track_lock_check_and_user_info(track, oneroll_trim_mode_pressed, "one roll trim mode"):
        set_default_edit_mode()
        return
    
    exit_trimmodes() # Stops looping 
    editorstate.edit_mode = editorstate.ONE_ROLL_TRIM

    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

    # init mode
    trimmodes.set_exit_mode_func = set_default_edit_mode
    trimmodes.set_oneroll_mode(track)

def tworoll_trim_mode_pressed():
    """
    User selects two roll mode
    """
    track = current_sequence().get_first_active_track()
    if track == None:
        return
    
    if track_lock_check_and_user_info(track, tworoll_trim_mode_pressed, "two roll trim mode",):
        set_default_edit_mode()
        return

    exit_trimmodes() # Stops looping 
    editorstate.edit_mode = editorstate.TWO_ROLL_TRIM

    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

    trimmodes.set_exit_mode_func = set_default_edit_mode
    trimmodes.launch_one_roll_trim = oneroll_trim_mode_pressed
    trimmodes.set_tworoll_mode(track)

def _set_move_mode():
    updater.set_move_mode_gui()
    updater.repaint_tline()


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
        # Set INSERT_MODE with programmed click if insert mode button not down
        # and just calling the mode intilizing  method if button is already pressed
        if  gui.mode_buttons[0].get_active() == False:
            set_default_edit_mode()  
        else:
            insert_move_mode_pressed() 
        return
        
    # Hitting timeline in clip display mode displays timeline in
    # default mode.
    if not timeline_visible():
        updater.display_sequence_in_monitor()
        set_default_edit_mode()
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
                success = _display_clip_menu(event.y, event, frame)
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
                                                            _compositor_menu_item_activated)
            return

    compositormodes.clear_compositor_selection()

    # Handle mouse button presses depending which button was pressed and
    # editor state.
    # RIGHT BUTTON: seek frame or display clip menu
    if (event.button == 3):
        if (editorstate.current_is_move_mode()
            and timeline_visible()):
            # Do seek or clip menu display(if ctrl pressed)
            if not(event.state & gtk.gdk.CONTROL_MASK):
                success = _display_clip_menu(event.y, event, frame)
                if not success:
                    PLAYER().seek_frame(frame)
            else:
                PLAYER().seek_frame(frame) 
        else:
            # Display default editorstate and seek frame
            mouse_disabled == True
            set_default_edit_mode()
            PLAYER().seek_frame(frame)
        return
    # LEFT BUTTON + CTRL: Select new trimmed clip in one roll trim mode
    elif (event.button == 1 
          and (event.state & gtk.gdk.CONTROL_MASK)
          and EDIT_MODE() == editorstate.ONE_ROLL_TRIM):
        track = tlinewidgets.get_track(event.y)
        if track == None:
            return
        trimmodes.set_oneroll_mode(track, frame)
        mouse_disabled = True
    # LEFT BUTTON + CTRL: Select new trimmed clip in two roll trim mode
    elif (event.button == 1 
          and (event.state & gtk.gdk.CONTROL_MASK)
          and EDIT_MODE() == editorstate.TWO_ROLL_TRIM):
        track = tlinewidgets.get_track(event.y)
        if track == None:
            return
        trimmodes.set_tworoll_mode(track, frame)
        mouse_disabled = True
    # LEFT BUTTON: Handle left mouse button edits by passing event to current edit mode
    # handler func
    elif event.button == 1:
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
    if mouse_disabled == True:
        return
    if not timeline_visible():
        return

    #Handle timeline position setting with right mouse button
    if button == 3:
        if not editorstate.current_is_move_mode():
            return
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
    global mouse_disabled
    if mouse_disabled == True:
        mouse_disabled = False
        return

    if not timeline_visible():
        return
        
    if PLAYER().looping():
        PLAYER().stop_loop_playback(trimmodes.trim_looping_stopped)
        return

    # Handle timeline position setting with right mouse button
    if button == 3:
        if not editorstate.current_is_move_mode():
            return
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
    _open_clip_in_effects_editor(data)

# -------------------------------------------------- DND release event callbacks
def tline_effect_drop(x, y):
    clip, track, index = tlinewidgets.get_clip_track_and_index_for_pos(x, y)
    if clip == None:
        return

    if clip != clipeffectseditor.clip:
        clipeffectseditor.set_clip(clip, track, index)
    
    clipeffectseditor.add_currently_selected_effect() # drag start selects the dragged effect

def tline_media_drop(media_file, x, y):
    track = tlinewidgets.get_track(y)
    if track == None:
        return
    if track.id < 1 or track.id >= (len(current_sequence().tracks) - 1):
        return 

    set_default_edit_mode()

    frame = tlinewidgets.get_frame(x)
    
    # Create new clip.
    if media_file.type != appconsts.PATTERN_PRODUCER:
        new_clip = current_sequence().create_file_producer_clip(media_file.path, media_file.name)
    else:
        new_clip = current_sequence().create_pattern_producer(media_file)
    new_clip.mark_in = 0
    new_clip.mark_out = new_clip.get_length() - 1 # - 1 because out is mark_out inclusive

    do_clip_insert(track, new_clip, frame)


# ---------------------------------- clip menu
def _display_clip_menu(y, event, frame):
    # See if we actually hit a clip
    track = tlinewidgets.get_track(y)
    if track == None:
        return False
    clip_index = current_sequence().get_clip_index(track, frame)
    if clip_index == -1:
        return False
    # Can't do anything to clips in locked tracks
    if track_lock_check_and_user_info(track, _display_clip_menu, "clip context menu"):
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
            # INFOWINDOW
            return
        clip_index = track.clips.index(origin_clip)
        clip_start = track.clip_start(clip_index)
        clip_end = clip_start + origin_clip.clip_out - origin_clip.clip_in
        data = {"compositor":compositor,"clip_in":clip_start,"clip_out":clip_end}
        action = edit.move_compositor_action(data)
        action.do_edit()

def _open_clip_in_effects_editor(data):
    clip, track, item_id, x = data
    frame = tlinewidgets.get_frame(x)
    index = current_sequence().get_clip_index(track, frame)
    
    clipeffectseditor.set_clip(clip, track, index)
    
def _open_clip_in_clip_monitor(data):
    clip, track, item_id, x = data
    
    media_file = PROJECT().get_media_file_for_path(clip.path)    
    updater.set_and_display_monitor_media_file(media_file)
    gui.pos_bar.widget.grab_focus()

def _show_clip_info(data):
    clip, track, item_id, x = data
    
    width = clip.get("width")
    height = clip.get("height")
    size = str(width) + " x " + str(height)
    l_frames = clip.clip_out - clip.clip_in + 1 # +1 out inclusive
    length = utils.get_tc_string(l_frames)
    
    dialogs.clip_properties_dialog((length, size, clip.path))
    
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
    x, compositor_index = item_data
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
                "compositor_index":compositor_index}
    action = edit.add_compositor_action(edit_data)
    action.do_edit()
    
    updater.repaint_tline()

def _add_blender(data):
    clip, track, item_id, item_data = data
    x, blender_index = item_data
    compositor_index = blender_index + len(mlttransitions.compositors) # see mlttransitions.create_compositor()
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
                "compositor_index":compositor_index}
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

def _mute_track(track, new_mute_state):
    # NOTE: THIS IS EDITOR STATE CHANGE, NOT AN UNDOABLE EDIT

    current_sequence().set_track_mute_state(track.id, new_mute_state)
    gui.tline_column.widget.queue_draw()

# ---------------------------------- tracks
def add_track():
    dialogs.track_add_dialog(_add_track_callback)
    
def _add_track_callback(dialog, response_id, side_combo):
    dialog.destroy()
    
    if response_id == gtk.RESPONSE_ACCEPT:
        if side_combo.get_active() == 0:
            track_type = appconsts.VIDEO
        else:
            track_type = appconsts.AUDIO

        current_sequence().user_add_new_track(track_type)            
        add_index = len(current_sequence().tracks) - 1
        get_track(add_index).height = appconsts.TRACK_HEIGHT_SMALL
        updater.window_resized() # Recaculates and draws timeline.
        gui.tline_column.widget.queue_draw()

def delete_track():
    deletable_indexes = [] # A1 or V1 can't be deleted
    for i in range(1, current_sequence().first_video_index - 1):
        deletable_indexes.append(i)
    for i in range(current_sequence().first_video_index + 1, len(current_sequence().tracks) - 1):
        deletable_indexes.append(i)

    deletable_indexes.reverse()
    dialogs.track_delete_dialog(_delete_track_callback, current_sequence(), deletable_indexes)

def _delete_track_callback(dialog, response_id, deletable_track_indexes, combo_box):
    selected = combo_box.get_active()
    dialog.destroy()

    if response_id == gtk.RESPONSE_ACCEPT:
        del_index = deletable_track_indexes[selected]
        edit.delete_sync_relations_from_track(get_track(del_index))
        current_sequence().delete_track(del_index)
        if del_index < current_sequence().first_video_index:
            # audio track was deleted
            current_sequence().first_video_index -= 1        
        updater.window_resized() # This does the needed recaculating and draws timeline.
        gui.tline_column.widget.queue_draw()
        
def track_active_switch_pressed(data):
    track = get_track(data.track) # data.track is index, not object

    # Flip active state
    if data.event.button == 1:
        track.active = (track.active == False)
        if current_sequence().all_tracks_off() == True:
            track.active = True
        gui.tline_column.widget.queue_draw()
    elif data.event.button == 3:
        guicomponents.display_tracks_popup_menu(data.event, data.track, \
                                                _track_menu_item_activated)

def track_mute_switch_pressed(data):
    if data.event.button == 1:
        current_sequence().next_mute_state(data.track) # data.track is index, not object
        gui.tline_column.widget.queue_draw()
    elif data.event.button == 3:
        guicomponents.display_tracks_popup_menu(data.event, data.track, \
                                                _track_menu_item_activated)

def track_center_pressed(data):
    if data.event.button == 3:
        guicomponents.display_tracks_popup_menu(data.event, data.track, \
                                                _track_menu_item_activated)

def _track_menu_item_activated(widget, data):
    track, item_id, selection_data = data
    handler = POPUP_HANDLERS[item_id]
    if selection_data == None:
        handler(track)
    else:
        handler(track, selection_data)

def _lock_track(track_index):
    track = get_track(track_index)
    if track.edit_freedom == appconsts.SYNC_LOCKED:
        _handle_sync_leave()
    track.edit_freedom = appconsts.LOCKED
    updater.repaint_tline()
    
def _unlock_track(track_index):
    track = get_track(track_index)
    track.edit_freedom = appconsts.FREE
    updater.repaint_tline()
    
def _sync_lock_track(track_index):
    track = get_track(track_index)
    track.edit_freedom = appconsts.SYNC_LOCKED
    updater.repaint_tline()

def _set_track_normal_height(track_index):
    track = get_track(track_index)
    track.height = appconsts.TRACK_HEIGHT_NORMAL
    
    # Check that new height tracks can be displayed and cancel if not.
    new_h = current_sequence().get_tracks_height()
    x, y, w, h = gui.tline_canvas.widget.allocation
    if new_h > h:
        track.height = appconsts.TRACK_HEIGHT_SMALL
        dialogs.warning_message(_("Not enough vertical space on Timeline to expand track"), 
                                _("Maximize or resize application window to get more\nspace for tracks if possible."),
                                gui.editor_window.window,
                                True)
        return
    
    
    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.allocation)
    gui.tline_column.init_listeners()
    audiowaveform.maybe_delete_waveforms(track.clips, track)
    updater.repaint_tline()

def _set_track_small_height(track_index):
    track = get_track(track_index)
    track.height = appconsts.TRACK_HEIGHT_SMALL
    
    tlinewidgets.set_ref_line_y(gui.tline_canvas.widget.allocation)
    gui.tline_column.init_listeners()
    audiowaveform.maybe_delete_waveforms(track.clips, track)
    updater.repaint_tline()

def _consolidate_blanks_from_popup(data):
    clip, track, item_id, item_data = data
    movemodes.select_blank_range(track, clip)    
    consolidate_selected_blanks()
    
def consolidate_selected_blanks():
    if movemodes.selected_track == -1:
        # INFOWINDOW
        return
    track = get_track(movemodes.selected_track)
    if track.clips[movemodes.selected_range_in].is_blanck_clip != True:
        return
    index = movemodes.selected_range_in
    movemodes.clear_selected_clips()
    data = {"track":track, "index":index}
    action = edit.consolidate_selected_blanks(data)
    action.do_edit()

    updater.repaint_tline()

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
        # INFOWINDOW
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
        # INFOWINDOW
        return 

    # Do edit
    movemodes.clear_selected_clips()
    data = {"track":track, "clip":cover_clip, "blank_index":blank_index}
    action = edit.trim_start_over_blanks(data)
    action.do_edit()
                  
def consolidate_all_blanks():
    action = edit.consolidate_all_blanks({})
    action.do_edit()

    updater.repaint_tline()

# ------------------------------------ menu selection edits
def clear_selection():
    movemodes.clear_selected_clips()
    updater.repaint_tline()
    
def track_selection_activated(widget, track_index):
    end_index = len(get_track(track_index).clips) - 1
    movemodes._select_multiple_clips(track_index, 0, end_index)
    updater.repaint_tline()

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

# ---------------------------------- create clips
def create_color_clip():
    dialogs.color_clip_dialog(_create_color_clip_callback)

def _create_color_clip_callback(dialog, response_id, widgets):
    if response_id == gtk.RESPONSE_ACCEPT:
        entry, color_button = widgets
        name = entry.get_text()
        color_str = color_button.get_color().to_string()
        
        PROJECT().add_color_clip(name, color_str)

        gui.media_list_view.fill_data_model()
        gui.bin_list_view.fill_data_model()

    dialog.destroy()

# ------------------------------------ track locks handling
def track_lock_check_and_user_info(track, calling_function, actionname):

    if track.edit_freedom == appconsts.LOCKED:
        track_name = utils.get_track_name(track, current_sequence())

        # entering trim modes is forbidden for locked tracks
        if ((calling_function == oneroll_trim_mode_pressed)
            or (calling_function == tworoll_trim_mode_pressed)):
            
            primary_txt = _("Can't enter ") + actioname + _(" on a locked track")
            secondary_txt = _("Track ") + track_name + _(" is locked. Unlock track to edit it.")
            dialogs.warning_message(primary_txt, secondary_txt, gui.editor_window.window)
            return True
            
        # No edits on locked tracks.
        primary_txt = _("Can't do ") + actioname + _(" edit on a locked track")
        secondary_txt = _("Track ") + track_name + _(" is locked. Unlock track to edit it.")
        dialogs.warning_message(primary_txt, secondary_txt, gui.editor_window.window)
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
TWO_ROLL_TRIM_FUNCS = [trimmodes.tworoll_trim_press,
                       trimmodes.tworoll_trim_move,
                       trimmodes.tworoll_trim_release]
COMPOSITOR_EDIT_FUNCS = [compositormodes.mouse_press,
                         compositormodes.mouse_move,
                         compositormodes.mouse_release]
                    
# (mode - mouse handler function list) table
EDIT_MODE_FUNCS = {editorstate.INSERT_MOVE:INSERT_MOVE_FUNCS,
                   editorstate.OVERWRITE_MOVE:OVERWRITE_MOVE_FUNCS,
                   editorstate.ONE_ROLL_TRIM:ONE_ROLL_TRIM_FUNCS,
                   editorstate.TWO_ROLL_TRIM:TWO_ROLL_TRIM_FUNCS,
                   editorstate.COMPOSITOR_EDIT:COMPOSITOR_EDIT_FUNCS}
              
# Functions to handle popup menu selections for strings 
# set as activation messages in guicomponents.py
# activation_message : _handler_func
POPUP_HANDLERS = {"lock":_lock_track,
                  "unlock":_unlock_track,
                  "sync_lock":_sync_lock_track,
                  "normal_height":_set_track_normal_height,
                  "small_height":_set_track_small_height,
                  "set_master":syncsplitevent.init_select_master_clip,
                  "open_in_editor":_open_clip_in_effects_editor,
                  "clip_info":_show_clip_info,
                  "open_in_clip_monitor":_open_clip_in_clip_monitor,
                  "split_audio":syncsplitevent.split_audio,
                  "split_audio_synched":syncsplitevent.split_audio_synched,
                  "resync":syncsplitevent.resync_clip,
                  "add_filter":_add_filter,
                  "add_compositor":_add_compositor,
                  "add_blender":_add_blender,
                  "clear_sync_rel":syncsplitevent.clear_sync_relation,
                  "mute_clip":_mute_clip,
                  "mute_track":_mute_track,
                  "display_waveform":_display_wavefrom,
                  "clear_waveform":_clear_waveform,
                  "delete_blank":_delete_blank,
                  "comsolidate_blanks":_consolidate_blanks_from_popup,
                  "cover_with_prev": _cover_blank_from_prev,
                  "cover_with_next": _cover_blank_from_next,
                  "clone_filters_from_next": _clone_filters_from_next,
                  "clone_filters_from_prev": _clone_filters_from_prev}

