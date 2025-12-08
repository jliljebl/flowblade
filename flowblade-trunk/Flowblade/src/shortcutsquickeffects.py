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
_active_edit_popover = None


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
    edit_menu_press = guicomponents.PressLaunch(lambda w,e : _launch_menu(w, shortcut_key, shortcut_value_label), surface)

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

def _launch_menu(widget, shortcut_key, shortcut_value_label):
    global _active_edit_popover
    
    _active_edit_popover = QuickKBShortcutEditPopover(widget, shortcut_key, shortcut_value_label)
    _active_edit_popover.show()

def _set_shortcut(data):
    shortcut_key, filter_info, shortcut_value_label = data

    global _quick_effects_dict
    _quick_effects_dict[shortcut_key] = filter_info.name
    editorpersistance.prefs.quick_effects = _quick_effects_dict
    editorpersistance.save()
    
    shortcut_value_label.set_text(_get_short_cut_value_text(shortcut_key))

def _delete_shortcut(data):
    shortcut_key, shortcut_value_label = data

    global _quick_effects_dict
    _quick_effects_dict[shortcut_key] = NO_SHORTCUT_SET
    editorpersistance.prefs.quick_effects = _quick_effects_dict
    editorpersistance.save()
 
    shortcut_value_label.set_text(_get_short_cut_value_text(shortcut_key))



class QuickKBShortcutEditPopover:
    def __init__(self, launch_widget, shortcut_key, shortcut_value_label):

        self.shortcut_key = shortcut_key
        self.shortcut_value_label = shortcut_value_label

        set_label_row = guiutils.get_left_justified_box([Gtk.Label(label=_("Select Quick Filter:"))])
        set_button = Gtk.Button(_("Set Quick Filter for Shortcut Key"))
        set_button.connect("clicked", self._set_shortcut)
        delete_button = Gtk.Button(_("Delete Quick Filter from Shortcut Key"))
        delete_button.connect("clicked", self._delete_shortcut)
        self.filter_select_combo = self._create_filter_select_combo()
        self.filter_select_combo.widget.set_margin_bottom(8)

        self.pop_over_pane = Gtk.VBox(False, 2)
        self.pop_over_pane.pack_start(set_label_row, False, False, 0)
        self.pop_over_pane.pack_start(self.filter_select_combo.widget, False, False, 0)
        self.pop_over_pane.pack_start(set_button, False, False, 0)
        self.pop_over_pane.pack_start(guiutils.pad_label(24, 24), False, False, 0)
        self.pop_over_pane.pack_start(delete_button, False, False, 0)
        guiutils.set_margins(self.pop_over_pane,8,8,8,8)
        self.pop_over_pane.show_all()

        self.popover = Gtk.Popover.new(launch_widget)
        self.popover.add(self.pop_over_pane)

    def _create_filter_select_combo(self):
        # categories_list is list of form [("category_name", [category_items]), ...]
        # with category_items list of form [("item_name", data_object), ...]
        categories_list = []

        for group in mltfilters.groups:
            group_name, filters_array = group
                
            items_list = []

            for filter_info in filters_array:
                filter_name = translations.get_filter_name(filter_info.name)
                items_list.append((filter_name, filter_info))

            categories_list.append((group_name, items_list))
        
        combo = guicomponents.CategoriesModelComboBoxWithData(categories_list)
        iter = combo.model.get_iter_from_string("0:0")
        combo.widget.set_active_iter(iter)
        
        return combo
    
    def _set_shortcut(self, widget):
        name, filter_info = self.filter_select_combo.get_selected()
        data = (self.shortcut_key, filter_info, self.shortcut_value_label)
        _set_shortcut(data)
        self.hide()
        
    def _delete_shortcut(self, widget):
        data = (self.shortcut_key, self.shortcut_value_label)
        _delete_shortcut(data)
        self.hide()

    def show(self):
        self.popover.show()

    def hide(self):
        self.popover.popdown()
