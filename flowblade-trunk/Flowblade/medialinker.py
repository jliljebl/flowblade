"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2015 Janne Liljeblad.

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
try:
    import mlt7 as mlt
except:
    import mlt7 as mlt
import locale
import os
import subprocess
import sys
import threading
from PIL import Image, ImageFont, ImageDraw
import time

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from gi.repository import Pango, GObject

import appconsts
import dialogs
import dialogutils
import editorstate
import editorpersistance
import gui
import guiutils
import guicomponents
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import patternproducer
import persistance
import processutils
import projectdata
import propertyparse
import respaths
import renderconsumer
import translations
import userfolders
import utils

linker_window = None
target_project = None
last_media_dir = None
media_assets = []

NO_PROJECT_AT_LAUNCH = "##&&noproject&&##"

def display_linker(filename=NO_PROJECT_AT_LAUNCH):
    print("Launching Media Relinker")
    FLOG = open(userfolders.get_cache_dir() + "log_media_relinker", 'w')
    subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowblademedialinker", filename], stdin=FLOG, stdout=FLOG, stderr=FLOG)


# -------------------------------------------------------- render thread
class ProjectLoadThread(threading.Thread):
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.filename = filename

    def run(self):
        Gdk.threads_enter()
        linker_window.project_label.set_text("Loading...")
        Gdk.threads_leave()

        persistance.show_messages = False
        project = persistance.load_project(self.filename, False, True)
        
        global target_project
        target_project = project
        target_project.c_seq = project.sequences[target_project.c_seq_index]
        _update_media_assets()

        Gdk.threads_enter()
        linker_window.relink_list.fill_data_model()
        linker_window.project_label.set_text(self.filename)
        linker_window.set_active_state()
        linker_window.update_files_info()
        linker_window.load_button.set_sensitive(False)
        Gdk.threads_leave()


class MediaLinkerWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.connect("delete-event", lambda w, e:_shutdown())

        app_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "flowblademedialinker.png")
        self.set_icon(app_icon)

        load_button = Gtk.Button(_("Load Project For Relinking"))
        load_button.connect("clicked",
                            lambda w: self.load_button_clicked())
        self.load_button = load_button
        project_row = Gtk.HBox(False, 2)
        project_row.pack_start(load_button, False, False, 0)
        project_row.pack_start(Gtk.Label(), True, True, 0)

        self.missing_label = guiutils.bold_label("<b>" + _("Original Media Missing:") + "</b> ")
        self.found_label = guiutils.bold_label("<b>" + _("Original Media Found:") + "</b> ")
        self.missing_count = Gtk.Label()
        self.found_count = Gtk.Label()
        self.proj = guiutils.bold_label("<b>" + _("Project:") + "</b> ")
        self.project_label = Gtk.Label(label=_("<not loaded>"))

        missing_info = guiutils.get_left_justified_box([self.missing_label, guiutils.pad_label(2, 2), self.missing_count])
        missing_info.set_size_request(250, 2)
        found_info = guiutils.get_left_justified_box([self.found_label, guiutils.pad_label(2, 2), self.found_count])

        status_row = Gtk.HBox(False, 2)
        status_row.pack_start(missing_info, False, False, 0)
        status_row.pack_start(found_info, False, False, 0)
        status_row.pack_start(Gtk.Label(), True, True, 0)
        status_row.pack_start(guiutils.pad_label(30, 12), False, False, 0)
        status_row.pack_start(self.proj, False, False, 0)
        status_row.pack_start(guiutils.pad_label(4, 12), False, False, 0)
        status_row.pack_start(self.project_label, False, False, 0)
        
        self.relink_list = MediaRelinkListView()

        self.find_button = Gtk.Button(_("Set File Relink Path"))
        self.find_button.connect("clicked", lambda w: _set_button_pressed())
        self.create_button = Gtk.Button(_("Create Placeholder File"))
        self.create_button.connect("clicked", lambda w: _create_relink_media_button_pressed())
        self.delete_button = Gtk.Button(_("Delete File Relink Path"))
        self.delete_button.connect("clicked", lambda w: _delete_button_pressed())

        self.display_combo = Gtk.ComboBoxText()
        self.display_combo.append_text(_("Display Missing Media Files"))
        self.display_combo.append_text(_("Display Found Media Files"))
        self.display_combo.set_active(0)
        self.display_combo.connect("changed", self.display_list_changed)
        
        buttons_row = Gtk.HBox(False, 2)
        buttons_row.pack_start(self.display_combo, False, False, 0)
        buttons_row.pack_start(Gtk.Label(), True, True, 0)
        buttons_row.pack_start(self.create_button, False, False, 0)
        buttons_row.pack_start(guiutils.pad_label(24, 4), False, False, 0)
        buttons_row.pack_start(self.delete_button, False, False, 0)
        buttons_row.pack_start(guiutils.pad_label(24, 4), False, False, 0)
        buttons_row.pack_start(self.find_button, False, False, 0)

        self.save_button = Gtk.Button(_("Save Relinked Project As..."))
        self.save_button.connect("clicked", lambda w:_save_project_pressed())
        cancel_button = Gtk.Button(_("Close"))
        cancel_button.connect("clicked", lambda w:_shutdown())
        dialog_buttons_box = Gtk.HBox(True, 2)
        dialog_buttons_box.pack_start(cancel_button, True, True, 0)
        dialog_buttons_box.pack_start(self.save_button, False, False, 0)
        
        self.msg_label = Gtk.Label("")
        dialog_buttons_row = Gtk.HBox(False, 2)
        dialog_buttons_row.pack_start(self.msg_label, True, True, 0)
        dialog_buttons_row.pack_start(dialog_buttons_box, False, False, 0)

        pane = Gtk.VBox(False, 2)
        pane.pack_start(project_row, False, False, 0)
        pane.pack_start(guiutils.pad_label(24, 24), False, False, 0)
        pane.pack_start(status_row, False, False, 0)
        pane.pack_start(guiutils.pad_label(24, 2), False, False, 0)
        pane.pack_start(self.relink_list, False, False, 0)
        pane.pack_start(buttons_row, False, False, 0)
        pane.pack_start(guiutils.pad_label(24, 24), False, False, 0)
        pane.pack_start(dialog_buttons_row, False, False, 0)
        
        align = guiutils.set_margins(pane, 12, 12, 12, 12)

        # Set pane and show window
        self.add(align)
        self.set_title(_("Media Relinker"))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()
        self.set_resizable(False)
        self.set_active_state()

    def load_button_clicked(self):
        dialogs.load_project_dialog(self.load_project_dialog_callback, self)
    
    def load_project_dialog_callback(self, dialog, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            filenames = dialog.get_filenames()
            
            dialog.destroy()
            
            self.load_project(filenames[0])
        else:
            dialog.destroy()

    def load_project(self, filename):
        global load_thread
        load_thread = ProjectLoadThread(filename)
        load_thread.start()
            
    def display_list_changed(self, display_combo):
        self.relink_list.fill_data_model()
        if display_combo.get_active() == 0:
            self.relink_list.text_col_1.set_title(self.relink_list.missing_text)
        else:
            self.relink_list.text_col_1.set_title(self.relink_list.found_text)

    def set_active_state(self):
        active = (target_project != None)
        
        self.save_button.set_sensitive(active) 
        self.relink_list.set_sensitive(active) 
        self.find_button.set_sensitive(active) 
        self.delete_button.set_sensitive(active) 
        self.display_combo.set_sensitive(active) 
        self.missing_label.set_sensitive(active) 
        self.found_label.set_sensitive(active) 
        self.missing_count.set_sensitive(active) 
        self.found_count.set_sensitive(active) 
        self.project_label.set_sensitive(active) 
        self.proj.set_sensitive(active) 
        self.create_button.set_sensitive(active)

    def update_files_info(self):
        found = 0
        missing = 0
        for asset in media_assets:
            if asset.orig_file_exists:
                found = found + 1
            else:
                missing = missing + 1

        self.missing_count.set_text(str(missing))
        self.found_count.set_text(str(found))

    def get_selected_media_asset(self):
        selection = self.relink_list.treeview.get_selection()
        (model, rows) = selection.get_selected_rows()
        row = max(rows[0])
        if len(self.relink_list.assets) == 0:
            return None
        
        return self.relink_list.assets[row]


class MediaRelinkListView(Gtk.VBox):

    def __init__(self):
        GObject.GObject.__init__(self)

        self.assets = [] # Used to store list displayed data items

        # Datamodel: text, text
        self.storemodel = Gtk.ListStore(str, str)
 
        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

        # View
        self.treeview = Gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(True)
        self.treeview.connect("button-press-event", self.row_pressed)

        # Column views
        self.missing_text = _("Missing Media File Path")
        self.found_text = _("Found Media File Path")
        self.text_col_1 = Gtk.TreeViewColumn("text1")
        self.text_col_1.set_title(self.missing_text)
        self.text_col_2 = Gtk.TreeViewColumn("text2")
        self.text_col_2.set_title(_("Media File Re-link Path"))
        
        # Cell renderers
        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", Pango.EllipsizeMode.START)

        self.text_rend_2 = Gtk.CellRendererText()
        self.text_rend_2.set_property("ellipsize", Pango.EllipsizeMode.START)
        self.text_rend_2.set_property("yalign", 0.0)

        # Build column views
        self.text_col_1.set_expand(True)
        self.text_col_1.pack_start(self.text_rend_1, True)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 0)
    
        self.text_col_2.set_expand(True)
        self.text_col_2.pack_start(self.text_rend_2, True)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 1)

        # Add column views to view
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()
        self.set_size_request(1100, 400)

    def fill_data_model(self):
        self.assets = []
        self.storemodel.clear()

        display_missing = linker_window.display_combo.get_active() == 0

        for media_asset in media_assets:
            if media_asset.orig_file_exists != display_missing:
                if media_asset.relink_path == None:
                    relink = ""
                else:
                    relink = media_asset.relink_path
                
                row_data = [media_asset.orig_path, relink]
                
                self.storemodel.append(row_data)
                self.assets.append(media_asset)
        
        if len(self.assets) > 0: # Set first selected if exists
            selection = self.treeview.get_selection()
            selection.unselect_all()
            selection.select_path(0)

        self.scroll.queue_draw()

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows

    def row_pressed(self, treeview, event):
        # Only handle right mouse on row, not empty or left mouse
        path_pos_tuple = treeview.get_path_at_pos(int(event.x), int(event.y))
        if path_pos_tuple == None:
            return False
        if not (event.button == 3):
            return False

        # Show pop-up
        path, column, x, y = path_pos_tuple
        selection = treeview.get_selection()
        selection.unselect_all()
        selection.select_path(path)
        row = int(max(path))

        guicomponents.display_media_linker_popup_menu(row, treeview, _media_asset_menu_item_selected, event)
        return  True

# ----------------------------------------------------------- logic
class MediaAsset:

    # Default file for missing files to relink
    def __init__(self, orig_path, media_type, media_length=0):
        self.orig_path = orig_path
        self.media_type = media_type
        self.length = media_length
    # End of Default file for missing files to relink

        self.orig_file_exists = os.path.isfile(orig_path)
        if self.media_type == appconsts.IMAGE_SEQUENCE:
            self._check_img_seq_existance(orig_path)
            
        self.relink_path = None

    def _check_img_seq_existance(self, orig_path):
        asset_folder, asset_file_name = os.path.split(orig_path)
        lookup_filename = utils.get_img_seq_glob_lookup_name(asset_file_name)
        lookup_path = asset_folder + "/" + lookup_filename          
        listing = glob.glob(lookup_path)

        if len(listing) > 0:
            self.orig_file_exists = True
        else:
            self.orig_file_exists = False
                
def _update_media_assets():
    # Collect all media assets used by project
    
    new_assets = []
    asset_paths = {}
            
    # Media file media assets
    for media_file_id, media_file in target_project.media_files.items():
        if isinstance(media_file, patternproducer.AbstractBinClip):
            continue
        try:
            # Default file for missing files to relink
            new_assets.append(MediaAsset(media_file.path, media_file.type, media_file.length))
            # End of Default file for missing files to relink
            asset_paths[media_file.path] = media_file.path
        except:
            print("failed loading:", media_file)
            
    for seq in target_project.sequences:
        # Clip media assets
        for track in seq.tracks:
            for i in range(0, len(track.clips)):
                clip = track.clips[i]
                # Only producer clips are affected
                if (clip.is_blanck_clip == False and (clip.media_type != appconsts.PATTERN_PRODUCER)):
                    if not(clip.path in asset_paths):
                        # Default file for missing files to relink
                        new_assets.append(MediaAsset(clip.path, clip.media_type,clip.clip_out - clip.clip_in + 1))  #clip.get_length()))
                        # End of Default file for missing files to relink
                        asset_paths[clip.path] = clip.path
        # Wipe lumas
        for compositor in seq.compositors:
            res_path = None
            if compositor.type_id == "##wipe": # Wipe may have user luma and needs to be looked up relatively
                res_path = propertyparse.get_property_value(compositor.transition.properties, "resource")
            if compositor.type_id == "##region": # Wipe may have user luma and needs to be looked up relatively
                res_path = propertyparse.get_property_value(compositor.transition.properties, "composite.luma")

            if res_path != None:
                if not(res_path in asset_paths):
                    new_assets.append(MediaAsset(res_path, appconsts.IMAGE))
                    asset_paths[res_path] = res_path

    global media_assets
    media_assets = new_assets

def _media_asset_menu_item_selected(widget, data):
    msg, row = data
    media_asset = linker_window.relink_list.assets[row]

    if msg == "set relink":
        _set_relink_path(media_asset)
    if msg == "delete relink":
        _delete_relink_path(media_asset)
    if msg == "show path":
        _show_paths(media_asset)
    if msg == "create placeholder":
        _create_relink_media_button_pressed()

def _set_button_pressed():
    media_asset = linker_window.get_selected_media_asset()
    if media_asset == None:
        return
    _set_relink_path(media_asset)

def _set_relink_path(media_asset):
    file_name = os.path.basename(media_asset.orig_path)
    # End of Default file for missing files to relink
    dialogs.media_file_dialog(_("Select Media File To Relink To") + " " + file_name, 
                                _select_relink_path_dialog_callback, False, 
                                media_asset, linker_window, last_media_dir)

def _create_relink_media_button_pressed():
    media_asset = linker_window.get_selected_media_asset()

    if media_asset.media_type == appconsts.IMAGE:
        info_text = _("Creating placeholder image...")
    elif media_asset.media_type == appconsts.AUDIO:
        info_text = _("Creating placeholder audio...")
    elif media_asset.media_type == appconsts.VIDEO:
        info_text = _("Creating placeholder video...")

    linker_window.msg_label.set_text(info_text)

    # We need to launch render on another thread and return from this function
    # as soon as possible or we will freeze GUI because we hold GDK lock during render.
    render_thread = MediaRecreateThread(media_asset) 
    render_thread.start()

    # Poll rendering from GDK with timeout events to get access to GDK lock on updates 
    # to be able to draw immediately.
    Gdk.threads_add_timeout(GLib.PRIORITY_HIGH_IDLE, 500, _recreate_update, render_thread, info_text)

def _recreate_update(render_thread, info_text):
    elapsed = utils.get_time_str_for_sec_float(render_thread.get_elapsed())
    linker_window.msg_label.set_text(info_text + " " + elapsed)
    linker_window.msg_label.queue_draw()

    if render_thread.running == False:
        linker_window.relink_list.fill_data_model()
        linker_window.msg_label.set_text(_("Place holder media ready."))
        return False # This stops repeated calls to this function.
    else:
        return True # Function will be called again in 500ms.
            
class MediaRecreateThread(threading.Thread):
    def __init__(self, media_asset):
        threading.Thread.__init__(self)
        self.media_asset = media_asset
        self.file_name = os.path.basename(media_asset.orig_path)
        self.running = True
        
    def run(self):
        
        self.start_time = time.monotonic()

        new_media_file_name = hashlib.md5(str(os.urandom(32)).encode('utf-8') +  str.encode(self.file_name)).hexdigest()
        link_path_no_ext = userfolders.get_render_dir() + "/" + new_media_file_name
        
        if self.media_asset.media_type == appconsts.IMAGE:
            link_path = link_path_no_ext + ".png"
            self.success = background_missing_image(link_path, self.file_name)
        elif self.media_asset.media_type == appconsts.AUDIO:
            link_path = link_path_no_ext + ".wav"
            self.success = sine_wav(link_path, self.media_asset.length)
        elif self.media_asset.media_type == appconsts.VIDEO:
            link_path = link_path_no_ext + ".mp4"
            self.success = video_file_replace(link_path, self.file_name, self.media_asset.length)

        self.media_asset.relink_path = link_path
        
        self.running = False
    
        # TODO: handle self.success == False with something
    
    def get_elapsed(self):
        return time.monotonic() - self.start_time 
        
def _select_relink_path_dialog_callback(file_select, response_id, media_asset):
    filenames = file_select.get_filenames()
    file_select.destroy()

    if response_id != Gtk.ResponseType.OK:
        return
    if len(filenames) == 0:
        return

    media_asset.relink_path = filenames[0]
    folder, file_name = os.path.split(filenames[0])
        
    global last_media_dir
    last_media_dir = folder

    # Default file for missing files to relink
    linker_window.set_title( folder + " " + file_name )    
    #End of Default file for missing files to relink

    # Relink all the files in a same directory
    for med_asset in media_assets:
        med_link_name = os.path.basename(med_asset.orig_path)
        link_path = os.path.join(folder, med_link_name)
        if os.path.isfile(link_path):
            if med_asset.media_type == appconsts.IMAGE_SEQUENCE: # img seqs need formatted path
                resource_name_str = utils.get_img_seq_resource_name(link_path)
                med_asset.relink_path = folder + "/" + resource_name_str
            else:
                med_asset.relink_path = link_path
            linker_window.relink_list.fill_data_model()
    # End of Relink all the files in a same directory

def _delete_button_pressed():
    media_asset = linker_window.get_selected_media_asset()
    if media_asset == None:
        return
    _delete_relink_path(media_asset)

def _delete_relink_path(media_asset):
    media_asset.relink_path = None
    linker_window.relink_list.fill_data_model()

def _show_paths(media_asset):
    orig_path_label = Gtk.Label(label=_("<b>Original path:</b> "))
    orig_path_label.set_use_markup(True)
    orig_path = guiutils.get_left_justified_box([orig_path_label, Gtk.Label(label=media_asset.orig_path)])
    relink_path_label = Gtk.Label(label=_("<b>Relink path:</b> "))
    relink_path_label.set_use_markup(True)
    relink_path = guiutils.get_left_justified_box([relink_path_label, Gtk.Label(label=media_asset.relink_path)])
    
    panel = Gtk.VBox()
    panel.pack_start(orig_path, False, False, 0)
    panel.pack_start(guiutils.pad_label(12, 12), False, False, 0)
    panel.pack_start(relink_path, False, False, 0)
    
    dialogutils.panel_ok_dialog(_("Media Asset Paths"), panel)
        
def _save_project_pressed():
    if  target_project.last_save_path != None:
        open_dir = os.path.dirname(target_project.last_save_path)
    else:
        open_dir = None
    
    no_ext_name = target_project.name.replace('.flb','')
        
    dialogs.save_project_as_dialog(_save_as_dialog_callback, 
                                   no_ext_name + "_RELINKED.flb", 
                                   open_dir, linker_window)

def _save_as_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        filenames = dialog.get_filenames()
        dialog.destroy()

        target_project.last_save_path = filenames[0]
        target_project.name = os.path.basename(filenames[0])
    
        # Test that saving is not IOError
        try:
            filehandle = open( target_project.last_save_path, 'w' )
            filehandle.close()
        except IOError as ioe:
            primary_txt = "I/O error({0})".format(ioe.errno)
            secondary_txt = ioe.strerror + "."
            dialogutils.warning_message(primary_txt, secondary_txt, linker_window, is_info=False)
            return 

        # Relink and save
        _relink_project_media_paths()
            
        persistance.save_project(target_project, target_project.last_save_path)

        dialogutils.info_message(_("Relinked version of the Project saved!"), 
                                 _("To test the project, close this tool and open the relinked version in Flowblade."), 
                                 linker_window)
    else:
        dialog.destroy()

def _relink_project_media_paths():
    # Collect relink paths
    relinked_paths = {}
    for media_asset in media_assets:
        if media_asset.relink_path != None:
            relinked_paths[media_asset.orig_path] = media_asset.relink_path
            
    # Relink media file media assets
    for media_file_id, media_file in target_project.media_files.items():
        if isinstance(media_file, patternproducer.AbstractBinClip):
            continue
        if media_file.path in relinked_paths:
            media_file.path = relinked_paths[media_file.path]

    for seq in target_project.sequences:

        # Relink clip media assets
        for track in seq.tracks:
            for i in range(0, len(track.clips)):
                clip = track.clips[i]
                if (clip.is_blanck_clip == False and (clip.media_type != appconsts.PATTERN_PRODUCER)):
                    if clip.path in relinked_paths:
                        clip.path = relinked_paths[clip.path]

        # Relink wipe lumas
        for compositor in seq.compositors:
            if compositor.type_id == "##wipe":
                res_path = propertyparse.get_property_value(compositor.transition.properties, "resource")
                if res_path in relinked_paths:
                    propertyparse.set_property_value(compositor.transition.properties, "resource", relinked_paths[res_path])
            if compositor.type_id == "##region":
                res_path = propertyparse.get_property_value(compositor.transition.properties, "composite.luma")
                if res_path in relinked_paths:
                    propertyparse.set_property_value(compositor.transition.properties,  "composite.luma", relinked_paths[res_path])

# Default file for missing files to relink

def background_missing_image(link_path, file_name, video_file_name=None):
    screen_width = 1920 #target_project.profile.width()
    screen_height  = 1080 #target_project.profile.height()

    if os.path.isfile(link_path):
        os.remove(link_path)

    size = (screen_width, screen_height)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    img = Image.new("RGBA",size, (200,40, 40))
    draw = ImageDraw.Draw(img)
    if video_file_name != None: # We use this to make images for both grphics and video media.
        new_file_name = video_file_name
    else:
        new_file_name = link_path
    draw.text((30,20), " >>>  " + new_file_name + "\n\nreplaces the missing file:\n\n<<<  " + file_name, (255,255,0), font=font)
    draw = ImageDraw.Draw(img)
    img.save(link_path)
    
    if os.path.isfile(link_path):
        return True
    else:
        return False

def sine_wav(link_path, duration):
    if os.path.isfile(link_path):
        os.remove(link_path)

    duration = int(duration/25) + 1
    dur = '\"sine=frequency=1000:duration="' + str(duration) + '"\" '
    command = 'ffmpeg -f lavfi -i ' +  dur + ' ' + link_path

    os.system(command)
    
    if os.path.isfile(link_path):
        return True
    else:
        return False

def  video_file_replace(link_path, file_name, duration):

    image_file = "/tmp/tmp.png"
    if os.path.isfile(image_file):
        os.remove(image_file)
    success = background_missing_image(image_file, file_name)
    
    audio_file = "/tmp/tmp.wav"
    if os.path.isfile(audio_file):
        os.remove(audio_file)
    success = sine_wav(audio_file, duration)
    
    if os.path.isfile(link_path):
        os.remove(link_path)
    command = "ffmpeg -loop 1 -i "+ image_file + " -i " +  audio_file  + " -c:v libx264 -c:a aac -strict experimental -b:a 192k -shortest " + link_path
    print("ml 696",  command)
    os.system(command)

    if os.path.isfile(link_path):
        return True
    else:
        return False


# ----------------------------------------------------------- main
def main(root_path, filename):
    gtk_version = "%s.%s.%s" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    print("GTK+ version:", gtk_version)
    editorstate.gtk_version = gtk_version
    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"

    # Create user folders if needed and determine if we are using xdg or dotfile userf folders.
    userfolders.init()

    # Set paths.
    respaths.set_paths(root_path)

    # Load editor prefs and list of recent projects
    editorpersistance.load()
    
    # Init translations module with translations data
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()

    # Init gtk threads
    Gdk.threads_init()
    Gdk.threads_enter()

    # Themes
    if editorpersistance.prefs.theme != appconsts.LIGHT_THEME:
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)
        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME \
            or editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_GRAY \
            or editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME_NEUTRAL:
            gui.apply_gtk_css(editorpersistance.prefs.theme)

    repo = mlt.Factory().init()
    processutils.prepare_mlt_repo(repo)
    
    # Set numeric locale to use "." as radix, MLT initializes this to OS locale and this causes bugs 
    locale.setlocale(locale.LC_NUMERIC, 'C')

    # Check for codecs and formats on the system
    mltenv.check_available_features(repo)
    renderconsumer.load_render_profiles()

    # Load filter and compositor descriptions from xml files.
    mltfilters.load_filters_xml(mltenv.services)
    mlttransitions.load_compositors_xml(mltenv.transitions)

    # Create list of available mlt profiles
    mltprofiles.load_profile_list()

    appconsts.SAVEFILE_VERSION = projectdata.SAVEFILE_VERSION

    global linker_window
    linker_window = MediaLinkerWindow()

    if filename != NO_PROJECT_AT_LAUNCH:
        linker_window.load_project(filename)

    Gtk.main()
    Gdk.threads_leave()
    
def _shutdown():
    Gtk.main_quit()
