"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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

import datetime
import gobject
import pygtk
pygtk.require('2.0');
import gtk

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import mlt
import md5
import locale
import os
from os import listdir
from os.path import isfile, join
import pango
import pickle
import shutil
import subprocess
import sys
import textwrap
import time
import threading

import dialogutils
import editorstate
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
UNQUEUED = 3
ABORTED = 4

render_queue = []
batch_window = None
render_thread = None
queue_runner_thread = None

timeout_id = None

_dbus_service = None

# -------------------------------------------------------- render thread
class QueueRunnerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):        
        self.running = True
        items = 0
        global render_queue, batch_window
        for render_item in render_queue.queue:
            if self.running == False:
                break
            if render_item.render_this_item == False:
                continue
            
            current_render_time = 0

            # Create render objects
            identifier = render_item.generate_identifier()
            project_file_path = get_projects_dir() + identifier + ".flb"
            persistance.show_messages = False

            project = persistance.load_project(project_file_path, False)

            producer = project.c_seq.tractor
            consumer = renderconsumer.get_mlt_render_consumer(render_item.render_path, 
                                                              project.profile,
                                                              render_item.args_vals_list)

            # Get render range
            start_frame, end_frame, wait_for_stop_render = get_render_range(render_item)
            
            # Create and launch render thread
            global render_thread 
            render_thread = renderconsumer.FileRenderPlayer(None, producer, consumer, start_frame, end_frame) # None == file name not needed this time when using FileRenderPlayer because callsite keeps track of things
            render_thread.wait_for_producer_end_stop = wait_for_stop_render
            render_thread.start()

            # Set render start time and item state
            render_item.render_started()

            gtk.gdk.threads_enter()
            batch_window.update_queue_view()
            batch_window.current_render.set_text("  " + render_item.get_display_name())
            gtk.gdk.threads_leave()

            # Make sure that render thread is actually running before
            # testing render_thread.running value later
            while render_thread.has_started_running == False:
                time.sleep(0.05)

            # View update loop
            self.thread_running = True
            self.aborted = False
            while self.thread_running:
                if self.aborted == True:
                    break        
                render_fraction = render_thread.get_render_fraction()
                now = time.time()
                current_render_time = now - render_item.start_time
                
                gtk.gdk.threads_enter()
                batch_window.update_render_progress(render_fraction, items, render_item.get_display_name(), current_render_time)
                gtk.gdk.threads_leave()
                
                if render_thread.running == False: # Rendering has reached end
                    self.thread_running = False
                    
                    gtk.gdk.threads_enter()
                    batch_window.render_progress_bar.set_fraction(1.0)
                    gtk.gdk.threads_leave()
                                    
                    render_item.render_completed()
                else:
                    time.sleep(0.33)
                    
            if not self.aborted:
                items = items + 1
                gtk.gdk.threads_enter()
                batch_window.update_render_progress(0, items, render_item.get_display_name(), 0)
                gtk.gdk.threads_leave()
            else:
                if render_item != None:
                    render_item.render_aborted()
                    break
            render_thread.shutdown()
        
        # Update view for render end
        gtk.gdk.threads_enter()
        batch_window.reload_queue() # item may havee added to queue while rendering
        batch_window.render_queue_stopped()
        gtk.gdk.threads_leave()
                    
    def abort(self):
        render_thread.shutdown()
        # It may be that 'aborted' and 'running' could combined into single flag, but whatevaar
        self.aborted = True
        self.running = False
        self.thread_running = False
        
        batch_window.reload_queue() # item may havee added to queue while rendering


class BatchRenderDBUSService(dbus.service.Object):
    def __init__(self):
        print "dbus service init"
        bus_name = dbus.service.BusName('flowblade.movie.editor.batchrender', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, '/flowblade/movie/editor/batchrender')

    @dbus.service.method('flowblade.movie.editor.batchrender')
    def render_item_added(self):
        if queue_runner_thread == None:
            batch_window.reload_queue()
        
        return "OK"

    @dbus.service.method('flowblade.movie.editor.batchrender')
    def remove_from_dbus(self):
        self.remove_from_connection()
        return
   

# --------------------------------------------------- adding item, always called from main app
def add_render_item(flowblade_project, render_path, args_vals_list, mark_in, mark_out, render_data):
    init_dirs_if_needed()
        
    timestamp = datetime.datetime.now()

    # Create item data file
    project_name = flowblade_project.name
    sequence_name = flowblade_project.c_seq.name
    sequence_index = flowblade_project.sequences.index(flowblade_project.c_seq)
    length = flowblade_project.c_seq.get_length()
    render_item = BatchRenderItemData(project_name, sequence_name, render_path, \
                                      sequence_index, args_vals_list, timestamp, length, \
                                      mark_in, mark_out, render_data)

    # Get identifier
    identifier = render_item.generate_identifier()

    # Write project 
    project_path = get_projects_dir() + identifier + ".flb"
    persistance.save_project(flowblade_project, project_path)

    # Write render item file
    render_item.save()

    bus = dbus.SessionBus()
    if bus.name_has_owner('flowblade.movie.editor.batchrender'):
        obj = bus.get_object('flowblade.movie.editor.batchrender', '/flowblade/movie/editor/batchrender')
        iface = dbus.Interface(obj, 'flowblade.movie.editor.batchrender')
        iface.render_item_added()
    else:
        launch_batch_rendering()

    print "Render queue item for rendering file into " + render_path + " with identifier " + identifier + " added."

# ------------------------------------------------------- file utils
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

def get_identifier_from_path(file_path):
    start = file_path.rfind("/")
    end = file_path.rfind(".")
    return file_path[start + 1:end]

def _get_pid_file_path():
    user_dir = utils.get_hidden_user_dir_path()
    return user_dir + PID_FILE
    
def destroy_for_identifier(identifier):
    try:
        item_path = get_datafiles_dir() + identifier + ".renderitem"
        os.remove(item_path)
    except:
        pass
    
    try:
        project_path = get_projects_dir() + identifier + ".flb"
        os.remove(project_path)
    except:
        pass    

def copy_project(render_item, file_name):
    try:
        shutil.copyfile(render_item.get_project_filepath(), file_name)
    except Exception as e:
        primary_txt = _("Render Item Project File Copy failed!")
        secondary_txt = _("Error message: ") + str(e)
        dialogutils.warning_message(primary_txt, secondary_txt, batch_window.window)

# --------------------------------------------------------------- app thread and data objects
def launch_batch_rendering():
    bus = dbus.SessionBus()
    if bus.name_has_owner('flowblade.movie.editor.batchrender'):
        print "flowblade.movie.editor.batchrender dbus service exists, batch rendering already running"
        _show_single_instance_info()
    else:
        FNULL = open(os.devnull, 'w')
        subprocess.Popen([sys.executable, respaths.LAUNCH_DIR + "flowbladebatch"], stdin=FNULL, stdout=FNULL, stderr=FNULL)

def main(root_path, force_launch=False):
    # Allow only on instance to run
    #can_run = test_and_write_pid()
    can_run = True
    init_dirs_if_needed()

    editorstate.gtk_version = gtk.gtk_version
    try:
        editorstate.mlt_version = mlt.LIBMLT_VERSION
    except:
        editorstate.mlt_version = "0.0.99" # magic string for "not found"
        
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
    gtk.gdk.threads_enter()

    repo = mlt.Factory().init()

    # Set numeric locale to use "." as radix, MLT initilizes this to OS locale and this causes bugs 
    locale.setlocale(locale.LC_NUMERIC, 'C')

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

    if render_queue.error_status != None:
        primary_txt = _("Error loading render queue items!")
        secondary_txt = _("Message:\n") + render_queue.get_error_status_message()
        dialogutils.warning_message(primary_txt, secondary_txt, batch_window.window)

    DBusGMainLoop(set_as_default=True)
    global _dbus_service
    _dbus_service = BatchRenderDBUSService()

    gtk.main()
    gtk.gdk.threads_leave()

def _show_single_instance_info():
    global timeout_id
    timeout_id = gobject.timeout_add(200, _display_single_instance_window)
    # Launch gtk+ main loop
    gtk.main()
    
def _display_single_instance_window():
    gobject.source_remove(timeout_id)
    primary_txt = _("Batch Render Queue already running!")

    msg = _("Batch Render Queue application was detected in session dbus.")
    #msg = msg1 + msg2
    content = dialogutils.get_warning_message_dialog_panel(primary_txt, msg, True)
    align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    align.set_padding(0, 12, 0, 0)
    align.add(content)

    dialog = gtk.Dialog("",
                        None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("OK").encode('utf-8'), gtk.RESPONSE_OK))

    dialog.vbox.pack_start(align, True, True, 0)
    dialogutils.default_behaviour(dialog)
    dialog.connect('response', _early_exit)
    dialog.show_all()

def _early_exit(dialog, response):
    dialog.destroy()
    gtk.main_quit() 
    
def shutdown():
    if queue_runner_thread != None:
        primary_txt = _("Application is rendering and cannot be closed!")
        secondary_txt = _("Stop rendering before closing the application.")
        dialogutils.info_message(primary_txt, secondary_txt, batch_window.window)
        return True # Tell callsite (inside GTK toolkit) that event is handled, otherwise it'll destroy window anyway.

    while(gtk.events_pending()):
        gtk.main_iteration()

    if _dbus_service != None:
        _dbus_service.remove_from_dbus()
    gtk.main_quit()


class RenderQueue:
    def __init__(self):
        self.queue = []
        self.error_status = None
        
    def load_render_items(self):
        self.queue = []
        self.error_status = None
        user_dir = utils.get_hidden_user_dir_path()
        data_files_dir = user_dir + DATAFILES_DIR
        data_files = [ f for f in listdir(data_files_dir) if isfile(join(data_files_dir,f)) ]
        for data_file_name in data_files:
            try:
                data_file_path = data_files_dir + data_file_name
                data_file = open(data_file_path)
                render_item = pickle.load(data_file)
                self.queue.append(render_item)
            except Exception as e:
                if self.error_status == None:
                    self.error_status = []
                self.error_status.append((data_file_name,  _(" datafile load failed with ") + str(e)))
            try:
                render_file = open(render_item.get_project_filepath())
            except Exception as e:
                if self.error_status == None:
                    self.error_status = []
                self.error_status.append((render_item.get_project_filepath(), _(" project file load failed with ") + str(e)))

        if self.error_status != None:
            for file_path, error_str in self.error_status:
                identifier = get_identifier_from_path(file_path)
                destroy_for_identifier(identifier)
                for render_item in self.queue:
                    if render_item.matches_identifier(identifier):
                        self.queue.remove(render_item)
                        break

        # Latest added items displayed on top
        self.queue.sort(key=lambda item: item.timestamp)
        self.queue.reverse()

    def get_error_status_message(self):
        msg = ""
        for file_path, error_str in self.error_status:
            err_str_item = file_path + error_str
            lines = textwrap.wrap(err_str_item, 80)
            for line in lines:
                msg = msg + line + "\n"

        return msg

    def check_for_same_paths(self):
        same_paths = {}
        path_counts = {}
        queued = []
        for render_item in self.queue:
            if render_item.status == IN_QUEUE:
                queued.append(render_item)
        for render_item in queued:
            try:
                count = path_counts[render_item.render_path]
                count = count + 1
                path_counts[render_item.render_path] = count
            except:
                path_counts[render_item.render_path] = 1
        
        for k,v in path_counts.iteritems():
            if v > 1:
                same_paths[k] = v
        
        return same_paths

        
class BatchRenderItemData:
    def __init__(self, project_name, sequence_name, render_path, sequence_index, \
                 args_vals_list, timestamp, length, mark_in, mark_out, render_data):
        self.project_name = project_name
        self.sequence_name = sequence_name
        self.render_path = render_path
        self.sequence_index = sequence_index
        self.args_vals_list = args_vals_list
        self.timestamp = timestamp
        self.length = length
        self.mark_in = mark_in
        self.mark_out = mark_out
        self.render_data = render_data
        self.render_this_item = True
        self.status = IN_QUEUE
        self.start_time = -1
        self.render_time = -1

    def generate_identifier(self):
        id_str = self.project_name + self.timestamp.ctime()
        return md5.new(id_str).hexdigest()

    def matches_identifier(self, identifier):
        if self.generate_identifier() == identifier:
            return True
        else:
            return False

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
    
    def render_aborted(self):
        self.status = ABORTED
        self.render_this_item = False
        self.render_time = -1
        self.save()

        global queue_runner_thread, render_thread
        render_thread = None
        queue_runner_thread = None      

    def get_status_string(self):
        if self.status == IN_QUEUE:
            return _("Queued")
        elif self.status == RENDERING:
            return _("Rendering")
        elif self.status == RENDERED:
            return _("Finished")
        elif self.status == UNQUEUED:
            return _("Unqueued")
        else:
            return _("Aborted")

    def get_display_name(self):
        return self.project_name + "/" + self.sequence_name
    
    def get_render_time(self):
        if self.render_time != -1:
            return utils.get_time_str_for_sec_float(self.render_time)
        else:
            return "-"
    
    def get_project_filepath(self):
        return get_projects_dir() + self.generate_identifier() + ".flb"


class RenderData:

    def __init__(self, enc_index, quality_index, user_args, profile_desc, profile_name, fps):
        self.enc_index = enc_index
        self.quality_index = quality_index
        self.user_args = user_args
        self.profile_desc = profile_desc
        self.profile_name = profile_name
        self.fps = fps

def get_render_range(render_item):
    if render_item.mark_in < 0: # no range defined
        start_frame = 0
        end_frame = render_item.length - 1 #
        wait_for_stop_render = True
    elif render_item.mark_out < 0: # only start defined
        start_frame = render_item.mark_in
        end_frame = render_item.length - 1 #
        wait_for_stop_render = True
    else: # both start and end defined
        start_frame = render_item.mark_in
        end_frame = render_item.mark_out
        wait_for_stop_render = False
    
    return (start_frame, end_frame, wait_for_stop_render)


# -------------------------------------------------------------------- gui
class BatchRenderWindow:

    def __init__(self):
        # Window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete-event", lambda w, e:shutdown())
        app_icon = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "flowbladebatchappicon.png")
        self.window.set_icon_list(app_icon)

        self.est_time_left = gtk.Label()
        self.current_render = gtk.Label()
        self.current_render_time = gtk.Label()
        est_r = guiutils.get_right_justified_box([guiutils.bold_label(_("Estimated Left:"))])
        current_r = guiutils.get_right_justified_box([guiutils.bold_label(_("Current Render:"))])
        current_r_t = guiutils.get_right_justified_box([guiutils.bold_label(_("Elapsed:"))])
        est_r.set_size_request(250, 20)
        current_r.set_size_request(250, 20)
        current_r_t.set_size_request(250, 20)
        
        info_vbox = gtk.VBox(False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([current_r, self.current_render]), False, False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([current_r_t, self.current_render_time]), False, False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([est_r, self.est_time_left]), False, False, 0)
        
        self.items_rendered = gtk.Label()
        items_r = gtk.Label(_("Items Rendered:"))
        self.render_started_label = gtk.Label()
        started_r = gtk.Label(_("Render Started:"))
    
        bottom_info_vbox = gtk.HBox(True, 0)
        bottom_info_vbox.pack_start(guiutils.get_left_justified_box([items_r, self.items_rendered]), True, True, 0)
        bottom_info_vbox.pack_start(guiutils.get_left_justified_box([started_r, self.render_started_label]), True, True, 0)
        
        self.not_rendering_txt = _("Not Rendering")
        self.render_progress_bar = gtk.ProgressBar()
        self.render_progress_bar.set_text(self.not_rendering_txt)

        self.remove_selected = gtk.Button(_("Delete Selected"))
        self.remove_selected.connect("clicked", 
                                     lambda w, e: self.remove_selected_clicked(), 
                                     None)
        self.remove_finished = gtk.Button(_("Delete Finished"))
        self.remove_finished.connect("clicked", 
                                     lambda w, e: self.remove_finished_clicked(), 
                                     None)

        self.reload_button = gtk.Button(_("Reload Queue"))
        self.reload_button.connect("clicked", 
                                     lambda w, e: self.reload_queue(), 
                                     None)


        self.render_button = guiutils.get_render_button()
        self.render_button.connect("clicked", 
                                   lambda w, e: self.launch_render(), 
                                   None)
                                         
        self.stop_render_button = gtk.Button(_("Stop Render"))
        self.stop_render_button.set_sensitive(False)
        self.stop_render_button.connect("clicked", 
                                   lambda w, e: self.abort_render(), 
                                   None)

        button_row =  gtk.HBox(False, 0)
        button_row.pack_start(self.remove_selected, False, False, 0)
        button_row.pack_start(self.remove_finished, False, False, 0)
        button_row.pack_start(gtk.Label(), True, True, 0)
        #button_row.pack_start(self.reload_button, True, True, 0)
        #button_row.pack_start(gtk.Label(), True, True, 0)
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
        pane.pack_start(top_align, False, False, 0)
        pane.pack_start(self.queue_view, True, True, 0)
        pane.pack_start(bottom_align, False, False, 0)

        # Set pane and show window
        self.window.add(pane)
        self.window.set_title(_("Flowblade Batch Render"))
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

    def remove_item(self, render_item):
        delete_list = []
        delete_list.append(render_item)
        self.display_delete_confirm(delete_list)

    def display_delete_confirm(self, delete_list):
        primary_txt = _("Delete ") + str(len(delete_list)) + _(" item(s) from render queue?")
        secondary_txt = _("This operation cannot be undone.")
        dialogutils.warning_confirmation(self._confirm_items_delete_callback, primary_txt, secondary_txt, self.window , data=delete_list, is_info=False)
        
    def _confirm_items_delete_callback(self, dialog, response_id, delete_list):
        if response_id == gtk.RESPONSE_ACCEPT:
            for delete_item in delete_list:
                delete_item.delete_from_queue()
            self.update_queue_view()
        
        dialog.destroy()

    def reload_queue(self):
        global render_queue
        render_queue = RenderQueue()
        render_queue.load_render_items()

        if render_queue.error_status != None:
            primary_txt = _("Error loading render queue items!")
            secondary_txt = _("Message:\n") + render_queue.get_error_status_message()
            dialogutils.warning_message(primary_txt, secondary_txt, batch_window.window)
            return
    
        self.queue_view.fill_data_model(render_queue)

    def update_queue_view(self):
        self.queue_view.fill_data_model(render_queue)

    def launch_render(self):
        same_paths = render_queue.check_for_same_paths()
        if len(same_paths) > 0:
            primary_txt = _("Multiple items with same render target file!")
            
            secondary_txt = _("Later items will render on top of earlier items if this queue is rendered.\n") + \
                            _("Delete or unqueue some items with same paths:\n\n")
            for k,v in same_paths.iteritems():
                secondary_txt = secondary_txt + str(v) + _(" items with path: ") + str(k) + "\n"
            dialogutils.warning_message(primary_txt, secondary_txt, batch_window.window)
            return

        # GUI pattern for rendering
        self.render_button.set_sensitive(False)
        self.reload_button.set_sensitive(False)
        self.stop_render_button.set_sensitive(True)
        self.est_time_left.set_text("")
        self.items_rendered.set_text("")
        start_time = datetime.datetime.now()
        start_str = start_time.strftime('  %H:%M, %d %B, %Y')
        self.render_started_label.set_text(start_str)
        self.remove_selected.set_sensitive(False)
        self.remove_finished.set_sensitive(False)

        global queue_runner_thread
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

    def abort_render(self):
        global queue_runner_thread
        queue_runner_thread.abort()
    
    def render_queue_stopped(self):
        self.render_progress_bar.set_fraction(0.0)
        self.render_button.set_sensitive(True)
        self.reload_button.set_sensitive(True)
        self.stop_render_button.set_sensitive(False)
        self.render_progress_bar.set_text(self.not_rendering_txt)
        self.current_render.set_text("")
        self.remove_selected.set_sensitive(True)
        self.remove_finished.set_sensitive(True)

        global queue_runner_thread, render_thread
        render_thread = None
        queue_runner_thread = None        


class RenderQueueView(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)
        
        self.storemodel = gtk.ListStore(bool, str, str, str, str)
        
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

        # Column views
        self.toggle_col = gtk.TreeViewColumn(_("Render"), self.toggle_rend)
        self.text_col_1 = gtk.TreeViewColumn(_("Project/Sequence"))
        self.text_col_2 = gtk.TreeViewColumn(_("Status"))
        self.text_col_3 = gtk.TreeViewColumn(_("Render File"))
        self.text_col_4 = gtk.TreeViewColumn(_("Render Time"))

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

        # Add column views to view
        self.treeview.append_column(self.toggle_col)
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)
        self.treeview.append_column(self.text_col_3)
        self.treeview.append_column(self.text_col_4)

        # popup menu
        self.treeview.connect("button-press-event", self.on_treeview_button_press_event)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
        self.scroll.show_all()
        self.show_all()

    def toggled(self, cell, path):
        item_index = int(path)
        global render_queue
        render_queue.queue[item_index].render_this_item = not render_queue.queue[item_index].render_this_item
        if render_queue.queue[item_index].render_this_item == True:
            render_queue.queue[item_index].status = IN_QUEUE
        else:
            render_queue.queue[item_index].status = UNQUEUED
        self.fill_data_model(render_queue)

    def on_treeview_button_press_event(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                display_render_item_popup_menu(self.item_menu_item_selected, event)
            return True
        else:
            return False

    def item_menu_item_selected(self, widget, msg):
        model, rows = self.treeview.get_selection().get_selected_rows()
        render_item = render_queue.queue[max(rows[0])]
        if msg == "renderinfo":
            show_render_properties_panel(render_item)
        elif msg == "delete":
            batch_window.remove_item(render_item)
        elif msg == "saveas":
            file_name = run_save_project_as_dialog(render_item.project_name)
            if file_name != None:
                copy_project(render_item, file_name)

    def fill_data_model(self, render_queue):
        self.storemodel.clear()        
        
        for render_item in render_queue.queue:
            row_data = [render_item.render_this_item,
                        render_item.get_display_name(),
                        render_item.get_status_string(),
                        render_item.render_path, 
                        render_item.get_render_time()]
            self.storemodel.append(row_data)
            self.scroll.queue_draw()


def run_save_project_as_dialog(project_name):
    dialog = gtk.FileChooserDialog(_("Save Render Item Project As"), None, 
                                   gtk.FILE_CHOOSER_ACTION_SAVE, 
                                   (_("Cancel").encode('utf-8'), gtk.RESPONSE_REJECT,
                                    _("Save").encode('utf-8'), gtk.RESPONSE_ACCEPT), None)
    dialog.set_action(gtk.FILE_CHOOSER_ACTION_SAVE)
    project_name = project_name.rstrip(".flb")
    dialog.set_current_name(project_name + "_FROM_BATCH.flb")
    dialog.set_do_overwrite_confirmation(True)
    response_id = dialog.run()
    if response_id == gtk.RESPONSE_NONE:
        dialog.destroy()
        return None
    file_name = dialog.get_filename()
    dialog.destroy()
    return file_name

def show_render_properties_panel(render_item):
    if render_item.render_data.user_args == False:
        enc_opt = renderconsumer.encoding_options[render_item.render_data.enc_index]
        enc_desc = enc_opt.name
        audio_desc = enc_opt.audio_desc
        quality_opt = enc_opt.quality_options[render_item.render_data.quality_index]
        quality_desc = quality_opt.name
    else:
        enc_desc = " -" 
        quality_desc = " -"
        audio_desc = " -"

    user_args = str(render_item.render_data.user_args)

    start_frame, end_frame, wait_for_stop_render = get_render_range(render_item)
    start_str = utils.get_tc_string_with_fps(start_frame, render_item.render_data.fps)
    end_str = utils.get_tc_string_with_fps(end_frame, render_item.render_data.fps)
    
    LEFT_WIDTH = 200
    render_item.get_display_name()
    row0 = guiutils.get_two_column_box(guiutils.bold_label(_("Encoding:")), gtk.Label(enc_desc), LEFT_WIDTH)
    row1 = guiutils.get_two_column_box(guiutils.bold_label(_("Quality:")), gtk.Label(quality_desc), LEFT_WIDTH)
    row2 = guiutils.get_two_column_box(guiutils.bold_label(_("Audio Encoding:")), gtk.Label(audio_desc), LEFT_WIDTH)
    row3 = guiutils.get_two_column_box(guiutils.bold_label(_("Use User Args:")), gtk.Label(user_args), LEFT_WIDTH)
    row4 = guiutils.get_two_column_box(guiutils.bold_label(_("Start:")), gtk.Label(start_str), LEFT_WIDTH)
    row5 = guiutils.get_two_column_box(guiutils.bold_label(_("End:")), gtk.Label(end_str), LEFT_WIDTH)
    row6 = guiutils.get_two_column_box(guiutils.bold_label(_("Frames Per Second:")), gtk.Label(str(render_item.render_data.fps)), LEFT_WIDTH)
    row7 = guiutils.get_two_column_box(guiutils.bold_label(_("Render Profile Name:")), gtk.Label(str(render_item.render_data.profile_name)), LEFT_WIDTH)
    row8 = guiutils.get_two_column_box(guiutils.bold_label(_("Render Profile:")), gtk.Label(render_item.render_data.profile_desc), LEFT_WIDTH)

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(gtk.Label(render_item.get_display_name()), False, False, 0)
    vbox.pack_start(guiutils.get_pad_label(12, 16), False, False, 0)
    vbox.pack_start(row0, False, False, 0)
    vbox.pack_start(row1, False, False, 0)
    vbox.pack_start(row2, False, False, 0)
    vbox.pack_start(row3, False, False, 0)
    vbox.pack_start(row4, False, False, 0)
    vbox.pack_start(row5, False, False, 0)
    vbox.pack_start(row6, False, False, 0)
    vbox.pack_start(row7, False, False, 0)
    vbox.pack_start(row8, False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)

    title = _("Render Properties")
    dialogutils.panel_ok_dialog(title, vbox)
    
def display_render_item_popup_menu(callback, event):
    menu = gtk.Menu()
    menu.add(_get_menu_item(_("Save Item Project As..."), callback,"saveas"))
    menu.add(_get_menu_item(_("Render Properties"), callback,"renderinfo")) 
    _add_separetor(menu)
    menu.add(_get_menu_item(_("Delete"), callback,"delete"))
    menu.popup(None, None, None, event.button, event.time)
    
def _add_separetor(menu):
    sep = gtk.SeparatorMenuItem()
    sep.show()
    menu.add(sep)

def _get_menu_item(text, callback, data, sensitive=True):
    item = gtk.MenuItem(text)
    item.connect("activate", callback, data)
    item.show()
    item.set_sensitive(sensitive)
    return item
