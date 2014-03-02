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

import gtk
import math
import mlt
import struct
import threading

from editorstate import PROJECT
import gui
import updater

RENDERING_FRAME_DISPLAY_STEP = 100

# Frame image cache for waveform images
# path -> tuple of two arrays (for small & large track heights) of 
# gtk.gdk.PixBuf images or Nones, depending if frames have been created
frames_cache = {}

# Thread creates waveform images after waveform displayer is changed or zoomed
waveform_thread = None


# ------------------------------------------------- waveforms
def set_waveform_displayer_clip_from_popup(data):
    clip, track, item_id, item_data = data

    global waveform_thread
    waveform_thread = WaveformCreator(clip, track.height)
    waveform_thread.run()

def clear_waveform(data):
    clip, track, item_id, item_data = data
    clip.waveform_data = None
    clip.waveform_data_frame_height = -1
    updater.repaint_tline()

def clear_caches():
    global frames_cache, waveform_thread
    if waveform_thread != None:
        waveform_thread.abort_rendering()
    frames_cache = {}
    waveform_thread = None


class WaveformCreator(threading.Thread):    
    def __init__(self, clip, track_height):
        threading.Thread.__init__(self)
        self.target_clip = clip
        self.clip = self._get_temp_producer(clip)
        self.track_height = track_height
        self.abort = False

    def run(self):
        global frames_cache
        temp_producer = self._get_temp_producer(self.clip)
    
        # Get clip data
        clip = self.clip
        clip.waveform_data = None # attempted draws won't draw half done image array


        # Get calculated and cached values for  media object frame audio levels
        if clip.path in frames_cache:
            frame_levels = frames_cache[clip.path]
            self.target_clip.waveform_data = frame_levels
            render_levels = False
        else:
            clip_media_length = PROJECT().get_media_file_for_path(clip.path).length
            frame_levels = [None] * clip_media_length 
            frames_cache[clip.path] = frame_levels

        #in_frame = 0
        #out_frame = len(prerendered_frames)
        
        # Calculate frame levels for current displayed clip area using waveform image 
        values = []
        VAL_MIN = 5100.0
        VAL_MAX = 15000.0
        VAL_RANGE = VAL_MAX - VAL_MIN
        for frame in range(0, len(frame_levels)):
            clip.seek(frame)
            wave_img_array = mlt.frame_get_waveform(clip.get_frame(), 10, 50)
            val = 0
            for i in range(0, len(wave_img_array)):
                val += max(struct.unpack("B", wave_img_array[i]))
            if val > VAL_MAX:
                val = VAL_MAX
            val = val - VAL_MIN
            val = math.sqrt(float(val) / VAL_RANGE)
                
            frame_levels[frame] = val

            if self.abort == True:
                break
            
            """
            if frame > 0 and frame % RENDERING_FRAME_DISPLAY_STEP == 0:
                self.target_clip.waveform_data = values
                updater.repaint_tline()
                while(gtk.events_pending()):
                    gtk.main_iteration()
            """

                
        # Set clip wavorm data and display
        self.target_clip.waveform_data = frame_levels
        updater.repaint_tline()

        print "dfdf"
        # Set thread ref to None to flag that no waveforms are being created
        global waveform_thread
        waveform_thread = None

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
        temp_producer.clip_in = 0
        temp_producer.clip_out = clip.get_length() - 1
        temp_producer.path = clip.path
        return temp_producer

    def abort_rendering(self):
        normal_cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
        gui.editor_window.window.window.set_cursor(normal_cursor)
        self.abort = True
