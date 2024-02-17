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
Intermediate layer to switch use Gtk.Box instead of Gtk.VBox and Gtk.HBox. 
"""


from gi.repository import Gtk

def HBox(homogeneous=False, spacing=0):
     box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, spacing)
     box.set_homogeneous(homogeneous)
     return box

def VBox(homogeneous=False, spacing=0):
     box = Gtk.Box.new(Gtk.Orientation.VERTICAL, spacing)
     box.set_homogeneous(homogeneous)
     return box

