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
MLT framework profiles. 
"""
import os
import mlt

import editorpersistance
import respaths
import utils

# Inside hidden user folder
USER_PROFILES_DIR = "user_profiles/"
DEFAULT_DEFAULT_PROFILE = "DV/DVD PAL"

# List of mlt profiles
_profile_list = []
_factory_profiles = []
_hidden_factory_profiles = []
_user_profiles = []


def load_profile_list():
    """ 
    Creates a list of MLT profile objects.
    Called at app start.
    """
    global _profile_list,_factory_profiles, _hidden_factory_profiles, _user_profiles, _proxy_profiles

    user_profiles_dir = utils.get_hidden_user_dir_path() + USER_PROFILES_DIR
    _user_profiles = _load_profiles_list(user_profiles_dir)
    _load_factory_profiles()

    _profile_list = _factory_profiles + _user_profiles

    _profile_list.sort(_sort_profiles)
    _factory_profiles.sort(_sort_profiles)
    _hidden_factory_profiles.sort(_sort_profiles)
    _user_profiles.sort(_sort_profiles)

def _load_profiles_list(dir_path):
    load_profiles = []
    file_list = os.listdir(dir_path)
    for fname in file_list:
        file_path = dir_path + fname
        profile = mlt.Profile(file_path)
        profile.file_path = file_path
        load_profiles.append([profile.description(), profile])
    
    return load_profiles

def _load_factory_profiles():
    global _factory_profiles, _hidden_factory_profiles
    factory_profiles_all = _load_profiles_list(respaths.PROFILE_PATH)
    visible_profiles = []
    hidden_profiles = []
    for profile in factory_profiles_all:
        blocked = False
        for hidden_name in editorpersistance.prefs.hidden_profile_names:
            if hidden_name == profile[0]:
                blocked = True
        if blocked == False:
            visible_profiles.append(profile)
        else:
            hidden_profiles.append(profile)
    _factory_profiles = visible_profiles
    _hidden_factory_profiles = hidden_profiles
    
def get_profiles():
    return _profile_list

def get_factory_profiles():
    return _factory_profiles

def get_hidden_profiles():
    return _hidden_factory_profiles

def get_user_profiles():
    return _user_profiles

def get_profile(profile_name):
    for fname, profile in _profile_list:
        if profile_name == profile.description():
            return profile
    
def get_profile_for_index(index):
    profile_name, profile = _profile_list[index]
    return profile

def get_profile_name_for_index(index):
    profile_name, profile = _profile_list[index]
    return profile_name
    
def get_default_profile():
    return get_profile_for_index(get_default_profile_index())

def get_default_profile_index():
    """
    We're making sure here that something is returned as default profile even if user may have removed some profiles.
    """
    def_profile_index = get_index_for_name(editorpersistance.prefs.default_profile_name)
    if def_profile_index == -1:
        print "default profile from prefs nor found"
        def_profile_index = get_index_for_name(DEFAULT_DEFAULT_PROFILE)
        def_profile_name =  DEFAULT_DEFAULT_PROFILE
        if def_profile_index == -1:
            def_profile_index = 0
            def_profile_name, profile = _profile_list[def_profile_index]
            print "DEFAULT_DEFAULT_PROFILE deleted returning first profile"
        editorpersistance.prefs.default_profile_name = def_profile_name
        editorpersistance.save()
    return def_profile_index
    
def get_index_for_name(lookup_profile_name):
    # fails if two profiles have same names
    for i in range(0, len(_profile_list)):
        profile = _profile_list[i]
        if lookup_profile_name == profile[0]:
            return i
    return -1

def _sort_profiles(a, b):
    a_desc, a_profile = a
    b_desc, b_profile = b

    if a_desc.lower() < b_desc.lower():
        return -1
    elif a_desc.lower() > b_desc.lower():
        return 1
    else:
        return 0

