"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2013 Janne Liljeblad.

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

# Apr-2017 - SvdB - Functions to scan available shortcut files, validate and load them
import collections
import os
import xml.etree.ElementTree as etree
import re

import appconsts
import editorpersistance
import respaths
import userfolders


DEFAULT_SHORTCUTS_FILE = "flowblade.xml"
CUSTOM_SHORTCUTS_FILE_NAME_START = "custom_shortcuts_"

# It is not allowed to set these as custom shortcuts.
RESERVED_SHORTCUTS = [  ("left",[]), ("right",[]), ("up",[]), ("down",[]), ("c",["CTRL"]), ("1", []), \
                        ("2", []), ("3", []), ("4", []), ("5", []), ("6", []), ("7", []), ("8", []), ("9", []), ("0", []), \
                        ("delete", []), ("return", []), ("tab", []), ("c", ["CTRL"]), ("v", ["CTRL"]), ("v", ["CTRL", "ALT"]),  ("n", ["CTRL"]), \
                        ("s", ["CTRL"]), ("q", ["CTRL"]), ("z", ["CTRL"]), ("y", ["CTRL"]), ("o", ["CTRL"]), ("f11", []), ("kp_1", []), \
                        ("kp_2", []), ("kp_3", []), ("kp_4", []), ("kp_5", []), ("kp_6", []), ("kp_7", []), ("kp_8", []), ("kp_9", []), ("kp_0", [])]

shortcut_files = []
shortcut_files_display_names = []
_keyboard_actions = {}
_keyboard_action_names = {}
_key_names = {}
_mod_names = {}
_gtk_mod_names = {}
_editable = False

def load_shortcut_files():
    global shortcut_files, shortcut_files_display_names
    default_shortcuts_file_found = False
    loadable_shortcuts_files = os.listdir(respaths.SHORTCUTS_PATH) + os.listdir(userfolders.get_data_dir() + "/" + appconsts.USER_SHORTCUTS_DIR)

    for f in loadable_shortcuts_files:
        format_error = True

        if f[-4:] == '.xml':
            # Get full path for either presets file on user custom shortcuts file.
            full_path = _get_shortcut_file_fullpath(f)

            # We have a valid file name. Now inspect the file for a valid format before loading it
            shortcuts = etree.parse(full_path)
            # Verify if the file has the right format
            root = shortcuts.getroot()
            # Check the 'tag' is flowblade
            if root.tag == appconsts.SHORTCUTS_ROOT_TAG:
                # Check if this is a shortcuts file
                if root.get('file') == appconsts.SHORTCUTS_TAG:
                    # Default file is added last to always be at index 0
                    if f != DEFAULT_SHORTCUTS_FILE:
                        shortcut_files.append(f)
                        shortcut_files_display_names.append(root.get('name'))
                        format_error = False
                    else:
                        # This is added below to index 0
                        default_shortcuts_file_found = True
                        format_error = False
                        
        else:
            format_error = False
            print("Shortcuts file " + f + " found, but ignored.")

        if format_error:
            print("Shortcuts file " + f + " found, but has incorrect format.")
    
    # Default shortcuts file always goes to index 0
    if default_shortcuts_file_found == True:# this is a bit unnecessary, it is there unless someone destroys it manually
        shortcut_files.insert(0, DEFAULT_SHORTCUTS_FILE)
        shortcut_files_display_names.insert(0, "Flowblade Default")

    print("Valid shortcut files found: " + str(shortcut_files))

# Apr-2017 - SvdB - keyboard shortcuts
def load_shortcuts():
    _set_keyboard_action_names()
    _set_key_names()
    set_keyboard_shortcuts()

def set_keyboard_shortcuts():
    global _keyboard_actions, _editable
    prefs = editorpersistance.prefs
    print("Keyboard shortcuts file:",  editorpersistance.prefs.shortcuts)
    _modifier_dict = {}

    # Make sure that whatever is in preferences is a valid and exists file. If it's not in shortcut_files it's not valid
    if not prefs.shortcuts in shortcut_files:
        # Load default shortcuts.
        prefs.shortcuts = DEFAULT_SHORTCUTS_FILE
        editorpersistance.save()
        set_keyboard_shortcuts()
        return
    try:
        shortcuts = etree.parse(_get_shortcut_file_fullpath(prefs.shortcuts))
        # Verify if the file has the right format
        root = shortcuts.getroot()
        # Check the 'tag' is flowblade
        if root.tag == appconsts.SHORTCUTS_ROOT_TAG:
            # Check if this is a shortcuts file
            if root.get('file') == appconsts.SHORTCUTS_TAG:
                # Get name and comments
                # We have good shortcuts file, destroy hardcoded defaults
                _keyboard_actions = {}
                # Now loop through all the events and assign them
                events = root.iter('event')
                for event in events:
                    # Retrieve any previous _modifier_dict values
                    try:
                        _modifier_dict = _keyboard_actions[event.text]
                    except:
                        _modifier_dict = {}
                    # Build up the _modifier_dict
                    # NB: The text string representing the modifiers is sorted alphabetically and converted to lower
                    # case. It is also stripped of spaces.
                    # ''.join(sorted(string)) will return the sorted string (sorted returns an array, join converts
                    # it to a string)
                    # re.sub('[\s]','',string) will remove the spaces
                    # .lower() will convert it all to lower space.
                    # to easily compare with any entered combo of the modifiers. In fact, CTRL+ALT becomes the
                    # same as ALT+CTRL and Alt+Ctrl- it will all be +acllrtt
                    if event.get('modifiers') == None:
                        _modifier_dict[''.join(sorted(re.sub('[\s]','','None'.lower())))] = event.get('code')
                    else:
                        _modifier_dict[''.join(sorted(re.sub('[\s]','',event.get('modifiers').lower())))] = event.get('code')
                    _keyboard_actions[event.text] = _modifier_dict
        _editable = root.get('editable')
    except:
        print("Error opening shortcuts file:" + prefs.shortcuts)

    #_print_shortcuts()


def update_custom_shortcuts():
    # If new shortcuts have been added and user is using custom shortcuts when updating, we need to update custom shortcuts.
    custom_files = os.listdir(userfolders.get_data_dir() + "/" + appconsts.USER_SHORTCUTS_DIR)
    for custom_prefs_file in custom_files:
        _update_custom_xml_file_nodes_to_default(_get_shortcut_file_fullpath(custom_prefs_file))

def _update_custom_xml_file_nodes_to_default(custom_xml_file_path):
    pref_shortcuts = etree.parse(custom_xml_file_path)
    default_shortcuts = etree.parse(_get_shortcut_file_fullpath(DEFAULT_SHORTCUTS_FILE))
    pref_root = pref_shortcuts.getroot()
    default_root = default_shortcuts.getroot()
    pref_dict = _get_events_dict(pref_root)
    default_dict = _get_events_dict(default_root)

    changed = False
    for code in default_dict:
        try:
            pref_event = pref_dict[code]
        except:
            print( "Adding missing keyevent ", code, " to custom shortcuts file ", custom_xml_file_path)
            default_event = default_dict[code]
            new_pref_event = etree.fromstring(etree.tostring(default_event))
            pref_shortcuts_node = pref_root.find("shortcuts")
            pref_shortcuts_node.append(new_pref_event)
            changed = True
    
    if changed == True:
        print("Writing ", custom_xml_file_path)
        pref_shortcuts.write(custom_xml_file_path)

# code -> xml.etree.ElementTree.Element
def _get_events_dict(xml_root):
    events_dict = {}
    events = xml_root.iter('event')
    for event in events:
        events_dict[event.get('code')] = event

    return events_dict

def get_root():
    shortcuts = etree.parse(_get_shortcut_file_fullpath(editorpersistance.prefs.shortcuts))
    return shortcuts.getroot()

def get_shortcut_info_for_keyname_and_modlist(key_val_name, mod_list):
    out_str = ""
    for mod in mod_list:
        out_str += _mod_names[mod]
        out_str += " + "
        
    key_name = _key_names[key_val_name]
    out_str += key_name
    return out_str

def get_shortcuts_xml_root_node(xml_file):
    try:
        shortcuts = etree.parse(_get_shortcut_file_fullpath(xml_file))
        return shortcuts.getroot()
    except:
        return None # This is handled at callsites

def get_shortcuts_editable():
    if _editable == "True":
        return True
    else:
        return False

def create_custom_shortcuts_xml(name):
    shortcuts = etree.parse( _get_shortcut_file_fullpath(editorpersistance.prefs.shortcuts))

    # Get numbered custom shortuts file path
    lowest_ver_number = 0
    custom_files = os.listdir(userfolders.get_data_dir() + "/" + appconsts.USER_SHORTCUTS_DIR)
    for f in custom_files:
        dot_pos = f.find(".")
        num_str = f[len(CUSTOM_SHORTCUTS_FILE_NAME_START):dot_pos]
        if int(num_str) > lowest_ver_number:
            lowest_ver_number = int(num_str) 
    
    new_custom_file_name = CUSTOM_SHORTCUTS_FILE_NAME_START + str(lowest_ver_number + 1) + ".xml"
    new_shortcuts_file_path = userfolders.get_data_dir() + "/" + appconsts.USER_SHORTCUTS_DIR + new_custom_file_name
        
    # Verify if the file has the right format
    root = shortcuts.getroot()
    root.set('name', name)
    root.set('editable', 'True')
    shortcuts.write(new_shortcuts_file_path)

    return new_custom_file_name

def delete_active_custom_shortcuts_xml():
    root = get_root()
    name = root.get('name')
    shortcut_files_display_names.remove(name)
    shortcut_files.remove(editorpersistance.prefs.shortcuts)
    
    file_path = _get_shortcut_file_fullpath(editorpersistance.prefs.shortcuts)
    os.remove(file_path)
                
    editorpersistance.prefs.shortcuts = DEFAULT_SHORTCUTS_FILE
    editorpersistance.save()

def change_custom_shortcut(code, key_val_name, mods_list, add_event=False):
    shortcuts_file = _get_shortcut_file_fullpath(editorpersistance.prefs.shortcuts)
    shortcuts = etree.parse(shortcuts_file)
    root = shortcuts.getroot()

    # Add new element if so ordered.
    if add_event == True:
        new_event = etree.Element("event")    
        new_event.text = key_val_name
        new_event.set('code', code)
        shortcuts_node = root.find("shortcuts")
        shortcuts_node.append(new_event)
        
    events = root.iter('event')
    
    target_event = None
    for event in events:
        if event.get('code') == code:
            target_event = event
            break
    
    if target_event == None:
        # we really should not hit this
        print("!!! no event for action name ", code, editorpersistance.prefs.shortcuts)
        return
    
    mods_str = ""
    for mod in mods_list:
        mods_str += mod
        mods_str += "+"
    mods_str = mods_str[0:-1]

    target_event.text = key_val_name
    if len(mods_str) == 0:
        try:
            target_event.attrib.pop("modifiers")
        except:
            pass
    else:
        target_event.set("modifiers", mods_str)

    shortcuts.write(shortcuts_file)

def is_blocked_shortcut(key_val, mods_list):
    for reserved in RESERVED_SHORTCUTS:
        r_key_val, r_mods_list = reserved
        if len(r_mods_list) == 0 and key_val == r_key_val:
            return True
        if key_val == r_key_val:
            if collections.Counter(mods_list) == collections.Counter(r_mods_list):
                return True
                
    return False

def get_shortcut_info(root, code):
    events = root.iter('event')

    for event in events:
        if event.get('code') == code:
            mod_name = _get_mod_string(event)
            if mod_name != "":
                mod_name = mod_name + " + "
            return (mod_name + _key_names[event.text], _keyboard_action_names[code]) 
    
    return (None, None)

def get_shortcut_gtk_code(root, code):
    events = root.iter('event')

    for event in events:
        if event.get('code') == code:
            gtk_code = ""
            mod = event.get("modifiers")
            if mod != "Any" and mod != None:
                gtk_code += _gtk_mod_names[mod]
                
            gtk_code += event.text.upper()
            return gtk_code

    return None

def _get_mod_string(event):
    mod = event.get("modifiers")
    if mod == "Any" or mod == None:
        return ""
    
    return _mod_names[mod]

def get_diff_to_defaults(xml_file):
    diff_str = ""
    test_root = get_shortcuts_xml_root_node(xml_file)
    def_root = get_shortcuts_xml_root_node(DEFAULT_SHORTCUTS_FILE)
    
    for code, action_name in _keyboard_action_names.items():
        key_name_test, action_name = get_shortcut_info(test_root, code)
        key_name_def, action_name = get_shortcut_info(def_root, code)
        if key_name_def != key_name_test:
            diff_str = diff_str + action_name + " (" + key_name_test + ")    "
    
    return diff_str

def _get_shortcut_file_fullpath(f):
    full_path = respaths.SHORTCUTS_PATH + f
    if os.path.isfile(full_path) == False:
        full_path = userfolders.get_data_dir() + "/" + appconsts.USER_SHORTCUTS_DIR + f
    return full_path

def _set_keyboard_action_names():
    global _keyboard_action_names
    # Start with an empty slate
    _keyboard_action_names = {}
    _keyboard_action_names['mark_in'] = _("Set Mark In")
    _keyboard_action_names['mark_out'] =  _("Set Mark Out")
    _keyboard_action_names['to_mark_in'] =  _("Go To Mark In")
    _keyboard_action_names['to_mark_out'] =  _("Go To Mark Out")
    _keyboard_action_names['clear_io_marks'] =  _("Clear In/Out Marks")
    _keyboard_action_names['play_pause'] = _("Start / Stop Playback")
    _keyboard_action_names['prev_cut'] = _("Prev Edit/Mark")
    _keyboard_action_names['next_cut'] = _("Next Edit/Mark")
    _keyboard_action_names['prev_frame'] =_("Prev Frame")
    _keyboard_action_names['next_frame'] = _("Next Frame")
    _keyboard_action_names['insert'] = _("Insert")
    _keyboard_action_names['append'] =  _("Append")
    _keyboard_action_names['append_from_bin'] = _("Append Selected Media From Bin")
    _keyboard_action_names['slower'] = _("Backwards Faster")
    _keyboard_action_names['stop'] = _("Stop")
    _keyboard_action_names['faster'] =  _("Forward Faster")
    _keyboard_action_names['log_range'] = _("Log Marked Clip Range")
    _keyboard_action_names['resync'] = _("Resync selected Clip or Compositor")
    _keyboard_action_names['delete'] = _("Delete Selected Item")
    _keyboard_action_names['lift'] = _("Lift Selected Item")
    _keyboard_action_names['to_start'] = _("Go To Start")
    _keyboard_action_names['to_end'] = _("Go To End")
    _keyboard_action_names['3_point_overwrite'] = _("3 Point Overwrite")
    _keyboard_action_names['overwrite_range'] = _("Overwrite Range")
    _keyboard_action_names['toggle_ripple'] = _("Trim Tool Ripple Mode On/Off")
    _keyboard_action_names['cut'] = _("Cut Active Tracks")
    _keyboard_action_names['cut_all'] = _("Cut All Tracks")
    _keyboard_action_names['edit_mode_insert'] = _("Insert")
    _keyboard_action_names['edit_mode_overwrite'] = _("Overwrite")
    _keyboard_action_names['edit_mode_trim'] =  _("Trim")
    _keyboard_action_names['edit_mode_roll'] = _("Roll")
    _keyboard_action_names['edit_mode_slip'] = _("Slip")
    _keyboard_action_names['edit_mode_spacer'] = _("Spacer")
    _keyboard_action_names['edit_mode_box'] =  _("Box")
    _keyboard_action_names['zoom_out'] = _("Zoom Out")
    _keyboard_action_names['zoom_in'] =  _("Zoom In")
    _keyboard_action_names['switch_monitor'] = _("Switch Monitor Source")
    _keyboard_action_names['add_marker'] = _("Add Mark")
    _keyboard_action_names['enter_edit'] =  _("Complete Keyboard Trim Edit")
    _keyboard_action_names['nudge_back'] =  _("Nudge Move Selection Back 1 Frame")
    _keyboard_action_names['nudge_forward'] =  _("Nudge Move Selection Forward 1 Frame")
    _keyboard_action_names['nudge_back_10'] =  _("Nudge Move Selection Back 10 Frames")
    _keyboard_action_names['nudge_forward_10'] =  _("Nudge Move Selection Forward 10 Frames")
    _keyboard_action_names['open_next'] =  _("Open Next Media Item In Monitor")
    _keyboard_action_names['clear_filters'] = _("Clear Filters")
    _keyboard_action_names['sync_all'] = _("Sync All Compositors")
    _keyboard_action_names['select_next'] = _("Open Next Clip In Filter Editor")
    _keyboard_action_names['select_prev'] = _("Open Previous Clip In Filter Editor")
    _keyboard_action_names['play_pause_loop_marks'] = _("Play / Pause Mark In to Mark Out Loop")
    _keyboard_action_names['trim_start'] = _("Trim Clip Start To Playhead")
    _keyboard_action_names['trim_end'] = _("Trim Clip End To Playhead")

def _set_key_names():
    global _key_names, _mod_names, _gtk_mod_names
    # Start with an empty slate
    _key_names = {}
    _key_names['i'] = "I"
    _key_names['a'] = "A"
    _key_names['o'] = "O"
    _key_names['y'] = "Y"
    _key_names['u'] = "U"
    _key_names['j'] = "J"
    _key_names['k'] = "K"
    _key_names['l'] = "L"
    _key_names['n'] = "N"
    _key_names['g'] = "G"
    _key_names['s'] = "S"
    _key_names['p'] = "P"
    _key_names['t'] = "T"
    _key_names['r'] = "R"
    _key_names['x'] = "X"
    _key_names['y'] = "Y"
    _key_names['m'] = "M"
    _key_names['q'] = "Q"
    _key_names['w'] = "W"
    _key_names['e'] = "E"
    _key_names['d'] = "D"
    _key_names['f'] = "F"
    _key_names['h'] = "H"
    _key_names['z'] = "Z"
    _key_names['c'] = "C"
    _key_names['v'] = "V"
    _key_names['b'] = "B"
    _key_names['space'] = _("SPACE")
    _key_names['down'] = _("Down Arrow")
    _key_names['up'] = _("Up Arrow")
    _key_names['left'] = _("Left Arrow")
    _key_names['right'] = _("Right Arrow")
    _key_names['delete'] = _("Delete")
    _key_names['home'] = _("HOME")
    _key_names['end'] = _("END")
    _key_names['1'] = "1"
    _key_names['kp_end'] = _("Key Pad END")
    _key_names['kp_1'] = _("Key Pad 1")
    _key_names['2'] = "2"
    _key_names['kp_2'] = _("Key Pad 2")
    _key_names['kp_down'] = _("Key Pad Down Arrow")
    _key_names['3'] = "3"
    _key_names['kp_3'] = _("Key Pad 2")
    _key_names['kp_next'] = _("Key Pad 2")
    _key_names['4'] = "4"
    _key_names['kp_4'] = _("Key Pad 4")
    _key_names['kp_left'] = _("Key Pad Left Arrow")
    _key_names['5'] = "5"
    _key_names['kp_5'] = _("Key Pad 5")
    _key_names['kp_begin'] = _("Key Pad Begin")
    _key_names['6'] = "6"
    _key_names['kp_6'] = _("Key Pad 6")
    _key_names['kp_right'] =_("Key Pad Right Arrow")
    _key_names['7'] = "7"
    _key_names['kp_7'] = _("Key Pad 7")
    _key_names['kp_home'] = _("Key Pad HOME")
    _key_names['minus'] = "-"
    _key_names['plus'] = "+"
    _key_names['tab'] = _("TAB")
    _key_names['return'] = _("ENTER")
    _key_names['equal'] = _("=")
    _key_names['comma'] = _(",")
    _key_names['period'] = _(".")
    
    _mod_names["ALT"] = _("Alt")
    _mod_names["SHIFT"] =  _("Shift")
    _mod_names["ALT+SHIFT"] = _("Alt + Shift")
    _mod_names["CTRL+ALT"] = _("Control + Alt")
    _mod_names["CTRL+SHIFT"] = _("Control + Shift")
    _mod_names["CTRL+ALT+SHIFT"] = _("Control + Alt + Shift")
    _mod_names["CTRL"] = _("Control")

    _gtk_mod_names["ALT"] = _("<alt>")
    _gtk_mod_names["SHIFT"] =  _("<shift>")
    _gtk_mod_names["ALT+SHIFT"] = _("<alt><shift>")
    _gtk_mod_names["CTRL+ALT"] = _("<control><alt>")
    _gtk_mod_names["CTRL+SHIFT"] = _("<control><shift>")
    _gtk_mod_names["CTRL+ALT+SHIFT"] = _("<control><alt><shift>")
    _gtk_mod_names["CTRL"] = _("<control>")
