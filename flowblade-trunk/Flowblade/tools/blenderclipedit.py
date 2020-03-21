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

import os

import guicomponents
import guiutils

EDITOR_PANEL_LEFT_LABEL_WIDTH = 150
EDITOR_PANEL_BUTTON_WIDTH = 150
 

_editor_manager_window = None

def show_project_editor_manager_dialog(container_data):
    global _editor_manager_window
    _editor_manager_window = EditorManagerWindow(container_data)


class EditorManagerWindow(Gtk.Window):
    def __init__(self, container_data):
        GObject.GObject.__init__(self)
        #self.connect("delete-event", lambda w, e:_shutdown())

        self.container_data = container_data

        info_row = self.get_info_row()

        panel_objects = self.get_objects_panel()
        guiutils.set_margins(panel_objects, 12, 12, 12, 4)
        
        panel_editors = self.get_editors_panel() 
        guiutils.set_margins(panel_editors, 12, 12, 0, 6)

        edit_pane = Gtk.HBox(False, 2)
        edit_pane.pack_start(panel_objects, False, False, 0)
        edit_pane.pack_start(panel_editors, True, True, 0)
        edit_pane.set_size_request(750, 600)
        
        save_button = Gtk.Button(_("Save Changes"))
        cancel_button = Gtk.Button(_("Cancel"))
        buttons_box = Gtk.HBox(True, 2)
        buttons_box.pack_start(cancel_button, True, True, 0)
        buttons_box.pack_start(save_button, False, False, 0)
        
        buttons_row = Gtk.HBox(False, 2)
        buttons_row.pack_start(Gtk.Label(), True, True, 0)
        buttons_row.pack_start(buttons_box, False, False, 0)

        pane = Gtk.VBox(False, 2)
        pane.pack_start(info_row, False, False, 0)
        pane.pack_start(edit_pane, False, False, 0)
        pane.pack_start(guiutils.pad_label(24,24), False, False, 0)
        pane.pack_start(buttons_row, True, True, 0)

        align = guiutils.set_margins(pane, 12, 12, 12, 12)

        self.objects_list.connect_selection_changed(self.object_selection_changed)
        self.objects_list.treeview.get_selection().select_path(Gtk.TreePath.new_from_string("0"))
        
        # Set pane and show window
        self.add(align)
        self.set_title(_("Media Relinker"))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()
        self.set_resizable(False)

    def get_info_row(self):
        folder, project_file = os.path.split(self.container_data.program)
        project_name_label = Gtk.Label(label=project_file)
        
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
        return info_row
        
    def get_objects_panel(self):
        self.objects_list = guicomponents.TextTextListView()
        
        self.objects_list.storemodel.clear()
        info_json = self.container_data.data_slots["project_edit_info"] 
        objects = info_json["objects"]
        for obj in objects:
            row_data = [obj[0], obj[1]] # obj is list [name, object_type]
            self.objects_list.storemodel.append(row_data)

        vbox = Gtk.VBox(True, 2)
        vbox.pack_start(guiutils.get_named_frame(_("Blender Project Objects"), self.objects_list), True, True, 0)
        return vbox
    
    def get_editors_panel(self):
        self.editors_list = guicomponents.MultiTextColumnListView(5)
        guiutils.set_margins(self.editors_list, 0, 12, 0, 6)

        # --- widgets
        add_button = Gtk.Button(label=_("Add Editor"))
        add_button.connect("clicked",lambda w: self.add_clicked())
        self.delete_button = Gtk.Button(label=_("Delete Editor"))
        
        self.obj_path_entry = Gtk.Entry()
        self.editor_label_entry = Gtk.Entry()
        self.tooltip_info_entry = Gtk.Entry() 
        self.default_value_entry = Gtk.Entry() 
        
        self.editor_select = Gtk.ComboBoxText()
        self.editor_select.append_text(_("Text Entry"))
        self.editor_select.append_text(_("Float Number"))
        self.editor_select.set_active(0)

        # --- panels
        editor_add_right = Gtk.VBox(True, 2)
        editor_add_right.pack_start(add_button, False, False, 0)
        editor_add_right.pack_start(Gtk.Label(), True, True, 0)
        
        editor_add_left = Gtk.VBox(True, 2)
        editor_add_left.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Property Path:")), self.obj_path_entry, EDITOR_PANEL_LEFT_LABEL_WIDTH), False, False, 0)
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
        panel.pack_start(guiutils.get_named_frame(_("Object Editors"), vbox), True, True, 0)
        return panel

    def get_selected_object(self):
        info_json = self.container_data.data_slots["project_edit_info"] 
        objects = info_json["objects"]
        return objects[self.objects_list.get_selected_row_index()]
        
    def object_selection_changed(self, tree_selection):
        obj = self.get_selected_object()
        self.display_object_editors_data(obj)
        
    def display_object_editors_data(self, obj):
        print(obj)
        editors_list = obj[2]
        self.editors_list.fill_data_model(editors_list)
    
    def add_clicked(self):
        editor_data = self.get_current_editor_data()
        print(editor_data)
        obj = self.get_selected_object()
        obj[2].append(editor_data)
        self.display_object_editors_data(obj)

    def get_current_editor_data(self):
        editor_data = []
        editor_data.append(self.obj_path_entry.get_text())
        editor_data.append(self.editor_label_entry.get_text())
        editor_data.append(self.tooltip_info_entry.get_text())
        editor_data.append(str(self.editor_select.get_active()))
        editor_data.append(self.default_value_entry.get_text())
        return editor_data
