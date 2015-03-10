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
    along with Flowblade Movie Editor. If not, see <http://www.gnu.org/licenses/>.
"""

import pygtk
pygtk.require('2.0');
import gtk

import datetime
import pango

import appconsts
import dialogs
import dialogutils
import dnd
import edit
import gui
import guicomponents
import guiutils
import editorstate
from editorstate import PROJECT
import monitorevent
import respaths
import updater
import utils


widgets = utils.EmptyClass()

do_multiple_clip_insert_func = None # this mankeypathched her in app.py

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


# ----------------------------------------------------------- dnd drop
def clips_drop(clips):
    for clip in clips:
        if clip.media_type == appconsts.VIDEO or clip.media_type == appconsts.AUDIO:
            log_event = MediaLogEvent(  appconsts.MEDIA_LOG_MARKS_SET,
                                        clip.clip_in,
                                        clip.clip_out,
                                        clip.name,
                                        clip.path)
            editorstate.PROJECT().media_log.append(log_event)
    _update_list_view()
    

# ----------------------------------------------------------- gui events
def media_log_filtering_changed():
    widgets.media_log_view.fill_data_model()

def media_log_star_button_pressed():
    selected = widgets.media_log_view.get_selected_rows_list()
    log_events = get_current_filtered_events()
    for row in selected:
        index = max(row) # these are tuples, max to extract only value
        log_events[index].starred = True

    widgets.media_log_view.fill_data_model()

def media_log_no_star_button_pressed():
    selected = widgets.media_log_view.get_selected_rows_list()
    log_events = get_current_filtered_events()
    for row in selected:
        index = max(row) # these are tuples, max to extract only value
        log_events[index].starred = False

    widgets.media_log_view.fill_data_model()

def log_range_clicked():
    media_file = editorstate.MONITOR_MEDIA_FILE()
    if media_file == None:
        return
    if media_file.type == appconsts.PATTERN_PRODUCER:
        # INFOWINDOW ???
       return 
    if media_file.mark_in == -1 or media_file.mark_out == -1:
        return

    log_event = MediaLogEvent(  appconsts.MEDIA_LOG_MARKS_SET,
                                media_file.mark_in,
                                media_file.mark_out,
                                media_file.name,
                                media_file.path)
    editorstate.PROJECT().media_log.append(log_event)
    _update_list_view()

def _update_list_view():
    widgets.media_log_view.fill_data_model()
    max_val = widgets.media_log_view.treeview.get_vadjustment().get_upper()
    gui.middle_notebook.set_current_page(1)
    widgets.media_log_view.treeview.get_selection().select_path(str(len(get_current_filtered_events())-1))
    widgets.media_log_view.treeview.get_vadjustment().set_value(max_val)

def log_item_name_edited(cell, path, new_text, user_data):
    if len(new_text) == 0:
        return

    item_index = int(path)
    current_view_events = get_current_filtered_events()
    current_view_events[item_index].comment = new_text

    widgets.media_log_view.fill_data_model()

def delete_selected():
    selected = widgets.media_log_view.get_selected_rows_list()
    log_events = get_current_filtered_events()
    delete_events = []
    for row in selected:
        index = max(row) # these are tuple, max to extract only value
        delete_events.append(log_events[index])
    PROJECT().delete_media_log_events(delete_events)

    widgets.media_log_view.fill_data_model()

def display_item(row):
    log_events = get_current_filtered_events()
    event_item = log_events[row]
    media_file = PROJECT().get_media_file_for_path(event_item.path)
    media_file.mark_in = event_item.mark_in
    media_file.mark_out = event_item.mark_out
    updater.set_and_display_monitor_media_file(media_file)
    monitorevent.to_mark_in_pressed()

def log_list_view_button_press(treeview, event):
    path_pos_tuple = treeview.get_path_at_pos(int(event.x), int(event.y))
    if path_pos_tuple == None:
        return False
    if not (event.button == 3):
        return False

    path, column, x, y = path_pos_tuple
    selection = treeview.get_selection()
    selection.unselect_all()
    selection.select_path(path)
    row = int(max(path))

    guicomponents.display_media_log_event_popup_menu(row, treeview, _log_event_menu_item_selected, event)                                    
    return True

def _log_event_menu_item_selected(widget, data):
    item_id, row, treeview = data
    
    if item_id == "delete":
        delete_selected()
    elif item_id == "toggle":
        log_events = get_current_filtered_events()
        log_events[row].starred = not log_events[row].starred 
        widgets.media_log_view.fill_data_model()
    elif item_id == "display":
        display_item(row)

def get_current_filtered_events():
    log_events = PROJECT().get_filtered_media_log_events(widgets.group_view_select.get_active() - 1,
                                                         widgets.star_check.get_active(),
                                                         widgets.star_not_active_check.get_active())
    return log_events

def append_log_events():
    clips = []
    log_events = get_current_filtered_events()
    for le in log_events:
        clips.append(get_log_event_clip(le))
    
    track = editorstate.current_sequence().get_first_active_track() # audio tracks??!!??
    
    data = {"track":track,
            "clips":clips}

    action = edit.append_media_log_action(data)
    action.do_edit()

def insert_selected_log_events():
    clips = []
    log_events = get_current_filtered_events()
    
    treeselection = widgets.media_log_view.treeview.get_selection()
    (model, rows) = treeselection.get_selected_rows()
    
    for row_tuple in rows:
        row = row_tuple[0]
        le = log_events[row]
        clips.append(get_log_event_clip(le))
    
    track = editorstate.current_sequence().get_first_active_track()
    tline_pos = editorstate.current_tline_frame()
    do_multiple_clip_insert_func(track, clips, tline_pos)

def get_log_event_clip(log_event):
    # currently quarateed not to be a pattern producer
    new_clip = editorstate.current_sequence().create_file_producer_clip(log_event.path)
        
    # Set clip in and out points
    new_clip.clip_in = log_event.mark_in
    new_clip.clip_out = log_event.mark_out
    if widgets.use_comments_check.get_active() == True:
        new_clip.name = log_event.comment
        if len(new_clip.name) == 0:
            new_clip.name = log_event.name
    else:
        new_clip.name = log_event.name
    return new_clip

def get_clips_for_rows(rows):
    clips = []
    log_events = get_current_filtered_events()
    for row in rows:
        log_event = log_events[max(row)]
        clips.append(get_log_event_clip(log_event))      
        
    return clips

def display_log_clip_double_click_listener(treeview, path, view_column):
    row = int(max(path))
    data = ("display", row, treeview)
    _log_event_menu_item_selected(treeview, data)

def _group_action_pressed(widget, event):
    actions_menu = gtk.Menu()        
    actions_menu.add(guiutils.get_menu_item(_("New Group..."), _actions_callback, "new"))
    actions_menu.add(guiutils.get_menu_item(_("New Group From Selected..."), _actions_callback, "newfromselected"))
    
    guiutils.add_separetor(actions_menu)

    item = guiutils.get_menu_item(_("Rename Current Group..."), _actions_callback, "rename")
    _unsensitive_for_all_view(item)
    actions_menu.add(item)

    guiutils.add_separetor(actions_menu)
    
    move_menu_item = gtk.MenuItem(_("Move Selected Items To Group").encode('utf-8'))
    move_menu = gtk.Menu()
    if len(PROJECT().media_log_groups) == 0:
        move_menu.add(guiutils.get_menu_item(_("No Groups").encode('utf-8'), _actions_callback, "dummy", False))
    else:
        index = 0
        for group in PROJECT().media_log_groups:
            name, items = group
            move_menu.add(guiutils.get_menu_item(name, _actions_callback, str(index)))
            index = index + 1
    move_menu_item.set_submenu(move_menu)
    actions_menu.add(move_menu_item)
    move_menu_item.show()

    guiutils.add_separetor(actions_menu)

    item = guiutils.get_menu_item(_("Delete Current Group"), _actions_callback, "delete")
    _unsensitive_for_all_view(item)
    actions_menu.add(item)

    #item = guiutils.get_menu_item(_("Delete Current Group and Items"), _actions_callback, "deletewithitems")
    #_unsensitive_for_all_view(item)
    #actions_menu.add(item)

    actions_menu.popup(None, None, None, event.button, event.time)

def _unsensitive_for_all_view(item):
    if widgets.group_view_select.get_active() == 0:
        item.set_sensitive(False)

def _actions_callback(widget, data):
    if data == "newfromselected":
        next_index = len(PROJECT().media_log_groups)
        dialogs.new_media_log_group_name_dialog(_new_group_name_callback, next_index, True)
    elif data == "new":
        next_index = len(PROJECT().media_log_groups)
        dialogs.new_media_log_group_name_dialog(_new_group_name_callback, next_index, False)
    elif data == "delete":
        current_group_index = widgets.group_view_select.get_active() - 1
        if current_group_index < 0:
            return
        PROJECT().media_log_groups.pop(current_group_index)
        _create_group_select()
        widgets.group_view_select.set_active(0)
    elif data == "deletewithitems":
        current_group_index = widgets.group_view_select.get_active() - 1
        if current_group_index < 0:
            return
        name, items = PROJECT().media_log_groups[current_group_index]
        primary_txt = _("Delete Group and Items?")
        secondary_txt = _("Are you sure you want to delete group ") + name + _(" and ") + str(len(items)) + _(" items it contains?\n") + \
                        _("This operation cannot be undone.")
        dialogutils.warning_confirmation(_delete_with_items_dialog_callback,
                            primary_txt, secondary_txt, gui.editor_window.window, None, True)
    elif data == "rename":
        current_group_index = widgets.group_view_select.get_active() - 1
        name, items = PROJECT().media_log_groups[current_group_index]
        dialogs.group_rename_dialog(_rename_callback, name)
    else:
        try:
            to_group_index = int(data)
        except:
            return

        current_group_index = widgets.group_view_select.get_active() - 1
        if to_group_index == current_group_index:
            return

        # Get items to move
        selected = widgets.media_log_view.get_selected_rows_list()
        log_events = get_current_filtered_events()
        move_items = []
        for row in selected:
            index = max(row) # these are tuples, max to extract only value
            move_items.append(log_events[index])

        # Move items and update
        PROJECT().remove_from_group(current_group_index, move_items)
        PROJECT().add_to_group(to_group_index, move_items)
        widgets.group_view_select.set_active(to_group_index + 1) # 0 index items is "All" items group not a user created group

def _delete_with_items_dialog_callback(dialog, response_id):
    dialog.destroy()
    if response_id != gtk.RESPONSE_ACCEPT:
        return
    
    current_group_index = widgets.group_view_select.get_active() - 1
    name, items = PROJECT().media_log_groups[current_group_index]
    PROJECT().delete_media_log_events(items)
    PROJECT().media_log_groups.pop(current_group_index)
    _create_group_select()
    widgets.group_view_select.set_active(0)
    
def _rename_callback(dialog, response_id, entry):
    new_name = entry.get_text()
    dialog.destroy()
    if response_id == gtk.RESPONSE_CANCEL:
        return
    if len(new_name) == 0:
        return
        
    current_group_index = widgets.group_view_select.get_active() - 1
    old_name, items = PROJECT().media_log_groups[current_group_index]

    PROJECT().media_log_groups.pop(current_group_index)
    PROJECT().media_log_groups.insert(current_group_index, (new_name, items))
    _create_group_select()
    widgets.group_view_select.set_active(current_group_index + 1)

def _viewed_group_changed(widget):
    update_media_log_view()

def _new_group_name_callback(dialog, response_id, data):
    if response_id == gtk.RESPONSE_CANCEL:
        dialog.destroy()
        return
    
    # Get group name and create type
    name_entry, add_selected = data
    new_name = name_entry.get_text()
    dialog.destroy()
    if len(new_name) == 0:
        new_name = _("Group ") + str(len(PROJECT().media_log_groups))

    # Add items to new group if requested
    items = []
    if add_selected:
        selected = widgets.media_log_view.get_selected_rows_list()
        log_events = get_current_filtered_events()
        for row in selected:
            index = max(row) # these are tuples, max to extract only value
            items.append(log_events[index])

        current_group_index = widgets.group_view_select.get_active() - 1
        if current_group_index >= 0:
            PROJECT().remove_from_group(current_group_index, items)

    # Update view
    PROJECT().add_media_log_group(new_name, items)
    _create_group_select()
    widgets.group_view_select.set_active(len(PROJECT().media_log_groups))
    update_media_log_view()

    
# ------------------------------------------------------------ gui
def get_media_log_list_view():
    media_log_view = MediaLogListView()
    global widgets
    widgets.media_log_view = media_log_view
    return media_log_view

def update_media_log_view():
    widgets.media_log_view.fill_data_model()
    # Does not show last line, do we need timer?
    max_val = widgets.media_log_view.treeview.get_vadjustment().get_upper()
    widgets.media_log_view.treeview.get_vadjustment().set_value(max_val)

    
class MediaLogListView(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)
        
       # Datamodel: icon, text, text
        self.storemodel = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str, str, str)
 
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
        self.treeview.connect("button-press-event", log_list_view_button_press)
        self.treeview.connect("row-activated", display_log_clip_double_click_listener)
                              
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

        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_END)

        self.text_rend_2 = gtk.CellRendererText()
        self.text_rend_2.set_property("yalign", 0.0)
        self.text_rend_2.set_property("editable", True)
        self.text_rend_2.connect("edited", log_item_name_edited, (self.storemodel, 2))
                                 
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

        self.text_col_2.set_expand(True)
        self.text_col_2.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.text_col_2.set_min_width(150)
        self.text_col_2.pack_start(self.text_rend_2)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 1)

        self.text_col_3.set_expand(True)
        self.text_col_3.pack_start(self.text_rend_3)
        self.text_col_3.add_attribute(self.text_rend_3, "text", 2)

        self.text_col_4.set_expand(True)
        self.text_col_4.pack_start(self.text_rend_4)
        self.text_col_4.add_attribute(self.text_rend_4, "text", 3)

        self.text_col_5.set_expand(True)
        self.text_col_5.pack_start(self.text_rend_5)
        self.text_col_5.add_attribute(self.text_rend_5, "text", 4)

        self.text_col_6.set_expand(True)
        self.text_col_6.pack_start(self.text_rend_6)
        self.text_col_6.add_attribute(self.text_rend_6, "text", 5)
        
        # Add column views to view
        self.treeview.append_column(self.icon_col_1)
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
        self.storemodel.clear()
        star_icon_path = respaths.IMAGE_PATH + "star.png"
        no_star_icon_path = respaths.IMAGE_PATH + "star_not_active.png"

        log_events = get_current_filtered_events()
        for log_event in log_events:
            if log_event.starred == True:
                icon = gtk.gdk.pixbuf_new_from_file(star_icon_path)
            else:
                icon =  gtk.gdk.pixbuf_new_from_file(no_star_icon_path)
            row_data = [icon, 
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
    global widgets
    actions_pixbuf = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "media_log_action.png")
    group_actions_menu = guicomponents.PressLaunch(_group_action_pressed, actions_pixbuf, 38, 22)

    star_check = gtk.CheckButton()
    star_check.set_active(True)
    star_check.connect("clicked", lambda w:media_log_filtering_changed())
    widgets.star_check = star_check

    star_label = gtk.Image()
    star_label.set_from_file(respaths.IMAGE_PATH + "star.png")

    star_not_active_check = gtk.CheckButton()
    star_not_active_check.set_active(True)
    star_not_active_check.connect("clicked", lambda w:media_log_filtering_changed())
    widgets.star_not_active_check = star_not_active_check

    star_not_active_label = gtk.Image()
    star_not_active_label.set_from_file(respaths.IMAGE_PATH + "star_not_active.png")

    star_button = gtk.Button()
    star_button.set_image(gtk.image_new_from_file(respaths.IMAGE_PATH + "star.png"))
    star_button.connect("clicked", lambda w: media_log_star_button_pressed())

    no_star_button = gtk.Button()
    no_star_button.set_image(gtk.image_new_from_file(respaths.IMAGE_PATH + "star_not_active.png"))
    no_star_button.connect("clicked", lambda w: media_log_no_star_button_pressed())

    widgets.group_box = gtk.HBox()
    _create_group_select()
    widgets.group_view_select.set_active(0)
    
    row1 = gtk.HBox()
    row1.pack_start(guiutils.get_pad_label(6, 12), False, True, 0)
    row1.pack_start(group_actions_menu.widget, False, True, 0)
    row1.pack_start(guiutils.get_pad_label(6, 12), False, True, 0)
    row1.pack_start(widgets.group_box, False, True, 0)
    row1.pack_start(guiutils.get_pad_label(6, 12), False, True, 0)
    row1.pack_start(star_check, False, True, 0)
    row1.pack_start(star_label, False, True, 0)
    row1.pack_start(guiutils.get_pad_label(6, 12), False, True, 0)
    row1.pack_start(star_not_active_check, False, True, 0)
    row1.pack_start(star_not_active_label, False, True, 0)
    row1.pack_start(guiutils.pad_label(12, 12), False, False, 0)
    row1.pack_start(star_button, False, True, 0)
    row1.pack_start(no_star_button, False, True, 0)
    row1.pack_start(gtk.Label(), True, True, 0)

    widgets.log_range = gtk.Button()
    widgets.log_range.set_image(gtk.image_new_from_file(respaths.IMAGE_PATH + "log_range.png"))
    widgets.log_range.set_size_request(80, 30)
    widgets.log_range.connect("clicked", lambda w:log_range_clicked())

    delete_button = gtk.Button()
    delete_button.set_image(gtk.image_new_from_file(respaths.IMAGE_PATH + "delete_log_range.png"))
    delete_button.set_size_request(80, 30)
    delete_button.connect("clicked", lambda w:delete_selected())

    use_comments_label = gtk.Label(_("Use Comments as Clip Names"))
    use_comments_check =  gtk.CheckButton()
    use_comments_check.set_active(False)
    widgets.use_comments_check = use_comments_check

    insert_displayed = gtk.Button()
    insert_displayed.set_image(gtk.image_new_from_file(respaths.IMAGE_PATH + "insert_media_log.png"))
    insert_displayed.set_size_request(80, 22)
    insert_displayed.connect("clicked", lambda w:insert_selected_log_events())

    append_displayed = gtk.Button()
    append_displayed.set_image(gtk.image_new_from_file(respaths.IMAGE_PATH + "append_media_log.png"))
    append_displayed.set_size_request(80, 22)
    append_displayed.connect("clicked", lambda w:append_log_events())

    row2 =  gtk.HBox()
    row2.pack_start(widgets.log_range, False, True, 0)
    row2.pack_start(delete_button, False, True, 0)
    row2.pack_start(gtk.Label(), True, True, 0)
    row2.pack_start(use_comments_label, False, True, 0)
    row2.pack_start(use_comments_check, False, True, 0)
    row2.pack_start(gtk.Label(), True, True, 0)
    row2.pack_start(insert_displayed, False, True, 0)
    row2.pack_start(append_displayed, False, True, 0)

    panel = gtk.VBox()
    panel.pack_start(row1, False, True, 0)
    panel.pack_start(events_list_view, True, True, 0)
    panel.pack_start(row2, False, True, 0)
    panel.set_size_request(400, 200)

    star_check.set_tooltip_text(_("Display starred ranges"))    
    star_not_active_check.set_tooltip_text(_("Display non-starred ranges"))
    star_button.set_tooltip_text(_("Set selected ranges starred"))
    no_star_button.set_tooltip_text(_("Set selected ranges non-starred"))
    widgets.log_range.set_tooltip_text(_("Log current marked range"))
    delete_button.set_tooltip_text(_("Delete selected ranges"))
    insert_displayed.set_tooltip_text(_("Insert selected ranges on Timeline"))
    append_displayed.set_tooltip_text(_("Append displayed ranges on Timeline"))

    dnd.connect_range_log(events_list_view.treeview)
        
    return panel

def _create_group_select():
    try:
        widgets.group_box.remove(widgets.group_view_select)
    except:
        pass
        
    group_view_select = gtk.combo_box_new_text() # filled later when current sequence known
    group_view_select.append_text(_("All Items"))
    for group_data in PROJECT().media_log_groups:
        name, items = group_data
        group_view_select.append_text(name)

    group_view_select.set_size_request(250, 30)
    group_view_select.connect('changed', _viewed_group_changed)
    group_view_select.set_tooltip_text(_("Select viewed Range Log Items Group"))

    widgets.group_view_select = group_view_select
    widgets.group_box.add(widgets.group_view_select)
    widgets.group_view_select.show()
