"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2022 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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
Helper functions that require Gtk dependency.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib


class GtkTicker:
    """
    Calls function repeatedly with given delay between calls.
    This cannot be restarted after calling destroy_ticker(),
    that would cause undefined behaviour,
    instead create a new one when needed.
    """
    def __init__(self, action, delay, data=None):
        self.action = action # callback function
        self.delay = delay # in milliseconds
        self.data = data
        self.running = False
        self.exited = False
    
    def start_ticker(self, delay=None):
        self.running = True
        # Poll rendering from GDK with timeout events to get access to GDK lock on updates 
        # to be able to draw immediately.
        GLib.timeout_add(self.delay, self._update)
    
    def destroy_ticker(self):
        self.running = False

    def _update(self):
        if not self.running:
            self.exited = True
            return False
        self.action(self.data)
        if not self.running:
            self.exited = True
            return False
        else:
            return True

def get_display_monitors_size_data():
    monitors_size_data = []
    
    display = Gdk.Display.get_default()
    num_monitors = display.get_n_monitors() # Get number of monitors.

    for monitor_index in range(0, num_monitors):
        monitor = display.get_monitor(monitor_index)
        geom = monitor.get_geometry()
        monitors_size_data.append((geom.width, geom.height))
    
    return monitors_size_data

def get_combined_monitors_size():
    monitor_data = get_display_monitors_size_data()
    combined_w, combined_h = 0, 0
    
    # We are using largest screen height
    disp_h_largest = 0
    for disp_w, disp_h in monitor_data:
        combined_w += disp_w
        if disp_h > disp_h_largest:
            disp_h_largest = disp_h

    return (combined_w, disp_h_largest)

def get_media_source_file_filter(include_audio=True):
    # No idea if these actually play or not, except images mime types
    f = Gtk.FileFilter()
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
    
    if include_audio == True:
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

def get_video_source_file_filter():
    # No idea if these actually play or not, except images mime types
    f = Gtk.FileFilter()
    f.set_name("Video files")
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

    return f

def get_image_sequence_file_filter():
    f = Gtk.FileFilter()
    f.set_name("Image files")
    f.add_mime_type("image/bmp")
    f.add_mime_type("image/tiff")
    f.add_mime_type("image/gif")
    f.add_mime_type("image/x-tga")
    f.add_mime_type("image/png")
    f.add_mime_type("image/jpeg")

    return f
