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

_tline_sync_data = None # Compound clip and tline sync functions can't pass the same data througn clapperless so we use this global to save data for  tline sync that needs more data

class ClapperlesLaunchThread(threading.Thread):
    def __init__(self, video_file, audio_file, completed_callback):
        threading.Thread.__init__(self)
        self.video_file = video_file
        self.audio_file = audio_file
        self.completed_callback = completed_callback
        
    def run(self):
        _write_offsets(self.video_file, self.audio_file, self.completed_callback)

# ------------------------------------------------------- module funcs
def _write_offsets(video_file_path, audio_file_path, completed_callback):
    print "Starting clapperless analysis..."
    fps = str(int(utils.fps() + 0.5))
    idstr = _get_offset_file_idstr(video_file_path, audio_file_path)
    print fps, idstr
    FLOG = open(utils.get_hidden_user_dir_path() + "log_clapperless", 'w')
    
    # clapperless.py computes offsets and writes them to file clapperless.OFFSETS_DATA_FILE
    p = subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladeclapperless", video_file_path, audio_file_path, "--rate", fps, "--idstr", idstr], stdin=FLOG, stdout=FLOG, stderr=FLOG)
    p.wait()
    
    # Offsets are now available
    GLib.idle_add(completed_callback, (video_file_path, audio_file_path, idstr))

def _get_offset_file_idstr(file_1, file_2):
    # Create unique file path in hidden render folder
    folder = editorpersistance.prefs.render_folder
    return md5.new(file_1 + file_2).hexdigest()
    
def _read_offsets(idstr):
    offsets_file = utils.get_hidden_user_dir_path() + clapperless.OFFSETS_DATA_FILE + "_"+ idstr
    with open(offsets_file) as f:
        file_lines = f.readlines()
    file_lines = [x.rstrip("\n") for x in file_lines]
    
    _files_offsets = {}
    for line in file_lines:
        tokens = line.split(" ")
        _files_offsets[tokens[0]] = tokens[1]
    
    os.remove(offsets_file)

    return _files_offsets


# ------------------------------------------------------- tline audio sync
def init_select_tline_sync_clip(popup_data):

    clip, track, item_id, x = popup_data
    frame = tlinewidgets.get_frame(x)
    child_index = current_sequence().get_clip_index(track, frame)

    if not (track.clips[child_index] == clip):
        # This should never happen 
        print "big fu at init_select_tline_sync_clip(...)"
        return

    gdk_window = gui.tline_display.get_parent_window();
    gdk_window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.TCROSS))
    editorstate.edit_mode = editorstate.SELECT_TLINE_SYNC_CLIP

    global _tline_sync_data
    _tline_sync_data = (clip, child_index, track)

def _get_sync_tline_clip(event, frame):
    action_origin_clip, action_origin_clip_index, action_origin_clip_track = _tline_sync_data
    sync_track = tlinewidgets.get_track(event.y)

    if sync_track == None:
        return None
        
    if sync_track == action_origin_clip_track:
        dialogutils.warning_message(_("Audio Sync parent clips must be on differnt tracks "), 
                                _("Selected audio sync clip is on the sametrack as the sync action origin clip."),
                                gui.editor_window.window,
                                True)
        return None

    sync_clip_index = current_sequence().get_clip_index(sync_track, frame)
    if sync_clip_index == -1:
        return None

    return sync_track.clips[sync_clip_index]
    
def select_sync_clip_mouse_pressed(event, frame):
    sync_clip = _get_sync_tline_clip(event, frame)

    if sync_clip == None:
        return # selection wasn't good

    sync_track =  tlinewidgets.get_track(event.y)
    sync_clip_index = sync_track.clips.index(sync_clip)

    global _tline_sync_data
    action_origin_clip, action_origin_clip_index, action_origin_clip_track = _tline_sync_data

    # TImeline media offset for clips
    sync_clip_start_in_tline = sync_track.clip_start(sync_clip_index)
    action_origin_start_in_tline = action_origin_clip_track.clip_start(action_origin_clip_index)
    
    clip_tline_media_offset = (sync_clip_start_in_tline - sync_clip.clip_in) - (action_origin_start_in_tline - action_origin_clip.clip_in)
    
    gdk_window = gui.tline_display.get_parent_window();
    gdk_window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR))
    
    _tline_sync_data = clip_tline_media_offset
    
    # This or GUI freezes, we really can't do Popen.wait() in a Gtk thread
    clapperless_thread = ClapperlesLaunchThread(action_origin_clip.path, sync_clip.path, _tline_sync_offsets_complete)
    clapperless_thread.start()
    

   
    #global _sync_selection_data
   # _sync_selection_data = None

    # Edit consumes selection
    movemodes.clear_selected_clips()

    updater.repaint_tline()

def _tline_sync_offsets_complete(data):
    print "Clapperless done for tline sync"

    global _tline_sync_data
    clip_tline_media_offset = _tline_sync_data 
    _tline_sync_data = None

    file_path_1, file_path_2, idstr = data
    files_offsets = _read_offsets(idstr)
    sync_data = (files_offsets, clip_tline_media_offset, data)
    
    dialogs.tline_audio_sync_dialog(_do_tline_audio_sync, sync_data)

def _do_tline_audio_sync(dialog, response_id, data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return
        
    dialog.destroy()
        
# ------------------------------------------------------- compound clip audio sync
def create_audio_sync_compound_clip():
    selection = gui.media_list_view.get_selected_media_objects()
    print selection
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
        print  "2 video file"
        #return


    # This or GUI freezes, we really can't do Popen.wait() in a Gtk thread
    clapperless_thread = ClapperlesLaunchThread(video_file.path, audio_file.path, _compound_offsets_complete)
    clapperless_thread.start()
    
def _compound_offsets_complete(data):
    print "Clapperless done for compound clip"
    print data
    video_file_path, audio_file_path, idstr = data
    files_offsets = _read_offsets(idstr)
    sync_data = (files_offsets, data)

    # lets's just set default name to something unique-ish 
    default_name = _("SYNC_CLIP_") +  str(datetime.date.today()) + "_" + time.strftime("%H%M%S") + ".xml"
    dialogs.compound_clip_name_dialog(_do_create_sync_compound_clip, default_name, _("Save Sync Compound Clip XML"), sync_data)
    
def _do_create_sync_compound_clip(dialog, response_id, data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    sync_data, name_entry = data
    files_offsets, clips = sync_data
    video_file, audio_file, idstr = clips
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
    offset = files_offsets[audio_file]
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
