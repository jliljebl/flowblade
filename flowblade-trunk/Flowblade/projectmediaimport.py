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

import mlt
import locale
import os
import subprocess
import sys
import threading

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk
from gi.repository import GLib

import editorstate
import editorpersistance
import gui
import guiutils
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import patternproducer
import persistance
import respaths
import renderconsumer
import translations
import utils

"""
This module implements media import from another project feature.

The easiest way to do it is to open file in own process and write media paths to disk.
There is so much bolierplate needed for this feature that it was best to create own module for it.
"""

MEDIA_ASSETS_IMPORT_FILE = "media_assets_import_file"

_info_window = None
_media_paths_written_to_disk_complete_callback = None

class ProjectLoadThread(threading.Thread):
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.filename = filename

    def run(self):
        Gdk.threads_enter()
        _info_window.info.set_text("Loading project " + self.filename + "...")
        Gdk.threads_leave()

        persistance.show_messages = False
        target_project = persistance.load_project(self.filename, False, True)
        
        target_project.c_seq = target_project.sequences[target_project.c_seq_index]

        # Media file media assets
        media_assets = ""
        for media_file_id, media_file in target_project.media_files.iteritems():
            if isinstance(media_file, patternproducer.AbstractBinClip):
                continue
            if os.path.isfile(media_file.path):                
                media_assets = media_assets + str(media_file.path) + "\n"
        
        f = open(_get_assets_file(), 'w')
        f.write(media_assets)
        f.close()

        _shutdown()


class ProcesslauchThread(threading.Thread):
    def __init__(self, filename):
        threading.Thread.__init__(self)
        self.filename = filename

    def run(self):
        write_files(self.filename)


# ----------------------------------------------------------- interface
def import_media_files(project_file_path, callback):
    
    global _media_paths_written_to_disk_complete_callback
    _media_paths_written_to_disk_complete_callback = callback

    # This or GUI freezes, we really can't do Popen.wait() in a Gtk thread
    process_launch_thread = ProcesslauchThread(project_file_path)
    process_launch_thread.start()

def get_imported_media():
    with open(_get_assets_file()) as f:
        files_list = f.readlines()

    files_list = [x.rstrip("\n") for x in files_list] 
    return files_list
    
def write_files(filename):
    print "Starting media import..."
    FLOG = open(utils.get_hidden_user_dir_path() + "log_media_import", 'w')
    p = subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowblademediaimport", filename], stdin=FLOG, stdout=FLOG, stderr=FLOG)
    p.wait()
    
    GLib.idle_add(assets_write_complete)

def assets_write_complete():
    _media_paths_written_to_disk_complete_callback()


# ------------------------------------------------------------ module internal
def _do_assets_write(filename):
    _create_info_dialog()
    
    global load_thread
    load_thread = ProjectLoadThread(filename)
    load_thread.start()
        
def _get_assets_file():
    return utils.get_hidden_user_dir_path() + MEDIA_ASSETS_IMPORT_FILE

def _create_info_dialog():
    dialog = Gtk.Window(Gtk.WindowType.TOPLEVEL)
    dialog.set_title(_("Loading Media Import Project"))

    info_label = Gtk.Label(label="")
    status_box = Gtk.HBox(False, 2)
    status_box.pack_start(info_label, False, False, 0)
    status_box.pack_start(Gtk.Label(), True, True, 0)

    progress_bar = Gtk.ProgressBar()
    progress_bar.set_fraction(0.2)
    progress_bar.set_pulse_step(0.1)

    est_box = Gtk.HBox(False, 2)
    est_box.pack_start(Gtk.Label(label=""),False, False, 0)
    est_box.pack_start(Gtk.Label(), True, True, 0)

    progress_vbox = Gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(progress_bar, True, True, 0)
    progress_vbox.pack_start(est_box, False, False, 0)

    alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)

    dialog.add(alignment)
    dialog.set_default_size(400, 70)
    dialog.set_position(Gtk.WindowPosition.CENTER)
    dialog.show_all()

    # Make refs available for updates
    dialog.progress_bar = progress_bar
    dialog.info = info_label

    global _info_window
    _info_window = dialog


# ----------------------------------------------------------- main
def main(root_path, filename):
    # This the main for launched process, this is reached via 'flowblademediaimport' laucher file
    gtk_version = "%s.%s.%s" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    print "GTK+ version:", gtk_version
    editorstate.gtk_version = gtk_version
    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"

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
        if editorpersistance.prefs.theme == appconsts.FLOWBLADE_THEME:
            gui.apply_gtk_css()
            
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

    GLib.idle_add(_do_assets_write, filename)
    
    Gtk.main()
    Gdk.threads_leave()
    
def _shutdown():
    Gtk.main_quit()
