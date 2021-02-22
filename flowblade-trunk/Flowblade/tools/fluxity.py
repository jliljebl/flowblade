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
import mlt
import os


# Script displayed at Flowblade Script tool on init.
DEFAULT_SCRIPT = \
"""
import cairo
import mlt

def init_script(fctx):
    # Script init here
    pass
    print("klklkl")
    return "init_script_done"

def init_render(fctx):
    # Render init here
    pass
 
def render_frame(frame, fctx):
    # Render init here
    cairo_surface = cairo.ImageSurface(cairo.Format.RGB24, 200, 200)
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
              
    def call_render_frame(self, frame, fctx):
        try:
          self.namespace['render_frame'](frame, fctx)
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
    
    def __init__(self):
        self.profile = None
        self.mlt_profile_path = None # We need a file for mlt.Profile so if one exits let's remember path
    
    def load_profile(self, mlt_profile_path):
        lines = []
        with open(mlt_profile_path, "r") as f:
            for line in f:
                lines.append(line.strip())
        data = {}
        data[FluxityProfile.DESCRIPTION] = _read_profile_prop_from_lines(lines, FluxityProfile.DESCRIPTION)
        data[FluxityProfile.FRAME_RATE_NUM] = _read_profile_prop_from_lines(lines, FluxityProfile.FRAME_RATE_NUM)
        data[FluxityProfile.FRAME_RATE_DEN] = _read_profile_prop_from_lines(lines, FluxityProfile.FRAME_RATE_DEN)
        data[FluxityProfile.WIDTH] = _read_profile_prop_from_lines(lines, FluxityProfile.WIDTH)
        data[FluxityProfile.HEIGHT] = _read_profile_prop_from_lines(lines, FluxityProfile.HEIGHT)
        data[FluxityProfile.PROGRESSIVE] = _read_profile_prop_from_lines(lines, FluxityProfile.PROGRESSIVE)
        data[FluxityProfile.SAMPLE_ASPECT_NUM] = _read_profile_prop_from_lines(lines, FluxityProfile.SAMPLE_ASPECT_NUM)
        data[FluxityProfile.SAMPLE_ASPECT_DEN] = _read_profile_prop_from_lines(lines, FluxityProfile.SAMPLE_ASPECT_DEN)
        data[FluxityProfile.DISPLAY_ASPECT_NUM] = _read_profile_prop_from_lines(lines, FluxityProfile.DISPLAY_ASPECT_NUM)
        data[FluxityProfile.DISPLAY_ASPECT_DEN] = _read_profile_prop_from_lines(lines, FluxityProfile.DISPLAY_ASPECT_DEN)
        data[FluxityProfile.COLORSPACE] = _read_profile_prop_from_lines(lines, FluxityProfile.COLORSPACE)

        self.profile = FluxityProfile(data)
        self.mlt_profile_path = mlt_profile_path
        
        return self.profile.profile_data


        
        

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
    raise FluxityError("Error on doing exec() script code object:\n" + exception_msg)