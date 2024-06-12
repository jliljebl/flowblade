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
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

from gi.repository import Gtk

import editorpersistance
import editorstate
import dialogutils
import guicomponents
import guiutils
import shortcuts
import shortcutsquickeffects


def keyboard_shortcuts_dialog(parent_window, get_tool_list_func, change_presets_callback, change_shortcut_callback, _kb_menu_callback):
    
    global kb_shortcut_changed_callback, kb_shortcut_dialog, shortcuts_combo
    kb_shortcut_changed_callback = change_shortcut_callback
    
    dialog = Gtk.Dialog(_("Keyboard Shortcuts"),
                        parent_window,
                        Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Close"), Gtk.ResponseType.ACCEPT))
    kb_shortcut_dialog = dialog
    
    presets_label = guiutils.bold_label(_("Active Shortcuts Group:"))
    shortcuts_combo = guicomponents.get_shorcuts_selector()

    button_data = (shortcuts_combo, dialog)
    
    add_button = Gtk.Button(label=_("Add Custom Shortcuts Group"))
    add_button.connect("clicked", _kb_menu_callback, ("add", button_data))
    add_button.set_margin_top(8)
    delete_button = Gtk.Button(label=_("Delete Active Custom Shortcuts Group"))
    delete_button.connect("clicked", _kb_menu_callback, ("delete", button_data))

    hbox = Gtk.HBox()
    hbox.pack_start(presets_label, False, True, 0)
    hbox.pack_start(guiutils.pad_label(4, 4), False, False, 0)
    hbox.pack_start(shortcuts_combo, True, True, 0)
    
    global scroll_hold_panel
    scroll_hold_panel = Gtk.HBox()
    
    content_panel = Gtk.VBox(False, 2)
    content_panel.pack_start(hbox, False, False, 0)
    content_panel.pack_start(add_button, False, False, 0)
    content_panel.pack_start(delete_button, False, False, 0)
    content_panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    content_panel.pack_start(scroll_hold_panel, True, True, 0)
    content_panel.pack_start(guiutils.pad_label(12,12), False, False, 0)

    scroll_window = display_keyboard_shortcuts(editorpersistance.prefs.shortcuts, get_tool_list_func(), scroll_hold_panel)

    guicomponents.KBShortcutEditor.edit_ongoing = False
        
    changed_id = shortcuts_combo.connect('changed', lambda w:_shorcuts_selection_changed(w, scroll_hold_panel, dialog))
    shortcuts_combo.changed_id = changed_id
    
    guiutils.set_margins(content_panel, 12, 12, 12, 12)
    
    dialog.vbox.pack_start(content_panel, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_resizable(False)
    dialog.connect('response', change_presets_callback, shortcuts_combo)
    dialog.show_all()
 
def _shorcuts_selection_changed(combo, scroll_hold_panel, dialog):
    selected_xml = shortcuts.shortcut_files[combo.get_active()]
    
    editorpersistance.prefs.shortcuts = selected_xml
    editorpersistance.save()
    shortcuts.set_keyboard_shortcuts()
    
    display_keyboard_shortcuts(selected_xml, workflow.get_tline_tool_working_set(), scroll_hold_panel)

    dialog.show_all()

def display_keyboard_shortcuts(xml_file, tool_set, scroll_hold_panel):
    widgets = scroll_hold_panel.get_children()
    if len(widgets) != 0:
        scroll_hold_panel.remove(widgets[0])

    shorcuts_panel = _get_dynamic_kb_shortcuts_panel(xml_file, tool_set)

    pad_panel = Gtk.HBox()
    pad_panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    pad_panel.pack_start(shorcuts_panel, True, False, 0)
    pad_panel.pack_start(guiutils.pad_label(12,12), False, False, 0)

    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    sw.add(pad_panel)
    if editorstate.screen_size_small_height() == True:
        sw.set_size_request(420, 450)
    else:
        sw.set_size_request(420, 550)
    
    scroll_hold_panel.pack_start(sw, False, False, 0)
    scroll_hold_panel.show_all()
    return sw

def _get_dynamic_kb_shortcuts_panel(xml_file, tool_set):   
    root_node = shortcuts.get_shortcuts_xml_root_node(xml_file)
    
    general_vbox = Gtk.VBox()
    general_vbox.pack_start(_get_kb_row(_("Control + N"), _("Create New Project")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + S"), _("Save Project")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("DELETE"), _("Delete Selected Item")), False, False, 0) # _get_dynamic_kb_row(root_node, "delete"), False, False, 0)
    general_vbox.pack_start(_get_dynamic_kb_row(root_node, "move_media"), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("ESCAPE"), _("Stop Rendering Audio Levels")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + Q"), _("Quit")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + Z"), _("Undo")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + Y"), _("Redo")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("Control + O"), _("Open Project")), False, False, 0)
    general_vbox.pack_start(_get_kb_row(_("TAB"), _("Switch Monitor Source")), False, False, 0) #_get_dynamic_kb_row(root_node, "switch_monitor"), False, False, 0)
    general_vbox.pack_start(_get_dynamic_kb_row(root_node, "open_next"), False, False, 0)
    general_vbox.pack_start(_get_dynamic_kb_row(root_node, "log_range"), False, False, 0)
    general_vbox.pack_start(_get_dynamic_kb_row(root_node, "zoom_in"), False, False, 0)
    general_vbox.pack_start(_get_dynamic_kb_row(root_node, "zoom_out"), False, False, 0)
    general = guiutils.get_named_frame(_("General"), general_vbox)

    tline_vbox = Gtk.VBox()
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "cut"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "cut_all"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "trim_start"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "trim_end"), False, False, 0)
    tline_vbox.pack_start(_get_kb_row(_("DELETE"),  _("Splice Out")), False, False, 0)
    tline_vbox.pack_start(_get_kb_row(_("Control + DELETE"),  _("Lift")), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "clear_filters"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "split_selected"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "resync"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "sync_all"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "insert"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "append"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "append_from_bin"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "3_point_overwrite"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "overwrite_range"), False, False, 0)
    tline_vbox.pack_start(_get_kb_row(_("Control + C"), _("Copy Clips")), False, False, 0)
    tline_vbox.pack_start(_get_kb_row(_("Control + V"), _("Paste Clips")), False, False, 0)
    tline_vbox.pack_start(_get_kb_row(_("Shift + Control + V"), _("Paste Filters/Properties")), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "nudge_back"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "nudge_forward"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "nudge_back_10"), False, False, 0)
    tline_vbox.pack_start(_get_dynamic_kb_row(root_node, "nudge_forward_10"), False, False, 0)
    tline = guiutils.get_named_frame(_("Timeline Edits"), tline_vbox)

    tline_action_vbox = Gtk.VBox()
    tline_action_vbox.pack_start(_get_dynamic_kb_row(root_node, "select_next"), False, False, 0)
    tline_action_vbox.pack_start(_get_dynamic_kb_row(root_node, "select_prev"), False, False, 0)
    tline_action_vbox.pack_start(_get_dynamic_kb_row(root_node, "tline_page_up"), False, False, 0)
    tline_action_vbox.pack_start(_get_dynamic_kb_row(root_node, "tline_page_down"), False, False, 0)
    tline_action_vbox.pack_start(_get_dynamic_kb_row(root_node, "toggle_track_output"), False, False, 0)
    tlineaction = guiutils.get_named_frame(_("Timeline Actions"), tline_action_vbox)
    
    trimming_box = Gtk.VBox()
    trimming_box.pack_start(_get_kb_row(_("Left Arrow "), _("Prev Frame Trim Edit")), False, False, 0)
    trimming_box.pack_start(_get_kb_row(_("Right Arrow"), _("Next Frame Trim Edit")), False, False, 0)
    trimming_box.pack_start(_get_kb_row(_("Shift + Left Arrow "), _("Back 10 Frames Trim Edit")), False, False, 0)
    trimming_box.pack_start(_get_kb_row(_("Shift + Right Arrow"), _("Forward 10 Frames Trim Edit")), False, False, 0)
    trimming_box.pack_start(_get_kb_row(_("ENTER"),  _("Complete Keyboard Trim Edit")), False, False, 0) #  _get_dynamic_kb_row(root_node, "enter_edit"), False, False, 0)
    trimming = guiutils.get_named_frame(_("Trimming"), trimming_box)

    marks_box = Gtk.VBox()
    marks_box.pack_start(_get_dynamic_kb_row(root_node, "mark_in"), False, False, 0)
    marks_box.pack_start(_get_dynamic_kb_row(root_node, "mark_out"), False, False, 0)
    marks_box.pack_start(_get_dynamic_kb_row(root_node, "to_mark_in"), False, False, 0)
    marks_box.pack_start(_get_dynamic_kb_row(root_node, "to_mark_out"), False, False, 0)
    marks_box.pack_start(_get_dynamic_kb_row(root_node, "clear_io_marks"), False, False, 0)
    marks_box.pack_start(_get_dynamic_kb_row(root_node, "add_marker"), False, False, 0)
    marks = guiutils.get_named_frame(_("Marks"), marks_box)

    track_head_vbox = Gtk.VBox()
    track_head_vbox.pack_start(_get_kb_row(_("Mouse Double Click"), _("Toggle Track Height")), False, False, 0)
    track_head = guiutils.get_named_frame(_("Track Head Column"), track_head_vbox)

    play_vbox = Gtk.VBox()
    play_vbox.pack_start(_get_dynamic_kb_row(root_node, "play_pause"), False, False, 0)
    play_vbox.pack_start(_get_dynamic_kb_row(root_node, "slower"), False, False, 0)
    play_vbox.pack_start(_get_dynamic_kb_row(root_node, "stop"), False, False, 0)
    play_vbox.pack_start(_get_dynamic_kb_row(root_node, "faster"), False, False, 0)
    play_vbox.pack_start(_get_dynamic_kb_row(root_node, "play_pause_loop_marks"), False, False, 0)
    play_vbox.pack_start(_get_kb_row(_("Left Arrow "), _("Next Frame")), False, False, 0)#_get_dynamic_kb_row(root_node, "prev_frame"), False, False, 0)
    play_vbox.pack_start(_get_kb_row(_("Right Arrow "), _("Previous Frames")), False, False, 0)#_get_dynamic_kb_row(root_node, "next_frame"), False, False, 0)
    play_vbox.pack_start(_get_kb_row(_("Control + Left Arrow"), _("Move Back at 10 fps slowmo")), False, False, 0)
    play_vbox.pack_start(_get_kb_row(_("Control + Right Arrow"), _("Move Forward  at 10 fps slowmo")), False, False, 0)
    play_vbox.pack_start(_get_kb_row(_("Shift + Left Arrow "), _("Move Back 10 Frames")), False, False, 0)
    play_vbox.pack_start(_get_kb_row(_("Shift + Right Arrow"), _("Move Forward 10 Frames")), False, False, 0)
    play_vbox.pack_start(_get_dynamic_kb_row(root_node, "prev_cut"), False, False, 0)
    play_vbox.pack_start(_get_dynamic_kb_row(root_node, "next_cut"), False, False, 0)
    play_vbox.pack_start(_get_kb_row(_("Home"), _("Go To Start")), False, False, 0)#_get_dynamic_kb_row(root_node, "to_start"), False, False, 0)
    play_vbox.pack_start(_get_kb_row(_("End"), _("Go To End")), False, False, 0)#_get_dynamic_kb_row(root_node, "to_end"), False, False, 0)
    play_vbox.pack_start(_get_dynamic_kb_row(root_node, "to_mark_in"), False, False, 0)
    play_vbox.pack_start(_get_dynamic_kb_row(root_node, "to_mark_out"), False, False, 0)
    play = guiutils.get_named_frame(_("Playback"), play_vbox)

    tools_vbox = Gtk.VBox()
    for tool_name, kb_shortcut in tool_set:
        tools_vbox.pack_start(_get_kb_row(kb_shortcut, tool_name), False, False, 0)
    tools_vbox.pack_start(_get_kb_row(_("Keypad 1-6"), _("Same as 1-6")), False, False, 0)
    tools = guiutils.get_named_frame(_("Edit Tools"), tools_vbox)

    kfs_vbox = Gtk.VBox()
    kfs_vbox.pack_start(_get_kb_row(_("Control + C"), _("Copy Keyframe Value")), False, False, 0)
    kfs_vbox.pack_start(_get_kb_row(_("Control + V"), _("Paste Keyframe Value")), False, False, 0)
    kfs_vbox.pack_start(_get_kb_row(_("Control + Mouse Drag"), _("Move all keyframes after selected")), False, False, 0)
    kfs = guiutils.get_named_frame(_("Keyframe and Geometry Editor"), kfs_vbox)
    
    geom_vbox = Gtk.VBox()
    geom_vbox.pack_start(_get_kb_row(_("Left Arrow "), _("Move Source Video Left 1px")), False, False, 0)
    geom_vbox.pack_start(_get_kb_row(_("Right Arrow"), _("Move Source Video Right 1px")), False, False, 0)
    geom_vbox.pack_start(_get_kb_row(_("Up Arrow"), _("Move Source Video Up 1px")), False, False, 0)
    geom_vbox.pack_start(_get_kb_row(_("Down Arrow"), _("Move Source Video Down 1px")), False, False, 0)
    geom_vbox.pack_start(_get_kb_row(_("Control + Arrow"), _("Move Source Video 10px")), False, False, 0)
    geom_vbox.pack_start(_get_kb_row(_("Control + Mouse Drag"), _("Keep Aspect Ratio in Affine Blend scaling")), False, False, 0)
    geom_vbox.pack_start(_get_kb_row(_("Shift + Left Arrow "), _("Scale Down")), False, False, 0)
    geom_vbox.pack_start(_get_kb_row(_("Shift + Right Arrow"), _("Scale Up")), False, False, 0)
    geom_vbox.pack_start(_get_kb_row(_("Shift + Control + Left Arrow "), _("Scale Down More")), False, False, 0)
    geom_vbox.pack_start(_get_kb_row(_("Shift + Control + Right Arrow"), _("Scale Up More")), False, False, 0)
    geom_vbox.pack_start(_get_kb_row(_("Shift"), _("Snap to X or Y of drag start point")), False, False, 0)
    geom = guiutils.get_named_frame(_("Geometry Editor GUI Panel"), geom_vbox)

    roto_vbox = Gtk.VBox()
    roto_vbox.pack_start(_get_kb_row(_("Delete"), _("Deletes Selected Handle")), False, False, 0)
    roto_vbox.pack_start(_get_kb_row(_("Left Arrow "), _("Previous Frame")), False, False, 0)
    roto_vbox.pack_start(_get_kb_row(_("Right Arrow"), _("Next Frame")), False, False, 0)
    roto = guiutils.get_named_frame(_("RotoMask Editor"), roto_vbox)

    quick_effects_panel = shortcutsquickeffects.get_shortcuts_panel()
 
    panel = Gtk.VBox()
    panel.pack_start(tools, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(tline, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(tlineaction, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(trimming, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(marks, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(track_head, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(play, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(general, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(kfs, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(geom, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(roto, False, False, 0)
    panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
    panel.pack_start(quick_effects_panel, False, False, 0)
    
    return panel

def _get_dynamic_kb_row(root_node, code):
    key_name, action_name = shortcuts.get_shortcut_info(root_node, code)
    editable = shortcuts.get_shortcuts_editable()
    if editable == True:
        edit_launch = guicomponents.KBShortcutEditor(code, key_name, kb_shortcut_dialog, kb_shortcut_changed_callback) # kb_shortcut_changed_callback is global, set at dialog launch
    else:
        edit_launch = guicomponents.KBShortcutEditor(code, key_name, kb_shortcut_dialog, None, False) 
    return _get_kb_row(key_name, action_name, edit_launch)

def _get_kb_row(msg1, msg2, edit_launch=None):
    label1 = Gtk.Label(label=msg1)
    label2 = guiutils.bold_label(str(msg2))
    if edit_launch == None:
        widget = Gtk.Label()
    else:
        widget = edit_launch.widget
        edit_launch.set_shortcut_label(label1)
        
    KB_SHORTCUT_ROW_WIDTH = 600
    KB_SHORTCUT_ROW_HEIGHT = 28

    row = guiutils.get_three_column_box(label1, guiutils.get_left_justified_box([label2]), widget, 240, 48)
    row.set_size_request(KB_SHORTCUT_ROW_WIDTH, KB_SHORTCUT_ROW_HEIGHT)
    row.show()
    return row