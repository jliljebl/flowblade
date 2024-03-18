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
Intermediate layer to switch use Gtk.Box instead of Gtk.VBox and Gtk.HBox. 
"""


from gi.repository import Gtk

def HBox(homogeneous=False, spacing=0):
     box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, spacing)
     box.set_homogeneous(homogeneous)
     box.pack_start = lambda child, expand, fill, padding: _pack_start(box, child, expand, fill, padding)
     box.clear_children = lambda : _clear_box(box)
     return box

def VBox(homogeneous=False, spacing=0):
     box = Gtk.Box.new(Gtk.Orientation.VERTICAL, spacing)
     box.set_homogeneous(homogeneous)
     box.pack_start = lambda child, expand, fill, padding: _pack_start(box, child, expand, fill, padding)
     box.clear_children = lambda : _clear_box(box)
     return box

def build_vertical(box):
    box.pack_start = lambda child, expand, fill, padding: _pack_start(box, child, expand, fill, padding)
    box.set_homogeneous(False)
    box.set_spacing(0)
    box.set_orientation(Gtk.Orientation.VERTICAL)

def build_horizontal(box):
    box.pack_start = lambda child, expand, fill, padding: _pack_start(box, child, expand, fill, padding)
    box.set_homogeneous(False)
    box.set_spacing(0)
    box.set_orientation(Gtk.Orientation.HORIZONTAL)

def EventBox():
    box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
    box.add = lambda widget: _event_box_add(box, widget)
    box.set_child = lambda widget: _event_box_add(box, widget)
    return box

def _pack_start(box, child, expand, fill, padding):
    print(type(box))

def _clear_box(box):
    first_child = box.get_first_child()
    while first_child != None:
        box.remove(first_child)
        first_child = box.first_child()

def _event_box_add(box, widget):
    box.append(widget)

def get_file_chooser_button():
    b = Gtk.Button.new_with_label("File Chooser")
    b.set_action = lambda a : _set_action(a)
    b.set_current_folder = lambda fp : _set_current_folder(fp)
    return b

def _set_action(action):
    pass
    
def _set_current_folder(file_path):
    pass
