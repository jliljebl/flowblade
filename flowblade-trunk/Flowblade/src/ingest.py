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
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

import threading

import editorstate
import jobs


class TranscodeRenderItemData:
    def __init__(   self, media_file_id, w, h, enc_index, 
                    transcode_file_path, transcode_rate, media_file_path, 
                    transcode_profile_desc, lookup_path):

        self.media_file_id = media_file_id
        self.w = w
        self.h = h
        self.enc_index = enc_index
        self.transcode_file_path = transcode_file_path
        self.transcode_rate = transcode_rate
        self.media_file_path = media_file_path
        self.transcode_profile_desc = transcode_profile_desc
        self.lookup_path = lookup_path # For img seqs only
        
        # We're packing this to go, jobs.py is imported into this module and we wish to not import this into jobs.py.
        self.do_auto_re_convert_func = _auto_re_convert_after_proxy_render_in_proxy_mode

    def get_data_as_args_tuple(self):
        args = ("media_file_id:" + str(self.media_file_id), 
                "w:" + str(self.w), 
                "w:" + str(self.h),
                "enc_index:" + str(self.enc_index),
                "transcode_file_path:" + str(self.transcode_file_path),
                "transcode_rate:"+ str(self.transcode_rate),
                "media_file_path:" + str(self.media_file_path),
                "transcode_profile_desc:" + str(self.transcode_profile_descs),
                "lookup_path:" + str(self.lookup_path)) 

        return args



