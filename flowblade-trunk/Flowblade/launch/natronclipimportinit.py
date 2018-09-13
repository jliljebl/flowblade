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
NOTE: THIS SCRIPT IS RUN BY NATRON WHEN LAUNCHING IT AND HAS NO ACCES TO
OTHER PYTHON MODULES IN FLOWBLADE.
"""
import os

def createInstance(app,group):
    # Get export data
    natron_dir = get_hidden_user_dir_path() + "natron"
    exportfile = get_latest_clip_export_file(natron_dir)
    clip_path, mark_in, mark_out = get_export_data(exportfile)

    # Create Natron graph
    readerNode = app.createReader(clip_path)
    readerNode.getParam("firstFrame").set(int(mark_in))
    readerNode.getParam("lastFrame").set(int(mark_out) + 1)
    readerNode.getParam("startingTime").set(0)
    
    #viewerNode = app.createNode("fr.inria.built-in.Viewer")
    #viewerNode.connectInput(0, readerNode)

    readerNode.setPosition(300.0, 100.0)
    #viewerNode.setPosition(315.0, 300.0)

    app.getProjectParam("frameRange").set(1, int(mark_out) - int(mark_in) + 1)

# ---------------------------------------------------- helper funcs
def get_hidden_user_dir_path():
    return os.getenv("HOME") + "/.flowblade/"

def get_latest_clip_export_file(dirpath):
    from os import listdir
    from os.path import isfile, join
    file_paths = [f for f in listdir(dirpath) if isfile(join(dirpath, f))]
    
    # Get files staring with "clipexport_"
    clip_export_files = []
    for fpath in file_paths:
        if fpath.startswith("clipexport_"):
            clip_export_files.append(dirpath + "/" + fpath)
            
    newest = max(clip_export_files, key=os.path.getctime)
    return newest

def get_export_data(export_file):
    data_file = open(export_file)
    data_text = data_file.read()
    tokens = data_text.split(" ")
    return (tokens[0], tokens[1], tokens[2])
