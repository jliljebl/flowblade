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
import sys

import vieweditorshape
import viewgeom

# Edit modes
MOVE_MODE = 0
ROTATE_MODE = 1

ROTO_POINT_MODE = 0
ROTO_MOVE_MODE = 1

ROTO_NO_EDIT = 0
ROTO_POINT_MOVE_EDIT = 1

    
# Edit types, used as kind of subtypes of modes if needed, e.g. MOVE_MODE can have MOVE_EDIT or HANDLE_EDIT 
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
        self.visible = True
        self.last_pressed_edit_point = None
        self.mouse_start_point = None
        self.mouse_current_point = None
        self.mouse_rotation_last = None
        self.last_press_hit_point = None
        self.edit_mode = None # determines how mouse press is interpreted
        self.edit_type = None # is interpretation of purpose of mouse press, 
                               # not always used if mouse press in edit_mode can only interpreted in one way
        self.mouse_released_listener = None
    
    # --------------------------------------------- state changes
    def frame_changed(self, frame):
        pass # override to react to frame change

    def mode_changed(self):
        pass # override to react to mode change

    # --------------------------------------------- hit detection
    def hit(self, p):
        """
        Test hit AND save hit point or clear hit point if only area hit.
        TODO: This isn't really "abstract" in anyway, move up inheritance chain.
        """
        self.last_press_hit_point = self.edit_point_shape.get_edit_point(p)
        if self.last_press_hit_point != None:
            return True
        if self.edit_point_shape.point_in_area(p) == True:
            self.last_press_hit_point = None
            return True
        
        return False

    # ---------------------------------------------- mouse events
    # All mouse coords in movie space, ViewEditor deals with panel space
    def handle_mouse_press(self, p):
        self.mouse_start_point = p
        self.mouse_current_point = p
        self.mouse_rotation_last = 0.0
        self.mouse_pressed()

    def convert_saved_points_to_panel_points(self):
        # RotoMaskEditLayer wants to handle everything in panel coords
        self.mouse_start_point = self.view_editor.movie_coord_to_panel_coord(self.mouse_start_point)
        self.mouse_current_point = self.view_editor.movie_coord_to_panel_coord(self.mouse_current_point)

    def handle_mouse_drag(self, p):
        self.mouse_current_point = p
        self.mouse_dragged()

    def handle_mouse_release(self, p):
        self.mouse_current_point = p
        self.mouse_released()
        if self.mouse_released_listener != None:
            self.mouse_released_listener()

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
    def draw(self, cr, write_out_layers, draw_overlays):
        print "AbstactEditorLayer.draw not overridden in" + self.__class__
        sys.exit(1)



class SimpleRectEditLayer(AbstactEditorLayer):
    
    def __init__(self, view_editor):
        AbstactEditorLayer.__init__(self, view_editor)
        self.edit_point_shape = vieweditorshape.SimpleRectEditShape()
        self.update_rect = False # flag to reinit rect shape
        self.edit_mode = MOVE_MODE
        self.edit_point_shape.set_all_points_invisible()
        self.resizing_allowed = True
        self.ACTIVE_COLOR = (0.55,0.55,0.55,1)
        self.NOT_ACTIVE_COLOR = (0.2,0.2,0.2,1)

    def set_rect_pos(self, x, y):
        # were always assuming that point 0 determines positiojn of shape
        self.edit_point_shape.translate_points_to_pos(x, y, 0)

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
        if self.resizing_allowed == False:
            return
        
        self.last_press_hit_point.translate_from_move_start(delta)

        self.guide_1.set_end_point_to_normal_projection(self.last_press_hit_point.get_pos())
        self.guide_2.set_end_point_to_normal_projection(self.last_press_hit_point.get_pos())

        if self.guide_1.get_length() < 0:
            self.guide_1.set_zero_length()
        if self.guide_2.get_length() < 0:
            self.guide_2.set_zero_length()

        self.edit_point_shape.edit_points[self.guide_1.point_index].set_pos(self.guide_1.end_point)
        self.edit_point_shape.edit_points[self.guide_2.point_index].set_pos(self.guide_2.end_point)

    def draw(self, cr, write_out_layers, draw_overlays):
        if write_out_layers:
            return # this layer is not drawn when writing out layers

        if draw_overlays:
            if self.active:
                cr.set_source_rgba(*self.ACTIVE_COLOR)
            else:
                cr.set_source_rgba(*self.NOT_ACTIVE_COLOR)
            self.edit_point_shape.draw_line_shape(cr, self.view_editor)
            self.edit_point_shape.draw_points(cr, self.view_editor)



class TextEditLayer(SimpleRectEditLayer):
    def __init__(self, view_editor, text_layout):
        # text_layout is titler.PangoLayout
        SimpleRectEditLayer.__init__(self, view_editor)
        self.text_layout = text_layout
        self.edit_mode = MOVE_MODE
        self.edit_point_shape.line_type = vieweditorshape.LINE_DASH
        self.resizing_allowed = False

    def draw(self, cr, write_out_layers, draw_overlays):
        x, y = self.edit_point_shape.get_panel_point(0, self.view_editor)
        rotation = self.edit_point_shape.get_first_two_points_rotation_angle()
        xscale = self.view_editor.scale #* self.view_editor.aspect_ratio
        yscale = self.view_editor.scale
        # x for write out image is on different place because computer screen has box pixels, 
        # some video formats do not
        # were not getting pixel perfect results here but its mostly ok
        if write_out_layers == True:
            x = x / self.view_editor.aspect_ratio
            
        self.text_layout.draw_layout(cr, x, y, rotation, xscale, yscale)

        if self.update_rect:
            # Text size in layout has changed for added text or attribute change.
            # rect size needs to be updated for new size of layout
            # Size of layout is always updated in self.text_layout.draw_layout(....)
            w, h = self.text_layout.pixel_size
            self.edit_point_shape.update_rect_size(w, h)
            self.update_rect = False
        SimpleRectEditLayer.draw(self, cr, write_out_layers, draw_overlays)



class RotoMaskEditLayer(AbstactEditorLayer):
    
    def __init__(self, view_editor, clip_editor, editable_property, rotomask_editor):
        AbstactEditorLayer.__init__(self, view_editor)
        self.view_editor = view_editor
        
        self.editable_property = editable_property
        self.clip_editor = clip_editor
        self.rotomask_editor = rotomask_editor

        self.allow_adding_points = False

        self.edit_point_shape = vieweditorshape.RotoMaskEditShape(view_editor, clip_editor)
        self.edit_point_shape.update_shape()

        #self.block_shape_update = False 
        
        self.ACTIVE_COLOR = (0.0,1.0,0.55,1)
        self.NOT_ACTIVE_COLOR = (0.2,0.2,0.2,1)

        self.edit_mode = ROTO_POINT_MODE

    # ----------------------------------------------------- mouse events
    def hit(self, p):
        self.last_pressed_edit_point = None
        self.mouse_press_panel_point = self.view_editor.movie_coord_to_panel_coord(p) #V This needed when adding new curve points

        if self.edit_mode == ROTO_POINT_MODE:
            # Hit test comes as movie coord point, but rotomask stuff is running on pamel points, need to convert
            ep = self.edit_point_shape.get_edit_point(self.view_editor.movie_coord_to_panel_coord(p))
            self.last_pressed_edit_point = ep
            # We want to get "mouse_pressed()" below always called from vieweditor so we always return True for hit.
            # self.last_pressed_edit_point is now None if we didn't hit anything and we use info to determine what ediy to do.
            return True

        elif self.edit_mode == ROTO_MOVE_MODE:
            # This mode has whole edit area active.
            return True
        
        #there are no other modes
        
    def mouse_pressed(self):
        self.view_editor.edit_area_update_blocked = True
        self.edit_point_shape.block_shape_updates = True
        self.edit_point_shape.save_start_pos()

        # Rotomask always adds keyframe on current frame if any changes are done.
        # Maybe make user settable?
        if self.clip_editor.get_active_kf_frame() != self.clip_editor.current_clip_frame:
            self.edit_point_shape.save_selected_point_data(self.last_pressed_edit_point)
            self.clip_editor.add_keyframe(self.clip_editor.current_clip_frame)
            self.edit_point_shape.convert_shape_coords_and_update_clip_editor_keyframes()
            self.editable_property.write_out_keyframes(self.clip_editor.keyframes)

        if self.edit_mode == ROTO_MOVE_MODE:
            pass
        elif self.edit_mode == ROTO_POINT_MODE:
            if self.last_pressed_edit_point != None:
                if self.edit_point_shape.closed == False:
                    if (self.edit_point_shape.curve_points.index(self.last_pressed_edit_point) == 0 and
                        len(self.edit_point_shape.curve_points) > 2):
                        self.edit_point_shape.closed = True
                        self.edit_point_shape.maybe_force_line_mask(True) # We start with line mask curve points
                    else:
                        # Point pressed, we are moving it
                        self.edit_point_shape.clear_selection()
                        self.last_pressed_edit_point.selected = True
                        self.edit_point_shape.save_selected_point_data(self.last_pressed_edit_point)
                else:
                    # Point pressed, we are moving it
                    self.edit_point_shape.clear_selection()
                    self.last_pressed_edit_point.selected = True
                    self.edit_point_shape.save_selected_point_data(self.last_pressed_edit_point)

            # No point hit attempt to add a point.
            else:
                if self.edit_point_shape.closed == True:
                    if self.allow_adding_points == False:
                        return
                    
                    # Closed curve, try add point in between existing points
                    self.edit_point_shape.block_shape_updates = False
                    self.edit_point_shape.clear_selection()
                    if len(self.edit_point_shape.curve_points) > 1:
                        side_index = self.edit_point_shape.get_point_insert_side(self.mouse_press_panel_point)
                        if side_index != -1:
                            insert_index = side_index + 1
                            if insert_index == len(self.edit_point_shape.curve_points):
                                insert_index = 0
                    elif len(self.edit_point_shape.curve_points) == 1:
                        insert_index = 1
                    else:
                        insert_index = 0

                    self.add_edit_point(insert_index, self.mouse_press_panel_point)
                    self.edit_point_shape.set_curve_point_as_selected(insert_index)
                else:
                    # Open curve, add point last
                    self.edit_point_shape.block_shape_updates = False

                    if len(self.edit_point_shape.curve_points) > 1:
                        self.add_edit_point(len(self.edit_point_shape.curve_points), self.mouse_press_panel_point, False)
                        self.edit_point_shape.maybe_force_line_mask(True)
                        self.edit_point_shape.convert_shape_coords_and_update_clip_editor_keyframes()
                        self.editable_property.write_out_keyframes(self.clip_editor.keyframes)
                        self.rotomask_editor.show_current_frame()
                    else:
                        self.add_edit_point(len(self.edit_point_shape.curve_points), self.mouse_press_panel_point)

        self.clip_editor.widget.queue_draw()
            
    def mouse_dragged(self):
        self.edit_point_shape.block_shape_updates = False
        
        # delta is given in movie coords, RotoMaskEditShape uses panel coords (because it needs to do complex drawing in those) so we have to convert mouse delta.
        mdx, mdy = self.view_editor.movie_coord_to_panel_coord(self.get_mouse_delta()) # panel coords mouse delta 
        odx, ody = self.view_editor.movie_coord_to_panel_coord((0, 0)) # movie origo in panel points
        delta = (mdx - odx, mdy - ody) # panel coords mouse delta - movie origo in panel points get delta in panel points

        if self.edit_mode == ROTO_MOVE_MODE:
            self.edit_point_shape.translate_from_move_start(delta)
        elif self.edit_mode == ROTO_POINT_MODE:
            if self.last_pressed_edit_point != None:
                if self.last_pressed_edit_point.display_type == vieweditorshape.ROTO_HANDLE_POINT:
                    self.last_pressed_edit_point.translate_from_move_start(delta)
                else: # curve point
                    hp1, hp2 = self.edit_point_shape.handles_for_curve_point[self.last_pressed_edit_point]
                    self.last_pressed_edit_point.translate_from_move_start(delta)
                    hp1.translate_from_move_start(delta)
                    hp2.translate_from_move_start(delta)
    
        self.edit_point_shape.maybe_force_line_mask()

    def mouse_released(self):
        self.edit_point_shape.block_shape_updates = False

        # delta is given in movie coords, RotoMaskEditShape uses panel coords  (because it needs to do complex drawing in those) so we have to convert mouse delta.
        mdx, mdy = self.view_editor.movie_coord_to_panel_coord(self.get_mouse_delta())
        odx, ody = self.view_editor.movie_coord_to_panel_coord((0, 0))
        delta = (mdx - odx, mdy - ody)
        
        if self.edit_mode == ROTO_MOVE_MODE:
            self.edit_point_shape.translate_from_move_start(delta)
        elif self.edit_mode == ROTO_POINT_MODE:
            if self.last_pressed_edit_point != None:
                if self.last_pressed_edit_point.display_type == vieweditorshape.ROTO_HANDLE_POINT:
                    self.last_pressed_edit_point.translate_from_move_start(delta)
                else: # curve point
                    hp1, hp2 = self.edit_point_shape.handles_for_curve_point[self.last_pressed_edit_point]
                    self.last_pressed_edit_point.translate_from_move_start(delta)
                    hp1.translate_from_move_start(delta)
                    hp2.translate_from_move_start(delta)
            else:
                return # no edit point moved, no update needed
        
        self.last_pressed_edit_point = None
        
        self.edit_point_shape.maybe_force_line_mask()
        
        self.edit_point_shape.convert_shape_coords_and_update_clip_editor_keyframes()
        self.editable_property.write_out_keyframes(self.clip_editor.keyframes)
        
        self.rotomask_editor.show_current_frame()
        self.rotomask_editor.update_effects_editor_value_labels()
        self.clip_editor.widget.queue_draw()
        self.view_editor.edit_area_update_blocked = False

    # --------------------------------------------- edit events
    def add_edit_point(self, index, p, show_current_frame=True):
        self.edit_point_shape.add_point(index, p)

        self.edit_point_shape.maybe_force_line_mask()

        self.editable_property.write_out_keyframes(self.clip_editor.keyframes)
        if show_current_frame:
            self.rotomask_editor.show_current_frame() #  callback for full update
        self.rotomask_editor.update_effects_editor_value_labels()
        
    def delete_selected_point(self):
        self.edit_point_shape.delete_selected_point()

        self.edit_point_shape.maybe_force_line_mask()

        self.editable_property.write_out_keyframes(self.clip_editor.keyframes)
        self.rotomask_editor.show_current_frame() #  callback for full update
        self.rotomask_editor.update_effects_editor_value_labels()

    # --------------------------------------------- state changes
    def frame_changed(self, tline_frame):
        self.edit_point_shape.update_shape()

    def mode_changed(self):
        pass
        
    # -------------------------------------------- draw
    def draw(self, cr, write_out_layers, draw_overlays):
        self.edit_point_shape.draw_line_shape(cr, self.view_editor)
        if self.edit_point_shape.closed == True:
            self.edit_point_shape.draw_points(cr, self.view_editor)
        else:
            self.edit_point_shape.draw_curve_points(cr, self.view_editor)


