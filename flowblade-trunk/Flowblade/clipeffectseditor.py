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
import cairo
import copy
from gi.repository import GLib
from gi.repository import Gtk, Gdk
import pickle
import threading
import time

import appconsts
import atomicfile
import dialogs
import dialogutils
import dnd
import edit
import editorlayout
import editorpersistance
import editorstate
from editorstate import PROJECT
import gui
import guicomponents
import guiutils
import mltfilters
import propertyedit
import propertyeditorbuilder
import respaths
import tlinerender
import translations
import updater
import utils

_filter_stack = None

widgets = utils.EmptyClass()

_block_changed_update = False # Used to block unwanted callback update from "changed"
_block_stack_update = False # Used to block full stack update when adding new filter. 
                            # Otherwise we got 2 updates EditAction objects must always try to update
                            # on undo/redo.

# Property change polling.
# We didn't put a layer of indirection to look for and launch events on filter property edits
# so now we detect filter edits by polling. This has no performance impect, n is so small.
_edit_polling_thread = None
filter_changed_since_last_save = False

# This is updated when filter panel is displayed and cleared when removed.
# Used to update kfeditors with external tline frame position changes
keyframe_editor_widgets = []

# Filter stack DND requires some state info to be maintained to make sure that it's only done when certain events
# happen in a certain sequence.
TOP_HALF = 0
BOTTOM_HALF = 1

NOT_ON = 0
MOUSE_PRESS_DONE = 1
INSERT_DONE = 2
stack_dnd_state = NOT_ON
stack_dnd_event_time = 0.0
stack_dnd_event_info = None



# ---------------------------------------------------------- filter stack objects
class FilterFooterRow:
    
    def __init__(self, filter_object, filter_stack):
        self.filter_object = filter_object
        self.filter_stack = filter_stack
        
        surface = guiutils.get_cairo_image("filter_save")
        if editorpersistance.prefs.double_track_hights  == False:
            save_button = guicomponents.PressLaunch(self.save_pressed, surface, w=22, h=22)
        else:
            save_button = guicomponents.PressLaunch(self.save_pressed, surface, w=44, h=44)
        save_button.widget.set_tooltip_markup(_("Save effect values"))
        
        surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "filter_load.png")
        load_button = guicomponents.PressLaunch(self.load_pressed, surface, w=22, h=22)
        load_button.widget.set_tooltip_markup(_("Load effect values"))

        surface = guiutils.get_cairo_image("filter_reset")
        if editorpersistance.prefs.double_track_hights  == False:
            reset_button = guicomponents.PressLaunch(self.reset_pressed, surface, w=22, h=22)
        else:
            reset_button = guicomponents.PressLaunch(self.reset_pressed, surface, w=44, h=44)
        reset_button.widget.set_tooltip_markup(_("Reset effect values"))
        
        surface = guiutils.get_cairo_image("filters_mask_add")
        if editorpersistance.prefs.double_track_hights  == False:
            mask_button = guicomponents.PressLaunch(self.add_mask_pressed, surface, w=22, h=22)
        else:
            mask_button = guicomponents.PressLaunch(self.add_mask_pressed, surface, w=44, h=44)
        mask_button.widget.set_tooltip_markup(_("Add Filter Mask"))

        surface = guiutils.get_cairo_image("filters_move_up")
        move_up_button = guicomponents.PressLaunch(self.move_up_pressed, surface, w=22, h=22)
        move_up_button.widget.set_tooltip_markup(_("Move Filter Up"))

        surface = guiutils.get_cairo_image("filters_move_down")
        move_down_button = guicomponents.PressLaunch(self.move_down_pressed, surface, w=22, h=22)
        move_down_button.widget.set_tooltip_markup(_("Move Filter Down"))

        surface = guiutils.get_cairo_image("filters_move_top")
        move_top_button = guicomponents.PressLaunch(self.move_top_pressed, surface, w=22, h=22)
        move_top_button.widget.set_tooltip_markup(_("Move Filter To Top"))

        surface = guiutils.get_cairo_image("filters_move_bottom")
        move_bottom_button = guicomponents.PressLaunch(self.move_bottom_pressed, surface, w=22, h=22)
        move_bottom_button.widget.set_tooltip_markup(_("Move Filter To Bottom"))
        
        self.widget = Gtk.HBox(False, 0)
        self.widget.pack_start(guiutils.pad_label(4,5), False, False, 0)
        self.widget.pack_start(mask_button.widget, False, False, 0)
        self.widget.pack_start(guiutils.pad_label(2,5), False, False, 0)
        self.widget.pack_start(reset_button.widget, False, False, 0)
        self.widget.pack_start(guiutils.pad_label(12,5), False, False, 0)
        self.widget.pack_start(move_up_button.widget, False, False, 0)
        self.widget.pack_start(move_down_button.widget, False, False, 0)
        self.widget.pack_start(move_top_button.widget, False, False, 0)
        self.widget.pack_start(move_bottom_button.widget, False, False, 0)
        self.widget.pack_start(guiutils.pad_label(12,5), False, False, 0)
        self.widget.pack_start(save_button.widget, False, False, 0)
        self.widget.pack_start(load_button.widget, False, False, 0)

        self.widget.pack_start(Gtk.Label(), True, True, 0)
        self.widget.set_name("lighter-bg-widget")
            
    def save_pressed(self, w, e):
        default_name = self.filter_object.info.name + _("_effect_values") + ".data"
        dialogs.save_effects_compositors_values(_save_effect_values_dialog_callback, default_name, True, self.filter_object)

    def load_pressed(self, w, e):
        dialogs.load_effects_compositors_values_dialog(_load_effect_values_dialog_callback, True, self.filter_object)

    def reset_pressed(self, w, e):
        _reset_filter_values(self.filter_object)

    def add_mask_pressed(self, w, e):
        filter_index = self.filter_stack.get_filter_index(self.filter_object)
        _filter_mask_launch_pressed(w, e, filter_index)

    def move_up_pressed(self, w, e):
        from_index = self.filter_stack.get_filter_index(self.filter_object)
        if len(self.filter_stack.filter_stack) == 1:
            return
        if from_index == 0:
            return
        to_index = from_index - 1
        do_stack_move(self.filter_stack.clip, to_index, from_index)
        
    def move_down_pressed(self, w, e):
        from_index = self.filter_stack.get_filter_index(self.filter_object)
        if len(self.filter_stack.filter_stack) == 1:
            return
        if from_index == len(self.filter_stack.filter_stack) - 1:
            return
        to_index = from_index + 1
        do_stack_move(self.filter_stack.clip, to_index, from_index)
        
    def move_top_pressed(self, w, e):
        from_index = self.filter_stack.get_filter_index(self.filter_object)
        if len(self.filter_stack.filter_stack) == 1:
            return
        if from_index == 0:
            return
        to_index = 0
        do_stack_move(self.filter_stack.clip, to_index, from_index)
                
    def move_bottom_pressed(self, w, e):
        from_index = self.filter_stack.get_filter_index(self.filter_object)
        if len(self.filter_stack.filter_stack) == 1:
            return
        if from_index == len(self.filter_stack.filter_stack) - 1:
            return
        to_index = len(self.filter_stack.filter_stack) - 1
        do_stack_move(self.filter_stack.clip, to_index, from_index)


class FilterHeaderRow:
    
    def __init__(self, filter_object):
        name = translations.get_filter_name(filter_object.info.name)
        self.filter_name_label = Gtk.Label(label= "<b>" + name + "</b>")
        self.filter_name_label.set_use_markup(True)
        self.icon = Gtk.Image.new_from_pixbuf(filter_object.info.get_icon())

        hbox = Gtk.HBox(False, 0)
        hbox.pack_start(guiutils.pad_label(4,5), False, False, 0)
        hbox.pack_start(self.icon, False, False, 0)
        hbox.pack_start(self.filter_name_label, False, False, 0)
        hbox.pack_start(Gtk.Label(), True, True, 0)
        self.widget = hbox


class FilterStackItem:

    def __init__(self, filter_object, edit_panel, filter_stack):
        self.filter_object = filter_object
        self.filter_header_row = FilterHeaderRow(filter_object)

        self.edit_panel = edit_panel
        self.edit_panel_frame = Gtk.Frame()
        self.edit_panel_frame.add(edit_panel)
        self.edit_panel_frame.set_shadow_type(Gtk.ShadowType.NONE)
        
        self.filter_stack = filter_stack
        self.expander = Gtk.Expander()
        self.expander.set_label_widget(self.filter_header_row.widget)
        self.expander.add(self.edit_panel_frame)
        self.expander.set_label_fill(True)

        self.expander_frame = Gtk.Frame()
        self.expander_frame.add(self.expander)
        self.expander_frame.set_shadow_type(Gtk.ShadowType.NONE)
        guiutils.set_margins(self.expander_frame, 2, 0, 0, 0)
        
        self.active_check = Gtk.CheckButton()
        self.active_check.set_active(self.filter_object.active)
        self.active_check.connect("toggled", self.toggle_filter_active)
        guiutils.set_margins(self.active_check, 4, 0, 0, 0)

        self.active_check_vbox = Gtk.VBox(False, 0)
        self.active_check_vbox.pack_start(self.active_check, False, False, 0)
        self.active_check_vbox.pack_start(Gtk.Label(), True, True, 0)

        surface = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + "trash.png")
        trash_button = guicomponents.PressLaunch(self.trash_pressed, surface, w=22, h=22)
        
        self.trash_vbox = Gtk.VBox(False, 0)
        self.trash_vbox.pack_start(trash_button.widget, False, False, 0)
        self.trash_vbox.pack_start(Gtk.Label(), True, True, 0)
        
        self.widget = Gtk.HBox(False, 0)
        self.widget.pack_start(self.active_check_vbox, False, False, 0)
        self.widget.pack_start(self.expander_frame, True, True, 0)
        self.widget.pack_start(self.trash_vbox, False, False, 0)
        self.widget.pack_start(guiutils.pad_label(10,2), False, False, 0)
        self.widget.show_all()

    def trash_pressed(self, w, e):
        self.filter_stack.delete_filter_for_stack_item(self)
    
    def toggle_filter_active(self, widget):
        self.filter_object.active = (self.filter_object.active == False)
        self.filter_object.update_mlt_disabled_value()


class ClipFilterStack:

    def __init__(self, clip, track, clip_index):
        self.clip = clip
        self.track = track
        self.clip_index = clip_index
        
        # Create filter stack and GUI
        self.filter_stack = []
        self.filter_kf_editors = {} # filter_object -> [kf_editors]
        self.widget = Gtk.VBox(False, 0)
        for filter_index in range(0, len(clip.filters)):
            filter_object = clip.filters[filter_index]
            edit_panel, kf_editors = _get_filter_panel(clip, filter_object, filter_index, track, clip_index)
            self.filter_kf_editors[filter_object] = kf_editors
            footer_row = FilterFooterRow(filter_object, self)
            edit_panel.pack_start(footer_row.widget, False, False, 0)
            edit_panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
            stack_item = FilterStackItem(filter_object, edit_panel, self)
            self.filter_stack.append(stack_item)
            self.widget.pack_start(stack_item.widget, False, False, 0)
        
        self.widget.show_all()

    def get_filters(self):
        filters = []
        for stack_item in self.filter_stack:
            filters.append(stack_item.filter_object)
        return filters

    def reinit_stack_item(self, filter_object):
        stack_index = -1
        for i in range(0, len(self.filter_stack)):
            stack_item = self.filter_stack[i]
            if stack_item.filter_object is filter_object:
                stack_index = i 
        
        if stack_index != -1:
            # Remove panels from box
            children = self.widget.get_children()
            for child in children:
                self.widget.remove(child)
                
            # Remove old stack item for reseted filter.
            self.filter_stack.pop(stack_index)
            self.clear_kf_editors_from_update_list(filter_object)

            # Create new stack item
            edit_panel, kf_editors = _get_filter_panel(self.clip, filter_object, stack_index, self.track, self.clip_index)
            self.filter_kf_editors[filter_object] = kf_editors
            footer_row = FilterFooterRow(filter_object, self)
            edit_panel.pack_start(footer_row.widget, False, False, 0)
            edit_panel.pack_start(guiutils.pad_label(12,12), False, False, 0)
            stack_item = FilterStackItem(filter_object, edit_panel, self)
            
            # Put eveything back
            self.filter_stack.insert(stack_index, stack_item)
            for stack_item in self.filter_stack:
                self.widget.pack_start(stack_item.widget,False, False, 0)
                
            self.set_filter_item_expanded(stack_index)
            
    def get_clip_data(self):
        return (self.clip, self.track, self.clip_index)
    
    def get_filter_index(self, filter_object):
        return self.clip.filters.index(filter_object)

    def delete_filter_for_stack_item(self, stack_item):
        filter_index = self.filter_stack.index(stack_item)
        delete_effect_pressed(self.clip, filter_index)

    def stack_changed(self, clip):
        if len(clip.filters) != len(self.filter_stack):
            return True

        for i in range(0, len(clip.filters)):
            clip_filter_info = clip.filters[i].info
            stack_filter_info = self.filter_stack[i].filter_object.info
            
            if stack_filter_info.mlt_service_id != clip_filter_info.mlt_service_id:
                return True

        return False

    def clear_kf_editors_from_update_list(self, filter_object):
        kf_editors = self.filter_kf_editors[filter_object]
        global keyframe_editor_widgets
        for editor in kf_editors:
            try:
                keyframe_editor_widgets.remove(editor)
            except:
                pass
                print("Trying to remove non-existing editor from keyframe_editor_widgets")
                
        self.filter_kf_editors.pop(filter_object)

    def set_filter_item_expanded(self, filter_index):
        filter_stack_item = self.filter_stack[filter_index]
        filter_stack_item.expander.set_expanded(True)

    def set_all_filters_expanded_state(self, expanded):
        for i in range(0, len(self.filter_stack)):
            stack_item = self.filter_stack[i]
            stack_item.expander.set_expanded(expanded)
            
    def get_expanded(self):
        state_list = []
        for stack_item in self.filter_stack:
            state_list.append(stack_item.expander.get_expanded())
        return state_list

    def set_expanded(self, state_list):
        for i in range(0, len(self.filter_stack)):
            stack_item = self.filter_stack[i]
            stack_item.expander.set_expanded(state_list[i])


# -------------------------------------------------------------- GUI INIT
def get_clip_effects_editor_info_row():
    _create_widgets()

    info_row = Gtk.HBox(False, 2)
    info_row.pack_start(widgets.hamburger_launcher.widget, False, False, 0)
    info_row.pack_start(widgets.filter_add_launch.widget, True, True, 0)
    info_row.pack_start(Gtk.Label(), True, True, 0)
    info_row.pack_start(widgets.clip_info, False, False, 0)
    info_row.pack_start(Gtk.Label(), True, True, 0)

    return info_row

def _create_widgets():
    """
    Widgets for editing clip effects properties.
    """
    widgets.clip_info = guicomponents.ClipInfoPanel()
    
    widgets.value_edit_box = Gtk.VBox()
    widgets.value_edit_frame = Gtk.Frame()
    widgets.value_edit_frame.set_shadow_type(Gtk.ShadowType.NONE)
    widgets.value_edit_frame.add(widgets.value_edit_box)
    
    widgets.hamburger_launcher = guicomponents.HamburgerPressLaunch(_hamburger_launch_pressed)
    guiutils.set_margins(widgets.hamburger_launcher.widget, 6, 8, 1, 0)

    surface_active = guiutils.get_cairo_image("filter_add")
    surface_not_active = guiutils.get_cairo_image("filter_add_not_active")
    surfaces = [surface_active, surface_not_active]
    widgets.filter_add_launch = guicomponents.HamburgerPressLaunch(lambda w,e:_filter_add_menu_launch_pressed(w, e), surfaces)
    guiutils.set_margins(widgets.filter_add_launch.widget, 6, 8, 1, 0)
    
# ------------------------------------------------------------------- interface
def set_clip(clip, track, clip_index, show_tab=True):
    """
    Sets clip being edited and inits gui.
    """
    if _filter_stack != None:
        if clip == _filter_stack.clip and track == _filter_stack.track and clip_index == _filter_stack.clip_index and show_tab == False:
            return

    global keyframe_editor_widgets
    keyframe_editor_widgets = []

    widgets.clip_info.display_clip_info(clip, track, clip_index)
    set_enabled(True)
    update_stack(clip, track, clip_index)

    if len(clip.filters) > 0:
        pass # remove if nothing needed here.
    else:
        show_text_in_edit_area(_("Clip Has No Filters"))

    if show_tab:
        editorlayout.show_panel(appconsts.PANEL_FILTERS)

    global _edit_polling_thread
    # Close old polling
    if _edit_polling_thread != None:
        _edit_polling_thread.shutdown()
    # Start new polling
    _edit_polling_thread = PropertyChangePollingThread()
    _edit_polling_thread.start()

def refresh_clip():
    if _filter_stack == None:
        return 
    
    expanded_panels = _filter_stack.get_expanded()
    
    clip, track, clip_index = _filter_stack.get_clip_data()
    set_clip(clip, track, clip_index)

    _filter_stack.set_expanded(expanded_panels)

def get_clip_editor_clip_data():
    if _filter_stack == None:
        return None
    else:
        return _filter_stack.get_clip_data()

def clip_is_being_edited(clip):
    if _filter_stack == None:
        return False

    if _filter_stack.clip == clip:
        return True

    return False

def get_edited_clip():
    if _filter_stack == None:
        return None
    else:
        return  _filter_stack.clip

def set_filter_item_expanded(filter_index):
    if _filter_stack == None:
        return 
    
    _filter_stack.set_filter_item_expanded(filter_index)

def effect_select_row_double_clicked(treeview, tree_path, col, effect_select_combo_box):
    if _filter_stack == None:
        return

    row_index = int(tree_path.get_indices()[0])
    group_index = effect_select_combo_box.get_active()

    _add_filter_from_effect_select_panel(row_index, group_index)

def add_currently_selected_effect():
    # Currently selected in effect select panel, not here.
    treeselection = gui.effect_select_list_view.treeview.get_selection()
    (model, rows) = treeselection.get_selected_rows()    
    row = rows[0]
    row_index = max(row)
    group_index = gui.effect_select_combo_box.get_active()

    _add_filter_from_effect_select_panel(row_index, group_index)

def get_currently_selected_filter_info():
    # Currently selected in effect select panel, not here.
    treeselection = gui.effect_select_list_view.treeview.get_selection()
    (model, rows) = treeselection.get_selected_rows()    
    row = rows[0]
    row_index = max(row)
    group_index = gui.effect_select_combo_box.get_active()
    group_name, filters_array = mltfilters.groups[group_index]
    filter_info = filters_array[row_index]
    return filter_info
    
def _add_filter_from_effect_select_panel(row_index, group_index):
    # Add filter
    group_name, filters_array = mltfilters.groups[group_index]
    filter_info = filters_array[row_index]

    data = {"clip":_filter_stack.clip, 
            "filter_info":filter_info,
            "filter_edit_done_func":filter_edit_done_stack_update}
    action = edit.add_filter_action(data)

    set_stack_update_blocked()
    action.do_edit()
    set_stack_update_unblocked()

    clip, track, clip_index = _filter_stack.get_clip_data()
    set_clip(clip, track, clip_index)

    updater.repaint_tline()

def _quit_editing_clip_clicked(): # this is a button callback
    clear_clip()

def clear_clip():
    """
    Removes clip from effects editing gui.
    """
    global _filter_stack
    _filter_stack = None
    _set_no_clip_info()
    show_text_in_edit_area(_("No Clip"))

    set_enabled(False)
    shutdown_polling()

def _set_no_clip_info():
    widgets.clip_info.set_no_clip_info()

def set_enabled(value):
    widgets.clip_info.set_enabled(value)
    widgets.hamburger_launcher.set_sensitive(value)
    widgets.hamburger_launcher.widget.queue_draw()
    widgets.filter_add_launch.set_sensitive(value)
    widgets.filter_add_launch.widget.queue_draw()

def set_stack_update_blocked():
    global _block_stack_update
    _block_stack_update = True

def set_stack_update_unblocked():
    global _block_stack_update
    _block_stack_update = False

def update_stack(clip, track, clip_index):
    new_stack = ClipFilterStack(clip, track, clip_index)
    global _filter_stack
    _filter_stack = new_stack

    scroll_window = Gtk.ScrolledWindow()
    scroll_window.add_with_viewport(_filter_stack.widget)
    scroll_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll_window.show_all()

    global widgets
    widgets.value_edit_frame.remove(widgets.value_edit_box)
    widgets.value_edit_frame.add(scroll_window)

    widgets.value_edit_box = scroll_window
    
def update_stack_changed_blocked():
    global _block_changed_update
    _block_changed_update = True
    update_stack()
    _block_changed_update = False

def _alpha_filter_add_maybe_info(filter_info):
    if editorpersistance.prefs.show_alpha_info_message == True and \
       editorstate. current_sequence().compositing_mode != appconsts.COMPOSITING_MODE_STANDARD_FULL_TRACK:
        dialogs.alpha_info_msg(_alpha_info_dialog_cb, translations.get_filter_name(filter_info.name))

def _alpha_info_dialog_cb(dialog, response_id, dont_show_check):
    if dont_show_check.get_active() == True:
        editorpersistance.prefs.show_alpha_info_message = False
        editorpersistance.save()

    dialog.destroy()

def get_filter_add_action(filter_info, target_clip):
    # Maybe show info on using alpha filters
    if filter_info.group == "Alpha":
        GLib.idle_add(_alpha_filter_add_maybe_info, filter_info)
    data = {"clip":target_clip, 
            "filter_info":filter_info,
            "filter_edit_done_func":filter_edit_done_stack_update}
    action = edit.add_filter_action(data)
    return action

def delete_effect_pressed(clip, filter_index):
    set_stack_update_blocked()

    current_filter = clip.filters[filter_index]
    
    if current_filter.info.filter_mask_filter == "":
        # Clear keyframe editors from update list
        _filter_stack.clear_kf_editors_from_update_list(current_filter)

        # Regular filters
        data = {"clip":clip,
                "index":filter_index,
                "filter_edit_done_func":filter_edit_done_stack_update}
        action = edit.remove_filter_action(data)
        action.do_edit()

    else:
        # Filter mask filters.
        index_1 = -1
        index_2 = -1
        for i in range(0, len(clip.filters)):
            f = clip.filters[i]
            if f.info.filter_mask_filter != "":
                if index_1 == -1:
                    index_1 = i
                else:
                    index_2 = i

        # Clear keyframe editors from update list
        filt_1 = clip.filters[index_1]
        filt_2 = clip.filters[index_2]
        _filter_stack.clear_kf_editors_from_update_list(filt_1)
        _filter_stack.clear_kf_editors_from_update_list(filt_2)
        
        # Do edit
        data = {"clip":clip,
                "index_1":index_1,
                "index_2":index_2,
                "filter_edit_done_func":filter_edit_done_stack_update}
        action = edit.remove_two_filters_action(data)
        action.do_edit()
        
    set_stack_update_unblocked()

    clip, track, clip_index = _filter_stack.get_clip_data()
    set_clip(clip, track, clip_index)

    updater.repaint_tline()

def _save_stack_pressed():
    default_name = _("unnamed_stack_values") + ".data"
    dialogs.save_effects_compositors_values(_save_effect_stack_values_dialog_callback, default_name, True, None, True)

def _load_stack_pressed():
    dialogs.load_effects_compositors_values_dialog(_load_effect_stack_values_dialog_callback, True, None, True)
        
def _toggle_all_pressed():
    if _filter_stack == None:
        return False
        
    for i in range(0, len(_filter_stack.clip.filters)):
        filter_object = _filter_stack.clip.filters[i]
        filter_object.active = (filter_object.active == False)
        filter_object.update_mlt_disabled_value()

    clip, track, clip_index = _filter_stack.get_clip_data()
    expanded_panels = _filter_stack.get_expanded()
    update_stack(clip, track, clip_index)
    _filter_stack.set_expanded(expanded_panels)

def do_stack_move(clip, insert_row, delete_row):
    data = {"clip":clip,
            "insert_index":insert_row,
            "delete_index":delete_row,
            "filter_edit_done_func":filter_edit_done_stack_update}
    action = edit.move_filter_action(data)
    set_stack_update_blocked()
    action.do_edit()
    set_stack_update_unblocked()
    
def reinit_stack_if_needed(force_update):
    clip, track, clip_index = _filter_stack.get_clip_data()
    if _filter_stack.stack_changed(clip) == True or force_update == True:
        # expanded state here 
        set_clip(clip, track, clip_index, show_tab=True)

def _get_filter_panel(clip, filter_object, filter_index, track, clip_index):
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

    filter_keyframe_editor_widgets = []

    vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)

    if len(editable_properties) > 0:
        # Create editor row for each editable property
        for ep in editable_properties:
            editor_row = propertyeditorbuilder.get_editor_row(ep)
            if editor_row == None:
                continue
            editor_row.set_name("editor-row-widget")
            # Set keyframe editor widget to be updated for frame changes if such is created 
            try:
                editor_type = ep.args[propertyeditorbuilder.EDITOR]
            except KeyError:
                editor_type = propertyeditorbuilder.SLIDER # this is the default value
            
            if ((editor_type == propertyeditorbuilder.KEYFRAME_EDITOR)
                or (editor_type == propertyeditorbuilder.KEYFRAME_EDITOR_RELEASE)
                or (editor_type == propertyeditorbuilder.KEYFRAME_EDITOR_CLIP)
                or (editor_type == propertyeditorbuilder.FILTER_RECT_GEOM_EDITOR)
                or (editor_type == propertyeditorbuilder.KEYFRAME_EDITOR_CLIP_FADE_FILTER)):
                    keyframe_editor_widgets.append(editor_row)
                    filter_keyframe_editor_widgets.append(editor_row)

            # if slider property is being edited as keyrame property
            if hasattr(editor_row, "is_kf_editor"):
                keyframe_editor_widgets.append(editor_row)
                filter_keyframe_editor_widgets.append(editor_row)

            vbox.pack_start(editor_row, False, False, 0)
            if not hasattr(editor_row, "no_separator"):
                vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)
            
        # Create NonMltEditableProperty wrappers for properties
        non_mlteditable_properties = propertyedit.get_non_mlt_editable_properties( clip, 
                                                                                   filter_object,
                                                                                   filter_index)

        # Extra editors. Editable properties may have already been created 
        # with "editor=no_editor" and now extra editors may be created to edit those
        # Non mlt properties are added as these are only needed with extraeditors
        editable_properties.extend(non_mlteditable_properties)
        editor_rows = propertyeditorbuilder.get_filter_extra_editor_rows(filter_object, editable_properties)
        for editor_row in editor_rows:
            vbox.pack_start(editor_row, False, False, 0)
            if not hasattr(editor_row, "no_separator"):
                vbox.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)
    else:
        vbox.pack_start(Gtk.Label(label=_("No editable parameters")), True, True, 0)
    vbox.show_all()

    return (vbox, filter_keyframe_editor_widgets)

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

def filter_edit_done_stack_update(edited_clip, index=-1):
    """
    EditAction object calls this after edits and undos and redos.
    Methods updates filter stack to new state. 
    """
    if _block_stack_update == True:
        return
        
    if edited_clip != get_edited_clip(): # This gets called by all undos/redos, we only want to update if clip being edited here is affected
        return

    global _block_changed_update
    _block_changed_update = True
    update_stack()
    _block_changed_update = False

    # Select row in effect stack view and to display corresponding effect editor panel.
    if not(index < 0):
        widgets.effect_stack_view.treeview.get_selection().select_path(str(index))
    else: # no effects after edit, clear effect editor panel
        clear_effects_edit_panel()

def filter_edit_multi_done_stack_update(clips):
    #print(clips)
    for clip in clips:
        if clip == get_edited_clip():
             clear_clip()

def display_kfeditors_tline_frame(frame):
    for kf_widget in keyframe_editor_widgets:
        kf_widget.display_tline_frame(frame)

def update_kfeditors_sliders(frame):
    for kf_widget in keyframe_editor_widgets:
        kf_widget.update_slider_value_display(frame)
        
def update_kfeditors_positions():
    if _filter_stack == None:
        return 

    for kf_widget in keyframe_editor_widgets:
        kf_widget.update_clip_pos()


# ------------------------------------------------ FILTER MASK 
def _filter_mask_launch_pressed(widget, event, filter_index):
    filter_names, filter_msgs = mltfilters.get_filter_mask_start_filters_data()
    guicomponents.get_filter_mask_menu(event, _filter_mask_item_activated, filter_names, filter_msgs, filter_index)

def _filter_mask_item_activated(widget, data):
    if _filter_stack == None:
        return False
    
    clip, track, clip_index = _filter_stack.get_clip_data()
    full_stack_mask, msg, current_filter_index = data
    
    filter_info_1 = mltfilters.get_filter_mask_filter(msg)
    filter_info_2 = mltfilters.get_filter_mask_filter("Mask - End")

    if full_stack_mask == True:
        index_1 = 0
        index_2 = len(clip.filters) + 1
    else:
        if current_filter_index != -1:
            index_1 = current_filter_index
            index_2 = current_filter_index + 2
        else:
            index_1 = 0
            index_2 = len(clip.filters) + 1

    data = {"clip":clip, 
            "filter_info_1":filter_info_1,
            "filter_info_2":filter_info_2,
            "index_1":index_1,
            "index_2":index_2,
            "filter_edit_done_func":filter_edit_done_stack_update}
    action = edit.add_two_filters_action(data)

    set_stack_update_blocked()
    action.do_edit()
    set_stack_update_unblocked()

    set_clip(clip, track, clip_index)
    _filter_stack.set_filter_item_expanded(current_filter_index + 1)

def _clip_has_filter_mask_filter():
    if clip == None:
        return False
    
    for f in clip.filters:
        if f.info.filter_mask_filter != "":
            return True
          
    return False

# ------------------------------------------------ SAVE, LOAD etc. from hamburger menu
def _hamburger_launch_pressed(widget, event):
    guicomponents.get_clip_effects_editor_hamburger_menu(event, _clip_hamburger_item_activated)

def _clip_hamburger_item_activated(widget, msg):
    if msg == "fade_length":
        dialogs.set_fade_length_default_dialog(_set_fade_length_dialog_callback, PROJECT().get_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH))

    if _filter_stack == None:
        return False
    
    if msg == "close":
        clear_clip()
    elif  msg == "expanded":
        _filter_stack.set_all_filters_expanded_state(True)
    elif  msg == "unexpanded":
        _filter_stack.set_all_filters_expanded_state(False)
    elif  msg == "toggle":
        _toggle_all_pressed()
    elif  msg == "save_stack":
        _save_stack_pressed()
    elif  msg == "load_stack":
        _load_stack_pressed()

def _filter_add_menu_launch_pressed(w, event):
    if _filter_stack != None:
        clip = _filter_stack.clip
        track = _filter_stack.track 
        guicomponents.display_effect_panel_filters_menu(event, clip, track, _filter_menu_callback)
            
def _filter_menu_callback(w, data):
    clip, track, item_id, item_data = data
    x, filter_info = item_data

    action = get_filter_add_action(filter_info, clip)
    set_stack_update_blocked() # We update stack on set_clip below
    action.do_edit()
    set_stack_update_unblocked()

    # (re)open clip in editor.
    index = track.clips.index(clip)
    set_clip(clip, track, index)
    set_filter_item_expanded(len(clip.filters) - 1)
    
def _save_effect_values_dialog_callback(dialog, response_id, filter_object):
    if response_id == Gtk.ResponseType.ACCEPT:
        save_path = dialog.get_filenames()[0]
        effect_data = EffectValuesSaveData(filter_object)
        effect_data.save(save_path)
    
    dialog.destroy()

def _load_effect_values_dialog_callback(dialog, response_id, filter_object):
    if response_id == Gtk.ResponseType.ACCEPT:
        load_path = dialog.get_filenames()[0]
        effect_data = utils.unpickle(load_path)
        
        if effect_data.data_applicable(filter_object.info):
            effect_data.set_effect_values(filter_object)
            _filter_stack.reinit_stack_item(filter_object)
        else:
            # Info window
            saved_effect_name = effect_data.info.name
            current_effect_name = filter_object.info.name
            primary_txt = _("Saved Filter data not applicaple for this Filter!")
            secondary_txt = _("Saved data is for ") + saved_effect_name + " Filter,\n" + _("current edited Filter is ") + current_effect_name + "."
            dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window)
    
    dialog.destroy()

def _save_effect_stack_values_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        save_path = dialog.get_filenames()[0]
        stack_data = EffectStackSaveData()
        stack_data.save(save_path)
    dialog.destroy()

def _load_effect_stack_values_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        load_path = dialog.get_filenames()[0]
        stack_data = utils.unpickle(load_path)

        for effect_data in stack_data.effects_data:
            filter_info, properties, non_mlt_properties = effect_data
      
            data = {"clip":_filter_stack.clip, 
                    "filter_info":filter_info,
                    "filter_edit_done_func":filter_edit_done_stack_update}
            action = edit.add_filter_action(data)

            set_stack_update_blocked()
            action.do_edit()
            set_stack_update_unblocked()
    
            filters = _filter_stack.get_filters()
            filter_object = filters[len(filters) - 1]
    
            filter_object.properties = copy.deepcopy(properties)
            filter_object.non_mlt_properties = copy.deepcopy(non_mlt_properties)
            filter_object.update_mlt_filter_properties_all()

            _filter_stack.reinit_stack_item(filter_object)
                    
    dialog.destroy()

def _reset_filter_values(filter_object):
        filter_object.properties = copy.deepcopy(filter_object.info.properties)
        filter_object.non_mlt_properties = copy.deepcopy(filter_object.info.non_mlt_properties)
        filter_object.update_mlt_filter_properties_all()
                
        _filter_stack.reinit_stack_item(filter_object)

def _set_fade_length_dialog_callback(dialog, response_id, spin):
    if response_id == Gtk.ResponseType.ACCEPT:
        default_length = int(spin.get_value())
        PROJECT().set_project_property(appconsts.P_PROP_DEFAULT_FADE_LENGTH, default_length)
        
    dialog.destroy()


class EffectValuesSaveData:
    
    def __init__(self, filter_object):
        self.info = filter_object.info
        self.multipart_filter = self.info.multipart_filter # DEPRECATED

        # Values of these are edited by the user.
        self.properties = copy.deepcopy(filter_object.properties)
        try:
            self.non_mlt_properties = copy.deepcopy(filter_object.non_mlt_properties)
        except:
            self.non_mlt_properties = [] # Versions prior 0.14 do not have non_mlt_properties and fail here on load

        if self.multipart_filter == True: # DEPRECATED
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
        if self.multipart_filter == True: # DEPRECATED
            filter_object.value = self.value
         
        filter_object.properties = copy.deepcopy(self.properties)
        filter_object.non_mlt_properties = copy.deepcopy(self.non_mlt_properties)
        filter_object.update_mlt_filter_properties_all()

class EffectStackSaveData:
    def __init__(self):
        self.effects_data = []
        self.empty = True
        filters = _filter_stack.get_filters()
        if len(filters) > 0:
            self.empty = False
            for f in filters:
                self.effects_data.append((f.info,
                                          copy.deepcopy(f.properties),
                                          copy.deepcopy(f.non_mlt_properties)))
                                      
    def save(self, save_path):
        with atomicfile.AtomicFileWriter(save_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(self, write_file)

    
# ------------------------------------------------------- CHANGE POLLING
def shutdown_polling():
    global _edit_polling_thread
    if _edit_polling_thread != None:
        _edit_polling_thread.shutdown()
        _edit_polling_thread = None


class PropertyChangePollingThread(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.last_properties = None
        
    def run(self):

        self.running = True
        while self.running:
            
            if _filter_stack == None:
                self.shutdown()
            else:
                if self.last_properties == None:
                    self.last_properties = self.get_clip_filters_properties()
                
                new_properties = self.get_clip_filters_properties()
                
                changed = False
                for new_filt_props, old_filt_props in zip(new_properties, self.last_properties):
                        for new_prop, old_prop in zip(new_filt_props, old_filt_props):
                            if new_prop != old_prop:
                                changed = True

                if changed:
                    global filter_changed_since_last_save
                    filter_changed_since_last_save = True
                    tlinerender.get_renderer().timeline_changed()

                self.last_properties = new_properties
                
                time.sleep(1.0)

    def get_clip_filters_properties(self):
        filters_properties = []
        for filt in _filter_stack.get_filters():
            filt_props = []
            for prop in filt.properties:
                filt_props.append(copy.deepcopy(prop))

            filters_properties.append(filt_props)
        
        return filters_properties
        
    def shutdown(self):
        self.running = False
