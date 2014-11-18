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

"""

"""

import pygtk
pygtk.require('2.0');
import gtk


import audiomonitoring
import editevent
import editorpersistance
import editorstate
import glassbuttons
import gui
import guicomponents
import guiutils
import respaths
import titler
import tlineaction
import updater
import undo

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

    editorpersistance.prefs.midbar_tc_left = True
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

    editorpersistance.prefs.midbar_tc_left = False
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
    editor_window.big_TC = guicomponents.BigTCDisplay()
    editor_window.modes_selector = guicomponents.ToolSelector(editor_window.mode_selector_pressed, m_pixbufs, 40, 22)

    editor_window.zoom_buttons = glassbuttons.GlassButtonsGroup(46, 23, 2, 4, 5)
    editor_window.zoom_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "zoom_in.png"), updater.zoom_in)
    editor_window.zoom_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "zoom_out.png"), updater.zoom_out)
    editor_window.zoom_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "zoom_length.png"), updater.zoom_project_length)
    editor_window.zoom_buttons.widget.set_tooltip_text(_("Zoom In - Mouse Middle Scroll\n Zoom Out - Mouse Middle Scroll\n Zoom Length - Mouse Middle Click"))

    editor_window.edit_buttons = glassbuttons.GlassButtonsGroup(46, 23, 2, 4, 5)
    editor_window.edit_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "cut.png"), tlineaction.cut_pressed)
    editor_window.edit_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "splice_out.png"), tlineaction.splice_out_button_pressed)
    editor_window.edit_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "lift.png"), tlineaction.lift_button_pressed)
    editor_window.edit_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "resync.png"), tlineaction.resync_button_pressed)
    editor_window.edit_buttons.widget.set_tooltip_text(_("Cut - X\nSplice Out - Delete\nLift\nResync Selected"))

    editor_window.monitor_insert_buttons = glassbuttons.GlassButtonsGroup(46, 23, 2, 4, 5)
    editor_window.monitor_insert_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "overwrite_range.png"), tlineaction.range_overwrite_pressed)
    editor_window.monitor_insert_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "overwrite_clip.png"), tlineaction.three_point_overwrite_pressed)
    editor_window.monitor_insert_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "insert_clip.png"), tlineaction.insert_button_pressed)
    editor_window.monitor_insert_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "append_clip.png"), tlineaction.append_button_pressed)
    editor_window.monitor_insert_buttons.widget.set_tooltip_text(_("Overwrite Range\nOverwrite Clip - T\nInsert Clip - Y\nAppend Clip - U"))

    editor_window.undo_redo = glassbuttons.GlassButtonsGroup(46, 23, 2, 2, 7)
    editor_window.undo_redo.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "undo.png"), undo.do_undo_and_repaint)
    editor_window.undo_redo.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "redo.png"), undo.do_redo_and_repaint)
    editor_window.undo_redo.widget.set_tooltip_text(_("Undo - Ctrl + X\nRedo - Ctrl + Y"))

    editor_window.tools_buttons = glassbuttons.GlassButtonsGroup(46, 23, 2, 14, 7)
    editor_window.tools_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "open_mixer.png"), audiomonitoring.show_audio_monitor)
    editor_window.tools_buttons.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "open_titler.png"), titler.show_titler)
    editor_window.tools_buttons.widget.set_tooltip_text(_("Audio Mixer\nTitler"))
    if editorstate.audio_monitoring_available == False:
        editor_window.tools_buttons.sensitive[0] = False
        editor_window.tools_buttons.widget.set_tooltip_text(_("Audio Mixer(not available)\nTitler"))

    editor_window.transition_button = glassbuttons.GlassButtonsGroup(46, 23, 2, 4, 5)
    editor_window.transition_button.add_button(gtk.gdk.pixbuf_new_from_file(IMG_PATH + "dissolve.png"), tlineaction.add_transition_pressed)
    editor_window.transition_button.widget.set_tooltip_text(_("Add Rendered Transition - 2 clips selected\nAdd Rendered Fade - 1 clip selected"))

def fill_with_TC_LEFT_pattern(buttons_row, window):
    global w
    w = window
    buttons_row.pack_start(w.big_TC.widget, False, True, 0)
    buttons_row.pack_start(guiutils.get_pad_label(7, MIDDLE_ROW_HEIGHT), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    buttons_row.pack_start(w.modes_selector.widget, False, True, 0)
    buttons_row.pack_start(gtk.Label(), True, True, 0)
    if editorstate.SCREEN_WIDTH > 1279:
        buttons_row.pack_start(_get_tools_buttons(), False, True, 0)
        buttons_row.pack_start(gtk.Label(), True, True, 0)
    buttons_row.pack_start(_get_undo_buttons_panel(), False, True, 0)
    buttons_row.pack_start(gtk.Label(), True, True, 0)
    buttons_row.pack_start(_get_zoom_buttons_panel(),False, True, 0)
    buttons_row.pack_start(gtk.Label(), True, True, 0)
    buttons_row.pack_start(_get_edit_buttons_panel(),False, True, 0)
    buttons_row.pack_start(gtk.Label(), True, True, 0)
    buttons_row.pack_start(_get_transition_button(), False, True, 0)
    buttons_row.pack_start(gtk.Label(), True, True, 0)
    buttons_row.pack_start(_get_monitor_insert_buttons(), False, True, 0)

def fill_with_TC_MIDDLE_pattern(buttons_row, window):
    global w
    w = window
    left_panel = gtk.HBox(False, 0)    
    left_panel.pack_start(_get_undo_buttons_panel(), False, True, 0)
    left_panel.pack_start(guiutils.get_pad_label(10, MIDDLE_ROW_HEIGHT), False, True, 0) #### NOTE!!!!!! THIS DETERMINES THE HEIGHT OF MIDDLE ROW
    left_panel.pack_start(_get_zoom_buttons_panel(), False, True, 0)
    if editorstate.SCREEN_WIDTH > 1279:
        left_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
        left_panel.pack_start(_get_tools_buttons(), False, True, 0)
        left_panel.pack_start(guiutils.get_pad_label(50, 10), False, True, 10) # to left and right panel same size for centering
    else:
        left_panel.pack_start(guiutils.get_pad_label(60, 10), False, True, 10) # to left and right panel same size for centering
    left_panel.pack_start(gtk.Label(), True, True, 0)

    middle_panel = gtk.HBox(False, 0) 
    middle_panel.pack_start(w.big_TC.widget, False, True, 0)
    middle_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
    middle_panel.pack_start(w.modes_selector.widget, False, True, 0)
    
    right_panel = gtk.HBox(False, 0) 
    right_panel.pack_start(gtk.Label(), True, True, 0)
    right_panel.pack_start(_get_edit_buttons_panel(), False, True, 0)
    right_panel.pack_start(guiutils.get_pad_label(10, 10), False, True, 0)
    right_panel.pack_start(_get_monitor_insert_buttons(), False, True, 0)

    buttons_row.pack_start(left_panel, True, True, 0)
    buttons_row.pack_start(middle_panel, False, False, 0)
    buttons_row.pack_start(right_panel, True, True, 0)

# These get methods are unnecessery, unless we later make possible to use differnt kinds of buttons
def _get_mode_buttons_panel():
    return w.mode_buttons_group.widget

def _get_zoom_buttons_panel():    
    return w.zoom_buttons.widget

def _get_undo_buttons_panel():
    return w.undo_redo.widget

def _get_edit_buttons_panel():
    return w.edit_buttons.widget

def _get_monitor_insert_buttons():
    return w.monitor_insert_buttons.widget

def _get_tools_buttons():
    return w.tools_buttons.widget

def _get_transition_button():
    return w.transition_button.widget

def _get_buttons_panel(btns_count, btn_width=BUTTON_WIDTH):
    panel = gtk.HBox(True, 0)
    panel.set_size_request(btns_count * btn_width, BUTTON_HEIGHT)
    return panel

def _b(button, icon, remove_relief=False):
    button.set_image(icon)
    button.set_property("can-focus",  False)
    if remove_relief:
        button.set_relief(gtk.RELIEF_NONE)

def _clear_container(cont):
    children = cont.get_children()
    for child in children:
        cont.remove(child)
