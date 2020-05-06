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

import json
import os
import sys

import gi

from gi.repository import GLib

project_data = {}
project_data["fps"] = bpy.context.scene.render.fps
project_data["resolution_x"] = bpy.context.scene.render.resolution_x
project_data["resolution_y"] = bpy.context.scene.render.resolution_y
project_data["frame_start"] = bpy.context.scene.frame_start
project_data["frame_end"] = bpy.context.scene.frame_end

objects_list = []
for obj in bpy.data.objects:
    name = str(obj.name)
    data_str = str(obj.data)
    ri = data_str.find("(")
    li = data_str.find(",")
    data_str = data_str[0:ri]
    data_str = data_str[li + 2:]
    json_obj = [name, data_str, []]
    objects_list.append(json_obj)

project_data["objects"] = objects_list

materials_list = []
for m in bpy.data.materials:
    name = str(m.name)
    json_obj = [name, "", []]
    materials_list.append(json_obj)

project_data["materials"] = materials_list

curves_list = []
for c in bpy.data.curves:
    name = str(c.name)
    json_obj = [name, "", []]
    curves_list.append(json_obj)

project_data["curves"] = curves_list
    
save_path = os.path.join(GLib.get_user_cache_dir(), "flowblade") + "/blender_container_projectinfo.json"

if not os.path.exists(save_path):
    os.remove(save_path)
    
with open(save_path, "w") as f: 
     json.dump(project_data, f, indent=4)

