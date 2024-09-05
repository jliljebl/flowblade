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
COMMAND_INSIDE_CREDIT_BLOCK_ERROR = 4
BAD_ARGUMENT_COUNT_ERROR = 5
BAD_ARGUMENT_TYPE_ERROR = 6
BAD_ARGUMENT_VALUE_ERROR = 7

DEFAULT_SCROLL_MARKUP_TEXT = \
"""
# CREDIT TITLE1
Alice Andersson

# CREDIT TITLE2
Bob Banner
Carl Carruthers

! ypad 40
! set-layout single-line-sides-justified

# CREDIT TITLE3
Donald Drake
Earl Easter
"""

def init_script(fctx):
    pypes = [int, int, str]
    fctx.log_line(str(pypes))
    fctx.set_name("Scrolling Credits")
    fctx.set_version(2)
    fctx.set_author("Janne Liljeblad")

    fctx.add_editor_group("Layout")
    fctx.add_editor("Credits Layout", fluxity.EDITOR_OPTIONS, (0, ["Single Line Centered", "Two Line Centered", "Single Line Right Justified", "Two Line Right Justified",
                    "Single Line Sides Justified", "Two Line Left Justified"]))
    fctx.add_editor("Center Gap", fluxity.EDITOR_INT, 30)
    fctx.add_editor("Credit Block Gap", fluxity.EDITOR_INT, 40)
    fctx.add_editor("Line Gap", fluxity.EDITOR_INT, 0)
    fctx.add_editor("Justified X Position", fluxity.EDITOR_INT, 150)
    fctx.add_editor("Justified X Position Offset", fluxity.EDITOR_INT, 1300)
    fctx.add_editor("Name X Offset", fluxity.EDITOR_INT, 0)
    fctx.add_editor("Name Y Offset", fluxity.EDITOR_INT, 0)
    fctx.add_editor("Background", fluxity.EDITOR_OPTIONS, (1, ["Transparent", "Solid Color"]))
    fctx.add_editor("Background Color", fluxity.EDITOR_COLOR, (1.0, 1.0, 1.0, 1.0))

    fctx.add_editor_group("Fonts")
    font_default_values = ("Liberation Sans", "Regular", 35, Pango.Alignment.LEFT, (0.0, 0.0, 0.0, 1.0), \
                       True, (0.3, 0.3, 0.3, 1.0) , False, 2, False, (0.0, 0.0, 0.0), \
                       100, 3, 3, 0.0, None, fluxity.VERTICAL)
    fctx.add_editor("Credit Font", fluxity.EDITOR_PANGO_FONT, font_default_values)
    fctx.add_editor("Creadit Case", fluxity.EDITOR_OPTIONS, (0, ["No Changes", "Uppercase", "Lowercase"]))
    fctx.add_editor("Name Font", fluxity.EDITOR_PANGO_FONT, font_default_values)
    fctx.add_editor("Name Case", fluxity.EDITOR_OPTIONS, (0, ["No Changes", "Uppercase", "Lowercase"]))
    fctx.add_editor("Use Credit Font for Name", fluxity.EDITOR_CHECK_BOX, False)
    fctx.add_editor("Section Title Font", fluxity.EDITOR_PANGO_FONT, font_default_values)
    fctx.add_editor("Section Title Case", fluxity.EDITOR_OPTIONS, (0, ["No Changes", "Uppercase", "Lowercase"]))
    fctx.add_editor("Use Credit Font for Section Title", fluxity.EDITOR_CHECK_BOX, False)

    fctx.add_editor_group("Animation")
    fctx.add_editor("Speed", fluxity.EDITOR_FLOAT_RANGE, (10.0, 0.0, 40.0))

    fctx.add_editor_group("Text")
    fctx.add_editor("Text", fluxity.EDITOR_TEXT_AREA, DEFAULT_SCROLL_MARKUP_TEXT)

def init_render(fctx):
    text = fctx.get_editor_value("Text")
    lines = text.splitlines()
    blocks_generator = ScrollBlocksGenerator(lines, fctx)
    scroll_blocks, err = blocks_generator.get_blocks()
    #fctx.log_line("blocks count " + str(len(scroll_blocks)))
    #fctx.log_line("BLOCKS")
    for block in scroll_blocks:
        fctx.log_line(str(block))
    fctx.set_data_obj("scroll_blocks", scroll_blocks)

def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    bg_selection = fctx.get_editor_value("Background")

    if bg_selection == 1:
        hue = fctx.get_editor_value("Background Color")
        bg_color = cairo.SolidPattern(*hue)
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
        self.print_line(LINE_TYPE_COMMAND, line)
        
        if self.state == STATE_WAITING_NEXT_NAME:
            self.add_error(COMMAND_INSIDE_CREDIT_BLOCK_ERROR, line)
            return
        
        tokens = line.split(" ")
        command_block_creator_func = COMMAND_CREATOR_FUNCS[tokens[1]]
        block = command_block_creator_func(tokens)
        err = block.check_command(self.fctx)
        self.fctx.log_line("error:" + str(err))
        block.exec_parse_command(self)
        self.blocks.append(block)

        log_str = "adding command block, line " + str(self.current_line) + " " + str(block)
        self.fctx.log_line(log_str)

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
        
        if fctx.get_editor_value("Use Credit Font for Name") == False:
            name_font = fctx.get_editor_value("Name Font")
        else:
            name_font = fctx.get_editor_value("Credit Font")

        mutable_layout_data = fctx.get_editors_values_clone_dict()

        if fctx.get_editor_value("Use Credit Font for Name") == True:
            mutable_layout_data["Name Font"] = fctx.get_editor_value("Credit Font") 

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

    def exec_parse_command(self, block_generator):
        pass
        
    def draw(self, fctx, cr, y):
        pass

    def _get_height_str(self):
        return "block_height: " + str(self.block_height)

    def __str__(self):
        return "AbstractBlock, " + self._get_height_str()


# ----------------------------------------------------- CREDIT BLOCKS

class AbstractCreditBlock(AbstractBlock):
    
    # These indexs must match those in editor "Credits Layout".
    LAYOUT_SINGLE_LINE_CENTERED = 0
    LAYOUT_TWO_LINE_CENTERED = 1
    LAYOUT_SINGLE_LINE_RIGHT_JUSTIFIED = 2
    LAYOUT_TWO_LINE_RIGHT_JUSTIFIED = 3
    LAYOUT_SINGLE_SIDES_JUSTIFIED = 4
    LAYOUT_TWO_LINE_LEFT_JUSTIFIED = 5
    
    # These indexs must match those in editors "Creadit Case" etc.
    CASE_NO_CHANGES = 0
    CASE_UPPERCASE = 1
    CASE_LOWERCASE = 2

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
        self.credit_layout = fctx.create_text_layout(mutable_layout_data["Credit Font"])
        self.credit_layout.create_pango_layout(cr, self.credit_title)
        self.credit_pixel_size = self.credit_layout.pixel_size

        self.name_layouts = []
        self.names_height = 0
        self.names_width = 0
        line_gap = fctx.get_editor_value("Line Gap")
        for name in self.names:
            name_layout = fctx.create_text_layout(mutable_layout_data["Name Font"])
            name_layout.create_pango_layout(cr, name)
            name_pixel_size = name_layout.pixel_size
            w, h = name_pixel_size
            if w > self.names_width:
                self.names_width = w
            self.name_layouts.append((name_layout, name_pixel_size))
            self.names_height = self.names_height + h + line_gap
        self.names_height = self.names_height - line_gap

    def get_layout_data(self, fctx, mutable_layout_data):
        return (mutable_layout_data["Center Gap"], mutable_layout_data["Line Gap"],
                mutable_layout_data["Justified X Position"],
                mutable_layout_data["Name Y Offset"], mutable_layout_data["Name X Offset"],
                mutable_layout_data["Creadit Case"], mutable_layout_data["Name Case"],
                fctx.get_profile_property(fluxity.PROFILE_WIDTH), fctx.get_profile_property(fluxity.PROFILE_HEIGHT))

    def add_text_draw_item(self, text, x, y, font_data, case):
        if case == AbstractCreditBlock.CASE_UPPERCASE:
            text = text.upper()
        elif case == AbstractCreditBlock.CASE_LOWERCASE:
            text = text.lower()
                    
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
 
        center_gap, line_gap, justified_x, name_y_off, name_x_off, credit_case, name_case, \
        screen_w, screen_h = self.get_layout_data(fctx, mutable_layout_data)
        
        cw, ch = self.credit_pixel_size

        total_height = self.names_height
        if total_height < ch:
            total_height = ch

        # Create draw items
        self.add_text_draw_item(self.credit_title,screen_w / 2.0 - cw - center_gap / 2.0, 0, mutable_layout_data["Credit Font"], credit_case)
        
        y =  name_y_off
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, screen_w / 2 + center_gap / 2.0 + name_x_off, y, mutable_layout_data["Name Font"], name_case)
            y += (h + line_gap)

        self.block_height = y - line_gap + name_y_off

class TwoLineCentered(AbstractCreditBlock):

    def __init__(self, block_gen):
        AbstractCreditBlock.__init__(self, block_gen)

    def init_layout(self, fctx, cr, frame, mutable_layout_data):
        self.create_layouts(fctx, cr, mutable_layout_data)
 
        center_gap, line_gap, justified_x, name_y_off, name_x_off, credit_case, name_case, \
        screen_w, screen_h = self.get_layout_data(fctx, mutable_layout_data)
        
        cw, ch = self.credit_pixel_size

        # Create draw items
        self.add_text_draw_item(self.credit_title,screen_w / 2.0 - cw / 2.0, 0, mutable_layout_data["Credit Font"], name_case)
        
        y =  ch +  name_y_off
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, screen_w / 2 - w / 2.0 + name_x_off, y, mutable_layout_data["Name Font"], credit_case)
            y += (h + line_gap)

        self.block_height = y - line_gap

class SingleLineRJustified(AbstractCreditBlock):

    def __init__(self, block_gen):
        AbstractCreditBlock.__init__(self, block_gen)

    def init_layout(self, fctx, cr, frame, mutable_layout_data):
        self.create_layouts(fctx, cr, mutable_layout_data)
 
        center_gap, line_gap, justified_x, name_y_off, name_x_off, credit_case, name_case, \
        screen_w, screen_h = self.get_layout_data(fctx, mutable_layout_data)
        
        cw, ch = self.credit_pixel_size

        # Create draw items
        self.add_text_draw_item(self.credit_title, justified_x, 0, mutable_layout_data["Credit Font"], name_case)
        
        y =  name_y_off
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, justified_x + cw + name_x_off + center_gap, y, mutable_layout_data["Name Font"], credit_case)
            y += (h + line_gap)

        self.block_height = y - line_gap + name_y_off

class TwoLineRJustified(AbstractCreditBlock):

    def __init__(self, block_gen):
        AbstractCreditBlock.__init__(self, block_gen)

    def init_layout(self, fctx, cr, frame, mutable_layout_data):
        self.create_layouts(fctx, cr, mutable_layout_data)
 
        center_gap, line_gap, justified_x, name_y_off, name_x_off, credit_case, name_case, \
        screen_w, screen_h = self.get_layout_data(fctx, mutable_layout_data)
        
        cw, ch = self.credit_pixel_size

        # Create draw items
        self.add_text_draw_item(self.credit_title, justified_x, 0, mutable_layout_data["Credit Font"], name_case)
        
        y = ch +  name_y_off
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, justified_x + name_x_off, y, mutable_layout_data["Name Font"], credit_case)
            y += (h + line_gap)

        self.block_height = y - line_gap

class SingleSidesJustified(AbstractCreditBlock):

    def __init__(self, block_gen):
        AbstractCreditBlock.__init__(self, block_gen)

    def init_layout(self, fctx, cr, frame, mutable_layout_data):
        self.create_layouts(fctx, cr, mutable_layout_data)
 
        center_gap, line_gap, justified_x, name_y_off, name_x_off, credit_case, name_case, \
        screen_w, screen_h = self.get_layout_data(fctx, mutable_layout_data)
        justified_x_offset = fctx.get_editor_value("Justified X Position Offset")
                        
        cw, ch = self.credit_pixel_size

        # Create draw items
        y =  name_y_off
        first_w = None
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, justified_x + justified_x_offset - w, y, mutable_layout_data["Name Font"], credit_case)
            y += (h + line_gap)

        self.add_text_draw_item(self.credit_title, justified_x,\
        0, mutable_layout_data["Credit Font"], name_case)
        
        self.block_height = y - line_gap + name_y_off

class TwoLineLJustified(AbstractCreditBlock):

    def __init__(self, block_gen):
        AbstractCreditBlock.__init__(self, block_gen)

    def init_layout(self, fctx, cr, frame, mutable_layout_data):
        self.create_layouts(fctx, cr, mutable_layout_data)
 
        center_gap, line_gap, justified_x, name_y_off, name_x_off, credit_case, name_case, \
        screen_w, screen_h = self.get_layout_data(fctx, mutable_layout_data)
        
        cw, ch = self.credit_pixel_size

        # Create draw items
        self.add_text_draw_item(self.credit_title, screen_w - justified_x - cw, 0, mutable_layout_data["Credit Font"], name_case)
        
        y = ch +  name_y_off
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, screen_w - justified_x - w, y, mutable_layout_data["Name Font"], credit_case)
            y += (h + line_gap)

        self.block_height = y - line_gap


def _get_single_line_centered(block_gen):
    return SingleLineCentered(block_gen)

def _get_two_line_centered(block_gen):
    return TwoLineCentered(block_gen)

def _get_single_line_rjustified(block_gen):
    return SingleLineRJustified(block_gen)
    
def _get_two_line_rjustified(block_gen):
    return TwoLineRJustified(block_gen)
    
def _get_single_line_sides_justified(block_gen):
    return SingleSidesJustified(block_gen)
    
def _get_two_line_ljustified(block_gen):
    return TwoLineLJustified(block_gen)


BLOC_CREATOR_FUNCS = {AbstractCreditBlock.LAYOUT_SINGLE_LINE_CENTERED:_get_single_line_centered,
                      AbstractCreditBlock.LAYOUT_TWO_LINE_CENTERED:_get_two_line_centered,
                      AbstractCreditBlock.LAYOUT_SINGLE_LINE_RIGHT_JUSTIFIED:_get_single_line_rjustified,
                      AbstractCreditBlock.LAYOUT_TWO_LINE_RIGHT_JUSTIFIED:_get_two_line_rjustified,
                      AbstractCreditBlock.LAYOUT_SINGLE_SIDES_JUSTIFIED:_get_single_line_sides_justified,
                      AbstractCreditBlock.LAYOUT_TWO_LINE_LEFT_JUSTIFIED:_get_two_line_ljustified}





# ----------------------------------------------------- COMMAND BLOCKS
def _get_ypad_command(tokens):
    return YPaddingCommand(tokens)

def _get_set_layout_command(tokens):
    return SetLayoutCommand(tokens)
    

class AbstractCommandBlock(AbstractBlock):
    
    TARGET_CREDIT = "credit"
    TARGET_NAME = "name"
    TARGET_SECTION_TITLE = "section-title"
    
    TARGETS = [TARGET_CREDIT, TARGET_NAME, TARGET_SECTION_TITLE]

    Y_PADDING = "ypad"
    SET_LAYOUT = "set-layout"

    def __init__(self, command_type, tokens):
        self.command_type = command_type
        self.tokens = tokens
        self.ALLOWED_TOKEN_COUNTS = None # list int
        self.ARGUMENT_TYPES = None # dict {token_index:argument_type,...}
        self.ARGUMENT_ALLOW_VALUES = None # dict (toke_index:[allowde_value_1,...]}

        AbstractBlock.__init__(self)

    def set_verification_data(self, token_counts, argument_types, argument_allowed_values):
        self.ALLOWED_TOKEN_COUNTS = token_counts
        self.ARGUMENT_TYPES = argument_types
        self.ARGUMENT_ALLOW_VALUES = argument_allowed_values

    def check_command(self, fctx):
        if not(len(self.tokens) in self.ALLOWED_TOKEN_COUNTS):
            return BAD_ARGUMENT_COUNT_ERROR
            
        for token_index, argument_type in self.ARGUMENT_TYPES.items():
            if argument_type == int:
                try:
                    int(self.tokens[token_index])
                except:
                    return BAD_ARGUMENT_TYPE_ERROR
                    
        for token_index, argument_allowed_values in self.ARGUMENT_ALLOW_VALUES.items():
            fctx.log_line("CHECKING------" + str(self.tokens[token_index] ) + str(argument_allowed_values))
            if not(self.tokens[token_index] in argument_allowed_values):
                return BAD_ARGUMENT_VALUE_ERROR

        return None

    def __str__(self):
        return self.command_type

class YPaddingCommand(AbstractCommandBlock):

    def __init__(self, tokens):
        AbstractCommandBlock.__init__(self, AbstractCommandBlock.Y_PADDING, tokens)
        
        ALLOWED_TOKEN_COUNTS = [3]
        ARGUMENT_TYPES = {2:int}
        
        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, {})

    def exec_command(self, fctx, cr, frame, mutable_layout_data):
        self.block_height = int(self.tokens[2])

class SetLayoutCommand(AbstractCommandBlock):

    LAYOUT_VALUES = {   "single-line-centered": AbstractCreditBlock.LAYOUT_SINGLE_LINE_CENTERED,
                        "two line-centered": AbstractCreditBlock.LAYOUT_TWO_LINE_CENTERED,
                        "single-line-right-justified": AbstractCreditBlock.LAYOUT_SINGLE_LINE_RIGHT_JUSTIFIED,
                        "two-line-right-justified": AbstractCreditBlock.LAYOUT_TWO_LINE_RIGHT_JUSTIFIED,
                        "single-line-sides-justified": AbstractCreditBlock.LAYOUT_SINGLE_SIDES_JUSTIFIED,
                        "two-line-left-justified": AbstractCreditBlock.LAYOUT_TWO_LINE_LEFT_JUSTIFIED}

    def __init__(self, tokens):
        AbstractCommandBlock.__init__(self, AbstractCommandBlock.SET_LAYOUT, tokens)
        
        ALLOWED_TOKEN_COUNTS = [3]
        ARGUMENT_TYPES = {2:str}
        ARGUMENT_ALLOW_VALUES = {2:SetLayoutCommand.LAYOUT_VALUES.keys()}
        
        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, ARGUMENT_ALLOW_VALUES)

    def exec_parse_command(self, blocks_generator):
        new_layout = SetLayoutCommand.LAYOUT_VALUES[self.tokens[2]]
        blocks_generator.current_layout = new_layout


COMMAND_CREATOR_FUNCS = {AbstractCommandBlock.Y_PADDING:_get_ypad_command,
                         AbstractCommandBlock.SET_LAYOUT:_get_set_layout_command}

