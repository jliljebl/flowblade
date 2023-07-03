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
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

from gi.repository import Gio, Gtk

from editorstate import APP
from editorstate import current_sequence
import guicomponents
import utils


_markers_popover = None
_markers_menu = None

# -------------------------------------------------- menuitems builder fuctions
def add_menu_action(menu, label, item_id, msg_str, callback):
    menu.append(label, "app." + item_id) 
    
    action = Gio.SimpleAction(name=item_id)
    action.connect("activate", callback, msg_str)
    APP().add_action(action)

def add_menu_action_check(menu, label, item_id, msg_str):
    action = Gio.SimpleAction.new_stateful(name=item_id, parameter_type=None, state=GLib.Variant.new_boolean(True))
    action.connect("activate", lambda w, e, msg:callback(msg), msg_str)
    APP().add_action(action)

    menu_item = Gio.MenuItem.new(label, item_id)
    menu_item.set_action_and_target_value(item_id, None)
    menu.append_item(menu_item)

def add_menu_action_radio(menu, label, item_id, msg_str):
    target_variat = GLib.Variant.new_string("stringiii")
    action = Gio.SimpleAction.new_stateful(name=item_id, parameter_type= GLib.VariantType.new("s"), state=target_variat)
    action.connect("activate", lambda w, e, msg:callback(msg), msg_str)
    APP().add_action(action)

    menu_item = Gio.MenuItem.new(label, item_id)
    menu_item.set_action_and_target_value(item_id, target_variat)
    menu.append_item(menu_item)


# --------------------------------------------------- popover builder functions
def markers_menu_launcher(callback, pixbuf, w=22, h=22):
    launch = guicomponents.PressLaunchPopover(callback, pixbuf, w, h)
    return launch

def markers_menu_show(launcher, widget, callback):
    global _markers_popover, _markers_menu

    if _markers_menu != None:
        _markers_menu.remove_all()
    else:
        _markers_menu = Gio.Menu.new()
    
    seq = current_sequence()
    markers_exist = len(seq.markers) != 0

    if markers_exist: 
        markers_section = Gio.Menu.new()
        for i in range(0, len(seq.markers)):
            marker = seq.markers[i]
            name, frame = marker
            item_str  = utils.get_tc_string(frame) + " " + name
                    
            add_menu_action(markers_section, item_str, "midbar.markers." + str(i), str(i), callback)

        _markers_menu.append_section(None, markers_section)

    actions_section = Gio.Menu.new()
    add_menu_action(actions_section, _("Add Marker"), "midbar.markers.addmarker", "add", callback)
    add_menu_action(actions_section, _("Delete Marker"), "midbar.markers.delete", "delete", callback)
    add_menu_action(actions_section, _("Delete All Markers"), "midbar.markers.deleteall", "deleteall", callback)
    add_menu_action(actions_section, _("Rename Marker"), "midbar.markers.rename", "rename", callback)
    _markers_menu.append_section(None, actions_section)

    _markers_popover = Gtk.Popover.new_from_model(widget, _markers_menu)
    launcher.connect_launched_menu(_markers_popover)
    _markers_popover.show()
