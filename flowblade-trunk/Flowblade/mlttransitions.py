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
import mlt
import os
import xml.dom.minidom

import appconsts
import mltrefhold
import patternproducer
import propertyparse
import respaths

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

# Renderered transitions
RENDERED_DISSOLVE = appconsts.RENDERED_DISSOLVE
RENDERED_WIPE = appconsts.RENDERED_WIPE
RENDERED_COLOR_DIP = appconsts.RENDERED_COLOR_DIP
RENDERED_FADE_IN = appconsts.RENDERED_FADE_IN
RENDERED_FADE_OUT = appconsts.RENDERED_FADE_OUT

rendered_transitions = None # list is set here at init_module() because otherwise translations can't be done (module load issue)

# Info objects used to create mlt.Transitions for CompositorObject objects.
# dict name : MLTCompositorInfo
mlt_compositor_transition_infos = {}

# Name -> type dict, used at creation when type is known, but name data has been left behind
name_for_type = {}

# Transitions not found in the system
not_found_transitions = [] 

wipe_lumas = None # User displayed name -> resource image
compositors = None
blenders = None

def init_module():

    # translations and module load order make us do this in method instead of at module load
    global wipe_lumas, compositors, blenders, name_for_type, rendered_transitions, single_track_render_type_names
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

    # name -> mlt_compositor_transition_infos key dict.
    unsorted_compositors = [ (_("Affine"),"##affine"),
                             (_("Dissolve"),"##opacity_kf"),
                             (_("Picture in Picture"),"##pict_in_pict"),
                             (_("Region"), "##region"),
                             (_("Affine Blend"), "##affineblend"),
                             (_("Blend"), "##blend"),
                             (_("Wipe Clip Length"),"##wipe")]

    compositors = sorted(unsorted_compositors, key=lambda comp: comp[0])   

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

    for comp in compositors:
        name, comp_type = comp
        name_for_type[comp_type] = name
    
    for blend in blenders:
        name, comp_type = blend
        name_for_type[comp_type] = name
    
    # change this, tuples are not need we only need list of translatd names
    rendered_transitions = [  (_("Dissolve"), RENDERED_DISSOLVE), 
                              (_("Wipe"), RENDERED_WIPE),
                              (_("Color Dip"), RENDERED_COLOR_DIP),
                              (_("Fade In"), RENDERED_FADE_IN),
                              (_("Fade Out"), RENDERED_FADE_OUT)]

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
        
        #  Extra editors that handle properties that have been set "no_editor"
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
        transition = mlt.Transition(mlt_profile, 
                                   str(self.info.mlt_service_id))
        mltrefhold.hold_ref(transition)
        self.mlt_transition = transition
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
        self.mlt_transition.set("aligned",1)
        self.mlt_transition.set("deinterlace",0)
        self.mlt_transition.set("distort",0)
        self.mlt_transition.set("fill",1)
        self.mlt_transition.set("operator","over")
        self.mlt_transition.set("luma_invert",0)
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
        
        self.destroy_id = os.urandom(16) # HACK, HACK, HACK - find a way to remove this stuff  
                                         # Objects are recreated often in Sequence.restack_compositors()
                                         # and cannot be destroyd in undo/redo with object identidy.
                                         # This is cloned in clone_properties

    def get_length(self):
        # ducktyping for clip for property editors
        return self.clip_out - self.clip_in  + 1 # +1 out inclusive

    def move(self, delta):
        self.clip_in = self.clip_in + delta
        self.clip_out = self.clip_out + delta
        self.transition.mlt_transition.set("in", str(self.clip_in))
        self.transition.mlt_transition.set("out", str(self.clip_out))

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
def load_compositors_xml(transitions):
    """
    Load filters document and create MLTCompositorInfo objects and
    put them in dict mlt_compositor_infos with names as keys.
    """
    compositors_doc = xml.dom.minidom.parse(respaths.COMPOSITORS_XML_DOC)

    print "Loading transitions..."
    compositor_nodes = compositors_doc.getElementsByTagName(COMPOSITOR)
    for c_node in compositor_nodes:
        compositor_info = CompositorTransitionInfo(c_node)
        if (not compositor_info.mlt_service_id in transitions) and len(transitions) > 0:
            print "MLT transition " + compositor_info.mlt_service_id + " not found."
            global not_found_transitions
            not_found_transitions.append(compositor_info)
            continue
        mlt_compositor_transition_infos[compositor_info.name] = compositor_info

def get_wipe_resource_path_for_sorted_keys_index(sorted_keys_index):
    # This exists to avoid sending a list of sorted keys around or having to use global variables
    keys = wipe_lumas.keys()
    keys.sort()
    return get_wipe_resource_path(keys[sorted_keys_index])
    
def get_wipe_resource_path(key):
    img_file = wipe_lumas[key]
    return respaths.WIPE_RESOURCES_PATH + img_file

def create_compositor(compositor_type):
    transition_info = mlt_compositor_transition_infos[compositor_type]
    compositor = CompositorObject(transition_info)
    compositor.compositor_index = -1 # not used since SAVEFILE = 3
    compositor.name = name_for_type[compositor_type]
    compositor.type_id = compositor_type # this is a string like "##add", "##affineblend", in compositors.xml it is name element: <name>##affine</name> etc...
    return compositor


# ------------------------------------------------------ rendered transitions
# These are tractor objects used to create rendered transitions.
def get_rendered_transition_tractor(current_sequence, 
                                    orig_from,
                                    orig_to,
                                    action_from_out,
                                    action_from_in,
                                    action_to_out,
                                    action_to_in,
                                    transition_type_selection_index,
                                    wipe_luma_sorted_keys_index,
                                    gdk_color_str):

    name, transition_type = rendered_transitions[transition_type_selection_index]

    # New from clip
    if orig_from.media_type != appconsts.PATTERN_PRODUCER:
        from_clip = current_sequence.create_file_producer_clip(orig_from.path)# File producer
    else:
        from_clip = current_sequence.create_pattern_producer(orig_from.create_data) # pattern producer
    current_sequence.clone_clip_and_filters(orig_from, from_clip)

    # New to clip
    if not(transition_type == RENDERED_FADE_IN or transition_type == RENDERED_FADE_OUT): # fades to not use to_clip
        if orig_to.media_type != appconsts.PATTERN_PRODUCER:
            to_clip = current_sequence.create_file_producer_clip(orig_to.path)# File producer
        else:
            to_clip = current_sequence.create_pattern_producer(orig_to.create_data) # pattern producer
        current_sequence.clone_clip_and_filters(orig_to, to_clip)

    # Create tractor and tracks
    tractor = mlt.Tractor()
    multitrack = tractor.multitrack()
    track0 = mlt.Playlist()
    track1 = mlt.Playlist()
    multitrack.connect(track0, 0)
    multitrack.connect(track1, 1)

    # we'll set in and out points for images and pattern producers.
    if not(transition_type == RENDERED_FADE_IN or transition_type == RENDERED_FADE_OUT): # fades to not use to_clip or some other data used here
        if from_clip.media_type == appconsts.IMAGE or from_clip.media_type == appconsts.PATTERN_PRODUCER:
            length = action_from_out - action_from_in
            from_clip.clip_in = 0
            from_clip.clip_out = length

        if to_clip.media_type == appconsts.IMAGE or to_clip.media_type == appconsts.PATTERN_PRODUCER:
            length = action_to_out - action_to_in
            to_clip.clip_in = 0
            to_clip.clip_out = length
    else:
        length = action_from_out
        if from_clip.media_type == appconsts.IMAGE or from_clip.media_type == appconsts.PATTERN_PRODUCER:
            from_clip.clip_in = 0
            from_clip.clip_out = length
            
    # Add clips to tracks and create keyframe string to contron mixing
    if transition_type == RENDERED_DISSOLVE or transition_type == RENDERED_WIPE:
        # Add clips. Images and pattern producers always fill full track.
        if from_clip.media_type != appconsts.IMAGE and from_clip.media_type != appconsts.PATTERN_PRODUCER:
            track0.insert(from_clip, 0, action_from_in, action_from_out)
        else:
            track0.insert(from_clip, 0, 0, action_from_out - action_from_in)
            
        if to_clip.media_type != appconsts.IMAGE and to_clip.media_type != appconsts.PATTERN_PRODUCER: 
            track1.insert(to_clip, 0, action_to_in, action_to_out)
        else:
            track1.insert(to_clip, 0, 0,  action_to_out - action_to_in)
        kf_str = "0=0/0:100%x100%:0.0;"+ str(tractor.get_length() - 1) + "=0/0:100%x100%:100.0"
    elif transition_type == RENDERED_COLOR_DIP:
        length = action_from_out - action_from_in
        first_clip_length = length / 2
        second_clip_length = length - first_clip_length
        color_clip = patternproducer.create_color_producer(current_sequence.profile, gdk_color_str)
        track0.insert(color_clip, 0, 0, length)
        track1.insert(from_clip, 0, action_from_in, action_from_in + first_clip_length)
        track1.insert(to_clip, 1, action_to_out - second_clip_length, action_to_out)
        kf_str = "0=0/0:100%x100%:100.0;"+ str(first_clip_length) + "=0/0:100%x100%:0.0;" + str(tractor.get_length() - 1) + "=0/0:100%x100%:100.0"
    elif (transition_type == RENDERED_FADE_IN or transition_type == RENDERED_FADE_OUT):
        color_clip = patternproducer.create_color_producer(current_sequence.profile, gdk_color_str)
        track0.insert(color_clip, 0, 0, length)
        if transition_type ==  RENDERED_FADE_IN:
            track1.insert(from_clip, 0, orig_from.clip_in, orig_from.clip_in + length)
            kf_str = "0=0/0:100%x100%:0.0;"+ str(length) + "=0/0:100%x100%:100.0"
        else: # transition_type ==  RENDERED_FADE_OUT
            track1.insert(from_clip, 0, orig_from.clip_out - length, orig_from.clip_out)
            kf_str = "0=0/0:100%x100%:100.0;"+ str(length) + "=0/0:100%x100%:0.0"

    # Create transition
    transition = mlt.Transition(current_sequence.profile, "region")
    mltrefhold.hold_ref(transition)
    transition.set("composite.geometry", str(kf_str)) # controls mix over time
    transition.set("composite.automatic",1)
    transition.set("composite.aligned", 0)
    transition.set("composite.deinterlace",0)
    transition.set("composite.distort",0)
    transition.set("composite.fill",1)
    transition.set("composite.operator","over")
    transition.set("composite.luma_invert",0)
    transition.set("composite.progressive",1)
    transition.set("composite.softness",0)
    transition.set("in", 0)
    transition.set("out", tractor.get_length() - 1)
    transition.set("a_track", 0)
    transition.set("b_track", 1)

    # Setting luma resource file turns dissolve into wipe
    if transition_type == RENDERED_WIPE:
        wipe_resource_path = get_wipe_resource_path_for_sorted_keys_index(wipe_luma_sorted_keys_index)
        transition.set("composite.luma", str(wipe_resource_path))

    # Add transition
    field = tractor.field()
    field.plant_transition(transition, 0,1)

    return tractor
