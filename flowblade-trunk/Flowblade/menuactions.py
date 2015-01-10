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
This module handles the less central actions inited by user from menu.
"""

import pygtk
pygtk.require('2.0');
import gtk

import platform
import threading
import webbrowser
import time

import appconsts
import dialogs
import dialogutils
from editorstate import PROJECT
from editorstate import PLAYER
from editorstate import current_sequence
import editorstate
import gui
import jackaudio
import mltenv
import mltfilters
import mlttransitions
import projectdata
import patternproducer
import profilesmanager
import renderconsumer
import respaths

profile_manager_dialog = None

# ---------------------------------------------- recreate icons
class RecreateIconsThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        # NEEDS FIXING FOR COMPACT PROJECTS
        gtk.gdk.threads_enter()
        recreate_progress_window = dialogs.recreate_icons_progress_dialog()
        time.sleep(0.1)
        gtk.gdk.threads_leave()

        no_icon_path = respaths.IMAGE_PATH + projectdata.FALLBACK_THUMB
        loaded = 0
        for key in PROJECT().media_files.iterkeys():
            media_file = PROJECT().media_files[key]
            gtk.gdk.threads_enter()
            recreate_progress_window.info.set_text(media_file.name)
            gtk.gdk.threads_leave()

            if ((not isinstance(media_file, patternproducer.AbstractBinClip))
                and (not isinstance(media_file, projectdata.BinColorClip))):
                if media_file.icon_path == no_icon_path:
                    if media_file.type == appconsts.AUDIO:
                        icon_path = respaths.IMAGE_PATH + "audio_file.png"
                    else:
                        (icon_path, length) = projectdata.thumbnailer.write_image(media_file.path)
                    media_file.icon_path = icon_path
                    media_file.create_icon()

            loaded = loaded + 1
            
            gtk.gdk.threads_enter()
            loaded_frac = float(loaded) / float(len(PROJECT().media_files))
            recreate_progress_window.progress_bar.set_fraction(loaded_frac)
            time.sleep(0.01)
            gtk.gdk.threads_leave()

        # Update editor gui
        gtk.gdk.threads_enter()
        recreate_progress_window.destroy()
        time.sleep(0.3)
        gtk.gdk.threads_leave()
        
        gtk.gdk.threads_enter()
        gui.media_list_view.fill_data_model()
        gui.bin_list_view.fill_data_model()
        gui.enable_save()
        gtk.gdk.threads_leave()

def recreate_media_file_icons():
    recreate_thread = RecreateIconsThread()
    recreate_thread.start()

def show_project_info():
     dialogs.project_info_dialog(gui.editor_window.window, _show_project_info_callback)

def _show_project_info_callback(dialog, response_id):
    dialog.destroy()

# ------------------------------------------------------ help menu
def about():
    dialogs.about_dialog(gui.editor_window)

def environment():
    dialogs.environment_dialog(gui.editor_window, write_env_data)

# ----------------------------------------------------- environment data
def write_env_data():
    dialogs.save_env_data_dialog(write_out_env_data_cb)

def write_out_env_data_cb(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        filenames = dialog.get_filenames()
        file_path = filenames[0]
        # Build env data string list
        str_list = []
        str_list.append("FLOWBLADE RUNTIME ENVIROMNMENT\n")
        str_list.append("------------------------------\n")
        str_list.append("\n")
        str_list.append("APPLICATION AND LIBRARIES\n")
        str_list.append("-------------------------\n")
        str_list.append("Application version: " + editorstate.appversion + "\n")
        if editorstate.app_running_from == editorstate.RUNNING_FROM_INSTALLATION:
            run_type = "INSTALLATION"
        else:
            run_type = "DEVELOPER VERSION"
        str_list.append("Application running from: " + run_type + "\n")
        str_list.append("MLT version: " + str(editorstate.mlt_version) + "\n")
        try:
            major, minor, rev = editorstate.gtk_version
            gtk_ver = str(major) + "." + str(minor) + "." + str(rev)
        except:
            gtk_ver = str(editorstate.gtk_version)
        str_list.append("GTK VERSION: " + gtk_ver + "\n")
        str_list.append("SCREEN_HEIGHT: " +  str(editorstate.SCREEN_HEIGHT) + "\n")

        str_list.append("\n")
        str_list.append("PLATFORM\n")
        str_list.append("--------\n")
        str_list.append(platform.platform())

        str_list.append("\n")
        str_list.append("\n")
        str_list.append("FORMATS\n")
        str_list.append("-------\n")
        sorted_formats = sorted(mltenv.formats)
        for f in sorted_formats:
            str_list.append(f + "\n")
        str_list.append("\n")
        str_list.append("\n")
        str_list.append("VIDEO_CODECS\n")
        str_list.append("------------\n")
        sorted_vcodecs = sorted(mltenv.vcodecs)
        for vc in sorted_vcodecs:
            str_list.append(vc + "\n")
        str_list.append("\n")
        str_list.append("\n")
        str_list.append("AUDIO_CODECS\n")
        str_list.append("------------\n")
        sorted_acodecs = sorted(mltenv.acodecs)
        for ac in sorted_acodecs:
            str_list.append(ac + "\n")
        str_list.append("\n")
        str_list.append("\n")
        str_list.append("MLT SERVICES\n")
        str_list.append("------------\n")
        sorted_services = sorted(mltenv.services)
        for s in sorted_services:
            str_list.append(s + "\n")
        str_list.append("\n")
        str_list.append("\n")
        str_list.append("MLT TRANSITIONS\n")
        str_list.append("---------------\n")
        sorted_transitions = sorted(mltenv.transitions)
        for t in sorted_transitions:
            str_list.append(t + "\n")
        str_list.append("\n")
        str_list.append("\n")
        str_list.append("ENCODING OPTIONS\n")
        str_list.append("----------------\n")
        enc_ops = renderconsumer.encoding_options + renderconsumer.not_supported_encoding_options
        for e_opt in enc_ops:
            if e_opt.supported:
                msg = e_opt.name + " AVAILABLE\n"
            else:
                msg = e_opt.name + " NOT AVAILABLE, " + e_opt.err_msg + " MISSING\n"
            str_list.append(msg)
        str_list.append("\n")
        str_list.append("\n")
        str_list.append("MISSING FILTERS\n")
        str_list.append("---------------\n")
        for f in mltfilters.not_found_filters:
            msg = "mlt.Filter " + f.mlt_service_id + " FOR FILTER " + f.name + " NOT FOUND\n"
            str_list.append(msg)
        str_list.append("\n")
        str_list.append("\n")
        str_list.append("MISSING TRANSITIONS\n")
        str_list.append("---------------\n")
        for t in mlttransitions.not_found_transitions:
            msg = "mlt.Transition " + t.mlt_service_id + " FOR TRANSITION " + t.name + " NOT FOUND\n"
            str_list.append(msg)

        # Write out data
        env_text = ''.join(str_list)
        env_file = open(file_path, "w")
        env_file.write(env_text)
        env_file.close()

        dialog.destroy()
    else:
        dialog.destroy()
        
def quick_reference():
    try:
        webbrowser.open('http://code.google.com/p/flowblade/wiki/FlowbladeReference')
    except:
        dialogutils.info_message(_("Help page not found!"), _("Unfortunately the webresource containing help information\nfor this application was not found."), None)

def profiles_manager():
    global profile_manager_dialog
    profile_manager_dialog = profilesmanager.profiles_manager_dialog()

def edit_watermark():
    dialogs.watermark_dialog(_watermark_add_callback, _watermark_remove_callback)

def _watermark_add_callback(button, widgets):
    dialogs.watermark_file_dialog(_watermark_file_select_callback, widgets)

def _watermark_file_select_callback(dialog, response_id, widgets):
    add_button, remove_button, file_path_value_label = widgets
    if response_id == gtk.RESPONSE_ACCEPT:
        filenames = dialog.get_filenames()
        current_sequence().add_watermark(filenames[0])
        add_button.set_sensitive(False)
        remove_button.set_sensitive(True)
        file_path_value_label.set_text(filenames[0])
    
    dialog.destroy()

def _watermark_remove_callback(button, widgets):
    add_button, remove_button, file_path_value_label = widgets
    add_button.set_sensitive(True)
    remove_button.set_sensitive(False)
    file_path_value_label.set_text("Not Set")
    current_sequence().remove_watermark()
      
def jack_output_managing():
    dialog = jackaudio.JackAudioManagerDialog()
    #PLAYER().jack_output_on()
