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
import md5
import mlt
import os
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
import editorpersistance
import editorstate
from editorstate import PROJECT
from editorstate import current_sequence
import gui
import movemodes
import projectaction
import renderconsumer
import respaths
import tlinewidgets
import updater
import utils


_files_offsets = {}
_parent_selection_data = None

class ClapperlesLaunchThread(threading.Thread):
    def __init__(self, video_file, audio_file, completed_callback):
        threading.Thread.__init__(self)
        self.video_file = video_file
        self.audio_file = audio_file
        self.completed_callback = completed_callback
        
    def run(self):
        _write_offsets(self.video_file, self.audio_file, self.completed_callback)


# ------------------------------------------------ compound clip interface
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
        # 2 video files???
        # INFOWINDOW
        return

    # This or GUI freezes, we really can't do Popen.wait() in a Gtk thread
    clapperless_thread = ClapperlesLaunchThread(video_file.path, audio_file.path, _compound_offsets_complete)
    clapperless_thread.start()
        
def create_audio_sync_group():
    pass

# ------------------------------------------------ compound clip interface
def init_select_tline_sync_clip(popup_data):
    print "jdjdjdjdjd"
    clip, track, item_id, x = popup_data
    frame = tlinewidgets.get_frame(x)
    child_index = current_sequence().get_clip_index(track, frame)

    if not (track.clips[child_index] == clip):
        # This should never happen 
        print "big fu at _init_select_master_clip(...)"
        return

    gdk_window = gui.tline_display.get_parent_window();
    gdk_window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.TCROSS))
    editorstate.edit_mode = editorstate.SELECT_TLINE_SYNC_CLIP
    global _parent_selection_data
    _parent_selection_data = (clip, child_index, track)

def select_sync_clip_mouse_pressed(event, frame):
    #_set_sync_parent_clip(event, frame)
    
    gdk_window = gui.tline_display.get_parent_window();
    gdk_window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR))
   
    global _parent_selection_data
    _parent_selection_data = None

    # Edit consumes selection
    movemodes.clear_selected_clips()

    updater.repaint_tline()
    
# ------------------------------------------------------- module funcs
def _write_offsets(video_file, audio_file, completed_callback):
    print "Starting clapperless analysis..."
    fps = str(int(utils.fps() + 0.5))
    print fps
    FLOG = open(utils.get_hidden_user_dir_path() + "log_clapperless", 'w')
    
    # clapperless.py computes offsets and writes them to file clapperless.OFFSETS_DATA_FILE
    p = subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladeclapperless", video_file, audio_file, "--rate", fps], stdin=FLOG, stdout=FLOG, stderr=FLOG)
    p.wait()
    
    # Offsets are now available
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
    
    #print _files_offsets

def _compound_offsets_complete(data):
    print "Clapperless done"

    _read_offsets()

    # lets's just set default name to something unique-ish 
    default_name = _("SYNC_CLIP_") +  str(datetime.date.today()) + "_" + time.strftime("%H%M%S") + ".xml"
    dialogs.compound_clip_name_dialog(_do_create_sync_compound_clip, default_name, _("Save Sync Compound Clip XML"), data)

def _do_create_sync_compound_clip(dialog, response_id, data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    clips, name_entry = data
    video_file, audio_file = clips
    media_name = name_entry.get_text()
    
    dialog.destroy()
    
    # Create unique file path in hidden render folder
    folder = editorpersistance.prefs.render_folder
    uuid_str = md5.new(str(os.urandom(32))).hexdigest()
    write_file = folder + "/"+ uuid_str + ".xml"
    
    # Create tractor
    tractor = mlt.Tractor()
    multitrack = tractor.multitrack()
    track_video = mlt.Playlist()
    track_audio = mlt.Playlist()
    track_audio.set("hide", 1) # video off, audio on as mlt "hide" value
    multitrack.connect(track_audio, 0)
    multitrack.connect(track_video, 0)

    # Create clips
    video_clip = mlt.Producer(PROJECT().profile, str(video_file)) 
    audio_clip = mlt.Producer(PROJECT().profile, str(audio_file))
    
    # Get offset
    offset = _files_offsets[audio_file]
    print audio_file, offset
    
    # Add clips
    if offset > 0:
        offset_frames = int(float(offset) + 0.5)
        print "plus"
        track_video.append(video_clip, 0, video_clip.get_length() - 1)
        track_audio.insert_blank(0, offset_frames)
        track_audio.append(audio_clip, 0, audio_clip.get_length() - 1)
    elif offset < 0:
        offset_frames = int(float(offset) - 0.5)
        print "miinus"
        track_video.insert_blank(0, offset_frames)
        track_video.append(video_clip, 0, video_clip.get_length() - 1)
        track_audio.append(audio_clip, 0, audio_clip.get_length() - 1)
    else:
        track_video.append(video_clip, 0, video_clip.get_length() - 1)
        track_audio.append(audio_clip, 0, audio_clip.get_length() - 1)

    # render MLT XML, callback in projectaction.py creates media object
    render_player = renderconsumer.XMLCompoundRenderPlayer(write_file, media_name, projectaction._xml_compound_render_done_callback, tractor)
    render_player.start()
