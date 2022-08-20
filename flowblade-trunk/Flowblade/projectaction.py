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

import datetime
import glob
import hashlib
try:
    import mlt7 as mlt
except:
    import mlt7 as mlt
import os
from os import listdir
from os.path import isfile, join, expanduser
from PIL import Image
import re
import shutil
import time
import threading

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

import app
import audiowaveformrenderer
import appconsts
import batchrendering
import containerprogramedit
import clipeffectseditor
import compositeeditor
import containerclip
import dialogs
import dialogutils
import gui
import guicomponents
import guiutils
import edit
import editorstate
from editorstate import current_sequence
from editorstate import current_bin
from editorstate import PROJECT
from editorstate import PLAYER
from editorstate import MONITOR_MEDIA_FILE
from editorstate import EDIT_MODE
import editorpersistance
import kftoolmode
import medialinker
import medialog
import modesetting
import movemodes
import mltprofiles
import persistance
import projectdata
import projectinfogui
import projectmediaimport
import propertyparse
import proxyediting
import render
import renderconsumer
import rendergui
import sequence
import tlinerender
import undo
import updater
import userfolders
import utils

media_panel_popup_menu = Gtk.Menu()
bin_popup_menu = Gtk.Menu()
sequence_popup_menu = Gtk.Menu()
hamburger_popup_menu = Gtk.Menu()
compositing_mode_menu = Gtk.Menu()

save_time = None
save_icon_remove_event_id = None

# Used to get some render confirmations
force_overwrite = False
force_proxy = False

# This is needed to pass only one event for double click, double init for monitor click possibly somewhat unstable
_media_panel_double_click_counter = 0


#--------------------------------------- worker threads
class LoadThread(threading.Thread):
    
    def __init__(self, filename, block_recent_files=False, is_first_video_load=False, is_autosave_load=False):
        self.filename = filename
        self.block_recent_files = block_recent_files
        self.is_first_video_load = is_first_video_load
        self.is_autosave_load = is_autosave_load
        threading.Thread.__init__(self)

    def run(self):
        Gdk.threads_enter()
        updater.set_info_icon(Gtk.STOCK_OPEN)

        dialog = dialogs.load_dialog()
        persistance.load_dialog = dialog
        Gdk.threads_leave()

        ticker = utils.Ticker(_load_pulse_bar, 0.15)
        ticker.start_ticker()

        old_project = editorstate.project
        try:
            editorstate.project_is_loading = True
            
            project = persistance.load_project(self.filename)

            sequence.set_track_counts(project)
            
            editorstate.project_is_loading = False

        except persistance.FileProducerNotFoundError as e:
            print("LoadThread.run() - FileProducerNotFoundError")
            self._error_stop(dialog, ticker)
            Gdk.threads_enter()
            primary_txt = _("Media asset was missing!")
            secondary_txt = _("Path of missing asset:") + "\n   <b>" + e.value + "</b>\n\n" + \
                            _("Relative search for replacement file in sub folders of project file failed.") + "\n\n" + \
                            _("To load the project you will need to either:") + "\n" + \
                            "\u2022" + " " + _("Open project in 'Media Relinker' tool to relink media assets to new files, or") + "\n" + \
                            "\u2022" + " " + _("Place a file with the same exact name and path on the hard drive")
            open_label = Gtk.Label(_("Open project in Media Relinker tool"))
            self.open_check = Gtk.CheckButton()
            self.open_check.set_active(True)
            check_row = Gtk.HBox(False, 1)
            check_row.pack_start(Gtk.Label(), True, True, 0)
            check_row.pack_start(self.open_check, False, False, 0)
            check_row.pack_start(open_label, False, False, 0)
            guiutils.set_margins(check_row,24,0,0,0)
            panels = [check_row]
            dialogutils.warning_message_with_panels(primary_txt, secondary_txt, 
                                                    gui.editor_window.window, 
                                                    False, self._missing_file_dialog_callback,
                                                    panels)
            editorstate.project = old_project # persistance.load_project() changes this,
                                              # we simply change it back as no GUI or other state is yet changed
            Gdk.threads_leave()
            return
        except persistance.ProjectProfileNotFoundError as e:
            self._error_stop(dialog, ticker)
            primary_txt = _("Profile with Description: '") + e.value  + _("' was not found on load!")
            secondary_txt = _("It is possible to load the project by creating a User Profile with exactly the same Description\nas the missing profile. ") + "\n\n" + \
                            _("User Profiles can be created by selecting 'Edit->Profiles Manager'.")
            dialogutils.warning_message(primary_txt, secondary_txt, None, is_info=False)
            editorstate.project = old_project # persistance.load_project() changes this,
                                              # we simply change it back as no GUI or other state is yet changed
            return

        Gdk.threads_enter()
        dialog.info.set_text(_("Opening"))
        Gdk.threads_leave()

        time.sleep(0.3)

        Gdk.threads_enter()
        
        app.open_project(project) # <-- HERE

        if self.block_recent_files: # naming flipped ????
            editorpersistance.add_recent_project_path(self.filename)
            gui.editor_window.fill_recents_menu_widget(gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent'), open_recent_project)
        Gdk.threads_leave()
        
        Gdk.threads_enter()
        selections = project.get_project_property(appconsts.P_PROP_LAST_RENDER_SELECTIONS)
        if selections != None:
            render.set_saved_gui_selections(selections)
        updater.set_info_icon(None)

        if self.is_autosave_load == False: # project loaded with autosave needs to keep its last_save_path data.
            # If project file is moved since last save we need to update last_save_path property and save to get everything working as expected.
            if self.filename != editorstate.project.last_save_path:
                print("Project file moved since last save, save with updated last_save_path data.")
                editorstate.project.last_save_path = self.filename
                editorstate.project.name = os.path.basename(self.filename)
                _save_project_in_last_saved_path()
        else:
            print("autosave load")

        dialog.destroy()
        gui.tline_canvas.connect_mouse_events() # mouse events during load cause crashes because there is no data to handle
        Gdk.threads_leave()

        # First video load is a media file change and needs to set flag for it
        # whereas other loads clear the flag above.
        if self.is_first_video_load == True:
            projectdata.media_files_changed_since_last_save = True
            project.last_save_path = None # This gets set to the temp file saved to change profile which is not correct.

        ticker.stop_ticker()

    def _error_stop(self, dialog, ticker):
        editorstate.project_is_loading = False
        Gdk.threads_enter()
        updater.set_info_icon(None)
        dialog.destroy()
        Gdk.threads_leave()
        ticker.stop_ticker()

    def _missing_file_dialog_callback(self, dialog, response_id):
        if self.open_check.get_active() == True:
            medialinker.display_linker(self.filename)
            dialog.destroy()
        else:
            dialog.destroy()


class AddMediaFilesThread(threading.Thread):
    
    def __init__(self, filenames, compound_clip_name=None):
        threading.Thread.__init__(self)
        self.filenames = filenames
        self.compound_clip_name = compound_clip_name # Compound clips saved in hidden folder need this name displayed to user, not the md5 hash.
                                                     # Underlying reason, XML clip creation overwrites existing profile objects property values, https://github.com/mltframework/mlt/issues/212
    def run(self): 
        Gdk.threads_enter()
        watch = Gdk.Cursor.new(Gdk.CursorType.WATCH)
        gui.editor_window.window.get_window().set_cursor(watch)
        Gdk.threads_leave()

        is_first_video_load = PROJECT().is_first_video_load()
        duplicates = []
        anim_gif_name = None
        extension_refused = []
        target_bin = PROJECT().c_bin
        succes_new_file = None
        filenames = self.filenames
        for new_file in filenames:
            (folder, file_name) = os.path.split(new_file)
            
            # Refuse to load animated gifs
            extension = os.path.splitext(file_name)[1].lower()
            if extension == ".gif":
                 if Image.open(new_file).is_animated == True:
                     anim_gif_name = file_name
                     continue

            if extension == "" or extension == None:
                extension_refused.append(new_file)
                continue
            
            media_type = utils.get_media_type(new_file)
            if media_type == appconsts.UNKNOWN:
                extension_refused.append(new_file)
                continue

            if PROJECT().media_file_exists(new_file):
                duplicates.append(file_name)
            else:
                try:
                    PROJECT().add_media_file(new_file, self.compound_clip_name, target_bin)
                    succes_new_file = new_file
                except projectdata.ProducerNotValidError as err:
                    Gdk.threads_enter()
                    dialogs.not_valid_producer_dialog(err.value, gui.editor_window.window)
                    Gdk.threads_leave()

            Gdk.threads_enter()
            gui.media_list_view.fill_data_model()
            max_val = gui.editor_window.media_scroll_window.get_vadjustment().get_upper()
            gui.editor_window.media_scroll_window.get_vadjustment().set_value(max_val)
            Gdk.threads_leave()

        add_count = len(filenames) - len(duplicates)
        project_event = projectdata.ProjectEvent(projectdata.EVENT_MEDIA_ADDED, str(add_count))
        PROJECT().events.append(project_event)
        
        if succes_new_file != None and self.compound_clip_name == None: # hidden rendered files folder for compound clips is not a last_opened_media_dir
            editorpersistance.prefs.last_opened_media_dir = os.path.dirname(succes_new_file)
            editorpersistance.save()

        # Update editor gui
        Gdk.threads_enter()
        gui.media_list_view.fill_data_model()
        update_current_bin_files_count()
        _enable_save()

        normal_cursor = Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR) #RTL
        gui.editor_window.window.get_window().set_cursor(normal_cursor)
        gui.editor_window.bin_info.display_bin_info()
        
        if anim_gif_name != None: # Tell we won't load animated gifs.
            primary_txt = _("Opening animated .gif file was refused!")
            secondary_txt = _("Flowblade does not support displaying animated GIF files as media objects.\n")
            secondary_txt = secondary_txt + _("A possible workaround is to render GIF into a frame sequence and\nopen that as a media item.")
            dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

        if len(extension_refused) > 0:
            primary_txt = _("Opening files with unknown  extensions refused!")
            secondary_txt = _("Flowblade does not open files that cannot be identified as media from file extensions.\nProblem files:\n\n")
            if len(extension_refused) > 10:
                secondary_txt = secondary_txt + _("Too many to list.\n")
            else:
                for bad_name in extension_refused:
                    secondary_txt = secondary_txt + bad_name + "\n"
                    
            secondary_txt = secondary_txt + _("\nAdd the correct extension to load a problem file.")
            dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
            
        Gdk.threads_leave()

        if len(duplicates) > 0:
            GObject.timeout_add(10, _duplicates_info, duplicates)

        if is_first_video_load:
            GObject.timeout_add(10, _first_load_profile_check)
            
        audiowaveformrenderer.launch_audio_levels_rendering(filenames)


class UpdateMediaLengthsThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print("Updating media lengths:")

        Gdk.threads_enter()
        dialog = dialogs.update_media_lengths_progress_dialog()
        time.sleep(0.1)
        Gdk.threads_leave()

        for key, media_file in PROJECT().media_files.items():
            if media_file.type == appconsts.VIDEO or media_file.type == appconsts.IMAGE_SEQUENCE:
                Gdk.threads_enter()
                dialog.info.set_text(media_file.name)
                Gdk.threads_leave()
        
                producer = mlt.Producer(PROJECT().profile, str(media_file.path))
                if producer.is_valid() == False:
                    print("not valid producer")
                    continue

                length = producer.get_length()
                media_file.length = length
                
        PROJECT().update_media_lengths_on_load = False
        
        Gdk.threads_enter()
        dialog.destroy()
        Gdk.threads_leave()
        
        print("Updating media lengths done.")
        
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
    
    secondary_txt = secondary_txt +  _("\nNo duplicate media items were added to project.")
    
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
    return False

def _first_load_profile_check():
    for uid, media_file in PROJECT().media_files.items():
        if media_file.type == appconsts.VIDEO:
            if media_file.matches_project_profile() == False:
                dialogs.not_matching_media_info_dialog(PROJECT(), media_file, _not_matching_media_info_callback)
                break

def _not_matching_media_info_callback(dialog, response_id, media_file):
    dialog.destroy()
    
    match_profile_index = mltprofiles.get_closest_matching_profile_index(media_file.info)
    profile = mltprofiles.get_profile_for_index(match_profile_index)
        
    if response_id == Gtk.ResponseType.ACCEPT:
        if EDIT_MODE() == editorstate.KF_TOOL:
            kftoolmode.exit_tool()
        # Save in hidden and open
        match_profile_index = mltprofiles.get_closest_matching_profile_index(media_file.info)
        profile = mltprofiles.get_profile_for_index(match_profile_index)
        path = userfolders.get_cache_dir() + "/" + PROJECT().name
        PROJECT().update_media_lengths_on_load = True
        
        persistance.save_project(PROJECT(), path, profile.description()) #<----- HERE
        
        actually_load_project(path, False, True)


def _load_pulse_bar():
    Gdk.threads_enter()
    try: 
        persistance.load_dialog.progress_bar.pulse()
    except:
        pass
    Gdk.threads_leave()

def _enable_save():
    gui.editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(True)


# ---------------------------------- project: new, load, save
def new_project():
    dialogs.new_project_dialog(_new_project_dialog_callback)

def _new_project_dialog_callback(dialog, response_id, profile_combo, tracks_select):

    v_tracks, a_tracks = tracks_select.get_tracks()
    
    if response_id == Gtk.ResponseType.ACCEPT:
        profile_name = profile_combo.get_selected()
        profile_index = mltprofiles.get_index_for_name(profile_name)
        app.new_project(profile_index, v_tracks, a_tracks)
        dialog.destroy()
        project_event = projectdata.ProjectEvent(projectdata.EVENT_CREATED_BY_NEW_DIALOG, None)
        PROJECT().events.append(project_event)
    else:
        dialog.destroy()

def load_project():
    dialogs.load_project_dialog(_load_project_dialog_callback)
    
def _load_project_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        filenames = dialog.get_filenames()
        dialog.destroy()
        actually_load_project(filenames[0])
    else:
        dialog.destroy()

def close_project():
    if was_edited_since_last_save() == False:
        _close_dialog_callback(None, None, True)
    else:
        dialogs.close_confirm_dialog(_close_dialog_callback, app.get_save_time_msg(), gui.editor_window.window, editorstate.PROJECT().name)

def _close_dialog_callback(dialog, response_id, no_dialog_project_close=False):
    if no_dialog_project_close == False:
        dialog.destroy()
        if response_id == Gtk.ResponseType.CLOSE:# "Don't Save"
            pass
        elif response_id ==  Gtk.ResponseType.YES:# "Save"
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
    sequence.AUDIO_TRACKS_COUNT = appconsts.INIT_A_TRACKS
    sequence.VIDEO_TRACKS_COUNT = appconsts.INIT_V_TRACKS

    new_project = projectdata.get_default_project()
    app.open_project(new_project)
    
def actually_load_project(filename, block_recent_files=False, is_first_video_load=False, is_autosave_load=False):
    gui.tline_canvas.disconnect_mouse_events() # mouse events dutring load cause crashes because there is no data to handle
    load_launch = LoadThread(filename, block_recent_files, is_first_video_load, is_autosave_load)
    load_launch.start()

def save_project():
    if PROJECT().last_save_path == None:
        save_project_as()
    else:
        _save_project_in_last_saved_path()

def _save_project_in_last_saved_path():
    updater.set_info_icon(Gtk.STOCK_SAVE)

    try:
        
        persistance.save_project(PROJECT(), PROJECT().last_save_path) #<----- HERE
        
    except IOError as ioe:
        updater.set_info_icon(None)
        primary_txt = "I/O error({0})".format(ioe.errno)
        secondary_txt = ioe.strerror + "."
        dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window, is_info=False)
        return

    editorpersistance.add_recent_project_path(PROJECT().last_save_path)
    gui.editor_window.fill_recents_menu_widget(gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent'), open_recent_project)
    PROJECT().events.append(projectdata.ProjectEvent(projectdata.EVENT_SAVED, PROJECT().last_save_path))
    
    global save_icon_remove_event_id
    save_icon_remove_event_id = GObject.timeout_add(500, remove_save_icon)

    global save_time
    save_time = time.monotonic()
    clear_changed_since_last_save_flags()
    
    projectinfogui.update_project_info()
        
def save_project_as():
    if  PROJECT().last_save_path != None:
        open_dir = os.path.dirname(PROJECT().last_save_path)
        
        # We don't  want to open hidden cache dir when saving file opened as autosave.
        if open_dir.startswith(userfolders.get_cache_dir()) == True:
            open_dir = expanduser("~")
    else:
        open_dir = expanduser("~")

    dialogs.save_project_as_dialog(_save_as_dialog_callback, PROJECT().name, open_dir)
    
def _save_as_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        filenames = dialog.get_filenames()
        PROJECT().last_save_path = filenames[0]
        PROJECT().name = os.path.basename(filenames[0])
        updater.set_info_icon(Gtk.STOCK_SAVE)

        try:
            
            persistance.save_project(PROJECT(), PROJECT().last_save_path) #<----- HERE
            
        except IOError as ioe:
            dialog.destroy()
            updater.set_info_icon(None)
            primary_txt = "I/O error({0})".format(ioe.errno)
            secondary_txt = ioe.strerror + "."
            dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window, is_info=False)
            return

        if len(PROJECT().events) == 0: # Save as... with 0 project events is considered Project creation
            p_event = projectdata.ProjectEvent(projectdata.EVENT_CREATED_BY_SAVING, PROJECT().last_save_path)
            PROJECT().events.append(p_event)
        else:
            p_event = projectdata.ProjectEvent(projectdata.EVENT_SAVED_AS, (PROJECT().name, PROJECT().last_save_path))
            PROJECT().events.append(p_event)
            
        app.stop_autosave()
        app.start_autosave()
        
        global save_icon_remove_event_id
        save_icon_remove_event_id = GObject.timeout_add(500, remove_save_icon)

        global save_time
        save_time = time.monotonic()
        clear_changed_since_last_save_flags()

        gui.editor_window.window.set_title(PROJECT().name + " - Flowblade")        
        gui.editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(False)
        gui.editor_window.uimanager.get_widget("/MenuBar/EditMenu/Undo").set_sensitive(False)
        gui.editor_window.uimanager.get_widget("/MenuBar/EditMenu/Redo").set_sensitive(False)

        editorpersistance.add_recent_project_path(PROJECT().last_save_path)
        gui.editor_window.fill_recents_menu_widget(gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent'), open_recent_project)
        
        projectinfogui.update_project_info()
        
        dialog.destroy()
    else:
        dialog.destroy()

def save_backup_snapshot():
    parts = PROJECT().name.split(".")
    name = parts[0] + datetime.datetime.now().strftime("-%y%m%d") + ".flb"
    dialogs.save_backup_snapshot(name, _save_backup_snapshot_dialog_callback)

def _save_backup_snapshot_dialog_callback(dialog, response_id, project_folder, name_entry):
    if response_id == Gtk.ResponseType.ACCEPT:

        root_path = project_folder.get_filenames()[0]
        if not (os.listdir(root_path) == []):
            dialog.destroy()
            primary_txt = _("Selected folder contains files")
            secondary_txt = _("When saving a back-up snapshot of the project, the selected folder\nhas to be empty.")
            dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
            return

        name = name_entry.get_text()
        dialog.destroy()
        
        GLib.idle_add(lambda : _do_snapshot_save(root_path + "/", name))

    else:
        dialog.destroy()

def _do_snapshot_save(root_folder_path, project_name):
    project_name = project_name.rstrip(".flb") + ".flb" # user may enter ".flb" ... or not
    save_thread = SnaphotSaveThread(root_folder_path, project_name)
    save_thread.start()

def update_media_lengths():
    update_thread = UpdateMediaLengthsThread()
    update_thread.start()
    
def change_project_profile():
    dialogs.change_profile_project_dialog(PROJECT(), _change_project_profile_callback)

def _change_project_profile_callback(dialog, response_id, profile_combo, out_folder, project_name_entry):
    if response_id == Gtk.ResponseType.ACCEPT:
        ou = out_folder.get_filename()
        folder = ("/" + ou.lstrip("file:/"))
        name = project_name_entry.get_text()
        profile_name = profile_combo.get_selected()
        profile = mltprofiles.get_profile(profile_name)
        path = (folder + "/" + name)

        PROJECT().update_media_lengths_on_load = True # saved version needs to do this
        old_name = PROJECT().name
        PROJECT().name  = name
        
        persistance.save_project(PROJECT(), path, profile.description()) #<----- HERE

        project_event = projectdata.ProjectEvent(projectdata.EVENT_PROFILE_CHANGED_SAVE, str(profile.description()))
        PROJECT().events.append(project_event)
        
        PROJECT().name = old_name
        PROJECT().update_media_lengths_on_load = False

        dialog.destroy()
    else:
        dialog.destroy()
        

class SnaphotSaveThread(threading.Thread):
    
    def __init__(self, root_folder_path, project_name):
        self.root_folder_path = root_folder_path
        self.project_name = project_name
        threading.Thread.__init__(self)

    def run(self):
        copy_txt = _("Copying project media assets")
        project_txt = _("Saving project file")
        
        Gdk.threads_enter()
        dialog = dialogs.save_snaphot_progess(copy_txt, project_txt)
        Gdk.threads_leave()
        
        media_folder = self.root_folder_path +  "media/"

        d = os.path.dirname(media_folder)
        os.mkdir(d)

        asset_paths = {}

        # Copy media files
        for idkey, media_file in list(PROJECT().media_files.items()):
            if media_file.type == appconsts.PATTERN_PRODUCER:
                continue

            # Copy asset file and fix path
            directory, file_name = os.path.split(media_file.path)
            
            # Message
            Gdk.threads_enter()
            dialog.media_copy_info.set_text(copy_txt + "... " +  file_name)
            Gdk.threads_leave()
            
            # Other media types than image sequences
            if media_file.type != appconsts.IMAGE_SEQUENCE:
                media_file_copy = media_folder + file_name

                # TEST THIS SOMEHOW FOR UNICODE PROBLEMS
                if media_file_copy in list(asset_paths.values()): # Create different filename for files 
                                                             # that have same basename but different path
                    file_name = get_snapshot_unique_name(media_file.path, file_name)

                    media_file_copy = media_folder + file_name
                    
                shutil.copyfile(media_file.path, media_file_copy)
                asset_paths[media_file.path] = media_file_copy
            else: # Image Sequences
                asset_folder, asset_file_name =  os.path.split(media_file.path)
                lookup_filename = utils.get_img_seq_glob_lookup_name(asset_file_name)
                lookup_path = asset_folder + "/" + lookup_filename
                copyfolder = media_folder.rstrip("/") + asset_folder + "/"
                os.makedirs(copyfolder)
                listing = glob.glob(lookup_path)
                for orig_path in listing:
                    orig_folder, orig_file_name = os.path.split(orig_path)
                    shutil.copyfile(orig_path, copyfolder + orig_file_name)

        # Copy clip producers paths. This is needed just for rendered files as clips
        # from media file objects should be covered as media files can't be destroyed 
        # if a clip made from them exists...I think
        for seq in PROJECT().sequences:
            for track in seq.tracks:
                for i in range(0, len(track.clips)):
                    clip = track.clips[i]
                    
                    # Image sequence files can't be rendered files
                    if clip.is_blanck_clip == False and clip.media_type == appconsts.IMAGE_SEQUENCE:
                        continue

                    # Only producer clips are affected
                    if (clip.is_blanck_clip == False and (clip.media_type != appconsts.PATTERN_PRODUCER)):
                        directory, file_name = os.path.split(clip.path)
                        clip_file_copy = media_folder + file_name
                        
                        if not os.path.isfile(clip_file_copy):
                            directory, file_name = os.path.split(clip.path)
                            Gdk.threads_enter()
                            dialog.media_copy_info.set_text(copy_txt + "... " +  file_name)
                            Gdk.threads_leave()
                            shutil.copyfile(clip.path, clip_file_copy) # only rendered files are copied here
                            asset_paths[clip.path] = clip_file_copy # This stuff is already md5 hashed, so no duplicate problems here
            for compositor in seq.compositors:
                if compositor.type_id == "##wipe": # Wipe may have user luma and needs to be looked up relatively
                    copy_comp_resourse_file(compositor, "resource", media_folder)
                if compositor.type_id == "##region": # Wipe may have user luma and needs to be looked up relatively
                    copy_comp_resourse_file(compositor, "composite.luma", media_folder)

        Gdk.threads_enter()
        dialog.media_copy_info.set_text(copy_txt + "    " +  "\u2713")
        Gdk.threads_leave()

        save_path = self.root_folder_path + self.project_name

        persistance.snapshot_paths = asset_paths
        persistance.save_project(PROJECT(), save_path)
        persistance.snapshot_paths = None

        Gdk.threads_enter()
        dialog.saving_project_info.set_text(project_txt + "    " +  "\u2713")
        Gdk.threads_leave()

        time.sleep(2)

        Gdk.threads_enter()
        dialog.destroy()
        Gdk.threads_leave()
        
        project_event = projectdata.ProjectEvent(projectdata.EVENT_SAVED_SNAPSHOT, self.root_folder_path)
        PROJECT().events.append(project_event)

        Gdk.threads_enter()
        projectinfogui.update_project_info()
        Gdk.threads_leave()

def get_snapshot_unique_name(file_path, file_name):
    (name, ext) = os.path.splitext(file_name)
    return hashlib.md5(file_path).hexdigest() + ext

def copy_comp_resourse_file(compositor, res_property, media_folder):
    res_path = propertyparse.get_property_value(compositor.transition.properties, res_property)
    directory, file_name = os.path.split(res_path)
    res_file_copy = media_folder + file_name
    if not os.path.isfile(res_file_copy):
        shutil.copyfile(res_path, res_file_copy)
                        
def remove_save_icon():
    GObject.source_remove(save_icon_remove_event_id)
    updater.set_info_icon(None)

def open_recent_project(widget, index):
    path = editorpersistance.recent_projects.projects[index]
    if _project_empty() == True:
        _actually_open_recent(path)
    else:
        dialogs.exit_confirm_dialog(_open_recent_shutdown_dialog_callback, get_save_time_msg(), gui.editor_window.window, editorstate.PROJECT().name, path)

def _project_empty():
    for seq in PROJECT().sequences:
        if not seq.is_empty():
            return False
    
    return True
    
def _open_recent_shutdown_dialog_callback(dialog, response_id, path):
    dialog.destroy()
    
    # Handle poroject close responses
    if response_id == Gtk.ResponseType.CLOSE:# "Don't Save"
        pass
    elif response_id ==  Gtk.ResponseType.YES:# "Save"
        if editorstate.PROJECT().last_save_path != None:
            persistance.save_project(editorstate.PROJECT(), editorstate.PROJECT().last_save_path)
        else:
            dialogutils.warning_message(_("Project has not been saved previously"), 
                                    _("Save project with File -> Save As before closing."),
                                    gui.editor_window.window)
            return
    else: # "Cancel"
        return
    
    _actually_open_recent(path)

def _actually_open_recent(path):
    if not os.path.exists(path):
        editorpersistance.remove_non_existing_recent_projects()
        gui.editor_window.fill_recents_menu_widget(gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent'), open_recent_project)
        primary_txt = _("Project not found on disk")
        secondary_txt = _("Project can't be loaded.")
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        return

    actually_load_project(path)

def get_save_time_msg():
    if save_time == None:
        return _("Project has not been saved since it was opened.")
    
    save_ago = (time.monotonic() - save_time) / 60.0

    if save_ago < 1:
        return _("Project was saved less than a minute ago.")

    if save_ago < 2:
        return _("Project was saved one minute ago.")
    
    return _("Project was saved ") + str(int(save_ago)) + _(" minutes ago.")

def clear_changed_since_last_save_flags():
    edit.edit_done_since_last_save = False
    compositeeditor.compositor_changed_since_last_save = False
    clipeffectseditor.filter_changed_since_last_save = False
    projectdata.media_files_changed_since_last_save = False
    medialog.log_changed_since_last_save = False

def was_edited_since_last_save():   
    if (edit.edit_done_since_last_save == False and 
        compositeeditor.compositor_changed_since_last_save == False and
        clipeffectseditor.filter_changed_since_last_save == False and
        medialog.log_changed_since_last_save == False and
        projectdata.media_files_changed_since_last_save == False):
        return False
    
    return True

def view_project_events():
    projectinfogui.show_project_events_dialog()

# ---------------------------------- rendering
def do_rendering():
    global force_overwrite, force_proxy
    if force_overwrite == False:
        render_path = render.get_file_path()
        if os.path.isfile(render_path):
            primary_txt = _("Render target file exists!")
            secondary_txt = _("Confirm overwriting existing file.")
            dialogutils.warning_confirmation(_overwrite_confirm_dialog_callback, primary_txt, secondary_txt, gui.editor_window.window, data=None, is_info=False, use_confirm_text=True)
            return

    if force_proxy == False:
        if PROJECT().proxy_data.proxy_mode == appconsts.USE_PROXY_MEDIA:
            primary_txt = _("Project is currently using proxy media!")
            secondary_txt = _("Rendering from proxy media will produce worse quality than rendering from original media.\nConvert to using original media in Proxy Manager for best quality.\n\nSelect 'Confirm' to render from proxy media anyway.")
            dialogutils.warning_confirmation(_proxy_confirm_dialog_callback, primary_txt, secondary_txt, gui.editor_window.window, data=None, is_info=False, use_confirm_text=True)
            return

    # We need to exit active trim modes or the hidden trim clip gets rendered.
    if EDIT_MODE() == editorstate.ONE_ROLL_TRIM:
        modesetting.oneroll_trim_no_edit_init()
    elif EDIT_MODE() == editorstate.TWO_ROLL_TRIM:
        modesetting.tworoll_trim_no_edit_init()
    elif EDIT_MODE() == editorstate.SLIDE_TRIM:
        modesetting.slide_trim_no_edit_init()
    
    force_overwrite = False
    force_proxy = False
    
    success = _write_out_render_item(True)
    if success:
        render_selections = render.get_current_gui_selections()
        PROJECT().set_project_property(appconsts.P_PROP_LAST_RENDER_SELECTIONS, render_selections)
        batchrendering.launch_single_rendering()
        
        project_event = projectdata.ProjectEvent(projectdata.EVENT_RENDERED, str(render.get_file_path()))
        PROJECT().events.append(project_event)
        
def _overwrite_confirm_dialog_callback(dialog, response_id):
    dialog.destroy()
    if response_id == Gtk.ResponseType.ACCEPT:
        global force_overwrite
        force_overwrite = True
        do_rendering()

def _proxy_confirm_dialog_callback(dialog, response_id):
    dialog.destroy()
    if response_id == Gtk.ResponseType.ACCEPT:
        global force_proxy
        force_proxy = True
        do_rendering()
    else:  # This could otherwise stay accepting overwrites until app close
        global force_overwrite
        force_overwrite = False
        
def add_to_render_queue():
    _write_out_render_item(False)

def _write_out_render_item(single_render_item_item):
    
    # Clear hidden track, timeline rendering is not part of rendered output.
    current_sequence().clear_hidden_track()
    
    # Get render arga and path
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
            return False

    # Create batchrendering.RenderData object.
    # batchrendering.RenderData object is only used to display info about render,
    # it is not used to set render args.
    user_args = render.widgets.args_panel.use_args_check.get_active()
    enc_index = render.widgets.encoding_panel.encoding_selector.widget.get_active()
    quality_index = render.widgets.encoding_panel.quality_selector.widget.get_active()
    profile = render.get_current_profile()
    profile_text = guicomponents.get_profile_info_text(profile)
    fps = profile.fps()
    profile_name = profile.description()
    r_data = batchrendering.RenderData(enc_index, quality_index, user_args, profile_text, profile_name, fps)
    r_data.proxy_mode = PROJECT().proxy_data.proxy_mode 
    if user_args == True:
        r_data.args_vals_list = args_vals_list # pack these to go for display purposes if used
    
    if single_render_item_item:
        # Add item
        try:
            batchrendering.add_single_render_item( PROJECT(), 
                                                   render_path,
                                                   args_vals_list,
                                                   start_frame,
                                                   end_frame,
                                                   r_data)
        except Exception as e:
            primary_txt = _("Render launch failed!")
            secondary_txt = _("Error message: ") + str(e)
            dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window, is_info=False)
            return False
    else: # batch render item
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
            return False
            
    # This puts existing rendered timeline segments back to be displayed.
    current_sequence().update_hidden_track_for_timeline_rendering()

    return True

# ----------------------------------- media files
def hamburger_pressed(widget, event):
    hamburger_menu = hamburger_popup_menu
    
    guiutils.remove_children(hamburger_menu)

    hamburger_menu.add(guiutils.get_menu_item(_("Render Proxy Files For Selected Media"), _hamburger_menu_item_selected, "render proxies", ))
    hamburger_menu.add(guiutils.get_menu_item(_("Render Proxy Files For All Media"), _hamburger_menu_item_selected, "render all proxies", ))
    guiutils.add_separetor(hamburger_menu)
    hamburger_menu.add(guiutils.get_menu_item(_("Select All"), _hamburger_menu_item_selected, "select all"))
    hamburger_menu.add(guiutils.get_menu_item(_("Select None"), _hamburger_menu_item_selected, "select none"))

    move_menu_item = Gtk.MenuItem(_("Move Selected Media To Bin"))
    move_menu = Gtk.Menu()
    if len(PROJECT().bins) == 1:
        item = guiutils.get_menu_item(_("No Target Bins"), _hamburger_menu_item_selected, "dummy")
        item.set_sensitive(False)
        move_menu.add(item)
    else:
        index = 0
        for media_bin in PROJECT().bins:
            if media_bin == PROJECT().c_bin:
                index = index + 1
                continue
            item = guiutils.get_menu_item(media_bin.name, _hamburger_menu_item_selected, str(index))
            move_menu.add(item)
            item.show()
            index = index + 1
    move_menu_item.set_submenu(move_menu)
    hamburger_menu.add(move_menu_item)
    move_menu_item.show()
    
    guiutils.add_separetor(hamburger_menu)
    hamburger_menu.add(guiutils.get_menu_item(_("Append All Media to Timeline"), _hamburger_menu_item_selected, "append all"))
    hamburger_menu.add(guiutils.get_menu_item(_("Append Selected Media to Timeline"), _hamburger_menu_item_selected, "append selected"))
    
    hamburger_menu.popup(None, None, None, None, event.button, event.time)

def _hamburger_menu_item_selected(widget, msg):
    if msg == "render proxies":
        proxyediting.create_proxy_files_pressed()
    elif msg == "render all proxies":
        proxyediting.create_proxy_files_pressed(True)
    elif msg == "select all":
        gui.media_list_view.select_all()
    elif msg == "select none":
        gui.media_list_view.clear_selection()
    elif msg == "append all":
        append_all_media_clips_into_timeline()
    elif msg == "append selected":
        append_selected_media_clips_into_timeline()
    else:
        target_bin_index = int(msg)
        
        moved_files = []
        for selected_object in gui.media_list_view.selected_objects:
            # selected_object is guicomponents.MediaObjectWidget
            moved_files.append(selected_object.media_file)
        
        move_files_to_bin(target_bin_index, moved_files)

def media_panel_popup_requested(event):
    panel_menu = media_panel_popup_menu
    
    guiutils.remove_children(panel_menu)

    panel_menu.add(guiutils.get_menu_item(_("Add Video, Audio or Image..."), _media_panel_menu_item_selected, "add media", ))
    panel_menu.add(guiutils.get_menu_item(_("Add Image Sequence..."), _media_panel_menu_item_selected, "add image sequence"))
    
    panel_menu.popup(None, None, None, None, event.button, event.time)

def _media_panel_menu_item_selected(widget, msg):
    if msg == "add media":
        add_media_files()
    elif msg == "add image sequence":
        add_image_sequence()

def media_panel_double_click(media_file):
    global _media_panel_double_click_counter
    _media_panel_double_click_counter += 1
    if _media_panel_double_click_counter == 2:
        _media_panel_double_click_counter = 0
        updater.set_and_display_monitor_media_file(media_file)
            
def add_media_files(this_call_is_retry=False):
    """
    User selects a media file to added to current bin.
    """
    dialogs.media_file_dialog(_("Open.."), _open_files_dialog_cb, True)

def _open_files_dialog_cb(file_select, response_id):
    filenames = file_select.get_filenames()
    file_select.destroy()

    if response_id != Gtk.ResponseType.OK:
        return
    if len(filenames) == 0:
        return
    
    # We're disallowing opening .mlt or .xml files as media because MLTs behaviour of overwriting project profile properties
    # when opening MLT XML files as media
    # Underlying reason: https://github.com/mltframework/mlt/issues/212
    mlt_files_deleted = False
    last_non_matching_profile = None
    for i in range(len(filenames) - 1, -1, -1):
        file_path = filenames[i]
        if utils.is_mlt_xml_file(file_path) == True:
            match, non_matching_profile = mltprofiles.is_mlt_xml_profile_match_to_profile(file_path, current_sequence().profile)
            if match == False:
                filenames.pop(i)
                mlt_files_deleted = True
                last_non_matching_profile = non_matching_profile
    
    open_file_names(filenames)

    # Info on disallowed files
    if mlt_files_deleted == True:
        primary_txt = _("Opening .mlt or .xml file as media was disallowed!")
        secondary_txt = _("Only XML files with matching Profiles can be opened as clips.\n\nLast non-matching MLT XML file had Profile: ") + last_non_matching_profile
        dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
        
def open_file_names(filenames):
    add_media_thread = AddMediaFilesThread(filenames)
    add_media_thread.start()

def add_image_sequence():
    dialogs.open_image_sequence_dialog(_add_image_sequence_callback, gui.editor_window.window)

def _add_image_sequence_callback(dialog, response_id, data):
    if response_id == Gtk.ResponseType.CANCEL:
        dialog.destroy()
        return

    file_chooser, spin = data
    frame_file = file_chooser.get_filename()
    ttl = int(spin.get_value())
    
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

    resource_name_str = utils.get_img_seq_resource_name(frame_file)
        
    # Detect highest file so that we know the length of the producer.
    # FIX: this fails if two similarly numbered sequences in same dir and both have same substring in frame name
    number_index = file_name.find(number_part)
    path_name_part = file_name[0:number_index]
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
    length = (highest_number_part - int(number_part)) * ttl

    PROJECT().add_image_sequence_media_object(resource_path, file_name + "(img_seq)", length, ttl)

    gui.media_list_view.fill_data_model()
    gui.bin_list_view.fill_data_model()

    editorpersistance.prefs.last_opened_media_dir = os.path.dirname(resource_path)
    editorpersistance.save()

def add_plugin_image_sequence(resource_path, file_name, length):
    PROJECT().add_image_sequence_media_object(resource_path, file_name + "(img_seq)", length, 1)

    gui.media_list_view.fill_data_model()
    gui.bin_list_view.fill_data_model()

    editorpersistance.prefs.last_opened_media_dir = os.path.dirname(resource_path)
    editorpersistance.save()

def add_plugin_rendered_media(path, plugin_name):
    add_media_thread = AddMediaFilesThread([path], plugin_name)
    add_media_thread.start()
    
def open_rendered_file(rendered_file_path):
    add_media_thread = AddMediaFilesThread([rendered_file_path])
    add_media_thread.start()

def delete_media_files(force_delete=False):
    """
    Deletes media file. Does not take into account if clips made from 
    media file are still in sequence.(maybe change this)
    """
    selection = gui.media_list_view.get_selected_media_objects()
    if len(selection) < 1:
        return
    
    file_ids = []
    # Get:
    # - list of integer keys to delete from Project.media_files
    # - list of indexes to delete from Bin.file_ids
    for media_obj in selection:
        file_id = media_obj.media_file.id
        file_ids.append(file_id)

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
    for file_id in file_ids:
        current_bin().file_ids.remove(file_id)
    update_current_bin_files_count()
    
    # Delete from project
    for file_id in file_ids:
        PROJECT().media_files.pop(file_id)

    gui.media_list_view.fill_data_model()
    _enable_save()
    gui.editor_window.bin_info.display_bin_info()

def _proxy_delete_warning_callback(dialog, response_id):
    dialog.destroy()
    if response_id == Gtk.ResponseType.OK:
        delete_media_files(True)

def open_next_media_item_in_monitor():
    # Get id for next media file
    selection = gui.media_list_view.get_selected_media_objects()
    if len(selection) < 1:
        try: # Nothing selected, get first media item
            next_media_file_id = current_bin().file_ids[0]
        except:
            return # bin is empty
    else: # Get next media item from selection
        current_media_file_id = selection[0].media_file.id
        next_media_index = current_bin().file_ids.index(current_media_file_id) + 1
        if next_media_index == len(current_bin().file_ids):
            next_media_index = 0
        
        next_media_file_id = current_bin().file_ids[next_media_index]
    
    # Get media file, select it and show in monitor
    media_file = PROJECT().media_files[next_media_file_id]
    
    gui.media_list_view.select_media_file(media_file)
    gui.media_list_view.update_selected_bg_colors()
    updater.set_and_display_monitor_media_file(media_file)
    gui.pos_bar.widget.grab_focus()
            
def display_media_file_rename_dialog(media_file):
    dialogs.new_media_name_dialog(media_file_name_edited, media_file)

def media_file_name_edited(dialog, response_id, data):
    """
    Sets edited value to liststore and project data.
    """
    name_entry, media_file = data
    new_text = name_entry.get_text()
    dialog.destroy()
            
    if response_id != Gtk.ResponseType.ACCEPT:
        return      
    if len(new_text) == 0:
        return

    media_file.name = new_text
    gui.media_list_view.fill_data_model()

def _display_file_info(media_file):
    # get info
    clip = current_sequence().create_file_producer_clip(media_file.path, None, False, media_file.ttl)
    info = utils.get_file_producer_info(clip)

    width = info["width"]
    height = info["height"]
    if media_file.type == appconsts.IMAGE:
        graphic_img = Image.open(media_file.path)
        width, height = graphic_img.size 

    size = str(width) + " x " + str(height)
    length = utils.get_tc_string(info["length"])

    try:
        img = guiutils.get_gtk_image_from_file(media_file.icon_path, 300)
    except:
        print("_display_file_info() failed to get thumbnail")
    
    vcodec = info["vcodec"]
    acodec = info["acodec"]
    
    if vcodec == None:
        vcodec = _("N/A")
    if acodec == None:
        acodec = _("N/A")

    channels = str(info["channels"]) 
    frequency =  str(info["frequency"]) + "Hz"

    if media_file.type == appconsts.VIDEO:
        match_profile_index = mltprofiles.get_closest_matching_profile_index(info)
        match_profile_name =  mltprofiles.get_profile_name_for_index(match_profile_index)
    else:
        match_profile_name = _("N/A")
    
    if media_file.type == appconsts.VIDEO:
        if media_file.matches_project_profile():
            matches_project_profile = _("Yes")
        else:
            matches_project_profile = _("No")
    else:
        matches_project_profile = _("N/A")
        
    try:
        num = info["fps_num"]
        den = info["fps_den"]
        fps = utils.get_fps_str_with_two_decimals(str(float(num/den)))
    except:
        fps = _("N/A")
    
    dialogs.file_properties_dialog((media_file, img, size, length, vcodec, acodec, channels, frequency, fps, match_profile_name, matches_project_profile))

def remove_unused_media():
    unused = unused_media()
    # It is most convenient to do remove via gui object
    gui.media_list_view.select_media_file_list(unused)
    delete_media_files()

def unused_media():
    # Create path -> media item dict
    path_to_media_object = {}
    for key, media_item in list(PROJECT().media_files.items()):
        if hasattr(media_item, "path") and media_item.path != "" and media_item.path != None:
            path_to_media_object[media_item.path] = media_item
    
    # Remove all items from created dict that have a clip with same path on any of the sequences
    for seq in PROJECT().sequences:
        for track in seq.tracks:
            for clip in track.clips:
                try:
                    path_to_media_object.pop(clip.path)
                except:
                    pass
    
    # Create a list of unused media objects
    unused = []
    for path, media_item in list(path_to_media_object.items()):
        unused.append(media_item)
    return unused

def media_filtering_select_pressed(widget, event):
    guicomponents.get_file_filter_popup_menu(widget, event, _media_filtering_selector_item_activated)

def _media_filtering_selector_item_activated(selector, index):
    gui.media_view_filter_selector.set_pixbuf(index)
    
    # Const value correspond with indexes here
    editorstate.media_view_filter = index
    gui.media_list_view.fill_data_model()

def columns_count_launch_pressed(widget, event):
    guicomponents.get_columns_count_popup_menu(event, _columns_count_item_selected)
    
def _columns_count_item_selected(w, data):
    gui.editor_window.media_list_view.columns_changed(data)
 
def import_project_media():
    dialogs.load_project_dialog(_media_import_project_select_dialog_callback, None, _("Select Project for Media Import"))
    
def _media_import_project_select_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        filenames = dialog.get_filenames()
        dialog.destroy()
        projectmediaimport.import_media_files(filenames[0], _media_import_data_ready)
    else:
        dialog.destroy()

def _media_import_data_ready():
    files_list = projectmediaimport.get_imported_media()
    open_file_names(files_list)

def create_selection_compound_clip():
    if movemodes.selected_track == -1:
        # info window no clips selected?
        return

    # lets's just set something unique-ish 
    default_name = _("selection_") + _get_compound_clip_default_name_date_str()
    dialogs.compound_clip_name_dialog(_do_create_selection_compound_clip, default_name, _("Save Selection Container Clip"))

def _do_create_selection_compound_clip(dialog, response_id, name_entry):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    media_name = name_entry.get_text()
    
    # Create unique file path in hidden render folder
    folder = userfolders.get_render_dir()
    uuid_str = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
    write_file = folder + "/"+ uuid_str + ".xml"

    dialog.destroy()
    
    # Create clones of selected clips
    track = current_sequence().tracks[movemodes.selected_track]
    clips = []
    for i in range(movemodes.selected_range_in, movemodes.selected_range_out + 1): # + 1 == to_index inclusive
        clips.append(current_sequence().create_clone_clip(track.clips[i]))
        
    # Create tractor
    tractor = mlt.Tractor()
    multitrack = tractor.multitrack()
    track0 = mlt.Playlist()
    multitrack.connect(track0, 0)
    for i in range(0, len(clips)):
        clip = clips[i]
        track0.append(clip, clip.clip_in, clip.clip_out)

    # Render compound clip as MLT XML file
    render_player = renderconsumer.XMLCompoundRenderPlayer(write_file, media_name, _xml_compound_render_done_callback, tractor, PROJECT())
    render_player.start()

def _xml_compound_render_done_callback(filename, media_name):
    containerclip.create_mlt_xml_media_item(filename, media_name)

def _sequence_xml_compound_render_done_callback(data):
    filename, media_name = data
    containerclip.create_mlt_xml_media_item(filename, media_name)

def _xml_freeze_compound_render_done_callback(filename, media_name):
    # Remove freeze filter
    current_sequence().tractor.detach(current_sequence().tractor.freeze_filter)
    delattr(current_sequence().tractor, "freeze_filter")
    
    add_media_thread = AddMediaFilesThread([filename], media_name)
    add_media_thread.start()

def create_sequence_compound_clip():
    # lets's just set something unique-ish 
    default_name = _("sequence_") + _get_compound_clip_default_name_date_str()
    dialogs.compound_clip_name_dialog(_do_create_sequence_compound_clip, default_name, _("Save Sequence Container Clip"))



def _do_create_sequence_compound_clip(dialog, response_id, name_entry):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    media_name = name_entry.get_text()
    folder = userfolders.get_render_dir()
    write_file = folder + "/"+ media_name + ".xml"

    dialog.destroy()

    render_player = renderconsumer.XMLRenderPlayer( write_file, _sequence_xml_compound_render_done_callback, 
                                                    (write_file, media_name), PROJECT().c_seq, 
                                                    PROJECT(), PLAYER())
    render_player.start()

# This is called from popup menu and can be used to create compound clips from non-active sequences
def create_sequence_compound_clip_from_selected():
    default_name = _("sequence_") + _get_compound_clip_default_name_date_str()
    dialogs.compound_clip_name_dialog(_do_create_sequence_compound_clip_from_selected, default_name, _("Save Sequence Compound Clip"))

def _do_create_sequence_compound_clip_from_selected(dialog, response_id, name_entry):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    media_name = name_entry.get_text()
    folder = userfolders.get_render_dir()
    write_file = folder + "/"+ media_name + ".xml"

    dialog.destroy()

    selection = gui.sequence_list_view.treeview.get_selection()
    model, iter = selection.get_selected()
    (model, rows) = selection.get_selected_rows()
    row = max(rows[0])
    selected_sequence = PROJECT().sequences[row]

    render_player = renderconsumer.XMLRenderPlayer( write_file, _sequence_xml_compound_render_done_callback, 
                                                    (write_file, media_name), selected_sequence, 
                                                    PROJECT(), PLAYER())
    render_player.start()
    
def create_sequence_freeze_frame_compound_clip():
    # lets's just set something unique-ish 
    default_name = _("frame_") + utils.get_tc_string_with_fps_for_filename(PLAYER().current_frame(), utils.fps()) + ".xml"
    dialogs.compound_clip_name_dialog(_do_create_sequence_freeze_frame_compound_clip, default_name, _("Save Freeze Frame Sequence Compound Clip"))

def _do_create_sequence_freeze_frame_compound_clip(dialog, response_id, name_entry):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return
    
    media_name = name_entry.get_text()
    folder = userfolders.get_render_dir()
    write_file = folder + "/"+ media_name + ".xml"

    dialog.destroy()
    
    freezed_tractor = current_sequence().tractor 

    freeze_filter = mlt.Filter(PROJECT().profile, "freeze")
    freeze_filter.set("frame", str(PLAYER().current_frame()))
    freeze_filter.set("freeze_after", "0") 
    freeze_filter.set("freeze_before", "0") 

    freezed_tractor.attach(freeze_filter)
    freezed_tractor.freeze_filter = freeze_filter # pack to go so it can be detached and attr removed

    # Render compound clip as MLT XML file
    render_player = renderconsumer.XMLCompoundRenderPlayer(write_file, media_name, _xml_freeze_compound_render_done_callback, freezed_tractor, PROJECT())
    render_player.start()
    
def _get_compound_clip_default_name_date_str():
    return str(datetime.date.today()) + "_" + time.strftime("%H%M%S")

def append_all_media_clips_into_timeline():
    media_files = []
    for file_id in PROJECT().c_bin.file_ids:
        media_files.append(PROJECT().media_files[file_id])
    
    _append_media_files(media_files)

def append_selected_media_clips_into_timeline():
    selection = gui.media_list_view.get_selected_media_objects()
    media_files = []
    for mobj in selection:
        media_files.append(mobj.media_file)
    _append_media_files(media_files)

def _append_media_files(media_files):
    clips = []
    for media_file in media_files:
    
        new_clip = current_sequence().create_file_producer_clip(media_file.path, None, False, media_file.ttl)
        new_clip.clip_in = 0
        new_clip.clip_out = new_clip.get_length() - 1
        if new_clip.media_type == appconsts.IMAGE:
            in_fr, out_fr, default_grfx_length = editorpersistance.get_graphics_default_in_out_length()
            new_clip.clip_in = in_fr
            new_clip.clip_out = out_fr

        clips.append(new_clip)

    track = editorstate.current_sequence().get_first_active_track()

    # Can't put audio media on video track
    for new_clip in clips:
        if ((new_clip.media_type == appconsts.AUDIO)
           and (track.type == appconsts.VIDEO)):
            dialogs.no_audio_dialog(track)
            return

    data = {"track":track,
            "clips":clips}

    action = edit.append_media_log_action(data)
    action.do_edit()

# ------------------------------------ bins
def bins_panel_popup_requested(event):
    bin_menu = bin_popup_menu
    
    guiutils.remove_children(bin_menu)

    bin_menu.add(guiutils.get_menu_item(_("Add Bin"), _bin_menu_item_selected, ("add bin", None)))
    bin_menu.add(guiutils.get_menu_item(_("Delete Selected Bin"), _bin_menu_item_selected, ("delete bin", None)))

    guiutils.add_separetor(bin_menu)
    
    move_menu_item = Gtk.MenuItem(_("Move Bin"))
    move_menu = Gtk.Menu()
    move_menu.add(guiutils.get_menu_item(_("Up"), _bin_menu_item_selected, ("up bin", None)))
    move_menu.add(guiutils.get_menu_item(_("Down"), _bin_menu_item_selected, ("down bin", None)))
    move_menu.add(guiutils.get_menu_item(_("First"), _bin_menu_item_selected, ("first bin", None)))
    move_menu.add(guiutils.get_menu_item(_("Last"), _bin_menu_item_selected, ("last bin", None)))
    move_menu_item.set_submenu(move_menu)
    bin_menu.add(move_menu_item)
    move_menu_item.show()
    
    bin_menu.popup(None, None, None, None, event.button, event.time)    

def bin_hambuger_pressed(widget, event):
    bins_panel_popup_requested(event)

def _bin_menu_item_selected(widget, data):
    msg, bin_obj = data
    if msg == "add bin":
        add_new_bin()
    elif msg == "delete bin":
        delete_selected_bin()
    elif msg == "up bin":
        c_index = PROJECT().bins.index(PROJECT().c_bin)
        if c_index == 0 or len(PROJECT().bins) == 1:
            return
        _move_bin(c_index, c_index - 1)
    elif msg == "down bin":
        c_index = PROJECT().bins.index(PROJECT().c_bin)
        if c_index >= len(PROJECT().bins) - 1:
            return # already last
        _move_bin(c_index, c_index + 1)
    elif msg == "first bin":
        c_index = PROJECT().bins.index(PROJECT().c_bin)
        if c_index == 0 or len(PROJECT().bins) == 1:
            return
        _move_bin(c_index, 0)
    elif msg == "last bin":
        c_index = PROJECT().bins.index(PROJECT().c_bin)
        if c_index >= len(PROJECT().bins) - 1:
            return # already last
        _move_bin(c_index, len(PROJECT().bins) - 1)

def _move_bin(pop_index, insert_index):
    PROJECT().bins.pop(pop_index)
    PROJECT().bins.insert(insert_index, PROJECT().c_bin)
    gui.bin_list_view.fill_data_model()
    selection = gui.bin_list_view.treeview.get_selection()
    model, iterator = selection.get_selected()
    selection.select_path(str(insert_index))
    
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
    gui.editor_window.bin_info.display_bin_info()

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
    gui.editor_window.bin_info.display_bin_info()
                  
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
    gui.editor_window.bin_info.display_bin_info()

def update_current_bin_files_count():
    # Get index for selected bin
    selection = gui.editor_window.bin_list_view.treeview.get_selection()
    (model, rows) = selection.get_selected_rows()
    if len(rows) == 0:
        return
    row = max(rows[0])
    
    value = str(len(PROJECT().bins[row].file_ids))

    tree_path = Gtk.TreePath.new_from_string(str(row))
    store_iter = gui.editor_window.bin_list_view.storemodel.get_iter(tree_path)
    
    gui.editor_window.bin_list_view.storemodel.set_value(store_iter, 2, value)
    
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
    gui.editor_window.bin_info.display_bin_info()
    
def move_files_to_bin(new_bin, moved_files):
    # If we're moving clips to bin that they're already in, do nothing.
    if PROJECT().bins[new_bin] == current_bin():
        return

    source_bin_index = PROJECT().bins.index(PROJECT().c_bin) # this gets reset to 0 and it is just easier to save and set again
    
    # Move
    for media_file in moved_files:
        current_bin().file_ids.remove(media_file.id)
        PROJECT().bins[new_bin].file_ids.append(media_file.id)

    gui.media_list_view.fill_data_model()
    gui.bin_list_view.fill_data_model()

    # We need to select current gin again to show it selected in GUI
    selection = gui.bin_list_view.treeview.get_selection()
    selection.select_path(str(source_bin_index))
    
    gui.editor_window.bin_info.display_bin_info()
    
    
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

def sequences_hamburger_pressed(widget, event):
    sequence_panel_popup_requested(event)

def sequence_panel_popup_requested(event):
    sequence_menu = sequence_popup_menu
    
    guiutils.remove_children(sequence_menu)

    sequence_menu.add(guiutils.get_menu_item(_("Add New Sequence"), _sequece_menu_item_selected, ("add sequence", None)))
    sequence_menu.add(guiutils.get_menu_item(_("Edit Selected Sequence"), _sequece_menu_item_selected, ("edit sequence", None)))
    sequence_menu.add(guiutils.get_menu_item(_("Delete Selected Sequence"), _sequece_menu_item_selected, ("delete sequence", None)))
    guiutils.add_separetor(sequence_menu)
    sequence_menu.add(guiutils.get_menu_item(_("Create Container Clip from Selected Sequence"), _sequece_menu_item_selected, ("compound clip", None)))
    
    sequence_menu.popup(None, None, None, None, event.button, event.time)    

def _sequece_menu_item_selected(widget, data):
    msg, bin_obj = data
    if msg == "add sequence":
        add_new_sequence()
    elif msg == "delete sequence":
        delete_selected_sequence()
    elif msg == "edit sequence":
        change_edit_sequence()
    elif msg == "compound clip":
        create_sequence_compound_clip_from_selected()
        
def add_new_sequence():
    default_name = _("sequence_") + str(PROJECT().next_seq_number)
    dialogs.new_sequence_dialog(_add_new_sequence_dialog_callback, default_name)

def _add_new_sequence_dialog_callback(dialog, response_id, widgets):    
    """
    Adds new unnamed sequence and sets it selected 
    """
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return
    
    name_entry, tracks_select, open_check = widgets
    
    # Get dialog data 
    name = name_entry.get_text()
    if len(name) == 0:
        name = (_("sequence_") + str(PROJECT().next_seq_number))

    v_tracks, a_tracks = tracks_select.get_tracks()
    open_right_away = open_check.get_active()
    
    # Get index for selected sequence
    selection = gui.sequence_list_view.treeview.get_selection()
    (model, rows) = selection.get_selected_rows()
    row = max(rows[0])
    
    # Set default track counts as module global values, this is not a good design.
    sequence.AUDIO_TRACKS_COUNT = a_tracks
    sequence.VIDEO_TRACKS_COUNT = v_tracks

    # Add new sequence.
    print("new seq", name)
    PROJECT().add_named_sequence(name)

    gui.sequence_list_view.fill_data_model()
    
    if open_right_away == False:
        selection.select_path(str(row)) # Keep previous selection
    else:
        app.change_current_sequence(len(PROJECT().sequences) - 1)
        gui.editor_window.init_compositing_mode_menu()
    
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

def sequence_list_double_click_done():
    selection = gui.sequence_list_view.treeview.get_selection()
    model, iter = selection.get_selected()
    (model, rows) = selection.get_selected_rows()
    row = max(rows[0])
    
    c_seq_index = PROJECT().sequences.index(PROJECT().c_seq)
    
    if c_seq_index != row:
        change_edit_sequence()

def _delete_confirm_callback(dialog, response_id):
    if response_id != Gtk.ResponseType.ACCEPT:
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
    gui.editor_window.monitor_tc_info.monitor_source.set_text(new_text + " - ")
    
    _enable_save()

def change_sequence_track_count():
    nv, na = PROJECT().c_seq.get_track_counts()
    dialogs.tracks_count_change_dialog(_change_track_count_dialog_callback, nv, na)

def _change_track_count_dialog_callback(dialog, response_id, tracks_select):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return
    
    v_tracks, a_tracks = tracks_select.get_tracks()
    dialog.destroy()

    cur_seq_index = PROJECT().sequences.index(PROJECT().c_seq)
    
    if len(PROJECT().c_seq.tracks[-1].clips) == 1: # Remove hidden hack trick blank so that is does not get copied 
        edit._remove_clip(PROJECT().c_seq.tracks[-1], 0)

    if current_sequence().compositing_mode == appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
        # These sequences have one compositor for every non-V1 video track that will be recreated after track count changed.
        current_sequence().destroy_compositors()

    new_seq = sequence.create_sequence_clone_with_different_track_count(PROJECT().c_seq, v_tracks, a_tracks)

    PROJECT().sequences.insert(cur_seq_index, new_seq)
    PROJECT().sequences.pop(cur_seq_index + 1)
    app.change_current_sequence(cur_seq_index)

    if current_sequence().compositing_mode == appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
        # Put track compositors back
        current_sequence().add_full_track_compositors()

    tlinerender.get_renderer().timeline_changed()

def combine_sequences():
    dialogs.combine_sequences_dialog(_combine_sequences_dialog_callback)

def _combine_sequences_dialog_callback(dialog, response_id, action_select, seq_select, selectable_seqs):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return
    
    action = action_select.get_active()
    seq = selectable_seqs[seq_select.get_active()]
    
    dialog.destroy()
    
    if action == 0:
        _append_sequence(seq)
    else:
        _insert_sequence(seq)

def _append_sequence(import_seq):
    start_track_range, end_track_range = _get_sequence_import_range(import_seq)
    tracks_off = current_sequence().first_video_index - import_seq.first_video_index
    orig_length = current_sequence().get_length()

    # Justify ends
    for i in range(start_track_range, end_track_range):
        track = current_sequence().tracks[i]
        
        # Add pad blank
        blank_length = current_sequence().get_length() - track.get_length()
        if blank_length > 0:
            edit._insert_blank(track, len(track.clips), blank_length)

    # Copy clips
    for i in range(start_track_range, end_track_range):
        track = current_sequence().tracks[i]
        
        import_track = import_seq.tracks[i - tracks_off]
        insert_start_index = len(track.clips)
        for j in range(0, len(import_track.clips)):
            import_clip = import_track.clips[j]
            if import_clip.is_blanck_clip != True:
                import_clip_clone = current_sequence().create_clone_clip(import_clip)
                edit.append_clip(track, import_clip_clone, import_clip_clone.clip_in, import_clip_clone.clip_out)
            else:
                edit._insert_blank(track, insert_start_index + j, import_clip.clip_out - import_clip.clip_in + 1)

    # Import compositors
    for import_compositor in import_seq.compositors:
        if import_compositor.transition.b_track + tracks_off < len(current_sequence().tracks) - 1:
            clone_compositor = current_sequence()._create_and_plant_clone_compositor_for_sequnce_clone(import_compositor, tracks_off)
            clone_compositor.move(orig_length)
            current_sequence().compositors.append(clone_compositor)
    current_sequence().restack_compositors()

    # Remove unneeded blanks
    for i in range(start_track_range, end_track_range):
        track = current_sequence().tracks[i]
        if len(track.clips) == 1:
            if track.clips[0].is_blanck_clip == True:
                edit._remove_clip(track, 0)
    # This method just needs some class to save data for undo which we are not using
    edit._consolidate_all_blanks_redo(utils.EmptyClass)
    edit._remove_all_trailing_blanks()
    
    _update_gui_after_sequence_import()

    undo.clear_undos()

    updater.repaint_tline()

def _insert_sequence(import_seq):
    insert_frame = editorstate.PLAYER().current_frame()
    start_track_range, end_track_range = _get_sequence_import_range(import_seq)
    tracks_off = current_sequence().first_video_index - import_seq.first_video_index
    
    # Cut tracks at insert frame
    for i in range(1, len(current_sequence().tracks) - 1):
        track = current_sequence().tracks[i]
        if track.get_length() > insert_frame:
            edit._overwrite_cut_track(track, insert_frame, True)

    # Justify ends
    for i in range(start_track_range, end_track_range):
        track = current_sequence().tracks[i]
        
        # Add pad blank
        blank_length = insert_frame - track.get_length()
        if blank_length > 0:
            edit._insert_blank(track, len(track.clips), blank_length)

    # Copy clips
    for i in range(start_track_range, end_track_range):
        track = current_sequence().tracks[i]
        
        import_track = import_seq.tracks[i - tracks_off]
        insert_start_index = track.get_clip_index_at(insert_frame)
        for j in range(0, len(import_track.clips)):
            import_clip = import_track.clips[j]
            if import_clip.is_blanck_clip != True:
                import_clip_clone = current_sequence().create_clone_clip(import_clip)
                edit._insert_clip(track, import_clip_clone, insert_start_index + j, import_clip_clone.clip_in, import_clip_clone.clip_out)
            else:
                edit._insert_blank(track, insert_start_index + j, import_clip.clip_out - import_clip.clip_in + 1)
        
        # Justify insert range end, add pad blank if needed
        blank_length = import_seq.get_length() - import_track.get_length()        
        if blank_length > 0 and blank_length < import_seq.get_length():
            edit._insert_blank(track, insert_start_index + len(import_track.clips), blank_length)

    # Move post insert point compositors
    for compositor in current_sequence().compositors:
        if compositor.clip_in >= insert_frame:
            compositor.move(import_seq.get_length())

    # Import compositors
    for import_compositor in import_seq.compositors:
        if import_compositor.transition.b_track + tracks_off < len(current_sequence().tracks) - 1:
            clone_compositor = current_sequence()._create_and_plant_clone_compositor_for_sequnce_clone(import_compositor, tracks_off)
            clone_compositor.move(insert_frame)
            current_sequence().compositors.append(clone_compositor)
    current_sequence().restack_compositors()
    
    # Remove unneeded blanks
    for i in range(start_track_range, end_track_range):
        track = current_sequence().tracks[i]
        if len(track.clips) == 1:
            if track.clips[0].is_blanck_clip == True:
                edit._remove_clip(track, 0)
    # This method just needs some class to save data for undo which we are not using
    edit._consolidate_all_blanks_redo(utils.EmptyClass)
    edit._remove_all_trailing_blanks()
        
    _update_gui_after_sequence_import()

    undo.clear_undos()
    
    updater.repaint_tline()
    
def _get_sequence_import_range(import_seq):
    # Compute corresponding tracks, import sequence may have less audio and/or video tracks
    first_video_off = current_sequence().first_video_index - import_seq.first_video_index
    
    # Compare audio tracks count to determine first track from current sequence to be added clips from import sequence
    if first_video_off > 0: # import_seq has less audio tracks
        start_track_range = 1 + first_video_off 
    else:  # import_seq has same number of audio tracks
        start_track_range = 1

    # Compare video tracks count to determine last track from current sequence to be added clips from import sequence
    cur_seq_video_tracks_count = len(current_sequence().tracks) - current_sequence().first_video_index
    import_seq_video_tracks_count = len(import_seq.tracks) - import_seq.first_video_index

    video_tracks_count_diff = cur_seq_video_tracks_count - import_seq_video_tracks_count
    if video_tracks_count_diff > 0: # Current sequence has more video tracks 
        end_track_range = len(current_sequence().tracks) - 1 - video_tracks_count_diff
    else:  # Current sequence has equak number or lass tracks 
        end_track_range = len(current_sequence().tracks) - 1

    return (start_track_range, end_track_range)

def _update_gui_after_sequence_import(): # This copied  with small modifications into projectaction.py for sequence imports, update there too if needed...yeah.
    updater.update_tline_scrollbar() # Slider needs to adjust to possibly new program length.
                                     # This REPAINTS TIMELINE as a side effect.
    updater.clear_effects_editor_clip()

    current_sequence().update_edit_tracks_length() # Needed for timeline rendering updates
    current_sequence().update_hidden_track_for_timeline_rendering() # Needed for timeline rendering updates
    editorstate.PLAYER().display_inside_sequence_length(current_sequence().seq_len)

    updater. update_seqence_info_text()

def compositing_mode_menu_launched(widget, event):
    guiutils.remove_children(compositing_mode_menu)

    comp_top_free = guiutils.get_image_menu_item(_("Top Down Free Move"), "top_down", change_current_sequence_compositing_mode_from_corner_menu)
    comp_standard_auto = guiutils.get_image_menu_item(_("Auto Follow"), "standard_auto", change_current_sequence_compositing_mode_from_corner_menu)
    comp_full_track = guiutils.get_image_menu_item(_("Standard Full Track"), "full_track_auto", change_current_sequence_compositing_mode_from_corner_menu)
    
    comp_top_free.connect("activate", lambda w: change_current_sequence_compositing_mode_from_corner_menu(appconsts.COMPOSITING_MODE_TOP_DOWN_FREE_MOVE))
    comp_standard_auto.connect("activate", lambda w: change_current_sequence_compositing_mode_from_corner_menu(appconsts.COMPOSITING_MODE_STANDARD_AUTO_FOLLOW))
    comp_full_track.connect("activate", lambda w: change_current_sequence_compositing_mode_from_corner_menu(appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK))

    compositing_mode_menu.add(comp_top_free)
    compositing_mode_menu.add(comp_standard_auto)
    compositing_mode_menu.add(comp_full_track)

    compositing_mode_menu.popup(None, None, None, None, event.button, event.time)
    
def change_current_sequence_compositing_mode_from_corner_menu(new_compositing_mode):
    if current_sequence().compositing_mode == new_compositing_mode:
        return 
        
    dialogs.confirm_compositing_mode_change(_compositing_mode_dialog_callback, new_compositing_mode)

def change_current_sequence_compositing_mode(menu_widget, new_compositing_mode):
    if menu_widget.get_active() == False:
        return
    
    dialogs.confirm_compositing_mode_change(_compositing_mode_dialog_callback, new_compositing_mode)
        
def _compositing_mode_dialog_callback(dialog, response_id, new_compositing_mode):
    dialog.destroy()
    if response_id != Gtk.ResponseType.ACCEPT:
        gui.editor_window.init_compositing_mode_menu()
        return
    
    # Destroy stuff
    compositeeditor.clear_compositor()
    current_sequence().destroy_compositors()
    undo.clear_undos()
    current_sequence().compositing_mode = new_compositing_mode
    if current_sequence().compositing_mode == appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK: 
        current_sequence().add_full_track_compositors()
    updater.repaint_tline()

    compositeeditor._display_compositor_edit_box()
    gui.comp_mode_launcher.set_pixbuf(new_compositing_mode) # pixbuf indexes correspond with compositing mode enums.

# --------------------------------------------------------- pop-up menus
def media_file_menu_item_selected(widget, data):
    item_id, media_file, event = data
    if item_id == "File Properties":
        _display_file_info(media_file)
    if item_id == "Open in Clip Monitor":
        updater.set_and_display_monitor_media_file(media_file)
    if item_id == "Render Slow/Fast Motion File":
        render.render_frame_buffer_clip(media_file)
    if item_id == "Render Reverse Motion File":
        render.render_reverse_clip(media_file)
    if item_id == "Rename":
        display_media_file_rename_dialog(media_file)
    if item_id == "Delete":
        gui.media_list_view.select_media_file(media_file)
        delete_media_files()
    if item_id == "Render Proxy File":
        proxyediting.create_proxy_menu_item_selected(media_file)
    if item_id == "Edit Container Data":
        containerprogramedit.show_container_data_program_editor_dialog(media_file.container_data)
    if item_id == "Save Container Data":
        media_file.save_program_edit_info()
    if item_id == "Load Container Data":
        media_file.load_program_edit_info()
    if item_id == "Recreate Icon":
        (icon_path, length, info) = projectdata.thumbnailer.write_image(media_file.path)
        media_file.info = info
        media_file.icon_path = icon_path
        media_file.create_icon()
        
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



