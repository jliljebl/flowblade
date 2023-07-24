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
"""
from gi.repository import Gtk, GObject

import gui
import guicomponents
import guiutils
import projectdatavault

_project_data_manager_window = None


def show_project_data_manager_window():
    global _project_data_manager_window

    _project_data_manager_window = ProjectDataManagerWindow()

def _close_window():
    global _project_data_manager_window
    _project_data_manager_window.set_visible(False)
    _project_data_manager_window.destroy()
    
    
class ProjectDataManagerWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)

        self.show_only_saved = True
        self.current_folders = []

        self.data_folders_list_view = guicomponents.TextTextListView()
        self.load_data_folders()

        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(Gtk.Label(label="Data manager"), False, False, 0)
        vbox.pack_start(self.data_folders_list_view, True, True, 0)

        if len(self.current_folders) > 0:
            folders_info_panel = self.create_folder_info_panel(self.current_folders[0])
        else:
            folders_info_panel = Gtk.Label(label=_("No data folders"))
            
            
        hbox = Gtk.HBox(False, 2)
        hbox.pack_start(vbox, False, False, 0)
        hbox.pack_start(folders_info_panel, False, False, 0)

        self.set_transient_for(gui.editor_window.window)
        self.set_title(_("Project Data Manager"))
        self.connect("delete-event", lambda w, e:_close_window())

        alignment = guiutils.set_margins(hbox, 8, 8, 12, 12)
        self.add(alignment)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()

    def create_folder_info_panel(self, folder_handle):
        info = folder_handle.data_folders_info()
        
        vbox = Gtk.VBox(False, 2)
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

        return vbox

    def get_data_row(self, info, name, folder_id):
        size_str = info[folder_id]
        
        box = Gtk.HBox(False, 2)
        box.pack_start(Gtk.Label(label=name), False, False, 0)
        box.pack_start(Gtk.Label(label=size_str), False, False, 0)
        
        return box
        
    def load_data_folders(self):

        # Fill current_folders list
        active_vault_path = projectdatavault.get_active_vault_folder()
        vault = projectdatavault.VaultDataHandle(active_vault_path)
        vault.create_data_folders_handles()

        self.current_folders = []
        for folder_handle in vault.data_folders:
            savefile, times_saved = folder_handle.get_save_info()
            if self.show_only_saved == True and times_saved == 0:
                continue
            else:
                self.current_folders.append(folder_handle)
                
        # Display current_folders
        self.data_folders_list_view.storemodel.clear()
        
        for folder_handle in self.current_folders:
            savefile, times_saved = folder_handle.get_save_info()
            if savefile == None:
                savefile = _("Not saved")
            row = [savefile, str(times_saved)]
            self.data_folders_list_view.storemodel.append(row)
        
        self.data_folders_list_view.scroll.queue_draw()
