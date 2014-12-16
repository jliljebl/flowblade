"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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

import gtk

import commands
import dbus
import os
import threading
import time

import appconsts
import dialogutils
import editorpersistance
import editorstate
import guiutils
import utils

_jack_frequencies = [22050, 32000, 44100, 48000, 88200, 96000, 192000]

_jack_failsafe_path = utils.get_hidden_user_dir_path() + "/jack_fail_safe"

_dialog = None

def start_up():
    pass

def use_jack_clicked(window):
    jackstart_thread = JackStartThread(window)
    jackstart_thread.start()


class JackChangeThread(threading.Thread):
    def __init__(self, window):
        threading.Thread.__init__(self)
        self.window = window

class JackStartThread(JackChangeThread):
    def run(self):
        editorstate.PLAYER().jack_output_on()

        time.sleep(1.0)

        gtk.gdk.threads_enter()
        self.window.set_gui_state()
        gtk.gdk.threads_leave()

def frequency_changed(freq_index):
    editorpersistance.prefs.jack_frequency = _jack_frequencies[freq_index]
    editorpersistance.save()

def start_op_changed(w):
    if w.get_active() == True:
        editorpersistance.prefs.jack_start_up_op = appconsts.JACK_ON_START_UP_YES
    else:
        editorpersistance.prefs.jack_start_up_op = appconsts.JACK_ON_START_UP_NO
    editorpersistance.save()

def output_type_changed(output_type):
    editorpersistance.prefs.jack_output_type = output_type
    editorpersistance.save()

def delete_failsafe_file():
    try:
        os.remove(_jack_failsafe_path)
    except:
        pass

class JackAudioManagerDialog:
    def __init__(self):
        self.dialog = gtk.Dialog(_("JACK Audio Manager"), None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (_("Close").encode('utf-8'), gtk.RESPONSE_CLOSE))

        start_up_label = gtk.Label(_("Start JACK output on application start-up"))

        self.startup_check_button = gtk.CheckButton()
        if editorpersistance.prefs.jack_start_up_op == appconsts.JACK_ON_START_UP_YES:
             self.startup_check_button.set_active(True)
        self.startup_check_button.connect("toggled", 
                                      lambda w,e: start_op_changed(w), 
                                      None)
        
        start_row = guiutils.get_checkbox_row_box(self.startup_check_button, start_up_label)
        
        self.frequency_select = gtk.combo_box_new_text()
        cur_value_index = 0
        count = 0
        for freq in _jack_frequencies:
            self.frequency_select.append_text(str(freq))
            if freq == editorpersistance.prefs.jack_frequency:
                cur_value_index = count
            count = count + 1
        self.frequency_select.set_active(cur_value_index)
        self.frequency_select.connect("changed", 
                                      lambda w,e: frequency_changed(w.get_active()), 
                                      None)
                                
        freq_row = guiutils.get_two_column_box_right_pad(gtk.Label("JACK frequency Hz:"), self.frequency_select, 190, 15)

        self.output_type_select = gtk.combo_box_new_text()
        self.output_type_select.append_text(_("Audio"))
        self.output_type_select.append_text(_("Sync Master Timecode"))
        # Indexes correspond with appconsts.JACK_OUT_AUDIO, appconsts.JACK_OUT_SYNC values
        self.output_type_select.set_active(editorpersistance.prefs.jack_output_type)
        self.output_type_select.connect("changed", 
                                      lambda w,e: output_type_changed(w.get_active()), 
                                      None)
                                      
        output_row = guiutils.get_two_column_box_right_pad(gtk.Label("JACK output type:"), self.output_type_select, 190, 15)
        
        vbox_props = gtk.VBox(False, 2)
        vbox_props.pack_start(freq_row, False, False, 0)
        vbox_props.pack_start(output_row, False, False, 0)
        vbox_props.pack_start(start_row, False, False, 0)
        vbox_props.pack_start(guiutils.pad_label(8, 12), False, False, 0)
        
        props_frame = guiutils.get_named_frame(_("Properties"), vbox_props)
        
        self.jack_output_status_value = gtk.Label("<b>OFF</b>")
        self.jack_output_status_value.set_use_markup(True)
        self.jack_output_status_label = gtk.Label("JACK output is ")
        status_row = guiutils.get_centered_box([self.jack_output_status_label, self.jack_output_status_value]) 
    
        self.dont_use_button = gtk.Button(_("Stop JACK Output"))
        self.use_button = gtk.Button(_("Start JACK Output"))

        self.use_button.connect("clicked", lambda w: use_jack_clicked(self))
        self.dont_use_button.connect("clicked", lambda w: _convert_to_original_media_project())

        self.set_gui_state()

        c_box_2 = gtk.HBox(True, 8)
        c_box_2.pack_start(self.dont_use_button, True, True, 0)
        c_box_2.pack_start(self.use_button, True, True, 0)

        row2_onoff = gtk.HBox(False, 2)
        row2_onoff.pack_start(gtk.Label(), True, True, 0)
        row2_onoff.pack_start(c_box_2, False, False, 0)
        row2_onoff.pack_start(gtk.Label(), True, True, 0)

        vbox_onoff = gtk.VBox(False, 2)
        vbox_onoff.pack_start(guiutils.pad_label(12, 4), False, False, 0)
        vbox_onoff.pack_start(status_row, False, False, 0)
        vbox_onoff.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        vbox_onoff.pack_start(row2_onoff, False, False, 0)
        
        onoff_frame = guiutils.get_named_frame(_("Output Status"), vbox_onoff)

        # Pane
        vbox = gtk.VBox(False, 2)
        vbox.pack_start(props_frame, False, False, 0)
        vbox.pack_start(onoff_frame, False, False, 0)

        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(12, 12, 12, 12)
        alignment.add(vbox)

        self.dialog.vbox.pack_start(alignment, True, True, 0)
        dialogutils.default_behaviour(self.dialog)
        self.dialog.connect('response', dialogutils.dialog_destroy)
        self.dialog.show_all()
        
        global _dialog
        _dialog = self

    def set_gui_state(self):
        if editorstate.PLAYER().jack_output_filter != None:
            self.use_button.set_sensitive(False)
            self.dont_use_button.set_sensitive(True)
            self.jack_output_status_value.set_text("<b>ON</b>")
            self.jack_output_status_value.set_use_markup(True)
        else:
            self.dont_use_button.set_sensitive(False)
            self.use_button.set_sensitive(True)
            self.jack_output_status_value.set_text("<b>OFF</b>")
            self.jack_output_status_value.set_use_markup(True)

