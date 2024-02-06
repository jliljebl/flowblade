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
    along with Flowblade Movie Editor.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
This module handles the less central actions inited by user from menu.
"""


from gi.repository import Gtk, GLib

import threading
import webbrowser
import time

import appconsts
import containeractions
import dialogs
import dialogutils
import editorpersistance
from editorstate import PROJECT
from editorstate import current_sequence
import editorstate
import gui
import guicomponents
import guipopover
import projectdata
import patternproducer
import profilesmanager
import shortcuts
import respaths
import workflow

profile_manager_dialog = None

# ---------------------------------------------- recreate icons
class RecreateIconsThread(threading.Thread):
    
    def __init__(self, recreate_progress_window):
        threading.Thread.__init__(self)
        self.recreate_progress_window = recreate_progress_window

    def run(self):
        loaded = 0
        for key in PROJECT().media_files.keys():
            media_file = PROJECT().media_files[key]
            GLib.idle_add(self._progress_window_set_text, media_file)

            if ((not isinstance(media_file, patternproducer.AbstractBinClip))
                and (not isinstance(media_file, projectdata.BinColorClip))):

                if hasattr(media_file, "container_data") and media_file.container_data != None:
                    # Generators
                    if media_file.container_data.container_type == appconsts.CONTAINER_CLIP_FLUXITY:
                        action_object = containeractions.get_action_object(media_file.container_data)
                        media_file.icon_path, media_file.icon = action_object.re_render_screenshot()
                        media_file.container_data.data_slots["icon_file"] = media_file.icon_path
                    else:
                        media_file.icon_path = None
                        media_file.icon = None
                        
                        media_file.create_icon()
                        
                        action_object = containeractions.get_action_object(media_file.container_data)
                        media_file.icon_path = action_object.get_container_thumbnail_path()
                        cr, media_file.icon = action_object.create_image_surface(media_file.icon_path)
                else:
                    # Media files
                    if media_file.type == appconsts.AUDIO:
                        icon_path = respaths.IMAGE_PATH + "audio_file.png"
                        media_file.info = None
                    else:
                        (icon_path, length, info) = projectdata.thumbnailer.write_image(media_file.path)
                        media_file.info = info
                    media_file.icon_path = icon_path
                    media_file.create_icon()

            loaded = loaded + 1

            GLib.idle_add(self._progress_window_update_fraction, loaded)

        GLib.idle_add(self._progress_window_destroy)

        GLib.idle_add(self._exit_update)

    def _progress_window_set_text(self, media_file):
        if self.recreate_progress_window != None:
            self.recreate_progress_window.info.set_text(media_file.name)

    def _progress_window_update_fraction(self, loaded):
        if self.recreate_progress_window != None:
            loaded_frac = float(loaded) / float(len(PROJECT().media_files))
            self.recreate_progress_window.progress_bar.set_fraction(loaded_frac)
            time.sleep(0.01)

    def _progress_window_destroy(self):
        self.recreate_progress_window.destroy()
        self.recreate_progress_window = None
        time.sleep(0.3)
        
    def _exit_update(self):
        gui.media_list_view.fill_data_model()
        gui.bin_list_view.fill_data_model()
        gui.enable_save(PROJECT())
        
def recreate_media_file_icons():
    recreate_progress_window = dialogs.recreate_icons_progress_dialog()
    recreate_thread = RecreateIconsThread(recreate_progress_window)
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
        webbrowser.open(url)
    except:
        dialogutils.info_message(_("Help page not found!"), _("Unfortunately the webresource containing help information\nfor this application was not found."), None)

def quick_reference_web():
    try:
        url = "http://jliljebl.github.io/flowblade/webhelp/help.html"
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
      
def toggle_fullscreen(w=None, e=None):
    if editorpersistance.prefs.global_layout == appconsts.SINGLE_WINDOW:
        if editorstate.fullscreen == False:
           gui.editor_window.window.fullscreen()
           editorstate.fullscreen = True
           gui.editor_window.fullscreen_press.surface = gui.editor_window.fullscreen_press.fullscreen_exit_icon
           gui.editor_window.fullscreen_press.widget.queue_draw()
        else:
           gui.editor_window.window.unfullscreen()
           editorstate.fullscreen = False
           gui.editor_window.fullscreen_press.surface = gui.editor_window.fullscreen_press.fullscreen_icon
           gui.editor_window.fullscreen_press.widget.queue_draw()
    else:
        if gui.editor_window.window.has_toplevel_focus() == True:
            if editorstate.fullscreen == False:
               gui.editor_window.window.fullscreen()
               editorstate.fullscreen = True
            else:
               gui.editor_window.window.unfullscreen()
               editorstate.fullscreen = False
        else:
            if editorstate.fullscreen_second_window == False:
                gui.editor_window.window2.fullscreen()
                editorstate.fullscreen_second_window = True
            else:
                gui.editor_window.window2.unfullscreen()
                editorstate.fullscreen_second_window = False
               
def keyboard_shortcuts_callback(dialog, response_id, presets_combo):
    selected_shortcuts_index = presets_combo.get_active()
    dialog.destroy()
    
    selected_xml = shortcuts.shortcut_files[selected_shortcuts_index]
    if selected_xml == editorpersistance.prefs.shortcuts:
        return

    editorpersistance.prefs.shortcuts = selected_xml
    editorpersistance.save()
    
    shortcuts.set_keyboard_shortcuts()

def keyboard_shortcuts_menu_item_selected_callback(widget, data):

    action, data = data
    if action == "add":
        dialog, entry = dialogutils.get_single_line_text_input_dialog(30, 180, _("Add New Custom Shortcuts Group"), _("Ok"),
                                      _("User Shortcuts Group name:"), "")
        dialog.connect('response', _create_new_kb_shortcuts_group, entry)
        dialog.show_all()
    if action == "delete":
        primary_txt = _("Delete Current User Shortcuts?")
        secondary_txt = _("This operation cannot be undone.")
        shortcuts_combo, dialog = data
        dialogutils.warning_confirmation(_delete_new_kb_shortcuts_group, primary_txt, secondary_txt, dialog)

def _create_new_kb_shortcuts_group(dialog, response_id, entry):
    if response_id != Gtk.ResponseType.CANCEL:
        name = entry.get_text()
        if name == "": # No need for info dialog, user should really get this.
            dialog.destroy()
            return
        custom_xml_file_name = shortcuts.create_custom_shortcuts_xml(name)
        editorpersistance.prefs.shortcuts = custom_xml_file_name
        editorpersistance.save()
        shortcuts.shortcut_files.append(custom_xml_file_name)
        root = shortcuts.get_root()
        shortcuts.shortcut_files_display_names.append(root.get('name'))
        shortcuts.set_keyboard_shortcuts()
        guicomponents.update_shortcuts_combo(dialogs.shortcuts_combo)
        dialogs.display_keyboard_shortcuts(editorpersistance.prefs.shortcuts, workflow.get_tline_tool_working_set(), dialogs.scroll_hold_panel)
        
    dialog.destroy()

def _delete_new_kb_shortcuts_group(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        shortcuts.delete_active_custom_shortcuts_xml()
        shortcuts.set_keyboard_shortcuts()
        guicomponents.update_shortcuts_combo(dialogs.shortcuts_combo)
        dialogs.display_keyboard_shortcuts(editorpersistance.prefs.shortcuts, workflow.get_tline_tool_working_set(), dialogs.scroll_hold_panel)
        
    dialog.destroy()

