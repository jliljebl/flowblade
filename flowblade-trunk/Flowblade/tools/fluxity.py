"""
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
"""

import cairo
import json
import mlt
import os

# Default length in frames for script duration
DEFAULT_LENGTH = 200

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
    
    def __init__(self, script_str):
        self.script = script_str
        self.code = None
        self.namespace = {}
    
    def compile_script(self):
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
        try:
          self.namespace['init_script'](fctx)
        except Exception as e:
          _raise_fluxity_error("error calling function'init_script()':\n\n" + str(e))

    def call_init_render(self, fctx):
        try:
          self.namespace['init_render'](fctx)
        except Exception as e:
          _raise_fluxity_error("error calling function'init_render()':\n\n" + str(e))
          
    def call_render_frame(self, frame, fctx, w, h):
        try:
          self.namespace['render_frame'](frame, fctx, w, h)
        except Exception as e:
          _raise_fluxity_error("error calling function'render_frame()':\n\n" + str(e))


# ---------------------------------------------------------- mlt profile
class FluxityProfile:

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
    EDITOR_VALUE = 1
    EDITOR_FLOAT = 2
    EDITOR_INT = 3
    EDITOR_COLOR = 4
    
    PROFILE_DESCRIPTION = FluxityProfile.DESCRIPTION
    PROFILE_FRAME_RATE_NUM = FluxityProfile.FRAME_RATE_NUM
    PROFILE_FRAME_RATE_DEN = FluxityProfile.FRAME_RATE_DEN
    PROFILE_WIDTH = FluxityProfile.WIDTH
    PROFILE_HEIGHT = FluxityProfile.HEIGHT
    PROFILE_PROGRESSIVE = FluxityProfile.PROGRESSIVE
    PROFILE_SAMPLE_ASPECT_NUM = FluxityProfile.SAMPLE_ASPECT_NUM
    PROFILE_SAMPLE_ASPECT_DEN = FluxityProfile.SAMPLE_ASPECT_DEN
    PROFILE_DISPLAY_ASPECT_NUM = FluxityProfile.DISPLAY_ASPECT_NUM
    PROFILE_DISPLAY_ASPECT_DEN = FluxityProfile.DISPLAY_ASPECT_DEN
    PROFILE_COLORSPACE = FluxityProfile.COLORSPACE

    def __init__(self, preview_render, output_folder):
        self.priv_context = FluxityContextPrivate(preview_render, output_folder)
        self.data = {}
        self.editors = {} # editors and script length
        self.length = DEFAULT_LENGTH
        self.name = "Name Not Set"
        self.version = 1
        self.author = "Author Not Set"
        self.error = None

    def get_frame_cr(self):
        return self.priv_context.frame_cr

    def get_dimensions(self):
        w = self.priv_context.profile.get_profile_property(FluxityProfile.WIDTH)
        h = self.priv_context.profile.get_profile_property(FluxityProfile.HEIGHT)
        return (w, h)
 
    def get_profile_property(self, p_property):
        return self.priv_context.profile.get_profile_property(p_property)
 
    def set_name(self, name):
        self.name = name
 
    def set_version(self, version):
        self.version = version

    def set_author(self, author):
        self.author = author

    def set_frame_name(self, frame_name):
        self.priv_context.frame_name = frame_name

    def set_data(self, label, item):
        self.data[label] = item

    def get_data(self, label):
        return self.data[label]

    def set_length(self, length):
        self.length = length

    def get_length(self, label):
        return self.length

    def add_editor(self, name, type, default_value):
        self.editors[name] = (type, default_value)

    def get_script_data(self):
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

        script_data["editors_list"] = editors_list

        return json.dumps(script_data)

class FluxityContextPrivate:
    """
    This object exists to keep FluxityContext API clean for script developers.
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

    def write_out_frame(self):
        if self.output_folder == None or os.path.isdir(self.output_folder) == False:
            exception_msg = "Output folder " + self.output_folder + " does not exist."
            _raise_fluxity_error(exception_msg)
        
        filepath = self.output_folder + "/" + self.frame_name + "_" + str(self.frame).rjust(5, "0") + ".png"
        self.frame_surface.write_to_png(filepath)

        if self.first_rendered_frame_path == None:
            self.first_rendered_frame_path = filepath
        
class FluxityEmptyClass:
    pass
    
# ---------------------------------------------------------- Errors 
class FluxityError(Exception):

    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)

def _raise_fluxity_error(exception_msg):
    raise FluxityError("Fluxity Error: " + exception_msg)
    
def _raise_compile_error(exception_msg):
    raise FluxityError("Error compiling Fluxity script:\n" + exception_msg)

def _raise_exec_error(exception_msg):
    raise FluxityError("Error on doing exec() to create script code object:\n" + exception_msg)

# ------------------------------------------------------ rendering
def render_preview_frame(script, frame, out_folder, profile_file_path):
    try:
        # Init script and context.
        error_msg, results = _init_script_and_context(script, out_folder, profile_file_path)
        if error_msg != None:
            fake_fctx = FluxityEmptyClass()
            fake_fctx.error = error_msg
            return fake_fctx
            
        fscript, fctx = results

        # Execute script to render a preview frame.
        fscript.call_init_script(fctx)

        fscript.call_init_render(fctx)

        fctx.priv_context.create_frame_surface(frame)
        w, h = fctx.get_dimensions()
        fscript.call_render_frame(frame, fctx, w, h)

        return fctx
    except Exception as e:
        fctx.error = str(e)
        return fctx

def render_frame_sequence(script, in_frame, out_frame, out_folder, profile_file_path):
    try:
        # Init script and context.
        error_msg, results = _init_script_and_context(script, out_folder, profile_file_path)
        if error_msg != None:
            fake_fctx = FluxityEmptyClass()
            fake_fctx.error = error_msg
            return fake_fctx

        fscript, fctx = results
        
        # Execute script to write frame sequence.
        fscript.call_init_script(fctx)

        fscript.call_init_render(fctx)

        fctx.priv_context.first_rendered_frame_path = None # Should be clear but make sure. 

        for frame in range(in_frame, out_frame):
            fctx.priv_context.create_frame_surface(frame)
            w, h = fctx.get_dimensions()
            fscript.call_render_frame(frame, fctx, w, h)
            fctx.priv_context.write_out_frame()

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
        