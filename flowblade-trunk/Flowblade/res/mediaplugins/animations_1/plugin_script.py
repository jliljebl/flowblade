
import cairo
import numpy as np
import random
import math

# ----------------------- fluxity funcs
def init_script(fctx):
    fctx.set_name("Floating Balls")
    fctx.set_author("Janne Liljeblad")
    
    fctx.add_editor("Hue", fctx.EDITOR_COLOR, (0.8, 0.50, 0.3, 1.0))
    fctx.add_editor("Speed", fctx.EDITOR_FLOAT_RANGE, (1.0, -5.0, 5.0))
    fctx.add_editor("Speed Variation %", fctx.EDITOR_INT_RANGE, (40, 0, 99))
    fctx.add_editor("Number of Items", fctx.EDITOR_INT_RANGE, (50, 10, 500))
    fctx.add_editor("Size", fctx.EDITOR_INT_RANGE, (330, 10, 800))
    fctx.add_editor("Size Variation %", fctx.EDITOR_INT_RANGE, (0, 0, 80))
    fctx.add_editor("Opacity", fctx.EDITOR_INT_RANGE, (100, 5, 100))

def init_render(fctx):
    hue = fctx.get_editor_value("Hue")
    hr, hg, hb, alpha = hue
    fctx.set_data_obj("hue_tuple", hue)
    color_array = list(hue)
    ball_colors = []
    color_mult = 1.05
    opacity = float(fctx.get_editor_value("Opacity")) / 100.0

    for i in range(0, 10):
        array = np.array(color_array) * color_mult
        r, g, b, a = array
        ball_colors.append(cairo.SolidPattern(_clamp(r), _clamp(g), _clamp(b), opacity))
        color_array = array
    fctx.set_data_obj("ball_colors", ball_colors)

    ball_data = []
    number_of_balls = fctx.get_editor_value("Number of Items")
    speed = fctx.get_editor_value("Speed")
    speed_var_size_precentage = fctx.get_editor_value("Speed Variation %")
    speed_var_max = speed * (speed_var_size_precentage  / 100.0)
    size = fctx.get_editor_value("Size")
    size_var_size_precentage = fctx.get_editor_value("Size Variation %")
    size_var_max = size * (size_var_size_precentage / 100.0)
    size_max = size + size_var_max
    fctx.set_data_obj("size_max", size_max)

    for i in range(0, number_of_balls):
        path_pos = random.uniform(0.0, 1.0)
        y = random.randint(-330, 1080 + 330)
        speed_var = random.uniform(-1.0, 1.0)

        ball_speed = speed + (speed_var * speed_var_max)
        size_var = random.uniform(-1.0, 1.0)
        ball_size = size + (size_var * size_var_max)
        color_index = random.randint(0, 9)
        ball_data.append((path_pos, y, ball_speed, ball_size, color_index))

    fctx.set_data_obj("ball_data", ball_data)

def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    bg_color = cairo.SolidPattern(*fctx.get_data_obj("hue_tuple"))
    ball_colors = fctx.get_data_obj("ball_colors")
    ball_data = fctx.get_data_obj("ball_data")

    cr.set_source(bg_color)
    cr.rectangle(0, 0, w, h)
    cr.fill()

    number_of_balls = fctx.get_editor_value("Number of Items")
    size_max = fctx.get_data_obj("size_max")
    path_start_x = - size_max
    path_end_x =  w + size_max
    path_len = path_end_x - path_start_x
    SPEED_NORM_PER_FRAME = 15.0 / float(w) 
    for i in range(0, number_of_balls):
        path_pos, y, ball_speed, ball_size, color_index = ball_data[i]
        xc = ball_size / 2.0
        yc = ball_size / 2.0
        xpos_norm = path_pos + (float(frame) * ball_speed * SPEED_NORM_PER_FRAME)
        while xpos_norm > 1.0:
            xpos_norm = xpos_norm - 1.0
        x = path_start_x + path_len * xpos_norm
        cr.save()
        cr.translate(x, y)
        cr.arc(xc, yc, ball_size / 4.0, 0.0, 2.0 * math.pi)
        cr.set_source(ball_colors[color_index])
        cr.fill()
        cr.restore()

# ----------------------- helper func
def _clamp(v):
    return max(min(v, 1.0), 0.0)

