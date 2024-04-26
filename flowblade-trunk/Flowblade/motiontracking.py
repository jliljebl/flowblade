"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2024 Janne Liljeblad.

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

from gi.repository import Gtk

from editorstate import PROJECT
import utils


# Values correspond with values in filters.xml
COORDINATES_ABSOLUTE = "absolute"
COORDINATES_TOP_LEFT_JUSTIFIED = "topleft"
SIZE_NOT_SCALED = "notscaled"
SIZE_SCALED = "scaled"


def get_tracking_data_select_combo(empty_text):
    tdata_select_combo = Gtk.ComboBoxText()
    tdata_keys = []
    if len(PROJECT().tracking_data) > 0:
        for key, tdata in PROJECT().tracking_data.items():
            label, file = tdata
            tdata_select_combo.append_text(label)
            tdata_keys.append(key)
    else:
        tdata_select_combo.append_text(empty_text)
        tdata_keys.append(None)

    tdata_select_combo.set_active(0)
    return (tdata_keys, tdata_select_combo)


def apply_tracking(tracking_data_id, filter, editable_properties, xoff, yoff, interpretation, size, clip_in):
    data_lable, data_path = PROJECT().tracking_data[tracking_data_id]
 
    f = open(data_path, "r")
    results = f.read()
    f.close()

    kf_list = get_kf_list_from_tracking_data(results)
    kf_list_user = get_user_edits_kf_list(kf_list, xoff, yoff, interpretation, size, clip_in)
    
    
    trans_rect_value = get_transition_rect_str_from_kf_list(kf_list_user)
    #print(trans_rect_value)

    trans_rect_prop = [ep for ep in editable_properties if ep.name == "transition.rect"][0]
    trans_rect_prop.write_value(trans_rect_value)

def get_kf_list_from_tracking_data(results):
    # Results are text file with kf info in format: '...;1430~=753 98 100 100 0;1431~=753 98 100 100 0'
    
    kf_strs = results.split(";")
    
    kf_list = []
    for kf_str in kf_strs:
        kf_parts = kf_str.split("~=")
        rect_tokens = kf_parts[1].split(" ")
        kf = (int(kf_parts[0]), int(rect_tokens[0]), int(rect_tokens[1]), int(rect_tokens[2]), int(rect_tokens[3]))
        kf_list.append(kf)
    
    #print(kf_list)
    return kf_list

def get_user_edits_kf_list(kf_list, xoff, yoff, interpretation, size, clip_in):
    kf_list_user = []
    
    #print("BBBB", xoff, yoff, interpretation, size, clip_in)
     
    # Get first kf data
    frame, x, y, w, h = kf_list[0]
        
    # Apply position interpretation to offsets
    if interpretation == COORDINATES_TOP_LEFT_JUSTIFIED:
        xoff -= x
        yoff -= y
    
    # Apply selected scaling.
    if size == SIZE_NOT_SCALED:
        source_width = w
        source_height = h
    else:
        source_width = w
        source_height = h

    # Apply tracking starting from 'clip_in' frame.
    if clip_in != 0:
        kf = (frame, x + xoff, y + yoff, source_width, source_height)
        kf_list_user.append(kf)
        frame_add = clip_in
    else:
        frame_add = 0

    # Create user kf list
    for kf in kf_list:
        frame, x, y, w, h = kf
        kf = (frame + frame_add, x + xoff, y + yoff, source_width, source_height)
        kf_list_user.append(kf)

    return kf_list_user

def get_transition_rect_str_from_kf_list(kf_list):
    transition_rect = ""
    for kf in kf_list:
        frame, x, y, w, h = kf
        transition_rect += str(frame) + "~=" + str(x) + " " + str(y) + " " + str(w) + " " + str(h) + " 1" + ";"
    
    transition_rect.rstrip(";")
    
    return transition_rect
