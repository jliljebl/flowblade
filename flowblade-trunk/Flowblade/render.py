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


from gi.repository import Gtk

try:
    import mlt7 as mlt
except:
    import mlt7 as mlt
import hashlib
import os
import time

import appconsts
import atomicfile
import dialogutils
import editorstate
from editorstate import current_sequence
from editorstate import PROJECT
import editorpersistance
import gui
import guicomponents
import guiutils
import jobs
import mltprofiles
import renderconsumer
import rendergui
import userfolders
import utils

# User defined render agrs file extension
FFMPEG_OPTS_SAVE_FILE_EXTENSION = ".rargs"

open_media_file_callback = None # monkeypatched in by app.py to avoid circular imports

render_start_time = 0
widgets = utils.EmptyClass()
# progress_window = None

aborted = False

# Motion clip rendering
motion_renderer = None
motion_progress_update = None

# Transition clip rendering 
transition_render_done_callback = None

# ---------------------------------- rendering action and dialogs
def get_args_vals_list_for_current_selections():
    profile = get_current_profile()
    encoding_option_index = widgets.encoding_panel.encoding_selector.get_selected_encoding_index()
    quality_option_index = widgets.encoding_panel.quality_selector.widget.get_active()
    """
    if widgets.render_type_panel.type_combo.get_active() == 1: # Preset encodings                                                                             -1)
        encoding_option = renderconsumer.non_user_encodings[widgets.render_type_panel.presets_selector.widget.get_active()]
        args_vals_list = encoding_option.get_args_vals_tuples_list(profile)
    """

    if widgets.args_panel.use_args_check.get_active() == False: # User encodings
        args_vals_list = renderconsumer.get_args_vals_tuples_list_for_encoding_and_quality( profile, 
                                                                                            encoding_option_index, 
                                                                                            quality_option_index)
        args_vals_list.append(("ar", str(widgets.encoding_panel.sample_rate_selector.get_selected_rate())))
    else: # Manual args encodings
        if widgets.args_panel.text_buffer == None:
            # Normal height args panel
            buf = widgets.args_panel.opts_view.get_buffer()
        else:
            # Small heights with dialog for setting args
            buf = widgets.args_panel.text_buffer
        args_vals_list, error = renderconsumer.get_ffmpeg_opts_args_vals_tuples_list(buf)
    
        if error != None:
            dialogutils.warning_message("FFMPeg Args Error", error, gui.editor_window.window)
            return None
    
    return args_vals_list

def get_current_gui_selections():
    selections = {}
    #selections["use_user_encodings"] = widgets.render_type_panel.type_combo.get_active()
    selections["encoding_option_index"] = widgets.encoding_panel.encoding_selector.get_selected_encoding_index()
    selections["encoding_option_name"]  = widgets.encoding_panel.encoding_selector.categorised_combo.get_selected_name() # FIXME
    selections["quality_option_index"]= widgets.encoding_panel.quality_selector.widget.get_active()
    #selections["presets_index"] = widgets.render_type_panel.presets_selector.widget.get_active()
    selections["folder"] = widgets.file_panel.out_folder.get_current_folder()
    selections["name"] = widgets.file_panel.movie_name.get_text()
    selections["range"] = widgets.range_cb.get_active()
    selections["markinmarkout"] = (PROJECT().c_seq.tractor.mark_in, PROJECT().c_seq.tractor.mark_out)
    selections["use_project_profile"] = widgets.profile_panel.use_project_profile_check.get_active()
    selections["render_profile"] = widgets.profile_panel.out_profile_combo.widget.get_active()
    selections["render_profile_name"] = widgets.profile_panel.out_profile_combo.categories_combo.get_selected()
    selections["audio_frequency"] = widgets.encoding_panel.sample_rate_selector.widget.get_active()
    if widgets.args_panel.use_args_check.get_active() == True:
        if widgets.args_panel.text_buffer == None:
            buf = widgets.args_panel.opts_view.get_buffer()
        else:
            buf = widgets.args_panel.text_buffer
            
        buf_text = buf.get_text( buf.get_start_iter(), 
                                 buf.get_end_iter(), 
                                 include_hidden_chars=True)
        selections["render_args"] = buf_text
    else:
        selections["render_args"] = None
    return selections

def set_saved_gui_selections(selections):
    #widgets.render_type_panel.type_combo.set_active(selections["use_user_encodings"])
    try:
        enc_op_name = selections["encoding_option_name"]
        widgets.encoding_panel.encoding_selector.categorised_combo.set_selected(enc_op_name)
    except:
        print("Old style encoding option value could not be loaded.")
    widgets.encoding_panel.quality_selector.widget.set_active(selections["quality_option_index"])
    #widgets.render_type_panel.presets_selector.widget.set_active(selections["presets_index"])
    widgets.file_panel.out_folder.set_current_folder(selections["folder"])
    widgets.file_panel.movie_name.set_text(selections["name"])
    widgets.range_cb.set_active(selections["range"])
    try:
        # These were added later so we may not have the data
        if selections["range"] == 1:
            mark_in, mark_out = selections["markinmarkout"]
            PROJECT().c_seq.tractor.mark_in = mark_in
            PROJECT().c_seq.tractor.mark_out = mark_out
        widgets.profile_panel.use_project_profile_check.set_active(selections["use_project_profile"] )
        try:
            profile_name = selections["render_profile_name"]
            widgets.profile_panel.out_profile_combo.categories_combo.set_selected(profile_name)
        except:
            print("Old style profile option value could not be loaded.")
        if selections["render_args"] != None:
            widgets.args_panel.use_args_check.set_active(True)

        widgets.encoding_panel.sample_rate_selector.widget.set_active(selections["audio_frequency"])
    except:
        pass
    
def get_file_path():
    folder = widgets.file_panel.out_folder.get_filenames()[0]        
    filename = widgets.file_panel.movie_name.get_text()

    if  widgets.args_panel.use_args_check.get_active() == False:
        extension = widgets.file_panel.extension_label.get_text()
    else:
        if widgets.args_panel.text_buffer == None:
            extension = "." +  widgets.args_panel.ext_entry.get_text()
        else:
            # Small height with dialog args setting
            try:
                ext_str = widgets.args_panel.args_edit_window.ext_entry.get_text()
            except:
                # args edit window was never opened, so requested value not available/set, use default extension
                ext_str = widgets.args_panel.ext
            extension = "." + ext_str
    return folder + "/" + filename + extension


# --------------------------------------------------- gui
def create_widgets():
    """
    Widgets for editing render properties and viewing render progress.
    """
    widgets.file_panel = rendergui.RenderFilePanel()
    #widgets.render_type_panel = rendergui.RenderTypePanel(_render_type_changed, _preset_selection_changed)
    widgets.profile_panel = rendergui.RenderProfilePanel(_out_profile_changed)
    widgets.encoding_panel = rendergui.RenderEncodingPanel(widgets.file_panel.extension_label)
    if (editorstate.SCREEN_HEIGHT > 898):
        widgets.args_panel = rendergui.RenderArgsPanel(_save_opts_pressed, _load_opts_pressed,
                                                       _display_selection_in_opts_view,
                                                       set_default_values_for_widgets)
    else:
        widgets.args_panel = rendergui.RenderArgsPanelSmall(_save_opts_pressed, _load_opts_pressed,
                                                            _display_selection_in_opts_view)
        
    # Range, Render, Reset, Render Queue
    widgets.render_button = guiutils.get_render_button()
    widgets.range_cb = rendergui.get_range_selection_combo()
    widgets.queue_button = Gtk.Button(_("To Queue"))
    widgets.queue_button.set_tooltip_text(_("Save Project in Render Queue"))
    widgets.render_range_panel = rendergui.RenderRangePanel(widgets.range_cb)

    # Add some tooltips
    widgets.range_cb.set_tooltip_text(_("Select render range"))
    widgets.render_button.set_tooltip_text(_("Begin Rendering"))

def set_default_values_for_widgets(movie_name_too=False):
    if len(renderconsumer.encoding_options) == 0:# this won't work if no encoding options available
        return                   # but we don't want crash, so that we can inform user
    widgets.encoding_panel.encoding_selector.categorised_combo.refill(renderconsumer.categorized_encoding_options)
    widgets.encoding_panel.encoding_selector.categorised_combo.set_selected(renderconsumer.DEFAULT_ENCODING_NAME)
    if movie_name_too == True:
        widgets.file_panel.movie_name.set_text("movie")

    # Default render path is ~/
    if editorpersistance.prefs.default_render_directory == appconsts.USER_HOME_DIR:
        widgets.file_panel.out_folder.set_current_folder(os.path.expanduser("~") + "/")
    else:
        widgets.file_panel.out_folder.set_current_folder(editorpersistance.prefs.default_render_directory)
    widgets.args_panel.use_args_check.set_active(False)
    widgets.profile_panel.use_project_profile_check.set_active(True)

def enable_user_rendering(value):
    widgets.encoding_panel.set_sensitive(value)
    widgets.profile_panel.set_sensitive(value)
    widgets.info_panel.set_sensitive(value)
    widgets.args_panel.set_sensitive(value)

def save_render_start_time():
    global render_start_time
    render_start_time = time.time()

def maybe_open_rendered_file_in_bin():
    if widgets.args_panel.open_in_bin.get_active() == False:
        return
        
    file_path = get_file_path()
    open_media_file_callback(file_path)

def get_current_profile():
    profile_desc = widgets.profile_panel.out_profile_combo.categories_combo.get_selected()
    profile = mltprofiles.get_profile(profile_desc)
    return profile

def fill_out_profile_widgets():
    """
    Called some time after widget creation when current_sequence is known and these can be filled.
    """
    
    widgets.profile_panel.out_profile_combo.set_initial_selection()
    _fill_info_box(current_sequence().profile)

def reload_profiles():
    renderconsumer.load_render_profiles()
    
    widgets.profile_panel.out_profile_combo.categories_combo.refill(mltprofiles._categorized_profiles)
    widgets.profile_panel.out_profile_combo.set_initial_selection()

def _out_profile_changed(categories_combo):
    # FIXME: 'out_profile_combo' is actually the panel containing the combobox
    try:
        profile_desc = widgets.profile_panel.out_profile_combo.categories_combo.get_selected()
    except TypeError:
        # We are getting events here when refilling the profile widget after user has updated profiles
        # and it is easier to ignore the events then to disconnect the listener.
        return 
    profile = mltprofiles.get_profile(profile_desc)
    _fill_info_box(profile)

def _fill_info_box(profile):
    info_panel = guicomponents.get_profile_info_small_box(profile)
    widgets.info_panel = info_panel
    widgets.profile_panel.out_profile_info_box.display_info(info_panel)

def _display_selection_in_opts_view():
    profile = get_current_profile()
    widgets.args_panel.display_encoding_args(profile,
                                             widgets.encoding_panel.encoding_selector.get_selected_encoding_index(), 
                                             widgets.encoding_panel.quality_selector.widget.get_active())
    
def _save_opts_pressed():
    rendergui.save_ffmpeg_opts_dialog(_save_opts_dialog_callback, FFMPEG_OPTS_SAVE_FILE_EXTENSION)

def _save_opts_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        file_path = dialog.get_filenames()[0]
        buf = widgets.args_panel.opts_view.get_buffer()
        opts_text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), include_hidden_chars=True)
        with atomicfile.AtomicFileWriter(file_path, "w") as afw:
            opts_file = afw.get_file()
            opts_file.write(opts_text)
        dialog.destroy()
    else:
        dialog.destroy()

def _load_opts_pressed():
    rendergui.load_ffmpeg_opts_dialog(_load_opts_dialog_callback, FFMPEG_OPTS_SAVE_FILE_EXTENSION)

def _load_opts_dialog_callback(dialog, response_id):
    if response_id == Gtk.ResponseType.ACCEPT:
        filename = dialog.get_filenames()[0]
        args_file = open(filename)
        args_text = args_file.read()
        widgets.args_panel.opts_view.get_buffer().set_text(args_text)
        dialog.destroy()
    else:
        dialog.destroy()

# ------------------------------------------------------------- framebuffer clip rendering
# Rendering a slow/fast motion version of media file.
def render_frame_buffer_clip(media_file, default_range_render=False):
    rendergui.show_slowmo_dialog(media_file, default_range_render, _render_frame_buffer_clip_dialog_callback)

def _render_frame_buffer_clip_dialog_callback(dialog, response_id, fb_widgets, media_file):
    if response_id == Gtk.ResponseType.ACCEPT:
        # Get data needed for render.
        speed = float(int(fb_widgets.adjustment.get_value())) / 100.0
        
        file_name = fb_widgets.file_name.get_text()
        filenames = fb_widgets.out_folder.get_filenames()
        folder = filenames[0]
        write_file = folder + "/"+ file_name + fb_widgets.extension_label.get_text()

        if os.path.exists(write_file):
            primary_txt = _("A File with given path exists!")
            secondary_txt = _("It is not allowed to render Motion Files with same paths as existing files.\nSelect another name for file.") 
            dialogutils.warning_message(primary_txt, secondary_txt, dialog)
            return
            
        profile_desc = fb_widgets.categories_combo.get_selected()
        profile = mltprofiles.get_profile(profile_desc)
        profile_desc = profile_desc.replace(" ", "_")
    
        encoding_option_index = fb_widgets.encodings_cb.get_active()
        quality_option_index = fb_widgets.quality_cb.get_active()

        range_selection = fb_widgets.render_range.get_active()

        dialog.destroy()
        
        source_path = media_file.path
        if media_file.is_proxy_file == True:
            source_path = media_file.second_file_path

        # start and end frames
        motion_producer = mlt.Producer(profile, None, str("timewarp:" + str(speed) + ":" + str(source_path)))
        start_frame = 0
        end_frame = motion_producer.get_length() - 1
        render_full_range = True # REMOVE THIS DONW THE LINE, NOT USED.
        if range_selection == 1:
            start_frame = int(float(media_file.mark_in) * (1.0 / speed))
            end_frame = int(float(media_file.mark_out + 1) * (1.0 / speed)) + int(1.0 / speed)
            
            if end_frame > motion_producer.get_length() - 1:
                end_frame = motion_producer.get_length() - 1
            
            render_full_range = False # consumer wont stop automatically and needs to stopped explicitly
        
        session_id = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
        
        args = ("session_id:" + str(session_id), 
                "speed:" + str(speed), 
                "write_file:" + str(write_file),
                "profile_desc:" + str(profile_desc),
                "encoding_option_index:" + str(encoding_option_index),
                "quality_option_index:"+ str(quality_option_index),
                "source_path:" + str(source_path),
                "render_full_range:" + str(render_full_range),
                "start_frame:" + str(start_frame),
                "end_frame:" + str(end_frame))

        job_queue_object = jobs.MotionRenderJobQueueObject(session_id, write_file, args)
        job_queue_object.add_to_queue()

    else:
        dialog.destroy()

def _FB_render_stop(dialog, response_id):
    print("motion clip render done")

    global motion_renderer, motion_progress_update
    motion_renderer.running = False
    motion_progress_update.running = False
    open_media_file_callback(motion_renderer.file_name)
    motion_renderer.running = None
    motion_progress_update.running = None

    dialogutils.delay_destroy_window(dialog, 1.6)

def render_reverse_clip(media_file, default_range_render=False):
    rendergui.show_reverse_dialog(media_file, default_range_render, _render_reverse_clip_dialog_callback)

def _render_reverse_clip_dialog_callback(dialog, response_id, fb_widgets, media_file):
    if response_id == Gtk.ResponseType.ACCEPT:
        print("_render_reverse_clip_dialog_callback")
        
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
        profile_desc = fb_widgets.categories_combo.get_selected()
        profile = mltprofiles.get_profile(profile_desc)
        profile_desc = profile_desc.replace(" ", "_")

        # Render consumer properties
        encoding_option_index = fb_widgets.encodings_cb.get_active()
        quality_option_index = fb_widgets.quality_cb.get_active()

        # Range
        range_selection = fb_widgets.render_range.get_active()
        
        dialog.destroy()

        # Create motion producer
        source_path = media_file.path
        if media_file.is_proxy_file == True:
            source_path = media_file.second_file_path

        motion_producer = mlt.Producer(profile, None, str("timewarp:" + str(speed) + ":" + str(source_path)))
        
        # start and end frames
        start_frame = 0
        end_frame = motion_producer.get_length() - 1
        render_full_range = True
        if range_selection == 1:
            start_frame = int(float(media_file.length - media_file.mark_out - 1) * (1.0 / -speed))
            end_frame = int(float(media_file.length - media_file.mark_out + (media_file.mark_out - media_file.mark_in) + 1) * (1.0 / -speed)) + int(1.0 / -speed)

            if end_frame > motion_producer.get_length() - 1:
                end_frame = motion_producer.get_length() - 1
            if start_frame < 0:
                start_frame = 0
            
            render_full_range = False # consumer wont stop automatically and needs to stopped explicitly
            
        session_id = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
        
        args = ("session_id:" + str(session_id), 
                "speed:" + str(speed), 
                "write_file:" + str(write_file),
                "profile_desc:" + str(profile_desc),
                "encoding_option_index:" + str(encoding_option_index),
                "quality_option_index:"+ str(quality_option_index),
                "source_path:" + str(source_path),
                "render_full_range:" + str(render_full_range),
                "start_frame:" + str(start_frame),
                "end_frame:" + str(end_frame))

        job_queue_object = jobs.MotionRenderJobQueueObject(session_id, write_file, args)
        job_queue_object.add_to_queue()
    else:
        dialog.destroy()

def _REVERSE_render_stop(dialog, response_id):
    print("Reverse clip render done")

    global motion_renderer, motion_progress_update
    motion_renderer.running = False
    motion_progress_update.running = False
    open_media_file_callback(motion_renderer.file_name)
    motion_renderer.running = None
    motion_progress_update.running = None

    dialogutils.delay_destroy_window(dialog, 1.6)
    
# ----------------------------------------------------------------------- single track transition render 
def render_single_track_transition_clip(transition_producer, encoding_option_index, quality_option_index, file_ext, transition_render_complete_cb, window_text):
    # Set render complete callback to available render stop callback using global variable
    global transition_render_done_callback
    transition_render_done_callback = transition_render_complete_cb

    # Profile
    profile = PROJECT().profile

    folder = userfolders.get_render_dir()

    file_name = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
    write_file = folder + "/"+ file_name + file_ext

    # Render consumer
    consumer = renderconsumer.get_render_consumer_for_encoding_and_quality(write_file, profile, encoding_option_index, quality_option_index)
    
    # start and end frames
    start_frame = 0
    end_frame = transition_producer.get_length() - 1
        
    # Launch render
    # TODO: fix naming, this isn't motion renderer
    global motion_renderer, motion_progress_update
    motion_renderer = renderconsumer.FileRenderPlayer(write_file, transition_producer, consumer, start_frame, end_frame)
    motion_renderer.start()
    
    title = _("Rendering Transition Clip")
    
    progress_bar = Gtk.ProgressBar()
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
