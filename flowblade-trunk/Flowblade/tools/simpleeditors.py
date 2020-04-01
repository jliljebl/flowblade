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

"""
Module for creating simple editors for e.g. container clips program data.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from gi.repository import GObject

import dialogutils
import gui
import guiutils


SIMPLE_EDITOR_STRING = 0
SIMPLE_EDITOR_VALUE = 1
SIMPLE_EDITOR_FLOAT = 2
SIMPLE_EDITOR_INT = 3
SIMPLE_EDITOR_COLOR = 4

DEFAULT_VALUES = ["Text", "a value", "0.0", "0", "(1.0, 1.0, 1.0, 1.0)"]

MIN_VAL = -pow(2, 63) # Gtk.Adjustments requires some bounds
MAX_VAL = pow(2, 63)

    
SIMPLE_EDITOR_LEFT_WIDTH = 150


def show_blender_container_clip_program_editor(callback, blender_objects):
    # Create panels for objects
    panels = []
    editors = []
    for obj in blender_objects:
        # object is [name, type, editors_list] see blenderprojectinit.py
        editors_data_list = obj[2]
        editors_panel = Gtk.VBox(True, 2)
        for editor_data in editors_data_list:
            prop_path, label_text, tooltip, editor_type, value = editor_data
            editor_type = int(editor_type)
            editor = get_editor(editor_type, (obj[0], prop_path), label_text, value, tooltip)
            editor.blender_editor_data = editor_data # We need this the later to apply the changes.
            editors.append(editor)
            
            editors_panel.pack_start(editor, False, False, 0)

        if len(editors_data_list) > 0:
            panel = guiutils.get_named_frame(obj[0] + " - " + obj[1], editors_panel)
            panels.append(panel)
        
    # Create and show dialog
    dialog = Gtk.Dialog(_("Blender Project Edit"), gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                         _("Save Changes"), Gtk.ResponseType.ACCEPT))

    pane = Gtk.VBox(False, 2)
    for panel in panels:
        pane.pack_start(panel, False, False, 0)

    alignment = dialogutils.get_default_alignment(pane)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.vbox.pack_start(alignment, True, True, 0)

    dialog.set_default_response(Gtk.ResponseType.REJECT)
    dialog.set_resizable(False)
    dialog.connect('response', callback, editors)
    dialog.show_all()

def get_simple_editor_selector(active_index, callback):

    editor_select = Gtk.ComboBoxText()
    editor_select.append_text(_("String")) # these corespond values above
    editor_select.append_text(_("Value"))
    editor_select.append_text(_("Float"))
    editor_select.append_text(_("Int"))
    editor_select.append_text(_("Color"))
    editor_select.set_active(active_index)
    if callback != None:
        editor_select.connect("changed", callback)
    
    return editor_select

# ----------------------------------------------------------------------- editors
def get_editor(editor_type, id_data, label_text, value, tooltip):
    if editor_type == SIMPLE_EDITOR_STRING:
        editor = TextEditor(id_data, label_text, value, tooltip)
        editor.return_quoted_string = True
        return editor
    elif editor_type == SIMPLE_EDITOR_VALUE:
        return  TextEditor(id_data, label_text, value, tooltip)
    elif editor_type == SIMPLE_EDITOR_FLOAT:
        return FloatEditor(id_data, label_text, value, tooltip)
    elif editor_type == SIMPLE_EDITOR_INT:
        return IntEditor(id_data, label_text, value, tooltip)
    elif editor_type == SIMPLE_EDITOR_COLOR:
        return ColorEditor(id_data, label_text, value, tooltip)


class AbstractSimpleEditor(Gtk.HBox):
    
    def __init__(self, id_data, tooltip):
        GObject.GObject.__init__(self)
        self.id_data = id_data # the data needed to target edited values on correct object.
        self.tooltip = tooltip
        
    def build_editor(self, label_text, widget):
        widget.set_tooltip_text (self.tooltip)
        left_box = guiutils.get_left_justified_box([Gtk.Label(label=label_text)])
        left_box.set_size_request(SIMPLE_EDITOR_LEFT_WIDTH, guiutils.TWO_COLUMN_BOX_HEIGHT)
        self.pack_start(left_box, False, True, 0)
        self.pack_start(widget, True, True, 0)


class TextEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)
        
        self.return_quoted_string = False # This is set elsewhere if needed
        
        # If input value has quotes we need to strip them before editing
        # and put back when value is asked for.
        if value[0:1] == '"':
            value = value[1:len(value) - 1]

        self.entry = Gtk.Entry()
        self.entry.set_text(value)
        
        self.build_editor(label_text, self.entry)

    def get_value(self):
        value = self.entry.get_text()
        if self.return_quoted_string == True:
            return '"' + self.entry.get_text()  + '"'
        else:
            return self.value


class FloatEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)

        self.spinbutton = Gtk.SpinButton.new_with_range(MIN_VAL, MAX_VAL, 0.1)
        self.spinbutton.set_snap_to_ticks(False)
        self.spinbutton.set_digits(2)
        self.spinbutton.set_value(float(value))
        
        self.build_editor(label_text, self.spinbutton)

    def get_value(self):
        self.spinbutton.get_value()
            

class IntEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)

        self.spinbutton = Gtk.SpinButton.new_with_range(MIN_VAL, MAX_VAL, 0.1)
        self.spinbutton.set_snap_to_ticks(False)
        self.spinbutton.set_digits(0)
        self.spinbutton.set_value(int(value))
        
        self.build_editor(label_text, self.spinbutton)

    def get_value(self):
        self.spinbutton.get_value_as_int()


class ColorEditor(AbstractSimpleEditor):

    def __init__(self, id_data, label_text, value, tooltip):
        AbstractSimpleEditor.__init__(self, id_data, tooltip)

        if value[0:1] == '(':
            value = value[1:len(value) - 1]

        if value[len(value) - 1:len(value)] == ')':
            value = value[0:len(value) - 1]
            
        four_float_tuple = tuple(map(float, value.split(', '))) 

        rgba = Gdk.RGBA(*four_float_tuple)
        print(rgba.to_string())

        self.colorbutton = Gtk.ColorButton.new_with_rgba(rgba)
        
        self.build_editor(label_text, self.colorbutton)

    def get_value(self):
        self.colorbutton.get_rgba().to_string()
    
