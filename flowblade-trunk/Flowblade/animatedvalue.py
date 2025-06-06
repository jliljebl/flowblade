"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2025 Janne Liljeblad.

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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

from gi.repository import Gtk

import math

import appconsts
import dialogutils


M_PI = math.pi
M_PI_2 = math.pi * 2.0

ease_in = 0
ease_out = 1
ease_inout = 2


KEYFRAME_TYPES = [ \
    appconsts.KEYFRAME_LINEAR,
    appconsts.KEYFRAME_SMOOTH,
    appconsts.KEYFRAME_DISCRETE,
    appconsts.KEYFRAME_SMOOTH_NATURAL,
    appconsts.KEYFRAME_SMOOTH_TIGHT,
    appconsts.KEYFRAME_SINUSOIDAL_IN,
    appconsts.KEYFRAME_SINUSOIDAL_OUT,
    appconsts.KEYFRAME_SINUSOIDAL_IN_OUT,
    appconsts.KEYFRAME_QUADRATIC_IN,
    appconsts.KEYFRAME_QUADRATIC_OUT,
    appconsts.KEYFRAME_QUADRATIC_IN_OUT,
    appconsts.KEYFRAME_CUBIC_IN,
    appconsts.KEYFRAME_CUBIC_OUT,
    appconsts.KEYFRAME_CUBIC_IN_OUT,
    appconsts.KEYFRAME_QUARTIC_IN,
    appconsts.KEYFRAME_QUARTIC_OUT,
    appconsts.KEYFRAME_QUARTIC_IN_OUT,
    appconsts.KEYFRAME_QUINTIC_IN,
    appconsts.KEYFRAME_QUINTIC_OUT,
    appconsts.KEYFRAME_QUINTIC_IN_OUT,
    appconsts.KEYFRAME_EXPONENTIAL_IN,
    appconsts.KEYFRAME_EXPONENTIAL_OUT,
    appconsts.KEYFRAME_EXPONENTIAL_IN_OUT,
    appconsts.KEYFRAME_CIRCULAR_IN,
    appconsts.KEYFRAME_CIRCULAR_OUT,
    appconsts.KEYFRAME_CIRCULAR_IN_OUT,
    appconsts.KEYFRAME_BACK_IN,
    appconsts.KEYFRAME_BACK_OUT,
    appconsts.KEYFRAME_BACK_IN_OUT,
    appconsts.KEYFRAME_ELASTIC_IN,
    appconsts.KEYFRAME_ELASTIC_OUT,
    appconsts.KEYFRAME_ELASTIC_IN_OUT,
    appconsts.KEYFRAME_BOUNCE_IN,
    appconsts.KEYFRAME_BOUNCE_OUT,
    appconsts.KEYFRAME_BOUNCE_IN_OUT]

KEYFRAME_EQ_STRS = [ \
    appconsts.KEYFRAME_LINEAR_EQUALS_STR, 
    appconsts.KEYFRAME_SMOOTH_EQUALS_STR,
    appconsts.KEYFRAME_DISCRETE_EQUALS_STR, 
    appconsts.KEYFRAME_SMOOTH_NATURAL_EQUALS_STR, 
    appconsts.KEYFRAME_SMOOTH_TIGHT_EQUALS_STR,
    appconsts.KEYFRAME_SINUSOIDAL_IN_EQUALS_STR, 
    appconsts.KEYFRAME_SINUSOIDAL_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_SINUSOIDAL_IN_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_QUADRATIC_IN_EQUALS_STR, 
    appconsts.KEYFRAME_QUADRATIC_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_QUADRATIC_IN_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_CUBIC_IN_EQUALS_STR, 
    appconsts.KEYFRAME_CUBIC_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_CUBIC_IN_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_QUARTIC_IN_EQUALS_STR, 
    appconsts.KEYFRAME_QUARTIC_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_QUARTIC_IN_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_QUINTIC_IN_EQUALS_STR, 
    appconsts.KEYFRAME_QUINTIC_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_QUINTIC_IN_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_EXPONENTIAL_IN_EQUALS_STR, 
    appconsts.KEYFRAME_EXPONENTIAL_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_EXPONENTIAL_IN_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_CIRCULAR_IN_EQUALS_STR, 
    appconsts.KEYFRAME_CIRCULAR_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_CIRCULAR_IN_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_BACK_IN_EQUALS_STR, 
    appconsts.KEYFRAME_BACK_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_BACK_IN_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_ELASTIC_IN_EQUALS_STR, 
    appconsts.KEYFRAME_ELASTIC_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_ELASTIC_IN_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_BOUNCE_IN_EQUALS_STR, 
    appconsts.KEYFRAME_BOUNCE_OUT_EQUALS_STR, 
    appconsts.KEYFRAME_BOUNCE_IN_OUT_EQUALS_STR]

EFFECT_KEYFRAME_TYPES = [ \
    appconsts.KEYFRAME_BACK_IN,
    appconsts.KEYFRAME_BACK_OUT,
    appconsts.KEYFRAME_BACK_IN_OUT,
    appconsts.KEYFRAME_ELASTIC_IN,
    appconsts.KEYFRAME_ELASTIC_OUT,
    appconsts.KEYFRAME_ELASTIC_IN_OUT,
    appconsts.KEYFRAME_BOUNCE_IN,
    appconsts.KEYFRAME_BOUNCE_OUT,
    appconsts.KEYFRAME_BOUNCE_IN_OUT,
    appconsts.KEYFRAME_SINUSOIDAL_IN,
    appconsts.KEYFRAME_SINUSOIDAL_OUT,
    appconsts.KEYFRAME_SINUSOIDAL_IN_OUT,]

SMOOTH_EXTENDED_KEYFRAME_TYPES = [ \
    appconsts.KEYFRAME_SMOOTH_NATURAL,
    appconsts.KEYFRAME_SMOOTH_TIGHT,
    appconsts.KEYFRAME_QUADRATIC_IN,
    appconsts.KEYFRAME_QUADRATIC_OUT,
    appconsts.KEYFRAME_QUADRATIC_IN_OUT,
    appconsts.KEYFRAME_CUBIC_IN,
    appconsts.KEYFRAME_CUBIC_OUT,
    appconsts.KEYFRAME_CUBIC_IN_OUT,
    appconsts.KEYFRAME_QUARTIC_IN,
    appconsts.KEYFRAME_QUARTIC_OUT,
    appconsts.KEYFRAME_QUARTIC_IN_OUT,
    appconsts.KEYFRAME_QUINTIC_IN,
    appconsts.KEYFRAME_QUINTIC_OUT,
    appconsts.KEYFRAME_QUINTIC_IN_OUT,
    appconsts.KEYFRAME_EXPONENTIAL_IN,
    appconsts.KEYFRAME_EXPONENTIAL_OUT,
    appconsts.KEYFRAME_EXPONENTIAL_IN_OUT,
    appconsts.KEYFRAME_CIRCULAR_IN,
    appconsts.KEYFRAME_CIRCULAR_OUT,
    appconsts.KEYFRAME_CIRCULAR_IN_OUT]

CATMILL_ROM_TYPES = [ \
    appconsts.KEYFRAME_SMOOTH,
    appconsts.KEYFRAME_DISCRETE,
    appconsts.KEYFRAME_SMOOTH_NATURAL,
    appconsts.KEYFRAME_SMOOTH_TIGHT]

POWER_TYPES = [ \
    appconsts.KEYFRAME_QUADRATIC_IN,
    appconsts.KEYFRAME_QUADRATIC_OUT,
    appconsts.KEYFRAME_QUADRATIC_IN_OUT,
    appconsts.KEYFRAME_CUBIC_IN,
    appconsts.KEYFRAME_CUBIC_OUT,
    appconsts.KEYFRAME_CUBIC_IN_OUT,
    appconsts.KEYFRAME_QUARTIC_IN,
    appconsts.KEYFRAME_QUARTIC_OUT,
    appconsts.KEYFRAME_QUARTIC_IN_OUT,
    appconsts.KEYFRAME_QUINTIC_IN,
    appconsts.KEYFRAME_QUINTIC_OUT,
    appconsts.KEYFRAME_QUINTIC_IN_OUT]

# Keyframe type -> eq str 
TYPE_TO_EQ_STRING = None # filled on init
# Keyframe type -> eq str 
EQ_STRING_TO_TYPE = None # filled on init
# Keyframe type -> translated name
TYPE_TO_NAME = None  # filled on init


# ------------------------------------------------------- interface
def init():
    global TYPE_TO_EQ_STRING, EQ_STRING_TO_TYPE, TYPE_TO_NAME
    
    TYPE_TO_EQ_STRING = {}
    for type_id, eq_str in zip(KEYFRAME_TYPES, KEYFRAME_EQ_STRS):
        TYPE_TO_EQ_STRING[type_id] = eq_str
     
    EQ_STRING_TO_TYPE = {}
    for type_id, eq_str in zip(KEYFRAME_TYPES, KEYFRAME_EQ_STRS):
        EQ_STRING_TO_TYPE[eq_str] = type_id
    
    
    names = [ \
        _("Linear"),
        _("Smooth"),
        _("Discrete"),
        _("Smooth Natural"),
        _("Smooth Tight"),
        _("Sinusoidal In"),
        _("Sinusoidal Out"),
        _("Sinusoidal In Out"),
        _("Quadratic In"),
        _("Quadratic Out"),
        _("Quadratic In Out"),
        _("Cubic In"),
        _("Cubic Out"),
        _("Cubic In Out"),
        _("Quatic In"),
        _("Quatic Out"),
        _("Quatic In Out"),
        _("Quintic In"),
        _("Quintic Out"),
        _("Quintic In Out"),
        _("Exponenetial In"),
        _("Exponenetial Out"),
        _("Exponenetial In Out"),
        _("Circular In"),
        _("Circular Out"),
        _("Circular In Out"),
        _("Back In"),
        _("Back Out"),
        _("Back In Out"),
        _("Elastic In"),
        _("Elastic Out"),
        _("Elastic In Out"),
        _("Bounce In"),
        _("Bounce Out"),
        _("Bounce In Out")]

    TYPE_TO_NAME = {}
    for type_id, name in zip(KEYFRAME_TYPES, names):
        TYPE_TO_NAME[type_id] = name

def create(keyframes, active_index=0):
    return AnimatedValue(keyframes, active_index=0)

def parse_kf_token(token):
    for eq_str in reversed(KEYFRAME_EQ_STRS):
        sides = token.split(eq_str)
        if len(sides) == 2:
            kf_type = EQ_STRING_TO_TYPE[eq_str]
            return (kf_type, sides)
    
    return (None, None) # we give bad data to crash


# ------------------------------------------------------- AnimatedValue 

class AnimatedValue:
    
    def __init__(self, keyframes, active_index=0):
        self.keyframes = keyframes
        self.active_kf_index = active_index
    
    def get_state(self):
        """
        Called after actions to get results.
        """
        return (self.keyframes, self.active_index)
    
    def add_keyframe(self, frame, value, kf_type):
        kf_index_on_frame = self.frame_has_keyframe(frame)
        if kf_index_on_frame != -1:
            # Trying add on top of existing keyframe makes it active
            self.active_kf_index = kf_index_on_frame
            return

        # Insert if not after last
        for i in range(0, len(self.keyframes)):
            kf_frame, kf_value, kf_type = self.keyframes[i]
            if kf_frame > frame:
                #prev_frame, prev_value = self.keyframes[i - 1]
                self.keyframes.insert(i, (frame, value, kf_type))
                self.active_kf_index = i
                return
        
        # Append
        self.keyframes.append((frame, value, kf_type))
        self.active_kf_index = len(self.keyframes) - 1

    def delete_active_keyframe(self):
        if self.active_kf_index == 0:
            # keyframe frame 0 cannot be removed
            return
        self.keyframes.pop(self.active_kf_index)
        self.active_kf_index -= 1
        if self.active_kf_index < 0:
            self.active_kf_index = 0

    def frame_has_keyframe(self, frame):
        """
        Returns index of keyframe if frame has keyframe or -1 if it doesn't.
        """
        for i in range(0, len(self.keyframes)):
            kf_frame, kf_value, kf_type = self.keyframes[i]
            if frame == kf_frame:
                return i

        return -1
    
    def get_interpolated_value_internal_kf_type(self, i, fract):
        frame, val, interpolated_kf_type = self.keyframes[i]
        return self.get_interpolated_value(i, fract, interpolated_kf_type)
    
    def get_interpolated_value(self, i, fract, interpolated_kf_type):
        # Get indexes of the four keyframes that affect the drawn curve. 
        prev = i
        if i == 0:
            prev_prev = 0
        else:
            prev_prev = i - 1
        
        next = i + 1
        if next >= len(self.keyframes):
            next = len(self.keyframes) - 1
        
        next_next = next + 1
        if next_next >= len(self.keyframes):
            next_next = len(self.keyframes) - 1

        if interpolated_kf_type == appconsts.KEYFRAME_DISCRETE:
            frame, value, kf_type = self.keyframes[prev]
            return value
        elif interpolated_kf_type == appconsts.KEYFRAME_LINEAR:
            frame, value, kf_type = self.keyframes[prev]
            if prev == next:
                return value
            frame_next, value_next, kf_type_next = self.keyframes[next]
            return value + (value_next - value) * fract
        else:
            return self.get_smooth_fract_value(prev_prev, prev, next, next_next, fract, interpolated_kf_type)
 
    def get_smooth_fract_value(self, prev_prev, prev, next, next_next, fract, interpolated_kf_type):
        frame, val0, kf_type = self.keyframes[prev_prev]
        frame, val1, kf_type = self.keyframes[prev]
        frame, val2, kf_type = self.keyframes[next]
        frame, val3, kf_type = self.keyframes[next_next]

        if interpolated_kf_type in CATMILL_ROM_TYPES:
            return _catmull_rom_interpolate(val0, val1, val2, val3, fract)
        elif interpolated_kf_type in POWER_TYPES:
            intepolation_func, ease_type, order = RP_POWER_FUNCS[interpolated_kf_type]
            return intepolation_func(val1, val2, fract, order, ease_type)
        else:
            intepolation_func, ease_type = RP_EASING_FUNCS[interpolated_kf_type]
            return intepolation_func(val1, val2, fract, ease_type)


# ------------------------------------------------ interpolation funcs
# These all need to be doubles.
def _catmull_rom_interpolate(y0, y1, y2, y3, t):
    t2 = t * t
    a0 = -0.5 * y0 + 1.5 * y1 - 1.5 * y2 + 0.5 * y3
    a1 = y0 - 2.5 * y1 + 2 * y2 - 0.5 * y3
    a2 = -0.5 * y0 + 0.5 * y2
    a3 = y1
    return a0 * t * t2 + a1 * t2 + a2 * t + a3

def _sinusoidal_interpolate(y1, y2, t, ease):
    factor = 0.0;
    if ease == ease_in:
        factor = math.sin((t - 1.0) * M_PI_2) + 1.0
    elif ease == ease_out:
        factor = math.sin(t * M_PI_2)
    else:
        factor = 0.5 * (1.0 - math.cos(t * M_PI))

    return y1 + (y2 - y1) * factor

def _exponential_interpolate(y1, y2, t, ease):
    factor = 0.0
    if (t == 0.0):
        factor = 0
    elif (t == 1.0):
        factor = 1.0
    elif (ease == ease_in):
        factor = math.pow(2.0, 10.0 * t - 10.0)
    elif (ease == ease_out):
        factor = 1.0 - math.pow(2.0, -10.0 * t)
    else: # ease_inout
        if (t < 0.5):
            factor = math.pow(2.0, 20.0 * t - 10.0) / 2.0;
        else:
            factor = (2.0 - pow(2.0, -20.0 * t + 10.0)) / 2.0;

    return y1 + (y2 - y1) * factor

def _power_interpolate(y1, y2, t, order, ease):
    factor = 0.0;
    if (ease == ease_in):
        factor = math.pow(t, order)
    elif (ease == ease_out):
        factor = 1.0 - math.pow(1.0 - t, order)
    else: # ease_inout
        if (t < 0.5):
            factor = math.pow(2.0, order) * pow(t, order) / 2.0
        else:
            factor = 1.0 - math.pow(-2.0 * t + 2.0, order) / 2.0

    return y1 + (y2 - y1) * factor

def _bounce_interpolate(y1, y2, t, ease):
    factor = 0.0
    if (ease == ease_in):
        factor = 1.0 - _bounce_interpolate(0.0, 1.0, 1.0 - t, ease_out)
    elif (ease == ease_out):
        if (t < 4.0 / 11.0):
            factor = (121.0 * t * t) / 16.0
        elif (t < 8.0 / 11.0):
            factor = (363.0 / 40.0 * t * t) - (99.0 / 10.0 * t) + 17.0 / 5.0
        elif (t < 9.0 / 10.0):
            factor = (4356.0 / 361.0 * t * t) - (35442.0 / 1805.0 * t) + 16061.0 / 1805.0
        else:
            factor = (54.0 / 5.0 * t * t) - (513.0 / 25.0 * t) + 268.0 / 25.0
    else: # { // ease_inout
        if (t < 0.5):
            factor = 0.5 * _bounce_interpolate(0.0, 1.0, t * 2.0, ease_in)
        else:
            factor = 0.5 * _bounce_interpolate(0.0, 1.0, 2.0 * t - 1.0, ease_out) + 0.5

    return y1 + (y2 - y1) * factor

def _elastic_interpolate(y1, y2, t, ease):
    factor = 0.0
    if (ease == ease_in):
        factor = math.sin(13.0 * M_PI_2 * t) * math.pow(2.0, 10.0 * (t - 1.0))
    elif (ease == ease_out):
        factor = math.sin(-13.0 * M_PI_2 * (t + 1.0)) * math.pow(2.0, -10.0 * t) + 1.0
    else: # ease_inout
        if (t < 0.5):
            factor = 0.5 * math.sin(13.0 * M_PI_2 * (2.0 * t)) * math.pow(2.0, 10.0 * ((2.0 * t) - 1.0))
        else:
            factor = 0.5 * (math.sin(-13.0 * M_PI_2 * ((2.0 * t - 1.0) + 1.0)) * math.pow(2.0, -10.0 * (2.0 * t - 1.0)) + 2.0)

    return y1 + (y2 - y1) * factor

def _back_interpolate(y1, y2, t, ease):
    factor = 0.0
    if (ease == ease_in):
        factor = t * t * t - t * math.sin(t * M_PI)
    elif (ease == ease_out):
        f = (1.0 - t)
        factor = 1.0 - (f * f * f - f * math.sin(f * M_PI))
    else:
        if (t < 0.5):
            f = 2.0 * t
            factor = 0.5 * (f * f * f - f * math.sin(f * M_PI))
        else:
            f = (1.0 - (2.0 * t - 1.0))
            factor = 0.5 * (1.0 - (f * f * f - f * math.sin(f * M_PI))) + 0.5

    return y1 + (y2 - y1) * factor

def _circular_interpolate(y1, y2, t, ease):
    factor = 0.0
    if (ease == ease_in):
        factor = 1.0 - math.sqrt(1.0 - math.pow(t, 2.0))
    elif (ease == ease_out):
        factor = math.sqrt(1.0 - math.pow(t - 1.0, 2.0))
    else: 
        if (t < 0.5):
            factor = 0.5 * (1 - math.sqrt(1 - 4 * (t * t)))
        else:
            factor = 0.5 * (math.sqrt(-((2 * t) - 3) * ((2 * t) - 1)) + 1)

    return y1 + (y2 - y1) * factor


# ------------------------------------------------ Utility funcs
def set_effect_keyframe_type(current_kf_type, completed_callback):
    
    kf_label = Gtk.Label(label=_("Effect Keyframe Type:"))
    kf_label.set_margin_right(4)

    combo = Gtk.ComboBoxText()
    current_index = 0
    for kf_type in EFFECT_KEYFRAME_TYPES:
        combo.append_text(TYPE_TO_NAME[kf_type])
        if kf_type == current_kf_type:
            current_index = EFFECT_KEYFRAME_TYPES.index(kf_type)
    combo.set_active(current_index)

    data = (combo, completed_callback, True)

    row = Gtk.HBox()
    row.pack_start(kf_label, False, False, 0)
    row.pack_start(combo, False, False, 0)

    panel = Gtk.VBox()
    panel.pack_start(row, False, False, 0)

    dialogutils.panel_ok_cancel_dialog( _("Set Effect Keyframe Type"), panel, _("Set Keyframe Type"), _set_keyframe_type_dialog_callback, data)


def set_smooth_extended_keyframe_type(current_kf_type, completed_callback):
    
    kf_label = Gtk.Label(label=_("Smooth Extended Keyframe Type:"))
    kf_label.set_margin_right(4)

    combo = Gtk.ComboBoxText()
    current_index = 0
    for kf_type in SMOOTH_EXTENDED_KEYFRAME_TYPES:
        combo.append_text(TYPE_TO_NAME[kf_type])
        if kf_type == current_kf_type:
            current_index = SMOOTH_EXTENDED_KEYFRAME_TYPES.index(kf_type)
    combo.set_active(current_index)

    data = (combo, completed_callback, False)

    row = Gtk.HBox()
    row.pack_start(kf_label, False, False, 0)
    row.pack_start(combo, False, False, 0)

    panel = Gtk.VBox()
    panel.pack_start(row, False, False, 0)

    dialogutils.panel_ok_cancel_dialog( _("Set Smooth Extended Keyframe Type"), panel, _("Set Keyframe Type"), _set_keyframe_type_dialog_callback, data)
    
def _set_keyframe_type_dialog_callback(dialog, response_id, data):
    combo, completed_callback, is_effect_kf = data
    if is_effect_kf == True:
        selected_kf_type = EFFECT_KEYFRAME_TYPES[combo.get_active()]
    else:
        selected_kf_type = SMOOTH_EXTENDED_KEYFRAME_TYPES[combo.get_active()]
    
    dialog.destroy()
    
    if response_id == Gtk.ResponseType.ACCEPT:
        completed_callback(selected_kf_type)


RP_EASING_FUNCS = { \
                    appconsts.KEYFRAME_SINUSOIDAL_IN: (_sinusoidal_interpolate, ease_in),
                    appconsts.KEYFRAME_SINUSOIDAL_OUT: (_sinusoidal_interpolate, ease_out),
                    appconsts.KEYFRAME_SINUSOIDAL_IN_OUT: (_sinusoidal_interpolate, ease_inout),
                    appconsts.KEYFRAME_EXPONENTIAL_IN: (_exponential_interpolate, ease_in),
                    appconsts.KEYFRAME_EXPONENTIAL_OUT: (_exponential_interpolate, ease_out),
                    appconsts.KEYFRAME_EXPONENTIAL_IN_OUT: (_exponential_interpolate, ease_inout),
                    appconsts.KEYFRAME_BOUNCE_IN: (_bounce_interpolate, ease_in),
                    appconsts.KEYFRAME_BOUNCE_OUT: (_bounce_interpolate, ease_out),
                    appconsts.KEYFRAME_BOUNCE_IN_OUT: (_bounce_interpolate, ease_inout),
                    appconsts.KEYFRAME_ELASTIC_IN: (_elastic_interpolate, ease_in),
                    appconsts.KEYFRAME_ELASTIC_OUT: (_elastic_interpolate, ease_out),
                    appconsts.KEYFRAME_ELASTIC_IN_OUT: (_elastic_interpolate, ease_inout),
                    appconsts.KEYFRAME_BACK_IN: (_back_interpolate, ease_in),
                    appconsts.KEYFRAME_BACK_OUT: (_back_interpolate, ease_out),
                    appconsts.KEYFRAME_BACK_IN_OUT: (_back_interpolate, ease_inout),
                    appconsts.KEYFRAME_CIRCULAR_IN: (_back_interpolate, ease_in),
                    appconsts.KEYFRAME_CIRCULAR_OUT: (_back_interpolate, ease_out),
                    appconsts.KEYFRAME_CIRCULAR_IN_OUT: (_back_interpolate, ease_inout) } 

RP_POWER_FUNCS = { \
                    appconsts.KEYFRAME_QUADRATIC_IN: (_power_interpolate, ease_in, 2),
                    appconsts.KEYFRAME_QUADRATIC_OUT: (_power_interpolate, ease_out, 2),
                    appconsts.KEYFRAME_QUADRATIC_IN_OUT: (_power_interpolate, ease_inout, 2),
                    appconsts.KEYFRAME_CUBIC_IN: (_power_interpolate, ease_in, 3),
                    appconsts.KEYFRAME_CUBIC_OUT: (_power_interpolate, ease_out, 3),
                    appconsts.KEYFRAME_CUBIC_IN_OUT: (_power_interpolate, ease_inout, 3),
                    appconsts.KEYFRAME_QUARTIC_IN: (_power_interpolate, ease_in, 4),
                    appconsts.KEYFRAME_QUARTIC_OUT: (_power_interpolate, ease_out, 4),
                    appconsts.KEYFRAME_QUARTIC_IN_OUT: (_power_interpolate, ease_inout, 4),
                    appconsts.KEYFRAME_QUINTIC_IN: (_power_interpolate, ease_in, 5),
                    appconsts.KEYFRAME_QUINTIC_OUT: (_power_interpolate, ease_out, 5),
                    appconsts.KEYFRAME_QUINTIC_IN_OUT: (_power_interpolate, ease_inout, 5)}
