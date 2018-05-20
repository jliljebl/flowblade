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

"""
Modeule handles displaying tool meni, tool keyboard shortuts and workflow configuration activating and moving tools,
and setting relevant timeline behaviours.

"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk

import appconsts
import editevent
import editorpersistance
import gui
import guiutils
import respaths

# Timeline tools data
_TOOLS_DATA = None

_tools_menu = Gtk.Menu()
_workflow_menu = Gtk.Menu()

def init_data():
    global _TOOLS_DATA
    _TOOLS_DATA = { appconsts.TLINE_TOOL_INSERT:    (_("Insert"), "insertmove_cursor.png"),
                    appconsts.TLINE_TOOL_OVERWRITE: (_("Overwrite"), "overwrite_cursor.png"),
                    appconsts.TLINE_TOOL_TRIM:      (_("Trim"), "oneroll_cursor.png"),
                    appconsts.TLINE_TOOL_ROLL:      (_("Roll"), "tworoll_cursor.png"),
                    appconsts.TLINE_TOOL_SLIP:      (_("Slip"), "slide_cursor.png"),
                    appconsts.TLINE_TOOL_SPACER:    (_("Spacer"), "multimove_cursor.png"),
                    appconsts.TLINE_TOOL_BOX:       (_("Box"), "overwrite_cursor_box.png") 
                  }

#----------------------------------------------------- workflow presets
def _set_workflow_SIMPLIFIED():
    pass

def _set_workflow_STANDARD():
    pass

def _set_workflow_FILM_STYLE():
    editorpersistance.prefs.active_tools = [1, 2, 3, 4, 5, 6, 7]
    editorpersistance.save()

    editevent.set_default_edit_mode()


# --------------------------------------------------------------- tools menu
def get_tline_tool_popup_menu(launcher, event, callback):
    menu = _tools_menu
    guiutils.remove_children(menu)

    menu.set_accel_group(gui.editor_window.accel_group)
    menu.set_take_focus(False)
    menu_items = []
    
    kb_shortcut_number = 1
    for tool_id in editorpersistance.prefs.active_tools:
        tool_name, tool_icon_file = _TOOLS_DATA[tool_id]

        menu_item = _get_image_menu_item(tool_icon_file, tool_name, callback, tool_id)
        accel_path = "<Actions>/WindowActions/TOOL_ACTION_KEY_" + str(kb_shortcut_number)
        menu_item.set_accel_path(accel_path)
        menu.add(menu_item)
        menu_items.append(menu_item)
        kb_shortcut_number = kb_shortcut_number + 1

    menu.connect("hide", lambda w : _tools_menu_hidden(w, menu_items))
    menu.show_all()
    menu.popup(None, None, None, None, event.button, event.time)

def _tools_menu_hidden(tools_menu, menu_items):
    # needed to make number 1-6 work elsewhere in the application
    for menu_item in menu_items:
        menu_item.set_accel_path(None)

def _get_image_menu_item(tool_icon_file, text, callback, data):
    item = Gtk.ImageMenuItem()
    tool_img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + tool_icon_file)
        
    item.set_image(tool_img)
    item.connect("activate", callback, data)
    item.set_always_show_image(True)
    item.set_use_stock(False)
    item.set_label(text)
    item.show()
    return item
    
    
# ---------------------------------------------------- workflow menu
def workflow_menu_launched(widget, event):
    guiutils.remove_children(_workflow_menu)

    # ---- preset
    presets_item = Gtk.MenuItem.new_with_label(_("Workflow Presets"))
    presets_item.show()

    presets_menu = Gtk.Menu()
    
    simplified = guiutils.get_menu_item(_("Simplified"), _workflow_menu_callback, (None, "preset simplified"))
    simplified.show()
    presets_menu.add(simplified)

    standart = guiutils.get_menu_item(_("Standard"), _workflow_menu_callback, (None, "preset standart"))
    standart.show()
    presets_menu.add(standart)

    standart = guiutils.get_menu_item(_("Film Style"), _workflow_menu_callback, (None, "preset filmstyle"))
    standart.show()
    presets_menu.add(standart)
    
    presets_item.set_submenu(presets_menu)
    _workflow_menu.add(presets_item)

    # --- behaviours
    guiutils.add_separetor(_workflow_menu)

    behaviours_item = Gtk.MenuItem.new_with_label(_("Behaviours"))
    behaviours_item.show()

    behaviours_menu = Gtk.Menu()
    
    delete_item = Gtk.MenuItem.new_with_label(_("Default Delete Action"))
    delete_item.show()

    delete_menu = Gtk.Menu()
    labels = [_("Lift"), _("Splice Out")]
    msgs = ["delete lift", "delete splice"]
    guiutils.get_radio_menu_items_group(delete_menu, labels, msgs, _workflow_menu_callback, 0)

    delete_item.set_submenu(delete_menu)
    behaviours_menu.add(delete_item)

    dnd_item = Gtk.MenuItem.new_with_label(_("Drag'n'Drop Action"))
    dnd_item.show()
    
    dnd_menu = Gtk.Menu()
    labels = [_("Always Overwrite"), _("Overwrite on non-V1"), _("Always Insert")]
    msgs = ["always overwrite", "verwrite nonV1", "always insert"]
    guiutils.get_radio_menu_items_group(dnd_menu, labels, msgs, _workflow_menu_callback, 0)

    dnd_item.set_submenu(dnd_menu)
    behaviours_menu.add(dnd_item)
    
    behaviours_item.set_submenu(behaviours_menu)
    _workflow_menu.add(behaviours_item)

    # --- tools
    guiutils.add_separetor(_workflow_menu)
    
    # Active tools
    non_active_tools = range(1, 8) # we have 7 tools currently
    for i in range(0, len(editorpersistance.prefs.active_tools)):#  tool_id in _TOOLS_DATA:
        tool_id = editorpersistance.prefs.active_tools[i]
        tool_name, tool_icon_file = _TOOLS_DATA[tool_id]
        _workflow_menu.add(_get_workflow_tool_menu_item(_workflow_menu_callback, tool_id, tool_name, tool_icon_file, i+1))
        non_active_tools.remove(tool_id)

    guiutils.add_separetor(_workflow_menu)
    
    # Non-active tools
    for tool_id in non_active_tools:
        tool_name, tool_icon_file = _TOOLS_DATA[tool_id]
        _workflow_menu.add(_get_workflow_tool_menu_item(_workflow_menu_callback, tool_id, tool_name, tool_icon_file, -1))
        
    _workflow_menu.popup(None, None, None, None, event.button, event.time)

def _get_workflow_tool_menu_item(callback, tool_id, tool_name, tool_icon_file, position):

    tool_active = (tool_id in editorpersistance.prefs.active_tools)

    tool_img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + tool_icon_file)
    tool_name_label = Gtk.Label(tool_name)
    
    hbox = Gtk.HBox()
    hbox.pack_start(guiutils.pad_label(4, 4), False, False, 0)
    hbox.pack_start(tool_img, False, False, 0)
    hbox.pack_start(guiutils.pad_label(4, 4), False, False, 0)
    hbox.pack_start(tool_name_label, False, False, 0)
    hbox.show_all()
    hbox.set_sensitive(tool_active)
    item = Gtk.MenuItem()
    item.add(hbox)
    item.show()
    
    item.set_submenu(_get_workflow_tool_submenu(callback, tool_id, position))

    return item

def _get_radio_menu_item_group(menu, labels, msgs, callback, active_index):
    first_item = Gtk.RadioMenuItem()
    first_item.set_label(labels[0])
    first_item.show()
    menu.append(first_item)
    if active_index == 0:
        first_item.set_active(True)
    first_item.connect("activate", callback, msgs[0])
    
    for i in range(1, len(labels)):
        radio_item = Gtk.RadioMenuItem.new_with_label([first_item], labels[i])
        menu.append(radio_item)
        radio_item.show()
        if active_index == i:
            radio_item.set_active(True)
        radio_item.connect("activate", callback, msgs[i])

def _get_workflow_tool_submenu(callback, tool_id, position):
    sub_menu = Gtk.Menu()
    
    tool_active = (tool_id in editorpersistance.prefs.active_tools)
    activity_item = Gtk.CheckMenuItem(_("Tool Active").encode('utf-8'))
    activity_item.set_active(tool_active)
    activity_item.connect("toggled", callback, (tool_id, "activity"))
    activity_item.show()
    sub_menu.add(activity_item)

    guiutils.add_separetor(sub_menu)
    
    position_item = Gtk.MenuItem.new_with_label(_("Set Position"))
    if tool_active == False:
        position_item.set_sensitive(False)
    position_item.show()

    position_menu = Gtk.Menu()
    
    for i in range(1, len(editorpersistance.prefs.active_tools) + 1):
        move_to_position_item = guiutils.get_menu_item(str(i), _workflow_menu_callback, (tool_id, str(i)))
        if i == position or position == -1:
            move_to_position_item.set_sensitive(False)
        move_to_position_item.show()
        position_menu.add(move_to_position_item)
        
    position_item.set_submenu(position_menu)

    sub_menu.add(position_item)
    
    return sub_menu
    
def _workflow_menu_callback(widget, data):
    #print data
    #print editorpersistance.prefs.active_tools
    tool_id, msg = data

    if msg == "activity":
        if widget.get_active() == False:
            editorpersistance.prefs.active_tools.remove(tool_id)
        else:
            editorpersistance.prefs.active_tools.append(tool_id)
    elif msg == "preset simplified":
        _set_workflow_SIMPLIFIED()
    elif msg == "preset standart":
        _set_workflow_STANDARD()
    elif msg == "preset filmstyle":
        _set_workflow_FILM_STYLE()
    else:
        try:
            pos = int(msg)
            current_index = editorpersistance.prefs.active_tools.index(tool_id)
            editorpersistance.prefs.active_tools.remove(tool_id)
            editorpersistance.prefs.active_tools.insert(pos - 1, tool_id)
        except:
            pass


# ------------------------------------------------------------- keyboard shortcuts
def tline_tool_keyboard_selected(event):
  
    try:
        keyboard_number = int(Gdk.keyval_name(event.keyval).lower())
        tool_id = editorpersistance.prefs.active_tools[keyboard_number - 1]
        gui.editor_window.change_tool(tool_id)
        return True
    except:
        # This fails if not a valid number was pressed, so probably most times.
        pass
        
    return False
