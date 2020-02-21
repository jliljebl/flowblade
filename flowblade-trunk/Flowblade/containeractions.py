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



import hashlib
import subprocess
import sys

import appconsts
from editorstate import PROJECT
import respaths
import userfolders

# ----------------------------------------------------- interface
def get_action_object(clip):
    if clip.container_data.container_type == appconsts.CONTAINER_CLIP_GMIC:
        return GMicContainerActions(clip)


# ---------------------------------------------------- action objects
class AbstractContainerActionObject:
    
    def __init__(self, clip):
        self.clip = clip
        self.container_data = clip.container_data

    def render_full_media(self):
        print("render_full_media not impl")

    def get_rendered_media_dir(self):
        return self.get_container_clips_dir() + "/" + self.get_container_program_id()

    def get_container_program_id(self):
        id_md_str = str(self.container_data.container_type) + self.container_data.program + self.container_data.unrendered_media
        return hashlib.md5(id_md_str.encode('utf-8')).hexdigest()

    def get_container_clips_dir(self):
        return userfolders.get_data_dir() + appconsts.CONTAINER_CLIPS_DIR


class GMicContainerActions(AbstractContainerActionObject):

    def __init__(self, clip):
        AbstractContainerActionObject.__init__(self, clip)

    def render_full_media(self):
        print("render full media")
        self._launch_render(0, self.container_data.unrendered_length)

    def _launch_render(self, range_in, range_out):
        media_dir = self.get_rendered_media_dir()
        args = ("session_id:" + self.get_container_program_id(), 
                "script:" + self.container_data.program,
                "clip_path:" + self.container_data.unrendered_media,
                "range_in:" + str(range_in),
                "range_out:"+ str(range_out),
                "profile_desc:" + PROJECT().profile.description())

        subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladegmicheadless", args[0], args[1],  args[2], args[3], args[4], args[5]])#, stdin=FLOG, stdout=FLOG, stderr=FLOG)

