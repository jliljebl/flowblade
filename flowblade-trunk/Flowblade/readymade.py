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
import json
import os

import dialogutils
import gui
import guiutils
import respaths


READYMADE_NAME = "name"
READYMADE_TYPE = "type"
READYMADE_PROGRAM = "program"
READYMADE_EDIT_DATA = "editdata"
READYMADE_CATEGORY = "category"
READYMADE_AUTHOR = "author"
READYMADE_VERSION = "version"
READYMADE_DATE = "date"


TYPE_NAMES = None


readymades = []


# Object represinting an available redy made media item.
# Data read from json metadata file.
"""
readymade.metadata file example.
{
    "name": "Colors",
    "type": "blenderproject",
    "program": "colors.blend",
    "editdata": "colors.editdata",
    "category": "textanimation",
    "author": "Janne Liljeblad",
    "version": "1",
    "date": "27-07-2020"
}
"""
class ReadyMade:

    def __init__(self, data_dir):
        
        self.data_dir = data_dir

        f = open(respaths.READYMADE_PATH + data_dir + "/readymade.metadata", 'r')
        obj_str = f.read()
        f.close()

        self.metad = json.loads(obj_str)
        


# ---------------------------------------------------------------------- INTERFACE
def init():
    global readymades
    readymades_dirs = os.listdir(respaths.READYMADE_PATH)
    for item_dir in readymades_dirs:
        readymade = ReadyMade(item_dir)
        readymades.append(readymade)

    global TYPE_NAMES
    TYPE_NAMES = {"blenderproject": _("Blender Project")}
        
def show_dialog():

    dialog = Gtk.Dialog(_("RaedyMade Media"), None,
                    Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    (_("Cancel"), Gtk.ResponseType.REJECT,
                    _("OK"), Gtk.ResponseType.ACCEPT))


    panel = _get_panel()

    dialog.connect('response', _preferences_dialog_callback)
    dialog.vbox.pack_start(panel, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    # Jul-2016 - SvdB - The next line is to get rid of the message "GtkDialog mapped without a transient parent. This is discouraged."
    dialog.set_transient_for(gui.editor_window.window)
    dialog.show_all()


# ----------------------------------------------------------------- MODULE FUNCTIONS
def _preferences_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:

        return

    dialog.destroy()


# ----------------------------------------------------------------- GUI OBJECTS
def _get_panel():
    vbox = Gtk.VBox(False, 2)
    
    for rm in readymades:
        rm_select_item = ReadyMadeItemSelectPanel(rm, _item_selected)
        vbox.pack_start(rm_select_item.widget, False, False, 0)

    return vbox

def _item_selected(ready_made_item):
    pass


class ReadyMadeItemSelectPanel:

    def __init__(self, ready_made_item, selected_callback):
        self.ready_made_item = ready_made_item
        self.data_dir = ready_made_item.data_dir
        self.selected_callback = selected_callback
        
        img_path = respaths.READYMADE_PATH + self.ready_made_item.data_dir + "/screenshot.png"
        print(img_path)
        screenshot_img = Gtk.Image.new_from_file (img_path)

        name = Gtk.Label(ready_made_item.metad[READYMADE_NAME])
        name.set_use_markup(True)
        #guiutils.set_margins(name, 0, 8, 0, 0)
        type_label = Gtk.Label(TYPE_NAMES[ready_made_item.metad[READYMADE_TYPE]])
        type_label.set_use_markup(True)

        text_vbox = Gtk.VBox(False, 2)
        text_vbox.pack_start(guiutils.get_left_justified_box([name]), False, False, 0)
        text_vbox.pack_start(guiutils.get_left_justified_box([type_label]), False, False, 0)
        #guiutils.set_margins(item_vbox, 12, 18, 12, 12)

        panel = Gtk.HBox(False, 2)
        panel.pack_start(screenshot_img, False, False, 0)
        panel.pack_start(text_vbox, False, False, 0)

        self.widget = Gtk.EventBox()
        self.widget.connect("button-press-event", lambda w,e: self.selected_callback(w, item_number))
        self.widget.set_can_focus(True)
        self.widget.add_events(Gdk.EventMask.KEY_PRESS_MASK)

        self.widget.add(panel)
        
        #widget.item_number = item_number
                
        #self.set_item_color(widget)

        #return widget
        
    def pressed(self):
        self.selected_callback(self.ready_made_item)


