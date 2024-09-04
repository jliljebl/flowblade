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
Carl Carruthers
"""

def init_script(fctx):
    fctx.set_name("Scrolling Credits")
    fctx.set_version(2)
    fctx.set_author("Janne Liljeblad")

    fctx.add_editor_group("Layout")
    fctx.add_editor("Credits Layout", fluxity.EDITOR_OPTIONS, (0, ["Single Line Centered", "Two Line Centered", "Single Line Right Justified", "Two Line Right Justified"]))
    fctx.add_editor("Center Gap", fluxity.EDITOR_INT, 30)
    fctx.add_editor("Credit Block Gap", fluxity.EDITOR_INT, 40)
    fctx.add_editor("Line Gap", fluxity.EDITOR_INT, 0)
    fctx.add_editor("Horizontal X Position", fluxity.EDITOR_INT, 150)
    fctx.add_editor("Name X Offset", fluxity.EDITOR_INT, 0)
    fctx.add_editor("Credit Name Gap", fluxity.EDITOR_INT, 0)
    fctx.add_editor("Background", fluxity.EDITOR_OPTIONS, (0, ["Transparent", "Solid Color"]))
    fctx.add_editor("Background Color", fluxity.EDITOR_COLOR, (1.0, 1.0, 1.0, 1.0))

    fctx.add_editor_group("Fonts")
    font_default_values = ("Liberation Sans", "Regular", 50, Pango.Alignment.LEFT, (0.0, 0.0, 0.0, 1.0), \
                       True, (0.3, 0.3, 0.3, 1.0) , False, 2, False, (0.0, 0.0, 0.0), \
                       100, 3, 3, 0.0, None, fluxity.VERTICAL)
    fctx.add_editor("Credit Font", fluxity.EDITOR_PANGO_FONT, font_default_values)
    fctx.add_editor("Name Font", fluxity.EDITOR_PANGO_FONT, font_default_values)
    fctx.add_editor("Use Credit Font for Name", fluxity.EDITOR_CHECK_BOX, False)
    fctx.add_editor("Section Title Font", fluxity.EDITOR_PANGO_FONT, font_default_values)
    fctx.add_editor("Use Credit Font for Section Title", fluxity.EDITOR_CHECK_BOX, False)

    fctx.add_editor_group("Animation")
    fctx.add_editor("Speed", fluxity.EDITOR_FLOAT_RANGE, (10.0, 0.0, 40.0))

    fctx.add_editor_group("Text")
    fctx.add_editor("Text", fluxity.EDITOR_TEXT_AREA, DEFAULT_SCROLL_MARKUP_TEXT)

    
def init_render(fctx):
    # Get editor values
    
    """
     hue = fctx.get_editor_value("Background Color")
    r, g, b, alpha = hue
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
        BLOCK_GAP = fctx.get_editor_value("Credit Block Gap")
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
 
        CENTER_GAP =  fctx.get_editor_value("Center Gap")
        LINE_GAP =  fctx.get_editor_value("Line Gap")
        
        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        
        # Compute layout positions data.
        names_height = 0
        for layout in self.name_layouts:
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            names_height += (h + LINE_GAP)
    
        names_height = names_height - LINE_GAP
        fctx.log_line("names_height:" + str(names_height))
    
        cw, ch = self.credit_pixel_size

        total_height = names_height
        if total_height < ch:
            total_height = ch
        
        # Create draw items
        self.add_text_draw_item(self.credit_title,screen_w / 2.0 - cw - CENTER_GAP / 2.0, 0, mutable_layout_data["credit_font_data"])
        
        y = 0
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, screen_w / 2 + CENTER_GAP / 2.0, y, mutable_layout_data["name_font_data"])
            y += (h + LINE_GAP)

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
