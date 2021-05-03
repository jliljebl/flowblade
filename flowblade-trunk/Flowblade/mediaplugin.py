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
from gi.repository import Gtk, GObject

import cairo
import copy
import json

import cairoarea
import containerclip
import editorpersistance
import gui
import guicomponents
import guiutils
import respaths

_plugins = []
_plugins_groups = []

_add_plugin_window = None
_plugins_menu = Gtk.Menu()

_selected_plugin = None
_current_screenshot_surface = None

# --------------------------------------------------------- plugin
class MediaPlugin:
    
    def __init__(self, folder, name, category):
        self.folder = folder
        self.name = name
        self.category = category
    
    def get_screenshot_surface(self):
        icon_path = respaths.MEDIA_PLUGINS_PATH + self.folder + "/screenshot.png"
        print(icon_path)
        return cairo.ImageSurface.create_from_png(icon_path)

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

    # Create categories with translated names and sorted scripts.
    # Category names have to correspond with category names in fluxity.py.
    _script_groups_names = {}
    _script_groups_names["Animations"] = _("Animations")
    _script_groups_names["Effects"] = _("Effects")
    _script_groups_names["Cover Transitions"] = _("Cover Transitions")

    load_groups = {}
    for plugin in _plugins:
        try:
            translated_group_name = _script_groups_names[plugin.category]
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
    global _add_plugin_window
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
            plugins_list.append((plugin.name,plugin))
        
        categories_list.append((group_name, plugins_list))
    
    return categories_list  
        
    
def fill_media_plugin_sub_menu(menu, callback=None):
    for group_data in _plugins_groups:

        group_name, group = group_data
        menu_item = Gtk.MenuItem.new_with_label(group_name)
        sub_menu = Gtk.Menu.new()
        menu_item.set_submenu(sub_menu)
        for plugin in group:
            plugin_menu_item = Gtk.MenuItem.new_with_label(plugin.name)
            if callback == None:
                plugin_menu_item.connect("activate", _add_media_plugin, plugin.folder)
            else:
                plugin_menu_item.connect("activate", callback, plugin.folder)
            sub_menu.append(plugin_menu_item)

        menu.append(menu_item)
    menu.show_all()

def _add_media_plugin(widget, plugin_folder):
    script_file = respaths.MEDIA_PLUGINS_PATH + plugin_folder + "/plugin_script.py"
    screenshot_file =  respaths.MEDIA_PLUGINS_PATH + plugin_folder + "/screenshot.png"
    containerclip.create_fluxity_media_item_from_plugin(script_file, screenshot_file)

def get_plugin_code(plugin_folder):
    script_file = respaths.MEDIA_PLUGINS_PATH + plugin_folder + "/plugin_script.py"
    args_file = open(script_file)
    return args_file.read()
        


# --------------------------------------------------------- window
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

        self.screenshot_canvas = cairoarea.CairoDrawableArea2(240, 180, self._draw_screenshot)
        screenshot_row = guiutils.get_centered_box([self.screenshot_canvas ])
        guiutils.set_margins(screenshot_row, 12, 12, 0, 0)
        
        close_button = Gtk.Button(_("Close"))
        close_button.connect("clicked", lambda w: _close_clicked())
        self.add_button = Gtk.Button(_("Add Media"))
        #self.add_button.connect("clicked", lambda w: _do_folder_media_import())
        self.add_button.set_sensitive(False)
        self.load_info_2 = Gtk.Label() 
        row8 = Gtk.HBox(False, 0)
        row8.pack_start(self.load_info_2, False, False, 0)
        row8.pack_start(Gtk.Label(), True, True, 0)
        row8.pack_start(close_button, False, False, 0)
        row8.pack_start(self.add_button, False, False, 0)

        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(plugin_select_row, False, False, 0)
        vbox.pack_start(screenshot_row, False, False, 0)
        vbox.pack_start(row8, False, False, 0)
        
        alignment = guiutils.set_margins(vbox, 8, 8, 12, 12)

        self.add(alignment)
        self.set_position(Gtk.WindowPosition.CENTER)  
        self.show_all()
    
        self.plugin_select.set_selected(_plugins[0].name)

    def _draw_screenshot(self, event, cr, allocation):
        if _selected_plugin == None:
            return

        cr.set_source_surface(_current_screenshot_surface, 0, 0)
        cr.paint()
                    
    def _plugin_selection_changed(self, combo):
        name, _new_selected_plugin = self.plugin_select.get_selected()
        print(_new_selected_plugin.name)
        global _selected_plugin, _current_screenshot_surface
        _selected_plugin = _new_selected_plugin
        _current_screenshot_surface = _selected_plugin.get_screenshot_surface()
        
        self.screenshot_canvas.queue_draw()
        
        

    
