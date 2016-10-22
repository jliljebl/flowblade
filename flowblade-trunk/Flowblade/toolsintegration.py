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

import gmic

_tools = []
_active_integrators = []

# --------------------------------------------------- interface
def init():
    
    if gmic.gmic_available():
        _tools.append(GMICIntegrator())

def get_export_integrators():
    export_integrators = []
    for tool_integrator in _tools:
        if tool_integrator.export_target == True:
            export_integrators.append(tool_integrator)
    
    return export_integrators

# --------------------------------------------------- integrator classes
class ToolIntegrator:
    
    
    def __init__(self, tool_name, export_target):
        self.tool_name = tool_name
        self.export_target = export_target

    def activate(self):
        _active_integrators.append(self)
    
    def deactivate(self):
        _active_integrators.remove(self)

    def get_export_callback(self, widget, data):
        print data


class GMICIntegrator(ToolIntegrator):
    
    def __init__(self):
        ToolIntegrator.__init__(self, "G'MIC Effects", True)
