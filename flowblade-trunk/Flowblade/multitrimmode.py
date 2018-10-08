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

_mouse_edit_context = appconsts.POINTER_CONTEXT_NONE


# --------------------------------------------- mouse events
def mouse_press(event, frame):
    global _mouse_edit_context
    _mouse_edit_context = gui.tline_canvas.get_pointer_context(event.x, event.y)
    if _mouse_edit_context == appconsts.POINTER_CONTEXT_NONE:
        return

    trimmodes.edit_complete_callback = _edit_completed
        
    if _mouse_edit_context == appconsts.POINTER_CONTEXT_TRIM_LEFT or _mouse_edit_context ==  appconsts.POINTER_CONTEXT_TRIM_RIGHT:
        success = modesetting.oneroll_trim_mode_init(event.x, event.y)
        if not success:
            # this should not happen (because we have pointer context) but in case we somehow do hit this, lets just get back to MULTI_TRIM
            _edit_completed()
            return
        
        trimmodes.oneroll_trim_press(event, frame)
    elif _mouse_edit_context == appconsts.POINTER_CONTEXT_MULTI_ROLL:
        success = modesetting.tworoll_trim_mode_init(event.x, event.y)
        if not success:
            # this should not happen (because we have pointer context) but in case we somehow do hit this, lets just get back to MULTI_TRIM
            _edit_completed()
            return
    
        trimmodes.tworoll_trim_press(event, frame)
    elif  _mouse_edit_context == appconsts.POINTER_CONTEXT_MULTI_SLIP:
        success = modesetting.slide_trim_mode_init(event.x, event.y)
        if not success:
            # this should not happen (because we have pointer context) but in case we somehow do hit this, lets just get back to MULTI_TRIM
            _edit_completed()
            return
    
        trimmodes.slide_trim_press(event, frame)

def mouse_move(x, y, frame, state):
    # If _mouse_edit_context == appconsts.POINTER_CONTEXT_NONE we don't need to do anything and mouse events for all other contexts are handled in trimmodes.py
    pass
        
def mouse_release(x, y, frame, state):
    # If _mouse_edit_context == appconsts.POINTER_CONTEXT_NONE we don't need to do anything and mouse events for all other contexts are handled in trimmodes.py
    pass


# ------------------------------------------------------- state handling
def _edit_completed():
    """
    Called after exit xcompleted in trimmodes.py
    """
    trimmodes.edit_complete_callback = None
  
    # Get back to MULTI_TRIM mode after doing the edit in press position context dependent trim mode
    editorstate.edit_mode = editorstate.MULTI_TRIM
    tlinewidgets.set_edit_mode(None, None) # No overlays are drawn in this edit mode
    updater.set_trim_mode_gui()
    
        
