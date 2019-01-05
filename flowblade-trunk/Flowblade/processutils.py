
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

"""
Module provides functions needed to get application processes in Flowblde running.

In addition to main application, Flowblade launches several processes that are essentially 
independently running applications. 
"""

import sys


def update_sys_path(modules_path):
    # Add all folders containing python modules to Python system path
    sys.path.insert(0, modules_path + "/vieweditor")
    sys.path.insert(0, modules_path + "/tools")


def prepare_mlt_repo(repo):
    # Remove mlt services that interfere with Flowblade running correctly
    repo.producers().set('qimage', None, 0)
    repo.producers().set('qtext', None, 0)
    repo.producers().set('kdenlivetitle', None, 0)
