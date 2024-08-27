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

"""
Thís module handels creating, editing and cloning of
Generators.

Generators are container clips that use Fluxity Scripts to render 
clips on timeline, see e.g. fluxity.py, containerclip.py, containeractions.py and simpleeditors.py.

Naming was changed to 'Generator' from 'Media Plugin' at the last moment before release,
so all code here refers to 'media plugins' instead of 'generators'.
"""  


from gi.repository import Gtk, GObject, Pango, Gio

import cairo
import copy
import hashlib
import json
import os
import pickle

import appconsts
import atomicfile
import cairoarea
import containerclip
import dialogs
import dialogutils
import editorlayout
from editorstate import current_sequence
import fluxity
import gui
import guicomponents
import guipopover
import guiutils
import mltprofiles
import positionbar
import respaths
import simpleeditors
import toolsencoding
import translations
import userfolders
import utils

MONITOR_WIDTH = 500
MONITOR_HEIGHT = -1
PREVIEW_WIDTH = 320

SIMPLE_EDITOR_LEFT_WIDTH = 150

_plugins = []
_plugins_groups = []

_add_plugin_window = None

_selected_plugin = None
_current_screenshot_surface = None
_current_plugin_data_object = None
_current_render_data = None
_preview_surface = None

widgets = utils.EmptyClass()
_edit_panel = None
_action_object = None
_clip = None 
_preview_popover = None
_preview_canvas = None

# --------------------------------------------------------- plugin
class MediaPlugin:
    
    def __init__(self, folder, script_file, name, category, default_render):
        self.folder = folder
        self.script_file = script_file # This is a fluxity script.
        self.name = name
        self.category = category
        self.default_render = default_render
    
    def get_screenshot_file(self):
        return respaths.MEDIA_PLUGINS_PATH + self.folder + "/screenshot.png"
    
    def get_screenshot_surface(self):
        return cairo.ImageSurface.create_from_png(self.get_screenshot_file())

    def get_plugin_script_file(self):
        script_file = respaths.MEDIA_PLUGINS_PATH + self.folder + "/" + self.script_file
        return script_file


# --------------------------------------------------------------- interface
def init():
    # Load Plugins
    plugins_list_json = open(respaths.MEDIA_PLUGINS_PATH + "plugins.json")
    plugins_obj = json.load(plugins_list_json)
    
    global _plugins
    plugins_list = plugins_obj["plugins"]
    for plugin_data in plugins_list:
        plugin = MediaPlugin(plugin_data["folder"], plugin_data["scriptfile"], plugin_data["name"], plugin_data["category"], plugin_data["defaultrender"])
        _plugins.append(plugin)
    
    load_groups = {}
    for plugin in _plugins:
        try:
            translated_group_name = translations.get_plugin_group_name(plugin.category)
        except:
            translated_group_name = "Misc"

        try:
            group = load_groups[translated_group_name]
            group.append(plugin)
        except:
            load_groups[translated_group_name] = [plugin]

    sorted_keys = sorted(load_groups.keys())
    global _plugins_groups
    for gkey in sorted_keys:
        group = load_groups[gkey]
        add_group = sorted(group, key=lambda plugin: plugin.name)
        _plugins_groups.append((gkey, add_group))

def show_add_media_plugin_window():
    global _add_plugin_window, _current_render_data
    _current_render_data = toolsencoding.create_container_clip_default_render_data_object(current_sequence().profile)
    _add_plugin_window = AddMediaPluginWindow()

def _close_window():
    global _add_plugin_window
    _add_plugin_window.set_visible(False)
    _add_plugin_window.destroy()

def _close_clicked():
    _close_window()

# ------------------------------------------------------------ functionality
def _get_categories_list():
    categories_list = []
    # categories_list is list of form [("category_name", [category_items]), ...]
    # with category_items list of form ["item_name", ...]
             
    for group in _plugins_groups:
        group_name, group_plugins = group
        plugins_list = []
        for plugin in group_plugins:
            plugins_list.append((translations.get_plugin_name(plugin.name), plugin))
        
        categories_list.append((translations.get_plugin_group_name(group_name), plugins_list))
    
    return categories_list  

# This method is used by scriptool.py create sub menu to load generator code into 
# editor window as an example.
def fill_media_plugin_sub_menu_gio(app, menu, callback):
    for group_data in _plugins_groups:
        group_name, group = group_data
        group_name_translated = translations.get_plugin_group_name(group_name)
        sub_menu = Gio.Menu.new()
        menu.append_submenu(group_name_translated, sub_menu)
        for plugin in group:
            label = translations.get_plugin_name(plugin.name)
            item_id = plugin.name.lower().replace(" ", "_")
            sub_menu.append(label, "app." + item_id) 
            
            action = Gio.SimpleAction(name=item_id)
            msg_string = plugin.folder + "/" + plugin.script_file
            action.connect("activate", lambda w, e, msg:callback(msg), msg_string)
            app.add_action(action)
    
def _add_media_plugin():
    script_file = _selected_plugin.get_plugin_script_file()
    md_str = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
    screenshot_file = userfolders.get_thumbnail_dir() + md_str +  ".png"
    fctx = _add_plugin_window._render_preview(int(_add_plugin_window.length_spin.get_value()/2))
    fctx.priv_context.frame_surface.write_to_png(screenshot_file)
    _current_plugin_data_object["editors_list"] = simpleeditors.get_editors_data_as_editors_list(_add_plugin_window.plugin_editors.editor_widgets)
    _current_plugin_data_object["length"] = int(_add_plugin_window.length_spin.get_value())
    _current_plugin_data_object["groups_list"] = fctx.groups
    
    if _add_plugin_window.import_select.get_active() == 0:
        _close_window()
        # Add as Container Clip
        containerclip.create_fluxity_media_item_from_plugin(script_file, screenshot_file, _current_plugin_data_object, None, _selected_plugin.default_render)
    else:
        # Add as Rendered Clip.
        _close_window()
        # We need to have a containerclip.ContainerClipData object to utilize container clips code to render a video clip.
        container_data = containerclip.ContainerClipData(appconsts.CONTAINER_CLIP_FLUXITY, _selected_plugin.get_plugin_script_file(), None)
        container_data.data_slots["icon_file"] = screenshot_file
        container_data.data_slots["fluxity_plugin_edit_data"] = _current_plugin_data_object
        container_data.render_data = _current_render_data
        container_data.unrendered_length = _current_plugin_data_object["length"]
        containerclip.create_renderered_fluxity_media_item(container_data, _current_plugin_data_object["length"]) 

def add_media_plugin_clone(data):
    dialogs.get_media_plugin_length(_clone_properties_callback, data)

def _clone_properties_callback(dialog, response_id, data, length_spin, name_entry):
    clip, track, item_id, item_data = data
    new_length = length_spin.get_value()
    name = name_entry.get_text()
    dialog.destroy()

    if response_id != Gtk.ResponseType.ACCEPT:
        return

    old_cd = clip.container_data
    
    if name == "":
        name = clip.name

    md_str = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
    screenshot_file = userfolders.get_thumbnail_dir() + md_str +  ".png"

    script_file = open(old_cd.program)
    user_script = script_file.read()
        
    profile_file_path = mltprofiles.get_profile_file_path(current_sequence().profile.description())

    fctx = fluxity.render_preview_frame(user_script, script_file, int(new_length / 2), new_length, None, profile_file_path, json.dumps(old_cd.data_slots["fluxity_plugin_edit_data"]["editors_list"]))
    fctx.priv_context.frame_surface.write_to_png(screenshot_file)

    new_plugin_edit_data = copy.deepcopy(old_cd.data_slots["fluxity_plugin_edit_data"])
    new_plugin_edit_data["name"] = name
    new_plugin_edit_data["length"] = int(new_length)

    default_render = toolsencoding.get_render_type_from_render_data(old_cd.render_data)
 
    containerclip.create_fluxity_media_item_from_plugin(old_cd.program, screenshot_file, new_plugin_edit_data, None, default_render)

def create_plugin_assests_for_media_import(old_cd):
    md_str = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
    screenshot_file = userfolders.get_thumbnail_dir() + md_str +  ".png"

    new_length = old_cd.unrendered_length
    
    script_file = open(old_cd.program)
    user_script = script_file.read()
        
    profile_file_path = mltprofiles.get_profile_file_path(current_sequence().profile.description())

    fctx = fluxity.render_preview_frame(user_script, script_file, int(new_length / 2), new_length, None, profile_file_path, json.dumps(old_cd.data_slots["fluxity_plugin_edit_data"]["editors_list"]))
    fctx.priv_context.frame_surface.write_to_png(screenshot_file)

    new_plugin_edit_data = copy.deepcopy(old_cd.data_slots["fluxity_plugin_edit_data"])

    return (old_cd.program, screenshot_file, new_plugin_edit_data)
    
def get_plugin_code(plugin_folder_and_script):
    script_file = get_plugin_script_path(plugin_folder_and_script)
    args_file = open(script_file)
    return args_file.read()

def get_plugin_script_path(plugin_folder_and_script):
    return respaths.MEDIA_PLUGINS_PATH + plugin_folder_and_script

# --------------------------------------------------------- Window
class AddMediaPluginWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)
        
        self.producer = PosBarProducer()
        
        self.set_modal(True)
        self.set_transient_for(gui.editor_window.window)
        self.set_title(_("Add Generator"))
        self.connect("delete-event", lambda w, e:_close_window())

        # categories_list is list of form [("category_name", [category_items]), ...]
        # with category_items list of form ["item_name", ...]
        self.plugin_select = guicomponents.CategoriesModelComboBoxWithData(_get_categories_list())
        self.plugin_select.set_changed_callback(self._plugin_selection_changed)

        plugin_label = Gtk.Label(label=_("Generator:"))
        plugin_select_row_left = guiutils.get_two_column_box(plugin_label, self.plugin_select.widget, 220)

        surface = guiutils.get_cairo_image("info_launch")
        self.info_launch = guicomponents.PressLaunch(self._show_info, surface, w=22, h=22)

        plugin_select_row = Gtk.HBox(False, 2)
        plugin_select_row.pack_start(plugin_select_row_left, True, True, 0)
        plugin_select_row.pack_start(self.info_launch.widget, False, False, 0)
        plugin_select_row.set_margin_bottom(24)
                    
        global MONITOR_HEIGHT
        MONITOR_HEIGHT = int(MONITOR_WIDTH * float(current_sequence().profile.display_aspect_den()) / float(current_sequence().profile.display_aspect_num()))
        self.screenshot_canvas = cairoarea.CairoDrawableArea2(MONITOR_WIDTH, MONITOR_HEIGHT, self._draw_screenshot)
        guiutils.set_margins(self.screenshot_canvas, 0, 8, 0, 0)

        self.frame_display = Gtk.Label(label=_("Clip Frame"))
        self.frame_display.set_margin_end(2)
        
        self.frame_select = Gtk.SpinButton.new_with_range (0, 200, 1)
        self.frame_select.set_value(0)
        
        self.preview_button = Gtk.Button(label=_("Preview"))
        self.preview_button.connect("clicked", lambda w: self._show_preview())

        # Control row
        self.tc_display = guicomponents.MonitorTCDisplay(56)
        self.tc_display.use_internal_frame = True
        self.tc_display.widget.set_valign(Gtk.Align.CENTER)
        self.tc_display.use_internal_fps = True
        self.tc_display.display_tc = False
        
        self.pos_bar = positionbar.PositionBar(False)
        self.pos_bar.set_listener(self.position_listener)
        self.pos_bar.mouse_press_listener = self.pos_bar_press_listener
        self.pos_bar.update_display_with_data(self.producer, -1, -1)

        pos_bar_frame = Gtk.HBox()
        pos_bar_frame.add(self.pos_bar.widget)
        pos_bar_frame.set_margin_top(10)
        pos_bar_frame.set_margin_bottom(9)
        pos_bar_frame.set_margin_start(6)
        pos_bar_frame.set_margin_end(2)
                                                 
                                                 
        control_panel = Gtk.HBox(False, 2)
        control_panel.pack_start(self.tc_display.widget, False, False, 0)
        control_panel.pack_start(pos_bar_frame, True, True, 0)
        control_panel.pack_start(self.preview_button, False, False, 0)
        guiutils.set_margins(control_panel, 0, 24, 0, 0)
        
        self.editors_box = Gtk.HBox(False, 0)

        self.import_select = Gtk.ComboBoxText()
        self.import_select.append_text(_("Add as Container Clip"))
        self.import_select.append_text(_("Add as Rendered Clip"))
        self.import_select.set_active(0)
        self.import_select.connect("changed", lambda w: self._export_action_changed(w))
        import_row = guiutils.get_sides_justified_box([Gtk.Label(label=_("Import Action:")), guiutils.pad_label(12,12), self.import_select])
        guiutils.set_margins(import_row,8,0,0,0)
        self.length_spin = Gtk.SpinButton.new_with_range (25, 100000, 1)
        self.length_spin.set_value(200)
        self.length_spin.connect("value-changed", self.lenght_value_changed)

        length_row = guiutils.get_left_justified_box([Gtk.Label(label=_("Generator Length:")), guiutils.pad_label(12,12), self.length_spin])

        self.encoding_button = Gtk.Button(label=_("Encode settings"))
        self.encoding_button.set_sensitive(False)
        self.encoding_button.connect("clicked", lambda w: self._set_encoding_button_pressed())
        self.encoding_info = Gtk.Label()
        self.encoding_info.set_markup("<small>" + "Not set" + "</small>")
        self.encoding_info.set_max_width_chars(32)
        self.encoding_info.set_sensitive(False)
        encoding_row = guiutils.get_left_justified_box([self.encoding_button, guiutils.pad_label(12,12), self.encoding_info])
                
        right_column_panel = Gtk.VBox(False, 2)
        right_column_panel.pack_start(self.screenshot_canvas, True, True, 0)
        right_column_panel.pack_start(control_panel, False, False, 0)
        right_column_panel.pack_start(length_row, False, False, 0)
        right_column_panel.pack_start(import_row, False, False, 0)
        right_column_panel.pack_start(encoding_row, False, False, 0)

        values_row = Gtk.HBox(False, 8)
        values_row.pack_start(self.editors_box, False, False, 0)
        values_row.pack_start(right_column_panel, True, True, 0)
        
        close_button = guiutils.get_sized_button(_("Close"), 150, 32)
        close_button.connect("clicked", lambda w: _close_clicked())
        self.add_button = guiutils.get_sized_button(_("Add Generator"), 150, 32)
        self.add_button.connect("clicked", lambda w: _add_media_plugin())
        
        buttons_row = Gtk.HBox(False, 0)
        buttons_row.pack_start(Gtk.Label(), True, True, 0)
        buttons_row.pack_start(close_button, False, False, 0)
        buttons_row.pack_start(self.add_button, False, False, 0)
        guiutils.set_margins(buttons_row, 24, 0, 0, 0)

        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(plugin_select_row, False, False, 0)
        vbox.pack_start(values_row, True, True, 0)
        vbox.pack_start(buttons_row, False, False, 0)
        
        alignment = guiutils.set_margins(vbox, 8, 8, 12, 12)

        self.add(alignment)
        self.set_position(Gtk.WindowPosition.CENTER)  
        self.show_all()
    
        self.plugin_select.set_selected(_plugins[0].name)
        self._display_current_render_data()

    def _show_info(self, w, e):
        info_popover = Gtk.Popover.new(self.info_launch.widget)
        
        author = Gtk.Label(label=_("<b>Author: </b> ") + _current_plugin_data_object["author"])
        author.set_use_markup(True)
        version = Gtk.Label(label=_("<b>Version: </b> ") + str(_current_plugin_data_object["version"]))
        version.set_use_markup(True)
        author_row = guiutils.get_left_justified_box([author])
        version_row = guiutils.get_left_justified_box([version])
        info_box = Gtk.VBox(False, 2)
        info_box.pack_start(author_row, False, True, 0)
        info_box.pack_start(version_row, True, True, 0)
        guiutils.set_margins(info_box, 12, 12, 12, 12)
        info_box.show_all()
        info_popover.add(info_box)
        info_popover.popup()
    
    def _build_editor_row(self, label_text, widget):
        row = Gtk.HBox(False, 2)
        left_box = guiutils.get_left_justified_box([Gtk.Label(label=label_text)])
        left_box.set_size_request(SIMPLE_EDITOR_LEFT_WIDTH, guiutils.TWO_COLUMN_BOX_HEIGHT)
        row.pack_start(left_box, False, True, 0)
        row.pack_start(widget, True, True, 0)
        return row
    
    def _draw_screenshot(self, event, cr, allocation):
        if _selected_plugin == None:
            return

        mx, my, mw, mh = self._get_monitor_image_rect()
        x, y, w, h = allocation

        cr.rectangle(0, 0, w, h)
        cr.set_source_rgb(0, 0, 0)
        cr.fill()

        scaled_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(mw), int(mh))
        crs = cairo.Context(scaled_surface)
        crs.save()
        crs.scale(mw / _current_screenshot_surface.get_width(), mh / _current_screenshot_surface.get_height())
        crs.set_source_surface(_current_screenshot_surface, 0, 0)
        crs.paint()
        crs.restore()
    
        cr.set_source_surface(scaled_surface, mx, my)
        cr.paint()
        
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.set_line_width(1.0)
        cr.move_to(mx + 0.5, my + 0.5)
        cr.line_to(mx + mw - 0.5, my + 0.5)
        cr.line_to(mx + mw - 0.5, my + mh - 0.5)
        cr.line_to(mx + 0.5, my + mh - 0.5)
        cr.line_to(mx + 0.5, my + 0.5)
        cr.stroke()
        
    def _plugin_selection_changed(self, combo):
        name, new_selected_plugin = self.plugin_select.get_selected()
        
        success, fctx = self.get_plugin_data(new_selected_plugin.get_plugin_script_file())
        script_data_object = json.loads(fctx.get_script_data())
        self._show_plugin_editors_panel(script_data_object)

        global _selected_plugin, _current_screenshot_surface, _current_plugin_data_object
        _selected_plugin = new_selected_plugin
        _current_plugin_data_object = script_data_object
        _current_screenshot_surface = new_selected_plugin.get_screenshot_surface()
        self.length_spin.set_value(_current_plugin_data_object["length"])

        # Create and set default render options data.
        global _current_render_data
        default_render = _selected_plugin.default_render
        if default_render == appconsts.DEFAULT_RENDER_CLIP:
            _current_render_data = toolsencoding.create_container_clip_default_render_data_object(current_sequence().profile)
            _current_render_data.do_video_render = True
        elif default_render == appconsts.DEFAULT_RENDER_ALPHA_CLIP:
            _current_render_data = toolsencoding.create_container_clip_default_alpha_render_data_object(current_sequence().profile)
            _current_render_data.do_video_render = True
        else:
            _current_render_data = toolsencoding.create_container_clip_default_render_data_object(current_sequence().profile)
        self._display_current_render_data()
        
        self.producer.set_frame(0)
        self.tc_display.set_frame(0)
        self.producer.set_length(_current_plugin_data_object["length"])
        self.pos_bar.update_display_with_data(self.producer, -1, -1)

        self.pos_bar.widget.queue_draw()
        self.screenshot_canvas.queue_draw()
    
    def _show_plugin_editors_panel(self, script_data_object):
        self.plugin_editors = simpleeditors.create_add_media_plugin_editors(script_data_object)

        children = self.editors_box.get_children()
        for child in children:
            self.editors_box.remove(child)
        
        self.editors_box.pack_start(self.plugin_editors.editors_panel, False, False, 0)
        self.show_all()
    
    def _get_monitor_image_rect(self):
        mw = self.screenshot_canvas.get_allocated_width()
        mh = self.screenshot_canvas.get_allocated_height()
        
        canv_aspect = mw / mh
        img_aspect = current_sequence().profile.width() / current_sequence().profile.height() 
        
        if canv_aspect > img_aspect:
            y = 0
            h = mh
            w = h * img_aspect
            x = mw / 2 - w / 2
        else:
            x = 0
            w = mw
            h = w / img_aspect
            y = mh / 2 - h / 2 
        
        return (x, y, w, h)

    def position_listener(self, normalized_pos, length):
        frame = int(normalized_pos * length)
        self.producer.set_frame(frame)
        self.tc_display.set_frame(frame)
        self.pos_bar.widget.queue_draw()

    def pos_bar_press_listener(self):
        pass #_player.stop_playback()

    def lenght_value_changed(self, adjustment):
        self.producer.set_length(adjustment.get_value())
        self.pos_bar.update_display_with_data(self.producer, -1, -1)

        self.pos_bar.widget.queue_draw()

    def _show_preview(self):
        global _selected_plugin, _current_screenshot_surface
        fctx = self._render_preview(int(self.producer.frame()))
        _current_screenshot_surface = fctx.priv_context.frame_surface

        self.screenshot_canvas.queue_draw()

    def _render_preview(self, frame):
        editor_widgets = self.plugin_editors.editor_widgets
        new_editors_list = simpleeditors.get_editors_data_as_editors_list(self.plugin_editors.editor_widgets)
        editors_data_json = json.dumps(new_editors_list)
        
        script_file = open(_selected_plugin.get_plugin_script_file())
        user_script = script_file.read()
        
        profile_file_path = mltprofiles.get_profile_file_path(current_sequence().profile.description())

        fctx = fluxity.render_preview_frame(user_script, script_file, frame, int(self.length_spin.get_value()), None, profile_file_path, editors_data_json)
        return fctx
        
    def get_plugin_data(self, plugin_script_path, frame=0):
        try:
            script_file = open(plugin_script_path)
            user_script = script_file.read()
            profile_file_path = mltprofiles.get_profile_file_path(current_sequence().profile.description())
            fctx = fluxity.render_preview_frame(user_script, script_file, frame, int(self.length_spin.get_value()), None, profile_file_path)
         
            if fctx.error == None:
                return (True, fctx) # no errors
            else:
                return (False,  fctx.error)
    
        except Exception as e:
            return (False, str(e))
            
    def _export_action_changed(self, combo):
        if combo.get_active() == 0:
            self.encoding_button.set_sensitive(False)
            self.encoding_info.set_sensitive(False)
        else:
            self.encoding_button.set_sensitive(True)
            self.encoding_info.set_sensitive(True)
            
    def _set_encoding_button_pressed(self):
        container_data = containerclip.ContainerClipData(appconsts.CONTAINER_CLIP_FLUXITY, _selected_plugin.get_plugin_script_file(), None)
        container_data.data_slots["icon_file"] = None
        container_data.data_slots["fluxity_plugin_edit_data"] = _current_plugin_data_object
        #self.length_spin.set_value(_current_plugin_data_object["length"])
        containerclip.set_render_settings_from_create_window(container_data, self._encode_settings_done)
    
    def _encode_settings_done(self, render_data):
        global _current_render_data
        _current_render_data = render_data
        self._display_current_render_data()
    
    def _display_current_render_data(self):
        if _current_render_data.do_video_render == True:
            args_vals = toolsencoding.get_args_vals_list_for_render_data(_current_render_data)
            desc_str = toolsencoding.get_encoding_desc(args_vals)

            self.encoding_info.set_markup("<small>" + desc_str + "</small>")
            self.encoding_info.set_ellipsize(Pango.EllipsizeMode.END)
        else:
            self.encoding_info.set_markup("<small>" + _("Image Sequence") + "</small>")
            self.encoding_info.set_ellipsize(Pango.EllipsizeMode.END)


class PosBarProducer:
    
    def __init__(self):
        self.length = 200
        self.mark_in = -1
        self.mark_out = -1
        self.plugin_frame = 0
        
    def get_length(self):
        return self.length

    def set_length(self, length):
        self.length = length
        
    def frame(self):
        return self.plugin_frame

    def set_frame(self, plugin_frame):
        self.plugin_frame = plugin_frame
        
# ---------------------------------------------------------------------edit panel 
def create_widgets():
    """
    Widgets for editing generator properties.
    """
    widgets.plugin_info = guicomponents.PluginInfoPanel()
    widgets.hamburger_launcher = guicomponents.HamburgerPressLaunch(_hamburger_launch_pressed)
    widgets.hamburger_launcher.do_popover_callback = True
    
    guiutils.set_margins(widgets.hamburger_launcher.widget, 4, 6, 6, 0)
    widgets.frame_select_box = Gtk.VBox()
    widgets.frame_select_button = None
    widgets.empty_label = Gtk.Label(label=_("No Generator"))
    widgets.empty_label.set_sensitive(False)

    # Edit area.
    widgets.value_edit_box = Gtk.VBox()
    widgets.value_edit_box.pack_start(widgets.empty_label, True, True, 0)
    widgets.value_edit_frame = Gtk.Frame()
    widgets.value_edit_frame.add(widgets.value_edit_box)

def get_plugin_hamburger_row():
    create_widgets()
    
    # Action row.
    action_row = Gtk.HBox(False, 2)
    action_row.pack_start(widgets.hamburger_launcher.widget, False, False, 0)
    action_row.pack_start(Gtk.Label(), True, True, 0)
    action_row.pack_start(widgets.plugin_info, False, False, 0)
    action_row.pack_start(Gtk.Label(), True, True, 0)
    
    return action_row

def get_plugin_buttons_row():
    cancel_b = guiutils.get_sized_button(_("Cancel"), 110, 28)
    cancel_b.connect("clicked", lambda w: _cancel())
    widgets.preview_b = Gtk.Button(label=_("Preview"))
    widgets.preview_b.connect("clicked", lambda w: _preview())
    render_b = guiutils.get_sized_button(_("Apply"), 110, 28)
    render_b.connect("clicked", lambda w: _apply())
    
    buttons_box = Gtk.HBox(False, 2)
    buttons_box.pack_start(widgets.preview_b, False, False, 0)
    buttons_box.pack_start(widgets.frame_select_box, False, False, 0)
    buttons_box.pack_start(Gtk.Label(), True, True, 0)
    buttons_box.pack_start(cancel_b, False, False, 0)

    buttons_box.pack_start(render_b, False, False, 0)
    
    return buttons_box    

def set_plugin_to_be_edited(clip, action_object):
    global _action_object, _clip
    _clip = clip
    _action_object = action_object

    plugin_name_label = Gtk.Label(label= "<b>" + clip.name + "</b>")
    plugin_name_label.set_use_markup(True)
    name_box = Gtk.VBox()
    name_box.pack_start(plugin_name_label, False, False, 0)
    name_box.pack_start(guicomponents.EditorSeparator().widget, False, False, 0)
    
    global _edit_panel
    _edit_panel = simpleeditors.show_fluxity_container_clip_program_editor(clip, action_object, action_object.container_data.data_slots["fluxity_plugin_edit_data"], name_box)

    try:
        widgets.value_edit_frame.remove(widgets.value_edit_box)
    except:
        pass
    widgets.value_edit_box = _edit_panel.scrolled_window 
    widgets.value_edit_frame.add(widgets.value_edit_box)
    
    track, index = current_sequence().get_track_and_index_for_id(clip.id)            
    track_name = utils.get_track_name(track, current_sequence())
    widgets.plugin_info.display_plugin_info(clip, track_name)

    try:
        widgets.frame_select_box.remove(widgets.frame_select_button)
    except:
        pass

    widgets.frame_select_button = Gtk.SpinButton.new_with_range(0, _action_object.container_data.unrendered_length, 1)
    widgets.frame_select_box.add(widgets.frame_select_button)
    
    editorlayout.show_panel(appconsts.PANEL_MULTI_EDIT)
    gui.editor_window.edit_multi.set_visible_child_name(appconsts.EDIT_MULTI_PLUGINS)

def _cancel():
    global _edit_panel, _action_object, _clip
    _edit_panel = None
    _action_object = None
    _clip = None

    gui.editor_window.edit_multi.set_visible_child_name(appconsts.EDIT_MULTI_EMPTY)

def panel_is_open():
    if _edit_panel != None and gui.editor_window.edit_multi.get_visible_child_name() == appconsts.EDIT_MULTI_PLUGINS:
        return True
    else:
        return False

def clip_is_being_edited(clip):
    if clip ==_clip:
        return True
    else:
        return False

def get_clip():
    return _clip

def clear_clip():
    _cancel()

def _preview():
    preview_frame = widgets.frame_select_button.get_value_as_int()
    callbacks = (_preview_render_complete, _preview_render_complete_error)
    _action_object.render_fluxity_preview(callbacks, _edit_panel.editor_widgets, preview_frame)

def _get_preview_file():
    return _action_object.get_preview_media_dir() + "/preview.png"

def _preview_render_complete():
    global _preview_surface
    _preview_surface_rendered = cairo.ImageSurface.create_from_png(_get_preview_file())
    preview_height = int(PREVIEW_WIDTH * _preview_surface_rendered.get_height() / _preview_surface_rendered.get_width())
    _preview_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, PREVIEW_WIDTH, preview_height)
    scale = PREVIEW_WIDTH / _preview_surface_rendered.get_width()
    cr = cairo.Context(_preview_surface)
    cr.scale(scale, scale)
    cr.set_source_surface(_preview_surface_rendered, 0, 0)
    cr.paint()
    
    preview_frame = -1
    global _preview_popover, _preview_canvas
    if _preview_popover == None:
        _preview_popover = Gtk.Popover.new(widgets.preview_b)
        _preview_canvas = PreviewCanvas()
        _preview_canvas.widget.show()
        _preview_popover.add(_preview_canvas.widget)
    _preview_popover.popup()

def _preview_render_complete_error(error_msg):
    preview_frame = -1

    txt = _("Error in Preview for frame: ") +  error_msg

    print("preview error" + error_msg)
    
def _apply():
    _action_object.apply_editors(_edit_panel.editor_widgets)
    _action_object.render_full_media(_clip)

def _hamburger_launch_pressed(launcher, widget, event, data):
    track, index = current_sequence().get_track_and_index_for_id(_clip.id)
    #guicomponents.get_media_plugin_editor_hamburger_menu(event, _hamburger_item_activated)
    guipopover.plugin_editor_hamburger_popover_show(launcher, widget, _hamburger_item_activated)
 
def _hamburger_item_activated(action, event, msg):
    if msg == "close":
        gui.editor_window.edit_multi.set_visible_child_name(appconsts.EDIT_MULTI_EMPTY)
    elif msg == "save_properties":
        plugin_name = _clip.name
        default_name = plugin_name.replace(" ", "_") + _("_media_plugin_properties") + ".mediaplugindata"
        dialogs.save_media_plugin_plugin_properties(_save_properties_callback, default_name, _action_object.container_data.data_slots["fluxity_plugin_edit_data"])
    elif msg == "load_properties":
        dialogs.load_media_plugin_plugin_properties(_load_properties_callback)

def _save_properties_callback(dialog, response_id, data):
    if response_id == Gtk.ResponseType.ACCEPT:
        save_path = dialog.get_filenames()[0]
        _action_object.apply_editors(_edit_panel.editor_widgets)
        with atomicfile.AtomicFileWriter(save_path, "wb") as afw:
            write_file = afw.get_file()
            pickle.dump(data, write_file)
            _action_object.render_full_media(_clip)
    
    dialog.destroy()

def _load_properties_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        load_path = dialog.get_filenames()[0]
        try:
            plugin_editors_data = utils.unpickle(load_path)
            _action_object.container_data.data_slots["fluxity_plugin_edit_data"] = plugin_editors_data
            _clip.container_data.data_slots["fluxity_plugin_edit_data"] = plugin_editors_data
            set_plugin_to_be_edited(_clip, _action_object)
            _action_object.render_full_media(_clip)
        except Exception as e:
            primary_txt = _("Generator properties load failed!")
            secondary_txt = _("Error message: ") + str(e)
            dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window)
            gui.editor_window.edit_multi.set_visible_child_name(appconsts.EDIT_MULTI_EMPTY)
    
    dialog.destroy()


class PreviewCanvas:
    def __init__(self):
        # This now hard coded to 16:9 screen ratio, others get clipped or we get some empty space.
        self.widget = cairoarea.CairoDrawableArea2( 320, 
                                                    180, 
                                                    self._draw)

    def _draw(self, event, cr, allocation):
        cr.set_source_surface(_preview_surface, 0, 0)
        cr.paint()
