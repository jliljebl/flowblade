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
Module holds current global editor state.

Accessor methods are there mainly to improve code readability elsewhere.

We're using BIG_METHOD_NAMES() for some state objects. This is a bit unusual,
but looks good when reading code.
"""

import appconsts

# NOTE: This cannot ever be made to import anything else.

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
CLIP_END_DRAG = 11
SELECT_TLINE_SYNC_CLIP = 12
CUT = 13
KF_TOOL = 14
MULTI_TRIM = 15

# Gtk.Application object for main app. 
app = None

# Project being edited
project = None

# Wrapped MLT framework producer->consumer media player 
player = None                 

# Current edit mode
edit_mode = INSERT_MOVE

# Ripple Trim tool is ONE_ROLL_TRIM mode + True on this flag
trim_mode_ripple = False

# Box tool is OVERWRITE_MOVE tool mode + True on this flag
overwrite_mode_box = False

# Media files view filter for selecting displayed media objects in bin
media_view_filter = appconsts.SHOW_ALL_FILES
media_view_ratings_filter = appconsts.MEDIA_RATINGS_SHOW_ALL

# Media file displayed in monitor when 'Clip' is pressed 
_monitor_media_file = None

# Flag for timeline/clip display in monitor
_timeline_displayed = True

# Used to ignore drag and release events when press doesn't start an action that can/should handle those events.
timeline_mouse_disabled = False

# Timeline current frame is saved here while clip is being displayed in monitor
# and PLAYER() current frame is not timeline frame 
tline_shadow_frame = -1

# Dict of current proxy media paths
_current_proxy_paths = {}

# Clips or compositors that are copy/pasted with CTRL+C, CTRL+V
# Code using this assumes that this is saved as tuple (type_info, paste_data)
_copy_paste_objects = None

# Used to alter gui layout and tracks configuration, set at startup
SCREEN_HEIGHT = -1
SCREEN_WIDTH = -1

# Runtime environment data
gtk_version = None
mlt_version = None
appversion = "2.22.1"
RUNNING_FROM_INSTALLATION = 0
RUNNING_FROM_DEV_VERSION = 1
RUNNING_FROM_FLATPAK = 2
app_running_from = RUNNING_FROM_INSTALLATION
audio_monitoring_available = False

# Whether to let the user set their user_dir using XDG Base dir spec
use_xdg = False

# Cursor position and sensitivity
cursor_on_tline = False
cursor_is_tline_sensitive = True
last_mouse_x = -1 # This is only used by multitrimmode.py 
last_mouse_y = -1 # This is only used by multitrimmode.py 

# Flag for running JACK audio server. If this is on when SDLConsumer created in mltplayer.py
# jack rack filter will bw attached to it
# NOT USED CURRENTLY.
attach_jackrack = False

# Flag is used to block unwanted draw events during loads  
project_is_loading = False

# Audio levels display mode, False means that audio levels are displayed on request
display_all_audio_levels = True
display_clip_media_thumbnails = True

# Flag for window being in fullscreen mode
fullscreen = False
fullscreen_second_window = False

# Trim view mode
show_trim_view = appconsts.TRIM_VIEW_OFF

# Remember fade and transition lengths for next invocation, users prefer this over one default value.
fade_length = -1
transition_length = -1
steal_frames = True

# Timeline rendering
tline_render_mode = appconsts.TLINE_RENDERING_OFF

# Timeline view mode
tline_view_mode = 0 # sequence.PROGRAM_OUT_MODE

# Trim clips cache for quicker inits, path -> clip
_trim_clips_cache = {}

# Normal installs and Flatpaks have G'Mic bin in different locations.
# Value set in gmic.py module. 
gmic_path = None

# For development and test use.
force_sdl2 = True 

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

def APP():
    return app

def PROJECT():
    return project
    
def PLAYER():
    return player

def EDIT_MODE():
    return edit_mode
    
def MONITOR_MEDIA_FILE():
    return _monitor_media_file

def get_compositing_mode():
    if project.c_seq == None:
        print ("get_compositing_mode(), trying to get compositing mode when no current sequence available!") 
        return appconsts.COMPOSITING_MODE_TOP_DOWN_FREE_MOVE
    else:
        return project.c_seq.compositing_mode

def get_tline_rendering_mode():
    return tline_render_mode
        
def get_track(index):
    return project.c_seq.tracks[index]

def timeline_visible():
    return _timeline_displayed

def mlt_version_is_greater_correct(test_version):
    runtime_ver = mlt_version.split(".")
    test_ver = test_version.split(".")
    
    if runtime_ver[0] > test_ver[0]:
        return True
    elif runtime_ver[0] == test_ver[0]:
        if runtime_ver[1] > test_ver[1]:
            return True
        elif runtime_ver[1] == test_ver[1]:
            if  runtime_ver[2] > test_ver[2]:
                return True
    
    return False

def runtime_version_greater_then_test_version(test_version, runtime_version):
    runtime_ver = list(map(int, runtime_version.split(".")))
    test_ver = list(map(int, test_version.split(".")))
    if int(runtime_ver[0]) > int(test_ver[0]):
        return True
    elif runtime_ver[0] == test_ver[0]:
        if runtime_ver[1] > test_ver[1]:
            return True
        elif runtime_ver[1] == test_ver[1]:
            if  runtime_ver[2] >  test_ver[2]:
                return True
    
    return False
    
def set_copy_paste_objects(objs):
    global _copy_paste_objects
    _copy_paste_objects = objs

def get_copy_paste_objects():
    return _copy_paste_objects

def clear_copy_paste_objects():
    global _copy_paste_objects
    _copy_paste_objects = None

def screen_size_small_height():
    if SCREEN_HEIGHT < 901:
        return True
    else:
        if SCREEN_WIDTH < 1280:
            return True
            
        return False

def screen_size_small_width():
    if SCREEN_WIDTH < 1420:
        return True
    else:
        return False

def screen_size_large_width():
    if SCREEN_WIDTH > 1670:
        return True
    else:
        return False

def screen_size_small():
    if screen_size_small_height() == True or screen_size_small_width() == True:
        return True
    
    return False

def screen_size_large_height():
    if SCREEN_HEIGHT > 1048:
        return True
    else:
        return False
        
def get_cached_trim_clip(path):
    try:
        return _trim_clips_cache[path]
    except:
        return None 

def add_cached_trim_clip(clip):
     _trim_clips_cache[clip.path] = clip

def clear_trim_clip_cache():
    global _trim_clips_cache
    _trim_clips_cache = {}
 
 
 
# Called from tline "motion_notify_event" when drag is not on.
# This is only used by multitrimmode.py to have data to enter trims with keyboard correctly.
def set_mouse_current_non_drag_pos(x, y):
    global last_mouse_x, last_mouse_y
    last_mouse_x = x
    last_mouse_y = y
