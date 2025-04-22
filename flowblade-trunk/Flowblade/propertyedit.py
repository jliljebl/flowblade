"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

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

"""
Module provides wrapper objects for editing property values of objects in
the sequence. 

Properties are (name, value, type) tuples that are wrapped in objects 
extending AbstractProperty class for editing. These wrappers convert
edit inputs into mlt property values (that effect how sequence is displayed)
and python side values (that are persistent).
"""
import json

from gi.repository import Gtk

import animatedvalue
import appconsts
from editorstate import current_sequence
import mlttransitions
import mltfilters
import propertyparse
import utils


# keys                                                      meaning of values for this key
RANGE_IN = "range_in"                                       # values define user input range
RANGE_OUT = "range_out"                                     # values define range of output to mlt
STEP = "step"                                               # Gtk.Adjustment step_increment value is set using this
EXPRESSION_TYPE = "exptype"                                 # type of string expression used as value
EDITOR = "editor"                                           # editor used to edit property
DISPLAY_NAME = "displayname"                                # name of property that is displayed to user
MULTIPART_START_PROP = "multistartprop"                     # Value used to set multipart value at part start
MULTIPART_END_PROP = "multiendprop"                         # Value used to set multipart value at part end
ACCESSABLE_EDITOR = "access_editor"                          # Editor is placed in extraeditors.py global structure for access.

# ranges values                                             expression is replaced with 
NORMALIZED_FLOAT = "NORMALIZED_FLOAT"                       # range 0.0 - 1.0

#  PROP_EXPRESSION values, e.g. "exptype=keyframe_hcs"      parsed output
DEFAULT = "default"                                         # value     (str(int), str(float) or str(str))
DEFAULT_TRANSITION = "default_transition"                   # value     (str(int), str(float) or str(str))
SINGLE_KEYFRAME = "singlekeyframe"                          # DEPRECATED, were juat presenting standard slider for these now. This kept for back wards compatibility.
OPACITY_IN_GEOM_SINGLE_KF = "opacity_in_geom_kf_single"     # 0=0/0:SCREEN_WIDTHxSCREEN_HEIGHT:opacity
OPACITY_IN_GEOM_KF = "opacity_in_geom_kf"                   # frame=0/0:SCREEN_WIDTHxSCREEN_HEIGHT:opacity (kf_str;kf_str;kf_str;...;kf_str)
GEOMETRY_OPACITY_KF ="geom_opac_kf"                         # frame=x/y:widthxheight:opacity
GEOMETRY_RECT_FILTER_KF = "geom_filt_rect_kf"               # frame=x y w h 1  with 1 being constant for full opacity
GEOMETRY_ROTATING_FILTER_KF = "geom_filt_rotating_kf"       # extra editor parameter for "Positioan Size Rotation" filter
GEOM_IN_AFFINE_FILTER = "geom_in_affine_filt"               # x/y:widthxheight:opacity
GEOM_IN_AFFINE_FILTER_V2 =  "geom_in_affine_filt_v2"        # x/y:widthxheight:opacity
AFFINE_SCALE = "affine_scale"                               # special property to get the 1/ x that the filter wants
KEYFRAME_HCS = "keyframe_hcs"                               # frame=value(;frame=value) HCS = half comma separated
KEYFRAME_HCS_TRANSITION = "keyframe_hcs_transition"         # frame=value(;frame=value) HCS = half comma separated, used to edit transitions
MULTIPART_KEYFRAME_HCS = "multipart_keyframe"               # frame=value(;frame=value) series of mlt.Filter objects that get their properties set, HCS = half comma separated
FREI_POSITION_HCS = "frei_pos_hcs"                          # frame=x:y
FREI_GEOM_HCS_TRANSITION = "frei_geom_hcs"                  # time=x:y:x_scale:y_scale:rotation:mix
COLOR = "color"                                             # #rrggbb
CAIRO_COLOR = "cairo_color"                                             # #rrggbb but displayed as r and b switched
LUT_TABLE = "lut_table"                                     # val;val;val;val;...;val
WIPE_RESOURCE = "wipe_resource"                             # /path/to/resource.pgm
FILTER_WIPE_RESOURCE = "filter_wipe_resource"               # /path/to/resource.pgm
FILE_RESOURCE = "file_resource"                             # /path/to/somefile
ROTO_JSON = "roto_json"                                     # JSON string of keyframes and values
PLAIN_STRING = "plain_string"                               # String is just string, for text input
RECT_NO_KF = "rect_no_kf"                                     # x y w h
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

    args = propertyparse.args_string_to_args_dict(args_str)

    try:
        exp_type = args[EXPRESSION_TYPE] 
    except:
        # This fails for PROP_INT and PROP_FLOAT properties that are edited as keyframe properties.
        # The given exp_type is irrelevant when set for PROP_INT and PROP_FLOAT but causes crashes/undetermined behaviour if exp_type not set correctly in filters.xml
        # when required.
        exp_type = SINGLE_KEYFRAME
        
    if p_type == appconsts.PROP_EXPRESSION:
        """
        For expressions we can't do straight input output numerical
        conversion so we need an extending class for expression type.
        """
        creator_func = EDITABLE_PROPERTY_CREATORS[exp_type]
        ep = creator_func(params)
    elif exp_type == AFFINE_SCALE:
        ep = AffineScaleProperty(params) # This needs special casing because slider input is a number and output value is inverse of input, not a linear range conversion.
    else:
        """
        Properties with single numerical values (int or float) can be handled with objects of EditableProperty class.
        """
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
            For expressions we can't do straight input->output numerical
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

def get_non_mlt_editable_properties(clip, filter_object, filter_index, track, clip_index):
    # Creates editable properties that do not write their values to MLT properties.
    # Sometimes these are just simply not used, sometiemes data is saved in these 
    # encodes info that gets written into MLT properties.
    editable_properties = []
    for i in range(0, len(filter_object.non_mlt_properties)):
        prop = filter_object.non_mlt_properties[i]
        p_name, p_value, p_type = prop
        try:
            args_str = filter_object.info.property_args[p_name]
        except:
            # We added new parameter to rotomask after release and need fix data here.
            # For all normal filters just create new filter, but rotomask is such a complex beast that this was needed.
            if p_name == "mask_type":
                args_str = "editor=no_editor"
                filter_object.info.property_args[p_name] = args_str

        ep = NonMltEditableProperty(prop, args_str, clip, filter_index, i)
        ep.track = track
        ep.clip_index = clip_index
        editable_properties.append(ep)
    
    return editable_properties

# -------------------------------------------- property wrappers objs
class AbstractProperty:
    """
    A base class for all wrappers of property tuples in
    mltfilters.FilterObject.properties array and in
    mlttransitions.CompositorObject.transition.properties array.

    This class and all extending classes convert input to output using set ranges or
    other GUI editors. GUI input -> MLT property value.
    
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

    def get_page_factor(self, upper, lower, step):
        range_count = int(abs(float(upper)-float(lower))/float(step)) # number of steps in the range. 
        if range_count > 50: 
            page_factor=10 
        elif range_count > 25:
            page_factor=5 
        else:
            page_factor=1
        
        return page_factor

    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range
        value = self.get_current_in_value()
        page_factor = self.get_page_factor(upper, lower, step)
    
        return Gtk.Adjustment(value=float(value), lower=float(lower), upper=float(upper), step_increment=float(step), page_increment=float(step)*page_factor)
            
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
        print("color_selected() not overridden")

    def combo_selection_changed(self, combo_box, values):
        value = values[combo_box.get_active()]
        self.write_value(str(value))
        
    def write_value(self, val):
        """
        This has to be overridden by all extending classes.
        """
        print("write_value() not overridden")
    
    def write_out_keyframes(self, keyframes):
        """
        This has to be overridden by extending classes 
        edited with keyframe editor.
        """
        print("write_out_keyframes() not overridden")
        
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
    A wrapper for a mltfilter.FilterObject.properties array property tuple 
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
        self.property_index = property_index # index of property in FilterObject.properties. This is the persistent object
        self.is_compositor_filter = False # This is after changed after creation if needed

        self.used_create_params = create_params # for get_as_KeyFrameHCSFilterProperty functionality
        
    def _get_filter_object(self):
        """
        Filter being edited is in different places for normal filters 
        and filters that are part of compositors
        """
        if self.is_compositor_filter:
            return self.clip.compositor.filter
        else:
            return self.clip.filters[self.filter_index]

    def get_as_KeyFrameHCSFilterProperty(self):
        # this is entirely for feature allowing user to change between slider and kf editing
        clone_ep = KeyFrameHCSFilterProperty(self.used_create_params)

        clone_ep.prop_orig_type = self.type # we need this if user wants to get back slider editing
        
        clone_ep.value = self.value
        clone_ep.type = appconsts.PROP_EXPRESSION
        clone_ep.is_compositor_filter = self.is_compositor_filter
        clone_ep.track = self.track
        clone_ep.clip_index = self.clip_index

        return clone_ep
        
    def write_value(self, str_value):
        self.write_mlt_property_str_value(str_value)
        self.value = str_value
        self.write_filter_object_property(str_value)

    def write_mlt_property_str_value(self, str_value):
        # mlt property value
        filter_object = self._get_filter_object()
        filter_object.mlt_filter.set(str(self.name), str(str_value))
        
    def write_filter_object_property(self, str_value):
        # Persistent python object
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
                                             # This is the persistent object

    def get_clip_tline_pos(self):
        # self.clip is actually compositor ducktyping for clip
        return self.clip.clip_in # compositor in and out points straight in timeline frames
        
    def write_value(self, str_value):
        self.write_mlt_property_str_value(str_value)
        self.value = str_value
        self.write_transition_object_property(str_value)

    def write_mlt_property_str_value(self, str_value):
        self.transition.mlt_transition.set(str(self.name), str(str_value))
        
    def write_transition_object_property(self, str_value):
        # Persistent python object
        prop = (str(self.name), str(str_value), self.type)
        self.transition.properties[self.property_index] = prop


class NonMltEditableProperty(AbstractProperty):
    """
    A wrapper for editable persistent properties that do not write out values to MLT objects.
    Values of these are used to compute values that _are_ written to MLT.
    
    NOTE: WHEN USED WITH EDITORS should be noted that all values are strings.
    """
    def __init__(self, prop, args_str, clip, filter_index, non_mlt_property_index):
        AbstractProperty.__init__(self, args_str)
        self.name, self.value, self.type = prop
        self.clip = clip
        self.filter_index = filter_index
        self.non_mlt_property_index = non_mlt_property_index
        self.adjustment_listener = None # External listener that may be monkeypathched here
        self.write_adjustment_values = False # We are having this to avoid possible regressions when adding more editing capabilities to 
                                             # NonMltEditableProperty objects for 2.16, some earlier functionality could assume
                                             # that this is not happening.
                                             
    def adjustment_value_changed(self, adjustment):
        if self.adjustment_listener != None:
            value = adjustment.get_value()
            out_value = self.get_out_value(value)
            self.adjustment_listener(self, out_value)
        else:
            if self.write_adjustment_values == True:
                value = adjustment.get_value()
                out_value = self.get_out_value(value)
                self.write_number_value(out_value)
            
    def _get_filter_object(self):
        return self.clip.filters[self.filter_index]

    def write_value(self, val):
        self.write_property_value(val)

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
    creates adjustments from expressions.
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
        page_factor = self.get_page_factor(upper, lower, step)
    
        return Gtk.Adjustment(value=float(in_value), lower=float(lower), upper=float(upper), step_increment=float(step), page_increment=float(step)*page_factor)

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


class AffineFilterGeomPropertyV2(EditableProperty):
    """
    Converts values of four sliders to position and size info
    """
    def slider_values_changed(self, all_sliders, height):
        x_s, y_s, xs_s = all_sliders
        x = x_s.get_adjustment().get_value()
        y = y_s.get_adjustment().get_value()
        w = xs_s.get_adjustment().get_value()

        # "0=x/y:widthxheight:opacity"
        val_str = "0=" + str(x) + "/" + str(y) + ":" + str(w) + "x" + str(height) + ":100" # 100x MLT does translate for height
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
        page_factor = self.get_page_factor(upper, lower, step)

        return Gtk.Adjustment(value=float(in_value), lower=float(lower), upper=float(upper), step_increment=float(step), page_increment=float(step)*page_factor)

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
        page_factor = self.get_page_factor(upper, lower, step)

        return Gtk.Adjustment(value=float(in_value), lower=float(lower), upper=float(upper), step_increment=float(step), page_increment=float(step)*page_factor)

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
        page_factor = self.get_page_factor(upper, lower, step)

        return Gtk.Adjustment(value=float(1.0), lower=float(lower), upper=float(upper), step_increment=float(step), page_increment=float(step)*page_factor)


    def write_out_keyframes(self, keyframes):
        # key frame array of tuples (frame, [x, y, width, height], opacity)
        val_str = ""
        for kf in keyframes:
            frame, rect, opac, kf_type = kf
            
            eq_str = animatedvalue.TYPE_TO_EQ_STRING[kf_type]
                        
            val_str += str(int(frame)) + eq_str # frame
            val_str += str(int(rect[0])) + "/" + str(int(rect[1])) + ":" # pos
            val_str += str(int(rect[2])) + "x" + str(int(rect[3])) + ":" # size
            val_str += str(self.get_out_value(opac)) + ";" # opac with converted range from slider
        
        val_str = val_str.strip(";")
        self.write_value(val_str)


class KeyFrameFilterGeometryRectProperty(EditableProperty):

    def get_input_range_adjustment(self):
        # Returns DUMMY noop Adjustment that needs to exist because AbstrackKeyframeEditor assumes a slider always exists,
        # but this not the case for this editor/property pair.
  
        return Gtk.Adjustment(value=float(1.0), lower=float(0.0), upper=float(1.0), step_increment=float(0.01)) # Value set later to first kf value
        
    def write_out_keyframes(self, keyframes):
        # key frame array of tuples (frame, [x, y, width, height], opacity)
        val_str = ""
        for kf in keyframes:
            frame, rect, opac, kf_type = kf
            
            eq_str = animatedvalue.TYPE_TO_EQ_STRING[kf_type]
                        
            val_str += str(int(frame)) + eq_str # frame
            val_str += str(int(rect[0])) + " " + str(int(rect[1])) + " " # pos
            val_str += str(int(rect[2])) + " " + str(int(rect[3])) + " " # size
            val_str += "1"
            val_str += str(self.get_out_value(opac)) + ";" # opac with converted range from slider

        val_str = val_str.strip(";")
        self.write_value(val_str)


class KeyFrameFilterRotatingGeometryProperty:

    def __init__(self, create_params, editable_properties, track, clip_index):

        # Pick up the editable properties that actually have their values being written to on user edits
        # and affect to filter output.
        self.rect_ep = [ep for ep in editable_properties if ep.name == "transition.rect"][0]
        self.fix_rotate_x_ep = [ep for ep in editable_properties if ep.name == "transition.fix_rotate_x"][0]

        # Get create data
        clip, filter_index, p, i, args_str = create_params
        p_name, p_value, p_type = p

        # We need a lot stuff to ba able to edit this with keyframe editor as
        # propertyedit.EditableProperty.
        self.clip = clip
        self.value = "this is set below"
        self.is_compositor_filter = False
        self.track = track
        self.clip_index = clip_index
        self.get_input_range_adjustment = lambda : Gtk.Adjustment(value=float(100), lower=float(0), upper=float(100), step_increment=float(1))
        self.get_display_name = lambda : "Opacity"

        # We also need these to be able to edit this in keyframeeditcanvas.RotatingEditCanvas
        self.get_pixel_aspect_ratio = lambda : (float(current_sequence().profile.sample_aspect_num()) / current_sequence().profile.sample_aspect_den())
        self.get_in_value = lambda out_value : out_value # hard coded for opacity 100 -> 100 range

        # This value is parsed to keyframes by keyframecanvas.RotatingEditCanvas
        # using method propertyparse.filter_rotating_geom_keyframes_value_string_to_geom_kf_array(),
        # and is only used to the initialize the editor. The original design was that editor is given
        # property value strings, and they then call keyframe_parser() method that is set when editor is 
        # build for particular type of property string. Here we need to write out keyframes
        # to _two_ different properties, so this "dummy" editable property is created to act as the 
        # property being edited, and it converts editor output to property values of two different 
        # properties in method write_out_keyframes() below.
        self.value = self.get_value_keyframes_str()

    def get_clip_length(self):
        return self.clip.clip_out - self.clip.clip_in + 1
        
    def get_clip_tline_pos(self):
        return self.track.clip_start(self.clip_index)
        
    def get_value_keyframes_str(self):
        # Create input string for keyframecanvas.RotatingEditCanvas editor.
        rect_tokens = self.rect_ep.value.split(";")
        rotation_tokens = self.fix_rotate_x_ep.value.split(";")

        value = ""
        for rect_token, rotation_token in zip(rect_tokens, rotation_tokens):
            frame, rect_str, kf_type = propertyparse.get_token_frame_value_type(rect_token)
            frame, rotation, kf_type = propertyparse.get_token_frame_value_type(rotation_token)

            # returns [x, y, w, h, opacity], the string we need to input into "transition.rect" mlt property for filter "affine"
            rect = rect_str.split(" ")

            eq_str = propertyparse._get_eq_str(kf_type)

            frame_str = str(frame) + eq_str + str(rect[0]) + ":" + str(rect[1]) + ":" + str(rect[2]) + ":" + str(rect[3]) + ":" + str(rotation)
            value += frame_str + ";"

        # This value is parsed as keyframes in propertyparse.filter_rotating_geom_keyframes_value_string_to_geom_kf_array()
        value = value.strip(";")
        return value

    def get_input_range_adjustment(self):
        # Returns DUMMY noop Adjustment that needs to exist because AbstrackKeyframeEditor assumes a slider always exists,
        # but this not the case for this editor/property pair.
  
        return Gtk.Adjustment(value=float(1.0), lower=float(0.0), upper=float(1.0), step_increment=float(0.01)) # Value set later to first kf value
        
    def write_out_keyframes(self, keyframes):    
        rect_val = ""
        roto_val = ""
        profile_width = float(current_sequence().profile.width())
        profile_height = float(current_sequence().profile.height())
    
        for kf in keyframes:
            frame, transf, opacity, kf_type = kf
            x, y, x_scale, y_scale, rotation = transf
            
            eq_str = propertyparse._get_eq_str(kf_type)

            # Transform pos coordinates to intpretation used by mlt "affine" filter property "transition.rect"
            x_trans = x - profile_width / 2.0 + (profile_width - x_scale * profile_width) / 2.0 
            y_trans = y - profile_height / 2.0 + (profile_height - y_scale * profile_height) / 2.0

            rect_val += str(frame) + eq_str + str(x_trans) + " " + str(y_trans) + " " + \
                         str(profile_width * x_scale) + " " + str(profile_height * y_scale) + " 1" + ";" # opacity always 1 
            roto_val += str(frame) + eq_str + str(rotation) + ";"

        rect_val = rect_val.strip(";")
        roto_val = roto_val.strip(";")

        self.rect_ep.write_value(rect_val)
        self.fix_rotate_x_ep.write_value(roto_val)
 
    def write_value(self, str_value):
        pass
         
    def write_mlt_property_str_value(self, str_value):
        pass
         
    def write_filter_object_property(self, str_value):
        pass

    def update_clip_index(self):
        self.clip_index = self.track.clips.index(self.clip)

# dummytypes as a propertyedit.EditableProperty object.
class GradientTintExtraEditorProperty:

    def __init__(self, create_params, editable_properties, track, clip_index):

        # Pick up the editable properties that actually have their values being written to on user edits
        # and affect to filter output.
        # Relevant filter definition in filters.xml
        #        <property name="2" args="editor=slider range_in=0,100 displayname=Start!Opacity">0.5</property>
        #        <property name="4" args="editor=slider range_in=0,100 displayname=End!Opacity">0.5</property>
        #        <property name="5" args="editor=slider range_in=0,100 displayname=Start!X">0.5</property>
        #        <property name="6" args="editor=slider range_in=0,100 displayname=Start!Y">0.8</property>
        self.start_x = [ep for ep in editable_properties if ep.name == "5"][0]
        self.start_y = [ep for ep in editable_properties if ep.name == "6"][0]
        self.end_x = [ep for ep in editable_properties if ep.name == "7"][0]
        self.end_y = [ep for ep in editable_properties if ep.name == "8"][0]

          
        # Get create data
        clip, filter_index, p, i, args_str = create_params
        p_name, p_value, p_type = p

        # We need a lot stuff to ba able to edit this with keyframe editor as
        # propertyedit.EditableProperty.
        self.clip = clip
        self.value = "this is set below"
        self.is_compositor_filter = False
        self.track = track
        self.clip_index = clip_index
        self.get_input_range_adjustment = lambda : Gtk.Adjustment(value=float(100), lower=float(0), upper=float(100), step_increment=float(1))
        self.get_display_name = lambda : "Opacity"

        # We also need these to be able to edit this in keyframeeditcanvas.RotatingEditCanvas
        self.get_pixel_aspect_ratio = lambda : (float(current_sequence().profile.sample_aspect_num()) / current_sequence().profile.sample_aspect_den())
        self.get_in_value = lambda out_value : out_value # hard coded for opacity 100 -> 100 range

        # This value is parsed to keyframes by keyframecanvas.GradientEditCanvas
        # using method propertyparse.gradient_tint_geom_keyframes_value_string_to_geom_kf_array(),
        # and is only used to the initialize the editor. The original design was that editor is given
        # property value strings, and they then call keyframe_parser() method that is set when editor is 
        # build for particular type of property string. Here we need to write out keyframes
        # to multiple different properties, so this "dummy" editable property is created to act as the 
        # property being edited, and it converts editor output to property values of the properties
        # in method write_out_keyframes() below.
        self.value = self.get_value_keyframes_str()

    def get_clip_length(self):
        return self.clip.clip_out - self.clip.clip_in + 1
        
    def get_clip_tline_pos(self):
        return self.track.clip_start(self.clip_index)
        
    def get_value_keyframes_str(self):
        # Create input string for keyframecanvas.RotatingEditCanvas editor.
        start_x_tokens = self.start_x.value.split(";")
        start_y_tokens = self.start_y.value.split(";")
        end_x_tokens = self.end_x.value.split(";")
        end_y_tokens = self.end_y.value.split(";")

        value = ""
        for i in range(0, len(start_x_tokens)): # these all have the asme amount of keyframes always
            start_x_token = start_x_tokens[0]
            start_y_token = start_y_tokens[0]
            end_x_token = end_x_tokens[0]
            end_y_token = end_y_tokens[0]

            frame, start_x, kf_type = propertyparse.get_token_frame_value_type(start_x_token)
            frame, start_y, kf_type = propertyparse.get_token_frame_value_type(start_y_token)
            frame, end_x, kf_type = propertyparse.get_token_frame_value_type(end_x_token)
            frame, end_y, kf_type = propertyparse.get_token_frame_value_type(end_y_token)

            eq_str = propertyparse._get_eq_str(kf_type)

            frame_str = str(frame) + eq_str + str(start_x) + ":" + str(start_y) + ":" + str(end_x) + ":" + str(end_y)
            value += frame_str + ";"

        # This value is parsed as keyframes in propertyparse.gradient_tint_geom_keyframes_value_string_to_geom_kf_array()
        value = value.strip(";")

        return value

    def get_input_range_adjustment(self):
        # Returns DUMMY noop Adjustment that needs to exist because AbstrackKeyframeEditor assumes a slider always exists,
        # but this not the case for this editor/property pair.
  
        return Gtk.Adjustment(value=float(1.0), lower=float(0.0), upper=float(1.0), step_increment=float(0.01)) # Value set later to first kf value
        
    def write_out_keyframes(self, keyframes):

        start_x_val = ""
        start_y_val = ""
        end_x_val = ""
        end_y_val = "" 
        
        profile_width = float(current_sequence().profile.width())
        profile_height = float(current_sequence().profile.height())
    
        for kf in keyframes:

            frame, values, kf_type = kf
            start_x, start_y, end_x, end_y = values
            
            eq_str = propertyparse._get_eq_str(kf_type)

            # Editor keyframes are in pixel coords, filter wants normalised coods.
            start_x_tr = start_x / profile_width
            start_y_tr = start_y / profile_height
            end_x_tr = end_x / profile_width
            end_y_tr = end_y / profile_height
            
            # Build kf value strings
            start_x_val += str(frame) + eq_str + str(start_x_tr) + ";"
            start_y_val += str(frame) + eq_str + str(start_y_tr) + ";"
            end_x_val += str(frame) + eq_str + str(end_x_tr) + ";"
            end_y_val += str(frame) + eq_str +  str(end_y_tr) + ";"

        start_x_val.strip(";")
        start_y_val.strip(";")
        end_x_val.strip(";")
        end_y_val.strip(";")
        
        self.start_x.write_value(start_x_val)
        self.start_y.write_value(start_y_val)
        self.end_x.write_value(end_x_val)
        self.end_y.write_value(end_y_val)
        
    def write_value(self, str_value):
        pass
         
    def write_mlt_property_str_value(self, str_value):
        pass
         
    def write_filter_object_property(self, str_value):
        pass

    def update_clip_index(self):
        self.clip_index = self.track.clips.index(self.clip)


# dummytypes as a propertyedit.EditableProperty object.
class CropEditorProperty:

    def __init__(self, create_params, editable_properties, track, clip_index):

        # Pick up the editable properties that actually have their values being written to on user edits
        # and affect to filter output.
        # Relevant filter definition in filters.xml
        # <property name="Left" args="range_in=0.0,100.0 editor=slider step=0.1 scale_digits=1">0</property>
        # <property name="Right" args="range_in=0.0,100.0 editor=slider step=0.1 scale_digits=1">0</property>
        #<property name="Top" args="range_in=0.0,100.0 editor=slider step=0.1 scale_digits=1">0</property>
        # <property name="Bottom" args="range_in=0.0,100.0 editor=slider step=0.1 scale_digits=1">0</property>
        self.left = [ep for ep in editable_properties if ep.name == "Left"][0]
        self.right = [ep for ep in editable_properties if ep.name == "Right"][0]
        self.top = [ep for ep in editable_properties if ep.name == "Top"][0]
        self.bottom = [ep for ep in editable_properties if ep.name == "Bottom"][0]

        # Get create data
        clip, filter_index, p, i, args_str = create_params # p is a NonMltEditableProperty created for the extara editor 
                                                           # that uses this property but we don't use it anything, 
                                                           # editor values are written to the four editable properties above.

        # We need a lot stuff to ba able to edit this with keyframe editor as
        # propertyedit.EditableProperty.
        self.clip = clip
        self.value = "this is set below"
        self.is_compositor_filter = False
        self.track = track
        self.clip_index = clip_index
        self.get_input_range_adjustment = lambda : Gtk.Adjustment(value=float(100), lower=float(0), upper=float(100), step_increment=float(1))
        self.get_display_name = lambda : "Opacity"

        # We also need these to be able to edit this in keyframeeditcanvas.RotatingEditCanvas
        self.get_pixel_aspect_ratio = lambda : (float(current_sequence().profile.sample_aspect_num()) / current_sequence().profile.sample_aspect_den())
        self.get_in_value = lambda out_value : out_value 

        # This value is parsed to keyframes by keyframecanvas.CropEditingCAnvas
        # using method propertyparse.crop_geom_keyframes_value_string_to_geom_kf_array(),
        # and is only used to the initialize the editor. The original design was that editor is given
        # property value strings, and they then call keyframe_parser() method that is set when editor is 
        # build for particular type of property string. Here we need to write out keyframes
        # to _two_ different properties, so this "dummy" editable property is created to act as the 
        # property being edited, and it converts editor output to property values of two different 
        # properties in method write_out_keyframes() below.
        self.value = self.get_value_keyframes_str()

    def get_clip_length(self):
        return self.clip.clip_out - self.clip.clip_in + 1
        
    def get_clip_tline_pos(self):
        return self.track.clip_start(self.clip_index)
        
    def get_value_keyframes_str(self):
        # Create input string for keyframecanvas.BoxEditCanvas editor from
        # values being edited.
        # Parsed to keyframes used by keyframecanvas.BoxEditCanvas at
        # propertyparse.crop_geom_keyframes_value_string_to_geom_kf_array()
        left_tokens = self.left.value.strip(";").split(";")
        right_tokens = self.right.value.strip(";").split(";")
        top_tokens = self.top.value.strip(";").split(";")
        bottom_tokens = self.bottom.value.strip(";").split(";")

        value = ""
        for i in range(0, len(left_tokens)): # these all have the same amount of keyframes always
            left_token = left_tokens[i]
            right_token = right_tokens[i]
            top_token = top_tokens[i]
            bottom_token = bottom_tokens[i]

            frame, left, kf_type = propertyparse.get_token_frame_value_type(left_token)
            frame, right, kf_type = propertyparse.get_token_frame_value_type(right_token)
            frame, top, kf_type = propertyparse.get_token_frame_value_type(top_token)
            frame, bottom, kf_type = propertyparse.get_token_frame_value_type(bottom_token)

            eq_str = propertyparse._get_eq_str(kf_type)

            frame_str = str(frame) + eq_str + str(left) + ":" + str(right) + ":" + str(top) + ":" + str(bottom)
            value += frame_str + ";"

        # This value is parsed as keyframes in propertyparse.crop_geom_keyframes_value_string_to_geom_kf_array()
        value = value.strip(";")

        return value

    def get_input_range_adjustment(self):
        # Returns DUMMY noop Adjustment that needs to exist because AbstrackKeyframeEditor assumes a slider always exists,
        # but this not the case for this editor/property pair.
  
        return Gtk.Adjustment(value=float(1.0), lower=float(0.0), upper=float(1.0), step_increment=float(0.01)) # Value set later to first kf value
        
    def write_out_keyframes(self, keyframes):

        left_val = ""
        right_val = ""
        top_val = ""
        bottom_val = "" 
        
        profile_width = float(current_sequence().profile.width())
        profile_height = float(current_sequence().profile.height())
    
        for kf in keyframes:

            frame, rect, opacity, kf_type = kf
            x = rect[0]
            y = rect[1]
            w = rect[2]
            h = rect[3] 

            eq_str = propertyparse._get_eq_str(kf_type) 

            # Editor keyframes are in pixel coords, filter wants normalised coods.
            left_tr = self._clamp_norm(x / profile_width)
            right_tr = self._clamp_norm((profile_width - (x + w)) / profile_width)
            top_tr = self._clamp_norm(y / profile_height)
            bottom_tr = self._clamp_norm((profile_height - (y + h)) / profile_height)
            
            # Build kf value strings
            left_val += str(frame) + eq_str + str(left_tr) + ";"
            right_val += str(frame) + eq_str + str(right_tr) + ";"
            top_val += str(frame) + eq_str + str(top_tr) + ";"
            bottom_val += str(frame) + eq_str +  str(bottom_tr) + ";"

        left_val.strip(";")
        right_val.strip(";")
        top_val.strip(";")
        bottom_val.strip(";")
        
        self.left.write_value(left_val)
        self.right.write_value(right_val)
        self.top.write_value(top_val)
        self.bottom.write_value(bottom_val)

    def _clamp_norm(self, val):
        if val < 0.0:
            val = 0.0
        elif val > 1.0:
            val = 1.0
        
        return val

    def write_value(self, str_value):
        pass
         
    def write_mlt_property_str_value(self, str_value):
        pass
         
    def write_filter_object_property(self, str_value):
        pass

    def update_clip_index(self):
        self.clip_index = self.track.clips.index(self.clip)


class AlphaShapeRotatingGeometryProperty:

    def __init__(self, create_params, editable_properties, track, clip_index):

        # Pick up the editable properties that actually have their values being written to on user edits
        # and affect to filter output.
        #<property name="Position X" args="range_in=0,100 editor=keyframe_editor exptype=keyframe_hcs displayname=Pos!X">0=0.5</property>
        #<property name="Position Y" args="range_in=0,100 editor=keyframe_editor exptype=keyframe_hcs displayname=Pos!Y">0=0.5</property>
        #<property name="Size X" args="range_in=0,100 editor=keyframe_editor exptype=keyframe_hcs displayname=Size!X">0=0.5</property>
        #<property name="Size Y" args="range_in=0,100 editor=keyframe_editor exptype=keyframe_hcs displayname=Size!Y">0=0.5</property>
        #<property name="Tilt" args="range_in=0,100 editor=keyframe_editor exptype=keyframe_hcs displayname=Tilt">0=0.5</property>
        
        self.pos_x = [ep for ep in editable_properties if ep.name == "Position X"][0]
        self.pos_y = [ep for ep in editable_properties if ep.name == "Position Y"][0]
        self.size_x = [ep for ep in editable_properties if ep.name == "Size X"][0]
        self.size_y = [ep for ep in editable_properties if ep.name == "Size Y"][0]
        self.tilt = [ep for ep in editable_properties if ep.name == "Tilt"][0]
        
        # Get create data
        clip, filter_index, p, i, args_str = create_params
        p_name, p_value, p_type = p

        # We need a lot stuff to ba able to edit this with keyframe editor as
        # propertyedit.EditableProperty.
        self.clip = clip
        self.value = "this is set below"
        self.is_compositor_filter = False
        self.track = track
        self.clip_index = clip_index
        self.get_input_range_adjustment = lambda : Gtk.Adjustment(value=float(100), lower=float(0), upper=float(100), step_increment=float(1))
        self.get_display_name = lambda : "Opacity"

        # We also need these to be able to edit this in keyframeeditcanvas.RotatingEditCanvas
        self.get_pixel_aspect_ratio = lambda : (float(current_sequence().profile.sample_aspect_num()) / current_sequence().profile.sample_aspect_den())
        self.get_in_value = lambda out_value : out_value # hard coded for opacity 100 -> 100 range

        # This value is parsed to keyframes by keyframecanvas.RotatingEditCanvas
        # using method propertyparse.filter_rotating_geom_keyframes_value_string_to_geom_kf_array(),
        # and is only used to the initialize the editor. The original design was that editor is given
        # property value strings, and they then call keyframe_parser() method that is set when editor is 
        # build for particular type of property string. Here we need to write out keyframes
        # to _two_ different properties, so this "dummy" editable property is created to act as the 
        # property being edited, and it converts editor output to property values of two different 
        # properties in method write_out_keyframes() below.
        self.value = self.get_value_keyframes_str()

    def get_clip_length(self):
        return self.clip.clip_out - self.clip.clip_in + 1
        
    def get_clip_tline_pos(self):
        return self.track.clip_start(self.clip_index)
        
    def get_value_keyframes_str(self):
        # Create input string for keyframecanvas.RotatingEditCanvas editor.
        pos_x_tokens = self.pos_x.value.strip(";").split(";")
        pos_y_tokens = self.pos_y.value.strip(";").split(";")
        size_x_tokens = self.size_x.value.strip(";").split(";")
        size_y_tokens = self.size_y.value.strip(";").split(";")
        tilt_tokens = self.tilt.value.strip(";").split(";")

        profile_width = float(current_sequence().profile.width())
        profile_height = float(current_sequence().profile.height())
        
        value = ""
        for i in range(0, len(pos_x_tokens)):
            pos_x_token = pos_x_tokens[i]
            pos_y_token = pos_y_tokens[i]
            size_x_token = size_x_tokens[i]
            size_y_token = size_y_tokens[i]
            tilt_token = tilt_tokens[i]
            frame, x, kf_type = propertyparse.get_token_frame_value_type(pos_x_token)
            frame, y, kf_type = propertyparse.get_token_frame_value_type(pos_y_token)
            frame, w, kf_type = propertyparse.get_token_frame_value_type(size_x_token)
            frame, h, kf_type = propertyparse.get_token_frame_value_type(size_y_token)
            frame, tilt, kf_type = propertyparse.get_token_frame_value_type(tilt_token)

            x_scale = (float(w) * 2.0)
            y_scale = (float(h) * 2.0)
            x_tr = (float(x) - 0.5 * x_scale) * profile_width 
            y_tr = (float(y) - 0.5 * y_scale) * profile_height
            size_x_tr = float(w) * 2.0 * profile_width
            size_y_tr = float(h) * 2.0 * profile_height
            rotation = (float(tilt) - 0.5) * 360.0 
            
            eq_str = propertyparse._get_eq_str(kf_type)

            frame_str = str(frame) + eq_str + str(x_tr) + ":" + str(y_tr) + ":" + str(size_x_tr) + ":" + str(size_y_tr) + ":" + str(rotation)
            value += frame_str + ";"

        # This value is parsed as keyframes in propertyparse.filter_rotating_geom_keyframes_value_string_to_geom_kf_array()
        value = value.strip(";")

        return value

    def get_input_range_adjustment(self):
        # Returns DUMMY noop Adjustment that needs to exist because AbstrackKeyframeEditor assumes a slider always exists,
        # but this not the case for this editor/property pair.
  
        return Gtk.Adjustment(value=float(1.0), lower=float(0.0), upper=float(1.0), step_increment=float(0.01)) # Value set later to first kf value
        
    def write_out_keyframes(self, keyframes):    
        pos_x_val = ""
        pos_y_val = ""
        size_x_val = ""
        size_y_val = ""
        tilt_val = ""

        profile_width = float(current_sequence().profile.width())
        profile_height = float(current_sequence().profile.height())
    
        for kf in keyframes:
            frame, transf, opacity, kf_type = kf
            x, y, x_scale, y_scale, rotation = transf
            
            eq_str = propertyparse._get_eq_str(kf_type)

            # Editor keyframes are in pixel coords, filter wants 0 - 1, where 0.5 is non-transformed value. 
            pos_x_tr = (x - (profile_width / 2.0)) / profile_width + 0.5
            pos_y_tr = (y - (profile_height / 2.0)) / profile_height + 0.5
            size_x_tr = x_scale / 2.0
            size_y_tr = y_scale / 2.0
            tilt_tr = rotation / 360.0 + 0.5
            
            # Build kf value strings
            pos_x_val += str(frame) + eq_str + str(pos_x_tr) + ";"
            pos_y_val += str(frame) + eq_str + str(pos_y_tr) + ";"
            size_x_val += str(frame) + eq_str + str(size_x_tr) + ";"
            size_y_val += str(frame) + eq_str +  str(size_y_tr) + ";"
            tilt_val += str(frame) + eq_str +  str(tilt_tr) + ";"



        pos_x_val = pos_x_val.strip(";")
        pos_y_val = pos_y_val.strip(";")
        size_x_val = size_x_val.strip(";")
        size_y_val = size_y_val.strip(";")
        tilt_val = tilt_val.strip(";")

        self.pos_x.write_value(pos_x_val)
        self.pos_y.write_value(pos_y_val)
        self.size_x.write_value(size_x_val)
        self.size_y.write_value(size_y_val)
        self.tilt.write_value(tilt_val)
 
    def write_value(self, str_value):
        pass
         
    def write_mlt_property_str_value(self, str_value):
        pass
         
    def write_filter_object_property(self, str_value):
        pass

    def update_clip_index(self):
        self.clip_index = self.track.clips.index(self.clip)
        

class FreiGeomHCSTransitionProperty(TransitionEditableProperty):
    def __init__(self, params):
        TransitionEditableProperty.__init__(self, params)


class KeyFrameHCSFilterProperty(EditableProperty):
    """
    Converts array of keyframe tuples to string of type "0=0.2;123=0.143"
    """
    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range
        page_factor = self.get_page_factor(upper, lower, step)

        return Gtk.Adjustment(value=float(0.1), lower=float(lower), upper=float(upper), step_increment=float(step), page_increment=float(step)*page_factor)
        
    def write_out_keyframes(self, keyframes):
        val_str = ""
        for kf in keyframes:
            frame, val, kf_type = kf
            
            eq_str = animatedvalue.TYPE_TO_EQ_STRING[kf_type]
            
            val_str += str(frame) + eq_str + str(self.get_out_value(val)) + ";"
        
        val_str = val_str.strip(";")
        self.write_value(val_str)


class RotoJSONProperty(EditableProperty):

    def write_out_keyframes(self, keyframes):
        val_str = "{"
        for kf_obj in keyframes:
            kf, points, kf_type = kf_obj
            val_str += '"' + str(kf) + '"' + ':'
            val_str += json.dumps(points) + ","
        
        val_str = val_str.rstrip(",")
        val_str += "}"
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
        page_factor = self.get_page_factor(upper, lower, step)
    
        return Gtk.Adjustment(value=float(0.1), lower=float(lower), upper=float(upper), step_increment=float(step), page_increment=float(step)*page_factor)

    def write_out_keyframes(self, keyframes):
        val_str = ""
        for kf in keyframes:
            frame, val, type = kf
            val_str += str(frame) + "=" + str(self.get_out_value(val)) + ";"

        val_str = val_str.strip(";")
        self.write_value(val_str)


class ColorProperty(EditableProperty):
    """
    Gives value as gdk color for gui and writes out color as 
    different type of hex to mlt.
    """

    def get_value_rgba(self):
        raw_r, raw_g, raw_b = utils.hex_to_rgb(self.value)
        return (float(raw_r)/255.0, float(raw_g)/255.0, float(raw_b)/255.0, 1.0)

    def color_selected(self, color_button):
        color = color_button.get_color()
        raw_r, raw_g, raw_b = color.to_floats()
        val_str = "#" + utils.int_to_hex_str(int(raw_r * 255.0)) + \
                        utils.int_to_hex_str(int(raw_g * 255.0)) + \
                        utils.int_to_hex_str(int(raw_b * 255.0))
        self.write_value(val_str)


class CairoColorProperty(EditableProperty):
    """
    Gives value as gdk color for gui and writes out color as 
    different type of hex to mlt, for uses R and B switched,
    there is something gone wrom
    """
    def get_value_rgba(self):
        raw_r, raw_g, raw_b = utils.hex_to_rgb(self.value)
        return (float(raw_r)/255.0, float(raw_g)/255.0, float(raw_b)/255.0, 1.0)

    def color_selected(self, color_button):
        color = color_button.get_color()
        raw_r, raw_g, raw_b = color.to_floats()
        val_str = "#" + utils.int_to_hex_str(int(raw_r * 255.0)) + \
                        utils.int_to_hex_str(int(raw_g * 255.0)) + \
                        utils.int_to_hex_str(int(raw_b * 255.0))
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


class FilterWipeResourceProperty(EditableProperty):
    """
    Converts user combobox selections to absolute paths containing wipe
    resource images.
    """
    def __init__(self, params):
        EditableProperty.__init__(self, params)

    def combo_selection_changed(self, combo_box, keys):
        key = keys[combo_box.get_active()]
        res_path = mlttransitions.get_wipe_resource_path(key)
        self.write_value(str(res_path))
    
    
class FileResourceProperty(EditableProperty):
    """
    A file path as property value set from file chooser dialog callback.
    """
    def dialog_response_callback(self, dialog, response_id):
        res_path = dialog.get_filename()
        if response_id == Gtk.ResponseType.ACCEPT and res_path != None:
            self.write_value(str(res_path))
        else:
            self.write_value(str(""))

        # We're using the gtkbuilder.get_file_chooser_button_with_dialog() thing here.
        dialog.b.set_label(dialog.b._filename(res_path))
        dialog.hide()


class RectNoKeyframes(EditableProperty):

    def write_out_keyframes(self, keyframes):
        val_str = ""
        kf =  keyframes[0]
        frame, rect, opac, kf_type = kf

        val_str += str(int(rect[0])) + " " + str(int(rect[1])) + " " # pos
        val_str += str(int(rect[2])) + " " + str(int(rect[3])) + " " # size

        self.write_value(val_str)


class MultipartKeyFrameProperty(AbstractProperty):
    
    def __init__(self, params):
        clip, filter_index, property, property_index, args_str = params
        AbstractProperty.__init__(self, args_str)
        self.name, self.value, self.type = property
        self.clip = clip
        self.filter_index = filter_index #index of param in clip.filters, clip created in sequence.py
        self.property_index = property_index # index of property in FilterObject.properties. This is the persistent object
        self.is_compositor_filter = False # This is after changed after creation if needed

    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range
        page_factor = self.get_page_factor(upper, lower, step)
    
        return Gtk.Adjustment(value=float(0.1), lower=float(lower), upper=float(upper), step_increment=float(step), page_increment=float(step)*page_factor)

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

    def get_out_value(self, in_value):
        """
        Converts input value to output value using ranges.
        """
        in_norm = float(in_value) / 100.0
        if in_norm < 0.001:
            in_norm = 0.001
        out =  1.0 / in_norm
        
        return out

    def get_in_value(self, out_value):
        """
        Converts output to input value
        """
        if out_value < 0.001:
            out_value = 0.001
        in_value = (1.0 / float(out_value)) * 100.0

        return in_value  


# ------------------------------------------ creator func dicts
# dict EXPRESSION_TYPE args value -> class extending AbstractProperty
# Note: HCS means half comma separated
EDITABLE_PROPERTY_CREATORS = { \
    DEFAULT:lambda params : EditableProperty(params),
    PLAIN_STRING:lambda params : EditableProperty(params),
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
    CAIRO_COLOR: lambda params : CairoColorProperty(params),
    GEOMETRY_OPACITY_KF: lambda params : KeyFrameGeometryOpacityProperty(params),
    GEOMETRY_RECT_FILTER_KF: lambda params : KeyFrameFilterGeometryRectProperty(params),
    GEOMETRY_ROTATING_FILTER_KF: lambda params : KeyFrameFilterRotatingGeometryProperty(params),
    GEOM_IN_AFFINE_FILTER: lambda params : AffineFilterGeomProperty(params),
    GEOM_IN_AFFINE_FILTER_V2: lambda params :AffineFilterGeomPropertyV2(params),
    WIPE_RESOURCE : lambda params : WipeResourceProperty(params),
    FILTER_WIPE_RESOURCE : lambda params : FilterWipeResourceProperty(params),
    FILE_RESOURCE : lambda params : FileResourceProperty(params),
    ROTO_JSON  : lambda params : RotoJSONProperty(params),
    LUT_TABLE : lambda params : LUTTableProperty(params),
    RECT_NO_KF : lambda params : RectNoKeyframes(params),
    NOT_PARSED : lambda params : EditableProperty(params), # This should only be used with params that have editor=NO_EDITOR
    NOT_PARSED_TRANSITION : lambda params : TransitionEditableProperty(params), # This should only be used with params that have editor=NO_EDITOR
    AFFINE_SCALE : lambda params : AffineScaleProperty(params) }

