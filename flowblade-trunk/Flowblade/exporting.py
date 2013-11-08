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

import gtk
import xml.dom.minidom

import dialogs
from editorstate import PLAYER
from editorstate import PROJECT
from editorstate import current_sequence
import gui
import mltprofiles
import renderconsumer
import utils

mpeg_renderer = None
progress_update = None

"""
def DVD_AUTHOR_export():
    dialogs.export_dvd_author_dialog(_export_dvd_author_dialog_callback, 
                                     current_sequence(),
                                     gui.editor_window.window)

def _export_dvd_author_dialog_callback(dialog, response_id, data):
    if response_id != gtk.RESPONSE_YES:
        dialog.destroy()
        return

    markers_check, file_chooser, name_entry, render_check, dvd_type_combo, mpg_name_entry = data
    
    file_dir = file_chooser.get_filename()
    xml_file_path = file_dir + "/" + name_entry.get_text()
    mpg_name = mpg_name_entry.get_text()
    do_render = render_check.get_active()
    dvd_type_index = dvd_type_combo.get_active()
    render_file_path = file_dir + "/" + mpg_name

    dialog.destroy()
    
    if file_dir == None:
        print "file_dir None"
        return

    # Create and write XML file
    impl = xml.dom.minidom.getDOMImplementation()
    doc = impl.createDocument(None, "dvdauthor", None)
    
    top_element = doc.documentElement
    
    wmgm_element = doc.createElement("vmgm")
    top_element.appendChild(wmgm_element)
    
    titleset_element = doc.createElement("titleset")
    top_element.appendChild(titleset_element)
    
    titles_element = doc.createElement("titles")
    titleset_element.appendChild(titles_element)

    #video_element = doc.createElement("video")
    #video_element.setAttribute("format", "pal")
    #video_element.setAttribute("aspect", "4:3")
    #<video format="pal" aspect="4:3" widescreen="nopanscan" />pal,  ntsc,  4:3,  16:9
    #titles_element.appendChild(video_element)

    pgc_element = doc.createElement("pgc")
    titles_element.appendChild(pgc_element)

    vob_element = doc.createElement("vob")
    chapters="0,"
    for marker in current_sequence().markers:
        name, frame = marker
        tc_string = utils.get_tc_string(frame)
        chapters = chapters + tc_string + ","
    
    chapters_final = chapters.rstrip(",")

    vob_element.setAttribute("chapters", chapters_final)
    vob_element.setAttribute("file", mpg_name)
    pgc_element.appendChild(vob_element)

    try:
        f = open(xml_file_path, 'wb')
        doc.writexml(f, encoding='utf-8')
        f.close()
    except:
        print "writing DVDAutnor xml failed"
        return

    if not do_render:
        return
    
    # Render mpeg
    # This relies on that first four renderconsumer.non_user_encodings[] objects
    # having matching indexes to dvd_type_combo
    enc_opt = renderconsumer.non_user_encodings[dvd_type_index]
    if dvd_type_index == 0:
        profile = mltprofiles.get_profile("DV/DVD PAL")
    elif dvd_type_index == 1:
        profile = mltprofiles.get_profile("DV/DVD Widescreen PAL")
    elif dvd_type_index == 2:
        profile = mltprofiles.get_profile("DV/DVD NTSC")
    else:
        profile = mltprofiles.get_profile("DV/DVD Widescreen NTSC")
    
    consumer = renderconsumer.get_render_consumer_for_encoding(render_file_path, profile, enc_opt)
        
    # start and end frames
    start_frame = 0
    end_frame = current_sequence().get_length()

    # Launch render
    global mpeg_renderer, progress_update
    mpeg_renderer = PLAYER() # we're rendering from producer current sequence tracktor so we have to use PLAYER()
    callbacks = utils.EmptyClass()
    callbacks.set_render_progress_gui = set_render_progress_gui
    callbacks.save_render_start_time = save_render_start_time
    callbacks.exit_render_gui = exit_render_gui
    callbacks.maybe_open_rendered_file_in_bin = maybe_open_rendered_file_in_bin
    mpeg_renderer.set_render_callbacks(callbacks)
    mpeg_renderer.start_rendering(consumer)

    title = _("Rendering DVD Mpeg")
            
    progress_bar = gtk.ProgressBar()
    dialog = dialogs.clip_render_progress_dialog(_mpeg_render_stop, title, render_file_path, progress_bar, gui.editor_window.window)
    
    progress_update = renderconsumer.ProgressWindowThread(dialog, progress_bar, mpeg_renderer, _mpeg_render_stop)
    progress_update.start()

def _mpeg_render_stop(dialog, response_id):
    dialog.destroy()

    global mpeg_renderer, progress_update
    mpeg_renderer.running = False
    progress_update.running = False
    mpeg_renderer = None
    progress_update = None
"""
    
def MELT_XML_export():
    dialogs.export_xml_dialog(_export_melt_xml_dialog_callback, PROJECT().name)

def _export_melt_xml_dialog_callback(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        filenames = dialog.get_filenames()
        save_path = filenames[0]
        
        callbacks = utils.EmptyClass()
        callbacks.set_render_progress_gui = set_render_progress_gui
        callbacks.save_render_start_time = save_render_start_time
        callbacks.exit_render_gui = exit_render_gui
        callbacks.maybe_open_rendered_file_in_bin = maybe_open_rendered_file_in_bin
        PLAYER().set_render_callbacks(callbacks)

        PLAYER().start_xml_rendering(save_path)
        dialog.destroy()
    else:
        dialog.destroy()


# ----------------------- mlt player render callbacks, we need to set these no-op when not doing standard rendering
# ----------------------- we're using different progress update mechanisms here
def set_render_progress_gui(fraction):
    pass
    
def save_render_start_time():
    pass

def exit_render_gui():
    pass

def maybe_open_rendered_file_in_bin():
    pass
