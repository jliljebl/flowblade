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

import mlt
import os
import threading
import time

import appconsts
import ccrutils
import mltheadlessutils
import mltprofiles
import processutils
import renderconsumer
import toolsencoding

_render_thread = None


# ----------------------------------------------------- module interface with message files
# We are using message files to communicate with application.
def session_render_complete(session_id):
    return ccrutils.session_render_complete(session_id)

def get_session_status(session_id):
    msg = ccrutils.get_session_status_message(session_id)
    if msg == None:
        return None
    fraction, elapsed = msg.split(" ")
    return (fraction, elapsed)
    
def abort_render(session_id):
    ccrutils.abort_render(session_id)

def delete_session_folders(session_id):
     ccrutils.delete_internal_folders(session_id)

# --------------------------------------------------- render thread launch
def main(root_path, session_id, speed, write_file, profile_desc, encoding_option_index, 
         quality_option_index, source_path, render_full_range, start_frame, end_frame):
        
    mltheadlessutils.mlt_env_init(root_path, session_id)

    global _render_thread
    _render_thread = MotionClipHeadlessRunnerThread(speed, write_file, profile_desc, encoding_option_index,
                                                    quality_option_index, source_path, render_full_range,
                                                    start_frame, end_frame)
    _render_thread.start()

       

class MotionClipHeadlessRunnerThread(threading.Thread):

    def __init__(self, speed, write_file, profile_desc, encoding_option_index,
                 quality_option_index, source_path, render_full_range,
                 start_frame, end_frame):
        threading.Thread.__init__(self)

        self.speed = speed
        self.write_file = write_file
        self.profile_desc = profile_desc
        self.encoding_option_index = int(encoding_option_index)
        self.quality_option_index = int(quality_option_index)
        self.source_path = source_path
        self.render_full_range = bool(render_full_range)
        self.start_frame = int(start_frame)
        self.end_frame = int(end_frame)

        self.abort = False

    def run(self):
        self.start_time = time.monotonic()

        profile = mltprofiles.get_profile(self.profile_desc) 
        motion_producer = mlt.Producer(profile, None, str("timewarp:" + str(self.speed) + ":" + str(self.source_path)))

        # Create tractor and track to get right length
        tractor = mlt.Tractor()
        multitrack = tractor.multitrack()
        track0 = mlt.Playlist()
        multitrack.connect(track0, 0)
        track0.insert(motion_producer, 0, 0, motion_producer.get_length() - 1)

        consumer = renderconsumer.get_render_consumer_for_encoding_and_quality(self.write_file, profile, self.encoding_option_index, self.quality_option_index)
        
        # start and end frames, renderer stop behaviour
        start_frame = self.start_frame 
        end_frame = self.end_frame
        wait_for_producer_stop = True
        if self.render_full_range == False:
            wait_for_producer_stop = False # consumer wont stop automatically and needs to stopped explicitly

        # Launch render
        self.render_player = renderconsumer.FileRenderPlayer(self.write_file, tractor, consumer, start_frame, end_frame)
        self.render_player.wait_for_producer_end_stop = False
        self.render_player.start()

        while self.render_player.stopped == False:
            
            self.check_abort_requested()
            
            if self.abort == True:
                self.render_player.shutdown()
                return
            
            fraction = self.render_player.get_render_fraction()
            self.render_update(fraction)

            time.sleep(0.3)

        # Write out completed flag file.
        ccrutils.write_completed_message()

    def check_abort_requested(self):
        self.abort = ccrutils.abort_requested()

    def render_update(self, fraction):
        elapsed = time.monotonic() - self.start_time
        msg = str(fraction) + " " + str(elapsed)
        ccrutils.write_status_message(msg)



