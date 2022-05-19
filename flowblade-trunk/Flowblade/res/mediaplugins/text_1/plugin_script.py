"""
    Copyright 2022 Janne Liljeblad, licenced under GPL3. 
    See  <http://www.gnu.org/licenses/> for licence text.
"""

import fluxity


ANIMATION_BY_LETTER = 0
ANIMATION_BY_WORD = 1
ANIMATION_BY_LINE = 2


def init_script(fctx):
    fctx.set_name("Text")
    fctx.set_author("Janne Liljeblad")
    fctx.add_editor("Text", fluxity.EDITOR_TEXT_AREA, "Lorejjjm ipsum dolor sit amet\nasdasdasdasd\nqweqweqweqwe")
    fctx.add_editor("Pos X", fluxity.EDITOR_INT, 500)
    fctx.add_editor("Pos Y", fluxity.EDITOR_INT, 500)
    fctx.add_editor("Font", fluxity.EDITOR_PANGO_FONT, fluxity.EDITOR_PANGO_FONT_DEFAULT_VALUES)
    fctx.add_editor("Line Gap", fluxity.EDITOR_INT, 8)
    fctx.add_editor("Lines Delay Frames", fluxity.EDITOR_INT_RANGE, (0, 0, 50))
    fctx.add_editor("Animation Type In", fluxity. EDITOR_OPTIONS, \
                    (0, ["From Left Clipped", "From Right Clipped", "From Up Clipped", \
                        "From Down Clipped", "From Left", "From Right", "From Up", \
                        "From Down"]))
    fctx.add_editor("Movement In", fluxity. EDITOR_OPTIONS, (1,["Linear", "Ease In", "Ease Out", "Stepped"]))
    fctx.add_editor("Frames In", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Steps In", fluxity.EDITOR_INT_RANGE, (3, 2, 10))
    fctx.add_editor("Fade In Frames", fluxity.EDITOR_INT_RANGE, (0, 0, 200))
    fctx.add_editor("Animation Type Out", fluxity. EDITOR_OPTIONS, \
                    (0, ["From Left Clipped", "From Right Clipped", "From Up Clipped", \
                        "From Down Clipped", "From Left", "From Right", "From Up", \
                        "From Down"]))
    fctx.add_editor("Movement Out", fluxity. EDITOR_OPTIONS, (0,["Linear", "Ease In", "Ease Out", "Stepped"]))
    fctx.add_editor("Frames Out", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Steps Out", fluxity.EDITOR_INT_RANGE, (3, 2, 10))
    fctx.add_editor("Fade Out Frames", fluxity.EDITOR_INT_RANGE, (0, 0, 200))
    fctx.add_editor("Background", fluxity. EDITOR_OPTIONS, (1, ["No Backround", "Color Background"]))
    fctx.add_editor("Background Pad", fluxity.EDITOR_INT, 30)

def init_render(fctx):
    # Get editor values
    font_data = fctx.get_editor_value("Font")
    text = fctx.get_editor_value("Text")

    x = fctx.get_editor_value("Pos X")
    y = fctx.get_editor_value("Pos Y") 

    line_gap = fctx.get_editor_value("Line Gap") 
    line_delay = fctx.get_editor_value("Lines Delay Frames")

    frames_in = fctx.get_editor_value("Frames In")
    frames_out = fctx.get_editor_value("Frames Out")
    
    animation_in_type = fctx.get_editor_value("Animation Type In")
    movement_in_type = fctx.get_editor_value("Movement In")
    steps_in = fctx.get_editor_value("Steps In")
    fade_in_frames = fctx.get_editor_value("Fade In Frames")
    in_anim_data = (animation_in_type, movement_in_type, steps_in, fade_in_frames )

    animation_out_type = fctx.get_editor_value("Animation Type Out")
    movement_out_type = fctx.get_editor_value("Movement Out")
    steps_out = fctx.get_editor_value("Steps Out")
    fade_out_frames = fctx.get_editor_value("Fade Out Frames")
    out_anim_data = (animation_out_type, movement_out_type, steps_out, fade_out_frames)
    
    # Create linetext objects
    lines = text.splitlines()
    linetexts = []
    for i, text in enumerate(lines):
        line_info = (i, line_gap, line_delay) 
        linetext = LineText(text, font_data, (x, y), line_info, in_anim_data, frames_in, out_anim_data, frames_out)
        linetexts.append(linetext)
        log_text = str(i) + " " + text
        fctx.log_line(log_text)
    fctx.set_data_obj("linetexts", linetexts)

def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    linetexts = fctx.get_data_obj("linetexts")

    for linetext in linetexts:
        linetext.create_layout_data(fctx, cr)

    bg_area = _get_bg_area_data(fctx, linetexts)
    bg_x, bg_y, bg_width, bg_height, pad = bg_area
    
    cr.rectangle(bg_x, bg_y, bg_width, bg_height)
    cr.set_source_rgb(0.8, 0.2, 0.2)
    cr.fill()
  
    for linetext in linetexts:
        linetext.create_animation_data(fctx, cr, bg_area)
        
    for linetext in linetexts:
        fctx.log_line(linetext.text)
        linetext.draw_text(fctx, frame, cr, bg_area)

def _get_bg_area_data(fctx, linetexts):
    # Create bg data
    bg_width = -1
    bg_height = -1
    line_gap = fctx.get_editor_value("Line Gap")
    pad =  fctx.get_editor_value("Background Pad") 
    for linetext in linetexts:
        w, h = linetext.pixel_size
        if w > bg_width:
            bg_width = w
        bg_height = bg_height + h + line_gap
    bg_height = bg_height - 2 * line_gap + 2 * pad
    bg_width = bg_width + 2 * pad
    bg_x = fctx.get_editor_value("Pos X") - pad
    bg_y = fctx.get_editor_value("Pos Y") - pad
    return (bg_x, bg_y, bg_width, bg_height, pad)
    


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
    EASE_IN = 1
    EASE_OUT = 2
    STEPPED = 3

    ANIMATION_IN = 0
    ANIMATION_OUT = 1
    
    NO_BACKGROUND = 0
    COLOR_BACKGROUND = 1

    HORIZONTAL_ANIMATIONS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED, FROM_LEFT, FROM_RIGHT]
    VERTICAL_ANIMATIONS = [FROM_UP_CLIPPED, FROM_DOWN_CLIPPED, FROM_UP, FROM_DOWN]
    ZOOM_ANIMATIONS = [ZOOM_IN, ZOOM_OUT]
    CLIPPED_ANIMATIONS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED, FROM_UP_CLIPPED, FROM_DOWN_CLIPPED]
        
    def __init__(self, text, font_data, pos, line_info, animation_in_data, in_frames, animation_out_data, out_frames):
        self.text = text
        self.font_data = font_data
        self.pos = pos
        self.line_index, self.line_gap, self.line_delay = line_info
        self.animation_type_in, self.movement_type_in, self.steps_in, self.fade_in_frames = animation_in_data
        self.animation_type_out, self.movement_type_out, self.steps_out, self.fade_out_frames = animation_out_data
        self.in_frames = in_frames
        self.out_frames = out_frames
        self.affine = None
        self.opacity = None
        self.pixel_size = None
 
    def _create_animations(self, fctx, bg_area):
        self.affine = fluxity.AffineTransform()
        self.opacity = fluxity.AnimatedValue()
        
        # Animation In
        start_x, start_y, end_x, end_y, start_scale, end_scale = self._get_in_animation_affine_data(fctx, bg_area)
 
        frame_start = 0
        length = self.in_frames
        movement_type = self.movement_type_in
        animation_type = self.animation_type_in
        self._apply_affine_data_with_movement(movement_type, animation_type, start_x, \
                                              start_y, end_x, end_y, start_scale, \
                                              end_scale, frame_start, length, self.steps_in)

        # Animation Out
        start_x, start_y, end_x, end_y, start_scale, end_scale = self._get_out_animation_affine_data(fctx, bg_area)
        
        frame_start = fctx.get_length() - self.out_frames - 1
        length = self.out_frames
        
        movement_type = self.movement_type_out
        animation_type = self.animation_type_out
        self._apply_affine_data_with_movement(movement_type, animation_type, start_x, \
                                              start_y, end_x, end_y, start_scale, \
                                              end_scale, frame_start, length, self.steps_out)
        fctx.log_line(str(self.affine.x.keyframes))                 
        self._apply_fade(fctx)

    def _apply_affine_data_with_movement(self, movement_type, animation_type, start_x, start_y, end_x, end_y, \
                                         start_scale, end_scale, frame_start, frame_end, steps):
                                         
        if movement_type == LineText.LINEAR:
            self._apply_linear_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
            self._apply_linear_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
            self._apply_linear_movement(self.affine.scale_x, start_scale, end_scale, frame_start, frame_end)
            self._apply_linear_movement(self.affine.scale_y, start_scale, end_scale, frame_start, frame_end) 
        elif movement_type == LineText.EASE_IN:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_fast_start_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
                self._apply_no_movement(self.affine.y, start_y)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_fast_start_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
        elif movement_type == LineText.EASE_OUT:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_slow_start_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
                self._apply_no_movement(self.affine.y, start_y)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_slow_start_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
        elif movement_type == LineText.STEPPED:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_stepped_movement(self.affine.x, start_x, end_x, frame_start, frame_end, steps)
                self._apply_no_movement(self.affine.y, start_y)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x)
                self._apply_stepped_movement(self.affine.y, start_y, end_y, frame_start, frame_end, steps)

    def _get_in_animation_affine_data(self, fctx, bg_area):
        static_x, static_y = self.pos
        lw, lh =  self.pixel_size 

        bg_type = fctx.get_editor_value("Background")
        pad = fctx.get_editor_value("Background Pad")
     
        if  bg_type != LineText.NO_BACKGROUND:
            bg_x, bg_y, bg_width, bg_height, pad = bg_area
            static_x = bg_x
            static_y = bg_y
            lw = bg_width
            
        # Get line y position 
        for line_index in range(self.line_index):
            static_y = static_y + lh + self.line_gap
            
        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        
        start_scale = 1.0
        end_scale = 1.0
        
        if self.animation_type_in == LineText.FROM_LEFT_CLIPPED:
            start_x = static_x - lw
            start_y = static_y + pad
            end_x = static_x + pad
            end_y = static_y + pad
        elif self.animation_type_in == LineText.FROM_RIGHT_CLIPPED:
            start_x = static_x + lw
            start_y = static_y + pad
            end_x = static_x + pad 
            end_y = static_y + pad
        elif self.animation_type_in == LineText.FROM_UP_CLIPPED:
            start_x = static_x + pad
            start_y = static_y - lh
            end_x = static_x + pad
            end_y = static_y + pad
        elif self.animation_type_in == LineText.FROM_DOWN_CLIPPED: # BUG!
            start_x = static_x + pad
            start_y = static_y + lh + pad * 2
            end_x = static_x + pad
            end_y = static_y + pad
        elif self.animation_type_in == LineText.FROM_LEFT:
            start_x = -lw
            start_y = static_y + pad
            end_x = static_x + pad
            end_y = static_y + pad
        elif self.animation_type_in == LineText.FROM_RIGHT:
            start_x = screen_w
            start_y = static_y + pad
            end_x = static_x  + pad
            end_y = static_y + pad
        elif self.animation_type_in == LineText.FROM_UP:
            start_x = static_x + pad
            start_y = -lh
            end_x = static_x + pad
            end_y = static_y + pad
        elif self.animation_type_in == LineText.FROM_DOWN:
            start_x = static_x + pad
            start_y = screen_h
            end_x = static_x + pad
            end_y = static_y + pad

        return (start_x, start_y, end_x, end_y, start_scale, end_scale)

    def _get_out_animation_affine_data(self, fctx, bg_area):
        static_x, static_y = self.pos
        lw, lh =  self.pixel_size 

        bg_type = fctx.get_editor_value("Background")
        pad = fctx.get_editor_value("Background Pad")
     
        if  bg_type != LineText.NO_BACKGROUND:
            bg_x, bg_y, bg_width, bg_height, pad = bg_area
            static_x = bg_x
            static_y = bg_y
            lw = bg_width

        # Get line y position
        first_line_static_y = static_y
        for line_index in range(self.line_index):
            static_y = static_y + lh + self.line_gap

        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        
        start_scale = 1.0
        end_scale = 1.0
        
        if self.animation_type_out == LineText.FROM_LEFT_CLIPPED:
            start_x = static_x + pad
            start_y = static_y + pad
            end_x = static_x - lw - pad * 2
            end_y = static_y + pad
        elif self.animation_type_out == LineText.FROM_RIGHT_CLIPPED:
            start_x = static_x + pad
            start_y = static_y + pad
            end_x = static_x + lw + pad * 2 
            end_y = static_y + pad
        elif self.animation_type_out == LineText.FROM_UP_CLIPPED:
            start_x = static_x + pad
            start_y = static_y + pad
            end_x = static_x + pad
            end_y = static_y - lh
        elif self.animation_type_out == LineText.FROM_DOWN_CLIPPED:
            start_x = static_x + pad
            start_y =  static_y + pad
            end_x = static_x + pad 
            end_y = static_y + lh + pad * 2
        elif self.animation_type_out == LineText.FROM_LEFT:
            start_x = static_x + pad
            start_y = static_y + pad
            end_x = -lw
            end_y = static_y + pad
        elif self.animation_type_out == LineText.FROM_RIGHT:
            start_x = static_x + pad
            start_y = static_y + pad
            end_x = screen_w + lw
            end_y = static_y + pad
        elif self.animation_type_out == LineText.FROM_UP:
            start_x = static_x + pad
            start_y = static_y + pad
            end_x = static_x + pad
            end_y = static_y - first_line_static_y - first_line_static_y + lh
        elif self.animation_type_out == LineText.FROM_DOWN:
            start_x = static_x + pad
            start_y = static_y + pad
            end_x = static_x + pad
            end_y = screen_h + static_y - first_line_static_y

        return (start_x, start_y, end_x, end_y, start_scale, end_scale)
        
    def _apply_fade(self, fctx):
        self.opacity.add_keyframe_at_frame(0, 0.0, fluxity.KEYFRAME_LINEAR)
        self.opacity.add_keyframe_at_frame(self.fade_in_frames, 1.0, fluxity.KEYFRAME_LINEAR) # With self.fade_in_frames == 0 this replaces kf from line above.
        if self.fade_out_frames > 0:
            self.opacity.add_keyframe_at_frame(fctx.get_length() - self.fade_out_frames - 1, 1.0, fluxity.KEYFRAME_LINEAR)
            self.opacity.add_keyframe_at_frame(fctx.get_length() - 1, 0.0, fluxity.KEYFRAME_LINEAR)

    def _apply_no_movement(self, animated_value, value):
        animated_value.add_keyframe_at_frame(0, value, fluxity.KEYFRAME_LINEAR)
           
    def _apply_linear_movement(self, animated_value, start_val, end_val, start_frame, length):
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_LINEAR)   
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)

    def _apply_smooth_movement(self, animated_value, start_val, end_val, start_frame, length):
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_SMOOTH)   
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)

    def _apply_fast_start_movement(self, animated_value, start_val, end_val, start_frame, length):
        mid_kf_frame = int(length * 0.2)
        mid_kf_value = start_val + (end_val - start_val) * 0.8
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + mid_kf_frame, mid_kf_value, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)

    def _apply_slow_start_movement(self, animated_value, start_val, end_val, start_frame, length):
        mid_kf_frame = int(length * 0.8)
        mid_kf_value = start_val + (end_val - start_val) * 0.2
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + mid_kf_frame, mid_kf_value, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)

    def _apply_stepped_movement(self, animated_value, start_val, end_val, start_frame, length, steps):
        step_frames = int(round(length/steps))
        step_value = (end_val - start_val)/(steps) 
        for i in range(0, steps):
            frame = int(start_frame + i * step_frames)
            value = start_val + step_value * i
            animated_value.add_keyframe_at_frame(frame, value, fluxity.KEYFRAME_DISCRETE)
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_DISCRETE) # maybe KEYFRAME_LINEAR but should not make difference.
 
    def create_layout_data(self, fctx, cr):
        # We need cairo.Context to be available to create layouts and do position calculations,
        # so we have do this on first frame when calling render_frame(frame, fctx, w, h).
        if self.pixel_size != None:
            return
        self.line_layout = fctx.create_text_layout(self.font_data)
        self.line_layout.create_pango_layout(cr, self.text)
        self.pixel_size = self.line_layout.get_pixel_size()
        
    def create_animation_data(self, fctx, cr, bg_area):
        # We need cairo.Context to be available to create layouts and do position calculations,
        # so we have do this on first frame when calling render_frame(frame, fctx, w, h).
        if self.affine != None:
            return
        self._create_animations(fctx, bg_area)

    def draw_text(self, fctx, frame, cr, bg_info):
        static_x, static_y = self.pos
        lw, lh = self.pixel_size
        
        # Get line y position for clipping
        for line_index in range(self.line_index):
            static_y = static_y + lh + self.line_gap

        # Draw text
        cr.save() # Same cairo.Context object used for all lines so we need to restore() after draw.

        if self.animation_type_in in LineText.CLIPPED_ANIMATIONS and frame <= self.in_frames:
            bg_x, bg_y, bg_width, bg_height, pad = bg_info
            cr.rectangle(bg_x, static_y - pad, bg_width, lh + pad * 2)
            cr.clip()
        elif self.animation_type_out in LineText.CLIPPED_ANIMATIONS and frame >= fctx.get_length() - self.out_frames:
            bg_x, bg_y, bg_width, bg_height, pad = bg_info
            cr.rectangle(bg_x, static_y - pad, bg_width, lh + pad * 2)
            cr.clip()
            
        frame_delay = self.line_index * self.line_delay
        line_frame = frame - frame_delay
        if line_frame < 0:
            cr.restore()
            return

        self.affine.apply_transform(cr, line_frame)
        self.line_layout.set_opacity(self.opacity.get_value(frame))
        self.line_layout.draw_layout(fctx, self.text, cr, 0, 0)

        cr.restore()
