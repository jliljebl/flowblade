"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2026 Janne Liljeblad.

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

import editorstate
import singletracktransition
import tlinewidgets
import updater

_enter_mode = None
_enter_draw_func = None

_edit_data = None

def init_for_mouse_press(track, clip, clip_index, frame):
    global _enter_mode, _enter_draw_func, _edit_data

    _enter_mode = editorstate.edit_mode
    _enter_draw_func = tlinewidgets.canvas_widget.edit_mode_overlay_draw_func

    _edit_data = {}
    try:
        from_clip = track.clips[clip_index - 1]
        to_clip = track.clips[clip_index + 1]
    except:
         _edit_data["legal"] = False
         
    _edit_data = singletracktransition.get_transition_drag_data(track, clip_index)
    _edit_data["clip_index"] = clip_index
    _edit_data["old_transition"] = clip
    _edit_data["press_frame"] = frame
    _edit_data["track"] = track
    _edit_data["legal"] = True
    
    tlinewidgets.set_edit_mode(_edit_data, tlinewidgets.draw_transion_length_drag_overlay)
    editorstate.edit_mode = editorstate.TRANSITION_LENGTH_DRAG
    
def transition_drag_press(event, frame):
    _update_edit_data(frame)
    updater.repaint_tline()
    
def transition_drag_move(x, y, frame, state):
    _update_edit_data(frame)
    updater.repaint_tline()
    
def transition_drag_release(x, y, frame, state):
    print("release")
    global _enter_mode, _enter_draw_func, _edit_data

    _update_edit_data(frame)

    editorstate.edit_mode = _enter_mode
    tlinewidgets.set_edit_mode(None, None)

    drag_length = abs(_edit_data["center_frame"] - frame)
    track = _edit_data["track"]
    index = _edit_data["clip_index"]

    singletracktransition.create_length_changed_transition(track, index, drag_length * 2)

    updater.repaint_tline()

def _update_edit_data(frame):
    global _edit_data

    if _edit_data["center_frame"] > frame:
        if _edit_data["center_frame"] - frame > _edit_data["max_handle_from_center"]:
            frame = _edit_data["center_frame"] +  _edit_data["max_handle_from_center"]
    if _edit_data["center_frame"] < frame:
        if frame - _edit_data["center_frame"] > _edit_data["max_handle_from_center"]:
            frame = _edit_data["center_frame"] -  _edit_data["max_handle_from_center"]

    if abs(frame - _edit_data["center_frame"]) < 2:
        _edit_data["legal"] = False

    _edit_data["press_frame"] = frame
