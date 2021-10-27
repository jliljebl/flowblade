
import cairo
from gi.repository import Pango

ANIMATION_BY_LETTER = 0
ANIMATION_BY_WORD = 0
ANIMATION_BY_LINE = 0


def init_script(fctx):
    fctx.set_name("Text")
    fctx.set_author("Janne Liljeblad")
 
    fctx.add_editor("Font", fctx.EDITOR_PANGO_FONT, fctx.EDITOR_PANGO_FONT_DEFAULT_VALUES)
    fctx.add_editor("Text", fctx.EDITOR_TEXT_AREA, "Lorem ipsum dolor sit amet,\nconsectetur adipiscing elit.\nAliquam non condimentum magna.")
    
def init_render(fctx):
    # Get editor values
    font_data = fctx.get_editor_value("Font")
    text = fctx.get_editor_value("Text")
    
    typewriter = TypeWriter(text, font_data, ANIMATION_BY_LETTER)
    fctx.set_data_obj("typewriter", typewriter)
    
def render_frame(frame, fctx, w, h):
    cr = fctx.get_frame_cr()

    typewriter = fctx.get_data_obj("typewriter")
    typewriter.draw_text(fctx, frame, cr, 100, 100)


class TypeWriter:
    
    def __init__(self, text, font_data, animation_type):
        self.lines = text.splitlines()
        self.font_data = font_data
        self.animation_type = animation_type

        self.line_gap = 5
        self.frames_per_letter = 2 
        
    def draw_text(self, fctx, frame, cr, x, y):
        # Create line layouts.
        self.line_layouts = []
        for line_text in self.lines:
            line_layout = fctx.create_text_layout(self.font_data)
            line_layout.create_pango_layout(cr, line_text) # add text now that we cairo context
            self.line_layouts.append(line_layout)
        
        # Compute line positions.
        pango_alignment = self.line_layouts[0].get_pango_alignment() # all lines have the same alignment
        line_positions = []
        if pango_alignment == Pango.Alignment.LEFT:
            for line_layout in self.line_layouts:
                w, h = line_layout.get_pixel_size()
                line_positions.append((x, y))
                y = y + h + self.line_gap
        elif pango_alignment == Pango.Alignment.CENTER:
            max_width = self.get_line_max_width()
            for line_layout in self.line_layouts:
                w, h = line_layout.get_pixel_size()
                line_positions.append((x + max_width/2 - w/2, y))
                y = y + h + self.line_gap
        else:
            max_width = self.get_line_max_width()
            for line_layout in self.line_layouts:
                w, h = line_layout.get_pixel_size()
                line_positions.append((x + max_width - w, y))
                y = y + h + self.line_gap
        
        # Get last letter index.
        if self.animation_type == ANIMATION_BY_LETTER:
            last_letter = int(frame / self.frames_per_letter)
        
        # Create line texts.
        line_texts = []
        line_first_char = 0
        for line_text in self.lines:
            line_last_char = line_first_char + len(line_text)
            if line_last_char < last_letter:
                line_texts.append(line_text)
            elif line_first_char > last_letter:
                line_texts.append("")
            else:
                line_texts.append(line_text[0:last_letter - line_first_char])
            line_first_char = line_last_char

        # Draw texts.
        for i in range(0, len(self.line_layouts)):
            line_layout = self.line_layouts[i]
            x, y = line_positions[i]
            txt = line_texts[i]
            line_layout.draw_layout(txt, cr, x, y)
    
    def get_line_max_width(self):
        max_width = 0
        for line_layout in self.line_layouts:
            w, h = line_layout.get_pixel_size()
            if w > max_width:
                max_width = w
        return max_width
                    
