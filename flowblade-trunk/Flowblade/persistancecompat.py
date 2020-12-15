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
import math

import appconsts
import miscdataobjects

# ----------------------------------------------------- Filter obejct replace
"""
def DO_DEPRECATED_FILTER_REPLACE(py_filter):
    if py_filter.info.mlt_service_id == "volume" and py_filter.info.multipart_filter == True:
        print("haolou")
        keyframes = py_filter._parse_value_to_keyframes()
        for kf in keyframes:
            frame, gain_value = kf
            db_value = _get_db_for_gain_value(float(gain_value))
            print(frame, gain_value)
            print(frame, db_value)

    return py_filter


def _get_db_for_gain_value(gain_value):
    if gain_value == 0.0:
        return -70.0
        
    print(20 * math.log10(gain_value))
    
    if gain_value <= 1.0:
        db_val = (20.0 * math.log10(gain_value))
    else:
        db_val = 1.5
        
    return db_val
"""
# ------------------------------------------------------- FIXING MISSING ATTRS
def FIX_MISSING_MEDIA_FILE_ATTRS(media_file):
    # This attr was added for 1.8. It is not computed for older projects.
    if (not hasattr(media_file, "info")):
        media_file.info = None
        
    # We need this in all media files, used only by img seq media
    if not hasattr(media_file, "ttl"):
        media_file.ttl = None

    # Add container data if not found.
    if not hasattr(media_file, "container_data"):
        media_file.container_data = None
            
def FIX_MISSING_CLIP_ATTRS(clip):
    # Add color attribute if not found
    if not hasattr(clip, "color"):
        clip.color = None
        
    # Add markers list if not found
    if not hasattr(clip, "markers"):
        clip.markers = []

    # Add img seq ttl value for all clips if not found, we need this present in every clip so we test for 'clip.ttl == None' to get stuff working
    if not hasattr(clip, "ttl"):
        clip.ttl = None

    # Add container data if not found.
    if not hasattr(clip, "container_data"):
        clip.container_data = None

def FIX_MISSING_FILTER_ATTRS(filter):
    if not hasattr(filter.info, "filter_mask_filter"):
        filter.info.filter_mask_filter = None
            
def FIX_MISSING_COMPOSITOR_ATTRS(compositor):
    # Keeping backwards compability
    if not hasattr(compositor, "obey_autofollow"): # "obey_autofollow" attr was added for 1.16
        compositor.obey_autofollow = True

def FIX_MISSING_SEQUENCE_ATTRS(seq):
    if not hasattr(seq, "compositing_mode"):
        seq.compositing_mode = appconsts.COMPOSITING_MODE_TOP_DOWN_FREE_MOVE
            
def FIX_MISSING_PROJECT_ATTRS(project):
    if (not(hasattr(project, "project_properties"))):
        project.project_properties = {}

    if(not hasattr(project, "update_media_lengths_on_load")):
        project.update_media_lengths_on_load = True # old projects < 1.10 had wrong media length data which just was never used.
                                                    # 1.10 needed that data for the first time and required recreating it correctly for older projects
