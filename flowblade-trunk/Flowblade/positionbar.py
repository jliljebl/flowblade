"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <http://code.google.com/p/flowblade>.

    Flowblade Movie Editor is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Flowblade Movie Editor is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
Module contents: 
class PositionBar - Displays position on a clip or a sequence
"""

import pygtk
pygtk.require('2.0');
import gtk
import cairo

from cairoarea import CairoDrawableArea
import editorpersistance
import editorstate
import trimmodes

# Draw params
BAR_WIDTH = 200 # NOTE: DOES NOT HAVE ANY EFFECT IF OTHER WIDTHS MAKE MONITOR AREA MIN WIDTH BIGGER, AS THIS EXPANDS TO FILL
BAR_HEIGHT = 20 # component height
LINE_WIDTH = 3
LINE_HEIGHT = 6
LINE_COLOR = (0.3, 0.3, 0.3)
LINE_COUNT = 11 # Number of range lines
BG_COLOR = (1, 1, 1)
DISABLED_BG_COLOR = (0.7, 0.7, 0.7)
SELECTED_RANGE_COLOR = (0.85, 0.85, 0.85)
DARK_LINE_COLOR = (0.9, 0.9, 0.9)
DARK_BG_COLOR = (0.3, 0.3, 0.3)
DARK_DISABLED_BG_COLOR = (0.1, 0.1, 0.1)
DARK_SELECTED_RANGE_COLOR = (0.5, 0.5, 0.5)
SPEED_TEST_COLOR = (0.5, 0.5, 0.5)
POINTER_COLOR = (1, 0.3, 0.3)
END_PAD = 6 # empty area at both ends in pixels
MARK_CURVE = 5
MARK_LINE_WIDTH = 4
MARK_PAD = 4

MARK_COLOR = (0.3, 0.3, 0.3)
DARK_MARK_COLOR = (0.1, 0.1, 0.1)


class PositionBar:
    """
    GUI component used to set/display position in clip/timeline
    """

    def __init__(self):
        self.widget = CairoDrawableArea(BAR_WIDTH, 
                                        BAR_HEIGHT, 
                                        self._draw)
        self.widget.press_func = self._press_event
        self.widget.motion_notify_func = self._motion_notify_event
        self.widget.release_func = self._release_event
        self._pos = END_PAD # in display pixels
        self.mark_in_norm = -1.0 # program length normalized
        self.mark_out_norm = -1.0
        self.disabled = False
        self.mouse_release_listener = None # when used in tools (Tiler ate.) this used to update bg image

        if editorpersistance.prefs.dark_theme == True:
            global LINE_COLOR, BG_COLOR, DISABLED_BG_COLOR, SELECTED_RANGE_COLOR, MARK_COLOR
            LINE_COLOR = DARK_LINE_COLOR
            BG_COLOR = DARK_BG_COLOR
            DISABLED_BG_COLOR = DARK_DISABLED_BG_COLOR
            SELECTED_RANGE_COLOR = DARK_SELECTED_RANGE_COLOR
            MARK_COLOR = DARK_MARK_COLOR

    def set_listener(self, listener):
        self.position_listener = listener

    def set_normalized_pos(self, norm_pos):
        """
        Sets position in range 0 - 1
        """
        self._pos = self._get_panel_pos(norm_pos)
        self.widget.queue_draw()

    def update_display_from_producer(self, producer):
        self.producer = producer
        length = producer.get_length() # Get from MLT
        try:
            self.mark_in_norm = float(producer.mark_in) / length
            self.mark_out_norm = float(producer.mark_out) / length
            frame_pos = producer.frame()
            norm_pos = float(frame_pos) / length
            self._pos = self._get_panel_pos(norm_pos)
        except ZeroDivisionError:
            self.mark_in_norm = 0
            self.mark_out_norm = 0
            self._pos = self._get_panel_pos(0)

        self.widget.queue_draw()

    def _get_panel_pos(self, norm_pos):
        return END_PAD + int(norm_pos * 
               (self.widget.allocation.width - 2 * END_PAD))

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation
        
        # Draw bb
        draw_color = BG_COLOR
        if self.disabled:
            draw_color = DISABLED_BG_COLOR
        cr.set_source_rgb(*draw_color)
        cr.rectangle(0,0,w,h)
        cr.fill()
        
        # Draw selected area if marks set
        if self.mark_in_norm >= 0 and self.mark_out_norm >= 0:
            cr.set_source_rgb(*SELECTED_RANGE_COLOR)
            m_in = self._get_panel_pos(self.mark_in_norm)
            m_out = self._get_panel_pos(self.mark_out_norm)
            cr.rectangle(m_in, 0, m_out - m_in, h)
            cr.fill()
                
        # Get area between end pads
        active_width = w - 2 * END_PAD

        # Draw lines
        cr.set_line_width(1.0)
        x_step = float(active_width) / (LINE_COUNT)        
        for i in range(LINE_COUNT + 1):
            cr.move_to(int((i) * x_step) + END_PAD + 0.5, -0.5)
            cr.line_to(int((i) * x_step) + END_PAD + 0.5, LINE_HEIGHT + 0.5)
        for i in range(LINE_COUNT + 1):
            cr.move_to(int((i) * x_step) + END_PAD + 0.5, BAR_HEIGHT)
            cr.line_to(int((i) * x_step) + END_PAD + 0.5, 
                       BAR_HEIGHT - LINE_HEIGHT  + 0.5)
            
        cr.set_source_rgb(*LINE_COLOR)
        cr.stroke()

        # Draw mark in and mark out
        self.draw_mark_in(cr, h)
        self.draw_mark_out(cr, h)

        # Draw position pointer
        if self.disabled:
            return
        cr.set_line_width(2.0)
        cr.set_source_rgb(*POINTER_COLOR)
        cr.move_to(self._pos + 0.5, 0)
        cr.line_to(self._pos + 0.5, BAR_HEIGHT)
        cr.stroke()

        speed = editorstate.PLAYER().producer.get_speed()
        if speed != 1.0 and speed != 0.0:
            cr.set_source_rgb(*SPEED_TEST_COLOR)
            cr.select_font_face ("sans-serif",
                                 cairo.FONT_SLANT_NORMAL,
                                 cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(11)
            disp_str = str(speed) + "x"
            tx, ty, twidth, theight, dx, dy = cr.text_extents(disp_str)
            cr.move_to( w/2 - twidth/2, 13)
            cr.show_text(disp_str)

    def draw_mark_in(self, cr, h):
        """
        Draws mark in graphic if set.
        """
        if self.mark_in_norm < 0:
            return
             
        x = self._get_panel_pos(self.mark_in_norm)

        cr.move_to (x, MARK_PAD)
        cr.line_to (x, h - MARK_PAD)
        cr.line_to (x - 2 * MARK_LINE_WIDTH, h - MARK_PAD)
        cr.line_to (x - 2 * MARK_LINE_WIDTH, 
                    h - MARK_LINE_WIDTH - MARK_PAD) 
        cr.line_to (x - MARK_LINE_WIDTH, h - MARK_LINE_WIDTH - MARK_PAD )
        cr.line_to (x - MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD)
        cr.line_to (x - 2 * MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD )
        cr.line_to (x - 2 * MARK_LINE_WIDTH, MARK_PAD)
        cr.close_path();

        cr.set_source_rgb(*MARK_COLOR)
        cr.fill()

    def draw_mark_out(self, cr, h):
        """
        Draws mark out graphic if set.
        """
        if self.mark_out_norm < 0:
            return
             
        x = self._get_panel_pos(self.mark_out_norm)

        cr.move_to (x, MARK_PAD)
        cr.line_to (x, h - MARK_PAD)
        cr.line_to (x + 2 * MARK_LINE_WIDTH, h - MARK_PAD)
        cr.line_to (x + 2 * MARK_LINE_WIDTH, 
                    h - MARK_LINE_WIDTH - MARK_PAD) 
        cr.line_to (x + MARK_LINE_WIDTH, h - MARK_LINE_WIDTH - MARK_PAD )
        cr.line_to (x + MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD)
        cr.line_to (x + 2 * MARK_LINE_WIDTH, MARK_LINE_WIDTH + MARK_PAD )
        cr.line_to (x + 2 * MARK_LINE_WIDTH, MARK_PAD)
        cr.close_path();

        cr.set_source_rgb(*MARK_COLOR)
        cr.fill()

    def _press_event(self, event):
        """
        Mouse button callback
        """
        if self.disabled:
            return
        if editorstate.timeline_visible():
            trimmodes.set_no_edit_trim_mode()

        if((event.button == 1)
            or(event.button == 3)):
            # Set pos to in active range to get normalized pos
            self._pos = self._legalize_x(event.x)
            # Listener calls self.set_normalized_pos()
            # _pos gets actually set twice
            # Listener also updates other frame displayers
            self.position_listener(self.normalized_pos(), self.producer.get_length())

    def _motion_notify_event(self, x, y, state):
        """
        Mouse move callback
        """
        if self.disabled:
            return

        if((state & gtk.gdk.BUTTON1_MASK)
            or (state & gtk.gdk.BUTTON3_MASK)):
            self._pos = self._legalize_x(x)
            # Listener calls self.set_normalized_pos()
            self.position_listener(self.normalized_pos(), self.producer.get_length())

    def _release_event(self, event):
        """
        Mouse release callback.
        """
        if self.disabled:
            return

        self._pos = self._legalize_x(event.x)
        # Listener calls self.set_normalized_pos()
        self.position_listener(self.normalized_pos(), self.producer.get_length())

        if self.mouse_release_listener != None:
            self.mouse_release_listener(self.normalized_pos(), self.producer.get_length())
 
    def _legalize_x(self, x):
        """
        Get x in pixel range corresponding normalized position 0.0 - 1.0.
        This is needed because of end pads.
        """
        w = self.widget.allocation.width
        if x < END_PAD:
            return END_PAD
        elif x > w - END_PAD:
            return w - END_PAD
        else:
            return x
    
    def normalized_pos(self):
        return float(self._pos - END_PAD) / \
                (self.widget.allocation.width - END_PAD * 2)

