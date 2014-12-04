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

import dialogs
from editorstate import PLAYER
from editorstate import PROJECT
import renderconsumer
import utils

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
    dialogs.export_edl_dialog(_export_edl_dialog_callback, PROJECT().name)
    

def _export_edl_dialog_callback(dialog, response_id):
    print "adasdad"
    if response_id == gtk.RESPONSE_ACCEPT:
        filenames = dialog.get_filenames()
        edl_path = filenames[0]
        global _xml_render_monitor
        _xml_render_player = renderconsumer.XMLRenderPlayer(get_edl_temp_xml_path(),
                                                            _edl_xml_render_done,
                                                            edl_path)
        _xml_render_player.start()
        dialog.destroy()
    else:
        dialog.destroy()

def _edl_xml_render_done(edl_path):
    print "wwwww"
    global _xml_render_player
    _xml_render_player = None
    mlt_parse = MLTXMLParse(get_edl_temp_xml_path())
    mlt_parse.create_edl()

def get_edl_temp_xml_path():
    return utils.get_hidden_user_dir_path() + "edl_temp_xml.xml"


class MLTXMLParse:
        
    def __init__(self, kdenliveFile):
        self.xmldoc = minidom.parse(kdenliveFile)
    
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
        for p in playlists:
            event_list = []
            pl_dict = {}
            pl_dict["pid"] = p.attributes["id"].value
            events = p.getElementsByTagName("entry")
            for event in events:
                ev_dict = {}
                ev_dict["producer"] = event.attributes["producer"].value
                ev_dict["inTime"] = event.attributes["in"].value
                ev_dict["outTime"] = event.attributes["out"].value
                event_list.append(ev_dict)
            pl_dict["events"] = event_list
            playlist_list.append(pl_dict)
        return tuple(playlist_list)

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
        return source_links

    def create_edl(self):
        source_links = self.link_references()
        for playlist in self.get_playlists():
            edl_event = 1
            prog_in = 0 # showtime tally
            prog_out = 0

            print "\n === " + playlist["pid"] + " === \n"
            for event in playlist["events"]:
                # Get source file
                producer = event["producer"]
                source_path = source_links[producer]
                source_file = source_path.split("/")[-1]

                # Get Source in and out
                src_in = int(event["inTime"]) # source clip IN time
                src_out = int(event["outTime"]) # source clip OUT time
                # Fix for first event
                if edl_event != 1:
                    src_out = src_out + 1 
                
                # Source duration and proram out
                src_dur = src_out - src_in 
                prog_out = prog_out + src_dur # increment program tally

                # Write out edl event
                self.write_edl_event(edl_event, producer, source_file, 
                                     src_in, src_out, prog_in, prog_out)

                # Fix for first event
                if edl_event == 1:
                    prog_in = prog_in + 1
                
                # Increment program in and event count     
                prog_in = prog_in + src_dur
                edl_event = edl_event + 1


    def write_edl_event(self, edl_event, producer, source_file, src_in, src_out, prog_in, prog_out):
        
            src_transition = "C"
            src_channel = "V"
            prod = "P"
            print "* FROM CLIP NAME: " + source_file
            print "{0:03d}".format(edl_event) + "  " + producer + "  ",
            print src_channel  + "  " + src_transition + "  ", 
            
            show_frames = False
            if show_frames == True:
                print str(src_in) + " " + str(src_out) + "",
                print str(prog_in) + " " + str(prog_out)
            else:
                print self.framesToDF(src_in) + " " + self.framesToDF(src_out) + "",
                print self.framesToDF(prog_in) + " " + self.framesToDF(prog_out)
                    
    def framesToDF(self, framenumber):
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



