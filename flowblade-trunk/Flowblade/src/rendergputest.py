"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2023 Janne Liljeblad.

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

"""
Module does render tests to find out which GPU encodings work on user system.
"""

try:
    import pgi
    pgi.install_as_gi()
except ImportError:
    pass
    
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib

try:
    import mlt7 as mlt
except:
    import mlt

import pickle
import subprocess
import sys
import time
import threading

import appconsts
import atomicfile
import editorpersistance
import editorstate
import renderconsumer
import respaths
import mltinit
import mltprofiles
import translations
import userfolders
import utils


CURRENT_TEST_RENDER_ARGS_VALS_LIST = "gpu_test_render.argsvalslist"
CURRENT_TEST_RENDER_OUT_FILE = "outfile"

test_thread = None

test_results = {}


def test_gpu_rendering_options(selector_update_func):
    test_runner_thread = GPUTestRunnerThread(selector_update_func)
    test_runner_thread.start()

def _update_encode_selector(selector_update_func):
    selector_update_func()


class GPUTestRunnerThread(threading.Thread):
    def __init__(self, selector_update_func):
        threading.Thread.__init__(self)
        self.selector_update_func = selector_update_func

    def run(self):
        profile = mltprofiles.get_default_profile()

        # NVENC_encs
        working_NVENC_encs = []
        for item in renderconsumer.NVENC_encs:
            name, enc_opt = item
            returncode = self._test_encoder_option(name, enc_opt)
            test_results[name] = returncode
            if returncode == 0:
                working_NVENC_encs.append((enc_opt.name, enc_opt))
            else:
                renderconsumer.remove_non_working_proxy_encodings(enc_opt.vcodec)

        if len(working_NVENC_encs) > 0:
            renderconsumer.categorized_encoding_options.insert(1, (translations.get_encoder_group_name(appconsts.PRESET_GROUP_NVENC), working_NVENC_encs))

        # VAAPI_encs
        working_VAAPI_encs = []
        for item in renderconsumer.VAAPI_encs:
            name, enc_opt = item
            returncode = self._test_encoder_option(name, enc_opt)
            test_results[name] = returncode
            if returncode == 0:
                working_VAAPI_encs.append((enc_opt.name, enc_opt))
            else:
                renderconsumer.remove_non_working_proxy_encodings(enc_opt.vcodec)
                
        if len(working_VAAPI_encs) > 0:
            renderconsumer.categorized_encoding_options.insert(1, (translations.get_encoder_group_name(appconsts.PRESET_GROUP_VAAPI), working_VAAPI_encs))

        print("GPU test results", test_results)
        
        if len(working_VAAPI_encs) > 0 or len(working_NVENC_encs) > 0:
            GLib.idle_add(_update_encode_selector, self.selector_update_func)

    def _test_encoder_option(self, name, enc_opt):

        # Create and write to disk argsvals list for test render.
        profile = mltprofiles.get_default_profile()
        args_vals_path = _get_test_render_args_vals_path()

        if enc_opt.quality_default_index != None:
            quality_option = enc_opt.quality_options[enc_opt.quality_default_index]
        else:
            quality_option = enc_opt.quality_options[0]

        args_vals_list = enc_opt.get_args_vals_tuples_list(profile, quality_option)

        with atomicfile.AtomicFileWriter(args_vals_path, "wb") as afw:
            item_write_file = afw.get_file()
            pickle.dump(args_vals_list, item_write_file)

        # Get unique string from enc name to save logs for all tests.
        enc_name = enc_opt.name.split(".")[0]
        enc_name = enc_name.replace(" ", "")
        enc_name = enc_name.replace("/", "")

        # Launch test render
        FLOG = open(userfolders.get_cache_dir() + "log_gputest_render_" + enc_name, 'w')

        process = subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladegputestrender"], stdin=FLOG, stdout=FLOG, stderr=FLOG)
        try:
            out, err = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            return -1
 
        return process.returncode


# ------------------------------------------------ TEST SUBPROCESS
def main(root_path):
    
    # called from .../launch/flowbladesinglerender script
    gtk_version = "%s.%s.%s" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    editorstate.gtk_version = gtk_version
    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"
    
    # Get XDG paths etc.
    userfolders.init()
    
    # Set paths.
    respaths.set_paths(root_path)

    # Load editor prefs and list of recent projects
    editorpersistance.load()

    mltinit.init_with_translations()
    
    global test_thread
    test_thread = GPUTestRenderThread()
    test_thread.start()

class GPUTestRenderThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):
        start = time.time()

        hidden_dir = userfolders.get_cache_dir()

        args_vals_list = utils.unpickle(_get_test_render_args_vals_path())

        profile = mltprofiles.get_default_profile()
        producer = _create_test_render_tractor(profile)

        render_path = _get_test_render_out_file_path_start() + ".mp4" # change hardcoded ".mp4" if needed

        consumer = renderconsumer.get_mlt_render_consumer(render_path, 
                                                          profile,
                                                          args_vals_list)

        # Get render range
        start_frame = 0
        end_frame = producer.get_length() - 1
        wait_for_stop_render = True
        
        # Create and launch render thread
        render_thread = renderconsumer.FileRenderPlayer(None, producer, consumer, start_frame, end_frame) # None == file name not needed this time when using FileRenderPlayer because callsite keeps track of things
        render_thread.wait_for_producer_end_stop = wait_for_stop_render
        render_thread.start()

        # Make sure that render thread is actually running before
        # testing render_thread.running value later
        while render_thread.has_started_running == False:
            time.sleep(0.05)

        while render_thread.running != False:
            time.sleep(0.1)

        end = time.time()
        print("render time:", str(end - start))

        render_thread.shutdown()

def _create_test_render_tractor(profile):
    # Create tractor and tracks
    tractor = mlt.Tractor()
    multitrack = tractor.multitrack()
    track0 = mlt.Playlist(profile)
    multitrack.connect(track0, 0)
    media_path = respaths.ROOT_PATH + "/res/gpu-test/gpu_test_clip.mp4"
    producer = mlt.Producer(profile, str(media_path)) 
    track0.insert(producer, 0, 0, 50)

    return tractor


# ------------------------------------------------ DISK DATA PATHS
def _get_test_render_args_vals_path():
    return userfolders.get_cache_dir() + CURRENT_TEST_RENDER_ARGS_VALS_LIST

def _get_test_render_out_file_path_start():
    return userfolders.get_cache_dir() + CURRENT_TEST_RENDER_OUT_FILE

