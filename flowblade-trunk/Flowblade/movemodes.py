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
Module handles user edit events for insert and over move modes. 
"""
import pygtk
pygtk.require('2.0');
import gtk


import appconsts
import dialogutils
import dnd
import edit
from editorstate import current_sequence
from editorstate import get_track
from editorstate import PLAYER
import gui
import updater
import tlinewidgets
import utils

# Mouse delta in pix needed before selection is interpreted as move.
MOVE_START_LIMIT = 5

# Width of area in pixels that is iterpreted as an attemp to place overwrite 
# clips, starting from edit
MAGNETIC_AREA_IN_PIX = 5

# Selected clips in timeline.
# Selection handling is part of this module because 
# selections can only be done when editing in move modes.
# Therea are no area or multitrack selections in this application.
selected_track = -1
selected_range_in = -1 # clip index 
selected_range_out = -1 # clip index, inclusive

# Flag for clearing selection when releasing after pressing on selected.
pressed_on_selected = True

# Blanck clips can be selected but not moved
drag_disabled = False

# Data/state for ongoing edit.
edit_data = None

#------------------------------ playback control
# These four buttons act differently in trimmodes and move modes
def play_pressed():
    # This handles only move modes, see trimmodes.py module for others.
    PLAYER().start_playback()  

def stop_pressed():
    # This handles only move modes, see trimmodes.py module for others.
    PLAYER().stop_playback() 
   
def prev_pressed():
    # This handles only move modes, see trimmodes.py module for others.
    PLAYER().seek_delta(-1)

def next_pressed():
    # This handles only movemodes, see trimmodes.py module for others.
    PLAYER().seek_delta(1)

# ----------------------------------- selection handling
def clear_selected_clips():
    if not selected_track == -1:
        set_range_selection(selected_track, selected_range_in, \
                             selected_range_out, False)

    clear_selection_values()

def clear_selection_values():
    global selected_track, selected_range_in, selected_range_out
    selected_track = -1
    selected_range_in = -1
    selected_range_out = -1
    
    updater.set_transition_render_edit_menu_items_sensitive(selected_range_in, selected_range_out)

def set_range_selection(track_index, range_in, range_out, is_selected):
    """
    Sets range of clips in track to selection value.
    """
    track = get_track(track_index)
    for i in range(range_in, range_out + 1): #+1, range_out is inclusive
        track.clips[i].selected = is_selected
    

def select_clip(track_index, clip_index):
    """
    Selects single clip.
    """
    clear_selected_clips()
    set_range_selection(track_index, clip_index, clip_index, True)
    updater.set_transition_render_edit_menu_items_sensitive(clip_index, clip_index)
    
    global selected_track, selected_range_in, selected_range_out
    selected_track = track_index
    selected_range_in = clip_index
    selected_range_out = clip_index

def _select_multiple_clips(track_index, range_start, range_end):
    """
    Selects continuous range of clips.
    """
    clear_selected_clips()
    set_range_selection(track_index, range_start, range_end, True)
    updater.set_transition_render_edit_menu_items_sensitive(range_start, range_end)

    global selected_track, selected_range_in, selected_range_out
    selected_track = track_index
    selected_range_in = range_start
    selected_range_out = range_end

def _get_blanck_range(track, clip_index):
    # look backwards
    start_index = _get_blanck_range_limit(track, clip_index, -1)

    # Look forward
    end_index = _get_blanck_range_limit(track, start_index, 1) 
    return (start_index, end_index)
    
def _get_blanck_range_limit(track, clip_index, delta):
    try:
        while track.clips[clip_index].is_blanck_clip:
            clip_index += delta
            if clip_index < 0: # It'll start looping from end other wise
                return 0
    except:
        pass
    
    return clip_index - delta

def select_blank_range(track, clip):
    clip_index = track.clips.index(clip)
    range_in, range_out = _get_blanck_range(track, clip_index)
    _select_multiple_clips(track.id, range_in, range_out)
            
# --------------------------------- INSERT MOVE EVENTS
def insert_move_press(event, frame):
    """
    User presses mouse when in insert move mode.
    """
    _move_mode_pressed(event, frame)
    
def insert_move_move(x, y, frame, state):
    """
    User moves mouse when in insert move mode.
    """
    global edit_data, drag_disabled
    
    if drag_disabled:
        return

    if edit_data == None:
        return

    _move_mode_move(frame, x, y)
    
    updater.repaint_tline()

def insert_move_release(x, y, frame, state):
    """
    User releases mouse when in insert move mode.
    """
    global edit_data, drag_disabled
    
    if drag_disabled:
        drag_disabled = False
        return

    # If mouse was not pressed on clip we cant move anyhing
    if edit_data == None:
        return

    # Get attempt insert frame
    press_frame = edit_data["press_frame"]
    first_clip_start = edit_data["first_clip_start"]
    attempt_insert_frame = first_clip_start + (frame - press_frame)
    
    # Get tracks and insert index
    track = edit_data["track_object"]
    to_track = edit_data["to_track_object"]
    insert_index = to_track.get_clip_index_at(attempt_insert_frame)
    
    # Check locking of target track. Source track checked at press event.
    if _track_is_locked(to_track):
        edit_data = None
        tlinewidgets.set_edit_mode_data(edit_data)
        updater.repaint_tline()
        return

    # Update data for editmode overlay
    edit_data["current_frame"] = frame
    edit_data["insert_frame"] = track.clip_start(insert_index)

    # Collect selection data
    range_in = edit_data["selected_range_in"]
    range_out = edit_data["selected_range_out"]
    
    data = {"track":track,
            "insert_index":insert_index,
            "selected_range_in":range_in,
            "selected_range_out":range_out,
            "move_edit_done_func":move_edit_done}
    
    # Do edit. Use different actions depending on if 
    # clip is moved to a differrent track
    if track == to_track:
        # Do edit if were moving and insert is not into same index
        # Update selection after edit
        if (edit_data["move_on"] == True
            and (insert_index < selected_range_in
            or insert_index > selected_range_out)):
            # Remeber selected range to later find index of dropped range
            # after edit
            old_range_length = selected_range_out - selected_range_in
            clear_selected_clips()
            action = edit.insert_move_action(data)
            action.do_edit()
            # Move playback to first frame of dropped range
            select_index = insert_index
            if (range_in < insert_index):#when moving forward clips are removed affecting later indexes
                select_index = insert_index - (old_range_length + 1)
            PLAYER().seek_frame(track.clip_start(select_index), False)
        else:
            _move_mode_released()
    else: # insert to different track 
        data["to_track"] = to_track
        clear_selected_clips()
        action = edit.multitrack_insert_move_action(data)
        action.do_edit()
        PLAYER().seek_frame(to_track.clip_start(insert_index), False)

    # Clear edit mode data
    edit_data = None
    tlinewidgets.set_edit_mode_data(edit_data)
    
    updater.repaint_tline()

# --------------------------------- OVERWRITE MOVE EVENTS
def overwrite_move_press(event, frame):
    """
    User presses mouse when in overwrite move mode.
    """
    _move_mode_pressed(event, frame)
    
    global edit_data
    if (not(edit_data == None)):
        edit_data["over_in"] = -1
        edit_data["over_out"] = -1
        
        # Length of moving clip/s
        moving_length = 0
        clip_lengths = edit_data["clip_lengths"] 
        for length in clip_lengths:
            moving_length += length
        edit_data["moving_length"] = moving_length

def overwrite_move_move(x, y, frame, state):
    """
    User moves mouse when in overwrite move mode.
    """
    global edit_data, drag_disabled    
    if drag_disabled:
        return 
    if edit_data == None:
        return

    _move_mode_move(frame, x, y)

    # Calculate overwrite area if moving
    if edit_data["move_on"] == True:
        # get in point
        over_in = edit_data["attempt_insert_frame"]
        
        # Check and do magnet
        cut_x = tlinewidgets._get_frame_x(edit_data["insert_frame"])
        clip_head_x = tlinewidgets._get_frame_x(edit_data["attempt_insert_frame"])
        if abs(clip_head_x - cut_x) < MAGNETIC_AREA_IN_PIX:
            over_in = edit_data["insert_frame"]

        over_out = over_in + edit_data["moving_length"] 

        edit_data["over_in"] = over_in
        edit_data["over_out"] = over_out

    updater.repaint_tline()

def overwrite_move_release(x, y, frame, state):
    """
    User releases mouse when in overwrite move mode.
    """
    global edit_data, drag_disabled    
    if drag_disabled:
        drag_disabled = False
        return   
    if edit_data == None:
        return

    press_frame = edit_data["press_frame"]
    first_clip_start = edit_data["first_clip_start"]
    track = edit_data["track_object"]
    to_track = edit_data["to_track_object"]
    over_in = first_clip_start + (frame - press_frame)
    over_out = over_in + edit_data["moving_length"]
    
    # Check locking of target track. Source track checked at press event.
    if _track_is_locked(to_track):
        edit_data = None
        tlinewidgets.set_edit_mode_data(edit_data)
        updater.repaint_tline()
        return
    
    
    # Moved lips are completely out of displayable track area, can't do edit.
    if over_out  < 1:
        return
        
    # Autocorrect moved clips to be fully on displayable track area
    if over_in  < 0:
        over_out += abs(over_in)
        over_in = 0

    # Collect data for edit action 
    data = {"track":track,
            "over_in":over_in,
            "over_out":over_out,
            "selected_range_in":selected_range_in,
            "selected_range_out":selected_range_out,
            "move_edit_done_func":move_edit_done}
            
    # Do edit. Use different actions depending on if 
    # clip is moved to a differrent track
    if track == to_track:
        # Do edit if were moving and clips have moved
        if (edit_data["move_on"] == True and (press_frame != frame)):
            clear_selected_clips()
            action = edit.overwrite_move_action(data)
            action.do_edit()

            PLAYER().seek_frame(over_in, False)
        else:
            _move_mode_released()
    else: # Moved to different track
        data["to_track"] = to_track
        clear_selected_clips()
        action = edit.multitrack_overwrite_move_action(data)
        action.do_edit()

        PLAYER().seek_frame(over_in, False)

    # Clear edit mode data
    edit_data = None
    tlinewidgets.set_edit_mode_data(edit_data)
    
    updater.repaint_tline()


# ------------------------------------- MOVE MODES EVENTS
def _move_mode_pressed(event, frame):
    """
    User presses mouse when in a move mode.
    Initializes move mode edit action based on user action and state.
    """
    x = event.x
    y = event.y

    global edit_data, pressed_on_selected, drag_disabled

    # Clear edit data in gui module
    edit_data = None
    drag_disabled = False
    tlinewidgets.set_edit_mode_data(edit_data)
    
    # Get pressed track
    track = tlinewidgets.get_track(y)  

    # Selecting empty clears selection
    if track == None:
        clear_selected_clips()
        pressed_on_selected = False
        updater.repaint_tline()
        return    
    
    # Get pressed clip index
    clip_index = current_sequence().get_clip_index(track, frame)

    # Selecting empty clears selection
    if clip_index == -1:
        clear_selected_clips()
        pressed_on_selected = False
        updater.repaint_tline()
        return
        
    # Check locking for pressed track
    if _track_is_locked(track):
        clear_selected_clips()
        pressed_on_selected = False
        updater.repaint_tline()
        return

    pressed_clip = track.clips[clip_index]

    # Handle pressed clip according to current selection state
    # Case: no selected clips, select single clip
    if selected_track == -1:
        if not pressed_clip.is_blanck_clip:
            select_clip(track.id, clip_index)
            pressed_on_selected = False
        else: 
            # There may be multiple blank clips in area that for user
            # seems to a single blank area. All of these must be
            # selected together automatically or user will be exposed to
            # this impl. detail unnecesserarely.
            range_in, range_out = _get_blanck_range(track, clip_index)
            _select_multiple_clips(track.id, range_in, range_out)
            pressed_on_selected = False
            drag_disabled = True
    # case: CTRL or SHIFT down, combine selection with earlier selected clips 
    elif ((event.state & gtk.gdk.CONTROL_MASK) or (event.state & gtk.gdk.SHIFT_MASK)):
        # CTRL pressing blank clears selection
        if pressed_clip.is_blanck_clip:
            clear_selected_clips()
            pressed_on_selected = False
            updater.repaint_tline()
            return
        # clip before range, make it start
        if clip_index < selected_range_in:
            _select_multiple_clips(track.id, clip_index,
                                   selected_range_out)
            pressed_on_selected = False
        # clip after range, make it end
        elif clip_index > selected_range_out:
            _select_multiple_clips(track.id, selected_range_in, 
                                   clip_index)
            pressed_on_selected = False
        else:
            # Pressing on selected clip clears selection on release
            pressed_on_selected = True
    # case: new single clip pressed
    else:
        if selected_track != track.id:
            clear_selected_clips()
            select_clip(track.id, clip_index)
            pressed_on_selected = False
        else:
            if not pressed_clip.is_blanck_clip:
                # Pressing on selected clip keeps selection unchanged
                if clip_index < selected_range_in or clip_index > selected_range_out:
                    select_clip(track.id, clip_index)
                    pressed_on_selected = False
                # Pressing on non-selected clip clears current selection and selects newly selected clip
                else:
                    pressed_on_selected = True
            else:
                # Black clip, see comment above
                range_in, range_out = _get_blanck_range(track, clip_index)
                _select_multiple_clips(track.id, range_in, range_out)
                pressed_on_selected = False
                drag_disabled = True

    # Get length info on selected clips
    clip_lengths = []
    for i in range(selected_range_in, selected_range_out + 1):
        clip = track.clips[i]
        clip_lengths.append(clip.clip_out - clip.clip_in + 1)

    # Overwrite mode ignores this
    insert_frame = track.clip_start(selected_range_in)
    
    # Set edit mode data. This is not used unless mouse delta big enough
    # to initiate move.
    edit_data = {"track_id":track.id,
                 "track_object":track,
                 "to_track_object":track,
                 "move_on":False,
                 "press_frame":frame,
                 "current_frame":frame,
                 "first_clip_start":insert_frame,
                 "insert_frame":insert_frame,
                 "clip_lengths":clip_lengths,
                 "mouse_start_x":x,
                 "mouse_start_y":y,
                 "selected_range_in":selected_range_in,     # clip index
                 "selected_range_out":selected_range_out}    # clip index
    
    tlinewidgets.set_edit_mode_data(edit_data)
    updater.repaint_tline()
    
def _move_mode_move(frame, x, y):
    """
    Updates edit data needed for doing edit and drawing overlay 
    based on mouse movement.
    """
    global edit_data

    # Get frame that is the one where insert is attempted
    press_frame = edit_data["press_frame"]
    first_clip_start = edit_data["first_clip_start"]
    attempt_insert_frame = first_clip_start + (frame - press_frame)
    edit_data["attempt_insert_frame"] = attempt_insert_frame    
    
    # Get track where insert is attempted. Track selection forced into range of editable tracks.
    to_track = tlinewidgets.get_track(y)
    if to_track == None:
        if y > tlinewidgets.REF_LINE_Y:
            to_track = get_track(1)
        else:
            to_track = get_track(len(current_sequence().tracks) - 2)
    if to_track.id < 1:
        to_track = get_track(1)
    if to_track.id > len(current_sequence().tracks) - 2:
        to_track = get_track(len(current_sequence().tracks) - 2)
    edit_data["to_track_object"] = to_track

    # Get index for insert in target track
    insert_index = to_track.get_clip_index_at(attempt_insert_frame)
    edit_data["insert_index"] = insert_index
    edit_data["insert_frame"] = to_track.clip_start(insert_index)
    
    _set_current_move_frame_and_check_move_start(frame, x, y)

def _set_current_move_frame_and_check_move_start(frame, x, y):
    """
    Sets current mouse frame in edit data and starts move if mouse moved
    enough
    """
    global edit_data
    edit_data["current_frame"] = frame

    if abs(x - edit_data["mouse_start_x"]) > MOVE_START_LIMIT:
        edit_data["move_on"] = True
    if abs(y - edit_data["mouse_start_y"]) > MOVE_START_LIMIT:
        edit_data["move_on"] = True

def _clear_after_illegal_edit():
    global edit_data
    edit_data = None # kill current edit
    tlinewidgets.set_edit_mode_data(None)
    clear_selected_clips()
    updater.repaint_tline()
    
def _move_mode_released():
    # Pressing on selection clears it on release
    if pressed_on_selected:
        clear_selected_clips()

def move_edit_done(clips):
    for clip in clips:
        clip.selected = False
    clear_selected_clips()

# ------------------------------------ track locks handling
def _track_is_locked(track):
    global drag_disabled
    if track.edit_freedom == appconsts.LOCKED:
        track_name = utils.get_track_name(track, current_sequence())
        # No edits on locked tracks.
        primary_txt = _("Can't do edit on a locked track")
        secondary_txt = _("Track ") + track_name + _(" is locked. Unlock track to edit it.\n")
        dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window)
        
        drag_disabled = True
        return True

    return False

# ------------------------------------- clip d'n'd to range log
def clips_drag_out_started(event):
    # Abort move edit
    global edit_data, drag_disabled
    edit_data = None
    drag_disabled = True
    tlinewidgets.set_edit_mode_data(None)
    
    # Set dnd
    track = current_sequence().tracks[selected_track]
    clips = []
    for i in range(selected_range_in, selected_range_out + 1):
        clips.append(track.clips[i])
    dnd.start_tline_clips_out_drag(event, clips, gui.tline_canvas.widget)
    
    # Update tlione gui
    updater.repaint_tline()
