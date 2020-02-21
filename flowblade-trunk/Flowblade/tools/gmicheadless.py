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
    
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import locale
import mlt
import os
import subprocess
import sys
import threading
import time

import appconsts
import editorstate
import editorpersistance
import gmicplayer
import mltfilters
import mltenv
import mltprofiles
import mlttransitions
import processutils
import renderconsumer
import respaths
import translations
import userfolders

_session_folder = None
_clip_frames_folder = None
_gmic_version = None


def main(root_path, session_id, script, clip_path, range_in, range_out, profile_desc):
    
    os.nice(10)
    
    prints_to_log_file("/home/janne/gmicheadless")
    print(session_id, script, clip_path, range_in, range_out, profile_desc)

    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"

    # Set paths.
    respaths.set_paths(root_path)

    # Check G'MIC version
    global _gmic_version
    _gmic_version = get_gmic_version()
    if _gmic_version == 2:
        respaths.set_gmic2(root_path)

    userfolders.init()
    editorpersistance.load()

    global _session_folder, _clip_frames_folder
    _session_folder = userfolders.get_data_dir() + appconsts.CONTAINER_CLIPS_DIR +  "/" + session_id
    _clip_frames_folder = _session_folder + "/clip_frames"

    # Init gmic session dirs
    if not os.path.exists(_session_folder):
        os.mkdir(_session_folder)
    if not os.path.exists(_clip_frames_folder):
        os.mkdir(_clip_frames_folder)

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

    # Launch server
    DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()
    global _dbus_service
    _dbus_service = GMicHeadlessDBUSService(loop, session_id, script, clip_path, range_in, range_out, profile_desc)
    print("tline render service running")
    loop.run()

def get_gmic_version():
    gmic_ver = 1
    cmd = "gmic -version"
    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    tokens = output.split()
    clended = []
    for token in tokens:
        token = token.decode("utf-8")
        str1 = token.replace('.','')
        str2 = str1.replace(',','')
        if str2.isdigit(): # this is based on assumtion that str2 ends up being number like "175" or 215" etc. only for version number token
            if str2[0] == '2':
                gmic_ver = 2

    return gmic_ver




class GMicHeadlessDBUSService(dbus.service.Object):
    
    def __init__(self, loop, session_id, script, clip_path, range_in, range_out, profile_desc):
        bus_name = dbus.service.BusName('flowblade.movie.editor.gmicheadless', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, '/flowblade/movie/editor/gmicheadless/' + session_id)
        self.main_loop = loop

        self.render_runner_thread = GMicHeadlessRunnerThread(self, script, clip_path, range_in, range_out, profile_desc)
        self.render_runner_thread.start()
        
    @dbus.service.method('flowblade.movie.editor.gmicheadless')
    def render_update_clips(self, sequence_xml_path, segments_paths, segments_ins, segments_outs, profile_name):
        print(sequence_xml_path, profile_name)

    def shutdown(self):
        print("GMicHeadlessDBUSService shutdown")
        self.remove_from_connection()
        self.main_loop.quit()
        

class GMicHeadlessRunnerThread(threading.Thread):
    """
    SINGLE THREADED RENDERING, SHOULD WE GET MULTIPLE PROCESSES GOING FOR MULTIPLE CLIPS LATER IN MODERN MULTICORE MACHINES?
    """
    def __init__(self, dbus_obj, script, clip_path, range_in, range_out, profile_desc):
        threading.Thread.__init__(self)
        self.dbus_obj = dbus_obj
        self.script_path = script
        self.clip_path = clip_path
        self.range_in = int(range_in)
        self.range_out = int(range_out)
        self.length = self.range_out - self.range_in + 1
        self.profile_desc = profile_desc
        self.aborted = False

    def run(self):
        self.render_player = None
        self.frames_range_writer = None
        
        self.abort = False
        self.script_renderer = None
       
        frame_name = "frame"
        profile = mltprofiles.get_profile(self.profile_desc)

        # Delete old preview frames
        for frame_file in os.listdir(_clip_frames_folder):
            file_path = os.path.join(_clip_frames_folder, frame_file)
            os.remove(file_path)
            
        self.frames_range_writer = gmicplayer.FramesRangeWriter(self.clip_path, self.frames_update, profile)
        self.frames_range_writer.write_frames(_clip_frames_folder + "/", frame_name, self.range_in, self.range_out)

        if self.abort == True:
            return

        script_file = open(self.script_path)
        user_script = script_file.read()
        print(user_script)
        while len(os.listdir(_clip_frames_folder)) != self.length:
            print("WAITING")
            time.sleep(0.5)
        
        # Render frames with gmic script
        self.script_renderer = gmicplayer.FolderFramesScriptRenderer(   user_script, 
                                                                        _clip_frames_folder,
                                                                        _session_folder + "/",
                                                                        frame_name,
                                                                        self.script_render_update_callback, 
                                                                        self.script_render_output_callback)
        self.script_renderer.write_frames()

        self.dbus_obj.shutdown()
        """
        # Render video
        if _window.encode_check.get_active() == True:
            # Render consumer
            args_vals_list = toolsencoding.get_args_vals_list_for_render_data(_render_data)
            profile = mltprofiles.get_profile_for_index(_current_profile_index) 
            file_path = _render_data.render_dir + "/" +  _render_data.file_name  + _render_data.file_extension
            
            consumer = renderconsumer.get_mlt_render_consumer(file_path, profile, args_vals_list)
            
            # Render producer
            frame_file = out_folder + frame_name + "_0000.png"
            if editorstate.mlt_version_is_equal_or_greater("0.8.5"):
                resource_name_str = utils.get_img_seq_resource_name(frame_file, True)
            else:
                resource_name_str = utils.get_img_seq_resource_name(frame_file, False)
            resource_path = out_folder + "/" + resource_name_str
            producer = mlt.Producer(profile, str(resource_path))

            self.render_player = renderconsumer.FileRenderPlayer("", producer, consumer, 0, len(clip_frames) - 1)
            self.render_player.wait_for_producer_end_stop = False
            self.render_player.start()

            while self.render_player.stopped == False:

                if self.abort == True:
                    return
                
                fraction = self.render_player.get_render_fraction()
                update_info = _("Rendering video, ") + str(int(fraction * 100)) + _("% done")
                
                Gdk.threads_enter()
                _window.render_percentage.set_markup("<small>" + update_info + "</small>")
                _window.render_progress_bar.set_fraction(fraction)
                Gdk.threads_leave()
                
                time.sleep(0.3)

        Gdk.threads_enter()
        _window.render_percentage.set_markup("<small>" + _("Render complete!") + "</small>")
        self.set_render_stopped_gui_state()
        Gdk.threads_leave()
        """
        
    def frames_update(self, frame):
        print(frame)
        
    def script_render_update_callback(self, frame_count):
        pass

    def script_render_output_callback(self, p, out):
        #Gdk.threads_enter()
        #_window.out_view.get_buffer().set_text(out + "Return code:" + str(p.returncode))
        if p.returncode != 0:
            pass
            
# ---- Debug helper
def prints_to_log_file(log_file):
    so = se = open(log_file, 'w', buffering=1)

    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
        
