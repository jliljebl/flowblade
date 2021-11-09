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
from gi.repository import Gtk, Gdk

import clipeffectseditor
import edit
import editorpersistance
from editorstate import current_sequence
import guiutils
import guicomponents
import mltfilters
import movemodes
import translations

_set_quick_effect_menu = Gtk.Menu()

NO_SHORTCUT_SET = "##¤¤NOSHORTCUTSET¤¤##"

_EMPTY_SHORTCUTS_DICT = {   "f1": NO_SHORTCUT_SET,
                            "f2": NO_SHORTCUT_SET,
                            "f3": NO_SHORTCUT_SET,
                            "f4": NO_SHORTCUT_SET,
                            "f5": NO_SHORTCUT_SET,
                            "f6": NO_SHORTCUT_SET,
                            "f7": NO_SHORTCUT_SET,
                            "f8": NO_SHORTCUT_SET,
                            "f9": NO_SHORTCUT_SET,
                            "f10": NO_SHORTCUT_SET,
                            "f11": NO_SHORTCUT_SET,
                            "f12": NO_SHORTCUT_SET}

_quick_effects_dict = None

def load_shortcuts():
    if editorpersistance.prefs.quick_effects == None:
        editorpersistance.prefs.quick_effects = _EMPTY_SHORTCUTS_DICT
        editorpersistance.save()

    global _quick_effects_dict
    _quick_effects_dict = editorpersistance.prefs.quick_effects

def maybe_do_quick_shortcut_filter_add(event):
    state = event.get_state()
    key_name = Gdk.keyval_name(event.keyval).lower()
    if state & Gdk.ModifierType.CONTROL_MASK:
        if key_name in _quick_effects_dict:
            quick_add_filter = _quick_effects_dict[key_name]
            if quick_add_filter != NO_SHORTCUT_SET:
                if movemodes.selected_track == -1:
                    return False
                filter_info = mltfilters.get_filter_for_name(quick_add_filter)
                range_in = movemodes.selected_range_in
                range_out = movemodes.selected_range_out
                track = current_sequence().tracks[movemodes.selected_track]
                clips = track.clips[range_in:range_out +1]
                data = {    "clips":clips,
                            "filter_info":filter_info,
                            "filter_edit_done_func": clipeffectseditor.filter_edit_multi_done_stack_update}
                action = edit.add_filter_multi_action(data)
                action.do_edit()
                return True

    return False

def get_shortcuts_panel():
    vbox = Gtk.VBox()
    vbox.pack_start(_get_row(_("Control + F1"), "f1"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F2"), "f2"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F3"), "f3"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F4"), "f4"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F5"), "f5"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F6"), "f6"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F7"), "f7"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F8"), "f8"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F9"), "f9"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F10"), "f10"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F11"), "f11"), False, False, 0)
    vbox.pack_start(_get_row(_("Control + F12"), "f12"), False, False, 0)
    
    frame = guiutils.get_named_frame(_("Quick Filters"), vbox)
    return frame

def _get_row(shotcut_name, shortcut_key):
    shotcut_name_label = Gtk.Label(label=shotcut_name)
    shortcut_value_text = _get_short_cut_value_text(shortcut_key)
    shortcut_value_label = Gtk.Label(label=shortcut_value_text)

    surface = guiutils.get_cairo_image("kb_configuration")
    edit_menu_press = guicomponents.PressLaunch(lambda w,e : _launch_menu(shortcut_key, e, shortcut_value_label), surface)

    edit_box = Gtk.HBox()
    edit_box.pack_start(edit_menu_press.widget, False, False, 0)

    KB_SHORTCUT_ROW_WIDTH = 500 # These are duplicated from dialogs.py
    KB_SHORTCUT_ROW_HEIGHT = 22
    
    row = guiutils.get_three_column_box(shotcut_name_label, shortcut_value_label, edit_box, 170, 48)
    row.set_size_request(KB_SHORTCUT_ROW_WIDTH, KB_SHORTCUT_ROW_HEIGHT)
    row.show()
    return row

def _get_short_cut_value_text(shortcut_key):
    shortcut_filter_name = _quick_effects_dict[shortcut_key]
    if shortcut_filter_name == NO_SHORTCUT_SET:
        return _("No Filter Set")
        
    filter_info = mltfilters.get_filter_for_name(shortcut_filter_name)
    return translations.get_filter_name(filter_info.name)

def _launch_menu(shortcut_key, event, shortcut_value_label):
    menu = _set_quick_effect_menu
    guiutils.remove_children(menu)

    add_item = Gtk.MenuItem(_("Set Quick Filter for Shortcut Key"))
    menu.append(add_item)
    add_menu = Gtk.Menu()
    add_item.set_submenu(add_menu)
    add_item.show()
    delete_item = Gtk.MenuItem(_("Delete Quick Filter from Shortcut Key"))
    delete_item.connect("activate", _delete_shortcut, (shortcut_key, shortcut_value_label))
    delete_item.show()
    menu.append(delete_item)
    
    for group in mltfilters.groups:
        group_name, filters_array = group

        # "Blend" group not available for quick shortcuts.
        if filters_array[0].mlt_service_id == "cairoblend_mode":
            continue
        
        group_item = Gtk.MenuItem(group_name)
        add_menu.append(group_item)
        sub_menu = Gtk.Menu()
        group_item.set_submenu(sub_menu)
        for filter_info in filters_array:
            filter_item = Gtk.MenuItem(translations.get_filter_name(filter_info.name))
            sub_menu.append(filter_item)
            filter_item.connect("activate", _set_shortcut, (shortcut_key, filter_info, shortcut_value_label))
            filter_item.show()
        group_item.show()

    menu.popup(None, None, None, None, event.button, event.time)

def _set_shortcut(w, data):
    shortcut_key, filter_info, shortcut_value_label = data

    global _quick_effects_dict
    _quick_effects_dict[shortcut_key] = filter_info.name
    editorpersistance.prefs.quick_effects = _quick_effects_dict
    editorpersistance.save()
    
    shortcut_value_label.set_text(_get_short_cut_value_text(shortcut_key))

def _delete_shortcut(w, data):
    shortcut_key, shortcut_value_label = data

    global _quick_effects_dict
    _quick_effects_dict[shortcut_key] = NO_SHORTCUT_SET
    editorpersistance.prefs.quick_effects = _quick_effects_dict
    editorpersistance.save()
 
    shortcut_value_label.set_text(_get_short_cut_value_text(shortcut_key))