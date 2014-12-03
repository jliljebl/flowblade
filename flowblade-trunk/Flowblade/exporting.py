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
    
# ----------------------- mlt player render callbacks, we need to set these no-op when not doing standard rendering
# ----------------------- we're using different progress update mechanisms here
def set_render_progress_gui(fraction):
    pass
    
def save_render_start_time():
    pass

def exit_render_gui():
    pass

def maybe_open_rendered_file_in_bin():
    pass


####---------------EDL--------------####
def EDL_export():
    dialogs.export_edl_dialog(_export_edl_dialog_callback, PROJECT().name)
    

def _export_edl_dialog_callback(dialog, response_id):
    print "adasdad"
    if response_id == gtk.RESPONSE_ACCEPT:
        filenames = dialog.get_filenames()
        save_path = filenames[0]
        path = "/home/janne/temppu4.xml"
        global _xml_render_monitor
        _xml_render_player = renderconsumer.XMLRenderPlayer(path,
                                                          _edl_xml_render_done,
                                                          None)
        _xml_render_player.start()
        dialog.destroy()
    else:
        dialog.destroy()

def _render_temp_xml(save_path):

    path = "/home/janne/temppu.xml"
    global _xml_render_monitor
    _xml_render_monitor = renderconsumer.XMLRenderMonitor(path,
                                                          _edl_xml_render_done,
                                                          None)
    _xml_render_monitor.start()
            

def _edl_xml_render_done(data):
    global _xml_render_player
    _xml_render_player = None
    
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
            event_lList = []
            pl_dict = {}
            pl_dict["pid"] = p.attributes["id"].value
            events = p.getElementsByTagName("entry")
            for event in events:
                ev_dict = {}
                ev_dict["producer"] = event.attributes["producer"].value
                ev_dict["inTime"] = event.attributes["in"].value
                ev_dict["outTime"] = event.attributes["out"].value
                event_dist.append(ev_dict)
            pl_dict["events"] = eventList
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
                
            producer_list.append(pDict)
        return tuple(producerList)
    
    def link_references(self):
        source_links = {}
        for i in self.get_producers():
            src_pid = i["pid"]
            source_links[srcPid] = i["resource"]
        return source_links

    def createEdl(self):
        sourceLinks = self.linkReferences()
        for playlist in self.getPlaylists():
            EdlEventCnt = 1
            progIn = 0 # showtime tally
            progOut = 0
            srcChannel = "C" # default channel/track assignment 
            print "\n === " + playlist["pid"] + " === \n"
            for event in playlist["events"]:
                prod = event["producer"]
                prodChunks = prod.split("_")
                srcType = prodChunks[-1].capitalize()[:1] 
                
                # if it's an audio event, extract channel info from producer id
                if srcType == "A":
                    srcChannel = prodChunks[1]

                srcIn = int(event["inTime"]) # source clip IN time
                srcOut = int(event["outTime"]) # source clip OUT time
                if EdlEventCnt != 1:
                    srcOut = srcOut + 1
                srcDur = srcOut - srcIn 
                progOut = progOut + srcDur # increment program tally
                
                sourcePath = sourceLinks[prod]
                sourceFile = sourcePath.split("/")[-1]
        
                # deref proxy


                print "* FROM CLIP NAME: " + sourceRef
                print str(EdlEventCnt) + "  " + prod + "  ",
                print srcType + "  " + srcChannel + "  ", 
                
                if args.show_frames:
                    print str(srcIn) + " " + str(srcOut) + "",
                    print str(progIn) + " " + str(progOut)
                else:
                    print self.framesToDF(srcIn) + " " + self.framesToDF(srcOut) + "",
                    print self.framesToDF(progIn) + " " + self.framesToDF(progOut)
        
                if EdlEventCnt == 1:
                    progIn = progIn + 1
                    
                progIn = progIn + srcDur
                EdlEventCnt = EdlEventCnt + 1

    def framesToDF(self, framenumber):
        """
            This method adapted from C++ code called "timecode" by Jason Wood.
            begin: Wed Dec 17 2003
            copyright: (C) 2003 by Jason Wood
            email: jasonwood@blueyonder.co.uk 
            Framerate should be 29.97, 59.94, or 23.976, otherwise the calculations will be off.
        """

        projectMeta = self.getProjectProfile()
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

