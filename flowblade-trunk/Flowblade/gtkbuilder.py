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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

"""
Widget builder module to help moving to Gtk 4.
"""

from gi.repository import Gtk

import os

import gui
import guiutils

GTK_3 = 3
GTK_3 = 4
GTK_VERSION = GTK_3 # Flip when moving over.


def HPaned():
    paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
    """
    Uncomment for eventual Gtk4.
    paned.pack1 = lambda child, resize, shrink: _pack1(paned, child, resize, shrink)
    paned.pack2 = lambda child, resize, shrink: _pack2(paned, child, resize, shrink)
    """
    return paned

def VPaned():
    paned = Gtk.Paned.new(Gtk.Orientation.VERTICAL)
    """
    Uncomment for eventual Gtk4.
    paned.pack1 = lambda child, resize, shrink: _pack1(paned, child, resize, shrink)
    paned.pack2 = lambda child, resize, shrink: _pack2(paned, child, resize, shrink)
    """
    return paned

def EventBox(widget, signal, callback, user_data=None):
    event_box = Gtk.EventBox()
    event_box.add(widget)
    
    if signal == "button-press-event":
        event_box.connect("button-press-event", callback)
    elif signal == "button-release-event":
        event_box.connect("button-release-event", callback)
            
    return event_box

def button_set_image(button, image_resource):
    button.set_image(guiutils.get_image(image_resource)) # for Gtk4 we're gonna use set_child() with GtkImage widget

def button_set_image_icon_name(button, icon_name):
    icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
    button.set_image(icon)
        
def get_file_chooser_button(title, action=Gtk.FileChooserAction.OPEN, parent=None):
    if action == Gtk.FileChooserAction.OPEN:
        b_title = _("(None)")
    else:
        b_title = title
    b = Gtk.Button.new_with_label(b_title)
    b.title = title
    b.priv_action = action
    b.priv_current_folder = None
    b.priv_filenames = None
    b.priv_parent = parent
    b.priv_file_filter = None
    b.priv_local_only = False
    b.priv_selection_changed_listener = None
    b.priv_selection_changed_data = None
    b._filename = _filename
    
    b.connect("clicked", _file_chooser_button_clicked)
    b.set_action = lambda a : _set_file_action(b, a)
    b.set_current_folder = lambda fp : _set_current_folder(b, fp)
    b.get_current_folder = lambda : _get_current_folder(b)
    b.set_current_folder_uri = lambda : _set_current_folder_uri(b)
    b.set_filename = lambda fn : _set_filename(b, fn)
    b.get_filenames = lambda : _get_filenames(b)
    b.get_filename = lambda : _get_filename(b)
    b.add_filter = lambda ff :_add_filter(b, ff)
    b.set_local_only = lambda lo : _set_local_only(b, lo)
    b.connect_selection_changed = lambda data, listener : _connect_selection_changed(b, data, listener) 
    b.dialog = None
    
    return b

def get_file_chooser_button_with_dialog(dialog):
    b = get_file_chooser_button("dummy")
    b.dialog = dialog
    dialog.b = b
    return b
    
# ---------------------------------------------------- Gtk 4 replace methods.
# --- H/VPaned
def _pack1(paned, child, resize, shrink):
    paned.set_start_child(child)

def _pack2(paned, child, resize, shrink):
    paned.set_end_child(child)

# --- FileChooserButton
def _file_chooser_button_clicked(b):
    if b.dialog != None:
        b.dialog.show()
        return 
        
    dialog = Gtk.FileChooserDialog(b.title, b.priv_parent,
                                   b.priv_action,
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _get_file_chooser_action_ok_name(b.priv_action), Gtk.ResponseType.ACCEPT))
    dialog.b = b
    dialog.set_action(b.priv_action)
    if b.priv_current_folder != None:
        dialog.set_current_folder(b.priv_current_folder)
    dialog.set_do_overwrite_confirmation(True)
    if b.priv_file_filter != None:
        dialog.set_filter(b.priv_file_filter)
    dialog.set_select_multiple(False)
    dialog.set_local_only(b.priv_local_only)
    dialog.connect('response', _file_selection_done)
    dialog.show()

def _file_selection_done(dialog, response_id):
    if response_id == Gtk.ResponseType.CANCEL:
        dialog.destroy()
        return

    b = dialog.b
    b.priv_filenames = dialog.get_filenames()
    if b.priv_action == Gtk.FileChooserAction.SELECT_FOLDER:
        b.priv_current_folder = b.priv_filenames[0] 
    b.set_label(_filename(b.priv_filenames[0]))
    
    dialog.destroy()
    
    if b.priv_selection_changed_listener != None:
        b.priv_selection_changed_listener(b, b.priv_selection_changed_data)

def _set_file_action(b, action):
    b.priv_action = action
    
def _set_current_folder(b, file_path):
    b.priv_current_folder = file_path
    b.priv_filenames = [file_path]
    if b.priv_action == Gtk.FileChooserAction.SELECT_FOLDER:
        b.set_label(_filename(file_path))
    
def _filename(path):
    path = path.rstrip("/")
    return os.path.basename(path)

def _get_file_chooser_action_ok_name(action):
    if action == Gtk.FileChooserAction.SELECT_FOLDER:
        return _("Open")
    else:
        return _("Open")

def _get_filenames(b):
    try:
        return b.priv_filenames
    except:
        return None

def _get_filename(b):
    try:
        return b.priv_filenames[0]
    except:
        return None

def _set_filename(b, fn):
    b.priv_filenames = []
    b.priv_filenames.append(fn)
    b.set_label(_filename(b.priv_filenames[0]))

def _get_current_folder(b):
    return b.priv_current_folder
    
def _add_filter(b, ff):
    b.priv_file_filter = ff

def _set_local_only(b, lo):
    b.priv_local_only = lo

def _connect_selection_changed(b, data, listener):
    b.priv_selection_changed_listener = listener
    b.priv_selection_changed_data = data
    
