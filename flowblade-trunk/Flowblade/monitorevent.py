"""
Module handles button presses from monitor control buttons row.
"""
import appconsts
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

# ---------------------------------------- playback
# Some events have different meanings depending on edit mode and
# are handled in either movemodes.py or trimmodes.py modules depending 
# on edit mode.
def play_pressed():
    if current_is_move_mode():
        movemodes.play_pressed()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        trimmodes.oneroll_play_pressed()
    else:
        trimmodes.tworoll_play_pressed()

def stop_pressed():
    if current_is_move_mode():
        movemodes.stop_pressed()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        trimmodes.oneroll_stop_pressed()
    else:
        trimmodes.tworoll_stop_pressed()
        
def next_pressed():
    if current_is_move_mode():
        movemodes.next_pressed()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        trimmodes.oneroll_next_pressed()
    else:
        trimmodes.tworoll_next_pressed()

def prev_pressed():
    if current_is_move_mode():
        movemodes.prev_pressed()
    elif EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        trimmodes.oneroll_prev_pressed()
    else:
        trimmodes.tworoll_prev_pressed()

def ff_pressed():
    PLAYER().start_variable_speed_playback(FF_REW_SPEED)
        
def ff_released():
    PLAYER().stop_playback()
    
def rew_pressed():
    PLAYER().start_variable_speed_playback(-FF_REW_SPEED)
    
def rew_released():
    PLAYER().stop_playback()
    
    
# -------------------------------------- marks
def mark_in_pressed():
    mark_in = PLAYER().producer.frame()
    
    if timeline_visible():
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
        PLAYER().producer.mark_in = -1
        PLAYER().producer.mark_out = -1
    else:
        current_sequence().monitor_clip.mark_in = -1
        current_sequence().monitor_clip.mark_out = -1

    _do_marks_update()
    updater.display_marks_tc()

def to_mark_in_pressed():
    mark_in = PLAYER().producer.mark_in
    if not timeline_visible():
        mark_in = current_sequence().monitor_clip.mark_in
    if mark_in == -1:
        return
    PLAYER().seek_frame(mark_in)

def to_mark_out_pressed():
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
        
    gui.pos_bar.update_display_from_producer(producer)
