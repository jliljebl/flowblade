
"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

import utils

NEWLINE = "\n"

NOOP = "noop"
COLOR_TO_HEX_TUPLE = "color_hex_to_tuple"


# --------------------------------------------------------- interface
def get_property_modyfying_str(value, natron_node, natron_property_name, interpretation):
    interpretation_func = INTERPRETATION_FUNCS[interpretation]
    return interpretation_func(value, natron_node, natron_property_name)

# --------------------------------------------------------- module funcs
def _get_modification_target(natron_node, natron_property_name):
    return "app." + natron_node +"." + natron_property_name

# --------------------------------------------------------- interpretations
def _noop(value, natron_node, natron_property_name):
    return _get_modification_target(natron_node, natron_property_name) + ".set(" + value + ")" + NEWLINE


def _color_hex_to_tuple(value, natron_node, natron_property_name):    
    r, g, b = utils.hex_to_rgb(value)
    interpreted_value = ".set(" + str(float(r)/255.0) + ", " + str(float(g)/255.0)  + ", " + str(float(b)/255.0)  + ", 1.0)"
    return _get_modification_target(natron_node, natron_property_name) + interpreted_value + NEWLINE



# interpretation name -> interpretation func
INTERPRETATION_FUNCS = { \
    NOOP:_noop,
    COLOR_TO_HEX_TUPLE:_color_hex_to_tuple}
