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
from os import listdir
from os.path import isfile, join
import pickle
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time

import appconsts
import atomicfile
import ccrutils
import editorpersistance
import editorstate
import gmicplayer
import mltenv
import mltfilters
import mltprofiles
import mlttransitions
import processutils
import renderconsumer
import respaths
import userfolders
import toolsencoding
import translations
import utils

_render_thread = None
_start_time = -1


# ----------------------------------------------------- module interface to render process with message files, used by main app
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
    step, fraction, elapsed = msg.split(" ")
    return (step, fraction, elapsed)
    
def abort_render(session_id):
    ccrutils.abort_render(session_id)


# --------------------------------------------------- render process
def main(root_path, session_id, project_path, range_in, range_out, profile_desc):

    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"

    ccrutils.prints_to_log_file("/home/janne/blenderrrender")

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
    
    log_path = GLib.get_user_cache_dir() + "/blenderrenderlog"
    FLOG = open(log_path, 'w')
    render_setup_script = respaths.ROOT_PATH + "/tools/blenderrendersetup.py"
    blender_launch = "/usr/bin/blender -b " + project_path + " -P " + render_setup_script

    global _start_time
    _start_time = time.monotonic()

    # Delete old frames
    rendered_frames_folder = ccrutils.rendered_frames_folder()
    for frame_file in os.listdir(rendered_frames_folder):
        file_path = os.path.join(rendered_frames_folder, frame_file)
        os.remove(file_path)
            
    p = subprocess.Popen(blender_launch, shell=True, stdin=FLOG, stdout=FLOG, stderr=FLOG, preexec_fn=os.setsid)

    manager_thread = ProgressPollingThread(range_in, range_out, p)
    manager_thread.start()
    
    p.wait()

    if manager_thread.abort == True:
        return

    render_data = ccrutils.get_render_data()

    # Render video
    if render_data.do_video_render == True:

        # Change file numbering to start from 0000 to please ffmpeg
        rendered_folder = ccrutils.rendered_frames_folder() + "/"

        files = [ f for f in listdir(rendered_folder) if isfile(join(rendered_folder,f)) ]
        files.sort(key=lambda var:[int(x) if x.isdigit() else x for x in re.findall(r'[^0-9]|[0-9]+', var)])

        number = 0
        for rendered_file in files:
            source_file = rendered_folder + rendered_file
            
            file_number = '{0:04d}'.format(number)
            dst_file = rendered_folder + "videoframe" + file_number + ".png"
            Path(source_file).rename(dst_file)
            
            number += 1
    
        # Render consumer
        args_vals_list = toolsencoding.get_args_vals_list_for_render_data(render_data)
        profile = mltprofiles.get_profile_for_index(render_data.profile_index) 
        
        if ccrutils.get_render_data().save_internally == True:
            file_path = ccrutils.session_folder() +  "/" + appconsts.CONTAINER_CLIP_VIDEO_CLIP_NAME + render_data.file_extension
        else:
            file_path = render_data.render_dir +  "/" + render_data.file_name + render_data.file_extension
    
        consumer = renderconsumer.get_mlt_render_consumer(file_path, profile, args_vals_list)
        
        # Render producer
        rendered_frames_folder = ccrutils.rendered_frames_folder()
        frames_info = gmicplayer.FolderFramesInfo(rendered_frames_folder)
        frame_file = frames_info.get_lowest_numbered_file()
        
        if editorstate.mlt_version_is_equal_or_greater("0.8.5"):
            resource_name_str = utils.get_img_seq_resource_name(frame_file, True)
        else:
            resource_name_str = utils.get_img_seq_resource_name(frame_file, False)
        resource_path = rendered_frames_folder + "/" + resource_name_str
        producer = mlt.Producer(profile, str(resource_path))

        frames_length = len(os.listdir(rendered_frames_folder))

        render_player = renderconsumer.FileRenderPlayer("", producer, consumer, 0, frames_length - 1)
        render_player.wait_for_producer_end_stop = False
        render_player.start()

        abort = False
        while render_player.stopped == False and abort == False:
            
            abort = ccrutils.abort_requested()
            if abort == True:
                render_player.shutdown()
                return
            else:
                fraction = render_player.get_render_fraction()
                elapsed = time.monotonic() - _start_time
                msg = "2 " + str(fraction) + " " + str(elapsed)
                ccrutils.write_status_message(msg)
            
            time.sleep(1.0)
    
    ccrutils.write_completed_message()



# ------------------------------------------------------------ poll thread for Blender rendering happening in different process.
class ProgressPollingThread(threading.Thread):
    
    def __init__(self, range_in, range_out, process):
        self.range_in = int(range_in)
        self.range_out = int(range_out)
        self.process = process
        self.abort = False
        threading.Thread.__init__(self)

    def run(self):
        completed = False
        
        while self.abort == False and completed == False:
            self.check_abort_request()
            
            length = self.range_out - self.range_in
            written_frames_count = self.get_written_frames_count()
            fraction = float(written_frames_count) / float(length)
            self.update_status(fraction)
            
            if written_frames_count == length:
                completed = True
            
            time.sleep(0.5)
        
        if ccrutils.get_render_data().do_video_render == False:
            ccrutils.write_completed_message()
     
    def update_status(self, fraction):
        elapsed = time.monotonic() - _start_time
        msg = "1 " + str(fraction) + " " + str(elapsed)
        ccrutils.write_status_message(msg)

    def get_written_frames_count(self):
        return len(os.listdir(ccrutils.rendered_frames_folder()))

    def check_abort_request(self):
        abort_request = ccrutils.abort_requested()
        if abort_request == True:
            self.process.kill()
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM) 
            self.abort = True

