"""
    Copyright 2022 Janne Liljeblad, licenced under GPL3. 
    See  <http://www.gnu.org/licenses/> for licence text.
"""
import cairo
from gi.repository import Pango

import fluxity


def init_script(fctx):
    fctx.set_name("Multiline Text")
    fctx.set_version(1)
    fctx.set_author("Janne Liljeblad")

    fctx.add_editor("Text", fluxity.EDITOR_TEXT_AREA, "Lorem ipsum dolor sit amet,\nconsectetur adipiscing elit.\nInteger nec odio.")
    fctx.add_editor("Pos X", fluxity.EDITOR_INT, 500)
    fctx.add_editor("Pos Y", fluxity.EDITOR_INT, 500)
    fctx.add_editor("Font", fluxity.EDITOR_PANGO_FONT, fluxity.EDITOR_PANGO_FONT_DEFAULT_VALUES)
    fctx.add_editor("Line Gap", fluxity.EDITOR_INT, 30)
    fctx.add_editor("Lines Delay Frames", fluxity.EDITOR_INT_RANGE, (0, 0, 50))
    fctx.add_editor("Animation Type In", fluxity. EDITOR_OPTIONS, \
                    (0, ["From Left Clipped", "From Right Clipped", "From Up Clipped", \
                        "From Down Clipped", "From Left", "From Right", "From Up", \
                        "From Down"]))
    fctx.add_editor("Movement In", fluxity. EDITOR_OPTIONS, (1,["Linear", "Ease In", "Ease Out", "Stepped"]))
    fctx.add_editor("Frames In", fluxity.EDITOR_INT, 20)
    fctx.add_editor("Steps In", fluxity.EDITOR_INT_RANGE, (3, 2, 10))
    fctx.add_editor("Fade In Frames", fluxity.EDITOR_INT_RANGE, (0, 0, 200))
    fctx.add_editor("Animation Type Out", fluxity. EDITOR_OPTIONS, \
                    (7, ["To Left Clipped", "To Right Clipped", "To Up Clipped", \
                        "To Down Clipped", "To Left", "To Right", "To Up", \
                        "To Down"]))
    fctx.add_editor("Movement Out", fluxity. EDITOR_OPTIONS, (2, ["Linear", "Ease In", "Ease Out", "Stepped"]))
    fctx.add_editor("Frames Out", fluxity.EDITOR_INT, 20)
    fctx.add_editor("Steps Out", fluxity.EDITOR_INT_RANGE, (3, 2, 10))
    fctx.add_editor("Fade Out Frames", fluxity.EDITOR_INT_RANGE, (0, 0, 200))
    fctx.add_editor("Background", fluxity. EDITOR_OPTIONS, (2, ["No Background", "Solid", "Lines", "Lines Word Length"]))
    fctx.add_editor("Background Pad", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Background Color", fluxity.EDITOR_COLOR, (0.8, 0.5, 0.2, 1.0))
    fctx.add_editor("Background Opacity", fluxity.EDITOR_INT_RANGE, (100, 0, 100))
    fctx.add_editor("Line Y Offset", fluxity.EDITOR_INT, 10)

def init_render(fctx):
    # Get editor values
    font_data = fctx.get_editor_value("Font")
    text = fctx.get_editor_value("Text")

    x = fctx.get_editor_value("Pos X")
    y = fctx.get_editor_value("Pos Y") 

    line_gap = fctx.get_editor_value("Line Gap") 
    line_delay = fctx.get_editor_value("Lines Delay Frames")
    line_y_offset = fctx.get_editor_value("Line Y Offset")

    frames_in = fctx.get_editor_value("Frames In")
    frames_out = fctx.get_editor_value("Frames Out")
    
    animation_in_type = fctx.get_editor_value("Animation Type In")
    movement_in_type = fctx.get_editor_value("Movement In")
    steps_in = fctx.get_editor_value("Steps In")
    fade_in_frames = fctx.get_editor_value("Fade In Frames")
    in_anim_data = (animation_in_type, movement_in_type, steps_in, fade_in_frames)

    animation_out_type = fctx.get_editor_value("Animation Type Out")
    movement_out_type = fctx.get_editor_value("Movement Out")
    steps_out = fctx.get_editor_value("Steps Out")
    fade_out_frames = fctx.get_editor_value("Fade Out Frames")
    out_anim_data = (animation_out_type, movement_out_type, steps_out, fade_out_frames)

    hue = fctx.get_editor_value("Background Color")
    r, g, b, alpha = hue
    alpha = float(fctx.get_editor_value("Background Opacity")) / 100.0
    fctx.set_data_obj("bg_color", cairo.SolidPattern(r, g, b, alpha))

    # Create linetext objects
    lines = text.splitlines()
    linetexts = []
    for i, text in enumerate(lines):
        line_info = (i, line_gap, line_delay, line_y_offset) 
        linetext = LineText(text, font_data, (x, y), line_info, in_anim_data, frames_in, out_anim_data, frames_out)
        linetexts.append(linetext)

    fctx.set_data_obj("linetexts", linetexts)

def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    linetexts = fctx.get_data_obj("linetexts")
    for linetext in linetexts:
        linetext.create_layout_data(fctx, cr)

    bg = BackGround(fctx)

    for linetext in linetexts:
        linetext.create_animation_data(fctx, bg)
 
    bg.draw_bg(cr, fctx)
     
    for linetext in linetexts:
        linetext.draw_text(fctx, frame, cr, bg)


    

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
    LINES_BACKGROUND = 2
    LINES_WORD_LENGTH_BACKGROUND = 3
    
    HORIZONTAL_ANIMATIONS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED, FROM_LEFT, FROM_RIGHT]
    VERTICAL_ANIMATIONS = [FROM_UP_CLIPPED, FROM_DOWN_CLIPPED, FROM_UP, FROM_DOWN]
    ZOOM_ANIMATIONS = [ZOOM_IN, ZOOM_OUT]
    CLIPPED_ANIMATIONS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED, FROM_UP_CLIPPED, FROM_DOWN_CLIPPED]
        
    def __init__(self, text, font_data, layout_pos, line_info, animation_in_data, in_frames, animation_out_data, out_frames):
        self.text = text
        self.font_data = font_data
        self.layout_pos = layout_pos
        self.line_index, self.line_gap, self.line_delay, self.line_y_off = line_info
        self.animation_type_in, self.movement_type_in, self.steps_in, self.fade_in_frames = animation_in_data
        self.animation_type_out, self.movement_type_out, self.steps_out, self.fade_out_frames = animation_out_data
        self.in_frames = in_frames
        self.out_frames = out_frames
        self.affine = None
        self.opacity = None
        self.pixel_size = None
 
    def create_layout_data(self, fctx, cr):
        # fluxity.PangoTextLayout objects probably SHOULD NOT be cached because all actual work
        # is done by PangoCairo.PangoLayout objects that hold reference to cairo.Context objects 
        # that are re-created for every frame. Caching them somehow worked, but changed it to be sure.
        self.line_layout = fctx.create_text_layout(self.font_data)
        self.line_layout.create_pango_layout(cr, self.text)
        self.pixel_size = self.line_layout.pixel_size

    def create_animation_data(self, fctx, bg):
        # We need cairo.Context to be available to create layouts and do position calculations,
        # so we have do this on first frame when calling render_frame(frame, fctx, w, h).
        if self.affine != None:
            # We've done this already.
            return

        self.affine = fluxity.AffineTransform()
        self.opacity = fluxity.AnimatedValue()
        
        start_scale = 1.0
        end_scale = 1.0
        
        self._apply_justified_position(bg)
        
        # Animation In
        start_x, start_y, end_x, end_y = self._get_in_animation_affine_data(fctx, bg)
 
        frame_start = 0
        length = self.in_frames
        movement_type = self.movement_type_in
        animation_type = self.animation_type_in
        self._apply_affine_data_with_movement(movement_type, animation_type, start_x, \
                                              start_y, end_x, end_y, start_scale, \
                                              end_scale, frame_start, length, self.steps_in)

        
        # Animation Out
        start_x, start_y, end_x, end_y = self._get_out_animation_affine_data(fctx, bg)
        
        frame_start = fctx.get_length() - self.out_frames - 1
        length = self.out_frames

        movement_type = self.movement_type_out
        animation_type = self.animation_type_out

        self._apply_affine_data_with_movement(movement_type, animation_type, start_x, \
                                              start_y, end_x, end_y, start_scale, \
                                              end_scale, frame_start, length, self.steps_out)

        self._apply_fade(fctx)

    def _apply_justified_position(self, bg):
        # Compute line position.
        area_x, area_y, max_width, area_height = bg.area_data
        line_w, line_h = self.pixel_size
        x, y = self.layout_pos
        pango_alignment = self.line_layout.get_pango_alignment() 
        if pango_alignment == Pango.Alignment.LEFT:
            return
        elif pango_alignment == Pango.Alignment.CENTER:
            self.layout_pos = (x + max_width/2 - line_w/2, y)
        else: # Pango.Alignment.RIGHT
            self.layout_pos = (x + max_width - line_w, y)
            
    def _get_in_animation_affine_data(self, fctx, bg):
        layout_x, layout_y = self.layout_pos
       	line_y = self.get_line_y_pos(fctx)
        lx, ly, lw, lh = bg.get_bounding_rect_for_line(fctx,  self)

        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)

        static_x = layout_x
        static_y = line_y

        bx, by, bw, bh = bg.area_data
        pad = bg.get_pad() # this will be 0 if no bg drawn, pad affects animation distance.

        bg_padded_w = bw + 2 * pad
        bg_padded_h = bh + 2 * pad

        # All animations stop at the same position. 
       	end_x = static_x
        end_y = static_y 
        
        if self.animation_type_in == LineText.FROM_LEFT_CLIPPED:
            start_x = static_x - pad - bg_padded_w
            start_y = static_y
        elif self.animation_type_in == LineText.FROM_RIGHT_CLIPPED:
            start_x = static_x + bg_padded_w + pad
            start_y = static_y
        elif self.animation_type_in == LineText.FROM_UP_CLIPPED:
            start_x = static_x
            start_y = static_y - lh - pad
        elif self.animation_type_in == LineText.FROM_DOWN_CLIPPED:
            start_x = static_x
            start_y = static_y + lh + pad * 2
        elif self.animation_type_in == LineText.FROM_LEFT:
            start_x = -bw
            start_y = static_y
        elif self.animation_type_in == LineText.FROM_RIGHT:
            start_x = screen_w
            start_y = static_y
        elif self.animation_type_in == LineText.FROM_UP:
            start_x = static_x
            start_y = -bg_padded_h + line_y - layout_y
        elif self.animation_type_in == LineText.FROM_DOWN:
            start_x = static_x
            start_y = screen_h + line_y - layout_y

        return (start_x, start_y + self.line_y_off, end_x, end_y + self.line_y_off)

    def _get_out_animation_affine_data(self, fctx, bg):
        layout_x, layout_y = self.layout_pos
       	line_y = self.get_line_y_pos(fctx)
        lx, ly, lw, lh = bg.get_bounding_rect_for_line(fctx,  self)

        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)

        static_x = layout_x
        static_y = line_y

        bx, by, bw, bh = bg.area_data
        pad = bg.get_pad() # this will be 0 if no bg drawn, pad affects animation distance.

        bg_padded_w = bw + 2 * pad
        bg_padded_h = bh + 2 * pad

        # All animations start at the same position.
       	start_x = static_x
        start_y = static_y
        
        if self.animation_type_out == LineText.FROM_LEFT_CLIPPED:
            end_x = static_x - pad - bg_padded_w
            end_y = static_y
        elif self.animation_type_out == LineText.FROM_RIGHT_CLIPPED:
            end_x = static_x + bg_padded_w + pad
            end_y = static_y
        elif self.animation_type_out == LineText.FROM_UP_CLIPPED:
            end_x = static_x + pad
            end_y = static_y - lh - pad
        elif self.animation_type_out == LineText.FROM_DOWN_CLIPPED:
            end_x = static_x + pad 
            end_y = static_y + lh + pad * 2
        elif self.animation_type_out == LineText.FROM_LEFT:
            end_x = -bw
            end_y = static_y
        elif self.animation_type_out == LineText.FROM_RIGHT:
            end_x = screen_w
            end_y = static_y
        elif self.animation_type_out == LineText.FROM_UP:
            end_x = static_x + pad
            end_y = -bg_padded_h + line_y - layout_y
        elif self.animation_type_out == LineText.FROM_DOWN:
            end_x = static_x + pad
            end_y = screen_h + line_y - layout_y

        return (start_x, start_y + self.line_y_off, end_x, end_y + self.line_y_off)

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
                self._apply_no_movement(self.affine.y, start_y, frame_start)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x, frame_start)
                self._apply_fast_start_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
        elif movement_type == LineText.EASE_OUT:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_slow_start_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
                self._apply_no_movement(self.affine.y, start_y, frame_start)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x, frame_start)
                self._apply_slow_start_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
        elif movement_type == LineText.STEPPED:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                self._apply_stepped_movement(self.affine.x, start_x, end_x, frame_start, frame_end, steps)
                self._apply_no_movement(self.affine.y, start_y, frame_start)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                self._apply_no_movement(self.affine.x, start_x, frame_start)
                self._apply_stepped_movement(self.affine.y, start_y, end_y, frame_start, frame_end, steps)
                
    def _apply_fade(self, fctx):
        self.opacity.add_keyframe_at_frame(0, 0.0, fluxity.KEYFRAME_LINEAR)
        frame_delay = self.line_index * self.line_delay
                
        if frame_delay > 0:
            self.opacity.add_keyframe_at_frame(frame_delay, 0.0, fluxity.KEYFRAME_LINEAR)
         
        self.opacity.add_keyframe_at_frame(frame_delay + self.fade_in_frames, 1.0, fluxity.KEYFRAME_LINEAR) # With self.fade_in_frames == 0 this replaces kf from line above.
        if self.fade_out_frames > 0:
            self.opacity.add_keyframe_at_frame(fctx.get_length() - self.fade_out_frames - 1 + frame_delay, 1.0, fluxity.KEYFRAME_LINEAR)
            self.opacity.add_keyframe_at_frame(fctx.get_length() - 1  + frame_delay, 0.0, fluxity.KEYFRAME_LINEAR)

    def _apply_no_movement(self, animated_value, value, frame):
        animated_value.add_keyframe_at_frame(frame, value, fluxity.KEYFRAME_LINEAR)
           
    def _apply_linear_movement(self, animated_value, start_val, end_val, start_frame, length):
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_LINEAR)   
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)

    def _apply_smooth_movement(self, animated_value, start_val, end_val, start_frame, length):
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_SMOOTH)   
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)

    def _apply_fast_start_movement(self, animated_value, start_val, end_val, start_frame, length):
        mid_kf_frame = int(length * 0.25)
        mid_kf_value = start_val + (end_val - start_val) * 0.75
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + mid_kf_frame, mid_kf_value, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)

    def _apply_slow_start_movement(self, animated_value, start_val, end_val, start_frame, length):
        mid_kf_frame = int(length * 0.70)
        mid_kf_value = start_val + (end_val - start_val) * 0.25
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

    def get_line_y_pos(self, fctx):
        y = fctx.get_editor_value("Pos Y")
        lw, lh = self.pixel_size # lh is same for all line because we always have the same font.
        for line_index in range(self.line_index):
           y = y + lh + self.line_gap
        return y
 
    def draw_text(self, fctx, frame, cr, bg):
        static_x, static_y = self.layout_pos
        lw, lh = self.pixel_size
        
        # Get line y position for clipping
        for line_index in range(self.line_index):
            static_y = static_y + lh + self.line_gap

        cr.save() # Same cairo.Context object used for all lines, so we need to restore() after clip and transform.

        bg.clip_for_line(fctx, cr, self, frame)

        # Don't draw if line delay causes line to not start animating yet.
        frame_delay = self.line_index * self.line_delay
        line_frame = frame - frame_delay
        if line_frame < 0:
            cr.restore()
            return

        self.affine.apply_transform(cr, line_frame)
        self.line_layout.set_opacity(self.opacity.get_value(frame))
        self.line_layout.draw_layout(fctx, self.text, cr, 0, 0)

        cr.restore()



class BackGround:

    def __init__(self, fctx):
        self.linetexts = fctx.get_data_obj("linetexts")
        self.line_gap = fctx.get_editor_value("Line Gap")
        self.pad = fctx.get_editor_value("Background Pad") 
        self.bg_type = fctx.get_editor_value("Background")
        self.bg_color = fctx.get_data_obj("bg_color")
        self.area_data = self.get_bounding_rect_for_area(fctx)
 
    def get_pad(self):
        # There is no bg padding for animations if bg bg drawn.
        if self.bg_type == LineText.NO_BACKGROUND:
            return 0
        else:
            return self.pad

    def get_bounding_rect_for_area(self, fctx):
        x, y, w, h = self.get_bounding_rect_for_line(fctx,  self.linetexts[0])
        x1, y1, w1, h1 = self.get_bounding_rect_for_line(fctx,  self.linetexts[-1])
        
        height = y1 + h1 - y
        
        max_width = w

        for linetext in self.linetexts:
            rx, ry, rw, rh = self.get_bounding_rect_for_line(fctx, linetext)
            if rw > max_width:
                max_width = rw

        return (x, y, max_width, height)
  
    def clip_for_line(self, fctx, cr, line_text, frame):
        rx, ry, rw, rh = self.get_bounding_rect_for_line(fctx, line_text)
        ax, ay, aw, ah = self.area_data
        p = self.pad
        line_x, line_y = line_text.layout_pos
        w, h = line_text.pixel_size


                
        # If and out may gave different animations and need different clipping.
        do_clip = False
        line_delay_addition = line_text.line_index * line_text.line_delay  # clipping application time needs to include line delays.
        # In and out animations have different clliping applied and need to be applied temporally on their own areas.
        if (line_text.animation_type_in in LineText.CLIPPED_ANIMATIONS) and (frame <= line_text.in_frames + line_delay_addition):
            do_clip = True
        elif (line_text.animation_type_out in LineText.CLIPPED_ANIMATIONS) and (frame >= fctx.get_length() - line_text.out_frames):
            do_clip = True
        
        if do_clip == True:
            if self.bg_type == LineText.LINES_WORD_LENGTH_BACKGROUND:
                cr.rectangle(line_x - p, ry - p, w + 2 * p, rh + 2 * p)
                cr.clip()
            else:
                cr.rectangle(rx - p, ry - p, aw + 2 * p, rh + 2 * p)
                cr.clip()
                
    def get_bounding_rect_for_line(self, fctx, line_text):
        line_x = fctx.get_editor_value("Pos X")
        lw, lh = line_text.pixel_size
        line_y = line_text.get_line_y_pos(fctx)
        top_pad = line_text.line_layout.get_top_pad()
 
        rx = line_x
        ry = line_y
        rw = lw
        rh = lh - top_pad
        
        return (rx, ry, rw, rh)
        
    def draw_bg(self, cr, fctx):
        if self.bg_type == LineText.COLOR_BACKGROUND:
            rx, ry, rw, rh = self.area_data
            p = self.pad
            rx = rx - p
            ry = ry - p
            rw = rw + 2 * p
            rh = rh + 2 * p

            cr.rectangle(rx, ry, rw, rh)
            cr.set_source(self.bg_color)
            cr.fill()
        elif self.bg_type == LineText.LINES_BACKGROUND:
            ax, ay, aw, ah = self.area_data
            for linetext in self.linetexts:
                rx, ry, rw, rh = self.get_bounding_rect_for_line(fctx, linetext)
                p = self.pad
                cr.rectangle(rx - p, ry - p, aw + 2 * p, rh + 2 * p)
                cr.set_source(self.bg_color)
                cr.fill()
        elif self.bg_type == LineText.LINES_WORD_LENGTH_BACKGROUND:
            for linetext in self.linetexts:
                rx, ry, rw, rh = self.get_bounding_rect_for_line(fctx, linetext)
                line_x, line_y = linetext.layout_pos
                w, h = linetext.pixel_size
                p = self.pad
                cr.rectangle(line_x - p, ry - p, w + 2 * p, rh + 2 * p)
                cr.set_source(self.bg_color)
                cr.fill()
                