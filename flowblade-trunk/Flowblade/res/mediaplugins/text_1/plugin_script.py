
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
    fctx.add_editor("Animation Type", fluxity. EDITOR_OPTIONS, (0,["From Left Clipped", "From Right Clipped",  "From Up Clipped", "From Down Clipped"]))
    fctx.add_editor("Movement", fluxity. EDITOR_OPTIONS, (0,["Linear", "Smooth",  "Fast Start", "Slow Start", "Stepped"]))
    fctx.add_editor("Frames In", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Frames Out", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Font", fluxity.EDITOR_PANGO_FONT, fluxity.EDITOR_PANGO_FONT_DEFAULT_VALUES)
    fctx.add_editor("Text", fluxity.EDITOR_TEXT, "Line of text.")

def init_render(fctx):
    # Get editor values
    font_data = fctx.get_editor_value("Font")
    text = fctx.get_editor_value("Text")
    animation_type = fctx.get_editor_value("Animation Type")
    movement_type = fctx.get_editor_value("Movement")
    x = fctx.get_editor_value("Pos X")
    y = fctx.get_editor_value("Pos Y") 
    frames_in = fctx.get_editor_value("Frames In") 
    # Create linetext object
    linetext = LineText(text, font_data, (x, y), animation_type, movement_type, frames_in)
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
    
    LINEAR = 0
    SMOOTH = 1
    FAST_START = 2
    SLOW_START = 3
    
    HORIZONTAL_MOVEMENTS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED]
    VERTICAL_MOVEMENTS = [FROM_UP_CLIPPED,FROM_DOWN_CLIPPED]
        
    def __init__(self, text, font_data, pos, animation_type, movement_type, in_frames):
        self.text = text
        self.font_data = font_data
        self.pos = pos
        self.animation_type = animation_type
        self.movement_type = movement_type
        self.in_frames = in_frames
        self.animated_x = None
        self.animated_y = None

    def _create_animations(self):
        static_x, static_y = self.pos
        lw, lh = self.line_layout.get_pixel_size() # Get line size
        
        self.animated_x = fluxity.AnimatedValue()
        self.animated_y = fluxity.AnimatedValue()
        
        if self.animation_type == LineText.FROM_LEFT_CLIPPED:
            start_x = static_x - lw
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type == LineText.FROM_RIGHT_CLIPPED:
            start_x = static_x + lw
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type == LineText.FROM_UP_CLIPPED:
            start_x = static_x
            start_y = static_y - lh
            end_x = static_x
            end_y = static_y
        elif self.animation_type == LineText.FROM_DOWN_CLIPPED:
            start_x = static_x
            start_y =  static_y + lh
            end_x = static_x
            end_y = static_y

        if self.movement_type == LineText.LINEAR:
            self._apply_linear_movement(self.animated_x, start_x, end_x, 0, self.in_frames)
            self._apply_linear_movement(self.animated_y, start_y, end_y, 0, self.in_frames)
        elif self.movement_type == LineText.SMOOTH:
            self._apply_smooth_movement(self.animated_x, start_x, end_x, 0, self.in_frames)
            self._apply_smooth_movement(self.animated_y, start_y, end_y, 0, self.in_frames)
        elif self.movement_type == LineText.FAST_START:
            if self.animation_type in LineText.HORIZONTAL_MOVEMENTS:
                self._apply_fast_start_movement(self.animated_x, start_x, end_x, 0, self.in_frames)
                self._apply_no_movement(self.animated_y, start_y)
            else:
                self._apply_no_movement(self.animated_x, start_x)
                self._apply_fast_start_movement(self.animated_y, start_y, end_y, 0, self.in_frames)

    def _apply_no_movement(self, animated_value, value):
        animated_value.add_keyframe_at_frame(0, value, fluxity.KEYFRAME_LINEAR)
           
    def _apply_linear_movement(self, animated_value, start_val, end_val, start_frame, length):
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_LINEAR)   
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)

    def _apply_smooth_movement(self, animated_value, start_val, end_val, start_frame, length):
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_SMOOTH)   
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_SMOOTH)

    def _apply_fast_start_movement(self, animated_value, start_val, end_val, start_frame, length):
        mid_kf_frame = int(length * 0.2)
        mid_kf_value = start_val + (end_val - start_val) * 0.8
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(mid_kf_frame, mid_kf_value, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_SMOOTH)
        
    def draw_text(self, fctx, frame, cr):
        # Create line layouts.
        self.line_layout = fctx.create_text_layout(self.font_data)
        self.line_layout.create_pango_layout(cr, self.text)

        if self.animated_x == None:
            self._create_animations() # We need cairo context to do calculations and have do this on first frame.

        static_x, static_y = self.pos
        lw, lh = self.line_layout.get_pixel_size() # Get line size
        x = self.animated_x.get_value(frame)
        y = self.animated_y.get_value(frame)

        # Do clip
        cr.rectangle(static_x, static_y, lw, lh)
        cr.clip()
        self.line_layout.draw_layout(self.text, cr, x, y)
