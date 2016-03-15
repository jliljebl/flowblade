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

from gi.repository import Gtk, Gdk

import copy

PH_COLOR_PARAM = "ColorParam"

def get_phantom_param_editors(phantom_prog):
    params = copy.deepcopy(phantom_prog.params)
    editors = []
    for param in params:
        editor_creator_func = EDITOR_CREATORS[param.paramtype]
        param_creator = PHANTOM_PARAMS_CREATORS[param.paramtype]
        editor = editor_creator_func(param_creator(param))
        editor.widget.show_all()
        editors.append(editor)
    
    return editors

# ---------------------------------------------------------- abstract editable param
# This is just used to establish interface, it is not 
# necessarily needed in langueage like Python
class AbstractEditableParam:

    def get_value(self):
        print "not impl"
        
    def update_value(self, value):
        print "not impl"

# ---------------------------------------------------------- phantom editable param
class AbstractPHParam(AbstractEditableParam):
    def __init__(self, phantom_param):
        self.phantom_param = phantom_param 
    
    def get_value(self):
        return self.phantom_param.value

class PHColorParam(AbstractPHParam):
    def __init__(self, phantom_param):
        AbstractPHParam.__init__(self, phantom_param)
        self.rgb = phantom_param.value.split(",")
        
    def get_value(self):
        r, g, b = self.rgb
        return Gdk.RGBA(float(r)/255.0, float(g)/255.0,float(b)/255.0, alpha=1.0)

    def update_value(self, value):
        self.phantom_param.value = value
        print value

# ---------------------------------------------------------- editors
class AbstractEditor:
    
    def __init__(self, editable_param):
        self.editable_param = editable_param
        self.widget = None
        
    def update_value(self, value):
        self.editable_param.update_value(value)


class ColorEditor(AbstractEditor):
    def __init__(self, editable_param):
        AbstractEditor.__init__(self, editable_param)

        value = editable_param.get_value()
        color_button = Gtk.ColorButton.new_with_rgba(value)
        color_button.connect("color-set", self.color_selected)

        self.widget = Gtk.HBox(False, 4)
        self.widget.pack_start(color_button, False, False, 4)
        self.widget.pack_start(Gtk.Label(), True, True, 0)

    def color_selected(self, color_button):
        print "pppaspasdppasdp"

# ------------------------------------------------------------- creator func tables
EDITOR_CREATORS = { \
    PH_COLOR_PARAM:lambda param : ColorEditor(param) \
    }


PHANTOM_PARAMS_CREATORS = { \
    PH_COLOR_PARAM:lambda param : PHColorParam(param) \
    }
