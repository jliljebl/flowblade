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
import updater
import undo
import workflow

# editorwindow.EditorWindow object.
# This needs to be set here because gui.py module ref is not available at init time
w = None

m_pixbufs = None

MIDDLE_ROW_HEIGHT = 30 # height of middle row gets set here

BUTTON_HEIGHT = 28 # middle edit buttons row
BUTTON_WIDTH = 48 # middle edit buttons row

NORMAL_WIDTH = 1420

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

def _show_buttons_COMPONENTS_CENTERED_layout(widget):
    global w
    w = gui.editor_window
    if w == None:
        return
    if widget.get_active() == False:
        return

    _clear_container(w.edit_buttons_row)
    _create_buttons(w)
    fill_with_COMPONENTS_CENTERED_pattern(w.edit_buttons_row, w)
    w.window.show_all()

    editorpersistance.prefs.midbar_layout = appconsts.MIDBAR_COMPONENTS_CENTERED
    editorpersistance.save()

def create_edit_buttons_row_buttons(editor_window, modes_pixbufs):
    global m_pixbufs
    m_pixbufs = modes_pixbufs
    _create_buttons(editor_window)

def _create_buttons(editor_window):
    # Aug-2019 - SvdB - BB
    prefs = editorpersistance.prefs
    size_adj = 1
    if prefs.double_track_hights:
       size_adj = 2

    editor_window.big_TC = Gtk.Stack()
    tc_disp = guicomponents.BigTCDisplay()
    tc_entry = guicomponents.BigTCEntry()
    tc_disp.widget.show()
    tc_entry.widget.show()
    editor_window.big_TC.add_named(tc_disp.widget, "BigTCDisplay")
    editor_window.big_TC.add_named(tc_entry.widget, "BigTCEntry")
    editor_window.big_TC.set_visible_child_name("BigTCDisplay")
    gui.big_tc = editor_window.big_TC 

    surface = guiutils.get_cairo_image("workflow")
    editor_window.worflow_launch = guicomponents.PressLaunch(workflow.workflow_menu_launched, surface, w=22*size_adj, h=22*size_adj)

    editor_window.tool_selector = guicomponents.ToolSelector(editor_window.mode_selector_pressed, m_pixbufs, 40*size_adj, 22*size_adj)

    if editorpersistance.prefs.buttons_style == 2: # NO_DECORATIONS
        no_decorations = True
    else:
        no_decorations = False

    editor_window.zoom_buttons = glassbuttons.GlassButtonsGroup(38*size_adj, 23*size_adj, 2*size_adj, 8*size_adj, 5*size_adj)
    editor_window.zoom_buttons.add_button(guiutils.get_cairo_image("zoom_in"), updater.zoom_in)
    editor_window.zoom_buttons.add_button(guiutils.get_cairo_image("zoom_out"), updater.zoom_out)
    editor_window.zoom_buttons.add_button(guiutils.get_cairo_image("zoom_length"), updater.zoom_project_length)
    tooltips = [_("Zoom In - Mouse Middle Scroll"), _("Zoom Out - Mouse Middle Scroll"), _("Zoom Length - Mouse Middle Click")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.zoom_buttons, tooltips)
    editor_window.zoom_buttons.no_decorations = no_decorations
    
    editor_window.edit_buttons = glassbuttons.GlassButtonsGroup(32*size_adj, 23*size_adj, 2*size_adj, 5*size_adj, 5*size_adj)
    editor_window.edit_buttons.add_button(guiutils.get_cairo_image("dissolve"), tlineaction.add_transition_pressed)
    editor_window.edit_buttons.add_button(guiutils.get_cairo_image("cut"), tlineaction.cut_pressed)
    tooltips = [_("Add Rendered Transition - 2 clips selected\nAdd Rendered Fade - 1 clip selected"), _("Cut Active Tracks - X\nCut All Tracks - Shift + X")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.edit_buttons, tooltips)
    editor_window.edit_buttons.no_decorations = no_decorations
        
    editor_window.edit_buttons_3 = glassbuttons.GlassButtonsGroup(46*size_adj, 23*size_adj, 2*size_adj, 3*size_adj, 5*size_adj)
    editor_window.edit_buttons_3.add_button(guiutils.get_cairo_image("splice_out"), tlineaction.splice_out_button_pressed)
    editor_window.edit_buttons_3.add_button(guiutils.get_cairo_image("lift"), tlineaction.lift_button_pressed)
    editor_window.edit_buttons_3.add_button(guiutils.get_cairo_image("ripple_delete"), tlineaction.ripple_delete_button_pressed)
    editor_window.edit_buttons_3.add_button(guiutils.get_cairo_image("delete_range"), tlineaction.delete_range_button_pressed)
    tooltips = [_("Splice Out - Delete"), _("Lift - Control + Delete"), _("Ripple Delete"), _("Range Delete")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.edit_buttons_3, tooltips)
    editor_window.edit_buttons_3.no_decorations = no_decorations

    editor_window.edit_buttons_2 = glassbuttons.GlassButtonsGroup(44*size_adj, 23*size_adj, 2*size_adj, 3*size_adj, 5*size_adj)
    editor_window.edit_buttons_2.add_button(guiutils.get_cairo_image("resync"), tlineaction.resync_button_pressed)
    editor_window.edit_buttons_2.add_button(guiutils.get_cairo_image("split_audio"), tlineaction.split_audio_button_pressed)
    tooltips = [_("Resync Selected"), _("Split Audio")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.edit_buttons_2, tooltips)
    editor_window.edit_buttons_2.no_decorations = no_decorations
    
    editor_window.monitor_insert_buttons = glassbuttons.GlassButtonsGroup(44*size_adj, 23*size_adj, 2*size_adj, 3*size_adj, 5*size_adj)
    editor_window.monitor_insert_buttons.add_button(guiutils.get_cairo_image("overwrite_range"), tlineaction.range_overwrite_pressed)
    editor_window.monitor_insert_buttons.add_button(guiutils.get_cairo_image("overwrite_clip"), tlineaction.three_point_overwrite_pressed)
    editor_window.monitor_insert_buttons.add_button(guiutils.get_cairo_image("insert_clip"), tlineaction.insert_button_pressed)
    editor_window.monitor_insert_buttons.add_button(guiutils.get_cairo_image("append_clip"), tlineaction.append_button_pressed)
    tooltips = [_("Overwrite Range"), _("Overwrite Clip - T"), _("Insert Clip - Y"), _("Append Clip - U")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.monitor_insert_buttons, tooltips)
    editor_window.monitor_insert_buttons.no_decorations = no_decorations
    
    editor_window.undo_redo = glassbuttons.GlassButtonsGroup(28*size_adj, 23*size_adj, 2*size_adj, 2*size_adj, 7*size_adj)
    editor_window.undo_redo.add_button(guiutils.get_cairo_image("undo"), undo.do_undo_and_repaint)
    editor_window.undo_redo.add_button(guiutils.get_cairo_image("redo"), undo.do_redo_and_repaint)
    tooltips = [_("Undo - Ctrl + Z"), _("Redo - Ctrl + Y")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.undo_redo, tooltips)
    editor_window.undo_redo.no_decorations = no_decorations
    
    editor_window.tools_buttons = glassbuttons.GlassButtonsGroup(30*size_adj, 23*size_adj, 2*size_adj, 14*size_adj, 7*size_adj)
    editor_window.tools_buttons.add_button(guiutils.get_cairo_image("open_mixer"), audiomonitoring.show_audio_monitor)
    editor_window.tools_buttons.add_button(guiutils.get_cairo_image("open_titler"), titler.show_titler)
    editor_window.tools_buttons.add_button(guiutils.get_cairo_image("open_gmic"), gmic.launch_gmic)
    editor_window.tools_buttons.add_button(guiutils.get_cairo_image("open_renderqueue"), lambda :batchrendering.launch_batch_rendering())
    tooltips = [_("Audio Mixer"), _("Titler"), _("G'Mic Effects"), _("Batch Render Queue")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.tools_buttons, tooltips)
    editor_window.tools_buttons.no_decorations = True
    
    if editorstate.audio_monitoring_available == False:
        editor_window.tools_buttons.sensitive[0] = False
        editor_window.tools_buttons.widget.set_tooltip_text(_("Audio Mixer(not available)\nTitler"))

def fill_with_TC_LEFT_pattern(buttons_row, window):
    buttons_row.set_homogeneous(False)
    global w
    w = window

    buttons_row.pack_start(w.worflow_launch.widget, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) 
    buttons_row.pack_start(w.big_TC, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    buttons_row.pack_start(w.tool_selector.widget, False, True, 0)

    if editorstate.SCREEN_WIDTH > NORMAL_WIDTH:
        buttons_row.pack_start(guiutils.get_pad_label(24, 10), False, True, 0)
        buttons_row.pack_start(_get_tools_buttons(), False, True, 0)
        buttons_row.pack_start(guiutils.get_pad_label(170, 10), False, True, 0)
    else:
        buttons_row.pack_start(guiutils.get_pad_label(30, 10), False, True, 0)
    
    
    buttons_row.pack_start(_get_undo_buttons_panel(), False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(30, 10), False, True, 0)
        
    buttons_row.pack_start(_get_zoom_buttons_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(30, 10), False, True, 0)
    
    buttons_row.pack_start(_get_edit_buttons_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(30, 10), False, True, 0)
    
    buttons_row.pack_start(_get_edit_buttons_2_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(20, 10), False, True, 0)
    
    buttons_row.pack_start(_get_edit_buttons_3_panel(),False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(30, 10), False, True, 0)
    
    buttons_row.pack_start(_get_monitor_insert_buttons(), False, True, 0)
    buttons_row.pack_start(Gtk.Label(), True, True, 0)
    
def fill_with_TC_MIDDLE_pattern(buttons_row, window):
    buttons_row.set_homogeneous(True)
    global w
    w = window
    left_panel = Gtk.HBox(False, 0)    
    left_panel.pack_start(_get_undo_buttons_panel(), False, True, 0)
    left_panel.pack_start(guiutils.get_pad_label(10, MIDDLE_ROW_HEIGHT), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    left_panel.pack_start(_get_zoom_buttons_panel(), False, True, 0)
    if editorstate.SCREEN_WIDTH > NORMAL_WIDTH:
        left_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
        left_panel.pack_start(_get_tools_buttons(), False, True, 0)
        left_panel.pack_start(guiutils.get_pad_label(50, 10), False, True, 10) # to left and right panel same size for centering
    else:
        left_panel.pack_start(guiutils.get_pad_label(60, 10), False, True, 10) # to left and right panel same size for centering
    left_panel.pack_start(Gtk.Label(), True, True, 0)

    middle_panel = Gtk.HBox(False, 0)
    middle_panel.pack_start(w.worflow_launch.widget, False, True, 0)
    middle_panel.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) 
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

def fill_with_COMPONENTS_CENTERED_pattern(buttons_row, window):
    buttons_row.set_homogeneous(False)
    global w
    w = window
    buttons_row.pack_start(Gtk.Label(), True, True, 0)
    buttons_row.pack_start(w.worflow_launch.widget, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) 
    buttons_row.pack_start(w.big_TC, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    buttons_row.pack_start(w.tool_selector.widget, False, True, 0)
    if editorstate.SCREEN_WIDTH > NORMAL_WIDTH:
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
