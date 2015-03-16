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

import pygtk
pygtk.require('2.0');
import gtk
import glib
import os, sys
from xml.dom import minidom
from decimal import Decimal,getcontext,ROUND_DOWN
from math import modf, floor
import mlt
import time
import md5
import re
import shutil

import dialogs
import dialogutils
from editorstate import PLAYER
from editorstate import PROJECT
from editorstate import current_sequence
import gui
import guiutils
import renderconsumer
import utils

EDL_TYPE_AVID_CMX3600 = 0

AUDIO_FROM_VIDEO = 0
AUDIO_FROM_AUDIO_TRACK = 1
NO_AUDIO = 2

REEL_NAME_3_NUMBER = 0
REEL_NAME_8_NUMBER = 1
REEL_NAME_FILE_NAME_START = 2

CLIP_OUT_IS_LAST_FRAME = -999

_xml_render_player = None

_screenshot_img = None
_img_types = ["png", "bmp", "targa","tiff"]
_img_extensions = ["png", "bmp", "tga","tif"]

####---------------MLT--------------####    
def MELT_XML_export():
    dialogs.export_xml_dialog(_export_melt_xml_dialog_callback, PROJECT().name)

def _export_melt_xml_dialog_callback(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        filenames = dialog.get_filenames()
        save_path = filenames[0]
        global _xml_render_monitor
        _xml_render_player = renderconsumer.XMLRenderPlayer(save_path,
                                                          _xml_render_done,
                                                          None)
        _xml_render_player.start()
        
        dialog.destroy()
    else:
        dialog.destroy()

def _xml_render_done(data):
    global _xml_render_player
    _xml_render_player = None



####---------------EDL--------------####
def EDL_export():
    dialogs.export_edl_dialog(_export_edl_dialog_callback, gui.editor_window.window, PROJECT().name)

def _export_edl_dialog_callback(dialog, response_id, data):
    if response_id == gtk.RESPONSE_YES:
        file_name, out_folder, track_select_combo, cascade_check, op_combo, audio_track_select_combo = data
        edl_path = out_folder.get_filename()+ "/" + file_name.get_text() + ".edl" 
        global _xml_render_monitor
        _xml_render_player = renderconsumer.XMLRenderPlayer(get_edl_temp_xml_path(),
                                                            _edl_xml_render_done,
                                                            (edl_path, track_select_combo, cascade_check, op_combo, audio_track_select_combo))
        _xml_render_player.start()

        dialog.destroy()
    else:
        dialog.destroy()

def _edl_xml_render_done(data):
    edl_path, track_select_combo, cascade_check, op_combo, audio_track_select_combo = data
    video_track = current_sequence().first_video_index + track_select_combo.get_active()
    audio_track = 1 + audio_track_select_combo.get_active()
    global _xml_render_player
    _xml_render_player = None
    mlt_parse = MLTXMLToEDLParse(get_edl_temp_xml_path(), edl_path)
    edl_contents = mlt_parse.create_edl(video_track, 
                                        cascade_check.get_active(),
                                        op_combo.get_active(), 
                                        audio_track)
    f = open(edl_path, 'w')
    f.write(edl_contents)
    f.close()

def get_edl_temp_xml_path():
    return utils.get_hidden_user_dir_path() + "edl_temp_xml.xml"


class MLTXMLToEDLParse:
    def __init__(self, xmlfile, title):
        self.xmldoc = minidom.parse(xmlfile)
        self.title = title
        self.reel_name_type = REEL_NAME_FILE_NAME_START
        self.from_clip_comment = False
        self.use_drop_frames = False
        self.blender_fix = False

    def get_project_profile(self):
        profile_dict = {}
        profile = self.xmldoc.getElementsByTagName("profile")
        key_list = profile.item(0).attributes.keys()
        for a in key_list:
            profile_dict[a] = profile.item(0).attributes[a].value
        return profile_dict
    
    def get_tracks(self):
        tracks = []
        t = self.xmldoc.getElementsByTagName("track")
        for track in t:
            tracks.append(track.attributes["producer"].value) 
        return tuple(tracks)
    
    def get_playlists(self):
        playlist_list = []
        playlists = self.xmldoc.getElementsByTagName("playlist")
        eid = 0
        for p in playlists:
            event_list = []
            pl_dict = {}
            pl_dict["pid"] = p.attributes["id"].value
 
            event_nodes = p.childNodes
            events = []
            for i in range(0, event_nodes.length):
                # Get edit event
                event = event_nodes.item(i)
                
                # Create event dict and give it id
                ev_dict = {}
                ev_dict["eid"] = eid
                eid = eid + 1
                
                # Set event data
                if event.localName == "entry":# or  event.localName == "blank":
                    ev_dict["type"] = event.localName
                    ev_dict["producer"] = event.attributes["producer"].value
                    ev_dict["inTime"] = event.attributes["in"].value
                    ev_dict["outTime"] = event.attributes["out"].value
                    event_list.append(ev_dict)
                elif  event.localName == "blank":
                    ev_dict["type"] = event.localName
                    ev_dict["length"] = event.attributes["length"].value
                    event_list.append(ev_dict)

            pl_dict["events"] = event_list
            playlist_list.append(pl_dict)
        return tuple(playlist_list)

    def get_events_dict(self, playlists, source_links):
        events_dict = {}
        for play_list in playlists:
            for event in play_list["events"]:
                # Replace pattern producer events with blanks
                try:
                    producer = event["producer"]
                    resource = source_links[producer]
                    if resource == "<producer>" or resource[0:1] == "#": # This is what MLT puts as resource for pattern producers or color clips
                        event["type"] = "blank"
                        event["length"] =  int(event["outTime"]) - int(event["inTime"]) + 1
                except:
                    pass

                # Add events to event dict
                eid = event["eid"]
                events_dict[eid] = event
        return events_dict

    def get_producers(self):
        producer_list = []
        producers = self.xmldoc.getElementsByTagName("producer")
        for p in producers:
            p_dict = {}
            p_dict["pid"] = p.attributes["id"].value
            p_dict["inTime"] = p.attributes["in"].value
            p_dict["outTime"] = p.attributes["out"].value
            properties = p.getElementsByTagName("property")
            for props in properties:
                p_dict[props.attributes["name"].value.replace(".","_")] = props.firstChild.data 
            producer_list.append(p_dict)

        return tuple(producer_list)
    
    def link_references(self):
        source_links = {}
        for i in self.get_producers():
            src_pid = i["pid"]
            source_links[src_pid] = i["resource"]

        reel_names = {}
        resources = []
        reel_count = 1
        for pid, resource in source_links.iteritems():
            # Only create reel name once for each unique resource
            if resource in resources:
                continue
            else:
                resources.append(resource)

            # Get 8 char uppercase alphanumeric reelname.
            reel_name = self.get_reel_name(resource, reel_count)
            
            # If we happen to get same reel name for two different resources we need to
            # create different reel names for them
            if reel_name in reel_names.values():
                reel_name = reel_name[0:4] + "{0:04d}".format(reel_count)

            reel_names[resource] = reel_name
            reel_count = reel_count + 1

        return (source_links, reel_names)

    def get_reel_name(self, resource, reel_count):
        if self.reel_name_type == REEL_NAME_3_NUMBER:
            return "{0:03d}".format(reel_count)
        elif self.reel_name_type == REEL_NAME_8_NUMBER:
            return "{0:08d}".format(reel_count)
        else:
            file_name = resource.split("/")[-1]
            file_name_no_ext = file_name.split(".")[0]
            file_name_no_ext = re.sub('[^0-9a-zA-Z]+', 'X', file_name_no_ext)
            file_name_len = len(file_name_no_ext)
            if file_name_len >= 8:
                reel_name = file_name_no_ext[0:8]
            else:
                reel_name = file_name_no_ext  + "XXXXXXXX"[0:8 - file_name_len]

            return reel_name.upper()
    
    def create_edl(self, track_index, cascade, audio_op, audio_track_index):
        str_list = []
        
        title = self.title.split("/")[-1] 
        title = title.split(".")[0].upper()
        str_list.append("TITLE:   " + title + "\n")
        
        source_links, reel_names = self.link_references()
        playlists = self.get_playlists()
        event_dict = self.get_events_dict(playlists, source_links)

        edl_event_count = 1 # incr. event index
        
        # Write video events
        if not cascade:
            playlist = playlists[track_index]
            track_frames = self.get_track_frame_array(playlist)
        else:
            track_frames = self.cascade_playlists(playlists, event_dict)

        if audio_op == AUDIO_FROM_VIDEO:
            src_channel = "AA/V"
        else:
            src_channel = "V"

        if len(track_frames) != 0:
            edl_event_count = self.write_track_events(str_list, 
                                            track_frames, src_channel, 
                                            source_links, 
                                            reel_names, event_dict, 
                                            edl_event_count)
        
        # Write audio events
        if audio_op == AUDIO_FROM_AUDIO_TRACK:
            src_channel = "AA"
            playlist = playlists[audio_track_index]
            track_frames = self.get_track_frame_array(playlist)
            self.write_track_events(str_list, track_frames, src_channel, 
                                    source_links, reel_names, event_dict, 
                                    edl_event_count)
            
        print ''.join(str_list).strip("\n")
        return ''.join(str_list).strip("\n")

    def write_track_events(self, str_list, track_frames, src_channel, 
                            source_links, reel_names, event_dict, 
                            edl_event_count):
        prog_in = 0
        prog_out = 0
        running = True
        while running:
            current_clip = track_frames[prog_in]
            event = event_dict[current_clip]
            prog_out = self.get_last_clip_frame(track_frames, prog_in)
            if prog_out == CLIP_OUT_IS_LAST_FRAME:
                running = False
                prog_out = len(track_frames)
                
            if event["type"] == "entry":
                # Get media producer atrrs
                producer = event["producer"]
                resource = source_links[producer]
                reel_name = reel_names[resource]
                src_in = int(event["inTime"]) # source clip IN time
                src_out = int(event["outTime"]) # source clip OUT time
                src_out = src_out + 1 # EDL out is exclusive, MLT out is inclusive
        
                if self.blender_fix:
                    src_in = src_in + 1
                    src_out =  src_in + 1

                self.write_producer_edl_event_CMX3600(str_list, resource, 
                                                     edl_event_count, reel_name, src_channel,
                                                     src_in, src_out, prog_in, prog_out)
                prog_in = prog_out
            elif event["type"] == "blank":
                reel_name = "BL"
                src_in = 0
                src_out = int(event["length"])
                prog_out = prog_in + int(event["length"])
                resource = None

                self.write_producer_edl_event_CMX3600(str_list, resource, 
                                                     edl_event_count, reel_name, src_channel,
                                                     src_in, src_out, prog_in, prog_out)
                prog_in = prog_out
            else:
                print "event type error at create_edl"
                break
                    
            edl_event_count = edl_event_count + 1
        
        return edl_event_count
                
    def get_last_clip_frame(self, frames, first):
        val = frames[first]
        last = first + 1
        try:
            while frames[last] == val:
                last = last + 1
            return last
        except:
            return CLIP_OUT_IS_LAST_FRAME

    def write_producer_edl_event_CMX3600(self, str_list, resource, edl_event, reel_name, 
                                src_channel, src_in, src_out, prog_in, prog_out):
            src_transition = "C"
            if self.from_clip_comment  == True and resource != None:
                str_list.append("* FROM CLIP NAME: " + resource.split("/")[-1] + "\n")
            
            str_list.append("{0:03d}".format(edl_event))
            str_list.append("  ")
            str_list.append(reel_name)
            str_list.append("  ")
            str_list.append(src_channel)            
            str_list.append("  ")
            str_list.append(src_transition)
            str_list.append("  ")
            str_list.append("  ")
            str_list.append(self.frames_to_tc(src_in))
            str_list.append(" ")
            str_list.append(self.frames_to_tc(src_out))
            str_list.append(" ")
            str_list.append(self.frames_to_tc(prog_in))
            str_list.append(" ")
            str_list.append(self.frames_to_tc(prog_out))
            str_list.append("\n")

    def cascade_playlists(self, playlists, event_dict):
        tracks_count = len(current_sequence().tracks) - current_sequence().first_video_index - 1

        # Handle 1 and 2 video tracks cases
        if tracks_count == 1:
            return self.get_track_frame_array(playlists[len(current_sequence().tracks) - 2])
        if tracks_count == 2:
            top_track_frames = self.get_track_frame_array(playlists[len(current_sequence().tracks) - 2])
            bottom_track_frames =  self.get_track_frame_array(playlists[len(current_sequence().tracks) - 3])
            return self.combine_two_tracks(top_track_frames, bottom_track_frames, event_dict)

        top_track_frames = self.get_track_frame_array(playlists[len(current_sequence().tracks) - 2])
        for i in range(len(current_sequence().tracks) - 3, current_sequence().first_video_index - 1, -1):
            bottom_track_frames = self.get_track_frame_array(playlists[i])
            top_track_frames = self.combine_two_tracks(top_track_frames, bottom_track_frames, event_dict)

        return top_track_frames

    def combine_two_tracks(self, t_frames, b_frames, event_dict):
        if len(t_frames) == 0 and len(b_frames) == 0:
            return []
            
        if len(t_frames) == 0:
            return b_frames

        if len(b_frames) == 0:
            return t_frames

        combined_frames = []
        
        if len(b_frames) > len(t_frames):
            length = len(b_frames)
            t_frames = self.ljust(t_frames, len(b_frames), None)
        elif len(b_frames) < len(t_frames):
            length = len(t_frames)
            b_frames = self.ljust(b_frames, len(t_frames), None)
        else:
            length = len(t_frames)

        for i in range(0, length):
            frame = t_frames[i]
            if frame != None:
                t_event = event_dict[frame]
            else:
                t_event = None

            frame = b_frames[i]
            if frame != None:
                b_event = event_dict[frame]
            else:
                b_event = None

            if t_event != None and t_event["type"] !=  "blank":
                combined_frames.append(t_frames[i])
            elif b_event != None:
                combined_frames.append(b_frames[i])
            else:
                combined_frames.append(None)

        return combined_frames

    def get_track_frame_array(self, track):
        frames = []
        for event in track["events"]:
            if event["type"] == "entry":
                count = int(event["outTime"]) - int(event["inTime"]) + 1
                self.append_frames(frames, count, event["eid"])
            elif event["type"] == "blank":
                count = int(event["length"])
                self.append_frames(frames, count, event["eid"])

        return frames

    def append_frames(self, frames, count, value):
        for i in range(0, count):
            frames.append(value)

    def ljust(self, lst, n, fillvalue=''):
        return lst + [fillvalue] * (n - len(lst))

    def frames_to_tc(self, frame):
        if self.use_drop_frames == True:
            return self.frames_to_DF(frame)
        else:
            return utils.get_tc_string(frame)

    def frames_to_DF(self, framenumber):
        """
            This method adapted from C++ code called "timecode" by Jason Wood.
            begin: Wed Dec 17 2003
            copyright: (C) 2003 by Jason Wood
            email: jasonwood@blueyonder.co.uk 
            Framerate should be 29.97, 59.94, or 23.976, otherwise the calculations will be off.
        """
        projectMeta = self.get_project_profile()
        framerate = float(projectMeta["frame_rate_num"]) / float(projectMeta["frame_rate_den"])
        
        # Number of frames to drop on the minute marks is the nearest integer to 6% of the framerate
        dropFrames = round(framerate * 0.066666) 
        # Number of frames in an hour
        framesPerHour = round(framerate * 60 * 60) 
        # Number of frames in a day - timecode rolls over after 24 hours
        framesPerDay = framesPerHour * 24 
        # Number of frames per ten minutes
        framesPer10Minutes = round(framerate * 60 * 10) 
        # Number of frames per minute is the round of the framerate * 60 minus the number of dropped frames
        framesPerMinute = (round(framerate) * 60) - dropFrames 
        
        if (framenumber < 0): # For negative time, add 24 hours.
            framenumber = framesPerDay + framenumber

        # If framenumber is greater than 24 hrs, next operation will rollover clock
        # % is the modulus operator, which returns a remainder. a % b = the remainder of a/b

        framenumber = framenumber % framesPerDay 
        d = floor(framenumber / framesPer10Minutes)
        m = framenumber % framesPer10Minutes

        if (m > 1):
            framenumber=framenumber + (dropFrames * 9 * d) + dropFrames * floor((m-dropFrames) / framesPerMinute)
        else:
            framenumber = framenumber + dropFrames * 9 * d;

        frRound = round(framerate);
        frames = framenumber % frRound;
        seconds = floor(framenumber / frRound) % 60;
        minutes = floor(floor(framenumber / frRound) / 60) % 60;
        hours = floor(floor(floor(framenumber / frRound) / 60) / 60);    

        tc = "%d:%02d:%02d;%02d" % (hours, minutes, seconds, frames)
        return tc
        

####---------------Screenshot--------------####
def screenshot_export():
    length = current_sequence().tractor.get_length()
    if length < 2:
        dialogutils.info_message("Sequence is too short", "Sequence needs to be at least 2 frames long to allow frame export.", None)
        return
    
    frame = PLAYER().current_frame()

    # Can't get last frame to render easily, so just force range.
    if frame > length - 2:
        frame = length - 2

    render_screen_shot(frame, get_displayed_image_render_path(), "png")
    export_screenshot_dialog(_export_screenshot_dialog_callback, frame,
                             gui.editor_window.window, PROJECT().name)
    PLAYER().seek_frame(frame)

def _export_screenshot_dialog_callback(dialog, response_id, data):
    file_name, out_folder, file_type_combo, frame = data
    if response_id == gtk.RESPONSE_YES:
        vcodec = _img_types[file_type_combo.get_active()]
        ext = _img_extensions[file_type_combo.get_active()]
        render_path = utils.get_hidden_screenshot_dir_path() + "screenshot_%01d." + ext
        rendered_file_path = utils.get_hidden_screenshot_dir_path() + "screenshot_1." + ext 
        out_file_path = out_folder.get_filename()+ "/" + file_name.get_text() + "." + ext
        dialog.destroy()

        render_screen_shot(frame, render_path, vcodec)
        shutil.copyfile(rendered_file_path, out_file_path)
    else:
        dialog.destroy()
    
    purge_screenshots()
    PLAYER().seek_frame(frame)

def get_displayed_image_render_path():
    return utils.get_hidden_screenshot_dir_path() + "screenshot_%01d.png"

def get_displayed_image_path():
    return utils.get_hidden_screenshot_dir_path() + "screenshot_1.png"

def _screenshot_frame_changed(adjustment):
    _update_displayed_image(int(adjustment.get_value()))

def render_screen_shot(frame, render_path, vcodec):
    producer = current_sequence().tractor   
    
    consumer = mlt.Consumer(PROJECT().profile, "avformat", str(render_path))
    consumer.set("real_time", -1)
    consumer.set("rescale", "bicubic")
    consumer.set("vcodec", str(vcodec))
    
    renderer = renderconsumer.FileRenderPlayer(None, producer, consumer, frame, frame + 1)
    renderer.wait_for_producer_end_stop = False
    renderer.consumer_pos_stop_add = 2 # Hack, see FileRenderPlayer
    renderer.start()

    while renderer.has_started_running == False:
        time.sleep(0.05)

    while renderer.stopped == False:
        time.sleep(0.05)

def export_screenshot_dialog(callback, frame, parent_window, project_name):
    cancel_str = _("Cancel").encode('utf-8')
    ok_str = _("Export Image").encode('utf-8')
    dialog = gtk.Dialog(_("Export Frame Image"),
                        parent_window,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (cancel_str, gtk.RESPONSE_CANCEL,
                        ok_str, gtk.RESPONSE_YES))

    global _screenshot_img
    _screenshot_img = guiutils.get_gtk_image_from_file(get_displayed_image_path(), 300)

    frame_frame = guiutils.get_named_frame_with_vbox(None, [_screenshot_img])
    
    INPUT_LABELS_WITDH = 320
    project_name = project_name.strip(".flb")

    file_name = gtk.Entry()
    file_name.set_text(project_name)

    extension_label = gtk.Label(".png")
    extension_label.set_size_request(35, 20)

    name_pack = gtk.HBox(False, 4)
    name_pack.pack_start(file_name, True, True, 0)
    name_pack.pack_start(extension_label, False, False, 0)

    name_row = guiutils.get_two_column_box(gtk.Label(_("Export file name:")), name_pack, INPUT_LABELS_WITDH)
 
    out_folder = gtk.FileChooserButton(_("Select target folder"))
    out_folder.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    out_folder.set_current_folder(os.path.expanduser("~") + "/")
    
    folder_row = guiutils.get_two_column_box(gtk.Label(_("Export folder:")), out_folder, INPUT_LABELS_WITDH)

    file_type_combo = gtk.combo_box_new_text()
    for img in _img_types:
        file_type_combo.append_text(img)
    file_type_combo.set_active(0)
    file_type_combo.connect("changed", _file_type_changed, extension_label)
    file_type_row = guiutils.get_two_column_box(gtk.Label(_("Image type:")), file_type_combo, INPUT_LABELS_WITDH)
    
    file_frame = guiutils.get_named_frame_with_vbox(None, [file_type_row, name_row, folder_row])
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(frame_frame, False, False, 0)
    vbox.pack_start(guiutils.pad_label(12, 12), False, False, 0)
    vbox.pack_start(file_frame, False, False, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.default_behaviour(dialog)
    dialog.connect('response', callback, (file_name, out_folder, file_type_combo, frame)) #(file_name, out_folder, track_select_combo, cascade_check, op_combo, audio_track_select_combo))
    dialog.show_all()

def _file_type_changed(combo, label):
    label.set_text("." + _img_extensions[combo.get_active()])

def purge_screenshots():
    d = utils.get_hidden_screenshot_dir_path()
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
