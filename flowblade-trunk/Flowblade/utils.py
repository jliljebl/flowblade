"""
Helper functions and data
"""
import gtk
import math
import mlt
import os
import threading
import time

import appconsts
from editorstate import PROJECT
import respaths

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
    
    def start_ticker(self):
        self.ev = threading.Event()
        self.thread = threading.Thread(target=self.runner,  
                                       args=(self.ev, 
                                       self.delay, 
                                       self.action))
        self.running = True
        self.thread.start()
    
    def stop_ticker(self):
        try:
            self.ev.set()
            self.running = False
        except Exception:
            pass # called when not running

    def runner(self, event, delay, action):
        while True:
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
    sec = length / fps()
    mins = sec / 60
    sec = int(math.floor(sec % 60))
    hours = int(math.floor(mins / 60))
    mins = int(math.floor(mins % 60))
    
    hr_str = ""
    if hours > 0:
        hr_str = str(hours) + "h"
    min_str = ""
    if mins > 0:
        min_str = str(mins) + "m"
    if sec > 0:
        s_str = str(sec) + "s"
    else:
        s_str = str(length) + "fr"
    return hr_str + min_str + s_str

def get_tc_string(frame):
    """ 
    Returns timecode string for frame
    """
    fr = frame % fps()
    sec = frame / fps()
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
    
    if hours >= 1.0:
        return str(int(hours)) + "h " + str(int(mins)) + "m " + str(int(sec)) + "s"
    if mins >= 1.0:
        return str(int(mins)) + "m " + str(int(sec)) + "s"
    return str(int(sec)) + "s"
        
def get_file_thumbnail(icon_file):
    try:
        pixbuf = gtk.gdk.pixbuf_new_from_file(source_file)
    except:
        return None
    else:
        return pixbuf.scale_simple(64, 100, gtk.gdk.INTERP_BILINEAR)
"""
def get_thumnail_path(file_name):
    tokens = file_name.split(".")
    return respaths.THUMBNAIL_PATH + tokens[0] +  "_1.png"
"""
def get_track_name(track, sequence):
    if track.type == appconsts.VIDEO:
        # Video tracks are numbered to USER as 'V1' ,'V2' with 'V1' being
        # tracks[current_sequence.first_video_index]
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
    filter = gtk.FileFilter()
    filter.set_name("Media MIME types")
    filter.add_mime_type("image*")
    filter.add_mime_type("video*")
    filter.add_mime_type("audio*")
    filter.add_mime_type("video/x-theora+ogg")
    filter.add_mime_type("video/x-sgi-movie")
    filter.add_mime_type("video/ogg")
    filter.add_mime_type("video/x-ogm")
    filter.add_mime_type("video/x-ogm+ogg")
    filter.add_mime_type("video/x-ms-asf")
    filter.add_mime_type("video/x-ms-wmv")
    filter.add_mime_type("video/x-msvideo")
    filter.add_mime_type("video/x-matroska")
    filter.add_mime_type("video/x-flv")
    filter.add_mime_type("video/vnd.rn-realvideo")
    filter.add_mime_type("video/quicktime")
    filter.add_mime_type("video/ogg")
    filter.add_mime_type("video/mpeg")
    filter.add_mime_type("video/mp4")
    filter.add_mime_type("video/mp2t")
    filter.add_mime_type("video/isivideo")
    filter.add_mime_type("video/dv")
    filter.add_mime_type("video/annodex")
    filter.add_mime_type("video/3gpp")
    filter.add_mime_type("video/webm")
    
    filter.add_mime_type("audio/aac")
    filter.add_mime_type("audio/ac3")
    filter.add_mime_type("audio/AMR")
    filter.add_mime_type("audio/ogg")
    filter.add_mime_type("audio/midi")
    filter.add_mime_type("audio/mp2")
    filter.add_mime_type("audio/mp4")
    filter.add_mime_type("audio/mpeg")
    filter.add_mime_type("audio/ogg")
    filter.add_mime_type("audio/vnd.rn-realaudio")
    filter.add_mime_type("audio/vorbis")
    filter.add_mime_type("audio/x-adpcm")
    filter.add_mime_type("audio/x-aifc")
    filter.add_mime_type("audio/x-aiff")
    filter.add_mime_type("audio/x-aiffc")
    filter.add_mime_type("audio/x-flac")
    filter.add_mime_type("audio/x-flac+ogg")
    filter.add_mime_type("audio/x-m4b")
    filter.add_mime_type("audio/x-matroska")
    filter.add_mime_type("audio/x-ms-wma")
    filter.add_mime_type("audio/x-oggflac")
    filter.add_mime_type("audio/x-ms-asx")
    filter.add_mime_type("audio/x-ms-wma")
    filter.add_mime_type("audio/x-ms-wma")
    filter.add_mime_type("audio/x-gsm")
    filter.add_mime_type("audio/x-riff")
    filter.add_mime_type("audio/x-speex")
    filter.add_mime_type("audio/x-speex+ogg")
    filter.add_mime_type("audio/x-tta")
    filter.add_mime_type("audio/x-voc")
    filter.add_mime_type("audio/x-vorbis+ogg")
    filter.add_mime_type("audio/x-wav")
    filter.add_mime_type("audio/annodex")

    filter.add_mime_type("image/bmp")
    filter.add_mime_type("image/tiff")
    filter.add_mime_type("image/gif")
    filter.add_mime_type("image/x-tga")
    filter.add_mime_type("image/png")
    filter.add_mime_type("image/jpeg")

    return filter

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

def get_line_for_points(p1, p2):
    """
    Points are (x, y) tuples
    """
    x1, y1 = p1
    x2, y2 = p2

    if (x1 == x2):
        is_vertical = True;
        x_icept = x1;
        m = None
        b = None
    else:
        is_vertical = False
        # slope
        m = (y2-y1) / (x2-x1)
        # get y intercept b
        b = y1 - (m * x1)
        x_icept = None

    return Line(m, b, is_vertical, x_icept)

def do_nothing():
    pass

def get_hidden_user_dir_path():
    return os.getenv("HOME") + "/.flowblade/"

class Line:
        """
        Mathematical line using function y = mx + b.
        """
        def __init__(self, m, b, is_vertical, x_icept):
            self.m = m
            self.b = b
            self.is_vertical = is_vertical
            self.x_icept = x_icept

        def get_normal_projection_point(self, p):
            # Returns point on this line and that is also on the line 
            # that is perpendicular with this and goes through provided point
            x, y = p

            # vertical
            if (self.is_vertical == True):
                return (self.x_icept, y)

            # horizontal
            if( self.m == 0 ):
                return (x, self.b)
                
            # has slope
            normal_m = -1.0 / self.m
            normal_b = y - normal_m * x               
            intersect_x = (normal_b - self.b) / (self.m - normal_m)
            intersect_y = intersect_x * self.m + self.b
            return (intersect_x, intersect_y)
