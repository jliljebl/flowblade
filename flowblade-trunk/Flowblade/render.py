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
Module loads render options, provides them in displayable form 
and builds a mlt.Consumer for rendering on request.

Rendering is done in app.player object of class mltplayer.Player
"""
import gtk
import mlt
import md5
import os
import time
import threading
import xml.dom.minidom

import dialogs
import dialogutils
from editorstate import current_sequence
from editorstate import PROJECT
from editorstate import PLAYER
import editorpersistance
import gui
import guicomponents
import guiutils
import mltenv
import mltprofiles
import projectdata
import projectinfogui
import renderconsumer
import rendergui
import respaths
import sequence
import utils

# User defined Ffmpeg opts file extension
FFMPEG_OPTS_SAVE_FILE_EXTENSION = ".rargs"

open_media_file_callback = None # monkeypathced in by useraction to avoid circular imports

render_start_time = 0
widgets = utils.EmptyClass()

aborted = False

# Motion clip rendering
motion_renderer = None
motion_progress_update = None

# Transition clip rendering 
transition_render_done_callback = None

# ---------------------------------- rendering action and dialogs
class RenderLauncher(threading.Thread):
    
    def __init__(self, render_consumer, start_frame, end_frame):
        threading.Thread.__init__(self)
        self.render_consumer = render_consumer
        
        # Hack. We seem to be getting range rendering starting 1-2 frame too late.
        # Changing in out frame logic in monitor is not a good idea,
        # especially as this may be mlt issue, so we just try this.
        start_frame += -1
        if start_frame < 0:
            start_frame = 0
        
        self.start_frame = start_frame
        self.end_frame = end_frame

    def run(self):
        callbacks = utils.EmptyClass()
        callbacks.set_render_progress_gui = set_render_progress_gui
        callbacks.save_render_start_time = save_render_start_time
        callbacks.exit_render_gui = exit_render_gui
        callbacks.maybe_open_rendered_file_in_bin = maybe_open_rendered_file_in_bin
        PLAYER().set_render_callbacks(callbacks)
        
        PLAYER().start_rendering(self.render_consumer, self.start_frame, self.end_frame)


def render_timeline():
    if len(widgets.movie_name.get_text()) == 0:
        primary_txt = _("Render file name entry is empty")
        secondary_txt = _("You have to provide a name for the file to be rendered.")
        dialogutils.warning_message(primary_txt, secondary_txt, gui.editor_window.window)
        return   

    if os.path.exists(get_file_path()):
        primary_txt = _("File: ") + get_file_path() + _(" already exists!")
        secondary_txt = _("Do you want to overwrite existing file?")
        dialogutils.warning_confirmation(_render_overwrite_confirm_callback, primary_txt, secondary_txt, gui.editor_window.window)
    else:
        _do_rendering()

def _render_overwrite_confirm_callback(dialog, response_id):
    dialog.destroy()
    
    if response_id == gtk.RESPONSE_ACCEPT:
        _do_rendering()

def _do_rendering():
    global aborted
    aborted = False
    render_consumer = get_render_consumer()
    if render_consumer == None:
        return

    # Set render start and end points
    if widgets.range_cb.get_active() == 0:
        start_frame = 0
        end_frame = -1 # renders till finish
    else:
        start_frame = current_sequence().tractor.mark_in
        end_frame = current_sequence().tractor.mark_out
    
    # Only render a range if it is defined.
    if start_frame == -1 or end_frame == -1:
        if widgets.range_cb.get_active() == 1:
            dialogs.no_good_rander_range_info()
            return

    file_path = get_file_path()
    project_event = projectdata.ProjectEvent(projectdata.EVENT_RENDERED, file_path)
    PROJECT().events.append(project_event)
    projectinfogui.update_project_info()
    
    set_render_gui()
    widgets.progress_window = dialogs.render_progress_dialog(
                                        _render_cancel_callback,
                                        gui.editor_window.window)
    render_launch = RenderLauncher(render_consumer, start_frame, end_frame)
    render_launch.start()

def _render_cancel_callback(dialog, response_id):
    global aborted
    aborted = True
    dialog.destroy()
    PLAYER().consumer.stop()
    PLAYER().producer.set_speed(0)
    
# -------------------------------------------------- render consumer
def get_render_consumer():
    file_path = get_file_path()
    if file_path == None:
        return None

    profile = get_current_profile()

    if widgets.type_combo.get_active() == 1: # Preset encodings
        encoding_option = renderconsumer.non_user_encodings[widgets.preset_encodings_cb.get_active()]
        consumer = renderconsumer.get_render_consumer_for_encoding(file_path,
                                                                   profile,
                                                                   encoding_option)
        return consumer

    if widgets.use_args_check.get_active() == False:
        # Using options comboboxes
        encoding_option_index = widgets.encodings_cb.get_active()
        quality_option_index = widgets.quality_cb.get_active()
        consumer = renderconsumer.get_render_consumer_for_encoding_and_quality( file_path,
                                                                                profile,
                                                                                encoding_option_index,
                                                                                quality_option_index)
    else:
        buf = widgets.opts_view.get_buffer()
        consumer, error = renderconsumer.get_render_consumer_for_text_buffer(file_path,
                                                                             profile,
                                                                             buf)
        if error != None:
            dialogutils.warning_message("FFMPeg Args Error", error, gui.editor_window.window)
            return None
        
    return consumer

def get_args_vals_list_for_current_selections():
    profile = get_current_profile()
    encoding_option_index = widgets.encodings_cb.get_active()
    quality_option_index = widgets.quality_cb.get_active()
        
    if widgets.type_combo.get_active() == 1: # Preset encodings
        args_vals_list = renderconsumer.get_args_vals_tuples_list_for_encoding_and_quality( profile, 
                                                                                            encoding_option_index, 
                                                                                            -1)
    elif widgets.use_args_check.get_active() == False: # User encodings
        args_vals_list = renderconsumer.get_args_vals_tuples_list_for_encoding_and_quality( profile, 
                                                                                            encoding_option_index, 
                                                                                            quality_option_index)
    else: # Manual args encodings
        buf = widgets.opts_view.get_buffer()
        args_vals_list, error = renderconsumer.get_ffmpeg_opts_args_vals_tuples_list(buf)
    
        if error != None:
            dialogutils.warning_message("FFMPeg Args Error", error, gui.editor_window.window)
            return None
    
    return args_vals_list

def get_file_path():
    folder = widgets.out_folder.get_filenames()[0]        
    filename = widgets.movie_name.get_text()
    
    return folder + "/" + filename + widgets.extension_label.get_text()

# --------------------------------------------------- gui
def create_widgets(normal_height):
    """
    Widgets for editing render properties and viewing render progress.
    """
    widgets.file_panel = rendergui.RenderFilePanel()
    widgets.out_folder = widgets.file_panel.out_folder
    widgets.movie_name = widgets.file_panel.movie_name
    widgets.extension_label = widgets.file_panel.extension_label
    
    widgets.render_type_panel = rendergui.RenderTypePanel(_render_type_changed, _preset_selection_changed)
    widgets.preset_encodings_cb = widgets.render_type_panel.presets_selector.widget
    widgets.type_combo = widgets.render_type_panel.type_combo
    
    widgets.profile_panel = rendergui.RenderProfilePanel(_out_profile_changed)
    widgets.use_project_label = widgets.profile_panel.use_project_label
    widgets.use_args_label = widgets.profile_panel.use_args_label
    widgets.use_project_profile_check = widgets.profile_panel.use_project_profile_check
    widgets.out_profile_combo = widgets.profile_panel.out_profile_combo
    widgets.out_profile_info_box = widgets.profile_panel.out_profile_info_box
    
    widgets.encoding_panel = rendergui.RenderEncodingPanel(widgets.file_panel.extension_label)
    widgets.quality_cb = widgets.encoding_panel.quality_selector.widget
    widgets.audio_desc = widgets.encoding_panel.audio_desc
    widgets.encodings_cb = widgets.encoding_panel.encoding_selector.widget

    widgets.args_panel = rendergui.RenderArgsPanel(normal_height,
                                                   _save_opts_pressed, _load_opts_pressed,
                                                   _display_selection_in_opts_view)
    widgets.use_args_check = widgets.args_panel.use_args_check
    widgets.opts_save_button = widgets.args_panel.opts_save_button
    widgets.opts_load_button = widgets.args_panel.opts_load_button
    widgets.load_selection_button = widgets.args_panel.load_selection_button
    widgets.opts_view = widgets.args_panel.opts_view
    widgets.open_in_bin = widgets.args_panel.open_in_bin

    # Range
    widgets.range_cb = gtk.combo_box_new_text()
    widgets.range_cb.append_text(_("Full Length"))
    widgets.range_cb.append_text(_("Marked Range"))
    widgets.range_cb.set_active(0) 

    # Render, Reset, Render Queue buttons
    widgets.render_button = guiutils.get_render_button()

    widgets.reset_button = gtk.Button(_("Reset"))
    widgets.reset_button.connect("clicked", lambda w: set_default_values_for_widgets())
    widgets.queue_button = gtk.Button(_("To Queue"))
    
    # Render progress window
    widgets.progress_window = None #created in dialogs.py, destroyed here
    
    # Render progress window widgets
    widgets.status_label = gtk.Label()
    widgets.remaining_time_label = gtk.Label()
    widgets.passed_time_label = gtk.Label()
    widgets.progress_bar = gtk.ProgressBar()
    widgets.estimation_label = gtk.Label()

    # Tooltips
    widgets.range_cb.set_tooltip_text(_("Select render range"))
    widgets.reset_button.set_tooltip_text(_("Reset all render options to defaults"))
    widgets.render_button.set_tooltip_text(_("Begin Rendering"))

def set_default_values_for_widgets():
    if len(renderconsumer.encoding_options) == 0:# this won't work if no encoding options available
        return                   # but we don't want crash, so that we can inform user
    widgets.encodings_cb.set_active(0)
    widgets.movie_name.set_text("movie")
    widgets.out_folder.set_current_folder(os.path.expanduser("~") + "/")
    widgets.use_args_check.set_active(False)
    widgets.use_project_profile_check.set_active(True)

def enable_user_rendering(value):
    widgets.encoding_panel.set_sensitive(value)
    widgets.profile_panel.set_sensitive(value)
    widgets.info_panel.set_sensitive(value)
    widgets.args_panel.set_sensitive(value)

def set_render_gui():
    widgets.status_label.set_text(_("<b>Output File: </b>") + get_file_path())
    widgets.status_label.set_use_markup(True)
    widgets.remaining_time_label.set_text(_("<b>Estimated time left: </b>"))
    widgets.remaining_time_label.set_use_markup(True)
    widgets.passed_time_label.set_text(_("<b>Render time: </b>"))
    widgets.passed_time_label.set_use_markup(True)
    widgets.estimation_label.set_text("0%")

def save_render_start_time():
    global render_start_time
    render_start_time = time.time()
    
def set_render_progress_gui(fraction):
    widgets.progress_bar.set_fraction(fraction)
    pros = int(fraction * 100)
    widgets.estimation_label.set_text(str(pros) + "%")

    if pros > 0.99: # Only start giving estimations after rendering has gone on for a while.
        passed_time = time.time() - render_start_time
        full_time_est = (1.0 / fraction) * passed_time
        left_est = full_time_est - passed_time

        left_str = utils.get_time_str_for_sec_float(left_est)
        passed_str = utils.get_time_str_for_sec_float(passed_time)

        widgets.remaining_time_label.set_text(_("<b>Estimated time left: </b>") + left_str)
        widgets.remaining_time_label.set_use_markup(True)
        widgets.passed_time_label.set_text(_("<b>Render time: </b>") + passed_str)
        widgets.passed_time_label.set_use_markup(True)

def exit_render_gui():
    # 'aborted' is set False at render start. If it is True now, rendering has been aborted and 
    # widgets.progress_window has already been destroyed (in useraction._render_cancel_callback).
    if aborted == True:
        return

    set_render_progress_gui(1.0)
    passed_time = time.time() - render_start_time
    passed_str = utils.get_time_str_for_sec_float(passed_time)

    widgets.remaining_time_label.set_text(_("<b>Estimated time left: </b>"))
    widgets.remaining_time_label.set_use_markup(True)
    widgets.passed_time_label.set_text(_("<b>Render time: </b>") + passed_str)
    widgets.passed_time_label.set_use_markup(True)
    widgets.estimation_label.set_text(_("Render Complete!"))
    
    time.sleep(2.0)
    widgets.progress_window.destroy()

def maybe_open_rendered_file_in_bin():
    if widgets.open_in_bin.get_active() == False:
        return
        
    file_path = get_file_path()
    open_media_file_callback(file_path)

def get_current_profile():
    profile_index = widgets.out_profile_combo.widget.get_active()
    if profile_index == 0:
        # project_profile is first selection in combo box
        profile = PROJECT().profile
    else:
        profile = mltprofiles.get_profile_for_index(profile_index - 1)
    return profile

def fill_out_profile_widgets():
    """
    Called some time after widget creation when current_sequence is known and these can be filled.
    """
    widgets.out_profile_combo.fill_options()
    _fill_info_box(current_sequence().profile)

def reload_profiles():
    renderconsumer.load_render_profiles()
    fill_out_profile_widgets()

def _render_type_changed():
    if widgets.type_combo.get_active() == 0:
        enable_user_rendering(True)
        set_default_values_for_widgets()
        widgets.preset_encodings_cb.set_sensitive(False)
        _preset_selection_changed()
    else:
        enable_user_rendering(False)
        widgets.preset_encodings_cb.set_sensitive(True)
        _preset_selection_changed()
        widgets.opts_save_button.set_sensitive(False)
        widgets.opts_load_button.set_sensitive(False)
        widgets.load_selection_button.set_sensitive(False)
        widgets.opts_view.set_sensitive(False)
        widgets.opts_view.get_buffer().set_text("")

def _out_profile_changed():
    selected_index = widgets.out_profile_combo.widget.get_active()
    if selected_index == 0:
        _fill_info_box(current_sequence().profile)
    else:
        profile = mltprofiles.get_profile_for_index(selected_index - 1)
        _fill_info_box(profile)

def _fill_info_box(profile):
    info_panel = guicomponents.get_profile_info_small_box(profile)
    widgets.info_panel = info_panel
    widgets.out_profile_info_box.display_info(info_panel)

def _preset_selection_changed():
    enc_index = widgets.preset_encodings_cb.get_active()
    ext = renderconsumer.non_user_encodings[enc_index].extension
    widgets.extension_label.set_text("." + ext)
   
def _display_selection_in_opts_view():
    profile = get_current_profile()
    widgets.args_panel.display_profile_args(profile, widgets.encodings_cb.get_active(), widgets.quality_cb.get_active())
    
def _save_opts_pressed():
    dialogs.save_ffmpep_optsdialog(_save_opts_dialog_callback, FFMPEG_OPTS_SAVE_FILE_EXTENSION)

def _save_opts_dialog_callback(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        file_path = dialog.get_filenames()[0]
        opts_file = open(file_path, "w")
        buf = widgets.opts_view.get_buffer()
        opts_text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), include_hidden_chars=True)
        opts_file.write(opts_text)
        opts_file.close()
        dialog.destroy()
    else:
        dialog.destroy()

def _load_opts_pressed():
    dialogs.load_ffmpep_optsdialog(_load_opts_dialog_callback, FFMPEG_OPTS_SAVE_FILE_EXTENSION)

def _load_opts_dialog_callback(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        filename = dialog.get_filenames()[0]
        args_file = open(filename)
        args_text = args_file.read()
        widgets.opts_view.get_buffer().set_text(args_text)
        dialog.destroy()
    else:
        dialog.destroy()

# ------------------------------------------------------------- framebuffer clip rendering
# Rendering a slow/fast motion version of media file.
# We're using 300 lines worth of copy/paste from above, because lazy
def render_frame_buffer_clip(media_file):
    
    folder, file_name = os.path.split(media_file.path)
    name, ext = os.path.splitext(file_name)
        
    dialog = gtk.Dialog(_("Render Slow/Fast Motion Video File"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                        _("Render").encode('utf-8'), gtk.RESPONSE_ACCEPT))

    media_file_label = gtk.Label(_("Source Media File: "))
    media_name = gtk.Label("<b>" + media_file.name + "</b>")
    media_name.set_use_markup(True)
    SOURCE_PAD = 8
    SOURCE_HEIGHT = 20
    mf_row = guiutils.get_left_justified_box([media_file_label,  guiutils.pad_label(SOURCE_PAD, SOURCE_HEIGHT), media_name])
    
    mark_in = gtk.Label(_("<b>not set</b>"))
    mark_out = gtk.Label(_("<b>not set</b>"))
    if media_file.mark_in != -1:
        mark_in = gtk.Label("<b>" + utils.get_tc_string(media_file.mark_in) + "</b>")
    if media_file.mark_out != -1:
        mark_out = gtk.Label("<b>" + utils.get_tc_string(media_file.mark_out) + "</b>")
    mark_in.set_use_markup(True)
    mark_out.set_use_markup(True)
    
    fb_widgets = utils.EmptyClass()

    fb_widgets.file_name = gtk.Entry()
    fb_widgets.file_name.set_text(name + "_MOTION")
    
    fb_widgets.extension_label = gtk.Label()
    fb_widgets.extension_label.set_size_request(45, 20)

    name_row = gtk.HBox(False, 4)
    name_row.pack_start(fb_widgets.file_name, True, True, 0)
    name_row.pack_start(fb_widgets.extension_label, False, False, 4)
    
    fb_widgets.out_folder = gtk.FileChooserButton(_("Select Target Folder"))
    fb_widgets.out_folder.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    fb_widgets.out_folder.set_current_folder(folder)
    
    label = gtk.Label(_("Speed %:"))

    adjustment = gtk.Adjustment(float(100), float(1), float(600), float(1))
    fb_widgets.hslider = gtk.HScale()
    fb_widgets.hslider.set_adjustment(adjustment)
    fb_widgets.hslider.set_draw_value(False)
    
    spin = gtk.SpinButton()
    spin.set_adjustment(adjustment)

    fb_widgets.hslider.set_digits(0)
    spin.set_digits(0)

    slider_hbox = gtk.HBox(False, 4)
    slider_hbox.pack_start(fb_widgets.hslider, True, True, 0)
    slider_hbox.pack_start(spin, False, False, 4)
    slider_hbox.set_size_request(350,35)

    hbox = gtk.HBox(False, 2)
    hbox.pack_start(guiutils.pad_label(8, 8), False, False, 0)
    hbox.pack_start(label, False, False, 0)
    hbox.pack_start(slider_hbox, False, False, 0)

    profile_selector = rendergui.ProfileSelector()
    profile_selector.fill_options()
    profile_selector.widget.set_sensitive(True)
    fb_widgets.out_profile_combo = profile_selector.widget

    quality_selector = rendergui.RenderQualitySelector()
    fb_widgets.quality_cb = quality_selector.widget
    
    # Encoding
    encoding_selector = rendergui.RenderEncodingSelector(quality_selector, fb_widgets.extension_label, None)
    encoding_selector.encoding_selection_changed()
    fb_widgets.encodings_cb = encoding_selector.widget
    
    objects_list = gtk.TreeStore(str, bool)
    objects_list.append(None, [_("Full Source Length"), True])
    if media_file.mark_in != -1 and media_file.mark_out != -1:
        range_available = True
    else:
        range_available = False
    objects_list.append(None, [_("Source Mark In to Mark Out"), range_available])
    
    fb_widgets.render_range = gtk.ComboBox(objects_list)
    renderer_text = gtk.CellRendererText()
    fb_widgets.render_range.pack_start(renderer_text, True)
    fb_widgets.render_range.add_attribute(renderer_text, "text", 0)
    fb_widgets.render_range.add_attribute(renderer_text, 'sensitive', 1)
    fb_widgets.render_range.set_active(0)
    fb_widgets.render_range.show()

    vbox = gtk.VBox(False, 2)
    vbox.pack_start(mf_row, False, False, 0)
    vbox.pack_start(guiutils.get_left_justified_box([gtk.Label(_("Source Mark In: ")), guiutils.pad_label(SOURCE_PAD, SOURCE_HEIGHT), mark_in]), False, False, 0)
    vbox.pack_start(guiutils.get_left_justified_box([gtk.Label(_("Source_Mark Out: ")), guiutils.pad_label(SOURCE_PAD, SOURCE_HEIGHT), mark_out]), False, False, 0)
    vbox.pack_start(guiutils.pad_label(18, 12), False, False, 0)
    vbox.pack_start(hbox, False, False, 0)
    vbox.pack_start(guiutils.pad_label(18, 12), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(gtk.Label(_("Target File:")), name_row, 120), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(gtk.Label(_("Target Folder:")), fb_widgets.out_folder, 120), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(gtk.Label(_("Target Profile:")), fb_widgets.out_profile_combo, 200), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(gtk.Label(_("Target Encoding:")), fb_widgets.encodings_cb, 200), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(gtk.Label(_("Target Quality:")), fb_widgets.quality_cb, 200), False, False, 0)
    vbox.pack_start(guiutils.pad_label(18, 12), False, False, 0)
    vbox.pack_start(guiutils.get_two_column_box(gtk.Label(_("Render Range:")), fb_widgets.render_range, 180), False, False, 0)
    
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(6, 24, 24, 24)
    alignment.add(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogs._default_behaviour(dialog)
    dialog.connect('response', _render_frame_buffer_clip_callback, fb_widgets, media_file)
    dialog.show_all()

def _render_frame_buffer_clip_callback(dialog, response_id, fb_widgets, media_file):
    if response_id == gtk.RESPONSE_ACCEPT:
        # speed, filename folder
        speed = float(int(fb_widgets.hslider.get_value())) / 100.0
        file_name = fb_widgets.file_name.get_text()
        filenames = fb_widgets.out_folder.get_filenames()
        folder = filenames[0]
        write_file = folder + "/"+ file_name + fb_widgets.extension_label.get_text()

         # Profile
        profile_index = fb_widgets.out_profile_combo.get_active()
        if profile_index == 0:
            # project_profile is first selection in combo box
            profile = PROJECT().profile
        else:
            profile = mltprofiles.get_profile_for_index(profile_index - 1)

        # Render consumer properties
        encoding_option_index = fb_widgets.encodings_cb.get_active()
        quality_option_index = fb_widgets.quality_cb.get_active()

        # Range
        range_selection = fb_widgets.render_range.get_active()
        
        dialog.destroy()

        # Create motion producer
        fr_path = "framebuffer:" + media_file.path + "?" + str(speed)
        motion_producer = mlt.Producer(profile, None, str(fr_path))
    
        # Create sequence and add motion producer into it
        seq = sequence.Sequence(profile)
        seq.create_default_tracks()
        track = seq.tracks[seq.first_video_index]
        track.append(motion_producer, 0, motion_producer.get_length() - 1)

        consumer = renderconsumer.get_render_consumer_for_encoding_and_quality(write_file, profile, encoding_option_index, quality_option_index)
        
        # start and end frames
        start_frame = 0
        end_frame = seq.get_length()
        if range_selection == 1:
            start_frame = media_file.mark_in
            end_frame = media_file.mark_out
            
        # Launch render
        global motion_renderer, motion_progress_update
        motion_renderer = renderconsumer.FileRenderPlayer(write_file, seq.tractor, consumer, start_frame, end_frame)
        motion_renderer.start()
        
        title = _("Rendering Motion Clip")
        
        progress_bar = gtk.ProgressBar()
        dialog = dialogs.clip_render_progress_dialog(_FB_render_stop, title, write_file, progress_bar, gui.editor_window.window)
        
        motion_progress_update = renderconsumer.ProgressWindowThread(dialog, progress_bar, motion_renderer, _FB_render_stop)
        motion_progress_update.start()
        
    else:
        dialog.destroy()

def _FB_render_stop(dialog, response_id):
    dialog.destroy()

    global motion_renderer, motion_progress_update
    motion_renderer.running = False
    motion_progress_update.running = False
    open_media_file_callback(motion_renderer.file_name)
    motion_renderer.running = None # wut? ...below too
    motion_progress_update.running = None


# ----------------------------------------------------------------------- single track transition render 
def render_single_track_transition_clip(transition_producer, encoding_option_index, quality_option_index, file_ext, transition_render_complete_cb, window_text):
    # Set render complete callback to availble render stop callback using global variable
    global transition_render_done_callback
    transition_render_done_callback = transition_render_complete_cb

    # Profile
    profile = PROJECT().profile

    # Get path for created file
    folder = editorpersistance.prefs.render_folder
    file_name = md5.new(str(os.urandom(32))).hexdigest()
    write_file = folder + "/"+ file_name + file_ext

    # Render consumer
    consumer = renderconsumer.get_render_consumer_for_encoding_and_quality(write_file, profile, encoding_option_index, quality_option_index)
    
    # start and end frames
    start_frame = 0
    end_frame = transition_producer.get_length()
        
    # Launch render
    global motion_renderer, motion_progress_update
    motion_renderer = renderconsumer.FileRenderPlayer(write_file, transition_producer, consumer, start_frame, end_frame)
    motion_renderer.start()
    
    title = _("Rendering Transition Clip")
    
    progress_bar = gtk.ProgressBar()
    dialog = dialogs.clip_render_progress_dialog(_transition_render_stop, title, window_text, progress_bar, gui.editor_window.window)
    
    motion_progress_update = renderconsumer.ProgressWindowThread(dialog, progress_bar, motion_renderer, _transition_render_stop)
    motion_progress_update.start()

def _transition_render_stop(dialog, response_id):
    dialog.destroy()

    global motion_renderer, motion_progress_update
    motion_renderer.running = False
    motion_progress_update.running = False
    motion_renderer.running = None
    motion_progress_update.running = None
    
    transition_render_done_callback(motion_renderer.file_name)
