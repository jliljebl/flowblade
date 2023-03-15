"""
    Copyright 2022 Janne Liljeblad, licenced under GPL3. 
    See  <http://www.gnu.org/licenses/> for licence text.
"""

import cairo
import numpy as np

import fluxity

MONDRIAN = [(0.18, 0.274, 0.477), (1.0, 1.0, 1.0), (0.968, 0.793, 0.0), (0.051, 0.505, 0.725), 
            (0.913, 0.0, 0.0), (0.0, 0.0, 0.0)]

PASTELS = [(0.38, 0.59, 0.83), (0.82, 0.48, 0.53), (0.48, 0.82, 0.60), (0.82, 0.65, 0.48), 
            (0.82, 0.82, 0.48), (0.80, 0.48, 0.82)]
            
USER_HUE_MULTIPLIERS = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3]


def init_script(fctx):
    fctx.set_name("Lines Sweep")
    fctx.set_version(1)
    fctx.set_author("Janne Liljeblad")
 
    fctx.add_editor("Colors", fluxity.EDITOR_OPTIONS, (0,["User Hue", "Mondrian", "Pastels"]))
    fctx.add_editor("User Hue", fluxity.EDITOR_COLOR, (0.8, 0.50, 0.3, 1.0))
    fctx.add_editor("Speed", fluxity.EDITOR_FLOAT_RANGE, (1.0, -5.0, 5.0))
    fctx.add_editor("Direction", fluxity. EDITOR_OPTIONS, (0,["Left To Right", "Right To Left"]))
    
    # This is hand tuned to get quaranteed 1 frame full coverage.
    # (width, path_len_mult, start_pos_off, end_pos_off, color_index)
    global lines_data
    lines_data = [  (0.1, 0.1, 0.7, 0.2, 0),
                    (0.2, 0.2, 1.8, 0.0, 1),
                    (0.3, 0.33, 3.24, 0.1, 2),
                    (0.15, 0.4, 0.1, 5.2, 3),
                    (0.22, 0.2, 0.2, 1.1, 5),
                    (0.18, 0.5, 0.1, 2.8, 4)]
   
def init_render(fctx):
    # Create user colors 
    user_hue = fctx.get_editor_value("User Hue")
    color_array = list(user_hue)
    user_colors = []

    for i in range(0, 6):
        color_mult = USER_HUE_MULTIPLIERS[i]
        array = np.array(color_array) * color_mult
        r, g, b , a= array
        user_colors.append((_clamp(r), _clamp(g), _clamp(b)))

    fctx.set_data_obj("colors_lists",  [user_colors, MONDRIAN, PASTELS])
    
def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    line_colors = fctx.get_editor_value("Line Colors")
    selected_colors = fctx.get_data_obj("colors_lists")[line_colors]
    user_hue = fctx.get_editor_value("User Hue")
    speed = fctx.get_editor_value("Speed")
    direction = fctx.get_editor_value("Direction")

    anim_length = 31 # make user settable
    for i in range(0, len(lines_data)):
        line_data = lines_data[i]
        width, path_len_mult,  start_pos_off, end_pos_off, color_index = line_data
        
        # More start_pos_off or path_len_mult or end_pos_off creates faster movement.
        # More start_pos_off makes line appear towards start at cover frame.
        # More end_pos_off makes line appear towards end at cover frame. 
        start_pos = -(w * width * path_len_mult) - (w * width) - (w * width * start_pos_off) 
        end_pos = w + (w * width * path_len_mult) + (w * width * end_pos_off)
        path_pos = float(frame) / float(anim_length)
        pos = start_pos + float(end_pos - start_pos) * path_pos

        color_tuple = selected_colors[color_index]
        color = cairo.SolidPattern(*color_tuple)
        
        cr.set_source(color)
        cr.rectangle(pos, 0, width * w, h)
        cr.fill()

# ----------------------- helper func
def _clamp(v):
    return max(min(v, 1.0), 0.0)

