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
Module handles initializing and displaying audiomonitor tool.
"""
import cairo
import pygtk
pygtk.require('2.0');
import gtk
import glib

import mlt
import pango
import pangocairo
import time

import appconsts
from cairoarea import CairoDrawableArea
import editorpersistance
import editorstate
import mltrefhold
import guiutils
import utils

SLOT_W = 60
METER_SLOT_H = 458
CONTROL_SLOT_H = 300
Y_TOP_PAD = 12

# Dash pattern used to create "LED"s
DASH_INK = 2.0
DASH_SKIP = 1.0
DASHES = [DASH_INK, DASH_SKIP, DASH_INK, DASH_SKIP]

METER_LIGHTS = 143 #57
#METER_HEIGHT = METER_LIGHTS * DASH_INK + (METER_LIGHTS - 1) * DASH_SKIP
METER_HEIGHT = METER_LIGHTS * DASH_INK + (METER_LIGHTS - 1) * DASH_SKIP
METER_WIDTH = 10

# These are calculated using IEC_Scale function in MLT and correspond to level values received here
DB_IEC_MINUS_2 = 0.95
DB_IEC_MINUS_4 = 0.9
DB_IEC_MINUS_6 = 0.85
DB_IEC_MINUS_10 = 0.75
DB_IEC_MINUS_12 = 0.70
DB_IEC_MINUS_20 = 0.5
DB_IEC_MINUS_40 = 0.15

PEAK_FRAMES = 14
OVER_FRAMES = 30

# Colors
METER_BG_COLOR = (0.15, 0.15, 0.15)
OVERLAY_COLOR = (0.70, 0.70, 0.70) #utils.get_cairo_color_tuple_255_rgb(63, 145, 188)#59, 140, 174) #(0.7, 0.7, 1.0)

# Color gradient used to draw "LED" colors
rr, rg, rb = utils.get_cairo_color_tuple_255_rgb(219, 69, 69)
RED_1 = (0, rr, rg, rb, 1)
RED_2 = (1 - DB_IEC_MINUS_4 - 0.005, rr, rg, rb, 1)
YELLOW_1 = (1 - DB_IEC_MINUS_4 - 0.005 + 0.001, 1, 1, 0, 1)
YELLOW_2 = (1 - DB_IEC_MINUS_12, 1, 1, 0, 1)
gr, gg, gb = utils.get_cairo_color_tuple_255_rgb(86, 188, 137)
GREEN_1 = (1 - DB_IEC_MINUS_12 + 0.001, gr, gg, gb, 1)
GREEN_2 = (1, gr, gg, gb, 1)

LEFT_CHANNEL = "_audio_level.0"
RIGHT_CHANNEL = "_audio_level.1"

MONITORING_AVAILABLE = False

# GUI compoents displaying levels
_monitor_window = None
_master_volume_meter = None

_update_ticker = None
_level_filters = [] # 0 master, 1 - (len - 1) editable tracks
_audio_levels = [] # 0 master, 1 - (len - 1) editable tracks
    
def init(profile):
    audio_level_filter = mlt.Filter(profile, "audiolevel")

    global MONITORING_AVAILABLE
    if audio_level_filter != None:
        MONITORING_AVAILABLE = True
        editorstate.audio_monitoring_available = True
    else:
        MONITORING_AVAILABLE = False
        editorstate.audio_monitoring_available = False

    # We want this to be always present when closing app or we'll need to handle it being missing.
    global _update_ticker
    _update_ticker = utils.Ticker(_audio_monitor_update, 0.04)
    _update_ticker.start_ticker()
    _update_ticker.stop_ticker()    

def init_for_project_load():
    # Monitor window is quaranteed to be closed
    if _update_ticker.running:
        _update_ticker.stop_ticker()    
        
    global _level_filters
    _level_filters = None
    _init_level_filters(False)

    _update_ticker.start_ticker()

def close():
    close_audio_monitor()
    close_master_meter()
    _update_ticker.stop_ticker()

def show_audio_monitor():
    global _monitor_window
    if _monitor_window != None:
        return
    
    _init_level_filters(True)

    _monitor_window = AudioMonitorWindow()
        
    global _update_ticker
    if _update_ticker.running == False:
        _update_ticker.start_ticker()

def close_audio_monitor():
    
    global _monitor_window
    if _monitor_window == None:
        return

    editorstate.PLAYER().stop_playback()

    # We're using _monitor_window as a flag here so we need to set to _monitor_window = None
    # to stop _audio_monitor_update running before destroying resources used by it
    temp_window = _monitor_window
    _monitor_window = None
    
    _destroy_level_filters(True)

    # Close and destroy window when gtk finds time to do it
    glib.idle_add(_audio_monitor_destroy, temp_window)

def _audio_monitor_destroy(closed_monitor_window):
    closed_monitor_window.set_visible(False)
    closed_monitor_window.destroy()
    
    return False

def get_master_meter():
    _init_level_filters(False)
    
    global _master_volume_meter, _update_ticker
    
    _master_volume_meter = MasterVolumeMeter()

    if _update_ticker.running == False:
        _update_ticker.start_ticker()

    align = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=1.0, yscale=1.0) 
    align.add(_master_volume_meter.widget)
    align.set_padding(3, 3, 3, 3)

    frame = gtk.Frame()
    frame.add(align)
    frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)

    return frame

def close_master_meter():
    global _master_volume_meter
    if _master_volume_meter == None:
        return

    editorstate.PLAYER().stop_playback()

    # To avoid crashes we can't actually lose widget object before everything is 
    # cleaned up well but _master_volume_meter == None is flag for doing audio updates so we must 
    # set that first
    temp_meter = _master_volume_meter
    _master_volume_meter = None

    _destroy_level_filters(False)
    
    # Close and destroy window when gtk finds time to do it
    glib.idle_add(_master_meter_destroy, temp_meter)

def _master_meter_destroy(closed_master_meter):
    closed_master_meter.widget.set_visible(False)
    closed_master_meter.widget.destroy()

    return False

def _init_level_filters(create_track_filters):
    # We're attaching level filters only to MLT objects and adding nothing to python objects,
    # so when Sequence is saved these filters will automatically be removed.
    # Filters are not part of sequence.Sequence object because they just used for monitoring,
    #
    # Track/master gain values are persistant, they're also editing desitions 
    # and are therefore part of sequence.Sequence objects.
    
    # Create levels filters array if it deosn't exist
    global _level_filters
    if _level_filters == None:
        _level_filters = []

    seq = editorstate.current_sequence()

    # Init master level filter if it does not exist
    if len(_level_filters) == 0:
        _level_filters.append(_add_audio_level_filter(seq.tractor, seq.profile))

    # Init track level filters if requested
    if create_track_filters == True:
        for i in range(1, len(seq.tracks) - 1):
            _level_filters.append(_add_audio_level_filter(seq.tracks[i], seq.profile))

def _destroy_level_filters(destroy_track_filters=False):
    global _level_filters, _audio_levels

    # We need to be sure that audio level updates are stopped before
    # detaching and destroying them
    _update_ticker.stop_ticker()
    #time.sleep(0.2)

    # Detach filters
    if len(_level_filters) != 0:
        seq = editorstate.current_sequence()
        # Only detach master filter if both GUI components destroyed
        if _monitor_window == None and _master_volume_meter == None:
            seq.tractor.detach(_level_filters[0])

        # Track filters are onlty detached when this called from wondow close
        if destroy_track_filters:
            for i in range(1, len(seq.tracks) - 1):
                seq.tracks[i].detach(_level_filters[i])

    # Destroy unneeded filters
    if _master_volume_meter == None and _monitor_window == None:
        _level_filters = []
        _audio_levels = []
    elif _monitor_window == None:
        _level_filters = [_level_filters[0]]
        _audio_levels[0] = 0.0

    if _master_volume_meter != None or _monitor_window != None:
        _update_ticker.start_ticker()

def _add_audio_level_filter(producer, profile):
    audio_level_filter = mlt.Filter(profile, "audiolevel")
    mltrefhold.hold_ref(audio_level_filter)
    producer.attach(audio_level_filter)
    return audio_level_filter

def _audio_monitor_update():
    # This is not called from gtk thread

    if _monitor_window == None and _master_volume_meter == None:
        return

    gtk.gdk.threads_enter()

    global _audio_levels
    _audio_levels = []
    for i in range(0, len(_level_filters)):
        #print i
        audio_level_filter = _level_filters[i]
        l_val = _get_channel_value(audio_level_filter, LEFT_CHANNEL)
        r_val = _get_channel_value(audio_level_filter, RIGHT_CHANNEL)
        _audio_levels.append((l_val, r_val))

    if _monitor_window != None:
        _monitor_window.meters_area.widget.queue_draw()
    if _master_volume_meter != None:
        _master_volume_meter.canvas.queue_draw()

    gtk.gdk.threads_leave()

def _get_channel_value(audio_level_filter, channel_property):
    level_value = audio_level_filter.get(channel_property)
    if level_value == None:
        level_value  = "0.0"

    try:
        level_float = float(level_value)
    except Exception:
        level_float = 0.0

    return level_float


class AudioMonitorWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.connect("delete-event", lambda w, e:close_audio_monitor())
        
        seq = editorstate.current_sequence()
        meters_count = 1 + (len(seq.tracks) - 2) # master + editable tracks
        self.gain_controls = []
        
        self.meters_area = MetersArea(meters_count)
        gain_control_area = gtk.HBox(False, 0)
        seq = editorstate.current_sequence()
        for i in range(0, meters_count):
            if i == 0:
                name = _("Master")
                gain = GainControl(name, seq, seq.tractor, True)
            else:
                name = utils.get_track_name(seq.tracks[i], seq)
                gain = GainControl(name, seq, seq.tracks[i])
            if i == 0:
                tmp = gain
                gain = gtk.EventBox()
                gain.add(tmp)
                bg_color = gtk.gdk.Color(red=0.8, green=0.8, blue=0.8)
                if editorpersistance.prefs.dark_theme == True:
                    bg_color = gtk.gdk.Color(red=0.4, green=0.4, blue=0.4)
                gain.modify_bg(gtk.STATE_NORMAL, bg_color)
            self.gain_controls.append(gain)
            gain_control_area.pack_start(gain, False, False, 0)

        meters_frame = gtk.Frame()
        meters_frame.add(self.meters_area.widget)

        pane = gtk.VBox(False, 1)
        pane.pack_start(meters_frame, True, True, 0)
        pane.pack_start(gain_control_area, True, True, 0)

        align = gtk.Alignment()
        align.set_padding(12, 12, 4, 4)
        align.add(pane)

        # Set pane and show window
        self.add(align)
        self.set_title(_("Audio Mixer"))
        self.show_all()
        self.set_resizable(False)
        self.set_keep_above(True) # Perhaps configurable later


class MetersArea:
    def __init__(self, meters_count):
        w = SLOT_W * meters_count
        h = METER_SLOT_H
        
        self.widget = CairoDrawableArea(w,
                                        h, 
                                        self._draw)
        
        self.audio_meters = [] # displays both l_Value and r_value
        for i in range(0, meters_count):
            meter = AudioMeter(METER_HEIGHT)
            if i != meters_count - 1:
                meter.right_channel.draw_dB = True
            self.audio_meters.append(meter)
            
    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation

        cr.set_source_rgb(*METER_BG_COLOR)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        grad = cairo.LinearGradient (0, Y_TOP_PAD, 0, METER_HEIGHT + Y_TOP_PAD)
        grad.add_color_stop_rgba(*RED_1)
        grad.add_color_stop_rgba(*RED_2)
        grad.add_color_stop_rgba(*YELLOW_1)
        grad.add_color_stop_rgba(*YELLOW_2)
        grad.add_color_stop_rgba(*GREEN_1)
        grad.add_color_stop_rgba(*GREEN_2)

        for i in range(0, len(_audio_levels)):
            meter = self.audio_meters[i]
            l_value, r_value = _audio_levels[i]
            x = i * SLOT_W
            meter.display_value(cr, x, l_value, r_value, grad)


class AudioMeter:
    def __init__(self, height):
        self.left_channel = ChannelMeter(height, "L")
        self.right_channel = ChannelMeter(height, "R")
        self.x_pad_l = 18 + 2
        self.x_pad_r = SLOT_W / 2 + 6 - 2
        self.meter_width = METER_WIDTH

    def display_value(self, cr, x, value_left, value_right, grad):
        cr.set_source(grad)
        cr.set_dash(DASHES, 0) 
        cr.set_line_width(self.meter_width)
        self.left_channel.display_value(cr, x + self.x_pad_l, value_left)

        cr.set_source(grad)
        cr.set_dash(DASHES, 0) 
        cr.set_line_width(self.meter_width)
        self.right_channel.display_value(cr, x + self.x_pad_r, value_right)

        
class ChannelMeter:
    def __init__(self, height, channel_text):
        self.height = height
        self.channel_text = channel_text
        self.peak = 0.0
        self.countdown = 0
        self.draw_dB = False
        self.dB_x_pad = 11
        self.y_top_pad = Y_TOP_PAD
        self.over_countdown = 0

    def display_value(self, cr, x, value):
        if value > 1.0:
            self.over_countdown = OVER_FRAMES

        top = self.get_meter_y_for_value(value)
        if (self.height - top) < 5: # fix for meter y rounding for vol 0
            top = self.height
        cr.move_to(x, self.height + self.y_top_pad)
        cr.line_to(x, top + self.y_top_pad)
        cr.stroke()
        
        if value > self.peak:
            self.peak = value
            self.countdown = PEAK_FRAMES
        
        if self.peak > value:
            if self.peak > 1.0:
                self.peak = 1.0
            cr.rectangle(x - METER_WIDTH / 2, 
                         self.get_meter_y_for_value(self.peak) + DASH_SKIP * 2 + DASH_INK + 3, # this y is just empirism, works
                         METER_WIDTH,
                         DASH_INK)
            cr.fill()

        self.countdown = self.countdown - 1
        if self.countdown <= 0:
             self.peak = 0

        if self.over_countdown > 0:
            cr.set_source_rgb(1,0.6,0.6)
            cr.move_to(x, 0)
            cr.line_to(x + 4, 4)
            cr.line_to(x, 8)
            cr.line_to(x - 4, 4)
            cr.close_path()
            cr.fill()
            self.over_countdown = self.over_countdown - 1
                    
        self.draw_channel_identifier(cr, x)

        if self.draw_dB == True:
            self.draw_value_line(cr, x, 1.0, "0", 7)
            self.draw_value_line(cr, x, DB_IEC_MINUS_4,"-4", 4)
            self.draw_value_line(cr, x, DB_IEC_MINUS_12, "-12", 1)
            self.draw_value_line(cr, x, DB_IEC_MINUS_20, "-20", 1)
            self.draw_value_line(cr, x, DB_IEC_MINUS_40, "-40", 1)
            self.draw_value_line(cr, x, 0.0,  u"\u221E", 5)
            
    def get_meter_y_for_value(self, value):
        y = self.get_y_for_value(value)
        # Get pad for y value between "LED"s
        dash_sharp_pad = y % (DASH_INK + DASH_SKIP)
        # Round to nearest full "LED" using pad value
        if dash_sharp_pad < ((DASH_INK + DASH_SKIP) / 2):
            meter_y = y - dash_sharp_pad
        else:
            dash_sharp_pad = (DASH_INK + DASH_SKIP) - dash_sharp_pad
            meter_y = y + dash_sharp_pad
        return meter_y

    def get_y_for_value(self, value):
        return self.height - (value * self.height)
    
    def draw_value_line(self, cr, x, value, val_text, x_fine_tune):
        y = self.get_y_for_value(value)
        self.draw_text(val_text, "Sans 8", cr, x + self.dB_x_pad + x_fine_tune, y - 8 + self.y_top_pad, OVERLAY_COLOR)
        
    def draw_channel_identifier(self, cr, x):
        self.draw_text(self.channel_text, "Sans Bold 8", cr, x - 4, self.height + 2 +  self.y_top_pad, OVERLAY_COLOR)

    def draw_text(self, text, font_desc, cr, x, y, color):
        pango_context = pangocairo.CairoContext(cr)
        layout = pango_context.create_layout()
        layout.set_text(text)
        desc = pango.FontDescription(font_desc)
        layout.set_font_description(desc)

        pango_context.set_source_rgb(*color)
        pango_context.move_to(x, y)
        pango_context.update_layout(layout)
        pango_context.show_layout(layout)
        

class GainControl(gtk.Frame):
    def __init__(self, name, seq, producer, is_master=False):
        gtk.Frame.__init__(self)
        
        self.seq = seq
        self.producer = producer
        self.is_master = is_master

        if is_master:
            gain_value = seq.master_audio_gain # tractor master
        else:
            gain_value = producer.audio_gain # track
        gain_value = gain_value * 100
        
        self.adjustment = gtk.Adjustment(value=gain_value, lower=0, upper=100, step_incr=1)
        self.slider = gtk.VScale()
        self.slider.set_adjustment(self.adjustment)
        self.slider.set_size_request(SLOT_W - 10, CONTROL_SLOT_H - 105)
        self.slider.set_inverted(True)
        self.slider.connect("value-changed", self.gain_changed)
   
        if is_master:
            pan_value = seq.master_audio_pan
        else:
            pan_value = producer.audio_pan
        if pan_value == appconsts.NO_PAN:
            pan_value = 0.5 # center
        pan_value = (pan_value - 0.5) * 200 # from range 0 - 1 to range -100 - 100

        self.pan_adjustment = gtk.Adjustment(value=pan_value, lower=-100, upper=100, step_incr=1)
        self.pan_slider = gtk.HScale()
        self.pan_slider.set_adjustment(self.pan_adjustment)
        self.pan_slider.connect("value-changed", self.pan_changed)

        self.pan_button = gtk.ToggleButton(_("Pan"))
        self.pan_button.connect("toggled", self.pan_active_toggled)
        
        if pan_value == 0.0:
            self.pan_slider.set_sensitive(False)
        else:
            self.pan_button.set_active(True)
            self.pan_adjustment.set_value(pan_value) # setting button active sets value = 0, set correct value again

        label = guiutils.bold_label(name)

        vbox = gtk.VBox(False, 0)
        vbox.pack_start(guiutils.get_pad_label(5,5), False, False, 0)
        vbox.pack_start(label, False, False, 0)
        vbox.pack_start(guiutils.get_pad_label(5,5), False, False, 0)
        vbox.pack_start(self.slider, False, False, 0)
        vbox.pack_start(self.pan_button, False, False, 0)
        vbox.pack_start(self.pan_slider, False, False, 0)
        vbox.pack_start(guiutils.get_pad_label(5,5), False, False, 0)

        self.add(vbox)
        self.set_size_request(SLOT_W, CONTROL_SLOT_H)

    def gain_changed(self, slider):
        gain = slider.get_value() / 100.0
        if self.is_master == True:
            self.seq.set_master_gain(gain)
        else:
            self.seq.set_track_gain(self.producer, gain)
        
    def pan_active_toggled(self, widget):
        self.pan_slider.set_value(0.0)
        if widget.get_active():
            self.pan_slider.set_sensitive(True)
            self.seq.add_track_pan_filter(self.producer, 0.5)
            if self.is_master:
                self.seq.master_audio_pan = 0.5
        else:
            self.pan_slider.set_sensitive(False)
            self.seq.remove_track_pan_filter(self.producer)
            if self.is_master:
                self.seq.master_audio_pan = appconsts.NO_PAN

    def pan_changed(self, slider):
        pan_value = (slider.get_value() + 100) / 200.0
        if self.is_master:
            self.seq.set_master_pan_value(pan_value)
        else:
            self.seq.set_track_pan_value(self.producer, pan_value)



class MasterVolumeMeter:
    def __init__(self):
        self.meter = AudioMeter(METER_HEIGHT + 40)
        self.meter.x_pad_l = 6
        self.meter.x_pad_r = 14
        self.meter.right_channel.draw_dB = True
        self.meter.right_channel.dB_x_pad = -14
        self.meter.meter_width = 5
        self.top_pad = 14
        self.meter.right_channel.y_top_pad = self.top_pad 
        self.meter.left_channel.y_top_pad = self.top_pad 

        w = SLOT_W - 40
        h = METER_SLOT_H + 2 + 40
        self.canvas = CairoDrawableArea(w,
                                        h, 
                                        self._draw)

        self.widget = gtk.VBox(False, 0)
        self.widget.pack_start(self.canvas, False, False, 0)

    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation

        cr.set_source_rgb(*METER_BG_COLOR)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        grad = cairo.LinearGradient (0, self.top_pad, 0, METER_HEIGHT + self.top_pad)
        grad.add_color_stop_rgba(*RED_1)
        grad.add_color_stop_rgba(*RED_2)
        grad.add_color_stop_rgba(*YELLOW_1)
        grad.add_color_stop_rgba(*YELLOW_2)
        grad.add_color_stop_rgba(*GREEN_1)
        grad.add_color_stop_rgba(*GREEN_2)

        l_value, r_value = _audio_levels[0]
        x = 0
        self.meter.display_value(cr, x, l_value, r_value, grad)
