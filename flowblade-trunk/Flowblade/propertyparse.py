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
Modules provides functions that:
- parses strings to property tuples or argument dicts
- build value strings from property tuples.
"""

import appconsts
from editorstate import current_sequence
import respaths

PROP_INT = appconsts.PROP_INT
PROP_FLOAT = appconsts.PROP_FLOAT
PROP_EXPRESSION = appconsts.PROP_EXPRESSION

NAME = appconsts.NAME
ARGS = appconsts.ARGS
SCREENSIZE = "SCREENSIZE"                                   # replace with "WIDTHxHEIGHT" of profile screensize in pix
WIPE_PATH = "WIPE_PATH"                                     # path to folder contining wipe resource images
SCREENSIZE_WIDTH = "SCREENSIZE_WIDTH"                       # replace with width of profile screensize in pix
SCREENSIZE_HEIGHT = "SCREENSIZE_HEIGHT"                     # replace with height of profile screensize in pix

# ------------------------------------------- parse funcs
def node_list_to_properties_array(node_list):
    """
    Returns list of property tuples of type (name, value, type)
    """
    properties = []
    for node in node_list:
        p_name = node.getAttribute(NAME)
        p_value = node.firstChild.nodeValue
        p_type = _property_type(p_value)
        properties.append((p_name, p_value, p_type))
    return properties

def node_list_to_non_mlt_properties_array(node_list):
    """
    Returns list of property tuples of type (name, value, type)
    """
    properties = []
    for node in node_list:
        p_name = node.getAttribute(NAME)
        p_value = node.firstChild.nodeValue
        p_type = _property_type(p_value)
        properties.append((p_name, p_value, p_type))
    return properties

def node_list_to_args_dict(node_list):
    """
    Returns dict of type property_name -> property_args_string
    """
    property_args = {}
    for node in node_list:
        p_name = node.getAttribute(NAME)
        p_args = node.getAttribute(ARGS)
        property_args[p_name] = p_args

    return property_args

def node_list_to_extraeditors_array(node_list):
    editors = []
    for node in node_list:
        e_name = node.getAttribute(NAME)
        editors.append(e_name)
    return editors

def args_string_to_args_dict(args_str):
    """
    Returns key->value dict of property args.
    """
    args_dict = {}
    args = args_str.split(" ")
    for arg in args:
        sides = arg.split("=")
        args_dict[sides[0]] = sides[1]
    return args_dict

def replace_value_keywords(properties, profile):
    """
    Property value expressions may have keywords in default values that 
    need to be replaced with other expressions when containing
    objects first become active.
    """
    sreensize_expr = str(profile.width()) + "x" + str(profile.height())
    for i in range(0, len(properties)):
        name, value, prop_type = properties[i]
        if prop_type == PROP_EXPRESSION:
            value = value.replace(SCREENSIZE, sreensize_expr)
            value = value.replace(WIPE_PATH, respaths.WIPE_RESOURCES_PATH)
            properties[i] = (name, value, prop_type)

def get_args_num_value(val_str):
    """
    Returns numerical value for expression in property
    args. 
    """
    try: # attempt int
        return int(val_str)
    except:
        try:# attempt float
            return float(val_str)
        except:
            # attempt expression
            if val_str == SCREENSIZE_WIDTH:
                return current_sequence().profile.width()
            elif val_str == SCREENSIZE_HEIGHT:
                return current_sequence().profile.height()
    return None

# ------------------------------------------ kf editor values strings to kfs funcs
def single_value_keyframes_string_to_kf_array(keyframes_str, out_to_in_func):
    #print "keyframes_str", keyframes_str
    new_keyframes = []
    keyframes_str = keyframes_str.strip('"') # expression have sometimes quotes that need to go away
    kf_tokens = keyframes_str.split(";")
    for token in kf_tokens:
        sides = token.split("=")
        add_kf = (int(sides[0]), out_to_in_func(float(sides[1]))) # kf = (frame, value)
        new_keyframes.append(add_kf)
        
    return new_keyframes
    
def geom_keyframes_value_string_to_opacity_kf_array(keyframes_str, out_to_in_func):
    # Parse "composite:geometry" properties value string into (frame,opacity_value)
    # keyframe tuples.
    new_keyframes = []
    keyframes_str = keyframes_str.strip('"') # expression have sometimes quotes that need to go away
    kf_tokens =  keyframes_str.split(";")
    for token in kf_tokens:
        sides = token.split("=")
        values = sides[1].split(':')
        add_kf = (int(sides[0]), out_to_in_func(float(values[2]))) # kf = (frame, opacity)
        new_keyframes.append(add_kf)
 
    return new_keyframes

def geom_keyframes_value_string_to_geom_kf_array(keyframes_str, out_to_in_func):
    # Parse "composite:geometry" properties value string into (frame, source_rect, opacity)
    # keyframe tuples.
    new_keyframes = []
    keyframes_str = keyframes_str.strip('"') # expression have sometimes quotes that need to go away
    kf_tokens =  keyframes_str.split(';')
    for token in kf_tokens:
        sides = token.split('=')
        values = sides[1].split(':')
        pos = values[0].split('/')
        size = values[1].split('x')
        source_rect = [int(pos[0]), int(pos[1]), int(size[0]), int(size[1])] #x,y,width,height
        add_kf = (int(sides[0]), source_rect, out_to_in_func(float(values[2])))
        new_keyframes.append(add_kf)
 
    return new_keyframes

def rotating_geom_keyframes_value_string_to_geom_kf_array(keyframes_str, out_to_in_func):
    # Parse extraeditor value properties value string into (frame, [x, y, x_scale, y_scale, rotation], opacity)
    # keyframe tuples.
    new_keyframes = []
    screen_width = current_sequence().profile.width()
    screen_height = current_sequence().profile.height()
    keyframes_str = keyframes_str.strip('"') # expression have sometimes quotes that need to go away
    kf_tokens =  keyframes_str.split(';')
    for token in kf_tokens:
        sides = token.split('=')
        values = sides[1].split(':')
        frame = int(sides[0])
        # get values and convert "frei0r.cairoaffineblend" values to editor values
        # this because all frei0r plugins require values in range 0 - 1
        x = _get_pixel_pos_from_frei0r_cairo_pos(float(values[0]), screen_width)
        y = _get_pixel_pos_from_frei0r_cairo_pos(float(values[1]), screen_height)
        x_scale = _get_scale_from_frei0r_cairo_scale(float(values[2]))
        y_scale = _get_scale_from_frei0r_cairo_scale(float(values[3]))
        rotation = float(values[4]) * 360
        opacity = float(values[5]) * 100
        source_rect = [x,y,x_scale,y_scale,rotation]
        add_kf = (frame, source_rect, float(opacity))
        new_keyframes.append(add_kf)

    return new_keyframes

def _get_pixel_pos_from_frei0r_cairo_pos(value, screen_dim):
    # convert positions from range used by frei0r cairo plugins to pixel values
    return -2.0 * screen_dim + value * 5.0 * screen_dim
    
def _get_scale_from_frei0r_cairo_scale(scale):
    return scale * 5.0

def get_frei0r_cairo_scale(scale):
    return scale / 5.0
    
def get_frei0r_cairo_position(pos, screen_dim):
    pix_range = screen_dim * 5.0
    range_pos = pos + screen_dim * 2.0
    return range_pos / pix_range

#------------------------------------------------------ util funcs
def _property_type(value_str):
    """
    Gets property type from value string by trying to interpret it 
    as int or float, if both fail it is considered an expression.
    """
    try:
        int(value_str)
        return PROP_INT
    except:
        try:
            float(value_str)
            return PROP_FLOAT
        except:
            return PROP_EXPRESSION

def set_property_value(properties, prop_name, prop_value):
    for i in range(0, len(properties)):
        name, value, t = properties[i]
        if prop_name == name:
            properties[i] = (name, prop_value, t)

def get_property_value(properties, prop_name):
    for i in range(0, len(properties)):
        name, value, t = properties[i]
        if prop_name == name:
            return value
    
    return None
