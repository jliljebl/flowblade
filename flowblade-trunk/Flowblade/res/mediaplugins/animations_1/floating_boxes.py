"""
    Copyright 2022 Janne Liljeblad, licenced under GPL3. 
    See  <http://www.gnu.org/licenses/> for licence text.
"""

import cairo
import numpy as np
import random

import fluxity

MONDRIAN = [(0.18, 0.274, 0.477), (1.0, 1.0, 1.0), (0.968, 0.793, 0.0), (0.051, 0.505, 0.725), 
            (0.913, 0.0, 0.0), (0.0, 0.0, 0.0)]

PASTELS = [(0.38, 0.59, 0.83), (0.82, 0.48, 0.53), (0.48, 0.82, 0.60), (0.82, 0.65, 0.48), 
            (0.82, 0.82, 0.48), (0.80, 0.48, 0.82)]

NEON = [(0.816, 0.169, 0.576), (0.929, 0.290, 0.953), (0.976, 0.976, 0.224), 
        (0.141, 0.157, 0.51), (0.345, 0.847, 0.937), (0.745, 0.898, 0.961)]

EARTHY = [(0.38, 0.463, 0.294), (0.812, 0.725, 0.592), (0.608, 0.631, 0.482), 
          (0.224, 0.318, 0.267), (0.306, 0.424, 0.314), (0.667, 0.545, 0.337)]

LIGHT = [(0.894, 0.576, 0.576), (0.941, 0.922, 0.553), (0.976, 0.961, 0.922),
         (0.894, 0.863, 0.812), (0.918, 0.329, 0.333), (0.02, 0.169, 0.357)]

COLORS_LIST = [PASTELS, LIGHT, EARTHY, NEON, MONDRIAN]

NUMBER_OF_HUES = 10

def init_script(fctx):
    fctx.set_name("Floating Boxes")
    fctx.set_version(1)
    fctx.set_author("Janne Liljeblad")

    fctx.add_editor("Colors", fluxity.EDITOR_OPTIONS, (0,["User Hue", "Pastels", "Light", "Earthy", "Neon", "Mondrian"]))
    fctx.add_editor("Hue", fluxity.EDITOR_COLOR, (0.8, 0.50, 0.3, 1.0))
    fctx.add_editor("Color Variation", fluxity.EDITOR_INT_RANGE, (4, 0, 20))
    fctx.add_editor("Speed", fluxity.EDITOR_FLOAT_RANGE, (0.09, -5.0, 5.0))
    fctx.add_editor("Number of Items", fluxity.EDITOR_INT_RANGE, (120, 10, 500))
    fctx.add_editor("Size", fluxity.EDITOR_INT_RANGE, (600, 10, 800))
    fctx.add_editor("Size Variation %", fluxity.EDITOR_INT_RANGE, (70, 0, 80))
    fctx.add_editor("Opacity", fluxity.EDITOR_INT_RANGE, (100, 5, 100))
    fctx.add_editor("Shadow Offset", fluxity.EDITOR_INT_RANGE, (40, 1, 50))
    fctx.add_editor("Shadow Opacity", fluxity.EDITOR_INT_RANGE, (10, 0, 100))
    fctx.add_editor("Random Seed", fluxity.EDITOR_INT, 42)
    
def init_render(fctx):
    # The script is usually rendered using multiple prosesses so we need to have the
    # same sequence of random numbers in all processes.
    random.seed(fctx.get_editor_value("Random Seed"))

    # Items colors data structure
    hue = fctx.get_editor_value("Hue")
    color_variation = fctx.get_editor_value("Color Variation")
    hr, hg, hb, alpha = hue
    fctx.set_data_obj("hue_tuple", hue)
    color_array = list(hue)
    item_colors = []
    color_mult = 1.0 + float(color_variation) / 100.0
    opacity = float(fctx.get_editor_value("Opacity")) / 100.0

    colors = fctx.get_editor_value("Colors")

    # Draw bg
    if colors == 0:
        for i in range(0, NUMBER_OF_HUES):
            array = np.array(color_array) * color_mult
            r, g, b, a = array
            item_colors.append(cairo.SolidPattern(_clamp(r), _clamp(g), _clamp(b), opacity))
            color_array = array
    else:
        palette = COLORS_LIST[colors - 1]
        for i in range(0, len(palette)):
            palette_hue = palette[i]
            color_array = list(palette_hue)
            hue_colors = []
            for j in range(0, 10):
                array = np.array(color_array) * color_mult
                r, g, b = array
                hue_colors.append(cairo.SolidPattern(_clamp(r), _clamp(g), _clamp(b), opacity))
                color_array = array
            item_colors.append(hue_colors)
    
    fctx.set_data_obj("item_colors", item_colors)

    # Animations data structure
    item_data = []
    number_of_items = fctx.get_editor_value("Number of Items")
    speed = fctx.get_editor_value("Speed")
    size = fctx.get_editor_value("Size")
    size_var_size_precentage = fctx.get_editor_value("Size Variation %")
    size_var_max = size * (size_var_size_precentage / 100.0)
    size_max = size + size_var_max
    fctx.set_data_obj("size_max", size_max)

    for i in range(0, number_of_items):
        path_pos = random.uniform(0.0, 1.0)
        y = random.randint(-330, 1080 + 330)

        size_var = random.uniform(-1.0, 1.0)
        item_size = size + (size_var * size_var_max)
        color_index = random.randint(0, NUMBER_OF_HUES - 1)
        # For palette colors we think of all hues being in single list.
        if colors != 0:
            hue_index = random.randint(0, len(palette) - 1)
            color_index = hue_index * NUMBER_OF_HUES + color_index
        item_data.append((path_pos, y, speed, item_size, color_index))

    data_sorted = sorted(item_data, key=lambda item: item[3])

    fctx.set_data_obj("item_data", data_sorted)

def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    colors = fctx.get_editor_value("Colors")

    # Draw bg
    if colors == 0:
        bg_color = cairo.SolidPattern(*fctx.get_data_obj("hue_tuple"))
    else:
        palette = COLORS_LIST[colors - 1]
        bg_color = cairo.SolidPattern(*palette[0])
    cr.set_source(bg_color)
    cr.rectangle(0, 0, w, h)
    cr.fill()

    item_colors = fctx.get_data_obj("item_colors")
    item_data = fctx.get_data_obj("item_data")

    shadow_offset = fctx.get_editor_value("Shadow Offset")
    shadow_opacity = float(fctx.get_editor_value("Shadow Opacity")) / 100.0

    screen_height = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)

    # Draw items
    number_of_items = fctx.get_editor_value("Number of Items")
    size_max = fctx.get_data_obj("size_max")
    path_start_x = - size_max
    path_end_x =  w + size_max
    path_len = path_end_x - path_start_x
    SPEED_NORM_PER_FRAME = 15.0 / float(w) # Speed value 1.0 gets 15 pixels of movement per frame.
    for i in range(0, number_of_items):
        path_pos, y, item_speed, item_size, color_index = item_data[i]
        xc = item_size / 2.0
        yc = item_size / 2.0
        xpos_norm = path_pos + (float(frame) * item_speed * SPEED_NORM_PER_FRAME)
        while xpos_norm > 1.0:
            xpos_norm = xpos_norm - 1.0
        x = path_start_x + path_len * xpos_norm

        cr.save()
        cr.translate(x + shadow_offset, y)
        cr.rectangle(0, 0, xc, screen_height)
        cr.set_source(cairo.SolidPattern(0,0,0, shadow_opacity))
        cr.fill()
        cr.restore()

        cr.save()
        cr.translate(x, y)
        cr.rectangle(0, 0, xc, screen_height)
        if colors == 0:
            draw_color = item_colors[color_index]
        else:
            palette_color_index = color_index // NUMBER_OF_HUES
            hue_index = color_index % NUMBER_OF_HUES
            palette_color_hues = item_colors[palette_color_index]
            draw_color = palette_color_hues[hue_index]

        cr.set_source(draw_color)
        cr.fill()
        cr.restore()

# ----------------------- helper func
def _clamp(v):
    return max(min(v, 1.0), 0.0)

