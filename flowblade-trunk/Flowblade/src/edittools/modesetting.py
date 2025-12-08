"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

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
Handles edit mode setting.
"""

#import boxmove
import clipeffectseditor
import editorstate
from editorstate import current_sequence
from editorstate import PLAYER
from editorstate import EDIT_MODE
import gui
import kftoolmode
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
    """
    gui.editor_window.tline_cursor_manager.set_default_edit_tool()
    if disable_mouse:
        editorstate.timeline_mouse_disabled = True

def set_clip_monitor_edit_mode():
    """
    Going to clip monitor exits active trimodes into non active trimmodes.
    """
    gui.editor_window.tline_cursor_manager.set_default_edit_tool()

def set_post_undo_redo_edit_mode():
    if EDIT_MODE() == editorstate.ONE_ROLL_TRIM or EDIT_MODE() == editorstate.TWO_ROLL_TRIM or EDIT_MODE() == editorstate.SLIDE_TRIM:
        modesetting.set_default_edit_mode()

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
    # Box tool is implemented as sub mode of OVERWRITE_MOVE so this false
    editorstate.overwrite_mode_box = False
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_overwrite_overlay)

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
def oneroll_trim_mode_init(x, y):
    """
    User enters ONE_ROLL_TRIM mode from ONE_ROLL_TRIM_NO_EDIT 
    """
    track = tlinewidgets.get_track(y)
    if track == None:
        return False

    stop_looping() 
    editorstate.edit_mode = editorstate.ONE_ROLL_TRIM

    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

    # init mode
    press_frame = tlinewidgets.get_frame(x)
    trimmodes.set_exit_mode_func = set_default_edit_mode
    trimmodes.set_no_edit_mode_func = set_default_edit_mode
    success = trimmodes.set_oneroll_mode(track, press_frame)
    return success

# --------------------------------------------------------- two roll trim
def tworoll_trim_mode_init(x, y):
    """
    User selects two roll mode
    """
    track = tlinewidgets.get_track(y)
    if track == None:
        return False

    stop_looping()
    editorstate.edit_mode = editorstate.TWO_ROLL_TRIM

    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

    press_frame = tlinewidgets.get_frame(x)
    trimmodes.set_exit_mode_func = set_default_edit_mode
    trimmodes.set_no_edit_mode_func = set_default_edit_mode
    success = trimmodes.set_tworoll_mode(track, press_frame)
    return success

# ----------------------------------------------------- slide trim
def slide_trim_mode_init(x, y):
    """
    User selects two roll mode
    """
    track = tlinewidgets.get_track(y)
    if track == None:
        return False

    stop_looping()
    editorstate.edit_mode = editorstate.SLIDE_TRIM

    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 
    updater.set_trim_mode_gui()

    press_frame = tlinewidgets.get_frame(x)
    trimmodes.set_exit_mode_func = set_default_edit_mode
    trimmodes.set_no_edit_mode_func = set_default_edit_mode
    success = trimmodes.set_slide_mode(track, press_frame)
    return success


# -------------------------------------- multi trim mode
def multitrim_mode_pressed():
    stop_looping()
    editorstate.edit_mode = editorstate.MULTI_TRIM
    trimmodes.clear_edit_data()
    tlinewidgets.set_edit_mode(None, None) # No overlays are drawn in this edit mode.
    movemodes.clear_selected_clips() # Entering trim edit mode clears selection.
    updater.set_trim_mode_gui()
    
# -------------------------------------- cut mode
def cut_mode_pressed():
    stop_looping()
    current_sequence().clear_hidden_track()

    # Box tool is implemented as sub mode of OVERWRITE_MOVE
    editorstate.edit_mode = editorstate.CUT
        
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_cut_overlay)
    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 

# -------------------------------------- kftool mode
def kftool_mode_pressed():
    stop_looping()
    current_sequence().clear_hidden_track()

    # Box tool is implemented as sub mode of OVERWRITE_MOVE
    editorstate.edit_mode = editorstate.KF_TOOL
    kftoolmode.enter_mode = None
    kftoolmode.set_no_clip_edit_data()

    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_kftool_overlay)
    movemodes.clear_selected_clips() # Entering trim edit mode clears selection 

    clipeffectseditor.keyframe_editor_widgets = []

def kftool_mode_from_popup_menu(clip, track, edit_type):
    stop_looping()
    current_sequence().clear_hidden_track()

    kftoolmode.enter_mode = editorstate.edit_mode 
    editorstate.edit_mode = editorstate.KF_TOOL
        
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_kftool_overlay)
    movemodes.clear_selected_clips() # Entering this edit mode clears selection 

    kftoolmode.set_no_clip_edit_data()

    kftoolmode.init_tool_for_clip(clip, track, edit_type)
    kftoolmode.edit_data["initializing"] = False
    gui.editor_window.tline_cursor_manager.set_cursor_to_mode()

    clipeffectseditor.keyframe_editor_widgets = []

def kftool_mode_from_kf_editor(clip, track, param_name, filter, filter_index, displayname):
    stop_looping()
    current_sequence().clear_hidden_track()

    kftoolmode.enter_mode = editorstate.edit_mode 
    editorstate.edit_mode = editorstate.KF_TOOL
        
    tlinewidgets.set_edit_mode(None, tlinewidgets.draw_kftool_overlay)
    movemodes.clear_selected_clips() # Entering this edit mode clears selection 

    kftoolmode.set_no_clip_edit_data()

    #kftoolmode.init_tool_for_clip(clip, track, edit_type)
    kftoolmode.init_for_clip_filter_and_param(clip, track, param_name, filter, filter_index, displayname)
    kftoolmode.edit_data["initializing"] = False
    gui.editor_window.tline_cursor_manager.set_cursor_to_mode()

    clipeffectseditor.keyframe_editor_widgets = []
    