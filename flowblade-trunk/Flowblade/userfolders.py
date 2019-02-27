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


import appconsts

USING_DOT_DIRS = 0 # This is only used during testing and if user forces .dot dirs.
USING_XDG_DIRS = 1

_user_dirs = USING_DOT_DIRS

_xdg_prefs_file_exists = False
_dot_prefs_file_exists = False

_dot_dir = None

_xdg_config_dir = None
_xdg_data_dir = None
_xdg_cache_dir = None

# --------------------------------------------------------- interface
def init():
    error = None
    
    # Get user folder locations
    global _dot_dir, _xdg_config_dir, _xdg_data_dir, _xdg_cache_dir
    _dot_dir = os.getenv("HOME") + "/.flowblade/"
    
    _xdg_config_dir = os.path.join(GLib.get_user_config_dir(), "flowblade")
    _xdg_data_dir = os.path.join(GLib.get_user_data_dir(), "flowblade")
    _xdg_cache_dir = os.path.join(GLib.get_user_cache_dir(), "flowblade")

    # Testing 
    print _xdg_config_dir
    print _xdg_data_dir
    print _xdg_cache_dir

    # Determine what wxists in system
    global _xdg_prefs_file_exists, _dot_prefs_file_exists
    # We consider existance _dot_prefs_file_exists to mean tha an earlier installation exists.
    _dot_prefs_file_exists = os.path.exists(_dot_dir + "prefs" )
    _xdg_prefs_file_exists = os.path.exists(_xdg_config_dir + "/prefs")
    
    global _user_dirs
    # If clean install we use xdg dirs and never will use dot folders
    if _dot_prefs_file_exists == False:
        _user_dirs = USING_XDG_DIRS
    
    # testing
    _user_dirs = USING_DOT_DIRS

    if _user_dirs == USING_XDG_DIRS:
        success = _maybe_create_xdg_dirs()
        _copy_data_from_dot_folders_xdg_folders()
        print success

    return error

def get_config_dir():
    if _user_dirs == USING_XDG_DIRS:
        return _xdg_config_dir + "/"
    else:
        return _dot_dir

def get_data_dir():
    if _user_dirs == USING_XDG_DIRS:
        return _xdg_data_dir + "/"
    else:
        return _dot_dir

def get_cache_dir():
    if _user_dirs == USING_XDG_DIRS:
        return _xdg_cache_dir + "/"
    else:
        return _dot_dir

def get_render_dir():
    return get_data_dir() + appconsts.RENDERED_CLIPS_DIR

def get_hidden_screenshot_dir_path():
    return get_cache_dir() + "screenshot/"
    
# ---------------------------------------------------------------- internal functions
def _get_dot_dir_path():
    return os.getenv("HOME") + "/.flowblade/"


def _create_dot_dirs():

    user_dir = _dot_dir

    if not os.path.exists(user_dir):
        os.mkdir(user_dir)
    if not os.path.exists(user_dir + mltprofiles.USER_PROFILES_DIR):
        os.mkdir(user_dir + mltprofiles.USER_PROFILES_DIR)
    if not os.path.exists(user_dir + AUTOSAVE_DIR):
        os.mkdir(user_dir + AUTOSAVE_DIR)
    if not os.path.exists(user_dir + BATCH_DIR):
        os.mkdir(user_dir + BATCH_DIR)
    if not os.path.exists(user_dir + appconsts.AUDIO_LEVELS_DIR):
        os.mkdir(user_dir + appconsts.AUDIO_LEVELS_DIR)
    if not os.path.exists(utils.get_hidden_screenshot_dir_path()):
        os.mkdir(utils.get_hidden_screenshot_dir_path())
    if not os.path.exists(user_dir + appconsts.GMIC_DIR):
        os.mkdir(user_dir + appconsts.GMIC_DIR)
    if not os.path.exists(user_dir + appconsts.MATCH_FRAME_DIR):
        os.mkdir(user_dir + appconsts.MATCH_FRAME_DIR)
    if not os.path.exists(user_dir + appconsts.TRIM_VIEW_DIR):
        os.mkdir(user_dir + appconsts.TRIM_VIEW_DIR)




def _maybe_create_xdg_dirs():

    try:
        # ---------------------- CONFIG
        # Prefs and recents files
        if not os.path.exists(_xdg_config_dir):
            print "CREATED XDG CONFIG DIR."
            os.mkdir(_xdg_config_dir)

        # --------------------- DATA
        # Data stuff that can break projects and cannot be regerated by app
        # Data root folder
        if not os.path.exists(_xdg_data_dir):
            print "CREATED XDG DATA DIR."
            os.mkdir(_xdg_data_dir)
        # Data individual folders
        if not os.path.exists(get_data_dir() + appconsts.USER_PROFILES_DIR):
            os.mkdir(get_data_dir() + appconsts.USER_PROFILES_DIR)
        if not os.path.exists(get_render_dir()):
            os.mkdir(get_render_dir())
        
        #----------------- CACHE
        # Stuff that can be regerated by app or is transient
        # Cache root folder
        if not os.path.exists(_xdg_cache_dir):
            print "CREATED XDG CACHE DIR."
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
            
        return True
        
    except Exception as e:
        print str(e)
        return False


def _copy_data_from_dot_folders_xdg_folders():
    # ---------------------- CONFIG
    file_util.copy_file(_dot_dir + "prefs", get_config_dir() + "prefs", verbose=1)
    file_util.copy_file(_dot_dir + "recent", get_config_dir() + "recent", verbose=1)
    
    # --------------------- DATA
    dir_util.copy_tree(_dot_dir + appconsts.USER_PROFILES_DIR, get_data_dir() + appconsts.USER_PROFILES_DIR, verbose=0)
    dir_util.copy_tree(_dot_dir + appconsts.RENDERED_CLIPS_DIR, get_render_dir(), verbose=1)
    
    # --------------------- CACHE
    dir_util.copy_tree(_dot_dir + appconsts.AUTOSAVE_DIR, get_cache_dir() + appconsts.AUTOSAVE_DIR, verbose=1)
    dir_util.copy_tree(_dot_dir + appconsts.THUMBNAILS_DIR, get_cache_dir() + appconsts.THUMBNAILS_DIR, verbose=1)
    dir_util.copy_tree(_dot_dir + appconsts.GMIC_DIR, get_cache_dir() + appconsts.GMIC_DIR, verbose=1)
    dir_util.copy_tree(_dot_dir + appconsts.MATCH_FRAME_DIR, get_cache_dir() + appconsts.MATCH_FRAME_DIR, verbose=1)
    dir_util.copy_tree(_dot_dir + appconsts.AUDIO_LEVELS_DIR, get_cache_dir() + appconsts.AUDIO_LEVELS_DIR, verbose=1)
    dir_util.copy_tree(_dot_dir + appconsts.TRIM_VIEW_DIR, get_cache_dir() + appconsts.TRIM_VIEW_DIR, verbose=1)
    dir_util.copy_tree(_dot_dir + appconsts.BATCH_DIR, get_cache_dir() + appconsts.BATCH_DIR, verbose=1)


