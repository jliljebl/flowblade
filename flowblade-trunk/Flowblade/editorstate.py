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
Module holds current editor state.

Accessor methods are there mainly to improve code readability elsewhere.

We're using BIG_METHOD_NAMES() for state objects. This is a bit unusual
but looks good when reading code.
"""
import appconsts

# Edit modes
INSERT_MOVE = 0
OVERWRITE_MOVE = 1
ONE_ROLL_TRIM = 2
TWO_ROLL_TRIM = 3
SELECT_PARENT_CLIP = 4
COMPOSITOR_EDIT = 5
ONE_ROLL_TRIM_NO_EDIT = 6
TWO_ROLL_TRIM_NO_EDIT = 7
SLIDE_TRIM = 8
SLIDE_TRIM_NO_EDIT = 9
MULTI_MOVE = 10

# Project being edited
project = None

# Wrapped MLT framework producer->consumer media player 
player = None                 

# Current edit mode
edit_mode = INSERT_MOVE

# Media files view filter for selecting displayed media objects in bin
media_view_filter = appconsts.SHOW_ALL_FILES

# Media file displayed in monitor when 'Clip' is pressed 
_monitor_media_file = None

# Flag for timeline/clip display in monitor
_timeline_displayed = True

# Timeline current frame is saved here while clip is being displayed in monitor
# and PLAYER() current frame is not timeline frame 
tline_shadow_frame = -1

# Dict of curren proxy media paths
_current_proxy_paths = {}

# Clips or compositor that are copy/pasted with CTRL+C, CTRL+V 
_copy_paste_objects = None

# Used to alter gui layout and tracks configuration, set at startup
SCREEN_HEIGHT = -1
SCREEN_WIDTH = -1

# Runtime environment data
gtk_version = None
mlt_version = None
appversion = "0.10"
RUNNING_FROM_INSTALLATION = 0
RUNNING_FROM_DEV_VERSION = 1
app_running_from = RUNNING_FROM_INSTALLATION
audio_monitoring_available = False

# Cursor pos
cursor_on_tline = False

# Flag for running JACK audio server. If this is on when SDLConsumer created in mltplayer.py
# jack rack filter will bw taached to it
attach_jackrack = False

# Flag is used to block unwanted draw events during loads  
project_is_loading = False

def current_is_move_mode():
    if ((edit_mode == INSERT_MOVE) or (edit_mode == OVERWRITE_MOVE) or (edit_mode == MULTI_MOVE)):
        return True
    return False

def current_is_active_trim_mode():
    if ((edit_mode == ONE_ROLL_TRIM) or (edit_mode == TWO_ROLL_TRIM) or (edit_mode == SLIDE_TRIM)):
        return True
    return False
    
def current_sequence():
    return project.c_seq

def current_bin():
    return project.c_bin

def current_proxy_media_paths():
    return _current_proxy_paths

def update_current_proxy_paths():
    global _current_proxy_paths
    _current_proxy_paths = project.get_current_proxy_paths()

def current_tline_frame():
    if timeline_visible():
        return PLAYER().current_frame()
    else:
        return tline_shadow_frame

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

def mlt_version_is_equal_or_greater(test_version):
    mlt_parts = mlt_version.split(".")
    test_parts = test_version.split(".")
    if test_parts[0] >= mlt_parts[0] and test_parts[1] >= mlt_parts[1] and test_parts[2] >= mlt_parts[2]:
        return True
    
    return False

def set_copy_paste_objects(objs):
    global _copy_paste_objects
    _copy_paste_objects = objs

def get_copy_paste_objects():
    return _copy_paste_objects

   
