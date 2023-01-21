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
Module provides a single, unified MLT and renderconsuner.py init procedure for all non-main app processes.
"""
try:
    import mlt7 as mlt
except:
    import mlt7 as mlt

import locale

import mltenv
import mltfilters
import mltprofiles
import mlttransitions
import processutils
import renderconsumer
import translations

def init_with_translations():
    # Init translations module with translations data,
    # mltX modules are written in  way that assumes translations to available
    # at init time.
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()

    # Create MLT repo
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

    # Return repo so that main() holds a reference to it for the duration of process runtime.
    return repo

