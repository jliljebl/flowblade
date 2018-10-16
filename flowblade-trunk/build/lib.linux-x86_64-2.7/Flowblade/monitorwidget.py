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
from gi.repository import Gdk
from gi.repository import Gtk, GLib

import cairo
import mlt
import numpy as np
import os
import threading
import time

import appconsts
import cairoarea
import editorstate
from editorstate import PLAYER
from editorstate import PROJECT
import respaths
import utils

"""
Module is used to display trim views for Trim, Roll and Slip tools and selected match frames.
"""

DEFAULT_VIEW = 0
START_TRIM_VIEW = 1
END_TRIM_VIEW = 2
ROLL_TRIM_RIGHT_ACTIVE_VIEW = 3
ROLL_TRIM_LEFT_ACTIVE_VIEW = 4
SLIP_TRIM_RIGHT_ACTIVE_VIEW = 5
SLIP_TRIM_LEFT_ACTIVE_VIEW = 6
FRAME_MATCH_VIEW = 7

TC_LEFT_SIDE_PAD = 172
TC_RIGHT_SIDE_PAD = 28
TC_HEIGHT = 27
        
MATCH_FRAME = "match_frame.png"

MONITOR_INDICATOR_COLOR = utils.get_cairo_color_tuple_255_rgb(71, 131, 169)
MONITOR_INDICATOR_COLOR_MATCH = utils.get_cairo_color_tuple_255_rgb(21, 71, 105)

FRAME_MATCH_VIEW_COLOR = (0.3, 0.3, 0.3)

# Continuos match frame update
CONTINUOS_UPDATE_PAUSE = 0.2
_last_render_time = 0.0
_producer = None
_consumer = None
_frame_write_on = False
            
_widget = None

def _get_match_frame_path():
    return utils.get_hidden_user_dir_path() + appconsts.TRIM_VIEW_DIR + "/" + MATCH_FRAME
        
class MonitorWidget:
    
    def __init__(self):
        self.widget = Gtk.VBox()
        
        self.view = DEFAULT_VIEW
        self.match_frame_surface = None
        self.match_frame = -1
        self.edit_tline_frame = -1
        self.edit_delta = None
        self.edit_clip_start_on_tline = -1
        
        self.slip_clip_media_length = -1
        self.slip_clip_length = -1

        self.clip_name = "clip name"
    
        self.match_not_updateble = False # Roll and Slip need this flag to know if surface updates needed
        
        # top row
        self.top_row = Gtk.HBox()
        
        self.top_edge_panel = cairoarea.CairoDrawableArea2(1, 1, self._draw_top_panel, use_widget_bg=False)
        self.top_edge_panel.press_func = self._press_event
        self.top_row.pack_start(self.top_edge_panel, True, True,0)
        
        # mid row
        self.mid_row = Gtk.HBox()

        self.left_display = cairoarea.CairoDrawableArea2(1, 1, self._draw_match_frame_left, use_widget_bg=False)

        black_box = Gtk.EventBox()
        black_box.add(Gtk.Label())
        bg_color = Gdk.Color(red=0.0, green=0.0, blue=0.0)
        black_box.modify_bg(Gtk.StateType.NORMAL, bg_color)
        self.monitor = black_box

        self.right_display = cairoarea.CairoDrawableArea2(1, 1, self._draw_match_frame_right, use_widget_bg=False)
        
        self.mid_row.pack_start(self.left_display, False, False,0)
        self.mid_row.pack_start(self.monitor, True, True,0)
        self.mid_row.pack_start(self.right_display, False, False,0)
        
        # bottom row
        self.bottom_edge_panel = cairoarea.CairoDrawableArea2(1, 1, self._draw_bottom_panel, use_widget_bg=False)
        self.bottom_row = Gtk.HBox()
        self.bottom_row.pack_start(self.bottom_edge_panel, True, True,0)
        
        # build pane
        self.widget.pack_start(self.top_row, False, False,0)
        self.widget.pack_start(self.mid_row , True, True,0)
        self.widget.pack_start(self.bottom_row, False, False,0)

        self.CLOSE_MATCH_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "close_match.png")
        self.PATTERN_PRODUCER_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "pattern_producer_trim_view.png")
        self.BLANK_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "blank_trim_view.png")
    
        global _widget
        _widget = self

    # ------------------------------------------------------------------ INTERFACE
    def get_monitor(self):
        return self.monitor
        
    def is_active(self, attempting_trim=False):
        if editorstate.show_trim_view == appconsts.TRIM_VIEW_ON:
            return True
            
        if editorstate.show_trim_view == appconsts.TRIM_VIEW_OFF:
            return False
        
        if editorstate.show_trim_view == appconsts.TRIM_VIEW_SINGLE and attempting_trim:
            return True
        
        if (editorstate.show_trim_view == appconsts.TRIM_VIEW_SINGLE and 
            (self.view == START_TRIM_VIEW or self.view == END_TRIM_VIEW)):
                return True

        return False

    # ------------------------------------------------------------------ SET VIEW TYPE
    def set_default_view_force(self):
        self.set_default_view(True)

    def set_default_view(self, force_default_mode=False):
        if self.view == DEFAULT_VIEW:
            return

        if self.view == FRAME_MATCH_VIEW and force_default_mode==False:
            return
            
        # Refreshing player while rendering overwrites file on disk and loses 
        # previous rendered data. 
        if PLAYER().is_rendering:
            return

        # Delete match frame
        try:
            os.remove(_get_match_frame_path())
        except:
            # This fails when done first time ever  
            pass
        
        self.match_frame_surface = None
                
        self.view = DEFAULT_VIEW
        
        self.left_display.set_pref_size(1, 1)
        self.right_display.set_pref_size(1, 1)

        self.top_edge_panel.set_pref_size(1, 1)
        self.bottom_edge_panel.set_pref_size(1, 1)
        
        self.widget.queue_draw()
        PLAYER().refresh()

    def set_frame_match_view(self, match_clip, frame):        
        # Refreshing while rendering overwrites file on disk and loses 
        # previous rendered data. 
        if PLAYER().is_rendering:
            return

        # Delete match frame
        try:
            os.remove(_get_match_frame_path())
        except:
            # This fails when done first time ever  
            pass
        
        self.match_frame_surface = None
                
        self.view = FRAME_MATCH_VIEW
        
        self._layout_match_frame_left()
        self._layout_expand_edge_panels()
        
        cpath, cname = os.path.split(match_clip.path)
        self.clip_name = cname
        self.match_frame = frame
        
        match_frame_write_thread = MonitorMatchFrameWriter(match_clip.path, frame, 
                                                            MATCH_FRAME, self.match_frame_write_complete)
                                        
        match_frame_write_thread.start()
        
    def set_start_trim_view(self, match_clip, edit_clip_start):
        if self.is_active(True) == False:
            return

        # Refreshing while rendering overwrites file on disk and loses 
        # previous rendered data. 
        if PLAYER().is_rendering:
            return
           
        self.view = START_TRIM_VIEW
        self.match_frame_surface = None
        self.edit_clip_start_on_tline = edit_clip_start
        
        self._layout_match_frame_left()
        self._layout_expand_edge_panels()
        
        self.widget.queue_draw()
        PLAYER().refresh()

        if match_clip == None: # track last clip end trim and track first clip start trim
            self.match_frame = -1
            return
        
        if match_clip.is_blanck_clip == True:
            self.match_not_updateble = True
            self.create_blank_match_frame()
            return
        elif match_clip.media_type == appconsts.PATTERN_PRODUCER:
            self.match_not_updateble = True
            self.create_pattern_producer_match_frame()
            return

        self.match_frame = match_clip.clip_out
        self.match_not_updateble = False
        data = (match_clip.path, match_clip.clip_out, MATCH_FRAME, self.match_frame_write_complete)
        GLib.idle_add(_launch_match_frame_writer, data)
        
    def set_end_trim_view(self, match_clip, edit_clip_start):
        if self.is_active(True) == False:
            return

        # Refreshing while rendering overwrites file on disk and loses 
        # previous rendered data. 
        if PLAYER().is_rendering:
            return
        
        self.view = END_TRIM_VIEW
        self.match_frame_surface = None
        self.edit_clip_start_on_tline = edit_clip_start

        self._layout_match_frame_right()        
        self._layout_expand_edge_panels()
        
        self.widget.queue_draw()
        PLAYER().refresh()
        
        if match_clip == None: # track last end trim and track first start trim
            self.match_frame = -1
            return

        if match_clip.is_blanck_clip == True:
            self.match_not_updateble = True
            self.create_blank_match_frame()
            return
        elif match_clip.media_type == appconsts.PATTERN_PRODUCER:
            self.match_not_updateble = True
            self.create_pattern_producer_match_frame()
            return
            
        self.match_frame = match_clip.clip_in
        self.match_not_updateble = False
        data = (match_clip.path, match_clip.clip_in, MATCH_FRAME, self.match_frame_write_complete)
        GLib.idle_add(_launch_match_frame_writer, data)
        
    def set_roll_trim_right_active_view(self, match_clip, edit_clip_start):
        if self.is_active() == False:
            return

        # Refreshing while rendering overwrites file on disk and loses 
        # previous rendered data. 
        if PLAYER().is_rendering:
            return
        
        self.view = ROLL_TRIM_RIGHT_ACTIVE_VIEW
        self.match_frame_surface = None
        self.edit_clip_start_on_tline = edit_clip_start

        self._layout_match_frame_left()
        self._layout_expand_edge_panels()
        
        self.widget.queue_draw()
        PLAYER().refresh()
        
        if match_clip == None: # track last end trim and track first start trim
            self.match_frame = -1
            return
            
        if match_clip.is_blanck_clip == True:
            self.match_not_updateble = True
            self.create_blank_match_frame()
            return
        elif match_clip.media_type == appconsts.PATTERN_PRODUCER:
            self.match_not_updateble = True
            self.create_pattern_producer_match_frame()
            return
            
        self.match_frame = match_clip.clip_out
        self.match_not_updateble = False
        data = (match_clip.path, match_clip.clip_out, MATCH_FRAME, self.match_frame_write_complete)
        GLib.idle_add(_launch_match_frame_writer, data)
        
    def set_roll_trim_left_active_view(self, match_clip, edit_clip_start):
        if self.is_active() == False:
            return
            
        # Refreshing while rendering overwrites file on disk and loses 
        # previous rendered data. 
        if PLAYER().is_rendering:
            return
        
        self.view = ROLL_TRIM_LEFT_ACTIVE_VIEW
        self.match_frame_surface = None
        self.edit_clip_start_on_tline = edit_clip_start

        self._layout_match_frame_right()        
        self._layout_expand_edge_panels()
        
        self.widget.queue_draw()
        PLAYER().refresh()
        
        if match_clip == None: # track last end trim and track first start trim
            self.match_frame = -1
            return
    
        if match_clip.is_blanck_clip == True:
            self.match_not_updateble = True
            self.create_blank_match_frame()
            return
        elif match_clip.media_type == appconsts.PATTERN_PRODUCER:
            self.match_not_updateble = True
            self.create_pattern_producer_match_frame()
            return
            
        self.match_frame = match_clip.clip_in
        self.match_not_updateble = False
        data = (match_clip.path, match_clip.clip_in, MATCH_FRAME, self.match_frame_write_complete)
        GLib.idle_add(_launch_match_frame_writer, data)
        
    def set_slip_trim_right_active_view(self, match_clip):
        if self.is_active() == False:
            return

        # Refreshing while rendering overwrites file on disk and loses 
        # previous rendered data. 
        if PLAYER().is_rendering:
            return

        self.view = SLIP_TRIM_RIGHT_ACTIVE_VIEW
        self.match_frame_surface = None
        self.edit_clip_start_on_tline = 0 # We're using tiline frames just as units to get edit deltas and displayed clip tc
        
        self.slip_clip_media_length = match_clip.get_length() # This is media length
        self.slip_clip_length = match_clip.clip_length() # this in-out range length
        
        self._layout_match_frame_left()
        self._layout_expand_edge_panels()
        
        self.widget.queue_draw()
        PLAYER().refresh()
        
        if match_clip == None:
            self.match_frame = -1
            return

        self.match_frame = match_clip.clip_in
        self.edit_delta = 0

        if match_clip.media_type == appconsts.PATTERN_PRODUCER:
            self.match_not_updateble = True
            self.create_pattern_producer_match_frame()
            return

        self.match_not_updateble = False
        data = (match_clip.path, match_clip.clip_in, MATCH_FRAME, self.match_frame_write_complete)
        GLib.idle_add(_launch_match_frame_writer, data)

    def set_slip_trim_left_active_view(self, match_clip):
        if self.is_active() == False:
            return

        # Refreshing while rendering overwrites file on disk and loses 
        # previous rendered data. 
        if PLAYER().is_rendering:
            return
    
        self.view = SLIP_TRIM_LEFT_ACTIVE_VIEW
        self.match_frame_surface = None
        self.edit_clip_start_on_tline = 0 # We're using tiline frames just as units to get edit deltas and displayed clip tc
                                          # Computations here assume that clip media starts from frame = 0 and timeline frames are 
                                          # are actually clip frames for this trim view mode
                                          
        self.slip_clip_media_length = match_clip.get_length() # This is media length
        self.slip_clip_length = match_clip.clip_length() # this in-out range length
        
        self._layout_match_frame_right()
        self._layout_expand_edge_panels()
        
        self.widget.queue_draw()
        PLAYER().refresh()
        
        if match_clip == None:
            self.match_frame = -1
            return
        
        self.match_frame = match_clip.clip_out

        if match_clip.media_type == appconsts.PATTERN_PRODUCER:
            self.match_not_updateble = True
            self.create_pattern_producer_match_frame()
            return

        self.match_not_updateble = False
        data = (match_clip.path, match_clip.clip_out, MATCH_FRAME, self.match_frame_write_complete)
        GLib.idle_add(_launch_match_frame_writer, data)
        
    # ------------------------------------------------------------------ LAYOUT
    def _layout_expand_edge_panels(self):
        self.top_edge_panel.set_pref_size(*self.get_edge_row_panel_size())
        self.bottom_edge_panel.set_pref_size(*self.get_edge_row_panel_size())
 
    def _layout_match_frame_left(self):
        self.left_display.set_pref_size(*self.get_match_frame_panel_size())
        self.right_display.set_pref_size(1,1)

    def _layout_match_frame_right(self):
        self.left_display.set_pref_size(1,1)
        self.right_display.set_pref_size(*self.get_match_frame_panel_size())

    def get_edge_row_panel_size(self):
        monitor_alloc = self.widget.get_allocation()
        inv_profile_screen_ratio = float(PROJECT().profile.height()) / float(PROJECT().profile.width())
        screen_height = int(inv_profile_screen_ratio * monitor_alloc.width/2)
        edge_row_height = (monitor_alloc.height - screen_height)/2
        return (monitor_alloc.width, edge_row_height)

    def get_match_frame_panel_size(self):
        monitor_alloc = self.widget.get_allocation()
        inv_profile_screen_ratio = float(PROJECT().profile.height()) / float(PROJECT().profile.width())
        return (int(monitor_alloc.width/2), int(inv_profile_screen_ratio * monitor_alloc.width/2))

    # ----------------------------------------------------------------- MOUSE EVENTS
    def set_edit_tline_frame(self, edit_tline_frame, edit_delta):
        if self.is_active() == False:
            return

        if self.view == DEFAULT_VIEW:
            return

        self.edit_tline_frame = edit_tline_frame
        self.edit_delta = edit_delta
        self.bottom_edge_panel.queue_draw()

    def update_roll_match_frame(self):
        if self.is_active() == False:
            return

        if self.view == DEFAULT_VIEW:
            return

        match_frame = self.match_frame + self.edit_delta

        if self.match_not_updateble == True:
            return
        
        match_surface_creator = MatchSurfaceCreator(match_frame)
        match_surface_creator.start()

    def set_slip_edit_tline_frame(self, clip, edit_delta):
        if self.is_active() == False:
            return

        if self.view == DEFAULT_VIEW:
            return
        
        if self.view == SLIP_TRIM_RIGHT_ACTIVE_VIEW:
            mouse_clip_frame = clip.clip_out + edit_delta
        else:
            mouse_clip_frame = clip.clip_in + edit_delta

        self.edit_tline_frame = mouse_clip_frame
    
        self.edit_delta = edit_delta
        self.bottom_edge_panel.queue_draw()
    
        match_frame = self.match_frame + self.edit_delta

        if self.match_not_updateble == True:
            return
            
        match_surface_creator = MatchSurfaceCreator(match_frame)
        match_surface_creator.start()
            
    def one_roll_mouse_release(self, edit_tline_frame, edit_delta):
        if self.is_active() == False:
            return
            
        self.edit_tline_frame = edit_tline_frame
        if self.view == START_TRIM_VIEW: # were computing displayed edit side TC 
                                         # from current_tline_frame - clip_start_frame and clip_start_frame changes now if START_TRIM_VIEW
            self.edit_clip_start_on_tline = self.edit_clip_start_on_tline - edit_delta
        self.edit_delta = None
        self.bottom_edge_panel.queue_draw()
    
    def _press_event(self, event):
        """
        Mouse button callback
        """
        if self.view == FRAME_MATCH_VIEW:
           if  event.x > 4 and event.y > 4 and event.x < 28 and event.y < 28:
                self.set_default_view_force()
            
    # ------------------------------------------------------------------ MATCH FRAME
    def match_frame_write_complete(self, frame_name):
        self.match_frame_surface = self.create_match_frame_image_surface(frame_name)
        
        Gdk.threads_enter()
        self.left_display.queue_draw()
        self.right_display.queue_draw()
        Gdk.threads_leave()

    def create_pattern_producer_match_frame(self):        
        w, h = self.get_match_frame_panel_size()
        
        scaled_icon = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(scaled_icon)
        cr.scale(float(w) / float(self.PATTERN_PRODUCER_ICON.get_width()), float(h) / float(self.PATTERN_PRODUCER_ICON.get_height()))
        cr.set_source_surface(self.PATTERN_PRODUCER_ICON, 0, 0)
        cr.paint()
        
        self.match_frame_surface = scaled_icon

        self.left_display.queue_draw()
        self.right_display.queue_draw()

    def create_blank_match_frame(self):        
        w, h = self.get_match_frame_panel_size()
        
        scaled_icon = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(scaled_icon)
        cr.scale(float(w) / float(self.BLANK_ICON.get_width()), float(h) / float(self.BLANK_ICON.get_height()))
        cr.set_source_surface(self.BLANK_ICON, 0, 0)
        cr.paint()
        
        self.match_frame_surface = scaled_icon

        self.left_display.queue_draw()
        self.right_display.queue_draw()
        
    def create_match_frame_image_surface(self, frame_name):
        # Create non-scaled surface
        matchframe_path = utils.get_hidden_user_dir_path() + appconsts.TRIM_VIEW_DIR + "/" + frame_name 
        
        surface = cairo.ImageSurface.create_from_png(matchframe_path)

        # Create and return scaled surface
        profile_screen_ratio = float(PROJECT().profile.width()) / float(PROJECT().profile.height())
        match_frame_width, match_frame_height = self.get_match_frame_panel_size()
        
        scaled_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(match_frame_width), int(match_frame_height))
        cr = cairo.Context(scaled_surface)
        cr.scale(float(match_frame_width) / float(surface.get_width()), float(match_frame_height) / float(surface.get_height()))

        cr.set_source_surface(surface, 0, 0)
        cr.paint()
        
        return scaled_surface
    
    def _get_cairo_buf_from_mlt_rgb(self, screen_rgb_data, img_w, img_h ):
        buf = np.fromstring(screen_rgb_data, dtype=np.uint8)
        buf.shape = (img_h + 1, img_w, 4) # +1 in h, seemeed to need it
        out = np.copy(buf)
        r = np.index_exp[:, :, 0]
        b = np.index_exp[:, :, 2]
        out[r] = buf[b]
        out[b] = buf[r]
        return out
        
    # ------------------------------------------------------------------ DRAW
    def _draw_match_frame_left(self, event, cr, allocation):
        if self.view == END_TRIM_VIEW or self.view == ROLL_TRIM_LEFT_ACTIVE_VIEW:
            return

        x, y, w, h = allocation

        if self.match_frame_surface == None:
            # Draw black
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.rectangle(0, 0, w, h)
            cr.fill()
        else:
            # Draw match frame
            cr.set_source_surface(self.match_frame_surface, 0, 0)
            cr.paint()

    def _draw_match_frame_right(self, event, cr, allocation):
        if self.view == START_TRIM_VIEW or self.view == ROLL_TRIM_RIGHT_ACTIVE_VIEW:
            return
            
        x, y, w, h = allocation

        if self.match_frame_surface == None:
            # Draw black
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.rectangle(0, 0, w, h)
            cr.fill()
        else:
            # Draw match frame
            cr.set_source_surface(self.match_frame_surface, 0, 0)
            cr.paint()
            
    def _draw_top_panel(self, event, cr, allocation):
        x, y, w, h = allocation

        # Draw bg
        cr.set_source_rgb(0.0, 0.0, 0.0)
        if self.view == FRAME_MATCH_VIEW:
            cr.set_source_rgb(*FRAME_MATCH_VIEW_COLOR)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # if were minimized, stop
        if h == 1:
            return
            
        # Draw screen info 
        cr.set_source_rgb(*MONITOR_INDICATOR_COLOR)
        if self.view == START_TRIM_VIEW or self.view == ROLL_TRIM_RIGHT_ACTIVE_VIEW or self.view == SLIP_TRIM_RIGHT_ACTIVE_VIEW:
            cr.rectangle(w/2, h - 4, w/2, 4)
            cr.fill()
            if self.view != START_TRIM_VIEW:
                cr.set_source_rgb(*MONITOR_INDICATOR_COLOR_MATCH)
                cr.rectangle(0, h - 4, w/2, 4)
                cr.fill()
        elif self.view == FRAME_MATCH_VIEW:
            cr.select_font_face ("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(21)
            cr.move_to(5, h - 20)
            cr.show_text(str(self.clip_name))
            cr.set_source_surface(self.CLOSE_MATCH_ICON, 5, 5)
            cr.paint()
        else:
            cr.rectangle(0, h - 4, w/2, 4)
            cr.fill()
            if self.view != END_TRIM_VIEW:
                cr.set_source_rgb(*MONITOR_INDICATOR_COLOR_MATCH)
                cr.rectangle(w/2, h - 4, w/2, 4)
                cr.fill()
            
    def _draw_bottom_panel(self, event, cr, allocation):
        x, y, w, h = allocation

        # Draw bg
        cr.set_source_rgb(0.0, 0.0, 0.0)
        if self.view == FRAME_MATCH_VIEW:
            cr.set_source_rgb(*FRAME_MATCH_VIEW_COLOR)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # if were minimized, stop
        if w == 1:
            return

        if self.view == START_TRIM_VIEW or self.view == END_TRIM_VIEW:
            self._draw_bottom_panel_one_roll(event, cr, allocation)
        elif self.view == ROLL_TRIM_RIGHT_ACTIVE_VIEW or self.view == ROLL_TRIM_LEFT_ACTIVE_VIEW:
            self._draw_bottom_panel_two_roll(event, cr, allocation)
        elif self.view == SLIP_TRIM_RIGHT_ACTIVE_VIEW or self.view == SLIP_TRIM_LEFT_ACTIVE_VIEW:
            self._draw_bottom_panel_slip(event, cr, allocation)
        elif self.view == FRAME_MATCH_VIEW:
            cr.set_source_rgb(*MONITOR_INDICATOR_COLOR)
            cr.select_font_face ("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(21)
            cr.move_to(5, 35)
            cr.show_text(utils.get_tc_string(self.match_frame))

    def _draw_bottom_panel_one_roll(self, event, cr, allocation):
        x, y, w, h = allocation

        # Draw active screen indicator and compute tc and frame delta positions
        cr.set_source_rgb(*MONITOR_INDICATOR_COLOR)

        match_tc_x = 0
        edit_tc_x = 0
        delta_frames_x = 0
        if self.view == START_TRIM_VIEW:
            cr.rectangle(w/2, 0, w/2, 4)

            delta_frames_x = (w/2) + 8
        elif self.view == END_TRIM_VIEW:
            cr.rectangle(0, 0, w/2, 4)

            delta_frames_x = (w/2) - 20
            # move left for every additional digit after ones
            CHAR_WIDTH = 12
            delta_frames_x = delta_frames_x - ((len(str(self.edit_delta)) - 1) * CHAR_WIDTH)
        cr.fill()
        
        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.select_font_face ("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(21)
        
        if self.edit_delta != None:
            cr.move_to(delta_frames_x, TC_HEIGHT + 30)
            cr.show_text(str(self.edit_delta))

        self._draw_range_mark(cr,(w/2) - 10, 14, -1)
        self._draw_range_mark(cr,(w/2) + 10, 14, 1)

    def _draw_bottom_panel_two_roll(self, event, cr, allocation):
        x, y, w, h = allocation

        # Draw active screen indicator and compute tc and frame delta positions
        cr.set_source_rgb(*MONITOR_INDICATOR_COLOR)
       
        match_tc_x = 0
        edit_tc_x = 0
        delta_frames_x = 0
        if self.view == ROLL_TRIM_RIGHT_ACTIVE_VIEW:
            cr.rectangle(w/2, 0, w/2, 4)
            cr.fill()
            cr.set_source_rgb(*MONITOR_INDICATOR_COLOR_MATCH)
            cr.rectangle(0, 0, w/2, 4)
            cr.fill()
                                
            delta_frames_x = (w/2) + 8
        elif self.view == ROLL_TRIM_LEFT_ACTIVE_VIEW:
            cr.rectangle(0, 0, w/2, 4)
            cr.fill()
            cr.set_source_rgb(*MONITOR_INDICATOR_COLOR_MATCH)
            cr.rectangle(w/2, 0, w/2, 4)
            cr.fill()

            delta_frames_x = (w/2) - 20
            # move left for every additional digit after ones
            CHAR_WIDTH = 12
            delta_frames_x = delta_frames_x - ((len(str(self.edit_delta)) - 1) * CHAR_WIDTH)

        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.select_font_face ("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(21)

        if self.edit_delta != None:
            cr.move_to(delta_frames_x, TC_HEIGHT + 30)
            cr.show_text(str(self.edit_delta))

        self._draw_range_mark(cr,(w/2) - 10, 14, -1)
        self._draw_range_mark(cr,(w/2) + 10, 14, 1)

    def _draw_bottom_panel_slip(self, event, cr, allocation):
        x, y, w, h = allocation

        # Draw active screen indicator and compute tc and frame delta positions
        cr.set_source_rgb(*MONITOR_INDICATOR_COLOR)
       
        match_tc_x = 0
        edit_tc_x = 0
        delta_frames_x = 0
        if self.view == SLIP_TRIM_RIGHT_ACTIVE_VIEW:
            cr.rectangle(w/2, 0, w/2, 4)
            cr.fill()
            cr.set_source_rgb(*MONITOR_INDICATOR_COLOR_MATCH)
            cr.rectangle(0, 0, w/2, 4)
            cr.fill()

            delta_frames_x = (w/2) + 8
        elif self.view == SLIP_TRIM_LEFT_ACTIVE_VIEW:
            cr.rectangle(0, 0, w/2, 4)
            cr.fill()
            cr.set_source_rgb(*MONITOR_INDICATOR_COLOR_MATCH)
            cr.rectangle(w/2, 0, w/2, 4)
            cr.fill()

            delta_frames_x = (w/2) - 20
            # move left for every additional digit after ones
            CHAR_WIDTH = 12
            delta_frames_x = delta_frames_x - ((len(str(self.edit_delta)) - 1) * CHAR_WIDTH)

        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.select_font_face ("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(21)

        delta_corr = 0
        if self.match_frame != -1:
            disp_match_frame = self.match_frame + self.edit_delta
            if disp_match_frame < 0:
                delta_corr = disp_match_frame
                disp_match_frame = 0

            if disp_match_frame >= self.slip_clip_media_length:
                delta_corr = disp_match_frame - self.slip_clip_media_length - 1
                disp_match_frame = self.slip_clip_media_length - 1

        if self.edit_delta != None:
            cr.move_to(delta_frames_x, TC_HEIGHT + 30)
            cr.show_text(str(-self.edit_delta + delta_corr))

        self._draw_range_mark(cr,(w/2) - 10, 14, 1)
        self._draw_range_mark(cr,(w/2) + 10, 14, -1)
        
    def _draw_black(self, event, cr, allocation):
        x, y, w, h = allocation  

        # Draw bg
        cr.set_source_rgb(0.0, 0.0, 0.0)
        cr.rectangle(0, 0, w, h)
        cr.fill()

    def _draw_red(self, event, cr, allocation):
        # testing
        x, y, w, h = allocation

        # Draw bg
        cr.set_source_rgb(1.0, 0.0, 0.0)
        cr.rectangle(0, 0, w, h)
        cr.fill()
    
    def _draw_range_mark(self, cr, x, y, dir_mult):
        cr.move_to (x + 8 * dir_mult, y)
        cr.line_to (x, y)
        cr.line_to (x, y + 10)
        cr.line_to (x + 8 * dir_mult, y + 10)
        cr.set_source_rgb(0.65, 0.65, 0.7)
        cr.set_line_width(4.0)
        cr.stroke()
        
        


    
# ---------------------------------------------------------------------------------- match frame cration
def _launch_match_frame_writer(data):
    match_clip_path, clip_frame, frame_name, callback = data        

    match_frame_write_thread = MonitorMatchFrameWriter(match_clip_path, clip_frame, frame_name, callback)
    match_frame_write_thread.start()


class MonitorMatchFrameWriter(threading.Thread):
    def __init__(self, clip_path, clip_frame, frame_name, completion_callback):
        self.clip_path = clip_path
        self.clip_frame = clip_frame
        self.completion_callback = completion_callback
        self.frame_name = frame_name
        threading.Thread.__init__(self)
        
    def run(self):
        """
        Writes thumbnail image from file producer
        """
        # Create consumer
        matchframe_path = utils.get_hidden_user_dir_path() + appconsts.TRIM_VIEW_DIR + "/" + self.frame_name
        consumer = mlt.Consumer(PROJECT().profile, "avformat", matchframe_path)
        consumer.set("real_time", 0)
        consumer.set("vcodec", "png")

        # Create one frame producer
        producer = mlt.Producer(PROJECT().profile, str(self.clip_path))
        producer.set("mlt_service", "avformat-novalidate")
        producer = producer.cut(int(self.clip_frame), int(self.clip_frame))

        # Delete match frame
        try:
            os.remove(matchframe_path)
        except:
            # This fails when done first time ever  
            pass
        
        # Save producer and consumer for view needing continues match frame update
        global _producer, _consumer
        if _widget.view != START_TRIM_VIEW and _widget.view != END_TRIM_VIEW:
            _producer = producer
            _consumer = consumer

        # Connect and write image
        consumer.connect(producer)
        consumer.run()
        
        # Wait until new file exists
        while os.path.isfile(matchframe_path) != True:
            time.sleep(0.1)

        # Do completion callback
        self.completion_callback(self.frame_name)


class MatchSurfaceCreator(threading.Thread):
    def __init__(self, match_frame):
        self.match_frame = match_frame
        threading.Thread.__init__(self)
        
    def run(self):
        # Create new producer to get mlt frame data
        while _producer == None:
            print "MatchSurfaceCreator: waiting for _producer"
            time.sleep(0.01)
            
        image_producer = _producer.cut(int(self.match_frame), int(self.match_frame))
        image_producer.set_speed(0)
        image_producer.seek(0)
        
        # Get MLT rgb frame data
        frame = image_producer.get_frame()
        # And make sureto deinterlace if input is interlaced
        frame.set("consumer_deinterlace", 1)
        size = _widget.get_match_frame_panel_size()
        mlt_rgb = frame.get_image(mlt.mlt_image_rgb24a, *size) 
   
        # Create cairo surface
        cairo_buf = _widget._get_cairo_buf_from_mlt_rgb(mlt_rgb, *size)
        img_w, img_h = size
        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_RGB24, img_w)
        surface = cairo.ImageSurface.create_for_data(cairo_buf, cairo.FORMAT_RGB24, img_w, img_h, stride)
        
        _widget.match_frame_surface = surface
        
        # Repaint
        Gdk.threads_enter()
        _widget.left_display.queue_draw()
        _widget.right_display.queue_draw()
        Gdk.threads_leave()
        
        
        
