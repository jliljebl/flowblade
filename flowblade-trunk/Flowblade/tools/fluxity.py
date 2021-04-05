"""
    ### GPL Licence text

    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2021 Janne Liljeblad.

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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
    
    
    # FLUXITY SCRIPTING
"""

import cairo
import json
import mlt
import os

# Default length in frames for script duration
DEFAULT_LENGTH = 200

METHOD_INIT_SCRIPT = 0
METHOD_INIT_RENDER = 1
METHOD_RENDER_FRAME = 2

# Script displayed at Flowblade Script tool on init.
DEFAULT_SCRIPT = \
"""
import cairo
import mlt

def init_script(fctx):
    # Script init here
    fctx.add_editor("float_editor", fctx.EDITOR_FLOAT, 1.0)
    fctx.set_name("Default Test Plugin")

def init_render(fctx):
    # Render init here
    fctx.set_data("bg_color", cairo.SolidPattern(0.8, 0.2, 0.2, 1.0))
 
def render_frame(frame, fctx, w, h):
    # Frame Render code here
    cr = fctx.get_frame_cr()
    color = fctx.get_data("bg_color")
    cr.set_source(color)
    cr.rectangle(0, 0, w, h)
    cr.fill()
"""


# ---------------------------------------------------------- script object
class FluxityScript:
    """
    Compiles scripts to executable object and calls methods *init_script()*, *init_render()*, *render_frame()* on it.
    
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


# ---------------------------------------------------------- mlt profile
class FluxityProfile:
    """
    Properties of this class correspond MLT profile objects.
    
    Internal class, do not use objects of this class directly in scripts. 
    """
    DESCRIPTION = "description"
    FRAME_RATE_NUM = "frame_rate_num"
    FRAME_RATE_DEN = "frame_rate_den"
    WIDTH = "width"
    HEIGHT = "height"
    PROGRESSIVE = "progressive"
    SAMPLE_ASPECT_NUM = "sample_aspect_num"
    SAMPLE_ASPECT_DEN = "sample_aspect_den"
    DISPLAY_ASPECT_NUM = "display_aspect_num"
    DISPLAY_ASPECT_DEN = "display_aspect_den"
    COLORSPACE = "colorspace"
        
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

    EDITOR_STRING = 0
    """ Editor for strings"""
    EDITOR_VALUE = 1
    """ Editor for values that are saved as strings but be could interpreted as other data."""
    EDITOR_FLOAT = 2
    """ Editor for float values."""
    EDITOR_INT = 3
    """ Editor for integer values."""
    EDITOR_COLOR = 4
    """ Editor for colors. Value is a (R,G,B,A) tuple with values in range 0-1."""
    
    PROFILE_DESCRIPTION = FluxityProfile.DESCRIPTION
    """MLT Profile descriptiption string."""
    PROFILE_FRAME_RATE_NUM = FluxityProfile.FRAME_RATE_NUM
    """Frame rate numerator."""
    PROFILE_FRAME_RATE_DEN = FluxityProfile.FRAME_RATE_DEN
    """Frame rate denominator."""
    PROFILE_WIDTH = FluxityProfile.WIDTH
    """Output image width in pixels."""
    PROFILE_HEIGHT = FluxityProfile.HEIGHT
    """Output image height in pixels."""
    PROFILE_PROGRESSIVE = FluxityProfile.PROGRESSIVE
    """
    MLT Profile image is progressive if value is *True*, if value is *False* image is interlaced.
    """
    PROFILE_SAMPLE_ASPECT_NUM = FluxityProfile.SAMPLE_ASPECT_NUM
    """
    Pixel size fraction numerator.
    """
    PROFILE_SAMPLE_ASPECT_DEN = FluxityProfile.SAMPLE_ASPECT_DEN
    """
    Pixel size fraction denominator.
    """
    PROFILE_DISPLAY_ASPECT_NUM = FluxityProfile.DISPLAY_ASPECT_NUM
    """Output image size fraction numerator."""
    PROFILE_DISPLAY_ASPECT_DEN = FluxityProfile.DISPLAY_ASPECT_DEN
    """Output image size fraction denominator."""
    PROFILE_COLORSPACE = FluxityProfile.COLORSPACE
    """Profile colorspace, value is either 709, 601 or 2020."""

    def __init__(self, preview_render, output_folder):
        self.priv_context = FluxityContextPrivate(preview_render, output_folder)
        self.data = {}
        self.editors = {} # editors and script length
        self.editor_tooltips = {}
        self.length = DEFAULT_LENGTH
        self.name = "Name Not Set"
        self.version = 1
        self.author = "Author Not Set"
        self.error = None

    def get_frame_cr(self):
        """
        For every rendered frame method *render_frame()* is called and a new **cairo.ImageSurface** object is created.
        
        This method provides access to **cairo.Context** object that can be used to draw onto that image surface. This is the way that output is achieved with **Flowblade Media Plugins**. 
        
        After method *render_frame()* exits, contents of **cairo.ImageSurface** are saved to disk.
        
        Must be called in script method *render_frame()*.
        
        **Returns:** (**cairo.Context**) Context object that can be drawn onto.
        """
        return self.priv_context.frame_cr

    def get_dimensions(self):
        """
        Pixel size of output image.
        
        **Returns:** (tuple(width, height)) Image size.
        """
        w = self.priv_context.profile.get_profile_property(FluxityProfile.WIDTH)
        h = self.priv_context.profile.get_profile_property(FluxityProfile.HEIGHT)
        return (w, h)

    def get_profile_property(self, p_property):
        """
        Used to access properties of MLT profile set before running the script that defines e.g. output image size.
        
        **Returns:** (int, boolean, string) Value depends on which profile property is being accessed.
        """
        return self.priv_context.profile.get_profile_property(p_property)
 
    def set_name(self, name):
        """
        **name(str):** name of script displayed to user.
        
        Must be called in script method *init_script()*.
        """
        self.name = name
        self.priv_context.error_on_wrong_method("set_name()", METHOD_INIT_SCRIPT)

    def set_version(self, version):
        """
        **version(int):** version of script, use increasing integer numbering. Default value is *1*.
        
        Must be called in script method *init_script()*.
        """
        self.version = version
        self.priv_context.error_on_wrong_method("set_version()", METHOD_INIT_SCRIPT)

    def set_author(self, author):
        """
        **author(str):** name of script creator.
        
        Must be called in script method *init_script()*.
        """
        self.author = author

    def set_frame_name(self, frame_name):
        """        
        **frame_name(str):** name used before number part in rendered frame files.
        """
        self.priv_context.frame_name = frame_name

    def set_data(self, label, item):
        """
        **label(str):** lable used to access data later using *get_data(self, label)*.

        **item(obj):** data item being saved.
        
        Saves data to be used later during execution of script. Using **global** would obivously be possible to replace this, but this is made available as a more clean solution.
        """
        self.data[label] = item

    def get_data(self, label):
        """
        **label(str):** lable of saved data item.
        
        Gives access to previously saved data.
        
        **Returns:** (obj) Saved data item.
        """
        return self.data[label]

    def set_length(self, length):
        """
        **length(int):** New length of script in frames.
        
        Sets length of script output in frames.
        
        Must *not* be called in  *render_frames()*.
        """
        self.length = length

    def get_length(self):
        """
        **Returns:** (int) Length of script in frames.
        """
        return self.length

    def add_editor(self, name, type, default_value, tooltip=None):
        """     
        **name(str):** Name for editor.
        
        **type(int):** Value either *EDITOR_STRING, EDITOR_VALUE, EDITOR_FLOAT, EDITOR_INT, EDITOR_COLOR.*
        
        **default_value():** Data type depends on editor type: *EDITOR_STRING(str), EDITOR_VALUE(str), EDITOR_FLOAT(float), EDITOR_INT(int), EDITOR_COLOR(tuple(R,G,B,A)).*
        
        **tooltip(str, optional):** Tooltip for editor if presented in GUI.
        
        Defines possible GUI editors used to affect script rendering. Edited value is accessed with method *get_editor_value(self, name, frame=0)*.
        
        Data describing editors can be accessed with *get_script_data(self)*. Edited values are made available for script with *set_editors_data(self, editors_data_json)*.
        
        Must be called in script method *init_script()*.
        """
        self.editors[name] = (type, default_value)

        if tooltip != None:
            self.editor_tooltips[name] = tooltip

        self.priv_context.error_on_wrong_method("add_editor()", METHOD_INIT_SCRIPT)
        
    def get_editor_value(self, name, frame=0):
        """     
        **name(str):** Name of editor.
        
        **frame(int):** Frame in range 0 - (script length - 1).
        
        Value of edited data at given frame. We currently have no animated values, but they will added with future API updates.
        
        Returned data type depends on editor type: *EDITOR_STRING(str), EDITOR_VALUE(str), EDITOR_FLOAT(float), EDITOR_INT(int), EDITOR_COLOR(tuple(R,G,B,A)).*
        
        **Returns:** (obj) Value at frame.
        """
        try:
            type, value = self.editors[name]
            return value
        except:
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

        script_data["editors_list"] = editors_list # this is dict inside, but is given out as list for convenience of Flowblade app integration.
        script_data["tooltips_list"] = self.editor_tooltips
        
        return json.dumps(script_data)

    def set_editors_data(self, editors_data_json):
        """
        **editors_data_json(str):** string representation of JSON object.
                 
        Sets edited data to be used when rendering.
        
        Input string must describe JSON object that can be turned into usable editor data.
        
        *Example with EDITOR_FLOAT and EDITOR_COLOR:*
        
        ```
        [
            ["Position X", 2, 1.0], 
            ["BG Color", 4, [0.8, 0.2, 0.2, 1.0]]
        ]
        ```
        
        *General form:*
        
        ```
        [
            [<name>, <type>, <value>], 
            ...
        ]
        ```
        
        Using this method is not needed when creating **Flowblade Media Plugins**, application handles setting editors data.
        
        Should be called in script method *init_render()*.
        """
        new_editors_list = json.loads(editors_data_json)
        for editor in new_editors_list:
            name, type, value = editor
            self.editors[name] = (type, value)

        
class FluxityContextPrivate:
    """
    This class exists to keep FluxityContext API clean for script developers.
    
    Internal class, do not use objects of this class directly in scripts.
    """
    def __init__(self, preview_render, output_folder):

        self.profile = None
        self.mlt_profile_path = None # We need a file for mlt.Profile so if one exits let's remember path, set with self.load_profile()
        
        self.preview_render = preview_render
        self.output_folder = output_folder
        
        self.frame = -1
        
        self.frame_surface = None
        self.frame_cr = None

        self.frame_name = "frame"
        self.first_rendered_frame_path = None # This is cleared by rendering routines.

        self.current_method = None
        self.method_name = {METHOD_INIT_SCRIPT:"init_script()", METHOD_INIT_RENDER:"init_render()", METHOD_RENDER_FRAME:"render_frame()"}
        
    def load_profile(self, mlt_profile_path):
        lines = []
        with open(mlt_profile_path, "r") as f:
            for line in f:
                lines.append(line.strip())
        data = {}
        data[FluxityProfile.DESCRIPTION] = _read_profile_prop_from_lines(lines, FluxityProfile.DESCRIPTION)
        data[FluxityProfile.FRAME_RATE_NUM] = _read_profile_prop_from_lines(lines, FluxityProfile.FRAME_RATE_NUM)
        data[FluxityProfile.FRAME_RATE_DEN] = _read_profile_prop_from_lines(lines, FluxityProfile.FRAME_RATE_DEN)
        data[FluxityProfile.WIDTH] = int(_read_profile_prop_from_lines(lines, FluxityProfile.WIDTH))
        data[FluxityProfile.HEIGHT] = int(_read_profile_prop_from_lines(lines, FluxityProfile.HEIGHT))
        data[FluxityProfile.PROGRESSIVE] = _read_profile_prop_from_lines(lines, FluxityProfile.PROGRESSIVE)
        data[FluxityProfile.SAMPLE_ASPECT_NUM] = _read_profile_prop_from_lines(lines, FluxityProfile.SAMPLE_ASPECT_NUM)
        data[FluxityProfile.SAMPLE_ASPECT_DEN] = _read_profile_prop_from_lines(lines, FluxityProfile.SAMPLE_ASPECT_DEN)
        data[FluxityProfile.DISPLAY_ASPECT_NUM] = _read_profile_prop_from_lines(lines, FluxityProfile.DISPLAY_ASPECT_NUM)
        data[FluxityProfile.DISPLAY_ASPECT_DEN] = _read_profile_prop_from_lines(lines, FluxityProfile.DISPLAY_ASPECT_DEN)
        data[FluxityProfile.COLORSPACE] = _read_profile_prop_from_lines(lines, FluxityProfile.COLORSPACE)

        self.profile = FluxityProfile(data)
        self.mlt_profile_path = mlt_profile_path
        
        return self.profile.profile_data
        
    def create_frame_surface(self, frame):
        self.frame = frame
        w = self.profile.profile_data[FluxityProfile.WIDTH]
        h = self.profile.profile_data[FluxityProfile.HEIGHT]
        self.frame_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        self.frame_cr = cairo.Context(self.frame_surface)

    def write_out_frame(self, is_preview_frame=False):
        if self.output_folder == None or os.path.isdir(self.output_folder) == False:
            exception_msg = "Output folder " + self.output_folder + " does not exist."
            _raise_fluxity_error(exception_msg)
        
        filepath = self.output_folder + "/" + self.frame_name + "_" + str(self.frame).rjust(5, "0") + ".png"
        if is_preview_frame == True:
            filepath = self.output_folder + "/preview.png"
        self.frame_surface.write_to_png(filepath)

        if self.first_rendered_frame_path == None:
            self.first_rendered_frame_path = filepath
    
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
def render_preview_frame(script, frame, out_folder, profile_file_path, editors_data_json=None):
    try:
        # Init script and context.
        error_msg, results = _init_script_and_context(script, out_folder, profile_file_path)
        if error_msg != None:
            fake_fctx = FluxityEmptyClass()
            fake_fctx.error = error_msg
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
        fctx.error = str(e)
        return fctx

def render_frame_sequence(script, in_frame, out_frame, out_folder, profile_file_path, frame_write_callback=None, editors_data_json=None):
    try:
        # Init script and context.
        error_msg, results = _init_script_and_context(script, out_folder, profile_file_path)
        if error_msg != None:
            fake_fctx = FluxityEmptyClass()
            fake_fctx.error = error_msg
            return fake_fctx

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
        
        for frame in range(in_frame, out_frame):
            fctx.priv_context.create_frame_surface(frame)
            w, h = fctx.get_dimensions()
            fscript.call_render_frame(frame, fctx, w, h)
            fctx.priv_context.write_out_frame()
            if frame_write_callback != None:
                frame_write_callback(frame) # for GUI app opdates.
        return fctx
        
    except Exception as e:
        fctx.error = str(e)
        return fctx

def _init_script_and_context(script, out_folder, profile_file_path):
    try:
        fscript = FluxityScript(script)
        fscript.compile_script()
        
        fctx = FluxityContext(True, out_folder)
        fctx.priv_context.load_profile(profile_file_path)

        return (None, (fscript, fctx)) # (error_msg, frame_iamge)
    except Exception as e:
        msg = str(e)
        return (msg, None) # (error_msg, frame_iamge)
        