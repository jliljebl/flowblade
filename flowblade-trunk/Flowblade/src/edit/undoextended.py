"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

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
Undo objects for multiproperty editors requiring specialized code to 
handle undo/redos.
"""


import undo


class ColorGraderUndo(undo.PropertyEditAction):
    
        def __init__(self, editor):
            undo.PropertyEditAction.__init__(self, self.undo_value_set_func, "")
            self.editor = editor

        def set_undo_val(self):
            hue, sat = self._get_hue_and_sat(self.editor.band)
            self.undo_val = self._get_value_str(self.editor.band, hue, sat) 
        
        def set_redo_val(self):
            hue, sat = self._get_hue_and_sat(self.editor.band)
            redo_val = self._get_value_str(self.editor.band, hue, sat) 
            self.edit_done(redo_val)
            
        def _get_hue_and_sat(self, band):
            if band == self.editor.SHADOW:
                hue = self.editor.shadow_hue.value
                sat = self.editor.shadow_saturation.value
            elif band == self.editor.MID:
                hue = self.editor.mid_hue.value
                sat = self.editor.mid_saturation.value
            else:
                hue = self.editor.hi_hue.value
                sat = self.editor.hi_saturation.value
            
            return (hue, sat)
    
        def _get_value_str(self, band, hue, sat):
            return str(band) + ":" + hue + ":" + sat 
    
        def undo_value_set_func(self, str_value):
            tokens = str_value.split(":")
            band = int(tokens[0])
            hue = float(tokens[1])
            sat = float(tokens[2])
        
            self.editor.undo_redo_update(band, hue, sat)


class ColorCurveUndo(undo.PropertyEditAction):
        
        RGB = 0
        R = 1
        G = 2
        B = 3


        def __init__(self, editor):
            undo.PropertyEditAction.__init__(self, self.undo_value_set_func, "")
            self.editor = editor

        def set_undo_val(self):
            channel = self.editor.current_edit_curve
            points_str = self.editor.curve_editor.curve.get_old_points_string()
            self.undo_val = self._get_val_str(channel, points_str)

        def set_redo_val(self):
            channel = self.editor.current_edit_curve
            points_str = self.editor.curve_editor.curve.get_points_string()
            redo_val = self._get_val_str(channel, points_str)
            self.edit_done(redo_val)

        def _get_val_str(self, channel, points_str):
            return str(channel) + ":" + points_str

        def undo_value_set_func(self, str_value):
            tokens = str_value.split(":")
            channel = int(tokens[0])
            points_str = tokens[1] 

            self.editor.undo_redo_update(channel, points_str)


