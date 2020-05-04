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
from gi.repository import Gdk, Gtk
import os
from os import listdir
from os.path import isfile, join
import time
import threading

import appconsts
import cairoarea
import dialogutils
import edit
import editorpersistance
from editorstate import current_sequence
from editorstate import get_tline_rendering_mode
from editorstate import PROJECT
from editorstate import PLAYER
from editorstate import timeline_visible
from editorstate import get_tline_rendering_mode
import editorstate
import gui
import guiutils
#import mltfilters can used for testing
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

MOUSE_DRAG_THRESHOLD_FRAMES = 3

tlinerender_mode_menu = Gtk.Menu()
strip_popup_menu = Gtk.Menu()

_segment_colors = { SEGMENT_NOOP:(0.26, 0.29, 0.42),
                    SEGMENT_RENDERED:(0.29, 0.78, 0.30),
                    SEGMENT_UNRENDERED:(0.76, 0.27, 0.27),
                    SEGMENT_DIRTY:(0.76, 0.27, 0.27)}
                    
DRAG_RANGE_COLOR = (1,1,1,0.3)

_project_session_id = -1
_timeline_renderer = None # this gets set to NoOpRenderer on launch, is never None for long.

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

def init_for_sequence():
    update_renderer_to_mode(None)

def update_renderer_to_mode(old_mode):

    global _timeline_renderer
    if get_tline_rendering_mode() == appconsts.TLINE_RENDERING_OFF:
        _timeline_renderer = NoOpRenderer()
    else:
        if old_mode == appconsts.TLINE_RENDERING_OFF:
            _timeline_renderer = TimeLineRenderer()

def settings_dialog_launch(widget, event):
    global manager_window
    manager_window = TLineSettingsRenderDialog()

def get_renderer():
    return _timeline_renderer

# --------------------------------------------------------- menus
def corner_mode_menu_launched(widget, event):
    guiutils.remove_children(tlinerender_mode_menu)
        
    render_off = guiutils.get_image_menu_item(_("Timeline Render Off"), "tline_render_off", _set_new_render_mode)
    render_auto = guiutils.get_image_menu_item(_("Timeline Render Auto"), "tline_render_auto", _set_new_render_mode)
    render_request = guiutils.get_image_menu_item(_("Timeline Render On Request"), "tline_render_request", _set_new_render_mode)

    render_off.connect("activate", lambda w: _set_new_render_mode(appconsts.TLINE_RENDERING_OFF))
    render_auto.connect("activate", lambda w: _set_new_render_mode(appconsts.TLINE_RENDERING_AUTO))
    render_request.connect("activate", lambda w: _set_new_render_mode(appconsts.TLINE_RENDERING_REQUEST))

    tlinerender_mode_menu.add(render_off)
    tlinerender_mode_menu.add(render_auto)
    tlinerender_mode_menu.add(render_request)

    tlinerender_mode_menu.popup(None, None, None, None, event.button, event.time)

def display_strip_context_menu(event, hit_segment):
    global strip_popup_menu
    guiutils.remove_children(strip_popup_menu)

    sensitive = ((hit_segment != None) and (get_tline_rendering_mode() == appconsts.TLINE_RENDERING_REQUEST))
    item = guiutils.get_menu_item(_("Render Segment"), _strip_menu_item_callback, ("render_segment", hit_segment), sensitive)
    strip_popup_menu.append(item)
    
    sensitive = (len(get_renderer().segments) > 0)
    item = guiutils.get_menu_item(_("Delete All Segments"), _strip_menu_item_callback, ("delete_all", None), sensitive)
    strip_popup_menu.append(item)

    sensitive = (hit_segment != None)
    item = guiutils.get_menu_item(_("Delete Segment"), _strip_menu_item_callback, ("delete_segment", hit_segment), sensitive)
    strip_popup_menu.append(item)

    strip_popup_menu.popup(None, None, None, None, event.button, event.time)

def _strip_menu_item_callback(widget, data):
    msg, segment = data
    if msg == "render_segment":
        segment.segment_state = SEGMENT_DIRTY
        get_renderer().clear_selection()
        get_renderer().launch_update_thread()
    elif msg == "delete_all":
        get_renderer().segments = []
        if timeline_visible() == True:
            current_sequence().update_hidden_track_for_timeline_rendering()
        gui.tline_render_strip.widget.queue_draw()
    else:
        get_renderer().delete_segment(segment)

# ----------------------------------------- timeline rendering
def change_current_tline_rendering_mode(menu_widget, new_tline_render_mode):
    if menu_widget.get_active() == False:
        return
    _set_new_render_mode(new_tline_render_mode)

def _set_new_render_mode(new_tline_render_mode):
    if new_tline_render_mode == get_tline_rendering_mode():
        return
    
    if new_tline_render_mode == appconsts.TLINE_RENDERING_OFF and get_tline_rendering_mode() != appconsts.TLINE_RENDERING_OFF:
        gui.editor_window.hide_tline_render_strip()
    elif new_tline_render_mode != appconsts.TLINE_RENDERING_OFF and get_tline_rendering_mode() == appconsts.TLINE_RENDERING_OFF: 
        gui.editor_window.show_tline_render_strip()
    
    old_mode = editorstate.tline_render_mode 
    editorstate.tline_render_mode = new_tline_render_mode
    update_renderer_to_mode(old_mode)
    gui.editor_window.tline_render_mode_launcher.set_pixbuf(new_tline_render_mode) 
    gui.editor_window.init_timeline_rendering_menu()
    
    if get_tline_rendering_mode() != appconsts.TLINE_RENDERING_OFF:
        get_renderer().launch_update_thread()

# ------------------------------------------------------------ MODULE INTERNAL FUNCS
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

def _sort_segments_comparator(segment):
    return int(segment.start_frame)


# ------------------------------------------------------------ RENDERER OBJECTS
class TimeLineRenderer:

    def __init__(self):
        self.segments = []
        
        self.press_frame = -1
        self.release_frame = -1

        self.drag_on = False
            
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

        if self.drag_on == True:
            cr.set_source_rgba(*DRAG_RANGE_COLOR)
            range_start, range_end = self.get_drag_range()
            xs = _get_x_for_frame_func(range_start)
            xe = _get_x_for_frame_func(range_end)
            cr.rectangle(int(xs), 0, int(xe - xs), h)
            cr.fill()

        
    # --------------------------------------------- MOUSE EVENTS    
    def press_event(self, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS and event.button == 1:
            self.mouse_double_clicked( _get_frame_for_x_func(event.x))
            return
            
        if event.button == 1:
            self.drag_on = True
            self.press_frame = _get_frame_for_x_func(event.x)
            self.release_frame = _get_frame_for_x_func(event.x)
        elif event.button == 3:
            pop_up_frame = _get_frame_for_x_func(event.x)
            hit_segment = self.get_hit_segment(pop_up_frame)
            display_strip_context_menu(event, hit_segment)

        gui.tline_render_strip.widget.queue_draw()
        
    def motion_notify_event(self, x, y, state):
        if (state & Gdk.ModifierType.BUTTON1_MASK):
            self.release_frame = _get_frame_for_x_func(x)

        gui.tline_render_strip.widget.queue_draw()
            
    def release_event(self, event):
        self.release_frame = _get_frame_for_x_func(event.x)
        moved_range = self.press_frame - self.release_frame
        if self.drag_on == True and abs(moved_range) > MOUSE_DRAG_THRESHOLD_FRAMES:
            self.drag_on = False
            self.mouse_drag_edit_completed()
        elif self.drag_on == True:
            self.drag_on = False
            self.mouse_clicked()

        self.press_frame = -1
        self.release_frame = -1

        if get_tline_rendering_mode() == appconsts.TLINE_RENDERING_AUTO:
             self.launch_update_thread()
            
        gui.tline_render_strip.widget.queue_draw()

    def mouse_drag_edit_completed(self):
        range_start, range_end = self.get_drag_range()        
        range_end = range_end - 1

        start_hit_seg = self.get_hit_segment(range_start)
        end_hit_seg = self.get_hit_segment(range_end)
        covered_seqs = self.get_covered_segments(range_start, range_end)
    
        if start_hit_seg == end_hit_seg and start_hit_seg != None:
            self.remove_segments([start_hit_seg])
            self.add_segment(range_start, range_end + 1)
        elif start_hit_seg != None and end_hit_seg != None:
            self.remove_segments(covered_seqs)
            self.remove_segments([start_hit_seg])
            self.remove_segments([end_hit_seg])
            self.add_segment(start_hit_seg.start_frame, end_hit_seg.end_frame)
        elif start_hit_seg != None and end_hit_seg == None:
            self.remove_segments(covered_seqs)
            self.remove_segments([start_hit_seg])
            self.add_segment(start_hit_seg.start_frame, range_end + 1)
        elif start_hit_seg == None and end_hit_seg != None:
            self.remove_segments(covered_seqs)
            self.remove_segments([end_hit_seg])
            self.add_segment(range_start, end_hit_seg.end_frame)
        elif start_hit_seg == None and end_hit_seg == None and len(covered_seqs) > 0:
            self.remove_segments(covered_seqs)
            self.add_segment(range_start, range_end + 1)
        else:
            self.add_segment(range_start, range_end + 1)
        
        self.segments.sort(key=_sort_segments_comparator)

    def mouse_clicked(self):
        hit_seg = self.get_hit_segment(self.release_frame)
        if hit_seg == None:
            return

        self.clear_selection()
        hit_seg.selected = True

    def mouse_double_clicked(self, frame):
        hit_seg = self.get_hit_segment(frame)
        if hit_seg == None:
            return
        
        hit_seg.segment_state = SEGMENT_DIRTY
        self.clear_selection()
        hit_seg.selected = True
        self.launch_update_thread()
        
    def get_drag_range(self):
        range_start = self.press_frame 
        range_end = self.release_frame

        if range_start > range_end:
            range_end, range_start = range_start, range_end
        
        return (range_start, range_end)

    def focus_out(self):
        self.clear_selection()
        gui.tline_render_strip.widget.queue_draw()

    def clear_selection(self):
        for seg in self.segments:
            seg.selected = False

    def delete_selected_segment(self):
        for seg in self.segments:
            if seg.selected == True:
                self.delete_segment(seg)
    
    def delete_segment(self, segment):
        self.segments.remove(segment)
        if timeline_visible() == True:
            current_sequence().update_hidden_track_for_timeline_rendering()
        gui.tline_render_strip.widget.queue_draw()
                
    # --------------------------------------------- CONTENT UPDATES
    def timeline_changed(self):
        if self.drag_on == True:
            return # Happens if user does keyboard edit while also doing s mouse edit on timeline render strip, we will do the update on mouse release.

        self.launch_update_thread()

    def launch_update_thread(self):
        global _update_thread
        if _update_thread != None:
            # We already have an update thread going, try to stop it before it launches renders.
            _update_thread.abort_before_render_request = True
        else:
            pass

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
                if segment.start_frame >= seq_len:
                    break
                 
                # Blank between segments/sequence start
                if segment.start_frame > in_frame:
                    edit._insert_blank(hidden_track, index, segment.start_frame - in_frame)
                    
                    index += 1
                
                segment_length = segment.end_frame - segment.start_frame
                
                # Segment contents
                if segment.segment_state == SEGMENT_UNRENDERED or segment.segment_state == SEGMENT_DIRTY:
                    edit._insert_blank(hidden_track, index, segment_length - 1)
                elif segment.segment_state == SEGMENT_RENDERED:
                    edit.append_clip(hidden_track, segment.producer, 0, segment_length - 1) # -1, out incl.

                in_frame = segment.end_frame
                index += 1
            
            if hidden_track.get_length() < seq_len:
                edit._insert_blank(hidden_track, index, seq_len - hidden_track.get_length())

    def get_hit_segment(self, frame):
        for segment in self.segments:
            if segment.hit(frame) == True:
                return segment
        
        return None

    def get_covered_segments(self, range_start, range_end):
        covered = []
        for segment in self.segments:
            if segment.covered(range_start, range_end) == True:
                covered.append(segment)
        return covered

    def add_segment(self, seg_start, seg_end):
        seg = TimeLineSegment(seg_start, seg_end)
        _timeline_renderer.segments.append(seg)
        
    def remove_segments(self, remove_list):
        remaining_set = set(self.segments) - set(remove_list)
        self.segments = list(remaining_set)

    # ------------------------------------------------ RENDERING
    def update_timeline_rendering_status(self, rendering_file, fract, render_completed, completed_segments):
        dirty = self.get_dirty_segments()
        for segment in dirty:
            if segment.get_clip_path() == rendering_file:
                segment.rendered_fract = fract
            else:
                segment.maybe_set_completed(completed_segments)
                

class NoOpRenderer():

    
    def __init__(self):
        """
        Instead of multiple tests for editorstate.get_tline_rendering_mode() we implement TLINE_RENDERING_OFF mode 
        as (mostly) no-op timeline renderer.
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

    def focus_out(self):
        pass

    def update_hidden_track(self, hidden_track, seq_len):
        # This was required for some real random crashes long time ago, may not be needed anymore but we're keeping this.
        edit._insert_blank(hidden_track, 0, seq_len)


class TimeLineSegment:

    def __init__(self, start_frame, end_frame):
        self.segment_state = SEGMENT_UNRENDERED
        
        self.start_frame = start_frame # inclusive
        self.end_frame = end_frame # exclusive

        self.selected = False

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

        if self.selected:
            outline_color = (0.8, 0.8, 0.8)
        else:
            outline_color = (0, 0, 0)
            
        if self.segment_state == SEGMENT_DIRTY:
            cr.fill()
            
            rendered_w = int(self.rendered_fract * float(w))
            cr.set_source_rgb(*_segment_colors[SEGMENT_RENDERED])
            cr.rectangle(x, 0, rendered_w, height)
            cr.fill()

            cr.rectangle(x, 0, w ,height)
            cr.set_source_rgb(*outline_color)
            cr.stroke()
        else:
            cr.fill_preserve()
            cr.set_source_rgb(*outline_color)
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
        
        """
        # THIS IS USEFUL WHEN TESTING
        filter_info = mltfilters.get_colorize_filter_info()
        filter_object = current_sequence().create_filter(filter_info)
        self.producer.attach(filter_object.mlt_filter)
        self.producer.filters.append(filter_object)
        """

    def hit(self, frame):
        if frame >= self.start_frame and frame < self.end_frame:
            return True
        
        return False

    def covered(self, range_start, range_end):
        if range_start < self.start_frame and range_end >= self.end_frame:
            return True
        
        return False
        
    # ----------------------------------------- CONTENT HASH
    def update_segment(self):
        new_hash = self.get_content_hash()
        
        if new_hash != self.content_hash:
            if get_tline_rendering_mode() == appconsts.TLINE_RENDERING_AUTO:
                self.segment_state = SEGMENT_DIRTY
                self.producer = None
            # With mode TLINE_RENDERING_REQUEST:
            # - segment updates set segment state to SEGMENT_UNRENDERED
            # - user double clicks set segment state to SEGMENT_DIRTY and _that has already happened before we get here._
            # So if user has double clicked to make segment to beSEGMENT_DIRTY we will ignore chnaged hash but if user edit has changed timeline we will 
            # update segment state to be SEGMENT_UNRENDERED.
            elif get_tline_rendering_mode() == appconsts.TLINE_RENDERING_REQUEST and self.segment_state != SEGMENT_DIRTY: 

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
 
        # Marks segments with changed contents dirty.
        _timeline_renderer.update_segments()

        self.dirty_segments = _timeline_renderer.get_dirty_segments()
        
        if len(self.dirty_segments) == 0:
            return
        
        try:
            # Blocks untils renders are stopped and cleaned
            tlinerenderserver.abort_current_renders()
        except:
            # Dbus default timeout of 25s was exceeded, something is very wrong, no use to attempt further work.
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
        
        destroy_segments = []
        for segment in self.dirty_segments:
            if segment.start_frame >= current_sequence().seq_len:
                segment.segment_state = SEGMENT_RENDERED
                segment.rendered_fract = 0.0
                segment.content_hash = "-1"
                segment.producer = None # any attempt to display segments after sequence end should crash immediately, this will not be displayed.
                continue # there can be myltple of these
                
            clip_path = segment.get_clip_path()
            if os.path.isfile(clip_path) == True:
                # We came here with undo or redo or new edit that recreates existing content for segment
                segment.update_segment_as_rendered()
            else:
                # Clip for this content does not exist.
                # Cut down segment to end at sequence end.
                if segment.end_frame >= current_sequence().seq_len:
                    segment.end_frame = current_sequence().seq_len
                    if  segment.end_frame - segment.start_frame < 4:
                        # Min length for segments is for, if something gets cut shorter it gets destroyd.
                        destroy_segments.append(segment)
                        continue
                        
                    # We need to update content hash and clip path to match the newly cut segment.
                    segment.content_hash = segment.get_content_hash()
                    clip_path = segment.get_clip_path()

                segments_paths.append(clip_path)
                segments_ins.append(segment.start_frame)
                segments_outs.append(segment.end_frame)
        
        for seg in destroy_segments: # There can only be 1 of these but whatever.
            _timeline_renderer.segments.remove(seg)
        
        if len(segments_paths) == 0:
            # clips for all new dirty segments existed or all segments after sequence end (or both in some combination)
            Gdk.threads_enter()
            gui.tline_render_strip.widget.queue_draw()
            Gdk.threads_leave()
            return

        tlinerenderserver.render_update_clips(self.save_path, segments_paths, segments_ins, segments_outs, current_sequence().profile.description())

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

            time.sleep(0.5)
            
            if render_completed == 1: 
                running = False
    
        while get_renderer().all_segments_ready() == False:
            time.sleep(0.1)
            
        current_sequence().update_hidden_track_for_timeline_rendering() # We should have correct sequence length known because this always comes after edits.



# ---------------------------------------------------------------- settings
class TLineSettingsRenderDialog:
    def __init__(self):
        self.dialog = Gtk.Dialog(_("Timeline Render Settings"), gui.editor_window.window,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (_("Close"), Gtk.ResponseType.CLOSE))

        # Encoding
        self.enc_select = Gtk.ComboBoxText()
        encodings = renderconsumer.proxy_encodings
        if len(encodings) < 1: # no encoding options available, system does not have right codecs
            # display info ?
            pass
        for encoption in encodings:
            self.enc_select.append_text(encoption.name)
            
        current_enc = editorpersistance.prefs.tline_render_encoding
        if current_enc >= len(encodings): # current encoding selection not available
            current_enc = 0
            editorpersistance.prefs.tline_render_encoding = 0
            editorpersistance.save()

        self.enc_select.set_active(current_enc)
        self.enc_select.connect("changed", 
                                lambda w,e: self.encoding_changed(w.get_active()), 
                                None)
                            
        self.size_select = Gtk.ComboBoxText()
        self.size_select.append_text(_("Project Image Size"))
        self.size_select.append_text(_("Half Project Image Size"))
        self.size_select.append_text(_("Quarter Project Image Size"))
        self.size_select.set_active(editorpersistance.prefs.tline_render_size)
        self.size_select.connect("changed", 
                                lambda w,e: self.size_changed(w.get_active()), 
                                None)
                                
        row_enc = Gtk.HBox(False, 2)
        row_enc.pack_start(Gtk.Label(), True, True, 0)
        row_enc.pack_start(self.enc_select, False, False, 0)
        row_enc.pack_start(self.size_select, False, False, 0)
        row_enc.pack_start(Gtk.Label(), True, True, 0)
        
        vbox_enc = Gtk.VBox(False, 2)
        vbox_enc.pack_start(row_enc, False, False, 0)
        vbox_enc.pack_start(guiutils.pad_label(8, 12), False, False, 0)
        
        panel_encoding = guiutils.get_named_frame(_("Render Encoding"), vbox_enc)


        # Pane
        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(panel_encoding, False, False, 0)
        guiutils.set_margins(vbox, 8, 12, 12, 12)

        self.dialog.vbox.pack_start(vbox, True, True, 0)
        dialogutils.set_outer_margins(self.dialog.vbox)
        
        self.dialog.connect('response', dialogutils.dialog_destroy)
        self.dialog.show_all()


    def encoding_changed(self, enc_index):
        editorpersistance.prefs.tline_render_encoding = enc_index
        editorpersistance.save()

    def size_changed(self, size_index):
        editorpersistance.prefs.tline_render_size = size_index
        editorpersistance.save()
    
