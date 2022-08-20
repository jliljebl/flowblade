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
- parse strings to property tuples or argument dicts
- build value strings from property tuples.
"""
from gi.repository import Gtk
import json

import appconsts
from editorstate import current_sequence
from editorstate import PROJECT
import respaths
import utils

PROP_INT = appconsts.PROP_INT
PROP_FLOAT = appconsts.PROP_FLOAT
PROP_EXPRESSION = appconsts.PROP_EXPRESSION

NAME = appconsts.NAME
ARGS = appconsts.ARGS
SCREENSIZE = "SCREENSIZE"                                   # replace with "WIDTHxHEIGHT" of profile screensize in pix
SCREENSIZE2 = "Screensize2"                                 # replace with "WIDTH HEIGHT" of profile screensize in pix
WIPE_PATH = "WIPE_PATH"                                     # path to folder contining wipe resource images
SCREENSIZE_WIDTH = "SCREENSIZE_WIDTH"                       # replace with width of profile screensize in pix
SCREENSIZE_HEIGHT = "SCREENSIZE_HEIGHT"                     # replace with height of profile screensize in pix
VALUE_REPLACEMENT = "value_replacement"                     # attr name for replacing value after clip is known
FADE_IN_REPLAMENT = "fade_in_replament"                     # replace with fade in keyframes
FADE_OUT_REPLAMENT = "fade_out_replament"                   # replace with fade out keyframes
FADE_IN_OUT_REPLAMENT = "fade_in_out_replament"             # replace with fade in and out keyframes

# ------------------------------------------- parse funcs
def node_list_to_properties_array(node_list):
    """
    Returns list of property tuples of type (name, value, type)
    """
    properties = []
    for node in node_list:
        p_name = node.getAttribute(NAME)
        p_value = node.firstChild.nodeValue # Crash here, is 'exptype' set in string value param args in filters.xml?
        p_type = _property_type(p_value)
        properties.append((p_name, p_value, p_type))
    return properties

def node_to_property(node):
        p_name = node.getAttribute(NAME)
        p_value = node.firstChild.nodeValue
        p_type = _property_type(p_value)
        return (p_name, p_value, p_type)

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
    sreensize_expr_2 = str(profile.width()) + " " + str(profile.height())
    for i in range(0, len(properties)):
        name, value, prop_type = properties[i]
        if prop_type == PROP_EXPRESSION:
            value = value.replace(SCREENSIZE, sreensize_expr)
            value = value.replace(SCREENSIZE2, sreensize_expr_2)
            value = value.replace(WIPE_PATH, respaths.WIPE_RESOURCES_PATH)
            properties[i] = (name, value, prop_type)

def replace_values_using_clip_data(properties, info, clip):
    """
    Property value expressions may need to be replaced with expressions that can only be created
    with knowing clip.
    """
    replacement_happened = False
    for i in range(0, len(properties)):
        prop_name, value, prop_type = properties[i]
        
        if prop_type == PROP_EXPRESSION:
            args_str = info.property_args[prop_name]
            args_dict = args_string_to_args_dict(args_str)
            
            for arg_name in args_dict:
                if arg_name == VALUE_REPLACEMENT:
                    arg_val = args_dict[arg_name]
                    clip_length = clip.clip_length()
                    fade_length = PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH)
                    
                    if arg_val == FADE_IN_REPLAMENT:
                        frame_1 = clip.clip_in
                        frame_2 = clip.clip_in + fade_length
                        value = ""
                        if frame_1 != 0:
                            value += "0=0;"
                        
                        value += str(frame_1) + "=0;" + str(frame_2) + "=1"

                        properties[i] = (prop_name, value, prop_type)
                        replacement_happened = True
                    elif arg_val == FADE_OUT_REPLAMENT:
                        frame_1 = clip.clip_out - fade_length
                        frame_2 = clip.clip_out
                        
                        if clip_length > fade_length:
                            value = "0=1;" + str(frame_1) + "=1;" + str(frame_2) + "=0"
                        else:
                            value = "0=1;" + str(frame_2) + "=0"
                        properties[i] = (prop_name, value, prop_type)
                        replacement_happened = True
                    elif arg_val == FADE_IN_OUT_REPLAMENT:
                        frame_1 = clip.clip_in
                        frame_2 = clip.clip_in + fade_length
                        frame_3 = clip.clip_out - fade_length
                        frame_4 = clip.clip_out
                        value = ""
                        if frame_1 != 0:
                            value += "0=0;"
                            
                        if clip_length > 40:
                            value += str(frame_1) + "=0;" + str(frame_2) + "=1;"
                            value += str(frame_3) + "=1;" + str(frame_4) + "=0"
                        else:
                            clip_half = int(clip_length//2)
                            value += str(frame_1) + "=0;"  + str(frame_1 + clip_half) + "=1;" + str(frame_4) + "=0"

                        properties[i] = (prop_name, value, prop_type)
                        replacement_happened = True

    return replacement_happened

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

# ------------------------------------------ kf editor values strings to kf arrays funcs
def single_value_keyframes_string_to_kf_array(keyframes_str, out_to_in_func):
    new_keyframes = []
    keyframes_str = keyframes_str.strip('"') # expressions have sometimes quotes that need to go away
    kf_tokens = keyframes_str.split(";")
    for token in kf_tokens:
        sides = token.split(appconsts.KEYFRAME_DISCRETE_EQUALS_STR)
        if len(sides) == 2:
            kf_type = appconsts.KEYFRAME_DISCRETE
        else:
            sides = token.split(appconsts.KEYFRAME_SMOOTH_EQUALS_STR)
            if len(sides) == 2:
                kf_type = appconsts.KEYFRAME_SMOOTH
            else:
                sides = token.split(appconsts.KEYFRAME_LINEAR_EQUALS_STR)
                kf_type = appconsts.KEYFRAME_LINEAR
        
        # Find out saved keyframe type here.
        add_kf = (int(sides[0]), out_to_in_func(float(sides[1])), kf_type) # kf = (frame, value, type)
        new_keyframes.append(add_kf)

    return new_keyframes
    
def geom_keyframes_value_string_to_opacity_kf_array(keyframes_str, out_to_in_func):
    # THIS SHOULD ONLY BE IN DEPRECATED COMPOSITORS
    print("NOTICE!!!!!! in: geom_keyframes_value_string_to_opacity_kf_array")
    # Parse "composite:geometry" properties value string into (frame,opacity_value)
    # keyframe tuples.
    new_keyframes = []
    keyframes_str = keyframes_str.strip('"') # expression have sometimes quotes that need to go away
    kf_tokens =  keyframes_str.split(";")
    for token in kf_tokens:
        sides = token.split(appconsts.KEYFRAME_DISCRETE_EQUALS_STR)
        if len(sides) == 2:
            kf_type = appconsts.KEYFRAME_DISCRETE
        else:
            sides = token.split(appconsts.KEYFRAME_SMOOTH_EQUALS_STR)
            if len(sides) == 2:
                kf_type = appconsts.KEYFRAME_SMOOTH
            else:
                sides = token.split(appconsts.KEYFRAME_LINEAR_EQUALS_STR)
                kf_type = appconsts.KEYFRAME_LINEAR
                
        values = sides[1].split(':')

        add_kf = (int(sides[0]), out_to_in_func(float(values[2])), kf_type) # kf = (frame, opacity, type)
        new_keyframes.append(add_kf)
 
    print(keyframes_str)
    print(new_keyframes)
    return new_keyframes

def geom_keyframes_value_string_to_geom_kf_array(keyframes_str, out_to_in_func):
    print("in geom_keyframes_value_string_to_geom_kf_array")
    # Parse "composite:geometry" properties value string into (frame, source_rect, opacity)
    # keyframe tuples.
    new_keyframes = []
    keyframes_str = keyframes_str.strip('"') # expression have sometimes quotes that need to go away
    kf_tokens =  keyframes_str.split(';')
    for token in kf_tokens:
        sides = token.split(appconsts.KEYFRAME_DISCRETE_EQUALS_STR)
        if len(sides) == 2:
            kf_type = appconsts.KEYFRAME_DISCRETE
        else:
            sides = token.split(appconsts.KEYFRAME_SMOOTH_EQUALS_STR)
            if len(sides) == 2:
                kf_type = appconsts.KEYFRAME_SMOOTH
            else:
                sides = token.split(appconsts.KEYFRAME_LINEAR_EQUALS_STR)
                kf_type = appconsts.KEYFRAME_LINEAR
                
        values = sides[1].split(':')
        pos = values[0].split('/')
        size = values[1].split('x')
        source_rect = [int(pos[0]), int(pos[1]), int(size[0]), int(size[1])] #x,y,width,height
        add_kf = (int(sides[0]), source_rect, out_to_in_func(float(values[2])), kf_type)
        new_keyframes.append(add_kf)
 
    return new_keyframes

def rect_keyframes_value_string_to_geom_kf_array(keyframes_str, out_to_in_func):
    print("in rect_keyframes_value_string_to_geom_kf_array")
    # Parse "composite:geometry" properties value string into (frame, source_rect, opacity)
    # keyframe tuples.
    new_keyframes = []
    keyframes_str = keyframes_str.strip('"') # expression have sometimes quotes that need to go away
    kf_tokens =  keyframes_str.split(';')
    for token in kf_tokens:
        sides = token.split(appconsts.KEYFRAME_DISCRETE_EQUALS_STR)
        if len(sides) == 2:
            kf_type = appconsts.KEYFRAME_DISCRETE
        else:
            sides = token.split(appconsts.KEYFRAME_SMOOTH_EQUALS_STR)
            if len(sides) == 2:
                kf_type = appconsts.KEYFRAME_SMOOTH
            else:
                sides = token.split(appconsts.KEYFRAME_LINEAR_EQUALS_STR)
                kf_type = appconsts.KEYFRAME_LINEAR
                
        values = sides[1].split(' ')
        x = values[0]
        y = values[1]
        w = values[2] 
        h = values[3] 
        source_rect = [int(x), int(y), int(w), int(h)] #x,y,width,height
        add_kf = (int(sides[0]), source_rect, out_to_in_func(float(1)), kf_type)
        new_keyframes.append(add_kf)
    
    return new_keyframes
    
def rotating_geom_keyframes_value_string_to_geom_kf_array(keyframes_str, out_to_in_func):
    print("keyframes_str", keyframes_str)
    # THIS WAS CREATED FOR frei0r cairoaffineblend FILTER. That filter has to use a very particular parameter values
    # scheme to satisty the frei0r requirement of all float values being in range 0.0 - 1.0.
    #
    # Parse extraeditor value properties value string into (frame, [x, y, x_scale, y_scale, rotation], opacity)
    # keyframe tuples.
    print("rotating_geom_keyframes_value_string_to_geom_kf_array")
    new_keyframes = []
    screen_width = current_sequence().profile.width()
    screen_height = current_sequence().profile.height()
    keyframes_str = keyframes_str.strip('"') # expression have sometimes quotes that need to go away
    kf_tokens =  keyframes_str.split(';')
    for token in kf_tokens:
        sides = token.split(appconsts.KEYFRAME_DISCRETE_EQUALS_STR)
        if len(sides) == 2:
            kf_type = appconsts.KEYFRAME_DISCRETE
        else:
            sides = token.split(appconsts.KEYFRAME_SMOOTH_EQUALS_STR)
            if len(sides) == 2:
                kf_type = appconsts.KEYFRAME_SMOOTH
            else:
                sides = token.split(appconsts.KEYFRAME_LINEAR_EQUALS_STR)
                kf_type = appconsts.KEYFRAME_LINEAR
                
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
        print("rotating_geom_keyframes_value_string_to_geom_kf_array")
        add_kf = (frame, source_rect, float(opacity), kf_type)
        print("add kf", add_kf)
        new_keyframes.append(add_kf)

    return new_keyframes

def non_freior_rotating_geom_keyframes_value_string_to_geom_kf_array(keyframes_str, out_to_in_func):
    # Parse extraeditor value properties value string into (frame, [x, y, x_scale, y_scale, rotation], opacity)
    # keyframe tuples.
    new_keyframes = []
    keyframes_str = keyframes_str.strip('"') # expression have sometimes quotes that need to go away
    kf_tokens =  keyframes_str.split(';')
    for token in kf_tokens:
        sides = token.split('=')
        values = sides[1].split(':')
        frame = int(sides[0])
        # get values and convert "frei0r.cairoaffineblend" values to editor values
        # this because all frei0r plugins require values in range 0 - 1
        x = float(values[0])
        y = float(values[1])
        x_scale = float(values[2])
        y_scale = float(values[3])
        rotation = float(values[4])
        opacity = float(values[5]) * 100
        source_rect = [x,y,x_scale,y_scale,rotation]
        add_kf = (frame, source_rect, float(opacity))
        new_keyframes.append(add_kf)

    return new_keyframes
    
def rotomask_json_value_string_to_kf_array(keyframes_str, out_to_in_func):
    new_keyframes = []
    json_obj = json.loads(keyframes_str)
    for kf in json_obj:
        kf_obj = json_obj[kf]
        add_kf = (int(kf), kf_obj)
        new_keyframes.append(add_kf)

    return sorted(new_keyframes, key=lambda kf_tuple: kf_tuple[0]) 
    
    
# ----------------------------------------------------------------------------- AFFINE BLEND
def create_editable_property_for_affine_blend(clip, editable_properties):
    print("create_editable_property_for_affine_blend")
    # Build a custom object that duck types for TransitionEditableProperty 
    # to be use in editor propertyeditor.RotatingGeometryEditor.
    ep = utils.EmptyClass()
    # pack real properties to go
    ep.x = [ep for ep in editable_properties if ep.name == "x"][0]
    ep.y = [ep for ep in editable_properties if ep.name == "y"][0]
    ep.x_scale = [ep for ep in editable_properties if ep.name == "x scale"][0]
    ep.y_scale = [ep for ep in editable_properties if ep.name == "y scale"][0]
    ep.rotation = [ep for ep in editable_properties if ep.name == "rotation"][0]
    ep.opacity = [ep for ep in editable_properties if ep.name == "opacity"][0]
    # Screen width and height are needed for frei0r conversions
    ep.profile_width = current_sequence().profile.width()
    ep.profile_height = current_sequence().profile.height()
    # duck type methods, using opacity is not meaningful, any property with clip member could do
    ep.get_clip_tline_pos = lambda : ep.opacity.clip.clip_in # clip is compositor, compositor in and out points are straight in timeline frames
    ep.get_clip_length = lambda : ep.opacity.clip.clip_out - ep.opacity.clip.clip_in + 1
    ep.get_input_range_adjustment = lambda : Gtk.Adjustment(value=float(100), lower=float(0), upper=float(100), step_incr=float(1))
    ep.get_display_name = lambda : "Opacity"
    ep.get_pixel_aspect_ratio = lambda : (float(current_sequence().profile.sample_aspect_num()) / current_sequence().profile.sample_aspect_den())
    ep.get_in_value = lambda out_value : out_value # hard coded for opacity 100 -> 100 range
    ep.write_out_keyframes = lambda w_kf : rotating_ge_write_out_keyframes(ep, w_kf)
    ep.update_prop_value = lambda : rotating_ge_update_prop_value(ep) # This is needed to get good update after adding kfs with fade buttons, iz all kinda fugly
                                                                            # We need this to reinit GUI components after programmatically added kfs.
    # duck type members
    x_tokens = ep.x.value.split(";")
    y_tokens = ep.y.value.split(";")
    x_scale_tokens = ep.x_scale.value.split(";")
    y_scale_tokens = ep.y_scale.value.split(";")
    rotation_tokens = ep.rotation.value.split(";")
    opacity_tokens = ep.opacity.value.split(";")
    
    value = ""
    for i in range(0, len(x_tokens)): # these better match, same number of keyframes for all values, or this will not work
        print("x_tokens[i]", x_tokens[i])
        frame, x, kf_type = _get_roto_geom_frame_value(x_tokens[i])
        frame, y, kf_type = _get_roto_geom_frame_value(y_tokens[i])
        frame, x_scale, kf_type = _get_roto_geom_frame_value(x_scale_tokens[i])
        frame, y_scale, kf_type = _get_roto_geom_frame_value(y_scale_tokens[i])
        frame, rotation, kf_type = _get_roto_geom_frame_value(rotation_tokens[i])
        frame, opacity, kf_type = _get_roto_geom_frame_value(opacity_tokens[i])

        eq_str = _get_eq_str(kf_type)

        frame_str = str(frame) + eq_str + str(x) + ":" + str(y) + ":" + str(x_scale) + ":" + str(y_scale) + ":" + str(rotation) + ":" + str(opacity)
        value += frame_str + ";"

    ep.value = value.strip(";")
    print("ep.value", ep.value)
    return ep

def _get_roto_geom_frame_value(token):
    sides = token.split(appconsts.KEYFRAME_DISCRETE_EQUALS_STR)
    if len(sides) == 2:
        kf_type = appconsts.KEYFRAME_DISCRETE
    else:
        sides = token.split(appconsts.KEYFRAME_SMOOTH_EQUALS_STR)
        if len(sides) == 2:
            kf_type = appconsts.KEYFRAME_SMOOTH
        else:
            sides = token.split(appconsts.KEYFRAME_LINEAR_EQUALS_STR)
            kf_type = appconsts.KEYFRAME_LINEAR
    
    return(sides[0], sides[1], kf_type)

def _get_eq_str(kf_type):
    if kf_type == appconsts.KEYFRAME_DISCRETE:
        eq_str = appconsts.KEYFRAME_DISCRETE_EQUALS_STR
    elif kf_type == appconsts.KEYFRAME_SMOOTH:
        eq_str = appconsts.KEYFRAME_SMOOTH_EQUALS_STR
    else:
        eq_str = appconsts.KEYFRAME_LINEAR_EQUALS_STR
    
    return eq_str
    
def rotating_ge_write_out_keyframes(ep, keyframes):
    print("rotating_ge_write_out_keyframes", keyframes)
    x_val = ""
    y_val = ""
    x_scale_val = ""
    y_scale_val = ""
    rotation_val = ""
    opacity_val = ""
    
    for kf in keyframes:
        frame, transf, opacity, kf_type = kf
        x, y, x_scale, y_scale, rotation = transf
        
        eq_str = _get_eq_str(kf_type)
            
        x_val += str(frame) + eq_str + str(get_frei0r_cairo_position(x, ep.profile_width)) + ";"
        y_val += str(frame) + eq_str + str(get_frei0r_cairo_position(y, ep.profile_height)) + ";"
        x_scale_val += str(frame) + eq_str + str(get_frei0r_cairo_scale(x_scale)) + ";"
        y_scale_val += str(frame) + eq_str + str(get_frei0r_cairo_scale(y_scale)) + ";"
        rotation_val += str(frame) + eq_str + str(rotation / 360.0) + ";"
        opacity_val += str(frame) + eq_str + str(opacity / 100.0) + ";"

    x_val = x_val.strip(";")
    y_val = y_val.strip(";")
    x_scale_val = x_scale_val.strip(";")
    y_scale_val = y_scale_val.strip(";")
    rotation_val = rotation_val.strip(";")
    opacity_val = opacity_val.strip(";")
   
    print(x_val, x_scale_val)
   
    ep.x.write_value(x_val)
    ep.y.write_value(y_val)
    ep.x_scale.write_value(x_scale_val)
    ep.y_scale.write_value(y_scale_val)
    ep.rotation.write_value(rotation_val)
    ep.opacity.write_value(opacity_val)

def rotating_ge_update_prop_value(ep):
    print("XXXXXXXXXXXXXXXXXXXXXXXXXXXX rotating_ge_update_prop_value", ep)
    # duck type members
    x_tokens = ep.x.value.split(";")
    y_tokens = ep.y.value.split(";")
    x_scale_tokens = ep.x_scale.value.split(";")
    y_scale_tokens = ep.y_scale.value.split(";")
    rotation_tokens = ep.rotation.value.split(";")
    opacity_tokens = ep.opacity.value.split(";")
    
    value = ""
    for i in range(0, len(x_tokens)): # these better match, same number of keyframes for all values, or this will not work
        frame, x, kf_type = _get_roto_geom_frame_value(x_tokens[i])
        frame, y, kf_type = _get_roto_geom_frame_value(y_tokens[i])
        frame, x_scale, kf_type = _get_roto_geom_frame_value(x_scale_tokens[i])
        frame, y_scale, kf_type = _get_roto_geom_frame_value(y_scale_tokens[i])
        frame, rotation, kf_type = _get_roto_geom_frame_value(rotation_tokens[i])
        frame, opacity, kf_type = _get_roto_geom_frame_value(opacity_tokens[i])

        eq_str = _get_eq_str(kf_type)
        
        frame_str = str(frame) + eq_str + str(x) + ":" + str(y) + ":" + str(x_scale) + ":" + str(y_scale) + ":" + str(rotation) + ":" + str(opacity)
        value += frame_str + ";"

    ep.value = value.strip(";")

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
