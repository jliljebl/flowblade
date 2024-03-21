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

NOTE: 'vault' in code is presented to user as 'Data Store'.
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
DEFAULT_VAULT = 0

# Project data folders
THUMBNAILS_FOLDER = "thumbnails/"
RENDERS_FOLDER = "rendered_clips/"
CONTAINER_CLIPS_FOLDER = "container_clips/"
CONTAINER_CLIPS_UNRENDERED = "container_clips/unrendered/"
AUDIO_LEVELS_FOLDER = "audio_levels/"
PROXIES_FOLDER = "proxies/"
INGEST_FOLDER = "ingest/"

# Enumerations for conditions that make folder an non-valid data vault.
VAULT_IS_VALID = 0
VAULT_HAS_NON_FOLDER_FILES = 1
VAULT_HAS_BAD_FOLDERS = 2

# Enumerations for conditions that make folder an non-valid data vault.
PROJECT_FOLDER_IS_VALID = 0
PROJECT_FOLDER_IS_EMPTY = 1
PROJECT_FOLDER_HAS_EXTRA_FILES_OR_FOLDERS = 2
PROJECT_FOLDER_HAS_MISSING_FOLDERS = 3
PROJECT_FOLDER_HAS_MISSING_SAVE_FILE_DATA = 4 

# Ssve files data file
SAVE_FILES_FILE = "savefiles"

# Project label file.
LABEL_FILE = "label"

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
        if _vaults.active_vault > len(_vaults.user_vaults_data):
            # We did hit this once during development, so this is here to save guard against
            # any bugs in release.
            _vaults.active_vault = DEFAULT_VAULT
            _vaults.save()

        #print("active_vault", _vaults.active_vault)
        #print(_vaults.user_vaults_data)


# --------------------------------------------------------- vault
def get_active_vault_folder():
    return _vaults.get_active_vault_folder()

def get_vault_folder_for_index(index):
    return _vaults.get_vault_folder_for_index(index)
    
def set_active_vault_index(index):
    _vaults.set_active_vault_index(index)

def get_active_vault_index():
    return _vaults.get_active_vault_index()
    
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
    # so they sometimes use '_project_data_folder' which set is in main() to be available
    # when neeeded.

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
    
def get_ingest_folder():
    return get_project_data_folder() + INGEST_FOLDER
    
# ----------------------------------------------------- functional methods
def create_project_data_folders():
    os.mkdir(get_project_data_folder())
    os.mkdir(get_thumbnails_folder())
    os.mkdir(get_render_folder())
    os.mkdir(get_containers_folder())
    os.mkdir(get_container_clips_unrendered_folder())
    os.mkdir(get_audio_levels_folder())
    os.mkdir(get_proxies_folder())
    os.mkdir(get_ingest_folder())
    
    savefiles_list = []
    savefiles_path = get_project_data_folder() + SAVE_FILES_FILE
    with atomicfile.AtomicFileWriter(savefiles_path, "wb") as afw:
        write_file = afw.get_file()
        pickle.dump(savefiles_list, write_file)

    project_label = ""
    label_file_path = get_project_data_folder() + LABEL_FILE
    with atomicfile.AtomicFileWriter(label_file_path, "wb") as afw:
        write_file = afw.get_file()
        pickle.dump(project_label, write_file)
        
def project_saved(project_path):
    try:
        savefiles_path = get_project_data_folder() + SAVE_FILES_FILE
    except:
        print("Old data layout project saved at:", project_path)
        return
        
    savefiles_list = utils.unpickle(savefiles_path)
    savefiles_list.append((project_path, datetime.datetime.now()))

    with atomicfile.AtomicFileWriter(savefiles_path, "wb") as afw:
        write_file = afw.get_file()
        pickle.dump(savefiles_list, write_file)

def delete_unsaved_data_folders():
    vault_handle = VaultDataHandle(get_active_vault_folder())
    vault_handle.create_data_folders_handles()

    non_saved = []
    for folder_handle in vault_handle.data_folders:
        path, s_times, s_data = folder_handle.get_save_info()
        if path == None:
            non_saved.append(folder_handle)
    
    for folder_handle in non_saved:
        folder_handle.destroy_data()


# ---------------------------------------------------- handle classes
class Vaults:
    def __init__(self):
        # 'self.active_vault' indexes work as follows:
        # 0 = DEFAULT_VAULT, the "Default XDG Data Store" in $XDG_DATA_HOME folder.
        # 1 - n = user defined aAta Stores self.user_vaults_data in indexes 0 - (n-1)
        #
        # The reason this scheme was selected was that "Default XDG Data Store"
        # cannot be deleted, named, dropped or connected, but its location can change
        # if user changes $XDG_DATA_HOME value and then a new "Default XDG Data Store"
        # gets created.
        #
        # User defined data stores are named and freely placed at creation time,
        # and can be dropped or connected at will later, but their locations are immutable
        # once created.
        #
        # The method we chose to enforce this difference was to special case index
        # 0, the DEFAULT_VAULT, and keep user defined data stores in separate 
        # data structure.
        self.active_vault = DEFAULT_VAULT
        self.user_vaults_data = []
        self.last_xdg_data_dir = _xdg_data_dir

    def add_user_vault(self, name, vault_path):
        new_vault_data = {"name":name, "vault_path":vault_path, "creation_time":datetime.datetime.now()}
        self.user_vaults_data.append(new_vault_data)

    def get_user_vaults_data(self):
        return copy.deepcopy(self.user_vaults_data)

    def get_active_vault_folder(self):
        return self.get_vault_folder_for_index(self.active_vault)

    def get_vault_folder_for_index(self, vault_index): 
        if vault_index == DEFAULT_VAULT:
            return get_default_vault_folder()
        else:
            vault_properties = self.user_vaults_data[vault_index - 1] # -1 because first vault is not user vault and is not in user_vaults_data list
            return vault_properties["vault_path"]

    def get_index_for_vault_folder(self, vault_folder): 
        if vault_folder == get_default_vault_folder():
            return 0
        else:
            for i in range(0, len(self.user_vaults_data)):
                user_vault = self.user_vaults_data[i]
                if vault_folder == user_vault["vault_path"]:
                    return i + 1
        
        return NONE
        
    def set_active_vault_index(self, index):
        self.active_vault = index

    def set_active_vault_for_path(self, active_vault_path):
        if active_vault_path == get_default_vault_folder():
            self.active_vault = DEFAULT_VAULT
            return

        for i in range(0, len(self.user_vaults_data)):
            user_vault = self.user_vaults_data[i]
            if active_vault_path == user_vault["vault_path"]:
                self.active_vault = i
                return

        self.active_vault = DEFAULT_VAULT
            
    def get_active_vault_index(self):
        return self.active_vault

    def get_user_vault_folder_name(self, vault_path):
        for vault_data in self.user_vaults_data:
            if vault_data["vault_path"] == vault_path:
                return vault_data["name"]
        
        return None 

    def get_vault_path_for_name(self, vault_name):
        for vault_data in self.user_vaults_data:
            if vault_data["name"] == vault_name:
                return vault_data["vault_path"]
        
        return None

    def save(self):
        vaults_info_file_path = get_vaults_info_path()
        with atomicfile.AtomicFileWriter(vaults_info_file_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(self, write_file)

    def drop_user_vault(self, drop_index):
        self.user_vaults_data.pop(drop_index) 


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

    def folder_is_valid_data_store(self):
        self.create_data_folders_handles()
        if len(self.data_folders) != len(listdir(self.vault_path)):
            # Valid data store only has folders in it.
            return (VAULT_HAS_NON_FOLDER_FILES, (len(self.data_folders), listdir(self.vault_path)))
        
        bad_folders = []
        for project_folder_handle in self.data_folders:
            if project_folder_handle.is_valid_project_folder() == False:
                bad_folders.append(project_folder_handle)
        
        if len(bad_folders) > 0:
            return(VAULT_HAS_BAD_FOLDERS, bad_folders)

        return (VAULT_IS_VALID, None)

    
class ProjectDataFolderHandle:
    def __init__(self, path):
        self.data_folder_path = path
        path = path.rstrip("/")
        self.data_id = path.split("/")[-1]
        self.folders_data = {}
        self.create_folder_data_handles()

    def get_save_info(self):
        savefiles = utils.unpickle(join(self.data_folder_path, SAVE_FILES_FILE))
        if len(savefiles) == 0:
            return [None, 0, 0]

        savefile_path, date_time = savefiles[-1]
        
        return [savefile_path, len(savefiles), date_time]

    def get_folder_path(self, folder):
        return self.data_folder_path + "/" + folder
        
    def create_folder_data_handles(self):
        self.folders_data[THUMBNAILS_FOLDER] = DiskFolderHandle(self.get_folder_path(THUMBNAILS_FOLDER))
        self.folders_data[RENDERS_FOLDER] = DiskFolderHandle(self.get_folder_path(RENDERS_FOLDER))
        self.folders_data[CONTAINER_CLIPS_FOLDER] = DiskFolderHandle(self.get_folder_path(CONTAINER_CLIPS_FOLDER))
        self.folders_data[CONTAINER_CLIPS_UNRENDERED] = DiskFolderHandle(self.get_folder_path(CONTAINER_CLIPS_UNRENDERED))
        self.folders_data[AUDIO_LEVELS_FOLDER] = DiskFolderHandle(self.get_folder_path(AUDIO_LEVELS_FOLDER))
        self.folders_data[PROXIES_FOLDER] = DiskFolderHandle(self.get_folder_path(PROXIES_FOLDER))
        self.folders_data[INGEST_FOLDER] = DiskFolderHandle(self.get_folder_path(PROXIES_FOLDER))
        
    def data_folders_info(self):
        info = {}
        info[THUMBNAILS_FOLDER] = self.folders_data[THUMBNAILS_FOLDER].get_folder_size_str()
        info[RENDERS_FOLDER] = self.folders_data[RENDERS_FOLDER].get_folder_size_str()
        info[CONTAINER_CLIPS_FOLDER] = self.folders_data[CONTAINER_CLIPS_FOLDER].get_folder_size_str()
        info[AUDIO_LEVELS_FOLDER] = self.folders_data[AUDIO_LEVELS_FOLDER].get_folder_size_str()
        info[PROXIES_FOLDER] = self.folders_data[PROXIES_FOLDER].get_folder_size_str()
        info[INGEST_FOLDER] = self.folders_data[INGEST_FOLDER].get_folder_size_str()
        
        return info
        
    def get_total_data_size(self):
        total = 0
        total += self.folders_data[PROXIES_FOLDER].get_folder_size()
        total += self.folders_data[AUDIO_LEVELS_FOLDER].get_folder_size()
        total += self.folders_data[CONTAINER_CLIPS_FOLDER].get_folder_size()
        total += self.folders_data[RENDERS_FOLDER].get_folder_size()
        total += self.folders_data[THUMBNAILS_FOLDER].get_folder_size()
        total += self.folders_data[INGEST_FOLDER].get_folder_size()
        
        return  self.folders_data[THUMBNAILS_FOLDER].get_size_str(total) 

    def is_valid_project_folder(self):
        if self.get_folder_valid_state() != PROJECT_FOLDER_IS_VALID:
            return False
        
        return True

    def get_folder_valid_state(self):
        if len(listdir(self.data_folder_path)) == 0:
            return PROJECT_FOLDER_IS_EMPTY

        if isfile(join(self.data_folder_path, SAVE_FILES_FILE)) == False:
            return PROJECT_FOLDER_HAS_MISSING_SAVE_FILE_DATA

        for folder_handle in self.folders_data.values():
            if folder_handle.folder_exists() == False:
                return PROJECT_FOLDER_HAS_MISSING_FOLDERS

        if len(listdir(self.data_folder_path)) > 8:
            return PROJECT_FOLDER_HAS_EXTRA_FILES_OR_FOLDERS

        return PROJECT_FOLDER_IS_VALID

    def destroy_data(self):
        # Only agree to destroy valid or empty folders.
        folder_state = self.is_valid_project_folder()
        if folder_state == PROJECT_FOLDER_HAS_MISSING_FOLDERS or \
           folder_state == PROJECT_FOLDER_HAS_MISSING_SAVE_FILE_DATA or \
           folder_state == PROJECT_FOLDER_HAS_EXTRA_FILES_OR_FOLDERS:
           print("Trying to destroy non-project data folder!!!!", self.data_folder_path)
           return

        #print("deleting", self.data_folder_path)
        self.destroy_recursively(self.data_folder_path)
        #print("removing data dir", self.data_folder_path)
        os.rmdir(self.data_folder_path)
                
    def destroy_recursively(self, folder):
        files = os.listdir(folder)
        for f in files:
            file_path = folder + "/" + f
            if os.path.isdir(file_path) == True:
                self.destroy_recursively(file_path)
                #print("removing dir", file_path)
                os.rmdir(file_path)
            else:
                #print("removing file", file_path)
                os.remove(file_path)


class DiskFolderHandle:
    
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def get_folder_files(self):
        return [f for f in listdir(self.folder_path) if isfile(join(self.folder_path, f))]
        
    def get_folder_contents(self):
        return os.listdir(self.folder_path)
        
    def get_folder_size(self):
        return self.get_folder_sizes_recursively(self.folder_path)

    def folder_exists(self):
        return isdir(self.folder_path)
    
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
