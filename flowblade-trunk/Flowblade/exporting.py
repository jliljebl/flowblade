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

import dialogs
from editorstate import PLAYER
from editorstate import PROJECT
from editorstate import current_sequence
import gui
import renderconsumer
import utils

EDL_TYPE_AVID_CMX3600 = 0

REEL_NAME_3_NUMBER = 0
REEL_NAME_8_NUMBER = 1
REEL_NAME_FILE_NAME_START = 2

CLIP_OUT_IS_LAST_FRAME = -999

_xml_render_player = None



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
        file_name, out_folder, track_select_combo = data
        edl_path = out_folder.get_filename()+ "/" + file_name.get_text() + ".edl" 
        global _xml_render_monitor
        _xml_render_player = renderconsumer.XMLRenderPlayer(get_edl_temp_xml_path(),
                                                            _edl_xml_render_done,
                                                            (edl_path, track_select_combo))
        _xml_render_player.start()

        dialog.destroy()
    else:
        dialog.destroy()

def _edl_xml_render_done(data):
    edl_path, track_select_combo = data
    global _xml_render_player
    _xml_render_player = None
    mlt_parse = MLTXMLToEDLParse(get_edl_temp_xml_path(), edl_path)
    edl_contents = mlt_parse.create_edl(track_select_combo.get_active() + 1, False)
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
        self.from_clip_comment = True
    
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
        print "get_playlists"
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
                    print  ev_dict["type"] 
                    event_list.append(ev_dict)
                elif  event.localName == "blank":
                    ev_dict["type"] = event.localName
                    ev_dict["length"] = event.attributes["length"].value
                    event_list.append(ev_dict)
                    print  ev_dict["type"] 

            pl_dict["events"] = event_list
            playlist_list.append(pl_dict)
        return tuple(playlist_list)

    def get_event_dict(self, playlists):
        event_dict = {}
        for play_list in playlists:
            for event in play_list["events"]:
                print type(event)
                eid = event["eid"]
                event_dict[eid] = event
        return event_dict

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
    
    def create_edl(self, track_index, cascade):
        str_list = []
        
        title = self.title.split("/")[-1] 
        title = title.split(".")[0].upper()
        str_list.append("TITLE:   " + title + "\n")
        
        source_links, reel_names = self.link_references()
        playlists = self.get_playlists()
        event_dict = self.get_event_dict(playlists)

        if not cascade:
            playlist = playlists[track_index]
            track_frames = self.get_track_frame_array(playlist)
        else:
            track_frames = self.cascade_playlists(playlists)

        src_channel = "AA/V" #"AA"

        edl_event_count = 1 # incr. event index
        prog_in = 0 # showtime tally
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
                
                self.write_producer_edl_event_CMX3600(str_list, resource, 
                                                     edl_event_count, reel_name, src_channel,
                                     src_in, src_out, prog_in, prog_out)
    
                prog_in = prog_out
            elif event["type"] == "blank":
                print "blank not impl"
                prog_out = prog_in + int(event["length"])
                prog_in = prog_out
            else:
                print "event type error at create_edl"
                break
                    
            edl_event_count = edl_event_count + 1 

        #print ''.join(str_list).strip("\n")
        return ''.join(str_list).strip("\n")

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
            if self.from_clip_comment  == True:
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
            str_list.append(utils.get_tc_string(src_in))
            str_list.append(" ")
            str_list.append(utils.get_tc_string(src_out))
            str_list.append(" ")
            str_list.append(utils.get_tc_string(prog_in))
            str_list.append(" ")
            str_list.append(utils.get_tc_string(prog_out))
            str_list.append("\n")

    def cascade_playlists(self, playlists):
        """
        if len(playlists) == 1:
            return playlists[0]
        if len(playlists) == 2:
            return self.combine_two_tracks(playlists[0], playlists[1])
        """
            
        for i in range(len(current_sequence().tracks) - 3, current_sequence().first_video_index - 1, -1):
            print i, i + 1 

    def combine_two_tracks(self, top_track, bottom_track):
        if len(top_track) == 0 and len(bottom_track) == 0:
            return []
            
        if len(top_track) == 0:
            return self.get_track_frame_array(bottom_track)

        if len(bottom_track) == 0:
            return self.get_track_frame_array(top_track)

        top_frames = self.get_track_frame_array(top_track)
        bottom_frames = self.get_track_frame_array(bottom_track)
        combined_frames = []
        
        length = len(top_frames)
        if len(bottom_frames) > len(top_frames):
            length = len(bottom_frames)
            self.ljust(top_frames, len(bottom_frames), None)
        elif len(bottom_frames) < len(top_frames):
            length = len(top_frames)
            self.ljust(bottom_frames, len(top_frames), None)
        else:
            length = len(top_frames)
            
        for i in range(0, length):
            if top_frames[i] != None:
                combined_frames.append(top_frames[i])
            elif bottom_frames[i] != None:
                combined_frames.append(bottom_frames[i])
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
        return lst + [fillvalue] * (n - len(self))
        

