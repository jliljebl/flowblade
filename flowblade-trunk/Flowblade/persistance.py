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


import pygtk
pygtk.require('2.0');
import gtk

import copy
import fnmatch
import os
import pickle
import time

import appconsts
import editorstate
import editorpersistance
import mltprofiles
import mltfilters
import mlttransitions
import miscdataobjects
import propertyparse
import resync

# Unpickleable attributes for all objects
# These are removed at save and recreated at load.
PROJECT_REMOVE = ['profile','c_seq']
SEQUENCE_REMOVE = ['profile','field','multitrack','tractor','monitor_clip','vectorscope','audiowave','rgbparade','outputfilter','watermark_filter']
PLAY_LIST_REMOVE = ['this','sequence','get_name','gain_filter','pan_filter']
CLIP_REMOVE = ['this','clip_length']
TRANSITION_REMOVE = ['this']
FILTER_REMOVE = ['mlt_filter','mlt_filters']
MEDIA_FILE_REMOVE = ['icon']

# Used to flag a not found relative path
NOT_FOUND = "/not_found_not_found/not_found"

# Used to send messages when loading project
load_dialog = None

# These are used to recrete parenting relationships
all_clips = {}
sync_clips = []

# Used for for convrtting to and from proxy media using projects
project_proxy_mode = -1
proxy_path_dict = None

# Flag for showing progress messages on GUI when loading
show_messages = True

# Path of file being loaded, global for convenience. Used toimplement relative paths search on load
_load_file_path = None

# Used to change media item and clip paths when saving backup snapshot.
# 'snapshot_paths != None' flags that snapsave is being done and paths need to be replaced 
snapshot_paths = None


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
    print "Save project " + os.path.basename(file_path)
    
    # Get shallow copy
    s_proj = copy.copy(project)
    
    # Set current sequence index
    s_proj.c_seq_index = project.sequences.index(project.c_seq)
    
    # Set project SAVEFILE_VERSION to current in case this is a resave of older file type.
    # Older file type has been converted to newer file type on load.
    s_proj.SAVEFILE_VERSION = appconsts.SAVEFILE_VERSION

    # Init proxy convert data
    global project_proxy_mode, proxy_path_dict
    project_proxy_mode = s_proj.proxy_data.proxy_mode
    proxy_path_dict = {}

    # Replace media file objects with pickleable copys
    media_files = {}
    for k, v in s_proj.media_files.iteritems():
        s_media_file = copy.copy(v)
        remove_attrs(s_media_file, MEDIA_FILE_REMOVE)
        
        # Convert media files between original and proxy files
        if project_proxy_mode == appconsts.CONVERTING_TO_USE_PROXY_MEDIA:
            if s_media_file.has_proxy_file:
                proxy_path_dict[s_media_file.path] = s_media_file.second_file_path
                s_media_file.set_as_proxy_media_file()
        elif project_proxy_mode == appconsts.CONVERTING_TO_USE_ORIGINAL_MEDIA:
            if s_media_file.is_proxy_file:
                proxy_path_dict[s_media_file.path] = s_media_file.second_file_path
                s_media_file.set_as_original_media_file()

        # Change paths when doing snapshot save
        if snapshot_paths != None:
            if s_media_file.type != appconsts.PATTERN_PRODUCER:
                s_media_file.path = snapshot_paths[s_media_file.path] 

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
     
    # Set 'type' attribute for MLT object type
    # This IS NOT USED anywhere anymore and should be removed.
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
    
    # Do proxy mode convert if needed
    if (project_proxy_mode == appconsts.CONVERTING_TO_USE_PROXY_MEDIA or 
        project_proxy_mode == appconsts.CONVERTING_TO_USE_ORIGINAL_MEDIA):
        try: # This fails when it is supposed to fail: for clips that have no proxy and pattern producers and blanks
            s_clip.path = proxy_path_dict[s_clip.path] 
        except:
            pass

    # Change paths when doing snapshot save
    try: # This fails for pattern producers and blanks
        if snapshot_paths != None:
            s_clip.path = snapshot_paths[s_clip.path] 
    except:
        pass

    return s_clip

def get_p_filter(f):
    """
    Creates pickleable version MLT Filter object.
    """
    s_filter = copy.copy(f)
    remove_attrs(s_filter, FILTER_REMOVE)
    if f.info.multipart_filter == False:
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
    if isinstance( sync_data.master_clip, int ): # When saving relinked projects sync_data.master_clip 
                                                   # is already int and does not need to be replaced
        return s_sync_data
    s_sync_data.master_clip = sync_data.master_clip.id
    return s_sync_data

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
def load_project(file_path, icons_and_thumnails=True, relinker_load=False):
    _show_msg("Unpickling")

    # Load project object
    f = open(file_path)
    project = pickle.load(f)

    # Relinker only operates on pickleable python data 
    if relinker_load:
        return project

    global _load_file_path
    _load_file_path = file_path
    
    # editorstate.project needs to be available for sequence building
    editorstate.project = project

    if(not hasattr(project, "SAVEFILE_VERSION")):
        project.SAVEFILE_VERSION = 1 # first save files did not have this
    print "Loading " + project.name + ", SAVEFILE_VERSION:", project.SAVEFILE_VERSION

    # Set MLT profile. NEEDS INFO USER ON MISSING PROFILE!!!!!
    project.profile = mltprofiles.get_profile(project.profile_desc)

    FIX_MISSING_PROJECT_ATTRS(project)

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

        handle_seq_watermark(seq)

        if not hasattr(seq, "seq_len"):
            seq.update_edit_tracks_length()

    all_clips = {}
    sync_clips = []

    for k, media_file in project.media_files.iteritems():
        if project.SAVEFILE_VERSION < 4:
            FIX_N_TO_4_MEDIA_FILE_COMPATIBILITY(media_file)
        media_file.current_frame = 0 # this is always reset on load, value is not considered persistent
        if media_file.type != appconsts.PATTERN_PRODUCER:
            media_file.path = get_media_asset_path(media_file.path, _load_file_path)
            
    # Add icons to media files
    if icons_and_thumnails == True:
        _show_msg(_("Loading icons"))
        for k, media_file in project.media_files.iteritems():
            media_file.create_icon()
    
    project.c_seq = project.sequences[project.c_seq_index]
    if icons_and_thumnails == True:
        project.init_thumbnailer()

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

    # editorstate.project.c_seq needs to be available for sequence building 
    editorstate.project.c_seq = seq
    
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
            _fix_wipe_relative_path(compositor)
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

    # This sets MLT properties that actually do mute
    seq.set_tracks_mute_state()

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
        append_created = True # blanks get appended at creation time, other clips don't

        # Add color attribute if not found
        if not hasattr(clip, "color"):
            clip.color = None

        # normal clip
        if (clip.is_blanck_clip == False and (clip.media_type != appconsts.PATTERN_PRODUCER)):
            orig_path = clip.path # Save the path for error message
            
            clip.path = get_media_asset_path(clip.path, _load_file_path)
                
            mlt_clip = sequence.create_file_producer_clip(clip.path)
            if mlt_clip == None:
                raise FileProducerNotFoundError(orig_path)
            mlt_clip.__dict__.update(clip.__dict__)
            fill_filters_mlt(mlt_clip, sequence)
        # pattern producer
        elif (clip.is_blanck_clip == False and (clip.media_type == appconsts.PATTERN_PRODUCER)):
            mlt_clip = sequence.create_pattern_producer(clip.create_data)
            mlt_clip.__dict__.update(clip.__dict__)
            fill_filters_mlt(mlt_clip, sequence)
        # blank clip
        elif (clip.is_blanck_clip == True): 
            length = clip.clip_out - clip.clip_in + 1
            mlt_clip = sequence.create_and_insert_blank(mlt_track, i, length)
            mlt_clip.__dict__.update(clip.__dict__)
            append_created = False
        else: # This is just for info, if this ever happens crash will happen.
            print "Could not recognize clip, dict:"
            print clip.__dict__

        mlt_clip.selected = False # This transient state gets saved and 
                                   # we want everything unselected to begin with
        # Mute 
        if clip.mute_filter != None:
            mute_filter = mltfilters.create_mute_volume_filter(sequence) 
            mltfilters.do_clip_mute(mlt_clip, mute_filter)
        
        # Add to track in MLT if hasn't already been appended (blank clip has)
        if append_created == True:
            append_clip(mlt_track, mlt_clip, clip.clip_in, clip.clip_out)

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
    
#------------------------------------------------------------ track building
# THIS IS COPYPASTED FROM edit.py TO NOT IMPORT IT.
def append_clip(track, clip, clip_in, clip_out):
    """
    Affects MLT c-struct and python obj values.
    """
    clip.clip_in = clip_in
    clip.clip_out = clip_out
    track.clips.append(clip) # py
    track.append(clip, clip_in, clip_out) # mlt
    resync.clip_added_to_timeline(clip, track)

# --------------------------------------------------------- watermarks
def handle_seq_watermark(seq):    
    if hasattr(seq, "watermark_file_path"):
        if seq.watermark_file_path != None:
            seq.add_watermark(seq.watermark_file_path)
        else:
            seq.watermark_filter = None
    else:
        seq.watermark_filter = None
        seq.watermark_file_path = None

# --------------------------------------------------------- relative paths
def get_media_asset_path(path, load_file_path):
    # Load order absolute, relative
    if editorpersistance.prefs.media_load_order == appconsts.LOAD_ABSOLUTE_FIRST:
        if not os.path.isfile(path):
            path = get_relative_path(load_file_path, path)
        return path
    # Load order relative, absolute
    elif editorpersistance.prefs.media_load_order == appconsts.LOAD_RELATIVE_FIRST:
        abspath = path
        path = get_relative_path(load_file_path, path)
        if path == NOT_FOUND:
            path = abspath
        return path
    else: # Only look in existing absolute path
        return path

def get_relative_path(project_file_path, asset_path):
    name = os.path.basename(asset_path)
    _show_msg("Relative file search for "  + name + "...", delay=0.0)
    matches = []
    asset_folder, asset_file_name = os.path.split(asset_path)
    project_folder, project_file_name =  os.path.split(project_file_path)
    
    for root, dirnames, filenames in os.walk(project_folder):
        for filename in fnmatch.filter(filenames, asset_file_name):
            matches.append(os.path.join(root, filename))
    if len(matches) == 1:
        return matches[0]
    elif  len(matches) > 1:
        # some error handling may be needed?
        return matches[0]
    else:
        return NOT_FOUND # no relative path found

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

def FIX_N_TO_4_MEDIA_FILE_COMPATIBILITY(media_file):
    media_file.has_proxy_file = False
    media_file.is_proxy_file = False
    media_file.second_file_path = None

def FIX_MISSING_PROJECT_ATTRS(project):
    if (not(hasattr(project, "proxy_data"))):
        project.proxy_data = miscdataobjects.ProjectProxyEditingData()

    if (not(hasattr(project, "media_log"))):
        project.media_log = []

    if (not(hasattr(project, "events"))):
        project.events = []

    if (not(hasattr(project, "media_log_groups"))):
        project.media_log_groups = []

def _fix_wipe_relative_path(compositor):
    if compositor.type_id == "##wipe": # Wipe may have user luma and needs to be looked up relatively
        _set_wipe_res_path(compositor, "resource")
    if compositor.type_id == "##region": # Wipe may have user luma and needs to be looked up relatively
        _set_wipe_res_path(compositor, "composite.luma")

def _set_wipe_res_path(compositor, res_property):
    res_path = propertyparse.get_property_value(compositor.transition.properties, res_property)
    new_path = get_media_asset_path(res_path, _load_file_path)
    propertyparse.set_property_value(compositor.transition.properties, res_property, new_path)

# List is used to convert SAVEFILE_VERSIONs 1 and 2 to SAVEFILE_VERSIONs 3 -> n by getting type_id string for compositor index 
compositors_index_to_type_id = ["##affine","##opacity_kf","##pict_in_pict", "##region","##wipe", "##add",
                                "##burn", "##color_only", "##darken", "##difference", "##divide", "##dodge",
                                "##grain_extract", "##grain_merge", "##hardlight", "##hue", "##lighten",
                                "##multiply", "##overlay", "##saturation", "##screen", "##softlight",
                                "##subtract", "##value"]
