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

import appconsts
import dialogutils
import editorstate
import guiutils

_dialog = None

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

def detect_running_pulse_audio():
    # This is hacky
    try:   
        output = commands.getoutput("ps aux | grep pulseaudio")
        if "/usr/bin/pulseaudio" in output:
            return True
    except:
        return False

    return False


class JackAudioManagerDialog:
    def __init__(self):
        self.dialog = gtk.Dialog(_("JACK Audio Manager"), None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (_("Close Manager").encode('utf-8'), gtk.RESPONSE_CLOSE))

        """
        # Encoding
        self.enc_select = gtk.combo_box_new_text()
        encodings = renderconsumer.proxy_encodings
        if len(encodings) < 1: # no encoding options available, system does not have right codecs
            # display info
            pass
        for encoption in encodings:
            self.enc_select.append_text(encoption.name)
            
        current_enc = editorstate.PROJECT().proxy_data.encoding
        if current_enc >= len(encodings): # current encoding selection not available
            current_enc = 0
            editorstate.PROJECT().proxy_data.encoding = 0
        self.enc_select.set_active(current_enc)
        self.enc_select.connect("changed", 
                                lambda w,e: self.encoding_changed(w.get_active()), 
                                None)
        """
        detect_op_select = gtk.Label(_("JACK start-up action:"))
                           
        self.detect_op_select = gtk.combo_box_new_text()
        self.detect_op_select.append_text(_("Start JACK output when running JACK Server detected"))
        self.detect_op_select.append_text(_("Never start JACK output"))
        self.detect_op_select.append_text(_("Always start JACK output"))
        self.detect_op_select.set_active(0)
        self.detect_op_select.connect("changed", 
                                lambda w,e: self.size_changed(w.get_active()), 
                                None)
        
        start_row = gtk.HBox(False, 2)
        start_row.pack_start(detect_op_select, False, False, 0)
        start_row.pack_start(self.detect_op_select, False, False, 0)
        start_row.pack_start(gtk.Label(), True, True, 0)
        
        #row_enc = gtk.HBox(False, 2)
        #row_enc.pack_start(gtk.Label(), True, True, 0)
        #row_enc.pack_start(self.enc_select, False, False, 0)
        #row_enc.pack_start(self.detect_op_select, False, False, 0)
        #row_enc.pack_start(gtk.Label(), True, True, 0)
        
        vbox_start = gtk.VBox(False, 2)
        vbox_start.pack_start(start_row, False, False, 0)
        vbox_start.pack_start(guiutils.pad_label(8, 12), False, False, 0)
        
        panel_encoding = guiutils.get_named_frame(_("Application start-up"), vbox_start)

        # Mode
        media_files = editorstate.PROJECT().media_files
        video_files = 0
        proxy_files = 0
        for k, media_file in media_files.iteritems():
            if media_file.type == appconsts.VIDEO:
                video_files = video_files + 1
                if media_file.has_proxy_file == True or media_file.is_proxy_file == True:
                    proxy_files = proxy_files + 1
                    
        if detect_running_pulse_audio() == True:
            audio_server = "Pulseaudio"
        elif detect_running_jack_server() == True:
            audio_server = "JACK"
        else:
            audio_server = "Unknown"
        
        proxy_status_label = gtk.Label(_("Running Audio Server:"))
        proxy_status_value = gtk.Label(audio_server)
        row_proxy_status = guiutils.get_two_column_box_right_pad(proxy_status_label, proxy_status_value, 150, 150)


        proxy_mode_label = gtk.Label(_("Audio output:"))
        self.proxy_mode_value = gtk.Label("MLT Default")
        
        row_proxy_mode = guiutils.get_two_column_box_right_pad(proxy_mode_label, self.proxy_mode_value, 150, 150)


        self.frequency_select = gtk.combo_box_new_text()
        self.frequency_select.append_text("44100Hz")
        self.frequency_select.append_text("48000Hz")
        self.frequency_select.set_active(0)
        freq_row = guiutils.get_two_column_box_right_pad(gtk.Label("JACK Frequency:"), self.frequency_select, 150, 150)
        
        self.convert_progress_bar = gtk.ProgressBar()
        self.convert_progress_bar.set_text(_("Press Button to Change Mode"))
            
        self.use_button = gtk.Button(_("Stop JACK Output and Server"))
        self.dont_use_button = gtk.Button(_("Start JACK Output and Server"))
        #self.set_convert_buttons_state()
        self.use_button.connect("clicked", lambda w: _convert_to_proxy_project())
        self.dont_use_button.connect("clicked", lambda w: _convert_to_original_media_project())

        c_box_2 = gtk.HBox(True, 8)
        c_box_2.pack_start(self.use_button, True, True, 0)
        c_box_2.pack_start(self.dont_use_button, True, True, 0)

        row2_onoff = gtk.HBox(False, 2)
        row2_onoff.pack_start(gtk.Label(), True, True, 0)
        row2_onoff.pack_start(c_box_2, False, False, 0)
        row2_onoff.pack_start(gtk.Label(), True, True, 0)

        vbox_onoff = gtk.VBox(False, 2)
        vbox_onoff.pack_start(row_proxy_status, False, False, 0)
        vbox_onoff.pack_start(row_proxy_mode, False, False, 0)
        vbox_onoff.pack_start(freq_row, False, False, 0)
        vbox_onoff.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        vbox_onoff.pack_start(self.convert_progress_bar, False, False, 0)
        vbox_onoff.pack_start(row2_onoff, False, False, 0)
        
        panel_onoff = guiutils.get_named_frame(_("JACK Audio Output"), vbox_onoff)

        # Pane
        vbox = gtk.VBox(False, 2)
        vbox.pack_start(panel_encoding, False, False, 0)
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

    def set_convert_buttons_state(self):
        proxy_mode = editorstate.PROJECT().proxy_data.proxy_mode
        if proxy_mode == appconsts.USE_PROXY_MEDIA:
            self.use_button.set_sensitive(False)
            self.dont_use_button.set_sensitive(True)
        else:
            self.use_button.set_sensitive(True)
            self.dont_use_button.set_sensitive(False)

    def set_mode_display_value(self):
        if editorstate.PROJECT().proxy_data.proxy_mode == appconsts.USE_PROXY_MEDIA:
            mode_str = _("Using Proxy Media")
        else:
            mode_str = _("Using Original Media")
        self.proxy_mode_value.set_text(mode_str)
        
    def encoding_changed(self, enc_index):
        editorstate.PROJECT().proxy_data.encoding = enc_index

    def size_changed(self, size_index):
        editorstate.PROJECT().proxy_data.size = size_index

    def update_proxy_mode_display(self):
        self.set_convert_buttons_state()
        self.set_mode_display_value()
        self.convert_progress_bar.set_text(_("Press Button to Change Mode"))
        self.convert_progress_bar.set_fraction(0.0)
