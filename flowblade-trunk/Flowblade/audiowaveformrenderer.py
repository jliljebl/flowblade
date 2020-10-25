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
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Modules handles creating and caching audio waveform images for clips.
"""

import locale
import mlt
import os
import pickle
import subprocess
import sys
import threading

import gi
gi.require_version('Gdk', '3.0') 
from gi.repository import Gdk

import appconsts
import atomicfile
import editorpersistance
import editorstate
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import processutils
import renderconsumer
import respaths
import translations
import updater
import userfolders
import utils

LEFT_CHANNEL = "_audio_level.0"
RIGHT_CHANNEL = "_audio_level.1"

FILE_SEPARATOR = "#&#file:"

_waveforms = {} # Memory cache for waveform data
_queued_waveform_renders = [] # Media queued for render during one timeline repaint
_render_already_requested = [] # Files that have been sent to rendering since last project load


# ------------------------------------------------- waveform cache
def clear_cache():
    global _waveforms, _queued_waveform_renders, _render_already_requested

    _waveforms = {}
    _queued_waveform_renders = []
    _render_already_requested = []

def get_waveform_data(clip):
    # Return from memory if present
    global _waveforms
    try:
        waveform = _waveforms[clip.path]
        return waveform
    except:
        pass
        
    # Load from disk if found, otherwise queue for levels render
    levels_file_path = _get_levels_file_path(clip.path, editorstate.PROJECT().profile)
    if os.path.isfile(levels_file_path):
        if os.path.getsize(levels_file_path) == 0:
             print( "Size zero Audio levels file, this is error!", levels_file_path)
        waveform = utils.unpickle(levels_file_path)
        _waveforms[clip.path] = waveform
        return waveform
    else:
        global _queued_waveform_renders
        _queued_waveform_renders.append(clip.path)
        return None
    
# ------------------------------------------------- launching render
def launch_queued_renders():
    # Render files that were not found when timeline was displayed
    global _queued_waveform_renders
    if len(_queued_waveform_renders) == 0:
        return

    launch_audio_levels_rendering(_queued_waveform_renders)
    _queued_waveform_renders = []

def launch_audio_levels_rendering(file_names):

    # Only render audio levels for media that does not have existing levels file
    rendered_media = ""

    for media_file in file_names:
        levels_file_path = _get_levels_file_path(media_file, editorstate.PROJECT().profile)
        if os.path.isfile(levels_file_path):
            continue
        else:
            global _render_already_requested
            if not (media_file in _render_already_requested):
                _render_already_requested.append(media_file)
                rendered_media = rendered_media + FILE_SEPARATOR + media_file

    if rendered_media == "":
        return
    
    profile_desc = editorstate.PROJECT().profile_desc
    
    # This is called from GTK thread, so we need to launch process from another thread to 
    # clean-up properly and not block GTK thread/GUI
    global single_render_launch_thread
    single_render_launch_thread = AudioRenderLaunchThread(rendered_media, profile_desc)
    single_render_launch_thread.start()

def _get_levels_file_path(media_file_path, profile):
    return userfolders.get_cache_dir() + appconsts.AUDIO_LEVELS_DIR + utils.get_unique_name_for_audio_levels_file(media_file_path, profile)
 

class AudioRenderLaunchThread(threading.Thread):
    def __init__(self, rendered_media, profile_desc):
        threading.Thread.__init__(self)
        self.rendered_media = rendered_media
        self.profile_desc = profile_desc

    def run(self):
        # Launch render process and wait for it to end
        FLOG = open(userfolders.get_cache_dir() + "log_audio_levels_render", 'w')
        # Sep-2018 - SvdB - Added self. to be able to access the thread through 'process'
        self.process = subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladeaudiorender", \
                  self.rendered_media, self.profile_desc, respaths.ROOT_PATH], \
                  stdin=FLOG, stdout=FLOG, stderr=FLOG)
        self.process.wait()
        
        Gdk.threads_enter()
        updater.repaint_tline()
        Gdk.threads_leave()


# --------------------------------------------------------- rendering
def main():
    # Set paths.
    root_path = sys.argv[3]
    respaths.set_paths(root_path)

    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"
    
    # Set folders paths
    userfolders.init()
    
    # Load editor prefs and list of recent projects
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

    profile_desc = sys.argv[2]
    profile = mltprofiles.get_profile(profile_desc)
        
    files_paths = sys.argv[1]
    files_paths = files_paths.lstrip(FILE_SEPARATOR)
    
    files = files_paths.split(FILE_SEPARATOR)

    for f in files:
       t = WaveformCreator(f, profile_desc)
       t.start()
       t.join()


class WaveformCreator(threading.Thread):    
    def __init__(self, clip_path, profile_desc):
        threading.Thread.__init__(self)
        self.clip_path = clip_path
        profile = mltprofiles.get_profile(profile_desc)
        self.temp_clip = self._get_temp_producer(clip_path, profile)
        self.file_cache_path =_get_levels_file_path(clip_path, profile)
        self.last_rendered_frame = 0

    def run(self):
        frame_levels = [None] * self.clip_media_length 

        for frame in range(0, len(frame_levels)):
            self.temp_clip.seek(frame)
            mlt.frame_get_waveform(self.temp_clip.get_frame(), 10, 50)
            val = self.levels.get(RIGHT_CHANNEL)
            if val == None:
                val = 0.0
            frame_levels[frame] = float(val)
            self.last_rendered_frame = frame

        with atomicfile.AtomicFileWriter(self.file_cache_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(frame_levels, write_file)

    def _get_temp_producer(self, clip_path, profile):
        temp_producer = mlt.Producer(profile, str(clip_path))
        channels = mlt.Filter(profile, "audiochannels")
        converter = mlt.Filter(profile, "audioconvert")
        self.levels = mlt.Filter(profile, "audiolevel")
        temp_producer.attach(channels)
        temp_producer.attach(converter)
        temp_producer.attach(self.levels)
        temp_producer.path = clip_path
        self.clip_media_length = temp_producer.get_length()

        return temp_producer




