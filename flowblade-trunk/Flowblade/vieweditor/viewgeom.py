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

CLOCKWISE = 1
COUNTER_CLOCKWISE = 2


def point_in_convex_polygon(test_point, points, first_point_index):
    # Polygon has to have > 2 points to contain anything.
    if len(points) < 3:
        return False

    # Get first points direction
    direction = get_points_direction(   points[first_point_index],
                                        points[first_point_index + 1],
                                        points[first_point_index + 2])

    # direction with two points and test point must always be same 
    # if point is inside polygon.
    for i in range(0, len(points) - 1):
        if get_points_direction(points[i], points[ i + 1], test_point) != direction:
            return False

    if get_points_direction(points[-1], points[0], test_point) != direction:
        return False

    return True;

def get_points_direction(p1, p2, p3):
    if points_clockwise(p1, p2, p3): 
        return CLOCKWISE
    else:
        return COUNTER_CLOCKWISE

def points_clockwise(p1, p2, p3):
    p1x, p1y = p1
    p2x, p2y = p2
    p3x, p3y = p3
    
    e1x = p1x - p2x
    e1y = p1y - p2y
    e2x = p3x - p2x
    e2y = p3y - p2y

    if ((e1x * e2y) - (e1y * e2x)) >= 0: 
        return True
    else:
        return False

def rotate_point_around_point(rotation_angle, p, anchor):
    px, py = p
    ax, ay = anchor
    offset_point = (px - ax, py - ay)
    rx, ry = rotate_point_around_origo(rotation_angle, offset_point)
    return (rx + ax, ry + ay)

def rotate_point_around_origo(rotation_angle, p):
    px, py = p
    angle_rad = math.radians(rotation_angle)
    sin_val = math.sin(angle_rad)
    cos_val = math.cos(angle_rad)
    new_x = px * cos_val - py * sin_val
    new_y = px * sin_val + py * cos_val
    return (new_x, new_y)

def get_angle_in_deg(p1, corner, p2):
    angle_in_rad = get_angle_in_rad(p1, corner, p2)
    return math.degrees(angle_in_rad)

def get_angle_in_rad(p1, corner, p2):
    side1 = distance(p1, corner)
    side2 = distance(p2, corner)
    if side1==0.0 or side2==0.0:
        # this get fed 0 lengh sides
        return 0.0
    opposite_side = distance(p1, p2)
    angle_cos = ((side1*side1) + (side2*side2) - (opposite_side*opposite_side)) / (2*side1*side2)
    return math.acos(angle_cos)

def distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def get_line_for_points(p1, p2):
    m, b, is_vertical, x_icept = _get_line_params_for_points(p1, p2)
    return Line(m, b, is_vertical, x_icept)

def get_vec_for_points(p1, p2):
    if p1 == p2:
        return None

    m, b, is_vertical, x_icept = _get_line_params_for_points(p1, p2)
    return Vec(m, b, is_vertical, x_icept, p1, p2)
    
def _get_line_params_for_points(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    if (x1 == x2):
        is_vertical = True;
        x_icept = x1;
        m = None
        b = None
    else:
        is_vertical = False
        # slope
        m = (y2-y1) / (x2-x1)
        # get y intercept b
        b = y1 - (m * x1)
        x_icept = None

    return (m, b, is_vertical, x_icept)
    
class Line:
        """
        Mathematical line using function y = mx + b.
        """
        def __init__(self, m, b, is_vertical, x_icept):
            self.m = m
            self.b = b
            self.is_vertical = is_vertical
            self.x_icept = x_icept

        def get_normal_projection_point(self, p):
            # Returns point on this line and that is also on the line 
            # that is perpendicular with this and goes through provided point
            x, y = p

            # vertical
            if (self.is_vertical == True):
                return (self.x_icept, y)

            # horizontal
            if( self.m == 0 ):
                return (x, self.b)

            # has slope
            normal_m = -1.0 / self.m
            normal_b = y - normal_m * x               
            intersect_x = (normal_b - self.b) / (self.m - normal_m)
            intersect_y = intersect_x * self.m + self.b
            return (intersect_x, intersect_y)

        def get_intersection_point(self, i_line):
            # If both are vertical, no inter section
            if i_line.is_vertical and self.is_vertical:
                return None

            # If both have same slope and neither is vertical, no intersection
            if (i_line.m == self.m) and (not i_line.is_vertical) and (not self.is_vertical):
                return None
                
            # One line is vertical
            if self.is_vertical: 
                return get_isp_for_vert_and_non_vert(self, i_line)
            if i_line.is_vertical:
                return get_isp_for_vert_and_non_vert(i_line, self)

            # Both lines are non-vertical
            intersect_x = (i_line.b - self.b) / (self.m - i_line.m)
            intersect_y = intersect_x * self.m + self.b
            return (intersect_x, intersect_y)

class Vec(Line):
    """
    A mathematical vector.
    """
    def __init__(self,  m, b, is_vertical, x_icept, start_point, end_point):
        Line.__init__(self,  m, b, is_vertical, x_icept)
        # start point and end point being on line is quaranteed by builder function so 
        # don't use this constructor directly or set start or end points directly
        # only use Vec.set_end_point_to_normal_projection() to set end point.
        self.start_point = start_point
        self.end_point = end_point
        self.direction = self.get_direction()
        self.orig_direction = self.direction
    
    def set_end_point_to_normal_projection(self, p):
        self.end_point = self.get_normal_projection_point(p)
    
    def get_direction(self):
        """
        Return 1 or -1 for direction and 0 if length is zero and direction undetermined)
        """
        sx, sy = self.start_point
        ex, ey = self.end_point

        if self.is_vertical:
            return (sy - ey) / abs(sy - ey)
        else:
            return (sx - ex ) / abs(sx - ex)

    def get_length(self):
        # Returns length as positive if direction same as original and as negative if reversed
        # and as zero is length is 0
        if self.is_zero_length():
            return 0;

        current_direction = self.get_direction() / self.orig_direction
        d = distance( self.start_point, self.end_point );
        return current_direction * d

    def get_multiplied_vec(self, multiplier):
        start_x, start_y = self.start_point
        end_x, end_y = self.end_point

        if (end_x - start_x) == 0:
            x_dist = 0
        else:
            x_dist = abs(end_x - start_x) * abs( end_x - start_x ) / (end_x - start_x)
        
        if (end_y - start_y ) == 0:
             y_dist = 0
        else:
            y_dist = abs(end_y - start_y) * abs(end_y - start_y) / (end_y - start_y)

        xm_dist = x_dist * multiplier
        ym_dist = y_dist * multiplier
        new_end_x = start_x + xm_dist
        new_end_y = start_y + ym_dist

        return get_vec_for_points(self.start_point, (new_end_x, new_end_y))

    def is_zero_length(self):
        if self.start_point == self.end_point:
            return True
        else:
            return False
    
    def set_zero_length(self):
        self.end_point = self.start_point

def get_isp_for_vert_and_non_vert(vertical, non_vertical):
    is_y = non_vertical.m * vertical.x_icept + non_vertical.b
    return (vertical.x_icept, is_y)
