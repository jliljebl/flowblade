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

import glob
import hashlib
import mlt
import os
import shutil
import threading
import time

from gi.repository import Gtk, Gdk

import app
import appconsts
import atomicfile
#import dialogs
import dialogutils
import editorpersistance
import editorstate
import gui
import guiutils
import jobs
import mltrefhold
import persistance
import render
import renderconsumer
import sequence
import utils
import userfolders

manager_window = None
progress_window = None
proxy_render_issues_window = None

render_thread = None
runner_thread = None
load_thread = None

# These are made to correspond with size selector combobox indexes on manager window
PROXY_SIZE_FULL = appconsts.PROXY_SIZE_FULL
PROXY_SIZE_HALF =  appconsts.PROXY_SIZE_HALF
PROXY_SIZE_QUARTER =  appconsts.PROXY_SIZE_QUARTER


class ProxyRenderItemData:
    def __init__(   self, media_file_id, proxy_w, proxy_h, enc_index, 
                    proxy_file_path, proxy_rate, media_file_path, 
                    proxy_profile_desc, lookup_path):

        self.media_file_id = media_file_id
        self.proxy_w = proxy_w
        self.proxy_h = proxy_h
        self.enc_index = enc_index
        self.proxy_file_path = proxy_file_path
        self.proxy_rate = proxy_rate
        self.media_file_path = media_file_path
        self.proxy_profile_desc = proxy_profile_desc
        self.lookup_path = lookup_path
        
        # We're packing this to go, jobs.py is imported into this module and we wish to not import this into jobs.py
        self.do_auto_re_convert_func = _auto_re_convert_after_proxy_render_in_proxy_mode

    def get_data_as_args_tuple(self):
        args = ("media_file_id:" + str(self.media_file_id), 
                "proxy_w:" + str(self.proxy_w), 
                "proxy_h:" + str(self.proxy_h),
                "enc_index:" + str(self.enc_index),
                "proxy_file_path:" + str(self.proxy_file_path),
                "proxy_rate:"+ str(self.proxy_rate),
                "media_file_path:" + str(self.media_file_path),
                "proxy_profile_desc:" + str(self.proxy_profile_desc),
                "lookup_path:" + str(self.lookup_path).replace(" ", "\ ")) # This is going through Popen shell=True and needs escaped spaces.
            
        return args


class ProxyRenderRunnerThread(threading.Thread):
    def __init__(self, proxy_profile, files_to_render):
        threading.Thread.__init__(self)
        self.proxy_profile = proxy_profile
        self.files_to_render = files_to_render

    def run(self):        

        proxy_w, proxy_h =  _get_proxy_dimensions(self.proxy_profile, editorstate.PROJECT().proxy_data.size)
        enc_index = editorstate.PROJECT().proxy_data.encoding

        proxy_render_items = []
        for media_file in self.files_to_render:
            if media_file.type != appconsts.IMAGE_SEQUENCE:
                
                
                proxy_encoding = renderconsumer.proxy_encodings[enc_index]
                proxy_file_path = media_file.create_proxy_path(proxy_w, proxy_h, proxy_encoding.extension)

                # Bit rates for proxy files are counted using 2500kbs for 
                # PAL size image as starting point.
                pal_pix_count = 720.0 * 576.0
                pal_proxy_rate = 2500.0
                proxy_pix_count = float(proxy_w * proxy_h)
                proxy_rate = pal_proxy_rate * (proxy_pix_count / pal_pix_count)
                proxy_rate = int(proxy_rate / 100) * 100 # Make proxy rate even hundred
                # There are no practical reasons to have bitrates lower than 500kbs.
                if proxy_rate < 500:
                    proxy_rate = 500

                item_data = ProxyRenderItemData(media_file.id, proxy_w, proxy_h, enc_index,
                                                proxy_file_path, proxy_rate, media_file.path,
                                                self.proxy_profile.description(), 
                                                None)
            else:


                asset_folder, asset_file_name = os.path.split(media_file.path)
                lookup_filename = utils.get_img_seq_glob_lookup_name(asset_file_name)
                lookup_path = asset_folder + "/" + lookup_filename

                proxy_file_path = media_file.create_proxy_path(proxy_w, proxy_h, None)
        
                # media_file.path, proxy_file_path, proxy_w, proxy_h, lookup_path
                item_data = ProxyRenderItemData(media_file.id, proxy_w, proxy_h, -1,
                                proxy_file_path, -1, media_file.path,
                                self.proxy_profile.description(),
                                lookup_path)
                
            proxy_render_items.append(item_data)
        
        Gdk.threads_enter()
        
        for proxy_render_data_item in proxy_render_items:
            session_id = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
            job_queue_object = jobs.ProxyRenderJobQueueObject(session_id, proxy_render_data_item)
            job_queue_object.add_to_queue()
            
        Gdk.threads_leave()

    def abort(self):
        render_thread.shutdown()
        self.aborted = True
        self.thread_running = False


class ProxyManagerDialog:
    def __init__(self):
        self.dialog = Gtk.Dialog(_("Proxy Manager"), gui.editor_window.window,
                            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            (_("Close Manager"), Gtk.ResponseType.CLOSE))

        # Encoding
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
            
        self.use_button = Gtk.Button(_("Use Proxy Media"))
        self.dont_use_button = Gtk.Button(_("Use Original Media"))
        self.set_convert_buttons_state()
        self.use_button.connect("clicked", lambda w: _convert_to_proxy_project())
        self.dont_use_button.connect("clicked", lambda w: _convert_to_original_media_project())

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
        vbox.pack_start(panel_encoding, False, False, 0)
        vbox.pack_start(panel_onoff, False, False, 0)

        guiutils.set_margins(vbox, 8, 12, 12, 12)

        self.dialog.vbox.pack_start(vbox, True, True, 0)
        dialogutils.set_outer_margins(self.dialog.vbox)
        
        self.dialog.connect('response', dialogutils.dialog_destroy)
        self.dialog.show_all()

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
                info_label = Gtk.Label(_("<b>Rerendering proxies currently not possible!</b>\nChange to 'Use Original Media' mode to rerender proxies."))
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


# ------------------------------------------------------------- event interface
def show_proxy_manager_dialog():
    global manager_window
    manager_window = ProxyManagerDialog()

def set_menu_to_proxy_state():
    if editorstate.PROJECT().proxy_data.proxy_mode == appconsts.USE_ORIGINAL_MEDIA:
        gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/SaveSnapshot').set_sensitive(True)
    else:
        gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/SaveSnapshot').set_sensitive(False)

def create_proxy_files_pressed(render_all=False):
    media_files = []
    if render_all == False:
        media_file_widgets = gui.media_list_view.get_selected_media_objects()
        if len(media_file_widgets) == 0:
            return
            
        for w in media_file_widgets:
            media_files.append(w.media_file)
    else:
        for item_id in editorstate.PROJECT().media_files:
            media_files.append(editorstate.PROJECT().media_files[item_id])
    
    _do_create_proxy_files(media_files)

def create_proxy_menu_item_selected(media_file):
    media_files = []
    media_files.append(media_file)

    _do_create_proxy_files(media_files)

def _do_create_proxy_files(media_files, retry_from_render_folder_select=False):
    proxy_profile = _get_proxy_profile(editorstate.PROJECT())
    proxy_w, proxy_h =  _get_proxy_dimensions(proxy_profile, editorstate.PROJECT().proxy_data.size)
    proxy_file_extension = _get_proxy_encoding().extension

    files_to_render = []
    not_video_files = 0
    already_have_proxies = []
    is_proxy_file = 0
    other_project_proxies = []
    for f in media_files:
        if f.is_proxy_file == True: # Can't create a proxy file for a proxy file
            is_proxy_file = is_proxy_file + 1
            continue
        if f.type != appconsts.VIDEO and f.type != appconsts.IMAGE_SEQUENCE: # only video files and img seqs can have proxy files
            not_video_files = not_video_files + 1
            continue
        if f.container_data != None:
            not_video_files = not_video_files + 1
            continue
        if f.has_proxy_file == True: # no need to to create proxy files again, unless forced by user
            if os.path.exists(f.second_file_path):
                already_have_proxies.append(f)
                continue
            p_folder, p_file = os.path.split(f.second_file_path)
            if os.path.isdir(p_folder):
                already_have_proxies.append(f)
                continue
                
        path_for_size_and_encoding = f.create_proxy_path(proxy_w, proxy_h, proxy_file_extension)
        if os.path.exists(path_for_size_and_encoding): # A proxy for media file (with these exact settings) has been created by other projects. 
                                                       # Get user to confirm overwrite
            other_project_proxies.append(f)
            continue

        if f.type == appconsts.IMAGE_SEQUENCE:
            p_folder, p_file = os.path.split(path_for_size_and_encoding)
            if os.path.isdir(p_folder):
                other_project_proxies.append(f)
                continue
            
        files_to_render.append(f)

    if  len(already_have_proxies) > 0 or len(other_project_proxies) > 0 or not_video_files > 0 or is_proxy_file > 0 or len(files_to_render) == 0:
        global proxy_render_issues_window
        proxy_render_issues_window = ProxyRenderIssuesWindow(files_to_render, already_have_proxies, 
                                                             not_video_files, is_proxy_file, other_project_proxies,
                                                             proxy_w, proxy_h, proxy_file_extension)
        return

    _create_proxy_files(files_to_render)

def _set_media_files_to_use_unique_proxies(media_files_list):
    for media_file in media_files_list:
        media_file.use_unique_proxy = True
    
def _create_proxy_files(media_files_to_render):
    proxy_profile = _get_proxy_profile(editorstate.PROJECT())

    global runner_thread
    #progress_window = ProxyRenderProgressDialog()
    runner_thread = ProxyRenderRunnerThread(proxy_profile, media_files_to_render)
    runner_thread.start()

# ------------------------------------------------------------------ module functions
def _get_proxy_encoding():
    enc_index = editorstate.PROJECT().proxy_data.encoding
    return renderconsumer.proxy_encodings[enc_index]

def _get_proxy_dimensions(project_profile, proxy_size):
    # Get new dimension that are about half of previous and diviseble by eight
    if proxy_size == PROXY_SIZE_FULL:
        size_mult = 1.0
    elif proxy_size == PROXY_SIZE_HALF:
        size_mult = 0.5
    else: # quarter size
        size_mult = 0.25

    old_width_half = int(project_profile.width() * size_mult)
    old_height_half = int(project_profile.height() * size_mult)
    new_width = old_width_half - old_width_half % 2
    new_height = old_height_half - old_height_half % 2
    return (new_width, new_height)

def _get_proxy_profile(project):
    project_profile = project.profile
    new_width, new_height = _get_proxy_dimensions(project_profile, project.proxy_data.size)
    
    file_contents = "description=" + "proxy render profile" + "\n"
    file_contents += "frame_rate_num=" + str(project_profile.frame_rate_num()) + "\n"
    file_contents += "frame_rate_den=" + str(project_profile.frame_rate_den()) + "\n"
    file_contents += "width=" + str(new_width) + "\n"
    file_contents += "height=" + str(new_height) + "\n"
    file_contents += "progressive=1" + "\n"
    file_contents += "sample_aspect_num=" + str(project_profile.sample_aspect_num()) + "\n"
    file_contents += "sample_aspect_den=" + str(project_profile.sample_aspect_den()) + "\n"
    file_contents += "display_aspect_num=" + str(project_profile.display_aspect_num()) + "\n"
    file_contents += "display_aspect_den=" + str(project_profile.display_aspect_den()) + "\n"

    proxy_profile_path = userfolders.get_cache_dir() + "temp_proxy_profile"
    with atomicfile.AtomicFileWriter(proxy_profile_path, "w") as afw:
        profile_file = afw.get_file()
        profile_file.write(file_contents)

    proxy_profile = mlt.Profile(proxy_profile_path)
    return proxy_profile

def _proxy_render_stopped():
    global progress_window, runner_thread
    progress_window.dialog.destroy()
    gui.media_list_view.widget.queue_draw()
    progress_window = None
    runner_thread = None


# ----------------------------------------------------------- changing proxy modes
def _convert_to_proxy_project():    
    editorstate.PROJECT().proxy_data.proxy_mode = appconsts.CONVERTING_TO_USE_PROXY_MEDIA
    conv_temp_project_path = userfolders.get_cache_dir() + "proxy_conv.flb"
    manager_window.convert_progress_bar.set_text(_("Converting Project to Use Proxy Media"))
    
    mark_in = editorstate.PROJECT().c_seq.tractor.mark_in
    mark_out = editorstate.PROJECT().c_seq.tractor.mark_out
    
    persistance.save_project(editorstate.PROJECT(), conv_temp_project_path)
    global load_thread
    load_thread = ProxyProjectLoadThread(conv_temp_project_path, manager_window.convert_progress_bar, mark_in, mark_out)
    load_thread.start()

def _convert_to_original_media_project():
    editorstate.PROJECT().proxy_data.proxy_mode = appconsts.CONVERTING_TO_USE_ORIGINAL_MEDIA
    conv_temp_project_path = userfolders.get_cache_dir() + "proxy_conv.flb"
    manager_window.convert_progress_bar.set_text(_("Converting to Use Original Media"))

    mark_in = editorstate.PROJECT().c_seq.tractor.mark_in
    mark_out = editorstate.PROJECT().c_seq.tractor.mark_out
    
    persistance.save_project(editorstate.PROJECT(), conv_temp_project_path)
    global load_thread
    load_thread = ProxyProjectLoadThread(conv_temp_project_path, manager_window.convert_progress_bar, mark_in, mark_out)
    load_thread.start()

def _auto_re_convert_after_proxy_render_in_proxy_mode():

    editorstate.project_is_loading = True

    # Save to temp to convert to using original media
    project = editorstate.PROJECT()
    project.proxy_data.proxy_mode = appconsts.CONVERTING_TO_USE_ORIGINAL_MEDIA
    conv_temp_project_path = userfolders.get_cache_dir() + "proxy_conv.flb"
    persistance.save_project(editorstate.PROJECT(), conv_temp_project_path)
    project.proxy_data.proxy_mode = appconsts.USE_ORIGINAL_MEDIA

    # Load saved temp original media project
    persistance.show_messages = False
    project = persistance.load_project(conv_temp_project_path)
    
    # Save to temp to convert back to using proxy media
    project.proxy_data.proxy_mode = appconsts.CONVERTING_TO_USE_PROXY_MEDIA
    persistance.save_project(project, conv_temp_project_path)
    
    # Load saved temp proxy project
    project = persistance.load_project(conv_temp_project_path)
    project.proxy_data.proxy_mode = appconsts.USE_PROXY_MEDIA
        
    editorstate.project_is_loading = False
            
    # Open saved temp project
    app.stop_autosave()

    Gdk.threads_enter()
    app.open_project(project)
    Gdk.threads_leave()

    app.start_autosave()
    
    editorstate.update_current_proxy_paths()
    
    persistance.show_messages = True

def _converting_proxy_mode_done():
    global load_thread
    load_thread = None

    editorstate.update_current_proxy_paths()
    
    manager_window.update_proxy_mode_display()
    gui.media_list_view.widget.queue_draw()
    gui.tline_left_corner.update_gui()
    set_menu_to_proxy_state()
    

class ProxyProjectLoadThread(threading.Thread):

    def __init__(self, proxy_project_path, progressbar, mark_in, mark_out):
        threading.Thread.__init__(self)
        self.proxy_project_path = proxy_project_path
        self.progressbar = progressbar
        self.mark_in = mark_in
        self.mark_out = mark_out
    
    def run(self):
        pulse_runner = guiutils.PulseThread(self.progressbar)
        pulse_runner.start()
        time.sleep(2.0)
        persistance.show_messages = False
        try:
            Gdk.threads_enter()
            project = persistance.load_project(self.proxy_project_path)
            sequence.set_track_counts(project)
            Gdk.threads_leave()
        except persistance.FileProducerNotFoundError as e:
            print("did not find file:", e)

        pulse_runner.running = False
        time.sleep(0.3) # need to be sure pulse_runner has stopped
        
        project.c_seq.tractor.mark_in = self.mark_in
        project.c_seq.tractor.mark_out = self.mark_out
    
        app.stop_autosave()

        Gdk.threads_enter()
        app.open_project(project)
        Gdk.threads_leave()

        # Loaded project has been converted, set proxy mode to correct mode 
        if project.proxy_data.proxy_mode == appconsts.CONVERTING_TO_USE_PROXY_MEDIA:
            project.proxy_data.proxy_mode = appconsts.USE_PROXY_MEDIA
        else:
            project.proxy_data.proxy_mode = appconsts.USE_ORIGINAL_MEDIA

        app.start_autosave()

        global load_thread
        load_thread = None
        persistance.show_messages = True

        Gdk.threads_enter()
        selections = project.get_project_property(appconsts.P_PROP_LAST_RENDER_SELECTIONS)
        if selections != None:
            render.set_saved_gui_selections(selections)
        _converting_proxy_mode_done()
        Gdk.threads_leave()

