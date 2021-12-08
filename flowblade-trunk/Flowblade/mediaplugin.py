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
from gi.repository import Gtk, GObject, Pango

import cairo
import copy
import hashlib
import json
import os

import appconsts
import cairoarea
import containerclip
import editorlayout
import editorpersistance
from editorstate import current_sequence
import fluxity
import gui
import guicomponents
import guiutils
import mltprofiles
import respaths
import simpleeditors
import toolsencoding
import translations
import userfolders
import utils

MONITOR_WIDTH = 400
MONITOR_HEIGHT = -1
PREVIEW_WIDTH = 320

SIMPLE_EDITOR_LEFT_WIDTH = 150

_plugins = []
_plugins_groups = []

_add_plugin_window = None
_plugins_menu = Gtk.Menu()

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
    
    def __init__(self, folder, name, category):
        self.folder = folder
        self.name = name
        self.category = category
    
    def get_screenshot_file(self):
        return respaths.MEDIA_PLUGINS_PATH + self.folder + "/screenshot.png"
    
    def get_screenshot_surface(self):
        return cairo.ImageSurface.create_from_png(self.get_screenshot_file())

    def get_plugin_script_file(self):
        script_file = respaths.MEDIA_PLUGINS_PATH + self.folder + "/plugin_script.py"
        return script_file


# --------------------------------------------------------------- interface
def init():
    # Load Plugins
    plugins_list_json = open(respaths.MEDIA_PLUGINS_PATH + "plugins.json")
    plugins_obj = json.load(plugins_list_json)
    
    global _plugins
    plugins_list = plugins_obj["plugins"]
    for plugin_data in plugins_list:
        plugin = MediaPlugin(plugin_data["folder"], plugin_data["name"], plugin_data["category"])
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

def fill_media_plugin_sub_menu(menu, callback=None):
    for group_data in _plugins_groups:

        group_name, group = group_data
        menu_item = Gtk.MenuItem.new_with_label(group_name)
        sub_menu = Gtk.Menu.new()
        menu_item.set_submenu(sub_menu)
        for plugin in group:
            plugin_menu_item = Gtk.MenuItem.new_with_label(translations.get_plugin_name(plugin.name))
            if callback == None:
                plugin_menu_item.connect("activate", _add_media_plugin, plugin.folder)
            else:
                plugin_menu_item.connect("activate", callback, plugin.folder)
            sub_menu.append(plugin_menu_item)

        menu.append(menu_item)
    menu.show_all()

def _add_media_plugin():
    script_file = _selected_plugin.get_plugin_script_file()
    md_str = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
    screenshot_file = userfolders.get_cache_dir() + appconsts.THUMBNAILS_DIR + "/" + md_str +  ".png"
    _current_screenshot_surface.write_to_png(screenshot_file)
    _current_plugin_data_object["editors_list"] = simpleeditors.get_editors_data_as_editors_list(_add_plugin_window.plugin_editors.editor_widgets)
    _current_plugin_data_object["length"] = int(_add_plugin_window.length_spin.get_value())

    if _add_plugin_window.import_select.get_active() == 0:
        _close_window()
        # Add as Container Clip
        containerclip.create_fluxity_media_item_from_plugin(script_file, screenshot_file, _current_plugin_data_object)
    else:
        # Add as rendered media.
        _close_window()

        # We need to have a containerclip.ContainerClipData object to utilize caontainer clips code to render a video clip.
        container_data = containerclip.ContainerClipData(appconsts.CONTAINER_CLIP_FLUXITY, _selected_plugin.get_plugin_script_file(), None)
        container_data.data_slots["icon_file"] = screenshot_file
        container_data.data_slots["fluxity_plugin_edit_data"] = _current_plugin_data_object
        container_data.render_data = _current_render_data
        container_data.unrendered_length = _current_plugin_data_object["length"]
        containerclip.create_renderered_fluxity_media_item(container_data, _current_plugin_data_object["length"]) 

def get_plugin_code(plugin_folder):
    script_file = respaths.MEDIA_PLUGINS_PATH + plugin_folder + "/plugin_script.py"
    args_file = open(script_file)
    return args_file.read()
        

# --------------------------------------------------------- Window
class AddMediaPluginWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.set_modal(True)
        self.set_transient_for(gui.editor_window.window)
        self.set_title(_("Add Media Plugin"))
        self.connect("delete-event", lambda w, e:_close_window())

        # categories_list is list of form [("category_name", [category_items]), ...]
        # with category_items list of form ["item_name", ...]
        self.plugin_select = guicomponents.CategoriesModelComboBoxWithData(_get_categories_list())
        self.plugin_select.set_changed_callback(self._plugin_selection_changed)

        plugin_label = Gtk.Label(label=_("Media Plugin:"))
        plugin_select_row = guiutils.get_two_column_box(plugin_label, self.plugin_select.widget, 220)
        plugin_select_row.set_margin_bottom(24)

        global MONITOR_HEIGHT
        MONITOR_HEIGHT = int(MONITOR_WIDTH * float(current_sequence().profile.display_aspect_den()) / float(current_sequence().profile.display_aspect_num()))
        self.screenshot_canvas = cairoarea.CairoDrawableArea2(MONITOR_WIDTH, MONITOR_HEIGHT, self._draw_screenshot)
        screenshot_row = guiutils.get_centered_box([self.screenshot_canvas ])
        guiutils.set_margins(screenshot_row, 0, 8, 0, 0)

        self.frame_display = Gtk.Label(_("Clip Frame"))
        self.frame_display.set_margin_right(2)
        
        self.frame_select = Gtk.SpinButton.new_with_range (0, 200, 1)
        self.frame_select.set_value(0)
        
        self.preview_button = Gtk.Button(_("Preview"))
        self.preview_button.connect("clicked", lambda w: self._show_preview())
                            
        control_panel = Gtk.HBox(False, 2)
        control_panel.pack_start(self.frame_display, False, False, 0)
        control_panel.pack_start(self.frame_select, False, False, 0)
        control_panel.pack_start(Gtk.Label(), True, True, 0)
        control_panel.pack_start(self.preview_button, False, False, 0)
        guiutils.set_margins(control_panel, 0, 24, 0, 0)
        
        self.editors_box = Gtk.HBox(False, 0)
        self.editors_box.set_size_request(550, 185)

        self.import_select = Gtk.ComboBoxText()
        self.import_select.append_text(_("Add as Container Clip"))
        self.import_select.append_text(_("Add as Rendered Media"))
        self.import_select.set_active(0)
        self.import_select.connect("changed", lambda w: self._export_action_changed(w))
        import_row = guiutils.get_left_justified_box([Gtk.Label(_("Import Action:")), guiutils.pad_label(12,12), self.import_select])
        guiutils.set_margins(import_row,8,0,0,0)
        self.length_spin = Gtk.SpinButton.new_with_range (25, 100000, 1)
        self.length_spin.set_value(200)
        length_row = guiutils.get_left_justified_box([Gtk.Label(_("Plugin Media Length:")), guiutils.pad_label(12,12), self.length_spin])

        self.encoding_button = Gtk.Button(_("Encode settings"))
        self.encoding_button.set_sensitive(False)
        self.encoding_button.connect("clicked", lambda w: self._set_encoding_button_pressed())
        self.encoding_info = Gtk.Label()
        self.encoding_info.set_markup("<small>" + "Not set" + "</small>")
        self.encoding_info.set_max_width_chars(32)
        self.encoding_info.set_sensitive(False)
        encoding_row = guiutils.get_left_justified_box([self.encoding_button, guiutils.pad_label(12,12), self.encoding_info])
                
        right_column_panel = Gtk.VBox(False, 2)
        right_column_panel.pack_start(screenshot_row, False, False, 0)
        right_column_panel.pack_start(control_panel, False, False, 0)
        right_column_panel.pack_start(length_row, False, False, 0)
        right_column_panel.pack_start(import_row, False, False, 0)
        right_column_panel.pack_start(encoding_row, False, False, 0)
        right_column_panel.pack_start(Gtk.Label(), True, True, 0)

        values_row = Gtk.HBox(False, 8)
        values_row.pack_start(self.editors_box, False, False, 0)
        values_row.pack_start(right_column_panel, False, False, 0)
        
        close_button = guiutils.get_sized_button(_("Close"), 150, 32)
        close_button.connect("clicked", lambda w: _close_clicked())
        self.add_button = guiutils.get_sized_button(_("Add Media Plugin"), 150, 32)
        self.add_button.connect("clicked", lambda w: _add_media_plugin())
        
        buttons_row = Gtk.HBox(False, 0)
        buttons_row.pack_start(Gtk.Label(), True, True, 0)
        buttons_row.pack_start(close_button, False, False, 0)
        buttons_row.pack_start(self.add_button, False, False, 0)
        guiutils.set_margins(buttons_row, 24, 0, 0, 0)

        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(plugin_select_row, False, False, 0)
        vbox.pack_start(values_row, False, False, 0)
        vbox.pack_start(buttons_row, False, False, 0)
        
        alignment = guiutils.set_margins(vbox, 8, 8, 12, 12)

        self.add(alignment)
        self.set_position(Gtk.WindowPosition.CENTER)  
        self.show_all()
    
        self.plugin_select.set_selected(_plugins[0].name)
        self._display_current_render_data()
        
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

        cr.set_source_surface(_current_screenshot_surface, 0, 0)
        cr.paint()
        
        w, y, w, h = allocation
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(1.0)
        cr.move_to(0.5, 0.5)
        cr.line_to(w - 0.5, 0.5)
        cr.line_to(w - 0.5, h - 0.5)
        cr.line_to(0.5, h - 0.5)
        cr.line_to(0.5, 0.5)
        cr.stroke()
                            
    def _plugin_selection_changed(self, combo):
        name, new_selected_plugin = self.plugin_select.get_selected()
        
        success, fctx = self.get_plugin_data(new_selected_plugin.get_plugin_script_file())
        script_data_object = json.loads(fctx.get_script_data())
        self._show_plugin_editors_panel(script_data_object)

        global _selected_plugin, _current_screenshot_surface, _current_plugin_data_object
        _selected_plugin = new_selected_plugin
        _current_plugin_data_object = script_data_object
        _current_screenshot_surface = self._create_preview_surface(new_selected_plugin.get_screenshot_surface())
        
        self.screenshot_canvas.queue_draw()
    
    def _show_plugin_editors_panel(self, script_data_object):
        self.plugin_editors = simpleeditors.create_add_media_plugin_editors(script_data_object)

        children = self.editors_box.get_children()
        for child in children:
            self.editors_box.remove(child)
        
        self.editors_box.pack_start(self.plugin_editors.editors_panel, False, False, 0)
        self.show_all()

    def _create_preview_surface(self, rendered_surface):
        scaled_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, MONITOR_WIDTH, MONITOR_HEIGHT)
        cr = cairo.Context(scaled_surface)
        cr.save()
        cr.scale(float(MONITOR_WIDTH) / float(rendered_surface.get_width()), float(MONITOR_HEIGHT) / float(rendered_surface.get_height()))
        cr.set_source_surface(rendered_surface, 0, 0)
        cr.paint()
        cr.restore()

        return scaled_surface
    
    def _show_preview(self):
        global _selected_plugin, _current_screenshot_surface
                
        frame = int(self.frame_select.get_value())
        editor_widgets = self.plugin_editors.editor_widgets
        new_editors_list = simpleeditors.get_editors_data_as_editors_list(self.plugin_editors.editor_widgets)
        editors_data_json = json.dumps(new_editors_list)
        
        script_file = open(_selected_plugin.get_plugin_script_file())
        user_script = script_file.read()
        
        profile_file_path = mltprofiles.get_profile_file_path(current_sequence().profile.description())

        fctx = fluxity.render_preview_frame(user_script, script_file, frame, None, profile_file_path, editors_data_json)
        _current_screenshot_surface = self._create_preview_surface(fctx.priv_context.frame_surface)
        self.screenshot_canvas.queue_draw()
        
    def get_plugin_data(self, plugin_script_path, frame=0):
        try:
            script_file = open(plugin_script_path)
            user_script = script_file.read()
            profile_file_path = mltprofiles.get_profile_file_path(current_sequence().profile.description())
            fctx = fluxity.render_preview_frame(user_script, script_file, frame, None, profile_file_path)
         
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
        

# ---------------------------------------------------------------------edit panel 
def create_widgets():
    """
    Widgets for editing compositing properties.
    """
    widgets.plugin_info = guicomponents.PluginInfoPanel()
    widgets.hamburger_launcher = guicomponents.HamburgerPressLaunch(_hamburger_launch_pressed)
    widgets.hamburger_launcher.connect_launched_menu(guicomponents.clip_effects_hamburger_menu)
    guiutils.set_margins(widgets.hamburger_launcher.widget, 4, 6, 6, 0)
    widgets.frame_select_box = Gtk.VBox()
    widgets.frame_select_button = None
    widgets.empty_label = Gtk.Label(label=_("No Media Plugin."))
    widgets.empty_label.set_sensitive(False)

    # Edit area.
    widgets.value_edit_box = Gtk.VBox()
    widgets.value_edit_box.pack_start(widgets.empty_label, True, True, 0)
    widgets.value_edit_frame = Gtk.Frame()
    widgets.value_edit_frame.add(widgets.value_edit_box)
    widgets.value_edit_frame.set_shadow_type(Gtk.ShadowType.NONE)

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

def _hamburger_launch_pressed(widget, event):
    pass
    #guicomponents.get_compositor_editor_hamburger_menu(event, _compositor_hamburger_item_activated)


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

def _preview_render_complete_error(self, error_msg):
    preview_frame = -1

    txt = _("Error in Preview for frame: ") +  error_msg
    #self.preview_panel.preview_monitor.queue_draw()

    print("preview error" + error_msg)
    
def _apply():
    _action_object.apply_editors(_edit_panel.editor_widgets)
    _action_object.render_full_media(_clip)


class PreviewCanvas:
    def __init__(self):
        # This now hard coded to 16:9 screen ratio, others get clipped or we get some empty space.
        self.widget = cairoarea.CairoDrawableArea2( 320, 
                                                    180, 
                                                    self._draw)

    def _draw(self, event, cr, allocation):
        cr.set_source_surface(_preview_surface, 0, 0)
        cr.paint()