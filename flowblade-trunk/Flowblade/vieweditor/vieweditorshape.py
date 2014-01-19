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

import math
import viewgeom

# Edit point display types
MOVE_HANDLE = 0
ROTATE_HANDLE = 1
CONTROL_POINT = 2
INVISIBLE_POINT = 3

# handle size
EDIT_POINT_SIDE_HALF = 4

# line types
LINE_NORMAL = 0
LINE_DASH = 1

class EditPoint:
    """
    A point that user can move on the screen to edit image data.
    """
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.rotation = 0.0
        self.is_hittable = True
        self.start_x = x
        self.start_y = y        
        self.display_type = MOVE_HANDLE # default value, can changed for different shapes and edit modes

    def set_pos(self, p):
        self.x, self.y = p

    def get_pos(self):
        return (self.x, self.y)
    
    def get_start_pos(self):
        return (self.start_x, self.start_y)

    def save_start_pos(self):
        self.start_x = self.x
        self.start_y = self.y

    def translate_from_move_start(self, delta):
        dx, dy = delta
        self.x = self.start_x + dx
        self.y = self.start_y + dy

    def translate(self, delta):
        dx, dy = delta
        self.x = self.x + dx
        self.y = self.y + dy

    def hit(self, test_p, view_scale=1.0):
        if not self.is_hittable:
            return False
        
        test_x, test_y = test_p
        side_mult = 1.0 / view_scale        
        if((test_x >= self.x - EDIT_POINT_SIDE_HALF * side_mult) 
            and (test_x <= self.x + EDIT_POINT_SIDE_HALF  * side_mult) 
            and (test_y >= self.y - EDIT_POINT_SIDE_HALF * side_mult)
            and (test_y <= self.y + EDIT_POINT_SIDE_HALF * side_mult)):
            return True;

        return False;

    def draw(self, cr, view_editor):
        if self.display_type == INVISIBLE_POINT:
            return
        else:
            x, y = view_editor.movie_coord_to_panel_coord((self.x, self.y))
            cr.rectangle(x - 4, y - 4, 8, 8)
            cr.fill()

class EditPointShape:
    """
    A shape that user can move, rotate or scale on the screen to edit image data.
    """
    def __init__(self):
        self.edit_points = []
        self.line_width = 2.0
        self.line_type = LINE_DASH

    def save_start_pos(self):
        for ep in self.edit_points:
            ep.save_start_pos()

    def translate_points_to_pos(self, px, py, anchor_point_index):
        anchor = self.edit_points[anchor_point_index]
        dx = px - anchor.x
        dy = py - anchor.y
        for ep in self.edit_points:
            ep.translate((dx, dy))

    def translate_from_move_start(self, delta):
        for ep in self.edit_points:
            ep.translate_from_move_start(delta)
            
    def rotate_from_move_start(self, anchor, angle):
        for ep in self.edit_points:
            rotated_pos = viewgeom.rotate_point_around_point(angle,
                                                            ep.get_start_pos(),
                                                            anchor )
            ep.set_pos(rotated_pos)

    def point_in_area(self, p):
        """
        Default hit test is to see if point is inside convex with points in order 0 - n.
        Override for different hit test.
        """
        points = self.editpoints_as_tuples_list()
        return viewgeom.point_in_convex_polygon(p, points, 0)

    def get_edit_point(self, p, view_scale=1.0):
        for ep in self.edit_points:
            if ep.hit(p, view_scale) == True:
                return ep
        return None

    def editpoints_as_tuples_list(self):
        points = []
        for ep in self.edit_points:
            points.append((ep.x, ep.y))
        return points

    def get_bounding_box(self, p):
        if len(self.edit_points) == 0:
            return None

        x_low = 1000000000
        x_high = -100000000
        y_low = 1000000000
        y_high = -100000000

        for p in self.edit_points:
            px, py = p
            if px < x_low:
                x_low = p.x
            if px > x_high:
                x_high = p.x;
            if py < y_low:
                y_low = p.y;
            if py > y_high:
                y_high = p.y;

        return (x_low, y_low, x_high - x_low, y_high - y_low)

    def draw_points(self, cr, view_editor):
        for ep in self.edit_points:
            ep.draw(cr, view_editor)
    
    def draw_line_shape(self, cr, view_editor):
        self._set_line(cr)
        x, y = view_editor.movie_coord_to_panel_coord((self.edit_points[0].x, self.edit_points[0].y))
        cr.move_to(x, y)
        for i in range(1, len(self.edit_points)):
            ep = self.edit_points[i]
            x, y = view_editor.movie_coord_to_panel_coord((ep.x, ep.y))
            cr.line_to(x, y)
        cr.close_path()
        cr.stroke()
        cr.set_dash([]) # turn dashing off
    
    def _set_line(self, cr):
        if self.line_type == LINE_DASH:
            dashes = [6.0, 6.0, 6.0, 6.0] # ink, skip, ink, skip
            offset = 0
            cr.set_dash(dashes, offset)
        cr.set_line_width(self.line_width)
        
    def get_panel_point(self, point_index, view_editor):
         ep = self.edit_points[point_index]
         return view_editor.movie_coord_to_panel_coord((ep.x, ep.y))

    def get_first_two_points_rotation_angle(self):
        anchor = (self.edit_points[0].x, self.edit_points[0].y)
        p1 = (self.edit_points[0].x + 10, self.edit_points[0].y)
        p2 = (self.edit_points[1].x,  self.edit_points[1].y)
        if self.edit_points[0].y < self.edit_points[1].y:
            return viewgeom.get_angle_in_rad(p1, anchor, p2)
        else:
            return 2 * math.pi - viewgeom.get_angle_in_rad(p1, anchor, p2)

    def set_all_points_invisible(self):
        for ep in self.edit_points:
            ep.display_type = INVISIBLE_POINT

class SimpleRectEditShape(EditPointShape):
    """
    A rect with four corner points.
    """
    def __init__(self):
        EditPointShape.__init__(self)
        self.rect = (0,0,100,100) # we use this to create points, user should set real rect immediately with set_rect()
        self.rotation = 0.0

        x, y, w, h = self.rect
        # edit point 0 determines the position of the shape
        self.edit_points.append(EditPoint(x, y))
        self.edit_points.append(EditPoint(x + w, y))
        self.edit_points.append(EditPoint(x + w, y + h))
        self.edit_points.append(EditPoint(x, y + h))
        self.edit_points[0].display_type = MOVE_HANDLE
        self.edit_points[2].display_type = MOVE_HANDLE
        self.edit_points[1].display_type = MOVE_HANDLE
        self.edit_points[3].display_type = MOVE_HANDLE

    def set_rect(self, rect):
        self.rect = rect
        self.reset_points()

    def update_rect_size(self, w, h):
        # edit point 0 determines the position of the shape
        self.rect = (self.edit_points[0].x, self.edit_points[0].y, w, h) 
        x, y, w, h = self.rect
        self.edit_points[0].x = x
        self.edit_points[0].y = y
        self.edit_points[1].x = x + w
        self.edit_points[1].y = y
        self.edit_points[2].x = x + w
        self.edit_points[2].y = y + h
        self.edit_points[3].x = x
        self.edit_points[3].y = y + h
        
    def reset_points(self):
        x, y, w, h = self.rect
        # edit point 0 determines the position of the shape
        self.edit_points[0].x = x
        self.edit_points[0].y = y
        self.edit_points[1].x = x + w
        self.edit_points[1].y = y
        self.edit_points[2].x = x + w
        self.edit_points[2].y = y + h
        self.edit_points[3].x = x
        self.edit_points[3].y = y + h
    
    def get_mid_point(self):
        diag1 = viewgeom.get_line_for_points((self.edit_points[0].x, self.edit_points[0].y),
                                          (self.edit_points[2].x, self.edit_points[2].y))
        diag2 = viewgeom.get_line_for_points((self.edit_points[1].x, self.edit_points[1].y),
                                            (self.edit_points[3].x, self.edit_points[3].y))
        return diag1.get_intersection_point(diag2)

    def get_handle_guides(self, hit_point):
        index = self.edit_points.index(hit_point)
        opp_handle_index = (index + 2) % 4;
        opp_handle = self.edit_points[opp_handle_index]

        guide_1_handle = self.edit_points[(opp_handle_index - 1) % 4]
        guide_2_handle = self.edit_points[(opp_handle_index + 1) % 4]

        guide_1 = viewgeom.get_vec_for_points(opp_handle.get_pos(), guide_1_handle.get_pos())
        guide_2 = viewgeom.get_vec_for_points(opp_handle.get_pos(), guide_2_handle.get_pos())
        guide_1.point_index = (opp_handle_index - 1) % 4
        guide_2.point_index = (opp_handle_index + 1) % 4

        return (guide_1, guide_2)
        

