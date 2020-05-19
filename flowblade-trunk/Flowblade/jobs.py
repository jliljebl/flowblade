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


from gi.repository import Gtk, GLib, Gdk
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
import proxyheadless
import respaths
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


class JobProxy: # Background renders provide these to give info on render status.
                  # Modules doing the rendering must manage setting all values.

    def __init__(self, uid, callback_object):
        self.proxy_uid = uid # modules doing the rendering and using this to display must make sure this matches always for a particular job
        self.type = NOT_SET_YET 
        self.status = RENDERING
        self.progress = 0.0 # 0.0. - 1.0
        self.text = ""
        self.elapsed = 0.0 # in fractional seconds

        # callback_object reqiured to implement interface:
        #     start_render()
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

def update_job_queue(update_msg_job_proxy): # We're using JobProxy objects as messages to update values on jobs in _jobs list.
    global _jobs_list_view, _remove_list
    row = -1
    job_proxy = None  
    for i in range (0, len(_jobs)):

        if _jobs[i].proxy_uid == update_msg_job_proxy.proxy_uid:
            if _jobs[i].status == CANCELLED:
                return # it is maybe possible to get update attempt here after cancellation.         
            # Update job proxy info and remember row
            row = i
            break

    if row == -1:
        # Something is wrong.
        print("trying to update non-existing job at jobs.show_message()!")
        return

    # Copy values
    _jobs[row].text = update_msg_job_proxy.text
    _jobs[row].elapsed = update_msg_job_proxy.elapsed
    _jobs[row].progress = update_msg_job_proxy.progress

    if update_msg_job_proxy.status == COMPLETED:
        _jobs[row].status = COMPLETED
        _jobs[row].text = _("Completed")
        _jobs[row].progress = 1.0
        _remove_list.append(_jobs[row])
        GObject.timeout_add(4000, _remove_jobs)
        waiting_jobs = _get_jobs_with_status(QUEUED)
        if len(waiting_jobs) > 0:
            waiting_jobs[0].start_render()
    else:
        _jobs[row].status = update_msg_job_proxy.status

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
    global _jobs_list_view #, widgets

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


# ----------------------------------------------------------------- polling
class ContainerStatusPollingThread(threading.Thread):
    
    def __init__(self):
        # poll_objects required to implement interface:
        #     update_render_status()
        #     get_proxy_uuid()
        #     abort_render()
        self.poll_objects = []
        self.abort = False

        threading.Thread.__init__(self)

    def run(self):
        
        while self.abort == False:
            for poll_obj in self.poll_objects:
                poll_obj.update_render_status() # make sure methids enter/exit Gtk threads
                    
                
            time.sleep(0.5)

    def remove_poll_object_for_matching_job_proxy(self, job_proxy):
        for poll_obj in self.poll_objects:
            if poll_obj.get_proxy_uuid() == job_proxy.proxy_uid:
                self.poll_objects.remove(poll_obj)
                
    def shutdown(self):
        for poll_obj in self.poll_objects:
            poll_obj.abort_render()
        
        self.abort = True

def add_as_status_polling_object(polling_object):
    global _status_polling_thread
    if _status_polling_thread == None:
        _status_polling_thread = ContainerStatusPollingThread()
        _status_polling_thread.start()
               
    _status_polling_thread.poll_objects.append(polling_object)

def remove_as_status_polling_object(polling_object):
    try:
        _status_polling_thread.poll_objects.remove(polling_object)
    except:
        print("remove_as_status_polling_object Except for", polling_object)
        pass

def shutdown_polling():
    if _status_polling_thread == None:
        return
    
    _status_polling_thread.shutdown()


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
        _jobs.remove(job)
        _status_polling_thread.remove_poll_object_for_matching_job_proxy(job)

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
# These objects satisfy two interfaces:
#
# As jobs.JobProxy callback_objects :
#
#     start_render()
#     abort_render()
# 
# As objects in ContainerStatusPollingThread,poll_objects they implement interface:
#     update_render_status()
#     abort_render()
# 
# Objects extending containeraction.AbstractContainerActionObject in module containeractions.py
# implement these interfaces too.


class AbstractJobQueueObject:
    
    def __init__(self, session_id, job_type):
        self.session_id = session_id
        self.job_type = job_type

    def get_proxy_uuid(self):
        return self.get_session_id()

    def get_session_id(self):
        return self.session_id
        
    def get_job_name(self):
        return "job name"
    
    def add_to_queue(self):
        add_job(self.get_launch_job_proxy())
        add_as_status_polling_object(self)

    def get_job_proxy(self):
        job_proxy = JobProxy(self.get_session_id(), self)
        job_proxy.type = self.job_type
        return job_proxy
    
    def get_launch_job_proxy(self):
        job_proxy = self.get_job_proxy()
        job_proxy.status = QUEUED
        job_proxy.progress = 0.0
        job_proxy.elapsed = 0.0 # jobs does not use this value
        job_proxy.text = _("In Queue - ") + " " + self.get_job_name()
        return job_proxy
        
    def get_completed_job_proxy(self):
        job_proxy = self.get_job_proxy()
        job_proxy.status = COMPLETED
        job_proxy.progress = 1.0
        job_proxy.elapsed = 0.0 # jobs does not use this value
        job_proxy.text = "dummy" # this will be overwritten with completion message
        return job_proxy


class MotionRenderJobQueueObject(AbstractJobQueueObject):

    def __init__(self, session_id, write_file, args):
        
        AbstractJobQueueObject.__init__(self, session_id, MOTION_MEDIA_ITEM_RENDER)
        
        self.write_file = write_file
        self.args = args

    def get_job_name(self):
        folder, file_name = os.path.split(self.write_file)
        return file_name
        
    def start_render(self):
        
        job_proxy = self.get_job_proxy()
        job_proxy.text = _("Render Starting...")
        job_proxy.status = RENDERING
        update_job_queue(job_proxy)
        
        # Run with nice to lower priority if requested (currently hard coded to lower)
        nice_command = "nice -n " + str(10) + " " + respaths.LAUNCH_DIR + "flowblademotionheadless"
        for arg in self.args:
            nice_command += " "
            nice_command += arg

        subprocess.Popen([nice_command], shell=True)

    def update_render_status(self):

        Gdk.threads_enter()
                    
        if motionheadless.session_render_complete(self.get_session_id()) == True:
            remove_as_status_polling_object(self)
            
            job_proxy = self.get_completed_job_proxy()
            update_job_queue(job_proxy)
            
            motionheadless.delete_session_folders(self.get_session_id())
            
            GLib.idle_add(self.create_media_item)

        else:
            status = motionheadless.get_session_status(self.get_session_id())
            if status != None:
                fraction, elapsed = status

                msg = _("Rendering Motion Clip ") + self.get_job_name()
                
                job_proxy = self.get_job_proxy()
                
                job_proxy.progress = float(fraction)
                if job_proxy.progress > 1.0:
                    # hack to fix how progress is calculated in gmicheadless because producers can render a bit longer then required.
                    job_proxy.progress = 1.0

                job_proxy.elapsed = float(elapsed)
                job_proxy.text = msg
                
                update_job_queue(job_proxy)
            else:
                print("MotionRenderQueueObject status none")
                pass # This can happen sometimes before gmicheadless.py has written a status message, we just do nothing here.

        Gdk.threads_leave()
    
    def abort_render(self):
        remove_as_status_polling_object(self)
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
        job_proxy = self.get_job_proxy()
        job_proxy.text = _("Render Starting...")
        job_proxy.status = RENDERING
        update_job_queue(job_proxy)
        
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
            remove_as_status_polling_object(self)
            
            job_proxy = self.get_completed_job_proxy()
            update_job_queue(job_proxy)
            self.completed_job_proxy = job_proxy
            
            proxyheadless.delete_session_folders(self.get_session_id()) # these were created mltheadlessutils.py, see proxyheadless.py
            
            GLib.idle_add(self.proxy_render_complete)

        else:
            status = proxyheadless.get_session_status(self.get_session_id())
            if status != None:
                fraction, elapsed = status

                msg = _("Rendering Proxy Clip for ") + self.get_job_name()
                
                job_proxy = self.get_job_proxy()
                
                job_proxy.progress = float(fraction)
                if job_proxy.progress > 1.0:
                    # hack to fix how progress is calculated in gmicheadless because producers can render a bit longer then required.
                    job_proxy.progress = 1.0

                job_proxy.elapsed = float(elapsed)
                job_proxy.text = msg
                
                update_job_queue(job_proxy)
            else:
                print("ProxyRenderJobQueueObject status none", self.get_job_name())
                pass

        Gdk.threads_leave()
    
    def abort_render(self):
        remove_as_status_polling_object(self)
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

