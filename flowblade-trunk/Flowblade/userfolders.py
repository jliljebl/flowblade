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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""
from gi.repository import GLib
import os
import threading

import appconsts

_init_error = None

_xdg_config_dir = None
_xdg_data_dir = None
_xdg_cache_dir = None

# --------------------------------------------------------- interface
def init():
    global _init_error
    
    # Get user folder locations
    global _xdg_config_dir, _xdg_data_dir, _xdg_cache_dir

    # XDG folders
    _xdg_config_dir = os.path.join(GLib.get_user_config_dir(), "flowblade")
    _xdg_data_dir = os.path.join(GLib.get_user_data_dir(), "flowblade")
    _xdg_cache_dir = os.path.join(GLib.get_user_cache_dir(), "flowblade")

    print("XDG Config", _xdg_config_dir)
    print("XDG Data", _xdg_data_dir)
    print("XDG Cache",_xdg_cache_dir)

    # Make sure XDG dirs data is available and usable by trying to create XDG folders
    try:
        _maybe_create_xdg_dirs()
    except Exception as e:
        _init_error = "Error message: " + str(e) + "\n\n"
        _init_error += "XDG Config dir: " + _xdg_config_dir + "\n"
        _init_error += "XDG Data dir: " + _xdg_data_dir + "\n"
        _init_error += "XDG Cache dir: " + _xdg_cache_dir + "\n"
        return

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
    if not os.path.exists(get_data_dir() + appconsts.CONTAINER_CLIPS_DIR):
        os.mkdir(get_data_dir() + appconsts.CONTAINER_CLIPS_DIR)
    if not os.path.exists(get_data_dir() + appconsts.CONTAINER_CLIPS_UNRENDERED):
        os.mkdir(get_data_dir() + appconsts.CONTAINER_CLIPS_UNRENDERED)
    if not os.path.exists(get_render_dir() +  "/" + appconsts.PROXIES_DIR):
        os.mkdir(get_render_dir() +  "/" + appconsts.PROXIES_DIR)
    if not os.path.exists(get_data_dir()  +  "/" + appconsts.USER_SHORTCUTS_DIR):
        os.mkdir(get_data_dir()  +  "/" + appconsts.USER_SHORTCUTS_DIR)

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
    if not os.path.exists(get_cache_dir() + appconsts.AUDIO_LEVELS_DIR):
        os.mkdir(get_cache_dir() + appconsts.AUDIO_LEVELS_DIR)
    if not os.path.exists(get_cache_dir() + appconsts.TRIM_VIEW_DIR):
        os.mkdir(get_cache_dir() + appconsts.TRIM_VIEW_DIR)
    if not os.path.exists(get_cache_dir() + appconsts.BATCH_DIR):
        os.mkdir(get_cache_dir() + appconsts.BATCH_DIR)
    if not os.path.exists(get_hidden_screenshot_dir_path()):
        os.mkdir(get_hidden_screenshot_dir_path())
    if not os.path.exists(get_cache_dir() + appconsts.SCRIP_TOOL_DIR):
        os.mkdir(get_cache_dir() + appconsts.SCRIP_TOOL_DIR)
