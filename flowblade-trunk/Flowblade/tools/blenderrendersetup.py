# Blender Python interface
import bpy

import gi
from gi.repository import GLib

import os


cont_info_id_path = os.path.join(GLib.get_user_cache_dir(), "flowblade") + "/blender_render_container_id"
f = open(cont_info_id_path)
cont_id = f.read()
f.close()

render_info_path = os.path.join(GLib.get_user_data_dir(), "flowblade") + "/container_clips/" + cont_id + "/blender_render_exec_lines"
f = open(render_info_path)
exec_lines = f.readlines()
f.close()


for line in exec_lines:
    print(line)
    exec(line)


bpy.ops.render.render(animation=True)
