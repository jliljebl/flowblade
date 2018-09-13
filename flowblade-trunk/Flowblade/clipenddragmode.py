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
Module handles clip end dragging edits.
"""


import appconsts
import gui
import edit
from editorstate import current_sequence
import editorstate
import tlinewidgets
import updater

# Edit mode that was active when mode was entered 
_enter_mode = None
_enter_draw_func = None


def maybe_init_for_mouse_press(event, frame): 
    # See if we actually hit a clip
    track = tlinewidgets.get_track(event.y)
    if track == None:
        return
    if track.id < 1 or (track.id >= len(current_sequence().tracks) - 1):
        return False
    clip_index = current_sequence().get_clip_index(track, frame)
    if clip_index == -1:
        return

    clip = track.clips[clip_index]
    
    if clip.is_blanck_clip:
        return
    
    # Now we will in fact enter CLIP_END_DRAG edit mode
    # See if we're dragging clip end or start
    cut_frame = current_sequence().get_closest_cut_frame(track.id, frame)
    editing_clip_end = True
    if frame >= cut_frame:
        editing_clip_end = False
    else:
        cut_frame = cut_frame - (clip.clip_out - clip.clip_in)

    if editing_clip_end == True: # clip end drags
        bound_end = cut_frame - clip.clip_in + clip.get_length() - 1 # get_length() is available media length, not current clip length
        bound_start = cut_frame - 1
        if clip_index == len(track.clips) - 1: # last clip
            bound_end = bound_end - 1
    else: # clip beginning drags
        bound_start = cut_frame - clip.clip_in 
        bound_end =  cut_frame + (clip.clip_out - clip.clip_in) + 1

    global _enter_mode, _enter_draw_func, _edit_data

    _enter_mode = editorstate.edit_mode
    editorstate.edit_mode = editorstate.CLIP_END_DRAG
    
    _enter_draw_func = tlinewidgets.canvas_widget.edit_mode_overlay_draw_func

    _edit_data = {}
    _edit_data["track"] = track
    _edit_data["clip_index"] = clip_index
    _edit_data["frame"] = frame
    _edit_data["press_frame"] = frame
    _edit_data["editing_clip_end"] = editing_clip_end
    _edit_data["bound_end"] = bound_end
    _edit_data["bound_start"] = bound_start
    _edit_data["track_height"] = track.height
    _edit_data["orig_in"] = cut_frame - 1
    _edit_data["orig_out"] = cut_frame + (clip.clip_out - clip.clip_in)

    tlinewidgets.set_edit_mode(_edit_data, tlinewidgets.draw_clip_end_drag_overlay)

    if tlinewidgets.pointer_context == appconsts.POINTER_CONTEXT_NONE:
        # We did CTRL + Mouse Right to get here, we need to set pointer context to left or right
        if editing_clip_end == True:
            tlinewidgets.pointer_context = appconsts.POINTER_CONTEXT_END_DRAG_RIGHT
        else:
            tlinewidgets.pointer_context = appconsts.POINTER_CONTEXT_END_DRAG_LEFT

    gui.editor_window.set_cursor_to_mode()

def mouse_press(event, frame):
    frame = _legalize_frame(frame)
    _edit_data["frame"] = frame

    updater.repaint_tline()

def mouse_move(x, y, frame, state):
    frame = _legalize_frame(frame)
    _edit_data["frame"] = frame
    updater.repaint_tline()

def mouse_release(x, y, frame, state):
    frame = _legalize_frame(frame)
    _edit_data["frame"] = frame
    updater.repaint_tline()

    track = _edit_data["track"]
    clip_index = _edit_data["clip_index"]
    clip = track.clips[clip_index]
    orig_in = _edit_data["orig_in"]
    orig_out = _edit_data["orig_out"]
    
    # do edit
    # Dragging clip end
    if _edit_data["editing_clip_end"] == True:
        delta = frame - orig_out
         # next clip is not blank or last clip
        if ((clip_index == len(track.clips) - 1) or 
            (track.clips[clip_index + 1].is_blanck_clip == False)):
            data = {"track":track,
                    "index":clip_index,
                    "clip":clip,
                    "delta":delta}
            action = edit.trim_last_clip_end_action(data)
            action.do_edit()
        else: # next clip is blank
            blank_clip = track.clips[clip_index + 1]
            blank_clip_length = blank_clip.clip_length()
            data = {"track":track,
                    "index":clip_index,
                    "clip":clip,
                    "blank_clip_length":blank_clip_length,
                    "delta":delta}
            if delta < blank_clip_length: # partial blank overwrite
                action = edit.clip_end_drag_on_blank_action(data)
                action.do_edit()
            else: # full blank replace
                action = edit.clip_end_drag_replace_blank_action(data)
                action.do_edit()
    else:# Dragging clip start
        delta = frame - orig_in  - 1 # -1 because..uhh..inclusive exclusive something something
        # prev clip is not blank or first clip
        if ((clip_index == 0) or
            (track.clips[clip_index - 1].is_blanck_clip == False)):
            data = {"track":track,
                    "index":clip_index,
                    "clip":clip,
                    "delta":delta}
            action = edit.trim_start_action(data)
            action.do_edit()
        else: # prev clip is blank
            blank_clip = track.clips[clip_index - 1]
            blank_clip_length = blank_clip.clip_length()
            data = {"track":track,
                    "index":clip_index,
                    "clip":clip,
                    "blank_clip_length":blank_clip_length,
                    "delta":delta}
            if -delta < blank_clip_length: # partial blank overwrite
                action = edit.clip_start_drag_on_blank_action(data)
                action.do_edit()
            else: # full blank replace
                action = edit.clip_start_drag_replace_blank_action(data)
                action.do_edit()

    _exit_clip_end_drag()

    updater.repaint_tline()

def _exit_clip_end_drag(): 
    # Go back to enter mode
    editorstate.edit_mode = _enter_mode
    tlinewidgets.set_edit_mode(None, _enter_draw_func)
    tlinewidgets.pointer_context = appconsts.POINTER_CONTEXT_NONE
    
    gui.editor_window.set_cursor_to_mode()
    updater.repaint_tline()

def _legalize_frame(frame):
    start = _edit_data["bound_start"]
    end = _edit_data["bound_end"]

    if _edit_data["editing_clip_end"] == True:
        if frame > end:
            frame = end
        if frame < (start + 1):
            frame = start + 1
    else:
        if frame > end - 1:
            frame = end - 1
        if frame < start:
            frame = start
    
    return frame
