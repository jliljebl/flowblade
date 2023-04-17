
try:
    import pgi
    pgi.install_as_gi()
except ImportError:
    pass
    
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

try:
    import mlt7 as mlt
except:
    import mlt

import pickle
import subprocess
import sys
import time
import threading

import atomicfile
import editorpersistance
import editorstate
import renderconsumer
import respaths
import mltinit
import mltprofiles
import userfolders
import utils

CURRENT_TEST_RENDER_ARGS_VALS_LIST = "gpu_test_render.argsvalslist"
CURRENT_TEST_RENDER_OUT_FILE = "outfile"

test_thread = None

def test_gpu_rendering_options():
    test_runner_thread = GPUTestRunnerThread()
    test_runner_thread.start()



    #if len(NVENC_encs) > 0 and H_264_NVENC_AVAILABLE == True: # we are assuming that hevc_nvenc is also available if this is
    #    categorized_encoding_options.append((translations.get_encoder_group_name(PRESET_GROUP_NVENC), NVENC_encs))
    #if len(VAAPI_encs) > 0 and H_264_VAAPI_AVAILABLE == True:
    #    categorized_encoding_options.append((translations.get_encoder_group_name(PRESET_GROUP_VAAPI), VAAPI_encs))
    


class GPUTestRunnerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        profile = mltprofiles.get_default_profile()
        
        print("NVENC_encs")
        for item in renderconsumer.NVENC_encs:
            name, enc_opt = item
            #print(name)

            args_vals_path = _get_test_render_args_vals_path()
            
            #print(enc_opt.quality_options, enc_opt.quality_default_index)
            if enc_opt.quality_default_index != None:
                quality_option = enc_opt.quality_options[enc_opt.quality_default_index]
            else:
                quality_option = enc_opt.quality_options[0]
            args_vals_list = enc_opt.get_args_vals_tuples_list(profile, quality_option)

            with atomicfile.AtomicFileWriter(args_vals_path, "wb") as afw:
                item_write_file = afw.get_file()
                pickle.dump(args_vals_list, item_write_file)

            FLOG = open(userfolders.get_cache_dir() + "log_gputest_render", 'w')
            
            process = subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladegputestrender"], stdin=FLOG, stdout=FLOG, stderr=FLOG)
            out, err = process.communicate()

            print(name, process.returncode)


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
        self.running = False
        hidden_dir = userfolders.get_cache_dir()

        args_vals_list = utils.unpickle(_get_test_render_args_vals_path())
        print(args_vals_list)
        profile = mltprofiles.get_default_profile()
        producer = _create_test_render_tractor(profile)

        render_path = _get_test_render_out_file_path_start() + ".mp4" # change hardcoded ".mp4" if needed

        consumer = renderconsumer.get_mlt_render_consumer(render_path, 
                                                          profile,
                                                          args_vals_list)

        # Get render range
        start_frame = 0
        end_frame = producer.get_length()
        wait_for_stop_render = True
        
        # Create and launch render thread
        render_thread = renderconsumer.FileRenderPlayer(None, producer, consumer, start_frame, end_frame) # None == file name not needed this time when using FileRenderPlayer because callsite keeps track of things
        render_thread.wait_for_producer_end_stop = wait_for_stop_render
        render_thread.start()

        # Make sure that render thread is actually running before
        # testing render_thread.running value later
        while render_thread.has_started_running == False:
            time.sleep(0.05)

        # View update loop
        self.running = True

        while self.running:
            if render_thread.running == False: # Rendering has reached end
                self.running = False

            time.sleep(0.1)
                
        render_thread.shutdown()

def _get_test_render_args_vals_path():
    return userfolders.get_cache_dir() + CURRENT_TEST_RENDER_ARGS_VALS_LIST

def _get_test_render_out_file_path_start():
    return userfolders.get_cache_dir() + CURRENT_TEST_RENDER_OUT_FILE
    
def _create_test_render_tractor(profile):
    # Create tractor and tracks
    tractor = mlt.Tractor()
    multitrack = tractor.multitrack()
    track0 = mlt.Playlist()
    multitrack.connect(track0, 0)
    producer = mlt.Producer(profile, "colour", "#000000")
    track0.insert(producer, 0, 0, 50)

    return tractor
    
#def _kill_
    

