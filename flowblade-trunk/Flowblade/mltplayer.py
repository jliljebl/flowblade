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

import gtk
import mlt
import os
import time
import threading

import gui
from editorstate import timeline_visible
import render
import respaths
import utils
import updater

TICKER_DELAY = 0.25

class Player(threading.Thread):
    
    def __init__(self, profile):
    
        self.init_for_profile(profile)

        self.ticker = utils.Ticker(self._ticker_event, TICKER_DELAY)

        threading.Thread.__init__(self)
    
    def init_for_profile(self, profile):
        # Get profile and create ticker for playback GUI updates
        self.profile = profile
        
        # Create black clip to display in the beginning 
        black_path = respaths.BLACK_IMAGE_PATH
        self.black_clip = mlt.Producer(self.profile, black_path)
        
        # black_clip is displayed in clip monitor which needs in and out
        self.black_clip.mark_in = -1
        self.black_clip.mark_out = -1
        
        # Trim loop preview
        self.loop_start = -1
        self.loop_end = -1
        self.is_looping = False
        
        # Rendering
        self.is_rendering = False
        self.render_stop_frame = -1
        self.render_start_frame = -1

    def create_sdl_consumer(self):
        """
        Creates consumer with sdl output to a gtk+ widget.
        """
        # Create consumer and set params
        self.consumer = mlt.Consumer(self.profile, "sdl")
        self.consumer.set("real_time", 1)
        self.consumer.set("rescale", "1")

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
        Connects current procer and comsumer and
        """
        self.consumer.purge()
        self.consumer.connect(self.producer)
        self.producer.set_speed(0)
        self.consumer.start()
 
    def run(self):
        """
        Player thread loop. Loop runs until stop requested 
        at project exit (quit or project load).
        """
        self.running = True
        self.name = "mltplayer"
        self.connect_and_start()

        # Block
        while self.running:
            time.sleep(1)

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

    def is_playing(self):
        return (self.producer.get_speed() != 0)

    def _ticker_event(self):
        # If we reach the end of playable/renderable sequence or user has
        # stopped playback/rendering we'll stop ticker and possibly
        # leave render state
        if (self.consumer.is_stopped() 
            or self.producer.get_speed() == 0):
            self.ticker.stop_ticker()
            updater.set_stopped_configuration()
            if self.is_rendering == True:
                self.stop_rendering()
                return

        current_frame = self.producer.frame()
        
        # Stop range rendring. This will not be frame perfect but feature isn't (probably)
        # used with need to get end perfect.
        if self.render_stop_frame != -1:
            if self.is_rendering == True and current_frame >= self.render_stop_frame:
                self.consumer.stop()
                self.stop_rendering()
                updater.set_stopped_configuration()
                return

        # if rendering, set progress bar and exit
        if self.is_rendering:
            if self.render_stop_frame == -1:
                if (self.producer.get_length() - 1) < 1:
                    render_fraction = 1.0
                else:
                    render_fraction = ((float(current_frame)) / 
                                      (float(self.producer.get_length() - 1)))
            else:
                if (self.producer.get_length() - 1) < 1:
                    render_fraction = 1.0
                else:
                    render_fraction = ((float(current_frame - self.render_start_frame)) / 
                      (float(self.render_stop_frame - self.render_start_frame)))
            render.set_render_progress_gui(render_fraction)
            return 

        # If we're out of active range, seek end and and stop play back
        if current_frame >= self.get_active_length():
            self.seek_frame(current_frame)
            return
            
        # If trim looping and past loop end, start from loop start
        if ((not(self.loop_start == -1)) and 
            ((current_frame >= self.loop_end)
            or (current_frame >= self.get_active_length()))):
            self.seek_frame(self.loop_start, False)
            self.producer.set_speed(1)

        updater.update_frame_displayers(current_frame)
        
    def get_active_length(self):
        # Displayed range is different
        # for timeline and clip displays
        if timeline_visible():
            return self.producer.get_length()
        else:
            return gui.pos_bar.producer.get_length()

    def start_rendering(self, render_consumer, start_frame=0, stop_frame=-1):
        self.ticker.stop_ticker()
        self.consumer.stop()
        self.producer.set_speed(0)
        self.producer.seek(start_frame) #self.producer.seek(start_frame)
        self.render_start_frame = start_frame
        self.render_stop_frame = stop_frame
        self.consumer = render_consumer
        self.consumer.connect(self.producer)
        self.producer.set_speed(1)
        self.consumer.start()
        self.is_rendering = True
        render.save_render_start_time()
        self.ticker.start_ticker()

    def stop_rendering(self):
        self.is_rendering = False
        self.ticker.stop_ticker()
        self.consumer = self.sdl_consumer
        self.connect_and_start()
        self.seek_frame(0)
        render.exit_render_gui()
        render.maybe_open_rendered_file_in_bin()

    def shutdown(self):
        self.ticker.stop_ticker()
        self.producer.set_speed(0)
        self.consumer.stop()
        self.running = False

