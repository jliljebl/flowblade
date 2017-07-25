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

shortcut_files = []
shortcut_files_display_names = []
_keyboard_actions = {}

def load_shortcut_files():
    global shortcut_files, shortcut_files_display_names
    try:
        for file in os.listdir(respaths.SHORTCUTS_PATH):
            format_error = True
            # Don't allow selection of the sample file
            if file[-4:] == '.xml':
                if file != appconsts.SHORTCUTS_DEFAULT_XML + '.xml':
                    # We have a valid file name. Now inspect the file for a valid format before loading it
                    shortcuts = etree.parse(respaths.SHORTCUTS_PATH + file)
                    # Verify if the file has the right format
                    root = shortcuts.getroot()
                    # Check the 'tag' is flowblade
                    if root.tag == appconsts.SHORTCUTS_ROOT_TAG:
                        # Check if this is a shortcuts file
                        if root.get('file') == appconsts.SHORTCUTS_TAG:
                            # Get name and comments
                            file_len = len(file) - 4
                            # We're requiring files names to match displayed name
                            if root.get('name').lower() == file[:file_len].lower(): 
                                shortcut_files.append(file)
                                shortcut_files_display_names.append(root.get('name'))
                                format_error = False
                else:
                    format_error = False
                    print "Shortcuts file " + file + " found, but ignored."
                if format_error:
                    print "Shortcuts file " + file + " found, but has incorrect format."
        print "Valid shortcut files found: " + str(shortcut_files)
    except:
        print "Could not open any shortcut files."
        
# Apr-2017 - SvdB - keyboard shortcuts
def load_shortcuts():
    global _keyboard_actions
    prefs = editorpersistance.prefs

    _modifier_dict = {}
    # Load hardcoded defaults
    _keyboard_actions_defaults()
    # Check if a shortcut preference is set
    if prefs.shortcuts == appconsts.SHORTCUTS_DEFAULT:
        # We have a default setting, so we don't need to load a file, we are using hardcoded.
        return
    # Make sure that whatever is in preferences is a valid file. If it's not in shortcut_files it's not valid
    if not prefs.shortcuts in shortcut_files:
        print "The shortcuts file selected in preferences is not valid: " + prefs.shortcuts
        print "Switching to defaults."
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

def _keyboard_actions_defaults():
    global _keyboard_actions
    # Start with an empty slate
    _keyboard_actions = {}
    _keyboard_actions['i'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'mark_in', \
                               ''.join(sorted(re.sub('[\s]','','ALT'.lower()))): 'to_mark_in', \
                               ''.join(sorted(re.sub('[\s]','','SHIFT'.lower()))): 'to_mark_in', \
                               ''.join(sorted(re.sub('[\s]','','ALT+SHIFT'.lower()))): 'to_mark_in'}
    _keyboard_actions['o'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'mark_out', \
                               ''.join(sorted(re.sub('[\s]','','ALT'.lower()))): 'to_mark_out', \
                               ''.join(sorted(re.sub('[\s]','','SHIFT'.lower()))): 'to_mark_out', \
                               ''.join(sorted(re.sub('[\s]','','ALT+SHIFT'.lower()))): 'to_mark_out'}
    _keyboard_actions['space'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'play_pause'}
    _keyboard_actions['down'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'prev_cut'}
    _keyboard_actions['up'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'next_cut'}
    _keyboard_actions['left'] = { ''.join(sorted(re.sub('[\s]','','Any'.lower()))): 'prev_frame'}
    _keyboard_actions['right'] = { ''.join(sorted(re.sub('[\s]','','Any'.lower()))): 'next_frame'}
    _keyboard_actions['y'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'insert', \
                               ''.join(sorted(re.sub('[\s]','','SHIFT'.lower()))): 'insert'}
    _keyboard_actions['u'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'append', \
                               ''.join(sorted(re.sub('[\s]','','SHIFT'.lower()))): 'append'}
    _keyboard_actions['j'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'slower'}
    _keyboard_actions['k'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'stop'}
    _keyboard_actions['l'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'faster'}
    _keyboard_actions['g'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'log_range'}
    _keyboard_actions['l'] = { ''.join(sorted(re.sub('[\s]','','CTRL'.lower()))): 'log_range'}
    _keyboard_actions['s'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'resync'}
    _keyboard_actions['delete'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'delete'}
    _keyboard_actions['home'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'to_start'}
    _keyboard_actions['end'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'to_end'}
    _keyboard_actions['t'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): '3_point_overwrite'}
    _keyboard_actions['r'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'toggle_ripple'}
    _keyboard_actions['x'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'cut'}
    _keyboard_actions['1'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_insert'}
    _keyboard_actions['kp_end'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_insert'}
    _keyboard_actions['kp_1'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_insert'}
    _keyboard_actions['2'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_overwrite'}
    _keyboard_actions['kp_2'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_overwrite'}
    _keyboard_actions['kp_down'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_overwrite'}
    _keyboard_actions['3'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_trim'}
    _keyboard_actions['kp_3'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_trim'}
    _keyboard_actions['kp_next'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_trim'}
    _keyboard_actions['4'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_roll'}
    _keyboard_actions['kp_4'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_roll'}
    _keyboard_actions['kp_left'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_roll'}
    _keyboard_actions['5'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_slip'}
    _keyboard_actions['kp_5'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_slip'}
    _keyboard_actions['kp_begin'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_slip'}
    _keyboard_actions['6'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_spacer'}
    _keyboard_actions['kp_6'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_spacer'}
    _keyboard_actions['kp_right'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_spacer'}
    _keyboard_actions['7'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_box'}
    _keyboard_actions['kp_7'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_box'}
    _keyboard_actions['kp_home'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'edit_mode_box'}
    _keyboard_actions['minus'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'zoom_out'}
    _keyboard_actions['plus'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'zoom_in'}
    _keyboard_actions['tab'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'switch_monitor'}
    _keyboard_actions['m'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'add_marker'}
    _keyboard_actions['enter'] = { ''.join(sorted(re.sub('[\s]','','None'.lower()))): 'enter_edit'}
