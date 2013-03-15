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

import gtk
import os
import platform
import threading
import webbrowser
import time

import appconsts
import editorpersistance
import dialogs
import dialogutils
from editorstate import PROJECT
import editorstate
import gui
import mltprofiles
import mltenv
import mltfilters
import mlttransitions
import panels
import patternproducer
import projectdata
import render
import renderconsumer
import respaths
import useraction
import utils

profile_manager_dialog = None

# ---------------------------------------------- recreate icons
class RecreateIconsThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):

        gtk.gdk.threads_enter()
        recreate_progress_window = dialogs.get_recreate_icons_progress_dialog()
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
                        (icon_path, length) = projectdata.thumbnail_thread.write_image(media_file.path)
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
        useraction._enable_save()
        
        gtk.gdk.threads_leave()


def recreate_media_file_icons():
    recreate_thread = RecreateIconsThread()
    recreate_thread.start()


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
        enc_msgs = []
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
        dialogutils.info_message("Help page not found!", "Unfortunately the webresource containing help information\nfor this application was not found.", None)


# --------------------------------------------------- profiles manager
def profiles_manager():
    callbacks = (_profiles_manager_load_values_clicked, _profiles_manager_save_profile_clicked,
                 _profiles_manager_delete_user_profiles_clicked, _profiles_manager_hide_profiles_clicked,
                 _profiles_manager_unhide_profiles_clicked)

    global profile_manager_dialog
    profile_manager_dialog = dialogs.profiles_manager_dialog(callbacks)

def _profiles_manager_load_values_clicked(widgets):
    load_profile_combo, description, f_rate_num, f_rate_dem, width, height, \
    s_rate_num, s_rate_dem, d_rate_num, d_rate_dem, progressive = widgets
    
    profile = mltprofiles.get_profile_for_index(load_profile_combo.get_active())
    panels.fill_new_profile_panel_widgets(profile, widgets)

def _profiles_manager_save_profile_clicked(widgets, user_profiles_view):
    load_profile_combo, description, f_rate_num, f_rate_dem, width, height, \
    s_rate_num, s_rate_dem, d_rate_num, d_rate_dem, progressive = widgets

    profile_file_name = description.get_text().lower().replace(os.sep, "_").replace(" ","_")
    
    file_contents = "description=" + description.get_text() + "\n"
    file_contents += "frame_rate_num=" + f_rate_num.get_text() + "\n"
    file_contents += "frame_rate_den=" + f_rate_dem.get_text() + "\n"
    file_contents += "width=" + width.get_text() + "\n"
    file_contents += "height=" + height.get_text() + "\n"
    if progressive.get_active() == True:
        prog_val = "1"
    else:
        prog_val = "0"
    file_contents += "progressive=" + prog_val + "\n"
    file_contents += "sample_aspect_num=" + s_rate_num.get_text() + "\n"
    file_contents += "sample_aspect_den=" + s_rate_dem.get_text() + "\n"
    file_contents += "display_aspect_num=" + d_rate_num.get_text() + "\n"
    file_contents += "display_aspect_den=" + d_rate_dem.get_text() + "\n"

    profile_path = utils.get_hidden_user_dir_path() + mltprofiles.USER_PROFILES_DIR + profile_file_name
    
    if os.path.exists(profile_path):
        dialogutils.warning_message("Profile '" +  description.get_text() + "' already exists!", \
                                "Delete profile and save again.",  gui.editor_window.window)
        return

    profile_file = open(profile_path, "w")
    profile_file.write(file_contents)
    profile_file.close()

    dialogutils.info_message("Profile '" +  description.get_text() + "' saved.", \
                 "You can now create a new project using the new profile.", gui.editor_window.window)
    
    mltprofiles.load_profile_list()
    render.reload_profiles()
    user_profiles_view.fill_data_model(mltprofiles.get_user_profiles())


def _profiles_manager_delete_user_profiles_clicked(user_profiles_view):
    delete_indexes = user_profiles_view.get_selected_indexes_list()
    if len(delete_indexes) == 0:
        return

    primary_txt = _("Confirm user profile delete")
    secondary_txt = _("This operation cannot be undone.") 
    
    dialogutils.warning_confirmation(_profiles_delete_confirm_callback, primary_txt, \
                                 secondary_txt, gui.editor_window.window, \
                                (user_profiles_view, delete_indexes))

def _profiles_delete_confirm_callback(dialog, response_id, data):
    if response_id != gtk.RESPONSE_ACCEPT:
        dialog.destroy()
        return

    user_profiles_view, delete_indexes = data
    for i in delete_indexes:
        pname, profile = mltprofiles.get_user_profiles()[i]
        profile_file_name = pname.lower().replace(os.sep, "_").replace(" ","_")
        profile_path = utils.get_hidden_user_dir_path() + mltprofiles.USER_PROFILES_DIR + profile_file_name
        print profile_path
        try:
            os.remove(profile_path)
        except:
            # This really should not happen
            print "removed user profile already gone ???"

    mltprofiles.load_profile_list()
    user_profiles_view.fill_data_model(mltprofiles.get_user_profiles())
    dialog.destroy()

def _profiles_manager_hide_profiles_clicked(visible_view, hidden_view):
    visible_indexes = visible_view.get_selected_indexes_list()
    prof_names = []
    default_profile = mltprofiles.get_default_profile()
    for i in visible_indexes:
        pname, profile = mltprofiles.get_factory_profiles()[i]
        if profile == default_profile:
            dialogutils.warning_message("Can't hide default Profile", 
                                    "Profile '"+ profile.description() + "' is default profile and can't be hidden.", 
                                    profile_manager_dialog)
            return
        prof_names.append(pname)

    editorpersistance.prefs.hidden_profile_names += prof_names
    editorpersistance.save()

    mltprofiles.load_profile_list()
    visible_view.fill_data_model(mltprofiles.get_factory_profiles())
    hidden_view.fill_data_model(mltprofiles.get_hidden_profiles())

def _profiles_manager_unhide_profiles_clicked(visible_view, hidden_view):
    hidden_indexes = hidden_view.get_selected_indexes_list()
    prof_names = []
    default_profile = mltprofiles.get_default_profile()
    for i in hidden_indexes:
        pname, profile = mltprofiles.get_hidden_profiles()[i]
        prof_names.append(pname)
    
    editorpersistance.prefs.hidden_profile_names = list(set(editorpersistance.prefs.hidden_profile_names) - set(prof_names))
    editorpersistance.save()
    
    mltprofiles.load_profile_list()
    visible_view.fill_data_model(mltprofiles.get_factory_profiles())
    hidden_view.fill_data_model(mltprofiles.get_hidden_profiles())


# ------------------------------------------------------- preferences
def display_preferences():
    dialogs.preferences_dialog(_preferences_dialog_callback, _thumbs_select_clicked)

def _thumbs_select_clicked(widget):
    dialogs.select_thumbnail_dir(useraction.select_thumbnail_dir_callback, gui.editor_window.window, editorpersistance.prefs.thumbnail_folder, False)

def _preferences_dialog_callback(dialog, response_id, all_widgets):
    if response_id == gtk.RESPONSE_ACCEPT:
        editorpersistance.update_prefs_from_widgets(all_widgets)
        editorpersistance.save()
        dialog.destroy()
        primary_txt = _("Restart required for some setting changes to take effect.")
        secondary_txt = _("If requested change is not in effect, restart application.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    dialog.destroy()
