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

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

import appconsts
import editorpersistance
import guiutils
import respaths

# Timeline tools data
_TOOLS_DATA = None

_menu = Gtk.Menu()

def init_data():
    global _TOOLS_DATA
    _TOOLS_DATA = { appconsts.TLINE_TOOL_INSERT:    (_("Insert"), Gtk.Image.new_from_file(respaths.IMAGE_PATH + "insertmove_cursor.png")),
                    appconsts.TLINE_TOOL_OVERWRITE: (_("Overwrite"), Gtk.Image.new_from_file(respaths.IMAGE_PATH + "overwrite_cursor.png")),
                    appconsts.TLINE_TOOL_TRIM:      (_("Trim"), Gtk.Image.new_from_file(respaths.IMAGE_PATH + "oneroll_cursor.png")),
                    appconsts.TLINE_TOOL_ROLL:      (_("Roll"), Gtk.Image.new_from_file(respaths.IMAGE_PATH + "tworoll_cursor.png")),
                    appconsts.TLINE_TOOL_SLIP:      (_("Slip"), Gtk.Image.new_from_file(respaths.IMAGE_PATH + "slide_cursor.png")),
                    appconsts.TLINE_TOOL_SPACER:    (_("Spacer"), Gtk.Image.new_from_file(respaths.IMAGE_PATH + "multimove_cursor.png")),
                    appconsts.TLINE_TOOL_BOX:       (_("Box"), Gtk.Image.new_from_file(respaths.IMAGE_PATH + "overwrite_cursor_box.png")) 
                  }

def menu_launched(widget, event):
    guiutils.remove_children(_menu)
    
    for tool_id in _TOOLS_DATA:
        name, icon = _TOOLS_DATA[tool_id]
        _menu.add(_get_workflow_tool_menu_item(_workflow_menu_callback, tool_id, name, icon))

    """
    _menu.add(_get_check_tool_menu_item(_menu_callback, "kkkkk"))
    _menu.add(guiutils.get_menu_item(_("Save Animation") + "...", _menu_callback, "save" ))
    guiutils.add_separetor(_menu)
    _menu.add(guiutils.get_menu_item(_("Natron Webpage"), _menu_callback, "web" ))
    guiutils.add_separetor(_menu)
    _menu.add(guiutils.get_menu_item(_("Close"), _menu_callback, "close" ))
    """
    
    _menu.popup(None, None, None, None, event.button, event.time)


    

def _get_workflow_tool_menu_item(callback, tool_id, tool_name, tool_icon):
    is_active_check_box = Gtk.CheckButton.new()
    tool_active = (tool_id in editorpersistance.prefs.active_tools)
    is_active_check_box.set_active(tool_active)
    #is_active_check_box.connect("toggled", lambda w: _tool_active_toggled(w, tool_id))

    tool_img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "overwrite_cursor.png")
    tool_name_label = Gtk.Label(tool_name)
    
    hbox = Gtk.HBox()
    hbox.pack_start(is_active_check_box, False, False, 0)
    hbox.pack_start(guiutils.pad_label(4, 4), False, False, 0)
    hbox.pack_start(tool_icon, False, False, 0)
    hbox.pack_start(guiutils.pad_label(4, 4), False, False, 0)
    hbox.pack_start(tool_name_label, False, False, 0)
    hbox.show_all()
    
    item = Gtk.MenuItem()
    item.add(hbox)
    #item.connect("activate", callback, tool_id)
    item.show()
    
    item.set_submenu(_get_workflow_tool_submenu(callback, tool_id))

    return item
"""
def _tool_active_toggled(widget, tool_id):
    print widget.get_active(), tool_id
"""

def _get_workflow_tool_submenu(callback, tool_id):
    sub_menu = Gtk.Menu()
    
    tool_active = (tool_id in editorpersistance.prefs.active_tools)
    if tool_active == True:
        activity_item = guiutils.get_menu_item(_("Deactivate Tool"), callback, (tool_id, "deactivate"))
    else:
        activity_item = guiutils.get_menu_item(_("Activate Tool"), callback, (tool_id, "activate"))
    
    activity_item.show()
    sub_menu.add(activity_item)

    guiutils.add_separetor(sub_menu)
    
    up = guiutils.get_menu_item(_("Move Up"), callback, (tool_id, "up"))
    up.show()
    down = guiutils.get_menu_item(_("Move Down"), callback, (tool_id, "down"))
    down.show()
    sub_menu.add(up)
    sub_menu.add(down)
    
    return sub_menu
    
def _workflow_menu_callback(widget, data):
    tool_id, msg = data
    if msg ==  "deactivate":
        editorpersistance.prefs.active_tools.remove(tool_id)
    elif msg ==  "activate":
        for i in range(0, len(editorpersistance.prefs.active_tools)):
            active_tool = editorpersistance.prefs.active_tools[i]
            if tool_id > active_tool:
                if i < len(editorpersistance.prefs.active_tools) - 1:
                    editorpersistance.prefs.active_tools.insert(i, tool_id)
                    return
                else:
                    editorpersistance.prefs.active_tools.append(tool_id)
                    return 

        editorpersistance.prefs.active_tools.append(tool_id)
