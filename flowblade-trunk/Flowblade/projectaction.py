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
Module handles user actions that are not edits on the current sequence.
Load, save, add media file, etc...
"""
import gobject
import pygtk
pygtk.require('2.0');
import gtk
import glib

import datetime
import md5
import os
from os import listdir
from os.path import isfile, join
import re
import shutil
import time
import threading

import app
import appconsts
import batchrendering
import dialogs
import dialogutils
import gui
import guicomponents
import guiutils
import editevent
import editorstate
from editorstate import current_sequence
from editorstate import current_bin
from editorstate import PROJECT
from editorstate import MONITOR_MEDIA_FILE
import editorpersistance
import movemodes
import persistance
import projectdata
import projectinfogui
import propertyparse
import proxyediting
import render
import rendergui
import sequence
import updater
import utils


save_time = None
save_icon_remove_event_id = None


#--------------------------------------- worker threads
class LoadThread(threading.Thread):
    
    def __init__(self, filename, block_recent_files=False):
        self.filename = filename
        self.block_recent_files = block_recent_files 
        threading.Thread.__init__(self)

    def run(self):
        gtk.gdk.threads_enter()
        updater.set_info_icon(gtk.STOCK_OPEN)

        dialog = dialogs.load_dialog()
        persistance.load_dialog = dialog
        gtk.gdk.threads_leave()

        ticker = utils.Ticker(_load_pulse_bar, 0.15)
        ticker.start_ticker()

        old_project = editorstate.project
        try:
            editorstate.project_is_loading = True
            
            project = persistance.load_project(self.filename)
            sequence.set_track_counts(project)
            
            editorstate.project_is_loading = False

        except persistance.FileProducerNotFoundError as e:
            print "did not find file:", e
            self._error_stop(dialog, ticker)
            primary_txt = _("Media asset was missing!")
            secondary_txt = _("Path of missing asset:") + "\n   <b>" + e.value  + "</b>\n\n" + \
                            _("Relative search for replacement file in sub folders of project file failed.") + "\n\n" + \
                            _("To load the project you will need to either:") + "\n" + \
                            u"\u2022" + " " + _("Use 'Media Linker' tool to relink media assets to new files, or") + "\n" + \
                            u"\u2022" + " " + _("Place a file with the same exact name and path on the hard drive")
            dialogutils.warning_message(primary_txt, secondary_txt, None, is_info=False)
            editorstate.project = old_project # persistance.load_project() changes this,
                                              # we simply change it back as no GUI or other state is yet changed
            return
        except persistance.ProjectProfileNotFoundError as e:
            self._error_stop(dialog, ticker)
            primary_txt = _("Profile with Description: '") + e.value + _("' was not found on load!")
            secondary_txt = _("It is possible to load the project by creating a User Profile with exactly the same Description\nas the missing profile. ") + "\n\n" + \
                            _("User Profiles can be created by selecting 'Edit->Profiles Manager'.")
            dialogutils.warning_message(primary_txt, secondary_txt, None, is_info=False)
            editorstate.project = old_project # persistance.load_project() changes this,
                                              # we simply change it back as no GUI or other state is yet changed
            return

        gtk.gdk.threads_enter()
        dialog.info.set_text(_("Opening"))
        gtk.gdk.threads_leave()

        time.sleep(0.3)

        gtk.gdk.threads_enter()
        app.open_project(project)

        if self.block_recent_files: # naming flipped ????
            editorpersistance.add_recent_project_path(self.filename)
            editorpersistance.fill_recents_menu_widget(gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent'), open_recent_project)
        gtk.gdk.threads_leave()
        
        gtk.gdk.threads_enter()
        updater.set_info_icon(None)
        dialog.destroy()
        gtk.gdk.threads_leave()

        ticker.stop_ticker()

    def _error_stop(self, dialog, ticker):
        editorstate.project_is_loading = False
        gtk.gdk.threads_enter()
        updater.set_info_icon(None)
        dialog.destroy()
        gtk.gdk.threads_leave()
        ticker.stop_ticker()

            

class AddMediaFilesThread(threading.Thread):
    
    def __init__(self, filenames):
        threading.Thread.__init__(self)
        self.filenames = filenames

    def run(self): 
        gtk.gdk.threads_enter()
        watch = gtk.gdk.Cursor(gtk.gdk.WATCH)
        gui.editor_window.window.window.set_cursor(watch)
        gtk.gdk.threads_leave()

        duplicates = []
        succes_new_file = None
        filenames = self.filenames
        for new_file in filenames:
            (folder, file_name) = os.path.split(new_file)
            if PROJECT().media_file_exists(new_file):
                duplicates.append(file_name)
            else:
                try:
                    PROJECT().add_media_file(new_file)
                    succes_new_file = new_file
                except projectdata.ProducerNotValidError as err:
                    print err.__str__()
                    dialogs.not_valid_producer_dialog(err.value, gui.editor_window.window)
            
            gtk.gdk.threads_enter()
            gui.media_list_view.fill_data_model()
            max_val = gui.editor_window.media_scroll_window.get_vadjustment().get_upper()
            gui.editor_window.media_scroll_window.get_vadjustment().set_value(max_val)
            gtk.gdk.threads_leave()

        if succes_new_file != None:
            editorpersistance.prefs.last_opened_media_dir = os.path.dirname(succes_new_file)
            editorpersistance.save()

        # Update editor gui
        gtk.gdk.threads_enter()
        gui.media_list_view.fill_data_model()
        gui.bin_list_view.fill_data_model()
        _enable_save()

        normal_cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR) #RTL
        gui.editor_window.window.window.set_cursor(normal_cursor)
        gtk.gdk.threads_leave()

        if len(duplicates) > 0:
            gobject.timeout_add(10, _duplicates_info, duplicates)

def _duplicates_info(duplicates):
    primary_txt = _("Media files already present in project were opened!")
    MAX_DISPLAYED_ITEMS = 3
    items = MAX_DISPLAYED_ITEMS
    if len(duplicates) < MAX_DISPLAYED_ITEMS:
        items = len(duplicates)
    
    secondary_txt = _("Files already present:\n\n")
    for i in range(0, items):
        secondary_txt = secondary_txt + "<b>" + duplicates[i] + "</b>" + "\n"
    
    if len(duplicates) > MAX_DISPLAYED_ITEMS:
        secondary_txt = secondary_txt + "\n" + "and " + str(len(duplicates) - MAX_DISPLAYED_ITEMS) + " other items.\n"
    
    secondary_txt = secondary_txt +  "\nNo duplicate media items were added to project."
    
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
    return False

def _load_pulse_bar():
    gtk.gdk.threads_enter()
    try: 
        persistance.load_dialog.progress_bar.pulse()
    except:
        pass
    gtk.gdk.threads_leave()

def _enable_save():
    gui.editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(True)


# ---------------------------------- project: new, load, save
def new_project():
    dialogs.new_project_dialog(_new_project_dialog_callback)

def _new_project_dialog_callback(dialog, response_id, profile_combo, tracks_combo, 
                                 tracks_combo_values_list):
    v_tracks, a_tracks = tracks_combo_values_list[tracks_combo.get_active()]
    if response_id == gtk.RESPONSE_ACCEPT:
        app.new_project(profile_combo.get_active(), v_tracks, a_tracks)
        dialog.destroy()
        project_event = projectdata.ProjectEvent(projectdata.EVENT_CREATED_BY_NEW_DIALOG, None)
        PROJECT().events.append(project_event)
    else:
        dialog.destroy()

def load_project():
    dialogs.load_project_dialog(_load_project_dialog_callback)
    
def _load_project_dialog_callback(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        filenames = dialog.get_filenames()
        dialog.destroy()
        actually_load_project(filenames[0])
    else:
        dialog.destroy()

def close_project():
    dialogs.close_confirm_dialog(_close_dialog_callback, app.get_save_time_msg(), gui.editor_window.window, editorstate.PROJECT().name)

def _close_dialog_callback(dialog, response_id):
    dialog.destroy()
    if response_id == gtk.RESPONSE_CLOSE:# "Don't Save"
        pass
    elif response_id ==  gtk.RESPONSE_YES:# "Save"
        if editorstate.PROJECT().last_save_path != None:
            persistance.save_project(editorstate.PROJECT(), editorstate.PROJECT().last_save_path)
        else:
            dialogutils.warning_message(_("Project has not been saved previously"), 
                                    _("Save project with File -> Save As before closing."),
                                    gui.editor_window.window)
            return
    else: # "Cancel"
        return
        
    # This is the same as opening default project
    sequence.AUDIO_TRACKS_COUNT = 4
    sequence.VIDEO_TRACKS_COUNT = 5

    new_project = projectdata.get_default_project()
    app.open_project(new_project)
    
def actually_load_project(filename, block_recent_files=False):
    load_launch = LoadThread(filename, block_recent_files)
    load_launch.start()

def save_project():
    if PROJECT().last_save_path == None:
        save_project_as()
    else:
        _save_project_in_last_saved_path()

def _save_project_in_last_saved_path():
    updater.set_info_icon(gtk.STOCK_SAVE)

    PROJECT().events.append(projectdata.ProjectEvent(projectdata.EVENT_SAVED, PROJECT().last_save_path))

    persistance.save_project(PROJECT(), PROJECT().last_save_path) #<----- HERE

    global save_icon_remove_event_id
    save_icon_remove_event_id = gobject.timeout_add(500, remove_save_icon)

    global save_time
    save_time = time.clock()
    
    projectinfogui.update_project_info()
        
def save_project_as():
    if  PROJECT().last_save_path != None:
        open_dir = os.path.dirname(PROJECT().last_save_path)
    else:
        open_dir = None
    dialogs.save_project_as_dialog(_save_as_dialog_callback, PROJECT().name, open_dir)
    
def _save_as_dialog_callback(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        filenames = dialog.get_filenames()
        PROJECT().last_save_path = filenames[0]
        PROJECT().name = os.path.basename(filenames[0])
        updater.set_info_icon(gtk.STOCK_SAVE)

        if len(PROJECT().events) == 0: # Save as... with 0 project events is considered Project creation
            p_event = projectdata.ProjectEvent(projectdata.EVENT_CREATED_BY_SAVING, PROJECT().last_save_path)
            PROJECT().events.append(p_event)
        else:
            p_event = projectdata.ProjectEvent(projectdata.EVENT_SAVED_AS, (PROJECT().name, PROJECT().last_save_path))
            PROJECT().events.append(p_event)
            
        persistance.save_project(PROJECT(), PROJECT().last_save_path) #<----- HERE
        
        app.stop_autosave()
        app.start_autosave()
        
        global save_icon_remove_event_id
        save_icon_remove_event_id = gobject.timeout_add(500, remove_save_icon)

        global save_time
        save_time = time.clock()

        gui.editor_window.window.set_title(PROJECT().name + " - Flowblade")        
        gui.editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(False)
        gui.editor_window.uimanager.get_widget("/MenuBar/EditMenu/Undo").set_sensitive(False)
        gui.editor_window.uimanager.get_widget("/MenuBar/EditMenu/Redo").set_sensitive(False)

        editorpersistance.add_recent_project_path(PROJECT().last_save_path)
        editorpersistance.fill_recents_menu_widget(gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent'), open_recent_project)
        
        projectinfogui.update_project_info()
        
        dialog.destroy()
    else:
        dialog.destroy()

def save_backup_snapshot():
    parts = PROJECT().name.split(".")
    name = parts[0] + datetime.datetime.now().strftime("-%y%m%d") + ".flb"
    dialogs.save_backup_snapshot(name, _save_backup_snapshot_dialog_callback)

def _save_backup_snapshot_dialog_callback(dialog, response_id, project_folder, name_entry):  
    if response_id == gtk.RESPONSE_ACCEPT:

        root_path = project_folder.get_filenames()[0]
        if not (os.listdir(root_path) == []):
            dialog.destroy()
            primary_txt = _("Selected folder contains files")
            secondary_txt = _("When saving a back-up snapshot of the project, the selected folder\nhas to be empty.")
            dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
            return

        name = name_entry.get_text()
        dialog.destroy()
        
        glib.idle_add(lambda : _do_snapshot_save(root_path + "/", name))

    else:
        dialog.destroy()

def _do_snapshot_save(root_folder_path, project_name):
    save_thread = SnaphotSaveThread(root_folder_path, project_name)
    save_thread.start()


class SnaphotSaveThread(threading.Thread):
    
    def __init__(self, root_folder_path, project_name):
        self.root_folder_path = root_folder_path
        self.project_name = project_name
        threading.Thread.__init__(self)

    def run(self):
        copy_txt = _("Copying project media assets")
        project_txt = _("Saving project file")
        
        gtk.gdk.threads_enter()
        dialog = dialogs.save_snaphot_progess(copy_txt, project_txt)
        gtk.gdk.threads_leave()
        
        media_folder = self.root_folder_path +  "media/"

        d = os.path.dirname(media_folder)
        os.mkdir(d)

        asset_paths = {}

        # Copy media files
        for idkey, media_file in PROJECT().media_files.items():
            if media_file.type == appconsts.PATTERN_PRODUCER:
                continue

            # Copy asset file and fix path
            directory, file_name = os.path.split(media_file.path)
            gtk.gdk.threads_enter()
            dialog.media_copy_info.set_text(copy_txt + "... " +  file_name)
            gtk.gdk.threads_leave()
            media_file_copy = media_folder + file_name
            if media_file_copy in asset_paths: # Create different filename for files 
                                               # that have same filename but different path
                file_name = get_snapshot_unique_name(media_file.path, file_name)
                media_file_copy = media_folder + file_name
                
            shutil.copyfile(media_file.path, media_file_copy)
            asset_paths[media_file.path] = media_file_copy

        # Copy clip producers paths
        for seq in PROJECT().sequences:
            for track in seq.tracks:
                for i in range(0, len(track.clips)):
                    clip = track.clips[i]
                    # Only producer clips are affected
                    if (clip.is_blanck_clip == False and (clip.media_type != appconsts.PATTERN_PRODUCER)):
                        directory, file_name = os.path.split(clip.path)
                        clip_file_copy = media_folder + file_name
                        if not os.path.isfile(clip_file_copy):
                            directory, file_name = os.path.split(clip.path)
                            gtk.gdk.threads_enter()
                            dialog.media_copy_info.set_text(copy_txt + "... " +  file_name)
                            gtk.gdk.threads_leave()
                            shutil.copyfile(clip.path, clip_file_copy) # only rendered files are copied here
                            asset_paths[clip.path] = clip_file_copy # This stuff is already md5 hashed, so no duplicate problems here
            for compositor in seq.compositors:
                if compositor.type_id == "##wipe": # Wipe may have user luma and needs to be looked up relatively
                    copy_comp_resourse_file(compositor, "resource", media_folder)
                if compositor.type_id == "##region": # Wipe may have user luma and needs to be looked up relatively
                    copy_comp_resourse_file(compositor, "composite.luma", media_folder)

        gtk.gdk.threads_enter()
        dialog.media_copy_info.set_text(copy_txt + "    " +  u"\u2713")
        gtk.gdk.threads_leave()
        
        save_path = self.root_folder_path + self.project_name

        persistance.snapshot_paths = asset_paths
        persistance.save_project(PROJECT(), save_path)
        persistance.snapshot_paths = None

        gtk.gdk.threads_enter()
        dialog.saving_project_info.set_text(project_txt + "    " +  u"\u2713")
        gtk.gdk.threads_leave()

        time.sleep(2)

        gtk.gdk.threads_enter()
        dialog.destroy()
        gtk.gdk.threads_leave()
        
        project_event = projectdata.ProjectEvent(projectdata.EVENT_SAVED_SNAPSHOT, self.root_folder_path)
        PROJECT().events.append(project_event)

        gtk.gdk.threads_enter()
        projectinfogui.update_project_info()
        gtk.gdk.threads_leave()

def get_snapshot_unique_name(file_path, file_name):
    (name, ext) = os.path.splitext(file_name)
    return md5.new(file_path).hexdigest() + ext

def copy_comp_resourse_file(compositor, res_property, media_folder):
    res_path = propertyparse.get_property_value(compositor.transition.properties, res_property)
    directory, file_name = os.path.split(res_path)
    res_file_copy = media_folder + file_name
    if not os.path.isfile(res_file_copy):
        shutil.copyfile(res_path, res_file_copy)
                        
def remove_save_icon():
    gobject.source_remove(save_icon_remove_event_id)
    updater.set_info_icon(None)

def open_recent_project(widget, index):
    path = editorpersistance.recent_projects.projects[index]
    if not os.path.exists(path):
        editorpersistance.recent_projects.projects.pop(index)
        editorpersistance.fill_recents_menu_widget(gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent'), open_recent_project)
        primary_txt = _("Project not found on disk")
        secondary_txt = _("Project can't be loaded.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    actually_load_project(path)

# ---------------------------------- rendering
def do_rendering():
    editevent.insert_move_mode_pressed()
    render.render_timeline()

def add_to_render_queue():
    args_vals_list = render.get_args_vals_list_for_current_selections()
    render_path = render.get_file_path()

    # Get render start and end points
    if render.widgets.range_cb.get_active() == 0:
        start_frame = 0
        end_frame = -1 # renders till finish
    else:
        start_frame = current_sequence().tractor.mark_in
        end_frame = current_sequence().tractor.mark_out
    
    # Only do if range defined.
    if start_frame == -1 or end_frame == -1:
        if render.widgets.range_cb.get_active() == 1:
            rendergui.no_good_rander_range_info()
            return

    # Create render data object
    if render.widgets.args_panel.use_args_check.get_active() == False:
        enc_index = render.widgets.encoding_panel.encoding_selector.widget.get_active()
        quality_index = render.widgets.encoding_panel.quality_selector.widget.get_active()
        user_args = False
    else: # This is not implemented
        enc_index = render.widgets.encoding_panel.encoding_selector.widget.get_active()
        quality_index = render.widgets.encoding_panel.quality_selector.widget.get_active()
        user_args = False

    profile = render.get_current_profile()
    profile_text = guicomponents.get_profile_info_text(profile)
    fps = profile.fps()
    profile_name = profile.description()
    r_data = batchrendering.RenderData(enc_index, quality_index, user_args, profile_text, profile_name, fps) 

    # Add item
    try:
        batchrendering.add_render_item(PROJECT(), 
                                       render_path,
                                       args_vals_list,
                                       start_frame,
                                       end_frame,
                                       r_data)
    except Exception as e:
        primary_txt = _("Adding item to render queue failed!")
        secondary_txt = _("Error message: ") + str(e)
        dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window, is_info=False)
        return

    #primary_txt = "New Render Item File Added to Queue"
    #secondary_txt = "Select <b>'Render->Batch Render Queue'</b> from menu\nto launch render queue application.\n" #Press <b>'Reload Queue'</b> button to load new item\ninto queue if application already running."
    #dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)


# ----------------------------------- media files
def add_media_files(this_call_is_retry=False):
    """
    User selects a media file to added to current bin.
    """
    # User neds to select thumbnail folder when promted to complete action
    if editorpersistance.prefs.thumbnail_folder == None:
        if this_call_is_retry == True:
            return

        dialogs.select_thumbnail_dir(select_thumbnail_dir_callback, gui.editor_window.window, os.path.expanduser("~"), True)
        return

    dialogs.media_file_dialog(_("Open.."), _open_files_dialog_cb, True)

def _open_files_dialog_cb(file_select, response_id):
    filenames = file_select.get_filenames()
    file_select.destroy()

    if response_id != gtk.RESPONSE_OK:
        return
    if len(filenames) == 0:
        return

    add_media_thread = AddMediaFilesThread(filenames)
    add_media_thread.start()

def add_image_sequence():
    dialogs.open_image_sequence_dialog(_add_image_sequence_callback, gui.editor_window.window)

def _add_image_sequence_callback(dialog, response_id, data):
    if response_id == gtk.RESPONSE_CANCEL:
        dialog.destroy()
        return

    file_chooser, spin = data
    frame_file = file_chooser.get_filename()
    dialog.destroy()
    
    if frame_file == None:
        dialogutils.info_message(_("No file was selected"), _("Select a numbered file to add an Image Sequence to Project."), gui.editor_window.window)
        return
    
    (folder, file_name) = os.path.split(frame_file)
    try:
        number_parts = re.findall("[0-9]+", file_name)
        number_part = number_parts[-1] # we want the last number part 
    except:
        dialogutils.info_message(_("Not a sequence file!"), _("Selected file does not have a number part in it,\nso it can't be an image sequence file."), gui.editor_window.window)
        return

    # Create resource name with MLT syntax for MLT producer
    number_index = file_name.find(number_part)
    path_name_part = file_name[0:number_index]
    end_part = file_name[number_index + len(number_part):len(file_name)]
    
    # The better version with "?begin=xxx" only available after 0.8.7
    if editorstate.mlt_version_is_equal_or_greater("0.8.5"):
        resource_name_str = path_name_part + "%" + "0" + str(len(number_part)) + "d" + end_part + "?begin=" + number_part
    else:
        resource_name_str = path_name_part + "%" + "0" + str(len(number_part)) + "d" + end_part
    
    # detect highest file
    # FIX: this fails if two similarily numbered sequences in same dir and both have same substring in frame name
    onlyfiles = [ f for f in listdir(folder) if isfile(join(folder,f)) ]
    highest_number_part = int(number_part)
    for f in onlyfiles:
        try:
            file_number_part = int(re.findall("[0-9]+", f)[-1]) # -1, we want the last number part 
        except:
            continue
        if f.find(path_name_part) == -1:
            continue
        if file_number_part > highest_number_part:
            highest_number_part = file_number_part
    
    dialog.destroy()
    
    resource_path = folder + "/" + resource_name_str
    length = highest_number_part - int(number_part)

    PROJECT().add_image_sequence_media_object(resource_path, file_name + "(img_seq)", length)

    gui.media_list_view.fill_data_model()
    gui.bin_list_view.fill_data_model()

def open_rendered_file(rendered_file_path):
    add_media_thread = AddMediaFilesThread([rendered_file_path])
    add_media_thread.start()

def select_thumbnail_dir_callback(dialog, response_id, data):
    file_select, retry_add_media = data
    folder = file_select.get_filenames()[0]
    dialog.destroy()
    if response_id == gtk.RESPONSE_YES:
        if folder ==  os.path.expanduser("~"):
            dialogutils.warning_message(_("Can't make home folder thumbnails folder"), 
                                    _("Please create and select some other folder then \'") + 
                                    os.path.expanduser("~") + _("\' as thumbnails folder"), 
                                    gui.editor_window.window)
        else:
            editorpersistance.prefs.thumbnail_folder = folder
            editorpersistance.save()
    
    if retry_add_media == True:
        add_media_files(True)

def select_render_clips_dir_callback(dialog, response_id, file_select):
    folder = file_select.get_filenames()[0]
    dialog.destroy()
    if response_id == gtk.RESPONSE_YES:
        if folder ==  os.path.expanduser("~"):
            dialogs.rendered_clips_no_home_folder_dialog()
        else:
            editorpersistance.prefs.render_folder = folder
            editorpersistance.save()

def delete_media_files(force_delete=False):
    """
    Deletes media file. Does not take into account if clips made from 
    media file are still in sequence.(maybe change this)
    """
    selection = gui.media_list_view.get_selected_media_objects()
    if len(selection) < 1:
        return
    
    file_ids = []
    bin_indexes = []
    # Get:
    # - list of integer keys to delete from Project.media_files
    # - list of indexes to delete from Bin.file_ids
    for media_obj in selection:
        file_id = media_obj.media_file.id
        file_ids.append(file_id)
        bin_indexes.append(media_obj.bin_index)

        # If clip is displayed in monitor clear it and disable clip button.
        if media_obj.media_file == MONITOR_MEDIA_FILE:
            editorstate._monitor_media_file = None
            gui.clip_editor_b.set_sensitive(False)

    # Check for proxy rendering issues if not forced delete
    if not force_delete:
        proxy_issues = False
        for file_id in file_ids:
            media_file = PROJECT().media_files[file_id]
            if media_file.has_proxy_file == True:
                proxy_issues = True
            if media_file.is_proxy_file == True:
                proxy_issues = True
            if proxy_issues:
                dialogs.proxy_delete_warning_dialog(gui.editor_window.window, _proxy_delete_warning_callback)
                return

    # Delete from bin
    bin_indexes.sort()
    bin_indexes.reverse()
    for i in bin_indexes:
        current_bin().file_ids.pop(i)
        
    # Delete from project
    for file_id in file_ids:
        PROJECT().media_files.pop(file_id)

    gui.media_list_view.fill_data_model()

    _enable_save()

def _proxy_delete_warning_callback(dialog, response_id):
    dialog.destroy()
    if response_id == gtk.RESPONSE_OK:
        delete_media_files(True)

def display_media_file_rename_dialog(media_file):
    dialogs.new_media_name_dialog(media_file_name_edited, media_file)

def media_file_name_edited(dialog, response_id, data):
    """
    Sets edited value to liststore and project data.
    """
    name_entry, media_file = data
    new_text = name_entry.get_text()
    dialog.destroy()
            
    if response_id != gtk.RESPONSE_ACCEPT:
        return      
    if len(new_text) == 0:
        return

    media_file.name = new_text
    gui.media_list_view.fill_data_model()

def _display_file_info(media_file):
    clip = current_sequence().create_file_producer_clip(media_file.path)

    width = clip.get("width")
    height = clip.get("height")
    size = str(width) + " x " + str(height)
    length = utils.get_tc_string(clip.get_length())

    try:
        img = guiutils.get_gtk_image_from_file(media_file.icon_path, 300)
    except:
        print "_display_file_info() failed to get thumbnail"

    video_index = clip.get_int("video_index")
    audio_index = clip.get_int("audio_index")
    long_video_property = "meta.media." + str(video_index) + ".codec.long_name"
    long_audio_property = "meta.media." + str(audio_index) + ".codec.long_name"
    vcodec = clip.get(str(long_video_property))
    acodec = clip.get(str(long_audio_property))
    
    frame = clip.get_frame()
    channels = str(frame.get_int("channels"))
    frequency = str(frame.get_int("frequency")) + "Hz"
    try:
        num = float(clip.get("meta.media.frame_rate_num")) # from producer_avformat.c
        den = float(clip.get("meta.media.frame_rate_den")) # from producer_avformat.c
        fps = str(num/den)
    except:
        fps ="N/A"
    
    dialogs.file_properties_dialog((media_file, img, size, length, vcodec, acodec, channels, frequency, fps))

def remove_unused_media():
    # Create path -> media item dict
    path_to_media_object = {}
    for key, media_item in PROJECT().media_files.items():
        if media_item.path != "" and media_item.path != None:
            path_to_media_object[media_item.path] = media_item
    
    # Remove all items from created dict that have a clip with same path on any of the sequences
    for seq in PROJECT().sequences:
        for track in seq.tracks:
            for clip in track.clips:
                try:
                    removed = path_to_media_object.pop(clip.path)
                    print "Removed: " + removed.path
                except:
                    pass
    
    # Create a list of unused media objects
    unused = []
    for path, media_item in path_to_media_object.items():
        unused.append(media_item)
    
    # It is most convenient to do remove via gui object
    gui.media_list_view.select_media_file_list(unused)
    delete_media_files()

def media_filtering_select_pressed(widget, event):
    guicomponents.get_file_filter_popup_menu(widget, event, _media_filtering_selector_item_activated)

def _media_filtering_selector_item_activated(selector, index):
    gui.media_view_filter_selector.set_pixbuf(index)
    
    # Const value correspond with indexes here
    editorstate.media_view_filter = index
    gui.media_list_view.fill_data_model()


# ------------------------------------ bins
def add_new_bin():
    """
    Adds new unnamed bin and sets it selected 
    """
    PROJECT().add_unnamed_bin()
    gui.bin_list_view.fill_data_model()
    selection = gui.bin_list_view.treeview.get_selection()
    model, iterator = selection.get_selected()
    selection.select_path(str(len(model)-1))
    _enable_save()

def delete_selected_bin():
    """
    Deletes current bin if it's empty and at least one will be left.
    """
    if len(current_bin().file_ids) != 0:
        dialogutils.warning_message(_("Can't remove a non-empty bin"), 
                                _("You must remove all files from the bin before deleting it."),
                                gui.editor_window.window)
        return
    
    # Get iter and index for (current) selected bin
    selection = gui.bin_list_view.treeview.get_selection()
    model, iter = selection.get_selected()
    if len(model) < 2:
        dialogutils.warning_message(_("Can't remove last bin"), 
                                _("There must always exist at least one bin."),
                                gui.editor_window.window)
        return 
    (model, rows) = selection.get_selected_rows()
    row = max(rows[0])
    
    # Remove from gui and project data
    model.remove(iter)
    PROJECT().bins.pop(row)
    
    # Set first bin selected, listener 'bin_selection_changed' updates editorstate.project.c_bin
    selection.select_path("0")
    _enable_save()
                  
def bin_name_edited(cell, path, new_text, user_data):
    """
    Sets edited value to liststore and project data.
    """
    # Can't have empty string names
    if len(new_text) == 0:
        return
    
    liststore, column = user_data
    liststore[path][column] = new_text
    PROJECT().bins[int(path)].name = new_text
    _enable_save()

def bin_selection_changed(selection):
    """
    Sets first selected row as current bin and displays media files in it
    if we get a selection with contents, empty selections caused by 
    adding / deleting bins are discarded.
    """
    # Get index for selected bin
    (model, rows) = selection.get_selected_rows()
    if len(rows) == 0:
        return
    row = max(rows[0])
    
    # Set current and display
    PROJECT().c_bin = PROJECT().bins[row]
    gui.media_list_view.fill_data_model()
    
def move_files_to_bin(new_bin, bin_indexes):
    # If we're moving clips to bin that they're already in, do nothing.
    if PROJECT().bins[new_bin] == current_bin():
        return

    # Delete from current bin
    moved_ids = []
    bin_indexes.sort()
    bin_indexes.reverse()
    for i in bin_indexes:
        moved_ids.append(current_bin().file_ids.pop(i))
        
    # Add to target bin
    for file_id in moved_ids:
        PROJECT().bins[new_bin].file_ids.append(file_id)

    gui.media_list_view.fill_data_model()
    gui.bin_list_view.fill_data_model()

    
    
# ------------------------------------ sequences
def change_edit_sequence():
    selection = gui.sequence_list_view.treeview.get_selection()
    (model, rows) = selection.get_selected_rows()
    row = max(rows[0])
    current_index = PROJECT().sequences.index(current_sequence())
    if row == current_index:
        dialogutils.warning_message(_("Selected sequence is already being edited"), 
                                _("Select another sequence. Press Add -button to create a\nnew sequence if needed."),
                                gui.editor_window.window)
        return 
    # Clear clips selection at exit. This is transient user focus state and
    # therefore is not saved.
    movemodes.clear_selected_clips()
    
    app.change_current_sequence(row)

def add_new_sequence():
    default_name = _("sequence_") + str(PROJECT().next_seq_number)
    dialogs.new_sequence_dialog(_add_new_sequence_dialog_callback, default_name)

def _add_new_sequence_dialog_callback(dialog, response_id, widgets):    
    """
    Adds new unnamed sequence and sets it selected 
    """
    if response_id != gtk.RESPONSE_ACCEPT:
        dialog.destroy()
        return
    
    name_entry, tracks_combo, open_check = widgets
    
    # Get dialog data 
    name = name_entry.get_text()

    if len(name) == 0:
        name = _("sequence_") + str(PROJECT().next_seq_number)
    v_tracks, a_tracks = appconsts.TRACK_CONFIGURATIONS[tracks_combo.get_active()]
    open_right_away = open_check.get_active()
    
    # Get index for selected sequence
    selection = gui.sequence_list_view.treeview.get_selection()
    (model, rows) = selection.get_selected_rows()
    row = max(rows[0])
    
    # Add new sequence
    sequence.AUDIO_TRACKS_COUNT = a_tracks
    sequence.VIDEO_TRACKS_COUNT = v_tracks
    PROJECT().add_named_sequence(name)
    gui.sequence_list_view.fill_data_model()
    
    if open_right_away == False:
        selection.select_path(str(row)) # Keep previous selection
    else:
        app.change_current_sequence(len(PROJECT().sequences) - 1)
    
    dialog.destroy()

def delete_selected_sequence():
    """
    Deletes selected sequence if confirmed and at least one will be left.
    """
    selection = gui.sequence_list_view.treeview.get_selection()
    model, iter = selection.get_selected()
    (model, rows) = selection.get_selected_rows()
    row = max(rows[0])
    name = PROJECT().sequences[row].name
    
    dialogutils.warning_confirmation(_delete_confirm_callback, 
                                 _("Are you sure you want to delete\nsequence \'") + name + _("\'?"), 
                                 _("This operation can not be undone. Sequence will be permanently lost."), 
                                 gui.editor_window.window)

def _delete_confirm_callback(dialog, response_id):
    if response_id != gtk.RESPONSE_ACCEPT:
        dialog.destroy()
        return
        
    dialog.destroy()

    selection = gui.sequence_list_view.treeview.get_selection()
    model, iter = selection.get_selected()

    # Have to have one sequence.
    if len(model) < 2:
        dialogutils.warning_message(_("Can't remove last sequence"), 
                                _("There must always exist at least one sequence."),
                                gui.editor_window.window)
        return

    (model, rows) = selection.get_selected_rows()
    row = max(rows[0])
    current_index = PROJECT().sequences.index(current_sequence())

    # Remove sequence from gui and project data
    model.remove(iter)
    PROJECT().sequences.pop(row)
    
    # If we deleted current sequence, open first sequence
    if row == current_index:
        app.change_current_sequence(0)
    
    _enable_save()

def sequence_name_edited(cell, path, new_text, user_data):
    """
    Sets edited value to liststore and project data.
    """
    # Can't have empty string names
    if len(new_text) == 0:
        return

    liststore, column = user_data
    liststore[path][column] = new_text
    PROJECT().sequences[int(path)].name = new_text

    _enable_save()

def change_sequence_track_count():
    dialogs.tracks_count_change_dialog(_change_track_count_dialog_callback)

def _change_track_count_dialog_callback(dialog, response_id, tracks_combo):
    if response_id != gtk.RESPONSE_ACCEPT:
        dialog.destroy()
        return
    
    v_tracks, a_tracks = appconsts.TRACK_CONFIGURATIONS[tracks_combo.get_active()]
    dialog.destroy()

    cur_seq_index = PROJECT().sequences.index(PROJECT().c_seq)
    new_seq = sequence.create_sequence_clone_with_different_track_count(PROJECT().c_seq, v_tracks, a_tracks)
    PROJECT().sequences.insert(cur_seq_index, new_seq)
    PROJECT().sequences.pop(cur_seq_index + 1)
    app.change_current_sequence(cur_seq_index)

# --------------------------------------------------------- pop-up menus
def media_file_menu_item_selected(widget, data):
    item_id, media_file, event = data
    if item_id == "File Properties":
        _display_file_info(media_file)
    if item_id == "Open in Clip Monitor":
        updater.set_and_display_monitor_media_file(media_file)
    if item_id == "Render Slow/Fast Motion File":
        render.render_frame_buffer_clip(media_file)
    if item_id == "Rename":
        display_media_file_rename_dialog(media_file)
    if item_id == "Delete":
        gui.media_list_view.select_media_file(media_file)
        delete_media_files()
    if item_id == "Render Proxy File":
        proxyediting.create_proxy_menu_item_selected(media_file)

def _select_treeview_on_pos_and_return_row_and_column_title(event, treeview):
    selection = treeview.get_selection()
    path_pos_tuple = treeview.get_path_at_pos(int(event.x), int(event.y))
    if path_pos_tuple == None:
        return (-1, -1) # Empty row was clicked
    path, column, x, y = path_pos_tuple
    title = column.get_title()
    selection.unselect_all()
    selection.select_path(path)
    (model, rows) = selection.get_selected_rows()
    row = max(rows[0])
    return (row, title)



