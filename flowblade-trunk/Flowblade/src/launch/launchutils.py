

import os
import sys


def get_modules_path():
    return os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))

def set_app_runtime_type(modules_path): 
    
    import editorstate
    root_dir = modules_path.split("/")[1]
    
     # Used to decide which translations from file system are used.
    if root_dir == "home":
        editorstate.app_running_from = editorstate.RUNNING_FROM_DEV_VERSION
    elif root_dir == "app":
        editorstate.app_running_from = editorstate.RUNNING_FROM_FLATPAK
    else:
        editorstate.app_running_from = editorstate.RUNNING_FROM_INSTALLATION

def get_arg_value(key_str):
    for arg in sys.argv:
        parts = arg.split(":")
        if len(parts) > 1:
            if parts[0] == key_str:
                return parts[1]

    return None