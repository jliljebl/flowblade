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

from gi.repository import Gtk

from os import listdir
from os.path import isfile, join
import os

import dialogutils
import gui
import guiutils
import utils


NO_WARNING = 0
RECREATE_WARNING = 1
PROJECT_DATA_WARNING = 2


class DiskFolderManagementPanel:
    
    def __init__(self, folder, info_text, warning_level):
        self.folder = folder
        self.warning_level = warning_level
                
        self.destroy_button = Gtk.Button(_("Destroy data"))
        self.destroy_button.connect("clicked", self.destroy_pressed)
        self.destroy_guard_check = Gtk.CheckButton()
        self.destroy_guard_check.set_active(False)
        self.destroy_guard_check.connect("toggled", self.destroy_guard_toggled)
        
        self.size_info = Gtk.Label()
        self.size_info.set_text(self.get_folder_size_str())

        folder_label = Gtk.Label("/<i>" + folder + "</i>")
        folder_label.set_use_markup(True)

        info = Gtk.HBox(True, 2)
        info.pack_start(guiutils.get_left_justified_box([guiutils.bold_label(info_text)]), True, True, 0)
        info.pack_start(guiutils.get_left_justified_box([guiutils.pad_label(40, 12), folder_label]), True, True, 0)
        info.pack_start(guiutils.get_left_justified_box([guiutils.pad_label(12, 12), self.size_info]), True, True, 0)

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

    def get_cache_folder(self):
        return utils.get_hidden_user_dir_path() + "/" + self.folder

    def get_folder_files(self):
        cache_folder = self.get_cache_folder()
        return [f for f in listdir(cache_folder) if isfile(join(cache_folder, f))]
    
    def get_folder_size(self):
        files = self.get_folder_files()
        size = 0
        for f in files:
            size += os.path.getsize(self.get_cache_folder() +"/" + f)
        return size

    def get_folder_size_str(self):
        size = self.get_folder_size()
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
            
        dialogutils. warning_confirmation(self.warning_confirmation, primaty_text, secondary_text, gui.editor_window.window, None, False, True)

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
        print "deleting ", self.folder
        
        files = self.get_folder_files()
        for f in files:
            os.remove(self.get_cache_folder() +"/" + f)

        self.size_info.set_text(self.get_folder_size_str())
        self.size_info.queue_draw()
            
def show_disk_management_dialog():
    dialog = Gtk.Dialog(_("Disk Cache Manager"), None,
                    Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    (_("Close").encode('utf-8'), Gtk.ResponseType.CLOSE))

    panels = _get_disk_dir_panels()

    pane = Gtk.VBox(True, 2)
    for panel in panels:
        pane.pack_start(panel.vbox, True, True, 0)

    guiutils.set_margins(pane, 12, 24, 12, 12)

    dialog.connect('response', dialogutils.dialog_destroy)
    
    dialog.vbox.pack_start(pane, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    dialog.show_all()
    return dialog

def _get_disk_dir_panels():
    panels = []
    panels.append(DiskFolderManagementPanel("audiolevels", _("Audio Levels Data"), RECREATE_WARNING))
    panels.append(DiskFolderManagementPanel("gmic", _("G'Mic Tool Session Data"), NO_WARNING))
    panels.append(DiskFolderManagementPanel("natron", _("Natron Clip Export Data"), NO_WARNING))
    panels.append(DiskFolderManagementPanel("rendered_clips", _("Rendered Files"), PROJECT_DATA_WARNING))
    panels.append(DiskFolderManagementPanel("thumbnails", _("Thumbnails"), RECREATE_WARNING))
    panels.append(DiskFolderManagementPanel("user_profiles", _("User Created Custom Profiles"), PROJECT_DATA_WARNING))

    return panels
