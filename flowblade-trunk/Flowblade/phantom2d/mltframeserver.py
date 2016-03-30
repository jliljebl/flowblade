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

import locale
import md5
import mlt
import os
import socket
import sys
import time
import thread 

import appconsts
import editorpersistance
import mltenv
import mltprofiles
import respaths
import renderconsumer
import utils


_session_id = None
_frame_sources = {}

# Answer strings
OK = "OK\n"
ERROR = "ERROR:"
NEW_LINE = "\n"
UNKNOWN = "UNKNOWN\n"

# Commands
SHUTDOWN = "SHUTDOWN"
LOAD = "LOAD"
RENDER_FRAME = "RENDER_FRAME"
RENDER_RANGE = "RENDER_RANGE"
DROP = "DROP"

# File consts
FRAME_NAME = "frame"

def main(root_path):
    respaths.set_paths(root_path)
    
    # Get session id from args
    try:
        global _session_id
        _session_id = sys.argv[1]
        print  "mltframeserver session id:", _session_id
    except:
        print "session id was not provided in args, exiting..."
        sys.exit()

    # Init necessary resources and MLT
    editorpersistance.load()
    
    repo = mlt.Factory().init()

    # Set numeric locale to use "." as radix, MLT initilizes this to OS locale and this causes bugs 
    locale.setlocale(locale.LC_NUMERIC, 'C')

    # Create list of available mlt profiles
    mltprofiles.load_profile_list()

    # Create a socket to listn to
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(("",0))
    serversocket.listen(1)
    port = serversocket.getsockname()[1]
    print "mltframeserver listening to port:", port

    # Write file with port number to indicate that server is ready accept connection
    socket_file_path = get_port_file()
    socket_port_file = open(socket_file_path, 'w')
    socket_port_file.write(str(port))
    socket_port_file.close()

    # Accept connection to listen to, this will on listen to on client
    (client, addr) = serversocket.accept()

    print "Accepted connection from address:", addr

    # Listen to commands in an endless loop
    try:
        running = True

        while running:

            # Get command
            command = client.recv(1024)
            command = command.rstrip(NEW_LINE)
            tokens = command.split(" ")
            
            print "command:" + command
            
            # Execute command
            if command == None:
                running = False
            else:
                if command.startswith(SHUTDOWN):
                    running = False
                    answer = shutdown()
                elif command.startswith(LOAD):
                    answer = load(tokens)
                elif command.startswith(RENDER_FRAME):
                    answer = render_frame(tokens)
                else:
                    answer = UNKNOWN
                    
            client.send(answer)
    except Exception as e:
        print e

    print "mltframeserver exited"

# ------------------------------------------------------------- files
def get_frames_cache_folder():
    return utils.get_hidden_user_dir_path() +  appconsts.NODE_COMPOSITORS_DIR + "/" + appconsts.PHANTOM_DISK_CACHE_DIR

def get_port_file():
    return get_frames_cache_folder() + "/" + "session_" + _session_id

def get_frames_folder_for_frame_source(frame_source):
    return get_frames_cache_folder() + "/" + frame_source.md5id

# ------------------------------------------------------------- commands
def load(tokens):
    try:
        clip_path = tokens[1]
    except:
        return ERROR + " malformed command " + LOAD + NEW_LINE
    
    if os.path.isfile(clip_path) == False:
        return ERROR + "file does not exist, path:" + clip_path + NEW_LINE
    
    profile_index = get_clip_profile_index(clip_path)
    clip_profile = mltprofiles.get_profile_for_index(profile_index)
    clip_producer = mlt.Producer(clip_profile, str(clip_path))

    frame_source = FrameSourceClip(clip_path, clip_producer, clip_profile)
    
    _frame_sources[frame_source.md5id] = frame_source

    print "Created producer for", clip_path, "using profile", clip_profile.description()

    frames_folder = get_frames_folder_for_frame_source(frame_source)
    if not os.path.exists(frames_folder):
        print "Created new folder " + frames_folder
        os.mkdir(frames_folder)

    return frame_source.md5id + " " + str(frame_source.length) + NEW_LINE

def render_frame(tokens):
    try:
        clip_path = tokens[1]
        frame = int(tokens[2])
    except:
        return ERROR + " malformed command " + RENDER_FRAME + NEW_LINE

    try:
        frame_source = get_frame_source(clip_path)
        consumer = get_img_seq_render_consumer( get_frames_folder_for_frame_source(frame_source), \
                                                frame_source.profile)
    except:
        return ERROR + " creating consumer failed " + NEW_LINE
        
    renderer = renderconsumer.FileRenderPlayer(None, frame_source.producer, consumer, frame, frame + 1)
    renderer.wait_for_producer_end_stop = False
    renderer.consumer_pos_stop_add = 2 # Hack, see FileRenderPlayer
    renderer.start()

    while renderer.has_started_running == False:
        time.sleep(0.05)

    while renderer.stopped == False:
        time.sleep(0.05)
    
    return OK

def shutdown():
    os.remove(get_port_file())
    return OK

#  ----------------------------------------------------------- rendering
class FrameSourceClip:
    
    def __init__(self, path, producer, profile):
        self.path = path
        self.producer = producer
        self.profile = profile
        self.length = producer.get_length()
        self.md5id = md5.new(path).hexdigest()
        
def get_frame_source(clip_path):
    return _frame_sources[md5.new(clip_path).hexdigest()]
    
def get_clip_profile_index(clip_path):
    profile = mltprofiles.get_default_profile()
    producer = mlt.Producer(profile, str(clip_path))
    profile_index = mltprofiles.get_closest_matching_profile_index(utils.get_file_producer_info(producer))
    return profile_index

def get_img_seq_render_consumer(frames_folder, profile):
    #render_path = "%1/%2-%05d.%3" + file_path

    render_path = frames_folder + "/" + FRAME_NAME + "_%05d.png"
    print render_path

    consumer = mlt.Consumer(profile, "avformat", str(render_path))
    consumer.set("real_time", -1)
    consumer.set("rescale", "bicubic")
    consumer.set("vcodec", "png")
    print "img seq render consumer created, path:" +  str(render_path) #+ ", args: " + args_msg
    return consumer
    
