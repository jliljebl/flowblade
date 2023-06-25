"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2023 Janne Liljeblad.

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
Module handles creating and changing tool cursors.
It is also part of edit mode changing callstack.
"""


from gi.repository import Gdk

import cairo

import appconsts
import boxmove
import editorstate
import editorpersistance
import gui
import guiutils
import modesetting
import respaths
import tlineaction
import tlinewidgets
import workflow
import updater

# Cursors
OVERWRITE_CURSOR = None
OVERWRITE_BOX_CURSOR = None
INSERTMOVE_CURSOR = None
ONEROLL_CURSOR = None
ONEROLL_NO_EDIT_CURSOR = None
TWOROLL_CURSOR = None
TWOROLL_NO_EDIT_CURSOR = None
SLIDE_CURSOR = None
SLIDE_NO_EDIT_CURSOR = None
MULTIMOVE_CURSOR = None
ONEROLL_RIPPLE_CURSOR = None
CUT_CURSOR = None
KF_TOOL_CURSOR = None
MULTI_TRIM_CURSOR = None

ONEROLL_TOOL = None
OVERWRITE_TOOL = None


class TLineCursorManager:

    def __init__(self):

        self._init_cursors()

    def _init_cursors(self):
        # Read cursors
        global INSERTMOVE_CURSOR, OVERWRITE_CURSOR, TWOROLL_CURSOR, ONEROLL_CURSOR, \
        ONEROLL_NO_EDIT_CURSOR, TWOROLL_NO_EDIT_CURSOR, SLIDE_CURSOR, SLIDE_NO_EDIT_CURSOR, \
        MULTIMOVE_CURSOR, MULTIMOVE_NO_EDIT_CURSOR, ONEROLL_RIPPLE_CURSOR, ONEROLL_TOOL, \
        OVERWRITE_BOX_CURSOR, OVERWRITE_TOOL, CUT_CURSOR, KF_TOOL_CURSOR, MULTI_TRIM_CURSOR

        # Aug-2019 - SvdB - BB
        INSERTMOVE_CURSOR = guiutils.get_cairo_image("insertmove_cursor")
        OVERWRITE_CURSOR = guiutils.get_cairo_image("overwrite_cursor")
        OVERWRITE_BOX_CURSOR = guiutils.get_cairo_image("overwrite_cursor_box")
        TWOROLL_CURSOR = guiutils.get_cairo_image("tworoll_cursor")
        SLIDE_CURSOR = guiutils.get_cairo_image("slide_cursor")
        ONEROLL_CURSOR = guiutils.get_cairo_image("oneroll_cursor")
        ONEROLL_NO_EDIT_CURSOR = guiutils.get_cairo_image("oneroll_noedit_cursor")
        TWOROLL_NO_EDIT_CURSOR = guiutils.get_cairo_image("tworoll_noedit_cursor")
        SLIDE_NO_EDIT_CURSOR = guiutils.get_cairo_image("slide_noedit_cursor")
        MULTIMOVE_CURSOR = guiutils.get_cairo_image("multimove_cursor")
        MULTIMOVE_NO_EDIT_CURSOR = guiutils.get_cairo_image("multimove_cursor")
        ONEROLL_TOOL = guiutils.get_cairo_image("oneroll_tool")
        ONEROLL_RIPPLE_CURSOR = guiutils.get_cairo_image("oneroll_cursor_ripple")
        OVERWRITE_TOOL = guiutils.get_cairo_image("overwrite_tool")
        CUT_CURSOR = guiutils.get_cairo_image("cut_cursor")
        KF_TOOL_CURSOR = guiutils.get_cairo_image("kftool_cursor")
        MULTI_TRIM_CURSOR = guiutils.get_cairo_image("multitrim_cursor")

        # Context cursors
        self.context_cursors = {appconsts.POINTER_CONTEXT_END_DRAG_LEFT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_left.png"), 3, 7),
                                appconsts.POINTER_CONTEXT_END_DRAG_RIGHT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_right.png"), 14, 7),
                                appconsts.POINTER_CONTEXT_TRIM_LEFT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_trim_left.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_TRIM_RIGHT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_trim_right.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_BOX_SIDEWAYS:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_sideways.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_COMPOSITOR_MOVE:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_sideways.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_COMPOSITOR_END_DRAG_LEFT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_left.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_COMPOSITOR_END_DRAG_RIGHT:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "ctx_drag_right.png"), 9, 9),
                                appconsts.POINTER_CONTEXT_MULTI_ROLL:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "tworoll_cursor.png"), 11, 9),
                                appconsts.POINTER_CONTEXT_MULTI_SLIP:(cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "slide_cursor.png"), 9, 9)}

    # --------------------------------------------------------- EDIT TOOL AND CURSOR CHANGE HANDLING
    def set_default_edit_tool(self):
        # First active tool is the default tool. So we need to always have atleast one tool available.
        self.change_tool(editorpersistance.prefs.active_tools[0])
        # Update paths for tool selector and tool dock are unfortunately a bit different.
        if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_LEFT_DOCK:
            workflow.set_default_tool_dock_item_selected()

    def kf_tool_exit_to_mode(self, mode): # Kf tool can be entered from popup menu and it exists to mode it was started in.
        tool_id = None
        if mode == editorstate.INSERT_MOVE:
            tool_id = appconsts.TLINE_TOOL_INSERT
        elif mode == editorstate.OVERWRITE_MOVE:
            if editorstate.overwrite_mode_box == False:
                tool_id = appconsts.TLINE_TOOL_OVERWRITE
            else:
                tool_id = appconsts.TLINE_TOOL_BOX
        elif mode == editorstate.ONE_ROLL_TRIM or mode == editorstate.ONE_ROLL_TRIM_NO_EDIT:
            if editorstate.trim_mode_ripple == False: # this was not touched on entering KF tool
                tool_id = appconsts.TLINE_TOOL_TRIM
            else:
                tool_id = appconsts.TLINE_TOOL_RIPPLE_TRIM
        elif mode == editorstate.TWO_ROLL_TRIM or mode == editorstate.TWO_ROLL_TRIM_NO_EDIT:
            tool_id = appconsts.TLINE_TOOL_ROLL
        elif mode == editorstate.SLIDE_TRIM or mode == editorstate.SLIDE_TRIM_NO_EDIT:
            tool_id = appconsts.TLINE_TOOL_SLIP
        elif mode == editorstate.MULTI_MOVE:
            tool_id = appconsts.TLINE_TOOL_SPACER
        elif mode == editorstate.CUT:
            tool_id = appconsts.TLINE_TOOL_CUT
        elif mode == editorstate.KF_TOOL:
            tool_id = appconsts.TLINE_TOOL_KFTOOL
        elif mode == editorstate.MULTI_TRIM:
            tool_id = appconsts.TLINE_TOOL_MULTI_TRIM
        if tool_id != None:
            self.change_tool(tool_id)
        else:
            print("kf_tool_exit_to_mode(): NO TOOL_ID!") # This should not happen, but lets print info instead of crashing if we get here

    def change_tool(self, tool_id):
        if tool_id == appconsts.TLINE_TOOL_INSERT:
            self.handle_insert_move_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_OVERWRITE:
            self.handle_over_move_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_TRIM:
            self.handle_one_roll_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_ROLL:
            self.handle_two_roll_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_SLIP:
            self.handle_slide_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_SPACER:
            self.handle_multi_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_BOX:
            self.handle_box_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_RIPPLE_TRIM:
            self.handle_one_roll_ripple_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_CUT:
            self.handle_cut_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_KFTOOL:
            self.handle_kftool_mode_button_press()
        elif tool_id == appconsts.TLINE_TOOL_MULTI_TRIM:
            self.handle_multitrim_mode_button_press()
        else:
            # We should not hit this.
            print("editorwindow.change_tool() else: hit!")
            return
            
        if hasattr(self, "tool_selector"):
            self.set_tool_selector_to_mode(self.tool_selector)

    def handle_over_move_mode_button_press(self):
        modesetting.overwrite_move_mode_pressed()
        self.set_cursor_to_mode()

    def handle_box_mode_button_press(self):
        modesetting.box_mode_pressed()
        self.set_cursor_to_mode()

    def handle_insert_move_mode_button_press(self):
        modesetting.insert_move_mode_pressed()
        self.set_cursor_to_mode()

    def handle_one_roll_mode_button_press(self):
        editorstate.trim_mode_ripple = False
        modesetting.oneroll_trim_no_edit_init()
        self.set_cursor_to_mode()

    def handle_one_roll_ripple_mode_button_press(self):
        editorstate.trim_mode_ripple = True
        modesetting.oneroll_trim_no_edit_init()
        self.set_cursor_to_mode()

    def handle_two_roll_mode_button_press(self):
        modesetting.tworoll_trim_no_edit_init()
        self.set_cursor_to_mode()

    def handle_slide_mode_button_press(self):
        modesetting.slide_trim_no_edit_init()
        self.set_cursor_to_mode()

    def handle_multi_mode_button_press(self):
        modesetting.multi_mode_pressed()
        self.set_cursor_to_mode()

    def handle_cut_mode_button_press(self):
        modesetting.cut_mode_pressed()
        self.set_cursor_to_mode()

    def handle_kftool_mode_button_press(self):
        modesetting.kftool_mode_pressed()
        self.set_cursor_to_mode()

    def handle_multitrim_mode_button_press(self):
        modesetting.multitrim_mode_pressed()
        self.set_cursor_to_mode()

    def toggle_trim_ripple_mode(self):
        editorstate.trim_mode_ripple = (editorstate.trim_mode_ripple == False)
        modesetting.stop_looping()
        editorstate.edit_mode = editorstate.ONE_ROLL_TRIM_NO_EDIT
        tlinewidgets.set_edit_mode(None, None)
        self.set_tool_selector_to_mode()
        self.set_tline_cursor(editorstate.EDIT_MODE())
        updater.set_trim_mode_gui()

    def mode_selector_pressed(self, selector, event):
        workflow.get_tline_tool_popup_menu(event, self.tool_selector_item_activated)

    def tool_selector_item_activated(self, selector, tool):
        if tool == appconsts.TLINE_TOOL_INSERT:
            self.handle_insert_move_mode_button_press()
        if tool == appconsts.TLINE_TOOL_OVERWRITE:
            self.handle_over_move_mode_button_press()
        if tool == appconsts.TLINE_TOOL_TRIM:
            self.handle_one_roll_mode_button_press()
        if tool == appconsts.TLINE_TOOL_RIPPLE_TRIM:
            self.handle_one_roll_ripple_mode_button_press()
        if tool == appconsts.TLINE_TOOL_ROLL:
            self.handle_two_roll_mode_button_press()
        if tool == appconsts.TLINE_TOOL_SLIP:
            self.handle_slide_mode_button_press()
        if tool == appconsts.TLINE_TOOL_SPACER:
            self.handle_multi_mode_button_press()
        if tool == appconsts.TLINE_TOOL_BOX:
            self.handle_box_mode_button_press()
        if tool == appconsts.TLINE_TOOL_CUT:
            self.handle_cut_mode_button_press()
        if tool == appconsts.TLINE_TOOL_KFTOOL:
            self.handle_kftool_mode_button_press()
        if tool == appconsts.TLINE_TOOL_MULTI_TRIM:
            self.handle_multitrim_mode_button_press()

        self.set_cursor_to_mode()
        self.set_tool_selector_to_mode()

    def set_cursor_to_mode(self):
        if editorstate.cursor_on_tline == True:
            self.set_tline_cursor(editorstate.EDIT_MODE())
        else:
            gdk_window = gui.tline_display.get_parent_window()
            gdk_window.set_cursor(Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR))

    def get_own_cursor(self, display, surface, hotx, hoty):
        pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, surface.get_width(), surface.get_height())
        return Gdk.Cursor.new_from_pixbuf(display, pixbuf, hotx, hoty)

    def set_tline_cursor(self, mode):
        display = Gdk.Display.get_default()
        gdk_window = gui.editor_window.window.get_window()

        if mode == editorstate.INSERT_MOVE:
            cursor = self.get_own_cursor(display, INSERTMOVE_CURSOR, 0, 0)
        elif mode == editorstate.OVERWRITE_MOVE:
            if editorstate.overwrite_mode_box == False:
                cursor = self.get_own_cursor(display, OVERWRITE_CURSOR, 0, 0)
            else:
                if boxmove.entered_from_overwrite == False:
                    cursor = self.get_own_cursor(display, OVERWRITE_BOX_CURSOR, 6, 15)
                else:
                    cursor = self.get_own_cursor(display, OVERWRITE_CURSOR, 0, 0)
        elif mode == editorstate.TWO_ROLL_TRIM:
            cursor = self.get_own_cursor(display, TWOROLL_NO_EDIT_CURSOR, 11, 9)
        elif mode == editorstate.TWO_ROLL_TRIM_NO_EDIT:
            cursor = self.get_own_cursor(display, TWOROLL_NO_EDIT_CURSOR, 11, 9)
        elif mode == editorstate.ONE_ROLL_TRIM:
            if editorstate.trim_mode_ripple == False:
                cursor = self.get_own_cursor(display, ONEROLL_NO_EDIT_CURSOR, 9, 9)
            else:
                cursor = self.get_own_cursor(display, ONEROLL_RIPPLE_CURSOR, 9, 9)
        elif mode == editorstate.ONE_ROLL_TRIM_NO_EDIT:
            if editorstate.trim_mode_ripple == False:
                cursor = self.get_own_cursor(display, ONEROLL_NO_EDIT_CURSOR, 9, 9)
            else:
                cursor = self.get_own_cursor(display, ONEROLL_RIPPLE_CURSOR, 9, 9)
        elif mode == editorstate.SLIDE_TRIM:
            cursor = self.get_own_cursor(display, SLIDE_NO_EDIT_CURSOR, 9, 9)
        elif mode == editorstate.SLIDE_TRIM_NO_EDIT:
            cursor = self.get_own_cursor(display, SLIDE_NO_EDIT_CURSOR, 9, 9)
        elif mode == editorstate.SELECT_PARENT_CLIP:
            cursor =  Gdk.Cursor.new(Gdk.CursorType.TCROSS)
        elif mode == editorstate.SELECT_TLINE_SYNC_CLIP:
            cursor =  Gdk.Cursor.new(Gdk.CursorType.TCROSS)
        elif mode == editorstate.MULTI_MOVE:
            cursor = self.get_own_cursor(display, MULTIMOVE_CURSOR, 4, 8)
        elif mode == editorstate.CLIP_END_DRAG:
            surface, px, py = self.context_cursors[tlinewidgets.pointer_context]
            cursor = self.get_own_cursor(display, surface, px, py)
        elif mode == editorstate.CUT:
            cursor = self.get_own_cursor(display, CUT_CURSOR, 1, 8)
        elif mode == editorstate.KF_TOOL:
            cursor = self.get_own_cursor(display, KF_TOOL_CURSOR, 1, 0)
        elif mode == editorstate.MULTI_TRIM:
            cursor = self.get_own_cursor(display, MULTI_TRIM_CURSOR, 1, 0)
        else:
            cursor = Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR)

        gdk_window.set_cursor(cursor)

    def set_tline_cursor_to_context(self, pointer_context):
        display = Gdk.Display.get_default()
        gdk_window = gui.editor_window.window.get_window()

        surface, px, py = self.context_cursors[pointer_context]
        cursor = self.get_own_cursor(display, surface, px, py)
        gdk_window.set_cursor(cursor)

    def set_tool_selector_to_mode(self, tool_selector=None):
        
        # We need reference in first call to hold of it.
        if tool_selector != None:
            self.tool_selector = tool_selector
        
        # This gets testd first time before tool_selector available in editor_window.
        try:
            if gui.editor_window.tool_selector == None:
                return # We are using dock
        except:
            pass
            
        if editorstate.EDIT_MODE() == editorstate.INSERT_MOVE:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_INSERT)
        elif editorstate.EDIT_MODE() == editorstate.OVERWRITE_MOVE:
            if editorstate.overwrite_mode_box == False:
                self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_OVERWRITE)
            else:
                self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_BOX)
        elif editorstate.EDIT_MODE() == editorstate.ONE_ROLL_TRIM or editorstate.EDIT_MODE() == editorstate.ONE_ROLL_TRIM_NO_EDIT:
            if editorstate.trim_mode_ripple == False:
                self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_TRIM)
            else:
                self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_RIPPLE_TRIM)
        elif editorstate.EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_ROLL)
        elif editorstate.EDIT_MODE() == editorstate.TWO_ROLL_TRIM_NO_EDIT:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_ROLL)
        elif editorstate.EDIT_MODE() == editorstate.SLIDE_TRIM:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_SLIP)
        elif editorstate.EDIT_MODE() == editorstate.SLIDE_TRIM_NO_EDIT:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_SLIP)
        elif editorstate.EDIT_MODE() == editorstate.MULTI_MOVE:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_SPACER)
        elif editorstate.EDIT_MODE() == editorstate.CUT:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_CUT)
        elif editorstate.EDIT_MODE() == editorstate.KF_TOOL:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_KFTOOL)
        elif editorstate.EDIT_MODE() == editorstate.MULTI_TRIM:
            self.tool_selector.set_tool_pixbuf(appconsts.TLINE_TOOL_MULTI_TRIM)

    def tline_cursor_leave(self, event):
        cursor = Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR)
        gdk_window = gui.editor_window.window.get_window()
        gdk_window.set_cursor(cursor)

        if event.get_state() & Gdk.ModifierType.BUTTON1_MASK:
            if editorstate.current_is_move_mode():
                tlineaction.mouse_dragged_out(event)

    def tline_cursor_enter(self, event):
        editorstate.cursor_on_tline = True
        self.set_cursor_to_mode()


def get_tools_pixbuffs():
    return [INSERTMOVE_CURSOR, OVERWRITE_CURSOR, ONEROLL_CURSOR, ONEROLL_RIPPLE_CURSOR,\
            TWOROLL_CURSOR, SLIDE_CURSOR, MULTIMOVE_CURSOR, OVERWRITE_BOX_CURSOR, CUT_CURSOR, KF_TOOL_CURSOR, MULTI_TRIM_CURSOR]

