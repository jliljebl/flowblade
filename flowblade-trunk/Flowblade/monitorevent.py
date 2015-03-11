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
Module handles button presses from monitor control buttons row.
"""

import editorstate
from editorstate import PLAYER
from editorstate import current_sequence
from editorstate import timeline_visible
from editorstate import EDIT_MODE
from editorstate import current_is_move_mode
from editorstate import MONITOR_MEDIA_FILE
import gui
import movemodes
import trimmodes
import updater


FF_REW_SPEED = 3.0


JKL_SPEEDS = [-32.0, -16.0, -8.0, -1.0, 0.0, 1.0, 3.0, 5.0, 8.0]
#JKL_SPEEDS = [-32.0, -16.0, -8.0, -1.0, -0.2, 0.0, 0.2, 1.0, 3.0, 5.0, 8.0]
JKL_STOPPED_INDEX = 4

# ---------------------------------------- playback
# Some events have different meanings depending on edit mode and
# are handled in either movemodes.py or trimmodes.py modules depending 
# on edit mode.
def play_pressed():
    if current_is_move_mode():
        movemodes.play_pressed()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        trimmodes.oneroll_play_pressed()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM_NO_EDIT:
        movemodes.play_pressed()
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        trimmodes.tworoll_play_pressed()
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM_NO_EDIT:
        movemodes.play_pressed()
    elif EDIT_MODE() == editorstate.SLIDE_TRIM:
        trimmodes.slide_play_pressed()
    elif EDIT_MODE() == editorstate.SLIDE_TRIM_NO_EDIT:
        movemodes.play_pressed()
    
def stop_pressed():
    if current_is_move_mode():
        movemodes.stop_pressed()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM_NO_EDIT:
        movemodes.stop_pressed()
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM_NO_EDIT:
        movemodes.stop_pressed()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        trimmodes.oneroll_stop_pressed()
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        trimmodes.tworoll_stop_pressed()
    elif EDIT_MODE() == editorstate.SLIDE_TRIM:
        trimmodes.slide_stop_pressed()
    elif EDIT_MODE() == editorstate.SLIDE_TRIM_NO_EDIT:
        movemodes.stop_pressed()

def next_pressed():
    if current_is_move_mode():
        movemodes.next_pressed()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        trimmodes.oneroll_next_pressed()
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        trimmodes.tworoll_next_pressed()
    elif EDIT_MODE() == editorstate.SLIDE_TRIM:
        trimmodes.slide_next_pressed()

def prev_pressed():
    if current_is_move_mode():
        movemodes.prev_pressed()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        trimmodes.oneroll_prev_pressed()
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        trimmodes.tworoll_prev_pressed()
    elif EDIT_MODE() == editorstate.SLIDE_TRIM:
        trimmodes.slide_prev_pressed()

def j_pressed():
    if timeline_visible():
        trimmodes.set_no_edit_trim_mode()
    jkl_index = _get_jkl_speed_index()
    if jkl_index > JKL_STOPPED_INDEX - 1: # JKL_STOPPPED_INDEX - 1 is first backwards speed, any bigger is forward, j starts backwards slow from any forward speed 
        jkl_index = JKL_STOPPED_INDEX - 1
    else:
        jkl_index = jkl_index - 1
    
    if jkl_index < 0:
        jkl_index = 0
    new_speed = JKL_SPEEDS[jkl_index]
    PLAYER().start_variable_speed_playback(new_speed)

def k_pressed():
    if timeline_visible():
        trimmodes.set_no_edit_trim_mode()
    PLAYER().stop_playback()

def l_pressed():
    if timeline_visible():
        trimmodes.set_no_edit_trim_mode()
    jkl_index = _get_jkl_speed_index()
    if jkl_index < JKL_STOPPED_INDEX + 1:# JKL_STOPPPED_INDEX + 1 is first forward speed, any smaller is backward, l starts forward slow from any backwards speed 
        jkl_index = JKL_STOPPED_INDEX + 1
    else:
        jkl_index = jkl_index + 1
    
    if jkl_index == len(JKL_SPEEDS):
        jkl_index = len(JKL_SPEEDS) - 1
    new_speed = JKL_SPEEDS[jkl_index]
    PLAYER().start_variable_speed_playback(new_speed)
    

def _get_jkl_speed_index():
    speed = PLAYER().producer.get_speed()
    if speed  < -8.0:
        return 0

    for i in range(len(JKL_SPEEDS) - 1):
        if speed <= JKL_SPEEDS[i]:
            return i
        
    return len(JKL_SPEEDS) - 1
    
# -------------------------------------- marks
def mark_in_pressed():
    mark_in = PLAYER().producer.frame()
    
    if timeline_visible():
        trimmodes.set_no_edit_trim_mode()
        mark_out_old = PLAYER().producer.mark_out
        PLAYER().producer.mark_in = mark_in
    else:
        mark_out_old = current_sequence().monitor_clip.mark_out
        current_sequence().monitor_clip.mark_in = mark_in

    # Clear illegal old mark out
    if mark_out_old != -1:
        if mark_out_old < mark_in:
            if timeline_visible():
                PLAYER().producer.mark_out = -1
            else:
                current_sequence().monitor_clip.mark_out = -1

    _do_marks_update()
    updater.display_marks_tc()


def mark_out_pressed():
    mark_out = PLAYER().producer.frame()

    if timeline_visible():
        trimmodes.set_no_edit_trim_mode()
        mark_in_old = PLAYER().producer.mark_in
        PLAYER().producer.mark_out = mark_out
    else:
        mark_in_old = current_sequence().monitor_clip.mark_in
        current_sequence().monitor_clip.mark_out = mark_out
    
    # Clear illegal old mark in
    if mark_in_old > mark_out:
        if timeline_visible():
            PLAYER().producer.mark_in = -1
        else:
            current_sequence().monitor_clip.mark_in = -1
            
    _do_marks_update()
    updater.display_marks_tc()
    
def marks_clear_pressed():
    if timeline_visible():
        trimmodes.set_no_edit_trim_mode()
        PLAYER().producer.mark_in = -1
        PLAYER().producer.mark_out = -1
    else:
        current_sequence().monitor_clip.mark_in = -1
        current_sequence().monitor_clip.mark_out = -1

    _do_marks_update()
    updater.display_marks_tc()

def to_mark_in_pressed():
    if timeline_visible():
        trimmodes.set_no_edit_trim_mode()
    mark_in = PLAYER().producer.mark_in
    if not timeline_visible():
        mark_in = current_sequence().monitor_clip.mark_in
    if mark_in == -1:
        return
    PLAYER().seek_frame(mark_in)

def to_mark_out_pressed():
    if timeline_visible():
        trimmodes.set_no_edit_trim_mode()
    mark_out = PLAYER().producer.mark_out
    if not timeline_visible():
        mark_out = current_sequence().monitor_clip.mark_out
    if mark_out == -1:
        return
    PLAYER().seek_frame(mark_out)

def _do_marks_update():

    if timeline_visible():
        producer = PLAYER().producer
    else:
        producer = current_sequence().monitor_clip
        MONITOR_MEDIA_FILE().mark_in = producer.mark_in
        MONITOR_MEDIA_FILE().mark_out = producer.mark_out
        gui.media_list_view.widget.queue_draw()

    gui.pos_bar.update_display_from_producer(producer)
    gui.tline_scale.widget.queue_draw()
    
# ------------------------------------------------------------ clip arrow seeks
def up_arrow_seek_on_monitor_clip():
    current_frame = PLAYER().producer.frame()

    if current_frame < MONITOR_MEDIA_FILE().mark_in:
        PLAYER().seek_frame(MONITOR_MEDIA_FILE().mark_in)
        return 

    if current_frame < MONITOR_MEDIA_FILE().mark_out:
        PLAYER().seek_frame(MONITOR_MEDIA_FILE().mark_out)
        return 

    PLAYER().seek_frame(PLAYER().producer.get_length() - 1)

def down_arrow_seek_on_monitor_clip():
    current_frame = PLAYER().producer.frame()
    mark_in = MONITOR_MEDIA_FILE().mark_in
    mark_out = MONITOR_MEDIA_FILE().mark_out

    if current_frame > mark_out and mark_out != -1:
        PLAYER().seek_frame(MONITOR_MEDIA_FILE().mark_out)
        return 

    if current_frame > mark_in and mark_in != -1:
        PLAYER().seek_frame(MONITOR_MEDIA_FILE().mark_in)
        return 

    PLAYER().seek_frame(0)

def set_monitor_playback_interpolation(new_interpolation):
    PLAYER().consumer.set("rescale", str(new_interpolation)) # MLT options "nearest", "bilinear", "bicubic", "hyper" hardcoded into menu items
    
    
