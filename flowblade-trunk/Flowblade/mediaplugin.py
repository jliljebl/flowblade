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
import json
import respaths

_plugins = []
_plugins_groups = []

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

    """
    for group_data in _plugins_groups:
        group_name, group = group_data
        print(group_name)
        for plugin in group:
            print(plugin.name)
    """

#def get_plugin_groups():
#    return _plugins_groups
    
def fill_app_menu(menu):
    for group_data in _plugins_groups:
        
        group_name, group = group_data
        print(group_name)
        for plugin in group:
            print(plugin.name)
    

class MediaPlugin:
    
    def __init__(self, folder, name, category):
        self.folder = folder
        self.name = name
        self.category = category
        