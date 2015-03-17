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
Module handles creating mlt.Filter objects and their FilterObject python wrappers that
are attached to mlt:Producer objects.
"""
import copy
import pygtk
pygtk.require('2.0');
import gtk

import mlt
import xml.dom.minidom

import appconsts
import editorstate
from editorstate import PROJECT
import mltrefhold
import propertyparse
import respaths
import translations

# Attr and node names in xml describing available filters.
PROPERTY = appconsts.PROPERTY
NON_MLT_PROPERTY = appconsts.NON_MLT_PROPERTY
NAME = appconsts.NAME
ARGS = appconsts.ARGS
MLT_SERVICE = appconsts.MLT_SERVICE
MLT_DROP_VERSION = "mlt_drop_version"
MLT_MIN_VERSION = "mlt_min_version"
EXTRA_EDITOR = appconsts.EXTRA_EDITOR
FILTER = "filter"
GROUP = "group"
ID = "id"
REPLACEMENT_RELATION = "replacementrelation"
USE_SERVICE = "useservice"
DROP_SERVICE = "dropservice"

COMPOSITOR_FILTER_GROUP = "COMPOSITOR_FILTER" # THIS IS NOT USED ANYMORE! DOUBLE CHECK THAT THIS REALLY IS THE CASE AND KILL!
MULTIPART_FILTER = "multipart" # identifies filter as multipart filter
MULTIPART_PROPERTY = "multipartproperty" # Describes properties of multipart filter
MULTIPART_START = "multistartprop" # name of property into which value at start of part-filter is set 
MULTIPART_END = "multiendprop" # name of property into which value at start of part-filter is set 

# Document
filters_doc = None

# Filters are saved as tuples of group name and array of FilterInfo objects.
groups = []

# Filters that are not present in the system 
not_found_filters = []

# dict groupname -> icon
group_icons = None

# Filters that are used as parts of mlttransitions.CompositorObject
# and are not displayed to user
# dict name:FilterInfo
# THIS IS NOT USED ANYMORE! DOUBLE CHECK THAT THIS REALLY IS THE CASE AND KILL!
compositor_filters = {}

# ICONS
FILTER_DEFAULT_ICON = None

# Property types.These map to what mlt accepts.
PROP_INT = appconsts.PROP_INT
PROP_FLOAT = appconsts.PROP_FLOAT
PROP_EXPRESSION = appconsts.PROP_EXPRESSION

# HACK! references to old filters are kept because freeing them causes crashes
old_filters = []

# We need this to mute clips
_volume_filter_info = None

def _load_icons():
    global FILTER_DEFAULT_ICON
    FILTER_DEFAULT_ICON = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "filter.png")
    
def _get_group_icon(group_name):
    global group_icons
    if group_icons == None:
        group_icons = {}
        group_icons["Color"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "color.png")
        group_icons["Color Effect"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "color_filter.png")
        group_icons["Audio"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "audio_filter.png")
        group_icons["Audio Filter"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "audio_filter_sin.png")
        group_icons["Blur"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "blur_filter.png")
        group_icons["Distort"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "distort_filter.png")
        group_icons["Alpha"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "alpha_filter.png")
        group_icons["Movement"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "movement_filter.png")
        group_icons["Transform"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "transform.png")
        group_icons["Edge"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "edge.png")
        group_icons["Fix"] = gtk.gdk.pixbuf_new_from_file(respaths.IMAGE_PATH + "fix.png")
        group_icons["Artistic"] = FILTER_DEFAULT_ICON

    try:
        return group_icons[group_name]
    except:
        return FILTER_DEFAULT_ICON
    
def _translate_group_name(group_name):
    """
    Not implemented.
    """
    return translations.filter_groups[group_name]

    
def get_translated_audio_group_name():
    """
    Not implemented.
    """
    translations.get_filter_group_name("Audio")

class FilterInfo:
    """
    Info of a filter (mlt.Service) that is is available to the user.
    Constructor input is a dom node object.
    This is used to create FilterObject objects.
    """
    def __init__(self, filter_node):
        self.mlt_service_id = filter_node.getAttribute(ID)
        
        try:
            self.multipart_filter = (filter_node.getAttribute(MULTIPART_FILTER) == "true")
        except: # default is False
            self.multipart_filter = False

        try:
            self.mlt_drop_version = filter_node.getAttribute(MLT_DROP_VERSION)
        except: 
            self.mlt_drop_version = None

        try:
            self.mlt_min_version = filter_node.getAttribute(MLT_MIN_VERSION)
        except:
            self.mlt_min_version = None

        self.xml = filter_node.toxml()
        self.name = filter_node.getElementsByTagName(NAME).item(0).firstChild.nodeValue
        self.group = filter_node.getElementsByTagName(GROUP).item(0).firstChild.nodeValue

        # Properties saved as name-value-type tuplets
        p_node_list = filter_node.getElementsByTagName(PROPERTY)
        self.properties = propertyparse.node_list_to_properties_array(p_node_list)
        
        # Property args saved in propertyname -> propertyargs_string dict
        self.property_args = propertyparse.node_list_to_args_dict(p_node_list)
    
        # Multipart property describes how filters are created and edited when filter 
        # constists of multiple filters.
        # There 0 or 1 of these in the info object.
        node_list = filter_node.getElementsByTagName(MULTIPART_PROPERTY)
        if len(node_list) == 1:
            mp = node_list[0]
            value = mp.firstChild.nodeValue
            args = mp.getAttribute(ARGS)
            start_property = mp.getAttribute(MULTIPART_START)
            end_property = mp.getAttribute(MULTIPART_END)
            self.multipart_desc = (args, start_property, end_property)
            self.multipart_value = value

        #  Extra editors that handle properties that have been set "no_editor"
        e_node_list = filter_node.getElementsByTagName(EXTRA_EDITOR)
        self.extra_editors = propertyparse.node_list_to_extraeditors_array(e_node_list)  

        # Non-MLT properties are persistent values like properties that values are not directly written out as MLT properties
        p_node_list = filter_node.getElementsByTagName(NON_MLT_PROPERTY)
        self.non_mlt_properties = propertyparse.node_list_to_non_mlt_properties_array(p_node_list)
        # Property args for Non-MLT properties saved in propertyname -> propertyargs_string dict
        self.property_args.update(propertyparse.node_list_to_args_dict(p_node_list))
        
    def get_icon(self):
        return _get_group_icon(self.group)


class FilterObject:
    """
    These objects are saved with projects. Thay are used to generate, 
    update and hold a reference to an mlt.Filter object attached to a mlt.Producer object
    representing a clip on the timeline.
    
    These are essentially wrappers to mlt.Filter objects which can't be saved or loaded with pickle().
    """
    def __init__(self, filter_info):
        self.info = filter_info
        # Values of these are edited by the user.
        self.properties = copy.deepcopy(filter_info.properties)
        try:
            self.non_mlt_properties = copy.deepcopy(filter_info.non_mlt_properties)
        except:
            self.non_mlt_properties = [] # Versions prior 0.14 do not have non_mlt_properties and fail here on load

        self.mlt_filter = None # reference to MLT C-object
        self.active = True 

        # PROP_EXPR values may have keywords that need to be replaced with
        # numerical values that depend on the profile we have. These need
        # to be replaced now that we have profile and we are ready to connect this.
        # For example default values of some properties depend on the screen size of the project
        propertyparse.replace_value_keywords(self.properties, PROJECT().profile)
    
    def create_mlt_filter(self, mlt_profile):
        self.mlt_filter = mlt.Filter(mlt_profile, str(self.info.mlt_service_id))
        mltrefhold.hold_ref(self.mlt_filter)
        self.update_mlt_filter_properties_all()
    
    def update_mlt_filter_properties_all(self):
        """
        Called at creation time and when loaded to set all mlt properties
        of a compositor filter to correct values.
        """
        for prop in self.properties:
            name, value, prop_type = prop
            self.mlt_filter.set(str(name), str(value)) # new const strings are created from values
    
    def update_mlt_disabled_value(self):
        if self.active == True:
             self.mlt_filter.set("disable", str(0))
        else:
             self.mlt_filter.set("disable", str(1))
    
    def reset_values(self,  mlt_profile=None, clip=None): #multipartfilters need profile and clip
        for i in range(0, len(self.properties)):
            name, o_value, prop_type = self.info.properties[i]
            name, value, prop_type = self.properties[i]
            self.properties[i] = (name, o_value, prop_type)
        
        self.update_mlt_filter_properties_all()


class MultipartFilterObject:
    """
    These objects are saved with projects. Thay are used to generate, 
    update and hold references to a GROUP of mlt.Filter objects attached to a mlt.Producer object.
    """
    def __init__(self, filter_info):
        self.info = filter_info
        # Values of these are edited by the user.
        self.properties = copy.deepcopy(filter_info.properties)
        self.non_mlt_properties = copy.deepcopy(filter_info.non_mlt_properties)
        self.value = copy.deepcopy(filter_info.multipart_value)
        self.active = True
        
    def create_mlt_filters(self, mlt_profile, clip):
        self.mlt_filters = []
        self.keyframes = self._parse_value_to_keyframes()
        # We need always at least 2 keyframes (at the start and end of 1 filter)
        # but we only know the position of last keyframe now that we have the clip.
        # The default value in filters.xml has only 1 keyframe for frame 0
        # so we add the second one now.
        if len(self.keyframes) == 1:
            f, v = self.keyframes[0]
            self.value = self.value.strip('"') + ";" + str(clip.get_length()) + "=" + str(v)
            self.keyframes.append((clip.get_length(), v))

        self.create_filters_for_keyframes(self.keyframes, mlt_profile)
        self.update_mlt_filters_values(self.keyframes)
        
    def update_value(self, kf_str, clip, mlt_profile):
        new_kf = self._parse_string_to_keyframes(kf_str)
        
        # If same amount of keyframes, just update values
        if len(new_kf) == len(self.keyframes):
            self.update_mlt_filters_values(new_kf)
            self.keyframes = new_kf
        else:
            self.detach_all_mlt_filters(clip)
            old_filters.append(self.mlt_filters) # hack to prevent object release crashes
            self.mlt_filters = []
            self.keyframes = new_kf
            self.create_filters_for_keyframes(self.keyframes, mlt_profile)
            self.update_mlt_filters_values(self.keyframes)
            self.attach_all_mlt_filters(clip)
        
        self.value = kf_str

    def create_filters_for_keyframes(self, keyframes, mlt_profile):
        for i in range(0, len(keyframes) - 1): # Theres one less filter parts than keyframes
            mlt_filter = mlt.Filter(mlt_profile, str(self.info.mlt_service_id))
            mltrefhold.hold_ref(mlt_filter)
            self.mlt_filters.append(mlt_filter)
            
    def update_mlt_filters_values(self, keyframes):
        """
        Called obove at creation time and when loaded to set all mlt properties
        of all filters
        """
        args, start_property, end_property = self.info.multipart_desc
        for i in range(0, len(keyframes) - 1):
            start_frame, start_value = keyframes[i]
            end_frame, end_value = keyframes[i + 1]

            mlt_filter = self.mlt_filters[i]

            # Set all property values to defaults
            for property in self.properties:
                name, val, type = property
                mlt_filter.set(str(name), str(val))
                
            # set in and out points
            mlt_filter.set("in", str(start_frame))
            end_frame = int(end_frame) - 1
            mlt_filter.set("out", str(end_frame))
            
            # set start and end values
            mlt_filter.set(str(start_property), str(start_value)) # Value at start of filter part
            mlt_filter.set(str(end_property), str(end_value)) # Value at end of filter part

    def _parse_value_to_keyframes(self):
        return self._parse_string_to_keyframes(self.value)
        
    def _parse_string_to_keyframes(self, kf_string):
        # returs list of (frame, value) tuples
        value = kf_string.strip('"') # for some reason we have to use " around values or something broke
        parts = value.split(";")
        kfs = []
        for part in parts:
            tokens = part.split("=")
            kfs.append((tokens[0],tokens[1]))
        return kfs
    
    def attach_all_mlt_filters(self, clip):
        for f in self.mlt_filters:
            clip.attach(f)
            
    def detach_all_mlt_filters(self, clip):
        for f in self.mlt_filters:
            clip.detach(f)

    def update_mlt_disabled_value(self):
        if self.active == True:
            for f in self.mlt_filters:
                f.set("disable", str(0))
        else:
            for f in self.mlt_filters:
                f.set("disable", str(1))
    
    def reset_values(self, mlt_profile, clip):
        self.value = copy.deepcopy(self.info.multipart_value)
        self.update_value(self.value, clip, mlt_profile)


def load_filters_xml(services):
    """
    Load filters document and save filters nodes as FilterInfo objects in array.
    Save them also as array of tuples of names and arrays of FilterInfo objects
    that represent named groups of filters as displayd to user.
    """
    _load_icons()
    
    print "Loading filters..."
    
    global filters_doc
    filters_doc = xml.dom.minidom.parse(respaths.FILTERS_XML_DOC)

    load_groups = {}
    filter_nodes = filters_doc.getElementsByTagName(FILTER)
    for f_node in filter_nodes:
        filter_info = FilterInfo(f_node)

        if filter_info.mlt_drop_version != "":
            if editorstate.mlt_version_is_equal_or_greater(filter_info.mlt_drop_version):
                print filter_info.name + " dropped, MLT version too high for this filter."
                continue

        if filter_info.mlt_min_version != "":
            if not editorstate.mlt_version_is_equal_or_greater(filter_info.mlt_min_version):
                print filter_info.name + " dropped, MLT version too low for this filter."
                continue

        if (not filter_info.mlt_service_id in services) and len(services) > 0:
            print "MLT service " + filter_info.mlt_service_id + " not found."
            global not_found_filters
            not_found_filters.append(filter_info)
            continue

        if filter_info.mlt_service_id == "volume": # we need this filter to do mutes so save reference to it
            global _volume_filter_info
            _volume_filter_info = filter_info

        # Add filter compositor filters or filter groups
        if filter_info.group == COMPOSITOR_FILTER_GROUP:
            global compositor_filters
            compositor_filters[filter_info.name] = filter_info
        else:
            translated_group_name = _translate_group_name(filter_info.group)
            try:
                group = load_groups[translated_group_name]
                group.append(filter_info)
            except:
                load_groups[translated_group_name] = [filter_info]

    # We used translated group names as keys in load_groups
    # Now we sort them and use them to place data in groups array in the same
    # order as it will be presented to user, so selection indexes in gui components will match
    # group array indexes here.
    sorted_keys = sorted(load_groups.keys())
    global groups
    for gkey in sorted_keys:
        group = load_groups[gkey]
        add_group = sorted(group, key=lambda finfo: translations.get_filter_name(finfo.name) )
        groups.append((gkey, add_group))

def clone_filter_object(filter_object, mlt_profile):
    """
    Creates new filter object with with copied properties values.
    """
    clone = FilterObject(filter_object.info)
    clone.properties = copy.deepcopy(filter_object.properties)
    clone.create_mlt_filter(mlt_profile)
    return clone

def replace_services(services):
    # this has gotta be a bullshit way to do this
    
    replacements_doc = xml.dom.minidom.parse(respaths.REPLACEMENTS_XML_DOC)

    # Build dict that has enough info to enable deleting and finding filters by name
    filters_dict = {}
    for group_data in groups:
        gkey, group = group_data
        for f in group:
            filters_dict[f.name] = (f, group)

    # Replace services
    replacement_nodes = replacements_doc.getElementsByTagName(REPLACEMENT_RELATION)
    for r_node in replacement_nodes:

        # Get use service values
        use_node = r_node.getElementsByTagName(USE_SERVICE).item(0)
        use_service_id = use_node.getAttribute(ID)
        use_service_name = use_node.getAttribute(NAME)

        # Try replace if use service and use filter exist
        if (use_service_id in services) and len(services) > 0:
            try:
                use_service_data = filters_dict[use_service_name]
            except:
                print "Replace service " + use_service_name + " not found."
                continue
            
            drop_nodes = r_node.getElementsByTagName(DROP_SERVICE)
            
            try:
                # Drop service if found
                for d_node in drop_nodes:
                    drop_service_id = d_node.getAttribute(ID)
                    drop_service_name = d_node.getAttribute(NAME)

                    drop_service_data = filters_dict[drop_service_name]
                    f_info, group = drop_service_data
                    for i in range(0, len(group)):
                        if group[i].name == f_info.name:
                            group.pop(i)
                            print f_info.name +" dropped for " + use_service_name
                            break
            except:
                print "Dropping a mlt service for " + use_service_name + " failed, maybe not present."

def get_compositor_filter(filter_id):
    return compositor_filters[filter_id]

def get_audio_filters_groups():
    for group_tuple in groups:
        gkey, group = group_tuple
        if gkey == translations.get_filter_group_name("Audio"):
            group_tuple1 = group_tuple
        if gkey == translations.get_filter_group_name("Audio Filter"):
            group_tuple2 = group_tuple

    return [group_tuple1, group_tuple2]

def get_volume_filters_info():
    return _volume_filter_info

def detach_all_filters(clip):
    for f in clip.filters:
        if isinstance(f, FilterObject):
            clip.detach(f.mlt_filter)
        else:# f is mltfilters.MultiFilterObject
            f.detach_all_mlt_filters(clip)

def attach_all_filters(clip):
    for f in clip.filters:
        if isinstance(f, FilterObject):
            clip.attach(f.mlt_filter)
        else:# f is mltfilters.MultiFilterObject
            f.attach_all_mlt_filters(clip)
            
def get_all_found_filters():
    all_filters = []
    for group_tuple in groups:
        gkey, group = group_tuple
        all_filters = all_filters + group
    return all_filters

def print_found_filters():
    all_filters = get_all_found_filters()
    for f in all_filters:
        print f.mlt_service_id + " for filter " + f.name  + " available"

def print_not_found_filters():
    for f in not_found_filters:
        print f.mlt_service_id + " for filter " + f.name + " not found"


# ------------------------------------------------------------- mute filters
def create_mute_volume_filter(seq):    
    mute_filter = seq.create_filter(get_volume_filters_info())
    mute_filter.mlt_filter.set("gain","0")
    mute_filter.mlt_filter.set("end","0")
    return mute_filter

def do_clip_mute(clip, volume_filter):
    clip.attach(volume_filter.mlt_filter)
    clip.mute_filter = volume_filter
    
