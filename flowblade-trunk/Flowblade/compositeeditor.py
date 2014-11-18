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
Module handles clips compositing gui.
"""

import copy
import pygtk
pygtk.require('2.0');
import gtk


import gui
import guicomponents
import guiutils
import edit
from editorstate import current_sequence
import editorpersistance
import propertyeditorbuilder
import propertyedit
import propertyparse
import utils

COMPOSITOR_PANEL_LEFT_WIDTH = 160

widgets = utils.EmptyClass()

compositor = None # Compositor being edited.

# This is updated when filter panel is displayed and cleared when removed.
# Used to update kfeditors with external tline frame position changes
keyframe_editor_widgets = []

def create_widgets():
    """
    Widgets for editing compositing properties.
    """
    # Left side
    widgets.compositor_info = guicomponents.CompositorInfoPanel()
    widgets.delete_b = gtk.Button(_("Delete"))
    widgets.delete_b.connect("clicked", lambda w,e: _delete_compositor_pressed(), None)
    widgets.reset_b = gtk.Button(_("Reset"))
    widgets.reset_b.connect("clicked", lambda w,e: _reset_compositor_pressed(), None)
    
    # Right side
    widgets.empty_label = gtk.Label(_("No Compositor"))
    widgets.value_edit_box = gtk.VBox()
    widgets.value_edit_box.pack_start(widgets.empty_label, True, True, 0)
    widgets.value_edit_frame = gtk.Frame()
    widgets.value_edit_frame.add(widgets.value_edit_box)

def get_compositor_clip_panel():
    create_widgets()
    
    compositor_vbox = gtk.VBox(False, 2)
    compositor_vbox.pack_start(widgets.compositor_info, False, False, 0)
    compositor_vbox.pack_start(gtk.Label(), True, True, 0)
    compositor_vbox.pack_start(widgets.reset_b, False, False, 0)
    compositor_vbox.pack_start(widgets.delete_b, False, False, 0)
    compositor_vbox.pack_start(guiutils.get_pad_label(5, 3), False, False, 0)
    compositor_vbox.set_size_request(COMPOSITOR_PANEL_LEFT_WIDTH, 200)

    set_enabled(False)
    
    return compositor_vbox
    
def set_compositor(new_compositor):
    """
    Sets clip to be edited in compositor editor.
    """
    global compositor
    if compositor != None and new_compositor.destroy_id != compositor.destroy_id:
        compositor.selected = False
    compositor = new_compositor

    widgets.compositor_info.display_compositor_info(compositor)

    set_enabled(True)
    _display_compositor_edit_box()
    if editorpersistance.prefs.default_layout == True:
        gui.middle_notebook.set_current_page(3)
    else:
        gui.editor_window.right_notebook.set_current_page(2)

def clear_compositor():
    global compositor
    compositor = None
    widgets.compositor_info.set_no_compositor_info()
    _display_compositor_edit_box()
    set_enabled(False)

def set_enabled(value):
    widgets.empty_label.set_sensitive(value)
    widgets.compositor_info.set_enabled(value)
    widgets.delete_b.set_sensitive(value)
    widgets.reset_b.set_sensitive(value)

def maybe_clear_editor(killed_compositor):
    if killed_compositor.destroy_id == compositor.destroy_id:
        clear_compositor()

def _delete_compositor_pressed():
    data = {"compositor":compositor}
    action = edit.delete_compositor_action(data)
    action.do_edit()

def _reset_compositor_pressed():
    global compositor
    compositor.transition.properties = copy.deepcopy(compositor.transition.info.properties)
    propertyparse.replace_value_keywords(compositor.transition.properties, current_sequence().profile)
    compositor.transition.update_editable_mlt_properties()
    _display_compositor_edit_box()

def _display_compositor_edit_box():
    # This gets called on startup before edit_frame is filled
    try:
        widgets.value_edit_frame.remove(widgets.value_edit_box)
    except:
        pass

    global keyframe_editor_widgets
    keyframe_editor_widgets = []

    vbox = gtk.VBox()

    # case: Empty edit frame
    global compositor
    if compositor == None:
        widgets.empty_label = gtk.Label(_("No Compositor"))
        vbox.pack_start(widgets.empty_label, True, True, 0)

        vbox.pack_start(gtk.Label(), True, True, 0)  
        vbox.show_all()
        widgets.value_edit_box = vbox
        widgets.value_edit_frame.add(vbox)
        return 
    
    compositor_name_label = gtk.Label( "<b>" + compositor.name + "</b>")
    compositor_name_label.set_use_markup(True)
    vbox.pack_start(compositor_name_label, False, False, 0)
    vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)

    # Track editor
    target_combo = guicomponents.get_compositor_track_select_combo(
                    current_sequence().tracks[compositor.transition.b_track], 
                    current_sequence().tracks[compositor.transition.a_track], 
                    _target_track_changed)

    target_row = gtk.HBox()
    target_row.pack_start(guiutils.get_pad_label(5, 3), False, False, 0)
    target_row.pack_start(gtk.Label(_("Destination Track:")), False, False, 0)
    target_row.pack_start(guiutils.get_pad_label(5, 3), False, False, 0)
    target_row.pack_start(target_combo, False, False, 0)
    target_row.pack_start(gtk.Label(), True, True, 0)
    vbox.pack_start(target_row, False, False, 0)
    vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)

    # Transition editors
    t_editable_properties = propertyedit.get_transition_editable_properties(compositor)
    for ep in t_editable_properties:
        editor_row = propertyeditorbuilder.get_editor_row(ep)
        if editor_row != None: # Some properties don't have editors
            vbox.pack_start(editor_row, False, False, 0)
            vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)

        # Add keyframe editor widget to be updated for frame changes if such is created.
        try:
            editor_type = ep.args[propertyeditorbuilder.EDITOR]
        except KeyError:
            editor_type = propertyeditorbuilder.SLIDER # this is the default value
        if ((editor_type == propertyeditorbuilder.KEYFRAME_EDITOR)
            or (editor_type == propertyeditorbuilder.KEYFRAME_EDITOR_RELEASE)
            or (editor_type == propertyeditorbuilder.KEYFRAME_EDITOR_CLIP)
            or (editor_type == propertyeditorbuilder.GEOMETRY_EDITOR)):
                keyframe_editor_widgets.append(editor_row)
    
    # Extra editors. Editable properties have already been created with "editor=no_editor"
    # and will be looked up by editors from clip
    editor_rows = propertyeditorbuilder.get_transition_extra_editor_rows(compositor, t_editable_properties)
    for editor_row in editor_rows:
        vbox.pack_start(editor_row, False, False, 0)
        vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)
    
    vbox.pack_start(gtk.Label(), True, True, 0)  
    vbox.show_all()

    scroll_window = gtk.ScrolledWindow()
    scroll_window.add_with_viewport(vbox)
    scroll_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    scroll_window.show_all()

    widgets.value_edit_box = scroll_window
    widgets.value_edit_frame.add(scroll_window)

def _target_track_changed(combo):
    if combo.get_active() == 0:
        force = True
    else:
        force = False
    a_track = compositor.transition.b_track - combo.get_active() - 1
    compositor.transition.set_target_track(a_track, force)
    widgets.compositor_info.display_compositor_info(compositor)

def display_kfeditors_tline_frame(frame):
    for kf_widget in keyframe_editor_widgets:
        kf_widget.display_tline_frame(frame)

def update_kfeditors_positions():
    for kf_widget in keyframe_editor_widgets:
        kf_widget.update_clip_pos()
