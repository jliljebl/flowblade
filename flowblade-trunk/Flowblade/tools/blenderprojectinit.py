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

import bpy

import os
import sys

import gi

from gi.repository import GLib

script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

msg = script_dir
print(os.path.join(GLib.get_user_data_dir(), "flowblade"))
print(bpy.context.scene.render.filepath)
print(str(bpy.context.scene.render.fps)) # + "/n"
print(str(bpy.context.scene.render.resolution_x)) #+ "/n"
print(str(bpy.context.scene.render.resolution_y)) #+ "/n"
print(str(bpy.context.scene.frame_start))# + "/n"
print(str(bpy.context.scene.frame_end))# + "/n"

print("objets")
for obj in bpy.data.objects:
    print(obj)
    print(obj.data)
    print(obj.name)
    print(obj.keys())
    print(obj.data.keys())

print("CURVES")
for obj in bpy.data.curves:
    print(obj)
    print(obj.data)
    print(obj.name)
    
print("meshes")
for obj in bpy.data.meshes:
    print(obj)
    print(obj.data)
    print(obj.name)
    
#f = open("/home/janne/blenderinfo","w")
#f.write(msg)
#f.close()
