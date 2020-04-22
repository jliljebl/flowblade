"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2013 Janne Liljeblad.

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

import dialogutils
from editorstate import PROJECT
import guicomponents
import guiutils
import utils

widgets = utils.EmptyClass()

PROJECT_INFO_PANEL_HEIGHT = 200
PROJECT_TOP_LEVEL_PANE_HEIGHT = 150

def get_project_info_panel():
    project_name_label = Gtk.Label(label=PROJECT().name)
    name_row = guiutils.get_left_justified_box([project_name_label])
    name_vbox = Gtk.VBox()
    name_vbox.pack_start(name_row, False, False, 0)
    name_vbox.pack_start(Gtk.Label(), True, True, 0)
    name_panel = guiutils.get_named_frame(_("Name"), name_vbox, 4)
    
    profile = PROJECT().profile
    desc_label = Gtk.Label(label=profile.description())
    info_box = guicomponents.get_profile_info_small_box(profile)
    vbox = Gtk.VBox()
    vbox.pack_start(guiutils.get_left_justified_box([desc_label]), False, True, 0)
    vbox.pack_start(info_box, False, True, 0)
    profile_panel = guiutils.get_named_frame(_("Profile"), vbox, 4)

    project_info_hbox = Gtk.HBox()
    project_info_hbox.pack_start(name_panel, False, True, 0)
    project_info_hbox.pack_start(guiutils.pad_label(24, 24), False, True, 0)
    project_info_hbox.pack_start(profile_panel, False, True, 0)
    project_info_hbox.pack_start(Gtk.Label(), True, True, 0)
    
    widgets.project_name_label = project_name_label
    widgets.desc_label = desc_label
    widgets.info_box = info_box

    return project_info_hbox

def get_top_level_project_info_panel():

    project_name_label = Gtk.Label(label=PROJECT().name)
    name_row = guiutils.get_left_justified_box([project_name_label])
    name_panel = guiutils.get_named_frame(_("Project"), name_row, 0, 6, 4, _("A <b>Project</b> contains one or more <b>Sequences</b> of edited media and a collection of media files stored in <b>Bins.</b>"))

    profile = PROJECT().profile
    desc_label = Gtk.Label(label=profile.description())
    info_box = guicomponents.get_profile_info_small_box(profile)
    vbox = Gtk.VBox()
    vbox.pack_start(guiutils.get_left_justified_box([desc_label]), False, True, 0)
    vbox.pack_start(info_box, False, True, 0)
    profile_panel = guiutils.get_named_frame(_("Profile"), vbox, 0, 6, 4, _("<b>Profile</b> determines frame rate per second, image size in pixels and pixel aspect ratio for all <b>Sequences</b> in <b>Project</b> ."))

    project_info_vbox = Gtk.VBox()
    project_info_vbox.pack_start(name_panel, False, True, 0)
    project_info_vbox.pack_start(profile_panel, False, True, 0)
    guiutils.set_margins(project_info_vbox, 4,4,4,4)

    widgets.project_name_label = project_name_label
    widgets.desc_label = desc_label
    widgets.info_box = info_box

    return project_info_vbox
    
def update_project_info():
    profile = PROJECT().profile
    widgets.project_name_label.set_markup(guiutils.bold_text(PROJECT().name))
    widgets.desc_label.set_text(profile.description())
    profile_info_text = guicomponents.get_profile_info_text(profile)
    widgets.info_box.get_children()[0].set_text(profile_info_text)


def show_project_events_dialog():
    events_list = ProjectEventListView()
    events_list.fill_data_model()
    events_list.set_size_request(620, 500)
    dialogutils.panel_ok_dialog(_("Project Events"), events_list)

class ProjectEventListView(Gtk.VBox):

    def __init__(self):
        GObject.GObject.__init__(self)

       # Datamodel: text, text, text
        self.storemodel = Gtk.ListStore(str, str, str)

        # Scroll container
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

        # View
        self.treeview = Gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(True)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(Gtk.SelectionMode.SINGLE)

        # Column views
        self.text_col_1 = Gtk.TreeViewColumn("text1")
        self.text_col_1.set_title(_("Date"))
        self.text_col_2 = Gtk.TreeViewColumn("text2")
        self.text_col_2.set_title(_("Event"))
        self.text_col_3 = Gtk.TreeViewColumn("text3")
        self.text_col_3.set_title(_("Data"))

        # Cell renderers
        self.text_rend_1 = Gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", Pango.EllipsizeMode.END)

        self.text_rend_2 = Gtk.CellRendererText()
        self.text_rend_2.set_property("yalign", 0.0)

        self.text_rend_3 = Gtk.CellRendererText()
        self.text_rend_3.set_property("yalign", 0.0)

        # Build column views
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1, True)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 0)

        self.text_col_2.set_expand(True)
        self.text_col_2.pack_start(self.text_rend_2, True)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 1)

        self.text_col_3.set_expand(True)
        self.text_col_3.pack_start(self.text_rend_3, True)
        self.text_col_3.add_attribute(self.text_rend_3, "text", 2)
        
        # Add column views to view
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)
        self.treeview.append_column(self.text_col_3)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll, True, True, 0)
        self.scroll.show_all()

    def fill_data_model(self):
        self.storemodel.clear()
        for e in PROJECT().events:
            t = e.get_date_str()
            desc, path = e.get_desc_and_path()
            row_data = [t, desc, path]
            self.storemodel.append(row_data)
        
        self.scroll.queue_draw()
    
