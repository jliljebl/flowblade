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
Helper functions and data
"""
import pygtk
pygtk.require('2.0');
import gtk

import math
import os
import threading

import appconsts
from editorstate import PROJECT

# ---------------------------------- CLASSES
class EmptyClass:
    pass


class Ticker:
    """
    Calls function repeatedly with given delay between calls.
    """
    def __init__(self, action, delay):
        self.action = action
        self.delay = delay
        self.running = False
        self.exited = False
    
    def start_ticker(self, delay=None):
        self.ev = threading.Event()
        if delay == None: # If no delay specified, use default delay set at creation time
            delay = self.delay
        self.thread = threading.Thread(target=self.runner,  
                                       args=(self.ev, 
                                       delay, 
                                       self.action))
        self.running = True
        self.thread.start()
    
    def stop_ticker(self):
        try:
            self.ev.set()
            self.running = False # ! self.ev.set() may go to Exception leave this having wrong value if already stopped? 
        except Exception:
            pass # called when not running

    def runner(self, event, delay, action):
        while True:
            if not self.running:
                break
            action()
            if not self.running:
                break
            if event.isSet():
                break
            event.wait(delay)
        self.exited = True

# -------------------------------- UTIL FUNCTIONS
def fps():
    return PROJECT().profile.fps()

def clip_length_string(length):
    """ 
    Returns length string for length in frames.
    """
    fr = length % fps()
    sec = length / fps()
    mins = sec / 60
    sec = int(math.floor(sec % 60))
    hours = int(math.floor(mins / 60))
    mins = int(math.floor(mins % 60))
    
    hr_str = ""
    if hours > 0:
        hr_str = str(hours) + "h"
    min_str = ""
    if mins > 0 or hours > 0:
        min_str = str(mins) + "m"
    if sec > 0 or min_str != "":
        s_str = str(sec) + "s"
    else:
        s_str = str(fr) + "fr"
    return hr_str + min_str + s_str

def get_tc_string(frame):
    """ 
    Returns timecode string for frame
    """
    return get_tc_string_with_fps(frame, fps())

def get_tc_string_with_fps(frame, frames_per_sec):
    fr = frame % frames_per_sec
    sec = frame / frames_per_sec
    mins = sec / 60
    sec = sec % 60
    hours = mins / 60
    mins = mins % 60
    return "%02d:%02d:%02d:%02d" % (hours, mins, sec, fr)

def get_time_str_for_sec_float(sec):
    mins = sec / 60
    sec = sec % 60
    hours = mins / 60
    mins = mins % 60
    
    if hours >= 24.0:
        days = hours / 24
        hours = hours % 24
        return str(int(days)) + " days " + str(int(hours)) + "h " + str(int(mins)) + "m " + str(int(sec)) + "s"
    if hours >= 1.0:
        return str(int(hours)) + "h " + str(int(mins)) + "m " + str(int(sec)) + "s"
    if mins >= 1.0:
        return str(int(mins)) + "m " + str(int(sec)) + "s"
    return str(int(sec)) + "s"
        
def get_track_name(track, sequence):
    if track.type == appconsts.VIDEO:
        # Video tracks are numbered to USER as 'V1' ,'V2' with 'V1' being
        # tracks[current_sequence.first_video_index]
        if track.id == sequence.first_video_index:
            text = "V1"
        else:
            text = "V" + str(track.id - sequence.first_video_index + 1)
    else:
        # Audio tracks are numbered in *opposite* direction for USER view
        # so if we have audio tracks in tracks[1] and tracks[2]
        # User thinks tracks[1] is 'A2' and track[2] is 'A1'
        # This is also compensated for in Sequence.get_first_active_track()
        text = "A" + str(sequence.first_video_index - track.id)
    return text

def get_media_source_file_filter():
    # No idea if these actually play or not, except images mime types
    f = gtk.FileFilter()
    f.set_name("Media MIME types")
    f.add_mime_type("image*")
    f.add_mime_type("video*")
    f.add_mime_type("audio*")
    f.add_mime_type("video/x-theora+ogg")
    f.add_mime_type("video/x-sgi-movie")
    f.add_mime_type("video/ogg")
    f.add_mime_type("video/x-ogm")
    f.add_mime_type("video/x-ogm+ogg")
    f.add_mime_type("video/x-ms-asf")
    f.add_mime_type("video/x-ms-wmv")
    f.add_mime_type("video/x-msvideo")
    f.add_mime_type("video/x-matroska")
    f.add_mime_type("video/x-flv")
    f.add_mime_type("video/vnd.rn-realvideo")
    f.add_mime_type("video/quicktime")
    f.add_mime_type("video/ogg")
    f.add_mime_type("video/mpeg")
    f.add_mime_type("video/mp4")
    f.add_mime_type("video/mp2t")
    f.add_mime_type("video/isivideo")
    f.add_mime_type("video/dv")
    f.add_mime_type("video/annodex")
    f.add_mime_type("video/3gpp")
    f.add_mime_type("video/webm")
    
    f.add_mime_type("audio/aac")
    f.add_mime_type("audio/ac3")
    f.add_mime_type("audio/AMR")
    f.add_mime_type("audio/ogg")
    f.add_mime_type("audio/midi")
    f.add_mime_type("audio/mp2")
    f.add_mime_type("audio/mp3")
    f.add_mime_type("audio/mp4")
    f.add_mime_type("audio/mpeg")
    f.add_mime_type("audio/ogg")
    f.add_mime_type("audio/vnd.rn-realaudio")
    f.add_mime_type("audio/vorbis")
    f.add_mime_type("audio/x-adpcm")
    f.add_mime_type("audio/x-aifc")
    f.add_mime_type("audio/x-aiff")
    f.add_mime_type("audio/x-aiffc")
    f.add_mime_type("audio/x-flac")
    f.add_mime_type("audio/x-flac+ogg")
    f.add_mime_type("audio/x-m4b")
    f.add_mime_type("audio/x-matroska")
    f.add_mime_type("audio/x-ms-wma")
    f.add_mime_type("audio/x-oggflac")
    f.add_mime_type("audio/x-ms-asx")
    f.add_mime_type("audio/x-ms-wma")
    f.add_mime_type("audio/x-ms-wma")
    f.add_mime_type("audio/x-gsm")
    f.add_mime_type("audio/x-riff")
    f.add_mime_type("audio/x-speex")
    f.add_mime_type("audio/x-speex+ogg")
    f.add_mime_type("audio/x-tta")
    f.add_mime_type("audio/x-voc")
    f.add_mime_type("audio/x-vorbis+ogg")
    f.add_mime_type("audio/x-wav")
    f.add_mime_type("audio/annodex")

    f.add_mime_type("image/bmp")
    f.add_mime_type("image/tiff")
    f.add_mime_type("image/gif")
    f.add_mime_type("image/x-tga")
    f.add_mime_type("image/png")
    f.add_mime_type("image/jpeg")
    f.add_mime_type("image/svg+xml")

    return f

def get_image_sequence_file_filter():
    f = gtk.FileFilter()
    f.set_name("Image files")
    f.add_mime_type("image/bmp")
    f.add_mime_type("image/tiff")
    f.add_mime_type("image/gif")
    f.add_mime_type("image/x-tga")
    f.add_mime_type("image/png")
    f.add_mime_type("image/jpeg")

    return f

def file_extension_is_graphics_file(ext):
    ext = ext.lstrip(".")
    ext = ext.lower()
    if ext in _graphics_file_extensions:
        return True
    else:
        return False

def get_file_type(file_path):
    name, ext = os.path.splitext(file_path)
    ext = ext.lstrip(".")
    ext = ext.lower()
    if ext in _video_file_extensions:
        return "video"
    
    if ext in _audio_file_extensions:
        return "audio"
    
    if ext in _graphics_file_extensions:
        return "image"
    
    return "unknown"

def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))

def int_to_hex(n):
    return hex(n)[2:]

def gdk_color_str_to_mlt_color_str(gdk_color_str):
    raw_r, raw_g, raw_b = hex_to_rgb(gdk_color_str)
    val_str = "#" + int_to_hex(int((float(raw_r) * 255.0) / 65535.0)) + \
                    int_to_hex(int((float(raw_g) * 255.0) / 65535.0)) + \
                    int_to_hex(int((float(raw_b) * 255.0) / 65535.0))
    return val_str

def gdk_color_str_to_int(gdk_color_str):
    # returned int is 32-bit RGBA, alpha is 00 
    raw_r, raw_g, raw_b = hex_to_rgb(gdk_color_str)
    red = int((float(raw_r) * 255.0) / 65535.0)
    green = int((float(raw_g) * 255.0) / 65535.0)
    blue = int((float(raw_b) * 255.0) / 65535.0)
    
    return (red << 24) + (green << 16) + (blue << 8)

def get_cairo_color_tuple_255_rgb(r, g, b):
    return (float(r)/255.0, float(g)/255.0, float(b)/255.0)

def cairo_color_from_gdk_color(gdk_color):
    raw_r, raw_g, raw_b = hex_to_rgb(gdk_color.to_string())
    return (float(raw_r)/65535.0, float(raw_g)/65535.0, float(raw_b)/65535)
    
def do_nothing():
    pass

def get_hidden_user_dir_path():
    return os.getenv("HOME") + "/.flowblade/"

def get_hidden_screenshot_dir_path():
    return get_hidden_user_dir_path() + "screenshot/"

# File exntension lists
_audio_file_extensions = [  "act",
                            "aif",
                            "aiff",
                            "alfc",
                            "aac",
                            "alac",
                            "amr",
                            "atrac",
                            "awb",
                            "dct",
                            "dss",
                            "dvf",
                            "flac",
                            "gsm",
                            "iklax",
                            "m4a",
                            "m4p",
                            "mmf",
                            "mp2",
                            "mp3",
                            "mpc",
                            "msv",
                            "ogg",
                            "oga",
                            "opus",
                            "pcm",
                            "u16be",
                            "u16le",
                            "u24be",
                            "u24le",
                            "u32be",
                            "u32le",
                            "u8",
                            "ra",
                            "rm",
                            "raw",
                            "tta",
                            "vox",
                            "wav",
                            "wma",
                            "wavpack"]

_graphics_file_extensions = [   "bmp",
                                "tiff",
                                "tif",
                                "gif",
                                "tga",
                                "png",
                                "pgm",
                                "jpeg",
                                "jpg",
                                "svg"]

_video_file_extensions = [  "avi",
                            "dv",
                            "flv",
                            "mkv",
                            "mpg",
                            "mpeg",
                            "m2t",
                            "mov",
                            "mp4",
                            "qt",
                            "vob",
                            "webm",
                            "3gp",
                            "3g2",
                            "asf",
                            "divx",
                            "dirac",
                            "f4v",
                            "h264",
                            "hdmov",
                            "hdv",
                            "m2p",
                            "m2ts",
                            "m2v",
                            "m4e",
                            "mjpg",
                            "mp4v",
                            "mts",
                            "m21",
                            "m2p",
                            "m4v",
                            "mj2",
                            "m1v",
                            "mpv",
                            "m4v",
                            "mxf",
                            "mpegts",
                            "mpegtsraw",
                            "mpegvideo", 
                            "nsv",
                            "ogv",
                            "ogx",
                            "ps",
                            "ts",
                            "tsv",
                            "tsa",
                            "vfw",
                            "video",
                            "wtv",
                            "wm",
                            "wmv",
                            "xvid",
                            "y4m",
                            "yuv"]
