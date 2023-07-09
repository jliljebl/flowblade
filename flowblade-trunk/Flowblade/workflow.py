"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

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

"""
Modeule handles displaying tool menu, tool keyboard shortuts and workflow configuration activating and moving tools,
and setting relevant timeline behaviours.

"""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

import appconsts
import dialogs
import dialogutils
import editorlayout
import editorpersistance
import editorstate
import gui
import guiutils
import modesetting
import projectdata
import respaths


# Initial layouts.
LAYOUT_MONITOR_CENTER = 0
LAYOUT_MEDIA_PANEL_LEFT = 1
LAYOUT_MONITOR_LEFT = 2
LAYOUT_TOP_ROW_FOUR = 3

# Default compositing modes. We have different enums here because of different presentation order.
COMPOSITING_MODE_STANDARD_FULL_TRACK = 0
COMPOSITING_MODE_TOP_DOWN_FREE_MOVE = 1
COMPOSITING_MODE_STANDARD_AUTO_FOLLOW = 2

# Colors
SELECTED_BG = Gdk.RGBA(0.1, 0.31, 0.58,1.0)
WHITE_TEXT = Gdk.RGBA(0.9, 0.9, 0.9,1.0)
DARK_TEXT = Gdk.RGBA(0.1, 0.1, 0.1,1.0)
        
# Timeline tools data
_TOOLS_DATA = None
_TOOL_TIPS = None
_PREFS_TOOL_TIPS = None

_tools_menu = Gtk.Menu()
_workflow_menu = Gtk.Menu()

# Tool items in dock if used.
dock_items = None

def init_data():
    global _TOOLS_DATA, _TOOL_TIPS, _PREFS_TOOL_TIPS
    _TOOLS_DATA = { appconsts.TLINE_TOOL_INSERT:        (_("Insert"), "insertmove_cursor.png"),
                    appconsts.TLINE_TOOL_OVERWRITE:     (_("Move"), "overwrite_cursor.png"),
                    appconsts.TLINE_TOOL_TRIM:          (_("Trim"), "oneroll_cursor.png"),
                    appconsts.TLINE_TOOL_ROLL:          (_("Roll"), "tworoll_cursor.png"),
                    appconsts.TLINE_TOOL_SLIP:          (_("Slip"), "slide_cursor.png"),
                    appconsts.TLINE_TOOL_SPACER:        (_("Spacer"), "multimove_cursor.png"),
                    appconsts.TLINE_TOOL_BOX:           (_("Box"), "overwrite_cursor_box.png"),
                    appconsts.TLINE_TOOL_RIPPLE_TRIM:   (_("Ripple Trim"), "oneroll_cursor_ripple.png"),
                    appconsts.TLINE_TOOL_CUT:           (_("Cut"), "cut_cursor.png"),
                    appconsts.TLINE_TOOL_KFTOOL:        (_("Keyframe"), "kftool_cursor.png"),
                    appconsts.TLINE_TOOL_MULTI_TRIM:    (_("Multitrim"), "multitrim_cursor.png")
                  }
                  
    _TOOL_TIPS =  { appconsts.TLINE_TOOL_INSERT:        _("<b>Left Mouse</b> to move and insert single clip between clips.\n<b>CTRL + Left Mouse</b> to select and move clip range.\n\n<b>Left Mouse</b> on clip ends to trim clip length."),
                    appconsts.TLINE_TOOL_OVERWRITE:     _("<b>Left Mouse</b> to select a clip, or to move clip or clip range into new position.\n<b>CTRL + Left Mouse</b> to select a clip range.\n\n<b>Left Mouse</b> near clip's end to trim clip length.<b>\n\nLeft Mouse Drag</b> to draw a box to select a group of clips. Multitrack selection disallows moving clips to another track."),
                    appconsts.TLINE_TOOL_TRIM:          _("<b>Left Mouse</b> to trim closest clip end.\n<b>Left or Right Arrow Key</b> + <b>Enter Key</b> to do the edit using keyboard."), 
                    appconsts.TLINE_TOOL_ROLL:          _("<b>Left Mouse</b> to move closest edit point between 2 clips.\n<b>Left or Right Arrow Key</b> + <b>Enter Key</b> to do the edit using keyboard."), 
                    appconsts.TLINE_TOOL_SLIP:          _("<b>Left Mouse</b> to move clip contents within clip.\n<b>Left or Right Arrow Key</b> + <b>Enter Key</b> to do the edit using keyboard."), 
                    appconsts.TLINE_TOOL_SPACER:        _("<b>Left Mouse</b> to move clip under cursor and all clips after it forward or backward, overwrites not allowed.\n<b>CTRL + Left Mouse</b> to move clip under cursor and all clips after it <b>on the same track</b> forward or backward, overwrites not allowed."), 
                    appconsts.TLINE_TOOL_BOX:           _("<b>1. Left Mouse</b> to draw a box to select a group of clips.\n<b>2. Left Mouse</b> inside the box to move selected clips forward or backward."), 
                    appconsts.TLINE_TOOL_RIPPLE_TRIM:   _("<b>Left Mouse</b> to trim closest clip end and move all clips after it to maintain sync, overwrites not allowed.\n<b>Left or Right Arrow Key</b> + <b>Enter Key</b> to do the edit using keyboard."), 
                    appconsts.TLINE_TOOL_CUT:           _("<b>Left Mouse</b> to cut clip under cursor.\n<b>CTRL + Left Mouse</b> to cut clips on all tracks at cursor position."), 
                    appconsts.TLINE_TOOL_KFTOOL:        _("Click <b>Left Mouse</b> on Clip to init Volume Keyframe editing, Brightness for media with no audio data.\nUse Hamburger menu to select other values to edit.\n<b>Left Mouse</b> to create or drag keyframes.\n<b>Left Mouse + Control</b> between keyframes drag and set same value for both.\n<b>Delete Key</b> to delete active Keyframe."),
                    appconsts.TLINE_TOOL_MULTI_TRIM:    _("Position cursor near or on clip edges for <b>Trim</b> and <b>Roll</b> edits.\nPosition cursor on clip center for <b>Slip</b> edit.\nDrag with <b>Left Mouse</b> to do edits.\n\n<b>Enter Key</b> to start keyboard edit, <b>Left or Right Arrow Key</b> to move edit point.\n<b>Enter Key</b> to complete keyboard edit.")
                  }


#----------------------------------------------------- workflow presets
def _set_workflow_STANDARD():
    editorpersistance.prefs.active_tools = [2, 11, 6, 1, 9, 10] # appconsts.TLINE_TOOL_ID_<X> values
    editorpersistance.prefs.dnd_action = appconsts.DND_OVERWRITE_NON_V1
    editorpersistance.save()

    modesetting.set_default_edit_mode()

# --------------------------------------------------------------- interface
def get_tline_tool_working_set():
    tools = []
    
    kb_shortcut_number = 1
    for tool_id in editorpersistance.prefs.active_tools:
        tool_name, tool_icon_file = _TOOLS_DATA[tool_id]
        tools.append((tool_name, kb_shortcut_number))

        kb_shortcut_number = kb_shortcut_number + 1

    return tools
    
# --------------------------------------------------------------- tools menu
def get_tline_tool_popup_menu(event, callback):
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
    # needed to make number 1-9 work elsewhere in the application
    for menu_item in menu_items:
        menu_item.set_accel_path(None)

def _get_image_menu_item(tool_icon_file, text, callback, tool_id):
    item = Gtk.ImageMenuItem()
    tool_img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + tool_icon_file)
        
    item.set_image(tool_img)
    item.connect("activate", callback, tool_id)
    item.set_always_show_image(True)
    item.set_use_stock(False)
    item.set_label(text)
    if editorpersistance.prefs.show_tool_tooltips:
        item.set_tooltip_markup(_get_tooltip_text(tool_id))
    item.show()
    return item
    
# ---------------------------------------------------- workflow menu
def workflow_menu_launched(widget, event):
    guiutils.remove_children(_workflow_menu)

    standard = guiutils.get_menu_item(_("Reset Tools"), _workflow_menu_callback, (None, "preset standard"))
    standard.show()
    _workflow_menu.add(standard)

    show_tooltips_item = Gtk.CheckMenuItem()
    show_tooltips_item.set_label(_("Show Tooltips for Edit Tools"))
    show_tooltips_item.set_active(editorpersistance.prefs.show_tool_tooltips)
    show_tooltips_item.connect("activate", _workflow_menu_callback, (None, "tooltips"))
    show_tooltips_item.show()
    _workflow_menu.append(show_tooltips_item)

    # --- tools
    guiutils.add_separetor(_workflow_menu)
    
    # Active tools
    non_active_tools = list(range(1, 12)) # we have 11 tools currently
    for i in range(0, len(editorpersistance.prefs.active_tools)):#  tool_id in _TOOLS_DATA:
        tool_id = editorpersistance.prefs.active_tools[i]
        tool_name, tool_icon_file = _TOOLS_DATA[tool_id]
        _workflow_menu.add(_get_workflow_tool_menu_item(_workflow_menu_callback, tool_id, tool_name, tool_icon_file, i+1))
        try: # needed to prevent crashes when manually changing preset tools during development.
            non_active_tools.remove(tool_id)
        except:
            pass

    guiutils.add_separetor(_workflow_menu)
    
    # Non-active tools
    for tool_id in non_active_tools:
        tool_name, tool_icon_file = _TOOLS_DATA[tool_id]
        _workflow_menu.add(_get_workflow_tool_menu_item(_workflow_menu_callback, tool_id, tool_name, tool_icon_file, -1))
        
    _workflow_menu.popup(None, None, None, None, event.button, event.time)

def _get_workflow_tool_menu_item(callback, tool_id, tool_name, tool_icon_file, position):

    tool_img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + tool_icon_file)
    tool_name_label = Gtk.Label(tool_name)
    
    hbox = Gtk.HBox()
    hbox.pack_start(guiutils.pad_label(4, 4), False, False, 0)
    hbox.pack_start(tool_img, False, False, 0)
    hbox.pack_start(guiutils.pad_label(4, 4), False, False, 0)
    hbox.pack_start(tool_name_label, False, False, 0)
    hbox.show_all()
    item = Gtk.MenuItem()
    item.add(hbox)
    if editorpersistance.prefs.show_tool_tooltips:
        item.set_tooltip_markup(_get_tooltip_text(tool_id))
    item.show()
    
    item.set_submenu(_get_workflow_tool_submenu(callback, tool_id, position))

    return item

def _build_radio_menu_items_group(menu, labels, msgs, callback, active_index):
    first_item = Gtk.RadioMenuItem()
    first_item.set_label(labels[0])
    first_item.show()
    menu.append(first_item)
    if active_index == 0:
        first_item.set_active(True)
    first_item.connect("activate", callback, (None,msgs[0]))
    
    for i in range(1, len(labels)):
        radio_item = Gtk.RadioMenuItem.new_with_label([first_item], labels[i])
        menu.append(radio_item)
        radio_item.show()
        if active_index == i:
            radio_item.set_active(True)
        
        radio_item.connect("activate", callback, (None, msgs[i]))

def _get_tooltip_text(tool_id):
    text = _TOOL_TIPS[tool_id]

    return text

def _get_workflow_tool_submenu(callback, tool_id, position):
    sub_menu = Gtk.Menu()
    
    tool_active = (tool_id in editorpersistance.prefs.active_tools)
    activity_item = Gtk.CheckMenuItem(_("Edit Tool Active"))
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
    tool_id, msg = data
    
    if msg == "activity":
        if widget.get_active() == False:
            editorpersistance.prefs.active_tools.remove(tool_id)
        else:
            editorpersistance.prefs.active_tools.append(tool_id)
        update_tool_dock()
    elif msg == "preset standard":
        _set_workflow_STANDARD()
    elif  msg == "always overwrite":
        editorpersistance.prefs.dnd_action = appconsts.DND_ALWAYS_OVERWRITE
    elif  msg == "overwrite nonV1":
        editorpersistance.prefs.dnd_action = appconsts.DND_OVERWRITE_NON_V1
    elif  msg == "always insert":
        editorpersistance.prefs.dnd_action = appconsts.DND_ALWAYS_INSERT
    elif  msg == "tooltips":
        editorpersistance.prefs.show_tool_tooltips = widget.get_active()
    else:
        try: # Set tool position
            pos = int(msg)
            current_index = editorpersistance.prefs.active_tools.index(tool_id)
            editorpersistance.prefs.active_tools.remove(tool_id)
            editorpersistance.prefs.active_tools.insert(pos - 1, tool_id)
            update_tool_dock()
        except:
            pass
    
    editorpersistance.save()

# ---------------------------------------------------- tools dock
def get_tline_tool_dock():
    dock = Gtk.VBox()
    global dock_items
    dock_items = []
    kb_shortcut_number = 1
    for tool_id in editorpersistance.prefs.active_tools:
        tool_name, tool_icon_file = _TOOLS_DATA[tool_id]

        dock_item = _get_tool_dock_item(kb_shortcut_number, tool_icon_file, tool_name, tool_id)
        dock.pack_start(dock_item.widget, False, False, 0)
        dock_items.append(dock_item)
        if kb_shortcut_number == 1:
            dock_item.set_item_color(True)
        kb_shortcut_number = kb_shortcut_number + 1

    dock.pack_start(Gtk.Label(), True, True, 0)

    align = guiutils.set_margins(dock, 10, 0, 0, 0)

    frame = Gtk.Frame()
    frame.add(align)
    frame.set_shadow_type(Gtk.ShadowType.ETCHED_OUT)
    guiutils.set_margins(frame, 0, 0, 1, 0)
    return frame

def update_tool_dock():
    if editorpersistance.prefs.tools_selection == appconsts.TOOL_SELECTOR_IS_LEFT_DOCK:
        gui.editor_window.update_tool_dock()

def _get_tool_dock_item(kb_shortcut_number, tool_icon_file, tool_name, tool_id):
    dock_item = ToolDockItem(kb_shortcut_number, tool_icon_file, tool_name, tool_id)
    return dock_item

def _tool_dock_item_press(tool_id, tool_dock_item):
    for item in dock_items:
        item.set_item_color(False)
    tool_dock_item.set_item_color(True)
    gui.editor_window.tline_cursor_manager.tool_selector_item_activated(None, tool_id)

def set_default_tool_dock_item_selected():
    for item in dock_items:
        item.set_item_color(False)
    dock_items[0].set_item_color(True)



class ToolDockItem:
    def __init__(self, kb_shortcut_number, tool_icon_file, tool_name, tool_id):
        tool_img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + tool_icon_file)
        guiutils.set_margins(tool_img, 5, 5, 9, 7)

        self.widget = Gtk.EventBox()
        self.widget.connect("button-press-event", lambda w,e: _tool_dock_item_press(tool_id, self))

        self.widget.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        if editorpersistance.prefs.show_tool_tooltips:
            self.widget.set_tooltip_markup("<b>" + tool_name + " - " + _("Keyboard shortcut: ") + str(kb_shortcut_number) + "</b>" "\n\n" + _get_tooltip_text(tool_id))
        
        self.widget.add(tool_img)

    def set_item_color(self, selected):
        if selected == True:
            self.widget.override_background_color(Gtk.StateType.NORMAL, SELECTED_BG)
        else:
            self.widget.override_background_color(Gtk.StateType.NORMAL, gui.get_bg_color())


# ------------------------------------------------------------- keyboard shortcuts
def tline_tool_keyboard_selected(event):
  
    try:
        keyboard_number = int(Gdk.keyval_name(event.keyval).lower())
        tool_id = editorpersistance.prefs.active_tools[keyboard_number - 1]
        gui.editor_window.tline_cursor_manager.change_tool(tool_id)
        for item in dock_items:
            item.set_item_color(False)
        dock_items[keyboard_number - 1].set_item_color(True)
        return True
    except:
        # This fails if a valid number was not pressed, so probably most times.
        pass
        
    return False

def select_default_tool():
    tool_id = editorpersistance.prefs.active_tools[0]
    gui.editor_window.tline_cursor_manager.change_tool(tool_id)
