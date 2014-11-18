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
Module is used to create pattern producer media objects for bins and 
corresponding mlt.Producers for timeline. 
"""
import copy
import pygtk
pygtk.require('2.0');
import gtk

import mlt

import appconsts
import dialogutils
import guiutils
from editorstate import PROJECT
import gui
import mltrefhold
import respaths
import utils

# Pattern producer types
UNDEFINED = 0
COLOR_CLIP = 1
NOISE_CLIP = 2
EBUBARS_CLIP = 3

# ---------------------------------------------------- create callbacks
def create_color_clip():
    _color_clip_dialog(_create_color_clip_callback)

def _create_color_clip_callback(dialog, response_id, widgets):
    if response_id == gtk.RESPONSE_ACCEPT:
        entry, color_button = widgets
        name = entry.get_text()
        color_str = color_button.get_color().to_string()
        media_object = BinColorClip(PROJECT().next_media_file_id, name, color_str)
        PROJECT().add_pattern_producer_media_object(media_object)
        _update_gui_for_patter_producer_media_object_add()

    dialog.destroy()

def create_noise_clip():
    media_object = BinNoiseClip(PROJECT().next_media_file_id, _("Noise"))
    PROJECT().add_pattern_producer_media_object(media_object)
    _update_gui_for_patter_producer_media_object_add()

def create_bars_clip():
    media_object = BinColorBarsClip(PROJECT().next_media_file_id, _("EBU Bars"))
    PROJECT().add_pattern_producer_media_object(media_object)
    _update_gui_for_patter_producer_media_object_add()

def _update_gui_for_patter_producer_media_object_add():
    gui.media_list_view.fill_data_model()
    gui.bin_list_view.fill_data_model()

# ----------------------------------------------------- dialogs
def _color_clip_dialog(callback):
    dialog = gtk.Dialog(_("Create Color Clip"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                    _("Create").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    name_entry = gtk.Entry()
    name_entry.set_text(_("Color Clip"))   

    color_button = gtk.ColorButton()

    cb_hbox = gtk.HBox(False, 0)
    cb_hbox.pack_start(color_button, False, False, 4)
    cb_hbox.pack_start(gtk.Label(), True, True, 0)

    row1 = guiutils.get_two_column_box(gtk.Label(_("Clip Name")), name_entry, 200)
    row2 = guiutils.get_two_column_box(gtk.Label(_("Select Color")), cb_hbox, 200)
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(12, 0, 12, 12)
    align.add(vbox)

    selection_widgets = (name_entry, color_button)

    dialog.connect('response', callback, selection_widgets)
    dialog.vbox.pack_start(align, True, True, 0)
    dialogutils.default_behaviour(dialog)
    dialog.show_all()

# ---------------------------------------------------- 
def create_pattern_producer(profile, pattern_producer_data):
    """
    pattern_producer_data is instance of projectdata.BinColorClip
    """
    if pattern_producer_data.patter_producer_type == COLOR_CLIP:
        clip = create_color_producer(profile, pattern_producer_data.gdk_color_str)
    elif pattern_producer_data.patter_producer_type == NOISE_CLIP:
        clip = _create_noise_clip(profile)
    elif pattern_producer_data.patter_producer_type == EBUBARS_CLIP:
        clip = _create_ebubars_clip(profile)
        
    clip.path = ""
    clip.filters = []
    clip.name = pattern_producer_data.name
    clip.media_type = appconsts.PATTERN_PRODUCER
    
    # Save creation data for cloning when editing or doing save/load 
    clip.create_data = copy.copy(pattern_producer_data)
    clip.create_data.icon = None # this is not pickleable, recreate when needed
    return clip

# --------------------------------------------------- producer create methods
def create_color_producer(profile, gdk_color_str):
    mlt_color = utils.gdk_color_str_to_mlt_color_str(gdk_color_str)

    producer = mlt.Producer(profile, "colour", mlt_color)
    mltrefhold.hold_ref(producer)
    producer.gdk_color_str = gdk_color_str

    return producer
        
def _create_noise_clip(profile):
    producer = mlt.Producer(profile, "frei0r.nois0r")
    mltrefhold.hold_ref(producer)
    return producer

def _create_ebubars_clip(profile):
    producer = mlt.Producer(profile, respaths.PATTERN_PRODUCER_PATH + "ebubars.png")
    mltrefhold.hold_ref(producer)
    return producer
    
# --------------------------------------------------- bin media objects
class AbstractBinClip:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.length = 15000
        self.type = appconsts.PATTERN_PRODUCER
        self.icon = None
        self.patter_producer_type = UNDEFINED # extending sets value

        self.mark_in = -1
        self.mark_out = -1

        self.has_proxy_file = False
        self.is_proxy_file = False
        self.second_file_path = None
        
        self.create_icon()

    def create_icon(self):
        print "patter producer create_icon() not implemented"

class BinColorClip(AbstractBinClip):
    """
    Color Clip that can added to and edited in Sequence.
    """   
    def __init__(self, id, name, gdk_color_str):
        self.gdk_color_str = gdk_color_str
        AbstractBinClip.__init__(self, id, name)
        self.patter_producer_type = COLOR_CLIP

    def create_icon(self):
        icon = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, appconsts.THUMB_WIDTH, appconsts.THUMB_HEIGHT)
        pixel = utils.gdk_color_str_to_int(self.gdk_color_str)
        icon.fill(pixel)
        self.icon = icon

class BinNoiseClip(AbstractBinClip):
    def __init__(self, id, name):
        AbstractBinClip.__init__(self, id, name)
        self.patter_producer_type = NOISE_CLIP

    def create_icon(self):
        self.icon = gtk.gdk.pixbuf_new_from_file(respaths.PATTERN_PRODUCER_PATH + "noise_icon.png")

class BinColorBarsClip(AbstractBinClip):
    def __init__(self, id, name):
        AbstractBinClip.__init__(self, id, name)
        self.patter_producer_type = EBUBARS_CLIP

    def create_icon(self):
        self.icon = gtk.gdk.pixbuf_new_from_file(respaths.PATTERN_PRODUCER_PATH + "bars_icon.png")
        
