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
import numpy
import struct
import time
import threading

import appconsts
from editorstate import PROJECT
import gui
import tlinewidgets
import updater

RENDERING_FRAME_DISPLAY_STEP = 100

# If adding clip to the ones displaying waveforms makes number of frames displaying 
# waveforms higher then this, some clips (FIFO) will no longer display waveforms
max_displayed_frames = 1500

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
    When clips are moved to other tracks wave images maybe worng size,
    and if so delete wavorm images. Called from edit.py
    """
    for clip in clip_list:
        if clip.waveform_data != None and clip.waveform_data_frame_height != new_track.height:
            waveform_displayer_clips.remove(clip)
            clip.waveform_data = None
            clip.waveform_data_frame_height = -1

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

        watch = gtk.gdk.Cursor(gtk.gdk.WATCH)
        gui.editor_window.window.window.set_cursor(watch)
        while(gtk.events_pending()):
            gtk.main_iteration()
        
        pix_per_frame = updater.PIX_PER_FRAME_MAX
        width = int(math.ceil(pix_per_frame))
        
        clip = self.clip
        clip.waveform_data = None # attempted draws won't draw half done image array
        in_frame = clip.clip_in
        out_frame = clip.clip_out

        if self.track_height == appconsts.TRACK_HEIGHT_SMALL:
            frame_image_height, draw_image_height, draw_image_first_row = SMALL_TRACK_DRAW_CONSTS
        else:
            frame_image_height, draw_image_height, draw_image_first_row = LARGE_TRACK_DRAW_CONSTS

        try:
            large_track_frames, small_track_frames = frames_cache[clip.path]
        except KeyError:
            clip_media_length = PROJECT().get_media_file_for_path(clip.path).length
            large_track_frames = []
            small_track_frames = []
            for i in range(0, clip_media_length + 1):
                large_track_frames.append(None)
                small_track_frames.append(None)
            frames_cache[clip.path] = (large_track_frames, small_track_frames)

        if self.track_height == appconsts.TRACK_HEIGHT_SMALL:
            prerendered_frames = small_track_frames
        else:
            prerendered_frames = large_track_frames
            
        frame_images = []
        for frame in range(in_frame, out_frame + 1):
            clip.seek(frame)
            frame_img = prerendered_frames[frame] 
            if frame_img == None:
                wave_img_array = mlt.frame_get_waveform(clip.get_frame(), width, frame_image_height)
                frame_img = self._draw_bitmap(wave_img_array, width, draw_image_height, draw_image_first_row)
                prerendered_frames[frame] = frame_img

            frame_images.append(frame_img)

            if self.abort == True:
                break
                
            if (frame - in_frame) > 0 and ((frame - in_frame) % RENDERING_FRAME_DISPLAY_STEP) == 0:
                clip.waveform_data = frame_images
                updater.repaint_tline()
                while(gtk.events_pending()):
                    gtk.main_iteration()

        clip.waveform_data = frame_images
        clip.waveform_data_frame_height = self.track_height
        self._update_displayed(clip)

        normal_cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
        gui.editor_window.window.window.set_cursor(normal_cursor)
        updater.repaint_tline()
        
        global waveform_thread
        waveform_thread = None

    def _draw_bitmap(self, wave_img_array, w, h, start_line):
        pix_buf_array = numpy.zeros([h, w, 4],'B')
        for x in range(0, w):
            for y in range(0, h):
                i = x + (y + start_line) * w
                val = max(struct.unpack("B", wave_img_array[i]))
                pix_buf_array[y][x] = (0, 0, 0, val) # image is full black, pattern is in alpha

        return gtk.gdk.pixbuf_new_from_array(pix_buf_array, gtk.gdk.COLORSPACE_RGB, 8)

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
