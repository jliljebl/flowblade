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



from gi.repository import Gtk, Gdk

import threading
import webbrowser
import time

import appconsts
import dialogs
import dialogutils
import editorpersistance
from editorstate import PROJECT
from editorstate import current_sequence
import editorstate
import gui
import jackaudio
import projectdata
import patternproducer
import profilesmanager
import shortcuts
import respaths

profile_manager_dialog = None

# ---------------------------------------------- recreate icons
class RecreateIconsThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        Gdk.threads_enter()
        recreate_progress_window = dialogs.recreate_icons_progress_dialog()
        time.sleep(0.1)
        Gdk.threads_leave()

        no_icon_path = respaths.IMAGE_PATH + projectdata.FALLBACK_THUMB
        loaded = 0
        for key in PROJECT().media_files.iterkeys():
            media_file = PROJECT().media_files[key]
            Gdk.threads_enter()
            recreate_progress_window.info.set_text(media_file.name)
            Gdk.threads_leave()

            if ((not isinstance(media_file, patternproducer.AbstractBinClip))
                and (not isinstance(media_file, projectdata.BinColorClip))):
                if media_file.type == appconsts.AUDIO:
                    icon_path = respaths.IMAGE_PATH + "audio_file.png"
                    media_file.info = None
                else:
                    (icon_path, length, info) = projectdata.thumbnailer.write_image(media_file.path)
                    media_file.info = info
                media_file.icon_path = icon_path
                media_file.create_icon()

            loaded = loaded + 1
            
            Gdk.threads_enter()
            loaded_frac = float(loaded) / float(len(PROJECT().media_files))
            recreate_progress_window.progress_bar.set_fraction(loaded_frac)
            time.sleep(0.01)
            Gdk.threads_leave()

        # Update editor gui
        Gdk.threads_enter()
        recreate_progress_window.destroy()
        time.sleep(0.3)
        Gdk.threads_leave()
        
        Gdk.threads_enter()
        gui.media_list_view.fill_data_model()
        gui.bin_list_view.fill_data_model()
        gui.enable_save()
        Gdk.threads_leave()

def recreate_media_file_icons():
    recreate_thread = RecreateIconsThread()
    recreate_thread.start()

def show_project_info():
     dialogs.project_info_dialog(gui.editor_window.window, _show_project_info_callback)

def _show_project_info_callback(dialog, response_id):
    dialog.destroy()

def about():
    dialogs.about_dialog(gui.editor_window)

def environment():
    dialogs.environment_dialog(gui.editor_window)
    
def quick_reference():
    try:
        url = "file://" + respaths.HELP_DOC
        print url 
        #webbrowser.open('http://code.google.com/p/flowblade/wiki/FlowbladeReference')
        webbrowser.open(url)
    except:
        dialogutils.info_message(_("Help page not found!"), _("Unfortunately the webresource containing help information\nfor this application was not found."), None)

def profiles_manager():
    global profile_manager_dialog
    profile_manager_dialog = profilesmanager.profiles_manager_dialog()

def edit_watermark():
    dialogs.watermark_dialog(_watermark_add_callback, _watermark_remove_callback)

def _watermark_add_callback(button, dialog, widgets):
    dialogs.watermark_file_dialog(_watermark_file_select_callback, dialog, widgets)

def _watermark_file_select_callback(dialog, response_id, widgets):
    add_button, remove_button, file_path_value_label = widgets
    if response_id == Gtk.ResponseType.ACCEPT:
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
    file_path_value_label.set_text(_("Not Set"))
    current_sequence().remove_watermark()
      
def jack_output_managing():
    dialog = jackaudio.JackAudioManagerDialog()
    #PLAYER().jack_output_on()


def toggle_fullscreen():
    print "toggle_fullscreen"
    if editorstate.fullscreen == False:
       gui.editor_window.window.fullscreen()
       editorstate.fullscreen = True
    else:
       gui.editor_window.window.unfullscreen()
       editorstate.fullscreen = False

def keyboard_shortcuts_callback(dialog, response_id, presets_combo):
    selected_shortcuts_index = presets_combo.get_active()
    dialog.destroy()
    
    if response_id == Gtk.ResponseType.REJECT:
        return
    
    selected_xml = shortcuts.shortcut_files[selected_shortcuts_index]
    if selected_xml == editorpersistance.prefs.shortcuts:
        return

    editorpersistance.prefs.shortcuts = selected_xml
    shortcuts.set_keyboard_shortcuts()
