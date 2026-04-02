"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2026 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib, GObject
from gi.repository import Pango

import os
import threading

import appconsts
import editorpersistance
import gui
import respaths
import guiutils
import userfolders
import utilsgtk
import translations

FIFO_PATH= "/tmp/flowblade_progress_fifo"

SHUTDOWN = "&&SHUTDOWN"

_app = None
_messages_thread = None
_window = None

        
def write_message(msg):
    os.mkfifo(FIFO_PATH) if not os.path.exists(FIFO_PATH) else None

    with open(FIFO_PATH, 'w') as fifo:
        fifo.write(msg)
        fifo.flush()

    
def main(root_path):
    respaths.set_paths(root_path)
    userfolders.init()
    editorpersistance.load()
    editorpersistance.prefs.theme = appconsts.FLOWBLADE_THEME_NEUTRAL
    
    app = LoadDialogApplication()
    global _app
    _app = app
    app.run(None)


class LoadDialogApplication(Gtk.Application):
    def __init__(self, *args, **kwargs):
        Gtk.Application.__init__(self, application_id=None,
                                 flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)

    def on_activate(self, data=None):
        translations.init_languages()
    
        gui.apply_theme()

        global _window
        _window = LoadProgressWindow()

        GLib.idle_add(_launch_threads)
        
        self.add_window(_window)


class LoadProgressWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)

        self.set_title(_("Loading project"))

        global _info_label
        _info_label = Gtk.Label(label="")
        _info_label.set_ellipsize(Pango.EllipsizeMode.END)
        status_box = Gtk.HBox(False, 2)
        status_box.pack_start(_info_label, False, False, 0)
        status_box.pack_start(Gtk.Label(), True, True, 0)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.2)
        self.progress_bar.set_pulse_step(0.1)

        est_box = Gtk.HBox(False, 2)
        est_box.pack_start(Gtk.Label(label=""),False, False, 0)
        est_box.pack_start(Gtk.Label(), True, True, 0)

        progress_vbox = Gtk.VBox(False, 2)
        progress_vbox.pack_start(status_box, False, False, 0)
        progress_vbox.pack_start(self.progress_bar, True, True, 0)
        progress_vbox.pack_start(est_box, False, False, 0)

        alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)

        self.add(alignment)
        self.set_default_size(500, 70)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()


def _load_pulse_bar(data):
    _info_label.set_text(_messages_thread.msg)
    _info_label.queue_draw()
    _window.progress_bar.pulse()
    _window.progress_bar.queue_draw()

def _launch_threads():
    global _messages_thread
    _messages_thread = ReadMessagesThread()
    _messages_thread.start()

def _shutdown():
    _window.destroy()


class ReadMessagesThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        self.msg = ""
        self.ticker = utilsgtk.GtkTicker(_load_pulse_bar, 250)
        self.ticker.start_ticker()

        os.mkfifo(FIFO_PATH) if not os.path.exists(FIFO_PATH) else None
        
        # Process B (Reader)
        with open(FIFO_PATH, 'r') as fifo:
            running = True
            while running == True:
                for line in fifo:
                    self.msg = line
                    if line == SHUTDOWN:
                        running = False
        
        os.remove(FIFO_PATH)

        self.ticker.destroy_ticker()

        GLib.idle_add(_shutdown)
