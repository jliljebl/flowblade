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

"""
Module handles clip effects editing logic and gui
"""

import copy
from gi.repository import GLib
from gi.repository import Gtk
import pickle
import time

import atomicfile
import dialogs
import dialogutils
import edit
import editorpersistance
from editorstate import PROJECT
import gui
import guicomponents
import guiutils
import mltfilters
import propertyedit
import propertyeditorbuilder
import respaths
import translations
import updater
import utils

widgets = utils.EmptyClass()

clip = None # Clip being edited
track = None # Track of the clip being editeds
clip_index = None # Index of clip being edited
block_changed_update = False # Used to block unwanted callback update from "changed", hack and a broken one, look to fix
current_filter_index = -1 # Needed to find right filter object when saving/loading effect values

# This is updated when filter panel is displayed and cleared when removed.
# Used to update kfeditors with external tline frame position changes
keyframe_editor_widgets = []

# Filter stack DND requires some state info to be maintained to make sure that it's only done when certain events
# happen in a certain sequence.
NOT_ON = 0
MOUSE_PRESS_DONE = 1
INSERT_DONE = 2
stack_dnd_state = NOT_ON
stack_dnd_event_time = 0.0
stack_dnd_event_info = None

filters_notebook_index = 2

def get_clip_effects_editor_panel(group_combo_box, effects_list_view):
    """
    Use components created at clipeffectseditor.py.
    """
    create_widgets()

    stack_label = guiutils.bold_label(_("Clip Filters Stack"))
    
    label_row = guiutils.get_left_justified_box([stack_label])
    guiutils.set_margins(label_row, 0, 4, 0, 0)
    
    ad_buttons_box = Gtk.HBox(True,1)
    ad_buttons_box.pack_start(widgets.add_effect_b, True, True, 0)
    ad_buttons_box.pack_start(widgets.del_effect_b, True, True, 0)

    stack_buttons_box = Gtk.HBox(False,1)
    stack_buttons_box.pack_start(ad_buttons_box, True, True, 0)
    stack_buttons_box.pack_start(widgets.toggle_all, False, False, 0)
    
    effect_stack = widgets.effect_stack_view    

    for group in mltfilters.groups:
        group_name, filters_array = group
        group_combo_box.append_text(group_name)
    group_combo_box.set_active(0)    

    # Same callback function works for filter select window too
    group_combo_box.connect("changed", 
                            lambda w,e: _group_selection_changed(w,effects_list_view), 
                            None)

    widgets.group_combo = group_combo_box
    widgets.effect_list_view = effects_list_view
    set_enabled(False)
    
    exit_button_vbox = Gtk.VBox(False, 2)
    exit_button_vbox.pack_start(widgets.exit_button, False, False, 0)

    info_row = Gtk.HBox(False, 2)
    info_row.pack_start(widgets.hamburger_launcher.widget, False, False, 0)
    info_row.pack_start(Gtk.Label(), True, True, 0)
    info_row.pack_start(widgets.clip_info, False, False, 0)
    info_row.pack_start(Gtk.Label(), True, True, 0)
    
    combo_row = Gtk.HBox(False, 2)
    combo_row.pack_start(group_combo_box, True, True, 0)

    group_name, filters_array = mltfilters.groups[0]
    effects_list_view.fill_data_model(filters_array)
    effects_list_view.treeview.get_selection().select_path("0")
    
    effects_vbox = Gtk.VBox(False, 2)
    effects_vbox.pack_start(label_row, False, False, 0)
    effects_vbox.pack_start(stack_buttons_box, False, False, 0)
    effects_vbox.pack_start(effect_stack, True, True, 0)
    effects_vbox.pack_start(combo_row, False, False, 0)
    effects_vbox.pack_start(effects_list_view, True, True, 0)
    
    widgets.group_combo.set_tooltip_text(_("Select Filter Group"))
    widgets.effect_list_view.set_tooltip_text(_("Current group Filters"))

    return effects_vbox, info_row

def _group_selection_changed(group_combo, filters_list_view):
    group_name, filters_array = mltfilters.groups[group_combo.get_active()]
    filters_list_view.fill_data_model(filters_array)
    filters_list_view.treeview.get_selection().select_path("0")

def set_clip(new_clip, new_track, new_index):
    """
    Sets clip being edited and inits gui.
    """
    global clip, track, clip_index
    clip = new_clip
    track = new_track
    clip_index = new_index
    
    widgets.clip_info.display_clip_info(clip, track, clip_index)
    set_enabled(True)
    update_stack_view()
    effect_selection_changed() # This may get called twice
    gui.middle_notebook.set_current_page(filters_notebook_index) # 2 == index of clipeditor page in notebook

def clip_removed_during_edit(removed_clip):
    """
    Called from edit.py after a clip is removed from timeline during edit
    so that we cannot edit effects on clip that is no longer on timeline.
    """
    if  clip == removed_clip:
        clear_clip()

def effect_select_row_double_clicked(treeview, tree_path, col):
    add_currently_selected_effect()

def filter_stack_button_press(treeview, event):
    path_pos_tuple = treeview.get_path_at_pos(int(event.x), int(event.y))
    if path_pos_tuple == None:
        row = -1 # Empty row was clicked
    else:
        path, column, x, y = path_pos_tuple
        selection = treeview.get_selection()
        selection.unselect_all()
        selection.select_path(path)
        (model, rows) = selection.get_selected_rows()
        row = max(rows[0])
    if row == -1:
        return False
    if event.button == 3:
        guicomponents.display_filter_stack_popup_menu(row, treeview, _filter_stack_menu_item_selected, event)                                    
        return True
    return False

def _filter_stack_menu_item_selected(widget, data):
    item_id, row, treeview = data

    if item_id == "toggle":
        toggle_filter_active(row)
    if item_id == "reset":
        reset_filter_values()
    if item_id == "moveup":
        delete_row = row
        insert_row = row + 2
        if insert_row > len(clip.filters):
            insert_row = len(clip.filters)
        do_stack_move(insert_row, delete_row)
    if item_id == "movedown":
        delete_row = row + 1
        insert_row = row - 1
        if insert_row < 0:
            insert_row = 0
        do_stack_move(insert_row, delete_row)
        
def _quit_editing_clip_clicked(): # this is a button callback
    clear_clip()

def clear_clip():
    """
    Removes clip from effects editing gui.
    """
    global clip
    clip = None
    _set_no_clip_info()
    effect_selection_changed()
    update_stack_view()
    set_enabled(False)

def _set_no_clip_info():
    widgets.clip_info.set_no_clip_info()

def create_widgets():
    """
    Widgets for editing clip effects properties.
    """
    widgets.clip_info = guicomponents.ClipInfoPanel()
    
    widgets.exit_button = Gtk.Button()
    icon = Gtk.Image.new_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
    widgets.exit_button.set_image(icon)
    widgets.exit_button.connect("clicked", lambda w: _quit_editing_clip_clicked())
    widgets.exit_button.set_tooltip_text(_("Quit editing Clip in editor"))

    widgets.effect_stack_view = guicomponents.FilterSwitchListView(lambda ts: effect_selection_changed(), 
                                                                   toggle_filter_active, dnd_row_deleted, dnd_row_inserted)
                                                                   
    widgets.effect_stack_view.treeview.connect("button-press-event", lambda w,e, wtf: stack_view_pressed(), None)
    gui.effect_stack_list_view = widgets.effect_stack_view
    
    widgets.value_edit_box = Gtk.VBox()
    widgets.value_edit_frame = Gtk.Frame()
    widgets.value_edit_frame.set_shadow_type(Gtk.ShadowType.NONE)
    widgets.value_edit_frame.add(widgets.value_edit_box)

    widgets.add_effect_b = Gtk.Button()#_("Add"))
    widgets.add_effect_b.set_image(Gtk.Image.new_from_file(respaths.IMAGE_PATH + "filter_add.png"))
    widgets.del_effect_b = Gtk.Button() #_("Delete"))
    widgets.del_effect_b.set_image(Gtk.Image.new_from_file(respaths.IMAGE_PATH + "filter_delete.png"))
    widgets.toggle_all = Gtk.Button()
    widgets.toggle_all.set_image(Gtk.Image.new_from_file(respaths.IMAGE_PATH + "filters_all_toggle.png"))

    widgets.add_effect_b.connect("clicked", lambda w,e: add_effect_pressed(), None)
    widgets.del_effect_b.connect("clicked", lambda w,e: delete_effect_pressed(), None)
    widgets.toggle_all.connect("clicked", lambda w: toggle_all_pressed())

    widgets.hamburger_launcher = guicomponents.HamburgerPressLaunch(_hamburger_launch_pressed)
    guiutils.set_margins(widgets.hamburger_launcher.widget, 6, 8, 1, 0)    
    # These are created elsewhere and then monkeypatched here
    widgets.group_combo = None
    widgets.effect_list_view = None

    widgets.clip_info.set_tooltip_text(_("Clip being edited"))
    widgets.effect_stack_view.set_tooltip_text(_("Clip Filter Stack"))
    widgets.add_effect_b.set_tooltip_text(_("Add Filter to Clip Filter Stack"))
    widgets.del_effect_b.set_tooltip_text(_("Delete Filter from Clip Filter Stack"))
    widgets.toggle_all.set_tooltip_text(_("Toggle all Filters On/Off"))

def set_enabled(value):
    widgets.clip_info.set_enabled( value)
    widgets.add_effect_b.set_sensitive(value)
    widgets.del_effect_b.set_sensitive(value)
    widgets.effect_stack_view.treeview.set_sensitive(value)
    widgets.exit_button.set_sensitive(value)
    widgets.toggle_all.set_sensitive(value)
    widgets.hamburger_launcher.set_sensitive(value)
    widgets.hamburger_launcher.widget.queue_draw()

def update_stack_view():
    if clip != None:
        filter_infos = []
        for f in clip.filters:
            filter_infos.append(f.info)
        widgets.effect_stack_view.fill_data_model(filter_infos, clip.filters)
    else:
        widgets.effect_stack_view.fill_data_model([], [])

    widgets.effect_stack_view.treeview.queue_draw()

def update_stack_view_changed_blocked():
    global block_changed_update
    block_changed_update = True
    update_stack_view()
    block_changed_update = False
    
def add_currently_selected_effect():
    # Check we have clip
    if clip == None:
        return
        
    filter_info = get_selected_filter_info()
    action = get_filter_add_action(filter_info, clip)
    action.do_edit() # gui update in callback from EditAction object.
    
    updater.repaint_tline()

    filter_info = get_selected_filter_info()

def get_filter_add_action(filter_info, target_clip):
    if filter_info.multipart_filter == False:
        # Maybe show info on using alpha filters
        if filter_info.group == "Alpha":
            GLib.idle_add(_alpha_filter_add_maybe_info, filter_info)
    
        data = {"clip":target_clip, 
                "filter_info":filter_info,
                "filter_edit_done_func":filter_edit_done}
        action = edit.add_filter_action(data)
    else:
        data = {"clip":target_clip, 
                "filter_info":filter_info,
                "filter_edit_done_func":filter_edit_done}
        action = edit.add_multipart_filter_action(data)
    return action

def _alpha_filter_add_maybe_info(filter_info):
    if editorpersistance.prefs.show_alpha_info_message == True:
        dialogs.alpha_info_msg(_alpha_info_dialog_cb, translations.get_filter_name(filter_info.name))

def _alpha_info_dialog_cb(dialog, response_id, dont_show_check):
    if dont_show_check.get_active() == True:
        editorpersistance.prefs.show_alpha_info_message = False
        editorpersistance.save()

    dialog.destroy()

def get_selected_filter_info():
    # Get current selection on effects treeview - that's a vertical list.
    treeselection = gui.effect_select_list_view.treeview.get_selection()
    (model, rows) = treeselection.get_selected_rows()    
    row = rows[0]
    row_index = max(row)
    
    # Add filter
    group_name, filters_array = mltfilters.groups[gui.effect_select_combo_box.get_active()]
    return filters_array[row_index]
    
def add_effect_pressed():
    add_currently_selected_effect()

def delete_effect_pressed():
    if len(clip.filters) == 0:
        return

    # Block updates until we have set selected row
    global edit_effect_update_blocked
    edit_effect_update_blocked = True
    
    """
    treeselection = widgets.effect_stack_view.treeview.get_selection()
    (model, rows) = treeselection.get_selected_rows()
    
    try:
        row = rows[0]
    except:
        return # This fails when there are filters but no rows are selected
    """
    
    #row_index = current_filter_index
    data = {"clip":clip,
            "index":current_filter_index,
            "filter_edit_done_func":filter_edit_done}
    action = edit.remove_filter_action(data)
    action.do_edit()

    updater.repaint_tline()

    # Set last filter selected and display in editor
    edit_effect_update_blocked = False
    if len(clip.filters) == 0:
        effect_selection_changed() # to display info text
        return
    path = str(len(clip.filters) - 1)
    # Causes edit_effect_selected() called as it is the "change" listener
    widgets.effect_stack_view.treeview.get_selection().select_path(path)

def toggle_all_pressed():
    for i in range(0, len(clip.filters)):
        filter_object = clip.filters[i]
        filter_object.active = (filter_object.active == False)
        filter_object.update_mlt_disabled_value()
    
    update_stack_view()

def reset_filter_values():
    treeselection = widgets.effect_stack_view.treeview.get_selection()
    (model, rows) = treeselection.get_selected_rows()
    row = rows[0]
    row_index = max(row)
    
    clip.filters[row_index].reset_values(PROJECT().profile, clip)
    effect_selection_changed()

def toggle_filter_active(row, update_stack_view=True):
    filter_object = clip.filters[row]
    filter_object.active = (filter_object.active == False)
    filter_object.update_mlt_disabled_value()
    if update_stack_view == True:
        update_stack_view_changed_blocked()

def dnd_row_deleted(model, path):
    now = time.time()
    global stack_dnd_state, stack_dnd_event_time, stack_dnd_event_info
    if stack_dnd_state == INSERT_DONE:
        if (now - stack_dnd_event_time) < 0.1:
            stack_dnd_state = NOT_ON
            insert_row = int(stack_dnd_event_info)
            delete_row = int(path.to_string())
            stack_dnd_event_info = (insert_row, delete_row)
            # Because of dnd is gtk thing for some internal reason it needs to complete before we go on
            # touching storemodel again with .clear() or it dies in gtktreeviewaccessible.c
            GLib.idle_add(do_dnd_stack_move)
        else:
            stack_dnd_state = NOT_ON
    else:
        stack_dnd_state = NOT_ON
        
def dnd_row_inserted(model, path, tree_iter):
    global stack_dnd_state, stack_dnd_event_time, stack_dnd_event_info
    if stack_dnd_state == MOUSE_PRESS_DONE:
        stack_dnd_state = INSERT_DONE
        stack_dnd_event_time = time.time()
        stack_dnd_event_info = path.to_string()
    else:
        stack_dnd_state = NOT_ON

def do_dnd_stack_move():
    insert, delete_row = stack_dnd_event_info
    do_stack_move(insert, delete_row)
    
def do_stack_move(insert_row, delete_row):
    if abs(insert_row - delete_row) < 2: # filter was dropped on its previous place or cannot moved further up or down
        return
    
    # The insert insert_row and delete_row values are rows we get when listening 
    # "row-deleted" and "row-inserted" events after setting treeview "reorderable"
    # Dnd is detected by order and timing of these events together with mouse press event
    data = {"clip":clip,
            "insert_index":insert_row,
            "delete_index":delete_row,
            "filter_edit_done_func":filter_edit_done}
    action = edit.move_filter_action(data)
    action.do_edit()
            
def stack_view_pressed():
    global stack_dnd_state
    stack_dnd_state = MOUSE_PRESS_DONE

def effect_selection_changed():
    global keyframe_editor_widgets

    # Check we have clip
    if clip == None:
        keyframe_editor_widgets = []
        show_text_in_edit_area(_("No Clip"))
        return
    
    # Check we actually have filters so we can display one.
    # If not, clear previous filters from view.
    if len(clip.filters) == 0:
        show_text_in_edit_area(_("Clip Has No Filters"))
        keyframe_editor_widgets = []
        return
    
    # "changed" get's called twice when adding filter and selecting last
    # so we use this do this only once 
    if block_changed_update == True:
        return

    keyframe_editor_widgets = []

    # Get selected row which is also index of filter in clip.filters
    treeselection = widgets.effect_stack_view.treeview.get_selection()
    (model, rows) = treeselection.get_selected_rows()

    # If we don't get legal selection select first filter
    try:
        row = rows[0]
        filter_index = max(row)
    except:
        filter_index = 0

    filter_object = clip.filters[filter_index]
    
    global current_filter_index
    current_filter_index = filter_index
    
    # Create EditableProperty wrappers for properties
    editable_properties = propertyedit.get_filter_editable_properties(
                                                               clip, 
                                                               filter_object,
                                                               filter_index,
                                                               track,
                                                               clip_index)

    # Get editors and set them displayed
    vbox = Gtk.VBox(False, 0)
    try:
        filter_name = translations.filter_names[filter_object.info.name]
    except KeyError:
        filter_name = filter_object.info.name

    filter_name_label = Gtk.Label(label= "<b>" + filter_name + "</b>")
    filter_name_label.set_use_markup(True)
    vbox.pack_start(filter_name_label, False, False, 0)
    vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)

    if len(editable_properties) > 0:
        # Create editor row for each editable property
        for ep in editable_properties:
            editor_row = propertyeditorbuilder.get_editor_row(ep)
            if editor_row == None:
                continue

            # Set keyframe editor widget to be updated for frame changes if such is created 
            try:
                editor_type = ep.args[propertyeditorbuilder.EDITOR]
            except KeyError:
                editor_type = propertyeditorbuilder.SLIDER # this is the default value
            if ((editor_type == propertyeditorbuilder.KEYFRAME_EDITOR)
                or (editor_type == propertyeditorbuilder.KEYFRAME_EDITOR_RELEASE)
                or (editor_type == propertyeditorbuilder.KEYFRAME_EDITOR_CLIP)):
                    keyframe_editor_widgets.append(editor_row)
            
            # if slider property is being dedited as keyrame property
            if hasattr(editor_row, "is_kf_editor"):
                keyframe_editor_widgets.append(editor_row)

            vbox.pack_start(editor_row, False, False, 0)
            if not hasattr(editor_row, "no_separator"):
                vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)
            
        # Create NonMltEditableProperty wrappers for properties
        non_mlteditable_properties = propertyedit.get_non_mlt_editable_properties( clip, 
                                                                                   filter_object,
                                                                                   filter_index)

        # Extra editors. Editable properties may have already been created 
        # with "editor=no_editor" and now extra editors may be created to edit those
        # Non mlt properties are added as these are only need with extraeditors
        editable_properties.extend(non_mlteditable_properties)
        editor_rows = propertyeditorbuilder.get_filter_extra_editor_rows(filter_object, editable_properties)
        for editor_row in editor_rows:
            vbox.pack_start(editor_row, False, False, 0)
            if not hasattr(editor_row, "no_separator"):
                vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)
        vbox.pack_start(guiutils.pad_label(12,12), False, False, 0)
        
        vbox.pack_start(Gtk.Label(), True, True, 0)

    else:
        vbox.pack_start(Gtk.Label(label=_("No editable parameters")), True, True, 0)
    vbox.show_all()

    scroll_window = Gtk.ScrolledWindow()
    scroll_window.add_with_viewport(vbox)
    scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll_window.show_all()

    widgets.value_edit_frame.remove(widgets.value_edit_box)
    widgets.value_edit_frame.add(scroll_window)

    widgets.value_edit_box = scroll_window

def show_text_in_edit_area(text):
    vbox = Gtk.VBox(False, 0)

    filler = Gtk.EventBox()
    filler.add(Gtk.Label())
    vbox.pack_start(filler, True, True, 0)
    
    info = Gtk.Label(label=text)
    info.set_sensitive(False)
    filler = Gtk.EventBox()
    filler.add(info)
    vbox.pack_start(filler, False, False, 0)
    
    filler = Gtk.EventBox()
    filler.add(Gtk.Label())
    vbox.pack_start(filler, True, True, 0)

    vbox.show_all()

    scroll_window = Gtk.ScrolledWindow()
    scroll_window.add_with_viewport(vbox)
    scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll_window.show_all()

    widgets.value_edit_frame.remove(widgets.value_edit_box)
    widgets.value_edit_frame.add(scroll_window)

    widgets.value_edit_box = scroll_window
    
        
def clear_effects_edit_panel():
    widgets.value_edit_frame.remove(widgets.value_edit_box)
    label = Gtk.Label()
    widgets.value_edit_frame.add(label)
    widgets.value_edit_box = label

def filter_edit_done(edited_clip, index=-1):
    """
    EditAction object calls this after edits and undos and redos.
    """
    if edited_clip != clip: # This gets called by all undos/redos, we only want to update if clip being edited here is affected
        return
    
    global block_changed_update
    block_changed_update = True
    update_stack_view()
    block_changed_update = False

    # Select row in effect stack view and so display corresponding effect editor panel.
    if not(index < 0):
        widgets.effect_stack_view.treeview.get_selection().select_path(str(index))
    else: # no effects after edit, clear effect editor panel  
        clear_effects_edit_panel()

def display_kfeditors_tline_frame(frame):
    for kf_widget in keyframe_editor_widgets:
        kf_widget.display_tline_frame(frame)

def update_kfeditors_positions():
    if clip == None:
        return
    for kf_widget in keyframe_editor_widgets:
        kf_widget.update_clip_pos()

        
# ------------------------------------------------ SAVE; LOAD etc. from hamburger menu
def _hamburger_launch_pressed(widget, event):
    guicomponents.get_clip_effects_editor_hamburger_menu(event, _clip_hamburger_item_activated)
    
def _clip_hamburger_item_activated(widget, msg):
    if msg == "save":
        filter_object = clip.filters[current_filter_index]
        default_name = filter_object.info.name + _("_effect_values") + ".data"
        dialogs.save_effects_compositors_values(_save_effect_values_dialog_callback, default_name)
    elif msg == "load":
        dialogs.load_effects_compositors_values_dialog(_load_effect_values_dialog_callback)
    elif msg == "reset":
        _reset_filter_values()
    elif msg == "delete":
        _delete_effect()
        
def _save_effect_values_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        save_path = dialog.get_filenames()[0]
        filter_object = clip.filters[current_filter_index]
        effect_data = EffectValuesSaveData(filter_object)
        effect_data.save(save_path)
    
    dialog.destroy()

def _load_effect_values_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        load_path = dialog.get_filenames()[0]
        f = open(load_path)
        effect_data = pickle.load(f)
        
        filter_object = clip.filters[current_filter_index]
        
        if effect_data.data_applicable(filter_object.info):
            effect_data.set_effect_values(filter_object)
            effect_selection_changed()
        else:
            # Info window
            saved_effect_name = effect_data.info.name
            current_effect_name = filter_object.info.name
            primary_txt = _("Saved Filter data not applicaple for this Filter!")
            secondary_txt = _("Saved data is for ") + saved_effect_name + " Filter,\n" + _("current edited Filter is ") + current_effect_name + "."
            dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window)
    
    dialog.destroy()

def _reset_filter_values():
    filter_object = clip.filters[current_filter_index]
    info = filter_object.info
    if filter_object.info.multipart_filter == True:
        filter_object.value = info.multipart_value

    filter_object.properties = copy.deepcopy(info.properties)
    filter_object.non_mlt_properties = copy.deepcopy(info.non_mlt_properties)
        
    effect_selection_changed()

def _delete_effect():
    delete_effect_pressed()


class EffectValuesSaveData:
    
    def __init__(self, filter_object):
        self.info = filter_object.info
        self.multipart_filter = self.info.multipart_filter

        # Values of these are edited by the user.
        self.properties = copy.deepcopy(filter_object.properties)
        try:
            self.non_mlt_properties = copy.deepcopy(filter_object.non_mlt_properties)
        except:
            self.non_mlt_properties = [] # Versions prior 0.14 do not have non_mlt_properties and fail here on load

        if self.multipart_filter == True:
            self.value = filter_object.value
        else:
            self.value = None
        
    def save(self, save_path):
        with atomicfile.AtomicFileWriter(save_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(self, write_file)
        
    def data_applicable(self, filter_info):
        if isinstance(self.info, filter_info.__class__):
            return self.info.__dict__ == filter_info.__dict__
        return False
        
    def set_effect_values(self, filter_object):
        if self.multipart_filter == True:
            filter_object.value = self.value
         
        filter_object.properties = copy.deepcopy(self.properties)
        filter_object.non_mlt_properties = copy.deepcopy(self.non_mlt_properties)
         
    
