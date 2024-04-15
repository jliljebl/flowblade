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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

try:
    import mlt7 as mlt
except:
    import mlt
import threading
import time

import ccrutils
import mltheadlessutils
import mltprofiles
import renderconsumer

_render_thread = None


# ----------------------------------------------------- module interface with message files
# We are using message files to communicate with application.
def session_render_complete(parent_folder, session_id):
    return ccrutils.session_render_complete(parent_folder, session_id)

def get_session_status(parent_folder, session_id):
    msg = ccrutils.get_session_status_message(parent_folder, session_id)
    if msg == None:
        return None
    fraction, elapsed = msg.split(" ")
    return (fraction, elapsed)
    
def abort_render(parent_folder, session_id):
    ccrutils.abort_render(parent_folder, session_id)

def delete_session_folders(parent_folder, session_id):
     ccrutils.delete_internal_folders(parent_folder, session_id)

# --------------------------------------------------- render thread launch
def main(root_path, session_id, parent_folder, profile_desc, write_file, clip_path, accuracy, shakiness):
    
    mltheadlessutils.mlt_env_init(root_path, parent_folder, session_id)

    global _render_thread
    _render_thread = StabilizeHeadlessRunnerThread(profile_desc, write_file, clip_path, accuracy, shakiness)
    _render_thread.start()

       

class StabilizeHeadlessRunnerThread(threading.Thread):

    def __init__(self, profile_desc, write_file, clip_path, accuracy, shakiness):
        threading.Thread.__init__(self)

        self.write_file = write_file
        self.clip_path = clip_path
        self.shakiness = shakiness
        self.accuracy = accuracy
        self.profile_desc = profile_desc
        self.abort = False

    def run(self):
        self.start_time = time.monotonic()

        profile = mltprofiles.get_profile(self.profile_desc) 
        producer = mlt.Producer(profile, str(self.clip_path)) # this runs 0.5s+ on some clips
        
        stabilize_filter = mlt.Filter(profile, "vidstab")
        # Init values, these may actually be defaults and not needed.
        stabilize_filter.set("stepsize", "6")
        stabilize_filter.set("algo", "1")
        stabilize_filter.set("mincontrast", 0.3)
        stabilize_filter.set("show", "0")
        stabilize_filter.set("tripod", "0")
        stabilize_filter.set("smoothing", "15")
        stabilize_filter.set("maxshift", "1")
        stabilize_filter.set("maxangle", "-1")
        stabilize_filter.set("crop", "0")
        stabilize_filter.set("invert", "0")
        stabilize_filter.set("relative", "1")
        stabilize_filter.set("zoom", "0")
        stabilize_filter.set("optzoom", "1")
        stabilize_filter.set("zoomspeed", "0.25")
        stabilize_filter.set("reload", "0")
        stabilize_filter.set("analyze", "0")
        #stabilize_filter.set("results", "")

        # Apply user set analyze parameters
        stabilize_filter.set("filename", str(self.write_file))
        stabilize_filter.set("shakiness", str(self.shakiness))
        stabilize_filter.set("accuracy", str(self.accuracy))

        # Add filter to producer.
        producer.attach(stabilize_filter)

        # Create tractor and track to get right length
        tractor = renderconsumer.get_producer_as_tractor(producer, producer.get_length() - 1)

        # Get render consumer
        print(self.write_file,"self.write_file")
        xml_consumer = mlt.Consumer(profile, "xml", str(self.write_file) + ".xml")
        xml_consumer.set("all", "1")
        xml_consumer.set("real_time", "-1")

        tractor.set_speed(0)
        tractor.seek(0)
        
        stabilize_filter.set("analyze", 1)
        
        # Wait until producer is at start
        while tractor.frame() != 0:
            time.sleep(0.1)

        # Connect and start rendering
        xml_consumer.connect(tractor)
        xml_consumer.start()
        tractor.set_speed(1)

        # Wait until done
        while xml_consumer.is_stopped() == False:
            render_fraction = float(producer.frame()) / float(producer.get_length())
            self.render_update(render_fraction)
            time.sleep(0.3)
        
        # Write out completed flag file.
        ccrutils.write_completed_message()

    def check_abort_requested(self):
        self.abort = ccrutils.abort_requested()

    def render_update(self, fraction):
        elapsed = time.monotonic() - self.start_time
        msg = str(fraction) + " " + str(elapsed)
        ccrutils.write_status_message(msg)



