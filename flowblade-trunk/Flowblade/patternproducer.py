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
ISING_CLIP = 4
COLOR_PULSE_CLIP = 5

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
        _update_gui_for_pattern_producer_media_object_add()

    dialog.destroy()

def create_noise_clip():
    media_object = BinNoiseClip(PROJECT().next_media_file_id, _("Noise"))
    PROJECT().add_pattern_producer_media_object(media_object)
    _update_gui_for_pattern_producer_media_object_add()

def create_bars_clip():
    media_object = BinColorBarsClip(PROJECT().next_media_file_id, _("EBU Bars"))
    PROJECT().add_pattern_producer_media_object(media_object)
    _update_gui_for_pattern_producer_media_object_add()

def create_icing_clip():
    _ising_clip_dialog(_create_ising_clip_callback)

def _create_ising_clip_callback(dialog, response_id, widgets):
    if response_id == gtk.RESPONSE_ACCEPT:
        media_object = BinIsingClip(PROJECT().next_media_file_id, _("Ising"))

        temp_slider, bg_slider, sg_slider = widgets
        media_object.set_property_values(temp_slider.get_adjustment().get_value() / 100.0,
                                         bg_slider.get_adjustment().get_value() / 100.0, 
                                         sg_slider.get_adjustment().get_value() / 100.0)

        PROJECT().add_pattern_producer_media_object(media_object)
        _update_gui_for_pattern_producer_media_object_add()
        
    dialog.destroy()

def create_color_pulse_clip():
    _color_pulse_clip_dialog(_create_color_pulse_clip_callback)

def _create_color_pulse_clip_callback(dialog, response_id, widgets):
    if response_id == gtk.RESPONSE_ACCEPT:
        media_object = BinColorPulseClip(PROJECT().next_media_file_id, _("Color Pulse"))

        s1_slider, s2_slider, s3_slider, s4_slider, m1_slider, m2_slider = widgets
        media_object.set_property_values(s1_slider.get_adjustment().get_value() / 100.0,
                                         s2_slider.get_adjustment().get_value() / 100.0, 
                                         s3_slider.get_adjustment().get_value() / 100.0,
                                         s4_slider.get_adjustment().get_value() / 100.0,
                                         m1_slider.get_adjustment().get_value() / 100.0,
                                         m2_slider.get_adjustment().get_value() / 100.0)

        PROJECT().add_pattern_producer_media_object(media_object)
        _update_gui_for_pattern_producer_media_object_add()

    dialog.destroy()
    
def _update_gui_for_pattern_producer_media_object_add():
    gui.media_list_view.fill_data_model()
    gui.bin_list_view.fill_data_model()

# ---------------------------------------------------- 
def create_pattern_producer(profile, bin_clip):
    """
    bin_clip is instance of AbstractBinClip extending class
    """
    try:
        clip = bin_clip.create_mlt_producer(profile)
    except:
        clip = _create_patten_producer_old_style(profile, bin_clip)

    clip.path = ""
    clip.filters = []
    clip.name = bin_clip.name
    clip.media_type = appconsts.PATTERN_PRODUCER

    # Save creation data for cloning when editing or doing save/load 
    clip.create_data = copy.copy(bin_clip)
    clip.create_data.icon = None # this is not pickleable, recreate when needed
    return clip

# --------------------------------------------------- DECPRECATED producer create methods
# --------------------------------------------------- REMOVE 2017
"""
We originally did producer creation using elifs and now using pickle() for save/load 
requires keeping this around until atleast 2017 for backwards compatibility.
"""
def _create_patten_producer_old_style(profile, bin_clip):
    if bin_clip.patter_producer_type == COLOR_CLIP:
        clip = create_color_producer(profile, bin_clip.gdk_color_str)
    elif bin_clip.patter_producer_type == NOISE_CLIP:
        clip = _create_noise_producer(profile)
    elif bin_clip.patter_producer_type == EBUBARS_CLIP:
        clip = _create_ebubars_producer(profile)
    
    return clip

def create_color_producer(profile, gdk_color_str):
    mlt_color = utils.gdk_color_str_to_mlt_color_str(gdk_color_str)

    producer = mlt.Producer(profile, "colour", mlt_color)
    mltrefhold.hold_ref(producer)
    producer.gdk_color_str = gdk_color_str

    return producer
        
def _create_noise_producer(profile):
    producer = mlt.Producer(profile, "frei0r.nois0r")
    mltrefhold.hold_ref(producer)
    return producer

def _create_ebubars_producer(profile):
    producer = mlt.Producer(profile, respaths.PATTERN_PRODUCER_PATH + "ebubars.png")
    mltrefhold.hold_ref(producer)
    return producer

# --------------------------------------------------- END DECPRECATED producer create methods

# --------------------------------------------------- bin media objects
class AbstractBinClip: # not extends projectdata.MediaFile? too late, too late. Also better name would be AbstractBinPatternProducer
    """
    A pattern producer object presnt in Media Bin.
    """
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

    def create_mlt_producer(self, profile):
        print "create_mlt_producer not implemented"

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

    def create_mlt_producer(self, profile):
        mlt_color = utils.gdk_color_str_to_mlt_color_str(self.gdk_color_str)

        producer = mlt.Producer(profile, "colour", mlt_color)
        mltrefhold.hold_ref(producer)
        producer.gdk_color_str = self.gdk_color_str

        return producer

    def create_icon(self):
        icon = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, appconsts.THUMB_WIDTH, appconsts.THUMB_HEIGHT)
        pixel = utils.gdk_color_str_to_int(self.gdk_color_str)
        icon.fill(pixel)
        self.icon = icon

class BinNoiseClip(AbstractBinClip):
    def __init__(self, id, name):
        AbstractBinClip.__init__(self, id, name)
        self.patter_producer_type = NOISE_CLIP

    def create_mlt_producer(self, profile):
        producer = mlt.Producer(profile, "frei0r.nois0r")        
        mltrefhold.hold_ref(producer)
        return producer
    
    def create_icon(self):
        self.icon = gtk.gdk.pixbuf_new_from_file(respaths.PATTERN_PRODUCER_PATH + "noise_icon.png")

class BinColorBarsClip(AbstractBinClip):
    def __init__(self, id, name):
        AbstractBinClip.__init__(self, id, name)
        self.patter_producer_type = EBUBARS_CLIP

    def create_mlt_producer(self, profile):
        producer = mlt.Producer(profile, respaths.PATTERN_PRODUCER_PATH + "ebubars.png")
        mltrefhold.hold_ref(producer)
        return producer

    def create_icon(self):
        self.icon = gtk.gdk.pixbuf_new_from_file(respaths.PATTERN_PRODUCER_PATH + "bars_icon.png")
        
class BinIsingClip(AbstractBinClip):
    def __init__(self, id, name):
        AbstractBinClip.__init__(self, id, name)
        self.patter_producer_type = ISING_CLIP

    def set_property_values(self, temp, bg, sg):
        self.temp = temp
        self.bg = bg
        self.sg = sg

    def create_mlt_producer(self, profile):
        producer = mlt.Producer(profile, "frei0r.ising0r")
        producer.set("Temperature", str(self.temp))
        producer.set("Border Growth", str(self.bg))
        producer.set("Spontaneous Growth", str(self.sg))
        mltrefhold.hold_ref(producer)
        return producer

    def create_icon(self):
        self.icon = gtk.gdk.pixbuf_new_from_file(respaths.PATTERN_PRODUCER_PATH + "ising_icon.png")
        
class BinColorPulseClip(AbstractBinClip):
    def __init__(self, id, name):
        AbstractBinClip.__init__(self, id, name)
        self.patter_producer_type = COLOR_PULSE_CLIP

    def set_property_values(self, s1, s2, s3, s4, m1, m2):
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3
        self.s4 = s4
        self.m1 = m1
        self.m2 = m2

    def create_mlt_producer(self, profile):
        producer = mlt.Producer(profile, "frei0r.plasma")
        producer.set("1_speed", str(self.s1))
        producer.set("2_speed", str(self.s2))
        producer.set("3_speed", str(self.s3))
        producer.set("4_speed", str(self.s4))
        producer.set("1_move", str(self.m1))
        producer.set("2_move", str(self.m2))
        mltrefhold.hold_ref(producer)
        return producer

    def create_icon(self):
        self.icon = gtk.gdk.pixbuf_new_from_file(respaths.PATTERN_PRODUCER_PATH + "color_pulse_icon.png")


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

    row1 = guiutils.get_two_column_box(gtk.Label(_("Clip Name:")), name_entry, 200)
    row2 = guiutils.get_two_column_box(gtk.Label(_("Select Color:")), cb_hbox, 200)
    
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

def _ising_clip_dialog(callback):
    dialog = gtk.Dialog(_("Create Ising Clip"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                    _("Create").encode('utf-8'), gtk.RESPONSE_ACCEPT))
 
    n_box, n_slider = guiutils.get_non_property_slider_row(0, 100, 1)
    bg_box, bg_slider = guiutils.get_non_property_slider_row(0, 100, 1)
    sg_box, sg_slider = guiutils.get_non_property_slider_row(0, 100, 1)

    row1 = guiutils.get_two_column_box(gtk.Label(_("Noise temperature:")), n_box, 200)
    row2 = guiutils.get_two_column_box(gtk.Label(_("Border growth:")), bg_box, 200)
    row3 = guiutils.get_two_column_box(gtk.Label(_("Spontanious growth:")), sg_box, 200)
    
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    vbox.set_size_request(450, 150)

    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(12, 0, 12, 12)
    align.add(vbox)

    selection_widgets = (n_slider, bg_slider, sg_slider)

    dialog.connect('response', callback, selection_widgets)
    dialog.vbox.pack_start(align, True, True, 0)
    dialogutils.default_behaviour(dialog)
    dialog.show_all()
    
def _color_pulse_clip_dialog(callback):
    dialog = gtk.Dialog(_("Create Color Pulse Clip"), None,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                    (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                    _("Create").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    s1_box, s1_slider = guiutils.get_non_property_slider_row(0, 100, 1, 100)
    s2_box, s2_slider = guiutils.get_non_property_slider_row(0, 100, 1, 100)
    s3_box, s3_slider = guiutils.get_non_property_slider_row(0, 100, 1, 100)
    s4_box, s4_slider = guiutils.get_non_property_slider_row(0, 100, 1, 100)
    m1_box, m1_slider = guiutils.get_non_property_slider_row(0, 100, 1, 100)
    m2_box, m2_slider = guiutils.get_non_property_slider_row(0, 100, 1, 100)

    row1 = guiutils.get_two_column_box(gtk.Label(_("Speed 1:")), s1_box, 200)
    row2 = guiutils.get_two_column_box(gtk.Label(_("Speed 2:")), s2_box, 200)
    row3 = guiutils.get_two_column_box(gtk.Label(_("Speed 3:")), s3_box, 200)
    row4 = guiutils.get_two_column_box(gtk.Label(_("Speed 4:")), s4_box, 200)
    row5 = guiutils.get_two_column_box(gtk.Label(_("Move 1:")), m1_box, 200)
    row6 = guiutils.get_two_column_box(gtk.Label(_("Move 2:")), m2_box, 200)

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    vbox.set_size_request(450, 220)

    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(12, 0, 12, 12)
    align.add(vbox)

    selection_widgets = (s1_slider, s2_slider, s3_slider, s4_slider, m1_slider, m2_slider)

    dialog.connect('response', callback, selection_widgets)
    dialog.vbox.pack_start(align, True, True, 0)
    dialogutils.default_behaviour(dialog)
    dialog.show_all()
    
