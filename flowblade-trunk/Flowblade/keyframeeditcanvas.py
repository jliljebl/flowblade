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
Module contains GUI widgets used edit geometries on canvas with a mouse.
"""

import copy
import math

from gi.repository import Gdk

import cairoarea
import utils
import viewgeom

EP_HALF = 4

GEOMETRY_EDITOR_WIDTH = 250
GEOMETRY_EDITOR_HEIGHT = 200

# Rectangle edit handles ids. Points numbered in clockwise direction 
# to get opposite points easily.
TOP_LEFT = 0
TOP_MIDDLE = 1
TOP_RIGHT = 2
MIDDLE_RIGHT = 3
BOTTOM_RIGHT = 4
BOTTOM_MIDDLE = 5
BOTTOM_LEFT = 6
MIDDLE_LEFT = 7

# Rotating rectangle handle ids
POS_HANDLE = 0
X_SCALE_HANDLE = 1
Y_SCALE_HANDLE = 2
ROTATION_HANDLE = 3

# Hit values for rect, edit point hits return edit point id
AREA_HIT = 9
NO_HIT = 10

EDITABLE_RECT_COLOR = (0,0,0)

_shift_down = None


# -------------------------------------------------------------- shape objects
class EditRect:
    """
    Line box with corner and middle handles that user can use to set
    position, width and height of rectangle geometry.
    """
    def __init__(self, x, y, w, h):
        self.edit_points = {}
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.start_x = None
        self.start_y = None
        self.start_w = None
        self.start_h = None
        self.start_op_x = None
        self.start_op_y = None
        self.projection_point = None
        self.set_edit_points()
        
    def set_geom(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.set_edit_points()
        
    def set_edit_points(self):
        self.edit_points[TOP_LEFT] = (self.x, self.y)
        self.edit_points[TOP_MIDDLE] = (self.x + self.w/2, self.y)
        self.edit_points[TOP_RIGHT] = (self.x + self.w, self.y)
        self.edit_points[MIDDLE_LEFT] = (self.x, self.y + self.h/2)
        self.edit_points[MIDDLE_RIGHT] = (self.x + self.w, self.y + self.h/2)
        self.edit_points[BOTTOM_LEFT] = (self.x, self.y + self.h)
        self.edit_points[BOTTOM_MIDDLE] = (self.x + self.w/2, self.y + self.h)
        self.edit_points[BOTTOM_RIGHT] = (self.x + self.w, self.y + self.h)
        
    def check_hit(self, x, y):
        for id_int, value in self.edit_points.iteritems():
            x1, y1 = value
            if (x >= x1 - EP_HALF and x <= x1 + EP_HALF and y >= y1 - EP_HALF and y <= y1 + EP_HALF):
                return id_int
            
        x1, y1 = self.edit_points[TOP_LEFT]     
        x2, y2 = self.edit_points[BOTTOM_RIGHT]
        
        if (x >= x1 and x <= x2 and y >= y1 and y <= y2):
            return AREA_HIT
            
        return NO_HIT
    
    def edit_point_drag_started(self, ep_id):
        opposite_id = (ep_id + 4) % 8
        
        self.drag_ep = ep_id
        self.guide_line = viewgeom.get_line_for_points( self.edit_points[ep_id],
                                                        self.edit_points[opposite_id])
        x, y = self.edit_points[ep_id]
        self.start_x = x
        self.start_y = y
        opx, opy = self.edit_points[opposite_id]
        self.start_op_x = opx
        self.start_op_y = opy
        self.start_w = self.w
        self.start_h = self.h
    
        self.projection_point = (x, y)
    
    def edit_point_drag(self, delta_x, delta_y):
        x = self.start_x + delta_x
        y = self.start_y + delta_y

        p = (x, y)
        lx, ly = self.guide_line.get_normal_projection_point(p)
        self.projection_point = (lx, ly)

        # Set new rect
        if self.drag_ep == TOP_LEFT:
            self.x = lx
            self.y = ly
            self.w = self.start_op_x - lx
            self.h = self.start_op_y - ly
        elif self.drag_ep == BOTTOM_RIGHT:
            self.x = self.start_op_x
            self.y = self.start_op_y
            self.w = lx - self.start_op_x
            self.h = ly - self.start_op_y
        elif self.drag_ep == BOTTOM_LEFT:
            self.x = lx
            self.y = self.start_op_y
            self.w = self.start_op_x - lx
            self.h = ly - self.start_op_y
        elif self.drag_ep == TOP_RIGHT:
            self.x = self.start_op_x
            self.y = ly
            self.w = lx - self.start_op_x
            self.h = self.start_op_y - ly
        elif self.drag_ep == MIDDLE_RIGHT:
            self.x = self.start_op_x
            self.y = self.start_op_y - (self.start_h / 2.0)
            self.w = lx - self.start_op_x
            self.h = self.start_h
        elif self.drag_ep == MIDDLE_LEFT:
            self.x = lx
            self.y = self.start_y - (self.start_h / 2.0)
            self.w = self.start_op_x - lx
            self.h = self.start_h
        elif self.drag_ep == TOP_MIDDLE:
            self.x = self.start_x - (self.start_w / 2.0)
            self.y = ly
            self.w = self.start_w
            self.h = self.start_op_y - ly
        elif self.drag_ep == BOTTOM_MIDDLE:
            self.x = self.start_op_x - (self.start_w / 2.0)
            self.y = self.start_op_y
            self.w = self.start_w
            self.h = ly - self.start_op_y
        
        # No negative size
        if self.w < 1.0:
            self.w = 1.0
        if self.h < 1.0:
            self.h = 1.0

        self.set_edit_points()
    
    def clear_projection_point(self):
        self.projection_point = None
    
    def move_started(self):
        self.start_x = self.x
        self.start_y = self.y
    
    def move_drag(self, delta_x, delta_y):
        self.x = self.start_x + delta_x
        self.y = self.start_y + delta_y

        self.set_edit_points()
        
    def draw(self, cr):
        # Box
        cr.set_line_width(1.0)
        color = EDITABLE_RECT_COLOR
        cr.set_source_rgb(*color)
        cr.rectangle(self.x + 0.5, self.y + 0.5, self.w, self.h)
        cr.stroke()

        # handles
        for id_int, pos in self.edit_points.iteritems():
            x, y = pos
            cr.rectangle(x - 2, y - 2, 4, 4)
            cr.fill()
        
        if self.projection_point != None:
            x, y = self.projection_point
            cr.set_source_rgb(0,1,0)
            cr.rectangle(x - 2, y - 2, 4, 4)
            cr.fill()

# ---------------------------------------------------- screen editors
def _geom_kf_sort(kf):
    """
    Function is used to sort keyframes by frame number.
    """
    frame, shape, opacity = kf
    return frame 
        

class AbstractEditCanvas:
    """
    Base class for editors used to edit something on top of rectangle representing 
    screen.
    
    parent_editor needs to implement interface
        mouse_scroll_up()
        mouse_scroll_down()
        geometry_edit_started()
        update_request_from_geom_editor()
        queue_draw()
        geometry_edit_finished()
    """
    def __init__(self, editable_property, parent_editor):
        self.widget = cairoarea.CairoDrawableArea2( GEOMETRY_EDITOR_WIDTH, 
                                                    GEOMETRY_EDITOR_HEIGHT, 
                                                    self._draw)

        self.widget.press_func = self._press_event
        self.widget.motion_notify_func = self._motion_notify_event
        self.widget.release_func = self._release_event
        self.widget.mouse_scroll_func = self._mouse_scroll_listener

        self.clip_length = editable_property.get_clip_length()
        self.pixel_aspect_ratio = editable_property.get_pixel_aspect_ratio()
        self.current_clip_frame = 0
        
        # Keyframe tuples are of type (frame, rect, opacity)
        self.keyframes = None # Set using function AbstractScreenEditor.set_keyframes(). Keyframes are in form [frame, shape, opacity]
        self.keyframe_parser = None # Function used to parse keyframes to tuples is different for different expressions
                                    # Parent editor sets this.
            
        self.current_mouse_hit = None
        self.start_x = None
        self.start_Y = None

        self.parent_editor = parent_editor
        
        self.source_width = -1 # unscaled source image width, set later
        self.source_height = -1 # unscaled source image height, set later
        
        self.coords = None # Calculated later when we have allocation available
        
    def init_editor(self, source_width, source_height, y_fract):
        self.source_width = source_width 
        self.source_height = source_height
        self.y_fract = y_fract
        self.screen_ratio = float(source_width) / float(source_height)

    # ---------------------------------------------------- draw params
    def _create_coords(self):
        self.coords = utils.EmptyClass()
        panel_w = self.widget.get_allocation().width
        panel_h = self.widget.get_allocation().height
        self.coords.screen_h = panel_h * self.y_fract
        self.coords.screen_w = self.coords.screen_h * self.screen_ratio * self.pixel_aspect_ratio
        self.coords.orig_x = (panel_w - self.coords.screen_w) / 2.0
        self.coords.orig_y = (panel_h - self.coords.screen_h) / 2.0
        self.coords.x_scale = self.source_width / self.coords.screen_w
        self.coords.y_scale = self.source_height / self.coords.screen_h

    def set_view_size(self, y_fract):
        self.y_fract = y_fract
        self._create_coords()

    def get_screen_x(self, x):
        p_x_from_origo = x - self.coords.orig_x
        return p_x_from_origo * self.coords.x_scale
        
    def get_screen_y(self, y):
        p_y_from_origo = y - self.coords.orig_y
        return p_y_from_origo * self.coords.y_scale

    def get_panel_point(self, x, y):
        px = self.coords.orig_x + x / self.coords.x_scale
        py = self.coords.orig_y + y / self.coords.y_scale
        return (px, py)       

    # --------------------------------------------------------- updates 
    def set_clip_frame(self, frame):
        self.current_clip_frame = frame
        self._clip_frame_changed()
    
    def _clip_frame_changed(self):
        print "_clip_frame_changed not impl"

    def set_keyframe_to_edit_shape(self, kf_index, value_shape=None):
        if value_shape == None:
            value_shape = self._get_current_screen_shape()
        
        frame, shape, opacity = self.keyframes[kf_index]
        self.keyframes.pop(kf_index)
        
        new_kf = (frame, value_shape, opacity)
        self.keyframes.append(new_kf)
        self.keyframes.sort(key=_geom_kf_sort)
        
        self._update_shape()
    
    def _get_current_screen_shape(self):
        print "_get_current_screen_shape not impl"
    
    def _update_shape(self):
        print "_update_shape not impl"

    # ------------------------------------------------- keyframes
    def add_keyframe(self, frame):
        if self._frame_has_keyframe(frame) == True:
            return

        # Get previous keyframe
        prev_kf = None
        for i in range(0, len(self.keyframes)):
            p_frame, p_shape, p_opacity = self.keyframes[i]
            if p_frame < frame:
                prev_kf = self.keyframes[i]                
        if prev_kf == None:
            prev_kf = self.keyframes[len(self.keyframes) - 1]
        
        # Add with values of previous
        p_frame, p_shape, p_opacity = prev_kf
        self.keyframes.append((frame, copy.deepcopy(p_shape), copy.deepcopy(p_opacity)))
        
        self.keyframes.sort(key=_geom_kf_sort)
        
    def delete_active_keyframe(self, keyframe_index):
        if keyframe_index == 0:
            # keyframe frame 0 cannot be removed
            return
        self.keyframes.pop(keyframe_index)

    def _frame_has_keyframe(self, frame):
        for i in range(0, len(self.keyframes)):
            kf = self.keyframes[i]
            kf_frame, rect, opacity = kf
            if frame == kf_frame:
                return True

        return False

    def set_keyframes(self, keyframes_str, out_to_in_func):
        self.keyframes = self.keyframe_parser(keyframes_str, out_to_in_func)
    
    def set_keyframe_frame(self, active_kf_index, frame):
        old_frame, shape, opacity = self.keyframes[active_kf_index]
        self.keyframes.pop(active_kf_index)
        self.keyframes.insert(active_kf_index, (frame, shape, opacity))    

    def get_keyframe(self, kf_index):
        return self.keyframes[kf_index]

    # ---------------------------------------------------- editor menu actions
    def reset_active_keyframe_shape(self, active_kf_index):
        print "reset_active_keyframe_shape not impl"

    def reset_active_keyframe_rect_shape(self, active_kf_index):
        print "reset_active_keyframe_rect_shape not impl" 

    def center_h_active_keyframe_shape(self, active_kf_index):
        print "center_h_active_keyframe_shape not impl"

    def center_v_active_keyframe_shape(self, active_kf_index):
        print "center_v_active_keyframe_shape not impl"

    # ------------------------------------------------------ arrow edit
    def handle_arrow_edit(self, keyval):
        print "handle_arrow_edit not impl"

    # -------------------------------------------------------- mouse events
    def _press_event(self, event):
        """
        Mouse button callback
        """
        self.current_mouse_hit = self._check_shape_hit(event.x, event.y)
        if self.current_mouse_hit == NO_HIT:
            return
        
        self.mouse_start_x = event.x
        self.mouse_start_y = event.y

        self._shape_press_event()

        self.parent_editor.geometry_edit_started()
        self.parent_editor.update_request_from_geom_editor()

    def _check_shape_hit(self, x, y):
        print "_check_shape_hit not impl"

    def _shape_press_event(self):
        print "_shape_press_event not impl"
        
    def _motion_notify_event(self, x, y, state):
        """
        Mouse move callback
        """
        if self.current_mouse_hit == NO_HIT:
            return
        
        delta_x = x - self.mouse_start_x
        delta_y = y - self.mouse_start_y
        
        global _shift_down 
        if state & Gdk.ModifierType.SHIFT_MASK:
            if abs(x - self.mouse_start_x) < abs(y - self.mouse_start_y):
                delta_x = 0
            else:
                delta_y = 0
            _shift_down = (self.mouse_start_x, self.mouse_start_y)
        else:
            _shift_down = None
                
        self._shape__motion_notify_event(delta_x, delta_y, (state & Gdk.ModifierType.CONTROL_MASK))

        self.parent_editor.queue_draw()
    
    def _shape__motion_notify_event(self, delta_x, delta_y, CTRL_DOWN):
        print "_shape__motion_notify_event not impl"

    def _release_event(self, event):
        global _shift_down 
        _shift_down = None
        
        if self.current_mouse_hit == NO_HIT:
            return
            
        delta_x = event.x - self.mouse_start_x
        delta_y = event.y - self.mouse_start_y

        if event.get_state() & Gdk.ModifierType.SHIFT_MASK:
            if abs(event.x - self.mouse_start_x) < abs(event.y - self.mouse_start_y):
                delta_x = 0
            else:
                delta_y = 0
                
        self._shape_release_event(delta_x, delta_y, (event.get_state() & Gdk.ModifierType.CONTROL_MASK))
            
        self.parent_editor.geometry_edit_finished()

    def _shape_release_event(self, delta_x, delta_y, CTRL_DOWN):
        print "_shape_release_event not impl"

    def _mouse_scroll_listener(self, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self.parent_editor.mouse_scroll_up()
        else:
            self.parent_editor.mouse_scroll_down()
        
        return True

    # ----------------------------------------------- drawing
    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo contect and allocation.
        """
        if self.coords == None:
            self._create_coords()
        
        x, y, w, h = allocation
        
        # Draw bg
        cr.set_source_rgb(0.75, 0.75, 0.77)
        cr.rectangle(0, 0, w, h)
        cr.fill()
        
        # Draw screen
        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.rectangle(self.coords.orig_x, self.coords.orig_y, 
                       self.coords.screen_w, self.coords.screen_h)
        cr.fill()

        if _shift_down != None:
            cr.set_source_rgb(0.0, 0.0, 0.77)
            cr.set_line_width(1.0)
            mx, my = _shift_down
            cr.move_to(mx, 0)
            cr.line_to(mx, h)
            cr.stroke()
            cr.move_to(0, my)
            cr.line_to(w, my)
            cr.stroke()
            
        screen_rect = [self.coords.orig_x, self.coords.orig_y, 
                       self.coords.screen_w, self.coords.screen_h]
        self._draw_edge(cr, screen_rect)
        
        self._draw_edit_shape(cr, allocation)

    def _draw_edge(self, cr, rect):
        cr.set_line_width(1.0)
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(rect[0] + 0.5, rect[1] + 0.5, rect[2], rect[3])
        cr.stroke()

    def _draw_edit_shape(self, cr, allocation):
        print "_draw_edit_shape not impl."
        

class BoxEditCanvas(AbstractEditCanvas):
    """
    GUI component for editing position and scale values of keyframes 
    of source image in compositors. 
    
    Component is used as a part of e.g GeometryEditor, which handles
    also keyframe creation and deletion and opacity, and
    writing out the keyframes with combined information.

    Required parent_editor callback interface:
        mouse_scroll_up()
        mouse_scroll_down()
        geometry_edit_started()
        update_request_from_geom_editor()
        queue_draw()
        geometry_edit_finished()
    """
    def __init__(self, editable_property, parent_editor):
        AbstractEditCanvas.__init__(self, editable_property, parent_editor)
        self.source_edit_rect = None # Created later when we have allocation available

    def reset_active_keyframe_shape(self, active_kf_index):
        frame, old_rect, opacity = self.keyframes[active_kf_index]
        rect = [0, 0, self.source_width, self.source_height]
        self.keyframes.pop(active_kf_index)
        self.keyframes.insert(active_kf_index, (frame, rect, opacity))     

    def reset_active_keyframe_rect_shape(self, active_kf_index):
        frame, old_rect, opacity = self.keyframes[active_kf_index]
        x, y, w, h = old_rect
        new_h = int(float(w) * (float(self.source_height) / float(self.source_width)))
        rect = [x, y, w, new_h]
        self.keyframes.pop(active_kf_index)
        self.keyframes.insert(active_kf_index, (frame, rect, opacity))   

    def center_h_active_keyframe_shape(self, active_kf_index):
        frame, old_rect, opacity = self.keyframes[active_kf_index]
        ox, y, w, h = old_rect
        x = self.source_width / 2 - w / 2
        rect = [x, y, w, h ]
        self.keyframes.pop(active_kf_index)
        self.keyframes.insert(active_kf_index, (frame, rect, opacity))

    def center_v_active_keyframe_shape(self, active_kf_index):
        frame, old_rect, opacity = self.keyframes[active_kf_index]
        x, oy, w, h = old_rect
        y = self.source_height / 2 - h / 2
        rect = [x, y, w, h ]
        self.keyframes.pop(active_kf_index)
        self.keyframes.insert(active_kf_index, (frame, rect, opacity))

    def _clip_frame_changed(self):
        if self.source_edit_rect != None:
            self._update_source_rect()
    
    def _update_shape(self):
        self._update_source_rect()
    
    def _update_source_rect(self):
        for i in range(0, len(self.keyframes)):
            frame, rect, opacity = self.keyframes[i]
            if frame == self.current_clip_frame:
                self.source_edit_rect.set_geom(*self._get_screen_to_panel_rect(rect))
                return
            
            try:
                # See if frame between this and next keyframe
                frame_n, rect_n, opacity_n = self.keyframes[i + 1]
                if ((frame < self.current_clip_frame)
                    and (self.current_clip_frame < frame_n)):
                    time_fract = float((self.current_clip_frame - frame)) / \
                                 float((frame_n - frame))
                    frame_rect = self._get_interpolated_rect(rect, rect_n, time_fract)
                    self.source_edit_rect.set_geom(*self._get_screen_to_panel_rect(frame_rect))
                    return
            except: # past last frame, use its value
                self.source_edit_rect.set_geom(*self._get_screen_to_panel_rect(rect))
                return
                
        print "reached end of _update_source_rect, this should be unreachable"
        
    def _get_interpolated_rect(self, rect_1, rect_2, fract):
        x1, y1, w1, h1 = rect_1
        x2, y2, w2, h2 = rect_2
        x = x1 + (x2 - x1) * fract
        y = y1 + (y2 - y1) * fract
        w = w1 + (w2 - w1) * fract
        h = h1 + (h2 - h1) * fract
        return (x, y, w, h)
        
    def _get_screen_to_panel_rect(self, rect):
        x, y, w, h = rect
        px = self.coords.orig_x + x / self.coords.x_scale
        py = self.coords.orig_y + y / self.coords.y_scale
        pw = w / self.coords.x_scale # scale is panel to screen, this is screen to panel
        ph = h / self.coords.y_scale # scale is panel to screen, this is screen to panel
        return (px, py, pw, ph)
    
    def _get_current_screen_shape(self):
        return self._get_source_edit_rect_to_screen_rect()

    def _get_source_edit_rect_to_screen_rect(self):
        p_x_from_origo = self.source_edit_rect.x - self.coords.orig_x
        p_y_from_origo = self.source_edit_rect.y - self.coords.orig_y
        
        screen_x = p_x_from_origo * self.coords.x_scale
        screen_y = p_y_from_origo * self.coords.y_scale
        screen_w = self.source_edit_rect.w * self.coords.x_scale
        screen_h = self.source_edit_rect.h * self.coords.y_scale
        
        return [screen_x, screen_y, screen_w, screen_h]

    def _draw_edit_shape(self, cr, allocation):
        # Edit rect is created here only when we're sure to have allocation
        if self.source_edit_rect == None:
            self.source_edit_rect = EditRect(10, 10, 10, 10) # values are immediately overwritten
            self._update_source_rect()

        # Draw source
        self.source_edit_rect.draw(cr)

    # ----------------------------------------- mouse press event
    def _check_shape_hit(self, x, y):
        return self.source_edit_rect.check_hit(x, y)
    
    def _shape_press_event(self):
        if self.current_mouse_hit == AREA_HIT:
            self.source_edit_rect.move_started()
        else:
            self.source_edit_rect.edit_point_drag_started(self.current_mouse_hit)

    def _shape__motion_notify_event(self, delta_x, delta_y, CTRL_DOWN):
        if self.current_mouse_hit == AREA_HIT:
            self.source_edit_rect.move_drag(delta_x, delta_y)
        else:
            self.source_edit_rect.edit_point_drag(delta_x, delta_y)

    def _shape_release_event(self, delta_x, delta_y, CTRL_DOWN):
        if self.current_mouse_hit == AREA_HIT:
            self.source_edit_rect.move_drag(delta_x, delta_y)
        else:
            self.source_edit_rect.edit_point_drag(delta_x, delta_y)
            self.source_edit_rect.clear_projection_point()

    def handle_arrow_edit(self, keyval, delta):
        if keyval == Gdk.KEY_Left:
            self.source_edit_rect.x -= delta
        if keyval == Gdk.KEY_Right:
            self.source_edit_rect.x += delta
        if keyval == Gdk.KEY_Up:
            self.source_edit_rect.y -= delta
        if keyval == Gdk.KEY_Down:                         
            self.source_edit_rect.y += delta
            
    def print_keyframes(self):
        for i in range(0, len(self.keyframes)):
            print self.keyframes[i]


class RotatingEditCanvas(AbstractEditCanvas):
    """
    Needed parent_editor callback interface:
        mouse_scroll_up()
        mouse_scroll_down()
        geometry_edit_started()
        update_request_from_geom_editor()
        queue_draw()
        geometry_edit_finished()
        
    Keyframes in form: [frame, [x, y, x_scale, y_scale, rotation] opacity]
    """
    def __init__(self, editable_property, parent_editor):
        AbstractEditCanvas.__init__(self, editable_property, parent_editor)
        self.edit_points = []
        self.shape_x = None
        self.shape_y = None
        self.rotation = None
        self.x_scale = None
        self.y_scale = None

    def create_edit_points_and_values(self):
        # creates untransformed edit shape to init array, values will overridden shortly
        self.edit_points.append((self.source_width / 2, self.source_height / 2)) # center
        self.edit_points.append((self.source_width, self.source_height / 2)) # x_Scale
        self.edit_points.append((self.source_width / 2, 0)) # y_Scale
        self.edit_points.append((0, 0)) # rotation
        self.edit_points.append((self.source_width, 0)) # top right
        self.edit_points.append((self.source_width, self.source_height)) # bottom right
        self.edit_points.append((0, self.source_height)) # bottom left

        self.untrans_points = copy.deepcopy(self.edit_points)
     
        self.shape_x = self.source_width / 2 # always == self.edit_points[0] x
        self.shape_y = self.source_height / 2 # always == self.edit_points[0] y
        self.rotation = 0.0
        self.x_scale = 1.0
        self.y_scale = 1.0
        
    # ------------------------------------------ hit testing
    def _check_shape_hit(self, x, y):
        edit_panel_points = []
        for ep in self.edit_points:
            edit_panel_points.append(self.get_panel_point(*ep))
        
        for i in range(0, 4):
            if self._check_point_hit((x, y), edit_panel_points[i], 10):
                return i #indexes correspond to edit_point_handle indexes

        if viewgeom.point_in_convex_polygon((x, y), edit_panel_points[3:7], 0) == True: # corners are edit points 3, 4, 5, 6
            return AREA_HIT
        
        return NO_HIT
    
    def _check_point_hit(self, p, ep, TARGET_HALF):
        x, y = p
        ex, ey = ep
        if (x >= ex - TARGET_HALF and x <= ex + TARGET_HALF and y >= ey - TARGET_HALF and y <= ey + TARGET_HALF):
            return True

        return False

    # ------------------------------------------------------- menu edit events
    def reset_active_keyframe_shape(self, active_kf_index):
        frame, trans, opacity = self.keyframes[active_kf_index]
        new_trans = [self.source_width / 2, self.source_height / 2, 1.0, 1.0, 0]
        self.keyframes.pop(active_kf_index)
        self.keyframes.insert(active_kf_index, (frame, new_trans, opacity))
        self._update_shape()

    def reset_active_keyframe_rect_shape(self, active_kf_index):
        frame, trans, opacity = self.keyframes[active_kf_index]
        x, y, x_scale, y_scale, rotation = trans
        new_trans = [x, y, x_scale, x_scale, rotation]
        self.keyframes.pop(active_kf_index)
        self.keyframes.insert(active_kf_index, (frame, new_trans, opacity))
        self._update_shape()

    def center_h_active_keyframe_shape(self, active_kf_index):
        frame, trans, opacity = self.keyframes[active_kf_index]
        x, y, x_scale, y_scale, rotation = trans
        new_trans = [self.source_width / 2, y, x_scale, y_scale, rotation]
        self.keyframes.pop(active_kf_index)
        self.keyframes.insert(active_kf_index, (frame, new_trans, opacity))
        self._update_shape()

    def center_v_active_keyframe_shape(self, active_kf_index):
        frame, trans, opacity = self.keyframes[active_kf_index]
        x, y, x_scale, y_scale, rotation = trans
        new_trans = [x, self.source_height / 2, x_scale, y_scale, rotation]
        self.keyframes.pop(active_kf_index)
        self.keyframes.insert(active_kf_index, (frame, new_trans, opacity))
        self._update_shape()

    # -------------------------------------------------------- updating
    def _clip_frame_changed(self):
        self._update_shape()
            
    def _get_current_screen_shape(self):
        return [self.shape_x, self.shape_y, self.x_scale, self.y_scale, self.rotation]

    def _update_shape(self):
        for i in range(0, len(self.keyframes)):
            frame, rect, opacity = self.keyframes[i]
            if frame == self.current_clip_frame:
                self.set_geom(*rect)
                return
            
            try:
                # See if frame between this and next keyframe
                frame_n, rect_n, opacity_n = self.keyframes[i + 1]
                if ((frame < self.current_clip_frame)
                    and (self.current_clip_frame < frame_n)):
                    time_fract = float((self.current_clip_frame - frame)) / \
                                 float((frame_n - frame))
                    frame_rect = self._get_interpolated_rect(rect, rect_n, time_fract)
                    self.set_geom(*frame_rect)
                    return
            except: # past last frame, use its value  ( line: frame_n, rect_n, opacity_n = self.keyframes[i + 1] failed)
                self.set_geom(*rect)
                return
    
    def set_geom(self, x, y, x_scale, y_scale, rotation):
        self.shape_x = x
        self.shape_y = y
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.rotation = rotation
        self._update_edit_points()

    def _get_interpolated_rect(self, rect_1, rect_2, fract):
        x1, y1, xs1, ys1, r1 = rect_1
        x2, y2, xs2, ys2, r2 = rect_2
        x = x1 + (x2 - x1) * fract
        y = y1 + (y2 - y1) * fract
        xs = xs1 + (xs2 - xs1) * fract
        ys = ys1 + (ys2 - ys1) * fract
        r = r1 + (r2 - r1) * fract
        return (x, y, xs, ys, r)

    def handle_arrow_edit(self, keyval, delta):
        if keyval == Gdk.KEY_Left:
            self.shape_x -= delta
        if keyval == Gdk.KEY_Right:
            self.shape_x += delta
        if keyval == Gdk.KEY_Up:
            self.shape_y -= delta
        if keyval == Gdk.KEY_Down:                         
            self.shape_y += delta
            
    # --------------------------------------------------------- mouse events
    def _shape_press_event(self):
        self.start_edit_points = copy.deepcopy(self.edit_points)

        if self.current_mouse_hit == X_SCALE_HANDLE:
            self.guide = viewgeom.get_vec_for_points((self.shape_x,self.shape_y), self.edit_points[X_SCALE_HANDLE])
        elif self.current_mouse_hit == Y_SCALE_HANDLE:
            self.guide = viewgeom.get_vec_for_points((self.shape_x,self.shape_y), self.edit_points[Y_SCALE_HANDLE])
        elif self.current_mouse_hit == ROTATION_HANDLE:
            ax, ay = self.edit_points[POS_HANDLE]
            zero_deg_point = (ax, ay + 10)
            m_end_point = (self.get_screen_x(self.mouse_start_x), self.get_screen_y(self.mouse_start_y))
            self.mouse_start_rotation = viewgeom.get_angle_in_deg(zero_deg_point, self.edit_points[POS_HANDLE], m_end_point)
            self.mouse_rotation_last = 0.0
            self.rotation_value_start = self.rotation
        elif self.current_mouse_hit == POS_HANDLE or self.current_mouse_hit == AREA_HIT:
            self.start_shape_x = self.shape_x 
            self.start_shape_y = self.shape_y
            
    def _shape__motion_notify_event(self, delta_x, delta_y, CTRL_DOWN):
        self._update_values_for_mouse_delta(delta_x, delta_y, CTRL_DOWN)

    def _shape_release_event(self, delta_x, delta_y, CTRL_DOWN):
        self._update_values_for_mouse_delta(delta_x, delta_y, CTRL_DOWN)
    
    def _update_values_for_mouse_delta(self, delta_x, delta_y, CTRL_DOWN):
        if self.current_mouse_hit == POS_HANDLE or self.current_mouse_hit == AREA_HIT:
            dx = self.get_screen_x(self.coords.orig_x + delta_x)
            dy = self.get_screen_y(self.coords.orig_y + delta_y)
            self.shape_x = self.start_shape_x + dx
            self.shape_y = self.start_shape_y + dy
            self._update_edit_points()
        elif self.current_mouse_hit == X_SCALE_HANDLE:
            dp = self.get_delta_point(delta_x, delta_y, self.edit_points[X_SCALE_HANDLE])
            pp = self.guide.get_normal_projection_point(dp)
            dist = viewgeom.distance(self.edit_points[POS_HANDLE], pp)
            orig_dist = viewgeom.distance(self.untrans_points[POS_HANDLE], self.untrans_points[X_SCALE_HANDLE])
            self.x_scale = dist / orig_dist
            if CTRL_DOWN:
                self.y_scale = self.x_scale
            self._update_edit_points()
        elif self.current_mouse_hit == Y_SCALE_HANDLE:
            dp = self.get_delta_point(delta_x, delta_y, self.edit_points[Y_SCALE_HANDLE])
            pp = self.guide.get_normal_projection_point(dp)
            dist = viewgeom.distance(self.edit_points[POS_HANDLE], pp)
            orig_dist = viewgeom.distance(self.untrans_points[POS_HANDLE], self.untrans_points[Y_SCALE_HANDLE])
            self.y_scale = dist / orig_dist
            if CTRL_DOWN:
                self.x_scale = self.y_scale
            self._update_edit_points()
        elif self.current_mouse_hit == ROTATION_HANDLE:
            ax, ay = self.edit_points[POS_HANDLE]
            
            m_start_point = (self.get_screen_x(self.mouse_start_x), self.get_screen_y(self.mouse_start_y))
            m_end_point = (self.get_screen_x(self.mouse_start_x + delta_x), self.get_screen_y(self.mouse_start_y + delta_y))
            current_mouse_rotation = self.get_mouse_rotation_angle(self.edit_points[POS_HANDLE], m_start_point, m_end_point)

            self.rotation = self.rotation_value_start + current_mouse_rotation
            self._update_edit_points()

    def get_mouse_rotation_angle(self, anchor, mr_start, mr_end):
        angle = viewgeom.get_angle_in_deg(mr_start, anchor, mr_end)
        clockw = viewgeom.points_clockwise(mr_start, anchor, mr_end)
        if not clockw: 
            angle = -angle

        # Crossed angle for 180 -> 181... range
        crossed_angle = angle + 360.0

        # Crossed angle for -180 -> 181 ...range.
        if angle > 0:
            crossed_angle = -360.0 + angle

        # See if crossed angle closer to last angle.
        if abs(self.mouse_rotation_last - crossed_angle) < abs(self.mouse_rotation_last - angle):
            angle = crossed_angle

        # Set last to get good results next time.
        self.mouse_rotation_last = angle

        return angle
        
    def get_delta_point(self, delta_x, delta_y, ep):
        dx = self.get_screen_x(self.coords.orig_x + delta_x)
        dy = self.get_screen_y(self.coords.orig_y + delta_y)
        sx = self.get_screen_x(self.mouse_start_x)
        sy = self.get_screen_y(self.mouse_start_y)
        return (sx + dx, sy + dy)

    def _update_edit_points(self):
        self.edit_points = copy.deepcopy(self.untrans_points) #reset before transform
        self._translate_edit_points()
        self._scale_edit_points()
        self._rotate_edit_points()
    
    def _translate_edit_points(self):
        ux, uy = self.untrans_points[0]
        dx = self.shape_x - ux
        dy = self.shape_y - uy
        for i in range(0,len(self.edit_points)):
            sx, sy = self.untrans_points[i]
            self.edit_points[i] = (sx + dx, sy + dy)
    
    def _scale_edit_points(self):
        ax, ay = self.edit_points[0]
        sax, say = self.untrans_points[0]
        for i in range(1, 7):
            sx, sy = self.untrans_points[i]
            x = ax + self.x_scale * (sx - sax)
            y = ay + self.y_scale * (sy - say)
            self.edit_points[i] = (x, y)

    def _rotate_edit_points(self):
        ax, ay = self.edit_points[0]
        for i in range(1, 7):
            x, y = viewgeom.rotate_point_around_point(self.rotation, self.edit_points[i], self.edit_points[0])
            self.edit_points[i] = (x, y)

    def _draw_edit_shape(self, cr, allocation):
        x, y = self.get_panel_point(*self.edit_points[3])
        cr.move_to(x, y)
        for i in range(4,7):
            x, y = self.get_panel_point(*self.edit_points[i])
            cr.line_to(x, y)
        cr.close_path()
        cr.stroke()

        self._draw_scale_arrow(cr, self.edit_points[2], 90)
        self._draw_scale_arrow(cr, self.edit_points[1], 0)


        # center cross
        cr.save()
        
        x, y = self.get_panel_point(*self.edit_points[0])
        cr.translate(x,y)
        cr.rotate(math.radians(self.rotation))
        CROSS_LENGTH = 3
        cr.move_to(-0.5, -CROSS_LENGTH-0.5)
        cr.line_to(-0.5, CROSS_LENGTH-0.5)
        cr.set_line_width(1.0)
        cr.stroke()
        cr.move_to(-CROSS_LENGTH - 0.5, -0.5)
        cr.line_to(CROSS_LENGTH - 0.5, -0.5)
        cr.stroke()

        cr.restore()

        # roto handle
        x, y = self.get_panel_point(*self.edit_points[3])
        cr.translate(x,y)
        cr.rotate(math.radians(self.rotation))
        cr.arc(0, 0, 6, math.radians(180), math.radians(-35))
        cr.set_line_width(3.0)
        cr.stroke()
        cr.move_to(-6, 3)
        cr.line_to(-9, 0)
        cr.line_to(-3, 0)
        cr.close_path()
        cr.fill()
        cr.arc(0, 0, 6, math.radians(0), math.radians(145))
        cr.set_line_width(3.0)
        cr.stroke()
        cr.move_to(6, -3)
        cr.line_to(9, 0)
        cr.line_to(3, 0)
        cr.close_path()
        cr.fill()
    
    def _draw_scale_arrow(self, cr, edit_point, add_angle):
        cr.save()
        
        x, y = self.get_panel_point(*edit_point)
        cr.translate(x,y)
        cr.rotate(math.radians(self.rotation + add_angle))
        
        SHAFT_WIDTH = 2
        SHAFT_LENGTH = 6
        HEAD_WIDTH = 6
        HEAD_LENGTH = 6
        cr.move_to(0, - SHAFT_WIDTH)
        cr.line_to(SHAFT_LENGTH, -SHAFT_WIDTH)
        cr.line_to(SHAFT_LENGTH, -HEAD_WIDTH)
        cr.line_to(SHAFT_LENGTH + HEAD_LENGTH, 0)
        cr.line_to(SHAFT_LENGTH, HEAD_WIDTH)
        cr.line_to(SHAFT_LENGTH, SHAFT_WIDTH)
        cr.line_to(-SHAFT_LENGTH, SHAFT_WIDTH)
        cr.line_to(-SHAFT_LENGTH, HEAD_WIDTH)
        cr.line_to(-SHAFT_LENGTH - HEAD_LENGTH, 0)
        cr.line_to(-SHAFT_LENGTH, -HEAD_WIDTH)
        cr.line_to(-SHAFT_LENGTH, -SHAFT_WIDTH)
        cr.close_path()
 
        cr.set_source_rgb(1,1,1)
        cr.fill_preserve()
        cr.set_line_width(2.0)
        cr.set_source_rgb(0,0,0)
        cr.stroke()
        
        cr.restore()
   
