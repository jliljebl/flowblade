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
import appconsts
import respaths
import os
import xml.etree.ElementTree as etree
import editorpersistance
import re


DEFAULT_SHORTCUTS_FILE = "flowblade.xml"
    
shortcut_files = []
shortcut_files_display_names = []
_keyboard_actions = {}
_keyboard_action_names = {}
_key_names = {}
_mod_names = {}


def load_shortcut_files():
    global shortcut_files, shortcut_files_display_names
    default_shortcuts_file_found = False

    for f in os.listdir(respaths.SHORTCUTS_PATH):
        format_error = True

        if f[-4:] == '.xml':
            # We have a valid file name. Now inspect the file for a valid format before loading it
            shortcuts = etree.parse(respaths.SHORTCUTS_PATH + f)
            # Verify if the file has the right format
            root = shortcuts.getroot()
            # Check the 'tag' is flowblade
            if root.tag == appconsts.SHORTCUTS_ROOT_TAG:
                # Check if this is a shortcuts file
                if root.get('file') == appconsts.SHORTCUTS_TAG:
                    # Get name and comments
                    file_len = len(f) - 4
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
            print "Shortcuts file " + f + " found, but ignored."

        if format_error:
            print "Shortcuts file " + f + " found, but has incorrect format."
    
    # Default shortcuts file always goes to index 0
    if default_shortcuts_file_found == True:# this is a bit unneccceasy, it is there unless someone destroys it manually
        shortcut_files.insert(0, DEFAULT_SHORTCUTS_FILE)
        shortcut_files_display_names.insert(0, "Flowblade Default")

    print "Valid shortcut files found: " + str(shortcut_files)

# Apr-2017 - SvdB - keyboard shortcuts
def load_shortcuts():
    _set_keyboard_action_names()
    _set_key_names()
    set_keyboard_shortcuts()

def set_keyboard_shortcuts():
    global _keyboard_actions
    prefs = editorpersistance.prefs
    print "Keyboard shortcuts file:",  editorpersistance.prefs.shortcuts
    _modifier_dict = {}

    # Make sure that whatever is in preferences is a valid file. If it's not in shortcut_files it's not valid
    if not prefs.shortcuts in shortcut_files:
        #print "The shortcuts file selected in preferences is not valid: " + prefs.shortcuts
        # print "Switching to defaults."
        return
    try:
        shortcuts = etree.parse(respaths.SHORTCUTS_PATH + prefs.shortcuts)
        # Verify if the file has the right format
        root = shortcuts.getroot()
        # Check the 'tag' is flowblade
        if root.tag == appconsts.SHORTCUTS_ROOT_TAG:
            # Check if this is a shortcuts file
            if root.get('file') == appconsts.SHORTCUTS_TAG:
                # Get name and comments
                print "Loading shortcuts: " + root.get('name')
                # We have good shortcuts file, destroy hardcoded defaults
                _keyboard_actions = {}
                # Now loop through all the events and assign them
                events = root.getiterator('event')
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
    except:
        print "Error opening shortcuts file:" + prefs.shortcuts

    #_print_shortcuts()

def get_shortcuts_xml_root_node(xml_file):
    try:
        shortcuts = etree.parse(respaths.SHORTCUTS_PATH + xml_file)
        return shortcuts.getroot()
    except:
        return None # This is handled at callsites

def get_shortcut_info(root, code):
    events = root.getiterator('event')
    for event in events:
        if event.get('code') == code:
            return (_key_names[event.text], _get_mod_string(event) + _keyboard_action_names[code]) 
    
    return (None, None)

def _get_mod_string(event):
    mod = event.get("modifier")
    if mod == "Any" or mod == None:
        return ""
    
    return _mod_names[mod]
 
def get_diff_to_defaults(xml_file):
    diff_str = ""
    test_root = get_shortcuts_xml_root_node(xml_file)
    def_root = get_shortcuts_xml_root_node(DEFAULT_SHORTCUTS_FILE)
    
    for code, action_name in _keyboard_action_names.iteritems():
        key_name_test, action_name = get_shortcut_info(test_root, code)
        key_name_def, action_name = get_shortcut_info(def_root , code)
    
        if key_name_def != key_name_test:
            diff_str = diff_str + action_name + " (" + key_name_test + ")    "
    
    return diff_str

def _set_keyboard_action_names():
    global _keyboard_action_names
    # Start with an empty slate
    _keyboard_action_names = {}
    _keyboard_action_names['mark_in'] = _("Set Mark In")
    _keyboard_action_names['mark_out'] =  _("Set Mark Out")
    _keyboard_action_names['play_pause'] = _("Start / Stop Playback")
    _keyboard_action_names['prev_cut'] = _("Prev Edit/Mark")
    _keyboard_action_names['next_cut'] = _("Next Edit/Mark")
    _keyboard_action_names['prev_frame'] =_("Prev Frame")
    _keyboard_action_names['next_frame'] = _("Next Frame")
    _keyboard_action_names['insert'] = _("Insert")
    _keyboard_action_names['append'] =  _("Append")
    _keyboard_action_names['slower'] = _("Backwards Faster")
    _keyboard_action_names['stop'] = _("Stop")
    _keyboard_action_names['faster'] =  _("Forward Faster")
    _keyboard_action_names['log_range'] = _("Log Marked Clip Range")
    _keyboard_action_names['resync'] = _("Resync selected Clip or Compositor")
    _keyboard_action_names['delete'] = _("Delete Selected Item")
    _keyboard_action_names['to_start'] = _("Go To Start")
    _keyboard_action_names['to_end'] = _("Go To End")
    _keyboard_action_names['3_point_overwrite'] = _("3 Point Overwrite")
    _keyboard_action_names['toggle_ripple'] = _("Trim Tool Ripple Mode On/Off")
    _keyboard_action_names['cut'] = _("Cut Clip")
    _keyboard_action_names['edit_mode_insert'] = _("Insert")
    _keyboard_action_names['edit_mode_overwrite'] =  _("Overwrite")
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
    _keyboard_action_names['sequence_split'] = ("Sequence Split")


def _set_key_names():
    global _key_names, _mod_names
    # Start with an empty slate
    _key_names = {}
    _key_names['i'] = "I"
    _key_names['o'] = "O"
    _key_names['space'] = _("SPACE")
    _key_names['down'] = _("Down Arrow")
    _key_names['up'] = _("Up Arrow")
    _key_names['left'] = _("Left Arrow")
    _key_names['right'] = _("Right Arrow")
    _key_names['y'] = "Y"
    _key_names['u'] = "U"
    _key_names['j'] = "J"
    _key_names['k'] = "K"
    _key_names['l'] = "L"
    _key_names['g'] = "G"
    _key_names['s'] = "S"
    _key_names['delete'] = _("Delete")
    _key_names['home'] = _("HOME")
    _key_names['end'] = _("END")
    _key_names['t'] = "T"
    _key_names['r'] = "R"
    _key_names['x'] = "X"
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
    _key_names['m'] = "M"
    _key_names['return'] = _("ENTER")
    _key_names['y'] = ("Y")
    _key_names['equal'] = _("=")

    _mod_names["ALT"] = _("Alt")
    _mod_names["SHIFT"] =  _("Shift")
    _mod_names["ALT+SHIFT"] = _("Alt + Shift")
    _mod_names["CONTROL"] = _("Control")
