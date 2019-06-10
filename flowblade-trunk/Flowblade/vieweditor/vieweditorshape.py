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
ROTO_CURVE_POINT = 4
ROTO_HANDLE_POINT = 5

# handle size
EDIT_POINT_SIDE_HALF = 4

# line types
LINE_NORMAL = 0
LINE_DASH = 1

# colors
ROTO_CURVE_COLOR = (0.97, 0.97, 0.30, 1)
HANDLE_LINES_COLOR = (0.82, 0.16, 0.16, 1)
ROTO_CURVE_POINT_COLOR = (0.9, 0.9, 0.9, 1)
ROTO_HANDLE_POINT_COLOR = (0.82, 0.16, 0.16, 1)
# Roto mask types
CURVE_MASK = 0
LINE_MASK = 1

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



class RotoMaskEditPoint(EditPoint):
    def __init__(self, point_type, x=0, y=0):
        EditPoint.__init__(self, x, y)
        self.display_type = point_type
        self.selected = None
        self.mask_type = CURVE_MASK

    def hit(self, test_p, view_scale=1.0):
        if self.mask_type == LINE_MASK and self.display_type == ROTO_HANDLE_POINT:
            return False # With LINE_MASK handles are not user draggable.
            
        test_x, test_y = test_p
      
        if((test_x >= self.x - EDIT_POINT_SIDE_HALF) 
            and (test_x <= self.x + EDIT_POINT_SIDE_HALF) 
            and (test_y >= self.y - EDIT_POINT_SIDE_HALF)
            and (test_y <= self.y + EDIT_POINT_SIDE_HALF)):
            return True

        return False
        
    def draw(self, cr, view_editor):
        if self.mask_type == LINE_MASK and self.display_type == ROTO_HANDLE_POINT:
            return 

        if self.display_type == ROTO_CURVE_POINT:
            cr.set_source_rgba(*ROTO_CURVE_COLOR)
        else:
            cr.set_source_rgba(*ROTO_HANDLE_POINT_COLOR)
            
        x, y = self.x, self.y
        cr.rectangle(x - 4, y - 4, 8, 8)
        if self.display_type == ROTO_CURVE_POINT:
            cr.stroke()
        else:
            cr.fill()

        if self.selected:
            cr.set_source_rgba(0,0,0,1)
            cr.rectangle(x - 4, y - 4, 8, 8)
            cr.stroke()


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
        


class RotoMaskEditShape(EditPointShape):
    """
    A Bezier spline creating a closed area.
    """
    def __init__(self, view_editor, clip_editor):
        EditPointShape.__init__(self)
        
        self.mask_type = CURVE_MASK
                
        self.curve_points = [] # panel coords, not movie coods or normalized movie coords
        self.handles1 =  [] # panel coords, not movie coods or normalized movie coords
        self.handles2 =  [] # panel coords, not movie coods or normalized movie coords
        
        self.handles_for_curve_point = {}

        self.selected_point_array = None
        self.selected_point_index = -1
            
        self.clip_editor = clip_editor # This is keyframeeditor.ClipKeyFrameEditor
        self.view_editor = view_editor # This is viewEditor.ViewEditor

        keyframe, bz_points = clip_editor.keyframes[0]
        if len(bz_points) > 2:
            self.closed = True
        else:
            self.closed = False
        
        self.block_shape_updates = False # We're getting a difficult to kill "size-allocate"., "window-resized" events and have to manage manually when updates to shape are allowed.
                                        # and this is used to block it from recreating edit shape in middle of mouse edit, bit hacky but works fine.

        self.update_shape()

    def add_point(self, index, p):
        if index == -1:
            return
    
        x, y = p
        add_cp = RotoMaskEditPoint(ROTO_CURVE_POINT, x, y)
        self.curve_points.insert(index, add_cp)
        if len(self.curve_points) > 1:
            hp1, hp2 = self.get_straight_line_handle_places(index)
        else:
            hp1 = (x, y + 30)
            hp2 = (x + 30, y)
    
        add_hp1 = RotoMaskEditPoint(ROTO_CURVE_POINT, *hp1)
        add_hp2 = RotoMaskEditPoint(ROTO_CURVE_POINT, *hp2)
        self.handles1.insert(index, add_hp1)
        self.handles2.insert(index, add_hp2)
            
        hch = [ self.view_editor.panel_coord_to_normalized_movie_coord(hp1), 
                self.view_editor.panel_coord_to_normalized_movie_coord(p), 
                self.view_editor.panel_coord_to_normalized_movie_coord(hp2)]

        for kf_tuple in self.clip_editor.keyframes:
            keyframe, bz_points = kf_tuple
            bz_points.insert(index, hch) 

    def delete_selected_point(self):
        if self.selected_point_index == -1:
            return

        for kf_tuple in self.clip_editor.keyframes:
            keyframe, bz_points = kf_tuple
            bz_points.pop(self.selected_point_index) 
        
        self.selected_point_array = None
        self.selected_point_index = -1
    
        if len(bz_points) < 3:
            self.closed = False # 2 points can't create a closed polygon/curve

        self.update_shape()

    def update_shape(self):
        if self.block_shape_updates == True:
            return


        # We're not using timeline frame for shape, we're using clip frame.
        frame = self.clip_editor.current_clip_frame

        self.edit_points = [] # all points

        del self.curve_points[:] # we want to array obj to be the same for maintaining point selections after this method has been called
        del self.handles1[:]
        del self.handles2[:]

        self.handles_for_curve_point = {}
        
        bezier_points = self.get_bezier_points_for_frame(frame)
        
        for p in bezier_points:
            # curve point 
            x, y = p[1]
            cp = RotoMaskEditPoint(ROTO_CURVE_POINT, *self.view_editor.normalized_movie_coord_to_panel_coord((x, y)))
            self.curve_points.append(cp)
            self.edit_points.append(cp)

            # handle 1
            x, y = p[0]
            hp1 = RotoMaskEditPoint(ROTO_HANDLE_POINT, *self.view_editor.normalized_movie_coord_to_panel_coord((x, y)))
            self.handles1.append(hp1)
            self.edit_points.append(hp1)
            
            # handle 2
            x, y = p[2]
            hp2 = RotoMaskEditPoint(ROTO_HANDLE_POINT, *self.view_editor.normalized_movie_coord_to_panel_coord((x, y)))
            self.handles2.append(hp2)
            self.edit_points.append(hp2)
            
            self.handles_for_curve_point[cp] = (hp1, hp2)

        # Keep point selection alive
        if self.selected_point_array != None:
            self.selected_point_array[self.selected_point_index].selected = True 

        self.maybe_force_line_mask()
        self.set_points_mask_type_data()

    """
    OLD ALGO FOR GETTING SEQ TO PLACE POINT IN BETWEEN
    KEEP AROUND FOR COMPARISON
    def get_point_insert_seq(self, p):
        # Return index of first curve point in the curve seqment that is closest to given point.
        seq_index = -1
        closest_dist = 10000000000.0
        for i in range(0, len(self.curve_points)):
            dist = self.get_point_dist_from_seq(p, i)
            if dist >= 0 and dist < closest_dist:
                closest_dist = dist
                seq_index = i
        
        return seq_index

    def get_point_dist_from_seq(self, p, seq_index):
        start = self.curve_points[seq_index].get_pos()

        if seq_index < len(self.curve_points) - 1:
            end = self.curve_points[seq_index + 1].get_pos()
        else:
            end = self.curve_points[0].get_pos()
        
        seq = viewgeom.get_vec_for_points(start, end)

        if seq.point_is_between(p) == True:
            dist = seq.get_distance_vec(p)
            return abs(dist.get_length())
        else:
            return -1
    """

    def get_point_insert_side(self, p):
        # We need possibility to have a closed polygon for this to be meaningful
        if len(self.curve_points) < 3:
            return -1
        
        # "between" meas in area defined by normal lines going through seg
        between_sides = self.get_between_sides_in_distance_order(p)
        sides_in_distance_order = self.get_sides_in_end_point_distance_order(p)
        
        i0, d0 = sides_in_distance_order[0]
        i1, d1 = sides_in_distance_order[1]
        i2, d2 = sides_in_distance_order[2]
        
        # If point not between any seq, return closest seq
        if len(between_sides) == 0:
            return i0
        
        # If closest between seq among two closest seqs return that
        ci, cd = between_sides[0]
        if ci == i0:
            return ci
        if ci == i1:
            return ci

        # Return closest, between seq is on opposite side
        # NOTE: This algorithm DOES NOT behave perfectly on all shapes of maskes.
        return i0
        
    def get_side_for_index(self, side_index):
        start = self.curve_points[side_index].get_pos()

        if side_index < len(self.curve_points) - 1:
            end = self.curve_points[side_index + 1].get_pos()
        else:
            end = self.curve_points[0].get_pos()
        
        return viewgeom.get_vec_for_points(start, end)
        
    def get_between_sides_in_distance_order(self, p):
        between_sides = []
        for i in range(0, len(self.curve_points)):
            side = self.get_side_for_index(i)
            if side.point_is_between(p) == True:
                dist = side.get_normal_projection_distance_vec(p)
                between_sides.append((i, dist.get_length()))
        return sorted(between_sides, key = lambda x: float(x[1]))

    def get_sides_in_end_point_distance_order(self, p):
        sides = []
        for i in range(0, len(self.curve_points)):
            side = self.get_side_for_index(i)
            d = side.get_minimum_end_point_distance(p)
            sides.append((i, d))

        return sorted(sides, key = lambda x: float(x[1]))

    def set_mask_type(self, mask_type):
        self.mask_type = mask_type
        self.maybe_force_line_mask()
        self.set_points_mask_type_data()

    def set_points_mask_type_data(self):
        for ep in self.edit_points:
            ep.mask_type = self.mask_type 

    def maybe_force_line_mask(self, force=False):
        if self.mask_type == LINE_MASK or force: 
            # Makes all lines between curve points straight
            for i in range(0, len(self.curve_points)):
                hp1, hp2 = self.get_straight_line_handle_places(i)
                self.handles1[i].set_pos(hp1)
                self.handles2[i].set_pos(hp2)
            
    def get_straight_line_handle_places(self, cp_index):
        prev_i = cp_index - 1
        next_i = cp_index + 1
        if next_i == len(self.curve_points):
            next_i = 0
        if prev_i < 0:
            prev_i = len(self.curve_points) - 1
        
        prev_p = self.curve_points[prev_i].get_pos()
        next_p = self.curve_points[next_i].get_pos()
        p = self.curve_points[cp_index].get_pos()
        
        forward = viewgeom.get_vec_for_points(p, next_p)
        back =  viewgeom.get_vec_for_points(p, prev_p)
        
        forward = forward.get_multiplied_vec(0.3)
        back = back.get_multiplied_vec(0.3)
        
        return (back.end_point, forward.end_point)

    def save_selected_point_data(self, selected_point):
        # These points get re-created all the time and we need to save data on which point was selectes
        if selected_point in self.curve_points:
            self.selected_point_array = self.curve_points
            self.selected_point_index = self.curve_points.index(selected_point)
        elif selected_point in self.handles1:
            self.selected_point_array = self.handles1
            self.selected_point_index = self.handles1.index(selected_point)
        elif selected_point in self.handles2:
            self.selected_point_array = self.handles2
            self.selected_point_index = self.handles2.index(selected_point)
        else:
            self.selected_point_array = None
            self.selected_point_index = -1

    def set_curve_point_as_selected(self, index):
        self.clear_selection()
        self.curve_points[index].selected = True
        self.selected_point_array = self.curve_points
        self.selected_point_index = index
            
    def clear_selection(self):
        for p in self.edit_points:
            p.selected = False

            self.selected_point_array = None
            self.selected_point_index = -1

    def get_selected_point(self):
        if self.selected_point_array != None:
            return self.selected_point_array[self.selected_point_index]
        else:
            return None
            
    def get_bezier_points_for_frame(self, current_frame):

        # We're replicating stuff from MLT file filter_rotoscoping.c to make sure out GUI matches the results there.
        keyframes = self.clip_editor.keyframes
        
        # If single keyframe, just return values of that 
        if len(keyframes) < 2:
            keyframe, bz_points = keyframes[0]
            return bz_points

        # if current_frame after last keyframe, use last kayframe for values, no continued interpolation
        last_keyframe = 0
        for kf_tuple in self.clip_editor.keyframes:
            keyframe, bz_points = kf_tuple
            if keyframe > last_keyframe:
                last_keyframe = keyframe
        
        # More of the last keyframe value fix, code below this block isn't getting the value for last kf and frames after that right
        l_keyframe, l_bz_points = self.clip_editor.keyframes[-1]       
        if current_frame >= last_keyframe:
            return l_bz_points
        
        # Get keyframe range containing current_frame
        for i in range(0, len(keyframes) - 1):
            keyframe, bz_points = keyframes[i]
            keyframe_next, bz_points2 = keyframes[i + 1] # were quaranteed to have at least 2 keyframes when getting here
            if current_frame >= keyframe and current_frame < keyframe_next:
                break
        
        frame_1 = float(keyframe)
        frame_2 = float(keyframe_next)
        current_frame = float(current_frame)
        
        # time in range 0 - 1 between frame_1, frame_2 range like in filter_rotoscoping.c
        t = ( current_frame - frame_1 ) / ( frame_2 - frame_1 + 1 )

        # Get point values  for current frame
        current_frame_bezier_points = [] # array of [handle_point1, curve_point, handle_point2] arrays
        for i in range(0, len(bz_points)):
            hch_array = []
            for j in range(0, 3):
                pa = bz_points[i][j]
                pb = bz_points2[i][j]
                value_point = self.lerp(pa, pb, t)
                hch_array.append(value_point)
            current_frame_bezier_points.append(hch_array)
            
        return current_frame_bezier_points

    def lerp(self, pa, pb, t):
        pax, pay = pa
        pbx, pby = pb
        x = pax + ( pbx - pax ) * t;
        y = pay + ( pby - pay ) * t;
        return (x, y)
    
    def draw_line_shape(self, cr, view_editor):
        if self.closed == True:
            if len(self.curve_points) > 1:
                cr.set_source_rgba(*ROTO_CURVE_COLOR)
                cr.move_to(self.curve_points[0].x, self.curve_points[0].y)
                for i in range(0, len(self.curve_points)):
                    next_point_index = i + 1
                    if next_point_index == len(self.curve_points):
                        next_point_index = 0
                    cr.curve_to(    self.handles2[i].x,
                                    self.handles2[i].y,
                                    self.handles1[next_point_index].x,
                                    self.handles1[next_point_index].y,
                                    self.curve_points[next_point_index].x,
                                    self.curve_points[next_point_index].y)
                cr.close_path()
                cr.stroke()
            
            if self.mask_type == LINE_MASK:
                return

            cr.set_source_rgba(*HANDLE_LINES_COLOR)
            for i in range(0, len(self.curve_points)):
                cr.move_to(self.handles1[i].x, self.handles1[i].y)
                cr.line_to(self.curve_points[i].x, self.curve_points[i].y)
                cr.line_to(self.handles2[i].x, self.handles2[i].y)

                cr.stroke()
        else:
            if len(self.curve_points) > 1:
                cr.set_source_rgba(*ROTO_CURVE_COLOR)
                cr.move_to(self.curve_points[0].x, self.curve_points[0].y)
                for i in range(0, len(self.curve_points)):
                    cr.line_to(self.curve_points[i].x, self.curve_points[i].y)
                
                cr.stroke()
    
    def draw_curve_points(self, cr, view_editor):
        for ep in self.curve_points:
            ep.draw(cr, view_editor)

    # ------------------------------------------------------------- saving edits
    def convert_shape_coords_and_update_clip_editor_keyframes(self):
        clip_editor_keyframes = []
        frame_shape = self._get_converted_frame_shape()
        self.clip_editor.set_active_kf_value(frame_shape)
     
    def _get_converted_frame_shape(self):
        frame_shape_array = []
        for i in range(0, len(self.curve_points)):
            hph_array = []
            cp = self.curve_points[i]
            hp1 = self.handles1[i]
            hp2 = self.handles2[i]
            # order is [handle1, curve_point, handle2]
            hph_array.append(self.get_point_as_normalized_array(hp1))
            hph_array.append(self.get_point_as_normalized_array(cp))
            hph_array.append(self.get_point_as_normalized_array(hp2))
            
            frame_shape_array.append(hph_array)
        
        return frame_shape_array

    def get_point_as_normalized_array(self, edit_point):
        np  = self.view_editor.panel_coord_to_normalized_movie_coord((edit_point.x, edit_point.y))
        nx, ny = np
        return [nx, ny]

        
        
        
