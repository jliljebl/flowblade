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

import subprocess
import sys

import respaths
import utils

_phantom_found = True

def launch_phantom():
    if _phantom_found == False:
        #primary_txt = _("G'Mic not found!")
        #secondary_txt = _("G'Mic binary was not present at <b>/usr/bin/gmic</b>.\nInstall G'MIC to use this tool.")
        #dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    FLOG = open(utils.get_hidden_user_dir_path() + "log_phantom", 'w')
    subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladephantom" + " " + respaths.PHANTOM_JAR], stdin=FLOG, stdout=FLOG, stderr=FLOG)

