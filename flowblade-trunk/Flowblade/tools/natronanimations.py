"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2014 Janne Liljeblad.

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

import copy
import os
import xml.dom.minidom

import appconsts
from editorstate import PROJECT
import natroninterpretations
import propertyparse
import respaths
import utils

ANIMATION_NODE = "animation"
NAME_NODE = "name"
NATRON_PROJECT_FILE_NODE = "projectfile"
LENGTH_NODE = "length"
NAME_ATTR = "name"
ARGS_ATTR = "args"
GROUP_NODE = "group"
INTERPRETATION = "propertyinterpretation"
PROPERTY = appconsts.PROPERTY
NATRON_NODE_NAME_ATTR = "nodename"
NATRON_PROPERTY_NAME_ATTR = "natronpropertyname"

NEWLINE = "\n"
QUOTE = "\""

_scripts = None
_animations_groups = []


# ----------------------------------------------------------------------- data class objects
class NatronAnimationInfo:
    
    def __init__(self, anim_node):
        self.name = anim_node.getElementsByTagName(NAME_NODE).item(0).firstChild.nodeValue
        self.group = anim_node.getElementsByTagName(GROUP_NODE).item(0).firstChild.nodeValue
        self.project_file = anim_node.getElementsByTagName(NATRON_PROJECT_FILE_NODE).item(0).firstChild.nodeValue
                
        self.property_node_list = anim_node.getElementsByTagName(PROPERTY)
        self.interpretation_node_list = anim_node.getElementsByTagName(INTERPRETATION)

        self.properties = propertyparse.node_list_to_properties_array(self.property_node_list)
        self.property_args = propertyparse.node_list_to_args_dict(self.property_node_list)

        self.length = anim_node.getElementsByTagName(LENGTH_NODE).item(0).firstChild.nodeValue

        # Create dict for interpretations for each property: property name -> (natron_node, natron_property, interpretation, args)
        self.interpretations = {}
        for i_node in self.interpretation_node_list:
            natron_node = i_node.getAttribute(NATRON_NODE_NAME_ATTR)
            natron_property = i_node.getAttribute(NATRON_PROPERTY_NAME_ATTR)
            args_str = i_node.getAttribute(ARGS_ATTR)
            if len(args_str) == 0:
                args = None
            else:
                args = propertyparse.args_string_to_args_dict(args_str)
             
            interpretation = i_node.firstChild.nodeValue
            
            self.interpretations[i_node.getAttribute(NAME_ATTR)] = (natron_node, natron_property, interpretation, args)

    def get_instance(self, profile):
        instance = NatronAnimationInstance(self, profile)
        return instance


class NatronAnimationInstance:
    def __init__(self, natron_animation_info, profile):
        self.info = natron_animation_info
        self.profile_desc = profile.description()
        self.properties = copy.deepcopy(natron_animation_info.properties)

        self.range_in = 1
        self.range_out = int(self.info.length)

        self.current_frame = 1
        self.mark_in = -1
        self.mark_out =-1
        
        # PROP_EXPR values may have keywords that need to be replaced with
        # numerical values that depend on the profile we have. These need
        # to be replaced now that we have profile and we are ready to connect this.
        # For example default values of some properties depend on the screen size of the project
        propertyparse.replace_value_keywords(self.properties, profile)
        
    def write_out_modify_data(self, editable_properties, uid, format_index):
        exec_str = self._get_profile_setting_exec_str(format_index)
        exec_str += self._get_natron_modifying_exec_string(editable_properties)
        #exec_str += self._get_test_exec_str()
        
        print exec_str
        export_data_file = open(self.get_modify_exec_data_file_path(uid), "w")
        export_data_file.write(exec_str)
        export_data_file.close()

        # NOTE: THIS CAN BREAK IF 2 ANIMATION RENDERS ARE STARTED VERY CLOSELY TO EACH OTHER AND WE READ WRONG SESSION FROM THIS FILE
        # IN PRACTICE WE CAN GET AWAY WITH IT, BUT LOOK BETTER STUFF
        render_session_id_file = open(self.get_render_session_id_file_path(), "w")
        render_session_id_file.write(uid)
        render_session_id_file.close()

    def get_modify_exec_data_file_path(self, uid):
        return utils.get_hidden_user_dir_path() + appconsts.NATRON_DIR + "/session_" + uid + "/mod_data"

    def get_render_session_id_file_path(self):
        return utils.get_hidden_user_dir_path() + appconsts.NATRON_DIR + "/LATEST_RENDER_INSTANCE_ID"

    def _get_natron_modifying_exec_string(self, editable_properties):
        exec_str = ""
        for ep in editable_properties:
            natron_node, natron_property, interpretation, args = self.info.interpretations[ep.name]
            property_modify_str = natroninterpretations.get_property_modyfying_str(ep.value, natron_node, natron_property, interpretation, args)
            exec_str = exec_str + property_modify_str
        
        return exec_str

    def _get_profile_setting_exec_str(self, format_index):
        exec_str = "formatType = app.Write1.getParam(" + QUOTE + "formatType" + QUOTE +  ")"  + NEWLINE 
        exec_str += "formatType.setValue(2)"  + NEWLINE 
        exec_str += "formatParam = app.Write1.getParam(" + QUOTE + "NatronParamFormatChoice" + QUOTE +  ")"  + NEWLINE 
        exec_str += "formatParam.setValue(" + str(format_index) + ")"  + NEWLINE   
        
        return exec_str

    # used for quick'n'dirty testing during dev
    def _get_test_exec_str(self):
        exec_str = "app.Text1_3.center.set(100, 100, 0)" + NEWLINE   
        exec_str += "app.Text1_3.center.set(400, 400, 100)" + NEWLINE   
        return exec_str
        
    def get_length(self):
        return self.range_out - self.range_in + 1 # # +1 out incl.

    def get_frame_range_str(self):
        return str(self.range_in) + "-" + str(self.range_out)

    def get_project_file_path(self):
        return respaths.ROOT_PATH + "/res/natron/project_files/" + self.info.project_file

    def frame(self):
        return self.current_frame

# --------------------------------------------------------- load data
def load_animations_projects_xml():
    print "Loading Natron animations..."
    
    _animations_groups_names = {}
    _animations_groups_names["Text Animation"] = _("Text Animation")
    _animations_groups_names["Background"] = _("Background")
    _animations_groups_names["Effect"] = _("Effect")

    anim_projects_doc = xml.dom.minidom.parse(respaths.NATRON_PROJECTS_XML_DOC)

    load_groups = {}
    animations_nodes = anim_projects_doc.getElementsByTagName(ANIMATION_NODE)
    for anim_node in animations_nodes:
        group_name = anim_node.getElementsByTagName(GROUP_NODE).item(0).firstChild.nodeValue
        natron_animation_info = NatronAnimationInfo(anim_node)

        # Add filter compositor filters or filter groups
        try:
            translated_group_name = _animations_groups_names[group_name]
        except Exception as e:
            translated_group_name = "Misc"
            
        try:
            # TODO: translations mechanic missing, see mltfilters.py
            group_list = load_groups[translated_group_name]
            group_list.append(natron_animation_info)
        except:
            load_groups[translated_group_name] = [natron_animation_info]

    # We used translated group names as keys in load_groups
    # Now we sort them and use them to place data in groups array in the same
    # order as it will be presented to user, so selection indexes in gui components will match
    # group array indexes here.
    sorted_keys = sorted(load_groups.keys())
    global _animations_groups
    for gkey in sorted_keys:
        group = load_groups[gkey]
        add_group = sorted(group, key=lambda natron_animation_info: natron_animation_info.name)
        _animations_groups.append((gkey, add_group))


# ----------------------------------------------------------------- module functions
def get_animations_groups():
    return _animations_groups

def get_default_animation_instance(profile):
    key, group = _animations_groups[0]
    return group[0].get_instance(profile)
        
def get_animation_instance(groups_index, group_animations_index):
    key, group = _animations_groups[groups_index]
    return group[group_animations_index].get_instance()


