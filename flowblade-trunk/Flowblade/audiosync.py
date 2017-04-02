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

"""
Application module.

Handles application initialization, shutdown, opening projects, autosave and changing
sequences.
"""
import datetime
import mlt
import subprocess
import sys
import time
import threading

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import GLib
from gi.repository import Gtk, Gdk, GdkPixbuf

import appconsts
import clapperless
import dialogs
from editorstate import PROJECT
import gui
import projectaction
import renderconsumer
import respaths
import utils


_files_offsets = {}


class ClapperlesLaunchThread(threading.Thread):
    def __init__(self, video_file, audio_file, completed_callback):
        threading.Thread.__init__(self)
        self.video_file = video_file
        self.audio_file = audio_file
        self.completed_callback = completed_callback
        
    def run(self):
        _write_offsets(self.video_file, self.audio_file, self.completed_callback)


# ------------------------------------------------ interface
def create_audio_sync_compound_clip():
    selection = gui.media_list_view.get_selected_media_objects()
    if len(selection) != 2:
        return

    video_file = selection[0].media_file
    audio_file = selection[1].media_file
    
    if video_file.type == appconsts.VIDEO and audio_file.type == appconsts.AUDIO:
        pass
    elif video_file.type == appconsts.AUDIO and audio_file.type == appconsts.VIDEO:
        video_file, audio_file = audio_file, video_file
    else:
        # INFOWINDOW
        return

    print "kkkkkkk"
    # This or GUI freezes, we really can't do Popen.wait() in a Gtk thread
    clapperless_thread = ClapperlesLaunchThread(video_file.path, audio_file.path, _compound_offsets_complete)
    clapperless_thread.start()
        
def create_audio_sync_group():
    pass


# ------------------------------------------------------- modiule funcs
def _write_offsets(video_file, audio_file, completed_callback):
    print "Starting clapperless analysis..."
    fps = str(int(utils.fps() + 0.5))
    print fps
    FLOG = open(utils.get_hidden_user_dir_path() + "log_clapperless", 'w')
    p = subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladeclapperless", video_file, audio_file, "--rate", fps], stdin=FLOG, stdout=FLOG, stderr=FLOG)
    p.wait()
    
    GLib.idle_add(completed_callback, (video_file, audio_file))


def _read_offsets():
    offsets_file = utils.get_hidden_user_dir_path() + clapperless.OFFSETS_DATA_FILE
    with open(offsets_file) as f:
        file_lines = f.readlines()
    file_lines = [x.rstrip("\n") for x in file_lines]
    
    global _files_offsets
    _files_offsets = {}
    for line in file_lines:
        tokens = line.split(" ")
        _files_offsets[tokens[0]] = tokens[1]
    
    print _files_offsets

def _compound_offsets_complete(data):
    print "Clapperless done"
    

    
    _read_offsets()

    # lets's just set something unique-ish 
    default_name = _("SYNC_CLIP_") +  str(datetime.date.today()) + "_" + time.strftime("%H%M%S") + ".xml"
    dialogs.export_xml_compound_clip_dialog(_do_create_sync_compound_clip, default_name, _("Save Sync Compound Clip XML"), data)


def _do_create_sync_compound_clip(dialog, response_id, data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    video_file, audio_file = data
    
    filenames = dialog.get_filenames()
    dialog.destroy()
    
    print filenames[0]
        
    # Create tractor
    tractor = mlt.Tractor()
    multitrack = tractor.multitrack()
    track_video = mlt.Playlist()
    track_audio = mlt.Playlist()
    multitrack.connect(track_video, 0)
    multitrack.connect(track_audio, 0)
    
    offset = _files_offsets[audio_file]
    video_clip = mlt.Producer(PROJECT().profile, str(video_file)) 
    audio_clip = mlt.Producer(PROJECT().profile, str(audio_file)) 
    print audio_file, offset
    
    """
    # Add video clip 
    if offset > 0:
        track_video.append(clip, clip.clip_in, clip.clip_out)
    elif < 0:
        
    else:
    """
    
    track_video.append(video_clip, 0, video_clip.get_length() - 1)
    track_audio.append(audio_clip, 0, audio_clip.get_length() - 1)
    
    
    render_player = renderconsumer.XMLCompoundRenderPlayer(filenames[0], _sync_compound_clip_render_done_callback, tractor)
    render_player.start()

def _sync_compound_clip_render_done_callback(filename):
    print filename, "iiiiiiiii"
    #projectaction.open_file_names([filename])

