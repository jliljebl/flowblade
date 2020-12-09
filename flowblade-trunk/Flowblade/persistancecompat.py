"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2020 Janne Liljeblad.

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
This module holds funtions that maintain campatibility between project savefiles
created by different versions of application.

Refactoring to move code here is an ongoing effort.
"""
import appconsts
import miscdataobjects



# ------------------------------------------------------- legacy project fix
def FIX_MISSING_PROJECT_ATTRS(project):
    if (not(hasattr(project, "project_properties"))):
        project.project_properties = {}
        