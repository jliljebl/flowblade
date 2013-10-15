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
Module for saving and loading projects.

Main functionality of the module is to replace unpickleable 
SwigPyObject MLT objects with pickleable python objects for save, 
and then create MLT objects from pickled objects when project is loaded.
"""

import copy
import gtk
import pickle
import time

import appconsts
import edit
import mltprofiles
import mltfilters
import mlttransitions
import resync

# Unpickleable attributes for all objects
# These are removed at save and recreated at load.
PROJECT_REMOVE = ['profile','c_seq', 'thumbnail_thread']
SEQUENCE_REMOVE = ['profile','field','multitrack','tractor','monitor_clip','vectorscope','audiowave','rgbparade','outputfilter']
PLAY_LIST_REMOVE = ['this','sequence','get_name','gain_filter','pan_filter']
CLIP_REMOVE = ['this','clip_length']
TRANSITION_REMOVE = ['this']
FILTER_REMOVE = ['mlt_filter','mlt_filters']
MEDIA_FILE_REMOVE = ['icon']

"""
MLT_TYPES = ('Mlt__Producer','Mlt__Filter','Mlt__Playlist','MLT_Field'
             ,'Mlt__Tractor','Mlt_Multitrack')

TRANSITION_TYPE = "##transition##"
"""

# Used to send messages when loading project
load_dialog = None

# These are used to recrete parenting relationships
all_clips = {}
sync_clips = []

show_messages = True


class FileProducerNotFoundError(Exception):
    """
    We're only catching this, other errors we'll just crash on load
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ProjectProfileNotFoundError(Exception):
    """
    We're only catching this, other errors we'll just crash on load
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# -------------------------------------------------- LOAD MESSAGES
def _show_msg(msg, delay=0.0):
    if show_messages == True:
        gtk.gdk.threads_enter()
        load_dialog.info.set_text(msg)
        time.sleep(delay)
        gtk.gdk.threads_leave()

# -------------------------------------------------- SAVE
def save_project(project, file_path):
    """
    Creates pickleable project object
    """
    print "Save project " + file_path
    
    # Get shallow copy
    s_proj = copy.copy(project)
    
    # Set current sequence index
    s_proj.c_seq_index = project.sequences.index(project.c_seq)
    
    # Set project SAVEFILE_VERSION to current in case this is a resave of older file type.
    # Older file type has been converted to newer file type on load.
    s_proj.SAVEFILE_VERSION = appconsts.SAVEFILE_VERSION
 
    # Replace media file objects with pickleable copys
    media_files = {}
    for k, v in s_proj.media_files.iteritems():
        s_media_file = copy.copy(v)
        remove_attrs(s_media_file, MEDIA_FILE_REMOVE)
        media_files[s_media_file.id] = s_media_file
    s_proj.media_files = media_files
    
    # Replace sequences with pickleable objects
    sequences = []
    for i in range(0, len(project.sequences)):
        add_seq = project.sequences[i]
        sequences.append(get_p_sequence(add_seq))
    s_proj.sequences = sequences

    # Remove unpickleable attributes
    remove_attrs(s_proj, PROJECT_REMOVE)
    
    # Write out file.
    write_file = file(file_path, "wb")
    pickle.dump(s_proj, write_file)

def get_p_sequence(sequence):
    """
    Creates pickleable sequence object from MLT Playlist
    """
    s_seq = copy.copy(sequence)
    
    # Replace tracks with pickleable objects
    tracks = []
    for i in range(0, len(sequence.tracks)):
        track = sequence.tracks[i]
        tracks.append(get_p_playlist(track))
    s_seq.tracks = tracks

    # Replace compositors with pwckleable objects
    s_compositors = get_p_compositors(sequence.compositors)
    s_seq.compositors = s_compositors

    # Remove unpickleable attributes
    remove_attrs(s_seq, SEQUENCE_REMOVE)

    return s_seq

def get_p_playlist(playlist):
    """
    Creates pickleable version of MLT Playlist
    """
    s_playlist = copy.copy(playlist)
    
    # Get replace clips
    add_clips = []
    for i in range(0, len(playlist.clips)):
        clip = playlist.clips[i]
        add_clips.append(get_p_clip(clip))

    s_playlist.clips = add_clips
    
    # Remove unpicleable attributes
    remove_attrs(s_playlist, PLAY_LIST_REMOVE)
   
    return s_playlist

def get_p_clip(clip):
    """
    Creates pickleable version of MLT Producer object
    """
    s_clip = copy.copy(clip)
    print "mlt clip:"
    swig_this = getattr(clip,'this')
    print clip.__dict__, str(swig_this), swig_this.__class__
     
    # Set 'type' attribute for MLT object type
    #set_pickled_type(s_clip, str(getattr(clip,'this')))
    s_clip.type = 'Mlt__Producer'

    # Get replace filters
    filters = []
    try: # This fails for blank clips
         # We'll just save them with empty filters array
        for i in range(0, len(clip.filters)):
            f = clip.filters[i]
            filters.append(get_p_filter(f))
    except:
        pass
    s_clip.filters = filters
    
    # Replace mute filter object with boolean to flag mute
    if s_clip.mute_filter != None:
        s_clip.mute_filter = True
        
    # Get replace sync data
    if s_clip.sync_data != None:
         s_clip.sync_data = get_p_sync_data(s_clip.sync_data)
    
    # Remove unpicleable attributes
    remove_attrs(s_clip, CLIP_REMOVE)

    # Don't save waveform data.
    s_clip.waveform_data = None

    # Add pickleable filters
    s_clip.filters = filters

    print "python clip:"
    print s_clip.__dict__

    return s_clip

def get_p_filter(filter):
    """
    Creates pickleable version MLT Filter object.
    """
    s_filter = copy.copy(filter)
    remove_attrs(s_filter, FILTER_REMOVE)
    if hasattr(filter, "mlt_filter"):
        s_filter.is_multi_filter = False
    else:
        s_filter.is_multi_filter = True

    return s_filter

def get_p_compositors(compositors):
    s_compositors = []
    for compositor in compositors:
        s_compositor = copy.copy(compositor)
        s_compositor.transition = copy.copy(compositor.transition)
        s_compositor.transition.mlt_transition = None
        s_compositors.append(s_compositor)

    return s_compositors

def get_p_sync_data(sync_data):
    s_sync_data = copy.copy(sync_data)
    s_sync_data.master_clip = sync_data.master_clip.id
    return s_sync_data

"""    
def set_pickled_type(obj, this):
    obj.type = "UNDEFINED"
    for mlt_type in MLT_TYPES:
        if this.find(mlt_type) > -1:
            obj.type = mlt_type
            return
"""
            
def remove_attrs(obj, remove_attrs):
    """
    Removes unpickleable attributes
    """
    for attr in remove_attrs:
        try:
            delattr(obj, attr)
        except Exception:
            pass


# -------------------------------------------------- LOAD
def load_project(file_path, icons_and_thumnails=True):
    _show_msg("Unpickling")

    # Load project object
    f = open(file_path)
    project = pickle.load(f)

    if(not hasattr(project, "SAVEFILE_VERSION")):
        project.SAVEFILE_VERSION = 1 # first save files did not have this
    print "Loading, SAVEFILE_VERSION:", project.SAVEFILE_VERSION

    # Set MLT profile
    project.profile = mltprofiles.get_profile(project.profile_desc)
    
    # Some profiles may not be available in system
    # inform user on fix
    if project.profile == None:
        raise ProjectProfileNotFoundError(project.profile_desc)

    # Add MLT objects to sequences.
    global all_clips, sync_clips
    for seq in project.sequences:
        FIX_N_TO_3_SEQUENCE_COMPATIBILITY(seq)
        _show_msg(_("Building sequence ") + seq.name)
        all_clips = {}
        sync_clips = []
                
        seq.profile = project.profile
        fill_sequence_mlt(seq, project.SAVEFILE_VERSION)
        
    all_clips = {}
    sync_clips = []

    # Add icons to media files
    if icons_and_thumnails == True:
        _show_msg(_("Loading icons"))
        for k, media_file in project.media_files.iteritems():
            media_file.create_icon()
    
    project.c_seq = project.sequences[project.c_seq_index]
    if icons_and_thumnails == True:
        project.start_thumbnail_thread()

    return project

def fill_sequence_mlt(seq, SAVEFILE_VERSION):
    """
    Replaces sequences py objects with mlt objects
    """
    # Create tractor, field, multitrack
    seq.init_mlt_objects()
    
    # Grap and replace py tracks. Do this way to use same create
    # method as when originally created.
    py_tracks = seq.tracks
    seq.tracks = []
    
    # Create and fill MLT tracks.
    for py_track in py_tracks:
        mlt_track = seq.add_track(py_track.type)
        fill_track_mlt(mlt_track, py_track)
        # Set audio gain and pan filter values
        if hasattr(mlt_track, "gain_filter"): # Hidden track and black track do not have these
            mlt_track.gain_filter.set("gain", str(mlt_track.audio_gain))
        if mlt_track.audio_pan != appconsts.NO_PAN:
            seq.add_track_pan_filter(mlt_track, mlt_track.audio_pan) # only rtack with non-center pan values have pan filters
    
    # Create and connect compositors.
    mlt_compositors = []
    for py_compositor in seq.compositors:
            # Keeping backwards compability
            if SAVEFILE_VERSION < 3:
                FIX_N_TO_3_COMPOSITOR_COMPABILITY(py_compositor, SAVEFILE_VERSION)
        
            # Create new compositor object
            compositor = mlttransitions.create_compositor(py_compositor.type_id)                                        
            compositor.create_mlt_objects(seq.profile)

            # Copy and set param values
            compositor.transition.properties = copy.deepcopy(py_compositor.transition.properties)
            compositor.transition.update_editable_mlt_properties()
    
            compositor.transition.set_tracks(py_compositor.transition.a_track, py_compositor.transition.b_track)
            compositor.set_in_and_out(py_compositor.clip_in, py_compositor.clip_out)
            compositor.origin_clip_id = py_compositor.origin_clip_id
            mlt_compositors.append(compositor)

    seq.compositors = mlt_compositors
    seq.restack_compositors()

    # Connect sync relations
    for clip_n_track in sync_clips:
        clip, track = clip_n_track
        try:
            master_clip = all_clips[clip.sync_data.master_clip] # master clip has been replaced with its id on save
            clip.sync_data.master_clip = master_clip # put back reference to master clip
            resync.clip_added_to_timeline(clip, track) # save data to enagble sync states monitoring after eddits
        except KeyError:
            clip.sync_data = None # masterclip no longer on track V1
            resync.clip_removed_from_timeline(clip)

    seq.length = None

def fill_track_mlt(mlt_track, py_track):
    """
    Replaces py objects in track (MLT Playlist) with mlt objects
    """
    # Update mlt obj attr values to saved ones
    mlt_track.__dict__.update(py_track.__dict__)
    
    # Clear py clips from MLT object
    mlt_track.clips = []
    
    # Create clips
    sequence = mlt_track.sequence
    for i in range(0, len(py_track.clips)):
        clip = py_track.clips[i]
        mlt_clip = None
        append_created = True # blanks get appended at creation time, others don't

        # Add color attribute if not found
        if not hasattr(clip, "color"):
            clip.color = None

        # normal clip
        if ((clip.type == "Mlt__Producer") and clip.is_blanck_clip == False and 
            (clip.media_type != appconsts.PATTERN_PRODUCER)): 
            mlt_clip = sequence.create_file_producer_clip(clip.path)
            if mlt_clip == None:
                raise FileProducerNotFoundError(clip.path)
            mlt_clip.__dict__.update(clip.__dict__)
            fill_filters_mlt(mlt_clip, sequence)
        # pattern producer    
        elif ((clip.type == "Mlt__Producer") and clip.is_blanck_clip == False and 
            (clip.media_type == appconsts.PATTERN_PRODUCER)):
            mlt_clip = sequence.create_pattern_producer(clip.create_data)
            mlt_clip.__dict__.update(clip.__dict__)
        # blank clip
        elif ((clip.type == "Mlt__Producer") and clip.is_blanck_clip == True): 
            length = clip.clip_out - clip.clip_in + 1
            mlt_clip = sequence.create_and_insert_blank(mlt_track, i, length)
            mlt_clip.__dict__.update(clip.__dict__)
            append_created = False
            """
            # quick transition clip
            # Clip is saved_as data object created in mlttransitions.py
            elif clip.type == TRANSITION_TYPE:
                action = mlttransitions.get_create_action(clip, sequence) 
                mlt_clip = sequence.create_transition(action)
            """
        else:
            print "Could not recognize clip, dict:"
            print clip.__dict__

        mlt_clip.selected = False # This transient state gets saved and 
                                  # we want everything unselected to begin with
        # Mute 
        if clip.mute_filter != None:
            mute_filter = edit._create_mute_volume_filter(sequence) 
            edit._do_clip_mute(mlt_clip, mute_filter)
        
        # Add to track is hasn't already been appended (blank clip has)
        if append_created == True:
            edit.append_clip(mlt_track, mlt_clip, clip.clip_in, clip.clip_out)

        # Save refences to recreate sync relations after all clips loaded
        global all_clips, sync_clips
        all_clips[mlt_clip.id] = mlt_clip
        if mlt_clip.sync_data != None:
            sync_clips.append((mlt_clip, mlt_track))

def fill_filters_mlt(mlt_clip, sequence):
    """
    Creates new FilterObject objects and creates and attaches mlt.Filter
    objects.
    """ 
    filters = []
    for py_filter in mlt_clip.filters:
        if py_filter.is_multi_filter == False:
            if py_filter.info.mlt_service_id == "affine":
                FIX_1_TO_N_BACKWARDS_FILTER_COMPABILITY(py_filter)
            filter_object = mltfilters.FilterObject(py_filter.info)
            filter_object.__dict__.update(py_filter.__dict__)
            filter_object.create_mlt_filter(sequence.profile)
            mlt_clip.attach(filter_object.mlt_filter)
        else:
            filter_object = mltfilters.MultipartFilterObject(py_filter.info)
            filter_object.__dict__.update(py_filter.__dict__)
            filter_object.create_mlt_filters(sequence.profile, mlt_clip)
            filter_object.attach_all_mlt_filters(mlt_clip)

        if filter_object.active == False:
            filter_object.update_mlt_disabled_value()

        filters.append(filter_object)
    
    mlt_clip.filters = filters
    

# ------------------------------------------------------- backwards compability
def FIX_N_TO_3_COMPOSITOR_COMPABILITY(compositor, SAVEFILE_VERSION):
    if SAVEFILE_VERSION == 1:
        FIX_1_TO_2_BACKWARDS_COMPOSITOR_COMPABILITY(compositor)
    
    FIX_2_TO_N_BACKWARDS_COMPOSITOR_COMPABILITY(compositor)
    
def FIX_1_TO_2_BACKWARDS_COMPOSITOR_COMPABILITY(compositor):
    # fix SAVEFILE_VERSION 1 -> N compability issue with x,y -> x/y in compositors
    new_properties = []
    for prop in compositor.transition.properties:
        name, value, prop_type = prop
        value = value.replace(",","/")
        new_properties.append((name, value, prop_type))
    compositor.transition.properties = new_properties

def FIX_2_TO_N_BACKWARDS_COMPOSITOR_COMPABILITY(compositor):
    compositor.type_id = compositors_index_to_type_id[compositor.compositor_index]

def FIX_1_TO_N_BACKWARDS_FILTER_COMPABILITY(py_filter):
    # This is only called on "affine" filters
    # fix SAVEFILE_VERSION 1 -> N compability issue with x,y -> x/y in compositors
    new_properties = []
    for prop in py_filter.properties:
        name, value, prop_type = prop
        value = value.replace(",","/")
        new_properties.append((name, value, prop_type))
    py_filter.properties = new_properties

def FIX_N_TO_3_SEQUENCE_COMPATIBILITY(seq):
    if not hasattr(seq, "master_audio_pan"):
        seq.master_audio_pan = appconsts.NO_PAN
        seq.master_audio_gain = 1.0

# List is used to convert SAVEFILE_VERSIONs 1 and 2 to SAVEFILE_VERSIONs 3 -> n by getting type_id string for compositor index 
compositors_index_to_type_id = ["##affine","##opacity_kf","##pict_in_pict", "##region","##wipe", "##add",
                                "##burn", "##color_only", "##darken", "##difference", "##divide", "##dodge",
                                "##grain_extract", "##grain_merge", "##hardlight", "##hue", "##lighten",
                                "##multiply", "##overlay", "##saturation", "##screen", "##softlight",
                                "##subtract", "##value"]
