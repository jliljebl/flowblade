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
import edit
from editorstate import current_sequence
from editorstate import get_tline_rendering_mode
from editorstate import PROJECT
from editorstate import PLAYER
import gui
import mltfilters
import renderconsumer
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
def app_launch_clean_up():
    for old_session_dir in listdir(_get_tline_render_dir()):
        _delete_dir_and_contents(_get_tline_render_dir() + "/" + old_session_dir)
    
def init_session(): # called when project is loaded
    
    global _project_session_id
    if _project_session_id != -1:
        _delete_session_dir()

    _project_session_id = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
    os.mkdir(_get_session_dir())

    tlinerenderserver.launch_render_server()

def delete_session():
    tlinerenderserver.shutdown_render_server()
    _delete_session_dir()

def init_for_sequence(sequence):
    update_renderer_to_mode()

def update_renderer_to_mode():
    #print("new renderer for mode:", get_tline_rendering_mode())
    
    global _timeline_renderer
    if get_tline_rendering_mode() == appconsts.TLINE_RENDERING_OFF:
        _timeline_renderer = NoOpRenderer()
    else:
        _timeline_renderer = TimeLineRenderer()
        #---testing
        #seg = TimeLineSegment(SEGMENT_NOOP, 0, 50)
        #_timeline_renderer.segments.append(seg)
        seg = TimeLineSegment(50, 170)
        _timeline_renderer.segments.append(seg)
        #seg = TimeLineSegment(SEGMENT_NOOP, 70, 80)
        #_timeline_renderer.segments.append(seg)
        seg = TimeLineSegment(200, 290)
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
    _delete_dir_and_contents(session_dir)

def _delete_dir_and_contents(del_dir):
    files = _get_folder_files(del_dir)
    for f in files:
        os.remove(del_dir +"/" + f)

    os.rmdir(del_dir)
        
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
            #print("press")

    def motion_notify_event(self, x, y, state):
        if((state & Gdk.ModifierType.BUTTON1_MASK)
           or(state & Gdk.ModifierType.BUTTON3_MASK)):
            if self.drag_on:
                pass
        #print("motion")
                
    def release_event(self, event):
        if self.drag_on:
            pass
        self.drag_on = False
        #print("release")
    
    # --------------------------------------------- CONTENT UPDATES
    def timeline_changed(self):
        global _update_thread
        if _update_thread != None:
            # We already have an update thread going, try to stop it before it launches renders.
            _update_thread.abort_before_render_request = True
    
        _update_thread = TimeLineUpdateThread()
        _update_thread.start()

    def all_segments_ready(self):
        return (len(self.get_dirty_segments()) == 0)

    def update_segments(self):
        for seg in self.segments:
            seg.update_segment()

    def get_dirty_segments(self):
        dirty = []
        for seg in self.segments:
            if seg.segment_state == SEGMENT_DIRTY:
                dirty.append(seg)
        
        return dirty

    def update_hidden_track(self, hidden_track, seq_len):
        if len(self.segments) == 0:
            edit._insert_blank(hidden_track, 0, seq_len)
        else:
            in_frame = 0
            index = 0
            for segment in self.segments:
                # Blank between segments/sequence start
                if segment.start_frame > in_frame:
                    edit._insert_blank(hidden_track, index, segment.start_frame - in_frame)
                    
                    #print("Inserting blank:", index, )
                    index += 1
                
                segment_length = segment.end_frame - segment.start_frame
                
                # Segment contents
                if segment.segment_state == SEGMENT_UNRENDERED or segment.segment_state == SEGMENT_DIRTY:
                    edit._insert_blank(hidden_track, index, segment_length - 1)
                elif segment.segment_state == SEGMENT_RENDERED:
                    #print("Inserting tline render clip at index:", index)
                    edit.append_clip(hidden_track, segment.producer, 0, segment_length - 1) # -1, out incl.

                in_frame = segment.end_frame
                index += 1
            
            if hidden_track.get_length() < seq_len:
                edit._insert_blank(hidden_track, index, seq_len - hidden_track.get_length())
                #print("end completion blank append", index)
        
    # ------------------------------------------------ RENDERING
    def update_timeline_rendering_status(self, rendering_file, fract, render_completed, completed_segments):
        dirty = self.get_dirty_segments()
        for segment in dirty:
            if segment.get_clip_path() == rendering_file:
                segment.rendered_fract = fract
                #print(segment.rendered_fract, segment.content_hash) 
            else:
                segment.maybe_set_completed(completed_segments)
                

class NoOpRenderer():

    
    def __init__(self):
        """
        Instead of multiple tests for editorstate.get_tline_rendering_mode() we implement TLINE_RENDERING_OFF mode 
        as no-op timeline renderer.
        """
        pass
        
    def draw(self, event, cr, allocation, pos, pix_per_frame):
        pass

    def timeline_changed(self):
        pass
 
    def press_event(self, event):
        pass

    def motion_notify_event(self, x, y, state):
        pass
                
    def release_event(self, event):
        pass
    
    def update_hidden_track(self, hidden_track, seq_len):
        edit._insert_blank(hidden_track, 0, seq_len)


class TimeLineSegment:

    def __init__(self, start_frame, end_frame):
        self.segment_state = SEGMENT_UNRENDERED
        
        self.start_frame = start_frame # inclusive
        self.end_frame = end_frame # exclusive

        self.content_hash = "-1"

        self.rendered_fract = 0.0
    
        self.producer = None
    
    # --------------------------------------------- DRAW
    def draw(self, cr, height, pos, pix_per_frame):
        x = int(_get_x_for_frame_func(self.start_frame))
        x_end = int(_get_x_for_frame_func(self.end_frame))
        w = x_end - x
        cr.set_source_rgb(*_segment_colors[self.segment_state])
        cr.rectangle(x, 0, w ,height)

        if self.segment_state == SEGMENT_DIRTY:
            cr.fill()
            
            rendered_w = int(self.rendered_fract * float(w))
            cr.set_source_rgb(*_segment_colors[SEGMENT_RENDERED])
            cr.rectangle(x, 0, rendered_w, height)
            cr.fill()

            cr.rectangle(x, 0, w ,height)
            cr.set_source_rgb(0, 0, 0)
            cr.stroke()
        else:
            cr.fill_preserve()
            cr.set_source_rgb(0, 0, 0)
            cr.stroke()

    # -------------------------------------------- CLIP AND RENDERING
    def get_clip_path(self):
        return _get_session_dir() + "/" + self.content_hash + "." + tlinerenderserver.get_encoding_extension()
    
    def maybe_set_completed(self, completed_segments):
        if self.get_clip_path() in completed_segments:
            self.update_segment_as_rendered()
            
    def update_segment_as_rendered(self):
        self.segment_state = SEGMENT_RENDERED
        self.rendered_fract = 0.0
        
        self.create_clip()
    
    def create_clip(self):
        self.producer = current_sequence().create_file_producer_clip(str(self.get_clip_path()))
        
        # testing
        filter_info = mltfilters.get_colorize_filter_info()
        filter_object = current_sequence().create_filter(filter_info)
        self.producer.attach(filter_object.mlt_filter)
        self.producer.filters.append(filter_object)
        
        #print("producer created",  self.content_hash)

    # ----------------------------------------- CONTENT HASH
    def update_segment(self):
        new_hash = self.get_content_hash()
        
        if new_hash != self.content_hash:
            if get_tline_rendering_mode() == appconsts.TLINE_RENDERING_AUTO:
                self.segment_state = SEGMENT_DIRTY
                self.producer = None
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
            content_strings.append(str(p_value))

        


#--------------------------------------- worker threads
class TimeLineUpdateThread(threading.Thread):
    
    def __init__(self):
        self.update_id = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest() # starting these is human speed so using time is ok.
        self.abort_before_render_request = False
        threading.Thread.__init__(self)

    def run(self):
        
        _timeline_renderer.update_segments()

        self.dirty_segments = _timeline_renderer.get_dirty_segments()
        #print("dirty segments:", len(self.dirty_segments))
        
        if len(self.dirty_segments) == 0:
            return
        
        try:
            # Blocks untils renders are stopped and cleaned
            tlinerenderserver.abort_current_renders()
        except:
            # Dbus default timeout of 25s was exceeded, something is very wrong, no use to attempt furher work.
            print("INFO: tlinerendersrver.abort_current_renders() exceeded DBus timeout of 25s.")
            return

        # Write out MLT XML for render
        self.save_path = _get_session_dir() + "/" + self.update_id + ".xml"
               
        _xml_render_player = renderconsumer.XMLRenderPlayer(  self.save_path,
                                                              self.xml_render_done,
                                                              None,
                                                              PROJECT().c_seq,
                                                              PROJECT(),
                                                              PLAYER())
        _xml_render_player.start()

    def xml_render_done(self, data):
        if self.abort_before_render_request == True:
            # A new update was requested before this update got ready to start rendering.
            # This is no longer needed,  we can let the later request do the update,
            return
        
        # Launch renders and completion polling
        segments_paths = []
        segments_ins = []
        segments_outs = []
        for segment in self.dirty_segments:
            clip_path = segment.get_clip_path()
            if os.path.isfile(clip_path) == True:
                # We came here with undo or redo or new edit that recreates existing content for segment
                #print ("CreatinG for existing")
                segment.update_segment_as_rendered()
            else:
                # Clip for this content does not exists
                segments_paths.append(clip_path)
                segments_ins.append(segment.start_frame)
                segments_outs.append(segment.end_frame)
        
        if len(segments_paths) == 0:
            # clips for all new dirty segments existed
            Gdk.threads_enter()
            gui.tline_render_strip.widget.queue_draw()
            Gdk.threads_leave()
            return

        tlinerenderserver.render_update_clips(self.save_path,  segments_paths, segments_ins, segments_outs, current_sequence().profile.description())

        status_display = TimeLineStatusPollingThread()
        status_display.start()


class TimeLineStatusPollingThread(threading.Thread):
    
    def __init__(self):
        self.update_id = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
        self.abort_before_render_request = False
        threading.Thread.__init__(self)

    def run(self):
        running = True
        
        while running:
            rendering_file, fract, render_completed, completed_segments = tlinerenderserver.get_render_status()
            get_renderer().update_timeline_rendering_status(rendering_file, fract, render_completed, completed_segments)

            Gdk.threads_enter()
            gui.tline_render_strip.widget.queue_draw()
            Gdk.threads_leave()

            #print(rendering_file, fract, render_completed, "\n\n")
            # print(completed_segments,"\n\n\n\n")

            time.sleep(0.5)
            
            if render_completed == 1: 
                running = False
    
        while get_renderer().all_segments_ready() == False:
            time.sleep(0.1)
            
        current_sequence().update_hidden_track_for_timeline_rendering() # We should have correct sequence length known because this always comes after edits.
    
        print("timeline update rendering done")
