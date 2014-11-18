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

import pygtk
pygtk.require('2.0');
import gtk



def load_titler_data_dialog(callback):    
    dialog = gtk.FileChooserDialog(_("Select Titler Data File"), None, 
                                   gtk.FILE_CHOOSER_ACTION_OPEN, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                    _("OK").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()

def save_titler_data_as_dialog(callback, current_name, open_dir):    
    dialog = gtk.FileChooserDialog(_("Save Titler Layers As"), None, 
                                   gtk.FILE_CHOOSER_ACTION_SAVE, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                   _("Save").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    dialog.set_current_name(current_name)
    dialog.set_do_overwrite_confirmation(True)
    if open_dir != None:
        dialog.set_current_folder(open_dir)
    
    dialog.set_select_multiple(False)
    dialog.connect('response', callback)
    dialog.show()

def save_titler_graphic_as_dialog(callback, current_name, open_dir):    
    dialog = gtk.FileChooserDialog(_("Save Titler Graphic As"), None, 
                                   gtk.FILE_CHOOSER_ACTION_SAVE, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                   _("Save").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    dialog.set_current_name(current_name)
    dialog.set_do_overwrite_confirmation(True)
    if open_dir != None:
        dialog.set_current_folder(open_dir)
    
    dialog.set_select_multiple(False)
    file_filter = gtk.FileFilter()
    file_filter.add_pattern("*" + ".png")
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()
