"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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
Module contains an object that is used to do playback from mlt.Producers to
a Xwindow of a GTK+ widget and os audiosystem using a SDL consumer.
"""
from gi.repository import Gdk

try:
    import mlt7 as mlt
except:
    import mlt
    
import os
import time

import gui
from editorstate import timeline_visible
import editorpersistance
import utilsgtk
import updater

TICKER_DELAY = 250 # in millis
RENDER_TICKER_DELAY = 0.05
SLOWMO_FRAME_DELAY = 0.1

class Player:
    
    def __init__(self, profile):

        self.init_for_profile(profile)
        self.last_slowmo_seektime = 0.0
        self.slowmo_ticker = None
        self.consumer = None
            
    def init_for_profile(self, profile):
        # Get profile and create ticker for playback GUI updates
        self.profile = profile
        print("Player initialized with profile: ", self.profile.description())
        
        # Trim loop preview
        self.loop_start = -1
        self.loop_end = -1
        self.is_looping = False
        
    def create_sdl_consumer(self, use_sdl2_consumer):
        """
        Creates consumer with sdl output to a gtk+ widget.
        """

        # Create consumer and set params
        if use_sdl2_consumer == True:
            print("Create SDL2 consumer...")
            self.consumer = mlt.Consumer(self.profile, "sdl2")
            self.consumer.set("window_id", self.window_xid)
            w = gui.tline_display.get_allocated_width()
            h = gui.tline_display.get_allocated_height()
            self.consumer.set("window_width", w)
            self.consumer.set("window_height", h)
        else:
            print("Create SDL1 consumer...")
            self.consumer = mlt.Consumer(self.profile, "sdl")
            # SDL 1 consumer uses env param to communicate 
        self.consumer.set("real_time", 1)
        self.consumer.set("rescale", "bicubic") # MLT options "nearest", "bilinear", "bicubic", "hyper"
        self.consumer.set("resize", 1)
        self.consumer.set("progressive", 1)

        self.start_ticker()
        
        # Hold ref to switch back from rendering
        self.sdl_consumer = self.consumer 

    def display_resized(self):
        if self.consumer != None:
            w = gui.tline_display.get_allocated_width()
            h = gui.tline_display.get_allocated_height()
            self.consumer.set("window_width", w)
            self.consumer.set("window_height", h)

    def set_scrubbing(self, scrubbing_active):
        if scrubbing_active == True:
            self.consumer.set("scrub_audio", 1)
        else:
            self.consumer.set("scrub_audio", 0)
            
    def set_sdl_xwindow(self, widget):
        """
        Connects SDL output to display widget's xwindow
        """
        self.window_xid = widget.get_window().get_xid()
        #os.putenv('SDL_WINDOWID', str(widget.get_window().get_xid()))
        #Gdk.flush()

    def set_tracktor_producer(self, tractor):
        """
        Sets a MLT producer from multitrack timeline to be displayed.
        """
        self.tracktor_producer = tractor
        self.producer = tractor
       
    def display_tractor_producer(self):
        self.producer = self.tracktor_producer
        self.connect_and_start()

    def refresh(self): # Window events need this to get picture back
        if self.consumer == None:
            return 

        self.stop_timer_slowmo_playback()

        self.consumer.stop()
        self.consumer.start()
        
    def is_stopped(self):
        if self.slowmo_ticker != None:
            return False
            
        return (self.producer.get_speed() == 0)
        
    def stop_consumer(self):
        if not self.consumer.is_stopped():
            self.consumer.stop()

    def connect_and_start(self):
        """
        Connects current procer and consumer and
        """
        self.stop_timer_slowmo_playback()
        
        self.consumer.purge()
        self.producer.set_speed(0)
        self.consumer.connect(self.producer)
        self.consumer.start()

    def start_playback(self):
        """
        Starts playback from current producer
        """
        self.stop_timer_slowmo_playback()
        
        self.producer.set_speed(1)
        self.stop_ticker()
        self.start_ticker()

    def get_speed(self):
        if self.slowmo_ticker != None:
            return self.slowmo_ticker.data
        
        return self.producer.get_speed()

    def start_variable_speed_playback(self, speed):
        """
        Starts playback from current producer
        """
        self.stop_timer_slowmo_playback()
        
        self.producer.set_speed(speed)
        self.stop_ticker()
        self.start_ticker()

    def start_timer_slowmo_playback(self, speed, fps):
        self.stop_timer_slowmo_playback()
        
        frames = speed * fps
        update_delay = abs(int(1000.0 / frames))
        
        self.slowmo_ticker = utilsgtk.GtkTicker(self._slowmo_plyback_ticker_event, update_delay, speed)
        self.slowmo_ticker.start_ticker()
    
    def _slowmo_plyback_ticker_event(self, speed):
        if speed > 0.0:
            self.seek_delta_from_timer_slowmo(1)
        else:
            self.seek_delta_from_timer_slowmo(-1)

    def stop_timer_slowmo_playback(self):
        if self.slowmo_ticker != None:
            self.stop_ticker()
            self.slowmo_ticker.destroy_ticker()
            self.slowmo_ticker = None

    def stop_playback(self):
        """
        Stops playback from current producer
        """
        self.stop_timer_slowmo_playback()
        
        self.loop_start = -1 # User possibly goes into marks looping but stops without Control key.
        self.loop_end = -1
        self.is_looping = False

        self.stop_ticker()
        self.producer.set_speed(0)
        updater.update_frame_displayers(self.producer.frame())

    def start_loop_playback(self, cut_frame, loop_half_length, track_length):
        self.stop_timer_slowmo_playback()
        
        self.loop_start = cut_frame - loop_half_length
        self.loop_end = cut_frame + loop_half_length
        if self.loop_start < 0:
            self.loop_start = 0
        if self.loop_end >= track_length:
            self.loop_end = track_length - 1
        self.is_looping = True
        self.seek_frame(self.loop_start, False)
        self.producer.set_speed(1)
        self.stop_ticker()
        self.start_ticker()

    def start_loop_playback_range(self, range_in, range_out):
        self.stop_timer_slowmo_playback()
        
        seq_len = self.producer.get_length()
        if range_in >= seq_len:
            return
        if range_out > seq_len:
            range_out = seq_len
        
        self.loop_start = range_in
        self.loop_end = range_out
        
        self.is_looping = True
        self.seek_frame(self.loop_start, False)
        self.producer.set_speed(1)
        self.stop_ticker()
        self.start_ticker()

    def stop_loop_playback(self, looping_stopped_callback):
        """
        Stops playback from current producer
        """
        self.stop_timer_slowmo_playback()
        
        self.loop_start = -1
        self.loop_end = -1
        self.is_looping = False
        self.producer.set_speed(0)
        self.stop_ticker()
        looping_stopped_callback() # Re-creates hidden track that was cleared for looping playback

    def looping(self):
        return self.is_looping

    def current_frame(self):
        return self.producer.frame()
    
    def seek_position_normalized(self, pos, length):
        self.stop_timer_slowmo_playback()
        
        frame_number = pos * length
        self.seek_frame(int(frame_number)) 

    def seek_delta(self, delta):
        self.stop_timer_slowmo_playback()
        
        # Get new frame
        frame = self.producer.frame() + delta
        # Seek frame
        self.seek_frame(frame)

    def seek_delta_from_timer_slowmo(self, delta):
        # Get new frame
        frame = self.producer.frame() + delta
        # Seek frame
        self.seek_frame(frame, True, False)
        
    def slowmo_seek_delta(self, delta):
        self.stop_timer_slowmo_playback()
        
        now = time.time()
        if (now - self.last_slowmo_seektime) > SLOWMO_FRAME_DELAY:
            self.last_slowmo_seektime = now
            frame = self.producer.frame() + delta
            # Seek frame
            self.seek_frame(frame)

    def seek_frame(self, frame, update_gui=True, stop_slowmo_timer=True):
        if stop_slowmo_timer == True:
            self.stop_timer_slowmo_playback()
        
        # Force range
        length = self.get_active_length()
        if frame < 0:
            frame = 0
        elif frame >= length:
            frame = length - 1

        self.producer.set_speed(0)
        self.producer.seek(frame) 

        # GUI update path starts here.
        # All user or program initiated seeks go through this method.
        if update_gui:
            updater.update_frame_displayers(frame)

    def seek_end(self, update_gui=True):
        self.stop_timer_slowmo_playback()
        
        length = self.get_active_length()
        last_frame = length - 1
        self.seek_frame(last_frame, update_gui)

    def seek_and_get_rgb_frame(self, frame, update_gui=True):
        self.stop_timer_slowmo_playback()
        
        # Force range
        length = self.get_active_length()
        if frame < 0:
            frame = 0
        elif frame >= length:
            frame = length - 1

        self.producer.set_speed(0)
        self.producer.seek(frame) 

        # GUI update path starts here.
        if update_gui:
            updater.update_frame_displayers(frame)
            
        frame = self.producer.get_frame()
        # And make sure we deinterlace if input is interlaced.
        frame.set("consumer_deinterlace", 1)

        # Now we are ready to get the image and save it.        
        rgb = frame.get_image(int(mlt.mlt_image_rgba), int(self.profile.width()), int(self.profile.height()))
        return rgb

    def display_inside_sequence_length(self, new_seq_len):
        if self.producer.frame() > new_seq_len:
            self.seek_frame(new_seq_len)

    def is_playing(self):
        if self.slowmo_ticker != None:
            return True

        return (self.producer.get_speed() != 0)

    def _ticker_event(self, unused_data):
        current_frame = self.producer.frame()
        
        loop_clips = editorpersistance.prefs.loop_clips
        if loop_clips and current_frame >= self.get_active_length() and timeline_visible() == False: # Looping for clips
            self.seek_frame(0, False) #NOTE: False==GUI not updated
            self.producer.set_speed(1)
            updater.update_frame_displayers(current_frame)
            return

        # Stop ticker if playback has stopped.
        if (self.consumer.is_stopped() or self.producer.get_speed() == 0):
            if self.slowmo_ticker == None:
                self.stop_ticker()

        # If we're out of active range seek end.
        if current_frame >= self.get_active_length():
            self.seek_frame(current_frame)
            return

        # If trim looping and past loop end, start from loop start
        if ((not(self.loop_start == -1)) and 
            ((current_frame >= self.loop_end)
            or (current_frame >= self.get_active_length()))):
            self.seek_frame(self.loop_start, False) #NOTE: False==GUI not updated
            self.producer.set_speed(1)

        # Frame displayers update
        if timeline_visible() == False:
            updater.update_frame_displayers(current_frame)
        else:
            # If prefs set and frame out tline view, move tline view
            range_moved = updater.maybe_move_playback_tline_range(current_frame) # range_moved flag returned just to avoid two updates
            if range_moved == False:
                # Just display tline
                updater.update_frame_displayers(current_frame)
        
    def get_active_length(self):
        # Displayed range is different
        # for timeline and clip displays
        if timeline_visible():
            return self.producer.get_length()
        else:
            return gui.pos_bar.producer.get_length()

    def shutdown(self):
        self.stop_ticker()
        self.stop_timer_slowmo_playback()
        self.producer.set_speed(0)
        self.consumer.stop()

    def start_ticker(self):
        self.ticker = utilsgtk.GtkTicker(self._ticker_event, TICKER_DELAY)
        self.ticker.start_ticker()
    
    def stop_ticker(self):
        self.ticker.destroy_ticker()


    
    


        
