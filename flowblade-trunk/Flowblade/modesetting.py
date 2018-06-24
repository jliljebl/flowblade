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

import boxmove
import editorstate
from editorstate import current_sequence
from editorstate import PLAYER
from editorstate import EDIT_MODE
import editorpersistance
import gui
import movemodes
import tlinewidgets
import trimmodes
import updater


# ------------------------------------- edit mode setting
def set_default_edit_mode(disable_mouse=False):
    """
    This is used as global 'go to start position' exit door from
    situations where for example user is in trim and exits it
    without specifying which edit mode to go to.
    
    NOTE: As this uses 'programmed click', this method does nothing if insert mode button
    is already down.
    """
    gui.editor_window.set_default_edit_tool()
    if disable_mouse:
        editorstate.timeline_mouse_disabled = True

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
        gui.editor_window.set_default_edit_tool()
        
    gui.editor_window.set_tool_selector_to_mode()

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
    User selects Insert tool.
    """
    stop_looping()
    current_sequence().clear_hidden_track()

    editorstate.edit_mode = editorstate.INSERT_MOVE
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_insert_overlay)

    _set_move_mode()

def overwrite_move_mode_pressed():
    """
    User selects Overwrite tool.
    """
    stop_looping()
    current_sequence().clear_hidden_track()

    editorstate.edit_mode = editorstate.OVERWRITE_MOVE
    # Box tool is implemeted as sub mode of OVERWRITE_MOVE so this false
    editorstate.overwrite_mode_box = False
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_overwrite_overlay)

    _set_move_mode()

def box_mode_pressed():
    """
    User selects Box tool.
    """
    stop_looping()
    current_sequence().clear_hidden_track()
    
    # Box tool is implemeted as sub mode of OVERWRITE_MOVE
    editorstate.edit_mode = editorstate.OVERWRITE_MOVE
    editorstate.overwrite_mode_box = True
    boxmove.clear_data()
        
    tlinewidgets.set_edit_mode(None, None) # these get set later for box move
        
    _set_move_mode()

def multi_mode_pressed():
    """
    User selects Spacer tool.
    """
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
            tlinewidgets.trim_mode_in_non_active_state = True
            editorstate.timeline_mouse_disabled = True
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

    # Feature disabled for now
    #if track_lock_check_and_user_info(track, oneroll_trim_mode_init, "one roll trim mode"):
    #    set_default_edit_mode()
    #    return False

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
            tlinewidgets.trim_mode_in_non_active_state = True
            editorstate.timeline_mouse_disabled = True
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
    
    #if track_lock_check_and_user_info(track, tworoll_trim_mode_init, "two roll trim mode",):
    #    set_default_edit_mode()
    #    return False

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
    stop_looping()
    editorstate.edit_mode = editorstate.SLIDE_TRIM_NO_EDIT
    gui.editor_window.set_cursor_to_mode()
    tlinewidgets.set_edit_mode(None, None) # No overlays are drawn in this edit mode
    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

def slide_trim_no_edit_press(event, frame):
    success = slide_trim_mode_init(event.x, event.y)
    if success:
        if not editorpersistance.prefs.quick_enter_trims:
            tlinewidgets.trim_mode_in_non_active_state = True
            editorstate.timeline_mouse_disabled = True
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
    
    #if track_lock_check_and_user_info(track, tworoll_trim_mode_init, "two roll trim mode"):
    #    set_default_edit_mode()
    #    return False

    stop_looping()
    editorstate.edit_mode = editorstate.SLIDE_TRIM

    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

    press_frame = tlinewidgets.get_frame(x)
    trimmodes.set_exit_mode_func = set_default_edit_mode
    trimmodes.set_no_edit_mode_func = slide_trim_no_edit_init
    success = trimmodes.set_slide_mode(track, press_frame)
    return success

# -------------------------------------- cut mode
def cut_mode_pressed():
    #print "cut_mode_pressed"
    stop_looping()
    current_sequence().clear_hidden_track()

    # Box tool is implemeted as sub mode of OVERWRITE_MOVE
    editorstate.edit_mode = editorstate.CUT
        
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_cut_overlay)
    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    
    #_set_move_mode()

# -------------------------------------- cut mode
def kftool_mode_pressed():
    print "kftool_mode_pressed"
    stop_looping()
    current_sequence().clear_hidden_track()

    # Box tool is implemeted as sub mode of OVERWRITE_MOVE
    editorstate.edit_mode = editorstate.KF_TOOL
        
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_kftool_overlay)
    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
