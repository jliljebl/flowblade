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

import sys

from cairoarea import CairoDrawableArea
import utils

CHANNEL_METERS_AREA_HEIGHT = 300 
CHANNEL_METERS_AREA_WIDTH = 300

METER_HEIGHT = 290
METER_WIDTH = 10

DASH_INK = 6.0
DASH_SKIP = 2.0
DASHES = [DASH_INK, DASH_SKIP, DASH_INK, DASH_SKIP]

# These are calculated using IEC_Scale function in MLT
DB_IEC_MINUS_2 = 0.95
DB_IEC_MINUS_4 = 0.9
DB_IEC_MINUS_6 = 0.85
DB_IEC_MINUS_10 = 0.75

PEAK_FRAMES = 5

RED_1 = (0, 1, 0, 0, 1)
RED_2 = (1 - DB_IEC_MINUS_2, 1, 0, 0, 1)
YELLOW_1 = (1 - DB_IEC_MINUS_2 + 0.001, 1, 1, 0, 1)
YELLOW_2 = (1 - DB_IEC_MINUS_6, 1, 1, 0, 1)
GREEN_1 = (1 - DB_IEC_MINUS_6 + 0.001, 0, 1, 0, 1)
GREEN_2 = (1, 0, 1, 0, 1)
        

MONITORING_AVAILABLE = False

_monitor_window = None
_update_ticker = None
_producer = None
 
def init():
    audio_level_filter = mlt.Filter(self.profile, "audiolevel")
    print DB_IEC_MINUS_2, DB_IEC_MINUS_6

    global MONITORING_AVAILABLE
    if audio_level_filter != None:
        MONITORING_AVAILABLE = True
    else:
        MONITORING_AVAILABLE = False
    
def add_audio_level_filter(producer, profile):
    audio_level_filter = mlt.Filter(profile, "audiolevel")
    producer.attach(audio_level_filter)
    producer.audio_level_filter = audio_level_filter
    global _producer
    _producer = producer
    
def remove_audio_level_filter(producer, profile):
    producer.detach(producer.audio_level_filter)
    producer.audio_level_filter = None

def start_monitoring():
    red = DB_IEC_MINUS_4
    yellow = DB_IEC_MINUS_10

    global _monitor_window
    _monitor_window = AudioMonitorWindow()
        
    global _update_ticker
    _update_ticker = utils.Ticker(_audio_monitor_update, 0.04)
    _update_ticker.start_ticker()

def _audio_monitor_update():
    level_value = _producer.audio_level_filter.get("_audio_level.1")
    if level_value == None:
        level_value  = "0.0"

    try:
        level_float = float(level_value)
    except Exception, err:
        print err
        level_float = 0.0

    _monitor_window.channel_meters.channel_values[0] = (level_float, level_float)
    _monitor_window.channel_meters.widget.queue_draw()

    """
    level_steps = int(level_float * 20)
    level_str = ''.join(["#" for num in xrange(level_steps)])
    #print level_str
    sys.stdout.write("\r\x1b[K"+level_str.__str__())
    sys.stdout.flush()
    """
    
class AudioMonitorWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        self.channel_meters = ChannelMetersArea(1)

        pane = gtk.VBox(False, 1)
        pane.pack_start(self.channel_meters.widget, True, True, 0)
        
        # Set pane and show window
        self.add(pane)
        self.show_all()

class ChannelMetersArea:
    def __init__(self, channels_count):    
        self.widget = CairoDrawableArea(CHANNEL_METERS_AREA_HEIGHT,
                                        CHANNEL_METERS_AREA_WIDTH, 
                                        self._draw)
        self.channels_count = channels_count
        
        self.channel_values = [] # (l_value, r_value) tuples
        self.channel_meters = [] # displays both l_Value and r_value
        for i in range(0, self.channels_count):
            self.channel_values.append((0.0, 0.0))
            self.channel_meters.append(AudioMeter(METER_HEIGHT))
            
    def _draw(self, event, cr, allocation):
        x, y, w, h = allocation

        cr.set_source_rgb(0,0,0)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        grad = cairo.LinearGradient (0, 0, 0, h)
        grad.add_color_stop_rgba(*RED_1)
        grad.add_color_stop_rgba(*RED_2)
        grad.add_color_stop_rgba(*YELLOW_1)
        grad.add_color_stop_rgba(*YELLOW_2)
        grad.add_color_stop_rgba(*GREEN_1)
        grad.add_color_stop_rgba(*GREEN_2)
        cr.set_source(grad)

        cr.set_dash(DASHES, 0) 
        cr.set_line_width(METER_WIDTH)
        
        for i in range(0, self.channels_count):
            meter = self.channel_meters[i]
            l_value, r_value = self.channel_values[i]
            meter.display_value(cr, 25, l_value)

class AudioMeter:
    def __init__(self, height):
        self.height = height
        self.peak = 0.0
        self.countdown = 0

    def display_value(self, cr, x, value):
        top = self.get_meter_y_for_value(value)
        
        cr.move_to(x, self.height)
        cr.line_to(x, top)
        cr.stroke()
        
        if value > self.peak:
            self.peak = value
            self.countdown = PEAK_FRAMES
        
        if self.peak > value:
            cr.rectangle(x - METER_WIDTH / 2, 
                         self.get_meter_y_for_value(self.peak) + DASH_SKIP,
                         METER_WIDTH,
                         DASH_INK)
            cr.fill()

        self.countdown = self.countdown - 1
        if self.countdown <= 0:
             self.peak = 0

    def get_meter_y_for_value(self, value):
        y = self.height -  (value * self.height)
        dash_sharp_pad = (self.height - y) % (DASH_INK + DASH_SKIP)
        return y + dash_sharp_pad
