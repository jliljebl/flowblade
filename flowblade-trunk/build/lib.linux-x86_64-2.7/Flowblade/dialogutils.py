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
Module contains functions to build generic dialogs.
"""
from gi.repository import GObject


from gi.repository import Gtk

import guiutils

def dialog_destroy(dialog, response):
    dialog.destroy()

def default_behaviour(dialog):
    dialog.set_default_response(Gtk.ResponseType.OK)
    dialog.set_resizable(False)

def panel_ok_dialog(title, panel):
    dialog = Gtk.Dialog(title, None,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        ( _("OK").encode('utf-8'), Gtk.ResponseType.OK))
                        
    alignment = get_default_alignment(panel)
    
    dialog.vbox.pack_start(alignment, True, True, 0)
    set_outer_margins(dialog.vbox)
    default_behaviour(dialog)
    dialog.connect('response', dialog_destroy)
    dialog.show_all()
    
def info_message(primary_txt, secondary_txt, parent_window):
    warning_message(primary_txt, secondary_txt, parent_window, is_info=True)

def warning_message(primary_txt, secondary_txt, parent_window, is_info=False):
    warning_message_with_callback(primary_txt, secondary_txt, parent_window, is_info, dialog_destroy)

def warning_message_with_callback(primary_txt, secondary_txt, parent_window, is_info, callback):
    content = get_warning_message_dialog_panel(primary_txt, secondary_txt, is_info)
    dialog = Gtk.Dialog("",
                        parent_window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        ( _("OK").encode('utf-8'), Gtk.ResponseType.ACCEPT))
    alignment = get_default_alignment(content)
    dialog.vbox.pack_start(alignment, True, True, 0)
    set_outer_margins(dialog.vbox)
    dialog.set_resizable(False)
    dialog.connect('response', callback)
    dialog.show_all()

def warning_message_with_panels(primary_txt, secondary_txt, parent_window, is_info, callback, panels):
    content = get_warning_message_dialog_panel(primary_txt, secondary_txt, is_info, None, panels)
    dialog = Gtk.Dialog("",
                        parent_window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        ( _("OK").encode('utf-8'), Gtk.ResponseType.ACCEPT))
    alignment = get_default_alignment(content)
    dialog.vbox.pack_start(alignment, True, True, 0)
    set_outer_margins(dialog.vbox)
    dialog.set_resizable(False)
    dialog.connect('response', callback)
    dialog.show_all()
    
def warning_confirmation(callback, primary_txt, secondary_txt, parent_window, data=None, is_info=False, use_confirm_text=False):
    content = get_warning_message_dialog_panel(primary_txt, secondary_txt, is_info)
    align = get_default_alignment(content)
    
    if use_confirm_text == True:
        accept_text = _("Confirm").encode('utf-8')
    else:
        accept_text = _("OK").encode('utf-8')
    
    dialog = Gtk.Dialog("",
                        parent_window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel").encode('utf-8'), Gtk.ResponseType.REJECT,
                         accept_text, Gtk.ResponseType.ACCEPT))
    dialog.vbox.pack_start(align, True, True, 0)
    set_outer_margins(dialog.vbox)
    dialog.set_resizable(False)
    if data == None:
        dialog.connect('response', callback)
    else:
        dialog.connect('response', callback, data)

    dialog.show_all()

def get_warning_message_dialog_panel(primary_txt, secondary_txt, is_info=False, alternative_icon=None, panels=None):

    if is_info == True:
        icon = Gtk.STOCK_DIALOG_INFO
    else:
        icon = Gtk.STOCK_DIALOG_WARNING
    
    if alternative_icon != None:
        icon = alternative_icon

    warning_icon = Gtk.Image.new_from_stock(icon, Gtk.IconSize.DIALOG)
    icon_box = Gtk.VBox(False, 2)
    icon_box.pack_start(warning_icon, False, False, 0)
    icon_box.pack_start(Gtk.Label(), True, True, 0)
    
    p_label = guiutils.bold_label(primary_txt)
    s_label = Gtk.Label(label=secondary_txt)
    s_label.set_use_markup(True)
    texts_pad = Gtk.Label()
    texts_pad.set_size_request(12,12)

    pbox = Gtk.HBox(False, 1)
    pbox.pack_start(p_label, False, False, 0)
    pbox.pack_start(Gtk.Label(), True, True, 0)

    sbox = Gtk.HBox(False, 1)
    sbox.pack_start(s_label, False, False, 0)
    sbox.pack_start(Gtk.Label(), True, True, 0)
    
    text_box = Gtk.VBox(False, 0)
    text_box.pack_start(pbox, False, False, 0)
    text_box.pack_start(texts_pad, False, False, 0)
    text_box.pack_start(sbox, False, False, 0)
    if panels != None:
        for panel in panels:
            text_box.pack_start(panel, False, False, 0)
    text_box.pack_start(Gtk.Label(), True, True, 0)

    hbox = Gtk.HBox(False, 12)
    hbox.pack_start(icon_box, False, False, 0)
    hbox.pack_start(text_box, True, True, 0)
    
    return hbox

def get_single_line_text_input_dialog(chars, label_width,title, ok_button_text,
                                      label, default_text):
    dialog = Gtk.Dialog(title, None,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (_("Cancel").encode('utf-8'), Gtk.ResponseType.REJECT,
                            ok_button_text, Gtk.ResponseType.OK))

    entry = Gtk.Entry()
    entry.set_width_chars(30)
    entry.set_text(default_text)
    entry.set_activates_default(True)

    entry_row = guiutils.get_two_column_box(Gtk.Label(label=label),
                                               entry,
                                               180)

    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(entry_row, False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(12, 12), False, False, 0)

    alignment = guiutils.set_margins(vbox, 6, 24, 24, 24)

    dialog.vbox.pack_start(alignment, True, True, 0)
    set_outer_margins(dialog.vbox)

    default_behaviour(dialog)
    dialog.set_default_response(Gtk.ResponseType.ACCEPT)
    
    return (dialog, entry)

def get_default_alignment(panel):
    alignment = Gtk.Frame.new("") #Gtk.Frame.new(None)
    alignment.add(panel)
    alignment.set_shadow_type(Gtk.ShadowType.NONE)
    guiutils.set_margins(alignment, 12, 24, 12, 18)
    return alignment

def get_alignment2(panel):
    alignment = Gtk.Frame.new("") #Gtk.Frame.new(None)
    alignment.add(panel)
    alignment.set_shadow_type(Gtk.ShadowType.NONE)
    guiutils.set_margins(alignment, 6, 24, 12, 12)
    
    return alignment

def set_outer_margins(cont):
    guiutils.set_margins(cont, 0, 6, 0, 6)

# ------------------------------------------------------------------ delayed window destroying 
def delay_destroy_window(window, delay):
    GObject.timeout_add(int(delay * 1000), _window_destroy_event, window)

def _window_destroy_event(window):
    window.destroy()
    
