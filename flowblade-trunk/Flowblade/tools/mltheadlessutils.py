"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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
Module provides utility methods for modules creating headless render procesesses
in initialized Flowblade/MLT environment.
"""

try:
    import mlt7 as mlt
except:
    import mlt
import os

import ccrutils
import editorstate
import editorpersistance
import mltinit
import respaths
import userfolders


def mlt_env_init(root_path, parent_folder, session_id):
    os.nice(10) # make user configurable

    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"

    # Set paths.
    respaths.set_paths(root_path)

    userfolders.init()
    editorpersistance.load()

    mltinit.init_with_translations()
    
    ccrutils.init_session_folders(parent_folder, session_id)
    
    ccrutils.load_render_data()
    render_data = ccrutils.get_render_data()
    
    # This needs to have render data loaded to know if we are using external folders.
    ccrutils.maybe_init_external_session_folders()
    
    return render_data


