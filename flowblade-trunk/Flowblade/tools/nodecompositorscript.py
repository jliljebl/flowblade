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

from gi.repository import Gtk

import xml.dom.minidom

import respaths

readymades_doc = None

# xml attr. and elem. names used to encode
PROGRAM = "program"
EDITABLE_PROGRAM = "editableparam"
NAME = "name"
GROUP = "group"
EDITABLE_PARAM = "editableparam"
NODE_ID = "nodeid"
PARAM_ID = "paramid"
PARAM_TYPE = "paramtype"
VALUE ="value"
PROJECT_FILE = "projectfile"

_phantom_programs = []
_phantom_program_groups = []

_programs_menu = Gtk.Menu()

def load_phantom_readymades_xml():
    print "Loading phantom readymades xml..."

    _program_groups_names = {}
    _program_groups_names["Group 1"] = _("Group 1")
    _program_groups_names["Group 2"] = _("Group 2")
    _program_groups_names["Misc"] = _("Misc")

    global readymades_doc
    readymades_doc = xml.dom.minidom.parse(respaths.PHANTOM_READYMADES_DOC)

    global _phantom_programs
    _phantom_programs = []
    load_groups = {}
    
    program_nodes = readymades_doc.getElementsByTagName(PROGRAM)
    for prog_node in program_nodes:
        program_info = PhantomProgram(prog_node)

        _phantom_programs.append(program_info)

        try:
            translated_group_name = _program_groups_names[program_info.group]
        except:
            translated_group_name = "Misc"

        try:
            group = load_groups[translated_group_name]
            group.append(program_info)
        except:
            load_groups[translated_group_name] = [program_info]

    # We used translated group names as keys in load_groups
    # Now we sort them and use them to place data in groups array in the same
    # order as it will be presented to user, so selection indexes in gui components will match
    # group array indexes here.
    sorted_keys = sorted(load_groups.keys())
    global _phantom_program_groups
    for gkey in sorted_keys:
        group = load_groups[gkey]
        add_group = sorted(group, key=lambda program_info: program_info.name)
        _phantom_program_groups.append((gkey, add_group))



class PhantomProgram:

    def __init__(self, phantom_program_node):
        self.name = phantom_program_node.getElementsByTagName(NAME).item(0).firstChild.nodeValue
        self.group = phantom_program_node.getElementsByTagName(GROUP).item(0).firstChild.nodeValue
        self.project_file = phantom_program_node.getElementsByTagName(PROJECT_FILE).item(0).firstChild.nodeValue

        self.params = []
        ep_list = phantom_program_node.getElementsByTagName(EDITABLE_PARAM)
        for ep in ep_list:
            self.params.append(PhantomEditableParam(ep))



class PhantomEditableParam:
    
    def __init__(self, editable_param_node):
        
        self.name = editable_param_node.getAttribute(NAME)
        self.nodeid = editable_param_node.getAttribute(NODE_ID)
        self.paramid = editable_param_node.getAttribute(PARAM_ID)
        self.paramtype = editable_param_node.getAttribute(PARAM_TYPE)
        self.value = editable_param_node.getElementsByTagName(VALUE).item(0).firstChild.nodeValue


# ---------------------------------------------------- interface
def get_default_phantom_prog():
    key, group = _phantom_program_groups[0]
    return group[0]
    

# ------------------------------------------------------- menu creation
def show_menu(event, callback):
    # Remove current items
    items = _programs_menu.get_children()
    for item in items:
        _programs_menu.remove(item)

    for programs_group in _phantom_program_groups:
        group_name, group = programs_group
        group_item = Gtk.MenuItem(group_name)

        _programs_menu.append(group_item)
        sub_menu = Gtk.Menu()
        group_item.set_submenu(sub_menu)

        for prog in group:
            prog_item = Gtk.MenuItem(prog.name)
            sub_menu.append(prog_item)
            prog_item.connect("activate", callback, prog)

    _programs_menu.show_all()
    _programs_menu.popup(None, None, None, None, event.button, event.time)
