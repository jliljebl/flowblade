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

"""
This module handles setting preview to lower then project 
profile screen dimensions for improved playback preformance.

Scaling actions:
- app start: project "preview_scale" set to PREVIEW_SCALE_NONE at creation, UX scaling values set.
- new project: project "preview_scale" set to PREVIEW_SCALE_NONE at creation, UX scaling values set.
- editing: project "preview_scale" set per user requests, UX scaling values set accordingly,
  filter properties scaled for matching output 
- project save: project "preview_scale" set to PREVIEW_SCALE_NONE, filter properties set to unscaled values. 
- project load: project loaded with non-scaled values, "preview_scale", UX and filter properties 
  scaled to user selected scale if preference set.
"""


import traceback

import animatedvalue
import appconsts
from editorstate import PROJECT, PLAYER
import mltprofiles


_scaling_variants = {
    appconsts.PREVIEW_SCALE_NONE: -1,
    appconsts.PREVIEW_SCALE_1080: 1080,
    appconsts.PREVIEW_SCALE_720: 720,
    appconsts.PREVIEW_SCALE_540: 540,
    appconsts.PREVIEW_SCALE_360: 360
}

def set_scale_heights(scaling):
    global _scaled_height, _scaled_width
    _scaled_height = get_scaling_height(scaling)
    if scaling == "noscaling":
        _scaled_width = PROJECT().unscaled_width 
    else:
        _scaled_width = int(PROJECT().unscaled_width  * _scaled_height / PROJECT().unscaled_height)

    print("Set preview_scale:", _scaled_width, _scaled_height)

def set_scaling_from_menu(new_value_variant):
    set_scaling(new_value_variant.get_string())

def set_scaling(scaling):
    if PROJECT().preview_scale == scaling:
        return
    
    old_scaled_height = get_scaling_height(PROJECT().preview_scale)
    
    PROJECT().preview_scale = scaling
    set_scale_heights(scaling)

    PLAYER().stop_consumer()

    scale_filter_parameters(PROJECT(), old_scaled_height, _scaled_height)

    PROJECT().profile.set_width(_scaled_width)
    PROJECT().profile.set_height(_scaled_height)


    PLAYER().consumer.set("width", _scaled_width)
    PLAYER().consumer.set("height",_scaled_height)
    PLAYER().start_consumer()

def get_scaling_height(scaling):
    h = _scaling_variants[scaling]
    if h == -1:
        return PROJECT().unscaled_height
    else:
        return h

def scale():
    return  _scaled_height / PROJECT().unscaled_height
    
def reverse_scale():
    return  PROJECT().unscaled_height / _scaled_height

# --------------------------------------------- convert funcs
def scale_filter_parameters(project, from_height, to_height, scale_mlt=True):
    conv_scale = to_height / from_height
    
    for seq in project.sequences:
        for ti in range(1, len(seq.tracks) - 1): # no bg or hidden trim track.
            track = seq.tracks[ti]
            for clip in track.clips:
                #print(clip.__dict__)
                if clip.is_blanck_clip == True:
                    continue
                for filter_object in clip.filters:
                    f_name = filter_object.info.name
                    for pi in range(0, len(filter_object.properties)):
                        p_name, p_value, p_type = filter_object.properties[pi]
                        try:
                            conv_func = PREVIEW_SCALING_FUNCS[(f_name, p_name)]
                            #print(f_name, p_name)
                            #print("pre", p_value)
                            p_value = conv_func(p_value, conv_scale)
                            #print("post", p_value)
                            filter_object.properties[pi] = (p_name, str(p_value), p_type)
                            if scale_mlt == True:
                                filter_object.mlt_filter.set(str(p_name), str(p_value))
                        except:
                            #traceback.print_exc()
                            #print("pass")
                            pass

def _Position_Scale_Rotate_transition_rect(keyframes_str, conv_scale):
    keyframes_str = keyframes_str.strip('"') # expressions have sometimes quotes that need to go away
    new_keyframes_str = ""
    kf_tokens =  keyframes_str.split(';')
    for token in kf_tokens:
        frame, value, kf_type = get_token_frame_value_type(token)

        values = value.split(' ')
        eq_str = animatedvalue.TYPE_TO_EQ_STRING[kf_type]
        new_value = frame + eq_str
        x = str(float(values[0]) * conv_scale)
        y = str(float(values[1]) * conv_scale)
        x_scale = str(float(values[2]) * conv_scale)
        y_scale = str(float(values[3]) * conv_scale)
        new_value += x + " " + y + " " + x_scale  + " " + y_scale + ";"

        new_keyframes_str += new_value
    
    new_keyframes_str = new_keyframes_str.strip(";")
    return new_keyframes_str

def get_token_frame_value_type(token):
    kf_type, sides = animatedvalue.parse_kf_token(token)

    # returns (frame, value, kf_type)
    return(sides[0], sides[1], kf_type)
    
    
PREVIEW_SCALING_FUNCS = { \
    ("Position Scale Rotate", "transition.rect"): _Position_Scale_Rotate_transition_rect
}
      