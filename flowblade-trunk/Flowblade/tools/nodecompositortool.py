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
from gi.repository import Pango

import locale
import md5
import mlt
import os
import socket
import subprocess
import time
import threading

import appconsts
import editorstate
import editorpersistance
import gui
import guiutils
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import nodecompositorscript
import nodecompositoreditors
import renderconsumer
import respaths
import toolguicomponents
import translations
import threading
import utils

_window = None
_session_id = None

_phantom_session_port = None
_phantom_socket = None
_current_phantom_prog = None

def main(root_path, force_launch=False):
       
    gtk_version = "%s.%s.%s" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
    editorstate.gtk_version = gtk_version
    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"
    
    global _session_id
    _session_id = md5.new(str(time.time())).hexdigest()

    # Set paths.
    respaths.set_paths(root_path)

    # Init gmic tool session dirs
    if os.path.exists(get_session_folder()):
        shutil.rmtree(get_session_folder())
        
    os.mkdir(get_session_folder())
    
    phantom_launch = PhantomServerLaunchScript()
    phantom_launch.start()

    #init_frames_dirs()
    
    # Load editor prefs and list of recent projects
    editorpersistance.load()
    if editorpersistance.prefs.dark_theme == True:
        respaths.apply_dark_theme()

    # Init translations module with translations data
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()

    nodecompositorscript.load_phantom_readymades_xml()

    # Load preset gmic scripts
    #gmicscript.load_preset_scripts_xml()
    
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
    
    # The lauched phantom server writes the port it is listening to
    # into a text file in session folder
    read_session_phantom_socket_port()
    # Create a socket to talk to phantom server
    create_phantom_socket()

    global _window
    _window = CompositorProgramsWindow()
    #_window.pos_bar.set_dark_bg_color()

    #os.putenv('SDL_WINDOWID', str(_window.monitor.get_window().get_xid()))
    #Gdk.flush()

    GLib.idle_add(init_session)

    Gtk.main()
    Gdk.threads_leave()

#----------------------------------------------- commands
def create_phantom_socket():
    global _phantom_socket, _phantom_socket_read_file
    _phantom_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _phantom_socket.connect(("localhost", _phantom_session_port))

def close_phantom_socket():
     _phantom_socket.close();
     
def send_phantom_command(command):
    _phantom_socket.send(command + "\n")

    print "PY command sent:", command
          
    answer = _phantom_socket.recv(1024)
    print "PY answer:", answer

def init_session():
    global _current_phantom_prog
    phantom_prog = nodecompositorscript.get_default_phantom_prog()
    init_phantom_prog(phantom_prog)

def init_phantom_prog(phantom_prog):
    global _current_phantom_prog
    _current_phantom_prog = phantom_prog
    
    load_command = "LOAD " + respaths.PHANTOM_READYMADES_DIR + _current_phantom_prog.project_file
    send_phantom_command(load_command)
    
    folder_command = "SET_FOLDER /home/janne/test/phantom_server_frames/"
    send_phantom_command(folder_command)
    
    editors = nodecompositoreditors.get_phantom_param_editors(_current_phantom_prog)
    
    _window.show_program_editors(editors)

    param = phantom_prog.params[ 0 ]

    param_command = "PARAM_VALUE " + str(param.nodeid) + " " + str(param.paramid) + " " + param.paramtype + " 128 128 255"
    print param_command
    send_phantom_command(param_command)
    
    render_command = "RENDER_FRAME 16"
    send_phantom_command(render_command)
    
    #close_phantom_socket()
    
#----------------------------------------------- session folders and files
def get_session_folder():
    return utils.get_hidden_user_dir_path() + appconsts.NODE_COMPOSITORS_DIR + "/session_" + str(_session_id)

def get_session_phantom_socket_file():
    return get_session_folder() + "/socketnumberfile"

def read_session_phantom_socket_port():
    while os.path.exists(get_session_phantom_socket_file()) == False:
        print "waiting for socket file..."
        time.sleep(0.2)
    
    f = open(get_session_phantom_socket_file(), "r")
    port_str = f.read()
    global _phantom_session_port
    _phantom_session_port = int(port_str)
    print "Phantom server port:", _phantom_session_port

# --------------------------------------------------------- #
def _shutdown():
    close_phantom_socket()
    # Exit gtk main loop.
    Gtk.main_quit()

def programs_menu_lauched(launcher, event):
    nodecompositorscript.show_menu(event, programs_menu_item_selected)

def programs_menu_item_selected(item, script):
    """
    if _window.action_select.get_active() == False:
        _window.script_view.get_buffer().set_text(script.script)
    else:
        buf = _window.script_view.get_buffer()
        buf.insert(buf.get_end_iter(), " " + script.script)
    _window.preset_label.set_text(script.name)
    """

def activate_phantom_program(prog):
    pass


class CompositorProgramsWindow(Gtk.Window):

    def __init__(self):
        GObject.GObject.__init__(self)
        self.connect("delete-event", lambda w, e:_shutdown())

        app_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "flowbladetoolicon.png")
        self.set_icon(app_icon)

        # Script area
        self.program_label = Gtk.Label()
        self.program_event_box = Gtk.EventBox()
        self.program_event_box.add(self.program_label)
        self.program_event_box.connect("button-press-event",  programs_menu_lauched)

        self.programs_menu = toolguicomponents.PressLaunch(programs_menu_lauched)

        programs_row = Gtk.HBox()
        programs_row.pack_start(self.programs_menu.widget, False, False, 0)
        programs_row.pack_start(self.program_event_box, False, False, 0)
        programs_row.pack_start(Gtk.Label(), True, True, 0)

        self.editors_box = Gtk.VBox(False, 2)
        self.editors_box.pack_start(Gtk.Label(), False, False, 0)
        self.editors_container = Gtk.VBox(False, 2)
        self.editors_container.pack_start(self.editors_box, False, False, 0)
        
        self.close_button = guiutils.get_sized_button(_("Close"), 150, 32)
        self.close_button.connect("clicked", lambda w:_shutdown())
        
        editor_buttons_row = Gtk.HBox()
        editor_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        editor_buttons_row.pack_start(self.close_button, False, False, 0)

        # Build window
        pane = Gtk.VBox(False, 2)
        pane.pack_start(programs_row, False, False, 0)
        pane.pack_start(self.editors_container, False, False, 0)
        pane.pack_start(editor_buttons_row, False, False, 0)

        align = guiutils.set_margins(pane, 12, 12, 12, 12)

        # Set pane and show window
        self.add(align)
        self.set_title(_("Node Compositor Programs"))
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()
        #self.set_resizable(False)

    def show_program_editors(self, editors):
        new_edit_box = Gtk.VBox()
        for editor in editors:
            new_edit_box.pack_start(editor.widget, False, False, 0)
            print editor
        new_edit_box.pack_start(Gtk.Label(), True, True, 0)
        
        self.editors_container.remove(self.editors_box)
        self.editors_box = new_edit_box
        self.editors_container.pack_start(self.editors_box, False, False, 0)
        self.editors_box.show_all()

class PhantomServerLaunchScript(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        launch_command = "java -jar " + respaths.PHANTOM_JAR + " -server " + get_session_phantom_socket_file()
        process = subprocess.Popen(launch_command.split(), stdout=subprocess.PIPE)
        while True:
          line = process.stdout.readline()
          if not line:
              break
          print line
          
