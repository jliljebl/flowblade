

from gi.repository import Gtk
from gi.repository import GObject

import os

import guiutils
import renderconsumer
import utils

widgets =  None

# ----------------------------------------------------- GUI objects
class RenderFilePanel():

    def __init__(self):

        self.out_folder = Gtk.FileChooserButton(_("Select Folder"))
        self.out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.out_folder.set_current_folder(os.path.expanduser("~") + "/")
        #gui.render_out_folder = self.out_folder
        out_folder_row = guiutils.get_two_column_box(Gtk.Label(label=_("Folder:")), self.out_folder, 60)
                              
        self.movie_name = Gtk.Entry()
        self.movie_name.set_text("movie")
        self.extension_label = Gtk.Label()
            
        name_box = Gtk.HBox(False, 8)
        name_box.pack_start(self.movie_name, True, True, 0)
        name_box.pack_start(self.extension_label, False, False, 0)
          
        movie_name_row = guiutils.get_two_column_box(Gtk.Label(label=_("Name:")), name_box, 60)

        self.vbox = Gtk.VBox(False, 2)
        self.vbox.pack_start(out_folder_row, False, False, 0)
        self.vbox.pack_start(movie_name_row, False, False, 0)

        self.out_folder.set_tooltip_text(_("Select folder to place rendered file in"))
        self.movie_name.set_tooltip_text(_("Give name for rendered file"))
        

class RenderTypePanel():
    
    def __init__(self, render_type_changed_callback, preset_selection_changed_callback):
        self.type_label = Gtk.Label(label=_("Type:"))
        self.presets_label = Gtk.Label(label=_("Presets:")) 
        
        self.type_combo = Gtk.ComboBoxText() # filled later when current sequence known
        self.type_combo.append_text(_("User Defined"))
        self.type_combo.append_text(_("Preset File type"))
        self.type_combo.set_active(0)
        self.type_combo.connect('changed', lambda w: render_type_changed_callback())
    
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
        self.use_project_label = Gtk.Label(label=_("Use Project Profile:"))
        self.use_args_label = Gtk.Label(label=_("Render using args:"))

        self.use_project_profile_check = Gtk.CheckButton()
        self.use_project_profile_check.set_active(True)
        self.use_project_profile_check.connect("toggled", self.use_project_check_toggled)

        self.out_profile_combo = ProfileSelector(out_profile_changed_callback)
        
        self.out_profile_info_box = ProfileInfoBox() # filled later when current sequence known
        
        use_project_profile_row = Gtk.HBox()
        use_project_profile_row.pack_start(self.use_project_label,  False, False, 0)
        use_project_profile_row.pack_start(self.use_project_profile_check,  False, False, 0)
        use_project_profile_row.pack_start(Gtk.Label(), True, True, 0)

        self.use_project_profile_check.set_tooltip_text(_("Select used project profile for rendering"))
        self.out_profile_info_box.set_tooltip_text(_("Render profile info"))
    
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
            self.out_profile_combo.widget.set_active(0)


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
        
        #self.sample_rate_selector = RenderAudioRateSelector()

        #self.speaker_image = Gtk.Image.new_from_file(respaths.IMAGE_PATH + "audio_desc_icon.png")

        quality_row  = Gtk.HBox()
        quality_row.pack_start(self.quality_selector.widget, False, False, 0)
        quality_row.pack_start(Gtk.Label(), True, False, 0)
        #quality_row.pack_start(self.speaker_image, False, False, 0)
        #quality_row.pack_start(self.sample_rate_selector.widget, False, False, 0)
        #quality_row.pack_start(self.audio_desc, False, False, 0)

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
            self.widget.connect('changed', lambda w:  out_profile_changed_callback())
        self.widget.set_sensitive(False)
        self.widget.set_tooltip_text(_("Select render profile"))
        
    def fill_options(self):
        self.widget.get_model().clear()
        self.widget.append_text(current_sequence().profile.description())
        profiles = mltprofiles.get_profiles()
        for profile in profiles:
            self.widget.append_text(profile[0])
        self.widget.set_active(0)

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
        for encoding in renderconsumer.non_user_encodings:
            self.widget.append_text(encoding.name)
        
        self.widget.set_active(0)
        self.widget.set_sensitive(False)
        self.widget.connect("changed", 
                             lambda w,e: selection_changed_callback(), 
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


# ------------------------------------------------------------ interface
def create_widgets():
    """
    Widgets for editing render properties and viewing render progress.
    """
    global widgets
    widgets = utils.EmptyClass()
     
    widgets.file_panel = RenderFilePanel()
    widgets.render_type_panel = RenderTypePanel(_render_type_changed, _preset_selection_changed)
    widgets.profile_panel = RenderProfilePanel(_out_profile_changed)
    widgets.encoding_panel = RenderEncodingPanel(widgets.file_panel.extension_label)
    
def get_gmic_render_panel():   
    file_opts_panel = guiutils.get_named_frame(_("File"), widgets.file_panel.vbox, 4)         
    profile_panel = guiutils.get_named_frame(_("Render Profile"), widgets.profile_panel.vbox, 4)
    encoding_panel = guiutils.get_named_frame(_("Encoding Format"), widgets.encoding_panel.vbox, 4)
    render_type_panel = guiutils.get_named_frame(_("Render Type"), widgets.render_type_panel.vbox, 4)
    
    render_panel = Gtk.VBox()
    render_panel.pack_start(file_opts_panel, False, False, 0)
    render_panel.pack_start(render_type_panel, False, False, 0)
    render_panel.pack_start(profile_panel, False, False, 0)
    render_panel.pack_start(encoding_panel, False, False, 0)
    #render_panel.pack_start(Gtk.Label(), True, True, 0)
        
    return render_panel


def _render_type_changed(w):
    pass
    
def _preset_selection_changed(w):
    pass
    
def _preset_selection_changed(w):
    pass

def _out_profile_changed(w):
    pass



