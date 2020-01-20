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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

import cairoarea

STRIP_HEIGHT = 8

_timeline_renderer = None

# These are monkeypatched in at app.py
_get_frame_for_x_func = None
_get_x_for_frame_func = None
_get_last_tline_view_frame_func = None

SEGMENT_NOOP = 0
SEGMENT_RENDERED_AREA = 1
SEGMENT_UNRENDERED_RENDERED_AREA = 2

_segment_colors = { SEGMENT_NOOP:(0.26, 0.29, 0.42),
                    SEGMENT_RENDERED_AREA:(0.29, 0.78, 0.30),
                    SEGMENT_UNRENDERED_RENDERED_AREA:(0.76, 0.27, 0.27)}

# ------------------------------------------------------------ MODULE INTERFACE
def init_for_sequence(sequence):
    global _timeline_renderer
    _timeline_renderer = TimeLineRenderer()

    #---testing
    seg = TimeLineSegment(SEGMENT_NOOP, 0, 50)
    _timeline_renderer.segments.append(seg)
    seg = TimeLineSegment(SEGMENT_RENDERED_AREA, 50, 70)
    _timeline_renderer.segments.append(seg)
    seg = TimeLineSegment(SEGMENT_NOOP, 70, 80)
    _timeline_renderer.segments.append(seg)
    seg = TimeLineSegment(SEGMENT_RENDERED_AREA, 80, 90)
    _timeline_renderer.segments.append(seg)

def get_renderer():
    return _timeline_renderer


class TimeLineRenderer:

    def __init__(self):
        self.segments = []


    # --------------------------------------------- DRAW
    def draw(self, event, cr, allocation, pos, pix_per_frame):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        x, y, w, h = allocation

        cr.set_source_rgb(*_segment_colors[SEGMENT_NOOP])
        cr.rectangle(0,0,w,h)
        cr.fill_preserve()
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()

        for seg in self.segments:
            if seg.end_frame < pos:
                continue
            if seg.start_frame > _get_last_tline_view_frame_func():
                break
            if seg.segment_type == SEGMENT_NOOP:
                continue
            seg.draw(cr, h, pos, pix_per_frame)


        # --------------------------------------------- MOUSE EVENTS    
    def _press_event(self, event):
        if event.button == 1 or event.button == 3:
            self.drag_on = True
            pass

    def _motion_notify_event(self, x, y, state):
        if((state & Gdk.ModifierType.BUTTON1_MASK)
           or(state & Gdk.ModifierType.BUTTON3_MASK)):
            if self.drag_on:
                pass
                
    def _release_event(self, event):
        if self.drag_on:
            pass
        self.drag_on = False
        
    

class TimeLineSegment:

    def __init__(self, segment_type, start_frame, end_frame):
        self.segment_type = segment_type
        
        self.start_frame = start_frame # inclusive
        self.end_frame = end_frame # exclusive

    # --------------------------------------------- DRAW
    def draw(self, cr, height, pos, pix_per_frame):
        x = int(_get_x_for_frame_func(self.start_frame))
        x_end = int(_get_x_for_frame_func(self.end_frame))
        w = x_end - x
        cr.set_source_rgb(*_segment_colors[self.segment_type ])
        cr.rectangle(x, 0, w ,height)
        cr.fill_preserve()
        #cr.rectangle(0.5,0.5, w - 0.5, h - 0.5)
        cr.set_source_rgb(0, 0, 0)
        cr.stroke()

