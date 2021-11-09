
import cairo
import numpy as np
import random
import math

cols = -1
rows = -1
shape_width = -1
shape_height = -1

def init_script(fctx):
    fctx.set_name("Hex Colors")
    fctx.set_author("Janne Liljeblad")
    
    fctx.add_editor("Hue", fctx.EDITOR_COLOR, (0.131, 0.0147, 0.163, 1.0))
    fctx.add_editor("Hue Change", fctx.EDITOR_FLOAT_RANGE, (0.5, 0.1, 5.0))
    fctx.add_editor("Speed", fctx.EDITOR_FLOAT_RANGE, (0.5, 0.1, 5.0))
    fctx.add_editor("Size", fctx.EDITOR_FLOAT_RANGE, (50.0, 10.0, 300.0))

    _points = []
    for i in range(0, 6):
        ang = 2 * math.pi * float(i)/ 6.0 + math.pi / 6.0
        _points.append((math.cos(ang), math.sin(ang)))

    fctx.set_data_obj("points", _points)
    
def init_render(fctx):
    hue = fctx.get_editor_value("Hue")
    hr, hg, hb, alpha = hue
    fctx.set_data_obj("hue_tuple", hue)
    size = fctx.get_editor_value("Size")

    global shape_width, shape_height, cols, rows
    shape_width = size * 2.0 * math.cos(math.pi / 6.0)
    shape_height = size + size * math.sin(math.pi / 6.0)
    cols = int(fctx.get_profile_property(fctx.PROFILE_WIDTH) / size + 2)
    rows = int(fctx.get_profile_property(fctx.PROFILE_HEIGHT) / size + 2)
    number_hex = cols * rows

    middle_hues = []
    color_positions = []
    deltas = []
    delta_size = 0.03 * fctx.get_editor_value("Speed")
    hue_change_size = 0.1 * fctx.get_editor_value("Hue Change")

    for i in range(0, number_hex):
        color_positions.append(random.uniform(-1.0, 1.0))
        color_add = random.uniform(-1.0, 1.0) * hue_change_size
        middle_hues.append((_clamp(hr + color_add), _clamp(hg + color_add), _clamp(hb + color_add)))
        d = delta_size if random.uniform(-1.0, 1.0) > 0.0 else -delta_size
        deltas.append(d)

    fctx.set_data_obj("middle_hues", middle_hues)
    fctx.set_data_obj("color_positions", color_positions)
    fctx.set_data_obj("deltas", deltas)

def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    bg_color = cairo.SolidPattern(*fctx.get_data_obj("hue_tuple"))
    color_positions = fctx.get_data_obj("color_positions")

    size = fctx.get_editor_value("Size")
    points = fctx.get_data_obj("points")
    middle_hues = fctx.get_data_obj("middle_hues")
    color_positions = fctx.get_data_obj("color_positions")
    deltas = fctx.get_data_obj("deltas")

    x0 = -size / 2.0
    y0 = -size / 2.0
    hue_change_anim_range = 0.1 * fctx.get_editor_value("Hue Change Amount")
    
    cr.set_source(bg_color)
    cr.rectangle(0, 0, w, h)
    cr.fill()

    for row in range(0, rows):
        yt = y0 + shape_height * row
        x_row = x0 + shape_width / 2.0  * (float(row) % 2.0)
        for col in range(0, cols):
            index = row * cols + col
            
            # get color for hex
            r, g, b = middle_hues[index]
            color_position = color_positions[index]
            delta = deltas[index]
            r = _clamp( r + color_position * hue_change_anim_range)
            g = _clamp( g + color_position * hue_change_anim_range)
            b = _clamp( b + color_position * hue_change_anim_range)
            
            # animate color
            color_position = color_position + delta
            color_positions[index] = color_position
            if abs(color_position) > 1.0:
                delta = -delta
                deltas[index] = delta
                
            # draw hex
            xt = x_row + shape_width * col
            cr.save()
            cr.translate(xt, yt)
            
            x, y = _point_mult(size, *points[0])
            cr.move_to(x, y)
            for i in range(1, 6):
                x, y = _point_mult(size, *points[i])
                cr.line_to(x, y)
            cr.close_path() 
            
            cr.set_source_rgb(r,g,b)
            cr.fill()
            cr.restore()
    

# ----------------------- helper func
def _clamp(v):
    return max(min(v, 1.0), 0.0)
    
def _point_mult(size, x, y):
    return (size * x, size * y)

