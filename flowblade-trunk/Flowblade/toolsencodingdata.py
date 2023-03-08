"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2021 Janne Liljeblad.

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

import mltprofiles
import renderconsumer


class ToolsRenderData():
    """
    This is used to save and communicate render selections defined by user
    for renders other the main application timeline render such as G'Mic tool and Container 
    clips renders.
    """
    def __init__(self):
        self.profile_index = None
        self.use_default_profile = None # NOT USED, 'profile_index' is the meaningful data here, this one should not have been included in this data struct.
        self.use_preset_encodings = None
        self.presets_index = None
        self.encoding_option_index = None
        self.quality_option_index = None
        self.render_dir = None
        self.file_name = None
        self.file_extension = None
        
        # Used by container clips only.
        self.do_video_render = True
        self.save_internally = True
        self.frame_name = "frame"
        self.is_preview_render = False
        self.is_flatpak_render = False
    
    
    
def get_args_vals_list_for_render_data(render_data):
    profile = mltprofiles.get_profile_for_index(render_data.profile_index)

    args_vals_list = renderconsumer.get_args_vals_tuples_list_for_encoding_and_quality( profile, 
                                                                                        render_data.encoding_option_index, 
                                                                                        render_data.quality_option_index)
    # sample rate not supported
    # args rendering not supported

    return args_vals_list
