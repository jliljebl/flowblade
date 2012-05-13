

import sys

import vieweditorshape

# Eedit modes
MOVE_MODE = 0
ROTATE_MODE = 1
    
# Mouse edit types
NO_EDIT = 0
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
        self.mouse_rotation_start = None
        self.mouse_rotation_end = None
        self.mouse_rotation_last = None
        self.last_press_hit_point = None
        self.edit_type = None

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
        self.mouse_rotation_start = p
        self.mouse_rotation_end = p
        self.mouse_rotation_last = p
        self.mouse_pressed()

    def handle_mouse_drag(self, p):
        self.mouse_current_point = p
        self.mouse_rotation_end = p
        self.mouse_dragged()

    def handle_mouse_release(self, p):
        self.mouse_current_point = p
        self.mouse_rotation_end = p
        self.mouse_released()

    def translate_points_for_mouse_move(self):
        sx, sy = self.mouse_start_point
        dx, dy = self.get_mouse_delta()
        for p in self.edit_point_shape.edit_points:
            p.x = sx + dx
            p.y = sy + dy
            
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

    def mouse_pressed(self):
        self.edit_point_shape.save_start_pos()
        if self.last_press_hit_point != None:
            self.last_press_hit_point.save_start_pos()
            self.edit_type = HANDLE_EDIT
        else:
            self.edit_type = MOVE_EDIT
        
    def mouse_dragged(self):
        delta = self.get_mouse_delta()
        if self.edit_type == HANDLE_EDIT:
            self.last_press_hit_point.translate_from_move_start(delta)
            edit_points = self.edit_point_shape.edit_points
            if self.last_press_hit_point == edit_points[0]:#top left
                edit_points[1].y = edit_points[0].y
                edit_points[3].x = edit_points[0].x
            else:
                edit_points[1].x = edit_points[2].x
                edit_points[3].y = edit_points[2].y
        else:
            self.edit_point_shape.translate_from_move_start(delta)
        
    def mouse_released(self):
        delta = self.get_mouse_delta()
        if self.edit_type == HANDLE_EDIT:
            self.last_press_hit_point.translate_from_move_start(delta)
            edit_points = self.edit_point_shape.edit_points
            if self.last_press_hit_point == edit_points[0]:#top left
                edit_points[1].y = edit_points[0].y
                edit_points[3].x = edit_points[0].x
            else:
                edit_points[1].x = edit_points[2].x
                edit_points[3].y = edit_points[2].y
        else:
            self.edit_point_shape.translate_from_move_start(delta)

    def draw(self, cr):
        cr.set_source_rgba(0.5,0.5,0.5,1)
        self.edit_point_shape.draw_line_shape(cr, self.view_editor, 2.0)
        cr.set_source_rgba(1,1,1,1)
        self.edit_point_shape.draw_points(cr, self.view_editor)
        
