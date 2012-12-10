import gtk
import mlt

import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import persistance
import respaths
import render
import utils    

PID_FILE = "batchrenderingpid"
    
def main(root_path):
    # Allow only on instance to run
    user_dir = utils.get_hidden_user_dir_path()
    pid_file_path = user_dir + PID_FILE
    can_run = utils.single_instance_pid_file_test_and_write(pid_file_path)
    if can_run == False:
        return

    # Set paths.
    respaths.set_paths(root_path)
    
    # Init gtk threads
    gtk.gdk.threads_init()

    repo = mlt.Factory().init()
    
    # Check for codecs and formats on the system
    mltenv.check_available_features(repo)
    render.load_render_profiles()

    # Load filter and compositor descriptions from xml files.
    mltfilters.load_filters_xml(mltenv.services)
    mlttransitions.load_compositors_xml(mltenv.transitions)

    # Create list of available mlt profiles
    mltprofiles.load_profile_list()
    

    window = BatchRenderWindow()

    # Launch gtk+ main loop
    gtk.main()
 

class BatchRenderWindow:

    def __init__(self):
        # Window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        # Content pane
        pane = gtk.VBox(False, 1)
        pane.pack_start(gtk.Label("Batchrendering"), False, True, 0)


        # Set pane and show window
        self.window.add(pane)
        self.window.set_title("Flowblade")
        self.window.set_position(gtk.WIN_POS_CENTER)  
        self.window.show_all()



"""
    mlttransitions.init_module()

    # Load editor prefs and list of recent projects
    editorpersistance.load()

    # Init gtk threads
    gtk.gdk.threads_init()

    # Accept only 
    if can_run == False:
        _not_first_instance_exit()
        return

    # Adjust gui parameters for smaller screens
    scr_w = gtk.gdk.screen_width()
    scr_h = gtk.gdk.screen_height()
    editorstate.SCREEN_HEIGHT = scr_h
    _set_draw_params(scr_w, scr_h)

    # Refuse to run on too small screen.
    if scr_w < 1151 or scr_h < 767:
        _too_small_screen_exit()
        return

    # Splash screen
    if editorpersistance.prefs.display_splash_screen == True: 
        show_splash_screen()

    # Init MLT framework
    repo = mlt.Factory().init()
    
    # Check for codecs and formats on the system
    mltenv.check_available_features(repo)
    render.load_render_profiles()

    # Load filter and compositor descriptions from xml files.
    mltfilters.load_filters_xml(mltenv.services)
    mlttransitions.load_compositors_xml(mltenv.transitions)

    # Create list of available mlt profiles
    mltprofiles.load_profile_list()
"""
