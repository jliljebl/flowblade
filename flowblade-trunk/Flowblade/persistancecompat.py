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
            
def FIX_MISSING_COMPOSITOR_ATTRS(compositor):
    # Keeping backwards compability
    if not hasattr(compositor, "obey_autofollow"): # "obey_autofollow" attr was added for 1.16
        compositor.obey_autofollow = True
                
def FIX_MISSING_PROJECT_ATTRS(project):
    if (not(hasattr(project, "project_properties"))):
        project.project_properties = {}

    if(not hasattr(project, "update_media_lengths_on_load")):
        project.update_media_lengths_on_load = True # old projects < 1.10 had wrong media length data which just was never used.
                                                    # 1.10 needed that data for the first time and required recreating it correctly for older projects
