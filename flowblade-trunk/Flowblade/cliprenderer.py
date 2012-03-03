"""
THIS IS NOT USED CURRENTLY.


Module runs process to render clips for timeline.

Main application process and process running in this module 
communicate using pipe messages.
 
After clips are rendered process returns a file path to new clip and
waits command to render next clip.

During rendering it send progress updates.

We're using some of same modules as main process but since 
this is different process, no state is shared. We also have to initialize
mocules here since we have different state.
"""

import mlt
import gnomevfs
import os
import time

#import render
import respaths
#import test

QUIT = "quit"
#action_object members:transition_data, mlt_service, positioning, lenght
#
# transition_data:"track","from_clip", "to_clip","from_handle","to_handle","max_length"
def render_transition(current_sequence, action, complete_callback):
    t_data = action.transition_data

    # Create clones of clips
    orig_from = t_data["from_clip"]
    orig_to = t_data["to_clip"]
    from_clip = current_sequence.create_file_producer_clip(orig_from.path)
    to_clip = current_sequence.create_file_producer_clip(orig_to.path)
    current_sequence.clone_clip_range_and_filters(orig_from, from_clip)
    current_sequence.clone_clip_range_and_filters(orig_to, to_clip)
    
    complete_callback()



"""
def main(conn,
         profile_file_path,
         root_path):
    print profile_file_path
    print root_path
    running = True
    while(running):
        msg = conn.recv()
        print msg[0]
        time.sleep(1)
        print "new round"
        if msg[0] == QUIT:
            running = False

    print "child renderer out"
"""
"""
class RenderSequence:

    Multitrack MLT object

    def __init__(self, profile):
        # Data members
        self.profile = profile
        self.tracks = []
        self.length = 100

        # MLT objects for a multitrack sequence
        self.init_mlt_objects()

    def create_tracks(self):

        This is donw when sequnece first created, but when sequence loaded
        tracks are added using add_track(...)

        # Default tracks
        self.add_track(VIDEO) # black bg
        self.add_track(VIDEO) # hidden video track for clip ang trim display

    def init_mlt_objects(self):
        # MLT objects for multitrack sequence
        self.tractor = mlt.Tractor()

        # Dummy values for great convenience (Monitor clip display looks for these
        # 
        self.tractor.mark_in = -1
        self.tractor.mark_out = -1
        
        self.field = self.tractor.field()
        self.multitrack = self.tractor.multitrack()

    def add_track(self, type, is_hidden=False):

        Creates a MLT playlist object, adds project
        data and adds to tracks list.

        new_track = mlt.Playlist()
        self._add_track_attributes(new_track, type)
        
        # Connect to MLT multitrack
        self.multitrack.connect(new_track, len(self.tracks))
        
        # Add to tracklist and set id to list index
        new_track.id = len(self.tracks)
        self.tracks.append(new_track)
        
        # Mix all audio to track 1 by combining them one after another 
        # using an always active field transition.
        transition = mlt.Transition(self.profile, "mix")
        transition.set("in", 0)
        transition.set("out", 0)
        transition.set("a_track", 1)
        transition.set("b_track", new_track.id)
        transition.set("always_active", 1)
        transition.set("combine", 1)
        self.field.plant_transition(transition, 1, new_track.id)

        return new_track

    def _add_track_attributes(self, track, type):                
        # Set MLT attributs
        track.set( "in", 0 );
        track.set( "out", DEFAULT_LENGTH - 1 );
        track.set( "length", DEFAULT_LENGTH);
        
        # Add data attr
        track.type = type

        # Set video and audio playback values
        if type == VIDEO:
            track.mute_state = 0 # video on, audio on as mlt "hide" value
        else:
            track.mute_state = 1 # video off, audio on as mlt "hide" value
        track.set("hide", track.mute_state)

        # 
        track.clips = [] 


    def create_file_producer_clip(self, path):

        Creates MLT Producer and adds attributes to it, but does 
        not add it to track/playlist object.

        producer = mlt.Producer(self.profile, path)
        producer.path = path
        producer.filters = []
        
        (dir, file_name) = os.path.split(path)
        (name, ext) = os.path.splitext(file_name)
        producer.name = name
        producer.media_type = get_media_type(path)
        
        self.add_clip_attr(producer)
        return producer

    def create_filter(self, filter_name):

        Creates MLT Filter object.

        filter = mlt.Filter(self.profile, filter_name)
        filter.filter_name = filter_name
        return filter

    def create_transition(self, transition_name, value):

        Creates MLT Transition object.
        Transition is a considered clip.

        transition = mlt.Transition(self.profile, transition_name, value)
        transition.name = transition_name
        transition.value = value 
        self.add_clip_attr(transition)
        return transition


 
    def get_length(self):
        return self.length

    def add_clip_attr(self, clip):

        File producers, transitions and black clips have same
        clip attributes.

        clip.id = self.get_next_id()
        # example: in 10, out 10 == 1 frame long clip
        clip.clip_in = -1 # inclusive. -1 == not set
        clip.clip_out = -1 # inclusive, -1 == not set 
        clip.is_blanck_clip = False
        clip.selected = False
        clip.master_clip_id = -1
        clip.master_track_id = -1
        clip.sync_data = None
"""


        



    













