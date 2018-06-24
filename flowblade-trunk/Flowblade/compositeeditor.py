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
Module handles Compositors edit panel.
"""

import copy
from gi.repository import Gtk
import pickle

import atomicfile
import compositorfades
import dialogs
import dialogutils
import gui
import guicomponents
import guiutils
import edit
from editorstate import current_sequence
import editorpersistance
import keyframeeditor
import mlttransitions
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

compositor_notebook_index = 3 # this is set 2 for the 2 window mode

def create_widgets():
    """
    Widgets for editing compositing properties.
    """
    widgets.compositor_info = guicomponents.CompositorInfoPanel()
    widgets.hamburger_launcher = guicomponents.HamburgerPressLaunch(_hamburger_launch_pressed)
    guiutils.set_margins(widgets.hamburger_launcher.widget, 4, 6, 6, 0)
    
    # Edit area
    widgets.empty_label = Gtk.Label(label=_("No Compositor"))
    widgets.value_edit_box = Gtk.VBox()
    widgets.value_edit_box.pack_start(widgets.empty_label, True, True, 0)
    widgets.value_edit_frame = Gtk.Frame()
    widgets.value_edit_frame.add(widgets.value_edit_box)
    widgets.value_edit_frame.set_shadow_type(Gtk.ShadowType.NONE)

def get_compositor_clip_panel():
    create_widgets()
    
    # Action row
    action_row = Gtk.HBox(False, 2)
    action_row.pack_start(widgets.hamburger_launcher.widget, False, False, 0)
    action_row.pack_start(Gtk.Label(), True, True, 0)
    action_row.pack_start(widgets.compositor_info, False, False, 0)
    action_row.pack_start(Gtk.Label(), True, True, 0)
    
    set_enabled(False)
    
    return action_row
    
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
        gui.middle_notebook.set_current_page(compositor_notebook_index)

def clear_compositor():
    global compositor
    compositor = None
    widgets.compositor_info.set_no_compositor_info()
    _display_compositor_edit_box()
    set_enabled(False)

def set_enabled(value):
    widgets.empty_label.set_sensitive(value)
    widgets.compositor_info.set_enabled(value)
    widgets.hamburger_launcher.set_sensitive(value)

def maybe_clear_editor(killed_compositor):
    if compositor == None:
        return
    if killed_compositor.destroy_id == compositor.destroy_id:
        clear_compositor()

def _add_fade_in_pressed():
    compositorfades.add_fade_in(compositor, int(widgets.fade_in_spin.get_value()))
    # We need GUI reload to show results
    set_compositor(compositor)

def _add_fade_out_pressed():
    compositorfades.add_fade_out(compositor, int(widgets.fade_out_spin.get_value()))
    # We need GUI reload to show results
    set_compositor(compositor)

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

    vbox = Gtk.VBox()

    # Case: Empty edit frame
    global compositor
    if compositor == None:
        #widgets.empty_label = Gtk.Label(label=_("No Compositor"))

        filler = Gtk.EventBox()
        filler.add(Gtk.Label())
        vbox.pack_start(filler, True, True, 0)
        
        info = Gtk.Label(label=_("No Compositor"))
        info.set_sensitive(False)
        filler = Gtk.EventBox()
        filler.add(info)
        vbox.pack_start(filler, False, False, 0)
        
        filler = Gtk.EventBox()
        filler.add(Gtk.Label())
        vbox.pack_start(filler, True, True, 0)
        vbox.show_all()

        scroll_window = Gtk.ScrolledWindow()
        scroll_window.add_with_viewport(vbox)
        scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll_window.show_all()

        widgets.value_edit_box = scroll_window
        widgets.value_edit_frame.add(scroll_window)
        return 

    # Case: Filled frame
    compositor_name_label = Gtk.Label(label= "<b>" + compositor.name + "</b>")
    compositor_name_label.set_use_markup(True)
    vbox.pack_start(compositor_name_label, False, False, 0)
    vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)

    # Track editor
    target_combo = guicomponents.get_compositor_track_select_combo(
                    current_sequence().tracks[compositor.transition.b_track], 
                    current_sequence().tracks[compositor.transition.a_track], 
                    _target_track_changed)

    target_row = Gtk.HBox()
    target_row.pack_start(guiutils.get_pad_label(5, 3), False, False, 0)
    target_row.pack_start(Gtk.Label(label=_("Destination Track:")), False, False, 0)
    target_row.pack_start(guiutils.get_pad_label(5, 3), False, False, 0)
    target_row.pack_start(target_combo, False, False, 0)
    target_row.pack_start(Gtk.Label(), True, True, 0)
    vbox.pack_start(target_row, False, False, 0)
    vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)

    # Fade buttons
    compositor_info = guicomponents.CompositorInfoPanel()
    fade_in_b = Gtk.Button(_("Add Fade In"))
    fade_in_b.connect("clicked", lambda w,e: _add_fade_in_pressed(), None)

    fade_out_b = Gtk.Button(_("Add Fade Out"))
    fade_out_b.connect("clicked", lambda w,e: _add_fade_out_pressed(), None)

    fade_in_spin = Gtk.SpinButton.new_with_range(0, 150, 1)
    fade_in_spin.set_value(10)
    
    fade_out_spin = Gtk.SpinButton.new_with_range(0, 150, 1)
    fade_out_spin.set_value(10)
    
    fades_row = Gtk.HBox()
    fades_row.pack_start(guiutils.get_pad_label(5, 3), False, False, 0)
    fades_row.pack_start(fade_in_b, False, False, 0)
    fades_row.pack_start(fade_in_spin, False, False, 0)
    fades_row.pack_start(fade_out_b, False, False, 0)
    fades_row.pack_start(fade_out_spin, False, False, 0)
    fades_row.pack_start(Gtk.Label(), True, True, 0)
    
    vbox.pack_start(fades_row, False, False, 0)
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
            or (editor_type == propertyeditorbuilder.FADE_LENGTH)
            or (editor_type == propertyeditorbuilder.GEOMETRY_EDITOR)):
                keyframe_editor_widgets.append(editor_row)
    
    # Extra editors. Editable properties have already been created with "editor=no_editor"
    # and will be looked up by editors from clip
    editor_rows = propertyeditorbuilder.get_transition_extra_editor_rows(compositor, t_editable_properties)
    for editor_row in editor_rows:
        # These are added to keyframe editor based on editor type, not based on EditableProperty type as above
        # because one editor sets values for multiple EditableProperty objects
        if editor_row.__class__ == keyframeeditor.RotatingGeometryEditor:
            keyframe_editor_widgets.append(editor_row)
        vbox.pack_start(editor_row, False, False, 0)
        vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)


        
    vbox.pack_start(Gtk.Label(), True, True, 0)  
    vbox.show_all()

    scroll_window = Gtk.ScrolledWindow()
    scroll_window.add_with_viewport(vbox)
    scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
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

# ----------------------------------------------------------- hamburger menu
def _hamburger_launch_pressed(widget, event):
    guicomponents.get_compositor_editor_hamburger_menu(event, _compositor_hamburger_item_activated)

def _compositor_hamburger_item_activated(widget, msg):
    if msg == "save":
        comp_name = mlttransitions.name_for_type[compositor.transition.info.name]
        default_name = comp_name.replace(" ", "_") + _("_compositor_values") + ".data"
        dialogs.save_effects_compositors_values(_save_compositor_values_dialog_callback, default_name, False)
    elif msg == "load":
        dialogs.load_effects_compositors_values_dialog(_load_compositor_values_dialog_callback, False)
    elif msg == "reset":
        _reset_compositor_pressed()
    elif msg == "delete":
        _delete_compositor_pressed()

def _save_compositor_values_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        save_path = dialog.get_filenames()[0]
        compositor_data = CompositorValuesSaveData(compositor.transition.info, compositor.transition.properties)
        compositor_data.save(save_path)
    
    dialog.destroy()

def _load_compositor_values_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        load_path = dialog.get_filenames()[0]
        f = open(load_path)
        compositor_data = pickle.load(f)

        if compositor_data.data_applicable(compositor.transition.info):
            compositor_data.set_values(compositor)
            set_compositor(compositor)
        else:
            saved_name_comp_name = mlttransitions.name_for_type[compositor_data.info.name]
            current_comp_name = mlttransitions.name_for_type[compositor.transition.info.name]
            primary_txt = _("Saved Compositor data not applicaple for this compositor!")
            secondary_txt = _("Saved data is for ") + saved_name_comp_name + " compositor,\n" + _(", current compositor is ") + current_comp_name + "."
            dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window)

    dialog.destroy()


class CompositorValuesSaveData:
    
    def __init__(self, info, properties):
        self.info = info
        self.properties = copy.deepcopy(properties)

    def save(self, save_path):
        with atomicfile.AtomicFileWriter(save_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(self, write_file)
        
    def data_applicable(self, compositor_info):        
        if isinstance(self.info, compositor_info.__class__):
            return self.info.__dict__ == compositor_info.__dict__
        return False
        
    def set_values(self, compositor):
        compositor.transition.properties = copy.deepcopy(self.properties)
        compositor.transition.update_editable_mlt_properties()
        
