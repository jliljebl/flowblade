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

import mlt
import os
import pickle
import threading
import time

from gi.repository import Gtk, Gdk

import appconsts
import dialogutils
from editorstate import PROJECT
import gui
import guiutils
import updater
import userfolders
import utils

# Frame level value cache for audio levels
# path -> list of frame levels
frames_cache = {}

waveform_thread = None

LEFT_CHANNEL = "_audio_level.0"
RIGHT_CHANNEL = "_audio_level.1"

# ------------------------------------------------- waveforms
def set_waveform_displayer_clip_from_popup(data):
    clip, track, item_id, item_data = data

    global frames_cache
    if clip.path in frames_cache:
        frame_levels = frames_cache[clip.path]
        clip.waveform_data = frame_levels
        updater.repaint_tline()
        return

    cache_file_path = userfolders.get_cache_dir() + appconsts.AUDIO_LEVELS_DIR + _get_unique_name_for_media(clip.path)
    if os.path.isfile(cache_file_path):
        f = open(cache_file_path)
        frame_levels = pickle.load(f)
        frames_cache[clip.path] = frame_levels
        clip.waveform_data = frame_levels
        updater.repaint_tline()
        return

    progress_bar = Gtk.ProgressBar()
    title = _("Audio Levels Data Render")
    text = "<b>Media File: </b>" + clip.path
    dialog = _waveform_render_progress_dialog(_waveform_render_abort, title, text, progress_bar, gui.editor_window.window)
    dialog.progress_bar = progress_bar
    
    global waveform_thread
    waveform_thread = WaveformCreator(clip, track.height, dialog)
    waveform_thread.start()

def _waveform_render_abort(dialog, response_id):
    if waveform_thread != None:
        waveform_thread.abort_rendering()
        
def _waveform_render_stop(dialog, response_id):
    global waveform_thread
    waveform_thread = None
    
    dialogutils.delay_destroy_window(dialog, 1.6)

def clear_waveform(data):
    # LOOK TO REMOVE; DOES NOT SEEMS CURRENT
    clip, track, item_id, item_data = data
    clip.waveform_data = None
    clip.waveform_data_frame_height = -1
    updater.repaint_tline()

def _get_unique_name_for_media(media_file_path):
    return utils.get_unique_name_for_audio_levels_file(media_file_path, PROJECT().profile)


class WaveformCreator(threading.Thread):    
    def __init__(self, clip, track_height, dialog):
        threading.Thread.__init__(self)
        self.clip = clip
        self.temp_clip = self._get_temp_producer(clip)
        self.file_cache_path = userfolders.get_cache_dir() + appconsts.AUDIO_LEVELS_DIR + _get_unique_name_for_media(clip.path)
        self.track_height = track_height
        self.abort = False
        self.clip_media_length = self.temp_clip.get_length()
        self.last_rendered_frame = 0
        self.stopped = False
        self.dialog = dialog
        
    def run(self):
        global frames_cache
        frame_levels = [None] * self.clip_media_length 
        frames_cache[self.clip.path] = frame_levels

        Gdk.threads_enter()
        self.dialog.progress_bar.set_fraction(0.0)
        self.dialog.progress_bar.set_text(str(0) + "%")
        while(Gtk.events_pending()):
            Gtk.main_iteration()
        Gdk.threads_leave()
        time.sleep(0.2)

        for frame in range(0, len(frame_levels)):
            if self.abort:
                break
            self.temp_clip.seek(frame)
            mlt.frame_get_waveform(self.temp_clip.get_frame(), 10, 50)
            val = self.levels.get(RIGHT_CHANNEL)
            if val == None:
                val = 0.0
            frame_levels[frame] = float(val)
            self.last_rendered_frame = frame
            if frame % 500 == 0:
                render_fraction = float(self.last_rendered_frame) / float(self.clip_media_length)
                Gdk.threads_enter()
                self.dialog.progress_bar.set_fraction(render_fraction)
                pros = int(render_fraction * 100)
                self.dialog.progress_bar.set_text(str(pros) + "%")
                while(Gtk.events_pending()):
                    Gtk.main_iteration()
                Gdk.threads_leave()
                time.sleep(0.1)

        if not self.abort:
            self.clip.waveform_data = frame_levels
            write_file = open(self.file_cache_path, "wb")
            pickle.dump(frame_levels, write_file)

            Gdk.threads_enter()
            self.dialog.progress_bar.set_fraction(1.0)
            self.dialog.progress_bar.set_text(_("Saving to Hard Drive"))
            Gdk.threads_leave()
        
        else:
            frames_cache.pop(self.clip.path, None)

        updater.repaint_tline()

        # Set thread ref to None to flag that no waveforms are being created
        global waveform_thread
        waveform_thread = None
        
        _waveform_render_stop(self.dialog, None)

    def _get_temp_producer(self, clip):
        service = clip.get("mlt_service")
        if service.startswith("xml"):
            service = "xml-nogl"
        temp_producer = mlt.Producer(PROJECT().profile, service.encode('utf-8'), clip.get("resource"))
        channels = mlt.Filter(PROJECT().profile, "audiochannels")
        converter = mlt.Filter(PROJECT().profile, "audioconvert")
        self.levels = mlt.Filter(PROJECT().profile, "audiolevel")
        temp_producer.attach(channels)
        temp_producer.attach(converter)
        temp_producer.attach(self.levels)
        temp_producer.path = clip.path
        return temp_producer

    def abort_rendering(self):
        self.abort = True

def _waveform_render_progress_dialog(callback, title, text, progress_bar, parent_window):
    dialog = Gtk.Dialog(title,
                         parent_window,
                         Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                         (_("Cancel").encode('utf-8'), Gtk.ResponseType.REJECT))

    dialog.text_label = Gtk.Label(label=text)
    dialog.text_label.set_use_markup(True)
    text_box = Gtk.HBox(False, 2)
    text_box.pack_start(dialog.text_label,False, False, 0)
    text_box.pack_start(Gtk.Label(), True, True, 0)

    status_box = Gtk.HBox(False, 2)
    status_box.pack_start(text_box, False, False, 0)
    status_box.pack_start(Gtk.Label(), True, True, 0)

    progress_vbox = Gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
    progress_vbox.pack_start(progress_bar, False, False, 0)

    alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)
        
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.set_default_size(500, 125)
    alignment.show_all()
    dialog.connect('response', callback)
    dialog.show()
    return dialog
