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

"""
Module contains functions used to implement motion tracking feature.
"""

# Values correspond with values in filters.xml
COORDINATES_ABSOLUTE = "absolute"
COORDINATES_TOP_LEFT_JUSTIFIED = "topleft"
SIZE_NOT_SCALED = "notscaled"
SIZE_SCALED = "scaled"


def get_tracking_data_select_combo(empty_text, current_selection_id):
    tdata_select_combo = Gtk.ComboBoxText()
    tdata_keys = []
    current_selection_index = -1
    indx = 0
    if len(PROJECT().tracking_data) > 0:
        for key, tdata in PROJECT().tracking_data.items():
            label, file = tdata
            tdata_select_combo.append_text(label)
            tdata_keys.append(key)
            if key == current_selection_id:
                current_selection_index = indx
            indx += 1
    else:
        tdata_select_combo.append_text(empty_text)
        tdata_keys.append(None)

    if current_selection_index == -1:
        tdata_select_combo.set_active(0)
    else:
        tdata_select_combo.set_active(current_selection_index)
    return (tdata_keys, tdata_select_combo)

def apply_tracking( tracking_data_id, filter, editable_properties, 
                    xoff, yoff, interpretation, size, clip_in,
                    source_width, source_height):
    data_lable, data_path = PROJECT().tracking_data[tracking_data_id]
 
    f = open(data_path, "r")
    results = f.read()
    f.close()

    kf_list = get_kf_list_from_tracking_data(results, True)
    kf_list_user = get_user_edits_kf_list(kf_list, xoff, yoff, interpretation, size, clip_in, source_width, source_height)
    trans_rect_value = get_transition_rect_str_from_kf_list(kf_list_user)

    trans_rect_prop = [ep for ep in editable_properties if ep.name == "transition.rect"][0]
    trans_rect_prop.write_value(trans_rect_value)

def get_kf_list_from_tracking_data(results, start_kfs_from_zero=False):
    # Results are text file with kf info in format: '...;1430~=753 98 100 100 0;1431~=753 98 100 100 0'
    
    kf_strs = results.split(";")
    
    kf_list = []
    for kf_str in kf_strs:
        kf_parts = kf_str.split("~=")
        rect_tokens = kf_parts[1].split(" ")
        kf = (int(kf_parts[0]), int(rect_tokens[0]), int(rect_tokens[1]), int(rect_tokens[2]), int(rect_tokens[3]))
        kf_list.append(kf)

    if start_kfs_from_zero == True:
        kf_list_fixed = []
        frame_zero, x, y, w, h  = kf_list[0]
        for kf in kf_list:
            frame,  x, y, w, h  = kf
            fix_kf = (frame - frame_zero, x, y, w, h)
            kf_list_fixed.append(fix_kf)
        kf_list = kf_list_fixed

    return kf_list

def get_user_edits_kf_list(kf_list, xoff, yoff, interpretation, size, clip_in, clip_source_width, clip_source_height):
    kf_list_user = []
     
    # Get first kf data
    frame, x, y, w, h = kf_list[0]
        
    # Apply position interpretation to offsets
    if interpretation == COORDINATES_TOP_LEFT_JUSTIFIED:
        xoff -= x
        yoff -= y
    
    # Apply selected scaling.
    if size == SIZE_NOT_SCALED:
        source_width = clip_source_width
        source_height = clip_source_height
    else:
        source_width = w
        source_height = h

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

def apply_filter_mask_tracking( tracking_data_id, filter, editable_properties,  xoff, yoff, scale, clip_in):
    data_lable, data_path = PROJECT().tracking_data[tracking_data_id]
 
    f = open(data_path, "r")
    results = f.read()
    f.close()

    kf_list = get_kf_list_from_tracking_data(results)
    kf_list_user = get_user_edits_kf_list(kf_list, xoff, yoff, COORDINATES_ABSOLUTE, SIZE_SCALED, 0, -1, -1)
    profile_w = float(PROJECT().profile.width())
    profile_h = float(PROJECT().profile.height())

    position_x_str = ""
    position_y_str = ""

    for kf in kf_list_user:
        frame, x, y, w, h = kf
        x = float(x)
        y = float(y)
        w = float(w)
        h = float(h)
        xn = (x + (w / 2.0)) / profile_w
        yn = (y + (h / 2.0)) / profile_h
        position_x_str += str(frame) + "~=" + str(xn) + ";"
        position_y_str += str(frame) + "~=" + str(yn) + ";"

    size_x_str = str( ((w * scale) / profile_w) / 2.0)
    size_y_str = str( ((h * scale) / profile_h) / 2.0)
    
    position_x_str.rstrip(";")
    position_y_str.rstrip(";")

    size_x_prop = [ep for ep in editable_properties if ep.name == "filter.Position X"][0]
    size_y_prop = [ep for ep in editable_properties if ep.name == "filter.Position Y"][0]
    position_x_prop = [ep for ep in editable_properties if ep.name == "filter.Size X"][0]
    position_y_prop = [ep for ep in editable_properties if ep.name == "filter.Size Y"][0]

    size_x_prop.write_value(position_x_str)
    size_y_prop.write_value(position_y_str)
    position_x_prop.write_value(size_x_str)
    position_y_prop.write_value(size_y_str)
