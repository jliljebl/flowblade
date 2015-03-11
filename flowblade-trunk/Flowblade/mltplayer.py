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
Module contains an object that is used to do playback from mlt.Producers to
a Xwindow of a GTK+ widget and os audiosystem using a SDL consumer.
"""

import pygtk
pygtk.require('2.0');
import gtk

import mlt
import os
import time

import gui
import editorpersistance
from editorstate import timeline_visible
import editorstate
import utils
import updater

TICKER_DELAY = 0.25
RENDER_TICKER_DELAY = 0.05

class Player:
    
    def __init__(self, profile):
    
        self.init_for_profile(profile)
        
        self.ticker = utils.Ticker(self._ticker_event, TICKER_DELAY)
            
    def init_for_profile(self, profile):
        # Get profile and create ticker for playback GUI updates
        self.profile = profile
        print "Player initialized with profile: ", self.profile.description()
        
        # Trim loop preview
        self.loop_start = -1
        self.loop_end = -1
        self.is_looping = False
        
        # Rendering
        self.is_rendering = False
        self.render_stop_frame = -1
        self.render_start_frame = -1
        self.render_callbacks = None
        self.wait_for_producer_end_stop = True
        self.render_gui_update_count = 0

        # JACK audio
        self.jack_output_filter = None
        
    def create_sdl_consumer(self):
        """
        Creates consumer with sdl output to a gtk+ widget.
        """
        # Create consumer and set params
        self.consumer = mlt.Consumer(self.profile, "sdl")
        self.consumer.set("real_time", 1)
        self.consumer.set("rescale", "bicubic") # MLT options "nearest", "bilinear", "bicubic", "hyper"
        self.consumer.set("resize", 1)
        self.consumer.set("progressive", 1)

        # Hold ref to switch back from rendering
        self.sdl_consumer = self.consumer 
        
    def set_sdl_xwindow(self, widget):
        """
        Connects SDL output to display widget's xwindow
        """
        os.putenv('SDL_WINDOWID', str(widget.window.xid))
        gtk.gdk.flush()
    
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
        self.consumer.stop()
        self.consumer.start()

    def is_stopped(self):
        return (self.producer.get_speed() == 0)
        
    def stop_consumer(self):
        if not self.consumer.is_stopped():
            self.consumer.stop()

    def connect_and_start(self):
        """
        Connects current procer and consumer and
        """
        self.consumer.purge()
        self.producer.set_speed(0)
        self.consumer.connect(self.producer)
        self.consumer.start()

    def start_playback(self):
        """
        Starts playback from current producer
        """
        self.producer.set_speed(1)
        self.ticker.stop_ticker()
        self.ticker.start_ticker()
        
    def start_variable_speed_playback(self, speed):
        """
        Starts playback from current producer
        """
        #print speed
        self.producer.set_speed(speed)
        self.ticker.stop_ticker()
        self.ticker.start_ticker()

    def stop_playback(self):
        """
        Stops playback from current producer
        """
        self.ticker.stop_ticker()
        self.producer.set_speed(0)
        updater.update_frame_displayers(self.producer.frame())
        updater.maybe_autocenter()

    def start_loop_playback(self, cut_frame, loop_half_length, track_length):
        self.loop_start = cut_frame - loop_half_length
        self.loop_end = cut_frame + loop_half_length
        if self.loop_start < 0:
            self.loop_start = 0
        if self.loop_end >= track_length:
            self.loop_end = track_length - 1
        self.is_looping = True
        self.seek_frame(self.loop_start, False)
        self.producer.set_speed(1)
        self.ticker.stop_ticker()
        self.ticker.start_ticker()

    def stop_loop_playback(self, looping_stopped_callback):
        """
        Stops playback from current producer
        """
        self.loop_start = -1
        self.loop_end = -1
        self.is_looping = False
        self.producer.set_speed(0)
        self.ticker.stop_ticker()
        looping_stopped_callback() # Re-creates hidden track that was cleared for looping playback

    def looping(self):
        return self.is_looping

    def current_frame(self):
        return self.producer.frame()
    
    def seek_position_normalized(self, pos, length):
        frame_number = pos * length
        self.seek_frame(int(frame_number)) 

    def seek_delta(self, delta):
        # Get new frame
        frame = self.producer.frame() + delta
        # Seek frame
        self.seek_frame(frame)
    
    def seek_frame(self, frame, update_gui=True):
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

    def seek_and_get_rgb_frame(self, frame, update_gui=True):
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
            
        frame = self.producer.get_frame()
        # And make sure we deinterlace if input is interlaced
        frame.set("consumer_deinterlace", 1)

        # Now we are ready to get the image and save it.
        size = (self.profile.width(), self.profile.height())
        rgb = frame.get_image(mlt.mlt_image_rgb24a, *size) 
        return rgb

    def display_inside_sequence_length(self, new_seq_len):
        if self.producer.frame() > new_seq_len:
            self.seek_frame(new_seq_len)

    def is_playing(self):
        return (self.producer.get_speed() != 0)

    def _ticker_event(self):
        # Stop ticker if playback has stopped.
        if (self.consumer.is_stopped() or self.producer.get_speed() == 0):
            self.ticker.stop_ticker()

        current_frame = self.producer.frame()
        
        # Stop rendering if last frame reached.
        if self.is_rendering == True and current_frame >= self.render_stop_frame:
            self.stop_rendering()
            return

        # If we're currently rendering, set progress bar and exit event handler.
        if self.is_rendering:
            if (self.producer.get_length() - 1) < 1:
                render_fraction = 1.0
            else:
                render_fraction = ((float(current_frame - self.render_start_frame)) / 
                  (float(self.render_stop_frame - self.render_start_frame)))
            self.render_gui_update_count = self.render_gui_update_count + 1
            if self.render_gui_update_count % 8 == 0: # we need quick updates for stop accuracy, but slower gui updating
                self.render_gui_update_count = 1
                gtk.gdk.threads_enter()
                self.render_callbacks.set_render_progress_gui(render_fraction)
                gtk.gdk.threads_leave()
            return 

        # If we're out of active range seek end.
        if current_frame >= self.get_active_length():
            gtk.gdk.threads_enter()
            self.seek_frame(current_frame)
            gtk.gdk.threads_leave()
            return

        # If trim looping and past loop end, start from loop start
        if ((not(self.loop_start == -1)) and 
            ((current_frame >= self.loop_end)
            or (current_frame >= self.get_active_length()))):
            self.seek_frame(self.loop_start, False) #NOTE: False==GUI not updated
            self.producer.set_speed(1)

        gtk.gdk.threads_enter()
        updater.update_frame_displayers(current_frame)
        gtk.gdk.threads_leave()
        
    def get_active_length(self):
        # Displayed range is different
        # for timeline and clip displays
        if timeline_visible():
            return self.producer.get_length()
        else:
            return gui.pos_bar.producer.get_length()

    def get_render_fraction(self):
        if self.render_stop_frame == -1:
            return float(self.producer.frame()) / float(self.producer.get_length() - 1)
        else:
            return float(self.producer.frame() - self.render_start_frame) / float(self.render_stop_frame - self.render_start_frame)
    
    def set_render_callbacks(self, callbacks):
        # Callbacks object interface:
        #
        # callbacks = utils.EmptyClass()
        # callbacks.set_render_progress_gui(fraction)
        # callbacks.save_render_start_time()
        # callbacks.exit_render_gui()
        # callbacks.maybe_open_rendered_file_in_bin()
        self.render_callbacks = callbacks

    def start_rendering(self, render_consumer, start_frame=0, stop_frame=-1):
        if stop_frame == -1:
            stop_frame = self.producer.get_length() - 1
        
        if stop_frame >= self.producer.get_length() - 1:
            self.wait_for_producer_end_stop = True
        else:
            self.wait_for_producer_end_stop = False
                
        print "start_rendering(), start frame :" + str(start_frame) + ", stop_frame: " + str(stop_frame)
        self.ticker.stop_ticker()
        self.consumer.stop()
        self.producer.set_speed(0)
        self.producer.seek(start_frame)
        time.sleep(0.5) # We need to be at correct frame before starting rendering or firts frame may get dropped
        self.render_start_frame = start_frame
        self.render_stop_frame = stop_frame
        self.consumer = render_consumer
        self.consumer.connect(self.producer)
        self.consumer.start()
        self.producer.set_speed(1)
        self.is_rendering = True
        self.render_callbacks.save_render_start_time()
        self.ticker.start_ticker(RENDER_TICKER_DELAY)

    def stop_rendering(self):
        print "stop_rendering, producer frame: " + str(self.producer.frame())
        # Stop render
        # This method of stopping makes sure that whole producer is rendered and written to disk
        if self.wait_for_producer_end_stop:
            while self.producer.get_speed() > 0:
                time.sleep(0.2)
            while not self.consumer.is_stopped():
                time.sleep(0.2)
        # This method of stopping stops producer
        # and waits for consumer to reach that frame.
        else:
            self.producer.set_speed(0)
            last_frame = self.producer.frame()
            # Make sure consumer renders all frames before exiting
            while self.consumer.position() + 1 < last_frame:
                time.sleep(0.2)
            self.consumer.stop()
        
        # Exit render state
        self.is_rendering = False
        self.ticker.stop_ticker()
        self.producer.set_speed(0)

        # Enter monitor playback state
        self.consumer = self.sdl_consumer
        gtk.gdk.threads_enter()
        self.connect_and_start()
        gtk.gdk.threads_leave()
        self.seek_frame(0)

        gtk.gdk.threads_enter()
        self.render_callbacks.exit_render_gui()
        self.render_callbacks.maybe_open_rendered_file_in_bin()
        gtk.gdk.threads_leave()

    def jack_output_on(self):
        # We're assuming that we are not rendering and consumer is SDL consumer
        self.producer.set_speed(0)
        self.ticker.stop_ticker()

        self.consumer.stop()

        self.create_sdl_consumer()

        self.jack_output_filter = mlt.Filter(self.profile, "jackrack")
        if editorpersistance.prefs.jack_output_type == appconsts.JACK_OUT_AUDIO:
            self.jack_output_filter.set("out_1", "system:playback_1")
            self.jack_output_filter.set("out_2", "system:playback_2")
        self.consumer.attach(self.jack_output_filter)
        self.consumer.set("audio_off", "1")
        self.consumer.set("frequency", str(editorpersistance.prefs.jack_frequency))

        self.consumer.connect(self.producer)
        self.consumer.start()

    def jack_output_off(self):
        # We're assuming that we are not rendering and consumer is SDL consumer
        self.producer.set_speed(0)
        self.ticker.stop_ticker()

        self.consumer.detach(self.jack_output_filter)
        self.consumer.set("audio_off", "0")

        self.consumer.stop()
        self.consumer.start()
        
        self.jack_output_filter = None
        
    def shutdown(self):
        self.ticker.stop_ticker()
        self.producer.set_speed(0)
        self.consumer.stop()

