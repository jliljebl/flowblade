"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2013 Janne Liljeblad.

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
from gi.repository import Pango

import math
import os

import dialogutils
import editorpersistance # Aug-2019- SvdB - BB
import editorstate
import gui
import guiutils
from editorstate import current_sequence
import mltprofiles
import renderconsumer
import respaths
import utils

destroy_window_event_id = -1

FFMPEG_VIEW_SIZE = (20, 20) # Text edit area height for render opts. Width 200 seems to be ignored in current layout?


# ----------------------------------------------------------- dialogs
def render_progress_dialog(callback, parent_window, frame_rates_match=True):
    dialog = Gtk.Dialog(_("Render Progress"),
                         parent_window,
                         Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                         (_("Cancel"), Gtk.ResponseType.REJECT))

    dialog.status_label = Gtk.Label()
    dialog.remaining_time_label = Gtk.Label()
    dialog.passed_time_label = Gtk.Label()
    dialog.progress_bar = Gtk.ProgressBar()

    status_box = Gtk.HBox(False, 2)
    status_box.pack_start(dialog.status_label,False, False, 0)
    status_box.pack_start(Gtk.Label(), True, True, 0)
    
    remaining_box = Gtk.HBox(False, 2)
    remaining_box.pack_start(dialog.remaining_time_label,False, False, 0)
    remaining_box.pack_start(Gtk.Label(), True, True, 0)

    passed_box = Gtk.HBox(False, 2)
    passed_box.pack_start(dialog.passed_time_label,False, False, 0)
    passed_box.pack_start(Gtk.Label(), True, True, 0)

    if frame_rates_match == False:
        # Aug-2019 - SvdB - BB
        if editorpersistance.prefs.double_track_hights:
            warning_icon = Gtk.Image.new_from_stock(Gtk.STOCK_DIALOG_WARNING, Gtk.IconSize.DND)
        else:
            warning_icon = Gtk.Image.new_from_stock(Gtk.STOCK_DIALOG_WARNING, Gtk.IconSize.MENU)
        warning_text = Gtk.Label(label=_("Project and Render Profile FPS values are not same. Rendered file may have A/V sync issues."))
        warning_box = Gtk.HBox(False, 2)
        warning_box.pack_start(warning_icon,False, False, 0)
        warning_box.pack_start(warning_text,False, False, 0)
        warning_box.pack_start(Gtk.Label(), True, True, 0)
        
    progress_vbox = Gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(remaining_box, False, False, 0)
    progress_vbox.pack_start(passed_box, False, False, 0)
    if frame_rates_match == False:
        progress_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
        progress_vbox.pack_start(warning_box, False, False, 0)
    progress_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
    progress_vbox.pack_start(dialog.progress_bar, False, False, 0)
    
    alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.set_default_size(500, 125)
    alignment.show_all()
    dialog.connect('response', callback)
    dialog.show()
    return dialog

def no_good_rander_range_info():
    primary_txt = _("Render range not defined!")
    secondary_txt = _("Define render range using Mark In and Mark Out points\nor select range option 'Sequence length' to start rendering.")
    dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window)

def load_ffmpeg_opts_dialog(callback, opts_extension):
    dialog = Gtk.FileChooserDialog(_("Load Render Args File"), None, 
                                   Gtk.FileChooserAction.OPEN, 
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                    _("OK"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.OPEN)
    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name(opts_extension + " files")
    file_filter.add_pattern("*" + opts_extension)
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def save_ffmpeg_opts_dialog(callback, opts_extension):
    dialog = Gtk.FileChooserDialog(_("Save Render Args As"), None, 
                                   Gtk.FileChooserAction.SAVE, 
                                   (_("Cancel"), Gtk.ResponseType.CANCEL,
                                   _("Save"), Gtk.ResponseType.ACCEPT))
    dialog.set_action(Gtk.FileChooserAction.SAVE)
    dialog.set_current_name("untitled" + opts_extension)
    dialog.set_do_overwrite_confirmation(True)
    dialog.set_select_multiple(False)
    file_filter = Gtk.FileFilter()
    file_filter.set_name(opts_extension + " files")
    file_filter.add_pattern("*" + opts_extension)
    dialog.add_filter(file_filter)
    dialog.connect('response', callback)
    dialog.show()

def clip_render_progress_dialog(callback, title, text, progress_bar, parent_window, no_cancel=False):
    if no_cancel == False:
        dialog = Gtk.Dialog( title,
                             parent_window,
                             Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                             (_("Cancel"), Gtk.ResponseType.REJECT))
    else:
        dialog = Gtk.Dialog( title,
                             parent_window,
                             Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT)
                             
    dialog.text_label = Gtk.Label(label=text)
    dialog.text_label.set_use_markup(True)
    text_box = Gtk.HBox(False, 2)
    text_box.pack_start(dialog.text_label,False, False, 0)
    text_box.pack_start(Gtk.Label(), True, True, 0)

    status_box = Gtk.HBox(False, 2)
    status_box.pack_start(text_box, False, False, 0)
    status_box.pack_start(Gtk.Label(), True, True, 0)

    progress_vbox = Gtk.VBox(False, 2)
    progress_vbox.pack_start(status_box, False, False, 0)
    progress_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
    progress_vbox.pack_start(progress_bar, False, False, 0)

    alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialog.set_default_size(500, 125)
    alignment.show_all()
    if no_cancel == False:
        dialog.connect('response', callback)
    dialog.show()
    return dialog

def show_slowmo_dialog(media_file, default_range_render, _response_callback):
    folder, file_name = os.path.split(media_file.path)
    if media_file.is_proxy_file:
        folder, file_name = os.path.split(media_file.second_file_path)

    name, ext = os.path.splitext(file_name)
        
    dialog = Gtk.Dialog(_("Render Slow/Fast Motion Video File"), gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                        _("Render"), Gtk.ResponseType.ACCEPT))

    media_file_label = Gtk.Label(label=_("Source Media File: "))
    media_name = Gtk.Label(label="<b>" + media_file.name + "</b>")
    media_name.set_use_markup(True)
    SOURCE_PAD = 8
    SOURCE_HEIGHT = 20
    mf_row = guiutils.get_left_justified_box([media_file_label,  guiutils.pad_label(SOURCE_PAD, SOURCE_HEIGHT), media_name])
    
    mark_in = Gtk.Label(label=_("<b>not set</b>"))
    mark_out = Gtk.Label(label=_("<b>not set</b>"))
    if media_file.mark_in != -1:
        mark_in = Gtk.Label(label="<b>" + utils.get_tc_string(media_file.mark_in) + "</b>")
    if media_file.mark_out != -1:
        mark_out = Gtk.Label(label="<b>" + utils.get_tc_string(media_file.mark_out) + "</b>")
    mark_in.set_use_markup(True)
    mark_out.set_use_markup(True)
    
    fb_widgets = utils.EmptyClass()

    fb_widgets.file_name = Gtk.Entry()
    fb_widgets.file_name.set_text(name + "_MOTION")
    
    fb_widgets.extension_label = Gtk.Label()
    fb_widgets.extension_label.set_size_request(45, 20)

    name_row = Gtk.HBox(False, 4)
    name_row.pack_start(fb_widgets.file_name, True, True, 0)
    name_row.pack_start(fb_widgets.extension_label, False, False, 4)
    
    fb_widgets.out_folder = Gtk.FileChooserButton(_("Select Target Folder"))
    fb_widgets.out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    fb_widgets.out_folder.set_current_folder(folder)
    
    label = Gtk.Label(label=_("Speed %:"))

    adjustment = Gtk.Adjustment(value=float(100), lower=float(1), upper=float(2900), step_incr=float(1))
    fb_widgets.adjustment = adjustment

    spin = Gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)
    spin.set_digits(0)

    objects_list = Gtk.TreeStore(str, bool)
    objects_list.append(None, [_("Full Source Length"), True])
    if media_file.mark_in != -1 and media_file.mark_out != -1:
        range_available = True
    else:
        range_available = False
    objects_list.append(None, [_("Source Mark In to Mark Out"), range_available])
    
    fb_widgets.render_range = Gtk.ComboBox.new_with_model(objects_list)
    renderer_text = Gtk.CellRendererText()
    fb_widgets.render_range.pack_start(renderer_text, True)
    fb_widgets.render_range.add_attribute(renderer_text, "text", 0)
    fb_widgets.render_range.add_attribute(renderer_text, 'sensitive', 1)
    if default_range_render == False:
        fb_widgets.render_range.set_active(0)
    else:
        fb_widgets.render_range.set_active(1)
    fb_widgets.render_range.show()
    
    clip_length = _get_rendered_slomo_clip_length(media_file, fb_widgets.render_range, 100)
    clip_length_label = Gtk.Label(label=utils.get_tc_string(clip_length))
    
    slider_hbox = Gtk.HBox(False, 4)
    slider_hbox.pack_start(Gtk.Label(), True, True, 0)
    slider_hbox.pack_start(spin, False, False, 4)
    slider_hbox.pack_start(Gtk.Label(label=_("Rendered Length:")), False, False, 4)
    slider_hbox.pack_start(clip_length_label, False, False, 4)
    slider_hbox.pack_start(Gtk.Label(), True, True, 0)
    slider_hbox.set_size_request(450,35)

    hbox = Gtk.HBox(False, 2)
    hbox.pack_start(guiutils.pad_label(8, 8), False, False, 0)
    hbox.pack_start(slider_hbox, False, False, 0)

    profile_selector = ProfileSelector()
    profile_selector.fill_options()
    profile_selector.widget.set_sensitive(True)
    fb_widgets.out_profile_combo = profile_selector.widget

    quality_selector = RenderQualitySelector()
    fb_widgets.quality_cb = quality_selector.widget
    
    # Encoding
    encoding_selector = RenderEncodingSelector(quality_selector, fb_widgets.extension_label, None)
    encoding_selector.encoding_selection_changed()
    fb_widgets.encodings_cb = encoding_selector.widget

    # To update rendered length display
    adjustment.connect("value-changed", _slomo_speed_changed, media_file, fb_widgets.render_range, clip_length_label)
    fb_widgets.render_range.connect("changed", _slomo_range_changed,  media_file, adjustment,  clip_length_label)

    # Build gui
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(mf_row, False, False, 0)
    vbox.pack_start(guiutils.get_left_justified_box([Gtk.Label(label=_("Source Mark In: ")), guiutils.pad_label(SOURCE_PAD, SOURCE_HEIGHT), mark_in]), False, False, 0)
    vbox.pack_start(guiutils.get_left_justified_box([Gtk.Label(label=_("Source Mark Out: ")), guiutils.pad_label(SOURCE_PAD, SOURCE_HEIGHT), mark_out]), False, False, 0)
    vbox.pack_start(guiutils.pad_label(18, 12), False, False, 0)
    vbox.pack_start(label, False, False, 0)
    vbox.pack_start(hbox, False, False, 0)
    vbox.pack_start(guiutils.pad_label(24, 12), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Target File:")), name_row, 120), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Target Folder:")), fb_widgets.out_folder, 120), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Target Profile:")), fb_widgets.out_profile_combo, 200), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Target Encoding:")), fb_widgets.encodings_cb, 200), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Target Quality:")), fb_widgets.quality_cb, 200), False, False, 0)
    vbox.pack_start(guiutils.pad_label(18, 12), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Render Range:")), fb_widgets.render_range, 180), False, False, 0)
    
    alignment = guiutils.set_margins(vbox, 6, 24, 24, 24)
    
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    dialog.connect('response', _response_callback, fb_widgets, media_file)
    dialog.show_all()

def _slomo_speed_changed(adjustment, media_file, range_combo, length_label):
    clip_length = _get_rendered_slomo_clip_length(media_file, range_combo, adjustment.get_value())
    length_label.set_text(utils.get_tc_string(clip_length))

def _slomo_range_changed(range_combo, media_file, adjustment, length_label):
    clip_length = _get_rendered_slomo_clip_length(media_file, range_combo, adjustment.get_value())
    length_label.set_text(utils.get_tc_string(clip_length))

def _get_rendered_slomo_clip_length(media_file, range_combo, speed):
    if range_combo.get_active() == 1:
        orig_len = media_file.mark_out -  media_file.mark_in + 1 # +1 mark out incl
    else:
        orig_len = media_file.length

    return int((float(orig_len) * 100.0) / float(speed))
    
def show_reverse_dialog(media_file, default_range_render, _response_callback):
    folder, file_name = os.path.split(media_file.path)
    if media_file.is_proxy_file:
        folder, file_name = os.path.split(media_file.second_file_path)

    name, ext = os.path.splitext(file_name)
        
    dialog = Gtk.Dialog(_("Render Reverse Motion Video File"), gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                        _("Render"), Gtk.ResponseType.ACCEPT))

    media_file_label = Gtk.Label(label=_("Source Media File: "))
    media_name = Gtk.Label(label="<b>" + media_file.name + "</b>")
    media_name.set_use_markup(True)
    SOURCE_PAD = 8
    SOURCE_HEIGHT = 20
    mf_row = guiutils.get_left_justified_box([media_file_label,  guiutils.pad_label(SOURCE_PAD, SOURCE_HEIGHT), media_name])
    
    mark_in = Gtk.Label(label=_("<b>not set</b>"))
    mark_out = Gtk.Label(label=_("<b>not set</b>"))
    if media_file.mark_in != -1:
        mark_in = Gtk.Label(label="<b>" + utils.get_tc_string(media_file.mark_in) + "</b>")
    if media_file.mark_out != -1:
        mark_out = Gtk.Label(label="<b>" + utils.get_tc_string(media_file.mark_out) + "</b>")
    mark_in.set_use_markup(True)
    mark_out.set_use_markup(True)
    
    fb_widgets = utils.EmptyClass()

    fb_widgets.file_name = Gtk.Entry()
    fb_widgets.file_name.set_text(name + "_REVERSE")
    
    fb_widgets.extension_label = Gtk.Label()
    fb_widgets.extension_label.set_size_request(45, 20)

    name_row = Gtk.HBox(False, 4)
    name_row.pack_start(fb_widgets.file_name, True, True, 0)
    name_row.pack_start(fb_widgets.extension_label, False, False, 4)
    
    fb_widgets.out_folder = Gtk.FileChooserButton(_("Select Target Folder"))
    fb_widgets.out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
    fb_widgets.out_folder.set_current_folder(folder)
    
    label = Gtk.Label(label=_("Speed %:"))

    adjustment = Gtk.Adjustment(value=float(-100), lower=float(-600), upper=float(-1), step_incr=float(1))
    fb_widgets.hslider = Gtk.HScale()
    fb_widgets.hslider.set_adjustment(adjustment)
    fb_widgets.hslider.set_draw_value(False)

    spin = Gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)

    fb_widgets.hslider.set_digits(0)
    spin.set_digits(0)

    slider_hbox = Gtk.HBox(False, 4)
    slider_hbox.pack_start(fb_widgets.hslider, True, True, 0)
    slider_hbox.pack_start(spin, False, False, 4)
    slider_hbox.set_size_request(450,35)

    hbox = Gtk.HBox(False, 2)
    hbox.pack_start(guiutils.pad_label(8, 8), False, False, 0)
    hbox.pack_start(slider_hbox, False, False, 0)

    profile_selector = ProfileSelector()
    profile_selector.fill_options()
    profile_selector.widget.set_sensitive(True)
    fb_widgets.out_profile_combo = profile_selector.widget

    quality_selector = RenderQualitySelector()
    fb_widgets.quality_cb = quality_selector.widget
    
    # Encoding
    encoding_selector = RenderEncodingSelector(quality_selector, fb_widgets.extension_label, None)
    encoding_selector.encoding_selection_changed()
    fb_widgets.encodings_cb = encoding_selector.widget
    
    objects_list = Gtk.TreeStore(str, bool)
    objects_list.append(None, [_("Full Source Length"), True])
    if media_file.mark_in != -1 and media_file.mark_out != -1:
        range_available = True
    else:
        range_available = False
    objects_list.append(None, [_("Source Mark In to Mark Out"), range_available])
    
    fb_widgets.render_range = Gtk.ComboBox.new_with_model(objects_list)
    
    renderer_text = Gtk.CellRendererText()
    fb_widgets.render_range.pack_start(renderer_text, True)
    fb_widgets.render_range.add_attribute(renderer_text, "text", 0)
    fb_widgets.render_range.add_attribute(renderer_text, 'sensitive', 1)
    if default_range_render == False:
        fb_widgets.render_range.set_active(0)
    else:
        fb_widgets.render_range.set_active(1)
    fb_widgets.render_range.show()

    # To update rendered length display
    clip_length = _get_rendered_slomo_clip_length(media_file, fb_widgets.render_range, 100)
    clip_length_label = Gtk.Label(label=utils.get_tc_string(clip_length))
    fb_widgets.hslider.connect("value-changed", _reverse_speed_changed, media_file, fb_widgets.render_range, clip_length_label)
    fb_widgets.render_range.connect("changed", _reverse_range_changed,  media_file, fb_widgets.hslider,  clip_length_label)

    # Build gui
    vbox = Gtk.VBox(False, 2)
    vbox.pack_start(mf_row, False, False, 0)
    vbox.pack_start(guiutils.get_left_justified_box([Gtk.Label(label=_("Source Mark In: ")), guiutils.pad_label(SOURCE_PAD, SOURCE_HEIGHT), mark_in]), False, False, 0)
    vbox.pack_start(guiutils.get_left_justified_box([Gtk.Label(label=_("Source Mark Out: ")), guiutils.pad_label(SOURCE_PAD, SOURCE_HEIGHT), mark_out]), False, False, 0)
    vbox.pack_start(guiutils.pad_label(18, 12), False, False, 0)
    vbox.pack_start(label, False, False, 0)
    vbox.pack_start(hbox, False, False, 0)
    vbox.pack_start(guiutils.pad_label(18, 12), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Target File:")), name_row, 120), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Target Folder:")), fb_widgets.out_folder, 120), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Target Profile:")), fb_widgets.out_profile_combo, 200), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Target Encoding:")), fb_widgets.encodings_cb, 200), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Target Quality:")), fb_widgets.quality_cb, 200), False, False, 0)
    vbox.pack_start(guiutils.pad_label(18, 12), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Render Range:")), fb_widgets.render_range, 180), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(Gtk.Label(label=_("Rendered Clip Length:")), clip_length_label, 180), False, False, 0)
    
    alignment = guiutils.set_margins(vbox, 6, 24, 24, 24)
    
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.default_behaviour(dialog)
    dialog.connect('response', _response_callback, fb_widgets, media_file)
    dialog.show_all()

def _reverse_speed_changed(slider, media_file, range_combo, length_label):
    clip_length = _get_rendered_reverse_clip_length(media_file, range_combo, slider.get_adjustment().get_value())
    length_label.set_text(utils.get_tc_string(clip_length))

def _reverse_range_changed(range_combo, media_file, slider, length_label):
    clip_length = _get_rendered_reverse_clip_length(media_file, range_combo, slider.get_adjustment().get_value())
    length_label.set_text(utils.get_tc_string(clip_length))

def _get_rendered_reverse_clip_length(media_file, range_combo, speed):
    if range_combo.get_active() == 1:
        orig_len = media_file.mark_out -  media_file.mark_in + 1 # +1 mark out incl
    else:
        orig_len = media_file.length

    return int((float(orig_len) * 100.0) / float(-speed))

# ----------------------------------------------------------- widgets
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


class RenderAudioRateSelector():
    def __init__(self):
        self.widget = Gtk.ComboBoxText()
        self.widget.set_tooltip_text(_("Select audio sample frequency"))
        self.sample_rates = [8000, 12000, 16000, 22500, 32000, 44100, 48000]
        for rate in self.sample_rates:
            val = rate / 1000.0
            if val == math.floor(val):
                val = int(val)
            self.widget.append_text(str(val) +" kHz")
        self.widget.set_active(6)
        
    def get_selected_rate(self):
        return self.sample_rates[self.widget.get_active()]
        

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


def get_range_selection_combo():
    range_cb = Gtk.ComboBoxText()
    range_cb.append_text(_("Full Length"))
    range_cb.append_text(_("Marked Range"))
    range_cb.set_active(0) 
    return range_cb

# ------------------------------------------------------------ panels
def get_render_panel_left(render_widgets):
    small_height = editorstate.screen_size_small_height()
    
    file_opts_panel = guiutils.get_named_frame(_("File"), render_widgets.file_panel.vbox, 4)         
    profile_panel = guiutils.get_named_frame(_("Render Profile"), render_widgets.profile_panel.vbox, 4)

    if small_height == False:
        encoding_panel = guiutils.get_named_frame(_("Encoding Format"), render_widgets.encoding_panel.vbox, 4)
    
    render_type_panel = guiutils.get_named_frame(_("Render Type"), render_widgets.render_type_panel.vbox, 4)
    
    render_panel = Gtk.VBox()
    render_panel.pack_start(file_opts_panel, False, False, 0)
    render_panel.pack_start(render_type_panel, False, False, 0)
    render_panel.pack_start(profile_panel, False, False, 0)
    if small_height == False:
        render_panel.pack_start(encoding_panel, False, False, 0)
        render_panel.pack_start(Gtk.Label(), True, True, 0)
    elif editorstate.SCREEN_HEIGHT == 900: # 900px height screens need most small height fixes but not this
        encoding_panel = guiutils.get_named_frame(_("Encoding Format"), render_widgets.encoding_panel.vbox, 4)
        render_panel.pack_start(encoding_panel, False, False, 0)
        render_panel.pack_start(Gtk.Label(), True, True, 0)
    
    return render_panel

def get_render_panel_right(render_widgets, render_clicked_cb, to_queue_clicked_cb):
    small_height = (editorstate.SCREEN_HEIGHT < 898)

    if small_height:
        encoding_panel = guiutils.get_named_frame(_("Encoding Format"), render_widgets.encoding_panel.vbox, 4)
           
    opts_panel = guiutils.get_named_frame(_("Render Args"), render_widgets.args_panel.vbox, 4)
    
    bin_row = Gtk.HBox()
    bin_row.pack_start(guiutils.get_pad_label(10, 8),  False, False, 0)
    bin_row.pack_start(Gtk.Label(label=_("Open File in Bin:")),  False, False, 0)
    bin_row.pack_start(guiutils.get_pad_label(10, 2),  False, False, 0)
    bin_row.pack_start(render_widgets.args_panel.open_in_bin,  False, False, 0)
    bin_row.pack_start(Gtk.Label(), True, True, 0)

    range_row = Gtk.HBox()
    range_row.pack_start(guiutils.get_pad_label(10, 8),  False, False, 0)
    if not editorstate.screen_size_small_width():
        range_row.pack_start(Gtk.Label(label=_("Render Range:")),  False, False, 0)
        range_row.pack_start(guiutils.get_pad_label(10, 2),  False, False, 0)
    range_row.pack_start(render_widgets.range_cb,  True, True, 0)

    buttons_panel = Gtk.HBox()
    buttons_panel.pack_start(guiutils.get_pad_label(10, 8), False, False, 0)
    buttons_panel.pack_start(render_widgets.reset_button, False, False, 0)
    if not  editorstate.screen_size_small_width():
        buttons_panel.pack_start(Gtk.Label(), True, True, 0)
        buttons_panel.pack_start(render_widgets.queue_button, False, False, 0)
    buttons_panel.pack_start(Gtk.Label(), True, True, 0)
    buttons_panel.pack_start(render_widgets.render_button, False, False, 0)

    render_widgets.queue_button.connect("clicked", 
                                         to_queue_clicked_cb, 
                                         None)

    render_widgets.render_button.connect("clicked", 
                                         render_clicked_cb, 
                                         None)

    render_panel = Gtk.VBox()
    if small_height:
        render_panel.pack_start(encoding_panel, False, False, 0)
        render_panel.pack_start(opts_panel, True, True, 0)
        #render_panel.pack_start(Gtk.Label(), True, True, 0)
    else:
        render_panel.pack_start(opts_panel, True, True, 0)
    if small_height == False:
        render_panel.pack_start(guiutils.get_pad_label(10, 22), False, False, 0)
        render_panel.pack_start(bin_row, False, False, 0)
    else:
        render_panel.pack_start(Gtk.Label(), True, True, 0)
    
    render_panel.pack_start(range_row, False, False, 0)
    if small_height == False:
        render_panel.pack_start(guiutils.get_pad_label(10, 12), False, False, 0)
    else:
        render_panel.pack_start(guiutils.get_pad_label(10, 4), False, False, 0)
    render_panel.pack_start(buttons_panel, False, False, 0)

    return render_panel


    
class RenderFilePanel():

    def __init__(self):

        self.out_folder = Gtk.FileChooserButton(_("Select Folder"))
        self.out_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.out_folder.set_current_folder(os.path.expanduser("~") + "/")
        gui.render_out_folder = self.out_folder
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
        if editorstate.screen_size_small_height() == False:
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
        
        self.sample_rate_selector = RenderAudioRateSelector()

        # Aug-2019 - SvdB - BB
        self.speaker_image = guiutils.get_image("audio_desc_icon")

        quality_row  = Gtk.HBox()
        quality_row.pack_start(self.quality_selector.widget, False, False, 0)
        quality_row.pack_start(Gtk.Label(), True, False, 0)
        quality_row.pack_start(self.speaker_image, False, False, 0)
        quality_row.pack_start(self.sample_rate_selector.widget, False, False, 0)
        quality_row.pack_start(self.audio_desc, False, False, 0)

        self.vbox = Gtk.VBox(False, 2)
        self.vbox.pack_start(self.encoding_selector.widget, False, False, 0)
        self.vbox.pack_start(quality_row, False, False, 0)

    def set_sensitive(self, value):
        self.quality_selector.widget.set_sensitive(value)
        self.audio_desc.set_sensitive(value)
        self.speaker_image.set_sensitive(value)
        self.encoding_selector.widget.set_sensitive(value)


class RenderArgsPanel():

    def __init__(self, save_args_callback, 
                 load_args_callback, display_selection_callback):
        self.display_selection_callback = display_selection_callback
        
        self.use_project_label = Gtk.Label(label=_("Use Project Profile:"))
        self.use_args_label = Gtk.Label(label=_("Render using args:"))
        self.text_buffer = None # only used for small screen heights with dialog for setting args, but this value is tested to determine where to get args from.
        
        self.use_args_check = Gtk.CheckButton()
        self.use_args_check.connect("toggled", self.use_args_toggled)

        self.opts_save_button = Gtk.Button()
        # Aug-2019 - SvdB - BB
        if editorpersistance.prefs.double_track_hights:
            icon = Gtk.Image.new_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.LARGE_TOOLBAR)
        else:
            icon = Gtk.Image.new_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.MENU)
        self.opts_save_button.set_image(icon)
        self.opts_save_button.connect("clicked", lambda w: save_args_callback())
        self.opts_save_button.set_sensitive(False)
    
        self.opts_load_button = Gtk.Button()
        # Aug-2019 - SvdB - BB
        if editorpersistance.prefs.double_track_hights:
            icon = Gtk.Image.new_from_stock(Gtk.STOCK_OPEN, Gtk.IconSize.LARGE_TOOLBAR)
        else:
            icon = Gtk.Image.new_from_stock(Gtk.STOCK_OPEN, Gtk.IconSize.MENU)
        self.opts_load_button.set_image(icon)
        self.opts_load_button.connect("clicked", lambda w: load_args_callback())
                
        self.load_selection_button = Gtk.Button(_("Load Selection"))
        self.load_selection_button.set_sensitive(False)
        self.load_selection_button.connect("clicked", lambda w: self.display_selection_callback())
        self.opts_load_button.set_sensitive(False)

        self.ext_label = Gtk.Label(label=_("Ext.:"))
        self.ext_label.set_sensitive(False)

        self.ext_entry = Gtk.Entry()
        self.ext_entry.set_width_chars(5)    
        self.ext_entry.set_sensitive(False)

        self.opts_view = Gtk.TextView()
        self.opts_view.set_sensitive(False)
        self.opts_view.set_pixels_above_lines(2)
        self.opts_view.set_left_margin(2)

        self.open_in_bin = Gtk.CheckButton()

        use_opts_row = Gtk.HBox()
        use_opts_row.pack_start(self.use_args_label,  False, False, 0)
        use_opts_row.pack_start(self.use_args_check,  False, False, 0)
        use_opts_row.pack_start(Gtk.Label(), True, True, 0)
        use_opts_row.pack_start(self.opts_load_button,  False, False, 0)
        use_opts_row.pack_start(self.opts_save_button,  False, False, 0)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(self.opts_view)
        sw.set_size_request(*FFMPEG_VIEW_SIZE)

        scroll_frame = Gtk.Frame()
        scroll_frame.add(sw)

        opts_buttons_row = Gtk.HBox(False)
        opts_buttons_row.pack_start(self.load_selection_button, False, False, 0)
        opts_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        opts_buttons_row.pack_start(self.ext_label, False, False, 0)
        opts_buttons_row.pack_start(self.ext_entry, False, False, 0)

        self.use_args_check.set_tooltip_text(_("Render using key=value rendering options"))
        self.load_selection_button.set_tooltip_text(_("Load render options from currently selected encoding"))
        self.opts_view.set_tooltip_text(_("Edit render options"))
        self.opts_save_button.set_tooltip_text(_("Save Render Args into a text file"))
        self.opts_load_button.set_tooltip_text(_("Load Render Args from a text file"))
    
        self.vbox = Gtk.VBox(False, 2)
        self.vbox.pack_start(use_opts_row , False, False, 0)
        self.vbox.pack_start(scroll_frame, True, True, 0)
        self.vbox.pack_start(opts_buttons_row, False, False, 0)

    def set_sensitive(self, value):
        self.use_args_check.set_sensitive(value)
        self.use_args_label.set_sensitive(value)
    
    def display_encoding_args(self, profile, enc_index, qual_index):
        encoding_option = renderconsumer.encoding_options[enc_index]
        quality_option = encoding_option.quality_options[qual_index]
        args_vals_list = encoding_option.get_args_vals_tuples_list(profile, quality_option)
        text = ""
        for arg_val in args_vals_list:
            k, v = arg_val
            line = str(k) + "=" + str(v) + "\n"
            text = text + line

        text_buffer = Gtk.TextBuffer()
        text_buffer.set_text(text)
        self.opts_view.set_buffer(text_buffer)

        self.ext_entry.set_text(encoding_option.extension)

    def use_args_toggled(self, checkbutton):
        active = checkbutton.get_active()
        self.opts_view.set_sensitive(active)
        self.load_selection_button.set_sensitive(active)
        self.opts_save_button.set_sensitive(active)
        self.opts_load_button.set_sensitive(active)

        self.ext_label.set_sensitive(active)
        self.ext_entry.set_sensitive(active)
        
        if active == True:
            self.display_selection_callback()
        else:
            self.opts_view.set_buffer(Gtk.TextBuffer())
            self.ext_entry.set_text("")


class RenderArgsPanelSmall():

    def __init__(self, save_args_callback, 
                 load_args_callback, display_selection_callback):
        self.display_selection_callback = display_selection_callback
        
        self.args_edit_window = None
        self.text_buffer = None # only used here for small screen heights with dialog for setting agrs, but this value is always tested to determine where to get agrs if set
        self.ext = ""
                
        self.use_project_label = Gtk.Label(label=_("Use Project Profile:"))
        self.use_args_label = Gtk.Label(label=_("Render using args:"))
    
        self.use_args_check = Gtk.CheckButton()
        self.use_args_check.connect("toggled", self.use_args_toggled)

        self.opts_save_button = Gtk.Button()
        icon = Gtk.Image.new_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.MENU)
        self.opts_save_button.set_image(icon)
        self.opts_save_button.connect("clicked", lambda w: save_args_callback())
        self.opts_save_button.set_sensitive(False)
    
        self.opts_load_button = Gtk.Button()
        icon = Gtk.Image.new_from_stock(Gtk.STOCK_OPEN, Gtk.IconSize.MENU)
        self.opts_load_button.set_image(icon)
        self.opts_load_button.connect("clicked", lambda w: load_args_callback())

        self.open_in_bin = Gtk.CheckButton()

        self.open_args_editor_button = Gtk.Button(_("Edit Args:"))
        self.open_args_editor_button.connect("clicked", lambda w: self.open_edit_window())
        self.open_args_editor_button.set_sensitive(False)

        self.args_info = Gtk.Label()
        self.args_info.set_sensitive(False)
        self.args_info.set_ellipsize(Pango.EllipsizeMode.END)
        
        use_opts_row = Gtk.HBox()
        use_opts_row.pack_start(self.use_args_label,  False, False, 0)
        use_opts_row.pack_start(self.use_args_check,  False, False, 0)
        use_opts_row.pack_start(Gtk.Label(), True, True, 0)
        use_opts_row.pack_start(self.opts_load_button,  False, False, 0)
        use_opts_row.pack_start(self.opts_save_button,  False, False, 0)

        args_edit_row = Gtk.HBox(False)
        args_edit_row.pack_start(self.open_args_editor_button, False, False, 0)
        args_edit_row.pack_start(guiutils.get_pad_label(4, 2), False, False, 0)
        args_edit_row.pack_start(self.args_info, True, True, 0)

        self.use_args_check.set_tooltip_text(_("Render using key=value rendering options"))

        self.opts_save_button.set_tooltip_text(_("Save Render Args into a text file"))
        self.opts_load_button.set_tooltip_text(_("Load Render Args from a text file"))
    
        self.vbox = Gtk.VBox(False, 2)
        self.vbox.pack_start(use_opts_row , False, False, 0)
        self.vbox.pack_start(args_edit_row, False, False, 0)

    def set_sensitive(self, value):
        self.use_args_check.set_sensitive(value)
        self.use_args_label.set_sensitive(value)
    
    def display_encoding_args(self, profile, enc_index, qual_index):
        encoding_option = renderconsumer.encoding_options[enc_index]
        quality_option = encoding_option.quality_options[qual_index]
        args_vals_list = encoding_option.get_args_vals_tuples_list(profile, quality_option)
        text = ""
        info_text = ""
        for arg_val in args_vals_list:
            k, v = arg_val
            line = str(k) + "=" + str(v) 
            text = text + line + "\n"
            info_text = info_text + line + ", "
        self.text_buffer = Gtk.TextBuffer()
        self.text_buffer.set_text(text)

        self.args_info.set_text(info_text)
        self.ext = encoding_option.extension
            
        if self.args_edit_window != None:
            self.args_edit_window.opts_view.set_buffer(self.text_buffer)        
            self.args_edit_window.ext_entry.set_text(encoding_option.extension)

    def open_edit_window(self):
        self.args_edit_window = RenderArgsEditWindow(self)

    def use_args_toggled(self, checkbutton):
        active = checkbutton.get_active()
        self.opts_save_button.set_sensitive(active)
        self.opts_load_button.set_sensitive(active)
        self.open_args_editor_button.set_sensitive(active)
        self.args_info.set_sensitive(active)
        
        if active == True:
            self.display_selection_callback()
        else:
            self.args_info.set_text("")

    def cancel_args_edit(self):
        self.args_edit_window.set_visible(False)
        self.args_edit_window.destroy()

    def do_args_edit(self):
        self.text_buffer = self.args_edit_window.opts_view.get_buffer()

        buf_text = self.text_buffer.get_text(self.text_buffer.get_start_iter(), 
                                             self.text_buffer.get_end_iter(), 
                                             include_hidden_chars=True)
        info_text = buf_text.replace("\n", ", ")
        self.args_info.set_text(info_text)
        
        self.args_edit_window.set_visible(False)
        self.args_edit_window.destroy()


class RenderArgsEditWindow(Gtk.Window):
    def __init__(self, args_panel):
        GObject.GObject.__init__(self)
        #self.connect("delete-event", lambda w, e:close_audio_monitor())
        
        self.args_panel = args_panel

        self.opts_view = Gtk.TextView()
        self.opts_view.set_sensitive(True)
        self.opts_view.set_pixels_above_lines(2)
        self.opts_view.set_left_margin(2)
        self.opts_view.set_buffer(self.args_panel.text_buffer)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(self.opts_view)
        sw.set_size_request(*FFMPEG_VIEW_SIZE)

        scroll_frame = Gtk.Frame()
        scroll_frame.add(sw)
        scroll_frame.set_size_request(400, 300)

        self.load_selection_button = Gtk.Button(_("Load Selection"))
        self.load_selection_button.connect("clicked", lambda w: self.args_panel.display_selection_callback())

        self.ext_label = Gtk.Label(label=_("Ext.:"))
        self.ext_label.set_sensitive(False)

        self.ext_entry = Gtk.Entry()
        self.ext_entry.set_width_chars(5)
        self.ext_entry.set_text(self.args_panel.ext)   
        
        self.load_selection_button.set_tooltip_text(_("Load render options from currently selected encoding"))
        self.opts_view.set_tooltip_text(_("Edit render options"))
        
        opts_buttons_row = Gtk.HBox(False)
        opts_buttons_row.pack_start(self.load_selection_button, False, False, 0)
        opts_buttons_row.pack_start(guiutils.get_pad_label(4, 2), False, False, 0)
        opts_buttons_row.pack_start(self.ext_label, False, False, 0)
        opts_buttons_row.pack_start(guiutils.get_pad_label(4, 2), False, False, 0)
        opts_buttons_row.pack_start(self.ext_entry, False, False, 0)

        cancel_b = guiutils.get_sized_button(_("Cancel"), 150, 32)
        cancel_b.connect("clicked", lambda w: self.args_panel.cancel_args_edit())
        set_args_b = guiutils.get_sized_button(_("Set Args"), 150, 32)
        set_args_b.connect("clicked", lambda w:self.args_panel.do_args_edit())
        
        editor_buttons_row = Gtk.HBox()
        editor_buttons_row.pack_start(Gtk.Label(), True, True, 0)
        editor_buttons_row.pack_start(cancel_b, False, False, 0)
        editor_buttons_row.pack_start(set_args_b, False, False, 0)
        
        pane = Gtk.VBox(False, 1)
        pane.pack_start(scroll_frame, True, True, 0)
        pane.pack_start(opts_buttons_row, False, True, 0)
        pane.pack_start(guiutils.get_pad_label(4, 12), False, True, 0)
        pane.pack_start(editor_buttons_row, False, True, 0)

        align = guiutils.set_margins(pane, 12, 12, 12, 12)
        # Set pane and show window
        self.add(align)
        self.set_title(_("Render Args"))
        self.show_all()
        self.set_resizable(False)
        self.set_keep_above(True) # Perhaps configurable later
    
    
