"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2026 Janne Liljeblad.

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

import appconsts
from editorstate import PROJECT, PLAYER
import mltprofiles

_scaling_variants = {
    "noscaling": -1,
    "scaling1080": 1080,
    "scaling720": 720,
    "scaling540": 540,
    "scaling360": 360
}

def set_scaling_from_menu(new_value_variant):
    set_scaling(new_value_variant.get_string())

def set_scaling(scaling):
    PROJECT().preview_scaling = scaling

    global _scaled_height, _scaled_width
    _scaled_height = _scaling_variants[scaling]
    if _scaled_height == -1:
        _scaled_height = PROJECT().unscaled_height
        _scaled_width = PROJECT().unscaled_width 
    else:
        _scaled_width = int(PROJECT().unscaled_width  * _scaled_height / PROJECT().unscaled_height)

    print("Set preview_scale:", _scaled_width, _scaled_height)

    PROJECT().profile.set_width(_scaled_width)
    PROJECT().profile.set_height(_scaled_height)

    PLAYER().stop_consumer()
    PLAYER().consumer.set("width", _scaled_width)
    PLAYER().consumer.set("height",_scaled_height)
    PLAYER().start_consumer()

def get_scaled_height(scaling):
    return _scaling_variants[scaling]



#self.consumer.set("width", int(self.profile.width() / 2.0))
#self.consumer.set("height", int(self.profile.height() / 2.0))