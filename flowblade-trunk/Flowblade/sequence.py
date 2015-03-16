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
Module contains class Sequence that is the multitrack media object being edited
by the application. A project has 1-n of these.
"""

import mlt
import os

import appconsts
import edit
import editorstate
import mltfilters
import mlttransitions
import mltrefhold
import patternproducer
import utils

# Media types for tracks or clips
UNKNOWN = appconsts.UNKNOWN
VIDEO = appconsts.VIDEO
AUDIO = appconsts.AUDIO
IMAGE = appconsts.IMAGE
IMAGE_SEQUENCE = appconsts.IMAGE_SEQUENCE
RENDERED_VIDEO = appconsts.RENDERED_VIDEO
PATTERN_PRODUCER = appconsts.PATTERN_PRODUCER
FILE_DOES_NOT_EXIST = appconsts.FILE_DOES_NOT_EXIST

# Allowed editing operations on a track
FREE = appconsts.FREE # all edits allowed
SYNC_LOCKED = appconsts.SYNC_LOCKED # FEATURE NOT AVAILABLE TO USER CURRENTLY!
                # no insert, splice out or one roll trim. 
                # Allowed edits do not change positions of later clips 
LOCKED = appconsts.LOCKED # no edits allowed

# Display heights
TRACK_HEIGHT_NORMAL = appconsts.TRACK_HEIGHT_NORMAL # track height in canvas and column
TRACK_HEIGHT_SMALL = appconsts.TRACK_HEIGHT_SMALL # track height in canvas and column

# pan magic value indicating that no pan is applied
NO_PAN = appconsts.NO_PAN #-99

# MLT types
MLT_PLAYLIST = 0
MLT_PRODUCER = 1
MLT_FILTER = 2

# Number of tracks available
# NOTE: These are set from other modules (and this one when cloning) when creating or loading projects
# and used in Sequence.__init__(...) when creating sequences.
# Weak design, tracks count should be provided via constructor at creation time.
AUDIO_TRACKS_COUNT = 4
VIDEO_TRACKS_COUNT = 5

def set_track_counts(project):
    global AUDIO_TRACKS_COUNT, VIDEO_TRACKS_COUNT
    AUDIO_TRACKS_COUNT = project.sequences[0].first_video_index - 1
    VIDEO_TRACKS_COUNT = AUDIO_TRACKS_COUNT + 1

# Output modes. These correspond to option indexes in guicomponents.get_monitor_view_select_combo()
PROGRAM_OUT_MODE = 0
VECTORSCOPE_MODE = 1
RGB_PARADE_MODE = 2

# black clip
black_track_clip = None

# DEAD CODE !??!
# Mute states as (video_on, audio_on) tuples
# Indexes correspond to "hide" property values 0 - 3
# for playlists in MLT
# USED FOR TRACKS, NOT CLIPS. Clips handled using values in appconsts.py
#MUTE_STATES = [(True, True), (False, True), (True, False), (False, False)]

# Track that all audio is mixed down to combine for output.
AUDIO_MIX_DOWN_TRACK = 0


class Sequence:
    """
    Multitrack MLT object
    """
    def __init__(self, profile, name="sequence"):

        # Data members
        self.name = name # name of sequence
        self.next_id = 0 # id for next created clip
        self.profile = profile
        self.master_audio_gain = 1.0
        self.master_audio_pan = NO_PAN
        self.tracks = []
        self.compositors = []
        self.markers = [] # markers are tuples (name_str, frame_int)
        self.proxyclips = {}
        self.rendered_versions = {} 
        self.watermark_filter = None
        self.watermark_file_path = None
        self.seq_len = 0 # used in trim crash hack, remove when fixed

        # MLT objects for a multitrack sequence
        self.init_mlt_objects()

    # ----------------------------------- mlt init
    def init_mlt_objects(self):
        # MLT objects for multitrack sequence
        self.tractor = mlt.Tractor()

        self.tractor.mark_in = -1
        self.tractor.mark_out = -1

        # Only create and add pan filter if actual pan is applied
        # This method gets called on load and we only want to add a filter then if pan is applied,
        # and not on initial creation.
        # audiomonitoring.py calls add_track_pan_filter() when pan turned on for initial creation
        if self.master_audio_pan != NO_PAN:
            self.add_track_pan_filter(self.tractor, self.master_audio_pan)

        # Create and ad gain filter
        gain_filter = mlt.Filter(self.profile, "volume")
        mltrefhold.hold_ref(gain_filter)
        gain_filter.set("gain", str(self.master_audio_gain))
        self.tractor.attach(gain_filter)
        self.tractor.gain_filter = gain_filter
        
        self.field = self.tractor.field()
        self.multitrack = self.tractor.multitrack()
        
        self.vectorscope = mlt.Filter(self.profile, "frei0r.vectorscope")
        mltrefhold.hold_ref(self.vectorscope) # ?? is this just some anti-crash hack attempt that was not removed
        self.vectorscope.set("mix", "0.5")
        self.vectorscope.set("overlay sides", "0.0") 
        self.rgbparade =  mlt.Filter(self.profile, "frei0r.rgbparade")
        mltrefhold.hold_ref(self.rgbparade) # ?? is this just some anti-crash hack attempt that was not removed
        self.rgbparade.set("mix", "0.4")
        self.rgbparade.set("overlay sides", "0.0")
        self.outputfilter = None

    # ---------------------------------------- tracks
    def create_default_tracks(self):
        """
        This is done when sequence first created, but when sequence is loaded
        tracks are added using add_track(...)
        
        TRACKS LAYOUT:
        index                                           track type
        -----                                           ----------
        0                                               black bg track
        1 - (self.first_video_index - 1)                audio tracks    
        self.first_video_index - (len(self.tracks) - 2) video tracks
        (len(self.tracks) - 1)                          hidden track
        
        Tracks are never changed after creation, changing tracks count feature is
        achieved by creating a new sequence.
        """
        # Default tracks
        # black bg track
        self.add_track(VIDEO)
        
        # Audio tracks
        for i in range(0, AUDIO_TRACKS_COUNT):
            track = self.add_track(AUDIO)
            track.height = TRACK_HEIGHT_SMALL
        
        # Video tracks
        self.first_video_index = AUDIO_TRACKS_COUNT + 1 # index of first editable video track

        for i in range(0, VIDEO_TRACKS_COUNT):
            self.add_track(VIDEO) # editable
            if i > 0:
                track_index = i + self.first_video_index
                self.tracks[track_index].height = TRACK_HEIGHT_SMALL # only V1 is normal size after creation
                self.tracks[track_index].active = False # only V1 is active after creation

        # ---Hidden track--- #
        # Hidden video track for clip and trimming display.
        # Hidden track is a video track that is always the topmost track.
        # It is used when displaying monitor clip and
        # displaying the clip that is being trim edited. When trim is loop previewed
        # the hidden track is cleared so that the edit that is on the tracks
        # below can be viewed.
        self.add_track(VIDEO, True) 

        self._create_black_track_clip()
        
        # Add black clip to black bg track
        self.tracks[0].clips.append(black_track_clip) # py
        self.tracks[0].append(black_track_clip, 0, 0) # mlt

    def _create_black_track_clip(self):
        # Create 1 fr long black bg clip and set in and out
        global black_track_clip # btw, why global?
        
        # This is not an actual bin clip so id can be -1, it is just used to create the producer
        pattern_producer_data = patternproducer.BinColorClip(-1, "black_bg", "#000000000000")
            
        black_track_clip = self.create_pattern_producer(pattern_producer_data)
        black_track_clip.clip_in = 0
        black_track_clip.clip_out = 0

    def add_track(self, track_type, is_hidden=False):
        """ 
        Creates a MLT playlist object, adds project
        data and adds to tracks list.
        """
        new_track = mlt.Playlist()

        self._add_track_attributes(new_track, track_type)
        new_track.is_sync_track = False

        # Connect to MLT multitrack
        self.multitrack.connect(new_track, len(self.tracks))
        
        # Add to tracklist and set id to list index
        new_track.id = len(self.tracks)
        self.tracks.append(new_track)
        
        # Mix all audio to track 1 by combining them one after another 
        # using an always active field transition.
        if ((new_track.id > AUDIO_MIX_DOWN_TRACK) # black bg or track1 it's self does not need to be mixed
            and (is_hidden == False)): # We actually do want hidden track to cover all audio below, which happens if it is not mixed.
            self._mix_audio_for_track(new_track)
        
        # Add method that returns track name
        new_track.get_name = lambda : utils.get_track_name(new_track, self) 
        
        return new_track

    def _add_track_attributes(self, track, type):                
        # Add data attr
        track.type = type
        track.sequence = self
        
        # Add state attr
        track.active = True

        # Set initial video and audio playback values
        if type == VIDEO:
            track.mute_state = 0 # video on, audio on as mlt "hide" value
        else:
            track.mute_state = 1 # video off, audio on as mlt "hide" value
        track.set("hide", track.mute_state)

        # This is kept in sync with mlt.Playlist inner data
        track.clips = []
        
        # Display height
        track.height = TRACK_HEIGHT_NORMAL
        if editorstate.SCREEN_HEIGHT < 863:# Fix for 786 screens
            track.height = TRACK_HEIGHT_SMALL
        
        # Audio gain and pan values, these are overwritten later with saved values when loading 
        track.audio_gain = 1.0 # active range 0 - 1
        track.audio_pan = NO_PAN # active range 0-1, 0.5 is middle
        
        # Tracks may be FREE or LOCKED
        track.edit_freedom = FREE

    def _mix_audio_for_track(self, track):
        # Create and add transition to combine track audios
        transition = mlt.Transition(self.profile, "mix")
        mltrefhold.hold_ref(transition)
        transition.set("a_track", int(AUDIO_MIX_DOWN_TRACK))
        transition.set("b_track", track.id)
        transition.set("always_active", 1)
        transition.set("combine", 1)
        self.field.plant_transition(transition, int(AUDIO_MIX_DOWN_TRACK), track.id)

        # Create and ad gain filter
        gain_filter = mlt.Filter(self.profile, "volume")
        mltrefhold.hold_ref(gain_filter)
        gain_filter.set("gain", str(track.audio_gain))
        track.attach(gain_filter)
        track.gain_filter = gain_filter

        # Add pan filter if this track is panorated
        if track.audio_pan != NO_PAN:
            self.add_track_pan_filter(track, 0.5) 
            track.audio_pan = 0.5

    def minimize_tracks_height(self):
        for i in range (1, len(self.tracks) - 1):# visible tracks
            track = self.tracks[i]
            track.height = TRACK_HEIGHT_SMALL

    def maximize_tracks_height(self, allocation):
        for i in range (1, len(self.tracks) - 1):# visible tracks
            track = self.tracks[i]
            track.height = TRACK_HEIGHT_NORMAL
    
        self.resize_tracks_to_fit(allocation)

    def maximize_video_tracks_height(self, allocation):
        self.minimize_tracks_height()
        for i in range (self.first_video_index, len(self.tracks) - 1):# visible tracks
            track = self.tracks[i]
            track.height = TRACK_HEIGHT_NORMAL
    
        self.resize_tracks_to_fit(allocation)

    def maximize_audio_tracks_height(self, allocation):
        self.minimize_tracks_height()
        for i in range (1, self.first_video_index):
            track = self.tracks[i]
            track.height = TRACK_HEIGHT_NORMAL
    
        self.resize_tracks_to_fit(allocation)

    def get_tracks_height(self):
        h = 0
        for i in range (1, len(self.tracks) - 1):# visible tracks
            track = self.tracks[i]
            h += track.height
        return  h

    def set_track_gain(self, track, gain):
        track.gain_filter.set("gain", str(gain))
        track.audio_gain = gain

    def set_master_gain(self, gain):
        self.tractor.gain_filter.set("gain", str(gain))
        self.master_audio_gain = gain

    def add_track_pan_filter(self, track, value):
        # This method is used for master too, and called with tractor then
        pan_filter = mlt.Filter(self.profile, "panner")
        mltrefhold.hold_ref(pan_filter)
        pan_filter.set("start", value)
        track.attach(pan_filter)
        track.pan_filter = pan_filter 

    def set_track_pan_value(self, track, value):
        track.pan_filter.set("start", str(value))
        track.audio_pan = value
    
    def remove_track_pan_filter(self, track):
        # This method is used for master too, and called with tractor then
        track.detach(track.pan_filter)
        track.pan_filter = None
        track.audio_pan = NO_PAN

    def set_master_pan_value(self, value):
        self.tractor.pan_filter.set("start", str(value))
        self.master_audio_pan = value

    def first_video_track(self):
        return self.tracks[self.first_video_index]

    def all_tracks_off(self):
        for i in range (1, len(self.tracks) - 1):
            track = self.tracks[i]
            if track.active == True:
                return False
        return True

    # -------------------------------------------------- clips
    def create_file_producer_clip(self, path, new_clip_name=None):
        """
        Creates MLT Producer and adds attributes to it, but does 
        not add it to track/playlist object.
        """
        producer = mlt.Producer(self.profile, str(path)) # this runs 0.5s+ on some clips
        mltrefhold.hold_ref(producer)
        producer.path = path
        producer.filters = []
        
        (dir, file_name) = os.path.split(path)
        (name, ext) = os.path.splitext(file_name)
        producer.name = name
        if new_clip_name != None:
            producer.name = new_clip_name
        producer.media_type = get_media_type(path)
        if producer.media_type == FILE_DOES_NOT_EXIST:
            print "file does not exist"
            return None

        self.add_clip_attr(producer)
        
        return producer

    def create_slowmotion_producer(self, path, speed):
        """
        Creates MLT Producer and adds attributes to it, but does 
        not add it to track/playlist object.
        """
        fr_path = "framebuffer:" + path + "?" + str(speed)
        producer = mlt.Producer(self.profile, None, str(fr_path)) # this runs 0.5s+ on some clips
        mltrefhold.hold_ref(producer)

        (folder, file_name) = os.path.split(path)
        (name, ext) = os.path.splitext(file_name)
        producer.name = name
        producer.path = path
        producer.speed = speed
        producer.media_type = get_media_type(path)
        if producer.media_type == FILE_DOES_NOT_EXIST:
            return None

        self.add_clip_attr(producer)
        
        return producer

    def create_pattern_producer(self, pattern_producer_data):
        """
        pattern_producer_data is instance of patternproducer.AbstractBinClip
        """
        clip = patternproducer.create_pattern_producer(self.profile, pattern_producer_data)
        self.add_clip_attr(clip)
        return clip

    def create_rendered_transition_clip(self, path, rendered_type):
        clip = self.create_file_producer_clip(path)
        clip.rendered_type = rendered_type
        return clip
    
    def add_clip_attr(self, clip):
        """
        File producers, transitions and black clips have same
        clip attributes.
        """
        clip.id = self.get_next_id()
        # example: in 10, out 10 == 1 frame long clip
        clip.clip_in = -1 # inclusive. -1 == not set
        clip.clip_out = -1 # inclusive, -1 == not set 
        clip.is_blanck_clip = False
        clip.selected = False
        clip.sync_data = None 
        clip.mute_filter = None #
        clip.stream_indexes = None # a, v stream indexes when not muted
        clip.clip_length = lambda: _clip_length(clip) # MLT get_length gives wrong values for blanks
        clip.waveform_data = None
        clip.color = None # None means that clip type default color is displayed

    def clone_track_clip(self, track, index):
        orig_clip = track.clips[index]
        return self.create_clone_clip(orig_clip)

    def create_clone_clip(self, clip):
        if clip.media_type != appconsts.PATTERN_PRODUCER:
            clone_clip = self.create_file_producer_clip(clip.path) # file producer
        else:
            clone_clip = self.create_pattern_producer(clip.create_data) # pattern producer
        self.clone_clip_and_filters(clip, clone_clip)
        return clone_clip
        
    def clone_clip_and_filters(self, clip, clone_clip):
        """
        Clones clip range properties and filters that are needed for clip to be
        used in another clip's place, but not id, master_clip and selection
        properties that are part of original clips state in sequence.
        """
        clone_clip.clip_in = clip.clip_in
        clone_clip.clip_out = clip.clip_out
        clone_clip.filters = []
        
        for f in clip.filters:
            clone_filter = mltfilters.clone_filter_object(f, self.profile)
            clone_clip.attach(clone_filter.mlt_filter)
            clone_clip.filters.append(clone_filter)

    def clone_filters(self, clip):
        clone_filters = []
        for f in clip.filters:
            clone_filter = mltfilters.clone_filter_object(f, self.profile)
            clone_filters.append(clone_filter)
        return clone_filters

    def get_next_id(self):
        """
        Growing id for newly created clip or transition. 
        """
        self.next_id += 1
        return self.next_id - 1

    # ------------------------------------------ blanks
    def create_and_insert_blank(self, track, index, length):
        """
        Used for persistance.
        """
        edit._insert_blank(track, index, length)
        return track.clips[index]
    
    def append_blank(self, blank_length, track):
        """
        Used in hack for trim editing last clip of a track.
        """
        index = len(track.clips)
        edit._insert_blank(track, index, blank_length)
        
    def remove_last_clip(self, track):
        """
        Used in hack for trim editing last clip of a track.
        """
        edit._remove_clip(track, len(track.clips) - 1)

    # ------------------------------------------ filters
    def create_filter(self, filter_info):
        filter_object = mltfilters.FilterObject(filter_info)
        filter_object.create_mlt_filter(self.profile)
        return filter_object

    def create_multipart_filter(self, filter_info, clip):
        filter_object = mltfilters.MultipartFilterObject(filter_info)
        filter_object.create_mlt_filters(self.profile, clip)
        return filter_object

    # ------------------------------------------------------ compositors
    def create_compositor(self, compositor_type):
        compositor = mlttransitions.create_compositor(compositor_type)
        compositor.create_mlt_objects(self.profile)
        return compositor

    def restack_compositors(self):
        self.sort_compositors()

        new_compositors = []
        for compositor in self.compositors:
            if compositor.planted == False:
                self._plant_compositor(compositor)
                new_compositors.append(compositor)
            else:
                clone_compositor = self._create_and_plant_clone_compositor(compositor)
                new_compositors.append(clone_compositor)
        self.compositors = new_compositors

    def _plant_compositor(self, compositor):
        self.field.plant_transition(compositor.transition.mlt_transition, 
                                    int(compositor.transition.a_track), 
                                    int(compositor.transition.b_track))
        compositor.planted = True

    def _create_and_plant_clone_compositor(self, old_compositor):
        # Remove old compositor
        #edit.old_compositors.append(old_compositor) # HACK. Garbage collecting compositors causes crashes.
        self.field.disconnect_service(old_compositor.transition.mlt_transition)
        
        # Create and plant new compositor
        compositor = self.create_compositor(old_compositor.type_id)
        compositor.clone_properties(old_compositor)
        compositor.set_in_and_out(old_compositor.clip_in, old_compositor.clip_out)
        compositor.transition.set_tracks(old_compositor.transition.a_track, old_compositor.transition.b_track)
        self._plant_compositor(compositor)
        return compositor
    
    def clone_compositors_from_sequence(self, from_sequence, track_delta):
        # Used when cloning compositors to change track count by cloning sequence
        new_compositors = []
        video_diff = self.first_video_index - from_sequence.first_video_index
        for old_compositor in from_sequence.compositors:
            if old_compositor.transition.b_track + video_diff < len(self.tracks) - 1:
                clone_compositor = self._create_and_plant_clone_compositor_for_sequnce_clone(old_compositor, track_delta)
                new_compositors.append(clone_compositor)
        self.compositors = new_compositors

    def _create_and_plant_clone_compositor_for_sequnce_clone(self, old_compositor, track_delta):      
        # Create and plant new compositor
        compositor = self.create_compositor(old_compositor.type_id)
        compositor.clone_properties(old_compositor)
        compositor.set_in_and_out(old_compositor.clip_in, old_compositor.clip_out)
        compositor.transition.set_tracks(old_compositor.transition.a_track + track_delta, old_compositor.transition.b_track + track_delta)
        self._plant_compositor(compositor)
        return compositor
        
    def get_compositors(self):
        return self.compositors

    def add_compositor(self, compositor):
        self.compositors.append(compositor)

    def remove_compositor(self, old_compositor):
        #edit.old_compositors.append(old_compositor)# HACK. Garbage collecting compositors causes crashes.
        try:
            self.compositors.remove(old_compositor)
        except ValueError: # has been restacked since creation, needs to looked up using destroy_id
            found = False
            for comp in self.compositors:
                if comp.destroy_id == old_compositor.destroy_id:
                    found = True
                    self.compositors.remove(comp)
                    #edit.old_compositors.append(comp)
                    old_compositor = comp
            if found == False:
                raise ValueError('compositor not found using destroy_id')
            
        self.field.disconnect_service(old_compositor.transition.mlt_transition)

    def get_compositor_for_destroy_id(self, destroy_id):
        for comp in self.compositors:
            if comp.destroy_id == destroy_id:
                return comp
        raise ValueError('compositor for id not found')

    def sort_compositors(self):
        """
        Compositor order must be from top to bottom or will not work.
        """
        self.compositors.sort(_sort_compositors_comparator)

    # -------------------------- monitor clip, trimming display, output mode and hidden track
    def display_monitor_clip(self, path, pattern_producer_data=None):
        """
        Adds media clip to hidden track for viewing and for setting mark
        in and mark out points.
        pattern_producer_data is MediaFile or AbstractPatternProduer object
        """
        track = self.tracks[-1] # Always last track
        if pattern_producer_data == None:
            self.monitor_clip = self.create_file_producer_clip(path)
        else:
            if pattern_producer_data.type == IMAGE_SEQUENCE:
                self.monitor_clip = self.create_file_producer_clip(pattern_producer_data.path)
            else:
                self.monitor_clip = self.create_pattern_producer(pattern_producer_data)
        
        edit._insert_clip(track, self.monitor_clip, 0, 0, \
                          self.monitor_clip.get_length() - 1)
        self._mute_editable()
        return self.monitor_clip

    def display_trim_clip(self, path, clip_start_pos, patter_producer_data=None):
        """
        Adds clip to hidden track for trim editing display.
        """
        track = self.tracks[-1] # Always last track
        track.clear() # # TRIM INIT CRASH HACK, see clear_hidden_track there may be blank clip here
        track.clips = []

        # Display trimmmed clip on hidden track by creating copy of it.
        # File producer
        if path != None:
            clip = self.create_file_producer_clip(path)
            if clip_start_pos > 0:
                edit._insert_blank(track, 0, clip_start_pos)
                edit._insert_clip(track, clip, 1, 0, clip.get_length() - 1)
            else:
                edit._insert_clip(track, clip, 1, -clip_start_pos, clip.get_length() - 1) # insert index 1 ?
        # Pattern producer (FIX ME: does not allow for keyframes in pattern producer)
        else:
            clip = self.create_pattern_producer(patter_producer_data)
            edit._insert_clip(track, clip, 0, 0, clip.get_length() - 1)
        
        self._mute_editable()

    def hide_hidden_clips(self):
        """
        Called to temporarely remove hidden clips for trim mode loop playback
        """
        self.tracks[-1].clear()
        self._unmute_editable()

    def redisplay_hidden_clips(self):
        """
        Called after trim mode loop playback to redisplay hidden track clips
        """
        clips = self.tracks[-1].clips
        self.tracks[-1].clips = []
        for i in range(0, len(clips)):
            clip = clips[i]
            if clip.is_blanck_clip:
                edit._insert_blank(self.tracks[-1], i, 
                                   clip.clip_out - clip.clip_in + 1)
            else:
                edit._insert_clip(self.tracks[-1], clip, i, 
                                   clip.clip_in, clip.clip_out)
        self._mute_editable()

    def clear_hidden_track(self):
        """
        Last track is hidden track used to display clips and trim edits.
        Here that track is cleared of any content.
        """
        self.update_edit_tracks_length()

        # Empty timeline needs blank clip of len atleast 1 because  
        # edit_insert_blank() always needs a clip to add attributes to 
        # and that method is fundamendal and cannot be changed. 
        seq_len = self.seq_len
        if seq_len < 1:
            seq_len = 1
        
        self.tracks[-1].clips = []
        self.tracks[-1].clear()

        edit._insert_blank(self.tracks[-1], 0, seq_len) # TRIM INIT CRASH HACK. This being empty crashes a lot, so far unexplained.
        
        self._unmute_editable()

    def update_edit_tracks_length(self):
        # NEEDED FOR TRIM CRASH HACK, REMOVE IF FIXED
        self.seq_len = 0  # muuta  arvoksi 1 ???
        for i in range(1, len(self.tracks) - 1):
            track_len = self.tracks[i].get_length()
            if track_len > self.seq_len:
                self.seq_len = track_len

    def update_trim_hack_blank_length(self):
        # NEEDED FOR TRIM CRASH HACK, REMOVE IF FIXED
        self.tracks[-1].clips = []
        self.tracks[-1].clear()

        seq_len = self.seq_len
        if seq_len < 1:
            seq_len = 1
            
        edit._insert_blank(self.tracks[-1], 0, seq_len)

    def get_seq_range_frame(self, frame):
        # NEEDED FOR TRIM CRASH HACK, REMOVE IF FIXED
        # remove TimeLineFrameScale then too
        if frame >= (self.seq_len - 1):
            return self.seq_len - 1
        else:
            return frame

    def _mute_editable(self):
        for i in range(1, len(self.tracks) - 1):
            track = self.tracks[i]
            track.set("hide", 3)
    
    def _unmute_editable(self):
        for i in range(1, len(self.tracks) - 1):
            track = self.tracks[i]
            track.set("hide", int(track.mute_state))
    
    def set_tracks_mute_state(self):
        self._unmute_editable() # same thing, this method exists to declare purpose
        
    def set_output_mode(self, mode):
        if self.outputfilter != None:
            self.tractor.detach(self.outputfilter)
        
        self.outputfilter = None

        if mode == PROGRAM_OUT_MODE:
            return
        elif mode == VECTORSCOPE_MODE:
            self.tractor.attach(self.vectorscope)
            self.outputfilter = self.vectorscope
        elif mode == RGB_PARADE_MODE:
            self.tractor.attach(self.rgbparade)
            self.outputfilter = self.rgbparade

    # ---------------------------------------------------- watermark
    def add_watermark(self, watermark_file_path):
        watermark = mlt.Filter(self.profile, "watermark")
        mltrefhold.hold_ref(watermark)
        watermark.set("resource",str(watermark_file_path))
        watermark.set("composite.always_active", 1)
        self.tractor.attach(watermark)
        self.watermark_filter = watermark
        self.watermark_file_path = watermark_file_path

    def remove_watermark(self):
        self.tractor.detach(self.watermark_filter)
        self.watermark_filter = None
        self.watermark_file_path = None

    # ------------------------------------------------ length, seek, misc
    def update_length(self):
        """
        Set black to track length of sequence.
        """
        global black_track_clip
        if black_track_clip == None: # This fails for launch with assoc Gnome file because this has not been made yet.
                                     # This global black_track_clip is brain dead.  
            self._create_black_track_clip()
        c_in = 0
        c_out = self.get_length()
        black_track_clip.clip_in = c_in
        black_track_clip.clip_out = c_out
        black_track_clip.set_in_and_out(c_in, c_out)

    def get_length(self):
        return self.multitrack.get_length()

    def resize_tracks_to_fit(self, allocation):
        x, y, w, panel_height = allocation
        count = 0
        fix_next = True
        while(fix_next):
            tracks_height = self.get_tracks_height()
            if tracks_height < panel_height:
                fix_next = False
            elif count + 1 == self.first_video_index:
                # This shold not happen because track heights should be set up so that minimized app 
                # has enough space to display all tracks.
                # Yet it happens sometimes, meh.
                print "sequence.resize_tracks_to_fit (): could not make panels fit"
                fix_next = False
            else:
                self.tracks[1 + count].height = TRACK_HEIGHT_SMALL
                self.tracks[len(self.tracks) - 2 - count].height = TRACK_HEIGHT_SMALL
                count += 1

    def find_next_cut_frame(self, tline_frame):
        """
        Returns frame of next cut in active tracks relative to timeline.
        """
        cut_frame = -1
        for i in range(1, len(self.tracks)):
            track = self.tracks[i]
            if track.active == False:
                continue
            
            # Get index and clip
            index = track.get_clip_index_at(tline_frame)
            try:
                clip = track.clips[index]            
            except Exception:
                continue # Frame after last clip in track
            
            # Get next cut frame
            clip_start_in_tline = track.clip_start(index)
            length = clip.clip_out - clip.clip_in 
            next_cut_frame = clip_start_in_tline + length + 1 # +1 clip out inclusive
 
            # Set cut frame
            if cut_frame == -1:
                cut_frame = next_cut_frame
            elif next_cut_frame < cut_frame:
                cut_frame = next_cut_frame
                
        return cut_frame

    def find_prev_cut_frame(self, tline_frame):
        """
        Returns frame of next cut in active tracks relative to timeline.
        """
        cut_frame = -1
        for i in range(1, len(self.tracks)):
            track = self.tracks[i]
            if track == False:
                continue
            
            # Get index and clip start
            index = track.get_clip_index_at(tline_frame)
            clip_start_frame = track.clip_start(index)
            
            # If we are on cut, we want previous cut
            if clip_start_frame == tline_frame:
                index = index - 1
            
            # Check index is good
            try:
                clip = track.clips[index]            
            except Exception:
                continue # index not good clip
            
            # Get prev cut frame
            next_cut_frame = track.clip_start(index)
            
            # Set cut frame
            if cut_frame == -1:
                cut_frame = next_cut_frame
            elif next_cut_frame > cut_frame:
                cut_frame = next_cut_frame
                
        return cut_frame
    
    def get_closest_cut_frame(self, track_id, frame):
        track = self.tracks[track_id]
        index = track.get_clip_index_at(frame)
        try:
            clip = track.clips[index]            
        except Exception:
            return -1
            
        start_frame = track.clip_start(index)
        start_dist = frame - start_frame
        end_frame = start_frame + (clip.clip_out - clip.clip_in + 1) # frames are inclusive
        end_dist = end_frame - frame
        
        if start_dist < end_dist:
            return start_frame
        else:
            return end_frame
        
        return start_frame # equal distance

    def get_first_active_track(self):
        """
        This is done in a way that the user sees the track displayed as top most
        on screen being the first active when doing for e.g. a monitor insert.
        track: 0, black bg video
        tracks: 1 - (self.first_video_index - 1), audio, numbered to user in opposite direction as 1 - n (user_index = self.first_video_index - index)
        tracks: self.first_video_index - (len - 2), video, numbered to user as 1 - n (user_index = index - self.first_video_index + 1)
        track: (len - 1). hidden video track for trim and clip display
        """
        # Video
        for i in range(len(self.tracks) - 2, self.first_video_index - 1, -1):
            if self.tracks[i].active:
                return self.tracks[i]
        # Audio
        for i in range(self.first_video_index - 1, 0, -1):
            if self.tracks[i].active:
                return self.tracks[i]

        return None

    def get_clip_index(self, track, frame):
        """
        Returns index or -1 if frame not on a clip
        """
        index = track.get_clip_index_at(frame)
        try:
            clip = track.clips[index]
        except Exception:
            return -1
        
        return index

    """
    def next_mute_state(self, track_index):
        # track.mute_state values corrspond to mlt "hide" values
        track = self.tracks[track_index]
        if track.type == VIDEO:
            track.mute_state = track.mute_state + 1
            if track.mute_state > 3:
                track.mute_state = 0 # mlt "hide" all on
        else:
            if track.mute_state == 1:
                track.mute_state = 3 # mlt "hide" all off
            else:
                track.mute_state = 1 # mlt "hide" video off
        track.set("hide", int(track.mute_state))
    """
    
    def set_track_mute_state(self, track_index, mute_state):
        track = self.tracks[track_index]
        track.mute_state = mute_state
        track.set("hide", int(track.mute_state))

    def print_all(self):
        print "------------------------######"
        for i in range(0, len(self.tracks)):
            print "TRACK:", i
            self.print_track(i)

    def print_track(self, track_id):
        track = self.tracks[track_id]

        print "PYTHON"
        for i in range(0, len(track.clips)):
            clip = track.clips[i]
            if clip.is_blank():
                msg = "BLANK"
            else:
                msg = clip.name
     
            print i, ": id:", clip.id, " in:",clip.clip_in," out:", \
            clip.clip_out, msg

        print "MLT"
        for i in range(0, track.count()):
            clip = track.get_clip(i)
            print i, " in:", clip.get_in()," out:", clip.get_out()


    def print_compositors(self):
        for compositor in self.compositors:
            print "---"
            print compositor.name
            print "a_track:" , compositor.transition.a_track
            print "b_track:" , compositor.transition.b_track

# ------------------------------------------------ module util methods
def get_media_type(file_path):
    """
    Returns media type of file.
    """
    if os.path.exists(file_path):
        mime_type = utils.get_file_type(file_path)
    else:
        # IMAGE_SEQUENCE media objects have a MLT formatted resource path that does not
        # point to an existing file in the file system. 
        # We're doing a heuristic here to identify those.
        pros_index = file_path.find("%0")
        d_index = file_path.find("d.")
        if pros_index != -1 and d_index != -1:
            return IMAGE_SEQUENCE
        all_index = file_path.find(".all")
        if all_index != -1:
            return IMAGE_SEQUENCE
            
        return FILE_DOES_NOT_EXIST
        
    if mime_type.startswith("video"):
        return VIDEO
    
    if mime_type.startswith("audio"):
        return AUDIO
    
    if mime_type.startswith("image"):
        return IMAGE
    
    return UNKNOWN

def _clip_length(clip):
    return clip.clip_out - clip.clip_in + 1

def _sort_compositors_comparator(a_comp, b_comp):
    # compositors on top most tracks first
    if a_comp.transition.b_track > b_comp.transition.b_track:
        return -1
    elif a_comp.transition.b_track < b_comp.transition.b_track:
        return 1
    else:
        return 0

# ----------------------------- sequence cloning for tracks count change
def create_sequence_clone_with_different_track_count(old_seq, v_tracks, a_tracks):
    # Create new sequence with different number of tracks
    global AUDIO_TRACKS_COUNT, VIDEO_TRACKS_COUNT
    AUDIO_TRACKS_COUNT = a_tracks
    VIDEO_TRACKS_COUNT = v_tracks
    new_seq = Sequence(old_seq.profile, old_seq.name)
    new_seq.create_default_tracks()

    # Clone track clips from old sequence to clone sequence
    if old_seq.first_video_index - 1 > a_tracks:
        _clone_for_fewer_tracks(old_seq, new_seq)
    else:
        _clone_for_more_tracks(old_seq, new_seq)

    # Clone compositors from old seq to new to correct tracks on new seq
    track_delta = new_seq.first_video_index - old_seq.first_video_index
    new_seq.clone_compositors_from_sequence(old_seq, track_delta)

    # copy next clip id data
    new_seq.next_id = old_seq.next_id
    return new_seq
        
def _clone_for_more_tracks(old_seq, new_seq):
    # clone track contentents
    audio_tracks_count_diff = new_seq.first_video_index - old_seq.first_video_index
    first_to_track_index = audio_tracks_count_diff + 1 # +1, black bg track
    last_to_track_index = first_to_track_index + len(old_seq.tracks) - 3 # - 3 because: black bg track, hidden track, out inclusive
    _clone_tracks(old_seq, new_seq, first_to_track_index, last_to_track_index, 1)

def _clone_for_fewer_tracks(old_seq, new_seq):
    first_to_track_index = 1
    last_to_track_index = first_to_track_index + len(new_seq.tracks) - 3 # - 3 because: black bg track, hidden track, out inclusive
    audio_tracks_count_diff = old_seq.first_video_index - new_seq.first_video_index
    from_track_index = audio_tracks_count_diff + 1  # +1, black bg track
    _clone_tracks(old_seq, new_seq, first_to_track_index, last_to_track_index, from_track_index)

def _clone_tracks(old_seq, new_seq, first_to_track_index, last_to_track_index, first_from_track_index):
    from_track_index = first_from_track_index
    for i in range(first_to_track_index, last_to_track_index + 1):
        if from_track_index > len(old_seq.tracks) - 1: # when changing to a (8V,1A) tracks sequence this range needs to be checked for
            continue 
        from_track = old_seq.tracks[from_track_index]
        
        if i > len(new_seq.tracks) - 1: # when changing to a (1V,8A) tracks sequence this range needs to be checked for
            continue
        to_track = new_seq.tracks[i]

        _copy_track_contents(from_track, to_track, new_seq)
        from_track_index = from_track_index + 1
    
def _copy_track_contents(from_track, to_track, to_sequence):
    # Copy clips
    for i in range(0, len(from_track.clips)):
        clip = from_track.clips[i]
        if clip.is_blanck_clip != True:
            edit.append_clip(to_track, clip, clip.clip_in, clip.clip_out)
        else:
            edit._insert_blank(to_track, i, clip.clip_out - clip.clip_in + 1)
    
    from_track.clear()
    from_track.clips = []

    # Copy track attributes.
    to_sequence.set_track_mute_state(to_track.id, from_track.mute_state)
    to_track.edit_freedom = from_track.edit_freedom
