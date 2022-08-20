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
import threading
import time

import appconsts
import atomicfile
import dialogs
import dialogutils
import gui
import guicomponents
import guiutils
import edit
import editorlayout
import editorstate
from editorstate import current_sequence
from editorstate import PROJECT
import keyframeeditor
import mlttransitions
import propertyeditorbuilder
import propertyedit
import propertyparse
import tlinerender
import utils

widgets = utils.EmptyClass()

compositor = None # Compositor being edited.

# Edit polling.
# We didn't put a layer of indirection to look for and launch events on edits,
# so now we detect edits by polling. This has no performance impect, n is so small.
_edit_polling_thread = None
compositor_changed_since_last_save = False

# This is updated when filter panel is displayed and cleared when removed.
# Used to update kfeditors with external tline frame position changes.
keyframe_editor_widgets = []


def shutdown_polling():
    global _edit_polling_thread
    if _edit_polling_thread != None:
        _edit_polling_thread.shutdown()
        _edit_polling_thread = None

def create_widgets():
    """
    Widgets for editing compositing properties.
    """
    widgets.compositor_info = guicomponents.CompositorInfoPanel()
    widgets.hamburger_launcher = guicomponents.HamburgerPressLaunch(_hamburger_launch_pressed)
    widgets.hamburger_launcher.connect_launched_menu(guicomponents.clip_effects_hamburger_menu)
    guiutils.set_margins(widgets.hamburger_launcher.widget, 4, 6, 6, 0)

    widgets.empty_label = Gtk.Label(label=_("No Compositor"))

    # Edit area.
    widgets.value_edit_box = Gtk.VBox()
    widgets.value_edit_box.pack_start(widgets.empty_label, True, True, 0)
    widgets.value_edit_frame = Gtk.Frame()
    widgets.value_edit_frame.add(widgets.value_edit_box)
    widgets.value_edit_frame.set_shadow_type(Gtk.ShadowType.NONE)

def get_compositor_clip_panel():
    create_widgets()
    
    # Action row.
    action_row = Gtk.HBox(False, 2)
    action_row.pack_start(widgets.hamburger_launcher.widget, False, False, 0)
    action_row.pack_start(Gtk.Label(), True, True, 0)
    action_row.pack_start(widgets.compositor_info, False, False, 0)
    action_row.pack_start(Gtk.Label(), True, True, 0)
    
    set_enabled(False)
    
    return action_row

def compositing_mode_changed():
    # Edit area
    if current_sequence().compositing_mode != appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
        widgets.empty_label.set_text(_("No Compositor"))
    else:
        widgets.empty_label.set_text(_("Compositor panel not used in/n Standard Full track Compositing Mode"))
        widgets.empty_label.set_justify(Gtk.Justification.CENTER)
        
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

    editorlayout.show_panel(appconsts.PANEL_MULTI_EDIT)

    gui.editor_window.edit_multi.set_visible_child_name(appconsts.EDIT_MULTI_COMPOSITORS)

    global _edit_polling_thread
    # Close old polling
    if _edit_polling_thread != None:
        _edit_polling_thread.shutdown()
    # Start new polling
    _edit_polling_thread = PropertyChangePollingThread()
    _edit_polling_thread.start()

def clear_compositor():
    global compositor
    compositor = None
    widgets.compositor_info.set_no_compositor_info()
    _display_compositor_edit_box()
    set_enabled(False)
    shutdown_polling()

def set_enabled(value):
    widgets.empty_label.set_sensitive(value)
    widgets.compositor_info.set_enabled(value)
    widgets.hamburger_launcher.set_sensitive(value)

def maybe_clear_editor(killed_compositor):
    if compositor == None:
        return
    if killed_compositor.destroy_id == compositor.destroy_id:
        clear_compositor()

def get_compositor():
    return compositor

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
        filler = Gtk.EventBox()
        filler.add(Gtk.Label())
        vbox.pack_start(filler, True, True, 0)

        if current_sequence().compositing_mode != appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
            info = Gtk.Label(label=_("No Compositor"))
            info.set_sensitive(False)
        else:
            info = Gtk.Label(label=_("This panel not used in\n Compositing Mode Standard Full Track."))
            info.set_justify(Gtk.Justification.CENTER)
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
    if editorstate.get_compositing_mode() != appconsts.COMPOSITING_MODE_STANDARD_AUTO_FOLLOW:
        target_combo = guicomponents.get_compositor_track_select_combo(
                        current_sequence().tracks[compositor.transition.b_track], 
                        current_sequence().tracks[compositor.transition.a_track], 
                        _target_track_changed)

        target_row = Gtk.HBox()
        target_row.pack_start(guiutils.get_pad_label(5, 3), False, False, 0)
        target_row.pack_start(Gtk.Label(label=_("Destination Track:")), False, False, 0)
        target_row.pack_start(guiutils.get_pad_label(5, 3), False, False, 0)
        target_row.pack_start(target_combo, False, False, 0)

        vbox.pack_start(target_row, False, False, 0)
        vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)

    blend_added = False # for GUI prettyness.
    
    # Transition editors
    t_editable_properties = propertyedit.get_transition_editable_properties(compositor)
    for ep in t_editable_properties:
        editor_row = propertyeditorbuilder.get_editor_row(ep)
  
        # Add blend mode editor in top row if exists, we decided on this later to save vertical space.
        # Using display name is bit hacky, but should work.
        try:
            if ep.args["displayname"] == "Blend!Mode":
                target_row.pack_start(guiutils.get_pad_label(8, 3), False, False, 0)
                editor_row.remove(editor_row.get_children()[0])
                target_row.pack_start(editor_row, True, True, 0)
                blend_added = True
                continue
        except:
            pass # Not all EditablePropty objects have "displayname" arg, move on.
    
        # Add editor row in panel
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
            or (editor_type == propertyeditorbuilder.KEYFRAME_EDITOR_CLIP_FADE)
            or (editor_type == propertyeditorbuilder.FADE_LENGTH)
            or (editor_type == propertyeditorbuilder.GEOMETRY_EDITOR)
            or (editor_type == propertyeditorbuilder.ROTATION_GEOMETRY_EDITOR_BUILDER)):
                keyframe_editor_widgets.append(editor_row)
    
    # Add pad label after possibly adding blend mode editor.
    if blend_added == False:
        target_row.pack_start(Gtk.Label(), True, True, 0)
            
    # Extra editors. Editable properties have already been created with "editor=no_editor"
    # and will be looked up by editors from clip
    editor_rows = propertyeditorbuilder.get_transition_extra_editor_rows(compositor, t_editable_properties)
    for editor_row in editor_rows:
        # These are added to keyframe editors list based on editor type, not based on EditableProperty type as above
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

def update_kfeditors_sliders(frame):
    for kf_widget in keyframe_editor_widgets:
        kf_widget.update_slider_value_display(frame)
        
def update_kfeditors_positions():
    for kf_widget in keyframe_editor_widgets:
        kf_widget.update_clip_pos()


def _compositor_uses_fade_buttons(compositor):
    # we hard coded compositors using fade buttons here because adding data in compostors.xml may have had some backwards compatibility issues.
    if compositor.transition.info.name  == "##opacity":
        return True
    elif compositor.transition.info.name  == "##pict_in_pict":
        return True
    elif compositor.transition.info.name  == "##affine":
        return True
    elif compositor.transition.info.name  == "##opacity_kf":
        return True
    elif compositor.transition.info.name  == "##region":
        return True
    elif compositor.transition.info.name  == "##affineblend":
        return True
    elif compositor.transition.info.name  == "##blend":
        return True
        
        
    return False
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
    elif msg == "close":
        clear_compositor()
    elif msg == "fade_length":
        dialogs.set_fade_length_default_dialog(_set_fade_length_dialog_callback, PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH))
         
def _save_compositor_values_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        save_path = dialog.get_filenames()[0]
        compositor_data = CompositorValuesSaveData(compositor.transition.info, compositor.transition.properties)
        compositor_data.save(save_path)
    
    dialog.destroy()

def _load_compositor_values_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        load_path = dialog.get_filenames()[0]
        compositor_data = utils.unpickle(load_path)

        if compositor_data.data_applicable(compositor.transition.info):
            compositor_data.set_values(compositor)
            set_compositor(compositor)
        else:
            saved_name_comp_name = mlttransitions.name_for_type[compositor_data.info.name]
            current_comp_name = mlttransitions.name_for_type[compositor.transition.info.name]
            primary_txt = _("Saved Compositor data not applicable for this compositor!")
            secondary_txt = _("Saved data is for ") + saved_name_comp_name + " compositor,\n" + _(", current compositor is ") + current_comp_name + "."
            dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window)

    dialog.destroy()

def _set_fade_length_dialog_callback(dialog, response_id, spin):
    if response_id == Gtk.ResponseType.ACCEPT:
        default_length = int(spin.get_value())
        PROJECT().set_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH, default_length)
        
    dialog.destroy()

class PropertyChangePollingThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.last_properties = None
        
    def run(self):
        self.running = True
        while self.running:
            global compositor
            if compositor == None:
                self.shutdown()
            else:
                if self.last_properties == None:
                    self.last_properties = self.get_compositor_properties()
                
                new_properties = self.get_compositor_properties()
                
                changed = False
                for new_prop, old_prop in zip(new_properties, self.last_properties):
                    if new_prop != old_prop:
                        changed = True

                if changed:
                    global compositor_changed_since_last_save
                    compositor_changed_since_last_save = True
                    tlinerender.get_renderer().timeline_changed()

                self.last_properties = new_properties
                
                time.sleep(1.0)
                
    def get_compositor_properties(self):
        compositor_properties = []

        for prop in compositor.transition.properties:
            compositor_properties.append(copy.deepcopy(prop))
    
        compositor_properties.append((copy.deepcopy(compositor.clip_in ), copy.deepcopy(compositor.clip_out)))
        
        return compositor_properties
        
    def shutdown(self):
        self.running = False
        

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
        
