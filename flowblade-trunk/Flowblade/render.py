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

import pygtk
pygtk.require('2.0');
import gtk

import mlt
import md5
import os
import time
import threading

import dialogutils
from editorstate import current_sequence
from editorstate import PROJECT
from editorstate import PLAYER
import editorpersistance
import gui
import guicomponents
import guiutils
import mltprofiles
import mltrefhold
import projectdata
import projectinfogui
import renderconsumer
import rendergui
import sequence
import utils

# User defined render agrs file extension
FFMPEG_OPTS_SAVE_FILE_EXTENSION = ".rargs"

open_media_file_callback = None # monkeypatched in by app.py to avoid circular imports

render_start_time = 0
widgets = utils.EmptyClass()
progress_window = None

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
    if len(widgets.file_panel.movie_name.get_text()) == 0:
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
    print "timeline render..."
    
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
            rendergui.no_good_rander_range_info()
            return

    file_path = get_file_path()
    project_event = projectdata.ProjectEvent(projectdata.EVENT_RENDERED, file_path)
    PROJECT().events.append(project_event)
    projectinfogui.update_project_info()

    # See if project and render fps match
    cnum = render_consumer.profile().frame_rate_num()
    cden = render_consumer.profile().frame_rate_den()
    pnum = PROJECT().profile.frame_rate_num()
    pden = PROJECT().profile.frame_rate_den()
    
    if (cnum == pnum) and (cden == pden):
        frames_rates_match = True
    else:
        frames_rates_match = False

    global progress_window
    progress_window = rendergui.render_progress_dialog(_render_cancel_callback,
                                                       gui.editor_window.window,
                                                       frames_rates_match)
                                                       
    set_render_gui()

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

    if widgets.render_type_panel.type_combo.get_active() == 1: # Preset encodings
        encoding_option = renderconsumer.non_user_encodings[widgets.render_type_panel.presets_selector.widget.get_active()]
        if encoding_option.type != "img_seq":
            consumer = renderconsumer.get_render_consumer_for_encoding(file_path,
                                                                       profile,
                                                                       encoding_option)
        else: # Image Sequence rendering consumers need to be created a bit differently
            consumer = renderconsumer.get_img_seq_render_consumer(file_path,
                                                                  profile,
                                                                  encoding_option)
        return consumer

    if widgets.args_panel.use_args_check.get_active() == False:
        # Using options comboboxes
        encoding_option_index = widgets.encoding_panel.encoding_selector.widget.get_active()
        quality_option_index = widgets.encoding_panel.quality_selector.widget.get_active()
        consumer = renderconsumer.get_render_consumer_for_encoding_and_quality( file_path,
                                                                                profile,
                                                                                encoding_option_index,
                                                                                quality_option_index)
    else:
        buf = widgets.args_panel.opts_view.get_buffer()
        consumer, error = renderconsumer.get_render_consumer_for_text_buffer(file_path,
                                                                             profile,
                                                                             buf)
        if error != None:
            dialogutils.warning_message("FFMPeg Args Error", error, gui.editor_window.window)
            return None
        
    return consumer

def get_args_vals_list_for_current_selections():
    profile = get_current_profile()
    encoding_option_index = widgets.encoding_panel.encoding_selector.widget.get_active()
    quality_option_index = widgets.encoding_panel.quality_selector.widget.get_active()
        
    if widgets.render_type_panel.type_combo.get_active() == 1: # Preset encodings
        args_vals_list = renderconsumer.get_args_vals_tuples_list_for_encoding_and_quality( profile, 
                                                                                            encoding_option_index, 
                                                                                            -1)
    elif widgets.args_panel.use_args_check.get_active() == False: # User encodings
        args_vals_list = renderconsumer.get_args_vals_tuples_list_for_encoding_and_quality( profile, 
                                                                                            encoding_option_index, 
                                                                                            quality_option_index)
    else: # Manual args encodings
        buf = widgets.args_panel.opts_view.get_buffer()
        args_vals_list, error = renderconsumer.get_ffmpeg_opts_args_vals_tuples_list(buf)
    
        if error != None:
            dialogutils.warning_message("FFMPeg Args Error", error, gui.editor_window.window)
            return None
    
    return args_vals_list

def get_file_path():
    folder = widgets.file_panel.out_folder.get_filenames()[0]        
    filename = widgets.file_panel.movie_name.get_text()

    if  widgets.args_panel.use_args_check.get_active() == False:
        extension = widgets.file_panel.extension_label.get_text()
    else:
        extension = "." +  widgets.args_panel.ext_entry.get_text()

    return folder + "/" + filename + extension


# --------------------------------------------------- gui
def create_widgets(normal_height):
    """
    Widgets for editing render properties and viewing render progress.
    """
    widgets.file_panel = rendergui.RenderFilePanel()
    widgets.render_type_panel = rendergui.RenderTypePanel(_render_type_changed, _preset_selection_changed)
    widgets.profile_panel = rendergui.RenderProfilePanel(_out_profile_changed)
    widgets.encoding_panel = rendergui.RenderEncodingPanel(widgets.file_panel.extension_label)
    widgets.args_panel = rendergui.RenderArgsPanel(normal_height,
                                                   _save_opts_pressed, _load_opts_pressed,
                                                   _display_selection_in_opts_view)

    # Range, Render, Reset, Render Queue
    widgets.render_button = guiutils.get_render_button()
    widgets.range_cb = rendergui.get_range_selection_combo()
    widgets.reset_button = gtk.Button(_("Reset"))
    widgets.reset_button.connect("clicked", lambda w: set_default_values_for_widgets())
    widgets.queue_button = gtk.Button(_("To Queue"))
    widgets.queue_button.set_tooltip_text(_("Save Project in Render Queue"))
    
    # Tooltips
    widgets.range_cb.set_tooltip_text(_("Select render range"))
    widgets.reset_button.set_tooltip_text(_("Reset all render options to defaults"))
    widgets.render_button.set_tooltip_text(_("Begin Rendering"))

def set_default_values_for_widgets(movie_name_too=False):
    if len(renderconsumer.encoding_options) == 0:# this won't work if no encoding options available
        return                   # but we don't want crash, so that we can inform user
    widgets.encoding_panel.encoding_selector.widget.set_active(0)
    if movie_name_too == True:
        widgets.file_panel.movie_name.set_text("movie")
    widgets.file_panel.out_folder.set_current_folder(os.path.expanduser("~") + "/")
    widgets.args_panel.use_args_check.set_active(False)
    widgets.profile_panel.use_project_profile_check.set_active(True)

def enable_user_rendering(value):
    widgets.encoding_panel.set_sensitive(value)
    widgets.profile_panel.set_sensitive(value)
    widgets.info_panel.set_sensitive(value)
    widgets.args_panel.set_sensitive(value)

def set_render_gui():
    progress_window.status_label.set_text(_("<b>Output File: </b>") + get_file_path())
    progress_window.status_label.set_use_markup(True)
    progress_window.remaining_time_label.set_text(_("<b>Estimated time left: </b>"))
    progress_window.remaining_time_label.set_use_markup(True)
    progress_window.passed_time_label.set_text(_("<b>Render time: </b>"))
    progress_window.passed_time_label.set_use_markup(True)
    progress_window.progress_bar.set_text("0%")

def save_render_start_time():
    global render_start_time
    render_start_time = time.time()
    
def set_render_progress_gui(fraction):
    progress_window.progress_bar.set_fraction(fraction)
    pros = int(fraction * 100)
    progress_window.progress_bar.set_text(str(pros) + "%")

    try:
        passed_time = time.time() - render_start_time
        full_time_est = (1.0 / fraction) * passed_time
        passed_str = utils.get_time_str_for_sec_float(passed_time)
        progress_window.passed_time_label.set_text(_("<b>Render Time: </b>") + passed_str)
        progress_window.passed_time_label.set_use_markup(True)

        if pros > 0.99: # Only start giving estimations after rendering has gone on for a while.
            left_est = full_time_est - passed_time
            left_str = utils.get_time_str_for_sec_float(left_est)
            progress_window.remaining_time_label.set_text(_("<b>Estimated Time Left: </b>") + left_str)
            progress_window.remaining_time_label.set_use_markup(True)

    except: # A fraction of 0 usually gets sent here at beginning of rendering
        pass
        
def exit_render_gui():
    if aborted == True:
        print "render aborted"
        return

    global progress_window

    set_render_progress_gui(1.0)
    passed_time = time.time() - render_start_time
    passed_str = utils.get_time_str_for_sec_float(passed_time)
    print "render done, time: " + passed_str
    
    progress_window.remaining_time_label.set_text(_("<b>Estimated Time Left: </b>"))
    progress_window.remaining_time_label.set_use_markup(True)
    progress_window.passed_time_label.set_text(_("<b>Render Time: </b>") + passed_str)
    progress_window.passed_time_label.set_use_markup(True)
    progress_window.progress_bar.set_text(_("Render Complete!"))
    
    dialogutils.delay_destroy_window(progress_window, 2.0)
    progress_window = None

def maybe_open_rendered_file_in_bin():
    if widgets.args_panel.open_in_bin.get_active() == False:
        return
        
    file_path = get_file_path()
    open_media_file_callback(file_path)

def get_current_profile():
    profile_index = widgets.profile_panel.out_profile_combo.widget.get_active()
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
    widgets.profile_panel.out_profile_combo.fill_options()
    _fill_info_box(current_sequence().profile)

def reload_profiles():
    renderconsumer.load_render_profiles()
    fill_out_profile_widgets()

def _render_type_changed():
    if widgets.render_type_panel.type_combo.get_active() == 0: # User Defined
        enable_user_rendering(True)
        set_default_values_for_widgets()
        widgets.render_type_panel.presets_selector.widget.set_sensitive(False)
        _preset_selection_changed()
        widgets.encoding_panel.encoding_selector.encoding_selection_changed()
    else: # Preset Encodings
        enable_user_rendering(False)
        widgets.render_type_panel.presets_selector.widget.set_sensitive(True)
        _preset_selection_changed()
        widgets.args_panel.opts_save_button.set_sensitive(False)
        widgets.args_panel.opts_load_button.set_sensitive(False)
        widgets.args_panel.load_selection_button.set_sensitive(False)
        widgets.args_panel.opts_view.set_sensitive(False)
        widgets.args_panel.opts_view.get_buffer().set_text("")

def _out_profile_changed():
    selected_index = widgets.profile_panel.out_profile_combo.widget.get_active()
    if selected_index == 0:
        _fill_info_box(current_sequence().profile)
    else:
        profile = mltprofiles.get_profile_for_index(selected_index - 1)
        _fill_info_box(profile)

def _fill_info_box(profile):
    info_panel = guicomponents.get_profile_info_small_box(profile)
    widgets.info_panel = info_panel
    widgets.profile_panel.out_profile_info_box.display_info(info_panel)

def _preset_selection_changed():
    enc_index = widgets.render_type_panel.presets_selector.widget.get_active()
    ext = renderconsumer.non_user_encodings[enc_index].extension
    widgets.file_panel.extension_label.set_text("." + ext)
   
def _display_selection_in_opts_view():
    profile = get_current_profile()
    widgets.args_panel.display_encoding_args(profile,
                                             widgets.encoding_panel.encoding_selector.widget.get_active(), 
                                             widgets.encoding_panel.quality_selector.widget.get_active())
    
def _save_opts_pressed():
    rendergui.save_ffmpeg_opts_dialog(_save_opts_dialog_callback, FFMPEG_OPTS_SAVE_FILE_EXTENSION)

def _save_opts_dialog_callback(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        file_path = dialog.get_filenames()[0]
        opts_file = open(file_path, "w")
        buf = widgets.args_panel.opts_view.get_buffer()
        opts_text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), include_hidden_chars=True)
        opts_file.write(opts_text)
        opts_file.close()
        dialog.destroy()
    else:
        dialog.destroy()

def _load_opts_pressed():
    rendergui.load_ffmpeg_opts_dialog(_load_opts_dialog_callback, FFMPEG_OPTS_SAVE_FILE_EXTENSION)

def _load_opts_dialog_callback(dialog, response_id):
    if response_id == gtk.RESPONSE_ACCEPT:
        filename = dialog.get_filenames()[0]
        args_file = open(filename)
        args_text = args_file.read()
        widgets.args_panel.opts_view.get_buffer().set_text(args_text)
        dialog.destroy()
    else:
        dialog.destroy()

# ------------------------------------------------------------- framebuffer clip rendering
# Rendering a slow/fast motion version of media file.
def render_frame_buffer_clip(media_file):
    rendergui.show_slowmo_dialog(media_file, _render_frame_buffer_clip_dialog_callback)

def _render_frame_buffer_clip_dialog_callback(dialog, response_id, fb_widgets, media_file):
    if response_id == gtk.RESPONSE_ACCEPT:
        # speed, filename folder
        speed = float(int(fb_widgets.hslider.get_value())) / 100.0
        file_name = fb_widgets.file_name.get_text()
        filenames = fb_widgets.out_folder.get_filenames()
        folder = filenames[0]
        write_file = folder + "/"+ file_name + fb_widgets.extension_label.get_text()

        if os.path.exists(write_file):
            primary_txt = _("A File with given path exists!")
            secondary_txt = _("It is not allowed to render Motion Files with same paths as existing files.\nSelect another name for file.") 
            dialogutils.warning_message(primary_txt, secondary_txt, dialog)
            return

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
        mltrefhold.hold_ref(motion_producer)
        
        # Create sequence and add motion producer into it
        seq = sequence.Sequence(profile)
        seq.create_default_tracks()
        track = seq.tracks[seq.first_video_index]
        track.append(motion_producer, 0, motion_producer.get_length() - 1)

        print "motion clip render starting..."

        consumer = renderconsumer.get_render_consumer_for_encoding_and_quality(write_file, profile, encoding_option_index, quality_option_index)
        
        # start and end frames
        start_frame = 0
        end_frame = motion_producer.get_length() - 1
        wait_for_producer_stop = True
        if range_selection == 1:
            start_frame = int(float(media_file.mark_in) * (1.0 / speed))
            end_frame = int(float(media_file.mark_out + 1) * (1.0 / speed)) + int(1.0 / speed) #+ 40 # I'm unable to get this frame perfect.
                                                                                                    # +40 is to make sure rendering stops after mark out.
            if end_frame > motion_producer.get_length() - 1:
                end_frame = motion_producer.get_length() - 1
            
            wait_for_producer_stop = False # consumer wont stop automatically and needs to stopped explicitly

        # Launch render
        global motion_renderer, motion_progress_update
        motion_renderer = renderconsumer.FileRenderPlayer(write_file, seq.tractor, consumer, start_frame, end_frame)
        motion_renderer.wait_for_producer_end_stop = wait_for_producer_stop
        motion_renderer.start()

        title = _("Rendering Motion Clip")
        text = "<b>Motion Clip File: </b>" + write_file
        progress_bar = gtk.ProgressBar()
        dialog = rendergui.clip_render_progress_dialog(_FB_render_stop, title, text, progress_bar, gui.editor_window.window)

        motion_progress_update = renderconsumer.ProgressWindowThread(dialog, progress_bar, motion_renderer, _FB_render_stop)
        motion_progress_update.start()
        
    else:
        dialog.destroy()

def _FB_render_stop(dialog, response_id):
    print "motion clip render done"

    global motion_renderer, motion_progress_update
    motion_renderer.running = False
    motion_progress_update.running = False
    open_media_file_callback(motion_renderer.file_name)
    motion_renderer.running = None
    motion_progress_update.running = None

    dialogutils.delay_destroy_window(dialog, 1.6)

# ----------------------------------------------------------------------- single track transition render 
def render_single_track_transition_clip(transition_producer, encoding_option_index, quality_option_index, file_ext, transition_render_complete_cb, window_text):
    # Set render complete callback to availble render stop callback using global variable
    global transition_render_done_callback
    transition_render_done_callback = transition_render_complete_cb

    # Profile
    profile = PROJECT().profile

    folder = editorpersistance.prefs.render_folder

    file_name = md5.new(str(os.urandom(32))).hexdigest()
    write_file = folder + "/"+ file_name + file_ext

    # Render consumer
    consumer = renderconsumer.get_render_consumer_for_encoding_and_quality(write_file, profile, encoding_option_index, quality_option_index)
    
    # start and end frames
    start_frame = 0
    end_frame = transition_producer.get_length() - 1
        
    # Launch render
    # TODO: fix naming this isn't motion renderer
    global motion_renderer, motion_progress_update
    motion_renderer = renderconsumer.FileRenderPlayer(write_file, transition_producer, consumer, start_frame, end_frame)
    motion_renderer.start()
    
    title = _("Rendering Transition Clip")
    
    progress_bar = gtk.ProgressBar()
    dialog = rendergui.clip_render_progress_dialog(_transition_render_stop, title, window_text, progress_bar, gui.editor_window.window)
    
    motion_progress_update = renderconsumer.ProgressWindowThread(dialog, progress_bar, motion_renderer, _transition_render_stop)
    motion_progress_update.start()

def _transition_render_stop(dialog, response_id):
    global motion_renderer, motion_progress_update
    motion_renderer.running = False
    motion_progress_update.running = False
    motion_renderer.running = None
    motion_progress_update.running = None
    
    transition_render_done_callback(motion_renderer.file_name)

    dialogutils.delay_destroy_window(dialog, 1.0)
