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


from gi.repository import Gtk, GLib, Gdk, GdkPixbuf
from gi.repository import GObject
from gi.repository import Pango

import copy
import os
import subprocess
import time
import threading

import appconsts
import editorpersistance
from editorstate import PROJECT
import gui
import guicomponents
import guiutils
import motionheadless
import persistance
import proxyheadless
import respaths
import userfolders
import utils

QUEUED = 0
RENDERING = 1
COMPLETED = 2
CANCELLED = 3

NOT_SET_YET = 0
CONTAINER_CLIP_RENDER_GMIC = 1
CONTAINER_CLIP_RENDER_MLT_XML = 2
CONTAINER_CLIP_RENDER_BLENDER = 3
MOTION_MEDIA_ITEM_RENDER = 4
PROXY_RENDER = 5

open_media_file_callback = None

_status_polling_thread = None

_hamburger_menu = Gtk.Menu()

_jobs_list_view = None

_jobs = [] # proxy objects that represent background renders and provide info on render status.

_remove_list = [] # objects are removed from GUI with delay to give user time to notice copmpletion

jobs_notebook_index = 4 # 4 for single window, app.py sets to 3 for two windows

_jobs_render_progress_window = None


class JobProxy: # This object represnts job in job queue. 


    def __init__(self, uid, callback_object):
        self.proxy_uid = uid
        self.type = NOT_SET_YET 
        self.status = RENDERING
        self.progress = 0.0 # 0.0. - 1.0
        self.text = ""
        self.elapsed = 0.0 # in fractional seconds

        # callback_object have to implement interface:
        #     start_render()
        #     update_render_status()
        #     abort_render()
        self.callback_object = callback_object

    def get_elapsed_str(self):
        return utils.get_time_str_for_sec_float(self.elapsed)

    def get_type_str(self):
        if self.type == NOT_SET_YET:
            return "NO TYPE SET" # this just error info, application has done something wrong.
        elif self.type == CONTAINER_CLIP_RENDER_GMIC:
            return _("G'Mic Clip")
        elif self.type == CONTAINER_CLIP_RENDER_MLT_XML:
            return _("Selection Clip")
        elif self.type == CONTAINER_CLIP_RENDER_BLENDER:
            return _("Blender Clip")
        elif self.type == MOTION_MEDIA_ITEM_RENDER:
            return _("Motion Clip")
        elif self.type == PROXY_RENDER:
            return _("Proxy Clip")
            
    def get_progress_str(self):
        if self.progress < 0.0:
            return "-"
        return str(int(self.progress * 100.0)) + "%"

    def start_render(self):
        self.callback_object.start_render()
        
    def abort_render(self):
        self.callback_object.abort_render()


class JobQueueMessage:  # Jobs communicate with job queue by sending these objecs.
    
    def __init__(self, uid, job_type, status, progress, text, elapsed):
        self.proxy_uid = uid       
        self.type = job_type 
        self.status = status
        self.progress = progress
        self.text = text
        self.elapsed = elapsed

                  
#---------------------------------------------------------------- interface
def add_job(job_proxy):
    global _jobs, _jobs_list_view 
    _jobs.append(job_proxy)
    _jobs_list_view.fill_data_model()
    if editorpersistance.prefs.open_jobs_panel_on_add == True:
        gui.middle_notebook.set_current_page(jobs_notebook_index)
    
    if editorpersistance.prefs.render_jobs_sequentially == False: # Feature not active for first release 2.6.
        job_proxy.start_render()
    else:
         running = _get_jobs_with_status(RENDERING)
         if len(running) == 0:
             job_proxy.start_render()

    # Get polling going if needed.
    global _status_polling_thread
    if _status_polling_thread == None:
        _status_polling_thread = ContainerStatusPollingThread()
        _status_polling_thread.start()

def update_job_queue(job_msg): # We're using JobProxy objects as messages to update values on jobs in _jobs list.
    global _jobs_list_view, _remove_list
    row = -1
    job_proxy = None  
    for i in range (0, len(_jobs)):

        if _jobs[i].proxy_uid == job_msg.proxy_uid:
            if _jobs[i].status == CANCELLED:
                return # it is maybe possible to get update attempts here after cancellation.         
            # Remember job row
            row = i
            break

    if row == -1:
        # Something is wrong.
        print("trying to update non-existing job at jobs.show_message()!")
        return

    # Copy values
    _jobs[row].text = job_msg.text
    _jobs[row].elapsed = job_msg.elapsed
    _jobs[row].progress = job_msg.progress

    if job_msg.status == COMPLETED:
        _jobs[row].status = COMPLETED
        _jobs[row].text = _("Completed")
        _jobs[row].progress = 1.0
        _remove_list.append(_jobs[row])
        GObject.timeout_add(4000, _remove_jobs)
        waiting_jobs = _get_jobs_with_status(QUEUED)
        if len(waiting_jobs) > 0:
            waiting_jobs[0].start_render()
    else:
        _jobs[row].status = job_msg.status

    tree_path = Gtk.TreePath.new_from_string(str(row))
    store_iter = _jobs_list_view.storemodel.get_iter(tree_path)

    _jobs_list_view.storemodel.set_value(store_iter, 0, _jobs[row].get_type_str())
    _jobs_list_view.storemodel.set_value(store_iter, 1, _jobs[row].text)
    _jobs_list_view.storemodel.set_value(store_iter, 2, _jobs[row].get_elapsed_str())
    _jobs_list_view.storemodel.set_value(store_iter, 3, _jobs[row].get_progress_str())

    _jobs_list_view.scroll.queue_draw()

def get_jobs_of_type(job_type):
    jobs_of_type = []
    for job in _jobs:
        job.type = job_type
        jobs_of_type.append(job)
    
    return jobs_of_type

def proxy_render_ongoing():
    proxy_jobs = get_jobs_of_type(PROXY_RENDER)
    if len(proxy_jobs) == 0:
        return False
    else:
        return True

def create_jobs_list_view():
    global _jobs_list_view
    _jobs_list_view = JobsQueueView()
    return _jobs_list_view

def get_jobs_panel():
    global _jobs_list_view

    actions_menu = guicomponents.HamburgerPressLaunch(_menu_action_pressed)
    guiutils.set_margins(actions_menu.widget, 8, 2, 2, 18)

    row2 =  Gtk.HBox()
    row2.pack_start(actions_menu.widget, False, True, 0)
    row2.pack_start(Gtk.Label(), True, True, 0)

    panel = Gtk.VBox()
    panel.pack_start(_jobs_list_view, True, True, 0)
    panel.pack_start(row2, False, True, 0)
    panel.set_size_request(400, 10)

    return panel





# ------------------------------------------------------------- module functions
def _menu_action_pressed(widget, event):
    menu = _hamburger_menu
    guiutils.remove_children(menu)
    menu.add(guiutils.get_menu_item(_("Cancel Selected Render"), _hamburger_item_activated, "cancel_selected"))
    menu.add(guiutils.get_menu_item(_("Cancel All Renders"), _hamburger_item_activated, "cancel_all"))
    
    guiutils.add_separetor(menu)

    """ Not settable for 2.6, let's see later
    sequential_render_item = Gtk.CheckMenuItem()
    sequential_render_item.set_label(_("Render All Jobs Sequentially"))
    sequential_render_item.set_active(editorpersistance.prefs.render_jobs_sequentially)
    sequential_render_item.connect("activate", _hamburger_item_activated, "sequential_render")
    menu.add(sequential_render_item)
    """
    
    open_on_add_item = Gtk.CheckMenuItem()
    open_on_add_item.set_label(_("Show Jobs Panel on Adding New Job"))
    open_on_add_item.set_active(editorpersistance.prefs.open_jobs_panel_on_add)
    open_on_add_item.connect("activate", _hamburger_item_activated, "open_on_add")
    menu.add(open_on_add_item)
    
    menu.show_all()
    menu.popup(None, None, None, None, event.button, event.time)

def _hamburger_item_activated(widget, msg):
    if msg == "cancel_all":
        global _jobs, _remove_list
        _remove_list = []
        for job in _jobs:
            if job.status == RENDERING:
                job.abort_render()
            job.progress = -1.0
            job.text = _("Cancelled")
            job.status = CANCELLED
            _remove_list.append(job)

        _jobs_list_view.fill_data_model()
        _jobs_list_view.scroll.queue_draw()
        GObject.timeout_add(4000, _remove_jobs)

    elif msg == "cancel_selected":
        try:
            jobs_list_index = _jobs_list_view.get_selected_row_index()
        except:
            return # nothing was selected
        
        job = _jobs[jobs_list_index]
        job.abort_render()
        job.progress = -1.0
        job.text = _("Cancelled")
        job.status = CANCELLED
        _remove_list.append(job)

        _jobs_list_view.fill_data_model()
        _jobs_list_view.scroll.queue_draw()
        GObject.timeout_add(4000, _remove_jobs)
        
    elif msg == "open_on_add":
        editorpersistance.prefs.open_jobs_panel_on_add = widget.get_active()
        editorpersistance.save()

    elif msg == "sequential_render":
        editorpersistance.prefs.render_jobs_sequentially = widget.get_active()
        editorpersistance.save()

def _get_jobs_with_status(status):
    running = []
    for job in _jobs:
        if job.status == status:
            running.append(job)
    
    return running

def _remove_jobs():
    global _jobs, _remove_list
    for  job in _remove_list:
        if job in _jobs:
            _jobs.remove(job)
        else:
            # We're getting attemps from container actions to release multiple times, find out why sometime.
            pass

    _jobs_list_view.fill_data_model()
    _jobs_list_view.scroll.queue_draw()

    _remove_list = []


# --------------------------------------------------------- GUI 
class JobsQueueView(Gtk.VBox):

    def __init__(self):
        GObject.GObject.__init__(self)
        
        self.storemodel = Gtk.ListStore(str, str, str, str)
        
        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

        # View
        self.treeview = Gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(True)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", Pango.EllipsizeMode.END)

        self.text_rend_2 = Gtk.CellRendererText()
        self.text_rend_2.set_property("yalign", 0.0)
        self.text_rend_2.set_property("ellipsize", Pango.EllipsizeMode.END)
        
        self.text_rend_3 = Gtk.CellRendererText()
        self.text_rend_3.set_property("yalign", 0.0)
        
        self.text_rend_4 = Gtk.CellRendererText()
        self.text_rend_4.set_property("yalign", 0.0)

        # Column views
        self.text_col_1 = Gtk.TreeViewColumn(_("Job Type"))
        self.text_col_2 = Gtk.TreeViewColumn(_("Info"))
        self.text_col_3 = Gtk.TreeViewColumn(_("Render Time"))
        self.text_col_4 = Gtk.TreeViewColumn(_("Progress"))

        #self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        self.text_col_1.set_min_width(200)
        self.text_col_1.pack_start(self.text_rend_1, True)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 0) # <- note column index

        self.text_col_2.set_expand(True)
        self.text_col_2.pack_start(self.text_rend_2, True)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 1)
        self.text_col_2.set_min_width(90)

        self.text_col_3.set_expand(False)
        self.text_col_3.pack_start(self.text_rend_3, True)
        self.text_col_3.add_attribute(self.text_rend_3, "text", 2)

        self.text_col_4.set_expand(False)
        self.text_col_4.pack_start(self.text_rend_4, True)
        self.text_col_4.add_attribute(self.text_rend_4, "text", 3)

        # Add column views to view
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)
        self.treeview.append_column(self.text_col_3)
        self.treeview.append_column(self.text_col_4)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()
        self.show_all()

    def get_selected_row_index(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return int(rows[0].to_string ())
        
    def fill_data_model(self):
        self.storemodel.clear()        
        
        for job in _jobs:
            row_data = [job.get_type_str(),
                        job.text,
                        job.get_elapsed_str(),
                        job.get_progress_str()]
            self.storemodel.append(row_data)
            self.scroll.queue_draw()



# ------------------------------------------------------------------------------- JOBS QUEUE OBJECTS
# These objects satisfy combined interface as jobs.JobProxy callback_objects and as update polling objects.
#
#     start_render()
#     update_render_status()
#     abort_render()
# 
# ------------------------------------------------------------------------------- JOBS QUEUE OBJECTS


class AbstractJobQueueObject(JobProxy):
    
    def __init__(self, session_id, job_type):
        self.session_id = session_id 
        JobProxy.__init__(self, session_id, self)

        self.type = job_type

    def get_session_id(self):
        return self.session_id
        
    def get_job_name(self):
        return "job name"
    
    def add_to_queue(self):
        add_job(self.create_job_queue_proxy())

    def get_job_queue_message(self):
        job_queue_message = JobQueueMessage(self.proxy_uid, self.type, self.status,
                                            self.progress, self.text, self.elapsed)
        return job_queue_message

    def create_job_queue_proxy(self):
        self.status = QUEUED
        self.progress = 0.0
        self.elapsed = 0.0 # jobs does not use this value
        self.text = _("In Queue - ") + " " + self.get_job_name()
        return self
        
    def get_completed_job_message(self):
        job_queue_message = self.get_job_queue_message()
        job_queue_message.status = COMPLETED
        job_queue_message.progress = 1.0
        job_queue_message.elapsed = 0.0 # jobs does not use this value
        job_queue_message.text = "dummy" # this will be overwritten with completion message
        return job_queue_message



class MotionRenderJobQueueObject(AbstractJobQueueObject):

    def __init__(self, session_id, write_file, args):
        
        AbstractJobQueueObject.__init__(self, session_id, MOTION_MEDIA_ITEM_RENDER)
        
        self.write_file = write_file
        self.args = args

    def get_job_name(self):
        folder, file_name = os.path.split(self.write_file)
        return file_name
        
    def start_render(self):
        
        job_msg = self.get_job_queue_message()
        job_msg.text = _("Render Starting...")
        job_msg.status = RENDERING
        update_job_queue(job_msg)
        
        # Run with nice to lower priority if requested (currently hard coded to lower)
        nice_command = "nice -n " + str(10) + " " + respaths.LAUNCH_DIR + "flowblademotionheadless"
        for arg in self.args:
            nice_command += " "
            nice_command += arg

        subprocess.Popen([nice_command], shell=True)

    def update_render_status(self):

        Gdk.threads_enter()
                    
        if motionheadless.session_render_complete(self.get_session_id()) == True:
            #remove_as_status_polling_object(self)
            
            job_msg = self.get_completed_job_message()
            update_job_queue(job_msg)
            
            motionheadless.delete_session_folders(self.get_session_id())
            
            GLib.idle_add(self.create_media_item)

        else:
            status = motionheadless.get_session_status(self.get_session_id())
            if status != None:
                fraction, elapsed = status
                
                self.progress = float(fraction)
                if self.progress > 1.0:
                    # A fix for how progress is calculated in gmicheadless because producers can render a bit longer then required.
                    self.progress = 1.0

                self.elapsed = float(elapsed)
                self.text = _("Rendering Motion Clip ") + self.get_job_name()
                
                job_msg = self.get_job_queue_message()
                
                update_job_queue(job_msg)
            else:
                # Process start/stop on their own and we hit trying to get non-existing status for e.g completed renders.
                pass

        Gdk.threads_leave()
    
    def abort_render(self):
        #remove_as_status_polling_object(self)
        motionheadless.abort_render(self.get_session_id())
        
    def create_media_item(self):
        open_media_file_callback(self.write_file)
 

class ProxyRenderJobQueueObject(AbstractJobQueueObject):

    def __init__(self, session_id, render_data):
        
        AbstractJobQueueObject.__init__(self, session_id, PROXY_RENDER)
        
        self.render_data = render_data

    def get_job_name(self):
        folder, file_name = os.path.split(self.render_data.media_file_path)
        return file_name
        
    def start_render(self):
        job_msg = self.get_job_queue_message()
        job_msg.text = _("Render Starting...")
        job_msg.status = RENDERING
        update_job_queue(job_msg)
        
        # Run with nice to lower priority if requested (currently hard coded to lower)
        nice_command = "nice -n " + str(10) + " " + respaths.LAUNCH_DIR + "flowbladeproxyheadless"
        args = self.render_data.get_data_as_args_tuple()
        for arg in args:
            nice_command += " "
            nice_command += arg

        session_arg = "session_id:" + str(self.session_id)
        nice_command += " "
        nice_command += session_arg
                
        subprocess.Popen([nice_command], shell=True)

    def update_render_status(self):

        Gdk.threads_enter()
                    
        if proxyheadless.session_render_complete(self.get_session_id()) == True:
            #remove_as_status_polling_object(self)
            
            job_msg = self.get_completed_job_message()
            update_job_queue(job_msg)
            
            proxyheadless.delete_session_folders(self.get_session_id()) # these were created mltheadlessutils.py, see proxyheadless.py
            
            GLib.idle_add(self.proxy_render_complete)

        else:
            status = proxyheadless.get_session_status(self.get_session_id())
            if status != None:
                fraction, elapsed = status
                
                self.progress = float(fraction)
                if self.progress > 1.0:
                    self.progress = 1.0

                self.elapsed = float(elapsed)
                self.text = _("Rendering Proxy Clip for ") + self.get_job_name()

                job_msg = self.get_job_queue_message()
                
                update_job_queue(job_msg)
            else:
                # Process start/stop on their own and we hit trying to get non-existing status for e.g completed renders.
                pass

        Gdk.threads_leave()
    
    def abort_render(self):
        # remove_as_status_polling_object(self)
        motionheadless.abort_render(self.get_session_id())
        
    def proxy_render_complete(self):
        try:
            media_file = PROJECT().media_files[self.render_data.media_file_id]
        except:
            # User has deleted media file before proxy render complete
            return

        media_file.add_proxy_file(self.render_data.proxy_file_path)

        if PROJECT().proxy_data.proxy_mode == appconsts.USE_PROXY_MEDIA: # When proxy mode is USE_PROXY_MEDIA all proxy files are used all the time
            media_file.set_as_proxy_media_file()
        
            # if the rendered proxy file was the last proxy file being rendered,
            # auto re-convert to update proxy clips.
            proxy_jobs = get_jobs_of_type(PROXY_RENDER)
            if len(proxy_jobs) == 0:
                self.render_data.do_auto_re_convert_func()
            elif len(proxy_jobs) == 1:
                self.render_data.do_auto_re_convert_func()



# ----------------------------------------------------------------- polling
class ContainerStatusPollingThread(threading.Thread):
    
    def __init__(self):

        self.abort = False

        threading.Thread.__init__(self)

    def run(self):

        while self.abort == False:
            for job in _jobs:
                if job.status != QUEUED:
                    job.callback_object.update_render_status() # Make sure these methods enter/exit Gtk threads.

            if _jobs_render_progress_window != None and len(_jobs) != 0:
                _jobs_render_progress_window.update_render_progress()
            elif _jobs_render_progress_window != None and len(_jobs) == 0:
                _jobs_render_progress_window.jobs_completed()
                self.abort = True
                
            time.sleep(0.5)

    def shutdown(self):
        for job in _jobs:
            job.abort_render()
        
        self.abort = True

def shutdown_polling():
    if _status_polling_thread == None:
        return
    
    _status_polling_thread.shutdown()



# --------------------------------------------------------------- post-close jobs progress 
def handle_shutdown(autosave_file):
    # Called just before maybe calling Gtk.main_quit() on app shutdown.
    if len(_jobs) == 0:
        # Shutdown polling thread, no jobs so no aborts are done.
        shutdown_polling()
        return True # Do Gtk.main_quit()
        
    else:
        # Unfinished jobs, launch progress window to info user after main app closed.
        global _jobs_render_progress_window
        _jobs_render_progress_window = JobsRenderProgressWindow(autosave_file)
        return False  # Do NOT do Gtk.main_quit()

class JobsRenderProgressWindow:

    def __init__(self, autosave_file):
        
        # Window
        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.connect("delete-event", lambda w, e:self.close_window())
        app_icon = GdkPixbuf.Pixbuf.new_from_file(respaths.IMAGE_PATH + "flowbladebatchappicon.png")
        self.window.set_icon(app_icon)
        
        self.last_saved_job = None
        self.start_time = time.monotonic()
        self.autosave_file = autosave_file
        
        self.render_progress_bar = Gtk.ProgressBar()
        self.render_progress_bar.set_text("0 %")
        
        prog_align = guiutils.set_margins(self.render_progress_bar, 0, 0, 6, 0)
        prog_align.set_size_request(550, 30)
        self.elapsed_value = Gtk.Label()
        self.current_render_value = Gtk.Label()
        self.items_value = Gtk.Label()
        
        est_label = guiutils.get_right_justified_box([guiutils.bold_label(_("Elapsed:"))])
        items_label = guiutils.get_right_justified_box([guiutils.bold_label(_("Jobs Remaining Item:"))])
        current_label = guiutils.get_right_justified_box([guiutils.bold_label(_("Current Job:"))])

        est_label.set_size_request(250, 20)
        current_label.set_size_request(250, 20)
        items_label.set_size_request(250, 20)

        self.status_label = Gtk.Label()
        self.status_label.set_text(_("Rendering"))
        cancel_button = Gtk.Button(_("Cancel All Jobs"))
        
        control_row = Gtk.HBox(False, 0)
        control_row.pack_start(self.status_label, False, False, 0)
        control_row.pack_start(Gtk.Label(), True, True, 0)
        control_row.pack_start(cancel_button, False, False, 0)
        
        info_vbox = Gtk.VBox(False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([est_label, self.elapsed_value]), False, False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([items_label, self.items_value]), False, False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([current_label, self.current_render_value]), False, False, 0)

        progress_vbox = Gtk.VBox(False, 2)
        progress_vbox.pack_start(info_vbox, False, False, 0)
        progress_vbox.pack_start(guiutils.get_pad_label(10, 8), False, False, 0)
        progress_vbox.pack_start(prog_align, False, False, 0)
        progress_vbox.pack_start(control_row, False, False, 0)

        alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)
        alignment.show_all()

        # Set pane and show window
        self.window.add(alignment)
        self.window.set_title(_("Jobs Render Progress"))
        self.window.set_position(Gtk.WindowPosition.CENTER)  
        self.window.show_all()
    
    def jobs_completed(self):
        self.close_window()

    def update_render_progress(self):
        job = _jobs[0]
        
        if job.status == COMPLETED and self.last_saved_job != id(job):
            
            Gdk.threads_enter()
            self.status_label.set_text(_("Saving..."))
            Gdk.threads_leave()
            
            self.last_saved_job = id(job)
            self.save_project()
        else:
            Gdk.threads_enter()
            self.status_label.set_text(_("Rendering"))
            Gdk.threads_leave()
            
        Gdk.threads_enter()

        elapsed = time.monotonic() - self.start_time
        elapsed_str= "  " + utils.get_time_str_for_sec_float(elapsed)
        self.elapsed_value .set_text(elapsed_str)
        self.current_render_value.set_text(" " + job.text)
        self.items_value.set_text( " " + str(len(_jobs)))
        self.render_progress_bar.set_fraction(job.progress)
        self.render_progress_bar.set_text(str(int(job.progress * 100)) + " %")

        Gdk.threads_leave()
    
    def save_project(self):
        persistance.show_messages = False
        if PROJECT().last_save_path != None:
            save_path = PROJECT().last_save_path 
        else:
            save_path = userfolders.get_cache_dir() +  self.autosave_file # if user didn't save before exit, save in autosave file to preserve render work somehow.
        
        print("saving", save_path)
        persistance.save_project(PROJECT(), save_path)
            
    def close_window(self):
        if len(_jobs) != 0:
            shutdown_polling()
        else:
            _status_polling_thread.abort = True

        self.status_label.set_text(_("Renders Complete."))
        self.save_project()
            
        Gtk.main_quit()
