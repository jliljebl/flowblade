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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

import gtk
import datetime
import pango

import appconsts
import utils
import guiutils
import editorstate
from editorstate import PROJECT
import respaths
    
LOGGING_MODE_AUTO_ALL = 0
LOGGING_MODE_AUTO_INSERTS = 1
LOGGING_MODE_AUTO_RANGES = 2
LOGGING_MODE_MANUAL = 3

widgets = utils.EmptyClass()

class MediaLogEvent:
    def __init__(self, event_type, mark_in, mark_out, name, path):
        self.event_type = event_type
        self.timestamp = datetime.datetime.now()
        self.mark_in = mark_in
        self.mark_out = mark_out
        self.name = name
        self.path = path
        self.comment = ""
        self.starred = False

    def get_event_name(self):
        if self.event_type == appconsts.MEDIA_LOG_INSERT:
            return "Insert"
        elif self.event_type == appconsts.MEDIA_LOG_MARKS_SET:
            return "Marks"

    def get_mark_in_str(self):
        return utils.get_tc_string(self.mark_in)

    def get_mark_out_str(self):
        return utils.get_tc_string(self.mark_out)
        
    def get_date_str(self):
        date_str = self.timestamp.strftime('%d %B, %Y - %H:%M')
        date_str = date_str.lstrip('0')
        return date_str

    
# ----------------------------------------------------------- 
def media_log_filtering_changed():
    widgets.media_log_view.fill_data_model()

def media_log_star_button_pressed():
    selected = widgets.media_log_view.get_selected_rows_list()
    event_type = widgets.auto_log_mode_combo.get_active() - 1 # -1 produces values corresponding to media log event types in projectdata.py
    log_events = PROJECT().get_filtered_media_log_events(event_type, 
                                                         widgets.star_check.get_active(),
                                                         widgets.star_not_active_check.get_active())
    for row in selected:
        index = max(row) # these are tuple, max to extract only value
        log_events[index].starred = not log_events[index].starred

    widgets.media_log_view.fill_data_model()

def register_media_insert_event():
    project = editorstate.PROJECT()
    media_file = editorstate.MONITOR_MEDIA_FILE()
    log_event = MediaLogEvent(  appconsts.MEDIA_LOG_INSERT,
                                media_file.mark_in,
                                media_file.mark_out,
                                media_file.name,
                                media_file.path)
    project.media_log.append(log_event)

def register_media_marks_set_event():
    project = editorstate.PROJECT()
    media_file = editorstate.MONITOR_MEDIA_FILE()
    if media_file.mark_in == -1 or media_file.mark_out == -1:
        return False
    log_event = MediaLogEvent(  appconsts.MEDIA_LOG_MARKS_SET,
                                media_file.mark_in,
                                media_file.mark_out,
                                media_file.name,
                                media_file.path)
    project.media_log.append(log_event)
    return True


def logging_mode_changed(combo):
    if (combo.get_active() == LOGGING_MODE_AUTO_ALL) or (combo.get_active() == LOGGING_MODE_AUTO_INSERTS):
        widgets.log_range.set_sensitive(False)
    else:
        widgets.log_range.set_sensitive(True)

# ------------------------------------------------------------ gui
def get_media_log_list_view():
    media_log_view = MediaLogListView()
    global widgets
    widgets.media_log_view = media_log_view
    return media_log_view

def update_media_log_view():
    widgets.media_log_view.fill_data_model()
    
    
class MediaLogListView(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)

        style = self.get_style()
        bg_col = style.bg[gtk.STATE_NORMAL]
        
       # Datamodel: icon, text, text
        self.storemodel = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str, str, str, str)
 
        # Scroll container
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # View
        self.treeview = gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(True)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(gtk.SELECTION_MULTIPLE)

        # Column views
        self.icon_col_1 = gtk.TreeViewColumn("icon1")
        self.icon_col_1.set_title(_("Star"))
        self.text_col_1 = gtk.TreeViewColumn("text1")
        self.text_col_1.set_title(_("Event"))
        self.text_col_2 = gtk.TreeViewColumn("text2")
        self.text_col_2.set_title(_("Comment"))
        self.text_col_3 = gtk.TreeViewColumn("text3")
        self.text_col_3.set_title(_("File Name"))
        self.text_col_4 = gtk.TreeViewColumn("text4")
        self.text_col_4.set_title(_("Mark In"))
        self.text_col_5 = gtk.TreeViewColumn("text5")
        self.text_col_5.set_title(_("Mark Out"))
        self.text_col_6 = gtk.TreeViewColumn("text6")
        self.text_col_6.set_title(_("Date"))
    
        # Cell renderers
        self.icon_rend_1 = gtk.CellRendererPixbuf()
        self.icon_rend_1.props.xpad = 6
        #self.icon_rend_1.set_property('activatable', True)

        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_END)

        self.text_rend_2 = gtk.CellRendererText()
        self.text_rend_2.set_property("yalign", 0.0)
        self.text_rend_2.set_property("editable", True)
        #self.text_rend_2.connect("edited", seq_name_edited_cb, (self.storemodel, 2))
                                 
        self.text_rend_3 = gtk.CellRendererText()
        self.text_rend_3.set_property("yalign", 0.0)

        self.text_rend_4 = gtk.CellRendererText()
        self.text_rend_4.set_property("yalign", 0.0)

        self.text_rend_5 = gtk.CellRendererText()
        self.text_rend_5.set_property("yalign", 0.0)

        self.text_rend_6 = gtk.CellRendererText()
        self.text_rend_6.set_property("yalign", 0.0)

        # Build column views
        self.icon_col_1.set_expand(False)
        self.icon_col_1.set_spacing(5)
        self.text_col_1.set_min_width(20)
        self.icon_col_1.pack_start(self.icon_rend_1)
        self.icon_col_1.add_attribute(self.icon_rend_1, 'pixbuf', 0)
    
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.text_col_1.set_min_width(50)
        self.text_col_1.pack_start(self.text_rend_1)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 1)

        self.text_col_2.set_expand(True)
        self.text_col_2.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.text_col_2.set_min_width(150)
        self.text_col_2.pack_start(self.text_rend_2)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 2)

        self.text_col_3.set_expand(True)
        self.text_col_3.pack_start(self.text_rend_3)
        self.text_col_3.add_attribute(self.text_rend_3, "text", 3)

        self.text_col_4.set_expand(True)
        self.text_col_4.pack_start(self.text_rend_4)
        self.text_col_4.add_attribute(self.text_rend_4, "text", 4)

        self.text_col_5.set_expand(True)
        self.text_col_5.pack_start(self.text_rend_5)
        self.text_col_5.add_attribute(self.text_rend_5, "text", 5)

        self.text_col_6.set_expand(True)
        self.text_col_6.pack_start(self.text_rend_6)
        self.text_col_6.add_attribute(self.text_rend_6, "text", 6)
        
        # Add column views to view
        self.treeview.append_column(self.icon_col_1)
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)
        self.treeview.append_column(self.text_col_3)
        self.treeview.append_column(self.text_col_4)
        self.treeview.append_column(self.text_col_5)
        self.treeview.append_column(self.text_col_6)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
        self.scroll.show_all()

    def fill_data_model(self):
        """
        Creates displayed data.
        Displays icon, sequence name and sequence length
        """
        self.storemodel.clear()
        star_icon_path = respaths.IMAGE_PATH + "star.png"
    
        event_type = widgets.auto_log_mode_combo.get_active() - 1 # -1 produces values corresponding to media log event types in appconsts.py
        log_events = PROJECT().get_filtered_media_log_events(event_type, 
                                                             widgets.star_check.get_active(),
                                                             widgets.star_not_active_check.get_active())
        for log_event in log_events:
            if log_event.starred == True:
                icon = gtk.gdk.pixbuf_new_from_file(star_icon_path)
            else:
                icon = None
            row_data = [icon, 
                        log_event.get_event_name(),
                        log_event.comment,
                        log_event.name,
                        log_event.get_mark_in_str(),
                        log_event.get_mark_out_str(),
                        log_event.get_date_str()]
            self.storemodel.append(row_data)

        self.scroll.queue_draw()

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows

def get_media_log_events_panel(events_list_view):
    auto_log_mode_combo = gtk.combo_box_new_text()
    auto_log_mode_combo.append_text(_("All Events"))
    auto_log_mode_combo.append_text(_("Insert Events"))
    auto_log_mode_combo.append_text(_("Range Events"))
    auto_log_mode_combo.set_active(0)

    star_check = gtk.CheckButton()
    star_check.set_active(True)
    star_label = gtk.Image()
    star_label.set_from_file(respaths.IMAGE_PATH + "star.png")
    star_not_active_check = gtk.CheckButton()
    star_not_active_check.set_active(True)
    star_not_active_label = gtk.Image()
    star_not_active_label.set_from_file(respaths.IMAGE_PATH + "star_not_active.png")

    global widgets
    widgets.star_check = star_check
    widgets.star_not_active_check = star_not_active_check
    widgets.auto_log_mode_combo = auto_log_mode_combo
    
    star_button = gtk.Button()
    star_button.set_image(gtk.image_new_from_file(respaths.IMAGE_PATH + "star.png"))
    star_button.connect("clicked", lambda w: media_log_star_button_pressed())
                
    auto_log_mode_combo.connect("changed", lambda w:media_log_filtering_changed())
    star_check.connect("clicked", lambda w:media_log_filtering_changed())
    star_not_active_check.connect("clicked", lambda w:media_log_filtering_changed())

    row1 = gtk.HBox()
    row1.pack_start(auto_log_mode_combo, False, True, 0)
    row1.pack_start(guiutils.get_pad_label(6, 12), False, True, 0)
    row1.pack_start(star_check, False, True, 0)
    row1.pack_start(star_label, False, True, 0)
    row1.pack_start(guiutils.get_pad_label(6, 12), False, True, 0)
    row1.pack_start(star_not_active_check, False, True, 0)
    row1.pack_start(star_not_active_label, False, True, 0)
    row1.pack_start(gtk.Label(), True, True, 0)
    row1.pack_start(star_button, False, True, 0)

    logging_mode_combo = gtk.combo_box_new_text()
    logging_mode_combo.append_text(_("Auto Log All"))
    logging_mode_combo.append_text(_("Auto Log Inserts"))
    logging_mode_combo.append_text(_("Auto Log Ranges"))
    logging_mode_combo.append_text(_("Manual Logging"))
    logging_mode_combo.set_active(0)
    logging_mode_combo.connect("changed", logging_mode_changed)
    widgets.logging_mode_combo = logging_mode_combo 

    widgets.log_range = gtk.Button()
    widgets.log_range.set_image(gtk.image_new_from_file(respaths.IMAGE_PATH + "log_range.png"))
    widgets.log_range.set_sensitive(False)

    append_displayed = gtk.Button()
    append_displayed.set_image(gtk.image_new_from_file(respaths.IMAGE_PATH + "append_media_log.png"))

    row2 =  gtk.HBox()
    row2.pack_start(logging_mode_combo, False, True, 0)
    row2.pack_start(widgets.log_range, False, True, 0)
    row2.pack_start(gtk.Label(), True, True, 0)
    row2.pack_start(append_displayed, False, True, 0)

    panel = gtk.VBox()
    panel.pack_start(row1, False, True, 0)
    panel.pack_start(events_list_view, True, True, 0)
    panel.pack_start(row2, False, True, 0)
    panel.set_size_request(400, 200)

    return panel
