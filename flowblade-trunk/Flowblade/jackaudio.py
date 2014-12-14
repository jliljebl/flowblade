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

import appconsts
import dialogutils
import editorpersistance
import editorstate
import guiutils
import utils

JACK_RUNNING = 0
PULSEAUDIO_RUNNING = 1
AUDIO_SERVER_UNKNOWN = 3

_audio_server = AUDIO_SERVER_UNKNOWN
_audio_server_names = None
_jack_frequencies = [22050, 32000, 44100, 48000, 88200, 96000, 192000]

_jack_failsafe_path = utils.get_hidden_user_dir_path() + "/jack_fail_safe"

_dialog = None

def start_up():
    global _audio_server_names # translations only work inside functions because initialization order
    _audio_server_names = ["JACK", "Pulseaudio", _("Unknown")]
    
    detect_running_audio_server()
    print _audio_server_names[_audio_server] + " audio server running."

    print editorpersistance.prefs.jack_start_up_op 

    # Do user selected jack start-up operation.
    if editorpersistance.prefs.jack_start_up_op == appconsts.JACK_START_NEVER:
        delete_failsafe_file()
        return

    if editorpersistance.prefs.jack_start_up_op == appconsts.JACK_START_ALWAYS:
        # In case starting JACK always actually crashes application we need to 
        # turn this user preference off after crashes
        if os.path.isfile(_jack_failsafe_path) == True:
            editorpersistance.prefs.jack_start_up_op = appconsts.JACK_START_WHEN_DETECTED
            editorpersistance.save()
            delete_failsafe_file()
            return

        # Write failsafe file to make sure that user doesn't 
        # get always crashing application and can't reach JACK Audio preferences 
        # to change start-up op.
        fail_safe_file = file(_jack_failsafe_path, "wb")
        fail_safe_file.write('jack_audio_failsafe')
        fail_safe_file.close()
    
        editorstate.attach_jackrack = True
        return

    # case: editorpersistance.prefs.jack_start_up_op == JACK_START_WHEN_DETECTED
    if _audio_server == JACK_RUNNING:
        delete_failsafe_file()
        editorstate.attach_jackrack = True

def detect_running_audio_server():
    # This is all very iffy and will fail if we're making wrong assumtions here
    global _audio_server
    if detect_running_jack_server() == True:
        _audio_server = JACK_RUNNING
    elif detect_pulse_audio_process() == True:
         _audio_server = PULSEAUDIO_RUNNING
    else:
         _audio_server = AUDIO_SERVER_UNKNOWN

def detect_running_jack_server():
    # This is hacky
    try:   
        output = commands.getoutput("ps -A")
        if "jackd\n" in output:
            return True
            
        if "jackdbus\n" in output:
            control_status = commands.getoutput("jack_control status")
            if "started" in  control_status:
                return True
    except:
        return False

    return False

def detect_pulse_audio_process():
    # This is hacky.
    # Pulse audio process can be present but not running
    try:   
        output = commands.getoutput("ps aux | grep pulseaudio")
        if "/usr/bin/pulseaudio" in output:
            return True
    except:
        return False

    return False

def delete_failsafe_file():
    try:
        os.remove(_jack_failsafe_path)
    except:
        pass

class JackAudioManagerDialog:
    def __init__(self):
        self.dialog = gtk.Dialog(_("JACK Audio Manager"), None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (_("Close Manager").encode('utf-8'), gtk.RESPONSE_CLOSE))

        detect_op_select = gtk.Label(_("Start-up action:"))
        
        # indexes correspond with values in appconsts.py
        self.detect_op_select = gtk.combo_box_new_text()
        self.detect_op_select.append_text(_("Start JACK output when running JACK Server detected"))
        self.detect_op_select.append_text(_("Never start JACK output"))
        self.detect_op_select.append_text(_("Always start JACK output"))
        self.detect_op_select.set_active(editorpersistance.prefs.jack_start_up_op)
        self.detect_op_select.connect("changed", 
                                lambda w,e: self.start_op_changed(w.get_active()), 
                                None)

        start_row = gtk.HBox(False, 2)
        start_row.pack_start(detect_op_select, False, False, 0)
        start_row.pack_start(guiutils.pad_label(4, 4), False, False, 0)
        start_row.pack_start(self.detect_op_select, False, False, 0)
        start_row.pack_start(gtk.Label(), True, True, 0)
        
        vbox_start = gtk.VBox(False, 2)
        vbox_start.pack_start(start_row, False, False, 0)
        vbox_start.pack_start(guiutils.pad_label(8, 12), False, False, 0)
        
        start_frame = guiutils.get_named_frame(_("Application Start-Up"), vbox_start)
                    
        detect_running_audio_server()
        
        running_server_label = gtk.Label(_("Running audio server:"))
        running_server_value = gtk.Label(_audio_server_names[_audio_server])
        running_row = guiutils.get_two_column_box_right_pad(running_server_label, running_server_value, 190, 15)

        audio_output_label = gtk.Label(_("Audio output:"))
        self.audio_output_value = gtk.Label("MLT Default")
        audio_output_row = guiutils.get_two_column_box_right_pad(audio_output_label, self.audio_output_value, 190, 15)

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
                                lambda w,e: self.frequency_changed(w.get_active()), 
                                None)
                                
        freq_row = guiutils.get_two_column_box_right_pad(gtk.Label("JACK frequency Hz:"), self.frequency_select, 190, 15)
        
        self.convert_progress_bar = gtk.ProgressBar()
        self.convert_progress_bar.set_text(_("Press Button to Change Mode"))
            
        self.use_button = gtk.Button(_("Stop JACK Output and Server"))
        self.dont_use_button = gtk.Button(_("Start JACK Output and Server"))

        self.use_button.connect("clicked", lambda w: _convert_to_proxy_project())
        self.dont_use_button.connect("clicked", lambda w: _convert_to_original_media_project())

        print _audio_server

        if _audio_server == JACK_RUNNING:
            self.dont_use_button.set_sensitive(False)
        else:
            self.use_button.set_sensitive(False)


        c_box_2 = gtk.HBox(True, 8)
        c_box_2.pack_start(self.use_button, True, True, 0)
        c_box_2.pack_start(self.dont_use_button, True, True, 0)

        row2_onoff = gtk.HBox(False, 2)
        row2_onoff.pack_start(gtk.Label(), True, True, 0)
        row2_onoff.pack_start(c_box_2, False, False, 0)
        row2_onoff.pack_start(gtk.Label(), True, True, 0)

        vbox_onoff = gtk.VBox(False, 2)
        vbox_onoff.pack_start(running_row, False, False, 0)
        vbox_onoff.pack_start(guiutils.pad_label(12, 2), False, False, 0)
        vbox_onoff.pack_start(audio_output_row, False, False, 0)
        vbox_onoff.pack_start(freq_row, False, False, 0)
        vbox_onoff.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        vbox_onoff.pack_start(self.convert_progress_bar, False, False, 0)
        vbox_onoff.pack_start(row2_onoff, False, False, 0)
        
        panel_onoff = guiutils.get_named_frame(_("JACK Audio Output"), vbox_onoff)

        # Pane
        vbox = gtk.VBox(False, 2)
        vbox.pack_start(start_frame, False, False, 0)
        vbox.pack_start(panel_onoff, False, False, 0)

        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(12, 12, 12, 12)
        alignment.add(vbox)

        self.dialog.vbox.pack_start(alignment, True, True, 0)
        dialogutils.default_behaviour(self.dialog)
        self.dialog.connect('response', dialogutils.dialog_destroy)
        self.dialog.show_all()
        
        global _dialog
        _dialog = self

    def set_start_stop_buttons_state(self):
        proxy_mode = editorstate.PROJECT().proxy_data.proxy_mode
        if proxy_mode == appconsts.USE_PROXY_MEDIA:
            self.use_button.set_sensitive(False)
            self.dont_use_button.set_sensitive(True)
        else:
            self.use_button.set_sensitive(True)
            self.dont_use_button.set_sensitive(False)
        
    def frequency_changed(self,freq_index):
        editorpersistance.prefs.jack_frequency = _jack_frequencies[freq_index]

    def start_op_changed(self, start_op):
        editorpersistance.prefs.jack_start_up_op = start_op

