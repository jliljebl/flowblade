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
Clip player used to select frames for preview and range selection.
"""

from gi.repository import Gdk

import mlt
import os

import mltprofiles

TICKER_DELAY = 0.25
RENDER_TICKER_DELAY = 0.05

class GmicPlayer:
    
    def __init__(self, clip_path):
        self.profile = mltprofiles.get_default_profile()
        self.producer = mlt.Producer(self.profile, str(clip_path))
        self.producer.mark_in = -1
        self.producer.mark_out = -1
        
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

    def refresh(self): # Window events need this to get picture back
        self.consumer.stop()
        self.consumer.start()

    def connect_and_start(self):
        """
        Connects current procer and consumer and
        """
        self.consumer.purge()
        self.producer.set_speed(0)
        self.consumer.connect(self.producer)
        self.consumer.start()

    def current_frame(self):
        return self.producer.frame()
    
    def seek_position_normalized(self, pos, length):
        frame_number = pos * length
        self.seek_frame(int(frame_number)) 
    
    def seek_frame(self, frame):
        # Force range
        length = self.get_active_length()
        if frame < 0:
            frame = 0
        elif frame >= length:
            frame = length - 1

        self.producer.set_speed(0)
        self.producer.seek(frame) 

    def seek_and_get_rgb_frame(self, frame, update_gui=True):
        # Force range
        length = self.get_active_length()
        if frame < 0:
            frame = 0
        elif frame >= length:
            frame = length - 1

        self.producer.set_speed(0)
        self.producer.seek(frame) 

        frame = self.producer.get_frame()
        # And make sure we deinterlace if input is interlaced
        frame.set("consumer_deinterlace", 1)

        # Now we are ready to get the image and save it.
        size = (self.profile.width(), self.profile.height())
        rgb = frame.get_image(mlt.mlt_image_rgb24a, *size) 
        return rgb

    def shutdown(self):
        self.producer.set_speed(0)
        self.consumer.stop()
