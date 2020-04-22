"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2017 Janne Liljeblad.

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

from gi.repository import Gtk, Gdk

from os import listdir
from os.path import isfile, join
import os
import threading

import appconsts
import dialogutils
import editorpersistance
import gui
import guiutils
import userfolders

NO_WARNING = 0
RECREATE_WARNING = 1
PROJECT_DATA_WARNING = 2

_panels = None


class DiskFolderManagementPanel:
    
    def __init__(self, xdg_folder, folder, info_text, warning_level, recursive=False):
        self.xdg_folder = xdg_folder
        self.folder = folder
        self.warning_level = warning_level
        self.recursive = recursive
        
        self.destroy_button = Gtk.Button(_("Destroy data"))
        self.destroy_button.connect("clicked", self.destroy_pressed)
        self.destroy_guard_check = Gtk.CheckButton()
        self.destroy_guard_check.set_active(False)
        self.destroy_guard_check.connect("toggled", self.destroy_guard_toggled)
        
        self.size_info = Gtk.Label()
        self.size_info.set_text(self.get_folder_size_str())

        info = Gtk.HBox(True, 2)
        info.pack_start(guiutils.get_left_justified_box([guiutils.bold_label(info_text)]), True, True, 0)
        info.pack_start(guiutils.get_left_justified_box([guiutils.pad_label(40, 12), self.size_info]), True, True, 0)

        button_area = Gtk.HBox(False, 2)
        if self.warning_level == PROJECT_DATA_WARNING:
            button_area.pack_start(self.destroy_guard_check, True, True, 0)
            self.destroy_button.set_sensitive(False)
        button_area.pack_start(self.destroy_button, True, True, 0)
        if self.warning_level == PROJECT_DATA_WARNING:
            warning_icon = Gtk.Image.new_from_stock(Gtk.STOCK_DIALOG_WARNING, Gtk.IconSize.SMALL_TOOLBAR)
            warning_icon.set_tooltip_text( _("Destroying this data may change contents of existing\nprojects and make some projects unopenable."))
            button_area.pack_start(warning_icon, False, False, 0)
        else:
            button_area.pack_start(guiutils.pad_label(16, 16), False, False, 0)
        button_area.set_size_request(150, 24)

        row = Gtk.HBox(False, 2)
        row.pack_start(info, True, True, 0)
        row.pack_start(button_area, False, False, 0)
        
        self.vbox = Gtk.VBox(False, 2)
        self.vbox.pack_start(row, False, False, 0)

    def get_disk_folder(self):
        cf = self.xdg_folder + self.folder
        return cf

    def get_folder_files(self):
        data_folder = self.get_disk_folder()
        return [f for f in listdir(data_folder) if isfile(join(data_folder, f))]
        
    def get_folder_contents(self, folder):
        return os.listdir(self.get_disk_folder())
        
    def get_folder_size(self):
        return self.get_folder_sizes_recursively(self.get_disk_folder())
    
    def get_folder_sizes_recursively(self, folder):
        files = os.listdir(folder)
        size = 0
        for f in files:
            if os.path.isdir(folder + "/" + f) and self.recursive == True:
                size += self.get_folder_sizes_recursively(folder + "/" + f)
            else:
                size += os.path.getsize(folder +"/" + f)
        return size

    def get_folder_size_str(self):
        size = self.get_folder_size()
        self.used_disk = size
        return self.get_size_str(size)

    def get_size_str(self, size):
        if size > 1000000:
            return str(int((size + 500000) / 1000000)) + _(" MB")
        elif size > 1000:
            return str(int((size + 500) / 1000)) + _(" kB")
        else:
            return str(int(size)) + " B"

    def destroy_pressed(self, widget):
        if self.warning_level == NO_WARNING:
            # Delete data
            self.destroy_data()
            return
            
        primaty_text = _("Confirm Destroying Cached Data!")
        if self.warning_level == PROJECT_DATA_WARNING:
            secondary_text = _("Destroying this data may <b>change contents</b> of existing\nprojects or <b>make some projects unopenable!</b>")
            secondary_text += "\n\n"
            secondary_text += _("You can use 'File->Save Backup Snapshot...' functionality to backup projects\nso that they can be opened later before destroying this data.")
        else:
            secondary_text = _("Destroying this data may require parts of it to be recreated later.")
            
        dialogutils.warning_confirmation(self.warning_confirmation, primaty_text, secondary_text, gui.editor_window.window, None, False, True)

    def destroy_guard_toggled(self, check_button):
        if check_button.get_active() == True:
            self.destroy_button.set_sensitive(True)
        else:
            self.destroy_button.set_sensitive(False)
         
    def warning_confirmation(self, dialog, response_id):
        dialog.destroy()

        if response_id != Gtk.ResponseType.ACCEPT:
            return
    
        self.destroy_data()
    
    def destroy_data(self):
        print("deleting", self.folder)
        self.destroy_recursively(self.get_disk_folder())

    def destroy_recursively(self, folder):
        files = os.listdir(folder)
        for f in files:
            file_path = folder + "/" + f
            if os.path.isdir(file_path) == True:
                if self.recursive == True:
                    self.destroy_recursively(file_path)
                    os.rmdir(file_path)
            else:
                os.remove(file_path)

        self.size_info.set_text(self.get_folder_size_str())
        self.size_info.queue_draw()

def show_disk_management_dialog():
    dialog = Gtk.Dialog(_("Disk Cache Manager"), None,
                    Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    (_("Close"), Gtk.ResponseType.CLOSE))

    global _panels
    _panels = _get_disk_dir_panels()

    pane = Gtk.VBox(True, 2)
    for panel in _panels:
        pane.pack_start(panel.vbox, True, True, 0)

    guiutils.set_margins(pane, 12, 24, 12, 12)

    dialog.connect('response', dialogutils.dialog_destroy)
    
    dialog.vbox.pack_start(pane, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    dialog.show_all()
    return dialog

def check_disk_cache_size():
    check_level = editorpersistance.prefs.disk_space_warning
    # check levels [off, 500 MB,1 GB, 2 GB], see preferenceswindow.py
    if check_level == 0:
        return

    check_thread = DiskCacheWarningThread()
    check_thread.start()


class DiskCacheWarningThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        check_level = editorpersistance.prefs.disk_space_warning
        
        Gdk.threads_enter()
        
        # Get disk cache size
        panels = _get_disk_dir_panels()
        used_disk_cache_size = 0
        for panel in panels:
            used_disk_cache_size += panel.used_disk
        
        size_str = panels[0].get_size_str(used_disk_cache_size)

        # check levels [off, 500 MB,1 GB, 2 GB], see preferenceswindow.py
        if check_level == 1 and used_disk_cache_size > 1000000 * 500:
            self.show_warning(size_str)
        elif check_level == 2 and used_disk_cache_size > 1000000 * 1000:
            self.show_warning(size_str)
        elif check_level == 3 and used_disk_cache_size > 1000000 * 2000:
            self.show_warning(size_str)

        Gdk.threads_leave()

    def show_warning(self, size_str):
        primary_txt = _("Disk Cache Size Exceeds Current Warning Level!")
        secondary_txt = _("Flowblade currently uses ") + size_str + _(" of disk space.") + "\n\n" + \
                        _("You can either delete saved data using dialog opened with <b>Edit->Disk Cache</b> or") + "\n" + \
                        _("change warning level in <b>Edit->Preferences 'General Options'</b> panel.") 
        dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window, is_info=False)


def _get_disk_dir_panels():
    panels = []
    panels.append(DiskFolderManagementPanel(userfolders.get_cache_dir(), appconsts.AUDIO_LEVELS_DIR, _("Audio Levels Data"), RECREATE_WARNING))
    panels.append(DiskFolderManagementPanel(userfolders.get_cache_dir(), appconsts.GMIC_DIR, _("G'Mic Tool Session Data"), NO_WARNING))
    panels.append(DiskFolderManagementPanel(userfolders.get_data_dir(), appconsts.RENDERED_CLIPS_DIR, _("Rendered Files"), PROJECT_DATA_WARNING))
    panels.append(DiskFolderManagementPanel(userfolders.get_render_dir(), "/" + appconsts.PROXIES_DIR, _("Proxy Files"), PROJECT_DATA_WARNING))
    panels.append(DiskFolderManagementPanel(userfolders.get_data_dir(), appconsts.CONTAINER_CLIPS_DIR, _("Container Clips"), PROJECT_DATA_WARNING, True))
    panels.append(DiskFolderManagementPanel(userfolders.get_cache_dir(), appconsts.THUMBNAILS_DIR, _("Thumbnails"), RECREATE_WARNING))
    panels.append(DiskFolderManagementPanel(userfolders.get_data_dir(), appconsts.USER_PROFILES_DIR_NO_SLASH, _("User Created Custom Profiles"), PROJECT_DATA_WARNING))

    return panels
