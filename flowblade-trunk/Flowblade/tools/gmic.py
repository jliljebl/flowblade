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

from gi.repository import GObject, GLib
from gi.repository import Gtk, Gdk, GdkPixbuf

import locale
import mlt
import os
import subprocess
import sys

import dialogutils
import editorstate
import editorpersistance
import guiutils
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
#import persistance
import positionbar
import respaths
import renderconsumer
import translations
import utils


gmic_window = None


def launch_gmic():
    print "Launch gmic..."
    FLOG = open(utils.get_hidden_user_dir_path() + "log_gmic", 'w')
    subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladegmic"], stdin=FLOG, stdout=FLOG, stderr=FLOG)


def main(root_path, force_launch=False):
    init_dirs_if_needed()
    
    gtk_version = "%s.%s.%s" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
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

    # Request dark them if so desired
    if editorpersistance.prefs.dark_theme == True:
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)

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

    global gmic_window
    gmic_window = GmicWindow()

    Gtk.main()
    Gdk.threads_leave()
    
def init_dirs_if_needed():
    user_dir = utils.get_hidden_user_dir_path()

    """
    if not os.path.exists(user_dir + BATCH_DIR):
        os.mkdir(user_dir + BATCH_DIR)
    if not os.path.exists(get_datafiles_dir()):
        os.mkdir(get_datafiles_dir())
    if not os.path.exists(get_projects_dir()):
        os.mkdir(get_projects_dir())
    """


class GmicWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.connect("delete-event", lambda w, e:_shutdown())

        app_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "flowblademedialinker.png")
        self.set_icon(app_icon)


        self.pos_bar = positionbar.PositionBar(False)
        self.pos_bar.set_listener(self.position_listener)

        load_button = Gtk.Button(_("Load Clip"))
        load_button.connect("clicked",
                            lambda w: self.load_button_clicked())

        project_row = Gtk.HBox(False, 2)
        project_row.pack_start(load_button, False, False, 0)
        project_row.pack_start(Gtk.Label(), True, True, 0)

        left_vbox = Gtk.VBox(False, 0)
        left_vbox.pack_start(self.pos_bar.widget, False, False, 0)

        pane = Gtk.VBox(False, 2)
        pane.pack_start(project_row, False, False, 0)
        pane.pack_start(left_vbox, False, False, 0)

        align = guiutils.set_margins(pane, 12, 12, 12, 12)

        # Set pane and show window
        self.add(align)
        self.set_title(_("G'MIC Effects"))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()
        self.set_resizable(False)
        self.set_active_state()
    
    def load_button_clicked(self):
        dialogs.load_project_dialog(self.load_project_dialog_callback, self)
    
    def set_active_state(self):
        pass

    def position_listener(self, normalized_pos, length):
        frame = normalized_pos * length
        self.tc_display.set_frame(int(frame))
        self.pos_bar.widget.queue_draw()
