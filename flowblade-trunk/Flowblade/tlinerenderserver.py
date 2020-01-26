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

from gi.repository import GLib
    
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import locale
import mlt
import subprocess
import sys

import editorstate
import mltenv
import mlttransitions
import mltfilters
import mltprofiles
import editorpersistance
import processutils
import renderconsumer
import respaths
import translations
import userfolders

_dbus_service = None


# --------------------------------------------------------------- lanch and shutdown
def launch_render_server():
    bus = dbus.SessionBus()
    if bus.name_has_owner('flowblade.movie.editor.tlinerenderserver'):
        print("flowblade.movie.editor.tlinerenderserver dbus service exists, timeline background rendering server running")
        return False
    else:
        FLOG = open(userfolders.get_cache_dir() + "log_tline_render", 'w')
        subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladetlinerender"], stdin=FLOG, stdout=FLOG, stderr=FLOG)
        return True

def shutdown_render_server():
    bus = dbus.SessionBus()
    if bus.name_has_owner('flowblade.movie.editor.tlinerenderserver'):
        obj = bus.get_object('flowblade.movie.editor.tlinerenderserver', '/flowblade/movie/editor/tlinerenderserver')
        iface = dbus.Interface(obj, 'flowblade.movie.editor.tlinerenderserver')
        iface.shutdown_render_server()
        print("Timeline background render service shutdown requested.")

    else:
        print("Timeline background render service not on DBus at shutdown")

# ---------------------------------------------------------------- server

def main(root_path, force_launch=False):
    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"

    # Get XDG paths etc.
    userfolders.init()
    
    # Set paths.
    respaths.set_paths(root_path)

    # Load editor prefs and list of recent projects
    editorpersistance.load()
    
    # Init translations module with translations data
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()
       
    editorpersistance.load()

    repo = mlt.Factory().init()
    processutils.prepare_mlt_repo(repo)
    
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

    # Launch server
    print("tline render service running")
    DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()
    print("tline render service running")
    global _dbus_service
    print("tline render service running")
    _dbus_service = TLineRenderDBUSService(loop)
    print("tline render service running")
    loop.run()



class TLineRenderDBUSService(dbus.service.Object):
    def __init__(self, loop):
        bus_name = dbus.service.BusName('flowblade.movie.editor.tlinerenderserver', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, '/flowblade/movie/editor/tlinerenderserver')
        self.main_loop = loop

        
    @dbus.service.method('flowblade.movie.editor.tlinerenderserver')
    def render_item_added(self):
        if queue_runner_thread == None:
            batch_window.reload_queue()
        
        return "OK"

    @dbus.service.method('flowblade.movie.editor.tlinerenderserver')
    def shutdown_render_server(self):
        self.remove_from_connection()
        self.main_loop.quit()

