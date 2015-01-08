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
Module checks environment for available codecs and formats.
"""
import gobject
import mlt

import dialogutils
import editorstate
import gui

acodecs = None
vcodecs = None
formats = None
services = None
transitions = None

environment_detection_success = False

def check_available_features(repo):
    try:
        print "Detecting environment..."
        global acodecs        
        global vcodecs    
        global formats
        global services
        global transitions
        global environment_detection_success
        acodecs = []
        vcodecs = []
        formats = []
        services = {}
        transitions = {}

        # video codecs
        cv = mlt.Consumer(mlt.Profile(), "avformat")
        cv.set('vcodec', 'list')
        cv.start()
        codecs = mlt.Properties(cv.get_data('vcodec'))
        for i in range(0, codecs.count()):
            vcodecs.append(codecs.get(i))

        # audio codecs
        ca = mlt.Consumer(mlt.Profile(), "avformat")
        ca.set('acodec', 'list')
        ca.start()
        codecs = mlt.Properties(ca.get_data('acodec'))
        for i in range(0, codecs.count()):
            acodecs.append(codecs.get(i))
            
        # formats
        cf = mlt.Consumer(mlt.Profile(), "avformat")
        cf.set('f', 'list')
        cf.start()
        codecs = mlt.Properties(cf.get_data('f'))
        for i in range(0, codecs.count()):
                formats.append(codecs.get(i))

        # filters
        envservices = mlt.Repository.filters(repo)
        for i in range(mlt.Properties.count(envservices)):
            services[mlt.Properties.get_name(envservices, i)] = True

        # transitions
        envtransitions = mlt.Repository.transitions(repo)
        for i in range(mlt.Properties.count(envtransitions)):
            transitions[mlt.Properties.get_name(envtransitions, i)] = True
            
        print "MLT detection succeeded, " + str(len(formats)) + " formats, "  \
        + str(len(vcodecs)) + " video codecs and " + str(len(acodecs)) + " audio codecs found."
        print str(len(services)) + " MLT services found."

        environment_detection_success = True

    except:
        print "Environment detection failed, environment unknown."
        gobject.timeout_add(2000, _show_failed_environment_info)

def render_profile_supported(frmt, vcodec, acodec):
    if environment_detection_success == False:
        return (True, "")

    if acodec in acodecs or acodec == None: # some encoding options do not specify audio codecs
        if vcodec in vcodecs or vcodec == None: # some encoding options do not specify video codecs
            if frmt in formats or frmt == None: # some encoding options do not specify formats
                return (True, "")
            else:
                err_msg = "format " + frmt
        else:
            err_msg = "video codec " + vcodec
    else:
        err_msg = "audio codec " + acodec

    return (False, err_msg)

def _show_failed_environment_info():
    primary_txt = "Environment detection failed!"
    secondary_txt = "You will probably be presented with filters, transitions\nand rendering options that are not available on your system." + \
    "\n---\nYou may experience sudden crashes when adding filters or\nattempting rendering." + \
    "\n---\nYour MLT Version is: "+ editorstate.mlt_version + "\n" + \
    "Only report this as a bug if the MLT version above is >= 0.7.6."
    
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
    return False

    
    
