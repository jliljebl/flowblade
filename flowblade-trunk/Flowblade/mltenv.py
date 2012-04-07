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

"""
Module checks environment for available codecs and formats.
"""
import subprocess
import os
import stat
import sys

import utils

TEST_SCRIPT_FILE = "testscript.sh"
ACODECS_FILE = "acodecs"
VCODECS_FILE = "vcodecs"
FORMATS_FILE = "formats"

acodecs = None
vcodecs = None
formats = None

melt_available = False

def check_available_features():
    """
    Create and run a script that genates lists files of codecs and formats and
    then them into lists.
    """
    melt_path = whereis('melt')
    if melt_path == None:
        # INFOWINDOW
        return
    
    global melt_available
    melt_available = True

    # Write script to file
    script_path = utils.get_hidden_user_dir_path() + TEST_SCRIPT_FILE
    script = open(script_path, "w")
    script.write('#!/bin/bash\n')
    script.write('\n')
    script.write(melt_path + " noise: -consumer avformat acodec=list > " +
            utils.get_hidden_user_dir_path() + ACODECS_FILE + "\n")
    script.write(melt_path + " noise: -consumer avformat vcodec=list > " +
            utils.get_hidden_user_dir_path() + VCODECS_FILE + "\n")
    script.write(melt_path + " noise: -consumer avformat f=list > " +
            utils.get_hidden_user_dir_path() + FORMATS_FILE + "\n")
    script.write('\n')
    script.close()

    # Run script
    # Out put is seen on console if this is run from console.
    os.chmod(script_path, stat.S_IRWXU)
    process = subprocess.Popen(script_path)
    process.wait()

    # Read script output to get codes and formats
    global acodecs
    ac_file = open(utils.get_hidden_user_dir_path() + ACODECS_FILE)
    acodecs = ac_file.readlines()[2:-1]
    ac_file.close()
    acodecs = _strip_ends(acodecs)

    global vcodecs
    vc_file = open(utils.get_hidden_user_dir_path() + VCODECS_FILE)
    vcodecs = vc_file.readlines()[2:-1]
    vc_file.close()
    vcodecs = _strip_ends(vcodecs)
    
    global formats
    f_file = open(utils.get_hidden_user_dir_path() + FORMATS_FILE)
    formats = f_file.readlines()[2:-1]
    f_file.close()
    formats = _strip_ends(formats)
    
def render_profile_supported(format, vcodec, acodec):   
    if acodec in acodecs:
        if vcodec in vcodecs:
            if format in formats:
                return True
    return False
    
def whereis(program):
    for path in os.environ.get('PATH', '').split(':'):
        if os.path.exists(os.path.join(path, program)) and \
           not os.path.isdir(os.path.join(path, program)):
            return os.path.join(path, program)
    return None

def _strip_ends(slist):
    rlist = []
    for s in slist:
        rlist.append(s[4:-1])
        
    return rlist
