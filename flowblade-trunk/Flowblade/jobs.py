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


from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Pango

import copy
import time

import editorpersistance
import guicomponents
import guiutils
import utils

RENDERING = 0
COMPLETE = 1
ABORTED = 2

NOT_SET_YET = 0
CONTAINER_CLIP_RENDER = 1
PROXY_RENDER = 2

_jobs_list_view = None

_jobs = [] # proxy objects that represent background renders and provide info on render status.



class JobProxy: # Background renders provide these to give info on render status.
                  # Modules doing the rendering must manage setting all values.

    def __init__(self, uid):
        self.proxy_uid = uid # modules doing the rendering and using this to display must make sure this matches always for a particular job
        self.type = NOT_SET_YET 
        self.status = RENDERING
        self.progress = 0.0 # 0.0. - 1.0
        self.text = ""
        self.elapsed = 0.0 # in fractional seconds

    def get_elapsed_str(self):
        return utils.get_time_str_for_sec_float(self.elapsed)

    def get_type_str(self):
        if self.type == NOT_SET_YET:
            return "NO TYPE SET" # this just error info, application has done something wrong.
        elif self.type == CONTAINER_CLIP_RENDER:
            return _("Container Clip")
    
    def get_progress_str(self):
        return str(int(self.progress * 100.0)) + "%"


#---------------------------------------------------------------- INTERFACE
def add_job(job_proxy):
    global _jobs
    _jobs.insert(0, job_proxy)
    _jobs_list_view.fill_data_model()
    
def show_message(update_job_proxy):
    row = -1
    job_proxy = None  
    for i in range (0, len(_jobs)):
        job_proxy = _jobs[i]
        if job_proxy.proxy_uid == update_job_proxy.proxy_uid:
            # Update job proxy info and remember row
            job_proxy = copy.copy(update_job_proxy)
            row = i
            break

    if row == -1:
        # Something is wrong.
        print("trying to update non-existing job at jobs.show_message()!")
        return

    tree_path = Gtk.TreePath.new_from_string(str(row))
    store_iter = _jobs_list_view.storemodel.get_iter(tree_path)

    
    _jobs_list_view.storemodel.set_value(store_iter, 0, job_proxy.get_type_str())
    _jobs_list_view.storemodel.set_value(store_iter, 1, job_proxy.text)
    _jobs_list_view.storemodel.set_value(store_iter, 2, job_proxy.get_elapsed_str())
    _jobs_list_view.storemodel.set_value(store_iter, 3, job_proxy.get_progress_str())

    _jobs_list_view.scroll.queue_draw()


#---------------------------------------------------------------- GUI
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

def _menu_action_pressed(widget, event):
    pass


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
        
        self.text_rend_3 = Gtk.CellRendererText()
        self.text_rend_3.set_property("yalign", 0.0)
        
        self.text_rend_4 = Gtk.CellRendererText()
        self.text_rend_4.set_property("yalign", 0.0)

        # Column views
        self.text_col_1 = Gtk.TreeViewColumn(_("Type"))
        self.text_col_2 = Gtk.TreeViewColumn(_("Info"))
        self.text_col_3 = Gtk.TreeViewColumn(_("Render Time"))
        self.text_col_4 = Gtk.TreeViewColumn(_("Progress"))

        #self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        self.text_col_1.set_min_width(150)
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

    def fill_data_model(self):
        self.storemodel.clear()        
        
        for job in _jobs:
            row_data = [job.get_type_str(),
                        job.text,
                        job.get_elapsed_str(),
                        job.get_progress_str()]
            self.storemodel.append(row_data)
            self.scroll.queue_draw()
