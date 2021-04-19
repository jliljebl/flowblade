
import cairo
import mlt

def init_script(fctx):
    # Script init here
    fctx.add_editor("float_editor", fctx.EDITOR_FLOAT, 1.0)
    fctx.set_name("Default Test Plugin")

def init_render(fctx):
    # Render init here
    fctx.set_data("bg_color", cairo.SolidPattern(0.8, 0.2, 0.2, 1.0))
    fctx.set_data("fg_color", cairo.SolidPattern(0.2, 0.8, 0.2, 1.0))

def render_frame(frame, fctx, w, h):
    # Frame Render code here
    cr = fctx.get_frame_cr()
    color = fctx.get_data("bg_color")
    cr.set_source(color)
    cr.rectangle(0, 0, w, h)
    cr.fill()

    x = 100.0 + 2.0 * frame
    y = 100.0 + 2.0 * frame
    color = fctx.get_data("fg_color")
    cr.set_source(color)
    cr.rectangle(x, y, 100, 100)
    cr.fill()