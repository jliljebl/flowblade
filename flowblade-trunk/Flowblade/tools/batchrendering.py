import datetime
import gobject
import gtk
import mlt
import md5
import os
import pango
import pickle
import subprocess
import sys

import editorpersistance
import guiutils
import mltenv
import mltprofiles
import mlttransitions
import mltfilters
import persistance
import respaths
import renderconsumer
import translations
import utils    


BATCH_DIR = "batchrender/"
DATAFILES_DIR = "batchrender/datafiles/"
PROJECTS_DIR = "batchrender/projects/"

PID_FILE = "batchrenderingpid"

WINDOW_WIDTH = 800
QUEUE_HEIGHT = 400

IN_QUEUE = 0
RENDERING = 1
RENDERED = 2

render_queue = []
batch_window = None


def lauch_batch_rendering():
    subprocess.Popen([sys.executable, respaths.ROOT_PARENT + "flowbladebatch"])

def add_render_item(flowblade_project, render_path, args_vals_list):
    init_dirs_if_needed()
        
    # Get time and user dir
    timestamp = datetime.datetime.now()
    user_dir = utils.get_hidden_user_dir_path()

    # Create item data file
    project_name = flowblade_project.name
    sequence_name = flowblade_project.c_seq.name
    sequence_index = flowblade_project.sequences.index(flowblade_project.c_seq)
    render_item = BatchRenderItemData(project_name, sequence_name, render_path, sequence_index, args_vals_list, timestamp)
    
    # Get identifier
    identifier = render_item.generate_identifier()

    # Write project 
    project_path = user_dir + PROJECTS_DIR + identifier + ".flb"
    print project_path
    persistance.save_project(flowblade_project, project_path)
    
    # Write render item file
    item_path = user_dir + DATAFILES_DIR + identifier + ".renderitem"
    print item_path
    item_write_file = file(item_path, "wb")
    pickle.dump(render_item, item_write_file)
    
    print "Render item for rendering file into " + render_path + " with identifier " + identifier + " added."

def init_dirs_if_needed():
    user_dir = utils.get_hidden_user_dir_path()

    if not os.path.exists(user_dir + BATCH_DIR):
        os.mkdir(user_dir + BATCH_DIR)
    if not os.path.exists(user_dir + DATAFILES_DIR):
        os.mkdir(user_dir + DATAFILES_DIR)
    if not os.path.exists(user_dir + PROJECTS_DIR):
        os.mkdir(user_dir + PROJECTS_DIR)
        
def main(root_path):
    # Allow only on instance to run
    user_dir = utils.get_hidden_user_dir_path()
    pid_file_path = user_dir + PID_FILE
    can_run = utils.single_instance_pid_file_test_and_write(pid_file_path)
    if can_run == False:
        return

    init_dirs_if_needed()


    # Set paths.
    respaths.set_paths(root_path)

    # Init translations module with translations data
    translations.init_languages()
    translations.load_filters_translations()
    mlttransitions.init_module()

    # Load editor prefs and list of recent projects
    editorpersistance.load()

    # Init gtk threads
    gtk.gdk.threads_init()

    repo = mlt.Factory().init()
    
    # Check for codecs and formats on the system
    mltenv.check_available_features(repo)
    renderconsumer.load_render_profiles()

    # Load filter and compositor descriptions from xml files.
    mltfilters.load_filters_xml(mltenv.services)
    mlttransitions.load_compositors_xml(mltenv.transitions)

    # Create list of available mlt profiles
    mltprofiles.load_profile_list()
    
    global render_queue
    render_queue.append(RenderQueueItem("lontoonmatka.flb  sequence_1", "/home/janne/testrender.mpg", 1500))
    render_queue.append(RenderQueueItem("titler_preview.flb  sequence_1", "/home/janne/ttitler.ogg", 750))
    render_queue.append(RenderQueueItem("mainos spotti.flb   sequence_1", "/home/janne/mainons.avi", 325))

    global window
    batch_window = BatchRenderWindow()

    # Launch gtk+ main loop
    gtk.main()

def shutdown():
    #batch_window.window.set_visible(False)

    while(gtk.events_pending()):
        gtk.main_iteration()
    
    gtk.main_quit()


class BatchRenderItemData:
    def __init__(self, project_name, sequence_name, render_path, sequence_index, args_vals_list, timestamp):
        self.project_name = project_name
        self.sequence_name = sequence_name
        self.sequence_index = sequence_index
        self.args_vals_list = args_vals_list
        self.timestamp = timestamp

    def generate_identifier(self):
        id_str = self.project_name + self.timestamp.ctime()
        return md5.new(id_str).hexdigest()
    

class RenderQueueItem:
    def __init__(self, sequence_name, path, length):
        self.render_this_item = True
        self.status = IN_QUEUE
        self.sequence_name = sequence_name
        self.target_file = path
        self.length = length
        self.start_time = -1
        self.render_time = -1
        self.custom_args = None
        self.enc_opt_index = -1
        self.qual_opt_index = -1
    
    def get_status_string(self):
        if self.status == IN_QUEUE:
            return _("Queued")
        elif self.status == RENDERING:
            return _("Rendering")
        else:
            return _("Finished")

    def get_start_time(self):
        return "-"
    
    def get_render_time(self):
        return "-"
    
class BatchRenderWindow:

    def __init__(self):
        # Window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete-event", lambda w, e:shutdown())
        
        
        self.total_render_time = gtk.Label()
        self.items_rendered = gtk.Label()
        tot_r = guiutils.get_right_justified_box([gtk.Label("Total Render Time:")])
        items_r = guiutils.get_right_justified_box([gtk.Label("Items Rendered:")])
        tot_r.set_size_request(250, 20)
        items_r.set_size_request(250, 20)
        
        info_vbox = gtk.VBox(False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([tot_r, self.total_render_time]), False, False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([items_r, self.items_rendered]), False, False, 0)

        self.render_progress_bar = gtk.ProgressBar()

        self.remove_selected = gtk.Button("Remove Selected")
        self.remove_finished = gtk.Button("Remove Finished")
        self.render_button = guiutils.get_render_button()
        self.stop_render_button = gtk.Button("Stop Render")
        self.stop_render_button.set_sensitive(False)

        button_row =  gtk.HBox(False, 0)
        button_row.pack_start(self.remove_selected, False, False, 0)
        button_row.pack_start(self.remove_finished, False, False, 0)
        button_row.pack_start(gtk.Label(), True, True, 0)
        button_row.pack_start(self.stop_render_button, False, False, 0)
        button_row.pack_start(self.render_button, False, False, 0)

        top_vbox = gtk.VBox(False, 0)
        top_vbox.pack_start(info_vbox, False, False, 0)
        top_vbox.pack_start(guiutils.get_pad_label(12, 12), False, False, 0)
        top_vbox.pack_start(self.render_progress_bar, False, False, 0)
        top_vbox.pack_start(guiutils.get_pad_label(12, 12), False, False, 0)
        top_vbox.pack_start(button_row, False, False, 0)

        top_align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        top_align.set_padding(12, 12, 12, 12)
        top_align.add(top_vbox)
    
        self.queue_view = RenderQueueView()
        self.queue_view.fill_data_model(render_queue)
        self.queue_view.set_size_request(WINDOW_WIDTH, QUEUE_HEIGHT)

        # Content pane
        pane = gtk.VBox(False, 1)
        pane.pack_start(top_align, False, True, 0)
        pane.pack_start(self.queue_view, False, True, 0)

        # Set pane and show window
        self.window.add(pane)
        self.window.set_title("Flowblade Batch Render")
        self.window.set_position(gtk.WIN_POS_CENTER)  
        self.window.show_all()




class RenderQueueView(gtk.VBox):
    """
    GUI component displaying list with columns: img, text, text
    Middle column expands.
    """

    def __init__(self):
        gtk.VBox.__init__(self)
        
       # Datamodel: icon, text, text
        self.storemodel = gtk.ListStore(bool, str, str, str, str, str)
 
        # Scroll container
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # View
        self.treeview = gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(True)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(gtk.SELECTION_SINGLE)

        # Cell renderers
        self.toggle_rend = gtk.CellRendererToggle()
        self.toggle_rend.set_property('activatable', True)
        self.toggle_rend.connect( 'toggled', self.toggled)

        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_END)

        self.text_rend_2 = gtk.CellRendererText()
        self.text_rend_2.set_property("yalign", 0.0)
        
        self.text_rend_3 = gtk.CellRendererText()
        self.text_rend_3.set_property("yalign", 0.0)
        
        self.text_rend_4 = gtk.CellRendererText()
        self.text_rend_4.set_property("yalign", 0.0)

        self.text_rend_5 = gtk.CellRendererText()
        self.text_rend_5.set_property("yalign", 0.0)
        

        # Column views
        self.toggle_col = gtk.TreeViewColumn("Render", self.toggle_rend)
        self.text_col_1 = gtk.TreeViewColumn("Project/Sequence")
        self.text_col_2 = gtk.TreeViewColumn("Status")
        self.text_col_3 = gtk.TreeViewColumn("Render File")
        self.text_col_4 = gtk.TreeViewColumn("Start Time")
        self.text_col_5 = gtk.TreeViewColumn("Render Time")

        # Build column views
        self.toggle_col.set_expand(False)
        self.toggle_col.add_attribute(self.toggle_rend, "active", 0) # <- note column index
        
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 1) # <- note column index

        self.text_col_2.set_expand(False)
        self.text_col_2.pack_start(self.text_rend_2)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 2)

        self.text_col_3.set_expand(False)
        self.text_col_3.pack_start(self.text_rend_3)
        self.text_col_3.add_attribute(self.text_rend_3, "text", 3)

        self.text_col_4.set_expand(False)
        self.text_col_4.pack_start(self.text_rend_4)
        self.text_col_4.add_attribute(self.text_rend_4, "text", 4)

        self.text_col_5.set_expand(False)
        self.text_col_5.pack_start(self.text_rend_5)
        self.text_col_5.add_attribute(self.text_rend_5, "text", 5)
        
        # Add column views to view
        self.treeview.append_column(self.toggle_col)
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)
        self.treeview.append_column(self.text_col_3)
        self.treeview.append_column(self.text_col_4)
        self.treeview.append_column(self.text_col_5)
        
        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
        self.scroll.show_all()
        self.show_all()

    def toggled(self, cell, path):
        self.storemodel[path][0] = not self.storemodel[path][0]
        self.scroll.queue_draw()

    def fill_data_model(self, render_queue):
        """
        Creates displayed data.
        Displays thumbnail icon, file name and length
        """
        self.storemodel.clear()
        for render_item in render_queue:
            row_data = [render_item.render_this_item,
                        render_item.sequence_name,
                        render_item.get_status_string(),
                        render_item.target_file, 
                        render_item.get_start_time(),
                        render_item.get_render_time()]
            print row_data
            self.storemodel.append(row_data)
            self.scroll.queue_draw()

