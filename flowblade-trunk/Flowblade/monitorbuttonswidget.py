
import cairo
import gtk
import math
import pango
import pangocairo

from cairoarea import CairoDrawableArea
import gui
import respaths

BUTTONS_GRAD_STOPS = [   (1, 0.5, 0.5, 0.5, 1),
                        (0, 0.7, 0.7, 0.7, 1)]

BUTTONS_PRESSED_GRAD_STOPS = [(1, 0.5, 0.5, 0.5, 1),
                             (0, 0.5, 0.5, 0.5, 1)]
                        
WIDTH = 400
HEIGHT = 30
TEXT_X = 10
TEXT_Y = 10
TC_COLOR = (0.7, 0.7, 0.7)

CORNER_DIVIDER = 5

BUTTON_HEIGHT = 22
BUTTON_WIDTH = 35
BUTTON_Y = 4
BUTTON_IMAGE_Y = 6

M_PI = math.pi

NO_HIT = -1

class MonitorButtons:

    def __init__(self):
        # Create widget and connect listeners
        self.widget = CairoDrawableArea(WIDTH, 
                                        HEIGHT, 
                                        self._draw)
        self.widget.press_func = self._press_event
        self.widget.motion_notify_func = self._motion_notify_event
        self.widget.release_func = self._release_event

        self.pressed_callback_funcs = None # set later
        self.released_callback_funcs = None # set later
        
        self.pressed_button = -1
        self.first = True

        self.font_desc = pango.FontDescription("Bitstream Vera Sans Mono Condensed 15")

        self.degrees = M_PI / 180.0

                            
        IMG_PATH = respaths.IMAGE_PATH
        rew_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "backward_s.png")
        ff_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "forward_s.png")
        play_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "play_2_s.png")
        stop_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "stop_s.png")
        next_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "next_frame_s.png")
        prev_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "prev_frame_s.png")
        mark_in_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "mark_in_s.png")
        mark_out_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "mark_out_s.png")
        marks_clear_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "marks_clear_s.png") 
        to_mark_in_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "to_mark_in_s.png")        
        to_mark_out_icon = gtk.gdk.pixbuf_new_from_file(IMG_PATH + "to_mark_out_s.png") 

        self.icons = [rew_icon, ff_icon,  prev_icon, next_icon, 
                      play_icon, stop_icon, mark_in_icon, mark_out_icon, 
                      marks_clear_icon, to_mark_in_icon, to_mark_out_icon]
        self.x_fix = [7, 11, 8, 10,
                      13, 13, 6, 14,
                      5, 10, 9]


    # ------------------------------------------------------------- mouse events
    def _press_event(self, event):
        """
        Mouse button callback
        """
        self.pressed_button = self._get_hit_code(event.x, event.y)
        if self.pressed_button > -1 and self.pressed_button < len(self.icons):
            callback_func = self.pressed_callback_funcs[self.pressed_button] # index is set to match at editorwindow.py where callback func list is created
            callback_func()
        self.widget.queue_draw()

    def _motion_notify_event(self, x, y, state):
        """
        Mouse move callback
        """
        button_under = self._get_hit_code(x, y)
        if self.pressed_button != button_under: # pressed button is released
            if self.pressed_button > 0 and self.pressed_button < 2: # ff, rew
                release_func = self.released_callback_funcs[self.pressed_button]
                release_func()
            self.pressed_button = -1
        self.widget.queue_draw()

    def _release_event(self, event):
        """
        Mouse release callback
        """
        if self.pressed_button > 0 and self.pressed_button < 2: # ff, rew
            release_func = self.released_callback_funcs[self.pressed_button]
            release_func()
        self.pressed_button = -1
        self.widget.queue_draw()

    def _get_hit_code(self, x, y):
        xa, ya, w, h = self.allocation
        mid_x = w / 2
        buttons_width = BUTTON_WIDTH * len(self.icons)
        button_x = mid_x - (buttons_width / 2)

        for i in range(0, len(self.icons)):
            if ((x >= button_x) and (x <= button_x + BUTTON_WIDTH)
                and (y >= BUTTON_Y) and (y <= BUTTON_Y + BUTTON_HEIGHT)):
                    return i 
            
            button_x += BUTTON_WIDTH
        return NO_HIT

    def set_callbacks(self, pressed_callback_funcs, released_callback_funcs):
        print "wqsasdqweqwdas"
        self.pressed_callback_funcs = pressed_callback_funcs 
        self.released_callback_funcs = released_callback_funcs

    # ---------------------------------------------------------------- painting
    def _draw(self, event, cr, allocation):
        """
        if self.first == True:
            bgr, bgg, bgb = gui.bg_color_tuple
            
            global BUTTONS_GRAD_STOPS, BUTTONS_PRESSED_GRAD_STOPS
            BUTTONS_GRAD_STOPS = [   (1, bgr - 0.1, bgr - 0.1, bgr - 0.1, 1),
                            (0, bgr + 0.1, bgr + 0.1, bgr + 0.1, 1)]
            BUTTONS_PRESSED_GRAD_STOPS = [(1, 0.5, 0.5, 0.5, 1),
                                 (0, 0.5, 0.5, 0.5, 1)]
            self.first = False
        """
        x, y, w, h = allocation
        self.allocation = allocation
        
        # Draw bg
        cr.set_source_rgb(*gui.bg_color_tuple)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        mid_x = w / 2
        buttons_width = BUTTON_WIDTH * len(self.icons)
        x_start = mid_x - (buttons_width / 2)

        # line width for all strokes
        cr.set_line_width(1.0)

        # buttons gradient 
        self._set_button_draw_consts(x_start + 0.5, BUTTON_Y + 0.5, buttons_width, BUTTON_HEIGHT + 1.0)
        self._round_rect_path(cr)
        grad = cairo.LinearGradient (x_start, BUTTON_Y, x_start, BUTTON_Y + BUTTON_HEIGHT)
        for stop in BUTTONS_GRAD_STOPS:
            grad.add_color_stop_rgba(*stop)
        cr.set_source(grad)
        cr.fill()

        # pressed button gradient
        if self.pressed_button > -1:
            grad = cairo.LinearGradient (x_start, BUTTON_Y, x_start, BUTTON_Y + BUTTON_HEIGHT)
            for stop in BUTTONS_PRESSED_GRAD_STOPS:
                grad.add_color_stop_rgba(*stop)
            cr.set_source(grad)
            cr.rectangle(x_start + self.pressed_button * BUTTON_WIDTH, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
            cr.fill()
        
        #light accent
        self._round_rect_path(cr)
        cr.set_source_rgb(1,1,1)
        cr.stroke()

        # dark line
        cr.set_source_rgb(0.3,0.3,0.3)
        self._set_button_draw_consts(x_start + 0.5, BUTTON_Y + 0.5, buttons_width, BUTTON_HEIGHT)
        self._round_rect_path(cr)
        cr.stroke()

        # icons and vert lines
        x = x_start
        for i in range(0, len(self.icons)):
            icon = self.icons[i]
            cr.set_source_pixbuf(icon, x + self.x_fix[i], BUTTON_IMAGE_Y)
            cr.paint()
            #cr.move_to(x + BUTTON_WIDTH, BUTTON_Y)
            if (i > 0) and (i < len(self.icons)):
                cr.move_to(x + 0.5, BUTTON_Y)
                cr.line_to(x + 0.5, BUTTON_Y + BUTTON_HEIGHT)
                #cr.line_to(x + BUTTON_WIDTH, BUTTON_Y + BUTTON_HEIGHT)
                
                cr.set_source_rgb(0,0,0)
                cr.stroke()
            
            x += BUTTON_WIDTH
            
        """
        self._round_rect_path(cr)        
        cr.set_source_rgb(1, 0.2, 0.2)
        #cr.fill_preserve()
        cr.stroke()

        pango_context = pangocairo.CairoContext(cr)
        layout = pango_context.create_layout()
        layout.set_text("seq1")
        layout.set_font_description(self.font_desc)

        pango_context.set_source_rgb(*TC_COLOR)#0.7, 0.7, 0.7)
        pango_context.move_to(TEXT_X, TEXT_Y)
        pango_context.update_layout(layout)
        pango_context.show_layout(layout)
        """

    def _set_button_draw_consts(self, x, y, width, height):
        aspect = 1.0
        corner_radius = height / CORNER_DIVIDER
        radius = corner_radius / aspect

        self._draw_consts = (x, y, width, height, aspect, corner_radius, radius)
        
    def _round_rect_path(self, cr):
        x, y, width, height, aspect, corner_radius, radius = self._draw_consts
        degrees = self.degrees

        cr.new_sub_path()
        cr.arc (x + width - radius, y + radius, radius, -90 * degrees, 0 * degrees)
        cr.arc (x + width - radius, y + height - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc (x + radius, y + height - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc (x + radius, y + radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path ()

