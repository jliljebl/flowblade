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
import dialogutils
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

def do_layout_after_dock_change(w):
    if editorpersistance.prefs.midbar_layout == appconsts.MIDBAR_TC_LEFT:
        _do_TC_LEFT_layout(w)
    elif editorpersistance.prefs.midbar_layout == appconsts.MIDBAR_TC_CENTER: 
        _do_TC_MIDDLE_layout(w)
    elif editorpersistance.prefs.midbar_layout == appconsts.MIDBAR_COMPONENTS_CENTERED:
        _do_COMPONENTS_CENTERED_layout(w)
    elif editorpersistance.prefs.midbar_layout == appconsts.MIDBAR_TC_FREE:
        _do_show_buttons_TC_FREE_layout(w)
    
def _show_buttons_TC_LEFT_layout(widget):
    global w
    w = gui.editor_window
    if w == None:
        return
    if widget.get_active() == False:
        return

    _do_TC_LEFT_layout(w)
    
def _do_TC_LEFT_layout(w):
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

    _do_TC_MIDDLE_layout(w)
    
def _do_TC_MIDDLE_layout(w):
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

    _do_COMPONENTS_CENTERED_layout(w)
    
def _do_COMPONENTS_CENTERED_layout(w):
    
    _clear_container(w.edit_buttons_row)
    _create_buttons(w)
    fill_with_COMPONENTS_CENTERED_pattern(w.edit_buttons_row, w)
    w.window.show_all()

    editorpersistance.prefs.midbar_layout = appconsts.MIDBAR_COMPONENTS_CENTERED
    editorpersistance.save()

# ----------------------------- Toolbar preferences panel for free elements and order
def _show_buttons_TC_FREE_layout(widget):
    global w
    w = gui.editor_window
    if w == None:
        return
    if widget.get_active() == False:
        return

    _do_show_buttons_TC_FREE_layout(w)

def _do_show_buttons_TC_FREE_layout(w):
    _clear_container(w.edit_buttons_row)
    _create_buttons(w)
    fill_with_TC_FREE_pattern(w.edit_buttons_row, w)
    w.window.show_all()

    editorpersistance.prefs.midbar_layout = appconsts.MIDBAR_TC_FREE
    editorpersistance.save()

# --------------------------- End of Toolbar preferences panel for free elements and order

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

    if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_MENU:
        editor_window.tool_selector = create_tool_selector(editor_window) #guicomponents.ToolSelector(editor_window.mode_selector_pressed, m_pixbufs, 40*size_adj, 22*size_adj)
    else:
        editor_window.tool_selector = None

    if editorpersistance.prefs.buttons_style == 2: # NO_DECORATIONS
        no_decorations = True
    else:
        no_decorations = False

    # Colorized icons
    if prefs.colorized_icons is True:
        icon_color = "_color"
    else:
        icon_color = ""
    # End of Colorized icons

    editor_window.zoom_buttons = glassbuttons.GlassButtonsGroup(38*size_adj, 23*size_adj, 2*size_adj, 8*size_adj, 5*size_adj)
    editor_window.zoom_buttons.add_button(guiutils.get_cairo_image("zoom_in" + icon_color), updater.zoom_in)
    editor_window.zoom_buttons.add_button(guiutils.get_cairo_image("zoom_out" + icon_color), updater.zoom_out)
    editor_window.zoom_buttons.add_button(guiutils.get_cairo_image("zoom_length" + icon_color), updater.zoom_project_length)
    tooltips = [_("Zoom In - Mouse Middle Scroll"), _("Zoom Out - Mouse Middle Scroll"), _("Zoom Length - Mouse Middle Click")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.zoom_buttons, tooltips)
    editor_window.zoom_buttons.no_decorations = no_decorations
    
    editor_window.edit_buttons = glassbuttons.GlassButtonsGroup(32*size_adj, 23*size_adj, 2*size_adj, 5*size_adj, 5*size_adj)
    editor_window.edit_buttons.add_button(guiutils.get_cairo_image("dissolve" + icon_color), tlineaction.add_transition_pressed)
    editor_window.edit_buttons.add_button(guiutils.get_cairo_image("cut" + icon_color), tlineaction.cut_pressed)
    tooltips = [_("Add Rendered Transition - 2 clips selected\nAdd Rendered Fade - 1 clip selected"), _("Cut Active Tracks - X\nCut All Tracks - Shift + X")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.edit_buttons, tooltips)
    editor_window.edit_buttons.no_decorations = no_decorations
        
    editor_window.edit_buttons_3 = glassbuttons.GlassButtonsGroup(46*size_adj, 23*size_adj, 2*size_adj, 3*size_adj, 5*size_adj)
    editor_window.edit_buttons_3.add_button(guiutils.get_cairo_image("splice_out" + icon_color), tlineaction.splice_out_button_pressed)
    editor_window.edit_buttons_3.add_button(guiutils.get_cairo_image("lift" + icon_color), tlineaction.lift_button_pressed)
    editor_window.edit_buttons_3.add_button(guiutils.get_cairo_image("ripple_delete" + icon_color), tlineaction.ripple_delete_button_pressed)
    editor_window.edit_buttons_3.add_button(guiutils.get_cairo_image("delete_range" + icon_color), tlineaction.delete_range_button_pressed)
    tooltips = [_("Splice Out - Delete"), _("Lift - Control + Delete"), _("Ripple Delete"), _("Range Delete")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.edit_buttons_3, tooltips)
    editor_window.edit_buttons_3.no_decorations = no_decorations

    editor_window.edit_buttons_2 = glassbuttons.GlassButtonsGroup(44*size_adj, 23*size_adj, 2*size_adj, 3*size_adj, 5*size_adj)
    editor_window.edit_buttons_2.add_button(guiutils.get_cairo_image("resync" + icon_color), tlineaction.resync_button_pressed)
    editor_window.edit_buttons_2.add_button(guiutils.get_cairo_image("split_audio" + icon_color), tlineaction.split_audio_button_pressed)
    tooltips = [_("Resync Selected"), _("Split Audio")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.edit_buttons_2, tooltips)
    editor_window.edit_buttons_2.no_decorations = no_decorations
    
    editor_window.monitor_insert_buttons = glassbuttons.GlassButtonsGroup(44*size_adj, 23*size_adj, 2*size_adj, 3*size_adj, 5*size_adj)
    editor_window.monitor_insert_buttons.add_button(guiutils.get_cairo_image("overwrite_range" + icon_color), tlineaction.range_overwrite_pressed)
    editor_window.monitor_insert_buttons.add_button(guiutils.get_cairo_image("overwrite_clip" + icon_color), tlineaction.three_point_overwrite_pressed)
    editor_window.monitor_insert_buttons.add_button(guiutils.get_cairo_image("insert_clip" + icon_color), tlineaction.insert_button_pressed)
    editor_window.monitor_insert_buttons.add_button(guiutils.get_cairo_image("append_clip" + icon_color), tlineaction.append_button_pressed)
    tooltips = [_("Overwrite Range"), _("Overwrite Clip - T"), _("Insert Clip - Y"), _("Append Clip - U")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.monitor_insert_buttons, tooltips)
    editor_window.monitor_insert_buttons.no_decorations = no_decorations
    
    editor_window.undo_redo = glassbuttons.GlassButtonsGroup(28*size_adj, 23*size_adj, 2*size_adj, 2*size_adj, 7*size_adj)
    editor_window.undo_redo.add_button(guiutils.get_cairo_image("undo" + icon_color), undo.do_undo_and_repaint)
    editor_window.undo_redo.add_button(guiutils.get_cairo_image("redo" + icon_color), undo.do_redo_and_repaint)
    tooltips = [_("Undo - Ctrl + Z"), _("Redo - Ctrl + Y")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.undo_redo, tooltips)
    editor_window.undo_redo.no_decorations = no_decorations
    
    editor_window.tools_buttons = glassbuttons.GlassButtonsGroup(30*size_adj, 23*size_adj, 2*size_adj, 14*size_adj, 7*size_adj)
    editor_window.tools_buttons.add_button(guiutils.get_cairo_image("open_mixer" + icon_color), audiomonitoring.show_audio_monitor)
    editor_window.tools_buttons.add_button(guiutils.get_cairo_image("open_titler" + icon_color), titler.show_titler)
    editor_window.tools_buttons.add_button(guiutils.get_cairo_image("open_gmic" + icon_color), gmic.launch_gmic)
    editor_window.tools_buttons.add_button(guiutils.get_cairo_image("open_renderqueue" + icon_color), lambda :batchrendering.launch_batch_rendering())
    tooltips = [_("Audio Mixer"), _("Titler"), _("G'Mic Effects"), _("Batch Render Queue")]
    tooltip_runner = glassbuttons.TooltipRunner(editor_window.tools_buttons, tooltips)
    editor_window.tools_buttons.no_decorations = True
    
    if editorstate.audio_monitoring_available == False:
        editor_window.tools_buttons.sensitive[0] = False
        editor_window.tools_buttons.widget.set_tooltip_text(_("Audio Mixer(not available)\nTitler"))

def create_tool_selector(editor_window):
    size_adj = 1
    if editorpersistance.prefs.double_track_hights:
       size_adj = 2
    return guicomponents.ToolSelector(editor_window.mode_selector_pressed, m_pixbufs, 40*size_adj, 22*size_adj)

def re_create_tool_selector(editor_window):
    editor_window.tool_selector = create_tool_selector(editor_window)
 
def fill_with_TC_LEFT_pattern(buttons_row, window):
    buttons_row.set_homogeneous(False)
    global w
    w = window

    buttons_row.pack_start(w.worflow_launch.widget, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) 
    buttons_row.pack_start(w.big_TC, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_MENU:
        buttons_row.pack_start(w.tool_selector.widget, False, True, 0)

    if editorstate.SCREEN_WIDTH > NORMAL_WIDTH:
        buttons_row.pack_start(guiutils.get_pad_label(24, 10), False, True, 0)
        buttons_row.pack_start(_get_tools_buttons(), False, True, 0)
        if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_MENU:
            buttons_row.pack_start(guiutils.get_pad_label(170, 10), False, True, 0)
        else:
            buttons_row.pack_start(guiutils.get_pad_label(100, 10), False, True, 0)
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
    if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_MENU:
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
    if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_MENU:
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

def fill_with_TC_FREE_pattern(buttons_row, window):
    global w
    w = window
    prefs = editorpersistance.prefs
    
    groups_tools_current = prefs.groups_tools
    cbutton_active_current = prefs.cbutton
    tools_dict = {appconsts.WORKFLOW_LAUNCH:w.worflow_launch.widget, appconsts.TOOL_SELECT:w.tool_selector.widget, appconsts.BUTTON_GROUP_ZOOM:_get_zoom_buttons_panel(),  \
                        appconsts.BUTTON_GROUP_UNDO:_get_undo_buttons_panel(), appconsts.BUTTON_GROUP_TOOLS:_get_tools_buttons(), appconsts.BUTTON_GROUP_EDIT:_get_edit_buttons_panel(),\
                        appconsts.BUTTON_GROUP_DELETE:_get_edit_buttons_3_panel(),  appconsts.BUTTON_GROUP_SYNC_SPLIT:_get_edit_buttons_2_panel(),  \
                        appconsts.BUTTON_GROUP_MONITOR_ADD:_get_monitor_insert_buttons(),  appconsts.BIG_TIME_CODE:w.big_TC}

    buttons_row.set_homogeneous(False)
    buttons_row.pack_start(Gtk.Label(), True, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    for row_number in range(0, len(groups_tools_current)):
        if cbutton_active_current[row_number] is True:
            tool = tools_dict[groups_tools_current[row_number]]
            buttons_row.pack_start(tool, False, True, 0) # does not support dock yet
            buttons_row.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
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

# ----------------------------------------------------------------------------- Free Bar conf GUI
def show_freebar_conf_dialog():
    dialog = Gtk.Dialog(_("Free Bar Configuration"), None,
                    Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    (_("Cancel"), Gtk.ResponseType.REJECT,
                    _("OK"), Gtk.ResponseType.ACCEPT))

    panel = _get_freebar_conf_panel()
    
    guiutils.set_margins(panel, 4, 24, 6, 0)
    dialog.connect('response', _freebar_dialog_callback, (None, None))
    dialog.vbox.pack_start(panel, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    dialog.set_transient_for(gui.editor_window.window)
    dialog.show_all()


def _freebar_dialog_callback(dialog, response_id, data):
    if response_id == Gtk.ResponseType.ACCEPT:
        editorpersistance.prefs.groups_tools = groups_tools
        editorpersistance.prefs.cbutton = cbutton_flag
        editorpersistance.save()

        _do_show_buttons_TC_FREE_layout(gui.editor_window)

    dialog.destroy()
    
# Toolbar preferences panel for free elements and order
def _get_freebar_conf_panel():
    prefs = editorpersistance.prefs

    global toolbar_list, groups_tools, cbutton_flag, cbutton, gui_object_names
    groups_tools = prefs.groups_tools
    cbutton_flag = prefs.cbutton


    gui_object_names = {appconsts.BUTTON_GROUP_TOOLS:_("Tools Group"),
                        appconsts.BUTTON_GROUP_UNDO:_("Undo Group"),
                        appconsts.BUTTON_GROUP_ZOOM:_("Zoom Group"),
                        appconsts.BUTTON_GROUP_EDIT:_("Edit Group"),
                        appconsts.BUTTON_GROUP_SYNC_SPLIT:_("Sync Split Group"),
                        appconsts.BUTTON_GROUP_DELETE:_("Delete Group"),
                        appconsts.BUTTON_GROUP_MONITOR_ADD:_("Monitor Add Group"),
                        appconsts.BIG_TIME_CODE:_("Timecode Display"),
                        appconsts.WORKFLOW_LAUNCH:_("Workflow Menu"),
                        appconsts.TOOL_SELECT:_("Edit Tool Menu")}
                        
    # Widgets
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    choice = Gtk.Label("Check the groups of buttons visible or not in the toolbar; select one and change order")
    
    toolbar_list = Gtk.ListBox()
    toolbar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)

    box_move = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    button_up = Gtk.Button(label="Up")
    button_up.connect("clicked", row_up, vbox)
    box_move.pack_start(button_up, False, False, 0)
    button_down = Gtk.Button(label="Down")
    button_down.connect("clicked", row_down, vbox)
    box_move.pack_start(button_down, False, False, 0)

    vbox.pack_start(choice, False, False, 0)
    vbox.pack_start(toolbar_list, False, False, 0)
    vbox.pack_start(box_move, False, False, 0)
    
    draw_listbox(vbox)

    return vbox
    
def toggle_click(button, row_number):
    cbutton_flag[row_number] = button.get_active()

def row_up(event, vbox):
    reselect_row = -1
    for row_number in range(0, len(groups_tools)):
        row = toolbar_list.get_row_at_index(row_number)
        if row ==  toolbar_list.get_selected_row() and row_number > 0:
            elem_plus_un = groups_tools[row_number]
            groups_tools[row_number] =  groups_tools[row_number - 1]
            groups_tools[row_number - 1] = elem_plus_un
            check_plus_un = cbutton_flag[row_number]
            cbutton_flag[row_number] =  cbutton_flag[row_number - 1]
            cbutton_flag[row_number - 1] = check_plus_un
            reselect_row = row_number - 1
            break

    toolbar_list.unselect_all()
    for row in toolbar_list:
        toolbar_list.remove(row)
        
    draw_listbox(vbox)

    if reselect_row != -1:
        row = toolbar_list.get_row_at_index(reselect_row)
        toolbar_list.select_row(row)
    
def row_down(event, vbox):
    reselect_row = -1
    for row_number in range(0, len(groups_tools)):
        row = toolbar_list.get_row_at_index(row_number)
        if row ==  toolbar_list.get_selected_row() and row_number < len(groups_tools) -1:
            elem_moins_un =  groups_tools[row_number]
            groups_tools[row_number] =  groups_tools[row_number + 1]
            groups_tools[row_number + 1] = elem_moins_un
            check_moins_un = cbutton_flag[row_number]
            cbutton_flag[row_number] =  cbutton_flag[row_number + 1]
            cbutton_flag[row_number + 1] = check_moins_un
            reselect_row = row_number + 1
            break
    toolbar_list.unselect_all()
    for row in toolbar_list:
        toolbar_list.remove(row)
    draw_listbox(vbox)

    if reselect_row != -1:
        row = toolbar_list.get_row_at_index(reselect_row)
        toolbar_list.select_row(row)

def draw_listbox(vbox):
    for row_number in range(0, len(groups_tools)):
        row = Gtk.ListBoxRow.new()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        but = Gtk.CheckButton(label=str(row_number))
        but.connect("toggled", toggle_click, row_number)
        but.set_active( cbutton_flag[row_number])
        box.pack_start(but, False, False, 0)
        lab = Gtk.Label(gui_object_names[groups_tools[row_number]])
        box.pack_start(lab, True, True, 0)
        row.add(box)
        toolbar_list.add(row)

    vbox.show_all()

    
