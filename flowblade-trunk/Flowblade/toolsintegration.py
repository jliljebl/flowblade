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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""
from gi.repository import GObject

import copy
import os

import appconsts
from editorstate import PROJECT
import gmic
import render
import utils

_tools = []
_render_items = []
test_timeout_id = None
           
# --------------------------------------------------- interface
def init():
    
    if gmic.gmic_available():
        _tools.append(GMICIntegrator())
        
    _tools.append(SlowMoIntegrator())
    _tools.append(ReverseIntegrator())
    
def get_export_integrators():
    export_integrators = []
    for tool_integrator in _tools:
        if tool_integrator.is_export_target == True:
            export_integrators.append(tool_integrator)
    
    return export_integrators

# --------------------------------------------------- integrator classes
class ToolIntegrator:
    
    def __init__(self, tool_name, supported_media_types, is_export_target):
        self.tool_name = tool_name
        self.is_export_target = is_export_target
        self.supported_media_types = supported_media_types
        self.data = None # Used at call sites to give needed info for exports
    
    def supports_clip_media(self, clip):
        if clip.media_type in self.supported_media_types:
            return True
        else:
            return False

    def export_callback(self, widget, data):
        new_instance = copy.deepcopy(self)
        new_instance.data = data
        new_instance.do_export()
        
    def do_export(self):
        print self.__class__.__name__ + " does not implement do_export()"
         
    def render_program(self, program_file, write_file, render_data, progress_callback, completion_callback):
        new_instance = copy.deepcopy(self)
        new_instance.program_file = program_file
        new_instance.write_file = write_file
        new_instance.render_data = render_data
        new_instance.progress_callback = progress_callback
        new_instance.completion_callback = completion_callback
        _render_items.append(new_instance)
        new_instance.start_render()

    def launch_render_ticker(self):
        self.ticker = utils.Ticker(self.render_tick, 1.0)
        self.ticker.start_ticker()

    def stop_render_ticker(self):
        self.ticker.stop_ticker()
        
    def start_render(self):
        print self.__class__.__name__ + " does not implement start_render()"

    def stop_render(self):
        print self.__class__.__name__ + " does not implement start_render()"
        
    def render_tick(self):
        print self.__class__.__name__ + " does not implement render_tick()"
        
    def create_render_ticker(self):
        self.render_ticker = utils.Ticker(self.render_tick, 1.0)


class GMICIntegrator(ToolIntegrator):
    
    def __init__(self):
        ToolIntegrator.__init__(self, _("G'MIC Effects"), [appconsts.VIDEO], True)
        
    def do_export(self):
        gmic.launch_gmic(self.data) # tuple (clip, track)
            
class SlowMoIntegrator(ToolIntegrator):
    
    def __init__(self):
        ToolIntegrator.__init__(self, _("Slow/Fast Motion"), [appconsts.VIDEO], True)
        
    def do_export(self):
        clip, track = self.data
        media_file = PROJECT().get_media_file_for_path(clip.path)
        media_file.mark_in = clip.clip_in
        media_file.mark_out = clip.clip_out
        render.render_frame_buffer_clip(media_file, True)


class ReverseIntegrator(ToolIntegrator):
    
    def __init__(self):
        ToolIntegrator.__init__(self, _("Reverse"), [appconsts.VIDEO], True)
        
    def do_export(self):
        clip, track = self.data
        media_file = PROJECT().get_media_file_for_path(clip.path)
        media_file.mark_in = clip.clip_in
        media_file.mark_out = clip.clip_out
        render.render_reverse_clip(media_file, True)
