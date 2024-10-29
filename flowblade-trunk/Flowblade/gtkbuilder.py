"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2024 Janne Liljeblad.

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
Widget builder module to help moving to Gtk 4.
"""

from gi.repository import Gtk

import os

import gui


GTK_3 = 3
GTK_3 = 4
GTK_VERSION = GTK_3 # Flip when moving over.


def HPaned():
    paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
    """
    Uncomment for eventual Gtk4.
    paned.pack1 = lambda child, resize, shrink: _pack1(paned, child, resize, shrink)
    paned.pack2 = lambda child, resize, shrink: _pack2(paned, child, resize, shrink)
    """
    return paned

def VPaned():
    paned = Gtk.Paned.new(Gtk.Orientation.VERTICAL)
    """
    Uncomment for eventual Gtk4.
    paned.pack1 = lambda child, resize, shrink: _pack1(paned, child, resize, shrink)
    paned.pack2 = lambda child, resize, shrink: _pack2(paned, child, resize, shrink)
    """
    return paned

def get_file_chooser_button(title, parent=None):
    b = Gtk.Button.new_with_label(title)
    b.title = title
    b.priv_action = None
    b.priv_current_folder = None
    b.priv_filenames = None
    b.priv_parent = parent
    b.connect("clicked", _file_chooser_button_clicked)
    b.set_action = lambda a : _set_file_action(b, a)
    b.set_current_folder = lambda fp : _set_current_folder(b, fp)
    b.get_current_folder = lambda : _get_current_folder(b)
    b.get_filenames = lambda : _get_filenames(b)
    b.get_filename = lambda : _get_filename(b)
    
    return b

# ---------------------------------------------------- Gtk 4 replace methods.
# --- H/VPaned
def _pack1(paned, child, resize, shrink):
    paned.set_start_child(child)

def _pack2(paned, child, resize, shrink):
    paned.set_end_child(child)

# --- FileChooserButton
def _file_chooser_button_clicked(b):
    dialog = Gtk.FileChooserDialog(b.title, b.priv_parent,
                                   b.priv_action,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _get_file_chooser_action_ok_name(b.priv_action), Gtk.ResponseType.ACCEPT))
    dialog.b = b
    dialog.set_action(b.priv_action)
    dialog.set_current_folder(b.priv_current_folder)
    dialog.set_do_overwrite_confirmation(True)
    dialog.connect('response', _file_selection_done)
    dialog.show()

def _file_selection_done(dialog, response_id):
    if response_id == Gtk.ResponseType.CANCEL:
        dialog.destroy()
        return
    b = dialog.b
    b.priv_filenames = dialog.get_filenames()
    if b.priv_action == Gtk.FileChooserAction.SELECT_FOLDER:
        b.priv_current_folder = b.priv_filenames[0] 
    b.set_label(_filename(b.priv_filenames[0]))
    
    dialog.destroy()

def _set_file_action(b, action):
    b.priv_action = action
    
def _set_current_folder(b, file_path):
    b.priv_current_folder = file_path
    b.priv_filenames = [file_path]
    b.set_label(_filename(file_path))
    
def _filename(path):
    path = path.rstrip("/")
    return os.path.basename(path)

def _get_file_chooser_action_ok_name(action):
    if GTK_VERSION == GTK_3:
        if action == Gtk.FileChooserAction.SELECT_FOLDER:
            return _("Open")
        else:
            return _("Open")

def _get_filenames(b):
    return b.priv_filenames

def _get_filename(b):
    return b.priv_filenames[0]

def _get_current_folder(b):
    return b.priv_current_folder