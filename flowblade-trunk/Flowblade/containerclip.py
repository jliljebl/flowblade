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

from gi.repository import Gtk, Gdk, GLib

import copy
import hashlib
import json
import os
import threading
import time

import appconsts
import containeractions
import dialogs
import dialogutils
import editorstate
from editorstate import PROJECT
from editorstate import current_sequence
import gui
import guicomponents
import guiutils
import projectaction
import respaths
import updater
import userfolders
import utils

"""
This module handles creating ContainerClipData objects that are the persistent
data representations of container clips, and ContainerClipMediaItem objects that represent
data in Media Bins that can be used to create container clips.

Wrapper objects of a type extending containeactions.AbstractContainerActionObject are created and discarded
as needed to execute all actions on container clips.
"""

_media_import_callback = None # Used to import generators sequentially from another project.

ROW_WIDTH = 300
FALLBACK_THUMB = "fallback_thumb.png"

class ContainerClipData:
    
        def __init__(self, container_type, program, unrendered_media):
            self.container_clip_uid = -1 # This is set at clip creation time.

            self.container_type = container_type
            self.program = program # path to program file

            self.rendered_media = None
            self.rendered_media_range_in = -1
            self.rendered_media_range_out = -1
            self.last_render_type = containeractions.FULL_RENDER
            
            self.unrendered_media = unrendered_media
            self.unrendered_length = None # This is also maximum length for media produced using this container data.
            # This gets set later for some container types
            if unrendered_media != None:
                self.unrendered_type = utils.get_media_type(unrendered_media)
            else:
                self.unrendered_type = None

            self.external_media_folder = None

            self.render_data = None # initialized to a toolsencoding.ToolsRenderData object later.
            
            # Some container clips need to save additional information.
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

def set_render_settings_from_create_window(container_data, callback):
    action_object = containeractions.get_action_object(container_data)
    action_object.set_video_endoding(None, callback)

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
    updater.update_current_bin_files_count()

def _show_not_all_data_info():
    dialogutils.info_message(_("Not all required files were defined"), _("Select all files asked for in dialog for successful Container Clip creation."), gui.editor_window.window)
        
        

# -------------------------------------------------------- MEDIA ITEM CREATION
# -------------------------------------------------------- G'Mic
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

        GLib.idle_add(_gmic_load_complete, self.container_clip_data, self.dialog, is_valid, err_msg)

def _gmic_load_complete(container_clip_data, dialog, is_valid, err_msg):
        dialog.destroy()
        
        if is_valid == True:
            container_clip = ContainerClipMediaItem(PROJECT().next_media_file_id, container_clip_data.get_unrendered_media_name(), container_clip_data)
            PROJECT().add_container_clip_media_object(container_clip)
            _update_gui_for_media_object_add()
        else:
            primary_txt = _("G'Mic Container Clip Validation Error")
            dialogutils.warning_message(primary_txt, err_msg, gui.editor_window.window)

    
# ------------------------------------------------------- Fluxity
# ------------------------------------------------------- ADDING GENERATOR FROM SCRIPT AS MEDIA ITEM
# Adding Generator item from loaded script file.
def create_fluxity_media_item():
    script_select, row1 = _get_file_select_row_and_editor(_("Generator Plugin Script:"), None, _("Generator Plugin Script"))
    _open_rows_dialog(_fluxity_clip_create_dialog_callback, _("Create Generator Plugin Script Media Item"), [row1], [script_select])

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

        container_clip_data = ContainerClipData(appconsts.CONTAINER_CLIP_FLUXITY, script_file, None)
        container_clip_data.data_slots["icon_file"] = None
    
        dialog.info_label.set_text("Test Render to validate script...")
        
        # We need to exit this Gtk callback to get info text above updated.
        completion_thread = FluxityLoadCompletionThread(container_clip_data, dialog)
        completion_thread.start()

# ------------------------------------------------------- ADDING GENERATOR FROM DIALOG AS MEDIA ITEM
# Called when user selects 'Add Generator' in with option 'Add as Container Clip'.
def create_fluxity_media_item_from_plugin(script_file, screenshot_file, plugin_data, import_callback=None):
    container_data = ContainerClipData(appconsts.CONTAINER_CLIP_FLUXITY, script_file, None)
    container_data.data_slots["icon_file"] = screenshot_file
    container_data.data_slots["fluxity_plugin_edit_data"] = plugin_data
    
    # Set callback
    global _media_import_callback
    _media_import_callback = import_callback

    # We need to exit this Gtk callback to get info text above updated.
    completion_thread = FluxityLoadCompletionThread(container_data, None, plugin_data)
    completion_thread.start()
    
class FluxityLoadCompletionThread(threading.Thread):
    
    def __init__(self, container_clip_data, dialog, plugin_data=None):
        self.container_clip_data = container_clip_data
        self.plugin_data = plugin_data
        self.dialog = dialog

        threading.Thread.__init__(self)
        
    def run(self):
        action_object = containeractions.get_action_object(self.container_clip_data)
        is_valid, err_msg = action_object.validate_program()

        # Media plugins have plugin data created with user set values, scripts loaded from file system
        # do not and just had it created in 'action_object.validate_program()'
        if self.plugin_data != None:
            # For media plugins use the provided user edited creation data.
            self.container_clip_data.data_slots["fluxity_plugin_edit_data"] = self.plugin_data
    
        time.sleep(0.5) # To make sure text is seen.

        if self.dialog != None:
            GLib.idle_add(dialogutils.dialog_destroy, self.dialog, None)
    
        if is_valid == False:
            GLib.idle_add(_show_fluxity_validation_error, err_msg)
            return 
    
        data_object = self.container_clip_data.data_slots["fluxity_plugin_edit_data"]
        length = data_object["length"]
        length = length - 1 # MLT handles out frames exclusive and we are using length as out frame value.

        fluxity_unrendered_media_image = respaths.IMAGE_PATH + "unrendered_fluxity.png"
        window_text = _("Creating Container for Generator...")
        containeractions.create_unrendered_clip(length, fluxity_unrendered_media_image, self.container_clip_data, _fluxity_unrendered_media_creation_complete, window_text)

def _show_fluxity_validation_error(err_msg):
    primary_txt = _("Generator Container Clip Validation Error")
    dialogutils.warning_message(primary_txt, err_msg, gui.editor_window.window)


def _fluxity_unrendered_media_creation_complete(created_unrendered_clip_path, container_clip_data):
    # Now that unrendered media has been created we have full container data info.
    data_object = container_clip_data.data_slots["fluxity_plugin_edit_data"]
    container_clip_data.editable = True
    container_clip_data.unrendered_length = data_object["length"]
    container_clip_data.unrendered_media = created_unrendered_clip_path
    container_clip_data.unrendered_type = appconsts.VIDEO

    # Copy created unrendered media clip.
    rand_id_str = str(os.urandom(16))
    clip_id_str = hashlib.md5(rand_id_str.encode('utf-8')).hexdigest()
    # CACHE
    unrendered_clip_path = userfolders.get_data_dir() + appconsts.CONTAINER_CLIPS_UNRENDERED +"/"+ clip_id_str + ".mp4"
    os.replace(created_unrendered_clip_path, unrendered_clip_path)
    container_clip_data.unrendered_media = unrendered_clip_path
    container_clip_data.unrendered_type = appconsts.VIDEO
    
    container_clip = ContainerClipMediaItem(PROJECT().next_media_file_id, data_object["name"], container_clip_data)
    PROJECT().add_container_clip_media_object(container_clip)
    _update_gui_for_media_object_add()
    
    # If we're doing media import we need to go back to do next.
    if _media_import_callback != None:
        _media_import_callback()
        
    
# ------------------------------------------------------------- ADDING GENERATOR AS PRE-RENDERED CLIP
# Called when user selects 'Add Generator' in with option 'Add as Rendered Clip'.
def create_renderered_fluxity_media_item(container_data, length):
    fluxity_unrendered_media_image = respaths.IMAGE_PATH + "unrendered_fluxity.png"
    containeractions.create_unrendered_clip(length, fluxity_unrendered_media_image, container_data, _add_fluxity_rendered_help_media_complete, "Please wait")

def _add_fluxity_rendered_help_media_complete(created_unrendered_clip_path, container_data):
    # We need to jump through some hoops here because we are using media plugin rendering functionality to 
    # add a rendered cidoa as new media item.
    rand_id_str = str(os.urandom(16))
    clip_id_str = hashlib.md5(rand_id_str.encode('utf-8')).hexdigest() 
    unrendered_clip_path = userfolders.get_data_dir() + appconsts.CONTAINER_CLIPS_UNRENDERED +"/"+ clip_id_str + ".mp4"
    os.replace(created_unrendered_clip_path, unrendered_clip_path)
    
    container_data.unrendered_media = unrendered_clip_path
    container_data.unrendered_type = appconsts.VIDEO
    
    throw_away_clip = current_sequence().create_file_producer_clip(unrendered_clip_path, "dummy", False, None)
    throw_away_clip.container_data = container_data
    throw_away_clip.container_data.generate_clip_id()

    action_object = containeractions.get_action_object(container_data)
    action_object.plugin_create_render_complete_callback = _plugin_create_render_complete_callback
    action_object.render_full_media(throw_away_clip)

def _plugin_create_render_complete_callback(resource_path, container_data):
    if container_data.render_data.do_video_render == False:
        projectaction.add_plugin_image_sequence(resource_path, container_data.data_slots["fluxity_plugin_edit_data"]["name"], container_data.unrendered_length)
    else:
        projectaction.add_plugin_rendered_media(resource_path, container_data.data_slots["fluxity_plugin_edit_data"]["name"])
    
# ---------------------------------------------------------------------- MLT XML
def create_mlt_xml_media_item(xml_file_path, media_name):
    container_clip_data = ContainerClipData(appconsts.CONTAINER_CLIP_MLT_XML, xml_file_path, xml_file_path)
    container_clip = ContainerClipMediaItem(PROJECT().next_media_file_id, media_name, container_clip_data)
    PROJECT().add_container_clip_media_object(container_clip)
    _update_gui_for_media_object_add()



# ---------------------------------------------------------------- MEDIA FILE OBJECT

class ContainerClipMediaItem:
    """
    Container clip media item in Media Bin.
    Any number of container clips can be created from this.
    """
    def __init__(self, media_item_id, name, container_data):
        self.id = media_item_id
        self.name = name
        self.path = container_data.unrendered_media
        self.container_data = container_data
        self.length = None
        self.type = container_data.unrendered_type
        self.icon = None # cairo.ImageSurface
        self.icon_path = None
        
        self.mark_in = -1
        self.mark_out = -1

        self.has_proxy_file = False
        self.is_proxy_file = False
        self.second_file_path = None

        self.ttl = None

        self.current_frame = 0

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
            print("ContainerClipMediaItem.create_icon() except")
            self.icon_path = respaths.IMAGE_PATH + FALLBACK_THUMB
            cr, scaled_icon = containeractions._create_image_surface(self.icon_path)
            self.icon = scaled_icon

