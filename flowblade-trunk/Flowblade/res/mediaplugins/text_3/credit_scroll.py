"""
    Copyright 2022 Janne Liljeblad, licenced under GPL3. 
    See  <http://www.gnu.org/licenses/> for licence text.
"""

import cairo
from gi.repository import Pango

import fluxity

STATE_CLEAR = 0
STATE_WAITING_NEXT_NAME = 1

LINE_TYPE_NAME = 0
LINE_TYPE_CREDIT = 1
LINE_TYPE_SECTION_TITLE = 2
LINE_TYPE_COMMAND = 3
LINE_TYPE_CLEAR = 4
LINE_TYPE_BAD = 5

MARKUP_CREDIT = "#"
MARKUP_COMMAND = "!"
MARKUP_SECTION_TITLE = "##"

NON_CREDITED_NAME_ERROR = 0
BAD_LINE_ERROR = 1
PARSE_CRASH_ERROR = 2
SECTION_TITLE_INSIDE_CREDIT_SECTION_ERROR = 3


DEFAULT_SCROLL_MARKUP_TEXT = \
"""
# CREDIT TITLE 1
Alice Andersson

# CREDIT TITLE 2
Bob Banner
"""

def init_script(fctx):
    fctx.set_name("Scrolling Credits")
    fctx.set_version(2)
    fctx.set_author("Janne Liljeblad")


    fctx.add_editor_group("Layout")
    fctx.add_editor("Credits Layout", fluxity.EDITOR_OPTIONS, (0, ["Single Line Centered", "Two Line Centered", "Single Line Right Justified", "Two Line Right Justified"]))

    fctx.add_editor_group("Fonts")
    font_default_values = ("Liberation Serif", "Regular", 80, Pango.Alignment.LEFT, (0.0, 0.0, 0.0, 1.0), \
                       True, (0.3, 0.3, 0.3, 1.0) , False, 2, False, (0.0, 0.0, 0.0), \
                       100, 3, 3, 0.0, None, fluxity.VERTICAL)
    fctx.add_editor("Credit Font", fluxity.EDITOR_PANGO_FONT, font_default_values)
    fctx.add_editor("Name Font", fluxity.EDITOR_PANGO_FONT, font_default_values)
    
    fctx.add_editor_group("Animation")
    fctx.add_editor("Speed", fluxity.EDITOR_FLOAT_RANGE, (10.0, 0.0, 40.0))

    fctx.add_editor_group("Text")
    fctx.add_editor("Text", fluxity.EDITOR_TEXT_AREA, DEFAULT_SCROLL_MARKUP_TEXT)
    """
    fctx.add_editor("Pos X", fluxity.EDITOR_INT, 200)
    fctx.add_editor("Pos Y", fluxity.EDITOR_INT, 200)
    fctx.add_editor("Centering", fluxity.EDITOR_OPTIONS, (0, ["Off", "Center", "Center Horizontal", "Center Vertical"]))
    font_default_values = ("Liberation Serif", "Regular", 80, Pango.Alignment.LEFT, (0.0, 0.0, 0.0, 1.0), \
                       True, (0.3, 0.3, 0.3, 1.0) , False, 2, False, (0.0, 0.0, 0.0), \
                       100, 3, 3, 0.0, None, fluxity.VERTICAL)
    fctx.add_editor("Font", fluxity.EDITOR_PANGO_FONT, font_default_values)
    fctx.add_editor("Line Gap", fluxity.EDITOR_INT, 30)

    fctx.add_editor("Line Y Offset", fluxity.EDITOR_INT, -5)

    fctx.add_editor_group("Animation")
    
    fctx.add_editor("Animation Type In", fluxity.EDITOR_OPTIONS, \
                    (1, ["None", "From Left Clipped", "From Right Clipped", "From Up Clipped", \
                        "From Down Clipped", "From Left", "From Right", "From Up", \
                        "From Down", "Reveal Horizontal", "Reveal Vertical", "Reveal Left", "Reveal Right"]))
    fctx.add_editor("Lines Delay Frames", fluxity.EDITOR_INT_RANGE, (0, 0, 50))
    fctx.add_editor("Movement In", fluxity. EDITOR_OPTIONS, (1,["Linear", "Ease In", "Ease Out", "Stepped"]))
    fctx.add_editor("Frames In", fluxity.EDITOR_INT, 12)
    fctx.add_editor("Steps In", fluxity.EDITOR_INT_RANGE, (3, 2, 10))
    fctx.add_editor("Fade In Frames", fluxity.EDITOR_INT_RANGE, (0, 0, 200))
    fctx.add_editor("Fade In Type", fluxity.EDITOR_OPTIONS, (1,["Linear", "Compact Linear"]))
    fctx.add_editor("Animation Type Out", fluxity. EDITOR_OPTIONS, \
                    (1, ["None", "To Left Clipped", "To Right Clipped", "To Up Clipped", \
                        "To Down Clipped", "To Left", "To Right", "To Up", \
                        "To Down", "Reveal Horizontal", "Reveal Vertical", "Reveal Left", "Reveal Right"]))
    fctx.add_editor("Movement Out", fluxity. EDITOR_OPTIONS, (2, ["Linear", "Ease In", "Ease Out", "Stepped"]))
    fctx.add_editor("Movement Out", fluxity. EDITOR_OPTIONS, (2, ["Linear", "Ease In", "Ease Out", "Stepped"]))
    fctx.add_editor("Frames Out", fluxity.EDITOR_INT, 12)
    fctx.add_editor("Steps Out", fluxity.EDITOR_INT_RANGE, (3, 2, 10))
    fctx.add_editor("Fade Out Frames", fluxity.EDITOR_INT_RANGE, (0, 0, 200))
    fctx.add_editor("Fade Out Type", fluxity.EDITOR_OPTIONS, (1,["Linear", "Compact Linear"]))

    fctx.add_editor_group("Background")

    fctx.add_editor("Background", fluxity.EDITOR_OPTIONS, (2, ["No Background", "Solid", "Lines Solid", "Lines Word Length Solid", "Lines Solid Screen Width", "Box", "Horizontal Lines", "Underline", "Strikethrought"]))
    fctx.add_editor("Background Color", fluxity.EDITOR_COLOR, (1.0, 1.0, 1.0, 1.0))
    fctx.add_editor("Background Line Width", fluxity.EDITOR_INT, 3)
    fctx.add_editor("Background Opacity", fluxity.EDITOR_INT_RANGE, (100, 0, 100))
    fctx.add_editor("Background Pad", fluxity.EDITOR_INT, 10)
    fctx.add_editor("Background Anim In", fluxity.EDITOR_OPTIONS, (0,["Off", "Fade", "Reveal Up", "Reveal Down", "Reveal Left", "Reveal Right", "Reveal Horizontal", "Reveal Vertical"]))
    fctx.add_editor("Background Frames In", fluxity.EDITOR_INT, 8)
    fctx.add_editor("Background Anim Out", fluxity.EDITOR_OPTIONS, (0,["Off", "Fade", "Reveal Up", "Reveal Down", "Reveal Left", "Reveal Right", "Reveal Horizontal", "Reveal Vertical"]))
    fctx.add_editor("Background Frames Out", fluxity.EDITOR_INT, 8)
    """
    
def init_render(fctx):
    # Get editor values
    """
    font_data = fctx.get_editor_value("Font")
    text = fctx.get_editor_value("Text")

    fctx.log_line("printti2")

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
    """
    
    text = fctx.get_editor_value("Text")
        
    # Create linetext objects
    lines = text.splitlines()
    blocks_generator = ScrollBlocksGenerator(lines, fctx)
    scroll_blocks, err = blocks_generator.get_blocks()
    fctx.log_line("blocks count " + str(len(scroll_blocks)))
    fctx.log_line("BLOCKS")
    for block in scroll_blocks:
        fctx.log_line(str(block))
    fctx.set_data_obj("scroll_blocks", scroll_blocks)

def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    bg_color = cairo.SolidPattern(0.8, 0.50, 0.3, 1.0)
    cr.set_source(bg_color)
    cr.rectangle(0, 0, w, h)
    cr.fill()
    
    anim_runner = ScroolAnimationRunner(fctx)
    anim_runner.init_blocks(fctx, cr, frame)
    anim_runner.draw_blocks(fctx, cr, frame)


class ScrollBlocksGenerator:


    def __init__(self, lines, fctx):
        self.lines = lines

        self.current_layout = fctx.get_editor_value("Credits Layout")
        self.fctx = fctx
        
    def get_blocks(self):
        self.running = True
        self.state = STATE_CLEAR
        self.current_line = 0
        self.current_credit_block_data = None
        self.blocks = []
        self.err_list = []
        
        while self.running == True:
            #try:
            line = self.lines[self.current_line]
            line_type = self.get_line_type(line)

            if line_type == LINE_TYPE_CLEAR:
                self.do_line_clear(line)
            elif line_type == LINE_TYPE_CREDIT:
                self.do_credit_line(line)
            elif line_type == LINE_TYPE_NAME:
                self.do_name_line(line)
            elif line_type == LINE_TYPE_COMMAND:
                self.do_command_line(line)
            elif line_type == LINE_TYPE_SECTION_TITLE:
                self.do_section_title_line(line)
            else:
                self.add_error(BAD_LINE_ERROR, line)

            self.current_line += 1
    
            """
            except Exception as e:
                if hasattr(e, 'message'):
                    msg = e.message
                else:
                    msg = str(e)
                self.add_error(PARSE_CRASH_ERROR, line, msg)
                self.running = False 
            """
            
            if self.current_line > len(self.lines) - 1:
                if self.state == STATE_WAITING_NEXT_NAME:
                     self.add_credit_block()
                self.running = False 
            
        return (self.blocks, None)

    def do_line_clear(self, line):
        self.print_line(LINE_TYPE_CLEAR, line)

        if self.state == STATE_CLEAR:
            return
        else:
            # State is STATE_WAITING_NEXT_NAME
            # Create new credit block using current data.
           self.add_credit_block()
           self.state = STATE_CLEAR
        
    def do_credit_line(self, line):
        self.print_line(LINE_TYPE_CREDIT, line)

        if self.state == STATE_CLEAR:
            credit_title = self.get_line_contents_str(line)
            self.current_credit_block_data = CredidBlockData(credit_title)
            self.state = STATE_WAITING_NEXT_NAME
        elif self.state == STATE_WAITING_NEXT_NAME:
            # Create new credit block using current data.
            self.add_credit_block()
            # Init next credit block
            credit_title = self.get_line_contents_str(line)
            self.current_credit_block_data = CreridBlockData(credit_title)
            self.state = STATE_WAITING_NEXT_NAME
        
    def do_name_line(self, line):
        self.print_line(LINE_TYPE_NAME, line)
        
        if self.state == STATE_WAITING_NEXT_NAME:
            self.current_credit_block_data.add_name(line)
        else:
            # We're trying to add name to without specifying 
            # credit for it, add error info.
            self.add_error(NON_CREDITED_NAME_ERROR, line)
        
    def do_command_line(self, line):
        command_exec_func, err = _get_command_exec_func(line)
        if err != None:
            self.add_error(BAD_COMMAND_ERROR, line)
        else:
            command_exec_func(line, self)

    def do_section_title_line(self, line):
        if self.state == STATE_WAITING_NEXT_NAME:
            self.add_error(SECTION_TITLE_INSIDE_CREDIT_SECTION_ERROR, line)
        else:
            section_title = self.get_line_contents_str(line)
            self.blocks.append(SectionTitleBlock(section_title))

    def get_line_type(self, line):
        if line == "":
            return LINE_TYPE_CLEAR
        
        markup = self.get_line_markup(line)
        if markup == None:
            line = line.strip()
            if line == "":
                return LINE_TYPE_CLEAR
            else:
                return LINE_TYPE_NAME

        if len(line) < 2:
            return LINE_TYPE_BAD

        if markup == MARKUP_CREDIT:
            return LINE_TYPE_CREDIT
        elif markup == MARKUP_COMMAND:
            return LINE_TYPE_COMMAND
        else:
            return LINE_TYPE_SECTION_TITLE

    def get_line_markup(self, line):
        if line.startswith(MARKUP_CREDIT):
            return MARKUP_CREDIT
        elif line.startswith(MARKUP_COMMAND):
            return MARKUP_COMMAND
        elif line.startswith(MARKUP_SECTION_TITLE):
            return MARKUP_SECTION_TITLE
        else:
            return None

    def get_line_contents_str(self, line):
        line_type = self.get_line_type(line)
        if line_type == LINE_TYPE_CLEAR or line_type == LINE_TYPE_BAD:
            return None
        elif line_type ==  LINE_TYPE_NAME:
            return line.strip()
        else:
            return line[1:].strip()

    def add_credit_block(self):
        bloc_creator_func = BLOC_CREATOR_FUNCS[self.current_layout]
        block = bloc_creator_func(self)
        self.blocks.append(block)

        log_str = "adding block, line " + str(self.current_line) + " " + str(block)
        self.fctx.log_line(log_str)

    def add_error(self, error_code, line, crash_msg=None):
        error_info = {  NON_CREDITED_NAME_ERROR:"Added neme without specifying credit for it",  
                        BAD_LINE_ERROR:"Bad line, maybe markup specified but no content given", 
                        PARSE_CRASH_ERROR:"Parser crashed with error message ",
                        SECTION_TITLE_INSIDE_CREDIT_SECTION_ERROR:"Section title spevified inside credit block."}
        
        if crash_msg != None:
            error_info = error_info + crash_msg
        
        self.err_list.append(( error_code, line,error_info,  self.current_line))

    def print_line(self, line_type, line):
        line_type_strs = { \
            LINE_TYPE_NAME:"NAME",
            LINE_TYPE_CREDIT:"CREDIT",
            LINE_TYPE_SECTION_TITLE:"SECTION_TITLE",
            LINE_TYPE_COMMAND:"COMMAND",
            LINE_TYPE_CLEAR:"CLEAR",
            LINE_TYPE_BAD:"BAD"}
        
        log_str = str(self.current_line) + " " + line_type_strs[line_type] + " " + str(self.get_line_contents_str(line))
        self.fctx.log_line(log_str)


class ScroolAnimationRunner:
    
    def __init__(self, fctx):
        self.scroll_blocks = fctx.get_data_obj("scroll_blocks")
        self.fctx = fctx

    def init_blocks(self, fctx, cr,  frame):
        mutable_layout_data = { \
            "credit_font_data":fctx.get_editor_value("Credit Font"),
            "name_font_data":fctx.get_editor_value("Name Font")}

        # Create layouts now that we have cairo.Context.
        for block in self.scroll_blocks:
            block.init_layout(fctx, cr, frame, mutable_layout_data)
            block.exec_command(fctx, cr, frame, mutable_layout_data)

    def draw_blocks(self, fctx, cr, frame):
        speed = fctx.get_editor_value("Speed")
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        y = screen_h - frame * speed
        BLOCK_GAP = 20
        for block in self.scroll_blocks:
            block.draw(fctx, cr, y)
            y += (block.block_height + BLOCK_GAP)



class CredidBlockData:

    def __init__(self, credit_title):
        self.credit_title = credit_title
        self.names = []

    def add_name(self, name):
        self.names.append(name)


class AbstractBlock:
    
    def __init__(self):
        self.block_height = 0

    def init_layout(self, fctx, cr, frame, mutable_layout_data):
        pass

    def exec_command(self, fctx, cr, frame, mutable_layout_data):
        pass

    def draw(self, fctx, cr, y):
        pass

    def _get_height_str(self):
        return "block_height: " + str(self.block_height)

    def __str__(self):
        return "AbstractBlock, " + self._get_height_str()


class AbstractCreditBlock(AbstractBlock):
    
    # These eindexs must match those in editor "Credits Layout".
    LAYOUT_SINGLE_LINE_CENTERED = 0
    LAYOUT_TWO_LINE_CENTERED = 1
    LAYOUT_SINGLE_LINE_RIGHT_JUSTIFIED = 2
    LAYOUT_TWO_LINE_RIGHT_JUSTIFIED = 3
    
    def __init__(self, block_gen):
        block_data = block_gen.current_credit_block_data

        self.credit_title = block_data.credit_title
        self.names = block_data.names
        self.fctx = block_gen.fctx
        self.draw_items = []
    
        AbstractBlock.__init__(self)

    def create_layouts(self, fctx, cr, mutable_layout_data):

        # fluxity.PangoTextLayout objects probably SHOULD NOT be cached because all actual work
        # is done by PangoCairo.PangoLayout objects that hold reference to cairo.Context objects 
        # that are re-created for every new frame. Caching them somehow worked, but changed it to be sure.
        self.credit_layout = fctx.create_text_layout(mutable_layout_data["credit_font_data"])
        self.credit_layout.create_pango_layout(cr, self.credit_title)
        self.credit_pixel_size = self.credit_layout.pixel_size

        self.name_layouts = []
        for name in self.names:
            name_layout = fctx.create_text_layout(mutable_layout_data["name_font_data"])
            name_layout.create_pango_layout(cr, name)
            name_pixel_size = name_layout.pixel_size
            self.name_layouts.append((name_layout, name_pixel_size))

    def add_text_draw_item(self, text, x, y, font_data):
        self.draw_items.append((text, x, y, font_data))

    def draw(self, fctx, cr, y):
        fctx.log_line("hereeee")
        if y + self.block_height < 0:
            return
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        if y > screen_h:
            return
        
        for draw_item in self.draw_items:
            text, tx, ty, font_data = draw_item
            layout = fctx.create_text_layout(font_data)
            layout.create_pango_layout(cr, text)
            layout.draw_layout(fctx, text, cr, tx, y + ty)
        
    def _get_credits_str(self):
        data_str = "credit_title: " + self.credit_title + "\n" + \
        "names: "
        for name in self.names:
            data_str = data_str + name + "n"
        
        return data_str

    def __str__(self):
        msg = type(self).__name__ + ", "  + self._get_height_str() + "\n" \
        + self._get_credits_str()
        return msg



class SingleLineCentered(AbstractCreditBlock):
    def __init__(self, block_gen):
        AbstractCreditBlock.__init__(self, block_gen)

    def init_layout(self, fctx, cr, frame, mutable_layout_data):
        self.create_layouts(fctx, cr, mutable_layout_data)

        CENTER_GAP = 10
        LINE_GAP = 10
        
        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        
        # Compute layout positions data.
        max_w = 0
        names_height = 0
        for layout in self.name_layouts:
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            fctx.log_line("h:" + str(h))
            if w > max_w:
                w = max_w
            names_height += (h + LINE_GAP)
    
        names_height = names_height - LINE_GAP
        fctx.log_line("names_height:" + str(names_height))
    
        cw, ch = self.credit_pixel_size
    
        total_width = cw + CENTER_GAP + max_w
        total_height = names_height
        if total_height < ch:
            total_height = ch
        
        # Create draw items
        self.add_text_draw_item(self.credit_title,screen_w / 2 - cw, 0, mutable_layout_data["credit_font_data"])
        
        y = 0
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, screen_w / 2, y, mutable_layout_data["name_font_data"])

        self.block_height = total_height
        fctx.log_line("block_height:" + str(self.block_height))
        
def _get_single_line_centered(block_gen):
    return SingleLineCentered(block_gen)

def _get_two_line_centered(block_gen):
    return TwoLineCentered(block_gen)
def _get_single_line_rjustified(block_gen):
    return SingleLineRJustified(block_gen)
    
def _get_two_line_rjustified(block_gen):
    return TwoLineRJustified(block_gen)
    

BLOC_CREATOR_FUNCS = {AbstractCreditBlock.LAYOUT_SINGLE_LINE_CENTERED:_get_single_line_centered,
                      AbstractCreditBlock.LAYOUT_TWO_LINE_CENTERED:_get_two_line_centered,
                      AbstractCreditBlock.LAYOUT_SINGLE_LINE_RIGHT_JUSTIFIED:_get_single_line_rjustified,
                      AbstractCreditBlock.LAYOUT_TWO_LINE_RIGHT_JUSTIFIED:_get_two_line_rjustified}

"""
class MultiLineAnimation:

    NO_BACKGROUND = 0
    COLOR_BACKGROUND = 1
    LINE_SOLID_BACKGROUND = 2
    LINE_SOLID_WORD_LENGTH_BACKGROUND = 3
    LINE_SOLID_SCREENWIDTH_BACKGROUND = 4
    BOX = 5
    HORIZONTAL_LINES = 6
    UNDERLINE = 7
    STRIKETHROUGHT = 8
    
    CONSTRAINT_OFF = 0   
    CONSTRAINT_CENTER = 1
    CONSTRAINT_HORIZONTAL = 2
    CONSTRAINT_VERTICAL = 3

    NO_ANIM = 0
    FADE = 1
    REVEAL_UP = 2
    REVEAL_DOWN = 3
    REVEAL_LEFT = 4
    REVEAL_RIGHT = 5
    REVEAL_HORIZONTAL = 6
    REVEAL_VERTICAL = 7
    
    def __init__(self, fctx):
        self.linetexts = fctx.get_data_obj("linetexts")
        self.line_gap = fctx.get_editor_value("Line Gap")
        self.pad = fctx.get_editor_value("Background Pad") 
        self.bg_type = fctx.get_editor_value("Background")
        self.bg_color = fctx.get_data_obj("bg_color")
        self.bg_anim_type_in = fctx.get_editor_value("Background Anim In")
        self.bg_frames_in = fctx.get_editor_value("Background Frames In")
        self.bg_anim_type_out = fctx.get_editor_value("Background Anim Out")
        self.bg_frames_out = fctx.get_editor_value("Background Frames Out")

    # -------------------------------------------------- Background dwaring data
    def get_pad(self):
        # There is no bg padding for animations if bg bg drawn.
        if self.bg_type == MultiLineAnimation.NO_BACKGROUND:
            return 0
        else:
            return self.pad

    def get_bounding_rect_for_area(self, fctx):
        # This return text lines bounding rect WITHOUT padding.
        # Get X and Y pos
        x = fctx.get_editor_value("Pos X")
        y = fctx.get_editor_value("Pos Y")

        # Compute height without linetext y data, we don't have it yet. 
        y_bottom = y
        line_w, line_h = self.linetexts[0].pixel_size 
        for line_index in range(0, len(self.linetexts)):
           y_bottom = y_bottom + line_h + self.line_gap  # line_h is same for all line because we always have the same font.
           
        height = y_bottom - fctx.get_editor_value("Pos Y")

        # Compute width.
        max_width = line_w
        for linetext in self.linetexts:
            rw, rh = linetext.pixel_size 
            if rw > max_width:
                max_width = rw

        # Apply Pos constraints
        x, y = self.get_constrained_pos(fctx, x, y, max_width, height)

        return (x, y, max_width, height)
  
    def clip_for_line(self, fctx, cr, line_text, frame):
        # Clipping area depends also on background type, so we do it here instead on LineText.
        rx, ry, rw, rh = line_text.get_bounding_rect_for_line(fctx, self)
        ax, ay, aw, ah = self.area_data # Bounding rect for bg NOT including pads
        p = self.pad
        w, h = line_text.pixel_size
     
        # In and out may have different animations and need different clipping.
        do_clip = False
        line_delay_addition = line_text.line_index * line_text.line_delay  # clipping application time needs to include line delays.
        out_frame_start = fctx.get_length() - line_text.out_frames - 1 - (len(self.linetexts) - 1) * line_text.line_delay

        # In and out animations have different clipping applied and need to be only applied temporally on their own frame ranges.
        if (line_text.animation_type_in in LineText.CLIPPED_ANIMATIONS) and (frame <= line_text.in_frames + line_delay_addition):
            anim_pos = float(frame - line_delay_addition) / float(line_text.in_frames)
            anim_type = line_text.animation_type_in
            do_clip = True
        elif (line_text.animation_type_out in LineText.CLIPPED_ANIMATIONS) and (frame >= out_frame_start):
            anim_pos = float(frame - out_frame_start) / float(line_text.out_frames)
            if anim_pos > 1.0:
                anim_pos = 1.0
            anim_type = line_text.animation_type_out
            if anim_type in LineText.REVEAL_ANIMATIONS:
                # These are in animations reversed.
                anim_pos = 1.0 - anim_pos
            do_clip = True

        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        if do_clip == True:
            # If we are doing reveal animations, use clipping to achieve those.
            if anim_type == LineText.REVEAL_HORIZONTAL:
                x_center = line_text.text_x + w / 2
                w_reveal_size = w / 2 * anim_pos
                cr.rectangle(x_center - w_reveal_size, 0, w_reveal_size * 2, screen_h)
                cr.clip()
            elif anim_type == LineText.REVEAL_VERTICAL:
                y_center = ry + h / 2 - line_text.line_layout.get_top_pad() // 2 + 4 # -15 is a hack because the 
                h_reveal_size = h / 2 * anim_pos
                cr.rectangle(0, y_center - h_reveal_size, screen_w, h_reveal_size * 2)
                cr.clip()
            elif anim_type == LineText.REVEAL_LEFT:
                x = line_text.text_x
                w_reveal_size = w * anim_pos
                cr.rectangle(x, 0, w_reveal_size, screen_h)
                cr.clip()
            elif anim_type == LineText.REVEAL_RIGHT:
                w_reveal_size = w * anim_pos
                x = line_text.text_x + w - w_reveal_size
                cr.rectangle(x, 0, w_reveal_size, screen_h)
                cr.clip()
            # Bg type LINE_SOLID_WORD_LENGTH_BACKGROUND requires clipping to word length during animation.
            elif self.bg_type == MultiLineAnimation.LINE_SOLID_WORD_LENGTH_BACKGROUND:
                cr.rectangle(line_text.text_x - p, ry - p, w + 2 * p, rh + 2 * p)
                cr.clip()
            else:
                # We give full non-affected dimension to allow for big y-Off values
                # in some animation types
                if anim_type in LineText.HORIZONTAL_ANIMATIONS:
                    cr.rectangle(rx - p, 0, aw + 2 * p, screen_h)
                    cr.clip()
                elif anim_type in LineText.VERTICAL_ANIMATIONS:
                    cr.rectangle(0, ry - p, screen_w, rh + 2 * p)
                    cr.clip()
                else:
                    # We should not hit this, but let's clip full text area if we're wrong.
                    cr.rectangle(ax - p, ay - p, aw + 2 * p, ah + 2 * p)
                    cr.clip()
        else:
            # Make sure earlier clipping does not affect us.
            cr.rectangle(0, 0, screen_w, screen_h)
            cr.clip()
            
    def get_constrained_pos(self, fctx, x, y, w, h):
        # Returns area position with centering applied.
        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        constraints = fctx.get_editor_value("Centering")
        if constraints == MultiLineAnimation.CONSTRAINT_CENTER or constraints == MultiLineAnimation.CONSTRAINT_HORIZONTAL:
            x = round(screen_w / 2 - w / 2)
        if constraints == MultiLineAnimation.CONSTRAINT_CENTER or constraints == MultiLineAnimation.CONSTRAINT_VERTICAL:
            y = round(screen_h / 2 - h / 2)
        
        return (x, y)

    def clip_bg_for_anim(self, fctx, cr, frame):
        ax, ay, aw, ah = self.area_data
        p = self.pad
        ax = ax - p
        ay = ay - p
        aw = aw + 2 * p
        ah = ah + 2 * p        
    
        # In and out may have different animations and need different clipping.
        do_clip = False
        anim_type = MultiLineAnimation.NO_ANIM
        anim_pos = -10.0

        if frame <= self.bg_frames_in:
            anim_pos = float(frame) / float(self.bg_frames_in)
            anim_type = self.bg_anim_type_in 
            do_clip = True
        elif frame >= fctx.get_length() - self.bg_frames_out:
            anim_pos = 1.0 - float(frame - fctx.get_length() + self.bg_frames_out) / float(self.bg_frames_out)
            anim_type = self.bg_anim_type_out
            do_clip = True
 
        if do_clip == True and anim_type != MultiLineAnimation.NO_ANIM and anim_type != MultiLineAnimation.FADE:
            if anim_type == MultiLineAnimation.REVEAL_HORIZONTAL:
                x_center = ax + aw / 2
                w_reveal_size = aw / 2 * anim_pos
                cr.rectangle(x_center - w_reveal_size, ay, w_reveal_size * 2, ah)
                cr.clip()
            elif anim_type == MultiLineAnimation.REVEAL_VERTICAL:
                y_center = ay + ah / 2 
                h_reveal_size = ah / 2 * anim_pos
                cr.rectangle(ax, y_center - h_reveal_size, aw, h_reveal_size * 2)
                cr.clip()
            elif anim_type == MultiLineAnimation.REVEAL_LEFT:
                w_reveal_size = aw * anim_pos
                cr.rectangle(ax, ay, w_reveal_size, ah)
                cr.clip()
            elif anim_type == MultiLineAnimation.REVEAL_RIGHT:
                w_reveal_size = aw * anim_pos
                x = ax + aw - w_reveal_size
                cr.rectangle(x, ay, w_reveal_size, ah)
                cr.clip()
            elif anim_type == MultiLineAnimation.REVEAL_UP:
                h_reveal_size = ah * anim_pos
                cr.rectangle(ax, ay + ah - h_reveal_size, aw, h_reveal_size)
                cr.clip()
            elif anim_type == MultiLineAnimation.REVEAL_DOWN:
                h_reveal_size = ah * anim_pos
                cr.rectangle(ax, ay, aw, h_reveal_size)
                cr.clip()

        # We need this data to do fades next if needed.
        return (anim_type, anim_pos)

    # ------------------------------------------------------------- DRAWING
    def draw(self, cr, fctx, frame):
        # Create layouts now that we have cairo.Context.
        for linetext in self.linetexts:
            linetext.create_layout_data(fctx, cr)

        # We can only compute bg dimensions now that we have linetext layouts.
        self.area_data = self.get_bounding_rect_for_area(fctx)
        
        # Create animation data for textlines. We need bg dimensions data for that.
        for linetext in self.linetexts:
            linetext.create_animation_data(fctx, self)
     
        # Draw background
        cr.save()
        anim_data = self.clip_bg_for_anim(fctx, cr, frame)
        self.draw_bg(cr, fctx, frame, anim_data)
        cr.restore()

        # Draw texts
        for linetext in self.linetexts:
            linetext.draw_text(fctx, frame, cr, self)
        
    def draw_bg(self, cr, fctx, frame, anim_data):
        ax, ay, aw, ah = self.area_data
        p = self.pad
        ax = ax - p
        ay = ay - p
        aw = aw + 2 * p
        ah = ah + 2 * p
        
        line_width = fctx.get_editor_value("Background Line Width")
        cr.set_line_width(line_width)
        anim_type, anim_pos = anim_data
        if anim_type == MultiLineAnimation.FADE and anim_pos >= 0.0:
            r, g, b, a = self.bg_color.get_rgba()
            a = a * anim_pos
            fade_bg = cairo.SolidPattern(r, g, b, a)
            cr.set_source(fade_bg)
        else:
            cr.set_source(self.bg_color)

        if self.bg_type == MultiLineAnimation.COLOR_BACKGROUND:
            cr.rectangle(ax, ay, aw, ah)
            cr.fill()
        elif self.bg_type == MultiLineAnimation.LINE_SOLID_BACKGROUND:
            ax, ay, aw, ah = self.area_data
            for linetext in self.linetexts:
                rx, ry, rw, rh = linetext.get_bounding_rect_for_line(fctx, self)
                cr.rectangle(rx - p, ry - p, aw + 2 * p, rh + 2 * p)
                cr.fill()
        elif self.bg_type == MultiLineAnimation.LINE_SOLID_WORD_LENGTH_BACKGROUND:
            for linetext in self.linetexts:
                w, h = linetext.pixel_size
                rx, ry, rw, rh = linetext.get_bounding_rect_for_line(fctx, self)
                cr.rectangle(linetext.text_x - p, ry - p, w + 2 * p, rh + 2 * p)
                cr.fill()
        elif self.bg_type == MultiLineAnimation.LINE_SOLID_SCREENWIDTH_BACKGROUND:
            screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
            for linetext in self.linetexts:
                w, h = linetext.pixel_size
                rx, ry, rw, rh = linetext.get_bounding_rect_for_line(fctx, self)
                cr.rectangle(0, ry - p, screen_w + 1, rh + 2 * p)
                cr.fill()
        elif self.bg_type == MultiLineAnimation.BOX:
            cr.rectangle(ax, ay, aw, ah)
            cr.stroke()
        elif self.bg_type == MultiLineAnimation.HORIZONTAL_LINES:
            cr.move_to(ax, ay)
            cr.line_to(ax + aw, ay)
            cr.move_to(ax, ay + ah)
            cr.line_to(ax + aw, ay + ah)
            cr.stroke()
        elif self.bg_type == MultiLineAnimation.UNDERLINE:
            for linetext in self.linetexts:
                w, h = linetext.pixel_size
                rx, ry, rw, rh = linetext.get_bounding_rect_for_line(fctx, self)
                y = ry - p + rh + 2 * p            
                cr.move_to(linetext.text_x - p, y)
                cr.line_to(linetext.text_x - p + w + 2 * p, y)
                cr.stroke()
        elif self.bg_type == MultiLineAnimation.STRIKETHROUGHT:
            for linetext in self.linetexts:
                w, h = linetext.pixel_size
                rx, ry, rw, rh = linetext.get_bounding_rect_for_line(fctx, self)
                y = ry + rh / 2            
                cr.move_to(linetext.text_x - p, y)
                cr.line_to(linetext.text_x - p + w + 2 * p, y)
                cr.stroke()

    

class LineText:

    ANIMATION_NONE = 0
    FROM_LEFT_CLIPPED = 1
    FROM_RIGHT_CLIPPED = 2
    FROM_UP_CLIPPED = 3
    FROM_DOWN_CLIPPED = 4
    FROM_LEFT = 5
    FROM_RIGHT = 6
    FROM_UP = 7
    FROM_DOWN = 8
    REVEAL_HORIZONTAL = 9
    REVEAL_VERTICAL = 10
    REVEAL_LEFT = 11
    REVEAL_RIGHT = 12
    
    ANIMATION_IN = 0
    ANIMATION_OUT = 1
    
    FADE_LINEAR = 0
    FADE_COMPACT = 1
    
    HORIZONTAL_ANIMATIONS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED, FROM_LEFT, FROM_RIGHT]
    VERTICAL_ANIMATIONS = [FROM_UP_CLIPPED, FROM_DOWN_CLIPPED, FROM_UP, FROM_DOWN]
    CLIPPED_ANIMATIONS = [FROM_LEFT_CLIPPED, FROM_RIGHT_CLIPPED, FROM_UP_CLIPPED, FROM_DOWN_CLIPPED, REVEAL_HORIZONTAL, REVEAL_VERTICAL, REVEAL_LEFT, REVEAL_RIGHT]
    REVEAL_ANIMATIONS = [REVEAL_HORIZONTAL, REVEAL_VERTICAL, REVEAL_LEFT, REVEAL_RIGHT]
    
    def __init__(self, text, font_data, user_pos, line_info, animation_in_data, in_frames, animation_out_data, out_frames):
        self.text = text
        self.font_data = font_data
        user_x, user_y = user_pos
        self.multiline_pos = user_pos # Top-left x,y of multiline text object position. These coordinates have been given by user.
        self.text_x = user_x # This needs layout data and will be computed later. Center and right justified lines will get changed x pos when line lengths are known.
        self.text_y = -1 # This needs layout data and will be computed later.
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
        # that are re-created for every new frame. Caching them somehow worked, but changed it to be sure.
        self.line_layout = fctx.create_text_layout(self.font_data)
        self.line_layout.create_pango_layout(cr, self.text)
        self.pixel_size = self.line_layout.pixel_size

    def create_animation_data(self, fctx, multiline_animation):
        # We need cairo.Context to be available to create layouts and do position calculations,
        # so we have do this on first frame when render_frame(frame, fctx, w, h) called.
        if self.affine != None:
            # We've done this already.
            return

        self.affine = fluxity.AffineTransform()
        self.opacity = fluxity.AnimatedValue()
        
        self._compute_line_position(fctx, multiline_animation)
        
        # Animation In
        start_x, start_y, end_x, end_y = self._get_in_animation_affine_data(fctx, multiline_animation)
 
        frame_start = 0
        length = self.in_frames
        movement_type = self.movement_type_in
        animation_type = self.animation_type_in
        self._apply_affine_data_with_movement(movement_type, animation_type, start_x, \
                                              start_y, end_x, end_y, \
                                              frame_start, length, self.steps_in)

        
        # Animation Out
        start_x, start_y, end_x, end_y = self._get_out_animation_affine_data(fctx, multiline_animation)
        # We need to shorten static lengths depending on line delay here to get all animations to complete.
        frame_start = fctx.get_length() - self.out_frames - 1 - (len(multiline_animation.linetexts) - 1) * self.line_delay
        length = self.out_frames

        movement_type = self.movement_type_out
        animation_type = self.animation_type_out

        self._apply_affine_data_with_movement(movement_type, animation_type, start_x, \
                                              start_y, end_x, end_y, \
                                              frame_start, length, self.steps_out)

        self._apply_fade(fctx)

    def _compute_line_position(self, fctx, multiline_animation):
        # Apply line y-offset, alignment and centering.
        # Compute line x position for user selected alignment.
        area_x, area_y, max_width, area_height = multiline_animation.area_data
        line_w, line_h = self.pixel_size
        x = self.text_x 
        
        pango_alignment = self.line_layout.get_pango_alignment()
        if pango_alignment == Pango.Alignment.LEFT:
            pass
        elif pango_alignment == Pango.Alignment.CENTER:
            self.text_x = x + max_width/2 - line_w/2
        else: # Pango.Alignment.RIGHT
            self.text_x = x + max_width - line_w
            
        line_x_off = self.text_x - fctx.get_editor_value("Pos X")
        
        # Compute line y position for line_index.
        y = fctx.get_editor_value("Pos Y")
        for line_index in range(self.line_index):
           y = y + line_h + self.line_gap  # line_h is same for all line because we always have the same font.

        self.text_y = y
        line_y_off = y - fctx.get_editor_value("Pos Y")
        
        # Apply Pos constraints
        constrained_x, constrained_y = multiline_animation.get_constrained_pos(fctx, self.text_x, self.text_y, max_width, area_height)
        # Reapply alignment if horizontal constraint applied.
        if constrained_x != self.text_x:
            self.text_x = constrained_x + line_x_off
        # Reapply line y off if vertical constraint applied.
        if constrained_y != self.text_y:
            self.text_y = constrained_y + line_y_off
        
    def _get_in_animation_affine_data(self, fctx, multiline_animation):
        # static_x, static_y is the position line is stopped between in and out animations.
        static_x = self.text_x
        static_y = self.text_y
        multiline_x, multiline_y = self.multiline_pos

        # Additional parameters needed to compute animations.
        line_w, line_h,\
        screen_w, screen_h,\
        pad, bw, bg_padded_w, bg_padded_h = self._get_basic_animation_data(fctx, multiline_animation)
        
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
            start_y = static_y - line_h - pad
        elif self.animation_type_in == LineText.FROM_DOWN_CLIPPED:
            start_x = static_x
            start_y = static_y + line_h + pad * 2
        elif self.animation_type_in == LineText.FROM_LEFT:
            start_x = -bw
            start_y = static_y
        elif self.animation_type_in == LineText.FROM_RIGHT:
            start_x = screen_w
            start_y = static_y
        elif self.animation_type_in == LineText.FROM_UP:
            start_x = static_x
            start_y = -bg_padded_h + static_y - multiline_y
        elif self.animation_type_in == LineText.FROM_DOWN:
            start_x = static_x
            start_y = screen_h + static_y - multiline_y
        elif self.animation_type_in == LineText.REVEAL_HORIZONTAL or self.animation_type_in == LineText.REVEAL_VERTICAL \
            or self.animation_type_in == LineText.REVEAL_LEFT or self.animation_type_in == LineText.REVEAL_RIGHT:
            start_x = static_x
            start_y = static_y
        elif self.animation_type_in == LineText.ANIMATION_NONE:
            end_x = static_x
            end_y = static_y
            
        return (start_x, start_y + self.line_y_off, end_x, end_y + self.line_y_off)

    def _get_out_animation_affine_data(self, fctx, multiline_animation):
        # static_x, static_y is the position line is stopped between in and out animations.
        static_x = self.text_x
        static_y = self.text_y
        multiline_x, multiline_y = self.multiline_pos
        
        # Additional parameters needed to compute animations.
        line_w, line_h,\
        screen_w, screen_h,\
        pad, bw, bg_padded_w, bg_padded_h = self._get_basic_animation_data(fctx, multiline_animation)

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
            end_y = static_y - line_h - pad
        elif self.animation_type_out == LineText.FROM_DOWN_CLIPPED:
            end_x = static_x + pad 
            end_y = static_y + line_h + pad * 2
        elif self.animation_type_out == LineText.FROM_LEFT:
            end_x = -bw
            end_y = static_y
        elif self.animation_type_out == LineText.FROM_RIGHT:
            end_x = screen_w
            end_y = static_y
        elif self.animation_type_out == LineText.FROM_UP:
            end_x = static_x + pad
            end_y = -bg_padded_h + static_y - multiline_y
        elif self.animation_type_out == LineText.FROM_DOWN:
            end_x = static_x + pad
            end_y = screen_h + static_y - multiline_y
        elif self.animation_type_out == LineText.REVEAL_HORIZONTAL or self.animation_type_out == LineText.REVEAL_VERTICAL \
            or self.animation_type_out == LineText.REVEAL_LEFT or self.animation_type_out == LineText.REVEAL_RIGHT:
            end_x = static_x
            end_y = static_y
        elif self.animation_type_out == LineText.ANIMATION_NONE:
            end_x = static_x
            end_y = static_y
            
        return (start_x, start_y + self.line_y_off, end_x, end_y + self.line_y_off)

    def _get_basic_animation_data(self, fctx, multiline_animation):
        lx, ly, line_w, line_h = self.get_bounding_rect_for_line(fctx, multiline_animation)

        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)

        bx, by, bw, bh = multiline_animation.area_data
        pad = multiline_animation.get_pad() # this will be 0 if no bg drawn, pad affects animation distance.

        bg_padded_w = bw + 2 * pad
        bg_padded_h = bh + 2 * pad

        return (line_w, line_h, screen_w, screen_h, pad, bw, bg_padded_w, bg_padded_h)
        
    def _apply_affine_data_with_movement(self, movement_type, animation_type, start_x, start_y, end_x, end_y, \
                                         frame_start, frame_end, steps):
        builder = AnimationBuilder()
        
        if movement_type == AnimationBuilder.LINEAR or animation_type in LineText.REVEAL_ANIMATIONS:
            builder.apply_linear_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
            builder.apply_linear_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
        elif movement_type == AnimationBuilder.EASE_IN:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                builder.apply_ease_in_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
                builder.apply_no_movement(self.affine.y, start_y, frame_start)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                builder.apply_no_movement(self.affine.x, start_x, frame_start)
                builder.apply_ease_in_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
        elif movement_type == AnimationBuilder.EASE_OUT:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                builder.apply_ease_out_movement(self.affine.x, start_x, end_x, frame_start, frame_end)
                builder.apply_no_movement(self.affine.y, start_y, frame_start)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                builder.apply_no_movement(self.affine.x, start_x, frame_start)
                builder.apply_ease_out_movement(self.affine.y, start_y, end_y, frame_start, frame_end)
        elif movement_type == AnimationBuilder.STEPPED:
            if animation_type in LineText.HORIZONTAL_ANIMATIONS:
                builder.apply_stepped_movement(self.affine.x, start_x, end_x, frame_start, frame_end, steps)
                builder.apply_no_movement(self.affine.y, start_y, frame_start)
            elif animation_type in LineText.VERTICAL_ANIMATIONS:
                builder.apply_no_movement(self.affine.x, start_x, frame_start)
                builder.apply_stepped_movement(self.affine.y, start_y, end_y, frame_start, frame_end, steps)

    def _apply_fade(self, fctx):
        self.opacity.add_keyframe_at_frame(0, 0.0, fluxity.KEYFRAME_LINEAR)
        frame_delay = self.line_index * self.line_delay
        fade_in_type = fctx.get_editor_value("Fade In Type")
        fade_out_type = fctx.get_editor_value("Fade Out Type")
        
        if frame_delay > 0:
            self.opacity.add_keyframe_at_frame(frame_delay, 0.0, fluxity.KEYFRAME_LINEAR)
         
        if fade_in_type == LineText.FADE_COMPACT:
            # Fade value curve for compact in:
            #    /
            #   /
            #--
            self.opacity.add_keyframe_at_frame(frame_delay + int(round(self.fade_in_frames / 2.0)), 0.0, fluxity.KEYFRAME_LINEAR) # With self.fade_in_frames == 0 this replaces kf from line above.
            
        self.opacity.add_keyframe_at_frame(frame_delay + self.fade_in_frames, 1.0, fluxity.KEYFRAME_LINEAR) # With self.fade_in_frames == 0 this replaces kf from line above.
        if self.fade_out_frames > 0:
            self.opacity.add_keyframe_at_frame(fctx.get_length() - self.fade_out_frames - 1 + frame_delay, 1.0, fluxity.KEYFRAME_LINEAR)
            if fade_out_type == LineText.FADE_COMPACT:
                # Fade value curve for compact out:
                #\
                # \
                #  --
                self.opacity.add_keyframe_at_frame(fctx.get_length() - int(round(self.fade_out_frames / 2.0)) - 1 + frame_delay, 0.0, fluxity.KEYFRAME_LINEAR) # With self.fade_in_frames == 0 this replaces kf
            self.opacity.add_keyframe_at_frame(fctx.get_length() - 1  + frame_delay, 0.0, fluxity.KEYFRAME_LINEAR)

    def get_bounding_rect_for_line(self, fctx, multiline_animation):
        bx, by, bw, bh = multiline_animation.area_data
        lw, lh = self.pixel_size
        top_pad = self.line_layout.get_top_pad()
 
        rx = bx # Bounding rect is for LINE not text, to the full to width of multiline area, not text so justifucation has no effect.
        ry = self.text_y
        rw = bw
        rh = lh - top_pad
        
        return (rx, ry, rw, rh)
    
    def draw_text(self, fctx, frame, cr, multiline_animation):

        cr.save() # Same cairo.Context object used for all lines, so we need to restore() after clip and transform.

        multiline_animation.clip_for_line(fctx, cr, self, frame)

        # Don't draw if line delay causes line to not start animating yet.
        # NOTE: We are are implementing line delay here, combined with shortening static position 
        # time in LineText.create_animation_data() and setting clipping times in 
        # Multiline.clip_for_line() so that all out animations have time
        # to complete and are clipped at correct times.
        frame_delay = self.line_index * self.line_delay
        line_frame = frame - frame_delay
        if line_frame < 0:
            cr.restore()
            return

        self.affine.apply_transform(cr, line_frame)
        self.line_layout.set_opacity(self.opacity.get_value(frame))
        self.line_layout.draw_layout(fctx, self.text, cr, 0, 0)

        cr.restore()



class AnimationBuilder:

    LINEAR = 0
    EASE_IN = 1
    EASE_OUT = 2
    STEPPED = 3
    
    def __init__(self):
        pass
        
    def apply_no_movement(self, animated_value, value, frame):
        animated_value.add_keyframe_at_frame(frame, value, fluxity.KEYFRAME_LINEAR)
           
    def apply_linear_movement(self, animated_value, start_val, end_val, start_frame, length):
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_LINEAR)   
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)
    
    def apply_ease_in_movement(self, animated_value, start_val, end_val, start_frame, length):
        mid_kf_frame = int(length * 0.375)
        mid_kf_value = start_val + (end_val - start_val) * 0.70
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + mid_kf_frame, mid_kf_value, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)

    def apply_ease_out_movement(self, animated_value, start_val, end_val, start_frame, length):
        mid_kf_frame = int(length * 0.625)
        mid_kf_value = start_val + (end_val - start_val) * 0.3
        animated_value.add_keyframe_at_frame(start_frame, start_val, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + mid_kf_frame, mid_kf_value, fluxity.KEYFRAME_SMOOTH)
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_LINEAR)

    def apply_stepped_movement(self, animated_value, start_val, end_val, start_frame, length, steps):
        step_frames = int(round(length/steps))
        step_value = (end_val - start_val)/(steps) 
        for i in range(0, steps):
            frame = int(start_frame + i * step_frames)
            value = start_val + step_value * i
            animated_value.add_keyframe_at_frame(frame, value, fluxity.KEYFRAME_DISCRETE)
        animated_value.add_keyframe_at_frame(start_frame + length, end_val, fluxity.KEYFRAME_DISCRETE) # maybe KEYFRAME_LINEAR but should not make difference.
"""
