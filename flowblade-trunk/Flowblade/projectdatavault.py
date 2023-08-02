"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2023 Janne Liljeblad.

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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

"""
This module handles creating data folders for individual projects data files and providing 
access to them for all later saved versions of the initial project. 
"""

from gi.repository import GLib

import copy
from os import listdir
from os.path import isfile, join, isdir

import atomicfile
import datetime
import os
import pickle
import utils

from editorstate import PROJECT

# Project data folder path is accessed with PROJECT() in main application, but 
# render processses receive it as parameter and set it here in init. 
_project_data_folder = None

# User folder locations
_xdg_config_dir = None
_xdg_data_dir = None
_xdg_cache_dir = None
    
# The one projects data folder quaranteed to always exist and the default one
# until user creates a new one and sets it active. 
DEFAULT_PROJECTS_DATA_FOLDER = "projectsdata"
DEFAULT_VAULT = -1

# Project data folders
THUMBNAILS_FOLDER = "thumbnails/"
RENDERS_FOLDER = "rendered_clips/"
CONTAINER_CLIPS_FOLDER = "container_clips/"
CONTAINER_CLIPS_UNRENDERED = "container_clips/unrendered/"
AUDIO_LEVELS_FOLDER = "audio_levels/"
PROXIES_FOLDER = "proxies/"

# Ssve files data file
SAVE_FILES_FILE = "savefiles"

# Vaults info data file.
VAULTS_INFO = "vaults"

# ------------------------------------------------------------------------ init
def init(_current_project_data_folder=None):
    # This data is duplicated with userfolders.py but thats really not an issue.
    global _xdg_config_dir, _xdg_data_dir, _xdg_cache_dir, _project_data_folder

    # XDG folders
    _xdg_config_dir = os.path.join(GLib.get_user_config_dir(), "flowblade")
    _xdg_data_dir = os.path.join(GLib.get_user_data_dir(), "flowblade")
    _xdg_cache_dir = os.path.join(GLib.get_user_cache_dir(), "flowblade")

    # Render processes don't have access to project data folder path via PROJECT(),
    # so they sometimes use this which set in main() to be available
    # using get_project_data_folder() as needed.
    _project_data_folder = _current_project_data_folder

    # This should only happen once on first use of application.
    if not os.path.exists(get_default_vault_folder()):
        os.mkdir(get_default_vault_folder())
    
    # Create or load vaults data.
    global _vaults
    if not os.path.exists(get_vaults_info_path()):
        # This should only happen once on first use of application.
        _vaults = Vaults()
        _vaults.save()
    else:
        _vaults = utils.unpickle(get_vaults_info_path())
        print(_vaults.user_vaults_data)
# --------------------------------------------------------- vault
def get_active_vault_folder():
    return _vaults.get_active_vault()

def get_vaults_object():
    return _vaults

def get_default_vault_folder():
    return _xdg_data_dir + "/" + DEFAULT_PROJECTS_DATA_FOLDER

def vault_data_exists_for_project():
    if get_project_data_folder() == None:
        return False
    else:
        return True

def get_vaults_info_path():
    return _xdg_config_dir + "/" + VAULTS_INFO

# --------------------------------------------------------- data folders paths
def get_project_data_folder():
    # Render processes don't have access to project data folder path via 'PROJECT()',
    # so they sometimes use '_project_data_folder' which set in main() to be available
    # when neeeded.
    path = PROJECT().vault_folder + "/" + PROJECT().project_data_id + "/"
    try:
        path = PROJECT().vault_folder + "/" + PROJECT().project_data_id + "/"
    except:
        path = _project_data_folder

    return path

def get_thumbnails_folder():
    return get_project_data_folder() + THUMBNAILS_FOLDER

def get_render_folder():
    return get_project_data_folder() + RENDERS_FOLDER

def get_containers_folder():
    return get_project_data_folder() + CONTAINER_CLIPS_FOLDER

def get_container_clips_unrendered_folder():
    return get_project_data_folder() + CONTAINER_CLIPS_UNRENDERED
    
def get_audio_levels_folder():
    return get_project_data_folder() + AUDIO_LEVELS_FOLDER

def get_proxies_folder():
    if PROJECT().vault_folder == None:
        return None
    return get_project_data_folder() + PROXIES_FOLDER
    
# ----------------------------------------------------- functional methods
def create_project_data_folders():
    os.mkdir(get_project_data_folder())
    os.mkdir(get_thumbnails_folder())
    os.mkdir(get_render_folder())
    os.mkdir(get_containers_folder())
    os.mkdir(get_container_clips_unrendered_folder())
    os.mkdir(get_audio_levels_folder())
    os.mkdir(get_proxies_folder())

    savefiles_list = []
    savefiles_path = get_project_data_folder() + SAVE_FILES_FILE
    with atomicfile.AtomicFileWriter(savefiles_path, "wb") as afw:
        write_file = afw.get_file()
        pickle.dump(savefiles_list, write_file)

def project_saved(project_path):
    savefiles_path = get_project_data_folder() + SAVE_FILES_FILE
    savefiles_list = utils.unpickle(savefiles_path)
    savefiles_list.append((project_path, datetime.datetime.now()))

    with atomicfile.AtomicFileWriter(savefiles_path, "wb") as afw:
        write_file = afw.get_file()
        pickle.dump(savefiles_list, write_file)


# ---------------------------------------------------- handle classes
class Vaults:
    def __init__(self):
        self.active_vault = DEFAULT_VAULT
        self.user_vaults_data = []
    
    def add_user_vault(self, name, vault_path):
        new_vault_data = {"name":name, "vault_path":vault_path, "creation_time":datetime.datetime.now()}
        self.user_vaults_data.append(new_vault_data)

    def get_user_vaults_data(self):
        return copy.deepcopy(self.user_vaults_data)

    def get_active_vault(self):
        if self.active_vault == DEFAULT_VAULT:
            return get_default_vault_folder()
        else:
            name, path, ct = self.user_vaults_data[self.active_vault]
            return path
    
    def save(self):
        vaults_info_file_path = get_vaults_info_path()
        with atomicfile.AtomicFileWriter(vaults_info_file_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(self, write_file)



class VaultDataHandle:
    def __init__(self, path):
        self.vault_path = path
        self.data_folders = []

    def create_data_folders_handles(self):
        self.data_folders = []
        folders = [f for f in listdir(self.vault_path) if isdir(join(self.vault_path, f))]
        
        for folder in folders:
            path = self.vault_path + folder
            
            self.data_folders.append(ProjectDataFolderHandle(join(self.vault_path, folder)))


class ProjectDataFolderHandle:
    def __init__(self, path):
        self.data_folder_path = path
        self.folders_data = {}
        self.create_folder_data_handles()

    def get_save_info(self):
        savefiles = utils.unpickle(join(self.data_folder_path, SAVE_FILES_FILE))
        if len(savefiles) == 0:
            return [None, 0]

        savefile_path, date_time = savefiles[-1]
        
        return [savefile_path, len(savefiles)]

    def get_folder_path(self, folder):
        return self.data_folder_path + "/" + folder
        
    def create_folder_data_handles(self):
        self.folders_data[THUMBNAILS_FOLDER] = DiskFolderHandle(self.get_folder_path(THUMBNAILS_FOLDER))
        self.folders_data[RENDERS_FOLDER] = DiskFolderHandle(self.get_folder_path(RENDERS_FOLDER))
        self.folders_data[CONTAINER_CLIPS_FOLDER] = DiskFolderHandle(self.get_folder_path(CONTAINER_CLIPS_FOLDER))
        self.folders_data[CONTAINER_CLIPS_UNRENDERED] = DiskFolderHandle(self.get_folder_path(CONTAINER_CLIPS_UNRENDERED))
        self.folders_data[AUDIO_LEVELS_FOLDER] = DiskFolderHandle(self.get_folder_path(AUDIO_LEVELS_FOLDER))
        self.folders_data[PROXIES_FOLDER] = DiskFolderHandle(self.get_folder_path(PROXIES_FOLDER))

    def data_folders_info(self):
        info = {}
        info[THUMBNAILS_FOLDER] = self.folders_data[THUMBNAILS_FOLDER].get_folder_size_str()
        info[RENDERS_FOLDER] = self.folders_data[RENDERS_FOLDER].get_folder_size_str()
        info[CONTAINER_CLIPS_FOLDER] = self.folders_data[CONTAINER_CLIPS_FOLDER].get_folder_size_str()
        info[AUDIO_LEVELS_FOLDER] = self.folders_data[AUDIO_LEVELS_FOLDER].get_folder_size_str()
        info[PROXIES_FOLDER] = self.folders_data[PROXIES_FOLDER].get_folder_size_str()

        return info

class DiskFolderHandle:
    
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def get_folder_files(self):
        return [f for f in listdir(self.folder_path) if isfile(join(self.folder_path, f))]
        
    def get_folder_contents(self):
        return os.listdir(self.folder_path)
        
    def get_folder_size(self):
        return self.get_folder_sizes_recursively(self.folder_path)
    
    def get_folder_sizes_recursively(self, folder):
        files = os.listdir(folder)
        size = 0
        for f in files:
            if os.path.isdir(folder + "/" + f):
                size += self.get_folder_sizes_recursively(folder + "/" + f)
            else:
                size += os.path.getsize(folder +"/" + f)
        return size

    def get_folder_size_str(self):
        size = self.get_folder_size()
        self.used_disk = size
        return self.get_size_str(size)

    def get_size_str(self, size):
        if size > 1000000:
            return str(int((size + 500000) / 1000000)) + _(" MB")
        elif size > 1000:
            return str(int((size + 500) / 1000)) + _(" kB")
        else:
            return str(int(size)) + " B"

    def destroy_data(self, folder):
        print("deleting", folder)
        self.destroy_recursively(folder)

    def destroy_recursively(self, folder):
        files = os.listdir(folder)
        for f in files:
            file_path = folder + "/" + f
            if os.path.isdir(file_path) == True:
                if self.recursive == True:
                    self.destroy_recursively(file_path)
                    os.rmdir(file_path)
            else:
                os.remove(file_path)
