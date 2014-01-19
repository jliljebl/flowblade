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

# If adding clip to the ones displaying waveforms makes number of frames displaying 
# waveforms higher then this, some clips (FIFO) will no longer display waveforms
max_displayed_frames = 150000

# (frame_image_height, draw_image_height, draw_image_first_row)
LARGE_TRACK_DRAW_CONSTS = (150, 45, 15)
SMALL_TRACK_DRAW_CONSTS = (75, 22, 7)

# Frame image cache for waveform images
# path -> tuple of two arrays (for small & large track heights) of 
# gtk.gdk.PixBuf images or Nones, depending if frames have been created
frames_cache = {}

# Clips currently displaying 
waveform_displayer_clips = []

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
    waveform_displayer_clips.remove(clip)
    clip.waveform_data = None
    clip.waveform_data_frame_height = -1
    updater.repaint_tline()
    
def maybe_delete_waveforms(clip_list, new_track):
    """
    When clips are moved to other tracks wave images maybe wrong size,
    and if so delete wavorm images. Called from edit.py
    """
    pass
    """
    for clip in clip_list:
        if clip.waveform_data != None and clip.waveform_data_frame_height != new_track.height:
            waveform_displayer_clips.remove(clip)
            clip.waveform_data = None
            clip.waveform_data_frame_height = -1
    """

def clear_caches():
    global frames_cache, waveform_displayer_clips, waveform_thread
    if waveform_thread != None:
        waveform_thread.abort_rendering()
    frames_cache = {}
    waveform_displayer_clips = []
    waveform_thread = None

def _displayed_frames_count():
    frames = 0
    for clip in waveform_displayer_clips:
        frames += len(clip.waveform_data)
    return frames

class WaveformCreator(threading.Thread):    
    def __init__(self, clip, track_height):
        threading.Thread.__init__(self)
        self.clip = clip
        self.track_height = track_height
        self.abort = False

    def run(self):
        global waveform_displayer_clip, frames_cache

        # Display wait/busy cursor
        gtk.gdk.threads_enter()
        watch = gtk.gdk.Cursor(gtk.gdk.WATCH)
        gui.editor_window.window.window.set_cursor(watch)
        while(gtk.events_pending()):
            gtk.main_iteration()
        gtk.gdk.threads_leave()

        # Get clip data
        clip = self.clip
        clip.waveform_data = None # attempted draws won't draw half done image array
        in_frame = clip.clip_in
        out_frame = clip.clip_out

        # Get calculated and cached values for  media object frame audio levels
        try:
            prerendered_frames = frames_cache[clip.path]
        except KeyError:
            clip_media_length = PROJECT().get_media_file_for_path(clip.path).length
            prerendered_frames = []
            for i in range(0, clip_media_length + 1):
                prerendered_frames.append(None)
            frames_cache[clip.path] = prerendered_frames

        # Calculate missing frame levels for current displayed clip area
        # Update cache values of media object and create waveform data for clip object 
        values = []
        VAL_MIN = 5100.0
        VAL_MAX = 15000.0
        VAL_RANGE = VAL_MAX - VAL_MIN
        for frame in range(in_frame, out_frame + 1):
            clip.seek(frame)
            val = prerendered_frames[frame] 
            if val == None:
                wave_img_array = mlt.frame_get_waveform(clip.get_frame(), 10, 50)
                val = 0
                for i in range(0, len(wave_img_array)):
                    val += max(struct.unpack("B", wave_img_array[i]))
                if val > VAL_MAX:
                    val = VAL_MAX
                val = val - VAL_MIN
                val = math.sqrt(float(val) / VAL_RANGE)
                
                prerendered_frames[frame] = val

            values.append(val)

            if self.abort == True:
                break
            
            if (frame - in_frame) > 0 and ((frame - in_frame) % RENDERING_FRAME_DISPLAY_STEP) == 0:
                clip.waveform_data = values
                gtk.gdk.threads_enter()
                updater.repaint_tline()
                while(gtk.events_pending()):
                    gtk.main_iteration()
                gtk.gdk.threads_leave()
        
        # Set clip wavorm data and display
        clip.waveform_data = values
        self._update_displayed(clip)
        
        # Display normal cursor
        gtk.gdk.threads_enter()
        normal_cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
        gui.editor_window.window.window.set_cursor(normal_cursor)
        updater.repaint_tline()
        gtk.gdk.threads_leave()
                
        # Set thread ref to None to flag that no waveforms are being created
        global waveform_thread
        waveform_thread = None

    def _update_displayed(self, clip):
        global waveform_displayer_clips
        waveform_displayer_clips.append(clip)

        # Remove earlier clips if too many frames displayed
        # 1 clip is always displayed no matter how many 
        while((len(waveform_displayer_clips) > 1) and
             (_displayed_frames_count() > max_displayed_frames)):
            clip = waveform_displayer_clips.pop(0)
            clip.waveform_data = None
            clip.waveform_data_frame_height = -1

    def abort_rendering(self):
        normal_cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
        gui.editor_window.window.window.set_cursor(normal_cursor)
        self.abort = True
