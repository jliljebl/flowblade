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

from gi.repository import Gtk, Gdk

import copy
import hashlib
import json
import os
import subprocess
import threading
import time

import appconsts
import containerprogramedit
import containeractions
import dialogs
import dialogutils
import editorstate
from editorstate import PROJECT
import gui
import guicomponents
import guiutils
import respaths
import userfolders
import utils

_blender_available = False

ROW_WIDTH = 300
FALLBACK_THUMB = "fallback_thumb.png"

class ContainerClipData:
    
        def __init__(self, container_type, program, unrendered_media):
            self.container_clip_uid = -1 # This is set at clip creation time.

            self.container_type = container_type
            self.program = program

            self.rendered_media = None
            self.rendered_media_range_in = -1
            self.rendered_media_range_out = -1
            self.last_render_type = containeractions.FULL_RENDER
            
            self.unrendered_media = unrendered_media
            self.unrendered_length = None
            # This gets set later for some container types
            if unrendered_media != None:
                self.unrendered_type = utils.get_media_type(unrendered_media)
            else:
                self.unrendered_type = None

            self.external_media_folder = None

            self.render_data = None # initialized to a toolsencoding.ToolsRenderData object later.
            
            # Some container clips need to save additional information gathered on init.
            self.data_slots = {}
            
            self.editable = False
                
        def get_program_name(self):
            directory, file_name = os.path.split(self.program)
            name, ext = os.path.splitext(file_name)
            return name

        def get_unrendered_media_name(self):
            directory, file_name = os.path.split(self.unrendered_media)
            name, ext = os.path.splitext(file_name)
            return name
        
        def get_rendered_thumbnail(self):
            action_object = containeractions.get_action_object(self)
            return action_object.get_rendered_thumbnail()

        def generate_clip_id(self):
            self.container_clip_uid = os.urandom(16)

        def clear_rendered_media(self):
            self.rendered_media = None
            self.rendered_media_range_in = -1
            self.rendered_media_range_out = -1
        

# ------------------------------------------------------- testing availebility on statrt up
def test_blender_availebility():
    global _blender_available
    if os.path.exists("/usr/bin/blender") == True:
        _blender_available = True
    elif editorstate.app_running_from == editorstate.RUNNING_FROM_FLATPAK:
        _blender_available = False
        """ Work o0n this continues for 2.8
        command_list = ["flatpak-spawn", "--host", "flatpak", "info","org.blender.Blender"]
        p = subprocess.Popen(command_list, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1)
        p.wait(timeout=3)
        
        if p.returncode == 0: # If not present we get returncode==1
            _blender_available = True
        """
def blender_available():
    return _blender_available
            

# -------------------------------------------------------- Clip menu actions
def render_full_media(data):
    clip, track, item_id, item_data = data
    action_object = containeractions.get_action_object(clip.container_data)
    action_object.render_full_media(clip)

def render_clip_length(data):
    clip, track, item_id, item_data = data
    action_object = containeractions.get_action_object(clip.container_data)
    action_object.render_clip_length_media(clip)
    
def switch_to_unrendered_media(data):
    clip, track, item_id, item_data = data
    action_object = containeractions.get_action_object(clip.container_data)
    action_object.switch_to_unrendered_media(clip)

def set_render_settings(data):
    clip, track, item_id, item_data = data
    action_object = containeractions.get_action_object(clip.container_data)
    action_object.set_video_endoding(clip)

def edit_program(data):
    clip, track, item_id, item_data = data
    action_object = containeractions.get_action_object(clip.container_data)
    action_object.edit_program(clip)




#------------------------------------------------------------- Cloning
def clone_clip(clip):
    action_object = containeractions.get_action_object(clip.container_data)
    return action_object.clone_clip(clip)


# ------------------------------------------------------------ GUI
def _get_file_select_row_and_editor(label_text, file_filter=None, title=None):
    if title == None:
        title = _("Select A File")
    file_chooser = Gtk.FileChooserButton.new(title, Gtk.FileChooserAction.OPEN)
    file_chooser.set_size_request(250, 25)
    file_chooser.set_current_folder(os.path.expanduser("~") + "/")

    if file_filter != None:
        file_chooser.add_filter(file_filter)

    row = guiutils.get_two_column_box(Gtk.Label(label=label_text), file_chooser, ROW_WIDTH)
    return (file_chooser, row)

def _open_rows_dialog(callback, title, rows, data):
    parent_window = gui.editor_window.window
    cancel_str = _("Cancel")
    ok_str = _("Ok")
    dialog = Gtk.Dialog(title,
                        parent_window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (cancel_str, Gtk.ResponseType.CANCEL,
                        ok_str, Gtk.ResponseType.ACCEPT))

    vbox = Gtk.VBox(False, 2)
    for row in rows:
        vbox.pack_start(row, False, False, 0)

    dialog.info_label = Gtk.Label()
    vbox.pack_start(dialog.info_label, False, False, 0)

    alignment = dialogutils.get_alignment2(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    dialog.connect('response', callback, data)
    dialog.show_all()

def _update_gui_for_media_object_add():
    gui.media_list_view.fill_data_model()
    gui.bin_list_view.fill_data_model()


def _show_not_all_data_info():
    dialogutils.info_message(_("Not all required files were defined"), _("Select all files asked for in dialog for succesful Container Clip creation."), gui.editor_window.window)
        
        

# -------------------------------------------------------- MEDIA ITEM CREATION
# --- G'Mic
def create_gmic_media_item():
    script_select, row1 = _get_file_select_row_and_editor(_("G'Mic Tool Script:"), None, _("Select G'Mic Tool Script"))
    media_file_select, row2 = _get_file_select_row_and_editor(_("Video Clip:"))
    _open_rows_dialog(_gmic_clip_create_dialog_callback, _("Create G'Mic Script Container Clip"), [row1, row2], [script_select, media_file_select])

def _gmic_clip_create_dialog_callback(dialog, response_id, data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
    else:
        script_select, media_file_select = data
        script_file = script_select.get_filename()
        media_file = media_file_select.get_filename()

        if script_file == None or media_file == None:
            dialog.destroy()
            _show_not_all_data_info()
            return

        container_clip_data = ContainerClipData(appconsts.CONTAINER_CLIP_GMIC, script_file, media_file)
        
        dialog.info_label.set_text("Test Render to validate script...")
        
        # We need to exit this Gtk callback to get info text above updated.
        completion_thread = GMicLoadCompletionThread(container_clip_data, dialog)
        completion_thread.start()


class GMicLoadCompletionThread(threading.Thread):
    
    def __init__(self, container_clip_data, dialog):
        self.container_clip_data = container_clip_data
        self.dialog = dialog

        threading.Thread.__init__(self)
        
    def run(self):
        
        action_object = containeractions.get_action_object(self.container_clip_data)
        is_valid, err_msg = action_object.validate_program()

        time.sleep(0.5) # To make sure text is seen.

        Gdk.threads_enter()

        self.dialog.destroy()
        
        if is_valid == True:
            container_clip = ContainerClipMediaItem(PROJECT().next_media_file_id, self.container_clip_data.get_unrendered_media_name(), self.container_clip_data)
            PROJECT().add_container_clip_media_object(container_clip)
            _update_gui_for_media_object_add()
        else:
            primary_txt = _("G'Mic Container Clip Validation Error")
            dialogutils.warning_message(primary_txt, err_msg, gui.editor_window.window)
            
        Gdk.threads_leave()
        
# --- Fluxity
def create_fluxity_media_item():
    script_select, row1 = _get_file_select_row_and_editor(_("Flowblade Media Plugin Script:"), None, _("Flowblade Media Plugin Script"))
    #media_file_select, row2 = _get_file_select_row_and_editor(_("Video Clip:"))
    _open_rows_dialog(_fluxity_clip_create_dialog_callback, _("Create Flowblade Media Plugin Script Container Clip"), [row1], [script_select])

def _fluxity_clip_create_dialog_callback(dialog, response_id, data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
    else:
        script_select = data
        script_file = script_select[0].get_filename()

        if script_file == None:
            dialog.destroy()
            _show_not_all_data_info()
            return

        #dialog.destroy()

        container_clip_data = ContainerClipData(appconsts.CONTAINER_CLIP_FLUXITY, script_file, None)
        
        dialog.info_label.set_text("Test Render to validate script...")
        
        # We need to exit this Gtk callback to get info text above updated.
        completion_thread = FluxityLoadCompletionThread(container_clip_data, dialog)
        completion_thread.start()

class FluxityLoadCompletionThread(threading.Thread):
    
    def __init__(self, container_clip_data, dialog):
        self.container_clip_data = container_clip_data
        self.dialog = dialog

        threading.Thread.__init__(self)
        
    def run(self):
        action_object = containeractions.get_action_object(self.container_clip_data)
        is_valid, err_msg = action_object.validate_program()

        time.sleep(0.5) # To make sure text is seen.

        Gdk.threads_enter()
        self.dialog.destroy()

        if is_valid == False:
            primary_txt = _("Flowblade Media Plugin Container Clip Validation Error")
            dialogutils.warning_message(primary_txt, err_msg, gui.editor_window.window)
                
        Gdk.threads_leave()

        if is_valid == False:
            return 
    
        data_object = self.container_clip_data.data_slots["fluxity_plugin_edit_data"]
        length = data_object["length"]
        fluxity_unrendered_media_image = respaths.IMAGE_PATH + "unrendered_fluxity.png"
        window_text = _("Creating Container for Flowblade Media Plugin...")
        containeractions.create_unrendered_clip(length, fluxity_unrendered_media_image, self.container_clip_data, _fluxity_unredered_media_creation_complete, window_text)

def _fluxity_unredered_media_creation_complete(created_unrendered_clip_path, container_clip_data):

    # This called from inside Gdk.threads_enter(), entering second time here crashes.
    # Now that unrendered media has been created we have full container data info.
    data_object = container_clip_data.data_slots["fluxity_plugin_edit_data"]
    container_clip_data.editable = True
    container_clip_data.unrendered_length = data_object["length"]
    container_clip_data.unrendered_media = created_unrendered_clip_path
    container_clip_data.unrendered_type = appconsts.VIDEO

    container_clip = ContainerClipMediaItem(PROJECT().next_media_file_id, data_object["name"], container_clip_data)
    PROJECT().add_container_clip_media_object(container_clip)
    _update_gui_for_media_object_add()

        
# --- MLT XML
def create_mlt_xml_media_item(xml_file_path, media_name):
    container_clip_data = ContainerClipData(appconsts.CONTAINER_CLIP_MLT_XML, xml_file_path, xml_file_path)
    container_clip = ContainerClipMediaItem(PROJECT().next_media_file_id, media_name, container_clip_data)
    PROJECT().add_container_clip_media_object(container_clip)
    _update_gui_for_media_object_add()


# --- Blender
def create_blender_media_item():
    f = Gtk.FileFilter()
    f.set_name(_("Blender Project"))
    f.add_pattern("*.blend")
    project_select, row1 = _get_file_select_row_and_editor(_("Select Blender Project File:"), f)

    _open_rows_dialog(_blender_clip_create_dialog_callback, _("Create Blender Project Container Clip"), [row1], [project_select])

def _blender_clip_create_dialog_callback(dialog, response_id, data):
    dialog.destroy()

    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
    else:
        project_select = data[0]
        project_file = project_select.get_filename()
        
        dialog.destroy()
    
        if project_file == None:
            _show_not_all_data_info()
            return

        container_clip_data = ContainerClipData(appconsts.CONTAINER_CLIP_BLENDER, project_file, None)
        
        action_object = containeractions.get_action_object(container_clip_data)
        
        is_valid, err_msg = action_object.validate_program()
        if is_valid == False:
            primary_txt = _("Blender Container Clip Validation Error")
            dialogutils.warning_message(primary_txt, err_msg, gui.editor_window.window)
            return
        
        action_object.initialize_project(project_file) # blocks until info data written

        project_edit_info_path = userfolders.get_cache_dir() + "blender_container_projectinfo.json"
        if editorstate.app_running_from == editorstate.RUNNING_FROM_FLATPAK:
            project_edit_info_path = userfolders.get_user_home_cache_for_flatpak() + "blender_container_projectinfo.json"
        
        info_file = open(project_edit_info_path, "r")
        project_edit_info = json.load(info_file)
        
        length = int(project_edit_info["frame_end"]) - int(project_edit_info["frame_start"])
        container_clip_data.data_slots["project_edit_info"] = project_edit_info
        container_clip_data.editable = True
        container_clip_data.unrendered_length = length

        blender_unrendered_media_image = respaths.IMAGE_PATH + "unrendered_blender.png"

        window_text = _("Creating Container for Blender Project")
 
        containeractions.create_unrendered_clip(length, blender_unrendered_media_image, container_clip_data, _blender_unredered_media_creation_complete, window_text)

def _blender_unredered_media_creation_complete(created_unrendered_clip_path, container_clip_data):
    rand_id_str = str(os.urandom(16))
    clip_id_str = hashlib.md5(rand_id_str.encode('utf-8')).hexdigest() 
    unrendered_clip_path = userfolders.get_data_dir() + appconsts.CONTAINER_CLIPS_UNRENDERED +"/"+ clip_id_str + ".mp4"

    os.replace(created_unrendered_clip_path, unrendered_clip_path)

    # Now that unrendered media has been created we have full container data info.
    container_clip_data.unrendered_media = unrendered_clip_path
    container_clip_data.unrendered_type = appconsts.VIDEO

    container_clip = ContainerClipMediaItem(PROJECT().next_media_file_id, container_clip_data.get_program_name(), container_clip_data)
    PROJECT().add_container_clip_media_object(container_clip)
    _update_gui_for_media_object_add()



# ---------------------------------------------------------------- MEDIA FILE OBJECT

class ContainerClipMediaItem:
    """
    Container clip media iem in Media Bin.
    1-N container clips can be created from this.
    """
    def __init__(self, media_item_id, name, container_data):
        self.id = media_item_id
        self.name = name
        self.path = container_data.unrendered_media
        self.container_data = container_data
        self.length = None
        self.type = container_data.unrendered_type
        self.icon = None
        self.icon_path = None
        
        self.mark_in = -1
        self.mark_out = -1

        self.has_proxy_file = False
        self.is_proxy_file = False
        self.second_file_path = None

        self.ttl = None

        self.create_icon()

    def matches_project_profile(self):
        return True # These are all created to match project profile.

    def create_mlt_producer(self, profile):
        print("create_mlt_producer() not implemented")

    def create_icon(self):
        try:
            action_object = containeractions.get_action_object(self.container_data)
            if self.icon_path == None:

                surface, length, icon_path = action_object.create_icon()      
                self.icon = surface
                self.icon_path = icon_path
                self.length = length
                self.container_data.unrendered_length = length - 1
            else:
                self.icon = action_object.load_icon()
        except:
            self.icon_path = respaths.IMAGE_PATH + FALLBACK_THUMB
            cr, scaled_icon = containeractions._create_image_surface(self.icon_path)
            self.icon = scaled_icon
            
    def save_program_edit_info(self):
        if self.container_data.container_type == appconsts.CONTAINER_CLIP_BLENDER:
            edit_info = self.container_data.data_slots["project_edit_info"]

            save_data = {}
            save_data["objects"] = copy.copy(edit_info["objects"])
            save_data["materials"] = copy.copy(edit_info["materials"])
            save_data["curves"] = copy.copy(edit_info["curves"])
            
            default_name = self.name  + "_edit_data"
            
            dialogs.save_cont_clip_edit_data(self._save_program_edit_info_callback, default_name, save_data)
        
    def _save_program_edit_info_callback(self, dialog, response_id, edit_data):
        
        if response_id != Gtk.ResponseType.ACCEPT:
            dialog.destroy()
        else:
            if self.container_data.container_type == appconsts.CONTAINER_CLIP_BLENDER:
                save_file = dialog.get_filename()
                dialog.destroy()
                if save_file == None:
                    return
                
                with open(save_file, "w") as f: 
                     json.dump(edit_data, f, indent=4)

    def load_program_edit_info(self):
        dialogs.load_cont_clip_edit_data(self._load_program_edit_info_callback)
    
    def _load_program_edit_info_callback(self, dialog, response_id):
        if response_id != Gtk.ResponseType.ACCEPT:
            dialog.destroy()
        else:
            load_file_path = dialog.get_filename()
            dialog.destroy()
            if load_file_path == None:
                return
                
            load_file = open(load_file_path, "r")
            loaded_project_edit_info = json.load(load_file)
            
            primary_txt = _("Container Program Edit Data is Executable!")
            secondary_txt = _("Only accept Container Program Edit Data from similar trustwothy sources\nyou would accept applications!\n\nContainer Program Edit Data will be used to call Python <b>exec()</b> function and\ncan maybe used as an attack vector against your system.")
            warning_panel = dialogutils.get_warning_message_dialog_panel(primary_txt, secondary_txt)
            
            sw = guicomponents.get_scroll_widget((300, 200), str(loaded_project_edit_info))
            
            content = Gtk.VBox(False, 2)
            content.pack_start(warning_panel, False, False, 0)
            content.pack_start(guiutils.bold_label("Loaded Container Program Edit Data"), False, False, 0)
            content.pack_start(sw, False, False, 0)
            
            align = dialogutils.get_default_alignment(content)
            
            dialog = Gtk.Dialog("",
                                 gui.editor_window.window,
                                Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                (_("Cancel"), Gtk.ResponseType.REJECT,
                                 _("Load Program Edit Data"), Gtk.ResponseType.ACCEPT))
            dialog.vbox.pack_start(align, True, True, 0)
            dialogutils.set_outer_margins(dialog.vbox)
            dialog.set_resizable(False)
            dialog.connect('response', self._load_warning_callback, loaded_project_edit_info)

            dialog.show_all()
            
    def _load_warning_callback(self, dialog, response_id, loaded_project_edit_info):
        if response_id != Gtk.ResponseType.ACCEPT:
            dialog.destroy()
        else:
            dialog.destroy()

            if self.container_data.container_type == appconsts.CONTAINER_CLIP_BLENDER:
                edit_data = self.container_data.data_slots["project_edit_info"]
                edit_data["objects"] = loaded_project_edit_info["objects"]
                edit_data["materials"] = loaded_project_edit_info["materials"]
                edit_data["curves"] = loaded_project_edit_info["curves"]

            
            
            
