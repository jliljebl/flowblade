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
import atomicfile
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
import toolsencoding
import translations
import userfolders
import utils


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
    fraction, elapsed = msg.split(" ")
    return (fraction, elapsed)
    
def abort_render(session_id):
    ccrutils.abort_render(session_id)



# --------------------------------------------------- render thread launch
def main(root_path, session_id, xml_file_path, range_in, range_out, profile_desc):
    
    os.nice(10) # make user configurable
    
    ccrutils.prints_to_log_file("/home/janne/xmlheadless")
    print(session_id, xml_file_path, range_in, range_out, profile_desc)

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
    
    global _render_thread
    _render_thread = BlenderHeadlessRunnerThread(render_data, xml_file_path, range_in, range_out, profile_desc)
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

        if self.render_data.do_video_render == True:
            args_vals_list = toolsencoding.get_args_vals_list_for_render_data(self.render_data)
            profile = mltprofiles.get_profile_for_index(self.render_data.profile_index)
            
            producer = mlt.Producer(profile, str(self.xml_file_path))

            # Video clip consumer
            if self.render_data.save_internally == True:
                file_path = ccrutils.session_folder() +  "/" + appconsts.CONTAINER_CLIP_VIDEO_CLIP_NAME + self.render_data.file_extension
            else:
                file_path = self.render_data.render_dir +  "/" + self.render_data.file_name + self.render_data.file_extension
            print(file_path)
            consumer = renderconsumer.get_mlt_render_consumer(file_path, profile, args_vals_list)

            self.render_player = renderconsumer.FileRenderPlayer("", producer, consumer, self.range_in, self.range_out)
            self.render_player.wait_for_producer_end_stop = False
            self.render_player.start()

            while self.render_player.stopped == False:
                
                self.abort_requested()
                
                if self.abort == True:
                    self.render_player.shutdown()
                    print("Aborted.")
                    return
                
                fraction = self.render_player.get_render_fraction()
                self.render_update_callback(fraction)
                
                time.sleep(0.3)
                
        # Write out completed flag file.
        completed_msg_file = ccrutils.session_folder() + "/" + ccrutils.COMPLETED_MSG_FILE
        script_text = "##completed##" # let's put something in here
        with atomicfile.AtomicFileWriter(completed_msg_file, "w") as afw:
            script_file = afw.get_file()
            script_file.write(script_text)

    def abort_requested(self):
        abort_file = ccrutils.session_folder() + "/" + ccrutils.ABORT_MSG_FILE
        if os.path.exists(abort_file):
            self.abort = True
            print("Abort requested.")
            return True
        
        return False

    def render_update_callback(self, fraction):
        elapsed = time.monotonic() - self.start_time
        msg = str(fraction) + " " + str(elapsed)
        self.write_status_message(msg)
        
    def write_status_message(self, msg):
        try:
            status_msg_file = ccrutils.session_folder() + "/" + ccrutils.STATUS_MSG_FILE
            
            with atomicfile.AtomicFileWriter(status_msg_file, "w") as afw:
                script_file = afw.get_file()
                script_file.write(msg)
        except:
            pass # this failing because we can't get file access will show as progress hickup to user, we don't care

        
