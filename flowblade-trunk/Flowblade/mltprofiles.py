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
    global _profile_list,_factory_profiles, _hidden_factory_profiles, _user_profiles

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

