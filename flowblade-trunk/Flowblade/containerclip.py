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

from gi.repository import Gtk

import hashlib
import json
import os

import appconsts
import containerprogramedit
import containeractions
import dialogutils
from editorstate import PROJECT
import gui
import guiutils
import respaths
#import toolsencoding
import userfolders
import utils

ROW_WIDTH = 300


class ContainerClipData:
    
        def __init__(self, container_type, program, unrendered_media):
            self.container_clip_uid = -1 # This is set at clip creation time.

            self.container_type = container_type
            self.program = program

            self.rendered_media = None
            self.rendered_media_range_in = -1
            self.rendered_media_range_out = -1
            
            self.unrendered_media = unrendered_media
            self.unrendered_length = None
            # This can get set later for some container types
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
        
        """ Feature dropped from 2.6, maybe put back later. Now we same icon for rendered and unredered.
        def get_rendered_thumbnail(self):
            action_object = containeractions.get_action_object(self)
            return action_object.get_rendered_thumbnail()
        """
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

def edit_program(data):
    clip, track, item_id, item_data = data
    action_object = containeractions.get_action_object(clip.container_data)
    action_object.edit_program(clip)


#------------------------------------------------------------- Cloning
def clone_clip(clip):
    action_object = containeractions.get_action_object(clip.container_data)
    return action_object.clone_clip(clip)


# ------------------------------------------------------------ GUI
def _get_file_select_row_and_editor(label_text, file_filter=None):
    file_chooser = Gtk.FileChooserButton()
    file_chooser.set_size_request(250, 25)
    file_chooser.set_current_folder(os.path.expanduser("~") + "/")

    if file_filter != None:
        file_chooser.add_filter(file_filter)

    row = guiutils.get_two_column_box(Gtk.Label(label=label_text), file_chooser, ROW_WIDTH)
    return (file_chooser, row)

def _open_image_sequence_dialog(callback, title, rows, data):
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
    script_select, row1 = _get_file_select_row_and_editor(_("Select G'Mic Tool Script:"))
    media_file_select, row2 = _get_file_select_row_and_editor(_("Video Clip:"))
    _open_image_sequence_dialog(_gmic_clip_create_dialog_callback, _("Create G'Mic Script Container Clip"), [row1, row2], [script_select, media_file_select])

def _gmic_clip_create_dialog_callback(dialog, response_id, data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
    else:
        script_select, media_file_select = data
        script_file = script_select.get_filename()
        media_file = media_file_select.get_filename()
        
        dialog.destroy()
    
        if script_file == None or media_file == None:
            _show_not_all_data_info()
            return

        container_clip_data = ContainerClipData(appconsts.CONTAINER_CLIP_GMIC, script_file, media_file)
        container_clip = ContainerClipMediaItem(PROJECT().next_media_file_id, container_clip_data.get_unrendered_media_name(), container_clip_data)
        PROJECT().add_container_clip_media_object(container_clip)
        _update_gui_for_media_object_add()

# --- MLT XML
def create_mlt_xml_media_item(xml_file_path, media_name):
    # xml file is both unrendered media and program
    #f = Gtk.FileFilter()
    #f.set_name(_("MLT XML"))
    #f.add_pattern("*.xml")
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

    _open_image_sequence_dialog(_blender_clip_create_dialog_callback, _("Create Blender Project Container Clip"), [row1], [project_select])

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
        action_object.initialize_project(project_file) # blocks until info data written

        project_edit_info_path = userfolders.get_cache_dir() + "blender_container_projectinfo.json"
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

    # Now that unrendere media has been created we have full container data info.
    container_clip_data.unrendered_media = unrendered_clip_path
    container_clip_data.unrendered_type = appconsts.VIDEO

    container_clip = ContainerClipMediaItem(PROJECT().next_media_file_id, container_clip_data.get_program_name(), container_clip_data)
    PROJECT().add_container_clip_media_object(container_clip)
    _update_gui_for_media_object_add()



# ---------------------------------------------------------------- MEDIA FILE OBJECT

class ContainerClipMediaItem:
    """
    A pattern producer object presnt in Media Bin.
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
        action_object = containeractions.get_action_object(self.container_data)
        if self.icon_path == None:

            surface, length, icon_path = action_object.create_icon()      
            self.icon = surface
            self.icon_path = icon_path
            self.length = length
            self.container_data.unrendered_length = length - 1
        else:
            self.icon = action_object.load_icon()


