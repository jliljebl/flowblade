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
import copy

from editorstate import PROJECT
import gmic
import toolnatron
import render

_tools = []
_active_integrators = []

# --------------------------------------------------- interface
def init():
    
    if gmic.gmic_available():
        _tools.append(GMICIntegrator())

    if toolnatron.natron_avavilable():
        _tools.append(NatronIntegrator())
        
    _tools.append(SlowMoIntegrator())
        
def get_export_integrators():
    export_integrators = []
    for tool_integrator in _tools:
        if tool_integrator.is_export_target == True:
            export_integrators.append(tool_integrator)
    
    return export_integrators

# --------------------------------------------------- integrator classes
class ToolIntegrator:
    
    def __init__(self, tool_name, is_export_target):
        self.tool_name = tool_name
        self.is_export_target = is_export_target
        self.data = None
         
    def activate(self):
        _active_integrators.append(self)
    
    def deactivate(self):
        _active_integrators.remove(self)

    def export_callback(self, widget, data):
        new_instance = copy.deepcopy(self)
        new_instance.data = data
        new_instance.activate()
        new_instance.do_export()
        
    def do_export(self):
        print self.__class__.__name__ + " does not implement do_export()"
         


class GMICIntegrator(ToolIntegrator):
    
    def __init__(self):
        ToolIntegrator.__init__(self, _("G'MIC Effects"), True)
        
    def do_export(self):
        gmic.launch_gmic(self.data) # tuple (clip, track)
            

class NatronIntegrator(ToolIntegrator):
    def __init__(self):
        ToolIntegrator.__init__(self, _("Natron"), True)

    def do_export(self):
        clip, track = self.data
        toolnatron.export_clip(clip)


class SlowMoIntegrator(ToolIntegrator):
    
    def __init__(self):
        ToolIntegrator.__init__(self, _("Slow/Fast Motion"), True)
        
    def do_export(self):
        clip, track = self.data
        media_file = PROJECT().get_media_file_for_path(clip.path)
        media_file.mark_in = clip.clip_in
        media_file.mark_out = clip.clip_out
        render.render_frame_buffer_clip(media_file, True)
                
