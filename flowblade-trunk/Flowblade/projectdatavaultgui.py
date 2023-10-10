"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2023 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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
This module provides GUI to manage project data and data vaults.

NOTE: 'vault' in code is presented to user as 'Data Store'.
"""
from gi.repository import Gtk, GObject, GLib

import copy
import datetime
import hashlib
import os
from os.path import isfile, join, isdir
import pickle
import shutil

import atomicfile
from editorstate import PROJECT
import dialogs
import dialogutils
import diskcachemanagement
import gui
import guicomponents
import guiutils
import persistance
import projectdatavault
import userfolders

PROJECT_DATA_WIDTH = 370
PROJECT_DATA_HEIGHT = 270

_project_data_manager_window = None
_current_project_info_window = None
_clone_window = None


# --------------------------------------------------------- interface
def show_project_data_manager_window():
    global _project_data_manager_window

    _project_data_manager_window = ProjectDataManagerWindow()

def _close_window():
    global _project_data_manager_window
    _project_data_manager_window.set_visible(False)
    _project_data_manager_window.destroy()

def show_current_project_data_store_info_window():
    global _current_project_info_window
    
    _current_project_info_window = CurrenProjectDataInfoWindow()

def _close_info_window():
    global _current_project_info_window
    _current_project_info_window.set_visible(False)
    _current_project_info_window.destroy()

def get_vault_select_combo(active_vault_index):
    vaults_combo = Gtk.ComboBoxText()
    fill_vaults_combo(vaults_combo, active_vault_index)
    
    return vaults_combo
        
def fill_vaults_combo(vaults_combo, active_vault_index):
    if hasattr(vaults_combo, "changed_id"):
        vaults_combo.handler_block(vaults_combo.changed_id)

    vaults_combo.remove_all()

    vaults_combo.append_text(_("Default XDG Data Store"))
    vaults_obj = projectdatavault.get_vaults_object()
    user_vaults_data = vaults_obj.get_user_vaults_data()
    for vault_properties in user_vaults_data:
        vaults_combo.append_text(vault_properties["name"])

    vaults_combo.set_active(active_vault_index)

    if hasattr(vaults_combo, "changed_id"):
        vaults_combo.handler_unblock(vaults_combo.changed_id)

def show_create_data_dialog(callback, data=None):
    label = Gtk.Label(label=_("Select Empty Folder to be added as Data Store"))
    
    data_folder_button = Gtk.FileChooserButton(_("Select Folder"))
    data_folder_button.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    data_folder_button.set_current_folder(os.path.expanduser("~") + "/")

    out_folder_row = guiutils.get_two_column_box(Gtk.Label(label=_("Data Folder:")), data_folder_button, 60)

    vaults_obj = projectdatavault.get_vaults_object()
    user_vaults_data = vaults_obj.get_user_vaults_data()

    name_label = Gtk.Label(label=_("Data Store Name"))
    name_entry = Gtk.Entry()
    now_str = "{:%b-%d-%Y-%H:%M}".format(datetime.datetime.now())
    name_entry.set_text("User Folder " + now_str)

    name_row = guiutils.get_two_column_box(name_label, name_entry, 60)
    
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(label, False, False, 0)
    vbox.pack_start(out_folder_row, False, False, 0)
    vbox.pack_start(name_row, False, False, 0)

    if data == None:
        widgets = (data_folder_button, name_entry)
    else:
        widgets = (data_folder_button, name_entry, data)
    dialogutils.panel_ok_cancel_dialog(_("Create Data Store"), vbox, _("Create Data Store"), callback, widgets)

        
# --------------------------------------------------------- window classes
class AbstractDataStoreWindow(Gtk.Window):

    def __init__(self):
        GObject.GObject.__init__(self)
        
        self.default_vault_name = _("Default XDG Data Store")
    
    def folder_properties_panel(self, folder_handle):
        
        info = folder_handle.data_folders_info()
        
        vbox = Gtk.VBox(False, 2)

        savefile, times_saved, last_date = folder_handle.get_save_info()

        save__name_label = guiutils.bold_label(_("Last File Name:"))
        save__name_label.set_margin_end(4)
        try:
            save_file_name = Gtk.Label(label=str(os.path.basename(savefile)))
        except:
            save_file_name = Gtk.Label(label=_("Not Saved"))
        row = guiutils.get_left_justified_box([save__name_label, save_file_name])
        vbox.pack_start(row, False, False, 0)
        
        save_label = guiutils.bold_label(_("Last Saved:"))
        save_label.set_margin_end(4)
        if str(last_date) != "0":
            save_date = Gtk.Label(label=str(last_date))
        else:
            save_date = Gtk.Label(label=_("Not Saved"))

        row = guiutils.get_left_justified_box([save_label, save_date])
        row.set_margin_bottom(12)
        vbox.pack_start(row, False, False, 0)
        
        data_id_label = guiutils.bold_label(_("Data ID:"))
        data_id_label.set_margin_end(4)
        data_id = Gtk.Label(label=folder_handle.data_id)
        row = guiutils.get_left_justified_box([data_id_label, data_id])
        row.set_margin_bottom(12)
        vbox.pack_start(row, False, False, 0)

        row = self.get_data_row(info, _("Thumbnails"), projectdatavault.THUMBNAILS_FOLDER)
        vbox.pack_start(row, False, False, 0)
        row = self.get_data_row(info, _("Audio Levels Data"), projectdatavault.AUDIO_LEVELS_FOLDER)
        vbox.pack_start(row, False, False, 0)
        row = self.get_data_row(info, _("Rendered Files"), projectdatavault.RENDERS_FOLDER)
        vbox.pack_start(row, False, False, 0)
        row = self.get_data_row(info, _("Container Clips"), projectdatavault.CONTAINER_CLIPS_FOLDER)
        vbox.pack_start(row, False, False, 0)
        row = self.get_data_row(info, _("Proxy Files"), projectdatavault.PROXIES_FOLDER)
        vbox.pack_start(row, False, False, 0)

        total_size_str = folder_handle.get_total_data_size()
        box = Gtk.HBox(True, 2)
        box.pack_start(guiutils.get_left_justified_box([guiutils.bold_label(_("Total"))]), True, True, 0)
        box.pack_start(guiutils.get_left_justified_box([guiutils.pad_label(40, 12), Gtk.Label(label=total_size_str)]), True, True, 0)
        box.set_margin_top(12)
        vbox.pack_start(box, False, False, 0)

        return vbox

    def get_data_row(self, info, name, folder_id):
        size_str = info[folder_id]

        box = Gtk.HBox(True, 2)
        box.pack_start(guiutils.get_left_justified_box([guiutils.bold_label(name)]), True, True, 0)
        box.pack_start(guiutils.get_left_justified_box([guiutils.pad_label(40, 12), Gtk.Label(label=size_str)]), True, True, 0)
        
        return box
            
    
class ProjectDataManagerWindow(AbstractDataStoreWindow):

    def __init__(self):
        AbstractDataStoreWindow.__init__(self)

        self.view_vault_index = projectdatavault.get_vaults_object().get_active_vault_index()

        self.current_folders = []
        self.current_folder_index = -1
        self.show_only_saved = True

        vaults_control_panel = self.create_vaults_control_panel()
        vaults_frame = guiutils.get_named_frame(_("Actions"), vaults_control_panel, 8)
        
        selection_panel = self.create_vault_selection_panel()
        self.update_vault_info()
        
        self.data_folders_list_view = guicomponents.TextTextListView(True, _("Last Saved File"), _("Times Saved"))
        self.load_data_folders()
        tree_sel = self.data_folders_list_view.treeview.get_selection()
        tree_sel.connect("changed", self.folder_selection_changed)
        
        if len(self.current_folders) > 0:
            self.current_folder_index = 0
            self.project_info_panel = self.create_folder_info_panel(self.current_folders[self.current_folder_index])
        else:
            self.project_info_panel = Gtk.Label(label=_("No data folders"))
            self.project_info_panel.set_size_request(PROJECT_DATA_WIDTH, PROJECT_DATA_HEIGHT)
            
        self.info_frame = Gtk.VBox()
        self.info_frame.pack_start(self.project_info_panel, False, False, 0)
        self.info_frame.set_margin_start(12)

        view_properties_panel = self.get_view_properties_panel()
        view_properties_panel.set_margin_start(12)

        hbox = Gtk.HBox(False, 2)
        hbox.pack_start(self.data_folders_list_view, True, True, 0)
        hbox.pack_start(self.info_frame, False, False, 0)
        #hbox.set_margin_top(4)
        hbox.set_margin_start(24)

        title_row = guiutils.get_centered_box([guiutils.bold_label(_("Projects"))])
        title_row.set_margin_bottom(12)

        selection_vbox = Gtk.VBox(False, 2)
        selection_vbox.pack_start(selection_panel, False, False, 0)
        selection_vbox.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        selection_vbox.pack_start(title_row, False, False, 0)
        #selection_vbox.pack_start(view_properties_panel, False, False, 0)
        selection_vbox.pack_start(hbox, False, False, 0)

        selections_frame = guiutils.get_named_frame(_("Data Stores"), selection_vbox, 8)

        close_button = Gtk.Button(_("Close"))
        close_button.connect("clicked", lambda w: _close_window())

        close_hbox = Gtk.HBox(False, 2)
        close_hbox.pack_start(Gtk.Label(), True, True, 0)
        close_hbox.pack_start(close_button, False, False, 0)
        close_hbox.set_margin_top(18)

        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(vaults_frame, False, False, 0)
        vbox.pack_start(guiutils.pad_label(24, 24), False, False, 0)
        vbox.pack_start(selections_frame, True, True, 0)
        vbox.pack_start(close_hbox, False, False, 0)

        vbox = guiutils.set_margins(vbox, 12, 12, 12, 12)

        pane = guiutils.set_margins(vbox, 12, 12, 12, 12)
        pane.set_size_request(780, 350)

        self.set_transient_for(gui.editor_window.window)
        self.set_title(_("Data Store Manager"))
        self.connect("delete-event", lambda w, e:_close_window())
        
        self.add(pane)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()

    def create_vault_selection_panel(self):
        self.vaults_combo = Gtk.ComboBoxText()
        self.fill_vaults_combo()
        changed_id = self.vaults_combo.connect("changed", lambda w: self.vault_changed(w))
        self.vaults_combo.changed_id = changed_id 

        self.drop_button = Gtk.Button(_("Drop Data Store"))
        self.drop_button.connect("clicked", lambda w: self.drop_button_clicked())

        hbox_select = Gtk.HBox(False, 2)
        hbox_select.pack_start(self.vaults_combo, False, False, 0)
        hbox_select.pack_start(Gtk.Label(), True, True, 0)
        hbox_select.pack_start(self.drop_button, False, False, 0)

        path_label = guiutils.bold_label(_("Data Store Folder: "))
        path = projectdatavault.get_vault_folder_for_index(self.view_vault_index)
        self.store_path_info = Gtk.Label(label=path)
        info_row_1 = guiutils.get_left_justified_box([path_label, self.store_path_info])
        info_row_1 = guiutils.set_margins(info_row_1, 12, 0, 4, 0)
 
        active_label = guiutils.bold_label(_("Active: "))
        self.active_info = Gtk.Label(label=_("Yes")) 
        activate_button = Gtk.Button(_("Make This Data Store Active"))
        activate_button.connect("clicked", lambda w: self.activate_button_clicked())
        active_info_left = guiutils.get_left_justified_box([active_label, self.active_info])
        info_row_2 = Gtk.HBox(False, 2)
        info_row_2.pack_start(active_info_left, True, True, 0)
        info_row_2.pack_start(activate_button, False, False, 0)
        info_row_2 = guiutils.set_margins(info_row_2, 4, 0, 4, 0)

        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(hbox_select, False, False, 0)
        vbox.pack_start(info_row_1, False, False, 0)
        vbox.pack_start(info_row_2, False, False, 0)

        return vbox

    def create_vaults_control_panel(self):
        create_button = Gtk.Button(_("Create Data Store"))
        create_button.connect("clicked", lambda w: self.create_button_clicked())
        connect_button = Gtk.Button(_("Connect Data Store"))
        connect_button.connect("clicked", lambda w: self.connect_button_clicked())

        if diskcachemanagement.legacy_disk_data_exists() == True:
            disk_cache_button = Gtk.Button(_("Legacy Disk Cache Manager"))
            disk_cache_button.connect("clicked", lambda w: diskcachemanagement.show_disk_management_dialog())
            
        hbox = Gtk.HBox(False, 2)
        hbox.pack_start(create_button, False, False, 0)
        hbox.pack_start(connect_button, False, False, 0)
        hbox.pack_start(Gtk.Label(), True, True, 0)
        if diskcachemanagement.legacy_disk_data_exists() == True:
            hbox.pack_start(disk_cache_button, False, False, 0)
        return hbox

    def fill_vaults_combo(self):
        if hasattr(self.vaults_combo, "changed_id"):
            self.vaults_combo.handler_block(self.vaults_combo.changed_id)

        self.vaults_combo.remove_all()
        
        self.vaults_combo.append_text(self.default_vault_name)
        
        vaults_obj = projectdatavault.get_vaults_object()
        user_vaults_data = vaults_obj.get_user_vaults_data()
        for vault_properties in user_vaults_data:
            self.vaults_combo.append_text(vault_properties["name"])

        self.vaults_combo.set_active(self.view_vault_index)

        if hasattr(self.vaults_combo, "changed_id"):
            self.vaults_combo.handler_unblock(self.vaults_combo.changed_id)
            
    def get_view_properties_panel(self):

        self.only_saved_check = Gtk.CheckButton()
        self.only_saved_check.set_active(self.show_only_saved)
        self.only_saved_check.connect("toggled", lambda w: self.show_only_saved_toggled(w))
        
        label = Gtk.Label(label=_("Show only Saved Projects"))
        label.set_margin_start(4)
        destroy_non_saved_button = Gtk.Button(_("Destroy Non-Saved Projects"))

        hbox = Gtk.HBox(False, 2)
        hbox.pack_start(self.only_saved_check, False, False, 0)
        hbox.pack_start(label, False, False, 0)
        hbox.pack_start(Gtk.Label(), True, True, 0)
        hbox.pack_start(destroy_non_saved_button, False, False, 0)

        guiutils.set_margins(hbox, 8, 8, 0, 0)
        
        return hbox

    def create_folder_info_panel(self, folder_handle):
        
        vbox = self.folder_properties_panel(folder_handle)
        
        self.destroy_button = Gtk.Button(label=_("Destroy Project Data"))
        self.destroy_button.connect("clicked", self.destroy_pressed)
        self.destroy_button.set_sensitive(False)
        self.destroy_guard_check = Gtk.CheckButton()
        self.destroy_guard_check.set_active(False)
        self.destroy_guard_check.connect("toggled", self.destroy_guard_toggled)

        hbox = Gtk.HBox(False, 2)
        if folder_handle.data_id != PROJECT().project_data_id:
            hbox.pack_start(Gtk.Label(), True, True, 0)
            hbox.pack_start(self.destroy_guard_check, False, False, 0)
            hbox.pack_start(self.destroy_button, False, False, 0)
        else:
            no_destroy = Gtk.Label(label=_("Currently open Project data cannot be destroyed."))
            hbox.pack_start(no_destroy, False, False, 0)
            
        hbox.set_margin_top(12)
            
        vbox.pack_start(hbox, False, False, 0)
        vbox.set_size_request(PROJECT_DATA_WIDTH, PROJECT_DATA_HEIGHT)
        
        return vbox

    def load_data_folders(self):

        # Fill current_folders list
        vault_path = projectdatavault.get_vault_folder_for_index(self.view_vault_index)
        vault = projectdatavault.VaultDataHandle(vault_path)
        vault.create_data_folders_handles()

        self.current_folders = []
        for folder_handle in vault.data_folders:
            savefile, times_saved, last_date = folder_handle.get_save_info()
            if self.show_only_saved == True and times_saved == 0:
                continue
            else:
                self.current_folders.append(folder_handle)
                
        # Display current_folders
        self.data_folders_list_view.storemodel.clear()
        
        for folder_handle in self.current_folders:
            savefile, times_saved, last_date = folder_handle.get_save_info()
            if savefile == None:
                file_name = _("not saved")
            else:
                file_name = os.path.basename(savefile)
            
            row = [file_name, str(times_saved)]
            self.data_folders_list_view.storemodel.append(row)
        
        if len(self.current_folders) > 0:
            selection = self.data_folders_list_view.treeview.get_selection()
            selection.select_path("0")
                    
        self.data_folders_list_view.scroll.queue_draw()

    def vault_changed(self, widget):
        self.view_vault_index = widget.get_active()
        self.load_data_folders()

        self.update_vault_info()

        if len(self.current_folders) == 0:
            hbox = Gtk.Label(label=_("No data folders"))
            hbox.set_size_request(PROJECT_DATA_WIDTH, PROJECT_DATA_HEIGHT)

            self.info_frame.remove(self.project_info_panel)
            self.project_info_panel = hbox
            self.project_info_panel.show_all()
            self.info_frame.pack_start(self.project_info_panel, False, False, 0)

    def update_vault_info(self):
        vault_folder = projectdatavault.get_vault_folder_for_index(self.view_vault_index)
        self.store_path_info.set_text(vault_folder)
        if vault_folder == projectdatavault.get_active_vault_folder():
            self.active_info.set_text(_("Yes")) 
        else:
            self.active_info.set_text(_("No")) 

        if self.view_vault_index == projectdatavault.DEFAULT_VAULT:
            self.drop_button.set_sensitive(False)
        else:
            self.drop_button.set_sensitive(True)

    def folder_selection_changed(self, selection):
        (model, rows) = selection.get_selected_rows()
        if len(rows) == 0:
            return
        self.current_folder_index = max(rows[0])
        try:
            hbox = self.create_folder_info_panel(self.current_folders[self.current_folder_index])
        except:
            self.current_folder_index = -1
            hbox = Gtk.Label(label=_("No data folders"))
            hbox.set_size_request(PROJECT_DATA_WIDTH, PROJECT_DATA_HEIGHT)
                            
        self.info_frame.remove(self.project_info_panel)
        self.project_info_panel = hbox
        self.project_info_panel.show_all()
        self.info_frame.pack_start(self.project_info_panel, False, False, 0)
        
    def create_button_clicked(self):
        show_create_data_dialog(self.create_button_callback)
        
    def create_button_callback(self, dialog, response, widgets):
        if response != Gtk.ResponseType.ACCEPT:
            dialog.destroy()
            return
        
        # Get and verify vault data.
        data_folder_button, name_entry = widgets
        dir_path = data_folder_button.get_filename()
        user_visible_name = name_entry.get_text() 
        dialog.destroy()
                        
        if not os.listdir(dir_path):
            pass
        else:
            self.show_non_empty_dialog_info()
            return

        if len(user_visible_name) == 0:
            user_visible_name = "{:%b-%d-%Y-%H:%M}".format(datetime.datetime.now())

        # Add new vault
        vaults_obj = projectdatavault.get_vaults_object()
        vaults_obj.add_user_vault(user_visible_name, dir_path)
        vaults_obj.save()

        # Update combo
        self.fill_vaults_combo()

    def show_non_empty_dialog_info(self):
        primary_txt = _("Selected folder was not empty!")
        secondary_txt = _("Can't add non-empty folder as new Project Data Folder.")
        dialogutils.warning_message(primary_txt, secondary_txt, None)
                
    def drop_button_clicked(self):

        label = guiutils.bold_label(_("Confirm Dropping Data Store:"))
        label.set_margin_bottom(12)
        
        vaults_obj = projectdatavault.get_vaults_object()
        user_vaults_data = vaults_obj.get_user_vaults_data()
        name = vaults_obj.get_user_vaults_data()[self.view_vault_index - 1]["name"] # -1 because first vault is the default vault
        name_label = Gtk.Label(label=name)

        data_label = Gtk.Label(label=_("Data inside folder will NOT be destroyd."))
        data_label.set_margin_top(24)

                
        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(guiutils.get_left_justified_box([label]), False, False, 0)
        vbox.pack_start(guiutils.get_left_justified_box([name_label]), False, False, 0)
        vbox.pack_start(guiutils.get_left_justified_box([data_label]), False, False, 0)
        vbox.set_size_request(400, 100)

        dialogutils.panel_ok_cancel_dialog(_("Drop Data Store"), vbox, _("Drop Data Store"), self.drop_button_callback)
        
    def drop_button_callback(self, dialog, response):
        dialog.destroy()
            
        if response != Gtk.ResponseType.ACCEPT:
            return

        drop_index = self.view_vault_index - 1 # -1 because 0 the default vault, 1 - n user vaults
                                               # and we are always dropping _user_ vault.
        
        # We need to get activa vault path before deleting anythin because active 
        # vault is saved as index and deleting anything can mess that up
        # and we need to restore correct active vault after droip.


        # Drop vault
        vaults_obj = projectdatavault.get_vaults_object()
        # We need to get active vault path before dropping anything because active 
        # vault is saved as index and deleting anything can mess that up
        # and we need to restore correct active vault after droip.
        active_vault_path = projectdatavault.get_active_vault_folder()
        
        vaults_obj.drop_user_vault(drop_index)
        vaults_obj.set_active_vault_for_path(active_vault_path)
        vaults_obj.save()

        # Update combo
        self.fill_vaults_combo()

    def connect_button_clicked(self):
        label = Gtk.Label(label=_("Select Folder With existing Data Store data"))
        
        self.connect_data_folder_button = Gtk.FileChooserButton(_("Select Folder"))
        self.connect_data_folder_button.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.connect_data_folder_button.set_current_folder(os.path.expanduser("~") + "/")

        out_folder_row = guiutils.get_two_column_box(Gtk.Label(label=_("Data Folder:")), self.connect_data_folder_button, 60)

        vaults_obj = projectdatavault.get_vaults_object()
        user_vaults_data = vaults_obj.get_user_vaults_data()

        name_label = Gtk.Label(label=_("Data Store Name"))
        self.connect_name_entry = Gtk.Entry()
        now_str = "{:%b-%d-%Y-%H:%M}".format(datetime.datetime.now())
        self.connect_name_entry.set_text("User Folder " + now_str)

        name_row = guiutils.get_two_column_box(name_label, self.connect_name_entry, 60)
        
        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(label, False, False, 0)
        vbox.pack_start(out_folder_row, False, False, 0)
        vbox.pack_start(name_row, False, False, 0)

        dialogutils.panel_ok_cancel_dialog(_("Connect Data Store"), vbox, _("Connect Data Store"), self.connect_dialog_callback)

    def connect_dialog_callback(self, dialog, response):
        if response != Gtk.ResponseType.ACCEPT:
            dialog.destroy()
            return

        # Get and verify vault data.
        dir_path = self.connect_data_folder_button.get_filename()
        user_visible_name = self.connect_name_entry.get_text() 
        dialog.destroy()
                        
        if not os.listdir(dir_path):
            # Empty is okay
            pass
        else:
            validate_success = self.validate_data_store(dir_path)
            if validate_success == False:
                return

        if len(user_visible_name) == 0:
            user_visible_name = "{:%b-%d-%Y-%H:%M}".format(datetime.datetime.now())

        # Add new vault
        vaults_obj = projectdatavault.get_vaults_object()
        vaults_obj.add_user_vault(user_visible_name, dir_path)
        vaults_obj.save()

        # Update combo
        self.fill_vaults_combo()
        
    def validate_data_store(self, dir_path):
        
        vault_handle = projectdatavault.VaultDataHandle(dir_path)
        vault_validity_state, data = vault_handle.folder_is_valid_data_store()
        
        if vault_validity_state == projectdatavault.VAULT_IS_VALID:
            return True
        
        msg = _("Data Store Validity Error: ")
        if vault_validity_state == projectdatavault.VAULT_HAS_NON_FOLDER_FILES:
            msg += _("Data Store folder has non-folder files.")
        if vault_validity_state == projectdatavault.VAULT_HAS_BAD_FOLDERS:
            msg += _("Data Store folder has bad folders.") + "\n"
            for project_folder_handle in data: # data is list of handles for bad folders.
                validity_state = project_folder_handle.get_folder_valid_state()
                if validity_state == projectdatavault.PROJECT_FOLDER_IS_EMPTY:
                    msg += project_folder_handle.data_id + _(" is empty.") + "\n"
                elif validity_state == projectdatavault.PROJECT_FOLDER_HAS_EXTRA_FILES_OR_FOLDERS:
                    msg += project_folder_handle.data_id + _(" has extra files or folders") + "\n"
                elif validity_state == projectdatavault.PROJECT_FOLDER_HAS_MISSING_FOLDERS:
                    msg += project_folder_handle.data_id + _(" has missing data folders") + "\n"
                else: # projectdatavault.PROJECT_FOLDER_HAS_MISSING_SAVE_FILE_DATA:
                    msg += project_folder_handle.data_id + _(" has no savefile data.") + "\n"
        primary_txt = _("Cannot connect Folder as Data Store!")
        dialogutils.warning_message(primary_txt, msg, gui.editor_window.window)
        return False

    def activate_button_clicked(self):
        projectdatavault.set_active_vault_index(self.view_vault_index)
        projectdatavault.get_vaults_object().save()

    def show_only_saved_toggled(self, widget):
        self.show_only_saved = widget.get_active()
        self.load_data_folders()

    def destroy_guard_toggled(self, widget):
        self.destroy_button.set_sensitive(widget.get_active())
    
    def destroy_pressed(self, widget):
        primary_txt = _("Confirm Destroying Project Data")
        secondary_txt = _("Data will be permanently destroyed and there is no undo for this operation.")

        dialogutils.warning_confirmation(self.destroy_confirm_callback, primary_txt, secondary_txt, gui.editor_window.window)
    
    def destroy_confirm_callback(self, dialog, response_id):
        dialog.destroy()
        
        if response_id != Gtk.ResponseType.ACCEPT:
            return
        
        destroy_folder = self.current_folders[self.current_folder_index]
        destroy_folder.destroy_data()

        self.vault_changed(self.vaults_combo)


class CurrenProjectDataInfoWindow(AbstractDataStoreWindow):
    
    def __init__(self):
        AbstractDataStoreWindow.__init__(self)

        data_folder_path = projectdatavault.get_project_data_folder()
        folder_handle = projectdatavault.ProjectDataFolderHandle(data_folder_path)

        vbox = Gtk.VBox(False, 2)

        if PROJECT().vault_folder == projectdatavault.get_default_vault_folder():
            vault_name = self.default_vault_name 
        else:
            vaults = projectdatavault.get_vaults_object()
            vault_name = vaults.get_user_vault_folder_name(PROJECT().vault_folder)
            if vault_name == None:
                vault_name = _("Project Data Store is not active")
        store_name_label = guiutils.bold_label(_("Project Data Store:"))
        store_name_label.set_margin_end(4)
        row = guiutils.get_left_justified_box([store_name_label, Gtk.Label(label=vault_name)])
        vbox.pack_start(row, False, False, 0)

        path_label = guiutils.bold_label(_("Data Store Path:"))
        path_label.set_margin_end(4)
        row = guiutils.get_left_justified_box([path_label, Gtk.Label(label=PROJECT().vault_folder)])
        row.set_margin_bottom(12)
        vbox.pack_start(row, False, False, 0)

        clone_button = Gtk.Button(_("Create Clone Project with Project Data in another Data Store"))
        clone_button.connect("clicked", lambda w: self.clone_button_clicked())
        row = guiutils.get_left_justified_box([clone_button])
        row.set_margin_bottom(24)
        vbox.pack_start(row, False, False, 0)
        
        vbox.pack_start(self.folder_properties_panel(folder_handle), False, False, 0)

        close_button = Gtk.Button(_("Close"))
        close_button.connect("clicked", lambda w: _close_info_window())

        close_hbox = Gtk.HBox(False, 2)
        close_hbox.pack_start(Gtk.Label(), True, True, 0)
        close_hbox.pack_start(close_button, False, False, 0)
        close_hbox.set_margin_top(18)
        
        vbox.pack_start(close_hbox, False, False, 0)
        
        pane = guiutils.set_margins(vbox, 12, 12, 12, 12)
        pane.set_size_request(400, 250)

        self.set_transient_for(gui.editor_window.window)
        self.set_title(_("Project Data"))
        self.connect("delete-event", lambda w, e:_close_info_window())

        self.add(pane)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()

    def clone_button_clicked(self):
        show_clone_project_dialog()
        
def show_clone_project_dialog():
    global _clone_window
    _clone_window = ProjectCloneWindow()

def _close_clone_window():
    global _clone_window
    _clone_window.set_visible(False)
    _clone_window.destroy()
    
# --------------------------------------------------------- window classes
class ProjectCloneWindow(Gtk.Window):

    def __init__(self):
        GObject.GObject.__init__(self)

        self.clone_project_path = None

        # Create Data store selection combo. This is a bit involved because default valult and uservaults 
        # are not in the same data structure.
        project_vault_index = projectdatavault.get_vaults_object().get_index_for_vault_folder(PROJECT().vault_folder)
        if project_vault_index == None:
            project_vault_index = -99

        sel_to_vault_index = {}
        self.vaults_combo = Gtk.ComboBoxText()
        if project_vault_index != 0:
            self.vaults_combo.append_text(self.default_vault_name)

        user_vaults_data = projectdatavault.get_vaults_object().get_user_vaults_data()
        user_vault_index = 0
        for vault_properties in user_vaults_data:
            if project_vault_index != user_vault_index + 1:
                self.vaults_combo.append_text(vault_properties["name"])
            user_vault_index += 1

        self.vaults_combo.set_active(0)
        self.vaults_combo.set_margin_start(4)
        vaults_combo_row = guiutils.get_left_justified_box([Gtk.Label(label=_("New Data Store:")), self.vaults_combo])

        set_path_button = Gtk.Button(label=_("Set Clone Project Path"))
        set_path_button.connect("clicked", lambda w:self.set_project_path_pressed())
        set_path_button.set_margin_end(4)
        self.clone_project_name = Gtk.Label(label=_("<not set>"))
        set_path_row = guiutils.get_left_justified_box([set_path_button, self.clone_project_name])

        self.info_label = Gtk.Label(label=_("<small>Set clone Project path and select new Data Store.</small>"))
        self.info_label.set_use_markup(True)
        info_row = guiutils.get_right_justified_box([self.info_label])
        info_row.set_margin_top(12)

        self.create_button = Gtk.Button(label=_("Create Clone Project"))
        self.create_button.connect("clicked", lambda w:self.create_clone_project_pressed())
        create_row = guiutils.get_right_justified_box([self.create_button])
        create_row.set_margin_bottom(12)
        self.update_create_button_state()
        
        vbox = Gtk.VBox(False, 2)

        vbox.pack_start(set_path_row, False, False, 0)
        vbox.pack_start(vaults_combo_row, False, False, 0)
        vbox.pack_start(info_row, False, False, 0)
        vbox.pack_start(create_row, False, False, 0)

        close_button = Gtk.Button(_("Exit"))
        close_button.connect("clicked", lambda w: _close_clone_window())

        close_hbox = Gtk.HBox(False, 2)
        close_hbox.pack_start(Gtk.Label(), True, True, 0)
        close_hbox.pack_start(close_button, False, False, 0)
        close_hbox.set_margin_top(24)
        
        vbox.pack_start(close_hbox, False, False, 0)
        
        pane = guiutils.set_margins(vbox, 12, 12, 12, 12)
        pane.set_size_request(400, 100)


        self.set_transient_for(gui.editor_window.window)
        self.set_title(_("Create Clone Project"))

        self.add(pane)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()

    def set_project_path_pressed(self):
        no_ext_name = "test_project"
            
        dialogs.save_project_as_dialog(self.set_project_path_dialog_callback, 
                                       no_ext_name + "_clone.flb", 
                                       None, _clone_window)

    def set_project_path_dialog_callback(self, dialog, response_id):
        if response_id != Gtk.ResponseType.ACCEPT:
            dialog.destroy()
            return

        save_path = dialog.get_filenames()[0]
        dialog.destroy()

        self.clone_project_path = save_path
        self.clone_project_name.set_text(".../" + os.path.basename(self.clone_project_path))
        self.update_create_button_state()

    def update_create_button_state(self):
        if self.clone_project_path == None:
            self.create_button.set_sensitive(False)
            self.info_label.set_text("<small>Set clone Project path and select new Data Store.</small>")
            self.info_label.set_use_markup(True)
        else:
            self.create_button.set_sensitive(True)
            self.info_label.set_text("<small>Click button to create clone Project.</small>")
            self.info_label.set_use_markup(True)

    def cloning_completed(self):
        self.info_label.set_text("<small>Project cloned succesfully.</small>")
        self.info_label.set_use_markup(True)
        self.create_button.set_sensitive(False)
            
    def create_clone_project_pressed(self):
        self.info_label.set_text("<small>Cloning Project...</small>")
        self.info_label.set_use_markup(True)
        
        try:
            # Copy Project data 
            md_key = str(datetime.datetime.now()) + str(os.urandom(16))
            clone_project_data_id_str = hashlib.md5(md_key.encode('utf-8')).hexdigest()
            clone_vault_name = self.vaults_combo.get_active_text()
            clone_vault_path = projectdatavault.get_vaults_object().get_vault_path_for_name(clone_vault_name)
            clone_project_data_folder_path = join(clone_vault_path, clone_project_data_id_str) + "/"
            source_data_folder = projectdatavault.get_project_data_folder()

            shutil.copytree(source_data_folder, clone_project_data_folder_path)

            # Create copy of project via saving to temp file.
            temp_path = userfolders.get_cache_dir() + "/temp_" + PROJECT().name
            persistance.save_project(PROJECT(), temp_path)

            persistance.show_messages = False
            cloneproject = persistance.load_project(temp_path, False, True)
            cloneproject.c_seq = cloneproject.sequences[cloneproject.c_seq_index] # c_seq is a seuquence.Sequence object so it is not saved twice, but reference set after load.
                
            # Set name and last save data
            cloneproject.last_save_path = self.clone_project_path
            cloneproject.name = os.path.basename(self.clone_project_path)

            # Set clone project data store data to point to new data folder.
            cloneproject.vault_folder = clone_vault_path
            cloneproject.project_data_id = clone_project_data_id_str
            
            # Test that saving is not IOError
            try:
                filehandle = open(cloneproject.last_save_path, 'w')
                filehandle.close()
            except IOError as ioe:
                primary_txt = "I/O error({0})".format(ioe.errno)
                secondary_txt = "Project cloning failed:" + ioe.strerror + "."
                dialogutils.warning_message(primary_txt, secondary_txt, self, is_info=False)
                return 

            # Update data store paths.
            # Media files.
            for key, mediafile in cloneproject.media_files.items():
                mediafile.icon_path = self.get_clone_data_store_path(mediafile.icon_path, source_data_folder, clone_project_data_folder_path)
                mediafile.path = self.get_clone_data_store_path(mediafile.path, source_data_folder, clone_project_data_folder_path)
                if mediafile.second_file_path != None:
                    mediafile.second_file_path = self.get_clone_data_store_path(mediafile.second_file_path, source_data_folder, clone_project_data_folder_path)
                if mediafile.container_data != None:
                    mediafile.container_data.unrendered_media = self.get_clone_data_store_path(mediafile.container_data.unrendered_media, source_data_folder, clone_project_data_folder_path)

            # Clips.
            for seq in cloneproject.sequences:
                for track in seq.tracks:
                    for clip in track.clips:
                        if hasattr(clip, "path") and clip.path != "" and clip.path != None:
                            clip.path = self.get_clone_data_store_path(clip.path, source_data_folder, clone_project_data_folder_path)
                        if hasattr(clip, "container_data") and clip.container_data != None:
                            clip.container_data.rendered_media = self.get_clone_data_store_path(clip.container_data.rendered_media, source_data_folder, clone_project_data_folder_path)
                            clip.container_data.unrendered_media = self.get_clone_data_store_path(clip.container_data.unrendered_media, source_data_folder, clone_project_data_folder_path)

            # Write clone project.
            persistance.save_project(cloneproject, cloneproject.last_save_path)
            
            # Update ./savefiles file for cloned project.
            savefiles_list = []
            savefiles_list.append((cloneproject.last_save_path, datetime.datetime.now()))
            savefiles_path = clone_project_data_folder_path + projectdatavault.SAVE_FILES_FILE
            with atomicfile.AtomicFileWriter(savefiles_path, "wb") as afw:
                write_file = afw.get_file()
                pickle.dump(savefiles_list, write_file)
            
            # Display info
            GLib.timeout_add(750, self.cloning_completed)

        except Exception as e:
            primary_txt = "Cloning failed"
            secondary_txt = "Project cloning failed: " + str(e) + "."
            dialogutils.warning_message(primary_txt, secondary_txt, self, is_info=False)


    def get_clone_data_store_path(self, orig_path, source_data_folder, clone_data_folder):
        if orig_path.find(source_data_folder) == -1:
            return orig_path
        else:
            return orig_path.replace(source_data_folder, clone_data_folder)

