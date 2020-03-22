er contains it's own version of Python
# with this library pre-installed.
import bpy

import gi

from gi.repository import GLib


cont_info_id_path = os.path.join(GLib.get_user_cache_dir(), "flowblade") + "/blender_render_container_id"
f = open(cont_info_id_psth)
cont_id = f.read()
f.close()

render_info_path = os.path.join(GLib.get_user_cache_dir(), "flowblade") +  "/" + cont_id "/blender_render_exec_lines"
f = open(cont_info_id_psth)
exec_lines = f.readlines()
f.close()

for line in exec_lines:
    print(line)
    exec(line)


# Render the current animation to the params["output_path"] folder
bpy.ops.render.render(animation=True)
