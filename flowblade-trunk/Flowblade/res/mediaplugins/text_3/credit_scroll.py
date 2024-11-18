"""
    Copyright 2022 Janne Liljeblad, licenced under GPL3. 
    See  <http://www.gnu.org/licenses/> for licence text.
"""

import cairo
import copy
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
UNKNOWN_COMMAND_ERROR = 8

DEFAULT_SCROLL_MARKUP_TEXT = \
"""
# CREDIT TITLE1
Alice Andersson

# CREDIT TITLE2
Bob Banner
Carl Carruthers

# CREDIT TITLE3
Donald Drake
Earl Easter

! page 50

! font-size section-title 60
! set-layout-property section-title-alignment right-justified

## This is some section title

! set-layout two-columns-centered
! font-size name 30

# CREDIT TITLE3
Donald Drake
Earl Easter
Bob Banner
Carl Carruthers
Donald Drake
Earl Easter
Alice Andersson
Earl Easter
Bob Banner
Carl Carruthers
Donald Drake

! page 100
! set-layout single-line-sides-justified

# CREDIT TITLE3
Donald Drake
Earl Easter
Bob Banner
Carl Carruthers
Donald Drake

"""
"""
! ypad 40
! set-layout single-line-sides-justified
! font-size credit 100
! font-family credit Ubuntu Sans
! font-face name italic
! font-property credit color-rgba (1.0,0.0,0.0,1.0)
! set-layout-property name-y-off -100
! text-case name lowercase
"""

def init_script(fctx):
    fctx.set_name("Scrolling Credits")
    fctx.set_version(2)
    fctx.set_author("Janne Liljeblad")

    fctx.add_editor_group("Layout")
    fctx.add_editor("Show Info", fluxity.EDITOR_HTML_LINK, fluxity.LOCAL_ROOT + "/res/help/en/advanced.html#9._Credits_Scroll_Generator")
    fctx.add_editor("Credits Layout", fluxity.EDITOR_OPTIONS, (0, ["Single Line Centered", "Two Line Centered", "Single Line Right Justified", "Two Line Right Justified",
                    "Single Line Sides Justified", "Two Line Left Justified", "Two Columns Centered"]))
    fctx.add_editor("Center Gap", fluxity.EDITOR_INT, 30)
    fctx.add_editor("Credit Block Gap", fluxity.EDITOR_INT, 40)
    fctx.add_editor("Line Gap", fluxity.EDITOR_INT, 0)
    fctx.add_editor("Justified X Position", fluxity.EDITOR_INT, 150)
    fctx.add_editor("Justified X Position Offset", fluxity.EDITOR_INT, 1300)
    fctx.add_editor("Name X Offset", fluxity.EDITOR_INT, 0)
    fctx.add_editor("Name Y Offset", fluxity.EDITOR_INT, 0)
    fctx.add_editor("Section Title Alignment", fluxity.EDITOR_OPTIONS, (0, ["Centered", "Left Justified", "Right Justified"]))
    fctx.add_editor("Background", fluxity.EDITOR_OPTIONS, (1, ["Transparent", "Solid Color"]))
    fctx.add_editor("Background Color", fluxity.EDITOR_COLOR, (1.0, 1.0, 1.0, 1.0))

    fctx.add_editor_group("Fonts")
    font_default_values = ("Liberation Sans", "Regular", 35, Pango.Alignment.LEFT, (0.0, 0.0, 0.0, 1.0), \
                       True, (0.3, 0.3, 0.3, 1.0) , False, 2, False, (1.0, 0.0, 0.0), \
                       100, 3, 3, 0.0, None, fluxity.VERTICAL)
    fctx.add_editor("Credit Font", fluxity.EDITOR_PANGO_FONT, font_default_values)
    fctx.add_editor("Creadit Case", fluxity.EDITOR_OPTIONS, (0, ["No Changes", "Uppercase", "Lowercase"]))
    fctx.add_editor("Name Font", fluxity.EDITOR_PANGO_FONT, copy.deepcopy(font_default_values))
    fctx.add_editor("Name Case", fluxity.EDITOR_OPTIONS, (0, ["No Changes", "Uppercase", "Lowercase"]))
    fctx.add_editor("Section Title Font", fluxity.EDITOR_PANGO_FONT, copy.deepcopy(font_default_values))
    fctx.add_editor("Section Title Case", fluxity.EDITOR_OPTIONS, (0, ["No Changes", "Uppercase", "Lowercase"]))

    fctx.add_editor_group("Animation")
    fctx.add_editor("Animation Type", fluxity.EDITOR_OPTIONS, (0, ["Scrolled", "Paged"]))
    fctx.add_editor("Speed", fluxity.EDITOR_FLOAT_RANGE, (10.0, 0.0, 40.0))
    fctx.add_editor("Default Frames Per Page", fluxity.EDITOR_INT_RANGE, (100, 5, 2000))

    fctx.add_editor_group("Text")
    fctx.add_editor("Text", fluxity.EDITOR_TEXT_AREA, DEFAULT_SCROLL_MARKUP_TEXT)

def init_render(fctx):
    text = fctx.get_editor_value("Text")
    lines = text.splitlines()
    blocks_generator = ScrollBlocksGenerator(lines, fctx)
    scroll_blocks, err = blocks_generator.get_blocks()
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

    if fctx.get_editor_value("Animation Type") == 0:
        anim_runner = ScrollAnimationRunner(fctx)
    else:
        anim_runner = PagedAnimationRunner(fctx)

    anim_runner.init_blocks(fctx, cr, frame)
    anim_runner.draw_blocks(fctx, cr, frame)

#------------------------------------------------- ERROR HANDLING
def throw_user_message_error(error_type, line, msg, current_line = None):
    type_name = { \
        NON_CREDITED_NAME_ERROR: "Name Outside Credit Block Error",
        BAD_LINE_ERROR: "Bad Line Error",
        PARSE_CRASH_ERROR:"Parse Crash Error",
        SECTION_TITLE_INSIDE_CREDIT_SECTION_ERROR:"Title Section Inside Credit Block Error",
        COMMAND_INSIDE_CREDIT_BLOCK_ERROR:"Command Inside Credit Block Error",
        BAD_ARGUMENT_COUNT_ERROR:"Bad Argument Count Error",
        BAD_ARGUMENT_TYPE_ERROR :"Bad Argument Type Error",
        BAD_ARGUMENT_VALUE_ERROR:"Bad Argument Value Error",
        UNKNOWN_COMMAND_ERROR:"Unknown Command Error"}

    line_number = str(current_line)
    if current_line == None:
        line_number = "unknown"
    error_str = type_name[error_type] + ", line " + line_number +  "  '" + line + "'.\n" + msg

    raise fluxity.FluxityUserMessageError(error_str)
        
#-------------------------------------------------- BLOCKS CREATION
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
                throw_user_message_error(BAD_LINE_ERROR, line, "Maybe you provided markup without line content?", self.current_line)

            self.current_line += 1

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
            throw_user_message_error(NON_CREDITED_NAME_ERROR, line, "Names must be given on consecutive lines after credit title.", self.current_line)
        
    def do_command_line(self, line):
        self.print_line(LINE_TYPE_COMMAND, line)
        
        if self.state == STATE_WAITING_NEXT_NAME:
            throw_user_message_error(COMMAND_INSIDE_CREDIT_BLOCK_ERROR, line, "All commands must be given outside credit blocks.", self.current_line)
        
        tokens = line.split(" ")
        try:
           command_block_creator_func = COMMAND_CREATOR_FUNCS[tokens[1]]
        except:
            msg = "Unknown command '" + tokens[1] + "'."
            throw_user_message_error(UNKNOWN_COMMAND_ERROR, line, msg, self.current_line)
            
        block = command_block_creator_func(tokens, self, line)
        block.check_command(self.fctx)
        block.exec_parse_command(self)
        self.blocks.append(block)

    def do_section_title_line(self, line):
        if self.state == STATE_WAITING_NEXT_NAME:
            throw_user_message_error(SECTION_TITLE_INSIDE_CREDIT_SECTION_ERROR, line, "Cannot put Title Section line inside Credit Block.", self.current_line)
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

        if len(list(filter(None, line.split(" ")))) < 2:
            return LINE_TYPE_BAD

        if markup == MARKUP_CREDIT:
            return LINE_TYPE_CREDIT
        elif markup == MARKUP_COMMAND:
            return LINE_TYPE_COMMAND
        elif  markup == MARKUP_SECTION_TITLE:
            return LINE_TYPE_SECTION_TITLE

        return LINE_TYPE_BAD # shouldn't hit this
            
    def get_line_markup(self, line):
        if line.startswith(MARKUP_COMMAND):
            return MARKUP_COMMAND
        elif line.startswith(MARKUP_SECTION_TITLE):
            return MARKUP_SECTION_TITLE
        elif line.startswith(MARKUP_CREDIT):
            return MARKUP_CREDIT
        else:
            return None

    def get_line_contents_str(self, line):
        line_type = self.get_line_type(line)
        if line_type == LINE_TYPE_CLEAR or line_type == LINE_TYPE_BAD:
            return None
        elif line_type == LINE_TYPE_NAME:
            return line.strip()
        elif line_type == LINE_TYPE_SECTION_TITLE:
            return line[2:].strip()
        else:
            return line[1:].strip()

    def add_credit_block(self):
        bloc_creator_func = BLOC_CREATOR_FUNCS[self.current_layout]
        block = bloc_creator_func(self)
        self.blocks.append(block)

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


class CredidBlockData:

    def __init__(self, credit_title):
        self.credit_title = credit_title
        self.names = []

    def add_name(self, name):
        self.names.append(name)



# ---------------------------------------------------- ANIMATION RUNNER

class ScrollAnimationRunner:
    
    def __init__(self, fctx):
        self.scroll_blocks = fctx.get_data_obj("scroll_blocks")
        self.fctx = fctx

    def init_blocks(self, fctx, cr,  frame):
        mutable_layout_data = fctx.get_editors_values_clone_dict()

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


class PagedAnimationRunner:
    
    def __init__(self, fctx):
        self.scroll_blocks = fctx.get_data_obj("scroll_blocks")
        self.fctx = fctx
        self.pages = []

    def init_blocks(self, fctx, cr,  frame):
        mutable_layout_data = fctx.get_editors_values_clone_dict()

        # Create layouts now that we have cairo.Context.
        current_page = []
        current_page_length = fctx.get_editor_value("Default Frames Per Page")

        for block in self.scroll_blocks:
            block.init_layout(fctx, cr, frame, mutable_layout_data)
            block.exec_command(fctx, cr, frame, mutable_layout_data)
            current_page.append(block)
            if block.page_length != AbstractBlock.PAGE_LENGTH_NOT_SET:
                if len(current_page) == 0:
                    # At start of with multiple paging commands we just set current page length.
                    current_page_length = block.page_length
                else:
                    self.pages.append((current_page_length, current_page))
                    current_page_length = block.page_length
                    current_page = []
        
        # Add last page
        if len(current_page) > 0:
            self.pages.append((current_page_length, current_page))

    def draw_blocks(self, fctx, cr, frame):
        screen_h = fctx.get_profile_property(fluxity.PROFILE_HEIGHT)
        
        # Get page.
        display_page = None
        current_page_end = 0
        for page_item in self.pages:
            page_length, page = page_item
            current_page_end += page_length
            if frame < current_page_end:
                display_page = page
                break
        
        # Get page height.
        h = 0
        BLOCK_GAP = fctx.get_editor_value("Credit Block Gap")
        for block in display_page:
            if block.block_height != 0:
            	h += (block.block_height + BLOCK_GAP)

        # Center page vertically if fits, else just display from top.
        if h - BLOCK_GAP > screen_h:
            y = 0
        else:
            y = (screen_h - h + BLOCK_GAP) / 2.0

        # Draw page.
        for block in display_page:
            block.draw(fctx, cr, y)
            y += (block.block_height + BLOCK_GAP)



# ----------------------------------------------------- BLOCKS

class AbstractBlock:

    # These indexes must match those in editors "Creadit Case" etc.
    CASE_NO_CHANGES = 0
    CASE_UPPERCASE = 1
    CASE_LOWERCASE = 2
    
    PAGE_LENGTH_NOT_SET = -1
    
    def __init__(self):
        self.block_height = 0
        self.page_length = self.PAGE_LENGTH_NOT_SET

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

class AbstractTextBlock(AbstractBlock):
    


    def __init__(self):
        self.draw_items = []
    
        AbstractBlock.__init__(self)

    def add_text_draw_item(self, text, x, y, font_data, case):
        if case == AbstractBlock.CASE_UPPERCASE:
            text = text.upper()
        elif case == AbstractBlock.CASE_LOWERCASE:
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
            

class AbstractCreditBlock(AbstractTextBlock):
    
    # These indexs must match those in editor "Credits Layout".
    LAYOUT_SINGLE_LINE_CENTERED = 0
    LAYOUT_TWO_LINE_CENTERED = 1
    LAYOUT_SINGLE_LINE_RIGHT_JUSTIFIED = 2
    LAYOUT_TWO_LINE_RIGHT_JUSTIFIED = 3
    LAYOUT_SINGLE_SIDES_JUSTIFIED = 4
    LAYOUT_TWO_LINE_LEFT_JUSTIFIED = 5
    LAYOUT_TWO_COLUMNS_CENTERED = 6

    def __init__(self, block_gen):
        block_data = block_gen.current_credit_block_data

        self.credit_title = block_data.credit_title
        self.names = block_data.names
        self.fctx = block_gen.fctx
        self.draw_items = []
    
        AbstractTextBlock.__init__(self)

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
        self.add_text_draw_item(self.credit_title,screen_w / 2.0 - cw / 2.0, 0, mutable_layout_data["Credit Font"], credit_case)
        
        y =  ch +  name_y_off
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, screen_w / 2 - w / 2.0 + name_x_off, y, mutable_layout_data["Name Font"], name_case)
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
        self.add_text_draw_item(self.credit_title, justified_x, 0, mutable_layout_data["Credit Font"], credit_case)
        
        y =  name_y_off
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, justified_x + cw + name_x_off + center_gap, y, mutable_layout_data["Name Font"], name_case)
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
        self.add_text_draw_item(self.credit_title, justified_x, 0, mutable_layout_data["Credit Font"], credit_case)
        
        y = ch +  name_y_off
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, justified_x + name_x_off, y, mutable_layout_data["Name Font"], name_case)
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
            self.add_text_draw_item(name, justified_x + justified_x_offset - w, y, mutable_layout_data["Name Font"], name_case)
            y += (h + line_gap)

        self.add_text_draw_item(self.credit_title, justified_x,\
        0, mutable_layout_data["Credit Font"], credit_case)
        
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
        self.add_text_draw_item(self.credit_title, screen_w - justified_x - cw, 0, mutable_layout_data["Credit Font"], credit_case)
        
        y = ch +  name_y_off
        for layout, name in zip(self.name_layouts, self.names):
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            self.add_text_draw_item(name, screen_w - justified_x - w, y, mutable_layout_data["Name Font"], name_case)
            y += (h + line_gap)

        self.block_height = y - line_gap

class TwoColumnsCentered(AbstractCreditBlock):

    def __init__(self, block_gen):
        AbstractCreditBlock.__init__(self, block_gen)

    def init_layout(self, fctx, cr, frame, mutable_layout_data):
        self.create_layouts(fctx, cr, mutable_layout_data)
 
        center_gap, line_gap, justified_x, name_y_off, name_x_off, credit_case, name_case, \
        screen_w, screen_h = self.get_layout_data(fctx, mutable_layout_data)
        
        cw, ch = self.credit_pixel_size

        # Create draw items
        self.add_text_draw_item(self.credit_title,screen_w / 2.0 - cw / 2.0, 0, mutable_layout_data["Credit Font"], credit_case)

        y = ch +  name_y_off
        for i in range(0, len(self.names)):
            if i%2 == 0 and i != 0:
                y += (h + line_gap)
                
            layout = self.name_layouts[i]
            name = self.names[i]
            fluxity_layout, pixel_size = layout
            w, h = pixel_size
            if i%2 == 0:
                # left column
                self.add_text_draw_item(name, justified_x + ((screen_w / 2.0 - justified_x) - w) / 2.0, y, mutable_layout_data["Name Font"], name_case)
            else:
                # right column
                self.add_text_draw_item(name, screen_w / 2.0 + ((screen_w / 2.0 - justified_x) - w) / 2.0, y, mutable_layout_data["Name Font"], name_case)


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

def _get_two_column_centered(block_gen):
    return TwoColumnsCentered(block_gen)
    

BLOC_CREATOR_FUNCS = {AbstractCreditBlock.LAYOUT_SINGLE_LINE_CENTERED:_get_single_line_centered,
                      AbstractCreditBlock.LAYOUT_TWO_LINE_CENTERED:_get_two_line_centered,
                      AbstractCreditBlock.LAYOUT_SINGLE_LINE_RIGHT_JUSTIFIED:_get_single_line_rjustified,
                      AbstractCreditBlock.LAYOUT_TWO_LINE_RIGHT_JUSTIFIED:_get_two_line_rjustified,
                      AbstractCreditBlock.LAYOUT_SINGLE_SIDES_JUSTIFIED:_get_single_line_sides_justified,
                      AbstractCreditBlock.LAYOUT_TWO_LINE_LEFT_JUSTIFIED:_get_two_line_ljustified,
                      AbstractCreditBlock.LAYOUT_TWO_COLUMNS_CENTERED:_get_two_column_centered}


# ------------------------------------------------- SECTION TITLE BLOCK
class SectionTitleBlock(AbstractTextBlock):

    def __init__(self, section_title):
        AbstractTextBlock.__init__(self)

        self.section_title = section_title

    def init_layout(self, fctx, cr, frame, mutable_layout_data):
        section_title_font = mutable_layout_data["Section Title Font"]
        section_title_layout = fctx.create_text_layout(section_title_font)
        section_title_layout.create_pango_layout(cr, self.section_title)
        stw, sth  = section_title_layout.pixel_size
        stcase = mutable_layout_data["Section Title Case"]
        alignment = mutable_layout_data["Section Title Alignment"]
        justified_x = mutable_layout_data["Justified X Position"]
        screen_w = fctx.get_profile_property(fluxity.PROFILE_WIDTH)
 
        # Index values correspond with option in "Section Alignment" editor.
        if alignment == 0: # centered
            self.add_text_draw_item(self.section_title, screen_w / 2.0 - stw / 2.0, 0, section_title_font, stcase)
        elif alignment == 1: # Left justified
            self.add_text_draw_item(self.section_title, justified_x, 0, section_title_font, stcase)
        else: # Right justified
            self.add_text_draw_item(self.section_title, screen_w - justified_x - stw, 0, section_title_font, stcase)

        self.block_height = sth


# ----------------------------------------------------- COMMAND BLOCKS
def _get_ypad_command(tokens, blocks_gen, line):
    return YPaddingCommand(tokens, blocks_gen, line)

def _get_paging_command(tokens, blocks_gen, line):
    return PagingCommand(tokens, blocks_gen, line)

def _get_set_layout_command(tokens, blocks_gen, line):
    return SetLayoutCommand(tokens, blocks_gen, line)
    
def _get_font_size_command(tokens, blocks_gen, line):
    return FontSizeCommand(tokens, blocks_gen, line)
    
def _get_font_family_command(tokens, blocks_gen, line):
    return FontFontFamilyCommand(tokens, blocks_gen, line)

def _get_font_face_command(tokens, blocks_gen, line):
    return FontFaceCommand(tokens, blocks_gen, line)

def _get_font_property_command(tokens, blocks_gen, line):
    return FontPropertyCommand(tokens, blocks_gen, line)

def _get_set_layout_property_command(tokens, blocks_gen, line):
    return SetLayoutPropertyCommand(tokens, blocks_gen, line)

def _get_text_case_command(tokens, blocks_gen, line):
    return TextCaseCommand(tokens, blocks_gen, line)


class AbstractCommandBlock(AbstractBlock):
    
    TARGET_CREDIT = "credit"
    TARGET_NAME = "name"
    TARGET_SECTION_TITLE = "section-title"
    
    TARGETS = [TARGET_CREDIT, TARGET_NAME, TARGET_SECTION_TITLE]
    
    Y_PADDING = "ypad"
    PAGING = "page"
    SET_LAYOUT = "set-layout"
    FONT_SIZE = "font-size"
    FONT_FAMILY = "font-family"
    FONT_FACE = "font-face"
    FONT_PROPERTY = "font-property"
    SET_LAYOUT_PROPERTY = "set-layout-property"
    TEXT_CASE = "text-case"
    
    def __init__(self, command_type, tokens, blocks_gen, line):
        self.command_type = command_type
        self.tokens = tokens
        self.blocks_gen = blocks_gen
        self.line = line
        
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
            
            if len(self.ALLOWED_TOKEN_COUNTS) == 1:
                expected = str(max(self.ALLOWED_TOKEN_COUNTS))
            elif len(self.ALLOWED_TOKEN_COUNTS) == 2:
                expected = str(self.ALLOWED_TOKEN_COUNTS[0]) + " or " + str(self.ALLOWED_TOKEN_COUNTS[1])
            else:
                expected = "more then " + str(self.ALLOWED_TOKEN_COUNTS[0])

            msg = "Wrong number of tokens in command. Line token count " + str(len(self.tokens)) + ", expected " + expected + "."
            throw_user_message_error(BAD_ARGUMENT_COUNT_ERROR, self.line, msg, self.blocks_gen.current_line)
            
        for token_index, argument_type in self.ARGUMENT_TYPES.items():
            if argument_type == int:
                try:
                    int(self.tokens[token_index])
                except:
                    msg = "Argument at position " + str(token_index) + " has wrong type. Was " + str(type(self.tokens[token_index]))  + ", expected 'inẗ́'."
                    throw_user_message_error(BAD_ARGUMENT_TYPE_ERROR, self.line, msg, self.blocks_gen.current_line)

        for token_index, argument_allowed_values in self.ARGUMENT_ALLOW_VALUES.items():
            if not(self.tokens[token_index] in argument_allowed_values):
                msg = "Argument at position " + str(token_index) + " has unknown value. Was " + self.tokens[token_index] + ", expected " +  str(argument_allowed_values) + "."
                throw_user_message_error(BAD_ARGUMENT_VALUE_ERROR, self.line, msg, self.blocks_gen.current_line)

    def __str__(self):
        return self.command_type

class YPaddingCommand(AbstractCommandBlock):

    def __init__(self, tokens, blocks_gen, line):
        AbstractCommandBlock.__init__(self, AbstractCommandBlock.Y_PADDING, tokens, blocks_gen, line)
        
        ALLOWED_TOKEN_COUNTS = [3]
        ARGUMENT_TYPES = {2:int}
        
        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, {})

    def exec_command(self, fctx, cr, frame, mutable_layout_data):
        self.block_height = int(self.tokens[2])

class PagingCommand(AbstractCommandBlock):

    def __init__(self, tokens, blocks_gen, line):
        AbstractCommandBlock.__init__(self, AbstractCommandBlock.PAGING, tokens, blocks_gen, line)
        
        ALLOWED_TOKEN_COUNTS = [2, 3]
        ARGUMENT_TYPES = {2:int}
        
        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, {})

    def exec_command(self, fctx, cr, frame, mutable_layout_data):
        try:
            self.page_length = int(self.tokens[2])
        except:
            self.page_length = fctx.get_editor_value("Default Frames Per Page")

class TextCaseCommand(AbstractCommandBlock):

    CASES = ["no-changes", "uppercase", "lowercase"]
    TARGETS_TO_CASE_EDITORS = {AbstractCommandBlock.TARGET_CREDIT:"Creadit Case",
                               AbstractCommandBlock.TARGET_NAME:"Name Case",
                               AbstractCommandBlock.TARGET_SECTION_TITLE:"Section title Case"}
    
    def __init__(self, tokens, blocks_gen, line):
        AbstractCommandBlock.__init__(self, AbstractCommandBlock.TEXT_CASE, tokens, blocks_gen, line)
        
        ALLOWED_TOKEN_COUNTS = [4]
        ARGUMENT_TYPES = {2:str, 3:str}
        ARGUMENT_ALLOW_VALUES = {2:AbstractCommandBlock.TARGETS, 3:TextCaseCommand.CASES}
        
        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, ARGUMENT_ALLOW_VALUES)

    def exec_command(self, fctx, cr, frame, mutable_layout_data):
        target = self.tokens[2]
        new_case = TextCaseCommand.CASES.index(self.tokens[3])
        target_editor = TextCaseCommand.TARGETS_TO_CASE_EDITORS[target]
        mutable_layout_data[target_editor] = new_case

class SetLayoutCommand(AbstractCommandBlock):

    LAYOUT_VALUES = {   "single-line-centered": AbstractCreditBlock.LAYOUT_SINGLE_LINE_CENTERED,
                        "two line-centered": AbstractCreditBlock.LAYOUT_TWO_LINE_CENTERED,
                        "single-line-right-justified": AbstractCreditBlock.LAYOUT_SINGLE_LINE_RIGHT_JUSTIFIED,
                        "two-line-right-justified": AbstractCreditBlock.LAYOUT_TWO_LINE_RIGHT_JUSTIFIED,
                        "single-line-sides-justified": AbstractCreditBlock.LAYOUT_SINGLE_SIDES_JUSTIFIED,
                        "two-line-left-justified": AbstractCreditBlock.LAYOUT_TWO_LINE_LEFT_JUSTIFIED,
                        "two-columns-centered": AbstractCreditBlock.LAYOUT_TWO_COLUMNS_CENTERED}

    def __init__(self, tokens, blocks_gen, line):
        AbstractCommandBlock.__init__(self, AbstractCommandBlock.SET_LAYOUT, tokens, blocks_gen, line)
        
        ALLOWED_TOKEN_COUNTS = [3]
        ARGUMENT_TYPES = {2:str}
        ARGUMENT_ALLOW_VALUES = {2:SetLayoutCommand.LAYOUT_VALUES.keys()}
        
        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, ARGUMENT_ALLOW_VALUES)

    def exec_parse_command(self, blocks_generator):
        new_layout = SetLayoutCommand.LAYOUT_VALUES[self.tokens[2]]
        blocks_generator.current_layout = new_layout

class AbstractFontCommand(AbstractCommandBlock):

    # These correspond with order and count with data in font data tuples 
    # provided for fluxity.PangoTextLayout objects on creation.
    FONT_DATA_PARAMS = ["font-family", "font-face", "font-size", "alignment", \
        "color-rgba", "fill-on", "outline-color-rgba", "outline-on", \
        "outline-width", "shadow-on", "shadow-color-rgb", "shadow-opacity", \
        "shadow-xoff", "shadow-yoff", "shadow-blur", "gradient-color-rgba", \
        "gradient-direction"]

    FONT_DATA_PARAMS_TYPES = [str,str,int,int,tuple,bool,tuple,bool,\
                              int,bool,tuple,int,int,int,float,tuple,int]

    TARGETS_TO_FONT_EDITORS = {AbstractCommandBlock.TARGET_CREDIT:"Credit Font", AbstractCommandBlock.TARGET_NAME:"Name Font", AbstractCommandBlock.TARGET_SECTION_TITLE:"Section Title Font"}
    
    FONT_REGULAR = "regular"
    FONT_ITALIC = "italic"
    FONT_BOLD = "bold"
    FONT_FACES = [FONT_REGULAR, FONT_ITALIC, FONT_BOLD]
    FONT_FACES_TO_PANGO = {FONT_REGULAR:"Regular",
                           FONT_ITALIC:"Italic",
                           FONT_BOLD:"Bold"}
        
    def __init__(self, command_type, tokens, blocks_gen, line):
        AbstractCommandBlock.__init__(self, command_type, tokens, blocks_gen, line)
    
    def set_font_param(self, target, param_name, value, mutable_data):
        target_editor = AbstractFontCommand.TARGETS_TO_FONT_EDITORS[target]
        new_font_data = self.get_updated_font_data( mutable_data[target_editor], 
                                                    param_name, 
                                                    value)
        mutable_data[target_editor] = new_font_data
  
    def get_updated_font_data(self, font_data, param_name, new_value):
        param_index = AbstractFontCommand.FONT_DATA_PARAMS.index(param_name)
        param_list = list(font_data)
        param_list[param_index] = new_value
        return tuple(param_list)

class FontSizeCommand(AbstractFontCommand):
    
    def __init__(self, tokens, blocks_gen, line):
        
        AbstractFontCommand. __init__(self, AbstractCommandBlock.FONT_SIZE, tokens, blocks_gen, line)

        ALLOWED_TOKEN_COUNTS = [4]
        ARGUMENT_TYPES = {2:str, 3:int}
        ARGUMENT_ALLOW_VALUES = {2:AbstractCommandBlock.TARGETS}
        
        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, ARGUMENT_ALLOW_VALUES)
        
    def exec_command(self, fctx, cr, frame, mutable_layout_data):
        param_name = "font-size"
        target = self.tokens[2]
        new_size = int(self.tokens[3])
        self.set_font_param(target, param_name, new_size, mutable_layout_data)

class FontFontFamilyCommand(AbstractFontCommand):
    
    def __init__(self, tokens, blocks_gen, line):
        
        AbstractFontCommand. __init__(self, AbstractCommandBlock.FONT_FAMILY, tokens, blocks_gen, line)

        ALLOWED_TOKEN_COUNTS = [4,5,6,7,8,9,10,11,12,13] # Font family names can have quite many parts in them.
        ARGUMENT_TYPES = {2:str}
        ARGUMENT_ALLOW_VALUES = {2:AbstractCommandBlock.TARGETS}
        
        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, ARGUMENT_ALLOW_VALUES)
        
    def exec_command(self, fctx, cr, frame, mutable_layout_data):
        param_name = "font-family"
        target = self.tokens[2]
        new_family = ""
        token = 3
        while token < len(self.tokens):
            new_family = new_family + self.tokens[token] + " "
            token += 1
        
        new_family = new_family[0:-1]
        self.set_font_param(target, param_name, new_family, mutable_layout_data)

class FontFaceCommand(AbstractFontCommand):
    
    def __init__(self, tokens, blocks_gen, line):
        
        AbstractFontCommand. __init__(self, AbstractCommandBlock.FONT_FACE, tokens, blocks_gen, line)

        ALLOWED_TOKEN_COUNTS = [4, 5]
        ARGUMENT_TYPES = {2:str, 3:str}
        ARGUMENT_ALLOW_VALUES = {2:AbstractCommandBlock.TARGETS, 3:AbstractFontCommand.FONT_FACES}
        
        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, ARGUMENT_ALLOW_VALUES)
        
    def exec_command(self, fctx, cr, frame, mutable_layout_data):
        param_name = "font-face"
        target = self.tokens[2]
        new_face = AbstractFontCommand.FONT_FACES_TO_PANGO[self.tokens[3]]
        self.set_font_param(target, param_name, new_face, mutable_layout_data)

class FontPropertyCommand(AbstractFontCommand):
    
    def __init__(self, tokens, blocks_gen, line):
        
        AbstractFontCommand. __init__(self, AbstractCommandBlock.FONT_PROPERTY, tokens, blocks_gen, line)

        ALLOWED_TOKEN_COUNTS = [5,6,7,8,9,10,11,12,13]
        ARGUMENT_TYPES = {2:str, 3:str}
        ARGUMENT_ALLOW_VALUES = {2:AbstractCommandBlock.TARGETS, 3:AbstractFontCommand.FONT_DATA_PARAMS}
        
        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, ARGUMENT_ALLOW_VALUES)
        
    def exec_command(self, fctx, cr, frame, mutable_layout_data):
        target = self.tokens[2]
        param_name = self.tokens[3]
        new_value, err =  self.get_typed_font_param_value(param_name, self.tokens[4])
        self.set_font_param(target, param_name, new_value, mutable_layout_data)

    def get_typed_font_param_value(self, param_name, value):
        if value == None:
            return (None, None)
        
        param_index = AbstractFontCommand.FONT_DATA_PARAMS.index(param_name)
        param_type = AbstractFontCommand.FONT_DATA_PARAMS_TYPES[param_index]
        
        try:
            if param_type == int:
                return (int(value), None)
            elif param_type == float:
                return (float(value), None)
            elif param_type == float:
                return (str(value), None)
            elif param_type == bool:
                if value == "False":
                    out_val = False
                elif value == "True":
                    out_val = True
                else:
                    msg = "Argument '" + value + "' was expected to be a boolean valuen, but cannot be interpreted as such."
                    throw_user_message_error(BAD_ARGUMENT_TYPE_ERROR, self.line, msg, self.blocks_gen.current_line)
                return (out_val, None)
            else:
                value = value[1:-1]
                value = value.replace(" ", "")
                tuple_tokens = value.split(",")
                tuple_tokens_float = [float(i) for i in tuple_tokens]
                return (tuple(tuple_tokens_float), None)
        except:
            msg = "Argument '" + value + "' has wrong type. Was " + str(type(value))  + ", expected " + str(param_type) + "."
            throw_user_message_error(BAD_ARGUMENT_TYPE_ERROR, self.line, msg, self.blocks_gen.current_line)


class SetLayoutPropertyCommand(AbstractCommandBlock):
    
    LAYOUT_PARAMS = ["center-gap", "line-gap","creadit-block-gap",
                     "justified-x", "justified-x-off", "name-y-off",
                     "name-x-off", "section-title-alignment",]
    
    LAYOUT_PARAMS_TO_EDITORS = { "center-gap":"Center Gap",
                                 "line-gap":"Line Gap",
                                 "credit-block-gap":"Credit Block Gap",
                                 "justified-x":"Justified X Position", 
                                 "justified-x-off":"Justified X Position Offset", 
                                 "name-y-off":"Name Y Offset",
                                 "name-x-off":"Name X Offset",
                                 "section-title-alignment":"Section Title Alignment"}
    
    ALIGNMENTS = ["centered", "left-justified", "right-justified"]
    
    def __init__(self, tokens, blocks_gen, line):
        
        AbstractCommandBlock. __init__(self, AbstractCommandBlock.SET_LAYOUT_PROPERTY, tokens, blocks_gen, line)

        ALLOWED_TOKEN_COUNTS = [4]
        ARGUMENT_TYPES = {2:str}
        ARGUMENT_ALLOW_VALUES = {2:SetLayoutPropertyCommand.LAYOUT_PARAMS}

        self.set_verification_data(ALLOWED_TOKEN_COUNTS, ARGUMENT_TYPES, ARGUMENT_ALLOW_VALUES)
        
    def exec_command(self, fctx, cr, frame, mutable_layout_data):
        param_name = self.tokens[2]
         # Here param type checking happens later then usual
         # because params can have two types (int, str) but whatever.
        if param_name == "section-title-alignment":
            if self.tokens[3] in self.ALIGNMENTS:
                new_value =  self.ALIGNMENTS.index(self.tokens[3])
            else:
                msg = "Argument " + self.tokens[3] + " has unknown value, expected " +  str(self.ALIGNMENTS) + "."
                throw_user_message_error(BAD_ARGUMENT_VALUE_ERROR, self.line, msg, self.blocks_gen.current_line)
        else:
            try:
                new_value = int(self.tokens[3])
            except:
                msg = "Argument '" + self.tokens[3] + "' has wrong type. Was " + str(type(self.tokens[3]))  + ", expected 'int'."
                throw_user_message_error(BAD_ARGUMENT_TYPE_ERROR, self.line, msg, self.blocks_gen.current_line)
                
        editor_name = SetLayoutPropertyCommand.LAYOUT_PARAMS_TO_EDITORS[param_name]
        mutable_layout_data[editor_name] = new_value



COMMAND_CREATOR_FUNCS = {AbstractCommandBlock.Y_PADDING:_get_ypad_command,
                         AbstractCommandBlock.PAGING: _get_paging_command,
                         AbstractCommandBlock.SET_LAYOUT:_get_set_layout_command,
                         AbstractCommandBlock.FONT_SIZE:_get_font_size_command,
                         AbstractCommandBlock.FONT_FAMILY:_get_font_family_command,
                         AbstractCommandBlock.FONT_FACE:_get_font_face_command,
                         AbstractCommandBlock.FONT_PROPERTY:_get_font_property_command,
                         AbstractCommandBlock.SET_LAYOUT_PROPERTY:_get_set_layout_property_command,
                         AbstractCommandBlock.TEXT_CASE:_get_text_case_command}

