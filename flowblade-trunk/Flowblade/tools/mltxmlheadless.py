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

try:
    import pgi
    pgi.install_as_gi()
except ImportError:
    pass
    
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GLib

import locale
import mlt
import os
import pickle
import subprocess
import sys
import threading
import time

import appconsts
import ccrutils
import mltheadlessutils
import mltprofiles
import processutils
import renderconsumer
import toolsencoding


_render_thread = None


# ----------------------------------------------------- module interface with message files
# We are using message files to communicate with application.
def clear_flag_files(session_id):
    ccrutils.clear_flag_files(session_id)

def set_render_data(session_id, video_render_data):
    ccrutils.set_render_data(session_id, video_render_data)
    
def session_render_complete(session_id):
    return ccrutils.session_render_complete(session_id)

def get_session_status(session_id):
    msg = ccrutils.get_session_status_message(session_id)
    if msg == None:
        return None
    fraction, elapsed = msg.split(" ")
    return (fraction, elapsed)
    
def abort_render(session_id):
    ccrutils.abort_render(session_id)



# --------------------------------------------------- render thread launch
def main(root_path, session_id, xml_file_path, range_in, range_out, profile_desc):
    
    render_data = mltheadlessutils.mlt_env_init(root_path, session_id)

    global _render_thread
    _render_thread = MLTXMLHeadlessRunnerThread(render_data, xml_file_path, range_in, range_out, profile_desc)
    _render_thread.start()

       

class MLTXMLHeadlessRunnerThread(threading.Thread):

    def __init__(self, render_data, xml_file_path, range_in, range_out, profile_desc):
        threading.Thread.__init__(self)

        self.render_data = render_data # toolsencoding.ToolsRenderData object
        self.xml_file_path = xml_file_path
        self.range_in = int(range_in)
        self.range_out = int(range_out)
        self.length = self.range_out - self.range_in + 1
        self.profile_desc = profile_desc
    
        self.abort = False

        
    def run(self):
        self.start_time = time.monotonic()

        args_vals_list = toolsencoding.get_args_vals_list_for_render_data(self.render_data)
        profile = mltprofiles.get_profile_for_index(self.render_data.profile_index)
        
        producer = mlt.Producer(profile, str(self.xml_file_path))

        # Video clip consumer
        if self.render_data.do_video_render == True:
            if self.render_data.save_internally == True:
                file_path = ccrutils.session_folder() +  "/" + appconsts.CONTAINER_CLIP_VIDEO_CLIP_NAME + self.render_data.file_extension
            else:
                file_path = self.render_data.render_dir +  "/" + self.render_data.file_name + self.render_data.file_extension

            consumer = renderconsumer.get_mlt_render_consumer(file_path, profile, args_vals_list)

            ccrutils.delete_rendered_frames() # in case we switched from img seq consumer we can now delete those frames to save space
        # img seq consumer
        else:
            # Image sequence gets project profile
            project_profile = mltprofiles.get_profile(self.profile_desc)
            if self.render_data.save_internally == True:
                frame_name = "frame"            
            else:
                frame_name = self.render_data.frame_name

            render_path = ccrutils.rendered_frames_folder() + frame_name + "_%04d." + "png"

            consumer = mlt.Consumer(project_profile, "avformat", str(render_path))
            consumer.set("real_time", -1)
            consumer.set("rescale", "bicubic")
            consumer.set("vcodec", "png")

        self.render_player = renderconsumer.FileRenderPlayer("", producer, consumer, self.range_in, self.range_out)
        self.render_player.wait_for_producer_end_stop = False
        self.render_player.start()

        while self.render_player.stopped == False:
            
            self.abort_requested()
            
            if self.abort == True:
                self.render_player.shutdown()
                return
            
            fraction = self.render_player.get_render_fraction()

            self.render_update_callback(fraction)
            
            time.sleep(0.3)
                
        # Write out completed flag file.
        ccrutils.write_completed_message()

    def abort_requested(self):
        self.abort = ccrutils.abort_requested()
        return self.abort

    def render_update_callback(self, fraction):
        elapsed = time.monotonic() - self.start_time
        msg = str(fraction) + " " + str(elapsed)
        self.write_status_message(msg)
        
    def write_status_message(self, msg):
        ccrutils.write_status_message(msg)

        
