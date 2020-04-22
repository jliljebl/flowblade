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

from gi.repository import Gtk
from gi.repository import GObject

import os

import appconsts
import guiutils
import mltprofiles
import renderconsumer
import utils



# NOTE: 
# On module globals:
# - when used by gmic.py for GMic Tool we have no problem with e.g widgets being module global
#   because gmic.py runs in own process.
# - when this module is used in main application process it is important that e.g.widgets object 
#   is created each time module is used to set rendering values for e.g. container clips.
# - when used by a rendering process like gmicheadless.py we are again good to use module freely,
#   process cotrols values in this module fully.
widgets = None
disable_audio_encoding = False
default_profile_index = None



class ToolsRenderData():
    """
    This is used to save render selections defined by user.
    """
    def __init__(self):
        self.profile_index = None
        self.use_default_profile = None
        self.use_preset_encodings = None
        self.presets_index = None
        self.encoding_option_index = None
        self.quality_option_index = None
        self.render_dir = None
        self.file_name = None
        self.file_extension = None
        
        # Used by container clips only.
        self.do_video_render = True
        self.save_internally = True
        self.frame_name = "frame"


def create_container_clip_default_render_data_object(profile):
    # When ToolsRenderData is used by G'Mic tool we need to have default values be 'None', for container clis we need different
    # default values.
    # 
    # When first render is attempted this created to have data availeble for render process
    # even if user has not set any values.
    render_data = ToolsRenderData()
    render_data.profile_index = mltprofiles.get_profile_index_for_profile(profile)
    render_data.use_default_profile = True
    render_data.use_preset_encodings = False
    render_data.presets_index = 0
    render_data.encoding_option_index = 0
    render_data.quality_option_index = 10
    render_data.render_dir = os.path.expanduser("~")
    render_data.file_name = appconsts.CONTAINER_CLIP_VIDEO_CLIP_NAME
    render_data.file_extension = ".mp4"

    return render_data
    
# ------------------------------------------------------------ GUI interface
def create_widgets(def_profile_index, disable_audio=True, create_container_file_panel=False):
    """
    Widgets for editing render properties and viewing render progress.
    """
    global widgets, disable_audio_encoding, default_profile_index
    default_profile_index = def_profile_index
    if disable_audio:
        disable_audio_encoding = True

    widgets = utils.EmptyClass()
     
    widgets.file_panel = RenderFilePanel(create_container_file_panel)
    widgets.profile_panel = RenderProfilePanel(_out_profile_changed)
    widgets.encoding_panel = RenderEncodingPanel(widgets.file_panel.extension_label)

    widgets.profile_panel.out_profile_combo.fill_options()
    _display_default_profile()
    
def get_encoding_panel(render_data, create_container_file_panel=False):
    # We are making two kinds of panels here:
    # - panel for G'Mic tool
    # - panels for Clip Containers render settings

    if create_container_file_panel == False:
        file_panel_title = _("File")
    else:
        file_panel_title = _("Save Location")

    file_opts_panel = guiutils.get_named_frame(file_panel_title, widgets.file_panel.vbox, 4)         
    profile_panel = guiutils.get_named_frame(_("Render Profile"), widgets.profile_panel.vbox, 4)
    encoding_panel = guiutils.get_named_frame(_("Encoding Format"), widgets.encoding_panel.vbox, 4)

    if create_container_file_panel == True:
        widgets.video_clip_panel = RenderVideoClipPanel(profile_panel, encoding_panel)
        video_clip_panel = guiutils.get_named_frame(_("Video Clip"), widgets.video_clip_panel.vbox, 4)
    else:
        widgets.video_clip_panel = None
        
    render_panel = Gtk.VBox()
    render_panel.pack_start(file_opts_panel, False, False, 0)
    if create_container_file_panel == False:
        render_panel.pack_start(profile_panel, False, False, 0)
        render_panel.pack_start(encoding_panel, False, False, 0)
    else:
        render_panel.pack_start(video_clip_panel, False, False, 0)
    
    print("render_data", render_data)
    if render_data != None:
        widgets.file_panel.movie_name.set_text(render_data.file_name)
        widgets.file_panel.extension_label.set_text(render_data.file_extension)
        widgets.file_panel.out_folder.set_current_folder(render_data.render_dir + "/")
        widgets.encoding_panel.encoding_selector.widget.set_active(render_data.encoding_option_index) 
        widgets.encoding_panel.quality_selector.widget.set_active(render_data.quality_option_index)
        widgets.profile_panel.out_profile_combo.widget.set_active(render_data.profile_index)
        widgets.profile_panel.use_project_profile_check.set_active(render_data.use_default_profile)
        
        if create_container_file_panel == True:
            video_clip_combo_index = render_location_combo_index = 0
            if render_data.do_video_render == False:
                video_clip_combo_index = 1
            if render_data.save_internally == False:
                render_location_combo_index = 1
             
            widgets.video_clip_panel.video_clip_combo.set_active(video_clip_combo_index)
            widgets.file_panel.render_location_combo.set_active(render_location_combo_index)
            widgets.file_panel.frame_name.set_text(render_data.frame_name)
            
    return render_panel

def get_profile_info_small_box(profile):
    text = get_profile_info_text(profile)
    label = Gtk.Label(label=text)

    hbox = Gtk.HBox()
    hbox.pack_start(label, False, False, 0)
    
    return hbox

def get_profile_info_text(profile):
    str_list = []
    str_list.append(str(profile.width()))
    str_list.append(" x ")    
    str_list.append(str(profile.height()))
    str_list.append(", " + str(profile.display_aspect_num()))
    str_list.append(":")
    str_list.append(str(profile.display_aspect_den()))
    str_list.append(", ")
    if profile.progressive() == True:
        str_list.append(_("Progressive"))
    else:
        str_list.append(_("Interlaced"))
        
    str_list.append("\n")
    str_list.append(_("Fps: ") + str(profile.fps()))
    pix_asp = float(profile.sample_aspect_num()) / profile.sample_aspect_den()
    pa_str =  "%.2f" % pix_asp
    str_list.append(", " + _("Pixel Aspect: ") + pa_str)

    return ''.join(str_list)

def get_render_data_for_current_selections():
    render_data = ToolsRenderData()
    render_data.profile_index = widgets.profile_panel.out_profile_combo.widget.get_active()
    render_data.use_default_profile = widgets.profile_panel.use_project_profile_check.get_active()
    render_data.encoding_option_index = widgets.encoding_panel.encoding_selector.widget.get_active()
    render_data.quality_option_index = widgets.encoding_panel.quality_selector.widget.get_active()
    render_data.presets_index = 0 # presents rendering not available
    render_data.use_preset_encodings = False # presents rendering not available
    render_data.render_dir = "/" + widgets.file_panel.out_folder.get_uri().lstrip("file:/")
    render_data.file_name = widgets.file_panel.movie_name.get_text()
    render_data.file_extension = widgets.file_panel.extension_label.get_text()
    
    if widgets.video_clip_panel != None:
        render_data.do_video_render = (widgets.video_clip_panel.video_clip_combo.get_active() == 0)
        render_data.save_internally = (widgets.file_panel.render_location_combo.get_active() == 0)
        render_data.frame_name = widgets.file_panel.frame_name.get_text()

    return render_data

def get_args_vals_list_for_render_data(render_data):
    profile = mltprofiles.get_profile_for_index(render_data.profile_index)
    if render_data.use_preset_encodings == 1:
        # Preset encodings THIS HAS BEEN DEACTIVATED FOR NOW.
        # Preset encodings THIS HAS BEEN DEACTIVATED FOR NOW.
        # Preset encodings THIS HAS BEEN DEACTIVATED FOR NOW.
        encs = renderconsumer.non_user_encodings
        if disable_audio_encoding == True:
            encs = renderconsumer.get_video_non_user_encodigs()
        encoding_option = encs[render_data.presets_index]
        args_vals_list = encoding_option.get_args_vals_tuples_list(profile)
    
    
    else: # User encodings
        args_vals_list = renderconsumer.get_args_vals_tuples_list_for_encoding_and_quality( profile, 
                                                                                            render_data.encoding_option_index, 
                                                                                            render_data.quality_option_index)
    # sample rate not supported
    # args rendering not supported

    return args_vals_list

def get_encoding_desc(args_vals_list):
    print(args_vals_list)
    vcodec = ""
    vb = ""
    for arg_val in args_vals_list:
        k, v = arg_val
        if k == "vcodec":
            vcodec = v
        if k == "vb":
            vb = v

    if vb  == "":
        vb = "lossless"

    return vcodec + ", " + vb


# ----------------------------------------------------------------- helper functions
def _render_type_changed(w):
    if w.get_active() == 0: # User Defined
        widgets.render_type_panel.presets_selector.widget.set_sensitive(False)
        widgets.encoding_panel.encoding_selector.encoding_selection_changed()
    else: # Preset Encodings
        widgets.render_type_panel.presets_selector.widget.set_sensitive(True)
        _preset_selection_changed(widgets.render_type_panel.presets_selector.widget)

def _preset_selection_changed(w):
    encs = renderconsumer.non_user_encodings
    if disable_audio_encoding == True:
        encs = renderconsumer.get_video_non_user_encodigs()

    enc_index = w.get_active()
    ext = encs[enc_index].extension
    widgets.file_panel.extension_label.set_text("." + ext)
    
def _out_profile_changed(w):
    profile = mltprofiles.get_profile_for_index(w.get_active())
    _fill_info_box(profile)

def _display_default_profile():
    profile = mltprofiles.get_profile_for_index(default_profile_index)
    _fill_info_box(profile)
    
def _fill_info_box(profile):
    info_panel = get_profile_info_small_box(profile)
    widgets.info_panel = info_panel
    widgets.profile_panel.out_profile_info_box.display_info(info_panel)



# ----------------------------------------------------- PANELS
class RenderFilePanel():

    def __init__(self, create_container_file_panel):

        if create_container_file_panel == True:
            self.render_location_combo = Gtk.ComboBoxText() # filled later when current sequence known
            self.render_location_combo.append_text(_("Save Rendered Container Media Internally"))
            self.render_location_combo.append_text(_("Save Rendered Container Media Externally"))
            self.render_location_combo.set_active(0)
            self.render_location_combo.connect('changed', lambda w: self.render_location_combo_changed(w))
        else:
            self.render_location_combo = None
            
        self.out_folder = Gtk.FileChooserButton(_("Select Folder"))
        self.out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.out_folder.set_current_folder(os.path.expanduser("~") + "/")
        self.out_folder.set_local_only(True)
        self.out_folder_label = Gtk.Label(label=_("Folder:"))
        out_folder_row = guiutils.get_two_column_box(self.out_folder_label, self.out_folder, 60)
                              
        self.movie_name = Gtk.Entry()
        self.movie_name.set_text("movie")
        self.extension_label = Gtk.Label()
        if create_container_file_panel == False:
            self.name_label = Gtk.Label(label=_("Name:"))
        else:
            self.name_label = Gtk.Label(label=_("Clip Name:"))
            
        name_box = Gtk.HBox(False, 8)
        name_box.pack_start(self.movie_name, True, True, 0)
        name_box.pack_start(self.extension_label, False, False, 0)
          
        movie_name_row = guiutils.get_two_column_box(self.name_label, name_box, 60)

        self.frame_name_label = Gtk.Label(label=_("Frame Name:"))
        self.frame_name = Gtk.Entry()
        self.frame_name.set_text("frame")
    
        frame_name_row = guiutils.get_two_column_box(self.frame_name_label, self.frame_name, 60)
        
        self.vbox = Gtk.VBox(False, 2)
        if self.render_location_combo != None:
            self.vbox.pack_start(self.render_location_combo, False, False, 0)
        self.vbox.pack_start(out_folder_row, False, False, 0)
        self.vbox.pack_start(movie_name_row, False, False, 0)
        if create_container_file_panel == True:
            self.vbox.pack_start(frame_name_row, False, False, 0)
            
        self.out_folder.set_tooltip_text(_("Select folder to place rendered file in"))
        self.movie_name.set_tooltip_text(_("Give name for rendered file"))

    def enable_file_selections(self, enabled):
        self.movie_name.set_sensitive(enabled)
        self.extension_label.set_sensitive(enabled)
        self.out_folder.set_sensitive(enabled)
        self.out_folder_label.set_sensitive(enabled)
        self.name_label.set_sensitive(enabled)
        self.frame_name_label.set_sensitive(enabled)
        self.frame_name.set_sensitive(enabled)

    def render_location_combo_changed(self, combo):
        if combo.get_active() == 1:
            self.enable_file_selections(True)
        else:
            self.enable_file_selections(False)


class RenderVideoClipPanel:
    def __init__(self, profile_panel, encoding_panel):

        self.profile_panel = profile_panel
        self.encoding_panel = encoding_panel

        self.video_clip_combo = Gtk.ComboBoxText() # filled later when current sequence known
        self.video_clip_combo.append_text(_("Render Video Clip"))
        self.video_clip_combo.append_text(_("Frame Sequence Only"))
        self.video_clip_combo.set_active(0)
        self.video_clip_combo.connect('changed', lambda w: self.video_clip_combo_changed(w))

        encoding_vbox = Gtk.VBox(False, 2)
        encoding_vbox.pack_start(profile_panel, False, False, 0)
        encoding_vbox.pack_start(encoding_panel, False, False, 0)

        encoding_hbox = Gtk.HBox(False, 2)
        encoding_hbox.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        encoding_hbox.pack_start(encoding_vbox, True, True, 0)

        
        self.vbox = Gtk.VBox(False, 2)
        self.vbox.pack_start(self.video_clip_combo, False, False, 0)
        self.vbox.pack_start(guiutils.pad_label(12, 24), False, False, 0)
        self.vbox.pack_start(encoding_hbox, False, False, 0)

    def enable_video_encoding(self, enabled):
        self.profile_panel.set_sensitive(enabled)
        self.encoding_panel.set_sensitive(enabled)
        
    def video_clip_combo_changed(self, combo):
        if combo.get_active() == 0:
            self.enable_video_encoding(True)
        else:
            self.enable_video_encoding(False)


class RenderTypePanel():
    
    def __init__(self, render_type_changed_callback, preset_selection_changed_callback):
        self.type_label = Gtk.Label(label=_("Type:"))
        self.presets_label = Gtk.Label(label=_("Presets:")) 
        
        self.type_combo = Gtk.ComboBoxText() # filled later when current sequence known
        self.type_combo.append_text(_("User Defined"))
        self.type_combo.append_text(_("Preset File type"))
        self.type_combo.set_active(0)
        self.type_combo.connect('changed', lambda w: render_type_changed_callback(w))
    
        self.presets_selector = PresetEncodingsSelector(preset_selection_changed_callback)

        self.vbox = Gtk.VBox(False, 2)
        self.vbox.pack_start(guiutils.get_two_column_box(self.type_label,
                                                         self.type_combo, 80), 
                                                         False, False, 0)
        self.vbox.pack_start(guiutils.get_two_column_box(self.presets_label,
                                                         self.presets_selector.widget, 80), 
                                                         False, False, 0)


class RenderProfilePanel():

    def __init__(self, out_profile_changed_callback):
        self.use_project_label = Gtk.Label(label=_("Use Default Profile:"))

        self.out_profile_info_box = ProfileInfoBox() # filled later when current sequence known

        self.use_project_profile_check = Gtk.CheckButton()
        self.use_project_profile_check.set_active(True)
        self.use_project_profile_check.connect("toggled", self.use_project_check_toggled)

        self.out_profile_combo = ProfileSelector(out_profile_changed_callback)

        use_project_profile_row = Gtk.HBox()
        use_project_profile_row.pack_start(self.use_project_label,  False, False, 0)
        use_project_profile_row.pack_start(self.use_project_profile_check,  False, False, 0)
        use_project_profile_row.pack_start(Gtk.Label(), True, True, 0)
    
        self.vbox = Gtk.VBox(False, 2)
        self.vbox.pack_start(use_project_profile_row, False, False, 0)
        self.vbox.pack_start(self.out_profile_combo.widget, False, False, 0)
        self.vbox.pack_start(self.out_profile_info_box, False, False, 0)

    def set_sensitive(self, value):
        self.use_project_profile_check.set_sensitive(value)
        self.use_project_label.set_sensitive(value)
        self.out_profile_combo.widget.set_sensitive(value)
        
    def use_project_check_toggled(self, checkbutton):
        self.out_profile_combo.widget.set_sensitive(checkbutton.get_active() == False)
        if checkbutton.get_active() == True:
            self.out_profile_combo.widget.set_active(default_profile_index)
            #_display_default_profile()
            

class RenderEncodingPanel():
    
    def __init__(self, extension_label):
        self.quality_selector = RenderQualitySelector()
        self.quality_selector.widget.set_size_request(110, 34)
        self.quality_selector.update_quality_selection(0)
        self.audio_desc = Gtk.Label()
        self.encoding_selector = RenderEncodingSelector(self.quality_selector,
                                                        extension_label,
                                                        self.audio_desc)
        self.encoding_selector.encoding_selection_changed()

        quality_row  = Gtk.HBox()
        quality_row.pack_start(self.quality_selector.widget, False, False, 0)
        quality_row.pack_start(Gtk.Label(), True, False, 0)

        self.vbox = Gtk.VBox(False, 2)
        self.vbox.pack_start(self.encoding_selector.widget, False, False, 0)
        self.vbox.pack_start(quality_row, False, False, 0)

    def set_sensitive(self, value):
        self.quality_selector.widget.set_sensitive(value)
        self.audio_desc.set_sensitive(value)
        self.speaker_image.set_sensitive(value)
        self.encoding_selector.widget.set_sensitive(value)



class ProfileSelector():
    def __init__(self, out_profile_changed_callback=None):
        self.widget = Gtk.ComboBoxText() # filled later when current sequence known
        if out_profile_changed_callback != None:
            self.widget.connect('changed', lambda w:  out_profile_changed_callback(w))
        self.widget.set_sensitive(False)
        self.widget.set_tooltip_text(_("Select render profile"))

    def fill_options(self):
        self.widget.get_model().clear()
        #self.widget.append_text(current_sequence().profile.description())
        profiles = mltprofiles.get_profiles()
        for profile in profiles:
            self.widget.append_text(profile[0])
        self.widget.set_active(default_profile_index)


class RenderQualitySelector():
    """
    Component displays quality option relevant for encoding slection.
    """
    def __init__(self):
        self.widget = Gtk.ComboBoxText()
        self.widget.set_tooltip_text(_("Select Render quality"))

    def update_quality_selection(self, enc_index):
        encoding = renderconsumer.encoding_options[enc_index]
        
        self.widget.get_model().clear()
        for quality_option in encoding.quality_options:
            self.widget.append_text(quality_option.name)

        if encoding.quality_default_index != None:
            self.widget.set_active(encoding.quality_default_index)
        else:
            self.widget.set_active(0)


class PresetEncodingsSelector():
    
     def __init__(self, selection_changed_callback):
        self.widget = Gtk.ComboBoxText()
        encs = renderconsumer.non_user_encodings
        
        if disable_audio_encoding == True:
            encs = renderconsumer.get_video_non_user_encodigs()
        
        for encoding in encs:
            self.widget.append_text(encoding.name)
        
        self.widget.set_active(0)
        self.widget.set_sensitive(False)
        self.widget.connect("changed", 
                             lambda w,e: selection_changed_callback(w), 
                             None)


class ProfileInfoBox(Gtk.VBox):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.add(Gtk.Label()) # This is removed when we have data to fill this
        
    def display_info(self, info_panel):
        info_box_children = self.get_children()
        for child in info_box_children:
            self.remove(child)
    
        self.add(info_panel)
        self.show_all()


class RenderEncodingSelector():

    def __init__(self, quality_selector, extension_label, audio_desc_label):
        self.widget = Gtk.ComboBoxText()
        for encoding in renderconsumer.encoding_options:
            self.widget.append_text(encoding.name)
            
        self.widget.set_active(0)
        self.widget.connect("changed", 
                            lambda w,e: self.encoding_selection_changed(), 
                            None)
        self.widget.set_tooltip_text(_("Select Render encoding"))
    
        self.quality_selector = quality_selector
        self.extension_label = extension_label
        self.audio_desc_label = audio_desc_label
        
    def encoding_selection_changed(self):
        enc_index = self.widget.get_active()
        
        self.quality_selector.update_quality_selection(enc_index)
        
        encoding = renderconsumer.encoding_options[enc_index]
        self.extension_label.set_text("." + encoding.extension)

        if self.audio_desc_label != None:
            self.audio_desc_label.set_markup(encoding.get_audio_description())



