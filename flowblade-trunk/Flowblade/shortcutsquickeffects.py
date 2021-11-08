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

import editorpersistance
import guiutils
import guicomponents

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
    
    frame = guiutils.get_named_frame(_("Quick Effects"), vbox)
    return frame

def _get_row(shotcut_name, shortcut_key):
    shotcut_name_label = Gtk.Label(label=shotcut_name)
    shortcut_value_text = _get_short_cut_value_text(shortcut_key)
    shotcut_value_label = Gtk.Label(label=shortcut_value_text)

    surface = guiutils.get_cairo_image("add_kf")
    plus_press = guicomponents.PressLaunch(_add_short_cut, surface)
    surface = guiutils.get_cairo_image("delete_kf")
    minus_press = guicomponents.PressLaunch(_delete_short_cut, surface)

    edit_box = Gtk.HBox()
    edit_box.pack_start(plus_press.widget, False, False, 0)
    edit_box.pack_start(minus_press.widget, False, False, 0)

    KB_SHORTCUT_ROW_WIDTH = 500
    KB_SHORTCUT_ROW_HEIGHT = 22
    
    row = guiutils.get_three_column_box(shotcut_name_label, shotcut_value_label, edit_box, 170, 48)
    row.set_size_request(KB_SHORTCUT_ROW_WIDTH, KB_SHORTCUT_ROW_HEIGHT)
    row.show()
    return row

def _get_short_cut_value_text(shortcut_key):
    return "Color Grading"

def _add_short_cut(widget):
    pass

def _delete_short_cut(widget):
    pass