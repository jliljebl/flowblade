"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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


from gi.repository import Gtk, GLib
from gi.repository import GObject
from gi.repository import Pango

import os
import subprocess
import sys
import time
import threading
try:
    import mlt7 as mlt
except:
    import mlt

import appconsts
import callbackbridge
import editorlayout
import editorpersistance
from editorstate import PROJECT
import guicomponents
import guipopover
import guiutils
import motionheadless
import proxyheadless
import renderconsumer
import respaths
import stabilizeheadless
import stabilizedvideoheadless
import trackingheadless
import userfolders
import utils

QUEUED = 0
RENDERING = 1
COMPLETED = 2
CANCELLED = 3

NOT_SET_YET = 0
CONTAINER_CLIP_RENDER_GMIC = 1
CONTAINER_CLIP_RENDER_MLT_XML = 2
CONTAINER_CLIP_RENDER_BLENDER = 3 # Deprecated
MOTION_MEDIA_ITEM_RENDER = 4
PROXY_RENDER = 5
CONTAINER_CLIP_RENDER_FLUXITY = 6
STABILIZE_DATA_RENDER = 7
MOTION_TRACKING_DATA_RENDER = 8
STABILIZED_MEDIA_ITEM_RENDER = 9

FFMPEG_ATTR_SOURCEFILE = "%SOURCEFILE"
FFMPEG_ATTR_SCREENSIZE = "%SCREENSIZE"
FFMPEG_ATTR_SCREENSIZE_2 = "%SCREEN%SIZE%TWO%"
FFMPEG_ATTR_PROXYFILE = "%PROXYFILE"

_status_polling_thread = None

_jobs_list_view = None

_jobs = [] # proxy objects that represent background renders and provide info on render status.
_remove_list = [] # objects are removed from GUI with delay to give user time to notice copmpletion

_jobs_render_progress_window = None


class JobProxy: # This object represents a job in the job queue. 


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
    
    def get_progress_str(self):
        if self.progress < 0.0:
            return "-"
        return str(int(self.progress * 100.0)) + "%"

    def start_render(self):
        self.callback_object.start_render()
        
    def abort_render(self):
        self.callback_object.abort_render()


class JobQueueMessage:  # Jobs communicate with job queue by sending these objects.
    
    def __init__(self, uid, job_type, status, progress, text, elapsed):
        self.proxy_uid = uid       
        self.type = job_type 
        self.status = status
        self.progress = progress
        self.text = text
        self.elapsed = elapsed

class ProcessCommandListRunner(threading.Thread):
    def __init__(self, command_list):
        threading.Thread.__init__(self)
        self.command_list = command_list
        
    def run(self):
        process = subprocess.Popen(self.command_list)
        process.wait()

#---------------------------------------------------------------- interface
def add_job(job_proxy):
    global _jobs, _jobs_list_view 
    _jobs.append(job_proxy)
    _jobs_list_view.fill_data_model(_jobs)
    if editorpersistance.prefs.open_jobs_panel_on_add == True:
        editorlayout.show_panel(appconsts.PANEL_JOBS)
    
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
        GLib.timeout_add(4000, _remove_jobs)
        waiting_jobs = _get_jobs_with_status(QUEUED)
        if len(waiting_jobs) > 0:
            waiting_jobs[0].start_render()
    else:
        _jobs[row].status = job_msg.status

    _jobs_list_view.update_row(row, _jobs)

def _cancel_all_jobs():
    global _jobs, _remove_list
    _remove_list = []
    for job in _jobs:
        if job.status == RENDERING:
            job.abort_render()
        job.progress = -1.0
        job.text = _("Cancelled")
        job.status = CANCELLED
        _remove_list.append(job)

    _jobs_list_view.fill_data_model(_jobs)
    GLib.timeout_add(4000, _remove_jobs)
        
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
    _jobs_list_view = guicomponents.JobsQueueView()
    return _jobs_list_view

def get_jobs_panel():
    global _jobs_list_view

    actions_menu = guicomponents.HamburgerPressLaunch(_menu_action_pressed)
    actions_menu.do_popover_callback = True
    guiutils.set_margins(actions_menu.widget, 8, 2, 2, 18)

    row2 =  Gtk.HBox()
    row2.pack_start(actions_menu.widget, False, True, 0)
    row2.pack_start(Gtk.Label(), True, True, 0)

    panel = Gtk.VBox()
    panel.pack_start(_jobs_list_view, True, True, 0)
    panel.pack_start(row2, False, True, 0)
            
    return panel

def get_active_jobs_count():
    return len(_jobs)



# ------------------------------------------------------------- module functions
def _menu_action_pressed(launcher, widget, event, data):
    guipopover.jobs_menu_popover_show(launcher, widget, _hamburger_item_activated)
    
def _hamburger_item_activated(action, variant, msg=None):
    global _jobs
        
    if msg == "cancel_all":
        _cancel_all_jobs()

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


        _jobs_list_view.fill_data_model(_jobs)
        GLib.timeout_add(4000, _remove_jobs)
        
    elif msg == "open_on_add":
        new_state = not(action.get_state().get_boolean())
        editorpersistance.prefs.open_jobs_panel_on_add = new_state
        editorpersistance.save()
        action.set_state(GLib.Variant.new_boolean(new_state))

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
            pass

    running = _get_jobs_with_status(RENDERING)
    if len(running) == 0:
        in_queue = _get_jobs_with_status(QUEUED)
        if len(in_queue) > 0:
            in_queue[0].start_render()

    _jobs_list_view.fill_data_model(_jobs)

    _remove_list = []


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

    def __init__(self, session_id, write_file, args, tline_clip_data=None):
        
        AbstractJobQueueObject.__init__(self, session_id, MOTION_MEDIA_ITEM_RENDER)
        
        self.write_file = write_file
        self.args = args
        self.parent_folder = userfolders.get_temp_render_dir() # THis is just used for message passing, output file goes where user decided.
        self.tline_clip_data = tline_clip_data

        # We are using same job object class to render slowmotion media items and 
        # slowmotion timeline clips, and need to do different things
        # when self.tline_clip_data != None and we are 
        # thus working on a timeline clip.
        if self.tline_clip_data != None:
            render_data, completed_callback = self.tline_clip_data
            clip, track, orig_file_path, slowmo_type, slowmo_clip_media_area, \
            speed, orig_media_in, orig_media_out, new_clip_in, new_clip_out = render_data
            self.target_clip = clip
                
    def get_job_name(self):
        folder, file_name = os.path.split(self.write_file)
        return file_name
        
    def start_render(self):
        job_msg = self.get_job_queue_message()
        job_msg.text = _("Render Starting...")
        job_msg.status = RENDERING
        update_job_queue(job_msg)
        
        # Create command list and launch process.
        command_list = [sys.executable]
        command_list.append(respaths.LAUNCH_DIR + "flowblademotionheadless")
        for arg in self.args:
            command_list.append(arg)
        parent_folder_arg = "parent_folder:" + str(self.parent_folder)
        command_list.append(parent_folder_arg)

        # We need to wait() in thread.
        command_list_runner = ProcessCommandListRunner(command_list)
        command_list_runner.start()
        
    def update_render_status(self):
        GLib.idle_add(self._update_from_gui_thread)
            
    def _update_from_gui_thread(self):

        if motionheadless.session_render_complete(self.parent_folder, self.get_session_id()) == True:
            job_msg = self.get_completed_job_message()
            update_job_queue(job_msg)
            
            if self.tline_clip_data != None:
                self.target_clip.render_progress = None
                callbackbridge.updater_repaint_tline()

            motionheadless.delete_session_folders(self.parent_folder, self.get_session_id())
            
            GLib.idle_add(self.create_media_item)

        else:
            status = motionheadless.get_session_status(self.parent_folder, self.get_session_id())

            if status != None:
                fraction, elapsed = status

                self.progress = float(fraction)
                if self.progress > 1.0:
                    # A fix for how progress is calculated in gmicheadless because producers can render a bit longer then required.
                    self.progress = 1.0

                if self.tline_clip_data != None:
                    self.target_clip.render_progress = self.progress
                    callbackbridge.updater_repaint_tline()

                self.elapsed = float(elapsed)
                self.text = _("Motion Clip Render") + " " + self.get_job_name()
                
                job_msg = self.get_job_queue_message()

                update_job_queue(job_msg)
            else:
                # Process start/stop on their own and we hit trying to get non-existing status for e.g completed renders.
                
                # This may not necessary to do here.
                if self.tline_clip_data != None:
                    self.target_clip.render_progress = None

    def abort_render(self):
        #remove_as_status_polling_object(self)
        if self.tline_clip_data != None:
            self.target_clip.render_progress = None
        motionheadless.abort_render(self.parent_folder, self.get_session_id())
        
    def create_media_item(self):
        if self.tline_clip_data == None:
            callbackbridge.projectaction_open_rendered_file(self.write_file)
        else:
            render_data, completed_callback = self.tline_clip_data
            completed_callback(render_data, self.write_file)



class StablizeDataRenderJobQueueObject(AbstractJobQueueObject):

    def __init__(self, session_id, filter, editable_properties, analyze_editor, args):
        
        AbstractJobQueueObject.__init__(self, session_id, STABILIZE_DATA_RENDER)
        
        self.analyze_editor = analyze_editor
        self.filter = filter
        self.editable_properties = editable_properties
        self.args = args
        self.parent_folder = userfolders.get_temp_render_dir() # This is used for message passing, output file goes to path given by 'write_file'.
        
    def start_render(self):
        
        job_msg = self.get_job_queue_message()
        job_msg.text = _("Render Starting...")
        job_msg.status = RENDERING
        update_job_queue(job_msg)
        
        # Set writefile.
        data_file_uid = utils.get_uid_str()
        self.write_file = userfolders.get_render_dir() + data_file_uid + appconsts.STABILIZE_DATA_EXTENSION

        # Create command list and launch process.
        command_list = [sys.executable]
        command_list.append(respaths.LAUNCH_DIR + "flowbladestabilizeheadless")
        for arg in self.args:
            command_list.append(arg)
        parent_folder_arg = "parent_folder:" + str(self.parent_folder)
        command_list.append(parent_folder_arg)
        write_file_arg = "write_file:" + str(self.write_file)
        command_list.append(write_file_arg)
        
        subprocess.Popen(command_list)
        
    def update_render_status(self):
        GLib.idle_add(self._update_from_gui_thread)
            
    def _update_from_gui_thread(self):

        if stabilizeheadless.session_render_complete(self.parent_folder, self.get_session_id()) == True:
            #remove_as_status_polling_object(self)
            
            job_msg = self.get_completed_job_message()
            update_job_queue(job_msg)
            
            stabilizeheadless.delete_session_folders(self.parent_folder, self.get_session_id())
            
            GLib.idle_add(self.update_filter_and_gui)

        else:
            status = stabilizeheadless.get_session_status(self.parent_folder, self.get_session_id())
            if status != None:
                fraction, elapsed = status
                
                self.progress = float(fraction)
                if self.progress > 1.0:
                    # A fix for how progress is calculated because producers can render a bit longer then required.
                    self.progress = 1.0

                self.elapsed = float(elapsed)
                self.text = _("Stabilizing Analysis") + " " + self.editable_properties[0].clip.name
                
                job_msg = self.get_job_queue_message()
                
                update_job_queue(job_msg)
            else:
                # Process start/stop on their own and we hit trying to get non-existing status for e.g completed renders.
                pass

    def update_filter_and_gui(self):
        self.filter.mlt_filter.set("results", str(self.write_file))
        # We have only one of these, so just recreate list.
        self.filter.non_mlt_properties = [("results_save_data",  str(self.write_file),  appconsts.PROP_EXPRESSION)]
        self.analyze_editor.analysis_complete()
        
    def abort_render(self):
        #remove_as_status_polling_object(self)
        stabilizeheadless.abort_render(self.parent_folder, self.get_session_id())


class StablizedMediaItemDataRenderJobQueueObject(AbstractJobQueueObject):

    def __init__(self, session_id, media_file, render_params, data_render_comple_callback, args):
        
        AbstractJobQueueObject.__init__(self, session_id, STABILIZE_DATA_RENDER)
        
        self.media_file = media_file
        self.render_params = render_params
        self.args = args
        self.parent_folder = userfolders.get_temp_render_dir() # This is used for message passing, output file goes to path given by 'write_file'.
        self.data_render_comple_callback = data_render_comple_callback
        
    def start_render(self):
        
        job_msg = self.get_job_queue_message()
        job_msg.text = _("Render Starting...")
        job_msg.status = RENDERING
        update_job_queue(job_msg)
        
        # Set writefile.
        data_file_uid = utils.get_uid_str()
        self.write_file = userfolders.get_render_dir() + data_file_uid + appconsts.STABILIZE_DATA_EXTENSION

        # Create command list and launch process.
        command_list = [sys.executable]
        command_list.append(respaths.LAUNCH_DIR + "flowbladestabilizeheadless")
        for arg in self.args:
            command_list.append(arg)
        parent_folder_arg = "parent_folder:" + str(self.parent_folder)
        command_list.append(parent_folder_arg)
        write_file_arg = "write_file:" + str(self.write_file)
        command_list.append(write_file_arg)
        
        subprocess.Popen(command_list)
        
    def update_render_status(self):
        GLib.idle_add(self._update_from_gui_thread)
            
    def _update_from_gui_thread(self):

        if stabilizeheadless.session_render_complete(self.parent_folder, self.get_session_id()) == True:
            
            job_msg = self.get_completed_job_message()
            update_job_queue(job_msg)
            
            stabilizeheadless.delete_session_folders(self.parent_folder, self.get_session_id())
            
            GLib.idle_add(self.data_render_done)

        else:
            status = stabilizeheadless.get_session_status(self.parent_folder, self.get_session_id())
            if status != None:
                fraction, elapsed = status
                
                self.progress = float(fraction)
                if self.progress > 1.0:
                    # A fix for how progress is calculated because producers can render a bit longer then required.
                    self.progress = 1.0

                self.elapsed = float(elapsed)
                self.text = _("Stabilizing Analysis") + " " + self.media_file.name
                
                job_msg = self.get_job_queue_message()
                
                update_job_queue(job_msg)
            else:
                # Process start/stop on their own and we hit trying to get non-existing status for e.g completed renders.
                pass

    def data_render_done(self):
        self.data_render_comple_callback(self.media_file, self.render_params, self.write_file)
        
    def abort_render(self):
        #remove_as_status_polling_object(self)
        stabilizeheadless.abort_render(self.parent_folder, self.get_session_id())


class StabilizedMediaItemVideoRenderJobQueueObject(AbstractJobQueueObject):

    def __init__(self, session_id, write_file, args):
        
        AbstractJobQueueObject.__init__(self, session_id, STABILIZED_MEDIA_ITEM_RENDER)
        
        self.write_file = write_file
        self.args = args
        self.parent_folder = userfolders.get_temp_render_dir() # THis is just used for message passing, output file goes where user decided.
                
    def get_job_name(self):
        folder, file_name = os.path.split(self.write_file)
        return file_name
        
    def start_render(self):
        
        job_msg = self.get_job_queue_message()
        job_msg.text = _("Render Starting...")
        job_msg.status = RENDERING
        update_job_queue(job_msg)
        
        # Create command list and launch process.
        command_list = [sys.executable]
        command_list.append(respaths.LAUNCH_DIR + "flowbladestabilizedvideoheadless")
        for arg in self.args:
            command_list.append(arg)
        parent_folder_arg = "parent_folder:" + str(self.parent_folder)
        command_list.append(parent_folder_arg)

        # We need to wait() in thread.
        command_list_runner = ProcessCommandListRunner(command_list)
        command_list_runner.start()
        
    def update_render_status(self):
        GLib.idle_add(self._update_from_gui_thread)
            
    def _update_from_gui_thread(self):

        if stabilizedvideoheadless.session_render_complete(self.parent_folder, self.get_session_id()) == True:
            job_msg = self.get_completed_job_message()
            update_job_queue(job_msg)
            
            stabilizedvideoheadless.delete_session_folders(self.parent_folder, self.get_session_id())
            
            GLib.idle_add(self.create_media_item)

        else:
            status = stabilizedvideoheadless.get_session_status(self.parent_folder, self.get_session_id())

            if status != None:
                fraction, elapsed = status

                self.progress = float(fraction)
                if self.progress > 1.0:
                    # A fix for how progress is calculated in gmicheadless because producers can render a bit longer then required.
                    self.progress = 1.0

                self.elapsed = float(elapsed)
                self.text = _("Stabilized Clip Render") + " " + self.get_job_name()
                
                job_msg = self.get_job_queue_message()

                update_job_queue(job_msg)
            else:
                # Process start/stop on their own and we hit trying to get non-existing status for e.g completed renders.
                pass

    def abort_render(self):
        stabilizedvideoheadless.abort_render(self.parent_folder, self.get_session_id())
        
    def create_media_item(self):
        callbackbridge.projectaction_open_rendered_file(self.write_file)

            

class TrackingDataRenderJobQueueObject(AbstractJobQueueObject):

    def __init__(self, session_id, filter, editable_properties, analyze_editor, args, data_label):
        
        AbstractJobQueueObject.__init__(self, session_id, MOTION_TRACKING_DATA_RENDER)
        
        self.analyze_editor = analyze_editor
        self.filter = filter
        self.editable_properties = editable_properties
        self.args = args
        self.data_label = data_label
        self.parent_folder = userfolders.get_temp_render_dir() # This is used for message passing, output file goes to path given by 'write_file'.
        
    def start_render(self):
        job_msg = self.get_job_queue_message()
        job_msg.text = _("Render Starting...")
        job_msg.status = RENDERING
        update_job_queue(job_msg)
        
        # Set writefile.
        self.write_file = userfolders.get_temp_render_dir() + utils.get_uid_str() + ".xml"

        # Set tracking data file path.
        self.data_file_path = userfolders.get_render_dir() +  utils.get_uid_str() + appconsts.MOTION_TRACKING_DATA_EXTENSION
            
        # Create command list and launch process.
        command_list = [sys.executable]
        command_list.append(respaths.LAUNCH_DIR + "flowbladetrackingheadless")
        for arg in self.args:
            command_list.append(arg)
            
        parent_folder_arg = "parent_folder:" + str(self.parent_folder)
        command_list.append(parent_folder_arg)
        write_file_arg = "write_file:" + str(self.write_file)
        command_list.append(write_file_arg)
        data_file_arg = "data_file_path:" + str(self.data_file_path)
        command_list.append(data_file_arg)

        # We need to wait() in thread.
        command_list_runner = ProcessCommandListRunner(command_list)
        command_list_runner.start()
        
    def update_render_status(self):
        GLib.idle_add(self._update_from_gui_thread)
            
    def _update_from_gui_thread(self):
            
        if trackingheadless.session_render_complete(self.parent_folder, self.get_session_id()) == True:
            
            job_msg = self.get_completed_job_message()
            update_job_queue(job_msg)
            
            trackingheadless.delete_session_folders(self.parent_folder, self.get_session_id())
            
            GLib.idle_add(self.update_filter_and_gui)

        else:
            status = trackingheadless.get_session_status(self.parent_folder, self.get_session_id())
            if status != None:
                fraction, elapsed = status
                
                self.progress = float(fraction)
                if self.progress > 1.0:
                    # A fix for how progress is calculated because producers can render a bit longer then required.
                    self.progress = 1.0

                self.elapsed = float(elapsed)
                self.text = _("Tracking Data Render") + " " + self.data_label #self.editable_properties[0].clip.name

                job_msg = self.get_job_queue_message()
                
                update_job_queue(job_msg)
            else:
                # Process start/stop on their own and we hit trying to get non-existing status for e.g completed renders.
                pass

    def update_filter_and_gui(self):    
        final_label = PROJECT().add_tracking_data(self.data_label, self.data_file_path)
        self.analyze_editor.analysis_complete(final_label, self.data_file_path)

    def abort_render(self):
        trackingheadless.abort_render(self.parent_folder, self.get_session_id())



class ProxyRenderJobQueueObject(AbstractJobQueueObject):

    def __init__(self, session_id, render_data):
        
        AbstractJobQueueObject.__init__(self, session_id, PROXY_RENDER)
        
        self.render_data = render_data # 'render_data' is proxyediting.ProxyRenderItemData
        self.parent_folder = userfolders.get_temp_render_dir()

    def get_job_name(self):
        folder, file_name = os.path.split(self.render_data.media_file_path)
        return file_name
        
    def start_render(self):
        job_msg = self.get_job_queue_message()
        job_msg.text = _("Render Starting...")
        job_msg.status = RENDERING
        update_job_queue(job_msg)
        
        enc_opt = renderconsumer.proxy_encodings[self.render_data.enc_index]
        args = self.render_data.get_data_as_args_tuple()
        if enc_opt.ffmpeggpuenc == None:
            # MLT proxy rendering
            self.is_mlt_render = True
            
            # Create command list and launch process.
            command_list = [sys.executable]
            command_list.append(respaths.LAUNCH_DIR + "flowbladeproxyheadless")


            # Info print, try to remove later.
            proxy_profile_path = userfolders.get_cache_dir() + "temp_proxy_profile"
            proxy_profile = mlt.Profile(proxy_profile_path)
            enc_index = int(utils.get_headless_arg_value(args, "enc_index"))

            for arg in args:
                command_list.append(arg)
                
            session_arg = "session_id:" + str(self.session_id)
            command_list.append(session_arg)

            parent_folder_arg = "parent_folder:" + str(self.parent_folder)
            command_list.append(parent_folder_arg)

            # We need to wait() in thread.
            command_list_runner = ProcessCommandListRunner(command_list)
            command_list_runner.start()
        else:
            # FFMPEG CLI proxy rendering.
            self.is_mlt_render = False
            
            # Build ffmpeg CLI string.
            proxy_attr_str = enc_opt.attr_string
            # Set scale size.
            screen_size_str = str(self.render_data.proxy_w) + "x" + str(self.render_data.proxy_h)
            proxy_attr_str = proxy_attr_str.replace(FFMPEG_ATTR_SCREENSIZE, screen_size_str)
            #...or
            screen_size_str = str(self.render_data.proxy_w) + ":" + str(self.render_data.proxy_h)
            proxy_attr_str = proxy_attr_str.replace(FFMPEG_ATTR_SCREENSIZE_2, screen_size_str)
            # Set source file.
            proxy_attr_str = proxy_attr_str.replace(FFMPEG_ATTR_SOURCEFILE, self.render_data.media_file_path)
            # Set proxy file.
            proxy_attr_str = proxy_attr_str.replace(FFMPEG_ATTR_PROXYFILE, self.render_data.proxy_file_path)

            ffmpeg_command = "ffmpeg -i " + str(proxy_attr_str)
            
            self.ffmpeg_start = time.monotonic()
            
            self.ffmpeg_remnder_thread = FFmpegRenderThread(ffmpeg_command)
            self.ffmpeg_remnder_thread.start()

    def update_render_status(self):

        GLib.idle_add(self._update_from_gui_thread)
            
    def _update_from_gui_thread(self):
        
        if self.is_mlt_render == True:
            if proxyheadless.session_render_complete(self.parent_folder, self.get_session_id()) == True:
                
                job_msg = self.get_completed_job_message()
                update_job_queue(job_msg)
                
                proxyheadless.delete_session_folders(self.parent_folder, self.get_session_id()) # these were created mltheadlessutils.py, see proxyheadless.py
                
                GLib.idle_add(self.proxy_render_complete)

            else:
                status = proxyheadless.get_session_status(self.parent_folder, self.get_session_id())
                if status != None:
                    fraction, elapsed = status
                    
                    self.progress = float(fraction)
                    if self.progress > 1.0:
                        self.progress = 1.0

                    self.elapsed = float(elapsed)
                    self.text = _("Proxy Render")  + " " + self.get_job_name()

                    job_msg = self.get_job_queue_message()
                    update_job_queue(job_msg)
                else:
                    # Process start/stop on their own and we hit trying to get non-existing status for e.g completed renders.
                    pass
        else:
            if self.ffmpeg_remnder_thread.completed == True:
                job_msg = self.get_completed_job_message()
                update_job_queue(job_msg)
                GLib.idle_add(self.proxy_render_complete)
            else:
                self.elapsed = float(time.monotonic() - self.ffmpeg_start)
                prog_step = 0.07
                if PROJECT().profile.height() > 1090:
                    prog_step = 0.035
                self.progress += prog_step
                if self.progress > 1.0:
                    self.progress = 0.99
                    
                self.text = _("Proxy Render")  + " " + self.get_job_name()

                job_msg = self.get_job_queue_message()
                update_job_queue(job_msg)
                    
    def abort_render(self):
        if self.is_mlt_render == True:
            # remove_as_status_polling_object(self)
            motionheadless.abort_render(self.parent_folder, self.get_session_id())
        
        # NOTE: ffmpeg cli render not abortable currently.
        
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



class TranscodeRenderJobQueueObject(AbstractJobQueueObject):

    def __init__(self, session_id, render_data):
        
        AbstractJobQueueObject.__init__(self, session_id, PROXY_RENDER)
        
        self.render_data = render_data # 'render_data' is proxyediting.ProxyRenderItemData
        self.parent_folder = userfolders.get_temp_render_dir()

    def get_job_name(self):
        folder, file_name = os.path.split(self.render_data.media_file_path)
        return file_name
        
    def start_render(self):
        job_msg = self.get_job_queue_message()
        job_msg.text = _("Render Starting...")
        job_msg.status = RENDERING
        update_job_queue(job_msg)
        
        enc_opt = renderconsumer.proxy_encodings[self.render_data.enc_index]
        args = self.render_data.get_data_as_args_tuple()
        if enc_opt.ffmpeggpuenc == None:
            # MLT proxy rendering
            self.is_mlt_render = True
            
            # Create command list and launch process.
            command_list = [sys.executable]
            command_list.append(respaths.LAUNCH_DIR + "flowbladeproxyheadless")


            # Info print, try to remove later.
            proxy_profile_path = userfolders.get_cache_dir() + "temp_proxy_profile"
            proxy_profile = mlt.Profile(proxy_profile_path)
            enc_index = int(utils.get_headless_arg_value(args, "enc_index"))

            for arg in args:
                command_list.append(arg)
                
            session_arg = "session_id:" + str(self.session_id)
            command_list.append(session_arg)

            parent_folder_arg = "parent_folder:" + str(self.parent_folder)
            command_list.append(parent_folder_arg)

            # We need to wait() in thread.
            command_list_runner = ProcessCommandListRunner(command_list)
            command_list_runner.start()
        else:
            # FFMPEG CLI proxy rendering.
            self.is_mlt_render = False
            
            # Build ffmpeg CLI string.
            proxy_attr_str = enc_opt.attr_string
            # Set scale size.
            screen_size_str = str(self.render_data.proxy_w) + "x" + str(self.render_data.proxy_h)
            proxy_attr_str = proxy_attr_str.replace(FFMPEG_ATTR_SCREENSIZE, screen_size_str)
            #...or
            screen_size_str = str(self.render_data.proxy_w) + ":" + str(self.render_data.proxy_h)
            proxy_attr_str = proxy_attr_str.replace(FFMPEG_ATTR_SCREENSIZE_2, screen_size_str)
            # Set source file.
            proxy_attr_str = proxy_attr_str.replace(FFMPEG_ATTR_SOURCEFILE, self.render_data.media_file_path)
            # Set proxy file.
            proxy_attr_str = proxy_attr_str.replace(FFMPEG_ATTR_PROXYFILE, self.render_data.proxy_file_path)

            ffmpeg_command = "ffmpeg -i " + str(proxy_attr_str)
            
            self.ffmpeg_start = time.monotonic()
            
            self.ffmpeg_remnder_thread = FFmpegRenderThread(ffmpeg_command)
            self.ffmpeg_remnder_thread.start()

    def update_render_status(self):

        GLib.idle_add(self._update_from_gui_thread)
            
    def _update_from_gui_thread(self):
        
        if self.is_mlt_render == True:
            if proxyheadless.session_render_complete(self.parent_folder, self.get_session_id()) == True:
                
                job_msg = self.get_completed_job_message()
                update_job_queue(job_msg)
                
                proxyheadless.delete_session_folders(self.parent_folder, self.get_session_id()) # these were created mltheadlessutils.py, see proxyheadless.py
                
                GLib.idle_add(self.proxy_render_complete)

            else:
                status = proxyheadless.get_session_status(self.parent_folder, self.get_session_id())
                if status != None:
                    fraction, elapsed = status
                    
                    self.progress = float(fraction)
                    if self.progress > 1.0:
                        self.progress = 1.0

                    self.elapsed = float(elapsed)
                    self.text = _("Proxy Render")  + " " + self.get_job_name()

                    job_msg = self.get_job_queue_message()
                    update_job_queue(job_msg)
                else:
                    # Process start/stop on their own and we hit trying to get non-existing status for e.g completed renders.
                    pass
        else:
            if self.ffmpeg_remnder_thread.completed == True:
                job_msg = self.get_completed_job_message()
                update_job_queue(job_msg)
                GLib.idle_add(self.proxy_render_complete)
            else:
                self.elapsed = float(time.monotonic() - self.ffmpeg_start)
                prog_step = 0.07
                if PROJECT().profile.height() > 1090:
                    prog_step = 0.035
                self.progress += prog_step
                if self.progress > 1.0:
                    self.progress = 0.99
                    
                self.text = _("Proxy Render")  + " " + self.get_job_name()

                job_msg = self.get_job_queue_message()
                update_job_queue(job_msg)
                    
    def abort_render(self):
        if self.is_mlt_render == True:
            # remove_as_status_polling_object(self)
            motionheadless.abort_render(self.parent_folder, self.get_session_id())
        
        # NOTE: ffmpeg cli render not abortable currently.
        
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


TranscodeRenderJobQueueObject

class FFmpegRenderThread(threading.Thread):
    
    def __init__(self, ffmpeg_command):
        
        self.ffmpeg_command = ffmpeg_command
        self.completed = False

        threading.Thread.__init__(self)

    def run(self):
        os.system(self.ffmpeg_command) # blocks
        self.completed = True 


# ----------------------------------------------------------------- polling
class ContainerStatusPollingThread(threading.Thread):
    
    def __init__(self):

        self.abort = False

        threading.Thread.__init__(self)

    def run(self):

        while self.abort == False:
            for job in _jobs:
                if job.status == RENDERING:
                    job.callback_object.update_render_status() # Make sure these methods enter/exit Gtk threads.

            # Handling post-app-close jobs rendering.
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

