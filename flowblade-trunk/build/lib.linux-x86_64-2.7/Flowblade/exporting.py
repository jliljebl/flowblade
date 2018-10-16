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



from gi.repository import Gtk
import os
from xml.dom import minidom
from math import floor
import mlt
import time
import md5
import re
import shutil

import appconsts
import dialogs
import dialogutils
from editorstate import PLAYER
from editorstate import PROJECT
from editorstate import current_sequence
import gui
import guiutils
import renderconsumer
import utils

REEL_NAME_HASH_8_NUMBER = 1
REEL_NAME_FILE_NAME_START = 2

_xml_render_player = None

_screenshot_img = None
_img_types = ["png", "bmp", "targa","tiff"]
_img_extensions = ["png", "bmp", "tga","tif"]

####---------------MLT--------------####    
def MELT_XML_export():
    dialogs.export_xml_dialog(_export_melt_xml_dialog_callback, PROJECT().name)

def _export_melt_xml_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        filenames = dialog.get_filenames()
        save_path = filenames[0]
        #global _xml_render_monitor
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

def _export_edl_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        filenames = dialog.get_filenames()
        edl_path = filenames[0]
        
        _xml_render_player = renderconsumer.XMLRenderPlayer(get_edl_temp_xml_path(),
                                                            _edl_xml_render_done,
                                                            edl_path)
        _xml_render_player.start()

        dialog.destroy()
    else:
        dialog.destroy()

def _edl_xml_render_done(data):
    edl_path  = data
    mlt_parse = MLTXMLToEDLParse(get_edl_temp_xml_path(), current_sequence())
    edl_contents = mlt_parse.create_edl()
    f = open(edl_path, 'w')
    f.write(edl_contents)
    f.close()


def get_edl_temp_xml_path():
    return utils.get_hidden_user_dir_path() + "edl_temp_xml.xml"


class MLTXMLToEDLParse:
    def __init__(self, xmlfile, current_sequence):
        self.xmldoc = minidom.parse(xmlfile)
        self.current_sequence = current_sequence

        self.producers = {} # producer id -> producer_data
        self.resource_to_reel_name = {}
        self.reel_name_to_resource = {}
        
        self.reel_name_type = REEL_NAME_FILE_NAME_START
        self.from_clip_comment = True
        self.use_drop_frames = False

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
            
            track_id_attr_value = p.attributes["id"].value

            # Don't empty, black or hidden tracks
            if track_id_attr_value == "playlist0":
                continue
            
            if len(p.getElementsByTagName("entry")) < 1:
                continue
                
            # plist contains id and events list data
            plist = {}
            plist["pl_id"] = track_id_attr_value
 
            # Set track type info
            track_index = int(track_id_attr_value.lstrip("playlist"))
            track_object =  self.current_sequence.tracks[track_index]
            plist["src_channel"] =  "AA/V" 
            if track_object.type == appconsts.AUDIO:
                plist["src_channel"] = "AA"
                        
            # Create events list
            event_list = []
            event_nodes = p.childNodes
            events = []
            for i in range(0, event_nodes.length):
                # Get edit event
                event_node = event_nodes.item(i)
                
                # Create event  and give it id
                event = {}
                event["eid"] = eid
                eid = eid + 1
                
                # Set event data
                if event_node.localName == "entry":# or  event.localName == "blank":
                    event["type"] = event_node.localName
                    event["producer"] = event_node.attributes["producer"].value
                    event["inTime"] = event_node.attributes["in"].value
                    event["outTime"] = event_node.attributes["out"].value
                    event_list.append(event)
                elif event_node.localName == "blank":
                    event["type"] = event_node.localName
                    event["length"] = event_node.attributes["length"].value
                    event_list.append(event)

            plist["events_list"] = event_list
            
            # Add to playlists list
            playlist_list.append(plist)
            
        return tuple(playlist_list)

    def create_producers_dict(self):
        producer_nodes = self.xmldoc.getElementsByTagName("producer")
        for p in producer_nodes:
            producer_data = {}
            producer_data["id"] = p.attributes["id"].value
            producer_data["inTime"] = p.attributes["in"].value
            producer_data["outTime"] = p.attributes["out"].value
            properties = p.getElementsByTagName("property")
            for props in properties:
                producer_data[props.attributes["name"].value.replace(".","_")] = props.firstChild.data
                
            self.producers[producer_data["id"]] = producer_data
    
    def link_resources(self):
        for producer_id, producer_data in self.producers.iteritems():

            producer_resource = producer_data["resource"]
            reel_name = self.get_reel_name(producer_resource)

            # If two reel names are same but point to different resources,
            # use md5 hash as reel name for the new resource.
            # This happens when two resources have same 8 first letters in file name.
            if reel_name in self.reel_name_to_resource:
                existing_resource = self.reel_name_to_resource[reel_name]

                if existing_resource != producer_resource:
                    reel_name = md5.new(producer_resource).hexdigest()[:8]
                    

            self.resource_to_reel_name[producer_resource] = reel_name
            self.reel_name_to_resource[reel_name] = producer_resource

    def get_reel_name(self, resource):
        if self.reel_name_type == REEL_NAME_HASH_8_NUMBER:
            return "{0:08d}".format(md5.new(resource).hexdigest())
        else:
            file_name = resource.split("/")[-1]
            file_name_no_ext = file_name.split(".")[0]
            file_name_no_ext = re.sub('[^0-9a-zA-Z]+', 'X', file_name_no_ext)
            file_name_len = len(file_name_no_ext)
            if file_name_len >= 8:
                reel_name = file_name_no_ext[0:8]
            else:
                reel_name = file_name_no_ext  + "XXXXXXXX"[0:8 - file_name_len]

            return reel_name

    def get_producer_media_data(self, producer_id):
        producer_data = self.producers[producer_id]
        producer_resource = producer_data["resource"]
        reel_name = self.resource_to_reel_name[producer_resource]
        
        return reel_name, producer_resource

    def create_edl(self):

        self.create_producers_dict()
        self.link_resources()

        playlists = self.get_playlists()

        edl_event_count = 1 # incr. event index

        str_list = []
        for plist in playlists:
            prog_in = 0
            prog_out = 0
            
            str_list.append("\n === " + plist["pl_id"] + " === \n\n")
            
            event_list = plist["events_list"]
            
            src_channel = plist["src_channel"] 
                    
            for event in event_list:
                
                if event["type"] == "entry":
                    src_in = int(event["inTime"])
                    src_out = int(event["outTime"])
                    src_len = src_out - src_in + 1
                     
                    prog_out = prog_in + src_len
                    
                    producer_id = event["producer"]
                    reel_name, resource = self.get_producer_media_data(producer_id)
                elif event["type"] == "blank":

                    src_in = 0
                    src_out = int(event["length"])
                    src_len = int(event["length"])
                    prog_out = prog_in + int(event["length"])

                    reel_name = "BL      "
                    resource = None

                src_transition = "C"
                
                str_list.append("{0:03d}".format(edl_event_count))
                str_list.append("  ")
                str_list.append(reel_name)
                str_list.append(" ")
                str_list.append(src_channel)            
                str_list.append("  ")
                str_list.append(src_transition)
                str_list.append("        ")
                str_list.append(self.frames_to_tc(src_in))
                str_list.append(" ")
                str_list.append(self.frames_to_tc(src_out + 1))
                str_list.append(" ")
                str_list.append(self.frames_to_tc(prog_in))
                str_list.append(" ")
                str_list.append(self.frames_to_tc(prog_out))
                str_list.append("\n")

                if self.from_clip_comment == True and resource != None:
                    str_list.append("* FROM CLIP NAME: " + resource.split("/")[-1] + "\n")
                    
                edl_event_count += 1;
   
                prog_in += src_len

                
        #print ''.join(str_list).strip("\n")
        return ''.join(str_list).strip("\n")

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
        dialogutils.info_message(_("Sequence is too short"), _("Sequence needs to be at least 2 frames long to allow frame export."), None)
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
    if response_id == Gtk.ResponseType.YES:
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
    dialog = Gtk.Dialog(_("Export Frame Image"),
                        parent_window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (cancel_str, Gtk.ResponseType.CANCEL,
                        ok_str, Gtk.ResponseType.YES))

    global _screenshot_img
    _screenshot_img = guiutils.get_gtk_image_from_file(get_displayed_image_path(), 300)

    frame_frame = guiutils.get_named_frame_with_vbox(None, [_screenshot_img])
    
    INPUT_LABELS_WITDH = 320
    project_name = project_name.strip(".flb")

    file_name = Gtk.Entry()
    file_name.set_text(project_name)

    extension_label = Gtk.Label(label=".png")
    extension_label.set_size_request(35, 20)

    name_pack = Gtk.HBox(False, 4)
    name_pack.pack_start(file_name, True, True, 0)
    name_pack.pack_start(extension_label, False, False, 0)

    name_row = guiutils.get_two_column_box(Gtk.Label(label=_("Export file name:")), name_pack, INPUT_LABELS_WITDH)
 
    out_folder = Gtk.FileChooserButton(_("Select target folder"))
    out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    out_folder.set_current_folder(os.path.expanduser("~") + "/")
    
    folder_row = guiutils.get_two_column_box(Gtk.Label(label=_("Export folder:")), out_folder, INPUT_LABELS_WITDH)

    file_type_combo = Gtk.ComboBoxText()
    for img in _img_types:
        file_type_combo.append_text(img)
    file_type_combo.set_active(0)
    file_type_combo.connect("changed", _file_type_changed, extension_label)
    file_type_row = guiutils.get_two_column_box(Gtk.Label(label=_("Image type:")), file_type_combo, INPUT_LABELS_WITDH)
    
    file_frame = guiutils.get_named_frame_with_vbox(None, [file_type_row, name_row, folder_row])
    
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(frame_frame, False, False, 0)
    vbox.pack_start(guiutils.pad_label(12, 12), False, False, 0)
    vbox.pack_start(file_frame, False, False, 0)

    alignment = guiutils.set_margins(vbox, 12, 12, 12, 12)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    dialog.connect('response', callback, (file_name, out_folder, file_type_combo, frame)) #(file_name, out_folder, track_select_combo, cascade_check, op_combo, audio_track_select_combo))
    dialog.show_all()

def _file_type_changed(combo, label):
    label.set_text("." + _img_extensions[combo.get_active()])

def purge_screenshots():
    d = utils.get_hidden_screenshot_dir_path()
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
