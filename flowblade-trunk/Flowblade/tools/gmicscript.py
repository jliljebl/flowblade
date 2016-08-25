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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""


from gi.repository import Gtk
import xml.dom.minidom

import respaths

GMIC_SCRIPT_NODE = "gmicscript"

_scripts = None
_script_groups = []
_scripts_menu = Gtk.Menu()

class GmicScript:
    """
    Info of a filter (mlt.Service) that is is available to the user.
    Constructor input is a dom node object.
    This is used to create FilterObject objects.
    """
    def __init__(self, script_node):
        self.name = script_node.getElementsByTagName("name").item(0).firstChild.nodeValue
        self.script = script_node.getElementsByTagName("script").item(0).firstChild.nodeValue
        self.group = script_node.getElementsByTagName("group").item(0).firstChild.nodeValue

def get_scripts():
    return _scripts

def load_preset_scripts_xml():

    _script_groups_names = {}
    _script_groups_names["Black and White"] = _("Black and White")
    _script_groups_names["Filter"] = _("Filter")
    _script_groups_names["Blur"] = _("Blur")
    _script_groups_names["Special Effect"] = _("Special Effect")
    _script_groups_names["Misc"] = _("Misc")
    _script_groups_names["Drawing"] = _("Drawing")
    _script_groups_names["Painting"] = _("Painting")
    _script_groups_names["Transform"] = _("Transform")
    _script_groups_names["Glow"] = _("Glow")
    _script_groups_names["Geometric"] = _("Geometric")
    _script_groups_names["Edges"] = _("Edges")
    _script_groups_names["New"] = _("New")
    _script_groups_names["Texture"] = _("Texture")
    _script_groups_names["Technical"] = _("Technical")
    _script_groups_names["Photographic"] = _("Photographic")
    _script_groups_names["Pattern"] = _("Pattern")
    _script_groups_names["Artistic"] = _("Artistic")
    _script_groups_names["Basic"] = _("Basic")
    _script_groups_names["Film Emulate Print"] = _("Film Emulate Print")
    _script_groups_names["Film Emulate Negative Color"] = _("Film Emulate Negative Color")
    _script_groups_names["Film Emulate Negative New"] = _("Film Emulate Negative New")

    presets_doc = xml.dom.minidom.parse(respaths.GMIC_SCRIPTS_DOC)

    global _scripts
    _scripts = []
    load_groups = {}
    script_nodes = presets_doc.getElementsByTagName(GMIC_SCRIPT_NODE)
    for script_node in script_nodes:
        gmic_script = GmicScript(script_node)
        _scripts.append(gmic_script)

        # Add filter compositor filters or filter groups
        try:
            translated_group_name = _script_groups_names[gmic_script.group]
        except:
            translated_group_name = "Misc"

        try:
            group = load_groups[translated_group_name]
            group.append(gmic_script)
        except:
            load_groups[translated_group_name] = [gmic_script]

    # We used translated group names as keys in load_groups
    # Now we sort them and use them to place data in groups array in the same
    # order as it will be presented to user, so selection indexes in gui components will match
    # group array indexes here.
    sorted_keys = sorted(load_groups.keys())
    global _script_groups
    for gkey in sorted_keys:
        group = load_groups[gkey]
        add_group = sorted(group, key=lambda gmic_script: gmic_script.name)
        _script_groups.append((gkey, add_group))

def get_default_script():
    key, group = _script_groups[0]
    return group[0]

def show_menu(event, callback):
    # Remove current items
    items = _scripts_menu.get_children()
    for item in items:
        _scripts_menu.remove(item)

    for script_group in _script_groups:
        group_name, group = script_group
        group_item = Gtk.MenuItem(group_name)
        #group_item.connect("activate", callback, i)
        _scripts_menu.append(group_item)
        sub_menu = Gtk.Menu()
        group_item.set_submenu(sub_menu)

        for script in group:
            script_item = Gtk.MenuItem(script.name)
            sub_menu.append(script_item)
            script_item.connect("activate", callback, script)

    _scripts_menu.show_all()
    _scripts_menu.popup(None, None, None, None, event.button, event.time)

