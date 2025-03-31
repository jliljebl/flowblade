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

import appconsts
import dialogutils

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
    appconsts.KEYFRAME_BOUNCE_IN_OUT]

SMOOTH_EXTENDED_KEYFRAME_TYPES = [ \
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
    appconsts.KEYFRAME_CIRCULAR_IN_OUT]






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
        print(eq_str)
        sides = token.split(eq_str)
        print(sides)
        if len(sides) == 2:
            kf_type = EQ_STRING_TO_TYPE[eq_str]
            print(kf_type)
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

    def get_value(self, frame):
        pass

# ------------------------------------------------ value computation helper funcs
# These all need to be doubles.
def _catmull_rom_interpolate(self, y0, y1, y2, y3, t):
    t2 = t * t
    a0 = -0.5 * y0 + 1.5 * y1 - 1.5 * y2 + 0.5 * y3
    a1 = y0 - 2.5 * y1 + 2 * y2 - 0.5 * y3
    a2 = -0.5 * y0 + 0.5 * y2
    a3 = y1
    return a0 * t * t2 + a1 * t2 + a2 * t + a3

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
