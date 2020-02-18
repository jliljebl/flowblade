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

import cairo
import mlt
import hashlib
import os

import appconsts
import dialogutils
from editorstate import PROJECT
import gui
import guiutils
import userfolders
import utils

ROW_WIDTH = 300


class ContainerClipData:
    
        def __init__(self, container_type, program, unrendered_media):
            self.container_type = container_type
            self.program = program

            self.rendered_media = None
            self.rendered_media_range_in = -1
            self.rendered_media_range_out = -1

            self.unrendered_media = unrendered_media
            self.unrendered_length = None
            self.unrendered_type = utils.get_media_type(unrendered_media)

        def get_unrendered_media_name(self):
            directory, file_name = os.path.split(self.unrendered_media)
            name, ext = os.path.splitext(file_name)
            return name



def _update_gui_for_media_object_add():
    gui.media_list_view.fill_data_model()
    gui.bin_list_view.fill_data_model()


# -------------------------------------------------------- G'Mic
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
            dialogutils.info_message(_("NOt all required files were defined"), _("Select all files asked for in dialog for succesful container clip creation."), gui.editor_window.window)
            return

        container_clip_data = ContainerClipData(appconsts.CONTAINER_CLIP_GMIC, script_file, media_file)
        container_clip = GMicContainerClip(PROJECT().next_media_file_id, container_clip_data.get_unrendered_media_name(), container_clip_data)
        PROJECT().add_container_clip_media_object(container_clip)
        _update_gui_for_media_object_add()


# ------------------------------------------------------------ Dialogs utils
def _get_file_select_row_and_editor(label_text):
    file_chooser = Gtk.FileChooserButton()
    file_chooser.set_size_request(250, 25)
    file_chooser.set_current_folder(os.path.expanduser("~") + "/")

    #filt = utils.get_image_sequence_file_filter()
    #file_chooser.add_filter(filt)
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


# ------------------------------------------------------------ thumbnail creation

def _write_thumbnail_image(profile, file_path):
    """
    Writes thumbnail image from file producer
    """
    # Get data
    md_str = hashlib.md5(file_path.encode('utf-8')).hexdigest()
    thumbnail_path = userfolders.get_cache_dir() + appconsts.THUMBNAILS_DIR + "/" + md_str +  ".png"

    # Create consumer
    consumer = mlt.Consumer(profile, "avformat", 
                                 thumbnail_path)
    consumer.set("real_time", 0)
    consumer.set("vcodec", "png")

    # Create one frame producer
    producer = mlt.Producer(profile, str(file_path))
    if producer.is_valid() == False:
        raise ProducerNotValidError(file_path)

    info = utils.get_file_producer_info(producer)

    length = producer.get_length()
    frame = length // 2
    producer = producer.cut(frame, frame)

    # Connect and write image
    consumer.connect(producer)
    consumer.run()
    
    return (thumbnail_path, length, info)

def _create_image_surface(icon_path):
    icon = cairo.ImageSurface.create_from_png(icon_path)
    scaled_icon = cairo.ImageSurface(cairo.FORMAT_ARGB32, appconsts.THUMB_WIDTH, appconsts.THUMB_HEIGHT)
    cr = cairo.Context(scaled_icon)
    cr.scale(float(appconsts.THUMB_WIDTH) / float(icon.get_width()), float(appconsts.THUMB_HEIGHT) / float(icon.get_height()))
    cr.set_source_surface(icon, 0, 0)
    cr.paint()
    
    return scaled_icon
    
# --------------------------------------------------- bin media objects
class AbstractBinContainerClip: # not extends projectdata.MediaFile? too late, too late. Also better name would be AbstractBinPatternProducer
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

        self.mark_in = -1
        self.mark_out = -1

        self.has_proxy_file = False
        self.is_proxy_file = False
        self.second_file_path = None

        self.ttl = None

        self.create_icon()


    def matches_project_profile(self):
        return True # these are created to match project profile

    def create_mlt_producer(self, profile):
        print("create_mlt_producer not implemented")

    def create_icon(self):
        print("patter producer create_icon() not implemented")



class GMicContainerClip(AbstractBinContainerClip):
    """
    Color Clip that can added to and edited in Sequence.
    """   
    def __init__(self, media_item_id, name, container_data):

        AbstractBinContainerClip.__init__(self, media_item_id, name, container_data)

    def create_icon(self):
        icon_path, length, info = _write_thumbnail_image(PROJECT().profile, self.container_data.unrendered_media)
        self.icon = _create_image_surface(icon_path)
        self.length = length
