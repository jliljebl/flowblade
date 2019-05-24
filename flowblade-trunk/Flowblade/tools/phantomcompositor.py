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
import os
import subprocess
import sys

from gi.repository import Gtk

import appconsts
import dialogutils
import editorstate
import guiutils
import gui
import respaths
import userfolders
import utils

_phantom_found = False

def test_availablity():
    global _phantom_found
    if os.path.exists(respaths.PHANTOM_JAR) == True:
        _phantom_found = True

def launch_phantom():
    respaths.PHANTOM_JAR
    if _phantom_found == False:
        info_row = guiutils.get_centered_box([Gtk.Label(_("Phantom2D tool has not been installed on your system."))])
        
        link_info_row = guiutils.get_centered_box([Gtk.Label(_("Install instructions:"))])
        link = Gtk.LinkButton.new("https://github.com/jliljebl/phantom2D")
        link_row = guiutils.get_centered_box([link])

        dir_info_row = guiutils.get_centered_box([Gtk.Label(_("Install directory for Phantom2D tool:"))])
        dir_label = Gtk.Label(respaths.PHANTOM_JAR.rstrip("/Phantom2D.jar"))
        dir_label.set_selectable(True)
        dir_row = guiutils.get_centered_box([Gtk.Label(respaths.PHANTOM_JAR.rstrip("/Phantom2D.jar"))])
        dir_row.set_margin_top(8)
        
        panel = Gtk.VBox()
        panel.pack_start(info_row, False, False, 0)
        panel.pack_start(guiutils.pad_label(12, 24), False, False, 0)
        panel.pack_start(link_info_row, False, False, 0)
        panel.pack_start(link_row, False, False, 0)
        panel.pack_start(guiutils.pad_label(12, 24), False, False, 0)
        panel.pack_start(dir_info_row, False, False, 0)
        panel.pack_start(dir_row, False, False, 0)
        dialogutils.panel_ok_dialog(_("Phantom2D not found"), panel)
        return

    FLOG = open(userfolders.get_cache_dir() + "log_phantom", 'w')
    subprocess.Popen([str(respaths.LAUNCH_DIR + "flowbladephantom") + " " + str(respaths.PHANTOM_JAR) \
                        + " profile" + " " + _get_underscored_profile() \
                        + " cachefolder "  + userfolders.get_cache_dir() + appconsts.PHANTOM_DIR + "/" + appconsts.PHANTOM_DISK_CACHE_DIR], shell=True, stdin=FLOG, stdout=FLOG, stderr=FLOG)

    print "Phantom2D launched"

def _get_underscored_profile():
    return editorstate.PROJECT().profile_desc.replace (" ", "_")
