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

import dialogutils
import guiutils

NO_WARNING = 0
RECREATE_WARNING = 1
PROJECT_DATA_WARNING = 2

class DiskFolderManagementPanel:
    
    def __init__(self, folder, info_text, warning_level):
        self.folder = folder
        self.warning_level = warning_level
                
        self.destroy_button = Gtk.Button(_("Destroy data"))
        
        
        toprow = Gtk.HBox(True, 2)
        toprow.pack_start(guiutils.get_left_justified_box([guiutils.bold_label(info_text)]), True, True, 0)
        toprow.pack_start(guiutils.get_left_justified_box([guiutils.pad_label(12, 12), Gtk.Label("/" + folder)]), True, True, 0)
        toprow.pack_start(guiutils.get_left_justified_box([guiutils.pad_label(12, 12), Gtk.Label("26 MB")]), True, True, 0)
        toprow.pack_start(self.destroy_button, False, False, 0)
        
        self.vbox = Gtk.VBox(False, 2)
        self.vbox.pack_start(toprow, False, False, 0)

        

def show_disk_management_dialog():
    dialog = Gtk.Dialog(_("Profiles Manager"), None,
                    Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    (_("Close Manager").encode('utf-8'), Gtk.ResponseType.CLOSE))

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
    panels.append(DiskFolderManagementPanel("audiolevels", _("Audio Leveld Data"), RECREATE_WARNING))
    panels.append(DiskFolderManagementPanel("gmic", _("G'Mic tool old session data"), NO_WARNING))
    panels.append(DiskFolderManagementPanel("natron", _("Natron Clip Export data"), NO_WARNING))
    panels.append(DiskFolderManagementPanel("rendered_clips", _("Natron Clip Export data"), PROJECT_DATA_WARNING))
    panels.append(DiskFolderManagementPanel("thumbnails", _("Natron Clip Export data"), RECREATE_WARNING))
    panels.append(DiskFolderManagementPanel("user_profiles", _("User Created Custom Profiles"), PROJECT_DATA_WARNING))

    return panels
