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
Module provides wrapper objects for editing property values of objects in
the sequence. 

Properties are (name, value, type) tuples that are wrapped in objects 
extending AbstractProperty class for editing. These wrappers convert
edit inputs into mlt property values (that effect how sequence is displayed)
and python side values (that are persistant).
"""

import pygtk
pygtk.require('2.0');
import gtk


import appconsts
from editorstate import current_sequence
import mlttransitions
import mltfilters
import propertyparse
import utils

# keys                                                      meaning of values for this key
RANGE_IN = "range_in"                                       # values define user input range
RANGE_OUT = "range_out"                                     # values define range of output to mlt
STEP = "step"                                               # gtk.Adjustment step_increment value is set using this
EXPRESSION_TYPE = "exptype"                                 # type of string expression used as value
EDITOR = "editor"                                           # editor used to edit property
DISPLAY_NAME = "displayname"                                # name of property that is displayed to user
MULTIPART_START_PROP = "multistartprop"                     # Value used to set multipart value at part start
MULTIPART_END_PROP = "multiendprop"                         # Value used to set multipart value at part end

# ranges values                                             expression is replaced with 
NORMALIZED_FLOAT = "NORMALIZED_FLOAT"                       # range 0.0 - 1.0

#  PROP_EXPRESSION values, e.g. "exptype=keyframe_hcs"      parsed output
DEFAULT = "default"                                         # value     (str(int), str(float) or str(str))
DEFAULT_TRANSITION = "default_transition"                   # value     (str(int), str(float) or str(str))
SINGLE_KEYFRAME = "singlekeyframe"                          # 0=value
OPACITY_IN_GEOM_SINGLE_KF = "opacity_in_geom_kf_single"     # 0=0/0:SCREEN_WIDTHxSCREEN_HEIGHT:opacity
OPACITY_IN_GEOM_KF = "opacity_in_geom_kf"                   # frame=0/0:SCREEN_WIDTHxSCREEN_HEIGHT:opacity (kf_str;kf_str;kf_str;...;kf_str)
GEOMETRY_OPACITY_KF ="geom_opac_kf"                         # frame=x/y:widthxheight:opacity
GEOM_IN_AFFINE_FILTER = "geom_in_affine_filt"               # x/y:widthxheight:opacity
AFFINE_SCALE = "affine_scale"                               # special property to get the 1/ x that the filter wants
KEYFRAME_HCS = "keyframe_hcs"                               # frame=value(;frame=value) HCS = half comma separeted
KEYFRAME_HCS_TRANSITION = "keyframe_hcs_transition"         # frame=value(;frame=value) HCS = half comma separeted, used to edit transitions
MULTIPART_KEYFRAME_HCS = "multipart_keyframe"               # frame=value(;frame=value) series of mlt.Filter objects that get their properties set, HCS = half comma separeted
FREI_POSITION_HCS = "frei_pos_hcs"                          # frame=x:y
FREI_GEOM_HCS_TRANSITION = "frei_geom_hcs";                 # time=x:y:x_scale:y_scale:rotation:mix
COLOR = "color"                                             # #rrggbb
LUT_TABLE = "lut_table"                                     # val;val;val;val;...;val
WIPE_RESOURCE = "wipe_resource"                             # /path/to/resource.pgm
NOT_PARSED = "not_parsed"                                   # A write out value is not parsed from value
NOT_PARSED_TRANSITION = "not_parsed_transition"             # A write out value is not parsed from value in transition object

DEFAULT_STEP = 1.0 # for sliders
                    
def get_filter_editable_properties(clip, filter_object, filter_index, 
                                   track, clip_index, compositor_filter=False):
    """
    Creates EditableProperty wrappers for all property tuples in a
    mltfilters.FilterObject and returns them in array.
    """
    
    editable_properties = []
    
    # Editable properties for normal filters
    for i in range(0, len(filter_object.properties)):
        p_name, p_value, p_type = filter_object.properties[i]
        args_str = filter_object.info.property_args[p_name]
        params = (clip, filter_index, (p_name, p_value, p_type), i, args_str)

        ep = _create_editable_property(p_type, args_str, params)

        ep.is_compositor_filter = compositor_filter
        ep.track = track
        ep.clip_index = clip_index
        editable_properties.append(ep)
    
    # Editable property for multipart filters
    if isinstance(filter_object, mltfilters.MultipartFilterObject):
        args_str, start_property, end_property = filter_object.info.multipart_desc
        property_index = len(editable_properties)
        params = (clip, filter_index, 
                 ("no dispname given", filter_object.value, appconsts.PROP_EXPRESSION), 
                 property_index, args_str)

        ep = _create_editable_property(appconsts.PROP_EXPRESSION, args_str, params)

        ep.is_compositor_filter = compositor_filter
        ep.track = track
        ep.clip_index = clip_index
        editable_properties.append(ep)
    
    return editable_properties

def _create_editable_property(p_type, args_str, params):
    
    if p_type == appconsts.PROP_EXPRESSION:
        """
        For expressions we can't do straight input output numerical
        conversion so we need a extending class for expression type.
        """
        args = propertyparse.args_string_to_args_dict(args_str)
        exp_type = args[EXPRESSION_TYPE] # 'exptype' arg missing?. if this fails, it's a bug in filters.xml
        creator_func = EDITABLE_PROPERTY_CREATORS[exp_type]
        ep = creator_func(params)
    else:
        ep = EditableProperty(params)

    return ep

def get_transition_editable_properties(compositor):
    """
    Creates AbstractProperty extending wrappers for all property tuples in
    mlttransitions.CompositorTransition.
    """
    transition = compositor.transition
    editable_properties = []
    for i in range(0, len(transition.properties)):
        p_name, p_value, p_type = transition.properties[i]
        args_str = transition.info.property_args[p_name]
        params = (compositor, (p_name, p_value, p_type), i, args_str)

        if p_type == mltfilters.PROP_EXPRESSION:
            """
            For expressions we can't do straight input output numerical
            conversion so we need a extending class for expression type.
            """
            args = propertyparse.args_string_to_args_dict(args_str)
            exp_type = args[EXPRESSION_TYPE] # 'exptype' arg missing?. if this fails, it's a bug in compositors.xml
            creator_func = EDITABLE_PROPERTY_CREATORS[exp_type]
            ep = creator_func(params)
        else:
            ep = TransitionEditableProperty(params)
        ep.track = None
        ep.clip_index = None
        editable_properties.append(ep)
    
    return editable_properties

def get_non_mlt_editable_properties(clip, filter_object, filter_index):
    editable_properties = []
    for i in range(0, len(filter_object.non_mlt_properties)):
        prop = filter_object.non_mlt_properties[i]
        p_name, p_value, p_type = prop
        args_str = filter_object.info.property_args[p_name]
        ep = NonMltEditableProperty(prop, args_str, clip, filter_index, i)
        editable_properties.append(ep)
    
    return editable_properties
        
# -------------------------------------------- property wrappers objs
class AbstractProperty:
    """
    A base class for all wrappers of property tuples in
    mltfilters.FilterObject.properties array and in
    mlttransitions.CompositorObject.transition.properties array.

    This class converts input to output using set ranges.
    
    Class also creates args name->value dict used by all extending classes
    and has default versions of editor component callbacks.
    """
    def __init__(self, args_str):
        self.args = propertyparse.args_string_to_args_dict(args_str)
        self.track = None # set in creator loops
        self.clip_index = None # set in creator loops
        self.name = None # mlt property name. set by extending classes
        self._set_input_range()
        self._set_output_range()
    
    def get_display_name(self):
        """
        Parses display name from args display_name value by replacing "!" with " ", a hack
        """
        try:
             disp_name = self.args[DISPLAY_NAME]
             return disp_name.replace("!"," ") # We're using space as separator in args 
                                               # so names with spaces use letter ! in places where spaces go
        except:
            return self.name

    def _set_input_range(self):
        try:
            range_in = self.args[RANGE_IN]
        except: # not defined, use default
            range_in = NORMALIZED_FLOAT

        if len(range_in.split(",")) == 2: # comma separated range
            vals = range_in.split(",")
            self.input_range = (propertyparse.get_args_num_value(vals[0]), 
                                propertyparse.get_args_num_value(vals[1]))
        elif range_in == NORMALIZED_FLOAT:
            self.input_range = (0.0, 1.0)
    
    def _set_output_range(self):
        try:
            range_out = self.args[RANGE_OUT]
        except: # not defined, use default
            range_out = NORMALIZED_FLOAT

        if len(range_out.split(",")) == 2: # comma separeated range
            vals = range_out.split(",")
            self.output_range = (propertyparse.get_args_num_value(vals[0]), 
                                propertyparse.get_args_num_value(vals[1]))
        elif range_out == NORMALIZED_FLOAT:
            self.output_range = (0.0, 1.0)
            
    def get_out_value(self, in_value):
        """
        Converts input value to output value using ranges.
        """
        in_l, in_h = self.input_range
        out_l, out_h = self.output_range
        in_range = in_h - in_l
        out_range = out_h - out_l
        in_frac = in_value - in_l
        in_norm = in_frac / in_range
        return out_l + (in_norm * out_range)
    
    def get_current_in_value(self):
        """
        Corresponding input value for current self.value
        """
        return self.get_in_value(float(self.value))
        
    def get_in_value(self, out_value):
        """
        Converts output to input value
        """
        in_l, in_h = self.input_range
        out_l, out_h = self.output_range
        in_range = in_h - in_l
        out_range = out_h - out_l
        out_frac = propertyparse.get_args_num_value(str(out_value)) - out_l
        out_norm = out_frac / out_range
        return in_l + (out_norm * in_range)

    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range
        value = self.get_current_in_value()
        return gtk.Adjustment(float(value), float(lower), float(upper), float(step))
    
    def adjustment_value_changed(self, adjustment):
        value = adjustment.get_value()
        out_value = self.get_out_value(value)
        str_value = str(out_value)
        self.write_value(str_value)

    def boolean_button_toggled(self, button):
        if button.get_active():
            val = "1"
        else:
            val = "0"
        self.write_value(val)
        
    def color_selected(self, color_button):
        print "color_selected() not overridden"

    def combo_selection_changed(self, combo_box, values):
        value = values[combo_box.get_active()]
        self.write_value(str(value))
        
    def write_value(self, val):
        """
        This has to be overridden by all extending classes.
        """
        print "write_value() not overridden"
    
    def write_out_keyframes(self, keyframes):
        """
        This has to be overridden by extending classes 
        edited with keyframe editor.
        """
        print "write_out_keyframes() not overridden"
        
    def get_clip_length(self):
        return self.clip.clip_out - self.clip.clip_in + 1
        
    def get_clip_tline_pos(self):
        return self.track.clip_start(self.clip_index)
    
    def update_clip_index(self):
        self.clip_index = self.track.clips.index(self.clip)
        
    def get_pixel_aspect_ratio(self):
        return (float(current_sequence().profile.sample_aspect_num()) / 
                    current_sequence().profile.sample_aspect_den())
       
        
class EditableProperty(AbstractProperty):
    """
    A wrapper for mltfilter.FilterObject.properties array property tuple 
    and related data that converts user input to 
    property values.

    This class is used for properties of type PROP_INT and PROP_FLOAT.
    
    If property type is PROP_EXPRESSION an extending class is used
    to parse value expression from input.
    """
    def __init__(self, create_params):
        """
        property is tuple from FilterObject.properties array.
        args_str is args attribute value from filters.xml.
        """
        clip, filter_index, prop, property_index, args_str = create_params
        AbstractProperty.__init__(self, args_str)
        
        self.name, self.value, self.type = prop
        self.clip = clip
        self.filter_index = filter_index #index of param in clip.filters, clip created in sequence.py
        self.property_index = property_index # index of property in FilterObject.properties. This is the persistant object
        self.is_compositor_filter = False # This is after changed after creation if needed

    def _get_filter_object(self):
        """
        Filter being edited is in different places for normal filters 
        and filters that are part of compositors
        """
        if self.is_compositor_filter:
            return self.clip.compositor.filter
        else:
            return self.clip.filters[self.filter_index]
            
    def write_value(self, str_value): # overrides ConvertingProperty.write_value(str_value)
        self.write_mlt_property_str_value(str_value)
        self.value = str_value
        self.write_filter_object_property(str_value)
        
    def write_mlt_property_str_value(self, str_value):
        # mlt property value
        filter_object = self._get_filter_object()
        filter_object.mlt_filter.set(str(self.name), str(str_value))
        
    def write_filter_object_property(self, str_value):
        # Persistant python object
        filter_object = self._get_filter_object()
        prop = (str(self.name), str(str_value), self.type)
        filter_object.properties[self.property_index] = prop


class TransitionEditableProperty(AbstractProperty):
    """
    A wrapper for mlttransitions.CompositorObject.transition.properties 
    array property tuple and related data that converts user input to 
    property values.

    This class is used for properties of type PROP_INT and PROP_FLOAT.

    If property type is PROP_EXPRESSION an extending class is used
    to parse value expression from input.
    """
    def __init__(self, create_params):
        clip, prop, property_index, args_str = create_params
        AbstractProperty.__init__(self, args_str)
        
        self.name, self.value, self.type = prop
        self.clip = clip # this is actually compositor ducktyping for clip
        self.transition = clip.transition # ... is compositor.transition
        self.property_index = property_index # index of property in mlttransitions.CompositorObject.transition.properties.
                                             # This is the persistant object

    def get_clip_tline_pos(self):
        # self.clip is actually compositor ducktyping for clip
        return self.clip.clip_in # compositor in and out points staright in timeline frames
        
    def write_value(self, str_value):
        self.write_mlt_property_str_value(str_value)
        self.value = str_value
        self.write_transition_object_property(str_value)

    def write_mlt_property_str_value(self, str_value):
        self.transition.mlt_transition.set(str(self.name), str(str_value))
        
    def write_transition_object_property(self, str_value):
        # Persistant python object
        prop = (str(self.name), str(str_value), self.type)
        self.transition.properties[self.property_index] = prop


class NonMltEditableProperty(AbstractProperty):
    """
    A wrapper for editable persistent properties that do not write out values to MLT objects.
    Values of these are used to compute valuse that _are_ written to MLT.
    """
    def __init__(self, prop, args_str, clip, filter_index, non_mlt_property_index):
        AbstractProperty.__init__(self, args_str)
        self.name, self.value, self.type = prop
        self.clip = clip
        self.filter_index = filter_index
        self.non_mlt_property_index = non_mlt_property_index
        self.adjustment_listener = None # External listener that may be monkeypathched here

    def adjustment_value_changed(self, adjustment):
        if self.adjustment_listener != None:
            value = adjustment.get_value()
            out_value = self.get_out_value(value)
            self.adjustment_listener(self, out_value)
        
    def _get_filter_object(self):
        return self.clip.filters[self.filter_index]

    def write_number_value(self, numb):
        self.write_property_value(str(numb))

    def write_property_value(self, str_value):
        filter_object = self._get_filter_object()
        prop = (str(self.name), str(str_value), self.type)
        filter_object.non_mlt_properties[self.non_mlt_property_index] = prop
        self.value = str_value

    def get_float_value(self):
        return float(self.value)

# ----------------------------------------- PROP_EXPRESSION types extending classes
class SingleKeyFrameProperty(EditableProperty):
    """
    Converts adjustments to expressions like "0=value" and
    crates adjustments from expressions.
    """
    
    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range
        val = self.value.strip('"')
        epxr_sides = val.split("=")
        in_value = self.get_in_value(float(epxr_sides[1]))
        return gtk.Adjustment(float(in_value), float(lower), float(upper), float(step))

    def adjustment_value_changed(self, adjustment):
        value = adjustment.get_value()
        out_value = self.get_out_value(value)
        val_str = "0=" + str(out_value)
        self.write_value(val_str)


class AffineFilterGeomProperty(EditableProperty):
    """
    Converts values of four sliders to position and size info
    """
    def slider_values_changed(self, all_sliders, w):
        x_s, y_s, h_s = all_sliders
        x = x_s.get_adjustment().get_value()
        y = y_s.get_adjustment().get_value()
        h = h_s.get_adjustment().get_value()

        # "0=x/y:widthxheight:opacity"
        val_str = "0=" + str(x) + "/" + str(y) + ":" + str(w) + "x" + str(h) + ":100" # 100x MLT ignores width
        self.write_value(val_str)


class FreiPosHCSFilterProperty(EditableProperty):    
    def adjustment_value_changed(self, adjustment):
        value = adjustment.get_value()
        out_value = self.get_out_value(value)
        val_str = "0=" + str(out_value)
        self.write_value(val_str)

class OpacityInGeomSKFProperty(TransitionEditableProperty):
    """
    Converts adjustments to expressions like "0/0:720x576:76" for
    opacity of 76% and creates adjustments from expressions.
    
    Only opacity part is edited.
    """
    def __init__(self, params):
        TransitionEditableProperty.__init__(self, params)
        clip, property, property_index, args_str = params
        name, value, type = property
        self.value_parts = value.split(":")
    
    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range
        in_value = self.get_in_value(float(self.value_parts[2]))
        return gtk.Adjustment(float(in_value), float(lower), float(upper), float(step))

    def adjustment_value_changed(self, adjustment):
        value = adjustment.get_value()
        out_value = self.get_out_value(value)
        val_str = self.value_parts[0] + ":" + self.value_parts[1] + ":" + str(out_value)
        self.write_value(val_str)
 
        
class OpacityInGeomKeyframeProperty(TransitionEditableProperty):
    
    def __init__(self, params):
        TransitionEditableProperty.__init__(self, params)
        clip, property, property_index, args_str = params
        name, value, type = property
        
        # We need values of first keyframe for later
        key_frames = value.split(";")
        self.value_parts = key_frames[0].split(":")
        self.screen_size_str = self.value_parts[1]
        
    def get_input_range_adjustment(self):
        # initial opacity value
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range
        in_value = self.get_in_value(float(self.value_parts[2]))
        return gtk.Adjustment(float(in_value), float(lower), float(upper), float(step))

    def write_out_keyframes(self, keyframes):
        # key frame array of tuples (frame, opacity)
        val_str = ""
        for kf in keyframes:
            frame, opac = kf
            val_str += str(int(frame)) + "=" # frame
            val_str += "0/0:" # pos
            val_str += str(self.screen_size_str) + ":" # size
            val_str += str(self.get_out_value(opac)) + ";" # opac with converted range from slider
        
        val_str = val_str.strip(";")
        self.write_value(val_str)


class LUTTableProperty(EditableProperty):
    def reset_to_linear(self):
        self.write_value("LINEAR")

    def write_out_table(self, table):
        l = []
        for i in range(0, len(table)):

            l.append(str(table[i]))
            l.append(";")
        val_str = ''.join(l).rstrip(";")
        self.write_value(val_str)

        
class PointsListProperty(EditableProperty):
    
    def set_value_from_cr_points(self, crpoints):
        val_str = ""
        for i in range(0, len(crpoints)):
            p = crpoints[i]
            val_str = val_str + str(p.x) + "/"  + str(p.y)
            if i < len(crpoints) - 1:
                val_str = val_str + ";"
        self.write_value(val_str)


class KeyFrameGeometryOpacityProperty(TransitionEditableProperty):
    """
    Converts user edits to expressions like "12=11/21:720x576:76" for
    to keyframes for position scale and opacity.
    """
    def __init__(self, params):
        TransitionEditableProperty.__init__(self, params)
    
    def get_input_range_adjustment(self):
        # This is used for opacity slider
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range

        return gtk.Adjustment(float(1.0), float(lower), float(upper), float(step)) # Value set later to first kf value

    def write_out_keyframes(self, keyframes):
        # key frame array of tuples (frame, [x, y, width, height], opacity)
        val_str = ""
        for kf in keyframes:
            frame, rect, opac = kf
            val_str += str(int(frame)) + "=" # frame
            val_str += str(int(rect[0])) + "/" + str(int(rect[1])) + ":" # pos
            val_str += str(int(rect[2])) + "x" + str(int(rect[3])) + ":" # size
            val_str += str(self.get_out_value(opac)) + ";" # opac with converted range from slider
        
        val_str = val_str.strip(";")
        self.write_value(val_str)


class FreiGeomHCSTransitionProperty(TransitionEditableProperty):
    def __init__(self, params):
        TransitionEditableProperty.__init__(self, params)


class KeyFrameHCSFilterProperty(EditableProperty):
    """
    Coverts array of keyframe tuples to string of type "0=0.2;123=0.143"
    """
    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range
        return gtk.Adjustment(float(0.1), float(lower), float(upper), float(step)) # Value set later to first kf value
        
    def write_out_keyframes(self, keyframes):
        val_str = ""
        for kf in keyframes:
            frame, val = kf
            val_str += str(frame) + "=" + str(self.get_out_value(val)) + ";"
        
        val_str = val_str.strip(";")
        self.write_value(val_str)


class KeyFrameHCSTransitionProperty(TransitionEditableProperty):
    """
    Coverts array of keyframe tuples to string of type "0=0.2;123=0.143"
    """
    def __init__(self, params):
        TransitionEditableProperty.__init__(self, params)

    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range
        return gtk.Adjustment(float(0.1), float(lower), float(upper), float(step)) # Value set later to first kf value

    def write_out_keyframes(self, keyframes):
        val_str = ""
        for kf in keyframes:
            frame, val = kf
            val_str += str(frame) + "=" + str(self.get_out_value(val)) + ";"

        val_str = val_str.strip(";")
        self.write_value(val_str)


class ColorProperty(EditableProperty):
    """
    Gives value as gdk color for gui and writes out color as 
    different type of hex to mlt 
    """
    
    def get_value_as_gdk_color(self):
        raw_r, raw_g, raw_b = utils.hex_to_rgb(self.value)
        return gtk.gdk.Color(red=(float(raw_r)/255.0),
                             green=(float(raw_g)/255.0),
                             blue=(float(raw_b)/255.0))
        
    def color_selected(self, color_button):
        color = color_button.get_color()
        value = utils.hex_to_rgb(color.to_string())
        raw_r, raw_g, raw_b = value
        val_str = "#" + utils.int_to_hex(int((float(raw_r) * 255.0) / 65535.0)) + \
                        utils.int_to_hex(int((float(raw_g) * 255.0) / 65535.0)) + \
                        utils.int_to_hex(int((float(raw_b) * 255.0) / 65535.0))
                        
        self.write_value(val_str)


class WipeResourceProperty(TransitionEditableProperty):
    """
    Converts user combobox selections to absolute paths containing wipe
    resource images.
    """
    def __init__(self, params):
        TransitionEditableProperty.__init__(self, params)

    def combo_selection_changed(self, combo_box, keys):
        key = keys[combo_box.get_active()]
        res_path = mlttransitions.get_wipe_resource_path(key)
        self.write_value(str(res_path))
        

class MultipartKeyFrameProperty(AbstractProperty):
    
    def __init__(self, params):
        clip, filter_index, property, property_index, args_str = params
        AbstractProperty.__init__(self, args_str)
        self.name, self.value, self.type = property
        self.clip = clip
        self.filter_index = filter_index #index of param in clip.filters, clip created in sequence.py
        self.property_index = property_index # index of property in FilterObject.properties. This is the persistant object
        self.is_compositor_filter = False # This is after changed after creation if needed

    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range

        return gtk.Adjustment(float(0.1), float(lower), float(upper), float(step)) # Value set later to first kf value

    def write_out_keyframes(self, keyframes):
        val_str = ""
        for kf in keyframes:
            frame, val = kf
            val_str += str(frame) + "=" + str(self.get_out_value(val)) + ";"
        val_str = val_str.strip(";")
        self.value = val_str
        filter_object = self.clip.filters[self.filter_index]
        filter_object.update_value(val_str, self.clip, current_sequence().profile)


class AffineScaleProperty(EditableProperty):
    
    def get_input_range_adjustment(self):
        step = DEFAULT_STEP
        lower = 0
        upper = 500
        val = self.value.strip('"')
        epxr_sides = val.split("=")
        in_value = self.get_in_value(float(epxr_sides[1]))
        return gtk.Adjustment(float(in_value), float(lower), float(upper), float(step))

    def adjustment_value_changed(self, adjustment):
        value = adjustment.get_value()
        out_value = self.get_out_value(value)
        val_str = "0=" + str(out_value)
        self.write_value(val_str)

    def get_out_value(self, in_value):
        """
        Converts input value to output value using ranges.
        """
        # in_range = 500 # hard coded special case
        in_norm = in_value / 100.0 # to get 0 - 5, 1.0 no scaling
        if in_norm < 0.001:
            in_norm = 0.001
        out =  1 / in_norm
        return out

    def get_in_value(self, out_value):
        """
        Converts output to input value
        """
        # out_value =  1 / in_norm, range 1 / 0.001 -> 1 / 5
        if out_value < 0.001:
            out_value = 0.001
        in_value = (1 / (out_value)) * 100 # 0 - 500 range
        return in_value  

    def write_mlt_property_str_value(self, str_value):
        val = str_value.strip('"')
        epxr_sides = val.split("=")
        # mlt property value
        filter_object = self._get_filter_object()
        filter_object.mlt_filter.set(str(self.name), str(epxr_sides[1]))
        

# ------------------------------------------ creator func dicts
# dict EXPRESSION_TYPE args value -> class extending AbstractProperty
# Note: HCS means half comma separated
EDITABLE_PROPERTY_CREATORS = { \
    DEFAULT:lambda params : EditableProperty(params),
    DEFAULT_TRANSITION:lambda params : TransitionEditableProperty(params),
    SINGLE_KEYFRAME:lambda params: SingleKeyFrameProperty(params),
    OPACITY_IN_GEOM_SINGLE_KF: lambda params : OpacityInGeomSKFProperty(params),
    OPACITY_IN_GEOM_KF: lambda params : OpacityInGeomKeyframeProperty(params),
    KEYFRAME_HCS: lambda params : KeyFrameHCSFilterProperty(params),
    FREI_POSITION_HCS: lambda params : FreiPosHCSFilterProperty(params),
    FREI_GEOM_HCS_TRANSITION: lambda params : FreiGeomHCSTransitionProperty(params),
    KEYFRAME_HCS_TRANSITION: lambda params : KeyFrameHCSTransitionProperty(params),
    MULTIPART_KEYFRAME_HCS: lambda params : MultipartKeyFrameProperty(params),
    COLOR: lambda params : ColorProperty(params),
    GEOMETRY_OPACITY_KF: lambda params : KeyFrameGeometryOpacityProperty(params),
    GEOM_IN_AFFINE_FILTER: lambda params : AffineFilterGeomProperty(params),
    WIPE_RESOURCE : lambda params : WipeResourceProperty(params),
    LUT_TABLE : lambda params  : LUTTableProperty(params),
    NOT_PARSED : lambda params : EditableProperty(params), # This should only be used with params that have editor=NO_EDITOR
    NOT_PARSED_TRANSITION : lambda params : TransitionEditableProperty(params), # This should only be used with params that have editor=NO_EDITOR
    AFFINE_SCALE : lambda params : AffineScaleProperty(params) }

