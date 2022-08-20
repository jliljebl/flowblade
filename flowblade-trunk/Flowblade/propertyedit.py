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
import json

from gi.repository import Gtk

import appconsts
from editorstate import current_sequence
import gui
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

def get_non_mlt_editable_properties(clip, filter_object, filter_index):
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

    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range
        value = self.get_current_in_value()

        return Gtk.Adjustment(value=float(value), lower=float(lower), upper=float(upper), step_incr=float(step))
    
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
       
    def enable_save_menu_item(self):
        gui.editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(True)

    
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
        self.property_index = property_index # index of property in FilterObject.properties. This is the persistant object
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
        return self.clip.clip_in # compositor in and out points straight in timeline frames
        
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
    Values of these are used to compute values that _are_ written to MLT.
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

    def write_value(self, val):
        pass # There has not defined need for this.

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

        return Gtk.Adjustment(value=float(in_value), lower=float(lower), upper=float(upper), step_incr=float(step))

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

        return Gtk.Adjustment(value=float(in_value), lower=float(lower), upper=float(upper), step_incr=float(step))

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

        return Gtk.Adjustment(value=float(in_value), lower=float(lower), upper=float(upper), step_incr=float(step))

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
        #print("write_out_keyframes", val_str)

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

        return Gtk.Adjustment(value=float(1.0), lower=float(lower), upper=float(upper), step_incr=float(step)) # Value set later to first kf value

    def write_out_keyframes(self, keyframes):
        # key frame array of tuples (frame, [x, y, width, height], opacity)
        val_str = ""
        for kf in keyframes:
            frame, rect, opac, kf_type = kf
            
            if kf_type == appconsts.KEYFRAME_LINEAR:
                eq_str = appconsts.KEYFRAME_LINEAR_EQUALS_STR
            elif kf_type == appconsts.KEYFRAME_SMOOTH:
                eq_str = appconsts.KEYFRAME_SMOOTH_EQUALS_STR
            else:
                eq_str = appconsts.KEYFRAME_DISCRETE_EQUALS_STR
                        
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
  
        return Gtk.Adjustment(value=float(1.0), lower=float(0.0), upper=float(1.0), step_incr=float(0.01)) # Value set later to first kf value
        
    def write_out_keyframes(self, keyframes):
        # key frame array of tuples (frame, [x, y, width, height], opacity)
        val_str = ""
        for kf in keyframes:
            frame, rect, opac, kf_type = kf
            
            if kf_type == appconsts.KEYFRAME_LINEAR:
                eq_str = appconsts.KEYFRAME_LINEAR_EQUALS_STR
            elif kf_type == appconsts.KEYFRAME_SMOOTH:
                eq_str = appconsts.KEYFRAME_SMOOTH_EQUALS_STR
            else:
                eq_str = appconsts.KEYFRAME_DISCRETE_EQUALS_STR
                        
            val_str += str(int(frame)) + eq_str # frame
            val_str += str(int(rect[0])) + " " + str(int(rect[1])) + " " # pos
            val_str += str(int(rect[2])) + " " + str(int(rect[3])) + " " # size
            val_str += "1"
            val_str += str(self.get_out_value(opac)) + ";" # opac with converted range from slider
        
        
        print(val_str)
        val_str = val_str.strip(";")
        self.write_value(val_str)

 
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
 
        return Gtk.Adjustment(value=float(0.1), lower=float(lower), upper=float(upper), step_incr=float(step)) # Value set later to first kf value
        
    def write_out_keyframes(self, keyframes):
        val_str = ""
        for kf in keyframes:
            frame, val, kf_type = kf
            
            if kf_type == appconsts.KEYFRAME_LINEAR:
                eq_str = appconsts.KEYFRAME_LINEAR_EQUALS_STR
            elif kf_type == appconsts.KEYFRAME_SMOOTH:
                eq_str = appconsts.KEYFRAME_SMOOTH_EQUALS_STR
            else:
                eq_str = appconsts.KEYFRAME_DISCRETE_EQUALS_STR
                
            val_str += str(frame) + eq_str + str(self.get_out_value(val)) + ";"
        
        val_str = val_str.strip(";")
        self.write_value(val_str)


class RotoJSONProperty(EditableProperty):

    def write_out_keyframes(self, keyframes):
        self.enable_save_menu_item()
        val_str = "{"
        for kf_obj in keyframes:
            kf, points = kf_obj
            val_str += '"' + str(kf) + '"' + ':'
            val_str += json.dumps(points) + ","
        
        val_str = val_str.rstrip(",")
        val_str += "}"
        self.write_value(val_str)


class KeyFrameHCSTransitionProperty(TransitionEditableProperty):
    """
    Converts array of keyframe tuples to string of type "0=0.2;123=0.143"
    """
    def __init__(self, params):
        TransitionEditableProperty.__init__(self, params)

    def get_input_range_adjustment(self):
        try:
            step = propertyparse.get_args_num_value(self.args[STEP])
        except:
            step = DEFAULT_STEP
        lower, upper = self.input_range

        return Gtk.Adjustment(value=float(0.1), lower=float(lower), upper=float(upper), step_incr=float(step)) # Value set later to first kf value

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

        return Gtk.Adjustment(value=float(0.1), lower=float(lower), upper=float(upper), step_incr=float(step)) # Value set later to first kf value

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


# ----------------------------------------------------------------------------- AFFINE FILTER TRANSFORM
"""
Refactor Affine Blend EditableProperty ducktyping object to be like the below instead of the current EmptyClass thing.

class FilterAffineTransformEditableProperty:
    
    def __init__(self, clip, editable_properties):

        # pack real properties to go
        self.x = [ep for ep in editable_properties if ep.name == "transition.ox"][0]
        self.y = [ep for ep in editable_properties if ep.name == "transition.oy"][0]
        self.x_scale = [ep for ep in editable_properties if ep.name == "transition.scale_x"][0]
        self.y_scale = [ep for ep in editable_properties if ep.name == "transition.scale_y"][0]
        self.rotation = [ep for ep in editable_properties if ep.name == "transition.fix_rotate_x"][0]
        self.opacity = [ep for ep in editable_properties if ep.name == "opacity"][0]
        # Screen width and height are needed for anchor point related conversions
        self.profile_width = current_sequence().profile.width()
        self.profile_height = current_sequence().profile.height()
        #self.aspect_ratio = float(self.profile_width) / self.profile_height
        # duck type methods, using opacity is not meaningful, any property with clip member could do
        self.clip = self.x.clip
        self.get_clip_tline_pos = lambda : clip.clip_in # clip is compositor, compositor in and out points straight in timeline frames
        self.get_clip_length = lambda : clip.get_length()
        self.get_input_range_adjustment = lambda : Gtk.Adjustment(float(100), float(0), float(100), float(1))
        self.get_display_name = lambda : "GGSFSF"
        self.get_pixel_aspect_ratio = lambda : (float(current_sequence().profile.sample_aspect_num()) / current_sequence().profile.sample_aspect_den())
        self.get_in_value = lambda out_value : out_value # hard coded for opacity 100 -> 100 range
        self.write_out_keyframes = lambda w_kf : self._rotating_ge_write_out_keyframes(w_kf)
        self.update_prop_value = lambda : self._noop()

        value = self._get_initial_value_str()
        self.value = value.strip(";")

    def _get_initial_value_str(self):
        # duck type members
        x_tokens = self.x.value.split(";")
        y_tokens = self.y.value.split(";")
        x_scale_tokens = self.x_scale.value.split(";")
        y_scale_tokens = self.y_scale.value.split(";")
        rotation_tokens = self.rotation.value.split(";")
        opacity_tokens = self.opacity.value.split(";")
        
        value = ""
        for i in range(0, len(x_tokens)): # these better match, same number of keyframes for all values, or this will not work
            frame, x = x_tokens[i].split("=")
            x = -float(x) + float(self.profile_width) / 2.0 # -x is how MLT wants this param, offset is to make editor and output match 
            frame, y = y_tokens[i].split("=")
            y = -float(y) + float(self.profile_height) / 2.0  # this how MLT want this param
            frame, x_scale = x_scale_tokens[i].split("=")
            x_scale = 1.0 / float(x_scale) # this how MLT want this param
            frame, y_scale = y_scale_tokens[i].split("=")
            y_scale = 1.0 / float(y_scale) # this how MLT want this param
            frame, rotation = rotation_tokens[i].split("=")
            frame, opacity = opacity_tokens[i].split("=")
            opacity = 1.0 # we ae not editing this so let's make it alwaus constant
            
            frame_str = str(frame) + "=" + str(x) + ":" + str(y) + ":" + str(x_scale) + ":" + str(y_scale) + ":" + str(rotation) + ":" + str(opacity)
            value += frame_str + ";"

        return value

    def _noop(self):
        pass

    def _rotating_ge_write_out_keyframes(self, keyframes):

        x_val = ""
        y_val = ""
        x_scale_val = ""
        y_scale_val = ""
        rotation_val = ""
        opacity_val = ""
        
        for kf in keyframes:
            frame, transf, opacity = kf
            x, y, x_scale, y_scale, rotation = transf
            print (type(x), type(y), type(x_scale), type(y_scale), type(rotation))
            print("X:", x, "Y:", y)
            x_val += str(frame) + "=" + str(((-x)) + (float(self.profile_width)/2.0) * x_scale) + ";" # (self.profile_width/2.0)) editor thinks anchor point has been offset into middle of image, filter does this automatically.
            y_val += str(frame) + "=" + str(((-y)) + (float(self.profile_height)/2.0) * y_scale) + ";"
            x_scale_val += str(frame) + "=" + str(1.0/x_scale) + ";"
            y_scale_val += str(frame) + "=" + str(1.0/y_scale) + ";"
            rotation_val += str(frame) + "=" + str(rotation) + ";"
            opacity_val += str(frame) + "=" + str(1.0) + ";"

            print("KF ____________________________________________________________________")
            print(x, y, x_scale, y_scale, rotation)
            print(x_val, y_val, x_scale_val, y_scale_val, rotation_val)
        
        x_val = x_val.strip(";")
        y_val = y_val.strip(";")
        x_scale_val = x_scale_val.strip(";")
        y_scale_val = y_scale_val.strip(";")
        rotation_val = rotation_val.strip(";")
        opacity_val = opacity_val.strip(";")
       

       
        self.x.write_value(x_val)
        self.y.write_value(y_val)
        self.x_scale.write_value(x_scale_val)
        self.y_scale.write_value(y_scale_val)
        self.rotation.write_value(rotation_val)
        self.opacity.write_value(opacity_val)

        print("kf write done")
"""
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
    GEOM_IN_AFFINE_FILTER: lambda params : AffineFilterGeomProperty(params),
    GEOM_IN_AFFINE_FILTER_V2: lambda params :AffineFilterGeomPropertyV2(params),
    WIPE_RESOURCE : lambda params : WipeResourceProperty(params),
    FILTER_WIPE_RESOURCE : lambda params : FilterWipeResourceProperty(params),
    FILE_RESOURCE : lambda params :FileResourceProperty(params),
    ROTO_JSON  : lambda params :RotoJSONProperty(params),
    LUT_TABLE : lambda params  : LUTTableProperty(params),
    NOT_PARSED : lambda params : EditableProperty(params), # This should only be used with params that have editor=NO_EDITOR
    NOT_PARSED_TRANSITION : lambda params : TransitionEditableProperty(params), # This should only be used with params that have editor=NO_EDITOR
    AFFINE_SCALE : lambda params : AffineScaleProperty(params) }

