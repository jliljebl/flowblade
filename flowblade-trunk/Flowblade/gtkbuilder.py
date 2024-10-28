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
Widget builder module to help moving to Gtk4.
"""

from gi.repository import Gtk

import os

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

def get_file_chooser_button(title):
    b = Gtk.Button.new_with_label(title)
    b.connect("clicked", _file_chooser_button_clicked)
    b.set_action = lambda a : _set_file_action(b, a)
    b.set_current_folder = lambda fp : _set_current_folder(b, fp)
    return b


    
# ---------------------------------------------------- Gtk 4 replace methods.
# H/VPaned
def _pack1(paned, child, resize, shrink):
    paned.set_start_child(child)

def _pack2(paned, child, resize, shrink):
    paned.set_end_child(child)

# FileChooserButton
def _set_file_action(b, action):
    b.priv_action = action
    
def _set_current_folder(b, file_path):
    b.current_folder = file_path
    b.set_label(_filename(file_path))
    
def _filename(path):
    path = path.rstrip("/")
    return os.path.basename(path)