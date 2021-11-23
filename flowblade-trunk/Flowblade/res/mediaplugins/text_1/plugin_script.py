
import cairo
from gi.repository import Pango

import fluxity


ANIMATION_BY_LETTER = 0
ANIMATION_BY_WORD = 1
ANIMATION_BY_LINE = 2


def init_script(fctx):
    fctx.set_name("Text")
    fctx.set_author("Janne Liljeblad")
    fctx.add_editor("Pos X", fluxity.EDITOR_INT, 100)
    fctx.add_editor("Pos Y", fluxity.EDITOR_INT, 100)
    fctx.add_editor("Animation Type", fluxity. EDITOR_OPTIONS, (0,["From Left Clipped", "From Right Clipped"]))
    fctx.add_editor("Frames In", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Frames Out", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Font", fluxity.EDITOR_PANGO_FONT, fluxity.EDITOR_PANGO_FONT_DEFAULT_VALUES)
    fctx.add_editor("Text", fluxity.EDITOR_TEXT, "Line of text.")
    
def init_render(fctx):
    # Get editor values
    font_data = fctx.get_editor_value("Font")
    text = fctx.get_editor_value("Text")
    animation_type = fctx.get_editor_value("Animation Type")
    x = fctx.get_editor_value("Pos X")
    y = fctx.get_editor_value("Pos Y") 
    frames_in = fctx.get_editor_value("Frames In") 
    # Create linetext object
    linetext = LineText(text, font_data,  (x, y), animation_type, frames_in)
    fctx.set_data_obj("linetext", linetext)

def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    linetext = fctx.get_data_obj("linetext")
    linetext.draw_text(fctx, frame, cr)


class LineText:
    FROM_LEFT_CLIPPED = 0
    FROM_RIGHT_CLIPPED = 1
    FROM_UP_CLIPPED = 2
    FROM_DOWN_CLIPPED = 3
    
    def __init__(self, text, font_data, pos, animation_type, in_frames):
        self.text = text
        self.font_data = font_data
        self.pos = pos
        self.animation_type = animation_type
        self.in_frames = in_frames
        
    def draw_text(self, fctx, frame, cr):
        # Create line layouts.
        line_layout = fctx.create_text_layout(self.font_data)
        line_layout.create_pango_layout(cr, self.text)
        lw, lh = line_layout.get_pixel_size() # Get line size
    
        static_x, static_y = self.pos
        
        start_x = static_x
        start_y = static_y - lh
        if frame < self.in_frames:
            fract = 1.0 - frame / self.in_frames
            pos_x = static_x
            pos_y = static_y - fract * (static_y - start_y)
        else:
            pos_x = static_x
            pos_y = static_y

        # Do clip
        cr.rectangle(static_x, static_y, lw, lh)
        cr.clip()
        line_layout.draw_layout(self.text, cr, pos_x, pos_y)
