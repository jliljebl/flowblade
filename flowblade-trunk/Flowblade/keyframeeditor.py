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
Module contains GUI widgets used to edit keyframed properties in filters and
compositors.

NOTE: All the editors are composites of smaller objects (so that similar 
but slighly different editors can be made in the future). There are a lots 
of callbacks to parent objects, this makes the design difficult to follow.
"""

import cairo

from gi.repository import Gtk, GObject
from gi.repository import Pango, PangoCairo

import appconsts
import cairoarea
import compositorfades
import editorpersistance
from editorstate import PLAYER
from editorstate import current_sequence
from editorstate import PROJECT
import gui
import guicomponents
import guiutils
import keyframeeditcanvas
import propertyedit
import propertyparse
import respaths
import utils

# Draw consts
CLIP_EDITOR_WIDTH = 250 
CLIP_EDITOR_HEIGHT = 21
END_PAD = 28
TOP_PAD = 2
OUT_OF_RANGE_ICON_PAD = 20
OUT_OF_RANGE_KF_ICON_HALF = 6
OUT_OF_RANGE_NUMBER_Y = 5
OUT_OF_RANGE_NUMBER_X_START = 1
OUT_OF_RANGE_NUMBER_X_END_PAD = 7

BUTTON_WIDTH = 22
BUTTON_HEIGHT = 24
KF_Y = 5
CENTER_LINE_Y = 11
POS_ENTRY_W = 38
POS_ENTRY_H = 20
KF_HIT_WIDTH = 4
KF_DRAG_THRESHOLD = 3

GEOM_EDITOR_SIZE_LARGE = 0.9 # displayed screensize as fraction of available height
GEOM_EDITOR_SIZE_SMALL = 0.3 # displayed screensize as fraction of available height
GEOM_EDITOR_SIZE_MEDIUM = 0.6 # displayed screensize as fraction of available height
GEOM_EDITOR_SIZES = [GEOM_EDITOR_SIZE_LARGE, GEOM_EDITOR_SIZE_MEDIUM, GEOM_EDITOR_SIZE_SMALL]

# Colors
POINTER_COLOR = (1, 0.3, 0.3)
CLIP_EDITOR_BG_COLOR = (0.1445, 0.172, 0.25)
CLIP_EDITOR_NOT_ACTIVE_BG_COLOR = (0.25, 0.28, 0.34)
CLIP_EDITOR_CENTER_LINE_COLOR = (0.098, 0.313, 0.574)
LIGHT_MULTILPLIER = 1.14
DARK_MULTIPLIER = 0.74

# Editor states
KF_DRAG = 0
POSITION_DRAG = 1
KF_DRAG_DISABLED = 2

# Icons
ACTIVE_KF_ICON = None
NON_ACTIVE_KF_ICON = None

# Magic value to signify disconnected signal handler 
DISCONNECTED_SIGNAL_HANDLER = -9999999

# Callbacks to compositeeditor.py, monkeypatched at startup
_get_current_edited_compositor = None

actions_menu = Gtk.Menu()
oor_before_menu = Gtk.Menu()
oor_after_menu = Gtk.Menu()

# ----------------------------------------------------- editor objects
class ClipKeyFrameEditor:
    """
    GUI component used to add, move and remove keyframes 
    inside a single clip. It is used as a component inside a parent editor and
    needs the parent editor to write out keyframe values.
    
    Parent editor must implement callback interface:
        def clip_editor_frame_changed(self, frame)
        def active_keyframe_changed(self)
        def keyframe_dragged(self, active_kf, frame)
        def update_slider_value_display(self, frame)
        def update_property_value(self)
    """

    def __init__(self, editable_property, parent_editor, use_clip_in=True):
        self.widget = cairoarea.CairoDrawableArea2( CLIP_EDITOR_WIDTH, 
                                                    CLIP_EDITOR_HEIGHT, 
                                                    self._draw)
        self.widget.press_func = self._press_event
        self.widget.motion_notify_func = self._motion_notify_event
        self.widget.release_func = self._release_event

        self.clip_length = editable_property.get_clip_length() - 1

        self.sensitive = True
    
        # Some filters start keyframes from *MEDIA* frame 0
        # Some filters or compositors start keyframes from *CLIP* frame 0
        # Filters starting from *MEDIA* 0 need offset 
        # to clip start added to all values.
        #
        # THIS IS NAMED A BIT UNCLEARLY: when use_clip_in=True this means that keyframes are relative to media
        # and clip in is used as first frame of edit range, use_clip_in=False means that first frame of edit range is 0 and all keyframes are relative to that
        #
        self.use_clip_in = use_clip_in
        if self.use_clip_in == True:
            self.clip_in = editable_property.clip.clip_in
        else:
            self.clip_in = 0
        self.current_clip_frame = self.clip_in

        self.keyframes = [(0, 0.0)]
        self.active_kf_index = 0

        self.parent_editor = parent_editor

        self.keyframe_parser = None # Function used to parse keyframes to tuples is different for different expressions
                                    # Parent editor sets this.
                                    
        self.current_mouse_action = None
        self.drag_on = False # Used to stop updating pos here if pos change is initiated here.
        self.drag_min = -1
        self.drag_max = -1

        self.mouse_listener = None #This is special service for RotoMaskKeyFrameEditor, not used by other editors

        # init icons if needed
        global ACTIVE_KF_ICON, NON_ACTIVE_KF_ICON
        if ACTIVE_KF_ICON == None:
            ACTIVE_KF_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "kf_active.png")
        if NON_ACTIVE_KF_ICON == None:
            NON_ACTIVE_KF_ICON = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "kf_not_active.png")    
            
    def set_keyframes(self, keyframes_str, out_to_in_func):
        self.keyframes = self.keyframe_parser(keyframes_str, out_to_in_func)

    def get_kf_info(self):
        return (self.active_kf_index, len(self.keyframes))
        
    def _get_panel_pos(self):
        return self._get_panel_pos_for_frame(self.current_clip_frame) 

    def _get_panel_pos_for_frame(self, frame):
        active_width = self.widget.get_allocation().width - 2 * END_PAD
        disp_frame = frame - self.clip_in 
        return END_PAD + int((float(disp_frame) / float(self.clip_length)) * 
                             active_width)

    def _get_frame_for_panel_pos(self, panel_x):
        active_width = self.widget.get_allocation().width - 2 * END_PAD
        clip_panel_x = panel_x - END_PAD
        norm_pos = float(clip_panel_x) / float(active_width)
        return int(norm_pos * self.clip_length) + self.clip_in
        
    def _set_clip_frame(self, panel_x):
        self.current_clip_frame = self._get_frame_for_panel_pos(panel_x)
    
    def move_clip_frame(self, delta):
        self.current_clip_frame = self.current_clip_frame + delta
        self._force_current_in_frame_range()

    def set_and_display_clip_frame(self, clip_frame):
        self.current_clip_frame = clip_frame
        self._force_current_in_frame_range()

    def _draw(self, event, cr, allocation):
        """
        Callback for repaint from CairoDrawableArea.
        We get cairo context and allocation.
        """
        x, y, w, h = allocation
        active_width = w - 2 * END_PAD
        active_height = h - 2 * TOP_PAD      
        
        # Draw clip bg  
        cr.set_source_rgb(*CLIP_EDITOR_BG_COLOR)
        if self.sensitive == False:
            cr.set_source_rgb(*CLIP_EDITOR_NOT_ACTIVE_BG_COLOR)
        cr.rectangle(END_PAD, TOP_PAD, active_width, active_height)
        cr.fill()

        # Clip edge and emboss
        rect = (END_PAD, TOP_PAD, active_width, active_height)
        self.draw_edge(cr, rect)
        self.draw_emboss(cr, rect, gui.get_bg_color())

        # Draw center line
        cr.set_source_rgb(*CLIP_EDITOR_CENTER_LINE_COLOR)
        cr.set_line_width(2.0)
        cr.move_to(END_PAD, CENTER_LINE_Y)
        cr.line_to(END_PAD + active_width, CENTER_LINE_Y)
        cr.stroke()

        # Draw keyframes
        for i in range(0, len(self.keyframes)):
            frame, value = self.keyframes[i]
            if frame < self.clip_in:
                continue
            if frame > self.clip_in + self.clip_length:
                continue  
            if i == self.active_kf_index:
                icon = ACTIVE_KF_ICON
            else:
                icon = NON_ACTIVE_KF_ICON
            try:
                kf_pos = self._get_panel_pos_for_frame(frame)
            except ZeroDivisionError: # math fails for 1 frame clip
                kf_pos = END_PAD
            cr.set_source_surface(icon, kf_pos - 6, KF_Y)
            cr.paint()

        # Draw out-of-range kf icons kf counts
        before_kfs = len(self.get_out_of_range_before_kfs())
        after_kfs = len(self.get_out_of_range_after_kfs())
        if before_kfs > 0:
            cr.set_source_surface(NON_ACTIVE_KF_ICON, OUT_OF_RANGE_ICON_PAD - OUT_OF_RANGE_KF_ICON_HALF * 2, KF_Y)
            cr.paint()
            self.draw_kf_count_number(cr, before_kfs, OUT_OF_RANGE_NUMBER_X_START, OUT_OF_RANGE_NUMBER_Y)
        if after_kfs > 0:
            cr.set_source_surface(NON_ACTIVE_KF_ICON, w - OUT_OF_RANGE_ICON_PAD, KF_Y)
            cr.paint()
            self.draw_kf_count_number(cr, after_kfs, w - OUT_OF_RANGE_NUMBER_X_END_PAD, OUT_OF_RANGE_NUMBER_Y)
        
        # Draw frame pointer
        try:
            panel_pos = self._get_panel_pos()
        except ZeroDivisionError: # math fails for 1 frame clip
            panel_pos = END_PAD
        cr.set_line_width(2.0)
        cr.set_source_rgb(*POINTER_COLOR)
        cr.move_to(panel_pos, 0)
        cr.line_to(panel_pos, CLIP_EDITOR_HEIGHT)
        cr.stroke()
        
    def draw_emboss(self, cr, rect, color):
        # Emboss, corner points
        left = rect[0] + 1.5
        up = rect[1] + 1.5
        right = left + rect[2] - 2.0
        down = up + rect[3] - 2.0
            
        # Draw lines
        color_tuple = gui.unpack_gdk_color(color)
        light_color = guiutils.get_multiplied_color(color_tuple, LIGHT_MULTILPLIER)
        cr.set_source_rgb(*light_color)
        cr.move_to(left, down)
        cr.line_to(left, up)
        cr.stroke()
            
        cr.move_to(left, up)
        cr.line_to(right, up)
        cr.stroke()

        dark_color = guiutils.get_multiplied_color(color_tuple, DARK_MULTIPLIER)
        cr.set_source_rgb(*dark_color)
        cr.move_to(right, up)
        cr.line_to(right, down)
        cr.stroke()
            
        cr.move_to(right, down)
        cr.line_to(left, down)
        cr.stroke()

    def draw_edge(self, cr, rect):
        cr.set_line_width(1.0)
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(rect[0] + 0.5, rect[1] + 0.5, rect[2], rect[3])
        cr.stroke()

    def draw_kf_count_number(self, cr, count, x, y):
        # Draw track name
        layout = PangoCairo.create_layout(cr)
        layout.set_text(str(count), -1)
        desc = Pango.FontDescription("Sans 8")
        layout.set_font_description(desc)

        cr.move_to(x, y)
        cr.set_source_rgb(0.9, 0.9, 0.9)
        PangoCairo.update_layout(cr, layout)
        PangoCairo.show_layout(cr, layout)
        
    def _press_event(self, event):
        """
        Mouse button callback
        """
        # Check if kf icon before or after clip range have been pressed
        if self.oor_start_kf_hit(event.x, event.y):
            self._show_oor_before_menu(self.widget, event)
            return

        if self.oor_end_kf_hit(event.x, event.y):
            self._show_oor_after_menu(self.widget, event)
            return
        
        if self.sensitive == False:
            return
        
        # Handle clip range mouse events
        self.drag_on = True

        lx = self._legalize_x(event.x)
        hit_kf = self._key_frame_hit(lx, event.y)

        if hit_kf == None: # nothing was hit
            self.current_mouse_action = POSITION_DRAG
            self._set_clip_frame(lx)
            self.parent_editor.clip_editor_frame_changed(self.current_clip_frame)
            self.widget.queue_draw()
        else: # some keyframe was pressed         
            self.active_kf_index = hit_kf
            frame, value = self.keyframes[hit_kf]
            self.current_clip_frame = frame
            self.parent_editor.active_keyframe_changed()
            if hit_kf == 0:
                self.current_mouse_action = KF_DRAG_DISABLED
            else:
                self.current_mouse_action = KF_DRAG
                
                self.drag_start_x = event.x
                
                prev_frame, val = self.keyframes[hit_kf - 1]
                self.drag_min = prev_frame  + 1
                try:
                    next_frame, val = self.keyframes[hit_kf + 1]
                    self.drag_max = next_frame - 1
                except:
                    self.drag_max = self.clip_in + self.clip_length

            self.widget.queue_draw()
            
    def _motion_notify_event(self, x, y, state):
        """
        Mouse move callback
        """
        if self.sensitive == False:
            return
            
        lx = self._legalize_x(x)
        
        if self.current_mouse_action == POSITION_DRAG:
            self._set_clip_frame(lx)
            self.parent_editor.clip_editor_frame_changed(self.current_clip_frame)
        elif self.current_mouse_action == KF_DRAG:
            frame = self._get_drag_frame(lx)
            self.set_active_kf_frame(frame)
            self.current_clip_frame = frame
            self.parent_editor.keyframe_dragged(self.active_kf_index, frame)
            self.parent_editor.active_keyframe_changed()

        self.widget.queue_draw()
        
        if self.mouse_listener != None:
            self.mouse_listener.mouse_pos_change_done()
        
    def _release_event(self, event):
        """
        Mouse release callback.
        """
        if self.sensitive == False:
            return

        lx = self._legalize_x(event.x)

        if self.current_mouse_action == POSITION_DRAG:
            self._set_clip_frame(lx)
            self.parent_editor.clip_editor_frame_changed(self.current_clip_frame)
            self.parent_editor.update_slider_value_display(self.current_clip_frame)
        elif self.current_mouse_action == KF_DRAG:
            frame = self._get_drag_frame(lx)
            self.set_active_kf_frame(frame)
            self.current_clip_frame = frame
            self.parent_editor.keyframe_dragged(self.active_kf_index, frame)
            self.parent_editor.active_keyframe_changed()
            self.parent_editor.update_property_value()
            self.parent_editor.update_slider_value_display(frame)   

        self.widget.queue_draw()
        self.current_mouse_action = None

        if self.mouse_listener != None:
            self.mouse_listener.mouse_pos_change_done()
            
        self.drag_on = False
        
    def _legalize_x(self, x):
        """
        Get x in pixel range between end pads.
        """
        w = self.widget.get_allocation().width
        if x < END_PAD:
            return END_PAD
        elif x > w - END_PAD:
            return w - END_PAD
        else:
            return x
    
    def _force_current_in_frame_range(self):
        if self.current_clip_frame < self.clip_in:
            self.current_clip_frame = self.clip_in
        if self.current_clip_frame > self.clip_in + self.clip_length:
            self.current_clip_frame = self.clip_in + self.clip_length

    def get_out_of_range_before_kfs(self):
        # returns Keyframes before current clip start
        kfs = []
        for i in range(0, len(self.keyframes)):
            frame, value = self.keyframes[i]
            if frame < self.clip_in:
                kfs.append(self.keyframes[i])
        return kfs

    def get_out_of_range_after_kfs(self):
        # returns Keyframes before current clip start
        kfs = []
        for i in range(0, len(self.keyframes)):
            frame, value = self.keyframes[i]
            if frame > self.clip_in + self.clip_length:
                kfs.append(self.keyframes[i])
        return kfs
                
    def _get_drag_frame(self, panel_x):
        """
        Get x in range available for current drag.
        """
        frame = self._get_frame_for_panel_pos(panel_x)
        if frame < self.drag_min:
            frame = self.drag_min
        if frame > self.drag_max:
            frame = self.drag_max
        return frame
    
    def _key_frame_hit(self, x, y):
        for i in range(0, len(self.keyframes)):
            frame, val = self.keyframes[i]
            frame_x = self._get_panel_pos_for_frame(frame)
            frame_y = KF_Y + 6
            if((abs(x - frame_x) < KF_HIT_WIDTH)
                and (abs(y - frame_y) < KF_HIT_WIDTH)):
                return i
            
        return None

    def oor_start_kf_hit(self, x, y):
        test_x = OUT_OF_RANGE_ICON_PAD - OUT_OF_RANGE_KF_ICON_HALF * 2
        if y >= KF_Y and y <= KF_Y + 12: # 12 icon size
            if x >= test_x and x <= test_x + 12:
                return True
        
        return False

    def oor_end_kf_hit(self, x, y):
        w = self.widget.get_allocation().width
        test_x = w - OUT_OF_RANGE_ICON_PAD
        if y >= KF_Y and y <= KF_Y + 12: # 12 icon size
            if x >= test_x and x <= test_x + 12:
                return True
        
        return False

    def add_keyframe(self, frame):
        # NOTE: This makes added keyframe the active keyframe too.
        kf_index_on_frame = self.frame_has_keyframe(frame)
        if kf_index_on_frame != -1:
            # Trying add on top of existing keyframe makes it active
            self.active_kf_index = kf_index_on_frame
            return

        for i in range(0, len(self.keyframes)):
            kf_frame, kf_value = self.keyframes[i]
            if kf_frame > frame:
                prev_frame, prev_value = self.keyframes[i - 1]
                self.keyframes.insert(i, (frame, prev_value))
                self.active_kf_index = i
                return
        prev_frame, prev_value = self.keyframes[len(self.keyframes) - 1]
        self.keyframes.append((frame, prev_value))
        self.active_kf_index = len(self.keyframes) - 1

    def print_keyframes(self, msg="no_msg"):
        print(msg, "clip edit keyframes:")
        for i in range(0, len(self.keyframes)):
            print(self.keyframes[i])
        
    def delete_active_keyframe(self):
        if self.active_kf_index == 0:
            # keyframe frame 0 cannot be removed
            return
        self.keyframes.pop(self.active_kf_index)
        self.active_kf_index -= 1
        if self.active_kf_index < 0:
            self.active_kf_index = 0
        self._set_pos_to_active_kf()

    def set_next_active(self):
        """
        Activates next keyframe or keeps last active to stay in range.
        """
        self.active_kf_index += 1
        if self.active_kf_index > (len(self.keyframes) - 1):
            self.active_kf_index = len(self.keyframes) - 1
        
        if self.active_kf_index > (len(self.keyframes) - 1 - len(self.get_out_of_range_after_kfs())):
            self.active_kf_index = (len(self.keyframes) - 1 - len(self.get_out_of_range_after_kfs()))
        self._set_pos_to_active_kf()
        
    def set_prev_active(self):
        """
        Activates previous keyframe or keeps first active to stay in range.
        """
        self.active_kf_index -= 1
        if self.active_kf_index < 0:
            self.active_kf_index = 0
            
        if self.active_kf_index < len(self.get_out_of_range_before_kfs()):
            self.active_kf_index = len(self.get_out_of_range_before_kfs())

        self._set_pos_to_active_kf()
    
    def _set_pos_to_active_kf(self):
        try:
            frame, value = self.keyframes[self.active_kf_index]
            self.current_clip_frame = frame
            self._force_current_in_frame_range()
            self.parent_editor.update_slider_value_display(self.current_clip_frame)   
        except:
            pass # This can fail if no keyframes exist in edit range but then we will just do nothing
            
    def frame_has_keyframe(self, frame):
        """
        Returns index of keyframe if frame has keyframe or -1 if it doesn't.
        """
        for i in range(0, len(self.keyframes)):
            kf_frame, kf_value = self.keyframes[i]
            if frame == kf_frame:
                return i

        return -1
    
    def get_active_kf_frame(self):
        frame, val = self.keyframes[self.active_kf_index]
        return frame

    def get_active_kf_value(self):
        frame, val = self.keyframes[self.active_kf_index]
        return val
    
    def set_active_kf_value(self, new_value):
        frame, val = self.keyframes.pop(self.active_kf_index)
        self.keyframes.insert(self.active_kf_index,(frame, new_value))

    def active_kf_pos_entered(self, frame):
        if self.active_kf_index == 0:
            return
        
        prev_frame, val = self.keyframes[self.active_kf_index - 1]
        prev_frame += 1
        try:
            next_frame, val = self.keyframes[self.active_kf_index + 1]
            next_frame -= 1
        except:
            next_frame = self.clip_in + self.clip_length

        frame = max(frame, prev_frame)
        frame = min(frame, next_frame)

        self.set_active_kf_frame(frame)
        self.current_clip_frame = frame    
    
    def maybe_set_first_kf_in_clip_area_active(self):
        index = 0
        for kf in self.keyframes:
            kf_frame, val = kf
        
            if kf_frame >= self.clip_in:
                 self.active_kf_index = index
                 self._set_pos_to_active_kf()
                 break
                 
            index += 1
    
    def set_active_kf_frame(self, new_frame):
        frame, val = self.keyframes.pop(self.active_kf_index)
        self.keyframes.insert(self.active_kf_index,(new_frame, val))

    def _show_oor_before_menu(self, widget, event):
        menu = oor_before_menu
        guiutils.remove_children(menu)
        before_kfs = len(self.get_out_of_range_before_kfs())

        if before_kfs == 0:
            # hit detection is active even if the kf icon is not displayed
            return

        if before_kfs > 1:
            menu.add(self._get_menu_item(_("Delete all but first Keyframe before Clip Range"), self._oor_menu_item_activated, "delete_all_before" ))
            sep = Gtk.SeparatorMenuItem()
            sep.show()
            menu.add(sep)

        if len(self.keyframes) > 1:
            menu.add(self._get_menu_item(_("Set Keyframe at Frame 0 to value of next Keyframe"), self._oor_menu_item_activated, "zero_next" ))
        elif before_kfs == 1:
            item = self._get_menu_item(_("No Edit Actions currently available"), self._oor_menu_item_activated, "noop" )
            item.set_sensitive(False)
            menu.add(item)

        menu.popup(None, None, None, None, event.button, event.time)

    def _show_oor_after_menu(self, widget, event):
        menu = oor_before_menu
        guiutils.remove_children(menu)
        after_kfs = self.get_out_of_range_after_kfs()
        
        if after_kfs == 0:
            # hit detection is active even if the kf icon is not displayed
            return

        menu.add(self._get_menu_item(_("Delete all Keyframes after Clip Range"), self._oor_menu_item_activated, "delete_all_after" ))
        menu.popup(None, None, None, None, event.button, event.time)
        
    def _oor_menu_item_activated(self, widget, data):
        if data == "delete_all_before":
            keep_doing = True
            while keep_doing:
                try:
                    frame, value = self.keyframes[1]
                    if frame < self.clip_in:
                        self.keyframes.pop(1)
                    else:
                        keep_doing = False 
                except:
                    keep_doing = False
        elif data == "zero_next":
            frame_zero, frame_zero_value = self.keyframes[0]
            frame, value = self.keyframes[1]
            self.keyframes.pop(0)
            self.keyframes.insert(0, (frame_zero, value))
            self.parent_editor.update_property_value()
        elif data == "delete_all_after":
            delete_done = False
            for i in range(0, len(self.keyframes)):
                frame, value = self.keyframes[i]
                if frame > self.clip_in + self.clip_length:
                    self.keyframes.pop(i)
                    popped = True
                    while popped:
                        try:
                            self.keyframes.pop(i)
                        except:
                            popped = False
                    delete_done = True
                if delete_done:
                    break
        self.widget.queue_draw()
        
    def _get_menu_item(self, text, callback, data):
        item = Gtk.MenuItem(text)
        item.connect("activate", callback, data)
        item.show()
        return item
        
    def set_sensitive(self, sensitive):
        self.sensitive = sensitive
 
# ----------------------------------------------------------- buttons objects
class ClipEditorButtonsRow(Gtk.HBox):
    """
    Row of buttons used to navigate and add keyframes and frame 
    entry box for active keyframe. Parent editor must implemnt interface
    defined by methods:
        editor_parent.add_pressed()
        editor_parent.delete_pressed()
        editor_parent.prev_pressed()
        editor_parent.next_pressed()
        editor_parent.prev_frame_pressed()
        editor_parent.next_frame_pressed()
    """
    def __init__(self, editor_parent, centered_buttons=False, show_fade_buttons=True):
        GObject.GObject.__init__(self)
        self.set_homogeneous(False)
        self.set_spacing(2)

        # Aug-2019 - SvdB - BB
        self.add_button = guiutils.get_image_button("add_kf", BUTTON_WIDTH, BUTTON_HEIGHT)
        self.delete_button = guiutils.get_image_button("delete_kf", BUTTON_WIDTH, BUTTON_HEIGHT)
        self.prev_kf_button = guiutils.get_image_button("prev_kf", BUTTON_WIDTH, BUTTON_HEIGHT)
        self.next_kf_button = guiutils.get_image_button("next_kf", BUTTON_WIDTH, BUTTON_HEIGHT)
        self.prev_frame_button = guiutils.get_image_button("kf_edit_prev_frame", BUTTON_WIDTH, BUTTON_HEIGHT)
        self.next_frame_button = guiutils.get_image_button("kf_edit_next_frame", BUTTON_WIDTH, BUTTON_HEIGHT)
        self.kf_to_prev_frame_button = guiutils.get_image_button("kf_edit_kf_to_prev_frame", BUTTON_WIDTH, BUTTON_HEIGHT)
        self.kf_to_next_frame_button = guiutils.get_image_button("kf_edit_kf_to_next_frame", BUTTON_WIDTH, BUTTON_HEIGHT)
        self.add_fade_in_button = guiutils.get_image_button("add_fade_in", BUTTON_WIDTH, BUTTON_HEIGHT)
        self.add_fade_out_button = guiutils.get_image_button("add_fade_out", BUTTON_WIDTH, BUTTON_HEIGHT)
        
        self.add_button.connect("clicked", lambda w,e: editor_parent.add_pressed(), None)
        self.delete_button.connect("clicked", lambda w,e: editor_parent.delete_pressed(), None)
        self.prev_kf_button.connect("clicked", lambda w,e: editor_parent.prev_pressed(), None)
        self.next_kf_button.connect("clicked", lambda w,e: editor_parent.next_pressed(), None)
        self.prev_frame_button.connect("clicked", lambda w,e: editor_parent.prev_frame_pressed(), None)
        self.next_frame_button.connect("clicked", lambda w,e: editor_parent.next_frame_pressed(), None)
        self.kf_to_prev_frame_button.connect("clicked", lambda w,e: editor_parent.move_kf_prev_frame_pressed(), None)
        self.kf_to_next_frame_button.connect("clicked", lambda w,e: editor_parent.move_kf_next_frame_pressed(), None)
        self.add_fade_in_button.connect("clicked", lambda w,e: editor_parent.add_fade_in(), None)
        self.add_fade_out_button.connect("clicked", lambda w,e: editor_parent.add_fade_out(), None)

        self.add_button.set_tooltip_text(_("Add Keyframe"))
        self.delete_button.set_tooltip_text(_("Delete Keyframe"))
        self.prev_kf_button.set_tooltip_text(_("Previous Keyframe"))
        self.next_kf_button.set_tooltip_text(_("Next Keyframe")) 
        self.prev_frame_button.set_tooltip_text(_("Previous Frame"))
        self.next_frame_button.set_tooltip_text(_("Next Frame"))
        self.kf_to_prev_frame_button.set_tooltip_text(_("Move Keyframe 1 Frame Back"))
        self.kf_to_next_frame_button.set_tooltip_text(_("Move Keyframe 1 Frame Forward"))
        self.add_fade_in_button.set_tooltip_text(_("Add Fade In"))
        self.add_fade_out_button.set_tooltip_text(_("Add Fade Out"))
        
        # Position entry
        self.kf_pos_label = Gtk.Label()
        self.modify_font(Pango.FontDescription("light 8"))
        self.kf_pos_label.set_text("0")

        self.kf_info_label = Gtk.Label()
        self.kf_info_label.set_text("1/1")
        
        # Build row
        if centered_buttons:
            self.pack_start(Gtk.Label(), True, True, 0)
        self.pack_start(self.add_button, False, False, 0)
        self.pack_start(self.delete_button, False, False, 0)
        self.pack_start(guiutils.pad_label(24,4), False, False, 0)
        self.pack_start(self.prev_kf_button, False, False, 0)
        self.pack_start(self.next_kf_button, False, False, 0)
        self.pack_start(self.kf_to_prev_frame_button, False, False, 0)
        self.pack_start(self.kf_to_next_frame_button, False, False, 0)
        self.pack_start(self.prev_frame_button, False, False, 0)
        self.pack_start(self.next_frame_button, False, False, 0)
        self.pack_start(guiutils.pad_label(24,4), False, False, 0)
        if show_fade_buttons:
            self.pack_start(self.add_fade_in_button, False, False, 0)
            self.pack_start(self.add_fade_out_button, False, False, 0)
        if not centered_buttons:
            self.pack_start(Gtk.Label(), True, True, 0)
        else:
            self.pack_start(guiutils.pad_label(4,4), False, False, 0)
            
        self.pack_start(self.kf_info_label, False, False, 0)
        self.pack_start(guiutils.pad_label(24,4), False, False, 0) 
        self.pack_start(self.kf_pos_label, False, False, 0)
        
        if centered_buttons:
            self.pack_start(Gtk.Label(), True, True, 0)
        else:
            self.pack_start(guiutils.get_pad_label(1, 10), False, False, 0)
            
    def set_frame(self, frame):
        frame_str = utils.get_tc_string(frame)
        self.kf_pos_label.set_text(frame_str)

    def set_kf_info(self, info):
        active_index, total = info
        self.kf_info_label.set_text(str(active_index + 1) + "/" + str(total))

    def set_buttons_sensitive(self, sensitive):
        self.add_button.set_sensitive(sensitive)
        self.delete_button.set_sensitive(sensitive)
        self.prev_kf_button.set_sensitive(sensitive)
        self.next_kf_button.set_sensitive(sensitive)
        self.prev_frame_button.set_sensitive(sensitive)
        self.next_frame_button.set_sensitive(sensitive)
        self.kf_to_prev_frame_button.set_sensitive(sensitive)
        self.kf_to_next_frame_button.set_sensitive(sensitive)



class GeometryEditorButtonsRow(Gtk.HBox):
    def __init__(self, editor_parent, empty_center=False):
        """
        editor_parent needs to implement interface:
        -------------------------------------------
        editor_parent.view_size_changed(widget_active_index)
        editor_parent.menu_item_activated()
        """
        GObject.GObject.__init__(self)
        self.set_homogeneous(False)
        self.set_spacing(2)
        
        self.editor_parent = editor_parent
        
        name_label = Gtk.Label(label=_("View:"))

        # Aug-2019 - SvdB - BB
        size_adj = 1
        if editorpersistance.prefs.double_track_hights:
            size_adj = 2
        surface = guiutils.get_cairo_image("geom_action")
        action_menu_button = guicomponents.PressLaunch(self._show_actions_menu, surface, 24*size_adj, 22*size_adj)
        
        size_select = Gtk.ComboBoxText()
        size_select.append_text("100%")
        size_select.append_text("66%")
        size_select.append_text("33%")
        size_select.set_active(1)
        size_select.connect("changed", lambda w,e: editor_parent.view_size_changed(w.get_active()), 
                            None)
        self.size_select = size_select
        
        # Build row
        self.pack_start(action_menu_button.widget, False, False, 0)
        if empty_center == True:
            self.pack_start(Gtk.Label(), True, True, 0)
        else:
            self.pack_start(guiutils.get_pad_label(12, 10), False, False, 0)
        self.pack_start(size_select, False, False, 0)

    def _show_actions_menu(self, widget, event):
        menu = actions_menu
        guiutils.remove_children(menu)
        menu.add(self._get_menu_item(_("Reset Geometry"), self.editor_parent.menu_item_activated, "reset" ))
        menu.add(self._get_menu_item(_("Geometry to Original Aspect Ratio"), self.editor_parent.menu_item_activated, "ratio" ))
        menu.add(self._get_menu_item(_("Center Horizontal"), self.editor_parent.menu_item_activated, "hcenter" ))
        menu.add(self._get_menu_item(_("Center Vertical"), self.editor_parent.menu_item_activated, "vcenter" ))
        menu.popup(None, None, None, None, event.button, event.time)

    def _get_menu_item(self, text, callback, data):
        item = Gtk.MenuItem(text)
        item.connect("activate", callback, data)
        item.show()
        return item

# ------------------------------------------------------------ master editors

class AbstractKeyFrameEditor(Gtk.VBox):
    """
    AbstractKeyFrameEditor is parent editor for ClipKeyFrameEditor and is updated with callbacks
    from there for timeline position changes keyframe changes. Extending classes KeyframeEditor and GeometryEditor
    handles some of the  ClipKeyFrameEditor callbacks.
    
    AbstractKeyFrameEditor editor also has slider for setting keyframe values.
    """
    def __init__(self, editable_property, use_clip_in=True, slider_switcher=None):
        # editable_property is KeyFrameProperty
        GObject.GObject.__init__(self)
        self.initializing = True # Hack against too early for on slider listner
        
        self.set_homogeneous(False)
        self.set_spacing(2)
        self.editable_property = editable_property
        self.clip_tline_pos = editable_property.get_clip_tline_pos()

        self.clip_editor = ClipKeyFrameEditor(editable_property, self, use_clip_in)
        """
        Callbacks from ClipKeyFrameEditor:
        def clip_editor_frame_changed(self, frame)
        def active_keyframe_changed(self)
        def keyframe_dragged(self, active_kf, frame)
        def update_slider_value_display(self, frame)
        
        These may be implemented here or in extending classes KeyframeEditor and GeometryEditor
        """
        
        # Some filters start keyframes from *MEDIA* frame 0
        # Some filters or compositors start keyframes from *CLIP* frame 0
        # Filters starting from *media* 0 need offset to clip start added to all values
        self.use_clip_in = use_clip_in
        if self.use_clip_in == True:
            self.clip_in = editable_property.clip.clip_in
        else:
            self.clip_in = 0

        # Value slider
        row, slider, spin = guiutils.get_slider_row_and_spin_widget(editable_property, self.slider_value_changed)
        
        if slider_switcher != None:
            hbox = Gtk.HBox(False, 4)
            hbox.pack_start(row, True, True, 0)
            hbox.pack_start(slider_switcher.widget, False, False, 4)
            row = hbox
    
        self.value_slider_row = row
        self.slider = slider
        self.spin = spin

        self.initializing = False # Hack against too early for on slider listner

    def display_tline_frame(self, tline_frame):
        # This is called after timeline current frame changed. 
        # If timeline pos changed because drag is happening _here_,
        # updating once more is wrong
        if self.clip_editor.drag_on == True:
            return

        # update clipeditor pos
        clip_frame = tline_frame - self.clip_tline_pos + self.clip_in
        self.clip_editor.set_and_display_clip_frame(clip_frame)
        self.update_editor_view(False)
    
    def update_clip_pos(self):
        # This is called after position of clip has been edited.
        # We'll need to update some values to get keyframes on correct positions again
        self.editable_property.update_clip_index()
        self.clip_tline_pos = self.editable_property.get_clip_tline_pos()
    
        if self.use_clip_in == True:
            self.clip_in = self.editable_property.clip.clip_in
        else:
            self.clip_in = 0
        self.clip_editor.clip_in = self.editable_property.clip.clip_in

        self.clip_editor.widget.queue_draw()
        
    def update_slider_value_display(self, frame):
        # This is called after frame changed or mouse release to update
        # slider value without causing 'changed' signal to update keyframes.
        if self.editable_property.value_changed_ID != DISCONNECTED_SIGNAL_HANDLER:
            self.slider.get_adjustment().handler_block(self.editable_property.value_changed_ID)

        new_value = _get_frame_value(frame, self.clip_editor.keyframes)
        self.editable_property.adjustment.set_value(new_value)
        if self.editable_property.value_changed_ID != DISCONNECTED_SIGNAL_HANDLER:
            self.slider.get_adjustment().handler_unblock(self.editable_property.value_changed_ID) 

    def seek_tline_frame(self, clip_frame):
        PLAYER().seek_frame(self.clip_tline_pos + clip_frame - self.clip_in)
    
    def update_editor_view(self, seek_tline=True):
        print(type(self), "update_editor_view not implemented")

    def paste_kf_value(self, value):
        print(type(self), "paste_kf_value not implemented")

    def get_copy_kf_value(self):
        print(type(self), "get_copy_kf_value not implemented")


class KeyFrameEditor(AbstractKeyFrameEditor):
    """
    Class combines named value slider with ClipKeyFrameEditor and 
    control buttons to create keyframe editor for a single keyframed
    numerical value property. 
    """
    def __init__(self, editable_property, use_clip_in=True, slider_switcher=None, fade_buttons=False):
        AbstractKeyFrameEditor.__init__(self, editable_property, use_clip_in, slider_switcher)

        self.slider_switcher = slider_switcher

        # default parser
        self.clip_editor.keyframe_parser = propertyparse.single_value_keyframes_string_to_kf_array

        # parsers for other editable_property types
        if isinstance(editable_property, propertyedit.OpacityInGeomKeyframeProperty):
            self.clip_editor.keyframe_parser = propertyparse.geom_keyframes_value_string_to_opacity_kf_array
            
        editable_property.value.strip('"')
        
        self.clip_editor.set_keyframes(editable_property.value, editable_property.get_in_value)
        clip_editor_row = Gtk.HBox(False, 0)
        clip_editor_row.pack_start(self.clip_editor.widget, True, True, 0)
        clip_editor_row.pack_start(guiutils.pad_label(4, 4), False, False, 0)
        
        self.buttons_row = ClipEditorButtonsRow(self, False, fade_buttons)
        
        self.pack_start(self.value_slider_row, False, False, 0)
        self.pack_start(clip_editor_row, False, False, 0)
        self.pack_start(self.buttons_row, False, False, 0)

        orig_tline_frame = PLAYER().current_frame()

        self.active_keyframe_changed() # to do update gui to current values
                                       # This also seeks tline frame to frame 0, thus value was saved in the line above

        # If we do not want to seek to kf 0 or clip start we, need seek back to original tline frame
        self.display_tline_frame(orig_tline_frame)
        PLAYER().seek_frame(orig_tline_frame)
        
    def slider_value_changed(self, adjustment):
        value = adjustment.get_value()        
        # Add key frame if were not on active key frame
        active_kf_frame = self.clip_editor.get_active_kf_frame()
        current_frame = self.clip_editor.current_clip_frame
        if current_frame != active_kf_frame:
            self.clip_editor.add_keyframe(current_frame)
            self.clip_editor.set_active_kf_value(value)
            self.update_editor_view()
            self.update_property_value()
        else: # if on kf, just update value
            self.clip_editor.set_active_kf_value(value)
            self.update_property_value()

    def active_keyframe_changed(self):
        frame = self.clip_editor.current_clip_frame
        keyframes = self.clip_editor.keyframes
        value = _get_frame_value(frame, keyframes)
        self.slider.set_value(value)
        self.buttons_row.set_frame(frame)
        self.seek_tline_frame(frame)
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())

    def clip_editor_frame_changed(self, clip_frame):
        self.seek_tline_frame(clip_frame)
        self.buttons_row.set_frame(clip_frame)

    def add_pressed(self):
        self.clip_editor.add_keyframe(self.clip_editor.current_clip_frame)
        self.update_editor_view()
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        
    def delete_pressed(self):
        self.clip_editor.delete_active_keyframe()
        self.update_editor_view()
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())

    def get_copy_kf_value(self):
        return self.clip_editor.get_active_kf_value()
        
    def paste_kf_value(self, value_data):
        self.clip_editor.set_active_kf_value(value_data)
        self.update_editor_view()
        self.update_property_value()
        
    def next_pressed(self):
        self.clip_editor.set_next_active()
        self.update_editor_view()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        
    def prev_pressed(self):
        self.clip_editor.set_prev_active()
        self.update_editor_view()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())

    def prev_frame_pressed(self):
        self.clip_editor.move_clip_frame(-1)
        self.update_editor_view()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        
    def next_frame_pressed(self):
        self.clip_editor.move_clip_frame(1)
        self.update_editor_view()

    def move_kf_next_frame_pressed(self):
        current_frame = self.clip_editor.get_active_kf_frame()
        self.clip_editor.active_kf_pos_entered(current_frame + 1)
        self.update_property_value()
        self.update_editor_view()

    def move_kf_prev_frame_pressed(self):
        current_frame = self.clip_editor.get_active_kf_frame()
        self.clip_editor.active_kf_pos_entered(current_frame - 1)
        self.update_property_value()
        self.update_editor_view()

    def keyframe_dragged(self, active_kf, frame):
        pass

    def update_editor_view(self, seek_tline=True):
        frame = self.clip_editor.current_clip_frame
        keyframes = self.clip_editor.keyframes
        value = _get_frame_value(frame, keyframes)
        self.buttons_row.set_frame(frame)
        if seek_tline == True:
            self.seek_tline_frame(frame)
        self.update_slider_value_display(frame) # NOTE!!!!!!!!!! Added for 2.0, observe if adds crashes
        self.queue_draw()

    def connect_to_update_on_release(self):
        self.editable_property.adjustment.disconnect(self.editable_property.value_changed_ID)
        self.editable_property.value_changed_ID = DISCONNECTED_SIGNAL_HANDLER
        self.spin.connect("activate", lambda w:self.spin_value_changed(w))
        self.spin.connect("button-release-event", lambda w, e:self.spin_value_changed(w))
        self.slider.connect("button-release-event", lambda w, e:self.slider_value_changed(w.get_adjustment()))
        
    def update_property_value(self):
        self.editable_property.write_out_keyframes(self.clip_editor.keyframes)

    def spin_value_changed(self, w):
        adj = w.get_adjustment()
        val = int(w.get_text())
        adj.set_value(float(val))
        self.slider_value_changed(adj)


class KeyFrameEditorClipFade(KeyFrameEditor):
    """
    Used for compositors with just slider and keyframes.
    """
    def __init__(self, editable_property):
        KeyFrameEditor.__init__(self, editable_property, use_clip_in=False, slider_switcher=None, fade_buttons=True)

    def add_fade_in(self):
        compositor = _get_current_edited_compositor()
        fade_default_length = PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH)
        keyframes = compositorfades.add_fade_in(compositor, fade_default_length) # updates editable_property.value.
        if keyframes == None:
            return # update failed, clip probably too short
        self._update_all_for_kf_vec(keyframes)
                
    def add_fade_out(self):
        compositor = _get_current_edited_compositor()
        fade_default_length = PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH)
        keyframes = compositorfades.add_fade_out(compositor, fade_default_length) # updates editable_property.value.
        if keyframes == None:
            return # update failed, clip probably too short
        self._update_all_for_kf_vec(keyframes)

    def _update_all_for_kf_vec(self, keyframes):
        self.editable_property.write_out_keyframes(keyframes)
        self.clip_editor.set_keyframes(self.editable_property.value, self.editable_property.get_in_value)
        self.update_editor_view()


class KeyFrameEditorClipFadeFilter(KeyFrameEditor):
    """
    Used for compositors with just slider and keyframes.
    """
    def __init__(self, editable_property):
        KeyFrameEditor.__init__(self, editable_property, use_clip_in=True, slider_switcher=None, fade_buttons=True)

    def add_fade_in(self):
        # The code to do fades was written originally for compositors so we are using module compositorfades with some added code for filters.
        fade_default_length = PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH)
        keyframes = compositorfades.add_filter_fade_in(self.editable_property.clip, self.editable_property, self.clip_editor.keyframes, fade_default_length)
        if keyframes == None:
            return # update failed, clip probably too short
        self._update_all_for_kf_vec(keyframes)
        
    def add_fade_out(self):
        # The code to do fades was written originally for compositors so we are using module compositorfades with some added code for filters.
        fade_default_length = PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH)
        keyframes = compositorfades.add_filter_fade_out(self.editable_property.clip, self.editable_property, self.clip_editor.keyframes, fade_default_length)
        if keyframes == None:
            return # update failed, clip probably too short
        self._update_all_for_kf_vec(keyframes)

    def _update_all_for_kf_vec(self, keyframes):
        self.editable_property.write_out_keyframes(keyframes)
        self.clip_editor.set_keyframes(self.editable_property.value, self.editable_property.get_in_value)
        self.update_editor_view()

    
class GeometryEditor(AbstractKeyFrameEditor):
    """
    GUI component that edits position, scale and opacity of a MLT property.
    """
    def __init__(self, editable_property, use_clip_in=True):
        AbstractKeyFrameEditor.__init__(self, editable_property, use_clip_in)
        self.init_geom_gui(editable_property)
        self.init_non_geom_gui()
        
    def init_geom_gui(self, editable_property):
        self.geom_kf_edit = keyframeeditcanvas.BoxEditCanvas(editable_property, self)
        self.geom_kf_edit.init_editor(current_sequence().profile.width(),
                                      current_sequence().profile.height(),
                                      GEOM_EDITOR_SIZE_MEDIUM)
        editable_property.value.strip('"')
        self.geom_kf_edit.keyframe_parser = propertyparse.geom_keyframes_value_string_to_geom_kf_array
        self.geom_kf_edit.set_keyframes(editable_property.value, editable_property.get_in_value)
    
    def init_non_geom_gui(self):
        # Create components
        self.geom_buttons_row = GeometryEditorButtonsRow(self)
        
        g_frame = Gtk.Frame()
        g_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        g_frame.add(self.geom_kf_edit.widget)
             
        self.buttons_row = ClipEditorButtonsRow(self, False, True)

        self.pos_entries_row = PositionNumericalEntries(self.geom_kf_edit, self, self.geom_buttons_row)
        
        # Create clip editor keyframes from geom editor keyframes
        # that contain the property values when opening editor.
        # From now on clip editor opacity values are used until editor is discarded.
        self.clip_editor.keyframes = self.get_clip_editor_keyframes()
      
        # Build gui
        #self.pack_start(self.geom_buttons_row, False, False, 0)
        self.pack_start(g_frame, False, False, 0)
        self.pack_start(self.pos_entries_row, False, False, 0)
        self.pack_start(guiutils.pad_label(1, 1), False, False, 0)
        self.pack_start(self.value_slider_row, False, False, 0)
        self.pack_start(self.clip_editor.widget, False, False, 0)
        self.pack_start(self.buttons_row, False, False, 0)

        orig_tline_frame = PLAYER().current_frame()
        self.active_keyframe_changed() # to do update gui to current values
                                       # This also seeks tline frame to frame 0, thus value was saved in the line above

        # If we do not want to seek to kf 0 or clip start we, need seek back to original tline frame
        self.display_tline_frame(orig_tline_frame)
        PLAYER().seek_frame(orig_tline_frame)
        
        self.queue_draw()

    def get_clip_editor_keyframes(self):
        keyframes = []
        for kf in self.geom_kf_edit.keyframes:
            frame, rect, opacity = kf
            clip_kf = (frame, opacity)
            keyframes.append(clip_kf)
        return keyframes
        
    def add_pressed(self):
        # These two have different keyframe, clip_editor only deals with opacity.
        # This because clip_editor is the same class used to keyframe edit single values
        self.clip_editor.add_keyframe(self.clip_editor.current_clip_frame)
        self.geom_kf_edit.add_keyframe(self.clip_editor.current_clip_frame)

        frame = self.clip_editor.get_active_kf_frame()
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        self.update_editor_view_with_frame(frame)
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())

    def delete_pressed(self):
        active = self.clip_editor.active_kf_index
        self.clip_editor.delete_active_keyframe()
        self.geom_kf_edit.delete_active_keyframe(active)
        
        frame = self.clip_editor.get_active_kf_frame()
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        self.update_editor_view_with_frame(frame)
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())

    def next_pressed(self):
        self.clip_editor.set_next_active()
        frame = self.clip_editor.get_active_kf_frame()
        self.update_editor_view_with_frame(frame)
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        
    def prev_pressed(self):
        self.clip_editor.set_prev_active()
        frame = self.clip_editor.get_active_kf_frame()
        self.update_editor_view_with_frame(frame)
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))

    def move_kf_next_frame_pressed(self):
        current_frame = self.clip_editor.get_active_kf_frame()
        self.clip_editor.active_kf_pos_entered(current_frame + 1)
        current_frame = self.clip_editor.get_active_kf_frame()
        self.update_property_value()
        self.update_editor_view()
        self.seek_tline_frame(current_frame)
        
    def move_kf_prev_frame_pressed(self):
        current_frame = self.clip_editor.get_active_kf_frame()
        self.clip_editor.active_kf_pos_entered(current_frame - 1)
        current_frame = self.clip_editor.get_active_kf_frame()
        self.update_property_value()
        self.update_editor_view()
        self.seek_tline_frame(current_frame)
        
    def slider_value_changed(self, adjustment):
        value = adjustment.get_value()
        self.clip_editor.set_active_kf_value(value)
        self.update_property_value()

    def get_copy_kf_value(self):
         return self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index)
         
    def paste_kf_value(self, value_data):
        frame, rect, opacity = value_data
        self.clip_editor.set_active_kf_value(opacity)
        self.geom_kf_edit.set_keyframe_to_edit_shape(self.clip_editor.active_kf_index, rect)
        self.update_property_value()
        self.update_editor_view()
        
    def add_fade_in(self):
        compositor = _get_current_edited_compositor()
        fade_default_length = PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH)
        keyframes = compositorfades.add_fade_in(compositor, fade_default_length) # updates editable_property.value. Remove fade length hardcoding in 2.4
        if keyframes == None:
            return # update failed, clip probably too short
        self._update_all_for_kf_vec(keyframes)
                
    def add_fade_out(self):
        compositor = _get_current_edited_compositor()
        fade_default_length = PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH)
        keyframes = compositorfades.add_fade_out(compositor, fade_default_length)
        if keyframes == None:
            return # update failed, clip probably too short
        self._update_all_for_kf_vec(keyframes)

    def _update_all_for_kf_vec(self, keyframes):
        self.editable_property.write_out_keyframes(keyframes)
        self.geom_kf_edit.set_keyframes(self.editable_property.value, self.editable_property.get_in_value)
        self.clip_editor.keyframes = self.get_clip_editor_keyframes()
        self.clip_editor.widget.queue_draw()
        self.update_editor_view()

    def view_size_changed(self, selected_index):
        y_fract = GEOM_EDITOR_SIZES[selected_index]
        self.geom_kf_edit.set_view_size(y_fract)
        self.update_editor_view_with_frame(self.clip_editor.current_clip_frame)
        
    def clip_editor_frame_changed(self, frame):
        self.update_editor_view_with_frame(frame)
    
    def prev_frame_pressed(self):
        self.clip_editor.move_clip_frame(-1)
        self.update_editor_view(True)

    def next_frame_pressed(self):
        self.clip_editor.move_clip_frame(1)
        self.update_editor_view(True)

    def geometry_edit_started(self): # callback from geom_kf_edit
        self.clip_editor.add_keyframe(self.clip_editor.current_clip_frame)
        self.geom_kf_edit.add_keyframe(self.clip_editor.current_clip_frame)
        
    def geometry_edit_finished(self): # callback from geom_kf_edit
        self.geom_kf_edit.set_keyframe_to_edit_shape(self.clip_editor.active_kf_index)
        self.update_editor_view_with_frame(self.clip_editor.current_clip_frame)
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))

    def numerical_edit_done(self, new_shape):
        # Callback from PositionNumericalEntries
        self.geom_kf_edit.set_keyframe_to_edit_shape(self.clip_editor.active_kf_index, new_shape)
        self.update_editor_view_with_frame(self.clip_editor.current_clip_frame)
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        
    def arrow_edit(self, keyval, CTRL_DOWN, SHIFT_DOWN):
        if CTRL_DOWN:
            delta = 10
        else:
            delta = 1
        
        if SHIFT_DOWN == False: # Move 
            self.geom_kf_edit.handle_arrow_edit(keyval, delta)
        else: # Scale
            self.geom_kf_edit.handle_arrow_scale_edit(keyval, delta)
            
        self.geom_kf_edit.set_keyframe_to_edit_shape(self.clip_editor.active_kf_index)
        self.update_editor_view_with_frame(self.clip_editor.current_clip_frame)
        self.update_property_value()
        
    def update_request_from_geom_editor(self): # callback from geom_kf_edit
        self.update_editor_view_with_frame(self.clip_editor.current_clip_frame)
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))

    def keyframe_dragged(self, active_kf, frame):
        self.geom_kf_edit.set_keyframe_frame(active_kf, frame)
        
    def active_keyframe_changed(self): # callback from clip_editor
        kf_frame = self.clip_editor.get_active_kf_frame()
        self.update_editor_view_with_frame(kf_frame)
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        # we need active index from clip_editor and geometry values from geom_kf_edit to update numerical entries
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
         
    def _reset_rect_pressed(self):
        self.geom_kf_edit.reset_active_keyframe_shape(self.clip_editor.active_kf_index)
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        frame = self.clip_editor.get_active_kf_frame()
        self.update_editor_view_with_frame(frame)
        self.update_property_value()

    def _reset_rect_ratio_pressed(self):
        self.geom_kf_edit.reset_active_keyframe_rect_shape(self.clip_editor.active_kf_index)
        frame = self.clip_editor.get_active_kf_frame()
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        self.update_editor_view_with_frame(frame)
        self.update_property_value()

    def _center_horizontal(self):
        self.geom_kf_edit.center_h_active_keyframe_shape(self.clip_editor.active_kf_index)
        frame = self.clip_editor.get_active_kf_frame()
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        self.update_editor_view_with_frame(frame)
        self.update_property_value()

    def _center_vertical(self):
        self.geom_kf_edit.center_v_active_keyframe_shape(self.clip_editor.active_kf_index)
        frame = self.clip_editor.get_active_kf_frame()
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        self.update_editor_view_with_frame(frame)
        self.update_property_value()
            
    def menu_item_activated(self, widget, data):
        if data == "reset":
            self._reset_rect_pressed()
        elif data == "ratio":
            self._reset_rect_ratio_pressed()
        elif data == "hcenter":
            self._center_horizontal()
        elif data == "vcenter":
            self._center_vertical()

    def update_editor_view(self, seek_tline_frame=False):
        # This gets called when tline frame is changed from outside
        # Call update_editor_view_with_frame that is used when udating from inside the object.
        # seek_tline_frame will be False to stop endless loop of updates
        frame = self.clip_editor.current_clip_frame
        self.update_editor_view_with_frame(frame, seek_tline_frame)

    def update_editor_view_with_frame(self, frame, seek_tline_frame=True):
        self.update_slider_value_display(frame)
        self.geom_kf_edit.set_clip_frame(frame)
        self.buttons_row.set_frame(frame)
        if seek_tline_frame == True:
            self.seek_tline_frame(frame)
        self.queue_draw()

    def seek_tline_frame(self, clip_frame):
        PLAYER().seek_frame(self.clip_tline_pos + clip_frame)

    def update_property_value(self):
        if self.initializing:
            return

        write_keyframes = []
        for opa_kf, geom_kf in zip(self.clip_editor.keyframes, self.geom_kf_edit.keyframes):
            frame, opacity = opa_kf
            frame, rect, rubbish_opacity = geom_kf # rubbish_opacity was just doing same thing twice for nothing,
                                                   # and can be removed to clean up code, but could not bothered right now
            write_keyframes.append((frame, rect, opacity))
        
        self.editable_property.write_out_keyframes(write_keyframes)
        
    def mouse_scroll_up(self):
        view_size_index = self.geom_buttons_row.size_select.get_active()
        view_size_index = view_size_index - 1
        if view_size_index < 0:
            view_size_index = 0
        self.geom_buttons_row.size_select.set_active(view_size_index)

    def mouse_scroll_down(self):
        view_size_index = self.geom_buttons_row.size_select.get_active()
        view_size_index = view_size_index + 1
        if view_size_index > 2:
            view_size_index = 2
        self.geom_buttons_row.size_select.set_active(view_size_index)


class RotatingGeometryEditor(GeometryEditor):

    def init_geom_gui(self, editable_property):
        self.geom_kf_edit = keyframeeditcanvas.RotatingEditCanvas(editable_property, self)
        self.geom_kf_edit.init_editor(current_sequence().profile.width(),
                                      current_sequence().profile.height(),
                                      GEOM_EDITOR_SIZE_MEDIUM)
        self.geom_kf_edit.create_edit_points_and_values()
        editable_property.value.strip('"')
        self.geom_kf_edit.keyframe_parser = propertyparse.rotating_geom_keyframes_value_string_to_geom_kf_array
        self.geom_kf_edit.set_keyframes(editable_property.value, editable_property.get_in_value)

    def add_fade_in(self):
        compositor = _get_current_edited_compositor()
        fade_default_length = PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH)
        keyframes = compositorfades.add_fade_in(compositor, fade_default_length) # updates editable_property.value. Remove fade length hardcoding in 2.4
        if keyframes == None:
            return # update failed, clip probably too short
        self._update_all_for_kf_vec(keyframes)
                
    def add_fade_out(self):
        compositor = _get_current_edited_compositor()
        fade_default_length = PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH)
        keyframes = compositorfades.add_fade_out(compositor, fade_default_length) # updates editable_property.value. Remove fade length hardcoding in 2.4
        if keyframes == None:
            return # update failed, clip probably too short
        self._update_all_for_kf_vec(keyframes)

    def _update_all_for_kf_vec(self, keyframes):
        self.editable_property.write_out_keyframes(keyframes)
        self.editable_property.update_prop_value()
        self.geom_kf_edit.set_keyframes(self.editable_property.value, self.editable_property.get_in_value)
        self.clip_editor.keyframes = self.get_clip_editor_keyframes()
        self.clip_editor.widget.queue_draw()
        self.update_editor_view()


class FilterRectGeometryEditor(AbstractKeyFrameEditor):

    def __init__(self, editable_property, use_clip_in=True):
        AbstractKeyFrameEditor.__init__(self, editable_property, use_clip_in)
        self.init_geom_gui(editable_property)
        self.init_non_geom_gui()

    def init_geom_gui(self, editable_property):
        self.geom_kf_edit = keyframeeditcanvas.BoxEditCanvas(editable_property, self)
        self.geom_kf_edit.init_editor(current_sequence().profile.width(),
                                      current_sequence().profile.height(),
                                      GEOM_EDITOR_SIZE_MEDIUM)
        editable_property.value.strip('"')
        self.geom_kf_edit.keyframe_parser = propertyparse.rect_keyframes_value_string_to_geom_kf_array
        self.geom_kf_edit.set_keyframes(editable_property.value, editable_property.get_in_value)
    
    def init_non_geom_gui(self):
        # Create components
        self.geom_buttons_row = GeometryEditorButtonsRow(self, True)
        
        g_frame = Gtk.Frame()
        g_frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        g_frame.add(self.geom_kf_edit.widget)
             
        self.buttons_row = ClipEditorButtonsRow(self, True, False)

        self.pos_entries_row = PositionNumericalEntries(self.geom_kf_edit, self, None)
        
        # Create clip editor keyframes from geom editor keyframes
        # that contain the property values when opening editor.
        # From now on clip editor opacity values are used until editor is discarded.
        self.clip_editor.keyframes = self.get_clip_editor_keyframes()
      
        # Build gui
        self.pack_start(g_frame, False, False, 0)
        self.pack_start(self.geom_buttons_row, False, False, 0)
        self.pack_start(self.pos_entries_row, False, False, 0)
        self.pack_start(self.clip_editor.widget, False, False, 0)
        self.pack_start(self.buttons_row, False, False, 0)

        orig_tline_frame = PLAYER().current_frame()

        self.clip_editor.add_keyframe(self.clip_editor.current_clip_frame)
        self.geom_kf_edit.add_keyframe(self.clip_editor.current_clip_frame)
        
        self.active_keyframe_changed() # to do update gui to current values
                                       # This also seeks tline frame to frame 0, thus value was saved in the line above

        # If we do not want to seek to kf 0 or clip start we, need seek back to original tline frame
        self.display_tline_frame(orig_tline_frame)
        PLAYER().seek_frame(orig_tline_frame)
            
        self.queue_draw()
        
    def active_keyframe_changed(self):
        kf_frame = self.clip_editor.get_active_kf_frame()
        self.update_editor_view_with_frame(kf_frame)
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        # we need active index from clip_editor and geometry values from geom_kf_edit to update numerical entries
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        
    def clip_editor_frame_changed(self, clip_frame):
        self.seek_tline_frame(clip_frame)
        self.buttons_row.set_frame(clip_frame)

    def add_pressed(self):
        self.clip_editor.add_keyframe(self.clip_editor.current_clip_frame)
        self.geom_kf_edit.add_keyframe(self.clip_editor.current_clip_frame)
        
        frame = self.clip_editor.get_active_kf_frame()
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        self.update_editor_view_with_frame(frame)
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        
    def delete_pressed(self):
        self.clip_editor.delete_active_keyframe()
        self.update_editor_view()
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())

    def get_copy_kf_value(self):
        return self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index)
         
    def paste_kf_value(self, value_data):
        frame, rect, opacity = value_data
        self.clip_editor.set_active_kf_value(opacity)
        self.geom_kf_edit.set_keyframe_to_edit_shape(self.clip_editor.active_kf_index, rect)
        self.update_property_value()
        self.update_editor_view()
        
    def next_pressed(self):
        self.clip_editor.set_next_active()
        self.update_editor_view()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        
    def prev_pressed(self):
        self.clip_editor.set_prev_active()
        self.update_editor_view()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())

    def prev_frame_pressed(self):
        self.clip_editor.move_clip_frame(-1)
        self.update_editor_view()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        
    def next_frame_pressed(self):
        self.clip_editor.move_clip_frame(1)
        self.update_editor_view()

    def move_kf_next_frame_pressed(self):
        current_frame = self.clip_editor.get_active_kf_frame()
        self.clip_editor.active_kf_pos_entered(current_frame + 1)
        self.update_property_value()
        self.update_editor_view()

    def move_kf_prev_frame_pressed(self):
        current_frame = self.clip_editor.get_active_kf_frame()
        self.clip_editor.active_kf_pos_entered(current_frame - 1)
        self.update_property_value()
        self.update_editor_view()

    def slider_value_changed(self, adjustment):
        print (adjustment)

    def get_clip_editor_keyframes(self):
        keyframes = []
        for kf in self.geom_kf_edit.keyframes:
            frame, rect, opacity = kf
            clip_kf = (frame, opacity)
            keyframes.append(clip_kf)
        return keyframes

    def view_size_changed(self, selected_index):
        y_fract = GEOM_EDITOR_SIZES[selected_index]
        self.geom_kf_edit.set_view_size(y_fract)
        self.update_editor_view_with_frame(self.clip_editor.current_clip_frame)
        
    def geometry_edit_started(self): # callback from geom_kf_edit
        self.clip_editor.add_keyframe(self.clip_editor.current_clip_frame)
        self.geom_kf_edit.add_keyframe(self.clip_editor.current_clip_frame)

    def geometry_edit_finished(self): # callback from geom_kf_edit
        self.geom_kf_edit.set_keyframe_to_edit_shape(self.clip_editor.active_kf_index)
        self.update_editor_view_with_frame(self.clip_editor.current_clip_frame)
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))

    def numerical_edit_done(self, new_shape):
        # Callback from PositionNumericalEntries
        self.geom_kf_edit.set_keyframe_to_edit_shape(self.clip_editor.active_kf_index, new_shape)
        self.update_editor_view_with_frame(self.clip_editor.current_clip_frame)
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        
    def update_request_from_geom_editor(self): # callback from geom_kf_edit
        self.update_editor_view_with_frame(self.clip_editor.current_clip_frame)
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
    
    def keyframe_dragged(self, active_kf, frame):
        self.geom_kf_edit.set_keyframe_frame(active_kf, frame)

    def menu_item_activated(self, widget, data):
        if data == "reset":
            self._reset_rect_pressed()
        elif data == "ratio":
            self._reset_rect_ratio_pressed()
        elif data == "hcenter":
            self._center_horizontal()
        elif data == "vcenter":
            self._center_vertical()

    def _reset_rect_pressed(self):
        self.geom_kf_edit.reset_active_keyframe_shape(self.clip_editor.active_kf_index)
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        frame = self.clip_editor.get_active_kf_frame()
        self.update_editor_view_with_frame(frame)
        self.update_property_value()

    def _reset_rect_ratio_pressed(self):
        self.geom_kf_edit.reset_active_keyframe_rect_shape(self.clip_editor.active_kf_index)
        frame = self.clip_editor.get_active_kf_frame()
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        self.update_editor_view_with_frame(frame)
        self.update_property_value()

    def _center_horizontal(self):
        self.geom_kf_edit.center_h_active_keyframe_shape(self.clip_editor.active_kf_index)
        frame = self.clip_editor.get_active_kf_frame()
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        self.update_editor_view_with_frame(frame)
        self.update_property_value()

    def _center_vertical(self):
        self.geom_kf_edit.center_v_active_keyframe_shape(self.clip_editor.active_kf_index)
        frame = self.clip_editor.get_active_kf_frame()
        self.pos_entries_row.update_entry_values(self.geom_kf_edit.get_keyframe(self.clip_editor.active_kf_index))
        self.update_editor_view_with_frame(frame)
        self.update_property_value()

    def update_editor_view(self, seek_tline_frame=True):
        # This gets called when tline frame is changed from outside
        # Call update_editor_view_with_frame that is used when udating from inside the object.
        # seek_tline_frame will be False to stop endless loop of updates
        frame = self.clip_editor.current_clip_frame
        self.update_editor_view_with_frame(frame, seek_tline_frame)

    def update_editor_view_with_frame(self, frame, seek_tline_frame=True):
        self.update_slider_value_display(frame)
        self.geom_kf_edit.set_clip_frame(frame)
        self.buttons_row.set_frame(frame)
        if seek_tline_frame == True:
            self.seek_tline_frame(frame)
        self.queue_draw()

    def update_property_value(self):
        if self.initializing:
            return

        write_keyframes = []
        for opa_kf, geom_kf in zip(self.clip_editor.keyframes, self.geom_kf_edit.keyframes):
            frame, opacity = opa_kf
            frame, rect, rubbish_opacity = geom_kf
            
            write_keyframes.append((frame, rect, opacity))
        
        self.editable_property.write_out_keyframes(write_keyframes)

class RotoMaskKeyFrameEditor(Gtk.VBox):
    """
    Class combines named value slider with ClipKeyFrameEditor and 
    control buttons to create keyframe editor for a single keyframed
    numerical value property. 
    """
    def __init__(self, editable_property, keyframe_parser):
        GObject.GObject.__init__(self)
        self.initializing = True # izneeded?!?

        use_clip_in = True
        
        self.set_homogeneous(False)
        self.set_spacing(2)
        
        self.editable_property = editable_property
        self.clip_tline_pos = editable_property.get_clip_tline_pos()

        self.clip_editor = ClipKeyFrameEditor(editable_property, self, use_clip_in)
        self.clip_editor.mouse_listener = self
        """
        Callbacks from ClipKeyFrameEditor:
            def clip_editor_frame_changed(self, frame)
            def active_keyframe_changed(self)
            def keyframe_dragged(self, active_kf, frame)
            def update_slider_value_display(self, frame)
        
        Via clip_editor.mouse_listener
            def mouse_pos_change_done(self)
        """
        
        # Some filters start keyframes from *MEDIA* frame 0
        # Some filters or compositors start keyframes from *CLIP* frame 0
        # Filters starting from *media* 0 need offset to clip start added to all values
        self.use_clip_in = use_clip_in
        if self.use_clip_in == True:
            self.clip_in = editable_property.clip.clip_in
        else:
            self.clip_in = 0
    
        self.initializing = False # Hack against too early for on slider listner
        
        self.clip_editor.keyframe_parser = keyframe_parser
            
        editable_property.value.strip('"') # This has been an issue sometimes
         
        self.clip_editor.set_keyframes(editable_property.value, editable_property.get_in_value)
        clip_editor_row = Gtk.HBox(False, 0)
        clip_editor_row.pack_start(self.clip_editor.widget, True, True, 0)
        clip_editor_row.pack_start(guiutils.pad_label(4, 4), False, False, 0)
        
        self.buttons_row = ClipEditorButtonsRow(self, True, False)
        
        self.pack_start(clip_editor_row, False, False, 0)
        self.pack_start(self.buttons_row, False, False, 0)

        self.set_editor_sensitive(False)

    def set_parent_editor(self, parent):
        # parent implements callback:
        #      parent.update_view(timeline_frame)
        self.parent = parent

    def active_keyframe_changed(self):
        frame = self.clip_editor.current_clip_frame
        keyframes = self.clip_editor.keyframes
        value = _get_frame_value(frame, keyframes)
        self.buttons_row.set_frame(frame)
        self.seek_tline_frame(frame)
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.parent.update_view()

    def update_slider_value_display(self, clip_frame):
        # we don't have slider but this gets called from ClipKeyFrameEditor
        pass
    
    def mouse_pos_change_done(self):
        # we make ClipKeyFrameEditor call this to update parent view
        self.parent.update_view()
        
    def clip_editor_frame_changed(self, clip_frame):
        self.seek_tline_frame(clip_frame)
        self.buttons_row.set_frame(clip_frame)

    def add_pressed(self):
        self.clip_editor.add_keyframe(self.clip_editor.current_clip_frame)
        self.update_editor_view()
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.parent.update_view()
        self.parent.update_effects_editor_value_labels()
        
    def delete_pressed(self):
        self.clip_editor.delete_active_keyframe()
        self.update_editor_view()
        self.update_property_value()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.parent.update_view()
        self.parent.update_effects_editor_value_labels()

    def next_pressed(self):
        self.clip_editor.set_next_active()
        self.update_editor_view()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.parent.update_view()
        
    def prev_pressed(self):
        self.clip_editor.set_prev_active()
        self.update_editor_view()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.parent.update_view()
        
    def prev_frame_pressed(self):
        self.clip_editor.move_clip_frame(-1)
        self.update_editor_view()
        self.buttons_row.set_kf_info(self.clip_editor.get_kf_info())
        self.parent.update_view()
        
    def next_frame_pressed(self):
        self.clip_editor.move_clip_frame(1)
        self.update_editor_view()
        self.parent.update_view()
                
    def move_kf_next_frame_pressed(self):
        current_frame = self.clip_editor.get_active_kf_frame()
        self.clip_editor.active_kf_pos_entered(current_frame + 1)
        self.update_property_value()
        self.update_editor_view()
        self.parent.update_view()
            
    def move_kf_prev_frame_pressed(self):
        current_frame = self.clip_editor.get_active_kf_frame()
        self.clip_editor.active_kf_pos_entered(current_frame - 1)
        self.update_property_value()
        self.update_editor_view()
        self.parent.update_view()
            
    def keyframe_dragged(self, active_kf, frame):
        pass

    def update_editor_view(self, seek_tline=True):
        frame = self.clip_editor.current_clip_frame
        keyframes = self.clip_editor.keyframes
        value = _get_frame_value(frame, keyframes)
        self.buttons_row.set_frame(frame)
        if seek_tline == True:
            self.seek_tline_frame(frame)
        self.queue_draw()

    def update_property_value(self):
        self.editable_property.write_out_keyframes(self.clip_editor.keyframes)

    def display_tline_frame(self, tline_frame):
        # This is called after timeline current frame changed. 
        # If timeline pos changed because drag is happening _here_,
        # updating once more is wrong
        if self.clip_editor.drag_on == True:
            return

        # update clipeditor pos
        clip_frame = tline_frame - self.clip_tline_pos + self.clip_in
        self.clip_editor.set_and_display_clip_frame(clip_frame)
        self.update_editor_view(False)
    
    def update_clip_pos(self):
        # This is called after position of clip has been edited.
        # We'll need to update some values to get keyframes on correct positions again
        self.editable_property.update_clip_index()
        self.clip_tline_pos = self.editable_property.get_clip_tline_pos()
        if self.use_clip_in == True:
            self.clip_in = self.editable_property.clip.clip_in
        else:
            self.clip_in = 0
        self.clip_editor.clip_in = self.editable_property.clip.clip_in
        self.clip_editor.widget.queue_draw()

    def seek_tline_frame(self, clip_frame):
        PLAYER().seek_frame(self.clip_tline_pos + clip_frame - self.clip_in)
    
    def set_editor_sensitive(self, sensitive):
        self.buttons_row.set_buttons_sensitive(sensitive)
        self.clip_editor.set_sensitive(sensitive)
        self.clip_editor.widget.queue_draw()


# ----------------------------------------------------------------- POSITION NUMERICAL ENTRY WIDGET
class PositionNumericalEntries(Gtk.HBox):
    
    def __init__(self, geom_editor, parent_editor, editor_buttons):
        GObject.GObject.__init__(self)

        self.parent_editor = parent_editor
        
        if isinstance(geom_editor, keyframeeditcanvas.RotatingEditCanvas):
            self.rotating_geom = True
            self.init_for_roto_geom(editor_buttons)
        else:
            self.rotating_geom = False
            self.init_for_box_geom(editor_buttons)     

    def init_for_box_geom(self, editor_buttons):
        x_label = Gtk.Label(_("X:"))
        y_label = Gtk.Label(_("Y:"))
        w_label = Gtk.Label(_("Width:"))
        h_label = Gtk.Label(_("Height:"))
        
        self.x_entry = Gtk.Entry.new()
        self.y_entry = Gtk.Entry.new()
        self.w_entry = Gtk.Entry.new()
        self.h_entry = Gtk.Entry.new()
        
        self.prepare_entry(self.x_entry)
        self.prepare_entry(self.y_entry)
        self.prepare_entry(self.w_entry)
        self.prepare_entry(self.h_entry)
        
        self.set_homogeneous(False)
        self.set_spacing(2)
        self.set_margin_top (4)

        if editor_buttons != None: # We smetimes put editor buttons elsewhere
            self.pack_start(editor_buttons, False, False, 0)
            
        self.pack_start(Gtk.Label(), True, True, 0)
        self.pack_start(x_label, False, False, 0)
        self.pack_start(self.x_entry, False, False, 0)
        self.pack_start(guiutils.pad_label(6, 6), False, False, 0)
        self.pack_start(y_label, False, False, 0)
        self.pack_start(self.y_entry, False, False, 0)
        self.pack_start(guiutils.pad_label(6, 6), False, False, 0)
        self.pack_start(w_label, False, False, 0)
        self.pack_start(self.w_entry, False, False, 0)
        self.pack_start(guiutils.pad_label(6, 6), False, False, 0)
        self.pack_start(h_label, False, False, 0)
        self.pack_start(self.h_entry, False, False, 0)
        self.pack_start(Gtk.Label(), True, True, 0)
        
    def init_for_roto_geom(self, editor_buttons):
        # [960.0, 540.0, 1.0, 1.0, 0.0]

        x_label = Gtk.Label(_("X:"))
        y_label = Gtk.Label(_("Y:"))
        x_scale_label = Gtk.Label(_("X scale:"))
        y_scale_label = Gtk.Label(_("Y scale:"))
        rotation_label = Gtk.Label(_("Rotation:"))
        
        self.x_entry = Gtk.Entry.new()
        self.y_entry = Gtk.Entry.new()
        self.x_scale_entry = Gtk.Entry.new()
        self.y_scale_entry = Gtk.Entry.new()
        self.rotation_entry = Gtk.Entry.new()
        
        self.prepare_entry(self.x_entry)
        self.prepare_entry(self.y_entry)
        self.prepare_entry(self.x_scale_entry)
        self.prepare_entry(self.y_scale_entry)
        self.prepare_entry(self.rotation_entry)
        
        self.set_homogeneous(False)
        self.set_spacing(2)
        self.set_margin_top (4)

        if editor_buttons != None: # We smetimes put editor buttons elsewhere
            self.pack_start(editor_buttons, False, False, 0)
            
        self.pack_start(Gtk.Label(), True, True, 0)
        self.pack_start(x_label, False, False, 0)
        self.pack_start(self.x_entry, False, False, 0)
        self.pack_start(guiutils.pad_label(6, 6), False, False, 0)
        self.pack_start(y_label, False, False, 0)
        self.pack_start(self.y_entry, False, False, 0)
        self.pack_start(guiutils.pad_label(6, 6), False, False, 0)
        self.pack_start(x_scale_label, False, False, 0)
        self.pack_start(self.x_scale_entry, False, False, 0)
        self.pack_start(guiutils.pad_label(6, 6), False, False, 0)
        self.pack_start(y_scale_label, False, False, 0)
        self.pack_start(self.y_scale_entry, False, False, 0)
        self.pack_start(guiutils.pad_label(6, 6), False, False, 0)
        self.pack_start(rotation_label, False, False, 0)
        self.pack_start(self.rotation_entry, False, False, 0)
        self.pack_start(guiutils.pad_label(1, 6), False, False, 0)
        if editor_buttons != None: # We smetimes put editor buttons elsewhere
            self.pack_start(guiutils.pad_label(1, 6), False, False, 0)
        else:
            self.pack_start(Gtk.Label(), True, True, 0)

    def prepare_entry(self, entry):
        entry.set_width_chars (4)
        entry.set_max_length (4)
        entry.set_max_width_chars (4)
        entry.connect("activate", self.enter_pressed)
        
    def enter_pressed(self, entry):
        if self.rotating_geom == True:
            try:
                x = float(self.x_entry.get_text())
                y = float(self.y_entry.get_text())
                xs = float(self.x_scale_entry.get_text())
                ys = float(self.y_scale_entry.get_text())
                rot = float(self.rotation_entry.get_text())
                shape = [x, y, xs, ys, rot]
                self.parent_editor.numerical_edit_done(shape)
            except Exception as e:
                # If user inputs non-ifloats we will just do nothing
                print("Numerical input Exception - ", e)
        else:
            try:
                x = float(self.x_entry.get_text())
                y = float(self.y_entry.get_text())
                w = float(self.w_entry.get_text())
                h = float(self.h_entry.get_text())
                shape = [x, y, w, h]
                self.parent_editor.numerical_edit_done(shape)
            except Exception as e:
                # If user inputs non-ifloats we will just do nothing
                print("Numerical input Exception - ", e)

    def update_entry_values(self, active_kf):
        frame, shape, opacity = active_kf

        if self.rotating_geom == False:
            x, y, w, h = shape
            self.x_entry.set_text(str(x))
            self.y_entry.set_text(str(y))
            self.w_entry.set_text(str(w))
            self.h_entry.set_text(str(h))
        else:
            x, y, xs, ys, rot = shape
            self.x_entry.set_text(str(x))
            self.y_entry.set_text(str(y))
            self.x_scale_entry.set_text(str(xs))
            self.y_scale_entry.set_text(str(ys))
            self.rotation_entry.set_text(str(rot))




# ----------------------------------------------------------------- linear interpolation
def _get_frame_value(frame, keyframes):
    for i in range(0, len(keyframes)):
        kf_frame, kf_value = keyframes[i]
        if kf_frame == frame:
            return kf_value
        
        try:
            # See if frame between this and next keyframe
            frame_n, value_n = keyframes[i + 1]
            if ((kf_frame < frame)
                and (frame < frame_n)):
                time_fract = float((frame - kf_frame)) / float((frame_n - kf_frame))
                value_range = value_n - kf_value
                return kf_value + time_fract * value_range
        except: # past last frame, use its value
            return kf_value
   
