"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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

import cairo

from gi.repository import Gtk

import appconsts
import audiomonitoring
import batchrendering
import editorpersistance
import editorstate
import glassbuttons
import gmic
import gui
import guicomponents
import guiutils
import respaths
import titler
import tlineaction
import toolnatron
import updater
import undo
import workflow

# editor window object
# This needs to be set here because gui.py module ref is not available at init time
w = None

m_pixbufs = None

MIDDLE_ROW_HEIGHT = 30 # height of middle row gets set here

BUTTON_HEIGHT = 28 # middle edit buttons row
BUTTON_WIDTH = 48 # middle edit buttons row

def _show_buttons_TC_LEFT_layout(widget):
    global w
    w = gui.editor_window
    if w == None:
        return
    if widget.get_active() == False:
        return

    _clear_container(w.edit_buttons_row)
    _create_buttons(w)
    fill_with_TC_LEFT_pattern(w.edit_buttons_row, w)
    w.window.show_all()

    editorpersistance.prefs.midbar_layout = appconsts.MIDBAR_TC_LEFT
    editorpersistance.save()
    
def _show_buttons_TC_MIDDLE_layout(widget):
    global w
    w = gui.editor_window
    if w == None:
        return
    if widget.get_active() == False:
        return

    _clear_container(w.edit_buttons_row)
    _create_buttons(w)
    fill_with_TC_MIDDLE_pattern(w.edit_buttons_row, w)
    w.window.show_all()

    editorpersistance.prefs.midbar_layout = appconsts.MIDBAR_TC_CENTER
    editorpersistance.save()

def _show_buttons_COMPONETS_CENTERED_layout(widget):
    global w
    w = gui.editor_window
    if w == None:
        return
    if widget.get_active() == False:
        return

    _clear_container(w.edit_buttons_row)
    _create_buttons(w)
    fill_with_COMPONETS_CENTERED_pattern(w.edit_buttons_row, w)
    w.window.show_all()

    editorpersistance.prefs.midbar_layout = appconsts.MIDBAR_COMPONENTS_CENTERED
    editorpersistance.save()
    
def _show_monitor_info_toggled(widget):
    editorpersistance.prefs.show_sequence_profile = widget.get_active()
    editorpersistance.save()

    if editorstate.timeline_visible():
        name = editorstate.current_sequence().name
        profile_desc = editorstate.current_sequence().profile.description()
        if editorpersistance.prefs.show_sequence_profile:
            gui.editor_window.monitor_source.set_text(name + " / " + profile_desc)
        else:
            gui.editor_window.monitor_source.set_text(name)

def create_edit_buttons_row_buttons(editor_window, modes_pixbufs):
    global m_pixbufs
    m_pixbufs = modes_pixbufs
    _create_buttons(editor_window)

def _create_buttons(editor_window):
    IMG_PATH = respaths.IMAGE_PATH
    editor_window.big_TC = Gtk.Stack()
    tc_disp = guicomponents.BigTCDisplay()
    tc_entry = guicomponents.BigTCEntry()
    tc_disp.widget.show()
    tc_entry.widget.show()
    editor_window.big_TC.add_named(tc_disp.widget, "BigTCDisplay")
    editor_window.big_TC.add_named(tc_entry.widget, "BigTCEntry")
    editor_window.big_TC.set_visible_child_name("BigTCDisplay")
    gui.big_tc = editor_window.big_TC 

    surface = cairo.ImageSurface.create_from_png(IMG_PATH + "workflow.png")
    editor_window.worflow_launch = guicomponents.PressLaunch(workflow.workflow_menu_launched, surface, w=22, h=22)

    editor_window.tool_selector = guicomponents.ToolSelector(editor_window.mode_selector_pressed, m_pixbufs, 40, 22)

    if editorpersistance.prefs.buttons_style == 2: # NO_DECORATIONS
        no_decorations = True
    else:
        no_decorations = False

    editor_window.zoom_buttons = glassbuttons.GlassButtonsGroup(38, 23, 2, 8, 5)
    editor_window.zoom_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "zoom_in.png"), updater.zoom_in)
    editor_window.zoom_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "zoom_out.png"), updater.zoom_out)
    editor_window.zoom_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "zoom_length.png"), updater.zoom_project_length)
    editor_window.zoom_buttons.widget.set_tooltip_text(_("Zoom In - Mouse Middle Scroll\n Zoom Out - Mouse Middle Scroll\n Zoom Length - Mouse Middle Click"))
    editor_window.zoom_buttons.no_decorations = no_decorations
    
    editor_window.edit_buttons = glassbuttons.GlassButtonsGroup(32, 23, 2, 5, 5)
    editor_window.edit_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "dissolve.png"), tlineaction.add_transition_pressed)
    editor_window.edit_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "cut.png"), tlineaction.cut_pressed)
    editor_window.edit_buttons.widget.set_tooltip_text(_("Add Rendered Transition - 2 clips selected\nAdd Rendered Fade - 1 clip selected\nCut - X"))
    editor_window.edit_buttons.no_decorations = no_decorations
        
    editor_window.edit_buttons_3 = glassbuttons.GlassButtonsGroup(46, 23, 2, 3, 5)
    editor_window.edit_buttons_3.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "splice_out.png"), tlineaction.splice_out_button_pressed)
    editor_window.edit_buttons_3.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "ripple_delete.png"), tlineaction.ripple_delete_button_pressed)
    editor_window.edit_buttons_3.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "lift.png"), tlineaction.lift_button_pressed)
    editor_window.edit_buttons_3.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "delete_range.png"), tlineaction.delete_range_button_pressed)
    editor_window.edit_buttons_3.widget.set_tooltip_text(_("Splice Out - Delete\nRipple Delete\nLift\nDelete Range"))
    editor_window.edit_buttons_3.no_decorations = no_decorations

    editor_window.edit_buttons_2 = glassbuttons.GlassButtonsGroup(44, 23, 2, 3, 5)
    editor_window.edit_buttons_2.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "resync.png"), tlineaction.resync_button_pressed)
    editor_window.edit_buttons_2.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "split_audio.png"), tlineaction.split_audio_button_pressed)
    editor_window.edit_buttons_2.widget.set_tooltip_text(_("Resync Selected\nSplit Audio"))
    editor_window.edit_buttons_2.no_decorations = no_decorations
    
    editor_window.monitor_insert_buttons = glassbuttons.GlassButtonsGroup(44, 23, 2, 3, 5)
    editor_window.monitor_insert_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "overwrite_range.png"), tlineaction.range_overwrite_pressed)
    editor_window.monitor_insert_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "overwrite_clip.png"), tlineaction.three_point_overwrite_pressed)
    editor_window.monitor_insert_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "insert_clip.png"), tlineaction.insert_button_pressed)
    editor_window.monitor_insert_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "append_clip.png"), tlineaction.append_button_pressed)
    editor_window.monitor_insert_buttons.widget.set_tooltip_text(_("Overwrite Range\nOverwrite Clip - T\nInsert Clip - Y\nAppend Clip - U"))
    editor_window.monitor_insert_buttons.no_decorations = no_decorations
    
    editor_window.undo_redo = glassbuttons.GlassButtonsGroup(28, 23, 2, 2, 7)
    editor_window.undo_redo.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "undo.png"), undo.do_undo_and_repaint)
    editor_window.undo_redo.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "redo.png"), undo.do_redo_and_repaint)
    editor_window.undo_redo.widget.set_tooltip_text(_("Undo - Ctrl + Z\nRedo - Ctrl + Y"))
    editor_window.undo_redo.no_decorations = no_decorations
    
    editor_window.tools_buttons = glassbuttons.GlassButtonsGroup(30, 23, 2, 14, 7)
    editor_window.tools_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "open_mixer.png"), audiomonitoring.show_audio_monitor)
    editor_window.tools_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "open_titler.png"), titler.show_titler)
    editor_window.tools_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "open_gmic.png"), gmic.launch_gmic)
    editor_window.tools_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "open_natron.png"), toolnatron.launch_natron_animations_tool)
    editor_window.tools_buttons.add_button(cairo.ImageSurface.create_from_png(IMG_PATH + "open_renderqueue.png"), lambda :batchrendering.launch_batch_rendering())
    editor_window.tools_buttons.widget.set_tooltip_text(_("Audio Mixer\nTitler\nG'Mic Effects\nNatron Animations\nBatch Render Queue"))
    editor_window.tools_buttons.no_decorations = True
    
    if editorstate.audio_monitoring_available == False:
        editor_window.tools_buttons.sensitive[0] = False
        editor_window.tools_buttons.widget.set_tooltip_text(_("Audio Mixer(not available)\nTitler"))

def fill_with_TC_LEFT_pattern(buttons_row, window):
    global w
    w = window
    buttons_row.pack_start(w.worflow_launch.widget, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) 
    buttons_row.pack_start(w.big_TC, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    buttons_row.pack_start(w.tool_selector.widget, False, True, 0)
    if editorstate.SCREEN_WIDTH > 1279:
        buttons_row.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
        buttons_row.pack_start(_get_tools_buttons(), False, True, 0)
        buttons_row.pack_start(guiutils.get_pad_label(150, 10), False, True, 0)
    else:
        buttons_row.pack_start(guiutils.get_pad_label(30, 10), False, True, 0)
    
    
    buttons_row.pack_start(_get_undo_buttons_panel(), False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(30, 10), False, True, 0)
    #buttons_row.pack_start(Gtk.Label(), True, True, 0)
        
    buttons_row.pack_start(_get_zoom_buttons_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(30, 10), False, True, 0)
    #buttons_row.pack_start(Gtk.Label(), True, True, 0)
    
    buttons_row.pack_start(_get_edit_buttons_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(30, 10), False, True, 0)
    # buttons_row.pack_start(Gtk.Label(), True, True, 0)
    
    #buttons_row.pack_start(_get_edit_buttons_2_panel(),False, True, 0)
    #buttons_row.pack_start(guiutils.get_pad_label(20, 10), False, True, 0)
    #buttons_row.pack_start(Gtk.Label(), True, True, 0)
    
    buttons_row.pack_start(_get_edit_buttons_3_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(30, 10), False, True, 0)
    #buttons_row.pack_start(Gtk.Label(), True, True, 0)
    
    buttons_row.pack_start(_get_monitor_insert_buttons(), False, True, 0)
    buttons_row.pack_start(Gtk.Label(), True, True, 0)
    
def fill_with_TC_MIDDLE_pattern(buttons_row, window):
    global w
    w = window
    left_panel = Gtk.HBox(False, 0)    
    left_panel.pack_start(_get_undo_buttons_panel(), False, True, 0)
    left_panel.pack_start(guiutils.get_pad_label(10, MIDDLE_ROW_HEIGHT), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    left_panel.pack_start(_get_zoom_buttons_panel(), False, True, 0)
    if editorstate.SCREEN_WIDTH > 1279:
        left_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
        left_panel.pack_start(_get_tools_buttons(), False, True, 0)
        left_panel.pack_start(guiutils.get_pad_label(50, 10), False, True, 10) # to left and right panel same size for centering
    else:
        left_panel.pack_start(guiutils.get_pad_label(60, 10), False, True, 10) # to left and right panel same size for centering
    left_panel.pack_start(Gtk.Label(), True, True, 0)

    middle_panel = Gtk.HBox(False, 0) 
    middle_panel.pack_start(w.big_TC, False, True, 0)
    middle_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
    middle_panel.pack_start(w.tool_selector.widget, False, True, 0)
    
    right_panel = Gtk.HBox(False, 0) 
    right_panel.pack_start(Gtk.Label(), True, True, 0)
    right_panel.pack_start(_get_edit_buttons_panel(), False, True, 0)
    right_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
    right_panel.pack_start(_get_edit_buttons_3_panel(),False, True, 0)
    right_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
    right_panel.pack_start(_get_edit_buttons_2_panel(),False, True, 0)
    right_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
    right_panel.pack_start(_get_monitor_insert_buttons(), False, True, 0)

    buttons_row.pack_start(left_panel, True, True, 0)
    buttons_row.pack_start(middle_panel, False, False, 0)
    buttons_row.pack_start(right_panel, True, True, 0)

def fill_with_COMPONETS_CENTERED_pattern(buttons_row, window):
    global w
    w = window
    buttons_row.pack_start(Gtk.Label(), True, True, 0)
    buttons_row.pack_start(w.big_TC, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    buttons_row.pack_start(w.tool_selector.widget, False, True, 0)
    if editorstate.SCREEN_WIDTH > 1279:
        buttons_row.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
        buttons_row.pack_start(_get_tools_buttons(), False, True, 0)
        #buttons_row.pack_start(guiutils.get_pad_label(120, 10), False, True, 0)
        buttons_row.pack_start(guiutils.get_pad_label(20, 10), False, True, 0)
    else:
        buttons_row.pack_start(guiutils.get_pad_label(20, 10), False, True, 0)
        
    buttons_row.pack_start(_get_undo_buttons_panel(), False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(20, 10), False, True, 0)
        
    buttons_row.pack_start(_get_zoom_buttons_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(20, 10), False, True, 0)
    
    buttons_row.pack_start(_get_edit_buttons_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(20, 10), False, True, 0)
    
    buttons_row.pack_start(_get_edit_buttons_2_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(20, 10), False, True, 0)
    
    buttons_row.pack_start(_get_edit_buttons_3_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(20, 10), False, True, 0)
    
    buttons_row.pack_start(_get_monitor_insert_buttons(), False, True, 0)
    buttons_row.pack_start(Gtk.Label(), True, True, 0)
    
def _get_zoom_buttons_panel():    
    return w.zoom_buttons.widget

def _get_undo_buttons_panel():
    return w.undo_redo.widget

def _get_edit_buttons_panel():
    return w.edit_buttons.widget

def _get_edit_buttons_2_panel():
    return w.edit_buttons_2.widget

def _get_edit_buttons_3_panel():
    return w.edit_buttons_3.widget
    
def _get_monitor_insert_buttons():
    return w.monitor_insert_buttons.widget

def _get_tools_buttons():
    return w.tools_buttons.widget

def _b(button, icon, remove_relief=False):
    button.set_image(icon)
    button.set_property("can-focus",  False)
    if remove_relief:
        button.set_relief(Gtk.ReliefStyle.NONE)

def _clear_container(cont):
    children = cont.get_children()
    for child in children:
        cont.remove(child)
