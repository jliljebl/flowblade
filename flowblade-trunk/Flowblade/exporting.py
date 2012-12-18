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

def DVD_AUTHOR_export(seq):
    impl = xml.dom.minidom.getDOMImplementation()
    doc = impl.createDocument(None, "dvdauthor", None)
    
    top_element = doc.documentElement
    
    wmgm_element = doc.createElement("wmgm")
    top_element.appendChild(wmgm_element)
    
    titleset_element = doc.createElement("titleset")
    top_element.appendChild(titleset_element)
    
    titles_element = doc.createElement("titles")
    titleset_element.appendChild(titles_element)

    pgc_element = doc.createElement("pgc")
    titles_element.appendChild(pgc_element)

    vob_element = doc.createElement("vob")
    vob_element.setAttribute("file", "video1.mpg")
    pgc_element.appendChild(vob_element)
    
    #f = open('/home/janne/dvdauthor.xml', 'wb')
    #doc.writexml(f, encoding='utf-8')
    #f.close()

def MELT_XML_export():
    dialogs.export_xml_dialog(_export_melt_xml_dialog_callback, PROJECT().name)

def _export_melt_xml_dialog_callback(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        filenames = dialog.get_filenames()
        save_path = filenames[0]
        PLAYER().start_xml_rendering(save_path)
        dialog.destroy()
    else:
        dialog.destroy()
