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
from gi.repository import GObject

import appconsts
import dialogs
import dialogutils
import edit
import editorlayout
import editorpersistance
import editorstate
from editorstate import PROJECT
import gui
import guiutils
import modesetting
import projectdata
import respaths
import updater

# New version start-up toolset selections.
STANDARD_PRESET = 0
FILM_STYLE_PRESET = 1
KEEP_EXISTING = 2

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
                    appconsts.TLINE_TOOL_OVERWRITE:     _("<b>Left Mouse</b> to move clip into new position.\n<b>CTRL + Left Mouse</b> to select and move clip range into new position.\n\n<b>Left Mouse</b> on clip ends to trim clip length."),
                    appconsts.TLINE_TOOL_TRIM:          _("<b>Left Mouse</b> to trim closest clip end.\n<b>Left or Right Arrow Key</b> + <b>Enter Key</b> to do the edit using keyboard."), 
                    appconsts.TLINE_TOOL_ROLL:          _("<b>Left Mouse</b> to move closest edit point between 2 clips.\n<b>Left or Right Arrow Key</b> + <b>Enter Key</b> to do the edit using keyboard."), 
                    appconsts.TLINE_TOOL_SLIP:          _("<b>Left Mouse</b> to move clip contents within clip.\n<b>Left or Right Arrow Key</b> + <b>Enter Key</b> to do the edit using keyboard."), 
                    appconsts.TLINE_TOOL_SPACER:        _("<b>Left Mouse</b> to move clip under cursor and all clips after it forward or backward, overwrites not allowed.\n<b>CTRL + Left Mouse</b> to move clip under cursor and all clips after it <b>on the same track</b> forward or backward, overwrites not allowed."), 
                    appconsts.TLINE_TOOL_BOX:           _("<b>1. Left Mouse</b> to draw a box to select a group of clips.\n<b>2. Left Mouse</b> inside the box to move selected clips forward or backward."), 
                    appconsts.TLINE_TOOL_RIPPLE_TRIM:   _("<b>Left Mouse</b> to trim closest clip end and move all clips after it to maintain sync, overwrites not allowed.\n<b>Left or Right Arrow Key</b> + <b>Enter Key</b> to do the edit using keyboard."), 
                    appconsts.TLINE_TOOL_CUT:           _("<b>Left Mouse</b> to cut clip under cursor.\n<b>CTRL + Left Mouse</b> to cut clips on all tracks at cursor position."), 
                    appconsts.TLINE_TOOL_KFTOOL:        _("Click <b>Left Mouse</b> on Clip to init Volume Keyframe editing, Brightness for media with no audio data.\n<b>Left Mouse</b> to create or drag keyframes.\n<b>Delete Key</b> to delete active Keyframe."),
                    appconsts.TLINE_TOOL_MULTI_TRIM:    _("Position cursor near or on clip edges for <b>Trim</b> and <b>Roll</b> edits.\nPosition cursor on clip center for <b>Slip</b> edit.\nDrag with <b>Left Mouse</b> to do edits.\n\n<b>Enter Key</b> to start keyboard edit, <b>Left or Right Arrow Key</b> to move edit point.\n<b>Enter Key</b> to complete keyboard edit.")
                  }

    _PREFS_TOOL_TIPS = {"editorpersistance.prefs.box_for_empty_press_in_overwrite_tool":       _("<b>\n\nLeft Mouse Drag</b> to draw a box to select a group of clips and move\nthe selected clips forward or backward.")}
    


#----------------------------------------------------- WorkflowDialog calls this to get default comp mode shown.
def _load_default_project(open_project_callback):
     project = projectdata.get_default_project()
     open_project_callback(project)

#----------------------------------------------------- workflow presets
def _set_workflow_STANDARD():
    editorpersistance.prefs.active_tools = [2, 11, 6, 1, 9, 10] # appconsts.TLINE_TOOL_ID_<X> values
    editorpersistance.prefs.dnd_action = appconsts.DND_ALWAYS_OVERWRITE
    editorpersistance.prefs.box_for_empty_press_in_overwrite_tool = True
    editorpersistance.save()

    modesetting.set_default_edit_mode()

def _set_workflow_FILM_STYLE():
    editorpersistance.prefs.active_tools = [1, 2, 3, 4, 5, 6, 7]  # appconsts.TLINE_TOOL_ID_<X> values
    editorpersistance.prefs.dnd_action = appconsts.DND_OVERWRITE_NON_V1
    editorpersistance.prefs.box_for_empty_press_in_overwrite_tool = False
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

    # ---- preset
    presets_item = Gtk.MenuItem.new_with_label(_("Workflow Presets"))
    presets_item.show()

    presets_menu = Gtk.Menu()
    
    standard = guiutils.get_menu_item(_("Standard"), _workflow_menu_callback, (None, "preset standard"))
    standard.show()
    presets_menu.add(standard)

    film_style = guiutils.get_menu_item(_("Film Style"), _workflow_menu_callback, (None, "preset filmstyle"))
    film_style.show()
    presets_menu.add(film_style)
    
    presets_item.set_submenu(presets_menu)
    _workflow_menu.add(presets_item)

    # --- behaviours
    guiutils.add_separetor(_workflow_menu)

    behaviours_item = Gtk.MenuItem.new_with_label(_("Behaviours"))
    behaviours_item.show()

    behaviours_menu = Gtk.Menu()

    dnd_item = Gtk.MenuItem.new_with_label(_("Drag'n'Drop Action"))
    dnd_item.show()

    dnd_menu = Gtk.Menu()
    labels = [_("Always Overwrite Blanks"), _("Overwrite Blanks on non-V1 Tracks"), _("Always Insert")]
    msgs = ["always overwrite", "overwrite nonV1", "always insert"]
    active_index = editorpersistance.prefs.dnd_action  # appconsts values correspond with order here.
    _build_radio_menu_items_group(dnd_menu, labels, msgs, _workflow_menu_callback, active_index)

    dnd_item.set_submenu(dnd_menu)
    behaviours_menu.add(dnd_item)

    default_compositing_item = Gtk.MenuItem.new_with_label(_("New Sequence Default Compositing Mode"))
    default_compositing_item.show()
    
    default_compositing_menu = Gtk.Menu()
    labels = [_("Top Down Free Move"), _("Top Down Auto Follow"), _("Standard Full Track")]
    msgs = ["top down", "standard auto", "standard full"]
    # Indexes do NOT match appconsts values.
    if editorpersistance.prefs.default_compositing_mode == appconsts.COMPOSITING_MODE_TOP_DOWN_FREE_MOVE:
        active_index = 0
    elif editorpersistance.prefs.default_compositing_mode == appconsts.COMPOSITING_MODE_STANDARD_AUTO_FOLLOW:
        active_index = 1
    else:
        active_index = 2
    _build_radio_menu_items_group(default_compositing_menu, labels, msgs, _workflow_menu_callback, active_index)

    default_compositing_item.set_submenu(default_compositing_menu)
    behaviours_menu.add(default_compositing_item)
    
    show_tooltips_item = Gtk.CheckMenuItem()
    show_tooltips_item.set_label(_("Show Tooltips for Edit Tools"))
    show_tooltips_item.set_active(editorpersistance.prefs.show_tool_tooltips)
    show_tooltips_item.connect("activate", _workflow_menu_callback, (None, "tooltips"))
    show_tooltips_item.show()

    behaviours_menu.append(show_tooltips_item)
    
    behaviours_item.set_submenu(behaviours_menu)
    _workflow_menu.add(behaviours_item)

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

    tool_active = (tool_id in editorpersistance.prefs.active_tools)

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
    
    # Add individual extensions based on current prefs
    if tool_id == appconsts.TLINE_TOOL_OVERWRITE:
        if editorpersistance.prefs.box_for_empty_press_in_overwrite_tool == True:
            text += _PREFS_TOOL_TIPS["editorpersistance.prefs.box_for_empty_press_in_overwrite_tool"]

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
    
    # Individual prefs for tools
    if tool_id == appconsts.TLINE_TOOL_OVERWRITE:
        pref_item = Gtk.CheckMenuItem(_("Do Box Selection and Box Move from empty press"))
        pref_item.set_active(editorpersistance.prefs.box_for_empty_press_in_overwrite_tool)
        pref_item.connect("toggled", _TLINE_TOOL_OVERWRITE_box_selection_pref)
        pref_item.show()
        sub_menu.add(pref_item)
        guiutils.add_separetor(sub_menu)

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
    elif msg == "preset filmstyle":
        _set_workflow_FILM_STYLE()
    elif  msg == "always overwrite":
        editorpersistance.prefs.dnd_action = appconsts.DND_ALWAYS_OVERWRITE
    elif  msg == "overwrite nonV1":
        editorpersistance.prefs.dnd_action = appconsts.DND_OVERWRITE_NON_V1
    elif  msg == "always insert":
        editorpersistance.prefs.dnd_action = appconsts.DND_ALWAYS_INSERT
    elif  msg == "tooltips":
        editorpersistance.prefs.show_tool_tooltips = widget.get_active()
    elif  msg == "top down":
        editorpersistance.prefs.default_compositing_mode = appconsts.COMPOSITING_MODE_TOP_DOWN_FREE_MOVE
    elif  msg == "standard auto":
        editorpersistance.prefs.default_compositing_mode = appconsts.COMPOSITING_MODE_STANDARD_AUTO_FOLLOW
    elif  msg == "standard full":
        editorpersistance.prefs.default_compositing_mode = appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK
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
    gui.editor_window.tool_selector_item_activated(None, tool_id)

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
            if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
                self.widget.override_color(Gtk.StateType.NORMAL, WHITE_TEXT)
        else:
            self.widget.override_background_color(Gtk.StateType.NORMAL, gui.get_bg_color())
            if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
                self.widget.override_color(Gtk.StateType.NORMAL, DARK_TEXT)


# ------------------------------------------------------------- keyboard shortcuts
def tline_tool_keyboard_selected(event):
  
    try:
        keyboard_number = int(Gdk.keyval_name(event.keyval).lower())
        tool_id = editorpersistance.prefs.active_tools[keyboard_number - 1]
        gui.editor_window.change_tool(tool_id)
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
    gui.editor_window.change_tool(tool_id)
        
# -------------------------------------------------------------- tool prefs
def _TLINE_TOOL_OVERWRITE_box_selection_pref(check_menu_item):
    editorpersistance.prefs.box_for_empty_press_in_overwrite_tool = check_menu_item.get_active()
    editorpersistance.save()



class WorkflowDialog(Gtk.Dialog):

    def __init__(self, project_open_callback):
        Gtk.Dialog.__init__(self, _("Workflow First Run Wizard"),  gui.editor_window.window,
                                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                (_("Select Presets and Continue"), Gtk.ResponseType.ACCEPT))


        self.project_open_callback = project_open_callback

        self.selection = STANDARD_PRESET
        self.comp_selection = COMPOSITING_MODE_STANDARD_FULL_TRACK 
        
        info_label_text_1 = _("<b>Welcome to Flowblade</b>")
        info_label_1 = Gtk.Label(info_label_text_1)
        info_label_1.set_use_markup(True)


        info_label_text_2 = _("<b>Flowblade</b> comes with a configurable workflow.")
        info_label_2 = Gtk.Label(info_label_text_2)
        info_label_2.set_use_markup(True)

        INDENT = "    "
        info_label_text_6 = INDENT + "\u2022" + _(" You can select which <b>Edit Tools</b> you want to use.\n") + \
                            INDENT + "\u2022" + _(" Many timeline edit <b>behaviours</b> are configurable.\n")

        info_label_6 = Gtk.Label(info_label_text_6)
        info_label_6.set_use_markup(True)

        info_label_text_3 = _("<b>Select Workflow Preset</b>")
        info_label_3 = Gtk.Label(info_label_text_3)
        info_label_3.set_use_markup(True)
        guiutils.set_margins(info_label_3, 0, 4, 0, 0)
            
        info_label_text_7 = _("You can change and configure individual tools and behaviours <b>anytime</b>")
        info_label_7 = Gtk.Label(info_label_text_7)
        info_label_7.set_use_markup(True)
        
        info_label_text_4 = _(" by pressing ")
        info_label_4 = Gtk.Label(info_label_text_4)
        info_label_4.set_use_markup(True)
        
        icon = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "workflow.png")
    
        info_label_text_5 = _(" icon.")
        info_label_5 = Gtk.Label(info_label_text_5)
        
        # Workflow selection 
        workflow_name = _("<b>Standard</b>")
        stadard_preset_workflow_text_1 = _("Standard workflow has the <b>Move</b> tool as default tool\nand presents a workflow similar to most video editors.")
        workflow_select_item_1 = self.get_select_item(STANDARD_PRESET, workflow_name, stadard_preset_workflow_text_1, self.selected_callback, self.selection )

        workflow_name = _("<b>Film Style</b>")
        filmstyle_preset_workflow_text_2 = _("Film Style workflow has the <b>Insert</b> tool as default tool.\nThis was the workflow in earlier versions of the application.")
        workflow_select_item_2 = self.get_select_item(FILM_STYLE_PRESET, workflow_name, filmstyle_preset_workflow_text_2, self.selected_callback, self.selection)

        workflow_name = _("<b>Keep Existing Workflow</b>")
        keep_workflow_text_2 = _("Select this if you have installed new version and wish to keep your existing workflow.")
        workflow_select_item_3 = self.get_select_item(KEEP_EXISTING, workflow_name, keep_workflow_text_2, self.selected_callback, self.selection)
        
        self.workflow_items = [workflow_select_item_1, workflow_select_item_2, workflow_select_item_3]
        framed_items_box = self.get_selection_box(self.workflow_items)

        workflow_vbox = Gtk.VBox(False, 2)
        workflow_vbox.pack_start(guiutils.get_centered_box([info_label_3]), False, False, 0)
        workflow_vbox.pack_start(framed_items_box, False, False, 0)
        workflow_vbox.pack_start(guiutils.get_pad_label(24, 12), False, False, 0)
        workflow_vbox.pack_start(guiutils.get_left_justified_box([info_label_2]), False, False, 0)
        workflow_vbox.pack_start(guiutils.get_left_justified_box([info_label_6]), False, False, 0)
        workflow_vbox.pack_start(guiutils.get_left_justified_box([info_label_7]), False, False, 0)
        workflow_vbox.pack_start(guiutils.get_left_justified_box([info_label_4, icon, info_label_5]), False, False, 0)
        workflow_vbox.pack_start(Gtk.Label(), True, True, 0)
    
        # Compositing default selection 
        comp_name = _("<b>Standard Full Track</b>")
        comp_text = _("The most simple and easiest to use <b>Compositing Mode</b>. No <b>Compositors</b> are used.\nFades, wipes and transforms are created with <b>Filters</b>.")
        comp_select_item_1 = self.get_select_item(0, comp_name, comp_text, self.comp_selection_callback, self.comp_selection)

        comp_name = _("<b>Top Down Free Move</b>")
        comp_text = _("The most powerful and complex <b>Compositing Mode</b>. Any number of <b>Compositors</b>\ncan be added and their destination <b>Tracks</b> and positions can be set freely.")
        comp_select_item_2 = self.get_select_item(1, comp_name, comp_text, self.comp_selection_callback, self.comp_selection)

        comp_name = _("<b>Standard Auto Follow</b>")
        comp_text = _("<b>Compositors</b> follow their origin clips automatically and users can only\nadd one compositor per clip. All <b>Compositors</b> have <b>Track V1</b> as their destination track.")
        comp_select_item_3 = self.get_select_item(2, comp_name, comp_text, self.comp_selection_callback, self.comp_selection)
        
        self.comp_items = [comp_select_item_1, comp_select_item_2, comp_select_item_3]
        comp_items_box = self.get_selection_box(self.comp_items)

        text = _("<b>Select Default Compositing Mode</b>")
        comp_info_label_1 = Gtk.Label(text)
        comp_info_label_1.set_use_markup(True)
        guiutils.set_margins(comp_info_label_1, 0, 4, 0, 0)

        text = _("You can change default <b>Compositing Mode</b> later by pressing ")
        comp_info_label_2 = Gtk.Label(text)
        comp_info_label_2.set_use_markup(True)

        text = _(" by pressing ")
        comp_info_label_3 = Gtk.Label(text)
        comp_info_label_3.set_use_markup(True)
        
        icon = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "workflow.png")
    
        text = _(" icon.")
        comp_info_label_4 = Gtk.Label(text)

        text = _("You can change <b>Compositing Mode</b> for current <b>Sequence</b> using\nmenu <b>Sequence -> Compositing Mode</b>.")
        comp_info_label_5 = Gtk.Label(text)
        comp_info_label_5.set_use_markup(True)
        guiutils.set_margins(comp_info_label_5, 4, 0, 0, 0)
        
        comp_vbox = Gtk.VBox(False, 2)
        comp_vbox.pack_start(guiutils.get_centered_box([comp_info_label_1]), False, False, 0)
        comp_vbox.pack_start(comp_items_box, False, False, 0)
        comp_vbox.pack_start(guiutils.get_pad_label(24, 12), False, False, 0)
        comp_vbox.pack_start(guiutils.get_left_justified_box([comp_info_label_2, icon, comp_info_label_4]), False, False, 0)
        comp_vbox.pack_start(guiutils.get_left_justified_box([comp_info_label_5]), False, False, 0)
        
        # Initial layout
        text = _("<b>Select Initial Layout</b>")
        layout_info_label_1 = Gtk.Label(text)
        layout_info_label_1.set_use_markup(True)
        guiutils.set_margins(layout_info_label_1, 48, 4, 0, 0)
        
        # indexes correspond with enums LAYOUT_MONITOR_CENTER etc.
        self.layout_combo_box = Gtk.ComboBoxText()
        self.layout_combo_box.append_text(_("Layout Monitor Center"))
        self.layout_combo_box.append_text(_("Layout Media Panel Left Column"))
        self.layout_combo_box.append_text(_("Layout Monitor Left"))
        if editorstate.SCREEN_WIDTH > 1900:
            self.layout_combo_box.append_text(_("Layout Top Row 4 Panels"))
        self.layout_combo_box.set_active(LAYOUT_MONITOR_CENTER)

        text = _("You can change layout using menu <b>View -> Panel Placement</b>.")
        layout_info_label_2 = Gtk.Label(text)
        layout_info_label_2.set_use_markup(True)
        guiutils.set_margins(layout_info_label_2, 24, 0, 0, 0)
        
        layout_vbox = Gtk.VBox(False, 2)
        layout_vbox.pack_start(layout_info_label_1, False, False, 0)
        layout_vbox.pack_start(self.layout_combo_box, False, False, 0)
        layout_vbox.pack_start(guiutils.get_left_justified_box([layout_info_label_2]), False, False, 0)
        
        # Build dialog
        presets_vbox = Gtk.VBox(False, 2)
        presets_vbox.pack_start(comp_vbox, False, False, 0)
        if editorstate.SCREEN_WIDTH > 1619:
            presets_vbox.pack_start(layout_vbox, False, False, 0)

        selections_hbox = Gtk.HBox(True, 8)
        selections_hbox.pack_start(workflow_vbox, True, True, 0)
        selections_hbox.pack_start(presets_vbox, True, True, 0)
        
        panel_vbox = Gtk.VBox(False, 2)
        panel_vbox.pack_start(guiutils.get_pad_label(24, 12), False, False, 0)
        panel_vbox.pack_start(guiutils.get_centered_box([info_label_1]), False, False, 0)
        panel_vbox.pack_start(guiutils.get_pad_label(24, 12), False, False, 0)
        panel_vbox.pack_start(selections_hbox, False, False, 0)

        panel_vbox.pack_start(guiutils.get_pad_label(24, 24), False, False, 0)

        alignment = dialogutils.get_alignment2(panel_vbox)

        self.vbox.pack_start(alignment, True, True, 0)
        dialogutils.set_outer_margins(self.vbox)
        dialogs._default_behaviour(self)
        self.connect('response', self.done)
        self.show_all()

    def get_select_item(self, item_number, item_name, item_text, callback, initial_selection):
        name = Gtk.Label(item_name)
        name.set_use_markup(True)
        guiutils.set_margins(name, 0, 8, 0, 0)
        label = Gtk.Label(item_text)
        label.set_use_markup(True)
        label.set_justify(Gtk.Justification.CENTER)

        item_vbox = Gtk.VBox(False, 2)
        item_vbox.pack_start(guiutils.get_centered_box([name]), False, False, 0)
        item_vbox.pack_start(guiutils.get_centered_box([label]), False, False, 0)
        guiutils.set_margins(item_vbox, 12, 18, 12, 12)
     
        widget = Gtk.EventBox()
        widget.connect("button-press-event", lambda w,e: callback(w, item_number)) #self.selected_callback(w, item_number))
        widget.set_can_focus(True)
        widget.add_events(Gdk.EventMask.KEY_PRESS_MASK)

        widget.add(item_vbox)
        
        widget.item_number = item_number
                
        self.set_item_color(widget, initial_selection)

        return widget

    def set_item_color(self, widget, selection_index):
        if widget.item_number == selection_index:
            widget.override_background_color(Gtk.StateType.NORMAL, SELECTED_BG)
            if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
                widget.override_color(Gtk.StateType.NORMAL, WHITE_TEXT)
        else:
            widget.override_background_color(Gtk.StateType.NORMAL, gui.get_bg_color())
            if editorpersistance.prefs.theme == appconsts.LIGHT_THEME:
                widget.override_color(Gtk.StateType.NORMAL, DARK_TEXT)

    def done(self, dialog, response_id):
        # Workflow
        if self.selection == STANDARD_PRESET:
            _set_workflow_STANDARD()
        elif self.selection == FILM_STYLE_PRESET:
            _set_workflow_FILM_STYLE()

        # Layout
        if editorstate.SCREEN_WIDTH > 1619:
            layout_selection = self.layout_combo_box.get_active()
            if layout_selection == LAYOUT_MONITOR_CENTER:
                editorlayout.apply_layout(editorlayout.MONITOR_CENTER_PANEL_POSITIONS)
            elif layout_selection == LAYOUT_MEDIA_PANEL_LEFT:
                editorlayout.apply_layout(editorlayout.MEDIA_PANEL_LEFT_POSITIONS)
            elif layout_selection == LAYOUT_MONITOR_LEFT:
                editorlayout.apply_layout(editorlayout.DEFAULT_PANEL_POSITIONS)
            else:
                # LAYOUT_TOP_ROW_FOUR
                editorlayout.apply_layout(editorlayout.TOP_ROW_FOUR_POSITIONS)

        # Default comp mode
        if self.comp_selection == COMPOSITING_MODE_STANDARD_FULL_TRACK:
            editorpersistance.prefs.default_compositing_mode = appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK
        elif self.comp_selection == COMPOSITING_MODE_TOP_DOWN_FREE_MOVE:
            editorpersistance.prefs.default_compositing_mode = appconsts.COMPOSITING_MODE_TOP_DOWN_FREE_MOVE
        else:
            editorpersistance.prefs.default_compositing_mode = appconsts.COMPOSITING_MODE_STANDARD_AUTO_FOLLOW

        dialog.destroy()

        editorpersistance.save()
        
        GObject.timeout_add(500, _load_default_project, self.project_open_callback)  
        
    
    def selected_callback(self, w, item_number):
        self.selection = item_number

        for widget in self.workflow_items:
            self.set_item_color(widget, self.selection)

    def comp_selection_callback(self, w, item_number):
        self.comp_selection = item_number

        for widget in self.comp_items:
            self.set_item_color(widget, self.comp_selection)
            
    def get_selection_box(self, selection_items):
        items_vbox = Gtk.VBox(False, 0)
        for item in selection_items:
            box_item =  guiutils.get_panel_etched_frame(item)
            guiutils.set_margins(box_item, 0, 0, 0, 0)
            items_vbox.pack_start(box_item, False, False, 0)

        framed_items_box = guiutils.get_panel_etched_frame(items_vbox)
        guiutils.set_margins(framed_items_box, 0, 0, 0, 0)
        
        return framed_items_box
