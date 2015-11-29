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
from gi.repository import GdkX11

import locale
import mlt
import os
import subprocess
import sys

import dialogutils
import editorstate
import editorpersistance
import gui
import guiutils
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import positionbar
import respaths
import renderconsumer
import translations
import utils

import gmicplayer

_window = None
_player = None

def launch_gmic():
    print "Launch gmic..."
    gui.save_current_colors()
    
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

    gui.load_current_colors()
    
    global _window
    _window = GmicWindow()
    
    #gui.set_theme_colors()
    _window.pos_bar.set_dark_bg_color()
    
    os.putenv('SDL_WINDOWID', str(_window.monitor.get_window().get_xid()))
    Gdk.flush()
        
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

def open_clip_dialog(callback):
    

    file_select = Gtk.FileChooserDialog(_("Select Image Media"), _window, Gtk.FileChooserAction.OPEN,
                                    (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

    file_select.set_default_response(Gtk.ResponseType.CANCEL)
    file_select.set_select_multiple(False)

    media_filter = utils.get_media_source_file_filter(False)
    all_filter = Gtk.FileFilter()
    all_filter.set_name(_("All files"))
    all_filter.add_pattern("*.*")
    file_select.add_filter(media_filter)
    file_select.add_filter(all_filter)

    if ((editorpersistance.prefs.open_in_last_opended_media_dir == True) 
        and (editorpersistance.prefs.last_opened_media_dir != None)):
        file_select.set_current_folder(editorpersistance.prefs.last_opened_media_dir)
    
    file_select.connect('response', callback)

    file_select.set_modal(True)
    file_select.show()

def _open_files_dialog_cb(file_select, response_id):
    filenames = file_select.get_filenames()
    file_select.destroy()

    if response_id != Gtk.ResponseType.OK:
        return
    if len(filenames) == 0:
        return

    global _player
    _player = gmicplayer.GmicPlayer(filenames[0])
    _window.init_for_new_clip(filenames[0])
    _player.create_sdl_consumer()
    _player.connect_and_start()
    #_window.pos_bar.widget.queue_draw()

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

        black_box = Gtk.EventBox()
        black_box.add(Gtk.Label())
        bg_color = Gdk.Color(red=0.0, green=0.0, blue=0.0)
        black_box.modify_bg(Gtk.StateType.NORMAL, bg_color)
        self.monitor = black_box  # This could be any GTK+ widget (that is not "windowless"), only its XWindow draw rect 
                                  # is used to position and scale SDL overlay that actually displays video.
        self.monitor.set_size_request(400, 300)

        
        pane = Gtk.VBox(False, 2)
        pane.pack_start(project_row, False, False, 0)
        pane.pack_start(self.monitor, False, False, 0)
        pane.pack_start(left_vbox, False, False, 0)

        align = guiutils.set_margins(pane, 12, 12, 12, 12)

        # Set pane and show window
        self.add(align)
        self.set_title(_("G'MIC Effects"))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()
        self.set_resizable(False)
        self.set_active_state(False)

    def init_for_new_clip(self, clip_path):
        self.clip_path = clip_path
        self.set_active_state(True)
        self.pos_bar.update_display_from_producer(_player.producer)
    
    def load_button_clicked(self):
        open_clip_dialog(_open_files_dialog_cb)
    
    def set_active_state(self, active):
        self.monitor.set_sensitive(active)
        self.pos_bar.widget.set_sensitive(active)

    def position_listener(self, normalized_pos, length):
        frame = normalized_pos * length
        #self.tc_display.set_frame(int(frame))
        self.pos_bar.widget.queue_draw()
