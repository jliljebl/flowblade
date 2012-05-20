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
Module contains objects that wrap mlt.Transition objects used to mix video betweeen
two tracks.
"""
import copy
import gtk
import mlt
import os
import xml.dom.minidom

import appconsts
import mltfilters
import persistance
import propertyparse
import respaths
import utils

# Attr and node names in compositors.xml
NAME = appconsts.NAME
ARGS = appconsts.ARGS
PROPERTY = appconsts.PROPERTY
EXTRA_EDITOR = appconsts.EXTRA_EDITOR
MLT_SERVICE = appconsts.MLT_SERVICE
COMPOSITOR = "compositortransition"

# Property types.
PROP_INT = appconsts.PROP_INT
PROP_FLOAT = appconsts.PROP_FLOAT
PROP_EXPRESSION = appconsts.PROP_EXPRESSION

# Info objects used to create mlt.Transitions for CompositorObject objects.
# dict name : MLTCompositorInfo
mlt_compositor_transition_infos = {}

# Wipes
# User displayed name -> resource image
wipe_lumas = None
compositors = None
blenders = None

def init_module():

    # translations and module load order make us do this
    global wipe_lumas, compositors, blenders
    wipe_lumas = { \
                _("Vertical From Center"):"bi-linear_x.pgm",
                _("Vertical Top to Bottom"):"wipe_top_to_bottom.svg",
                _("Vertical Bottom to Top"):"wipe_bottom_to_top.svg",
                _("Horizontal From Center"):"bi-linear_y.pgm",
                _("Horizontal Left to Right"):"wipe_left_to_right.svg",
                _("Horizontal Right to Left"):"wipe_right_to_left.svg",
                _("Clock Left To Right"):"clock_left_to_right.pgm",
                _("Clock Right to Left"):"clock_right_to_left.pgm",
                _("Clock Symmetric"):"symmetric_clock.pgm",
                _("Stripes Horizontal"):"blinds_in_to_out.pgm",
                _("Stripes Horizontal Big"):"blinds_in_to_out_big.pgm",
                _("Stripes Horizontal Moving"):"blinds_sliding.png",
                _("Stripes Vertical"):"vertical_blinds_in_to_out.pgm",
                _("Stripes Vertical Big"):"vertical_blinds_in_to_out_big.pgm",
                _("Burst"):"burst.pgm",
                _("Circle From In"):"circle_in_to_out.svg",
                _("Circle From Out"):"circle_out_to_in.svg",
                _("Cloud"):"cloud.pgm",
                _("Hatched 1"):"hatched_1.png",
                _("Hatched 2"):"hatched_2.png",
                _("Hourglass"):"hourglass_1.png",
                _("Puddles"):"mountains.png",
                _("Rings"):"radial-bars.pgm",
                _("Rectangle From In"):"rectangle_in_to_out.pgm",
                _("Rectangle From Out"):"rectangle_out_to_in.pgm",
                _("Rectangle Bars"):"square2-bars.pgm",
                _("Sand"):"sand.svg",
                _("Sphere"):"sphere.png",
                _("Spiral Abstract"):"spiral_abstract_1.png",
                _("Spiral"):"spiral.pgm",
                _("Spiral Galaxy"):"spiral2.pgm",
                _("Spiral Big"):"spiral_big.pgm",
                _("Spiral Medium"):"spiral_medium.pgm",
                _("Spots"):"spots.png",
                _("Star"):"star_2.png",
                _("Arch"):"fractal_1.png",
                _("Patches"):"fractal_4.png",
                _("Free Stripes"):"fractal_5.png",
                _("Free Curves"):"fractal_7.png",
                _("Diagonal 1"):"wipe_diagonal_1.png",
                _("Diagonal 2"):"wipe_diagonal_2.png",
                _("Diagonal 3"):"wipe_diagonal_3.png",
                _("Diagonal 4"):"wipe_diagonal_4.png",
                _("Checkerboard"):"checkerboard_small.pgm"}

    # Name -> creator funcion dict.
    compositors = [ (_("Affine"),_create_affine_compositor),
                    (_("Dissolve"),_create_dissolve_compositor),
                    (_("Picture in Picture"),_create_pict_in_pict_compositor),
                    (_("Region"), _create_region_wipe_compositor),
                    (_("Wipe Clip Length"), _create_wipe_compositor)]

    # name -> mlt_compositor_transition_infos key dict.
    blenders = [(_("Add"),"##add"),
                (_("Burn"),"##burn"),
                (_("Color only"),"##color_only"),
                (_("Darken"),"##darken"),
                (_("Difference"),"##difference"),
                (_("Divide"),"##divide"),
                (_("Dodge"),"##dodge"),
                (_("Grain extract"),"##grain_extract"),
                (_("Grain merge"),"##grain_merge"),
                (_("Hardlight"),"##hardlight"),
                (_("Hue"),"##hue"),
                (_("Lighten"),"##lighten"),
                (_("Multiply"),"##multiply"),
                (_("Overlay"),"##overlay"),
                (_("Saturation"),"##saturation"),
                (_("Screen"),"##screen"),
                (_("Softlight"),"##softlight"),
                (_("Subtract"),"##subtract"),
                (_("Value"),"##value")]

# ------------------------------------------ compositors
class CompositorTransitionInfo:
    """
    Constructor input is a XML dom node object. Convers XML data to another form
    used to create CompositorTransition objects.
    """
    def __init__(self, compositor_node):
        self.mlt_service_id = compositor_node.getAttribute(MLT_SERVICE)
        self.xml = compositor_node.toxml()
        self.name = compositor_node.getElementsByTagName(NAME).item(0).firstChild.nodeValue
        
        # Properties saved as name-value-type tuplets
        p_node_list = compositor_node.getElementsByTagName(PROPERTY)
        self.properties = propertyparse.node_list_to_properties_array(p_node_list)
        
        # Property args saved in propertyname -> propertyargs_string dict
        self.property_args = propertyparse.node_list_to_args_dict(p_node_list)
        
        #  Extra editors that handle hardcoded properties that have been set "no_editor"
        e_node_list = compositor_node.getElementsByTagName(EXTRA_EDITOR)
        self.extra_editors = propertyparse.node_list_to_extraeditors_array(e_node_list)  


class CompositorTransition:
    """
    These objects are part of sequence.Sequence and desribew video transition between two tracks.
    They wrap mlt.Transition objects that do the actual mixing.
    """
    def __init__(self, transition_info):
        self.mlt_transition = None
        self.info = transition_info
        # Editable properties, usually a subset of all properties of 
        # mlt_serveice "composite", defined in compositors.xml
        self.properties = copy.deepcopy(transition_info.properties)

        self.a_track = -1 # to, destination
        self.b_track = -1 # from, source
    
    def create_mlt_transition(self, mlt_profile):
        self.mlt_transition = mlt.Transition(mlt_profile, 
                                              str(self.info.mlt_service_id))
                                              
        self.set_default_values()
        
        # PROP_EXPR values may have keywords that need to be replaced with
        # numerical values that depend on the profile we have. These need
        # to be replaced now that we have profile and we are ready to connect this.
        propertyparse.replace_value_keywords(self.properties, mlt_profile)
        
        self.update_editable_mlt_properties()

    def set_default_values(self):
        if self.info.mlt_service_id == "composite":
            self._set_composite_service_default_values() 
        elif self.info.mlt_service_id == "affine":
            self._set_affine_service_default_values()
        elif self.info.mlt_service_id == "luma":
            self._set_luma_service_default_values()
        elif self.info.mlt_service_id == "region":
            self._set_region_service_default_values()
        else:
            self._set_blend_service_default_values()
        
    def _set_composite_service_default_values(self):
        self.mlt_transition.set("automatic",1)
        self.mlt_transition.set("aligned", 1)
        self.mlt_transition.set("deinterlace",0)
        self.mlt_transition.set("distort",0)
        self.mlt_transition.set("fill",1)
        self.mlt_transition.set("operator","over")
        self.mlt_transition.set("luma_invert",0)
        self.mlt_transition.set("progressive",1)
        self.mlt_transition.set("softness",0)

    def _set_affine_service_default_values(self):
        self.mlt_transition.set("distort",0)
        self.mlt_transition.set("automatic",1)
        self.mlt_transition.set("keyed",1)
   
    def _set_luma_service_default_values(self):
        self.mlt_transition.set("automatic",1)
        self.mlt_transition.set("invert",0)
        self.mlt_transition.set("reverse",0)
        self.mlt_transition.set("softness",0)

    def _set_region_service_default_values(self):
        self.mlt_transition.set("automatic",1)
        self.mlt_transition.set("aligned", 1)
        self.mlt_transition.set("deinterlace",0)
        self.mlt_transition.set("distort",0)
        self.mlt_transition.set("fill",1)
        self.mlt_transition.set("operator","over")
        self.mlt_transition.set("luma_invert",0)
        self.mlt_transition.set("fill",1)
        self.mlt_transition.set("progressive",1)
        self.mlt_transition.set("softness",0)
  
    def _set_blend_service_default_values(self):
        self.mlt_transition.set("automatic",1)
    
    def set_tracks(self, a_track, b_track):
        self.a_track = a_track
        self.b_track = b_track
        self.mlt_transition.set("a_track", str(a_track))
        self.mlt_transition.set("b_track", str(b_track))

    def set_target_track(self, a_track, force_track):
        self.a_track = a_track
        self.mlt_transition.set("a_track", str(a_track))
        if force_track == True:
            fval = 1
        else:
            fval = 0
        self.mlt_transition.set("force_track",str(fval))

    def update_editable_mlt_properties(self):
        for prop in self.properties:
            name, value, prop_type = prop
            self.mlt_transition.set(str(name), str(value)) # new const strings are created from values


class CompositorObject:
    """
    These objects are saved with projects. Thay are used to create, 
    update and hold references to mlt.Transition
    objects that define a composite between two tracks.

    mlt.Transition (self.transition) needs it in and out and visibility to be updated
    for every single edit action ( see edit.py _insert_clip() and
    _remove_clip() ) 
    """
    def __init__(self, transition_info):
        self.transition = CompositorTransition(transition_info)
        self.clip_in = -1 # ducktyping for clip for property editors
        self.clip_out = -1 # ducktyping for clip for property editors
        self.planted = False
        self.compositor_index = None
        self.name = None # ducktyping for clip for property editors
        self.selected = False
        self.origin_clip_id = None
        self.destroy_id = os.urandom(16) # Objects are recreated often in Sequence.restack_compositors()
                                         # and cannot be destroyd in undo/redo with object identidy.
                                         # This is cloned in clone_properties

    def get_length(self):
        # ducktyping for clip for property editors
        return self.clip_out - self.clip_in  + 1 # +1 out inclusive

    def set_in_and_out(self, in_frame, out_frame):
        self.clip_in = in_frame
        self.clip_out = out_frame
        self.transition.mlt_transition.set("in", str(in_frame))
        self.transition.mlt_transition.set("out", str(out_frame))

    def create_mlt_objects(self, mlt_profile):
        self.transition.create_mlt_transition(mlt_profile)
    
    def clone_properties(self, source_compositor):
        self.destroy_id = source_compositor.destroy_id
        self.origin_clip_id = source_compositor.origin_clip_id
        self.transition.properties = copy.deepcopy(source_compositor.transition.properties)
        self.transition.update_editable_mlt_properties()

# -------------------------------------------------- compositor interface methods
def load_compositors_xml():
    """
    Load filters document and create MLTCompositorInfo objects and
    put them in dict mlt_compositor_infos with names as keys.
    """
    compositors_doc = xml.dom.minidom.parse(respaths.COMPOSITORS_XML_DOC)

    compositor_nodes = compositors_doc.getElementsByTagName(COMPOSITOR)
    for c_node in compositor_nodes:
        compositor_info = CompositorTransitionInfo(c_node)
        mlt_compositor_transition_infos[compositor_info.name] = compositor_info

def get_wipe_resource_path(key):
    img_file = wipe_lumas[key]
    return respaths.WIPE_RESOURCES_PATH + img_file

def create_compositor(compositor_type_index):
    if compositor_type_index < len(compositors): #Create compositor
        name, create_func = compositors[compositor_type_index]
        compositor = create_func()
    else: # Create blender compositor
        name, transition_id_str = blenders[compositor_type_index - len(compositors)]
        compositor = _create_blender(transition_id_str)
    """
    for persistance, used to recreate at load
    INDEXES:
    0                     - len(compositors) - 1                     --- compositors
    len(compositors)      - len(compositors) + len(blenders) - 1     --- blenders
    """
    compositor.compositor_index = compositor_type_index
    compositor.name = name
    return compositor


# ------------------------------------------------- CompositorObject creators
def _create_affine_compositor():
    transition_info = mlt_compositor_transition_infos["##affine"]
    return CompositorObject(transition_info)

def _create_pict_in_pict_compositor():
    transition_info = mlt_compositor_transition_infos["##pict_in_pict"]
    return CompositorObject(transition_info)

def _create_dissolve_compositor():
    transition_info = mlt_compositor_transition_infos["##opacity_kf"]
    return CompositorObject(transition_info)

def _create_region_wipe_compositor():
    transition_info = mlt_compositor_transition_infos["##region"]
    return CompositorObject(transition_info)

def _create_wipe_compositor():
    transition_info = mlt_compositor_transition_infos["##wipe"]
    return CompositorObject(transition_info)

def _create_blender(transition_id_str):
    transition_info = mlt_compositor_transition_infos[transition_id_str]
    return CompositorObject(transition_info)
 
def _get_transition_wrapper_object(transition_info):
    return CompositorTransition(transition_info)



