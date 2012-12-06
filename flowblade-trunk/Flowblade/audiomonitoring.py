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
import cairo
import gtk
import mlt
import pango
import pangocairo

from cairoarea import CairoDrawableArea
import editorstate
import guiutils
import utils

SLOT_W = 60
METER_SLOT_H = 426
CONTROL_SLOT_H = 300
Y_TOP_PAD = 12

# Dash pattern used to create "LED"s
DASH_INK = 5.0
DASH_SKIP = 2.0
DASHES = [DASH_INK, DASH_SKIP, DASH_INK, DASH_SKIP]

METER_LIGHTS = 57
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

PEAK_FRAMES = 7
OVER_FRAMES = 20

# Color gradient used to draw "LED" colors
RED_1 = (0, 1, 0, 0, 1)
RED_2 = (1 - DB_IEC_MINUS_4, 1, 0, 0, 1)
YELLOW_1 = (1 - DB_IEC_MINUS_4 + 0.001, 1, 1, 0, 1)
YELLOW_2 = (1 - DB_IEC_MINUS_12, 1, 1, 0, 1)
GREEN_1 = (1 - DB_IEC_MINUS_12 + 0.001, 0, 1, 0, 1)
GREEN_2 = (1, 0, 1, 0, 1)

LEFT_CHANNEL = "_audio_level.0"
RIGHT_CHANNEL = "_audio_level.1"

MONITORING_AVAILABLE = False

_monitor_window = None
_update_ticker = None
_level_filters = [] # 0 master, 1 - (len - 1) editable tracks
_audio_levels = [] # 0 master, 1 - (len - 1) editable tracks
    
def init():
    audio_level_filter = mlt.Filter(self.profile, "audiolevel")

    global MONITORING_AVAILABLE
    if audio_level_filter != None:
        MONITORING_AVAILABLE = True
    else:
        MONITORING_AVAILABLE = False
    
def show_audio_monitor():
    #print DB_IEC_MINUS_2, DB_IEC_MINUS_6, IEC_Scale(-40)
    global _monitor_window
    if _monitor_window != None:
        return
    
    _init_level_filters()

    _monitor_window = AudioMonitorWindow()
        
    global _update_ticker
    _update_ticker = utils.Ticker(_audio_monitor_update, 0.04)
    _update_ticker.start_ticker()

def _init_level_filters():
    # We're attaching level filters only to MLT objects and adding nothing to python objects,
    # so when Sequence is saved these filters will automatically be removed.
    # Filters are not part of sequence.Sequence object because they just used for monitoring,
    #
    # Track/master gain values are persistant, they're also editing desitions 
    # and are therefpre part of Sequence objects.
    global _level_filters
    _level_filters = []
    seq = editorstate.current_sequence()
    # master level filter
    _level_filters.append(_add_audio_level_filter(seq.tractor, seq.profile))
    # editable track level filters
    for i in range(1, len(seq.tracks) - 1):
        _level_filters.append(_add_audio_level_filter(seq.tracks[i], seq.profile))

def _add_audio_level_filter(producer, profile):
    audio_level_filter = mlt.Filter(profile, "audiolevel")
    producer.attach(audio_level_filter)
    return audio_level_filter

def _audio_monitor_update():
    global _audio_levels
    _audio_levels = []
    for i in range(0, len(_level_filters)):
        audio_level_filter = _level_filters[i]
        l_val = _get_channel_value(audio_level_filter, LEFT_CHANNEL)
        r_val = _get_channel_value(audio_level_filter, RIGHT_CHANNEL)
        _audio_levels.append((l_val, r_val))

    _monitor_window.meters_area.widget.queue_draw()


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
        seq = editorstate.current_sequence()
        meters_count = 1 + (len(seq.tracks) - 2) # master + editable tracks
        self.gain_controls = []
        
        self.meters_area = MetersArea(meters_count)
        gain_control_area = gtk.HBox(False, 0)
        for i in range(0, meters_count):
            if i == 0:
                name = "Master"
            else:
                name = utils.get_track_name(seq.tracks[i], seq)
            gain = GainControl(name)
            if i == 0:
                tmp = gain
                gain = gtk.EventBox()
                gain.add(tmp)
                gain.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(red=0.8, green=0.8, blue=0.8))
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
        self.show_all()
        self.set_resizable(False)

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

        cr.set_source_rgb(0,0,0)
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

    def display_value(self, cr, x, value_left, value_right, grad):
        cr.set_source(grad)
        cr.set_dash(DASHES, 0) 
        cr.set_line_width(METER_WIDTH)
        self.left_channel.display_value(cr, x + 18, value_left)

        cr.set_source(grad)
        cr.set_dash(DASHES, 0) 
        cr.set_line_width(METER_WIDTH)
        self.right_channel.display_value(cr, x + SLOT_W / 2 + 6, value_right)
        
class ChannelMeter:
    def __init__(self, height, channel_text):
        self.height = height
        self.channel_text = channel_text
        self.peak = 0.0
        self.countdown = 0
        self.draw_dB = False
        self.over_countdown = 0

    def display_value(self, cr, x, value):
        if value > 1.0:
            cr.set_source_rgb(1,0,0)
            self.over_countdown = OVER_FRAMES

        top = self.get_meter_y_for_value(value)
        if (self.height - top) < 5: # fix for meter y rounding for vol 0
            top = self.height
        cr.move_to(x, self.height + Y_TOP_PAD)
        cr.line_to(x, top + Y_TOP_PAD)
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
            self.draw_value_line(cr, x, 1.0, "0", 6)
            self.draw_value_line(cr, x, DB_IEC_MINUS_4,"-4", 3)
            self.draw_value_line(cr, x, DB_IEC_MINUS_12, "-12", 0)
            self.draw_value_line(cr, x, DB_IEC_MINUS_20, "-20", 0)
            self.draw_value_line(cr, x, DB_IEC_MINUS_40, "-40", 0)
        
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
        self.draw_text(val_text, "Sans 8", cr, x + 11 + x_fine_tune, y - 8 + Y_TOP_PAD, (1,1,1))
        
    def draw_channel_identifier(self, cr, x):
        self.draw_text(self.channel_text, "Sans Bold 8", cr, x - 4, self.height + 2 + Y_TOP_PAD, (1,1,1))

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
    def __init__(self, name):
        gtk.Frame.__init__(self)
        self.adjustment = gtk.Adjustment(value=100, lower=0, upper=100, step_incr=1)
        self.slider = gtk.VScale()
        self.slider.set_adjustment(self.adjustment)
        self.slider.set_size_request(SLOT_W - 10, CONTROL_SLOT_H - 105)
        self.slider.set_inverted(True)

        self.pan_adjustment = gtk.Adjustment(value=0, lower=-100, upper=100, step_incr=1)
        self.pan_slider = gtk.HScale()
        self.pan_slider.set_adjustment(self.pan_adjustment)
        self.pan_slider.set_sensitive(False)
        
        self.pan_button = gtk.ToggleButton("Pan")
        self.pan_button.connect("toggled", self.pan_active_toggled)

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
        
    def pan_active_toggled(self, widget):
        if widget.get_active():
            self.pan_slider.set_sensitive(True)
        else:
            self.pan_slider.set_sensitive(False)
        
        self.pan_slider.set_value(0.0)
        
        
        
