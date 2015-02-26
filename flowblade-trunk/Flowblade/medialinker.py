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

import pygtk
pygtk.require('2.0');
import gtk
import mlt
import locale
import os
import pango
import subprocess
import sys
import threading

import dialogs
import dialogutils
import editorstate
import editorpersistance
import guiutils
import guicomponents
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import persistance
import respaths
import renderconsumer
import translations


linker_window = None
target_project = None
media_assets = []


def display_linker():
    print "Launching Media Re-linker"
    FNULL = open(os.devnull, 'w')
    subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowblademedialinker"], stdin=FNULL, stdout=FNULL, stderr=FNULL)


# -------------------------------------------------------- render thread
class ProjectLoadThread(threading.Thread):
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.filename = filename

    def run(self):
        gtk.gdk.threads_enter()
        linker_window.project_label.set_text("Loading...")
        gtk.gdk.threads_leave()

        persistance.loading_for_batch_render = True # !?!
        persistance.show_messages = False
        project = persistance.load_project(self.filename, False, True)
        persistance.loading_for_batch_render = False
        
        global target_project
        target_project = project
        _update_media_assets()
        
        gtk.gdk.threads_enter()
        linker_window.relink_list.fill_data_model()
        linker_window.project_label.set_text(self.filename)
        linker_window.set_active_state()
        linker_window.update_files_info()
        gtk.gdk.threads_leave()


class MediaLinkerWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.connect("delete-event", lambda w, e:_shutdown())
        
        load_button = gtk.Button(_("Load Project For Relinking"))
        load_button.connect("clicked",
                            lambda w: self.load_button_clicked())

        
        project_row = gtk.HBox(False, 2)
        project_row.pack_start(load_button, False, False, 0)
        project_row.pack_start(gtk.Label(), True, True, 0)

        self.missing_label = gtk.Label(_("Original Media Missing:"))
        self.found_label = gtk.Label(_("Original Media Found:"))
        self.missing_count = gtk.Label()
        self.found_count = gtk.Label()
        self.proj = gtk.Label(_("Project:"))
        self.project_label = gtk.Label(_("<not loaded>"))
            
        missing_info = guiutils.get_left_justified_box([self.missing_label, guiutils.pad_label(2, 2), self.missing_count])
        missing_info.set_size_request(200, 2)
        found_info = guiutils.get_left_justified_box([self.found_label, guiutils.pad_label(2, 2), self.found_count])

        status_row = gtk.HBox(False, 2)
        status_row.pack_start(missing_info, False, False, 0)
        status_row.pack_start(found_info, False, False, 0)
        status_row.pack_start(gtk.Label(), True, True, 0)
        status_row.pack_start(guiutils.pad_label(30, 12), False, False, 0)
        status_row.pack_start(self.proj, False, False, 0)
        status_row.pack_start(guiutils.pad_label(4, 12), False, False, 0)
        status_row.pack_start(self.project_label, False, False, 0)
        
        self.relink_list = MediaRelinkListView()

        self.find_button = gtk.Button(_("Set File Relink Path"))
        self.delete_button = gtk.Button(_("Delete File Relink Path"))
        self.auto_locate_check = gtk.CheckButton()
        self.auto_label = gtk.Label(_("Autorelink other files"))

        self.display_combo = gtk.combo_box_new_text()
        self.display_combo.append_text(_("Display Missing Media Files"))
        self.display_combo.append_text(_("Display Found Found Media Files"))
        self.display_combo.set_active(0)
        self.display_combo.connect("changed", self.display_list_changed)
        
        buttons_row = gtk.HBox(False, 2)
        buttons_row.pack_start(self.display_combo, False, False, 0)
        buttons_row.pack_start(gtk.Label(), True, True, 0)
        buttons_row.pack_start(self.delete_button, False, False, 0)
        buttons_row.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        buttons_row.pack_start(self.auto_locate_check, False, False, 0)
        buttons_row.pack_start(self.auto_label, False, False, 0)
        buttons_row.pack_start(guiutils.pad_label(4, 4), False, False, 0)
        buttons_row.pack_start(self.find_button, False, False, 0)

        self.save_button = gtk.Button(_("Save Project As..."))
        cancel_button = gtk.Button(_("Close"))
        dialog_buttons_box = gtk.HBox(True, 2)
        dialog_buttons_box.pack_start(cancel_button, True, True, 0)
        dialog_buttons_box.pack_start(self.save_button, False, False, 0)
        
        dialog_buttons_row = gtk.HBox(False, 2)
        dialog_buttons_row.pack_start(gtk.Label(), True, True, 0)
        dialog_buttons_row.pack_start(dialog_buttons_box, False, False, 0)

        pane = gtk.VBox(False, 2)
        pane.pack_start(project_row, False, False, 0)
        pane.pack_start(guiutils.pad_label(24, 24), False, False, 0)
        pane.pack_start(status_row, False, False, 0)
        pane.pack_start(guiutils.pad_label(24, 2), False, False, 0)
        pane.pack_start(self.relink_list, False, False, 0)
        pane.pack_start(buttons_row, False, False, 0)
        pane.pack_start(guiutils.pad_label(24, 24), False, False, 0)
        pane.pack_start(dialog_buttons_row, False, False, 0)
        
        align = gtk.Alignment()
        align.set_padding(12, 12, 12, 12)
        align.add(pane)

        # Set pane and show window
        self.add(align)
        self.set_title(_("Media Re-linker"))
        self.show_all()
        self.set_resizable(False)
        self.set_keep_above(True) # Perhaps configurable later
        self.set_active_state()

    def load_button_clicked(self):
        dialogs.load_project_dialog(self.load_project_dialog_callback)
    
    def load_project_dialog_callback(self, dialog, response_id):
        if response_id == gtk.RESPONSE_ACCEPT:
            filenames = dialog.get_filenames()
            
            dialog.destroy()
            
            global load_thread
            load_thread = ProjectLoadThread(filenames[0])
            load_thread.start()

        else:
            dialog.destroy()

    def display_list_changed(self, display_combo):
         self.relink_list.fill_data_model()

    def set_active_state(self):
        active = (target_project != None)
        
        self.save_button.set_sensitive(active) 
        self.relink_list.set_sensitive(active) 
        self.find_button.set_sensitive(active) 
        self.delete_button.set_sensitive(active) 
        self.auto_locate_check.set_sensitive(active) 
        self.auto_label.set_sensitive(active) 
        self.display_combo.set_sensitive(active) 
        self.missing_label.set_sensitive(active) 
        self.found_label.set_sensitive(active) 
        self.missing_count.set_sensitive(active) 
        self.found_count.set_sensitive(active) 
        self.project_label.set_sensitive(active) 
        self.proj.set_sensitive(active) 

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


class MediaRelinkListView(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)

        self.assets = [] # Used to store list displayd data items
        
       # Datamodel: icon, text, text
        self.storemodel = gtk.ListStore(str, str)
 
        # Scroll container
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # View
        self.treeview = gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(True)
        self.treeview.connect("button-press-event", self.row_pressed)
        tree_sel = self.treeview.get_selection()

        # Column views
        self.text_col_1 = gtk.TreeViewColumn("text1")
        self.text_col_1.set_title(_("Media File Path"))
        self.text_col_2 = gtk.TreeViewColumn("text2")
        self.text_col_2.set_title(_("Media File Re-link Path"))
        
        # Cell renderers
        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_START)

        self.text_rend_2 = gtk.CellRendererText()
        self.text_rend_2.set_property("ellipsize", pango.ELLIPSIZE_START)
        self.text_rend_2.set_property("yalign", 0.0)

        # Build column views
        self.text_col_1.set_expand(True)
        self.text_col_1.pack_start(self.text_rend_1)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 0)
    
        self.text_col_2.set_expand(True)
        self.text_col_2.pack_start(self.text_rend_2)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 1)

        # Add column views to view
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
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
                row_data = [media_asset.media_file.path,
                            relink]
                self.storemodel.append(row_data)
                self.assets.append(media_asset)

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

    def __init__(self, media_file):
        self.media_file = media_file
        self.orig_file_exists = os.path.isfile(media_file.path) 
        self.relink_path = None

def _update_media_assets():
    new_assets = []
    for media_file_id, media_file in target_project.media_files.iteritems():
        new_assets.append(MediaAsset(media_file))
    
    global media_assets
    media_assets = new_assets
        
def _media_asset_menu_item_selected(widget, data):
    msg, row = data
    media_asset = linker_window.relink_list.assets[row]
    print media_asset, msg
    if msg == "set relink":
        _set_relink_path(media_asset)
    if msg == "delete relink":
        _delete_relink_path(media_asset)
        
def _set_relink_path(media_asset):
    dialogs.media_file_dialog(_("Select Media File To Relink"), _select_relink_path_dialog_callback, False, media_asset)

def _select_relink_path_dialog_callback(file_select, response_id, media_asset):
    filenames = file_select.get_filenames()
    file_select.destroy()

    if response_id != gtk.RESPONSE_OK:
        return
    if len(filenames) == 0:
        return

    media_asset.relink_path = filenames[0]
    linker_window.relink_list.fill_data_model()
        
def _delete_relink_path(media_asset):
    media_asset.relink_path = None
    linker_window.relink_list.fill_data_model()
            
# ----------------------------------------------------------- main
def main(root_path, force_launch=False):
    editorstate.gtk_version = gtk.gtk_version
    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"
        
    # Set paths.
    respaths.set_paths(root_path)

    # Init translations module with translations data
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()

    # Load editor prefs and list of recent projects
    editorpersistance.load()

    # Init gtk threads
    gtk.gdk.threads_init()
    gtk.gdk.threads_enter()

    repo = mlt.Factory().init()

    # Set numeric locale to use "." as radix, MLT initilizes this to OS locale and this causes bugs 
    locale.setlocale(locale.LC_NUMERIC, 'C')

    # Check for codecs and formats on the system
    mltenv.check_available_features(repo)
    renderconsumer.load_render_profiles()

    # Load filter and compositor descriptions from xml files.
    mltfilters.load_filters_xml(mltenv.services)
    mlttransitions.load_compositors_xml(mltenv.transitions)

    # Create list of available mlt profiles
    mltprofiles.load_profile_list()

    global linker_window
    linker_window = MediaLinkerWindow()

    gtk.main()
    gtk.gdk.threads_leave()
    
def _shutdown():
    gtk.main_quit()
