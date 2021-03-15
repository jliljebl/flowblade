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

def init():
    plugins_list_json = open(respaths.MEDIA_PLUGINS_PATH + "plugins.json")
    plugins_obj = json.load(plugins_list_json)
    
    global _plugins
    plugins_list = plugins_obj["plugins"]
    for plugin_data in plugins_list:
        plugin = MediaPlugin(plugin_data["folder"], plugin_data["name"], plugin_data["category"])
        _plugins.append(plugin)

#def get_categories_dict:
        
    

class MediaPlugin:
    
    def __init__(self, folder, name, category):
        self.folder = folder
        self.name = name
        self.category = category
        