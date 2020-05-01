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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""
import gi

from gi.repository import GLib
import distutils
from distutils import dir_util, file_util
import os
import threading

import appconsts
import mltprofiles
import utils

USING_DOT_DIRS = 0 # This is only used during testing and if user forces .dot dirs.
USING_XDG_DIRS = 1

_user_dirs = USING_XDG_DIRS # Which dirs we are using

_copy_needed = False # If this true we need to copy data from dot dir to XDG dirs

_init_error = None
    
_dot_dir = None

_xdg_config_dir = None
_xdg_data_dir = None
_xdg_cache_dir = None

# --------------------------------------------------------- interface
def init():
    global _init_error
    
    # Get user folder locations
    global _dot_dir, _xdg_config_dir, _xdg_data_dir, _xdg_cache_dir
    # Dot folder
    _dot_dir = os.getenv("HOME") + "/.flowblade/"
    # XDG folders
    _xdg_config_dir = os.path.join(GLib.get_user_config_dir(), "flowblade")
    _xdg_data_dir = os.path.join(GLib.get_user_data_dir(), "flowblade")
    _xdg_cache_dir = os.path.join(GLib.get_user_cache_dir(), "flowblade")

    # Make sure XDG dirs data is available and usable by trying to create XDG folders
    try:
        _maybe_create_xdg_dirs()
    except Exception as e:
        _init_error = "Error message: " + str(e) + "\n\n"
        _init_error += "XDG Config dir: " + _xdg_config_dir + "\n"
        _init_error += "XDG Data dir: " + _xdg_data_dir + "\n"
        _init_error += "XDG Cache dir: " + _xdg_cache_dir + "\n"
        return
    
    # Determine if this a clean install or do we need to copy files fron dot dir to XDG dirs
    # We think existance of prefs files will tell us what the state of the system is.
    _dot_prefs_file_exists = os.path.exists(_dot_dir + "prefs" )
    _xdg_prefs_file_exists = os.path.exists(_xdg_config_dir + "/prefs")

    # If previous install exits and no data in XDG dirs, we need to copy existing data.
    if _dot_prefs_file_exists == True and _xdg_prefs_file_exists == False:
        print("userfolders.init(): .flowblade/ data exists, we need to copy to XDG folders.")
        global _copy_needed
        _copy_needed = True
    else:
        print("XDG user data exists.")

    # Set folders and maybe create them
    global _user_dirs
    
    _user_dirs = USING_XDG_DIRS
     
# --------------------------------------------------------- dirs paths
def get_config_dir():
    return _xdg_config_dir + "/"

def get_data_dir():
    return _xdg_data_dir + "/"

def get_cache_dir():
    return _xdg_cache_dir + "/"

def get_render_dir():
    return get_data_dir() + appconsts.RENDERED_CLIPS_DIR

def get_hidden_screenshot_dir_path():
    return get_cache_dir() + "screenshot/"

#------------------------------------------------------ state functions
def data_copy_needed():
    return _copy_needed

def get_init_error():
    return _init_error

# ---------------------------------------------------------------- internal functions       
def _maybe_create_xdg_dirs():

    # ---------------------- CONFIG
    # Prefs and recents files
    if not os.path.exists(_xdg_config_dir):
        print("CREATED XDG CONFIG DIR.")
        os.mkdir(_xdg_config_dir)

    # --------------------- DATA
    # Data that can break projects and cannot be regerated by app
    # Data root folder
    if not os.path.exists(_xdg_data_dir):
        print("CREATED XDG DATA DIR.")
        os.mkdir(_xdg_data_dir)
    # Data individual folders
    if not os.path.exists(get_data_dir() + appconsts.USER_PROFILES_DIR):
        os.mkdir(get_data_dir() + appconsts.USER_PROFILES_DIR)
    if not os.path.exists(get_render_dir()):
        os.mkdir(get_render_dir())
    if not os.path.exists(get_data_dir() + appconsts.TLINE_RENDERS_DIR):
        os.mkdir(get_data_dir() + appconsts.TLINE_RENDERS_DIR)
    if not os.path.exists(get_data_dir() + appconsts.CONTAINER_CLIPS_DIR):
        os.mkdir(get_data_dir() + appconsts.CONTAINER_CLIPS_DIR)
    if not os.path.exists(get_data_dir() + appconsts.CONTAINER_CLIPS_UNRENDERED):
        os.mkdir(get_data_dir() + appconsts.CONTAINER_CLIPS_UNRENDERED)
    if not os.path.exists(get_render_dir() +  "/" + appconsts.PROXIES_DIR):
        os.mkdir(get_render_dir() +  "/" + appconsts.PROXIES_DIR)


    #----------------- CACHE
    # Data that can be regerated by app or is transient
    # Cache root folder
    if not os.path.exists(_xdg_cache_dir):
        print("CREATED XDG CACHE DIR.")
        os.mkdir(_xdg_cache_dir)
    # Cache individual folders
    if not os.path.exists(get_cache_dir() + appconsts.AUTOSAVE_DIR):
        os.mkdir(get_cache_dir() + appconsts.AUTOSAVE_DIR)
    if not os.path.exists(get_cache_dir() + appconsts.THUMBNAILS_DIR):
        os.mkdir(get_cache_dir() + appconsts.THUMBNAILS_DIR)
    if not os.path.exists(get_cache_dir() + appconsts.GMIC_DIR):
        os.mkdir(get_cache_dir() + appconsts.GMIC_DIR)
    if not os.path.exists(get_cache_dir() + appconsts.MATCH_FRAME_DIR):
        os.mkdir(get_cache_dir() + appconsts.MATCH_FRAME_DIR)
    if not os.path.exists(get_cache_dir() + appconsts.AUDIO_LEVELS_DIR):
        os.mkdir(get_cache_dir() + appconsts.AUDIO_LEVELS_DIR)
    if not os.path.exists(get_cache_dir() + appconsts.TRIM_VIEW_DIR):
        os.mkdir(get_cache_dir() + appconsts.TRIM_VIEW_DIR)
    if not os.path.exists(get_cache_dir() + appconsts.BATCH_DIR):
        os.mkdir(get_cache_dir() + appconsts.BATCH_DIR)
    if not os.path.exists(get_hidden_screenshot_dir_path()):
        os.mkdir(get_hidden_screenshot_dir_path())


# --------------------------------------------------------------- copying existing data to XDG folders
class XDGCopyThread(threading.Thread):
    
    def __init__(self, dialog, completed_callback):
        self.dialog = dialog
        self.completed_callback = completed_callback
        threading.Thread.__init__(self)

    def run(self):
        _copy_data_from_dot_folders_xdg_folders()
        self.completed_callback(self.dialog)
        
def _copy_data_from_dot_folders_xdg_folders():
    # ---------------------- CONFIG
    print("Copying CONFIG...")
    file_util.copy_file(_dot_dir + "prefs", get_config_dir() + "prefs", verbose=1)
    file_util.copy_file(_dot_dir + "recent", get_config_dir() + "recent", verbose=1)
    
    # --------------------- DATA
    print("Copying DATA...")
    dir_util.copy_tree(_dot_dir + appconsts.USER_PROFILES_DIR, get_data_dir() + appconsts.USER_PROFILES_DIR, verbose=0)
    dir_util.copy_tree(_dot_dir + appconsts.RENDERED_CLIPS_DIR, get_render_dir(), verbose=1)
    
    # --------------------- CACHE
    print("CACHE DATA WILL BE LOST...")

    print("XDG Copy done.")
