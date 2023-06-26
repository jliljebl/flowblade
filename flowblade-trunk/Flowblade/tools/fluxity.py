"""
    ### GPL Licence text

    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2021 Janne Liljeblad.

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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
    
    
    # FLUXITY SCRIPTING
    
    Fluxity scripting is a **Python scripting solution** created to provide **Flowblade Movie Editor** with a *Plugin API*.
    
    Currently *Fluxity API*  is used by Flowblade *Generators* feature.
    
    
    *Fluxity API*  is made available to scripts mainly by *fluxity.FluxityContext* object and its methods. This object is created to communicate with the script before calling any of the methods of the script.
    
    Some constants mentioned in this source file - such as `EDITOR_FLOAT` or `PROFILE_WIDTH` - can also be used by scripts. 
    
    See this below for *fluxity.FluxityContext* object API details.

    ## SCRIPT INTERFACE
    
    A Python script needs to have the following functions to load and run without crashing as a Fluxity API conforming script.
    
    ```
    def init_script(fctx):
        pass
    
    def init_render(fctx):
        pass
    
    def render_frame(frame, fctx, w, h):
        pass
    ```

    ## SCRIPT LIFECYCLE
    
    **`init_script(fctx):`** This method is called when script is first loaded by Flowblade to create data structures with info on editors and script metadata. 
    
    **`init_render(fctx):`** This method is called before a render is started to get user input from editors, and possibly to create some additional data structures.
    
    **`render_frame(frame, fctx, w, h):`** This method is called for each rendered frame to create an output image.
    
    
    ## EXAMPLE SCRIPT
    
    ### init_script()
    
    ```
    import cairo
    import numpy as np
    import random
    import math

    import fluxity

    def init_script(fctx):
        fctx.set_name("Floating Balls")
        fctx.set_version(1)
        fctx.set_author("Janne Liljeblad")

        fctx.add_editor("Hue", fluxity.EDITOR_COLOR, (0.8, 0.50, 0.3, 1.0))
        fctx.add_editor("Speed", fluxity.EDITOR_FLOAT_RANGE, (1.0, -5.0, 5.0))
        fctx.add_editor("Speed Variation %", fluxity.EDITOR_INT_RANGE, (40, 0, 99))
        fctx.add_editor("Number of Items", fluxity.EDITOR_INT_RANGE, (50, 10, 500))
        fctx.add_editor("Size", fluxity.EDITOR_INT_RANGE, (330, 10, 800))
        fctx.add_editor("Size Variation %", fluxity.EDITOR_INT_RANGE, (0, 0, 80))
        fctx.add_editor("Opacity", fluxity.EDITOR_INT_RANGE, (100, 5, 100))
        fctx.add_editor("Random Seed", fluxity.EDITOR_INT, 42)
    ```
    In *init_script()* we define the editors that will be presented to the user and set some metadata like the name of the script displayed to the user and the script author.

    ### init_render()
    ```
    def init_render(fctx):
        # The script is possibly rendered using multiple prosesses and we need to have the
        # same sequence of random numbers in all processes. If we don't set seed we'll get completely different
        # ball positions, colors and speeds in different rendering processes.
        random.seed(fctx.get_editor_value("Random Seed"))

        # Ball colors data structure
        hue = fctx.get_editor_value("Hue")
        hr, hg, hb, alpha = hue
        fctx.set_data_obj("hue_tuple", hue)
        color_array = list(hue)
        ball_colors = []
        color_mult = 1.05
        opacity = float(fctx.get_editor_value("Opacity")) / 100.0

        for i in range(0, 10):
            array = np.array(color_array) * color_mult
            r, g, b, a = array
            ball_colors.append(cairo.SolidPattern(_clamp(r), _clamp(g), _clamp(b), opacity))
            color_array = array
        fctx.set_data_obj("ball_colors", ball_colors)

        # Ball animations data structure
        ball_data = []
        number_of_balls = fctx.get_editor_value("Number of Items")
        speed = fctx.get_editor_value("Speed")
        speed_var_size_precentage = fctx.get_editor_value("Speed Variation %")
        speed_var_max = speed * (speed_var_size_precentage  / 100.0)
        size = fctx.get_editor_value("Size")
        size_var_size_precentage = fctx.get_editor_value("Size Variation %")
        size_var_max = size * (size_var_size_precentage / 100.0)
        size_max = size + size_var_max
        fctx.set_data_obj("size_max", size_max)

        for i in range(0, number_of_balls):
            path_pos = random.uniform(0.0, 1.0)
            y = random.randint(-330, 1080 + 330)
            speed_var = random.uniform(-1.0, 1.0)

            ball_speed = speed + (speed_var * speed_var_max)
            size_var = random.uniform(-1.0, 1.0)
            ball_size = size + (size_var * size_var_max)
            color_index = random.randint(0, 9)
            ball_data.append((path_pos, y, ball_speed, ball_size, color_index))

        fctx.set_data_obj("ball_data", ball_data)
    ```
    In *init_render()* we read editor values set by the user and create data structures for moving ball animations.

    Also note that **we need to set seed for Pythom module 'random'** because when a frame sequence is rendered using multiple processes we need the exact same sequence of random numbers produced in every process. 
    
    ### render_frame()
    ```
    def render_frame(frame, fctx, w, h):
        cr = fctx.get_frame_cr()

        # Draw bg
        bg_color = cairo.SolidPattern(*fctx.get_data_obj("hue_tuple"))
        ball_colors = fctx.get_data_obj("ball_colors")
        ball_data = fctx.get_data_obj("ball_data")

        cr.set_source(bg_color)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # Draw balls
        number_of_balls = fctx.get_editor_value("Number of Items")
        size_max = fctx.get_data_obj("size_max")
        path_start_x = - size_max
        path_end_x =  w + size_max
        path_len = path_end_x - path_start_x
        SPEED_NORM_PER_FRAME = 15.0 / float(w) # Speed value 1.0 gets 15 pixels of movement per frame.
        for i in range(0, number_of_balls):
            path_pos, y, ball_speed, ball_size, color_index = ball_data[i]
            xc = ball_size / 2.0
            yc = ball_size / 2.0
            xpos_norm = path_pos + (float(frame) * ball_speed * SPEED_NORM_PER_FRAME)
            while xpos_norm > 1.0:
                xpos_norm = xpos_norm - 1.0
            x = path_start_x + path_len * xpos_norm
            cr.save()
            cr.translate(x, y)
            cr.arc(xc, yc, ball_size / 4.0, 0.0, 2.0 * math.pi)
            cr.set_source(ball_colors[color_index])
            cr.fill()
            cr.restore()

    # ----------------------- helper func
    def _clamp(v):
        return max(min(v, 1.0), 0.0)

    ```
    In *render_frame()* we first acquire *Cairo.Context* object that can be drawn onto to create output for the frame.
    
    After that the data structures created in *init_render()* are accessed and image is drawn.
    
    There is a helper function *_clamp(v)* used to make sure that all color values are in range 0-1. Any number of helper functions, objects and data structures can be created.


    ## DEVELOPING FLUXITY SCRIPTS
    
    **Flowblade** comes with a simple GUI tool for developing Fluxity scripts. It can be accessed from menu **Tools->Generator Script Editor**.
    
    Using the development tool you can edit scripts, render output from them, and receive error messages whenthings go wrong. From hamburger menu you can open and save your own scripts, access this document, and open and inspect example code from *Generators* distributed with Flowblade. 
    
    Since the text editor in the development tool is quite rudimentary, it can be a useful workflow to use an external text editor to edit the scripts, and press *Reload Script* button to update text area contents before attempting render.
    
    # FLUXITY API
"""
__pdoc__ = {}
__pdoc__['FluxityError'] = False
__pdoc__['FluxityContextPrivate'] = False
__pdoc__['FluxityScript'] = False
__pdoc__['FluxityProfile'] = False
__pdoc__['FluxityEmptyClass'] = False
__pdoc__['render_frame_sequence'] = False
__pdoc__['render_preview_frame'] = False

import gi
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango
from gi.repository import PangoCairo

import array
import cairo
import json
import math
import multiprocessing
import os
from PIL import Image, ImageFilter
import sys
import traceback


# Default length in frames for script duration.
DEFAULT_LENGTH = 200

METHOD_INIT_SCRIPT = 0
METHOD_INIT_RENDER = 1
METHOD_RENDER_FRAME = 2

# Pango font constants.
FACE_REGULAR = "Regular"
FACE_BOLD = "Bold"
FACE_ITALIC = "Italic"
FACE_BOLD_ITALIC = "Bold Italic"
DEFAULT_FONT_SIZE = 40

FLUXITY_ERROR_MSG = "ERROR"
FLUXITY_LOG_MSG = "LOG"

VERTICAL = 0
HORIZONTAL = 1

# The script displayed by Flowblade Script tool on open.
DEFAULT_SCRIPT = \
"""
import cairo
import math

import fluxity


SIDE_LENGTH = 200
SPEED_CONSTANT = 30.0 / 360.0


def init_script(fctx):
    fctx.set_name("Editor Default Plugin")
    
    fctx.add_editor("BG Color", fluxity.EDITOR_COLOR, (0.8, 0.2, 0.2, 1.0))
    fctx.add_editor("FG Color", fluxity.EDITOR_COLOR, (1.0, 1.0, 1.0, 1.0))
    fctx.add_editor("Rotation Speed", fluxity.EDITOR_FLOAT_RANGE, (3.0, 0.0, 10.0))

def init_render(fctx):
    hue_bg = fctx.get_editor_value("BG Color")
    hue_fg = fctx.get_editor_value("FG Color")
    
    fctx.set_data_obj("bg_color", cairo.SolidPattern(*hue_bg))
    fctx.set_data_obj("fg_color", cairo.SolidPattern(*hue_fg))
     
def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()
 
    bg_color = fctx.get_data_obj("bg_color")
    cr.set_source(bg_color)
    cr.rectangle(0, 0, w, h)
    cr.fill()
    
    affine = fluxity.AffineTransform()

    affine.x.add_keyframe_at_frame(0, w / 2, fluxity.KEYFRAME_LINEAR)
    affine.y.add_keyframe_at_frame(0, h / 2, fluxity.KEYFRAME_LINEAR)

    side_half = SIDE_LENGTH / 2
    affine.anchor_x.add_keyframe_at_frame(0, side_half, fluxity.KEYFRAME_LINEAR)
    affine.anchor_y.add_keyframe_at_frame(0, side_half, fluxity.KEYFRAME_LINEAR)

    rotation_speed = fctx.get_editor_value("Rotation Speed", frame) # Value is constant, so frame is optional here
    rotation = frame * 2 * math.pi * rotation_speed * SPEED_CONSTANT
    affine.rotation.add_keyframe_at_frame(0, rotation, fluxity.KEYFRAME_LINEAR)
    
    affine.apply_transform(cr, frame)
 
    fg_color = fctx.get_data_obj("fg_color")
    cr.set_source(fg_color)
    cr.rectangle(0, 0, SIDE_LENGTH, SIDE_LENGTH)
    cr.fill()
"""

EDITOR_TEXT = 1
""" Editor for strings."""
EDITOR_FLOAT = 2
""" Editor for float values."""
EDITOR_INT = 3
""" Editor for integer values."""
EDITOR_COLOR = 4
""" Editor for colors. Value is a *(R,G,B,A)* tuple with values in range 0-1."""
EDITOR_FILE_PATH = 5
""" Editor for selecting a file path. Value is Python pathname or *None*."""
EDITOR_OPTIONS = 6
""" Editor for selecting between  2 - N  string options. Value is tuple *(selected_index,[option_str_1, option_str_2, ...])*."""
EDITOR_CHECK_BOX = 7
""" Editor for boolean value. Value is either *True* or *False*"""
EDITOR_FLOAT_RANGE = 8
""" Editor for float values with a defined range of accepted values. Value is a 3-tuple *(default_val, min_val, max_val)*."""
EDITOR_INT_RANGE = 9
""" Editor for integer values with a defined range of accepted values. Value is a 3-tuple *(default_val, min_val, max_val)*"""
EDITOR_PANGO_FONT = 10
""" Editor for setting pango font properties."""
EDITOR_TEXT_AREA = 11
""" Editor for creating multiline text."""

EDITOR_PANGO_FONT_DEFAULT_VALUES = ("Liberation Serif", "Regular", 80, Pango.Alignment.LEFT, (1.0, 1.0, 1.0, 1.0), \
              True, (0.3, 0.3, 0.3, 1.0) , False, 2, False, (0.0, 0.0, 0.0), \
              100, 3, 3, 0.0, None, VERTICAL)
""" Pango Font Editor default values."""
    
PROFILE_DESCRIPTION = "description"
"""MLT Profile descriptiption string."""
PROFILE_FRAME_RATE_NUM = "frame_rate_num"
"""Frame rate numerator."""
PROFILE_FRAME_RATE_DEN = "frame_rate_den"
"""Frame rate denominator."""
PROFILE_WIDTH = "width"
"""Output image width in pixels."""
PROFILE_HEIGHT = "height"
"""Output image height in pixels."""
PROFILE_PROGRESSIVE = "progressive"
"""
MLT Profile image is progressive if value is *True*, if value is *False* image is interlaced.
"""
PROFILE_SAMPLE_ASPECT_NUM = "sample_aspect_num"
"""
Pixel size fraction numerator.
"""
PROFILE_SAMPLE_ASPECT_DEN = "sample_aspect_den"
"""
Pixel size fraction denominator.
"""
PROFILE_DISPLAY_ASPECT_NUM = "display_aspect_num"
"""Output image size fraction numerator."""
PROFILE_DISPLAY_ASPECT_DEN = "display_aspect_den"
"""Output image size fraction denominator."""
PROFILE_COLORSPACE = "colorspace"
"""Profile colorspace, value is either 709, 601 or 2020."""

KEYFRAME_LINEAR = 0
"""Value after keyframe of this type is linearly interpolated using two surrounding keyframe values."""
KEYFRAME_SMOOTH = 1
"""Value after keyframe of this type is calculated using a Catmull-Rom curve created from four surrounding keyframe values."""
KEYFRAME_DISCRETE = 2
"""Value after keyframe of this type is value at keyframe."""

# ---------------------------------------------------------- script object
class FluxityScript:
    """
    Compiles script to an executable object and calls methods *init_script()*, *init_render()*, *render_frame()* on it.
    
    Internal class, do not use objects of this class directly in scripts.
    """
    
    def __init__(self, script_str):
        self.script = script_str
        self.code = None
        self.namespace = {}
    
    def compile_script(self):
        """
        Compiles user script.
        """
        try:
            self.code = compile(self.script, "<fluxityscript>", "exec")
        except Exception as e:
            _raise_compile_error(str(e))
        
        code_names = sorted(self.code.co_names)
        required_names = sorted(["init_script","init_render","render_frame"])
        contains_all = all(elem in code_names for elem in required_names)
        if contains_all == False:
            _raise_fluxity_error("Functions names " + str(required_names) + " all required to be in script, you have: " + str(code_names))
  
        try:
            exec(self.code, self.namespace)
        except Exception as e:
            _raise_exec_error(str(e))
    
    def call_init_script(self, fctx):
        """
        Calls method *init_script()* on script.
        """
        try:
            self.namespace['init_script'](fctx)
        except Exception as e:
            _raise_fluxity_error("error calling function 'init_script()':" + str(e))

    def call_init_render(self, fctx):
        """
        Calls method *init_render()* on script.
        """
        try:
            self.namespace['init_render'](fctx)
        except Exception as e:
            _raise_fluxity_error("error calling function 'init_render()':\n\n" + str(e))
          
    def call_render_frame(self, frame, fctx, w, h):
        """
        Calls method *render_frame()* on script.
        """
        try:
            self.namespace['render_frame'](frame, fctx, w, h)
        except Exception as e:
            _raise_fluxity_error("error calling function 'render_frame()':\n\n" + str(e))


# ----------------------------------------------------------  Data structure corresponding with mlt.Profile
class FluxityProfile:
    """    
    Properties of this class correspond MLT profile objects.
    
    Internal class, do not use objects of this class directly in scripts. 
    """
        
    def __init__(self, profile_data):
        self.profile_data = profile_data
    
    def get_profile_property(self, prop):
        return self.profile_data[prop]

def _read_profile_prop_from_lines(lines, prop):
    for line in lines:
        sides = line.split("=")
        if sides[0] == prop:
            return sides[1]

    return None
        

# ---------------------------------------------------------- context object
class FluxityContext:

    def __init__(self, script_file, output_folder):
        self.priv_context = FluxityContextPrivate(output_folder)
        self.script_file = script_file
        self.data = {}
        self.editors = {} # editors and script length
        self.editor_tooltips = {}
        self.length = DEFAULT_LENGTH
        self.name = "Name Not Set"
        self.version = 1
        self.author = "Author Not Set"
        self.error = None
        self.log_msg = ""

    def get_frame_cr(self):
        """
        For every rendered frame method *`render_frame()`* is called and a new **`cairo.ImageSurface`** object is created.
        
        This method provides access to **`cairo.Context`** object that can be used to draw onto that image surface. This is the way that output is achieved with **Flowblade Media Plugins**. 
        
        After method *`render_frame()`* exits, **`cairo.Context`** object is no longer valid and contents of **`cairo.ImageSurface`** are saved to disk.
        
        Must be called in script method *`render_frame()`*.
        
        **Returns:** (**`cairo.Context`**) Context object that can be drawn onto.
        """
        return self.priv_context.frame_cr

    def get_dimensions(self):
        """
        Pixel size of output image.
        
        **Returns:** (int, int) Tuple (width, height) of output image size.
        """
        w = self.priv_context.profile.get_profile_property(PROFILE_WIDTH)
        h = self.priv_context.profile.get_profile_property(PROFILE_HEIGHT)
        return (w, h)

    def get_profile_property(self, p_property):
        """
        **`p_property(str):`** propertyr identyfier, e.g. `fluxity.PROFILE_PROGRESSIVE`.
        
        Used to access properties of MLT profile set before running the script that defines e.g. output image size.
        
        **Returns:** (int || boolean || string) Value depends on which profile property is being accessed.
        """
        return self.priv_context.profile.get_profile_property(p_property)
 
    def set_name(self, name):
        """
        **`name(str):`** name of script displayed to user.
        
        Sets name of the script displayed to the user. Must be called in script method *`init_script()`*.
        """
        self.priv_context.error_on_wrong_method("set_name()", METHOD_INIT_SCRIPT)
        self.name = name


    def set_version(self, version):
        """
        **`version(int):`** version of script, use increasing integer numbering. Default value is *1*.
        
        Sets version of script. Must be called in script method *`init_script()`*.
        """
        self.priv_context.error_on_wrong_method("set_version()", METHOD_INIT_SCRIPT)
        self.version = version

    def set_author(self, author):
        """
        **`author(str):`** name of script creator.
        
        Sets author of the script. Must be called in script method *init_script()*.
        """
        self.author = author

    def set_frame_name(self, frame_name):
        """        
        **`frame_name(str):`** name used before number part in rendered frame files.
        """
        self.priv_context.frame_name = frame_name

    def set_data_obj(self, label, item):
        """
        **`label(str):`** label used to access data later using *`get_data_obj(self, label)`*.

        **`item(obj):`** data item being saved.
        
        Saves data to be used later during execution of script. Using **global** would obviously be possible to replace this, but this is made available as a more clean solution.
        """
        self.data[label] = item

    def get_data_obj(self, label):
        """
        **`label(str):`** label of saved data item.
        
        Gives access to previously saved data.
        
        **Returns:** (obj) Saved data item.
        """
        return self.data[label]

    def set_length(self, length):
        """
        **`length(int):`** New length of script in frames.
        
        Sets length of script output in frames.
        
        Must *not* be called in  *`render_frames()`*.
        """
        self.length = length

    def get_length(self):
        """
        **Returns:** (int) Length of script in frames.
        """
        return self.length

    def add_editor(self, name, type, default_value, tooltip=None):
        """     
        **`name(str):`** Name for editor.
        
        **`type(int):`** Value either *`EDITOR_FLOAT`, `EDITOR_INT`, `EDITOR_COLOR`, `EDITOR_FILE_PATH`, `EDITOR_OPTIONS`, `EDITOR_CHECK_BOX`, `EDITOR_FLOAT_RANGE`, `EDITOR_INT_RANGE`.*
        
        **`default_value(str||int||float||tuple):`** Data type depends on editor type:
        
          * `EDITOR_TEXT`(str),

          * `EDITOR_TEXT_AREA`(str),

          * `EDITOR_FLOAT`(float),
          
          * `EDITOR_INT`(int), 
          
          * `EDITOR_COLOR`(4-tuple with float values in range 0-1, (R,G,B,A)), 
          
          * `EDITOR_FILE_PATH`(str), 
          
          * `EDITOR_OPTIONS`(2-tuple (int, [str]), (selected_index,[option_str_1, option_str_2, ...]),
          
          * `EDITOR_CHECK_BOX`(bool), 
          
          * `EDITOR_FLOAT_RANGE`(3-tuple with float values, (default, min, max)), 
          
          * `EDITOR_INT_RANGE`(3-tuple with int values, (default, min, max))
          
          * `EDITOR_PANGO_FONT` (17-tuple (font_family, font_face, font_size, alignment, color_rgba,
                  fill_on, outline_color_rgba, outline_on, outline_width, shadow_on, shadow_color_rgb, 
                  shadow_opacity, shadow_xoff, shadow_yoff, shadow_blur, 
                  gradient_color_rgba, gradient_direction))
          
        **`tooltip(str, optional):`** Tooltip for editor if presented in GUI.
        
        Defines possible GUI editors used to affect script rendering. Edited value is accessed with method *get_editor_value(self, name, frame=0)*.
        
        Data describing editors can be accessed with *get_script_data(self)*. Edited values are made available for script with *set_editors_data(self, editors_data_json)*.
        
        Must be called in script method *init_script()*.
        """
        self.priv_context.error_on_wrong_method("add_editor()", METHOD_INIT_SCRIPT)
        self.editors[name] = (type, default_value)
        if tooltip != None:
            self.editor_tooltips[name] = tooltip

    def get_editor_value(self, name, frame=0):
        """     
        **`name(str):`** Name of editor.
        
        **`frame(int):`** Frame in range 0 - (script length - 1).
        
        Value of edited data at given frame. We currently have no animated values, but they will added with future API updates.
        
        **Returns:** (obj) Value at frame.
        
        Data type depends on editor type:
        
          * `EDITOR_TEXT`(str),

          * `EDITOR_TEXT_AREA`(str),
          
          * `EDITOR_FLOAT`(float), 
          
          * `EDITOR_INT`(int), 
          
          * `EDITOR_COLOR`(4-tuple with float values in range 0-1, (R,G,B,A)), 
          
          * `EDITOR_FILE_PATH`(str),
          
          * `EDITOR_OPTIONS`(selection index int),
          
          * `EDITOR_CHECK_BOX`(bool), 
          
          * `EDITOR_FLOAT_RANGE`(3-tuple with float values, (default, min, max)), 
          
          * `EDITOR_INT_RANGE`(3-tuple with int values, (default, min, max))

          * `EDITOR_PANGO_FONT`(17-tuple (font_family, font_face, font_size, alignment, color_rgba,
                  fill_on, outline_color_rgba, outline_on, outline_width, shadow_on, shadow_color_rgb, 
                  shadow_opacity, shadow_xoff, shadow_yoff, shadow_blur,
                  gradient_color_rgba, gradient_direction))
        """
        try:
            type, value = self.editors[name]
            if type == EDITOR_INT_RANGE or type == EDITOR_FLOAT_RANGE:
                val, min, max = value
                return val 
            elif type == EDITOR_OPTIONS:
                selected_index, options = value
                return selected_index
            return value
        except Exception as e:
            exception_msg = "No editor for name '" + name + "' found."
            _raise_fluxity_error(exception_msg)

    def get_script_data(self):
        """             
        Returns data of all editors and their default values, and script metadata like script author and version. 
        
        Output can be turned into Python object tree using *json.loads()* method.
        
        **Returns:** (str) string representation of JSON object.
        """
        script_data = {}
        script_data["length"] = self.length
        script_data["name"] = self.name
        script_data["version"] = self.version
        script_data["author"] = self.author

        editors_list = []
        for name in self.editors:
            type, value = self.editors[name]
            json_obj = [name, type, value]
            editors_list.append(json_obj)

        script_data["editors_list"] = editors_list # this is dict inside FluxityContext object, but is given out as list for convenience of Flowblade app integration.
        script_data["tooltips_list"] = self.editor_tooltips
        
        return json.dumps(script_data)

    def get_script_dir(self):
        """             
        Returns path to directory where the script being executed is located.  
        
        Sometimes script directory information is not available (e.g. when executing a non-saved script in Flowblade *Script Tool* application) and *None* is returned. It is recommended that all Fluxity scripts handle getting *None* gracefully.
        
        This functionality is useful when script is being distributed with some associated media files.
        
        **Returns:** (str) script directory path or *None*.
        """
        if self.script_file == None:
            return None
            
        dir_path = os.path.dirname(self.script_file) + "/"
        return dir_path
        
    def set_editors_data(self, editors_data_json):
        """
        **`editors_data_json(str):`** string representation of JSON object.
                 
        Sets edited data to be used when rendering.
        
        Input string must describe JSON object that can be turned into usable editor data.
        
        Example with `EDITOR_FLOAT` and `EDITOR_COLOR`:
        
        ```
        [
            ["Position X", 2, 1.0], 
            ["BG Color", 4, [0.8, 0.2, 0.2, 1.0]]
        ]
        ```
        
        General form:
        
        ```
        [
            [<name>, <type>, <value>], 
            ...
        ]
        ```
        
        Using this method is not needed when writing **Flowblade Media Plugins**, application handles setting editors data.
        
        Should be called in script method *init_render()*.
        """
        new_editors_list = json.loads(editors_data_json)
        for editor in new_editors_list:
            name, type, value = editor
            self.editors[name] = (type, value)

    def create_text_layout(self, font_data):
        """
        **`font_data(tuple)`** this tuple can be acquired by calling *FluxityContext.get_editor_value()* on editors of type *EDITOR_PANGO_FONT*.
                
        Creates objects used to draw text.

        **Returns:** (fluxity.PangoTextLayout) object for drawing text.
        """
        return PangoTextLayout(font_data)
    
    def log_line(self, log_line):
        """
        **`log_line(str):`** line of text.
                 
        Adds a line of text to log message displayed after render completion or error.
        """
        self.log_msg = self.log_msg + log_line + "\n"

    def set_prints_to_log_file(self, log_file):
        """
        **`log_file(str):`** File path.
                 
        Save output from 'print()' to file at given path. Must be called in script method *init_script()*.
        """
        self.priv_context.error_on_wrong_method("add_editor()", METHOD_INIT_SCRIPT)
        _prints_to_log_file(log_file)
    
class FluxityContextPrivate:
    # This class exists to keep FluxityContext API clean for script developers.
    #
    # Internal class, do not use objects of this class directly in scripts. 
    def __init__(self, output_folder):

        self.profile = None
        
        self.output_folder = output_folder
        self.start_out_from_frame_one = False
        self.in_frame = -1

        self.frame = -1
        
        self.frame_surface = None
        self.frame_cr = None

        self.frame_name = "frame"
        self.first_rendered_frame_path = None # This is cleared by rendering routines.

        self.current_method = None
        self.method_name = {METHOD_INIT_SCRIPT:"init_script()", METHOD_INIT_RENDER:"init_render()", METHOD_RENDER_FRAME:"render_frame()"}
        
        self.repo = None

        self.process_id = None # Used for de-bugging, scripts normally would not access this.

    def load_profile(self, mlt_profile_path):
        lines = []
        with open(mlt_profile_path, "r") as f:
            for line in f:
                lines.append(line.strip())
        data = {}
        data[PROFILE_DESCRIPTION] = _read_profile_prop_from_lines(lines, PROFILE_DESCRIPTION)
        data[PROFILE_FRAME_RATE_NUM] = _read_profile_prop_from_lines(lines, PROFILE_FRAME_RATE_NUM)
        data[PROFILE_FRAME_RATE_DEN] = _read_profile_prop_from_lines(lines, PROFILE_FRAME_RATE_DEN)
        data[PROFILE_WIDTH] = int(_read_profile_prop_from_lines(lines, PROFILE_WIDTH))
        data[PROFILE_HEIGHT] = int(_read_profile_prop_from_lines(lines, PROFILE_HEIGHT))
        data[PROFILE_PROGRESSIVE] = _read_profile_prop_from_lines(lines, PROFILE_PROGRESSIVE)
        data[PROFILE_SAMPLE_ASPECT_NUM] = _read_profile_prop_from_lines(lines, PROFILE_SAMPLE_ASPECT_NUM)
        data[PROFILE_SAMPLE_ASPECT_DEN] = _read_profile_prop_from_lines(lines, PROFILE_SAMPLE_ASPECT_DEN)
        data[PROFILE_DISPLAY_ASPECT_NUM] = _read_profile_prop_from_lines(lines, PROFILE_DISPLAY_ASPECT_NUM)
        data[PROFILE_DISPLAY_ASPECT_DEN] = _read_profile_prop_from_lines(lines, PROFILE_DISPLAY_ASPECT_DEN)
        data[PROFILE_COLORSPACE] = _read_profile_prop_from_lines(lines, PROFILE_COLORSPACE)

        self.profile = FluxityProfile(data)

        return self.profile.profile_data
        
    def create_frame_surface(self, frame):
        self.frame = frame
        w = self.profile.profile_data[PROFILE_WIDTH]
        h = self.profile.profile_data[PROFILE_HEIGHT]
        self.frame_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        self.frame_cr = cairo.Context(self.frame_surface)
        self.frame_cr.set_antialias(cairo.Antialias.GOOD)

    def write_out_frame(self, is_preview_frame=False):
        if self.output_folder == None or os.path.isdir(self.output_folder) == False:
            exception_msg = "Output folder " + self.output_folder + " does not exist."
            _raise_fluxity_error(exception_msg)
        
        out_frame_number = self.frame
        if self.start_out_from_frame_one == True:
            out_frame_number = self.frame - self.in_frame + 1 

        filepath = self.output_folder + "/" + self.frame_name + "_" + str(out_frame_number).rjust(5, "0") + ".png"
        if is_preview_frame == True:
            filepath = self.output_folder + "/preview.png"
        self.frame_surface.write_to_png(filepath)

        if self.first_rendered_frame_path == None:
            self.first_rendered_frame_path = filepath

    def get_preview_frame_path(self):
        return self.output_folder + "/preview.png"
    
    def error_on_wrong_method(self, method_name, required_method):
        if required_method == self.current_method:
            return
        
        error_str = "'FluxityContext." + method_name + "' has to called in script method '" + self.method_name[required_method] + "'."
        _raise_contained_error(error_str)
    
class FluxityEmptyClass:
    """
    Internal class, do not use objects of this class directly in scripts.
    """
    pass

class PangoTextLayout:

    """
    **`font_data(tuple)`** this tuple can be acquired by calling *`FluxityContext.get_editor_value()`* on editors of type *`EDITOR_PANGO_FONT`*.
            
    Object for drawing text. Uses internally Pango.
    
    Instances of this object can be created using *`FluxityContext.create_text_layout()`*.
    """
    def __init__(self, font_data):
        self.font_family, self.font_face, self.font_size, self.alignment, \
        self.color_rgba, self.fill_on, self.outline_color_rgba, self.outline_on, \
        self.outline_width, self.shadow_on, self.shadow_color_rgb, self.shadow_opacity, \
        self.shadow_xoff, self.shadow_yoff, self.shadow_blur, self.gradient_color_rgba, \
        self.gradient_direction = font_data
        self.font_desc = None
        self.pango_layout = None
        self.opacity = 1.0 
        self.pixel_size = None
        
    def create_pango_layout(self, cr, text):
        """
        **`cr(cairo.Context)`** frame cairo context acquired with *`FluxityContext.get_frame_cr()`*.
        
        **`text(str)`** displayed text.
        
        Creates internally *`PangoCairo`* layout object. Calling this is required before calling *`PangoTextLayout.get_pixel_size()`*.
        """
        self.text = text
        
        fontmap = PangoCairo.font_map_new()
        context = fontmap.create_context()
        font_options = cairo.FontOptions()
        font_options.set_antialias(cairo.Antialias.GOOD)
        PangoCairo.context_set_font_options(context, font_options)
        context.changed()
        
        self.pango_layout = Pango.Layout.new(context)
        
        self.pango_layout.set_text(self.text, -1)
        font_desc = Pango.FontDescription(self.font_family + " " + self.font_face + " " + str(self.font_size))
        self.pango_layout.set_font_description(font_desc)
        self.pango_layout.set_alignment(self.alignment)
        if self.pixel_size == None:
            metrics = self.pango_layout.get_context().get_metrics(font_desc, None)
            self.ascent = metrics.get_ascent() / Pango.SCALE
            self.descent = metrics.get_descent() / Pango.SCALE
            self.height = metrics.get_height() / Pango.SCALE
            w, h = self.pango_layout.get_size()
            self.pixel_size = (w / Pango.SCALE, self.height)

    def get_top_pad(self):
        """             
        Returns pixel distance from layout top to highest possible pixel drawn for any font. 
        
        **Returns:** (int)(pad) Top pad size in pixels.
        """
        return self.height - self.descent - self.ascent
        
        
    def get_pixel_size(self):
        """             
        Returns size of layout.

        Before calling this PangoCairo layout object needs to created *`PangoTextLayout.create_pango_layout()`* or *`PangoTextLayout.draw_layout()`.*
        
        **Returns:** (int, int)(width, height) pixel size of layout.
        """
        return self.pixel_size 
        
    def set_opacity(self, opacity):
        """
        **`opacity(float)`** Opacity in range 0.0 - 1.0.
        
        Sets opacity for the text to be drawn. Default value is 1.0
        """
        if opacity < 0.0:
            opacity = 0.0
        if opacity > 1.0:
            opacity = 1.0
            
        self.opacity = opacity

    # called from vieweditor draw vieweditor-> editorlayer->here
    def draw_layout(self, fctx, text, cr, x, y, rotation=0.0, xscale=1.0, yscale=1.0):
        """
        ** fctx(fluxity.FluxityContext ** context object.
        
        **`text(str)`** displayed text.
        
        **`cr(cairo.Context)`** frame cairo context acquired with *`FluxityContext.get_frame_cr()`*.
        
        **`x(float)`** Text X position.

        **`y(float)`** Text Y position.

        **`rotation(float)`** Text rotation.

        **`xscale(float)`** Text X scaling.

        **`yscale(float)`** Text Y scaling.

        Draws text on provided *`cairo.Context`*.
        
        Calls internally *`PangoTextLayout.create_pango_layout()`* so *`PangoTextLayout.get_pixel_size()`* can be called after this.
        """
        self.text = text
        cr.save() # Created each frame
        
        self.create_pango_layout(cr, text)
        layout = self.pango_layout # this just artifact of dev. history, create_pango_layout() was added later then draw_layout()
                                   # to be used in typewriter plugin.
        # Shadow
        if self.shadow_on:
            cr.save()

            # Get colors.
            r, g, b = self.shadow_color_rgb
            a = (self.shadow_opacity / 100.0) * self.opacity 

            # Blurred shadow need its own ImageSurface
            if self.shadow_blur != 0.0:
                w, h = fctx.get_dimensions()
                blurred_img = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
                cr_blurred = cairo.Context(blurred_img)
                cr_blurred.set_antialias(cairo.Antialias.GOOD)
                transform_cr = cr_blurred # Set draw transform_cr to context for newly created image.
            else:
                transform_cr = cr # Set draw transform_cr to out context.

            # Transform and set color.
            transform_cr.set_source_rgba(r, g, b, a)
            effective_shadow_xoff = self.shadow_xoff * xscale
            effective_shadow_yoff = self.shadow_yoff * yscale
            transform_cr.move_to(x + effective_shadow_xoff, y + effective_shadow_yoff)
            transform_cr.scale(xscale, yscale)
            transform_cr.rotate(rotation)

            # If no blur for shadow, just draw layout on out context.
            if self.shadow_blur == 0.0:
                PangoCairo.update_layout(cr, layout)
                PangoCairo.show_layout(cr, layout)
                cr.restore()
            else:
                # If we have blur - draw shadow, blur it and then draw on out context.
                PangoCairo.update_layout(cr_blurred, layout)
                PangoCairo.show_layout(cr_blurred, layout)

                img2 = Image.frombuffer("RGBA", (blurred_img.get_width(), blurred_img.get_height()), blurred_img.get_data(), "raw", "RGBA", 0, 1)
                effective_blur = xscale * self.shadow_blur # This is not going to be exact
                                                           # on non-100% scales but let's try to get approximation. 
                img2 = img2.filter(ImageFilter.GaussianBlur(radius=int(effective_blur)))
                imgd = img2.tobytes()
                a = array.array('B',imgd)

                stride = blurred_img.get_width() * 4
                draw_surface = cairo.ImageSurface.create_for_data (a, cairo.FORMAT_ARGB32,
                                                              blurred_img.get_width(), blurred_img.get_height(), stride)
                cr.restore()
                cr.set_source_surface(draw_surface, 0, 0)
                cr.paint()

        # Text
        if self.fill_on:
            if self.gradient_color_rgba == None:
                cr.set_source_rgba(*self._get_opacity_rgba(self.color_rgba))
            else:
                w, h = self.pixel_size
                w = float(w) * xscale
                h = float(h) * yscale
                if self.gradient_direction == HORIZONTAL:
                    grad = cairo.LinearGradient (x, 0, x + w, 0)
                else:
                    grad = cairo.LinearGradient (0, y, 0, y + h)
                
                r, g, b, a = self.color_rgba
                rg, gg, bg, ag =  self.gradient_color_rgba 
                    
                CLIP_COLOR_GRAD_1 = (0,  r, g, b, 1.0)
                CLIP_COLOR_GRAD_2 = (1,  rg, gg, bg, 1.0)
                grad.add_color_stop_rgba(*CLIP_COLOR_GRAD_1)
                grad.add_color_stop_rgba(*CLIP_COLOR_GRAD_2)
                cr.set_source(grad)

            cr.move_to(x, y)
            cr.scale(xscale, yscale)
            cr.rotate(rotation)

            PangoCairo.update_layout(cr, layout)
            PangoCairo.show_layout(cr, layout)
        
        # Outline
        if self.outline_on:
            if self.fill_on == False: # case when user only wants outline we need to transform here
                cr.move_to(x, y)
                cr.scale(xscale, yscale)
                cr.rotate(rotation)
            PangoCairo.layout_path(cr, layout)
            cr.set_source_rgba(*self._get_opacity_rgba(self.outline_color_rgba))
            cr.set_line_width(self.outline_width)
            cr.stroke()
        
        cr.restore()

    def get_pango_alignment(self):
        """             
        Returns alignment for his layout.

        To interpret enums script must do import *`from gi.repository import Pango`*
        
        **Returns:** (int) alignment enum, either *`Pango.Alignment.CENTER`*, *`Pango.Alignment.LEFT`* or *`Pango.Alignment.RIGHT`*.
        """
        return self.alignment

    def _get_opacity_rgba(self, rbga):
        r, g, b, a = rbga
        return (r, g, b, a * self.opacity)

class AnimatedValue:

    """
    Object for animating a float value.
    
    Changing value is controlled by adding keyframes.
    
    A keyframe has *frame position, value* and *type*. There are three types of keyframes: `KEYFRAME_LINEAR`, `KEYFRAME_SMOOTH` and `KEYFRAME_DISCRETE`.
    
      * **`KEYFRAME_LINEAR`** Value after keyframe is linearly interpolated using two surrounding keyframe values.
      
      * **`KEYFRAME_SMOOTH`** Value after keyframe is calculated using a Catmull-Rom curve created from four surrounding keyframe values.
      
      * **`KEYFRAME_DISCRETE`** Value after keyframe is value at keyframe.

    Implementation assumes there always being a keyframe at frame 0, and removing that will result in undefined behaviour. It is of course possible to overwrite existing keyframe at frame 0 using method *add_keyframe_at_frame().*
    """
    def __init__(self, value=0.0):
        # We enforce a keyframe always existing in frame 0
        self.keyframes = [(0, value, KEYFRAME_LINEAR)]

    def add_keyframe_at_frame(self, frame, value, kf_type):
        """
        **`frame(int)`** Frame number in range 0 - (plugin length).
        
        **`value(float)`** A float value.
        
        **`kf_type(KEYFRAME_LINEAR|KEYFRAME_SMOOTH|KEYFRAME_DISCRETE)`** Type of added keyframe.
        
        Adds or overwrites a keyframe.
                    
        If frame is on existing keyframe that keyframe is replaced.
        
        If frame is between two keyframes a new keyframe is added between keyframes.

        If frame is after last keyframe a new keyframe is appended.
        """
        
        # Replace if kf in frame exists.
        new_kf = (frame, value, kf_type)
        kf_index_on_frame = self._frame_has_keyframe(frame)
        if kf_index_on_frame != -1:
            self.keyframes.pop(kf_index_on_frame)
            self.keyframes.insert(kf_index_on_frame, new_kf)
            return

        # Insert between if frame between two kfs.
        for i in range(0, len(self.keyframes)):
            kf_frame, kf_value, kf_type = self.keyframes[i]
            if kf_frame > frame:
                prev_frame, prev_value, prev_type = self.keyframes[i - 1]
                self.keyframes.insert(i, new_kf)
                self.active_kf_index = i
                return

        # Append last if after last kf.
        self.keyframes.append(new_kf)

    def _frame_has_keyframe(self, frame):
        for i in range(0, len(self.keyframes)):
            kf_frame, kf_value, type = self.keyframes[i]
            if frame == kf_frame:
                return i

        return -1
        
    def get_value(self, frame):
        """
        **`frame(int)`** Frame number in range 0 - (plugin length).
                
        Computes and returns value at frame using current keyframe values, positions and types.

        **Returns:** (float) value at frame.
        """
        last_frame, last_value, last_type  = self.keyframes[-1]
        if frame >= last_frame: # This also handles case len(self.keyframes) == 1 because first keyframe always at frame 0.
            return last_value

        for i in range(0, len(self.keyframes) - 1):
            kf_frame, kf_value, kf_type = self.keyframes[i]
            if frame == kf_frame:
                return kf_value
            next_frame, next_value, next_type = self.keyframes[i + 1]
            if frame == next_frame:
                return next_value
            if frame > kf_frame and frame < next_frame:
                if kf_type == KEYFRAME_LINEAR:
                    fract = (frame - kf_frame) / (next_frame - kf_frame)
                    return kf_value + fract * (next_value - kf_value)
                elif kf_type == KEYFRAME_SMOOTH:
                    return self._get_smooth_value(i, frame)
                else: # KEYFRAME_DISCRETE
                    return kf_value
                    
        return None # We absolutely want to crash if somehow we hit this.
 
    def _get_smooth_value(self, i, frame):
        # Get indexes of the four keyframes that affect the drawn curve. 
        prev = i
        if i == 0:
            prev_prev = 0
        else:
            prev_prev = i - 1
        
        next = i + 1
        if next >= len(self.keyframes):
            next = len(self.keyframes) - 1
        
        next_next = next + 1
        if next_next >= len(self.keyframes):
            next_next = len(self.keyframes) - 1

        # Get keyframes.
        frame_pp, val0, kf_type = self.keyframes[prev_prev]
        frame_p, val1, kf_type = self.keyframes[prev]
        frame_n, val2, kf_type = self.keyframes[next]
        frame_nn, val3, kf_type = self.keyframes[next_next]

        # Get value
        fract = (frame - frame_p) / (frame_n - frame_p)
        smooth_val = self._catmull_rom_interpolate(val0, val1, val2, val3, fract)
        return smooth_val

    # These all need to be doubles.
    def _catmull_rom_interpolate(self, y0, y1, y2, y3, t):
        t2 = t * t
        a0 = -0.5 * y0 + 1.5 * y1 - 1.5 * y2 + 0.5 * y3
        a1 = y0 - 2.5 * y1 + 2 * y2 - 0.5 * y3
        a2 = -0.5 * y0 + 0.5 * y2
        a3 = y1
        return a0 * t * t2 + a1 * t2 + a2 * t + a3


class AffineTransform:

    """
    Object for describing animated affine transforms and applying them on *`cairo.Context`*.

    On creation object creates following instance *`fluxity.AnimatedValue`* attributes:
     
    **`x`** X position in pixels.
    
    **`y`** Y position in pixels.
    
    **`anchor_x`** Rotation and scaling offset from *`source`* top left corner in x axis pixels.
    
    **`anchor_y`** Rotation and scaling offset from *`source`* top left corner in y axis pixels.
    
    **`scale_x`** Scaling in x-axis as float value.
    
    **`scale_y`** Scaling in y-axis as float value.
    
    **`rotation`** Rotation in degrees.
    
    Default value for all attributes is value 0.0 at keyframe 0, except `scale_x` and `scale_y` which have default value of 1.0 at keyframe 0.
    
    The intended usage pattern:
    
      * create *`fluxity.AffineTransform`* object and set values to needed attributes to create animations.
      
      * for each frame first call method *`fluxity.AffineTransform.apply_transform()`* to apply the affine transform.
      
      * draw *`source`* in `origo(0,0)` position.
    """

    def __init__(self):
        self.x = AnimatedValue()
        self.y = AnimatedValue()
        self.anchor_x = AnimatedValue()
        self.anchor_y = AnimatedValue()
        self.scale_x = AnimatedValue(1.0)
        self.scale_y = AnimatedValue(1.0)
        self.rotation = AnimatedValue()

    def apply_transform(self, cr, frame):
        """
        **`cr(cairo.Context)`** a `cairo.Context` object.
        
        **`frame(int)`** Frame number in range 0 - (plugin length).
                
        Applies affine transform defined by object instance at given frame on `cairo.Context` object.
        """
        scale_x = self.scale_x.get_value(frame)
        scale_y = self.scale_y.get_value(frame)
        rotation_angle = self.rotation.get_value(frame)

        anchor_x = scale_x * self.anchor_x.get_value(frame)
        anchor_y = scale_y * self.anchor_y.get_value(frame) 
        
        axr, ayr = self._rotate_point_around_origo(rotation_angle, (anchor_x, anchor_y))
        
        tx = self.x.get_value(frame) - axr
        ty = self.y.get_value(frame) - ayr
        
        cr.translate(tx, ty)
        cr.rotate(math.radians(rotation_angle))
        cr.scale(scale_x, scale_y)

    def _rotate_point_around_origo(self, rotation_angle, p):
        px, py = p
        angle_rad = math.radians(rotation_angle)
        sin_val = math.sin(angle_rad)
        cos_val = math.cos(angle_rad)
        new_x = px * cos_val - py * sin_val
        new_y = px * sin_val + py * cos_val
        return (new_x, new_y)
    

# ---------------------------------------------------------- Errors 
class FluxityError(Exception):
    """
    Errors specific to using Fluxity API.
    
    Internal class, do not use objects of this class directly in scripts. 
    """
    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)

def _raise_contained_error(exception_msg):
    raise FluxityError(exception_msg)
    
def _raise_fluxity_error(exception_msg):
    raise FluxityError("Fluxity Error: " + exception_msg)
    
def _raise_compile_error(exception_msg):
    raise FluxityError("Error compiling Fluxity script:\n" + exception_msg)

def _raise_exec_error(exception_msg):
    raise FluxityError("Error on doing exec() to create script code object:\n" + exception_msg)

# ------------------------------------------------------ rendering
def render_preview_frame(script, script_file, frame, out_folder, profile_file_path, editors_data_json=None):
    """
    **script(str)** Script to be rendered as a string.
    
    **script_file(str)** Absolute path to file containing script. If this is not provided methods some like *FluxityContext.get_script_dir()* will not function as intended.
    
    **frame(int)** Frame to be rendered in range 0 - *(script_length - 1)*.
    
    **out_folder(str)** Path to folder where rendered frame will be saved.
    
    **profile_file_path(str)** Path to a file containing a file describing MLT profile used to when rendering the script.
    
    **editors_data_json(str)** String representation of JSON object containing editors described in the script and their values. This is optional, not providing this will use default values given in script when rendering.
    
    Renders a single frame from provided script.
    
    **Returns:** (FluxityContext) Object created during rendering. This object has attributes *error* and *log_msg* providing error and logging information.
    """

    try:
        # Init script and context.
        error_msg, results = _init_script_and_context(script, script_file, out_folder, profile_file_path)
        if error_msg != None:
            fake_fctx = FluxityEmptyClass()
            fake_fctx.error = error_msg
            fake_fctx.log_msg = ""
            return fake_fctx

        fscript, fctx = results

        # Execute script to render a preview frame.
        fctx.priv_context.current_method = METHOD_INIT_SCRIPT
        fscript.call_init_script(fctx)

        if editors_data_json != None:
            fctx.set_editors_data(editors_data_json)

        fctx.priv_context.current_method = METHOD_INIT_RENDER
        fscript.call_init_render(fctx)

        fctx.priv_context.current_method = METHOD_RENDER_FRAME
        fctx.priv_context.create_frame_surface(frame)
        w, h = fctx.get_dimensions()
        fscript.call_render_frame(frame, fctx, w, h)

        return fctx
    except Exception as e:
        fctx.error = str(e) + traceback.format_exc(6,True)
        return fctx

def render_frame_sequence(script, script_file, in_frame, out_frame, out_folder, profile_file_path, editors_data_json=None, start_out_from_frame_one=False):
    """
    **script(str)** Script to be rendered as a string.
    
    **script_file(str)** Absolute path to file containing script. If this is not provided methods some like *FluxityContext.get_script_dir()* will not function as intended.
    
    **in_frame(int)** First frame of rendered range.

    **out_frame(int)** Last frame of rendered range, exclusive.
    
    **out_folder(str)** Path to folder where rendered frame will be saved.
    
    **profile_file_path(str)** Path to a file containing a file describing MLT profile used to when rendering the script.
    
    **editors_data_json(str)** String representation of JSON object containing editors described in the script and their values. This is optional, not providing this will use default values given in script when rendering.
    
    **start_out_from_frame_one(boolean)** Setting this *True* will cause numbering of rendered frame sequence to start from *1*, otherwise it will start from *in_frame*. 
    
    Renders a range of frames from provided script.
    
    **Returns:** (dict) Dictionary object created during rendering with the following information:
    
    * for each process it has *key -> value* pair *process number(str) -> path to first frame rendered by process(str)*.
    * if errors occurred during rendering it has *key -> value* pair *fluxity.FLUXITY_ERROR_MSG -> error message(str)*.
    * if script created log messages it has *key -> value* pair *fluxity.FLUXITY_LOG_MSG -> log message(str)*.
    """
    # Some simple heuristics to decide how many processes will be used for rendering
    cpu_count = multiprocessing.cpu_count()
    threads = cpu_count - 2
    # Computer does not have that many cores, let's only use one.
    if threads < 2:
        threads = 1
    # This gets diminshing returns so let's cap it at 8.
    if threads > 8:
        threads = 8
    # If we are rendering a very small amount of frames, there isn't much benefit to use multiple processes.
    if out_frame - in_frame < threads * 2:
        threads = 1

    result_queue = multiprocessing.Queue()
    
    jobs = []
    for i in range(threads):
        
        render_data = ( script, script_file, in_frame, out_frame, out_folder, \
                        profile_file_path, editors_data_json, start_out_from_frame_one)
        
        proc_info = (i, threads, result_queue)
        p = multiprocessing.Process(target=_render_process_launch, args=(render_data, proc_info))
        jobs.append(p)
        p.start()

    proc_fctx_dict = {}
    for proc in jobs:
        results_dict = result_queue.get()
        proc.join()
        proc_fctx_dict.update(results_dict)

    return proc_fctx_dict
        
def _render_process_launch(render_data, proc_info):

    try:
        script, script_file, in_frame, out_frame, out_folder, \
        profile_file_path, editors_data_json, start_out_from_frame_one = render_data
        
        procnum, threads_count, result_queue = proc_info
     
        # Used to communicate to app what happened.
        results_dict = {}
        
        # Init script and context.
        error_msg, results = _init_script_and_context(script, script_file, out_folder, profile_file_path)
        if error_msg != None:
            results_dict[str(FLUXITY_ERROR_MSG) ] = str(error_msg)
            result_queue.put(results_dict)
            return 

        fscript, fctx = results

        # Execute script to write frame sequence.
        fctx.priv_context.current_method = METHOD_INIT_SCRIPT
        fscript.call_init_script(fctx)

        if editors_data_json != None:
            fctx.set_editors_data(editors_data_json)
            
        fctx.priv_context.current_method = METHOD_INIT_RENDER
        fscript.call_init_render(fctx)
        
        fctx.priv_context.first_rendered_frame_path = None # Should be clear but let's make sure. 
        fctx.priv_context.current_method = METHOD_RENDER_FRAME
        fctx.priv_context.start_out_from_frame_one = start_out_from_frame_one
        fctx.priv_context.in_frame = in_frame
        fctx.priv_context.process_id = procnum
        
        for frame in range(in_frame + procnum, out_frame, threads_count):
            fctx.priv_context.create_frame_surface(frame)
            w, h = fctx.get_dimensions()
            fscript.call_render_frame(frame, fctx, w, h)
            fctx.priv_context.write_out_frame()

        results_dict[str(procnum)] = str(fctx.priv_context.first_rendered_frame_path)
        if len(fctx.log_msg) > 0:
            results_dict[str(FLUXITY_LOG_MSG)] = str(fctx.log_msg)
        
        result_queue.put(results_dict)
                    
    except Exception as e:
        fctx.error = str(e) + traceback.format_exc(6,True) 
        results_dict[str(FLUXITY_ERROR_MSG)] = str(fctx.error)
        result_queue.put(results_dict)

def get_script_default_edit_data(script, script_file, out_folder, profile_file_path):
    """
    **script(str)** Script to be rendered as a string.
    
    **script_file(str)** Absolute path to a file containing script. If this is not provided, some methods like *FluxityContext.get_script_dir()* will not function as intended.
    
    **out_folder(str)** Path to the folder where rendered frame will be saved.
    
    **profile_file_path(str)** Path to a file containing a file describing a MLT profile used when rendering the script.

    Creates a *FluxityContext* object, calls *init_script()* on it 
    
    **Returns:** (str, dict) Tuple of error message string and Python dict representation of Json object created with *FluxityContext.get_script_data()*. Error message string will be *None* if no error occurred.
    """
    
    # Init script and context.
    try:
        error_msg, results = _init_script_and_context(script, script_file, out_folder, profile_file_path)
        if error_msg != None:
            return (error_msg, None)

        fscript, fctx = results

        # Execute init script to create data structures.
        fctx.priv_context.current_method = METHOD_INIT_SCRIPT
        fscript.call_init_script(fctx)
        
        data_json = fctx.get_script_data()
        edit_data = json.loads(data_json) # we want this as Python dict
    except Exception as e:
        return (str(e) + traceback.format_exc(6,True), None)
                    
    return (None, edit_data)
            
def _init_script_and_context(script, script_file, out_folder, profile_file_path):
    try:

        fscript = FluxityScript(script)
        fscript.compile_script()
        
        fctx = FluxityContext(script_file, out_folder)
        fctx.priv_context.load_profile(profile_file_path)
        
        return (None, (fscript, fctx))
    except Exception as e:
        msg = str(e)
        return (msg, None)

# ---- Debug helper
def _prints_to_log_file(log_file):
    so = se = open(log_file, 'w', buffering=1)

    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
    
    
        
