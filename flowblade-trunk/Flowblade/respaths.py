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
Module contains absolute paths to various resources.
"""

ROOT_PATH = None

BLACK_IMAGE_PATH = None
IMAGE_PATH = None
PROFILE_PATH = None
PREFS_PATH = None
WIPE_RESOURCES_PATH = None
FILTERS_XML_DOC = None
COMPOSITORS_XML_DOC = None
HELP_DOC = None
GPL_3_DOC = None
LOCALE_PATH = None
ROOT_PARENT = None

def set_paths(root_path):
    global ROOT_PATH, IMAGE_PATH, THUMBNAIL_PATH, PROFILE_PATH,\
    BLACK_IMAGE_PATH, FILTERS_XML_DOC, COMPOSITORS_XML_DOC, \
    WIPE_RESOURCES_PATH, PREFS_PATH, HELP_DOC, LOCALE_PATH, \
    GPL_3_DOC, ROOT_PARENT
    
    ROOT_PATH = root_path
    IMAGE_PATH = root_path + "/res/img/"
    WIPE_RESOURCES_PATH = root_path + "/res/filters/wipes/"
    PROFILE_PATH = root_path + "/res/profiles/"
    BLACK_IMAGE_PATH = root_path + "/res/img/black.jpg"
    FILTERS_XML_DOC = root_path + "/res/filters/filters.xml"
    COMPOSITORS_XML_DOC = root_path + "/res/filters/compositors.xml"
    PREFS_PATH = root_path + "/res/prefs/"
    HELP_DOC = root_path + "/res/help/help.xml"
    LOCALE_PATH = root_path + "/locale/"
    GPL_3_DOC = root_path + "/res/help/gpl3"
    ROOT_PARENT = ROOT_PATH.strip("Flowblade")
    print "ggfg"
    print ROOT_PARENT
    
