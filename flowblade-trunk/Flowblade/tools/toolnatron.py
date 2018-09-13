"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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

import md5
import os
import subprocess
import sys

import appconsts
import dialogutils
from editorstate import PROJECT
import gui
import natronanimations
import respaths
import utils

_natron_found = False

def init():
    global _natron_found
    if utils.program_is_installed("Natron"):
        _natron_found = True

        print "Natron found"
    else:
        _natron_found = False
        print "Natron not found"

def launch_natron_animations_tool():
    if _natron_found == False:
        primary_txt = _("Natron not found!")
        secondary_txt = _("Natron was not present in the system.") # TODO: more info
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    gui.save_current_colors()

    current_profile_name = PROJECT().profile.description().replace(" ", "_")
    print current_profile_name
    print "Launch Natron tool..."
    FLOG = open(utils.get_hidden_user_dir_path() + "log_natron_tool", 'w')
    subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladenatron", current_profile_name], stdin=FLOG, stdout=FLOG, stderr=FLOG)
    #subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladenatron", args[0], args[1], args[2]], stdin=FLOG, stdout=FLOG, stderr=FLOG)
        
def natron_available():
    return _natron_found

def export_clip(clip):
    # Write export data file
    natron_dir = utils.get_hidden_user_dir_path() + appconsts.NATRON_DIR + "/"
    file_path = natron_dir + "clipexport_" + md5.new(str(os.urandom(32))).hexdigest()
    data_text = clip.path + " " + str(clip.clip_in) + " " + str(clip.clip_out + 1)
    
    export_data_file = open(file_path, "w")
    export_data_file.write(data_text)
    export_data_file.close()

    # Launch Natron
    print "Launch Natron..."
    args = [str(respaths.LAUNCH_DIR + "natron_clip_export_start.sh"), str(respaths.LAUNCH_DIR)]
    subprocess.Popen(args)

def render_program(render_folder, frame_name, project_file, writer, start_frame, end_frame):
    render_frame = render_folder + "/" + frame_name + "####.png"
    range_str = str(start_frame) + "-" + str(end_frame)
    #NatronRenderer -w Write2 1-10 /home/janne/test/natrontest.ntp
    #NatronRenderer -w Write2 1-10 /home/janne/test/natrontestout/frame###.png /home/janne/test/natrontest.ntp
    #NatronRenderer -w Write2 1-10 /home/janne/test/natrontestout/frame###.png /home/janne/test/natrontest.ntp
    
    # Launch Natron
    print "Launch Natron render with ", writer, range_str, render_frame, project_file
    args = [str(respaths.LAUNCH_DIR + "natron_render.sh"), writer, range_str, render_frame, project_file]
    p = subprocess.Popen(args)
    p.wait()
    
    
    
        
