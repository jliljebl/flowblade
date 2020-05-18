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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from gi.repository import GObject

import copy
import os

import guicomponents
import guiutils
import simpleeditors

EDITOR_PANEL_LEFT_LABEL_WIDTH = 220
EDITOR_PANEL_BUTTON_WIDTH = 150

# Editor targets
BLENDER_OBJECTS = 1
BLENDER_MATERIALS = 2
BLENDER_CURVES = 3

_editor_manager_window = None

def show_container_data_program_editor_dialog(container_data):
    global _editor_manager_window
    # Only Blender has this for now
    _editor_manager_window = BlenderProjectEditorManagerWindow(container_data)

def _shutdown_save():
    # Edits already saved, destroy window.
    _editor_manager_window.destroy()

def _shutdown_cancel():
    # Roll back changes.
    _editor_manager_window.container_data.data_slots["project_edit_info"] = _editor_manager_window.original_edit_data
    
    _editor_manager_window.destroy()
    
     
class BlenderProjectEditorManagerWindow(Gtk.Window):
    
    def __init__(self, container_data):
        GObject.GObject.__init__(self)
        self.edit_targets = BLENDER_OBJECTS
        
        self.connect("delete-event", lambda w, e:_shutdown_cancel())

        self.container_data = container_data
        self.original_edit_data = copy.deepcopy(self.container_data.data_slots["project_edit_info"])

        folder, project_name = os.path.split(self.container_data.program)

        info_row = self.get_info_row()

        panel_objects = self.get_targets_panel()
        guiutils.set_margins(panel_objects, 12, 12, 12, 4)
        
        panel_editors = self.get_editors_panel()
        panel_editors.set_size_request(800, 400)
        guiutils.set_margins(panel_editors, 12, 12, 0, 6)

        edit_pane = Gtk.HBox(False, 2)
        edit_pane.pack_start(panel_objects, False, False, 0)
        edit_pane.pack_start(panel_editors, True, True, 0)
        
        self.save_button = Gtk.Button(_("Save Changes"))
        self.save_button.connect("clicked",lambda w: _shutdown_save())
        self.save_button.set_sensitive(False)
        self.save_button.set_tooltip_markup(_("Add or delete editors to enable <b>Save Changes</b> button"))
        cancel_button = Gtk.Button(_("Cancel"))
        cancel_button.connect("clicked",lambda w: _shutdown_cancel())
        buttons_box = Gtk.HBox(True, 2)
        buttons_box.pack_start(cancel_button, True, True, 0)
        buttons_box.pack_start(self.save_button, False, False, 0)
        
        buttons_row = Gtk.HBox(False, 2)
        buttons_row.pack_start(Gtk.Label(), True, True, 0)
        buttons_row.pack_start(buttons_box, False, False, 0)

        pane = Gtk.VBox(False, 2)
        pane.pack_start(info_row, False, False, 0)
        pane.pack_start(edit_pane, True, True, 0)
        pane.pack_start(buttons_row, False, False, 0)

        align = guiutils.set_margins(pane, 12, 12, 12, 12)

        self.targets_list.connect_selection_changed(self.target_selection_changed)
        self.targets_list.treeview.get_selection().select_path(Gtk.TreePath.new_from_string("0"))
        
        # Set pane and show window
        self.add(align)
        self.set_title(_("Blender Project Property Editors") + " - " + project_name)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()
        self.set_resizable(False)

    def get_info_row(self):
        folder, project_file = os.path.split(self.container_data.program)
        project_name_label = Gtk.Label(label=project_file)

        self.targets_select = Gtk.ComboBoxText()
        self.targets_select.append_text(_("Objects"))
        self.targets_select.append_text(_("Materials"))
        self.targets_select.append_text(_("Curves"))
        self.targets_select.set_active(0)
        self.targets_select.connect("changed", self.edit_targets_changed)  

        project_box = Gtk.HBox(False, 2)
        project_box.pack_start(guiutils.set_margins(guiutils.bold_label("Blender Project:"), 0, 0, 0, 4), False, False, 0)
        project_box.pack_start(project_name_label, False, False, 0)
        project_box.pack_start(Gtk.Label(), True, True, 0)
        
        self.editors_count_label = Gtk.Label("0")
        editors_box = Gtk.HBox(False, 2)
        editors_box.pack_start(guiutils.set_margins(guiutils.bold_label("Blender Project:"), 0, 0, 0, 4), False, False, 0)
        editors_box.pack_start(self.editors_count_label, False, False, 0)
        editors_box.pack_start(Gtk.Label(), True, True, 0)
        
        info_row = Gtk.HBox(True, 2)
        info_row.pack_start(project_box, True, True, 0)
        info_row.pack_start(editors_box, False, False, 0)
        
        info_row_full = Gtk.HBox(False, 2)
        info_row_full.pack_start(self.targets_select, True, True, 0)
        info_row_full.pack_start(guiutils.pad_label(24,4), False, False, 0)
        info_row_full.pack_start(info_row, False, False, 0)
        
        return info_row_full

    def get_targets_panel(self):
        self.targets_list = guicomponents.TextTextListView()

        self.fill_targets_list()

        self.targets_frame = guiutils.get_named_frame(_("Blender Project Objects"), self.targets_list)

        vbox = Gtk.VBox(True, 2)
        vbox.pack_start(self.targets_frame, True, True, 0)
        return vbox

    def get_editors_panel(self):
        self.editors_list = guicomponents.MultiTextColumnListView(5)
        guiutils.set_margins(self.editors_list, 0, 12, 0, 6)
        self.editors_list.set_size_request(900, 360)

        titles = [_("Property Path"), _("Label"), _("Info"), _("Type"), _("Value")]
        self.editors_list.set_column_titles(titles)
    
        # --- widgets
        add_button = Gtk.Button(label=_("Add Editor"))
        add_button.connect("clicked", lambda w: self.add_clicked())
        self.delete_button = Gtk.Button(label=_("Delete Editor"))
        self.delete_button.set_sensitive(False)
        self.delete_button.connect("clicked", lambda w: self.delete_clicked())
        
        self.obj_path_entry = Gtk.Entry()
        self.editor_label_entry = Gtk.Entry()
        self.tooltip_info_entry = Gtk.Entry() 
        self.default_value_entry = Gtk.Entry()
        self.default_value_entry.set_text(simpleeditors.DEFAULT_VALUES[simpleeditors.SIMPLE_EDITOR_STRING])
        
        self.editor_select = simpleeditors.get_simple_editor_selector(0, self.editor_selection_changed)

        # --- object path row right.
        self.obj_path_label = Gtk.Label()
        self.obj_path_label.set_use_markup(True)
        obj_path_row_right = Gtk.HBox(False, 2)
        obj_path_row_right.pack_start(guiutils.pad_label(4, 4), False, False, 0)
        obj_path_row_right.pack_start(self.obj_path_label, False, False, 0)
        obj_path_row_right.pack_start(self.obj_path_entry, False, False, 0)
        
        # --- panels
        editor_add_right = Gtk.VBox(False, 2)
        editor_add_right.pack_start(add_button, False, False, 0)
        editor_add_right.pack_start(Gtk.Label(), True, True, 0)
        
        editor_add_left = Gtk.VBox(True, 2)
        editor_add_left.pack_start(guiutils.bold_label(_("New Editor Properties")), False, False, 0)
        editor_add_left.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Blender Object Property Path:")), obj_path_row_right, EDITOR_PANEL_LEFT_LABEL_WIDTH), False, False, 0)
        editor_add_left.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Editor Label:")), self.editor_label_entry, EDITOR_PANEL_LEFT_LABEL_WIDTH), False, False, 0)
        editor_add_left.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Tooltip Info:")), self.tooltip_info_entry, EDITOR_PANEL_LEFT_LABEL_WIDTH), False, False, 0)
        editor_add_left.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Editor Type:")), self.editor_select, EDITOR_PANEL_LEFT_LABEL_WIDTH), False, False, 0)
        editor_add_left.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Default Value:")), self.default_value_entry, EDITOR_PANEL_LEFT_LABEL_WIDTH), False, False, 0)
        
        add_row = guiutils.get_two_column_box(editor_add_right, editor_add_left, EDITOR_PANEL_BUTTON_WIDTH)
        delete_row = guiutils.get_two_column_box(self.delete_button , Gtk.Label(), EDITOR_PANEL_BUTTON_WIDTH)
        
        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(self.editors_list, True, True, 0)
        vbox.pack_start(add_row, False, False, 0)
        vbox.pack_start(delete_row, False, False, 0)

        panel = Gtk.VBox(True, 2)
        self.object_editors_frame = guiutils.get_named_frame("to be replaced", vbox)
        panel.pack_start(self.object_editors_frame, True, True, 0)
        return panel

    def get_edit_targets(self):
        info_json = self.container_data.data_slots["project_edit_info"] 
        if self.edit_targets == BLENDER_OBJECTS:
            return info_json["objects"]
        elif self.edit_targets == BLENDER_MATERIALS:
            return info_json["materials"]
        elif self.edit_targets == BLENDER_CURVES:
            return info_json["curves"]
            
    def fill_targets_list(self):
        self.targets_list.storemodel.clear()
        targets = self.get_edit_targets()
        for t in targets:
            row_data = [t[0], t[1]] # obj is list [name, object_type]
            self.targets_list.storemodel.append(row_data)
            
    def get_editors_list_title(self, obj_name):
        if self.edit_targets == BLENDER_OBJECTS:
            return "<b>" + _("Object Editors for ") + "'" + obj_name +  "'" + "</b>"
        elif self.edit_targets == BLENDER_MATERIALS:
            return "<b>" + _("Materials Editors for ") + "'" + obj_name +  "'" + "</b>"
        elif self.edit_targets == BLENDER_CURVES:
            return "<b>" + _("Curves Editors for ") + "'" + obj_name +  "'" + "</b>"
            
    def get_selected_object(self):
        targets = self.get_edit_targets()
        return targets[self.targets_list.get_selected_row_index()]

    def edit_targets_changed(self, w):
        if w.get_active() == 0:
            self.edit_targets = BLENDER_OBJECTS
        elif w.get_active() == 1:
            self.edit_targets = BLENDER_MATERIALS
        else:
            self.edit_targets = BLENDER_CURVES

        self.fill_targets_list()
        self.targets_list.treeview.get_selection().select_path(Gtk.TreePath.new_from_string("0"))
                    
    def target_selection_changed(self, tree_selection):
        try:
            obj = self.get_selected_object()
        except:
            # storemodel.clear() list triggers "changed" and self.get_selected_object() crashes if this event 
            # is from there. We will move forward with the intentional selection made after list filled properly.
            return
               
        self.display_object_editors_data(obj)
        
        if self.edit_targets == BLENDER_OBJECTS:
            obj_text = '<i>bpy.data.objects["' + obj[0] + '"].</i>'
        elif self.edit_targets == BLENDER_MATERIALS:
            obj_text = '<i>bpy.data.materials["' + obj[0] + '"].</i>'
        elif self.edit_targets == BLENDER_CURVES:
            obj_text = '<i>bpy.data.curves["' + obj[0] + '"].</i>'
            
        self.obj_path_label.set_markup(obj_text)
        
        editors_frame_title = self.get_editors_list_title(obj[0])
        self.object_editors_frame.name_label.set_use_markup(True)
        self.object_editors_frame.name_label.set_markup(editors_frame_title)
        
        if len(obj[2]) > 0:
            path = Gtk.TreePath.new_from_indices([0])
            self.editors_list.treeview.get_selection().select_path(path)
            self.delete_button.set_sensitive(True)
        else:
            self.delete_button.set_sensitive(False)

    def display_object_editors_data(self, obj):
        editors_list = obj[2]  # object is [name, type, editors_list] see blenderprojectinit.py
        self.editors_list.fill_data_model(editors_list)

    def add_clicked(self):
        editor_data = self.get_current_editor_data()
        obj = self.get_selected_object()
        obj[2].append(editor_data)
        self.display_object_editors_data(obj)
        self.save_button.set_sensitive(True)
        self.delete_button.set_sensitive(True)
        path = Gtk.TreePath.new_from_indices([len(obj[2]) - 1])
        self.editors_list.treeview.get_selection().select_path(path)
        self.clear_editors()

    def delete_clicked(self):
        selected_row_index = self.editors_list.get_selected_row_index()
        obj = self.get_selected_object()
        obj[2].pop(selected_row_index)
        self.target_selection_changed(None)

    def get_current_editor_data(self):
        editor_data = []
        # [prop_path, label, tooltip, editor_type, value]
        editor_data.append(self.obj_path_entry.get_text())
        editor_data.append(self.editor_label_entry.get_text())
        editor_data.append(self.tooltip_info_entry.get_text())
        editor_data.append(str(self.editor_select.get_active()))
        text = self.default_value_entry.get_text()
        if self.editor_select.get_active() == simpleeditors.SIMPLE_EDITOR_STRING:
             text = '"' + text + '"'
        editor_data.append(text)
        return editor_data

    def clear_editors(self):
        self.obj_path_entry.set_text("")
        self.editor_label_entry.set_text("")
        self.tooltip_info_entry.set_text("")
        self.editor_select.set_active(0)
        self.default_value_entry.set_text("")

    def editor_selection_changed(self, combo):
        value = simpleeditors.DEFAULT_VALUES[combo.get_active()]
        self.default_value_entry.set_text(value)
        
