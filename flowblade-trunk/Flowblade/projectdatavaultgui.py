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
from gi.repository import Gtk, GObject


import datetime
import os

from editorstate import PROJECT
import dialogutils
import gui
import guicomponents
import guiutils
import projectdatavault

PROJECT_DATA_WIDTH = 370
PROJECT_DATA_HEIGHT = 270


_project_data_manager_window = None
_current_project_info_window = None

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

# --------------------------------------------------------- window classes
class AbstractDataStoreWindow(Gtk.Window):

    def __init__(self):
        GObject.GObject.__init__(self)
    
    def folder_properties_panel(self, folder_handle):
        info = folder_handle.data_folders_info()
        
        vbox = Gtk.VBox(False, 2)

        savefile, times_saved, last_date = folder_handle.get_save_info()

        save__name_label = guiutils.bold_label(_("Last File Name:"))
        save__name_label.set_margin_right(4)
        try:
            save_file_name = Gtk.Label(label=str(os.path.basename(savefile)))
        except:
            save_file_name = Gtk.Label(label=_("Not Saved"))
        row = guiutils.get_left_justified_box([save__name_label, save_file_name])
        vbox.pack_start(row, False, False, 0)
        
        save_label = guiutils.bold_label(_("Last Saved:"))
        save_label.set_margin_right(4)
        if str(last_date) != "0":
            save_date = Gtk.Label(label=str(last_date))
        else:
            save_date = Gtk.Label(label=_("Not Saved"))

        row = guiutils.get_left_justified_box([save_label, save_date])
        row.set_margin_bottom(12)
        vbox.pack_start(row, False, False, 0)
        
        data_id_label = guiutils.bold_label(_("Data ID:"))
        data_id_label.set_margin_right(4)
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

        self.default_vault_name = _("Default XDG Data Store")

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
        self.info_frame.set_margin_left(12)

        view_properties_panel = self.get_view_properties_panel()
        view_properties_panel.set_margin_left(12)

        hbox = Gtk.HBox(False, 2)
        hbox.pack_start(self.data_folders_list_view, True, True, 0)
        hbox.pack_start(self.info_frame, False, False, 0)
        #hbox.set_margin_top(4)
        hbox.set_margin_left(24)

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

        hbox = Gtk.HBox(False, 2)
        hbox.pack_start(create_button, False, False, 0)
        hbox.pack_start(connect_button, False, False, 0)
        hbox.pack_start(Gtk.Label(), True, True, 0)

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
        label.set_margin_left(4)
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
        print("VAULT CHNAGED")
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
        label = Gtk.Label(label=_("Select Empty Folder to be added as Data Store"))
        
        self.data_folder_button = Gtk.FileChooserButton(_("Select Folder"))
        self.data_folder_button.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.data_folder_button.set_current_folder(os.path.expanduser("~") + "/")

        out_folder_row = guiutils.get_two_column_box(Gtk.Label(label=_("Data Folder:")), self.data_folder_button, 60)

        vaults_obj = projectdatavault.get_vaults_object()
        user_vaults_data = vaults_obj.get_user_vaults_data()

        name_label = Gtk.Label(label=_("Data Store Name"))
        self.name_entry = Gtk.Entry()
        now_str = "{:%b-%d-%Y-%H:%M}".format(datetime.datetime.now())
        self.name_entry.set_text("User Folder " + now_str)

        name_row = guiutils.get_two_column_box(name_label, self.name_entry, 60)
        
        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(label, False, False, 0)
        vbox.pack_start(out_folder_row, False, False, 0)
        vbox.pack_start(name_row, False, False, 0)

        dialogutils.panel_ok_cancel_dialog(_("Create Data Store"), vbox, _("Create Data Store"), self.create_button_callback)
 
    def create_button_callback(self, dialog, response):
        if response != Gtk.ResponseType.ACCEPT:
            dialog.destroy()
            return
        
        # Get and verify vault data.
        dir_path = self.data_folder_button.get_filename()
        user_visible_name = self.name_entry.get_text() 
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

        vbox = self.folder_properties_panel(folder_handle)

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
        self.set_title(_("Current Project Data Info"))
        self.connect("delete-event", lambda w, e:_close_info_window())
        
        self.add(pane)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()
        