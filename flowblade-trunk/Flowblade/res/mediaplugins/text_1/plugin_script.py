
import cairo
from gi.repository import Pango

import fluxity


ANIMATION_BY_LETTER = 0
ANIMATION_BY_WORD = 1
ANIMATION_BY_LINE = 2


def init_script(fctx):
    fctx.set_name("Text")
    fctx.set_author("Janne Liljeblad")
    fctx.add_editor("Pos X", fluxity.EDITOR_INT, 500)
    fctx.add_editor("Pos Y", fluxity.EDITOR_INT, 500)
    fctx.add_editor("Animation Type", fluxity. EDITOR_OPTIONS, \
                    (0,["From Left Clipped", "From Right Clipped", "From Up Clipped", \
                        "From Down Clipped", "From Left", "From Right", "From Up", \
                        "From Down", "Zoom In", "Zoom Out"]))
    fctx.add_editor("Movement", fluxity. EDITOR_OPTIONS, (0,["Linear", "Smooth",  "Fast Start", "Slow Start", "Stepped"]))
    fctx.add_editor("Frames In", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Frames Out", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Steps", fluxity.EDITOR_INT_RANGE, (3, 2, 10))
    fctx.add_editor("Fade In", fluxity. EDITOR_OPTIONS, (0,["Off", "Linear", "Smooth",  "Fast Start", "Slow Start", "Stepped"]))
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
    FROM_LEFT = 4
    FROM_RIGHT = 5
    FROM_UP = 6
    FROM_DOWN = 7
    ZOOM_IN = 8
    ZOOM_OUT = 9
    
    LINEAR = 0
    SMOOTH = 1
    FAST_START = 2
    SLOW_START = 3
    STEPPED = 4
    
    HORIZONTAL_ANIMATIONS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED, FROM_LEFT, FROM_RIGHT]
    VERTICAL_ANIMATIONS = [FROM_UP_CLIPPED, FROM_DOWN_CLIPPED, FROM_UP, FROM_DOWN]
    ZOOM_ANIMATIONS = [ZOOM_IN, ZOOM_OUT]
    CLIPPED_ANIMATIONS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED, FROM_UP_CLIPPED, FROM_DOWN_CLIPPED]
        
    def __init__(self, text, font_data, pos, animation_type, movement_type, in_frames):
        self.text = text
        self.font_data = font_data
        self.pos = pos
        self.animation_type = animation_type
        self.movement_type = movement_type
        self.in_frames = in_frames
        self.affine = None
        self.opacity = None

    def _create_animations(self, fctx):
        static_x, static_y = self.pos
        lw, lh = self.line_layout.get_pixel_size() # Get line size
        
        self.affine = fluxity.AffineTransform()
        self.opacity = fluxity.AnimatedValue()
    
        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        start_scale = 1.0
        end_scale = 1.0
        anchor_x = 0.0
        anchor_y = 0.0
        
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
        elif self.animation_type == LineText.FROM_LEFT:
            start_x = -lw
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type == LineText.FROM_RIGHT:
            start_x = screen_w + lw
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type == LineText.FROM_UP:
            start_x = static_x
            start_y = -lh
            end_x = static_x
            end_y = static_y
        elif self.animation_type == LineText.ZOOM_IN:
            start_scale = 0.5
            end_scale = 1.0
            anchor_x = lw / 2.0
            anchor_y = lh / 2.0
            start_x = static_x
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type == LineText.ZOOM_OUT:
            start_scale = 1.0
            end_scale = 0.5
            anchor_x = lw / 2.0
            anchor_y = lh / 2.0
            start_x = static_x
            start_y = static_y
            end_x = static_x
            end_y = static_y

        if self.movement_type == LineText.LINEAR:
            self._apply_linear_movement(self.affine.x, start_x, end_x, 0, self.in_frames)
            self._apply_linear_movement(self.affine.y, start_y, end_y, 0, self.in_frames)
            self._apply_linear_movement(self.affine.scale_x, start_scale, end_scale, 0, self.in_frames)
            self._apply_linear_movement(self.affine.scale_y, start_scale, end_scale, 0, self.in_frames)
            self._apply_no_movement(self.affine.anchor_x, anchor_x)
            self._apply_no_movement(self.affine.anchor_y, anchor_y)
        elif self.movement_type == LineText.SMOOTH:
            self._apply_smooth_movement(self.affine.x, start_x, end_x, 0, self.in_frames)
            self._apply_smooth_movement(self.affine.y, start_y, end_y, 0, self.in_frames)
            self._apply_linear_movement(self.affine.scale_x, start_scale, end_scale, 0, self.in_frames)
            self._apply_linear_movement(self.affine.scale_y, start_scale, end_scale, 0, self.in_frames)
            self._apply_no_movement(self.affine.anchor_x, anchor_x)
            self._apply_no_movement(self.affine.anchor_y, anchor_y)
        elif self.movement_type == LineText.FAST_START:
            if self.animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_fast_start_movement(self.affine.x, start_x, end_x, 0, self.in_frames)
                self._apply_no_movement(self.affine.y, start_y)
            elif self.animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_fast_start_movement(self.affine.y, start_y, end_y, 0, self.in_frames)
            else: # Zooms
                self._apply_no_movement(self.affine.y, start_y)
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_fast_start_movement(self.affine.scale_x, start_scale, end_scale, 0, self.in_frames)
                self._apply_fast_start_movement(self.affine.scale_y, start_scale, end_scale, 0, self.in_frames)
                self._apply_no_movement(self.affine.anchor_x, anchor_x)
                self._apply_no_movement(self.affine.anchor_y, anchor_y)
        elif self.movement_type == LineText.SLOW_START:
            if self.animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_slow_start_movement(self.affine.x, start_x, end_x, 0, self.in_frames)
                self._apply_no_movement(self.affine.y, start_y)
            elif self.animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_slow_start_movement(self.affine.y, start_y, end_y, 0, self.in_frames)
            else: # Zooms
                self._apply_no_movement(self.affine.y, start_y)
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_slow_start_movement(self.affine.scale_x, start_scale, end_scale, 0, self.in_frames)
                self._apply_slow_start_movement(self.affine.scale_y, start_scale, end_scale, 0, self.in_frames)
                self._apply_no_movement(self.affine.anchor_x, anchor_x)
                self._apply_no_movement(self.affine.anchor_y, anchor_y)
        elif self.movement_type == LineText.STEPPED:
            if self.animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_stepped_movement(self.affine.x, start_x, end_x, 0, self.in_frames, fctx)
                self._apply_no_movement(self.affine.y, start_y)
            elif self.animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_stepped_movement(self.affine.y, start_y, end_y, 0, self.in_frames, fctx)
            else: # Zooms
                self._apply_no_movement(self.affine.y, start_y)
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_stepped_movement(self.affine.scale_x, start_scale, end_scale, 0, self.in_frames, fctx)
                self._apply_stepped_movement(self.affine.scale_y, start_scale, end_scale, 0, self.in_frames, fctx)
                self._apply_no_movement(self.affine.anchor_x, anchor_x)
                self._apply_no_movement(self.affine.anchor_y, anchor_y)

        fade_type = fctx.get_editor_value("Fade In")
        if fade_type == 0:
            self._apply_no_movement(self.opacity, 1.0)
            return
        else:
            fade_type = fade_type - 1
        if fade_type == LineText.LINEAR:
            self._apply_linear_movement(self.opacity, 0.0, 1.0, 0, self.in_frames)
        elif fade_type == LineText.SMOOTH:
            self._apply_smooth_movement(self.opacity, 0.0, 1.0, 0, self.in_frames)
        elif fade_type == LineText.FAST_START:
            self._apply_fast_start_movement(self.opacity, 0.0, 1.0, 0, self.in_frames)
        elif fade_type == LineText.SLOW_START:
            self._apply_slow_start_movement(self.opacity, 0.0, 1.0, 0, self.in_frames)
        elif fade_type == LineText.STEPPED:
            self._apply_stepped_movement(self.opacity, 0.0, 1.0, 0, self.in_frames)


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

    def _apply_slow_start_movement(self, animated_value, start_val, end_val, start_frame, length):
        mid_kf_frame = int(length * 0.8)
        mid_kf_value = start_val + (end_val - start_val) * 0.2
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(mid_kf_frame, mid_kf_value, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_SMOOTH)

    def _apply_stepped_movement(self, animated_value, start_val, end_val, start_frame, length, fctx):
        steps = fctx.get_editor_value("Steps")
        step_frames = int(round(length/steps))
        step_value = (end_val - start_val)/(steps) 
        for i in range(0, steps):
            frame = int(start_frame + i * step_frames)
            value = start_val + step_value * i
            animated_value.add_keyframe_at_frame(frame, value, fluxity.KEYFRAME_DISCRETE)
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_DISCRETE) # maybe KEYFRAME_LINEAR but should not make difference.
         
    def draw_text(self, fctx, frame, cr):
        # Create line layouts.
        self.line_layout = fctx.create_text_layout(self.font_data)
        self.line_layout.create_pango_layout(cr, self.text)

        if self.affine == None:
            self._create_animations(fctx) # We need cairo context and layout available 
                                          # to do calculations and have do this on first frame.

        static_x, static_y = self.pos
        lw, lh = self.line_layout.get_pixel_size() # Get line size

        if self.animation_type in LineText.CLIPPED_ANIMATIONS:
            cr.rectangle(static_x, static_y, lw, lh)
            cr.clip()

        self.affine.apply_transform(cr, frame)
        self.line_layout.set_opacity(self.opacity.get_value(frame))
        self.line_layout.draw_layout(self.text, cr, 0, 0)
