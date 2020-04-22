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
import xml.dom.minidom

import appconsts
import editorpersistance
import respaths
import userfolders

# Inside hidden user folder
USER_PROFILES_DIR = appconsts.USER_PROFILES_DIR
DEFAULT_DEFAULT_PROFILE = "HD 1080p 30 fps"

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

    user_profiles_dir = userfolders.get_data_dir() + USER_PROFILES_DIR
    _user_profiles = _load_profiles_list(user_profiles_dir)
    _load_factory_profiles()

    _profile_list = _factory_profiles + _user_profiles

    _profile_list.sort(key=_sort_profiles)
    _factory_profiles.sort(key=_sort_profiles)
    _hidden_factory_profiles.sort(key=_sort_profiles)
    _user_profiles.sort(key=_sort_profiles)

def _load_profiles_list(dir_path):
    load_profiles = []
    file_list = os.listdir(dir_path)
    for fname in file_list:
        ## Feb-2017 - SvdB - Filter out duplicate profiles based on profile name
        found_duplicate = False
        
        file_path = dir_path + fname
        profile = mlt.Profile(file_path)
        profile.file_path = file_path
        load_profiles.append([profile.description(), profile])

        # Feb-2017 - SvdB - Filter out duplicate profiles based on profile name
        for enu_count, prof in enumerate(load_profiles):
            for prof_idx, prof_name in enumerate(prof):
                if prof_name == profile.description():
                    found_duplicate = True
        if found_duplicate == False:
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

def get_profile_index_for_profile(test_profile):
    for i in range(0, len(_profile_list)):
        fname, profile = _profile_list[i]
        if profile.description() == test_profile.description():
            return i
    
    return -1 # not found
    
def get_default_profile():
    return get_profile_for_index(get_default_profile_index())

def get_default_profile_index():
    """
    We're making sure here that something is returned as default profile even if user may have removed some profiles.
    """
    def_profile_index = get_index_for_name(editorpersistance.prefs.default_profile_name)
    if def_profile_index == -1:
        print("default profile from prefs not found")
        def_profile_index = get_index_for_name(DEFAULT_DEFAULT_PROFILE)
        def_profile_name =  DEFAULT_DEFAULT_PROFILE
        if def_profile_index == -1:
            def_profile_index = 0
            def_profile_name, profile = _profile_list[def_profile_index]
            print("DEFAULT_DEFAULT_PROFILE deleted returning first profile")
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

def get_profile_node(profile):
    node_str = '<profile description="' +  profile.description() + '" '
    node_str += 'width="' + str(profile.width()) + '" '
    node_str += 'height="' +  str(profile.height()) + '" '
    if profile.progressive() == True:
        prog_val = "1"
    else:
        prog_val = "0"
    node_str += 'progressive="' + prog_val + '" '
    node_str += 'sample_aspect_num="' + str(profile.sample_aspect_num()) + '" '
    node_str += 'sample_aspect_den="' + str(profile.sample_aspect_den()) + '" '
    node_str += 'display_aspect_num="' + str(profile.display_aspect_num()) + '" '
    node_str += 'display_aspect_den="' + str(profile.display_aspect_den()) + '" '
    node_str += 'frame_rate_num="' + str(profile.frame_rate_num()) + '" '
    node_str += 'frame_rate_den="' + str(profile.frame_rate_den()) + '" '
    node_str += 'colorspace="' + str(profile.colorspace()) + '"/>'

    return node_str

def is_mlt_xml_profile_match_to_profile(mlt_xml_path, profile):
    mlt_xml_doc = xml.dom.minidom.parse(mlt_xml_path)
    try:
        profile_node = mlt_xml_doc.getElementsByTagName("profile")[0]
    except:
        print("no profile node")
        return (False, "Unknown")
    
    match = True
    if profile_node.getAttribute("description") != profile.description():
        match = False
    if profile_node.getAttribute("width") != str(profile.width()):
        match = False
    if profile_node.getAttribute("height") != str(profile.height()):
        match = False
    if profile.progressive() == True:
        prog_val = "1"
    else:
        prog_val = "0"
    if profile_node.getAttribute("progressive") != prog_val:
        match = False
    if profile_node.getAttribute("sample_aspect_num") != str(profile.sample_aspect_num()):
        match = False
    if profile_node.getAttribute("sample_aspect_den") != str(profile.sample_aspect_den()):
        match = False
    if profile_node.getAttribute("display_aspect_num") != str(profile.display_aspect_num()):
        match = False
    if profile_node.getAttribute("display_aspect_den") != str(profile.display_aspect_den()):
        match = False
    if profile_node.getAttribute("frame_rate_num") != str(profile.frame_rate_num()):
        match = False
    if profile_node.getAttribute("frame_rate_den") != str(profile.frame_rate_den()):
        match = False
    if profile_node.getAttribute("colorspace") != str(profile.colorspace()):
        match = False

    return (match, profile_node.getAttribute("description"))


def get_closest_matching_profile_index(producer_info):
    # producer_info is dict from utils.get_file_producer_info
    width = producer_info["width"]
    height = producer_info["height"]
    fps_num =  producer_info["fps_num"]
    fps_den = producer_info["fps_den"]
    progressive = producer_info["progressive"]
    fps = round(float(float(fps_num)/float(fps_den)), 1)
    fps_2 = round(float(float(fps_num)/float(fps_den)), 2) # We added as a fix later for #290
    
    # We calculate match score for all available profiles and return 
    # the one with the highest score
    current_match_index = -1
    current_match_score = 0
    for i in range(0, len(_profile_list)):
        match_score = 0
        name, profile = _profile_list[i]

        prof_width = profile.width()
        prof_height = profile.height()
        prof_fps_num =  profile.frame_rate_num()
        prof_fps_den = profile.frame_rate_den()
        prof_progressive = profile.progressive()
        prof_fps = round(float(float(prof_fps_num)/float(prof_fps_den)), 1)
        prof_fps_2 = round(float(float(prof_fps_num)/float(prof_fps_den)), 2) # We added this as a fix later for #290
        
        if width == prof_width and height == prof_height:
            match_score = match_score + 1000
        if (width * 2) < prof_width or (height * 2) < prof_height: # We some time got matches where given profile was hugely different size if other properties matched
            match_score = match_score - 500
        if fps == prof_fps:
            match_score = match_score + 100
        if fps_2 == prof_fps_2: # We added this as a fix later for #290
            match_score = match_score + 5
        if prof_progressive: # prefer progressive always
            match_score = match_score + 10
        if match_score > current_match_score:
            current_match_score = match_score
            current_match_index = i

    if current_match_index == -1:
        return get_default_profile_index()
    
    return current_match_index

def _sort_profiles(profile_item):
    a_desc, a_profile = profile_item
    return a_desc.lower()
