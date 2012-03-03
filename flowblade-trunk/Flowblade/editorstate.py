"""
Module holds current editor state.

Accerssor methods are there mainly to improve code readability elsewhere.

We're using BIG_METHOD_NAMES() for state objects. This is a bit unusual
but looks good when reading code.
"""
# Edit modes
INSERT_MOVE = 0
OVERWRITE_MOVE = 1
ONE_ROLL_TRIM = 2
TWO_ROLL_TRIM = 3
SELECT_PARENT_CLIP = 4
COMPOSITOR_EDIT = 5

# Project being edited
project = None

# Wrapped MLT framework producer->consumer media player 
player = None                 

# Current edit mode
edit_mode = INSERT_MOVE

# Media file displayed in monitor when 'Clip' is pressed 
_monitor_media_file = None

# Flag for timeline/clip display in monitor
_timeline_displayed = True

def current_is_move_mode():
    if ((edit_mode == INSERT_MOVE) or (edit_mode == OVERWRITE_MOVE)):
        return True
    return False

def current_sequence():
    return project.c_seq

def current_bin():
    return project.c_bin
    
def PROJECT():
    return project
    
def PLAYER():
    return player
    
def EDIT_MODE():
    return edit_mode
    
def MONITOR_MEDIA_FILE():
    return _monitor_media_file

def get_track(index):
    return project.c_seq.tracks[index]

def timeline_visible():
    return _timeline_displayed
