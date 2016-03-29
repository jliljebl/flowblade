
import locale
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
import utils


_session_id = None

# Answer strings
OK = "OK\n"
ERROR = "ERROR:"
NEW_LINE = "\n"

# Commandss
SHUTDOWN = "SHUTDOWN"
LOAD = "LOAD"
                
def main(root_path):
    respaths.set_paths(root_path)
    
    print sys.argv[0]
    
    # Get seesion id from args
    try:
        global _session_id
        _session_id = sys.argv[1]
        print  "mltframeserver session id:", _session_id
    except:
        print "session id was not provided in args, exiting..."
        sys.exit()

    editorpersistance.load()
    
    repo = mlt.Factory().init()

    # Set numeric locale to use "." as radix, MLT initilizes this to OS locale and this causes bugs 
    locale.setlocale(locale.LC_NUMERIC, 'C')

    # Create list of available mlt profiles
    mltprofiles.load_profile_list()

    # Create socket to listn to
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind(("",0))
    serversocket.listen(1)
    port = serversocket.getsockname()[1]
    print "mltframeserver listening to port:", port

    socket_file_path = get_port_file()
    socket_port_file = open(socket_file_path, 'w')
    socket_port_file.write(str(port))
    socket_port_file.close()

    # Accept connection to listen to, this will on listen to on client
    (client, addr) = serversocket.accept()

    print addr

    # Listen to commands in an edless loop
    try:
        running = True

        while running:

            # Get command
            command = client.recv(1024)
            command = command.rstrip(NEW_LINE)
            tokens = command.split(" ")
            
            print "command:" + command
            
            # Excute command
            if command == None:
                running = False
            else:
                if command.startswith(SHUTDOWN):
                    running = False
                    answer = shutdown()
                elif command.startswith(LOAD):
                    answer = load(tokens)

            client.send(answer)
    except Exception as e:
        print e

    print "mltframeserver exited"

# ------------------------------------------------------------- files
def get_frames_cache_folder():
    return utils.get_hidden_user_dir_path() +  appconsts.NODE_COMPOSITORS_DIR + "/" + appconsts.PHANTOM_DISK_CACHE_DIR

def get_port_file():
    return get_frames_cache_folder() + "/" + "session_" + _session_id

# ------------------------------------------------------------- commands
def load(tokens):
    try:
        clip_path = tokens[1]
    except:
        return ERROR + " malformed command " + LOAD + NEW_LINE
    
    if os.path.isfile(clip_path) == False:
        return ERROR + "file does not exist, path:" + clip_path + NEW_LINE
    
    profile_index = get_clip_profile_index(clip_path)
    print clip_path, profile_index
    
    return OK

def shutdown():
    os.remove(get_port_file())
    return OK

#  --------------------------------------------------------------------- clip
def get_clip_profile_index(clip_path):
    profile = mltprofiles.get_default_profile()
    producer = mlt.Producer(profile, str(clip_path))
    #global _current_profile
    profile_index = mltprofiles.get_closest_matching_profile_index(utils.get_file_producer_info(producer))
    #_current_profile = mltprofiles.get_profile_for_index(profile_index)
    return profile_index
