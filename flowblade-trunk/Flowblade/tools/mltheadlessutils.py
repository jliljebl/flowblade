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
Module provides utility methods for moduless creating headless render procesesses
in initialized Flowblade/MLT enviroment.
"""

import locale
import mlt
import os

import ccrutils
import editorstate
import editorpersistance
import mltfilters
import mltenv
import mltprofiles
import mlttransitions
import processutils
import renderconsumer
import respaths
import translations
import userfolders


def mlt_env_init(root_path, session_id):
    os.nice(10) # make user configurable

    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"

    # Set paths.
    respaths.set_paths(root_path)

    userfolders.init()
    editorpersistance.load()

    # Init translations module with translations data
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()

    repo = mlt.Factory().init()
    processutils.prepare_mlt_repo(repo)
    
    # Set numeric locale to use "." as radix, MLT initilizes this to OS locale and this causes bugs 
    locale.setlocale(locale.LC_NUMERIC, 'C')

    # Check for codecs and formats on the system
    mltenv.check_available_features(repo)
    renderconsumer.load_render_profiles()

    # Load filter and compositor descriptions from xml files.
    mltfilters.load_filters_xml(mltenv.services)
    mlttransitions.load_compositors_xml(mltenv.transitions)

    # Create list of available mlt profiles
    mltprofiles.load_profile_list()
    
    ccrutils.init_session_folders(session_id)
    
    ccrutils.load_render_data()
    render_data = ccrutils.get_render_data()
    
    # This needs to have render data loaded to know if we are using external folders.
    ccrutils.maybe_init_external_session_folders()
    
    return render_data


