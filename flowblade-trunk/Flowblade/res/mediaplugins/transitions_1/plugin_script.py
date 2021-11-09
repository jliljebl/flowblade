
import cairo

MONDRIAN = [(0.18, 0.274, 0.477), (1.0, 1.0, 1.0), (0.968, 0.793, 0.0), (0.051, 0.505, 0.725), 
            (0.913, 0.0, 0.0), (0.0, 0.0, 0.0)]


# ----------------------- fluxity funcs
def init_script(fctx):
    fctx.set_name("Lines Sweep")
    fctx.set_author("Janne Liljeblad")
 
    fctx.add_editor("Line Colors", fctx.EDITOR_OPTIONS, (0,["Mondrian", "Pastels", "User Hue"]))
    fctx.add_editor("User Hue", fctx.EDITOR_COLOR, (0.8, 0.50, 0.3, 1.0))
    fctx.add_editor("Speed", fctx.EDITOR_FLOAT_RANGE, (1.0, -5.0, 5.0))
    fctx.add_editor("Direction", fctx. EDITOR_OPTIONS, (0,["Left To Right", "Right To Left"]))
    
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
    # Get editor values
    line_colors = fctx.get_editor_value("Line Colors")
    user_hue = fctx.get_editor_value("User Hue")
    speed = fctx.get_editor_value("Speed")
    direction = fctx.get_editor_value("Direction")

def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    line_colors = fctx.get_editor_value("Line Colors")
    user_hue = fctx.get_editor_value("User Hue")
    speed = fctx.get_editor_value("Speed")
    direction = fctx.get_editor_value("Direction")
        
    anim_length = 31 # make user settable
    for i in range(0, len(lines_data)):
        line_data = lines_data[i]
        width, path_len_mult,  start_pos_off, end_pos_off, color_index = line_data
        
        # more start_pos_off or path_len_mult or end_pos_off creates faster movement
        # more start_pos_off makes line appear towads start end at cover frame
        # more end_pos_off makes line appear towads end at cover frame 
        start_pos = -(w * width * path_len_mult) - (w * width) - (w * width * start_pos_off) 
        end_pos = w + (w * width * path_len_mult) + (w * width * end_pos_off)
        path_pos = float(frame) / float(anim_length)
        pos = start_pos + float(end_pos - start_pos) * path_pos

        color_tuple = MONDRIAN[color_index] # TODO: other color options
        color = cairo.SolidPattern(*color_tuple)
        
        cr.set_source(color)
        cr.rectangle(pos, 0, width * w, h)
        cr.fill()


