

import sys

import vieweditorshape
import viewgeom

# Edit modes
MOVE_MODE = 0
ROTATE_MODE = 1
    
# Edit types
NO_EDIT = 0 # mouse hit meaningless
ROTATE_EDIT = 1
MOVE_EDIT = 2
HANDLE_EDIT = 4

class AbstactEditorLayer:

    def __init__(self, view_editor):
        self.view_editor = view_editor
        self.edit_point_shape = None
        self.name = "unnamed layer"
        self.active = False
        self.last_pressed_edit_point = None
        self.mouse_start_point = None
        self.mouse_current_point = None
        self.mouse_rotation_last = None
        self.last_press_hit_point = None
        self.edit_mode = None # determines how mouse press is interpreted
        self.edit_type = None # is interpretation of purpose of mouse press, 
                               # not always used if mouse press in edit_mode can only interpreted in one way

    # --------------------------------------------- state changes
    def frame_changed(self):
        pass # override to react to frame change

    def mode_changed(self):
        pass # override to react to mode change

    # --------------------------------------------- hit detection
    def hit(self, p):
        """
        Test hit AND save hit point or clear hit point if only area hit.
        """
        self.last_press_hit_point = self.edit_point_shape.get_edit_point(p)
        if self.last_press_hit_point != None:
            return True
        if self.edit_point_shape.point_in_area(p) == True:
            self.last_press_hit_point = None
            return True
        
        return False

    # ---------------------------------------------- mouse events
    # All mouse coords in movie space, ViewEditor onle deals with panel space
    def handle_mouse_press(self, p):
        self.mouse_start_point = p
        self.mouse_current_point = p
        self.mouse_rotation_last = 0.0
        self.mouse_pressed()

    def handle_mouse_drag(self, p):
        self.mouse_current_point = p
        self.mouse_dragged()

    def handle_mouse_release(self, p):
        self.mouse_current_point = p
        self.mouse_released()

    def translate_points_for_mouse_move(self):
        sx, sy = self.mouse_start_point
        dx, dy = self.get_mouse_delta()
        for p in self.edit_point_shape.edit_points:
            p.x = sx + dx
            p.y = sy + dy

    def get_current_mouse_rotation(self, anchor):
        return self.get_mouse_rotation_angle(anchor, self.mouse_start_point, self.mouse_current_point)

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

    
    def mouse_pressed(self):
        print "AbstactEditorLayer.mouse_pressed not overridden in" + self.__class__
        sys.exit(1)
        
    def mouse_dragged(self):
        print "AbstactEditorLayer.mouse_dragged not overridden in" + self.__class__
        sys.exit(1)
        
    def mouse_released(self):
        print "AbstactEditorLayer.mouse_released not overridden in" + self.__class__
        sys.exit(1)

    def get_mouse_delta(self):
        cx, cy = self.mouse_current_point
        sx, sy = self.mouse_start_point
        return (cx - sx, cy - sy)

    # -------------------------------------------- draw
    def draw(self, cr):
        print "AbstactEditorLayer.draw not overridden in" + self.__class__
        sys.exit(1)

class SimpleRectEditLayer(AbstactEditorLayer):
    
    def __init__(self, view_editor):
        AbstactEditorLayer.__init__(self, view_editor)
        self.edit_point_shape = vieweditorshape.SimpleRectEditShape()
        self.edit_mode = ROTATE_MODE

    def mouse_pressed(self):
        self.edit_point_shape.save_start_pos()
        if self.edit_mode == MOVE_MODE:
            if self.last_press_hit_point != None:
                self.last_press_hit_point.save_start_pos()
                self.edit_type = HANDLE_EDIT
                self.guide_1, self.guide_2 = self.edit_point_shape.get_handle_guides(self.last_press_hit_point)
            else:
                self.edit_type = MOVE_EDIT
        else: # ROTATE_MODE
            self.roto_mid = self.edit_point_shape.get_mid_point()
        
    def mouse_dragged(self):
        delta = self.get_mouse_delta()
        if self.edit_mode == MOVE_MODE:
            if self.edit_type == HANDLE_EDIT:
                self._update_corner_edit(delta)
            else:
                self.edit_point_shape.translate_from_move_start(delta)
        else: # ROTATE_MODE
            angle_change = self.get_current_mouse_rotation(self.roto_mid)
            self.edit_point_shape.rotate_from_move_start(self.roto_mid, angle_change)

    def mouse_released(self):
        delta = self.get_mouse_delta()
        if self.edit_mode == MOVE_MODE:
            if self.edit_type == HANDLE_EDIT:
                self._update_corner_edit(delta)
            else:
                self.edit_point_shape.translate_from_move_start(delta)
        else: # ROTATE_MODE
            angle_change = self.get_current_mouse_rotation(self.roto_mid)
            self.edit_point_shape.rotate_from_move_start(self.roto_mid, angle_change)
            self.mouse_rotation_last = 0.0

    def _update_corner_edit(self, delta):
        self.last_press_hit_point.translate_from_move_start(delta)

        self.guide_1.set_end_point_to_normal_projection(self.last_press_hit_point.get_pos())
        self.guide_2.set_end_point_to_normal_projection(self.last_press_hit_point.get_pos())

        if self.guide_1.get_length() < 0:
            self.guide_1.set_zero_length()
        if self.guide_2.get_length() < 0:
            self.guide_2.set_zero_length()

        self.edit_point_shape.edit_points[self.guide_1.point_index].set_pos(self.guide_1.end_point)
        self.edit_point_shape.edit_points[self.guide_2.point_index].set_pos(self.guide_2.end_point)

    def draw(self, cr):
        cr.set_source_rgba(0.5,0.5,0.5,1)
        self.edit_point_shape.draw_line_shape(cr, self.view_editor, 2.0)
        cr.set_source_rgba(1,1,1,1)
        self.edit_point_shape.draw_points(cr, self.view_editor)
        
