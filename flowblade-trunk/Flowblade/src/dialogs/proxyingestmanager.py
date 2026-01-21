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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""
import hashlib
try:
    import mlt7 as mlt
except:
    import mlt
import os
import threading
import time

from gi.repository import Gtk, GLib

import appconsts
import dialogutils
import editorstate
import gui
import guiutils
import jobs
import miscdataobjects
import proxyediting
import renderconsumer

manager_window = None
progress_window = None
proxy_render_issues_window = None


# These are made to correspond with size selector combobox indexes on manager window
PROXY_SIZE_FULL = appconsts.PROXY_SIZE_FULL
PROXY_SIZE_HALF =  appconsts.PROXY_SIZE_HALF
PROXY_SIZE_QUARTER =  appconsts.PROXY_SIZE_QUARTER



# ------------------------------------------------------------- event interface
def show_proxy_manager_dialog():
    global manager_window
    manager_window = ProxyManagerDialog()
    

class ProxyManagerDialog:
    def __init__(self):
        self.dialog = Gtk.Dialog(_("Proxy and Ingest Manager"), gui.editor_window.window,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (_("Close Manager"), Gtk.ResponseType.CLOSE))


        proxy_panel = self.get_proxy_panel()
        ingest_panel = self.get_ingest_panel()

        guiutils.set_margins(proxy_panel, 8, 12, 12, 12)
        guiutils.set_margins(ingest_panel, 8, 12, 12, 12)

        notebook = Gtk.Notebook()
        #notebook.set_size_request(PREFERENCES_WIDTH, PREFERENCES_HEIGHT)
        notebook.append_page(proxy_panel, Gtk.Label(label=_("Proxy Editing")))
        notebook.append_page(ingest_panel, Gtk.Label(label=_("Media Ingest")))
        guiutils.set_margins(notebook, 4, 24, 6, 0)
            
        self.dialog.vbox.pack_start(notebook, True, True, 0)
        dialogutils.set_outer_margins(self.dialog.vbox)
        
        self.dialog.connect('response', dialogutils.dialog_destroy)
        self.dialog.show_all()

    def get_proxy_panel(self):
        # Encoding combo
        self.enc_select = Gtk.ComboBoxText()
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
        # Size combo.
        self.size_select = Gtk.ComboBoxText()
        self.size_select.append_text(_("Project Image Size"))
        self.size_select.append_text(_("Half Project Image Size"))
        self.size_select.append_text(_("Quarter Project Image Size"))
        self.size_select.set_active(editorstate.PROJECT().proxy_data.size)
        self.size_select.connect("changed", 
                                lambda w,e: self.size_changed(w.get_active()), 
                                None)
                                
        row_enc = Gtk.HBox(False, 2)
        row_enc.pack_start(Gtk.Label(), True, True, 0)
        row_enc.pack_start(self.enc_select, False, False, 0)
        row_enc.pack_start(self.size_select, False, False, 0)
        row_enc.pack_start(Gtk.Label(), True, True, 0)
        
        vbox_enc = Gtk.VBox(False, 2)
        vbox_enc.pack_start(row_enc, False, False, 0)
        vbox_enc.pack_start(guiutils.pad_label(8, 12), False, False, 0)
        
        panel_encoding = guiutils.get_named_frame(_("Proxy Encoding"), vbox_enc)

        # Mode
        media_files = editorstate.PROJECT().media_files
        video_files = 0
        proxy_files = 0
        for k, media_file in media_files.items():
            if media_file.type == appconsts.VIDEO:
                video_files = video_files + 1
                if media_file.has_proxy_file == True or media_file.is_proxy_file == True:
                    proxy_files = proxy_files + 1
                    
        proxy_status_label = Gtk.Label(label=_("Proxy Stats:"))
        proxy_status_value = Gtk.Label(label=str(proxy_files) + _(" proxy file(s) for ") + str(video_files) + _(" video file(s)"))
        row_proxy_status = guiutils.get_two_column_box_right_pad(proxy_status_label, proxy_status_value, 150, 150)

        proxy_mode_label = Gtk.Label(label=_("Current Proxy Mode:"))
        self.proxy_mode_value = Gtk.Label()
        self.set_mode_display_value()
               
        row_proxy_mode = guiutils.get_two_column_box_right_pad(proxy_mode_label, self.proxy_mode_value, 150, 150)

        self.info_label = Gtk.Label()

        self.convert_progress_bar = Gtk.ProgressBar()
        self.convert_progress_bar.set_text(_("Press Button to Change Mode"))
            
        self.use_button = Gtk.Button(label=_("Use Proxy Media"))
        self.dont_use_button = Gtk.Button(label=_("Use Original Media"))
        self.set_convert_buttons_state()
        self.use_button.connect("clicked", lambda w: proxyediting.convert_to_proxy_project(self))
        self.dont_use_button.connect("clicked", lambda w: proxyediting.convert_to_original_media_project(self))

        c_box_2 = Gtk.HBox(True, 8)
        c_box_2.pack_start(self.use_button, True, True, 0)
        c_box_2.pack_start(self.dont_use_button, True, True, 0)

        row2_onoff = Gtk.HBox(False, 2)
        row2_onoff.pack_start(Gtk.Label(), True, True, 0)
        row2_onoff.pack_start(c_box_2, False, False, 0)
        row2_onoff.pack_start(Gtk.Label(), True, True, 0)

        vbox_onoff = Gtk.VBox(False, 2)
        vbox_onoff.pack_start(row_proxy_status, False, False, 0)
        vbox_onoff.pack_start(row_proxy_mode, False, False, 0)
        vbox_onoff.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        vbox_onoff.pack_start(self.info_label, False, False, 0)
        vbox_onoff.pack_start(self.convert_progress_bar, False, False, 0)
        vbox_onoff.pack_start(row2_onoff, False, False, 0)

        panel_onoff = guiutils.get_named_frame(_("Project Proxy Mode"), vbox_onoff)

        # Pane
        vbox = Gtk.VBox(False, 2)
        vbox.set_margin_top(12)
        vbox.pack_start(panel_encoding, False, False, 0)
        vbox.pack_start(panel_onoff, False, False, 0)

        return vbox

    def get_ingest_panel(self):

        if editorstate.PROJECT().ingest_data == None:
            editorstate.PROJECT().ingest_data = miscdataobjects.IngestTranscodeData()
            
        # Encoding combo
        self.ingest_enc_select = Gtk.ComboBoxText()
        encodings = renderconsumer.ingest_encodings
        if len(encodings) < 1: # no encoding options available, system does not have right codecs
            editorstate.PROJECT().ingest_data.set_default_encoding(miscdataobjects.INGEST_ENCODING_NOT_SET)
            self.ingest_enc_select.append_text(_("No Encoding Options Available"))
        else:
            if editorstate.PROJECT().ingest_data.get_default_encoding() == miscdataobjects.INGEST_ENCODING_NOT_SET:
                # Environment has changed so that ingest encodigns are now available.
                editorstate.PROJECT().ingest_data.set_default_encoding(0)
                
            for enc in encodings:
                self.ingest_enc_select.append_text(enc.name)
        
                current_enc = editorstate.PROJECT().ingest_data.get_default_encoding()
                if current_enc >= len(encodings): # current encoding selection not available
                    current_enc = 0
                    editorstate.PROJECT().ingest_data.set_default_encoding(0)

                self.ingest_enc_select.set_active(current_enc)
                self.ingest_enc_select.connect("changed", 
                                        lambda w,e: self.ingest_encoding_changed(w.get_active()), 
                                        None)

        row_enc = Gtk.HBox(False, 2)
        row_enc.pack_start(self.ingest_enc_select, False, False, 0)
        row_enc.pack_start(Gtk.Label(), True, True, 0)
        
        panel_encoding = guiutils.get_named_frame(_("Ingest Optimized Transcode"), row_enc)

        self.ingest_action_select = Gtk.ComboBoxText()
        self.ingest_action_select.append_text(_("No Action"))
        self.ingest_action_select.append_text(_("Ingest Copy"))
        self.ingest_action_select.append_text(_("Ingest Optimized Transcode"))

        self.ingest_action_select.set_active(editorstate.PROJECT().ingest_data.get_action())
        self.ingest_action_select.connect(  "changed", 
                                            lambda w,e: self.ingest_action_changed(w.get_active()), 
                                            None)

        row_action = Gtk.HBox(False, 2)
        row_action.pack_start(self.ingest_action_select, False, False, 0)
        row_action.pack_start(Gtk.Label(), True, True, 0)
        
        panel_action = guiutils.get_named_frame(_("Media Add Ingest Action"), row_action)
        panel_action.set_margin_top(24)

        vbox = Gtk.VBox(False, 2)
        vbox.set_margin_top(12)
        vbox.pack_start(panel_encoding, False, False, 0)
        vbox.pack_start(panel_action, False, False, 0)

        return vbox
        
    def set_convert_buttons_state(self):
        proxy_mode = editorstate.PROJECT().proxy_data.proxy_mode
        if jobs.proxy_render_ongoing() == True:
            self.use_button.set_sensitive(False)
            self.dont_use_button.set_sensitive(False)
            self.info_label.set_text(_("There are on going Proxy renders, changing Proxy Mode not allowed."))
        elif proxy_mode == appconsts.USE_PROXY_MEDIA:
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

    def ingest_encoding_changed(self, enc_index):
        editorstate.PROJECT().ingest_data.set_default_encoding(enc_index)

    def ingest_action_changed(self, action):
        editorstate.PROJECT().ingest_data.set_action(action)

    def size_changed(self, size_index):
        editorstate.PROJECT().proxy_data.size = size_index

    def update_proxy_mode_display(self):
        self.set_convert_buttons_state()
        self.set_mode_display_value()
        self.convert_progress_bar.set_fraction(0.0)


class ProxyRenderIssuesWindow:
    def __init__(self, files_to_render, already_have_proxies, not_video_files, is_proxy_file, 
                 other_project_proxies, proxy_w, proxy_h, proxy_file_extension):
        dialog_title =_("Proxy Render Info")
        
        self.files_to_render = files_to_render
        self.other_project_proxies = other_project_proxies
        self.already_have_proxies = already_have_proxies
        self.proxy_w = proxy_w
        self.proxy_h = proxy_h
        self.proxy_file_extension = proxy_file_extension

        self.issues = 1
        if (len(files_to_render) + len(already_have_proxies) + len(other_project_proxies)) == 0 and not_video_files > 0:
            self.dialog = Gtk.Dialog(dialog_title,
                                     gui.editor_window.window,
                                     Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                     (_("Close"), Gtk.ResponseType.CLOSE))
            info_box = dialogutils.get_warning_message_dialog_panel(_("Nothing will be rendered"), 
                                                                      _("No video files were selected.\nOnly video files can have proxy files."),
                                                                      True)
            self.dialog.connect('response', dialogutils.dialog_destroy)
        else:
            self.dialog = Gtk.Dialog(dialog_title,
                                     gui.editor_window.window,
                                     Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                     (_("Cancel"), Gtk.ResponseType.CANCEL,
                                      _("Do Render Action" ), Gtk.ResponseType.OK))
            self.dialog.connect('response', self.response)

            rows = ""
            if len(already_have_proxies) > 0 and len(other_project_proxies) > 0:
                text = _("Proxies exist that were created by this and other projects for ") + str(len(already_have_proxies) + len(other_project_proxies)) + _(" file(s).\n")
                rows = rows + self.issues_str() + text
            elif len(already_have_proxies) > 0 and len(other_project_proxies) == 0:
                text = _("Proxies have already been created for ") + str(len(already_have_proxies)) + _(" file(s).\n")
                rows = rows + self.issues_str() + text
            elif  len(other_project_proxies) > 0:
                text = _("Proxies exist that were created by other projects for ") + str(len(other_project_proxies)) + _(" file(s).\n")
                rows = rows + self.issues_str() + text
            if not_video_files > 0:
                text = _("You are trying to create proxies for ") + str(not_video_files) + _(" non-video file(s).\n")
                rows = rows + self.issues_str() + text
            if is_proxy_file > 0:
                text = _("You are trying to create proxies for ") + str(not_video_files) + _(" proxy file(s).\n")
                rows = rows + self.issues_str() + text
            issues_box = dialogutils.get_warning_message_dialog_panel(_("There are some issues with proxy render request"), 
                                                                    rows,
                                                                    True)
  
            proxy_mode = editorstate.PROJECT().proxy_data.proxy_mode
            if proxy_mode == appconsts.USE_PROXY_MEDIA:
                info_label = Gtk.Label(label=_("<b>Rerendering proxies currently not possible!</b>\nChange to 'Use Original Media' mode to rerender proxies."))
                info_label.set_use_markup(True)
                info_row = guiutils.get_left_justified_box([guiutils.get_pad_label(24, 10), info_label])

            self.action_select = Gtk.ComboBoxText()

            self.action_select.append_text(_("Render Unrendered Possible & Use existing"))
            if proxy_mode != appconsts.USE_PROXY_MEDIA:
                self.action_select.append_text(_("Rerender All Possible" ))
            self.action_select.set_active(0)
                            
            action_row = guiutils.get_left_justified_box([guiutils.get_pad_label(24, 10), Gtk.Label(label=_("Select Render Action: ")), self.action_select])

            info_box = Gtk.VBox()
            info_box.pack_start(issues_box, False, False, 0)
            if proxy_mode == appconsts.USE_PROXY_MEDIA:
                info_box.pack_start(info_row, False, False, 0)
                info_box.pack_start(guiutils.get_pad_label(12, 24), False, False, 0)
            info_box.pack_start(action_row, False, False, 0)

        guiutils.set_margins(info_box, 12, 48, 12, 0)
        self.dialog.vbox.pack_start(info_box, True, True, 0)
        dialogutils.set_outer_margins(self.dialog.vbox)
        self.dialog.show_all()

    def issues_str(self):
        issue_str = str(self.issues) + ") "
        self.issues = self.issues + 1
        return issue_str

    def response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.CANCEL:
            dialog.destroy()
        else:
            if self.action_select.get_active() == 0: # Render Unrendered Possible & Use existing
                for f in self.other_project_proxies:
                    f.add_existing_proxy_file(self.proxy_w, self.proxy_h, self.proxy_file_extension)
                    if editorstate.PROJECT().proxy_data.proxy_mode == appconsts.USE_PROXY_MEDIA:
                        f.set_as_proxy_media_file()
        
            else: # Rerender All Possible
                # We can't mess existing proxy files that are used by other projects
                _set_media_files_to_use_unique_proxies(self.other_project_proxies)
                _set_media_files_to_use_unique_proxies(self.already_have_proxies)
                # Add to files being rendered
                self.files_to_render.extend(self.other_project_proxies)
                self.files_to_render.extend(self.already_have_proxies)
            dialog.destroy()

            global proxy_render_issues_window
            proxy_render_issues_window = None
        
            _create_proxy_files(self.files_to_render)


