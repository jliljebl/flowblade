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
import appconsts
import editorstate
import propertyedit
import propertyparse

"""
This module handles adding fade-ins and fade-outs to compositors.

Creating and managing keyframes is mostly handled by editor GUI components which cannot reasonbly 
be used for adding fade-ins and fade outs, so this dedicated module is needed.
"""

def add_default_fades(compositor):

    # Create editable properties list for compositor.
    t_editable_properties = propertyedit.get_transition_editable_properties(compositor)
    
    # Find keyframe property and its class.
    keyframe_property = None
    klass = None
    for ep in t_editable_properties:
        klass = ep.__class__.__name__
        if klass == "OpacityInGeomKeyframeProperty":
            keyframe_property = ep
            break
        
        try:
            print ep
            print ep.__class__.__name__
            print ep.name
            print ep.args
            print ep.value
        except:
            print "in except#"
    
    if keyframe_property == None:
        print "add_default_fades failed"
        return
    
    # Get keyframes list
    keyframes = None
    if klass == "OpacityInGeomKeyframeProperty":
        keyframes = propertyparse.geom_keyframes_value_string_to_opacity_kf_array(keyframe_property.value, keyframe_property.get_in_value)
        
    print keyframes
    
    
    fade_in = editorstate.PROJECT().get_project_property(appconsts.P_PROP_DISSOLVE_GROUP_FADE_IN)
    fade_out = editorstate.PROJECT().get_project_property(appconsts.P_PROP_DISSOLVE_GROUP_FADE_OUT) 
    
    print fade_in, fade_out
    
    
    
    
    
    
