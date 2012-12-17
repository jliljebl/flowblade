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
import gtk
import os
import subprocess
import sys
import time
import threading
    
import app
import appconsts
import clipeffectseditor
import dialogs
import dialogutils
import gui
import guicomponents
import editorstate
from editorstate import current_sequence
from editorstate import current_bin
from editorstate import PLAYER
from editorstate import PROJECT
from editorstate import MONITOR_MEDIA_FILE
import editorpersistance
import mltplayer
import mltprofiles
import movemodes
import panels
import persistance
import projectdata
import render
import respaths
import sequence
import test
import undo
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

        dialog = dialogs.get_load_dialog()
        persistance.load_dialog = dialog
        gtk.gdk.threads_leave()

        ticker = utils.Ticker(_load_pulse_bar, 0.15)
        ticker.start_ticker()

        try:
            project = persistance.load_project(self.filename)
            sequence.set_track_counts(project)
        except persistance.FileProducerNotFoundError as e:
            print "did not find file:", e
            gtk.gdk.threads_enter()
            updater.set_info_icon(None)
            dialog.destroy()
            gtk.gdk.threads_leave()
            ticker.stop_ticker()
            primary_txt = _("File: ") + e.value + _(" was not found on load!")
            secondary_txt = _("Place dummy file with same name and similar content to enable") + "\n" + _("project load. ") + \
                            _("Doing so does not quarantee succesful load") + "\n" + _("if files have different properties.")
            dialogutils.warning_message(primary_txt, secondary_txt, None, is_info=False)
            return
    
        gtk.gdk.threads_enter()
        dialog.info.set_text(_("Opening"))
        gtk.gdk.threads_leave()

        time.sleep(0.3)
        
        gtk.gdk.threads_enter()
        app.open_project(project)

        if self.block_recent_files:
            editorpersistance.add_recent_project_path(self.filename)
            editorpersistance.fill_recents_menu_widget(gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent'), open_recent_project)

        gtk.gdk.threads_leave()
        
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

        duplicates = 0
        succes_new_file = None
        filenames = self.filenames
        for new_file in filenames:
            (dir, file_name) = os.path.split(new_file)
            if PROJECT().media_file_exists(new_file):
                duplicates = duplicates + 1
            else:
                try:
                    PROJECT().add_media_file(new_file)
                    succes_new_file = new_file
                except projectdata.ProducerNotValidError as err:
                    dialogs.not_valid_producer_dialog(err.value, gui.editor_window.window)
                    
        if succes_new_file != None:
            editorpersistance.prefs.last_opened_media_dir = os.path.dirname(succes_new_file)
            editorpersistance.save()

        # Update editor gui
        gtk.gdk.threads_enter()
        gui.media_list_view.fill_data_model()
        gui.bin_list_view.fill_data_model()
        _enable_save()
        
        selection = gui.media_list_view.treeview.get_selection()
        selection.select_path("0")
        normal_cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR) #RTL
        gui.editor_window.window.window.set_cursor(normal_cursor)
        gtk.gdk.threads_leave()


def _load_pulse_bar():
    gtk.gdk.threads_enter()
    try: 
        # For visual reasons we destroy window before we stop pulsebar events
        # so this might get called on a destroyd dialog.
        # ...and pulse still freezes, meh.
        persistance.load_dialog.progress_bar.pulse()
    except:
        pass
    gtk.gdk.threads_leave()

def _enable_save():
    gui.editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(True)
 
# ---------------------------------- project: new, load, save
def new_project():
    dialogs.new_project_dialog(_new_project_dialog_callback)

def _new_project_dialog_callback(dialog, response_id, profile_combo, tracks_combo, tracks_combo_values_list):
    v_tracks, a_tracks = tracks_combo_values_list[tracks_combo.get_active()]
    if response_id == gtk.RESPONSE_ACCEPT:
        app.new_project(profile_combo.get_active(), v_tracks, a_tracks)
        dialog.destroy()
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

    profile = mltprofiles.get_default_profile()
    new_project = projectdata.Project(profile)
    app.open_project(new_project)
    
def actually_load_project(filename, block_recent_files=False):
    load_launch = LoadThread(filename, block_recent_files)
    load_launch.start()

def save_project():
    if PROJECT().last_save_path == None:
        save_project_as()
    else:
        updater.set_info_icon(gtk.STOCK_SAVE)

        persistance.save_project(PROJECT(), PROJECT().last_save_path) #<----- HERE

        global save_icon_remove_event_id
        save_icon_remove_event_id = gobject.timeout_add(500, remove_save_icon)

        global save_time
        save_time = time.clock()
        
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
        
        persistance.save_project(PROJECT(), PROJECT().last_save_path) #<----- HERE
        
        app.stop_autosave()
        app.start_autosave()
        
        global save_icon_remove_event_id
        save_icon_remove_event_id = gobject.timeout_add(500, remove_save_icon)

        global save_time
        save_time = time.clock()

        gui.editor_window.window.set_title(PROJECT().name + " - pyedit")        
        gui.editor_window.uimanager.get_widget("/MenuBar/FileMenu/Save").set_sensitive(False)
        gui.editor_window.uimanager.get_widget("/MenuBar/EditMenu/Undo").set_sensitive(False)
        gui.editor_window.uimanager.get_widget("/MenuBar/EditMenu/Redo").set_sensitive(False)

        editorpersistance.add_recent_project_path(PROJECT().last_save_path)
        editorpersistance.fill_recents_menu_widget(gui.editor_window.uimanager.get_widget('/MenuBar/FileMenu/OpenRecent'), open_recent_project)
        
        updater.update_project_info(PROJECT())
        
        dialog.destroy()
    else:
        dialog.destroy()

def export_melt_xml():
    dialogs.export_xml_dialog(_export_melt_xml_dialog_callback, PROJECT().name)

def _export_melt_xml_dialog_callback(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        filenames = dialog.get_filenames()
        save_path = filenames[0]
        PLAYER().start_xml_rendering(save_path)
        dialog.destroy()
    else:
        dialog.destroy()

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
    render.render_timeline()

     
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

    file_select = gtk.FileChooserDialog(_("Open.."),None, 
                                    gtk.FILE_CHOOSER_ACTION_OPEN,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OPEN, gtk.RESPONSE_OK))

    file_select.set_default_response(gtk.RESPONSE_CANCEL)
    file_select.set_select_multiple(True)

    media_filter = utils.get_media_source_file_filter()
    all_filter = gtk.FileFilter()
    all_filter.set_name(_("All files"))
    all_filter.add_pattern("*.*")
    file_select.add_filter(media_filter)
    file_select.add_filter(all_filter)

    if ((editorpersistance.prefs.open_in_last_opended_media_dir == True) 
        and (editorpersistance.prefs.last_opened_media_dir != None)):
        file_select.set_current_folder(editorpersistance.prefs.last_opened_media_dir)
    
    file_select.connect('response', _open_files_dialog_cb)
    file_select.set_modal(True)
    file_select.show()

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
    print "add image sequence"

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
    
            
def delete_media_files():
    """
    Deletes media file. Does not take into account if clips made from 
    media file are still in sequence.(maybe change this)
    """
    selection = gui.media_list_view.treeview.get_selection()
    (model, rows) = selection.get_selected_rows()
    if len(rows) < 1:
        return
    
    refs = []
    file_ids = []
    bin_indexes = []
    # Get:
    # - list of integer keys to delete from Project.media_files
    # - list of indexes to delete from Bin.file_ids
    # - references to ListStore rows to delete from gui
    for row in rows:
        row_index = max(row) # row is single element tuple, for some reason
        bin_indexes.append(row_index) 
        file_id = current_bin().file_ids[row_index] 
        file_ids.append(file_id)
        media_file = PROJECT().media_files[file_id]

        # If clip is displayed in monitor clear it and disable clip button.
        if media_file == MONITOR_MEDIA_FILE:
            editorstate._monitor_media_file = None
            gui.clip_editor_b.set_sensitive(False)

        ref = gtk.TreeRowReference(model, row)
        refs.append(ref)
    
    # Delete rows from ListStore (gui)
    for ref in refs:
        iter = model.get_iter(ref.get_path())
        model.remove(iter)
        
    # Delete from bin
    bin_indexes.reverse()
    for i in bin_indexes:
        current_bin().file_ids.pop(i)
        
    # Delete from project
    for file_id in file_ids:
        PROJECT().media_files.pop(file_id)
    
    _enable_save()

def media_file_name_edited(cell, path, new_text, user_data):
    """
    Sets edited value to liststore and project data.
    """
    # Can't have empty string names
    if len(new_text) == 0:
        return
    
    # Update liststore data
    liststore, column = user_data
    liststore[path][column] = new_text
    
    # Set media file name
    file_id = current_bin().file_ids[int(path)] 
    media_file = PROJECT().media_files[file_id]
    media_file.name = new_text
    _enable_save()

def _display_file_info(media_file):
    clip = current_sequence().create_file_producer_clip(media_file.path)

    width = clip.get("width")
    height = clip.get("height")
    size = str(width) + " x " + str(height)
    length = utils.get_tc_string(clip.get_length())

    try:
        img = gtk.Image()
        source_path = media_file.icon_path
        pixbuf = gtk.gdk.pixbuf_new_from_file(source_path)
        IMG_HEIGHT = 300
        icon_width = int((float(pixbuf.get_width()) / float(pixbuf.get_height())) * IMG_HEIGHT)
        s_pbuf = pixbuf.scale_simple(icon_width, IMG_HEIGHT, gtk.gdk.INTERP_BILINEAR)
        p_map, mask = s_pbuf.render_pixmap_and_mask()
        img.set_from_pixmap(p_map, None)
    except:
        print "_display_file_info() failed to get thumbnail"
        # stock broken here?
    
    video_index = clip.get_int("video_index")
    audio_index = clip.get_int("audio_index")
    long_video_property = "meta.media." + str(video_index) + ".codec.long_name"
    long_audio_property = "meta.media." + str(audio_index) + ".codec.long_name"
    vcodec = clip.get(str(long_video_property))
    acodec = clip.get(str(long_audio_property))
    
    frame = clip.get_frame()
    channels = str(frame.get_int("channels"))
    frequency = str(frame.get_int("frequency")) + "Hz"
    
    dialogs.file_properties_dialog((media_file, img, size, length, vcodec, acodec, channels, frequency))

# ------------------------------------ bins
def add_new_bin():
    """
    Adds new unnamed bin and sets it selected 
    """
    PROJECT().add_unnamed_bin()
    gui.bin_list_view.fill_data_model()
    selection = gui.bin_list_view.treeview.get_selection()
    model, iter = selection.get_selected()
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
    
def move_files_to_bin(new_bin, moved_rows):
    # If we're moving clips to bin that they're already in, do nothing.
    if PROJECT().bins[new_bin] == current_bin():
        return

    # Delete from current bin
    refs = []
    moved_ids = []
    bin_indexes = []
    
    selection = gui.media_list_view.treeview.get_selection()
    (model, rows) = selection.get_selected_rows()

    for row_index in moved_rows:
        bin_indexes.append(row_index)

        ref = gtk.TreeRowReference(model, (row_index))
        refs.append(ref)
    
    # Delete rows from ListStore (gui)
    for ref in refs:
        iter = model.get_iter(ref.get_path())
        model.remove(iter)
        
    # Delete from bin
    bin_indexes.reverse()
    for i in bin_indexes:
        moved_ids.append(current_bin().file_ids.pop(i))
        
    # Add to target bin
    for file_id in moved_ids:
        PROJECT().bins[new_bin].file_ids.append(file_id)

    gui.bin_list_view.fill_data_model()
    gui.bin_list_view.queue_draw()
    
    

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
    dialogs.get_new_sequence_dialog(_add_new_sequence_dialog_callback, default_name)
    
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
    dialogs.get_tracks_count_change_dialog(_change_track_count_dialog_callback)

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
    


# -------------------------------------------------------- effects editor
def effect_select_row_double_clicked(treeview, tree_path, col):
    clipeffectseditor.add_currently_selected_effect()




# --------------------------------------------------------- pop-up menus
def media_list_button_press(widget, event):
    if event.button == 3:
        row, column_title = _select_treeview_on_pos_and_return_row_and_column_title(event, gui.media_list_view.treeview)
        try:
            media_file_id = current_bin().file_ids[row]
        except:# right clicking on empty bin fails on previous line
            return False
        guicomponents.diplay_media_file_popup_menu(PROJECT().media_files[media_file_id],
                                                   _media_file_menu_item_selected,
                                                   event)
        return True
            
    return False
    
def _media_file_menu_item_selected(widget, data):
    item_id, media_file, event = data
    if item_id == "File Properties":
        _display_file_info(media_file)
    if item_id == "Open in Clip Monitor":
        updater.set_and_display_monitor_media_file(media_file)
    if item_id == "Delete":
        delete_media_files()
    if item_id == "Render Slow/Fast Motion File":
        render.render_frame_buffer_clip(media_file)

def filter_stack_button_press(widget, event):
    row, column_title = _select_treeview_on_pos_and_return_row_and_column_title(event, widget)
    if row == -1:
        return False
    if event.button == 3:
        guicomponents.display_filter_stack_popup_menu(row, widget, _filter_stack_menu_item_selected, event)                                    
        return True
    return False

def _filter_stack_menu_item_selected(widget, data):
    item_id, row, treeview = data
    # Toggle filter active state
    if item_id == "toggle":
        clipeffectseditor.toggle_filter_active(row)
    if item_id == "reset":
        clipeffectseditor.reset_filter_values()

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


def lauch_batch_rendering():
    subprocess.Popen([sys.executable, respaths.ROOT_PARENT + "flowbladebatch"], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.STDOUT)

# We need to do this on app start-up
# we'll get circular imports with useraction->mltplayer->render->useraction
# if just try to import so we'll just put this callback func in
render.open_media_file_callback = open_rendered_file
