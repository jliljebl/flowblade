import datetime
import gobject
import gtk
import mlt
import md5
import os
from os import listdir
from os.path import isfile, join
import pango
import pickle
import subprocess
import sys
import threading
import time

import dialogutils
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
render_thread = None
queue_runner_thread = None


class QueueRunnerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):        
        self.running = True
        items = 0
        global render_queue, batch_window, render_thread
        for render_item in render_queue.queue:
            if self.running == False:
                break
            current_render_time = 0

            identifier = render_item.generate_identifier()
            project_file_path = get_projects_dir() + identifier + ".flb"
            persistance.show_messages = False
            project = persistance.load_project(project_file_path, False)
            producer = project.c_seq.tractor
            consumer = renderconsumer.get_mlt_render_consumer(render_item.render_path, 
                                                              project.profile,
                                                              render_item.args_vals_list)
            global render_thread 
            render_thread = renderconsumer.FileRenderPlayer(None, producer, consumer, 0, render_item.length) # None == file name not needed this time when using FileRenderPlayer because callsite keeps track of things
            render_thread.start()
            
            render_item.render_started()
            batch_window.queue_view.fill_data_model(render_queue)
            batch_window.current_render.set_text("  " + render_item.get_display_name())
            
            self.thread_running = True
            while self.thread_running:         
                render_fraction = render_thread.get_render_fraction()
                now = time.time()
                current_render_time = now - render_item.start_time
                batch_window.update_render_progress(render_fraction, items, render_item.get_display_name(), current_render_time)
                if render_thread.producer.get_speed() == 0: # Rendering has reached end
                    self.thread_running = False
                    batch_window.render_progress_bar.set_fraction(1.0)
                    render_item.render_completed()
                else:
                    time.sleep(1)
            items = items + 1
            batch_window.update_render_progress(0, items, render_item.get_display_name(), 0)

        batch_window.render_queue_stopped()

def launch_batch_rendering():
    subprocess.Popen([sys.executable, respaths.ROOT_PARENT + "flowbladebatch"])

def add_render_item(flowblade_project, render_path, args_vals_list):
    init_dirs_if_needed()
        
    timestamp = datetime.datetime.now()

    # Create item data file
    project_name = flowblade_project.name
    sequence_name = flowblade_project.c_seq.name
    sequence_index = flowblade_project.sequences.index(flowblade_project.c_seq)
    length = flowblade_project.c_seq.get_length()
    render_item = BatchRenderItemData(project_name, sequence_name, render_path, sequence_index, args_vals_list, timestamp, length)
    
    # Get identifier
    identifier = render_item.generate_identifier()

    # Write project 
    project_path = get_projects_dir() + identifier + ".flb"
    persistance.save_project(flowblade_project, project_path)
    
    # Write render item file
    render_item.save()
    
    print "Render queue item for rendering file into " + render_path + " with identifier " + identifier + " added."

def init_dirs_if_needed():
    user_dir = utils.get_hidden_user_dir_path()

    if not os.path.exists(user_dir + BATCH_DIR):
        os.mkdir(user_dir + BATCH_DIR)
    if not os.path.exists(get_datafiles_dir()):
        os.mkdir(get_datafiles_dir())
    if not os.path.exists(get_projects_dir()):
        os.mkdir(get_projects_dir())

def get_projects_dir():
    return utils.get_hidden_user_dir_path() + PROJECTS_DIR

def get_datafiles_dir():
    return utils.get_hidden_user_dir_path() + DATAFILES_DIR

def main(root_path):
    # Allow only on instance to run
    """
    user_dir = utils.get_hidden_user_dir_path()
    pid_file_path = user_dir + PID_FILE
    can_run = utils.single_instance_pid_file_test_and_write(pid_file_path)
    if can_run == False:
        return
    """

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
    render_queue = RenderQueue()
    render_queue.load_render_items()

    global batch_window
    batch_window = BatchRenderWindow()

    # Launch gtk+ main loop
    gtk.main()

def shutdown():
    #batch_window.window.set_visible(False)

    while(gtk.events_pending()):
        gtk.main_iteration()
    
    gtk.main_quit()


class RenderQueue:
    def __init__(self):
        self.queue = []
        
    def load_render_items(self):
        user_dir = utils.get_hidden_user_dir_path()
        data_files_dir = user_dir + DATAFILES_DIR
        data_files = [ f for f in listdir(data_files_dir) if isfile(join(data_files_dir,f)) ]
        for data_file_name in data_files:
            data_file_path = data_files_dir + data_file_name
            data_file = open(data_file_path)
            render_item = pickle.load(data_file)
            self.queue.append(render_item)


class BatchRenderItemData:
    def __init__(self, project_name, sequence_name, render_path, sequence_index, args_vals_list, timestamp, length):
        self.project_name = project_name
        self.sequence_name = sequence_name
        self.render_path = render_path
        self.sequence_index = sequence_index
        self.args_vals_list = args_vals_list
        self.timestamp = timestamp
        self.length = length
        self.render_this_item = True
        self.status = IN_QUEUE
        self.start_time = -1
        self.render_time = -1

    def generate_identifier(self):
        id_str = self.project_name + self.timestamp.ctime()
        return md5.new(id_str).hexdigest()

    def save(self):
        item_path = get_datafiles_dir() + self.generate_identifier() + ".renderitem"
        item_write_file = file(item_path, "wb")
        pickle.dump(self, item_write_file)

    def delete_from_queue(self):
        identifier = self.generate_identifier()
        item_path = get_datafiles_dir() + identifier + ".renderitem"
        os.remove(item_path)
        project_path = get_projects_dir() + identifier + ".flb"
        os.remove(project_path)
        render_queue.queue.remove(self)

    def render_started(self):
        self.status = RENDERING 
        self.start_time = time.time() 
        
    def render_completed(self):
        self.status = RENDERED
        self.render_this_item = False
        self.render_time = time.time() - self.start_time
        self.save()

    def get_status_string(self):
        if self.status == IN_QUEUE:
            return _("Queued")
        elif self.status == RENDERING:
            return _("Rendering")
        else:
            return _("Finished")

    def get_display_name(self):
        return self.project_name + "/" + self.sequence_name

    def get_start_time(self):
        #passed_str = utils.get_time_str_for_sec_float(passed_time)
        return "-"
    
    def get_render_time(self):
        if self.render_time != -1:
            return utils.get_time_str_for_sec_float(self.render_time)
        else:
            return "-"


class BatchRenderWindow:

    def __init__(self):
        # Window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete-event", lambda w, e:shutdown())

        self.est_time_left = gtk.Label()
        self.current_render = gtk.Label()
        self.current_render_time = gtk.Label()
        est_r = guiutils.get_right_justified_box([guiutils.bold_label("Estimated Left:")])
        current_r = guiutils.get_right_justified_box([guiutils.bold_label("Current Render:")])
        current_r_t = guiutils.get_right_justified_box([guiutils.bold_label("Elapsed:")])
        est_r.set_size_request(250, 20)
        current_r.set_size_request(250, 20)
        current_r_t.set_size_request(250, 20)
        
        info_vbox = gtk.VBox(False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([current_r, self.current_render]), False, False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([current_r_t, self.current_render_time]), False, False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([est_r, self.est_time_left]), False, False, 0)
        
        self.items_rendered = gtk.Label()
        items_r = gtk.Label("Items Rendered:")
        self.render_started = gtk.Label()
        started_r = gtk.Label("Render Started:")
    
        bottom_info_vbox = gtk.HBox(True, 0)
        bottom_info_vbox.pack_start(guiutils.get_left_justified_box([items_r, self.items_rendered]), True, True, 0)
        bottom_info_vbox.pack_start(guiutils.get_left_justified_box([started_r, self.render_started]), True, True, 0)
        
        self.not_rendering_txt = "Not Rendering"
        self.render_progress_bar = gtk.ProgressBar()
        self.render_progress_bar.set_text(self.not_rendering_txt)

        self.remove_selected = gtk.Button("Delete Selected")
        self.remove_selected.connect("clicked", 
                                     lambda w, e: self.remove_selected_clicked(), 
                                     None)
        self.remove_finished = gtk.Button("Delete Finished")
        self.remove_finished.connect("clicked", 
                                     lambda w, e: self.remove_finished_clicked(), 
                                     None)

        self.render_button = guiutils.get_render_button()
        self.render_button.connect("clicked", 
                                   lambda w, e: self.launch_render(), 
                                   None)
                                         
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

        bottom_align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        bottom_align.set_padding(0, 2, 8, 8)
        bottom_align.add(bottom_info_vbox)

        # Content pane
        pane = gtk.VBox(False, 1)
        pane.pack_start(top_align, False, True, 0)
        pane.pack_start(self.queue_view, False, True, 0)
        pane.pack_start(bottom_align, False, False, 0)

        # Set pane and show window
        self.window.add(pane)
        self.window.set_title("Flowblade Batch Render")
        self.window.set_position(gtk.WIN_POS_CENTER)  
        self.window.show_all()

    def remove_finished_clicked(self):
        delete_list = []
        for render_item in render_queue.queue:
            if render_item.status == RENDERED:
                delete_list.append(render_item)
        if len(delete_list) > 0:
            self.display_delete_confirm(delete_list)

    def remove_selected_clicked(self):
        model, rows = self.queue_view.treeview.get_selection().get_selected_rows()
        delete_list = []
        for row in rows:
            delete_list.append(render_queue.queue[max(row)])
        if len(delete_list) > 0:
            self.display_delete_confirm(delete_list)

    def display_delete_confirm(self, delete_list):
        primary_txt = "Delete " + str(len(delete_list)) + " item(s) from render queue?"
        secondary_txt = "This operation cannot be undone."
        dialogutils.warning_confirmation(self._confirm_items_delete_callback, primary_txt, secondary_txt, self.window , data=delete_list, is_info=False)
        
    def _confirm_items_delete_callback(self, dialog, response_id, delete_list):
        if response_id == gtk.RESPONSE_ACCEPT:
            for delete_item in delete_list:
                delete_item.delete_from_queue()
            self.update_queue_view()
        
        dialog.destroy()

    def update_queue_view(self):
        self.queue_view.fill_data_model(render_queue)

    def launch_render(self):
        global queue_runner_thread
        self.render_button.set_sensitive(False)
        self.stop_render_button.set_sensitive(True)
        self.est_time_left.set_text("")
        self.items_rendered.set_text("")
        start_time = datetime.datetime.now()
        start_str = start_time.strftime('  %H:%M, %d %B, %Y')
        self.render_started.set_text(start_str)
        self.remove_selected.set_sensitive(False)
        self.remove_finished.set_sensitive(False)
        queue_runner_thread = QueueRunnerThread()
        queue_runner_thread.start()

    def update_render_progress(self, fraction, items, current_name, current_render_time_passed):
        self.render_progress_bar.set_fraction(fraction)

        progress_str = str(int(fraction * 100)) + " %"
        self.render_progress_bar.set_text(progress_str)

        if fraction != 0:
            full_time_est = (1.0 / fraction) * current_render_time_passed
            left_est = full_time_est - current_render_time_passed
            est_str = "  " + utils.get_time_str_for_sec_float(left_est)
        else:
            est_str = ""
        self.est_time_left.set_text(est_str)
        
        if current_render_time_passed != 0:
            current_str= "  " + utils.get_time_str_for_sec_float(current_render_time_passed)
        else:
            current_str = ""
        self.current_render_time.set_text(current_str)
        
        self.items_rendered.set_text("  " + str(items))

    def render_queue_stopped(self):
        self.render_progress_bar.set_fraction(0.0)
        self.render_button.set_sensitive(True)
        self.stop_render_button.set_sensitive(False)
        self.render_progress_bar.set_text(self.not_rendering_txt)
        self.current_render.set_text("")
        self.remove_selected.set_sensitive(True)
        self.remove_finished.set_sensitive(True)

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
        tree_sel.set_mode(gtk.SELECTION_MULTIPLE)

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
        
        for render_item in render_queue.queue:
            row_data = [render_item.render_this_item,
                        render_item.get_display_name(),
                        render_item.get_status_string(),
                        render_item.render_path, 
                        render_item.get_start_time(),
                        render_item.get_render_time()]
            print row_data
            self.storemodel.append(row_data)
            self.scroll.queue_draw()


"""
  def foreach_cb(model, path, iter, pathlist):
      list.append(path)

  def my_get_selected_rows(treeselection):
      pathlist = []
      treeselection.selected_foreach(foreach_cb, pathlist)
      model = sel.get_treeview().get_model()
      return (model, pathlist)
"""
