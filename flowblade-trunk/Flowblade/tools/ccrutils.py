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

"""
Module provides utility methods for moduless creating headless render procesesses.
Used mostly for container clips rendering, hence ContainerClipsRenderingUTILS.
"""
import os
import pickle
import sys

import appconsts
import atomicfile
import userfolders
import utils


CLIP_FRAMES_DIR = appconsts.CC_CLIP_FRAMES_DIR
RENDERED_FRAMES_DIR = appconsts.CC_RENDERED_FRAMES_DIR

COMPLETED_MSG_FILE = "completed"
STATUS_MSG_FILE = "status"
ABORT_MSG_FILE = "abort"
RENDER_DATA_FILE = "render_data"


_session_folder = None
_clip_frames_folder_internal = None
_rendered_frames_folder_internal = None

_render_data = None


# ----------------------------------------------------- interface with message files, used by main appp
# We are using message files to communicate with application.
def clear_flag_files(session_id):
    folder = _get_session_folder(session_id)
    
    completed_msg = folder + "/" + COMPLETED_MSG_FILE
    if os.path.exists(completed_msg):
        os.remove(completed_msg)

    status_msg_file = folder + "/" + STATUS_MSG_FILE
    if os.path.exists(status_msg_file):
        os.remove(status_msg_file)

    abort_msg_file = folder + "/" +  ABORT_MSG_FILE
    if os.path.exists(abort_msg_file):
        os.remove(abort_msg_file)

def set_render_data(session_id, video_render_data):
    folder = _get_session_folder(session_id)
    render_data_path = folder + "/" + RENDER_DATA_FILE
     
    if os.path.exists(render_data_path):
        os.remove(render_data_path)
    
    with atomicfile.AtomicFileWriter(render_data_path, "wb") as afw:
        outfile = afw.get_file()
        pickle.dump(video_render_data, outfile)
    
def session_render_complete(session_id):
    folder = _get_session_folder(session_id)
    completed_msg_path = folder + "/" + COMPLETED_MSG_FILE

    if os.path.exists(completed_msg_path):
        return True
    else:
        return False

def get_session_status(session_id):
    msg = get_session_status_message(session_id)
    if msg == None:
        return None
    
    step, frame, length, elapsed = msg.split(" ")
    return (step, frame, length, elapsed)

def get_session_status_message(session_id):
    try:
        status_msg_file = _get_session_folder(session_id) + "/" + STATUS_MSG_FILE
        with open(status_msg_file) as f:
            msg = f.read()
        return msg
    except:
        return None
        
def abort_render(session_id):
    folder = _get_session_folder(session_id)
    abort_msg_file = folder + "/" +  ABORT_MSG_FILE
    with atomicfile.AtomicFileWriter(abort_msg_file, "wb") as afw:
        outfile = afw.get_file()
        pickle.dump("##abort", outfile)
        
def _get_session_folder(session_id):
    return userfolders.get_data_dir() + appconsts.CONTAINER_CLIPS_DIR +  "/" + session_id
    

# ------------------------------------------------------ headless session folders and files, used by render processes
def init_session_folders(session_id):
    global _session_folder, _clip_frames_folder_internal, _rendered_frames_folder_internal
    _session_folder = _get_session_folder(session_id)
    _clip_frames_folder_internal = _session_folder + CLIP_FRAMES_DIR
    _rendered_frames_folder_internal = _session_folder + RENDERED_FRAMES_DIR

    # Init gmic session dirs, these might exist if clip has been rendered before
    if not os.path.exists(_session_folder):
        os.mkdir(_session_folder)
    if not os.path.exists(_clip_frames_folder_internal):
        os.mkdir(_clip_frames_folder_internal)
    if not os.path.exists(_rendered_frames_folder_internal):
        os.mkdir(_rendered_frames_folder_internal)

def delete_internal_folders(session_id):
    # This works only if clip frames and rendered frames folder are empty already.
    # This is used my motinheadless.py that uses container clips folders only to communicate render status
    # back and forth.
    _session_folder = _get_session_folder(session_id)
    _clip_frames_folder_internal = _session_folder + CLIP_FRAMES_DIR
    _rendered_frames_folder_internal = _session_folder + RENDERED_FRAMES_DIR
    
    if os.path.exists(_clip_frames_folder_internal):
        os.rmdir(_clip_frames_folder_internal)
    if os.path.exists(_rendered_frames_folder_internal):
        os.rmdir(_rendered_frames_folder_internal)
    if os.path.exists(_session_folder):
        files = os.listdir(_session_folder)
        for f in files:
            file_path = _session_folder + "/" + f
            os.remove(file_path)
        os.rmdir(_session_folder)

def maybe_init_external_session_folders():
    if _render_data == None:
        return

    if _render_data.save_internally == False:
        if not os.path.exists(clip_frames_folder()):
            os.mkdir(clip_frames_folder())
        if not os.path.exists(rendered_frames_folder()):
            os.mkdir(rendered_frames_folder())
                
def session_folder():
    return _session_folder

def clip_frames_folder():
    if _render_data.save_internally == True:
        return _clip_frames_folder_internal
    else:
        return _render_data.render_dir + CLIP_FRAMES_DIR
        
def rendered_frames_folder():
    if _render_data.save_internally == True:
        return _rendered_frames_folder_internal
    else:
        return _render_data.render_dir + RENDERED_FRAMES_DIR

def write_status_message(msg):
    try:
        status_msg_file = session_folder() + "/" + STATUS_MSG_FILE
        with atomicfile.AtomicFileWriter(status_msg_file, "w") as afw:
            script_file = afw.get_file()
            script_file.write(msg)
    except:
        pass # this failing because we can't get file access will show as progress hickup to user, we don't care

def write_completed_message():
    completed_msg_file = session_folder() + "/" + COMPLETED_MSG_FILE
    script_text = "##completed##" # let's put something in here
    with atomicfile.AtomicFileWriter(completed_msg_file, "w") as afw:
        script_file = afw.get_file()
        script_file.write(script_text)
            
def load_render_data():
    global _render_data
    try:
        render_data_path = _session_folder + "/" + RENDER_DATA_FILE
        _render_data = utils.unpickle(render_data_path)  # toolsencoding.ToolsRenderData object
    except:
        _render_data = None

def get_render_data():
    return _render_data

def delete_clip_frames():
    cf_folder = clip_frames_folder()
    frames = os.listdir(cf_folder)
    for f in frames:
        file_path = cf_folder + "/" + f
        os.remove(file_path)

def delete_rendered_frames():
    rf_folder = rendered_frames_folder()
    frames = os.listdir(rf_folder)
    for f in frames:
        file_path = rf_folder + "/" + f
        os.remove(file_path)

def abort_requested():
    abort_file = session_folder() + "/" + ABORT_MSG_FILE
    if os.path.exists(abort_file):
        return True
    else:
        return False

# ---- Debug helper
def prints_to_log_file(log_file):
    so = se = open(log_file, 'w', buffering=1)

    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())
