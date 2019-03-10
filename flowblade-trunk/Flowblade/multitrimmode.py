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
Module handles Multitrim tool functionality. 
"""

import appconsts
import editorstate
import gui
import modesetting
import tlinewidgets
import trimmodes
import updater

set_default_mode_func = None

_mouse_edit_context = appconsts.POINTER_CONTEXT_NONE


# --------------------------------------------- mouse events
def mouse_press(event, frame):
    _enter_trim_mode_edit(event.x, event.y, frame)
    if _mouse_edit_context == appconsts.POINTER_CONTEXT_NONE:
        set_default_mode_func()

def mouse_move(x, y, frame, state):
    # If _mouse_edit_context == appconsts.POINTER_CONTEXT_NONE we don't need to do anything and mouse events for all other contexts are handled in trimmodes.py
    pass
        
def mouse_release(x, y, frame, state):
    # If _mouse_edit_context == appconsts.POINTER_CONTEXT_NONE we don't need to do anything and mouse events for all other contexts are handled in trimmodes.py
    pass


# ------------------------------------------------------- keyboard events
def enter_pressed():
    # With Enter key we enter keyboard trim on current pointer context
    x = editorstate.last_mouse_x
    y = editorstate.last_mouse_y
    frame = tlinewidgets.get_frame(x)
    
    _enter_trim_mode_edit(x, y, frame)
    trimmodes.submode = trimmodes.KEYB_EDIT_ON
    updater.repaint_tline()

# ------------------------------------------------------- entering and exiting trims handling
def _enter_trim_mode_edit(x, y, frame):
    global _mouse_edit_context
    _mouse_edit_context = gui.tline_canvas.get_pointer_context(x, y)
    if _mouse_edit_context == appconsts.POINTER_CONTEXT_NONE:
        # No context for edit, do nothing.
        return
        
    trimmodes.edit_complete_callback = _edit_completed
        
    if _mouse_edit_context == appconsts.POINTER_CONTEXT_TRIM_LEFT or _mouse_edit_context == appconsts.POINTER_CONTEXT_TRIM_RIGHT:
        success = modesetting.oneroll_trim_mode_init(x, y)
        if not success:
            # this should not happen (because we have pointer context) but in case we somehow do hit this, lets just get back to MULTI_TRIM mode
            _edit_completed()
            return
        
        trimmodes.oneroll_trim_press(None, frame, x, y)
    elif _mouse_edit_context == appconsts.POINTER_CONTEXT_MULTI_ROLL:
        success = modesetting.tworoll_trim_mode_init(x, y)
        if not success:
            # this should not happen (because we have pointer context) but in case we somehow do hit this, lets just get back to MULTI_TRIM mode
            _edit_completed()
            return
    
        trimmodes.tworoll_trim_press(None, frame, x, y)
    elif  _mouse_edit_context == appconsts.POINTER_CONTEXT_MULTI_SLIP:
        success = modesetting.slide_trim_mode_init(x, y)
        if not success:
            # this should not happen (because we have pointer context) but in case we somehow do hit this, lets just get back to MULTI_TRIM mode
            _edit_completed()
            return
    
        trimmodes.slide_trim_press(None, frame, x, y)
                
def _edit_completed():
    """
    Called after edit completed in trimmodes.py
    """
    trimmodes.edit_complete_callback = None
  
    # Get back to MULTI_TRIM mode after doing the edit
    editorstate.edit_mode = editorstate.MULTI_TRIM
    tlinewidgets.set_edit_mode(None, None) # No overlays are drawn in this edit mode
    updater.set_trim_mode_gui()
    


    

