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
import hashlib
from gi.repository import Gdk
import os
from os import listdir
from os.path import isfile, join
import time
import threading

import appconsts
import cairoarea
from editorstate import current_sequence
from editorstate import get_tline_rendering_mode
import userfolders
import tlinerenderserver

STRIP_HEIGHT = 8

# These are monkeypatched in at app.py
_get_frame_for_x_func = None
_get_x_for_frame_func = None
_get_last_tline_view_frame_func = None

SEGMENT_NOOP = 0
SEGMENT_RENDERED = 1
SEGMENT_UNRENDERED = 2
SEGMENT_DIRTY = 3

_segment_colors = { SEGMENT_NOOP:(0.26, 0.29, 0.42),
                    SEGMENT_RENDERED:(0.29, 0.78, 0.30),
                    SEGMENT_UNRENDERED:(0.76, 0.27, 0.27),
                    SEGMENT_DIRTY:(0.76, 0.27, 0.27)}

_project_session_id = -1
_timeline_renderer = None

_update_thread = None

# ------------------------------------------------------------ MODULE INTERFACE
def init_session(): # called when project is loaded
    
    global _project_session_id
    if _project_session_id != -1:
        _delete_session_dir()

    global _updates
    _updates = []
    
    _project_session_id = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
    os.mkdir(_get_session_dir())

    success = tlinerenderserver.launch_render_server()
    if success:
        print ("Timeline background render service launch succeeded.")
    else:
        print ("Timeline background render service launch failed.")
        
def delete_session():
    tlinerenderserver.shutdown_render_server()
    _delete_session_dir()

def init_for_sequence(sequence):
    global _timeline_renderer
    _timeline_renderer = TimeLineRenderer()

    #---testing
    #seg = TimeLineSegment(SEGMENT_NOOP, 0, 50)
    #_timeline_renderer.segments.append(seg)
    seg = TimeLineSegment(50, 70)
    _timeline_renderer.segments.append(seg)
    #seg = TimeLineSegment(SEGMENT_NOOP, 70, 80)
    #_timeline_renderer.segments.append(seg)
    seg = TimeLineSegment(80, 90)
    _timeline_renderer.segments.append(seg)

def get_renderer():
    return _timeline_renderer


# ------------------------------------------------------------ MODULE FUNCS
def _get_tline_render_dir():
    return userfolders.get_data_dir() + appconsts.TLINE_RENDERS_DIR

def _get_session_dir():
    return _get_tline_render_dir() + "/" + _project_session_id

def _delete_session_dir():
    session_dir = _get_session_dir()
    files = _get_folder_files(session_dir)
    for f in files:
        os.remove(session_dir +"/" + f)

    os.rmdir(session_dir)
        
def _get_folder_files(folder):
    return [f for f in listdir(folder) if isfile(join(folder, f))]


# ------------------------------------------------------------ RENDERER OBJECTS
class TimeLineRenderer:

    def __init__(self):
        self.segments = []


    # --------------------------------------------- DRAW
    def draw(self, event, cr, allocation, pos, pix_per_frame):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation

        cr.set_source_rgb(*_segment_colors[SEGMENT_NOOP])
        cr.rectangle(0,0,w,h)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()

        for seg in self.segments:
            if seg.end_frame < pos:
                continue
            if seg.start_frame > _get_last_tline_view_frame_func():
                break
            if seg.segment_state == SEGMENT_NOOP:
                continue
            seg.draw(cr, h, pos, pix_per_frame)

    # --------------------------------------------- MOUSE EVENTS    
    def press_event(self, event):
        if event.button == 1 or event.button == 3:
            self.drag_on = True
            print("press")

    def motion_notify_event(self, x, y, state):
        if((state & Gdk.ModifierType.BUTTON1_MASK)
           or(state & Gdk.ModifierType.BUTTON3_MASK)):
            if self.drag_on:
                pass
        print("motion")
                
    def release_event(self, event):
        if self.drag_on:
            pass
        self.drag_on = False
        print("release")
    
    # --------------------------------------------- CONTENT UPDATES
    def timeline_changed(self):
        global _update_thread
        if _update_thread != None:
            # We already have an update thread going, try to stop it before it launches renders.
            _update_thread.abort_before_render_request = True
    
        _update_thread = TimeLineUpdateThread()
        _update_thread.start()

    def update_segments(self):
        for seg in self.segments:
            seg.update_segment()

    def get_dirty_segments(self):
        dirty = []
        for seg in self.segments:
            seg.segment_state = SEGMENT_DIRTY
            dirty.append(seg)
        
        return dirty
            
            

class TimeLineSegment:

    def __init__(self, start_frame, end_frame):
        self.segment_state = SEGMENT_UNRENDERED
        
        self.start_frame = start_frame # inclusive
        self.end_frame = end_frame # exclusive

        self.content_hash = "-1"

    # --------------------------------------------- DRAW
    def draw(self, cr, height, pos, pix_per_frame):
        x = int(_get_x_for_frame_func(self.start_frame))
        x_end = int(_get_x_for_frame_func(self.end_frame))
        w = x_end - x
        cr.set_source_rgb(*_segment_colors[self.segment_state])
        cr.rectangle(x, 0, w ,height)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()

    # ----------------------------------------- CONTENT HASH
    def update_segment(self):
        new_hash = self.get_content_hash()
        
        if new_hash != self.content_hash:
            if get_tline_rendering_mode() == appconsts.TLINE_RENDERING_AUTO:
                self.segment_state = SEGMENT_DIRTY
            elif get_tline_rendering_mode() == appconsts.TLINE_RENDERING_REQUEST:
                self.segment_state = SEGMENT_UNRENDERED

        self.content_hash = new_hash
    
    def get_content_hash(self):
        content_strings = []
        for i in range(1, len(current_sequence().tracks) - 1):
            track = current_sequence().tracks[i]
            self._get_track_segment_content_strings(track, content_strings)
        
        content_desc = "".join(content_strings)
        
        return hashlib.md5(content_desc.encode('utf-8')).hexdigest()
        
    def _get_track_segment_content_strings(self, track, content_strings):
        start_clip_index, clips = self._get_track_segment_clips(track, self.start_frame, self.end_frame)
        if len(clips) == 0:
            content_strings.append("-1")
            return
            
        for i in range(0, len(clips)):
            clip = clips[i]
            self._get_clip_content_strings(track, clip, start_clip_index + i, content_strings)
                
    def _get_track_segment_clips(self, track, start_frame, end_frame):
        clips = []
        
        # Get start range index, outer selection required
        start_clip_index = current_sequence().get_clip_index(track, start_frame)
        if start_clip_index == -1:
            # Segment start aftr track end no clips in segments on this track
            return (-1, clips)
        
        # Get end range index, outer selection required
        end_clip_index = current_sequence().get_clip_index(track, end_frame)
        if end_clip_index == -1:
            # Segment contains last clip on track
            end_clip_index = len(track.clips) - 1

        for i in range(start_clip_index, end_clip_index + 1):
            clips.append(track.clips[i])
        
        return (start_clip_index, clips)
        
    def _get_clip_content_strings(self, track, clip, clip_index, content_strings):

        length = clip.clip_out - clip.clip_in 
    
        # Position and range data
        # offset from segment start + in, out
        clip_start_in_tline = track.clip_start(clip_index)
        content_strings.append(str(clip_start_in_tline - self.start_frame))
        content_strings.append(str(clip.clip_in))
        content_strings.append(str(clip.clip_out))
        
        # Content data
        if clip.is_blanck_clip == True:
            content_strings.append("##blank")
            return

        if len(clip.filters) == 0:
            content_strings.append("##no_filters")
        else:
            for filter_object in clip.filters:
                self._get_filter_content_strings(filter_object, content_strings)
        
        if clip.mute_filter == None:
            content_strings.append("##no_mute")
        else:
            self._get_filter_content_strings(clip.mute_filter, content_strings)

    def _get_filter_content_strings(self, filter_object, content_strings):
        for i in range(0, len(filter_object.properties)):
            p_name, p_value, p_type = filter_object.properties[i]
            content_strings.append(p_name)
            content_strings.append(str(p_type))

        


#--------------------------------------- worker threads
class TimeLineUpdateThread(threading.Thread):
    
    def __init__(self):
        self.update_id = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest() # starting these is human speed so using time is ok.
        self.abort_before_render_request = False
        threading.Thread.__init__(self)

    def run(self):
        
        _timeline_renderer.update_segments()

        dirty_segments = _timeline_renderer.get_dirty_segments()
        
        if len(dirty_segments) == 0:
            return
        
        # Blocks
        try:
            # Blocks untils renders are stopped and cleaned
            tlinerenderserver.abort_current_renders()
        except:
            # Timeout of 25s was exceeded, sometrhing is very wrong, no use to attempt furher work.
            print("INFO: tlinerendersrver.abort_current_renders() exceeded timeout of 25s.")
            return

        # Write out MLT XML for render

        if self.abort_before_render_request == True:
            # A new update was requested before this update got ready to start rendering.
            # This is no longer needed,  we can let the later request do the update,
            return
        
        # Launch renders and completion polling
