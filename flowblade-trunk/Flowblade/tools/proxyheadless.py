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

import glob
import mlt
import os
from PIL import Image
import threading
import time

import appconsts
import ccrutils
import mltheadlessutils
import mltprofiles
import processutils
import renderconsumer
import toolsencoding
import userfolders

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
def main(root_path, session_id, media_file_id, proxy_w, proxy_h, enc_index, \
            proxy_file_path, proxy_rate, media_file_path, profile_desc, lookup_path):
    
    mltheadlessutils.mlt_env_init(root_path, session_id)

    global _render_thread
    _render_thread = ProxyClipRenderThread(media_file_id, proxy_w, proxy_h, enc_index, 
            proxy_file_path, proxy_rate, media_file_path, profile_desc, lookup_path)
    _render_thread.start()

       

class ProxyClipRenderThread(threading.Thread):

    def __init__(self, media_file_id, proxy_w, proxy_h, enc_index, 
                    proxy_file_path, proxy_rate, media_file_path, proxy_profile_desc, lookup_path):

        threading.Thread.__init__(self)

        self.media_file_id = int(media_file_id)
        self.proxy_w = int(proxy_w)
        self.proxy_h = int(proxy_h)
        self.enc_index = int(enc_index)
        self.proxy_file_path = proxy_file_path
        self.proxy_rate = int(proxy_rate)
        self.media_file_path = media_file_path
        self.proxy_profile_desc = proxy_profile_desc
        self.lookup_path = lookup_path # For img seqs only
        
        self.abort = False

    def run(self):
        self.start_time = time.monotonic()
        
        if self.lookup_path == "None":
            # Video clips
            
            proxy_profile = mltprofiles.get_profile(self.proxy_profile_desc)
            
            # App wrote the temp profile when launching proxy render.
            # NOTE: this needs to be created here for future
            proxy_profile_path = userfolders.get_cache_dir() + "temp_proxy_profile"
            proxy_profile = mlt.Profile(proxy_profile_path)
        
            renderconsumer.performance_settings_enabled = False # uuh...we're obivously disabling something momentarily.
            consumer = renderconsumer.get_render_consumer_for_encoding(
                                                        self.proxy_file_path,
                                                        proxy_profile, 
                                                        renderconsumer.proxy_encodings[self.enc_index])
            renderconsumer.performance_settings_enabled = True
            
            consumer.set("vb", str(int(self.proxy_rate)) + "k")
            consumer.set("rescale", "nearest")
            
            file_producer = mlt.Producer(proxy_profile, str(self.media_file_path))

            start_frame = 0
            end_frame = file_producer.get_length() - 1
            
            self.render_player = renderconsumer.FileRenderPlayer(None, file_producer, consumer, 0, end_frame)
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
                
        else:
            # Image Sequences

            copyfolder, copyfilename = os.path.split(self.proxy_file_path)
            if not os.path.isdir(copyfolder):
                os.makedirs(copyfolder)
            
            listing = glob.glob(self.lookup_path)
            size = self.proxy_w, self.proxy_h
            done = 0
            for orig_path in listing:
                orig_folder, orig_file_name = os.path.split(orig_path)

                try:
                    im = Image.open(orig_path)
                    im.thumbnail(size, Image.ANTIALIAS)
                    im.save(copyfolder + "/" + orig_file_name, "PNG")
                except IOError:
                    print("proxy img seq frame failed for '%s'" % orig_path)

                done = done + 1
            
                if done % 5 == 0:
                    fraction = float(done) / float(len(listing))
                    self.render_update(fraction)

        # Write out completed flag file.
        ccrutils.write_completed_message()

    def check_abort_requested(self):
        self.abort = ccrutils.abort_requested()

    def render_update(self, fraction):
        elapsed = time.monotonic() - self.start_time
        msg = str(fraction) + " " + str(elapsed)
        ccrutils.write_status_message(msg)



