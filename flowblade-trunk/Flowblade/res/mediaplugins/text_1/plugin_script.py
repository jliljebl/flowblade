
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
    fctx.add_editor("Animation Type In", fluxity. EDITOR_OPTIONS, \
                    (0,["From Left Clipped", "From Right Clipped", "From Up Clipped", \
                        "From Down Clipped", "From Left", "From Right", "From Up", \
                        "From Down", "Zoom In", "Zoom Out"]))
    fctx.add_editor("Movement In", fluxity. EDITOR_OPTIONS, (0,["Linear", "Smooth",  "Fast Start", "Slow Start", "Stepped"]))
    fctx.add_editor("Frames In", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Steps In", fluxity.EDITOR_INT_RANGE, (3, 2, 10))
    fctx.add_editor("Fade In", fluxity. EDITOR_OPTIONS, (0,["Off", "Linear", "Smooth",  "Fast Start", "Slow Start", "Stepped"]))
    fctx.add_editor("Animation Type Out", fluxity. EDITOR_OPTIONS, \
                    (0,["From Left Clipped", "From Right Clipped", "From Up Clipped", \
                        "From Down Clipped", "From Left", "From Right", "From Up", \
                        "From Down", "Zoom In", "Zoom Out"]))
    fctx.add_editor("Movement Out", fluxity. EDITOR_OPTIONS, (0,["Linear", "Smooth",  "Fast Start", "Slow Start", "Stepped"]))
    fctx.add_editor("Frames Out", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Steps Out", fluxity.EDITOR_INT_RANGE, (3, 2, 10))
    fctx.add_editor("Fade Out", fluxity. EDITOR_OPTIONS, (0,["Off", "Linear", "Smooth",  "Fast Start", "Slow Start", "Stepped"]))
    fctx.add_editor("Font", fluxity.EDITOR_PANGO_FONT, fluxity.EDITOR_PANGO_FONT_DEFAULT_VALUES)
    fctx.add_editor("Text", fluxity.EDITOR_TEXT, "Line of text.")

def init_render(fctx):
    # Get editor values
    font_data = fctx.get_editor_value("Font")
    text = fctx.get_editor_value("Text")

    x = fctx.get_editor_value("Pos X")
    y = fctx.get_editor_value("Pos Y") 
    
    frames_in = fctx.get_editor_value("Frames In")
    frames_out = fctx.get_editor_value("Frames Out")
    
    animation_in_type = fctx.get_editor_value("Animation Type In")
    movement_in_type = fctx.get_editor_value("Movement In")
    steps_in = fctx.get_editor_value("Steps In")
    fade_in_type = fctx.get_editor_value("Fade In")
    in_anim_data = (animation_in_type, movement_in_type, steps_in, fade_in_type)

    animation_out_type = fctx.get_editor_value("Animation Type Out")
    movement_out_type = fctx.get_editor_value("Movement Out")
    steps_out = fctx.get_editor_value("Steps Out")
    fade_out_type = fctx.get_editor_value("Fade Out")
    out_anim_data = (animation_out_type, movement_out_type, steps_out, fade_out_type)
    
    # Create linetext object
    linetext = LineText(text, font_data, (x, y), in_anim_data, frames_in, out_anim_data, frames_out)
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

    ANIMATION_IN = 0
    ANIMATION_OUT = 1

    HORIZONTAL_ANIMATIONS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED, FROM_LEFT, FROM_RIGHT]
    VERTICAL_ANIMATIONS = [FROM_UP_CLIPPED, FROM_DOWN_CLIPPED, FROM_UP, FROM_DOWN]
    ZOOM_ANIMATIONS = [ZOOM_IN, ZOOM_OUT]
    CLIPPED_ANIMATIONS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED, FROM_UP_CLIPPED, FROM_DOWN_CLIPPED]
        
    def __init__(self, text, font_data, pos, animation_in_data, in_frames, animation_out_data, out_frames):
        self.text = text
        self.font_data = font_data
        self.pos = pos
        self.animation_type_in, self.movement_type_in, self.steps_in, self.fadein_type = animation_in_data
        self.animation_type_out, self.movement_type_out, self.steps_out, self.fadeout_type = animation_out_data
        self.in_frames = in_frames
        self.out_frames = out_frames
        self.affine = None
        self.opacity = None

    def _create_animations(self, fctx):
        self.affine = fluxity.AffineTransform()
        self.opacity = fluxity.AnimatedValue()
        
        # Animation In
        start_x, start_y, end_x, end_y, start_scale, end_scale, \
        anchor_x, anchor_y = self._get_in_animation_affine_data(fctx)
        fctx.log_line(str(start_x) + " " + str(end_x))
        
        frame_start = 0
        length = self.in_frames
        #fctx.log_line(str(frame_end - frame_start))
        movement_type = self.movement_type_in
        animation_type = self.animation_type_in
        self._apply_affine_data_with_movement(movement_type, animation_type, start_x, \
                                              start_y, end_x, end_y, start_scale, \
                                              end_scale, anchor_x, anchor_y, \
                                              frame_start, length, self.steps_in)
                                     
        self._apply_fade(self.fadein_type, frame_start, frame_start + length, LineText.ANIMATION_IN)

        # Animation Out
        start_x, start_y, end_x, end_y, start_scale, end_scale, \
        anchor_x, anchor_y = self._get_out_animation_affine_data(fctx)
        fctx.log_line(str(start_x) + " " + str(end_x))
        
        frame_start = fctx.get_length() - self.out_frames
        length = self.out_frames
        #fctx.log_line(str(frame_end - frame_start))
        
        movement_type = self.movement_type_out
        animation_type = self.animation_type_out
        self._apply_affine_data_with_movement(movement_type, animation_type, start_x, \
                                              start_y, end_x, end_y, start_scale, \
                                              end_scale, anchor_x, anchor_y, \
                                              frame_start, length, self.steps_out)
                                     
        self._apply_fade(self.fadeout_type, frame_start, frame_start + length, LineText.ANIMATION_OUT)

    def _apply_affine_data_with_movement(self, movement_type, animation_type, start_x, start_y, end_x, end_y, \
                                         start_scale, end_scale, anchor_x, anchor_y, \
                                         frame_start, frame_end, steps):
                                         
        if movement_type == LineText.LINEAR:
            self._apply_linear_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
            self._apply_linear_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
            self._apply_linear_movement(self.affine.scale_x, start_scale, end_scale, frame_start, frame_end)
            self._apply_linear_movement(self.affine.scale_y, start_scale, end_scale, frame_start, frame_end)
            self._apply_no_movement(self.affine.anchor_x, anchor_x)
            self._apply_no_movement(self.affine.anchor_y, anchor_y)
        elif movement_type == LineText.SMOOTH:
            self._apply_smooth_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
            self._apply_smooth_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
            self._apply_linear_movement(self.affine.scale_x, start_scale, end_scale, frame_start, frame_end)
            self._apply_linear_movement(self.affine.scale_y, start_scale, end_scale, frame_start, frame_end)
            self._apply_no_movement(self.affine.anchor_x, anchor_x)
            self._apply_no_movement(self.affine.anchor_y, anchor_y)
        elif movement_type == LineText.FAST_START:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_fast_start_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
                self._apply_no_movement(self.affine.y, start_y)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_fast_start_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
            else: # Zooms
                self._apply_no_movement(self.affine.y, start_y)
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_fast_start_movement(self.affine.scale_x, start_scale, end_scale, frame_start, frame_end)
                self._apply_fast_start_movement(self.affine.scale_y, start_scale, end_scale, frame_start, frame_end)
                self._apply_no_movement(self.affine.anchor_x, anchor_x)
                self._apply_no_movement(self.affine.anchor_y, anchor_y)
        elif movement_type == LineText.SLOW_START:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_slow_start_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
                self._apply_no_movement(self.affine.y, start_y)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_slow_start_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
            else: # Zooms
                self._apply_no_movement(self.affine.y, start_y)
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_slow_start_movement(self.affine.scale_x, start_scale, end_scale, frame_start, frame_end)
                self._apply_slow_start_movement(self.affine.scale_y, start_scale, end_scale, frame_start, frame_end)
                self._apply_no_movement(self.affine.anchor_x, anchor_x)
                self._apply_no_movement(self.affine.anchor_y, anchor_y)
        elif movement_type == LineText.STEPPED:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_stepped_movement(self.affine.x, start_x, end_x, frame_start, frame_end, steps)
                self._apply_no_movement(self.affine.y, start_y)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_stepped_movement(self.affine.y, start_y, end_y, frame_start, frame_end, steps)
            else: # Zooms
                self._apply_no_movement(self.affine.y, start_y)
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_stepped_movement(self.affine.scale_x, start_scale, end_scale, frame_start, frame_end, steps)
                self._apply_stepped_movement(self.affine.scale_y, start_scale, end_scale, frame_start, frame_end, steps)
                self._apply_no_movement(self.affine.anchor_x, anchor_x)
                self._apply_no_movement(self.affine.anchor_y, anchor_y)

    def _get_in_animation_affine_data(self, fctx):
        static_x, static_y = self.pos
        lw, lh = self.line_layout.get_pixel_size() # Get line size
    
        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        
        start_scale = 1.0
        end_scale = 1.0
        anchor_x = 0.0
        anchor_y = 0.0
        
        if self.animation_type_in == LineText.FROM_LEFT_CLIPPED:
            start_x = static_x - lw
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type_in == LineText.FROM_RIGHT_CLIPPED:
            start_x = static_x + lw
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type_in == LineText.FROM_UP_CLIPPED:
            start_x = static_x
            start_y = static_y - lh
            end_x = static_x
            end_y = static_y
        elif self.animation_type_in == LineText.FROM_DOWN_CLIPPED:
            start_x = static_x
            start_y =  static_y + lh
            end_x = static_x
            end_y = static_y
        elif self.animation_type_in == LineText.FROM_LEFT:
            start_x = -lw
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type_in == LineText.FROM_RIGHT:
            start_x = screen_w + lw
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type_in == LineText.FROM_UP:
            start_x = static_x
            start_y = -lh
            end_x = static_x
            end_y = static_y
        elif self.animation_type_in == LineText.ZOOM_IN:
            start_scale = 0.5
            end_scale = 1.0
            anchor_x = lw / 2.0
            anchor_y = lh / 2.0
            start_x = static_x
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type_in == LineText.ZOOM_OUT:
            start_scale = 2.0
            end_scale = 1.0
            anchor_x = lw / 2.0
            anchor_y = lh / 2.0
            start_x = static_x
            start_y = static_y
            end_x = static_x
            end_y = static_y

            start_x, start_y, end_x, end_y, start_scale, end_scale, anchor_x, anchor_y

        return (start_x, start_y, end_x, end_y, start_scale, end_scale, anchor_x, anchor_y)

    def _get_out_animation_affine_data(self, fctx):
        static_x, static_y = self.pos
        lw, lh = self.line_layout.get_pixel_size() # Get line size
    
        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        
        start_scale = 1.0
        end_scale = 1.0
        anchor_x = 0.0
        anchor_y = 0.0
        
        if self.animation_type_out == LineText.FROM_LEFT_CLIPPED:
            start_x = static_x
            start_y = static_y
            end_x = static_x - lw
            end_y = static_y
        elif self.animation_type_out == LineText.FROM_RIGHT_CLIPPED:
            start_x = static_x
            start_y = static_y
            end_x = static_x + lw
            end_y = static_y
        elif self.animation_type_out == LineText.FROM_UP_CLIPPED:
            start_x = static_x
            start_y = static_y
            end_x = static_x
            end_y = static_y - lh
        elif self.animation_type_out == LineText.FROM_DOWN_CLIPPED:
            start_x = static_x
            start_y =  static_y
            end_x = static_x
            end_y = static_y + lh
        elif self.animation_type_out == LineText.FROM_LEFT:
            start_x = static_x
            start_y = static_y
            end_x = -lw
            end_y = static_y
        elif self.animation_type_out == LineText.FROM_RIGHT:
            start_x = static_x
            start_y = static_y
            end_x = screen_w + lw
            end_y = static_y
        elif self.animation_type_out == LineText.FROM_UP:
            start_x = static_x
            start_y = static_y
            end_x = static_x
            end_y = -lh
        elif self.animation_type_out == LineText.ZOOM_IN:
            start_scale = 1.0
            end_scale = 0.5
            anchor_x = lw / 2.0
            anchor_y = lh / 2.0
            start_x = static_x
            start_y = static_y
            end_x = static_x
            end_y = static_y
        elif self.animation_type_out == LineText.ZOOM_OUT:
            start_scale = 1.0
            end_scale = 2.0
            anchor_x = lw / 2.0
            anchor_y = lh / 2.0
            start_x = static_x
            start_y = static_y
            end_x = static_x
            end_y = static_y


        return (start_x, start_y, end_x, end_y, start_scale, end_scale, anchor_x, anchor_y)
        
    def _apply_fade(self, fade_type, frame_start, frame_end, direction):
        fade_type = self.fadein_type
        if fade_type == 0:
            self._apply_no_movement(self.opacity, 1.0)
            return
        else:
            fade_type = fade_type - 1

        if direction == LineText.ANIMATION_IN:
            opa1 = 0.0
            opa2 = 1.0
        else:
            opa1 = 1.0
            opa2 = 0.0

        if fade_type == LineText.LINEAR:
            self._apply_linear_movement(self.opacity, opa1, opa2, frame_start, frame_end)
        elif fade_type == LineText.SMOOTH:
            self._apply_smooth_movement(self.opacity, opa1, opa2, frame_start, frame_end)
        elif fade_type == LineText.FAST_START:
            self._apply_fast_start_movement(self.opacity, opa1, opa2, frame_start, frame_end)
        elif fade_type == LineText.SLOW_START:
            self._apply_slow_start_movement(self.opacity, opa1, opa2, frame_start, frame_end)
        elif fade_type == LineText.STEPPED:
            self._apply_stepped_movement(self.opacity, opa1, opa2,  frame_start, frame_end)
            
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

    def _apply_stepped_movement(self, animated_value, start_val, end_val, start_frame, length, steps):
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

        # NEED TO USE FRAME DATA HERE
        if self.animation_type_in in LineText.CLIPPED_ANIMATIONS:
            cr.rectangle(static_x, static_y, lw, lh)
            cr.clip()

        self.affine.apply_transform(cr, frame)
        self.line_layout.set_opacity(self.opacity.get_value(frame))
        self.line_layout.draw_layout(self.text, cr, 0, 0)
