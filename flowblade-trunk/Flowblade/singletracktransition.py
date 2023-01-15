"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2022 Janne Liljeblad.

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
This module handles creating single track rendered transitions.
"""

from gi.repository import Gtk, GLib

import hashlib
import os
import threading
import time

import appconsts
import dialogs
import dialogutils
import edit
import editorstate
from editorstate import current_sequence
from editorstate import get_track
from editorstate import PROJECT
from editorstate import PLAYER
import gui
import guiutils
import mlttransitions
import movemodes
import panels
import renderconsumer
import render
import userfolders

# Used to store transition render data used at render complete callback.
transition_render_data = None

def add_transition_menu_item_selected():
    if movemodes.selected_track == -1:
        # INFOWINDOW
        return

    clip_count = movemodes.selected_range_out - movemodes.selected_range_in + 1 # +1 out incl.
    if not (clip_count == 2):
        # INFOWINDOW
        return
    add_transition_pressed()

def add_transition_pressed(retry_from_render_folder_select=False):
    if movemodes.selected_track == -1:
        print("no selection track")
        # INFOWINDOW
        return

    track = get_track(movemodes.selected_track)
    clip_count = movemodes.selected_range_out - movemodes.selected_range_in + 1 # +1 out incl.

    if not (clip_count == 2):
        return

    from_clip = track.clips[movemodes.selected_range_in]
    to_clip = track.clips[movemodes.selected_range_out]
    
    transition_data = get_transition_data_for_clips(track, from_clip, to_clip)
    
    if track.id >= current_sequence().first_video_index:
        transition_edit_dialog(_add_transition_dialog_callback, 
                                       transition_data)
    else:
        _no_audio_tracks_mixing_info()

def get_transition_data_for_clips(track, from_clip, to_clip):
    
    # Get available clip handles to do transition
    from_handle = from_clip.get_length() - from_clip.clip_out
    from_clip_length = from_clip.clip_out - from_clip.clip_in                                                 
    to_handle = to_clip.clip_in
    to_clip_length = to_clip.clip_out - to_clip.clip_in
    
    if to_clip_length < from_handle:
        from_handle = to_clip_length
    if from_clip_length < to_handle:
        to_handle = from_clip_length
        
    # Images have limitless handles, but we simulate that with big value
    IMAGE_MEDIA_HANDLE_LENGTH = 1000
    if from_clip.media_type == appconsts.IMAGE:
        from_handle = IMAGE_MEDIA_HANDLE_LENGTH
    if to_clip.media_type == appconsts.IMAGE:
        to_handle = IMAGE_MEDIA_HANDLE_LENGTH
     
    max_length = from_handle + to_handle
    
    transition_data = {"track":track,
                       "from_clip":from_clip,
                       "to_clip":to_clip,
                       "from_handle":from_handle,
                       "to_handle":to_handle,
                       "max_length":max_length}
    return transition_data

def _add_transition_dialog_callback(dialog, response_id, selection_widgets, transition_data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    # Get input data
    type_combo, length_entry, enc_combo, quality_combo, wipe_luma_combo_box, steal_frames, encodings = selection_widgets
    transition_type_selection_index = type_combo.get_active()

    quality_option_index = quality_combo.get_active()
    
    # 'encodings' is subset of 'renderconsumer.encoding_options' because libx264 was always buggy for this 
    # use. We find out right 'renderconsumer.encoding_options' index for rendering.
    selected_encoding_option_index = enc_combo.get_active()
    enc = encodings[selected_encoding_option_index]
    encoding_option_index = renderconsumer.encoding_options.index(enc)
    
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension
    sorted_wipe_luma_index = wipe_luma_combo_box.get_active()
    force_steal_frames = steal_frames.get_active()
    editorstate.steal_frames = force_steal_frames # making this selection as default for next invocation

    try:
        length = int(length_entry.get_text())
    except Exception as e:
        # INFOWINDOW, bad input
        return

    dialog.destroy()

    from_clip = transition_data["from_clip"]
    to_clip = transition_data["to_clip"]

    # Get values to build transition render sequence
    # Divide transition lenght between clips, odd frame goes to from_clip 
    real_length = length + 1 # first frame is 100% a from_clip frame so we are going to have to drop that
    to_part = real_length // 2
    from_part = real_length - to_part

    # HACKFIX, I just tested this till it worked, not entirely sure on math here
    if to_part == from_part:
        add_thingy = 0
    else:
        add_thingy = 1

    # Get required handle lengths.
    from_req = from_part - add_thingy
    to_req = to_part - (1 - add_thingy)
    from_handle = transition_data["from_handle"]
    to_handle = transition_data["to_handle"]
    from_clip_index = movemodes.selected_range_in
    
    # Check that we have enough handles
    if from_req > from_handle or to_req > to_handle:
        if force_steal_frames == False:
            _show_no_handles_dialog( from_req,
                                     from_handle, 
                                     to_req,
                                     to_handle,
                                     length)
            return

        # Force trim from clip if needed
        from_needed = from_req - from_handle
        if from_needed > 0:
            if from_needed + 1 < from_clip.clip_length():
                data = {"track":transition_data["track"],
                        "clip":transition_data["from_clip"],
                        "index":from_clip_index,
                        "delta":-from_needed,
                        "undo_done_callback":None, # we're not doing the callback because we are not in trim tool that needs it
                        "first_do":False} # setting this False prevents callback
                action = edit.trim_end_action(data)
                edit.do_gui_update = False
                action.do_edit()
                edit.do_gui_update = True
            else:
                # Clip is not long enough for frame steeling, transition fails.
                _show_failure_to_steal_frames_dialog(from_needed, from_clip.clip_length(), -1, -1)
                return
                
        # Force trim to clip if needed
        to_needed = to_req - to_handle
        if to_needed > 0:
            if to_needed + 1 < to_clip.clip_length():
                data = {"track":transition_data["track"],
                        "clip":transition_data["to_clip"],
                        "index":from_clip_index + 1,
                        "delta":to_needed,
                        "undo_done_callback":None, # we're not doing the callback because we are not in trim tool that needs it
                        "first_do":False} # setting this False prevents callback
                action = edit.trim_start_action(data)
                edit.do_gui_update = False
                action.do_edit()
                edit.do_gui_update = True
            else:
                # Clip is not long enough for frame steeling, transition fails.
                _show_failure_to_steal_frames_dialog(-1, -1, to_needed, to_clip.clip_length())
                return

    editorstate.transition_length = length # Saved for user so that last length becomes default for next invocation.
    
    # Get from in and out frames
    from_in = from_clip.clip_out - from_part + add_thingy
    from_out = from_in + length # or transition will include one frame too many
    
    # Get to in and out frames
    to_in = to_clip.clip_in - to_part - 1 
    to_out = to_in + length # or transition will include one frame too many

    # Edit clears selection, get transition index before selection is cleared
    trans_index = from_clip_index + 1
    movemodes.clear_selected_clips()

    # Save encoding
    PROJECT().set_project_property(appconsts.P_PROP_TRANSITION_ENCODING, (encoding_option_index, quality_option_index))

    producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                        from_clip,
                                                                        to_clip,
                                                                        from_out,
                                                                        from_in,
                                                                        to_out,
                                                                        to_in,
                                                                        transition_type_selection_index,
                                                                        sorted_wipe_luma_index)

    creation_data = (   from_clip.id,
                        to_clip.id,
                        from_out,
                        from_in,
                        to_out,
                        to_in,
                        transition_type_selection_index,
                        sorted_wipe_luma_index)
                                                
    # Save transition data into global variable to be available at render complete callback
    global transition_render_data
    transition_render_data = (trans_index, from_clip, to_clip, transition_data["track"], from_in, to_out, transition_type_selection_index, creation_data, add_thingy)
    window_text, type_id = mlttransitions.rendered_transitions[transition_type_selection_index]
    window_text = _("Rendering ") + window_text

    render.render_single_track_transition_clip( producer_tractor,
                                                encoding_option_index,
                                                quality_option_index, 
                                                str(extension_text), 
                                                _transition_render_complete,
                                                window_text)

def _transition_render_complete(clip_path):
    print("Render complete")

    global transition_render_data
    transition_index, from_clip, to_clip, track, from_in, to_out, transition_type, creation_data, length_fix = transition_render_data

    transition_clip = current_sequence().create_rendered_transition_clip(clip_path, transition_type)
    transition_clip.creation_data = creation_data

    data = {"transition_clip":transition_clip,
            "transition_index":transition_index,
            "from_clip":from_clip,
            "to_clip":to_clip,
            "track":track,
            "from_in":from_in,
            "to_out":to_out,
            "length_fix":length_fix}

    action = edit.add_centered_transition_action(data)
    action.do_edit()

def re_render_transition(data):
    clip, track, msg, x = data
    if not hasattr(clip, "creation_data"):
        _no_creation_data_dialog()
        return
    
    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_selection_index, \
    sorted_wipe_luma_index, color_str = clip.creation_data
    
    from_clip = editorstate.current_sequence().get_clip_for_id(from_clip_id)
    to_clip = editorstate.current_sequence().get_clip_for_id(to_clip_id)
    if from_clip == None or to_clip == None:
        _source_clips_not_found_dialog()
        return

    transition_data = {"track":track,
                        "clip":clip,
                        "from_clip":from_clip,
                        "to_clip":to_clip}

    dialogs.transition_re_render_dialog(_transition_RE_render_dialog_callback, transition_data)

def _transition_RE_render_dialog_callback(dialog, response_id, selection_widgets, transition_data):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return

    enc_combo, quality_combo, encodings = selection_widgets
    quality_option_index = quality_combo.get_active()

    # 'encodings' is subset of 'renderconsumer.encoding_options' because libx264 was always buggy for this 
    # use. We find out right 'renderconsumer.encoding_options' index for rendering.
    selected_encoding_option_index = enc_combo.get_active()
    enc = encodings[selected_encoding_option_index]
    encoding_option_index = renderconsumer.encoding_options.index(enc)
    
    dialog.destroy()
        
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension

    clip = transition_data["clip"]
    track =  transition_data["track"]
    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_selection_index, \
    sorted_wipe_luma_index, color_str = clip.creation_data
    
    trans_index = track.clips.index(clip)

    producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                        transition_data["from_clip"],
                                                                        transition_data["to_clip"],
                                                                        from_out,
                                                                        from_in,
                                                                        to_out,
                                                                        to_in,
                                                                        transition_type_selection_index,
                                                                        sorted_wipe_luma_index,
                                                                        color_str)
    

    # Save transition data into global variable to be available at render complete callback
    global transition_render_data
    transition_render_data = (trans_index, track, clip, transition_type_selection_index, clip.creation_data)
    window_text, type_id = mlttransitions.rendered_transitions[transition_type_selection_index]
    window_text = _("Rerendering ") + window_text

    render.render_single_track_transition_clip( producer_tractor,
                                                encoding_option_index,
                                                quality_option_index, 
                                                str(extension_text), 
                                                _transition_RE_render_complete,
                                                window_text)

def _transition_RE_render_complete(clip_path):
    global transition_render_data
    transition_index, track, orig_clip, transition_type, creation_data = transition_render_data

    transition_clip = current_sequence().create_rendered_transition_clip(clip_path, transition_type)
    transition_clip.creation_data = creation_data
    transition_clip.clip_in = orig_clip.clip_in
    transition_clip.clip_out = orig_clip.clip_out

    data = {"track":track,
            "transition_clip":transition_clip,
            "transition_index":transition_index}

    action = edit.replace_centered_transition_action(data)
    action.do_edit()

def _show_no_handles_dialog(from_req, from_handle, to_req, to_handle, length):
    SPACE_TAB = "    "
    info_text = _("To create a rendered transition you need enough media overlap from both clips!\n\n")
    first_clip_info = None
    if from_req > from_handle:

        first_clip_info = \
                    _("<b>FIRST CLIP MEDIA OVERLAP:</b>  ") + \
                    SPACE_TAB + _("Available <b>") + str(from_handle) + _("</b> frame(s), " ) + \
                    SPACE_TAB + _("Required <b>") + str(from_req) + _("</b> frame(s)") + "\n"  + \
                    SPACE_TAB + _("Trim first clip end back <b>") + str(from_req) + _("</b> frame(s)") + "\n"

    second_clip_info = None
    if to_req  > to_handle:
        second_clip_info = \
                        _("<b>SECOND CLIP MEDIA OVERLAP:</b> ") + \
                        SPACE_TAB + _("Available <b>") + str(to_handle) + _("</b> frame(s), ") + \
                        SPACE_TAB + _("Required <b>") + str(to_req) + _("</b> frame(s) ") + "\n" + \
                        SPACE_TAB + _("Trim second clip start forward <b>") + str(from_req) + _("</b> frame(s)") + "\n"

    img = Gtk.Image.new_from_file ((respaths.IMAGE_PATH + "transition_wrong.png"))
    img2 = Gtk.Image.new_from_file ((respaths.IMAGE_PATH + "transition_right.png"))
    img2.set_margin_bottom(24)

    label1 = Gtk.Label(label=_("Current situation, not enought media overlap:"))
    label1.set_margin_bottom(12)
    label2 = Gtk.Label(label=_("You need more media overlap:"))
    label2.set_margin_bottom(12)
    label2.set_margin_top(24)
    if first_clip_info != None:
        label4 = Gtk.Label(label=first_clip_info)
        label4.set_use_markup(True)
    if second_clip_info != None:
        label5 = Gtk.Label(label=second_clip_info)
        label5.set_use_markup(True)

    row1 = guiutils.get_centered_box([label1])
    row2 = guiutils.get_centered_box([img])
    row3 = guiutils.get_centered_box([label2])
    row4 = guiutils.get_centered_box([img2])

    rows = [row1, row2, row3, row4]


    if first_clip_info != None:
        row6 = guiutils.get_left_justified_box([label4])
        rows.append(row6)
    if second_clip_info != None:
        row7 = guiutils.get_left_justified_box([label5])
        rows.append(row7)
    
    label = Gtk.Label(label=_("Activating 'Steal frames from clips if needed' checkbox can help too."))
    row = guiutils.get_left_justified_box([label])
    row.set_margin_top(24)
    rows.append(row)

    dialogutils.warning_message_with_panels(_("More media overlap needed to create transition!"), 
                                            "", gui.editor_window.window, True, dialogutils.dialog_destroy, rows)
            
def _show_failure_to_steal_frames_dialog(from_needed, from_length, to_needed, to_length):
    SPACE_TAB = "    "
    first_clip_info = None
    if from_needed > 0:

        first_clip_info = \
                    _("<b>FIRST CLIP:</b>  ") + \
                    SPACE_TAB + _("Length <b>") + str(from_length) + _("</b> frame(s), " ) + \
                    SPACE_TAB + _("Required shortning <b>") + str(from_needed) + _("</b> frame(s)")


    second_clip_info = None
    if to_needed  > 0:
        second_clip_info = \
                        _("<b>SECOND CLIP:</b> ") + \
                        SPACE_TAB + _("Length <b>") + str(to_length) + _("</b> frame(s), ") + \
                        SPACE_TAB + _("Required shortning <b>") + str(to_needed) + _("</b> frame(s) ")

    rows = []
    if first_clip_info != None:
        first_clip_info_label = Gtk.Label(label=first_clip_info)
        first_clip_info_label.set_use_markup(True)
        row = guiutils.get_left_justified_box([first_clip_info_label])
        rows.append(row)
        label1 = Gtk.Label(label="\u2022" + " " + _("Lengthen first Clip from beginning:"))
        label1.set_margin_bottom(12)
        label1.set_margin_top(24)
        img = Gtk.Image.new_from_file ((respaths.IMAGE_PATH + "transition_fix_first_clip.png"))
        row1 = guiutils.get_left_justified_box([guiutils.pad_label(40,12), label1])
        row2 = guiutils.get_centered_box([img])
        rows.append(row1)
        rows.append(row2)
        label2 = Gtk.Label(label="\u2022" + " " + _("or make Transition shorter."))
        row1 = guiutils.get_left_justified_box([guiutils.pad_label(40,12), label2])
        rows.append(row1)

    if second_clip_info != None:
        last_clip_info_label = Gtk.Label(label=second_clip_info)
        last_clip_info_label.set_use_markup(True)
        row = guiutils.get_left_justified_box([last_clip_info_label])
        rows.append(row)
        label1 = Gtk.Label(label="\u2022" + " " + _("Lengthen second Clip from end:"))
        label1.set_margin_bottom(12)
        label1.set_margin_top(24)
        img = Gtk.Image.new_from_file ((respaths.IMAGE_PATH + "transition_fix_last_clip.png"))
        row1 = guiutils.get_left_justified_box([guiutils.pad_label(40,12), label1])
        row2 = guiutils.get_centered_box([img])
        rows.append(row1)
        rows.append(row2)
        label2 = Gtk.Label(label="\u2022" + " " + _("or make Transition shorter."))
        row1 = guiutils.get_left_justified_box([guiutils.pad_label(40,12), label2])
        rows.append(row1)

    dialogutils.warning_message_with_panels(_("<b>Stealing frames from clips to transition failed!</b>"), 
                                            "", gui.editor_window.window, True, dialogutils.dialog_destroy, rows)





def rerender_all_rendered_transitions():
    seq = editorstate.current_sequence()
    
    # Get list of rerendered transitions and unrenderable count
    rerender_list = []
    unrenderable = 0
    for i in range(1, len(seq.tracks)):
        track = seq.tracks[i]
        for j in range(0, len(track.clips)):
            clip = track.clips[j]
            if hasattr(clip, "rendered_type"):
                if hasattr(clip, "creation_data"):
                    from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, \
                    transition_type_selection_index, sorted_wipe_luma_index = clip.creation_data
                    from_clip = editorstate.current_sequence().get_clip_for_id(from_clip_id)
                    to_clip = editorstate.current_sequence().get_clip_for_id(to_clip_id)
                    # transition
                    if from_clip == None or to_clip == None:
                         unrenderable += 1
                    else:
                        rerender_list.append((clip, track))
            
                else:
                    unrenderable += 1
    
    # Show dialog and pass data
    dialogs.re_render_all_dialog(_RE_render_all_dialog_callback, rerender_list, unrenderable)

def _RE_render_all_dialog_callback(dialog, response_id, selection_widgets, rerender_list):
    if response_id != Gtk.ResponseType.ACCEPT:
        dialog.destroy()
        return
    

    # Get input data
    enc_combo, quality_combo, encodings = selection_widgets
    quality_option_index = quality_combo.get_active()
    
    # 'encodings' is subset of 'renderconsumer.encoding_options' because libx264 was always buggy for this 
    # use. We find out right 'renderconsumer.encoding_options' index for rendering.
    selected_encoding_option_index = enc_combo.get_active()
    enc = encodings[selected_encoding_option_index]
    encoding_option_index = renderconsumer.encoding_options.index(enc)
    
    extension_text = "." + renderconsumer.encoding_options[encoding_option_index].extension

    dialog.destroy()
    
    renrender_window = ReRenderderAllWindow((encoding_option_index, quality_option_index, extension_text), rerender_list)
    renrender_window.create_gui()
    renrender_window.start_render()


class ReRenderderAllWindow:
    
    def __init__(self, encoding_selections, rerender_list):
        self.rerender_list = rerender_list
        self.rendered_items = []
        self.encoding_selections = encoding_selections
        self.dialog = Gtk.Dialog(_("Rerender all Rendered Transitions / Fades"),
                         gui.editor_window.window,
                         Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                         (_("Cancel"), Gtk.ResponseType.REJECT))
        self.current_item = 0
        self.runner_thread = None
        self.renderer = None
    
    def create_gui(self):
        text = ""
        self.text_label = Gtk.Label(label=text)
        self.text_label.set_use_markup(True)
        
        text_box = Gtk.HBox(False, 2)
        text_box.pack_start(self.text_label,False, False, 0)
        text_box.pack_start(Gtk.Label(), True, True, 0)

        status_box = Gtk.HBox(False, 2)
        status_box.pack_start(text_box, False, False, 0)
        status_box.pack_start(Gtk.Label(), True, True, 0)

        self.progress_bar = Gtk.ProgressBar()
    
        progress_vbox = Gtk.VBox(False, 2)
        progress_vbox.pack_start(status_box, False, False, 0)
        progress_vbox.pack_start(guiutils.get_pad_label(10, 10), False, False, 0)
        progress_vbox.pack_start(self.progress_bar, False, False, 0)

        alignment = guiutils.set_margins(progress_vbox, 12, 12, 12, 12)

        self.dialog.vbox.pack_start(alignment, True, True, 0)
        dialogutils.set_outer_margins(self.dialog.vbox)
        self.dialog.set_default_size(500, 125)
        alignment.show_all()
        self.dialog.connect('response', self._cancel_pressed)
        self.dialog.show()

    def start_render(self):
        self.runner_thread = ReRenderRunnerThread(self)
        self.runner_thread.start()

    def render_next(self):
        # Update item text          
        info_text = _("Rendering item ") + str(self.current_item + 1) + "/" + str(len(self.rerender_list))
        GLib.idle_add(self._update_text_label, info_text)
        
        # Get render data
        clip, track = self.rerender_list[self.current_item]
        encoding_option_index, quality_option_index, file_ext = self.encoding_selections 

        # Dreate render consumer
        profile = PROJECT().profile
        folder = userfolders.get_render_dir()
        file_name = hashlib.md5(str(os.urandom(32)).encode('utf-8')).hexdigest()
        self.write_file = folder + "/"+ file_name + file_ext
        consumer = renderconsumer.get_render_consumer_for_encoding_and_quality(self.write_file, profile, encoding_option_index, quality_option_index)
        
        if clip.rendered_type > appconsts.RENDERED_COLOR_DIP:
            self._render_fade(clip, track, consumer, self.write_file)
        else:
            self._render_transition(clip, track, consumer, self.write_file)

    def _render_transition(self, clip, track, consumer, write_file):
        from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_selection_index, \
        sorted_wipe_luma_index = clip.creation_data

        from_clip = editorstate.current_sequence().get_clip_for_id(from_clip_id)
        to_clip = editorstate.current_sequence().get_clip_for_id(to_clip_id)
                    
        producer_tractor = mlttransitions.get_rendered_transition_tractor(  editorstate.current_sequence(),
                                                                            from_clip,
                                                                            to_clip,
                                                                            from_out,
                                                                            from_in,
                                                                            to_out,
                                                                            to_in,
                                                                            transition_type_selection_index,
                                                                            sorted_wipe_luma_index)
        
        # start and end frames
        start_frame = 0
        end_frame = producer_tractor.get_length() - 1
        
        # Launch render
        self.renderer = renderconsumer.FileRenderPlayer(write_file, producer_tractor, consumer, start_frame, end_frame)
        self.renderer.start()
        
    def update_fraction(self):
        if self.renderer == None:
            return
        render_fraction = self.renderer.get_render_fraction()
        GLib.idle_add(self._update_progressbar, render_fraction)

    def show_full_fraction(self):
        GLib.idle_add(self._update_progressbar, 1.0)
        
    def item_render_complete(self):
        clip, track = self.rerender_list[self.current_item]
        self.rendered_items.append((clip, track, str(self.write_file)))
        self.current_item += 1

    def all_items_done(self):
        return self.current_item == len(self.rerender_list)

    def _cancel_pressed(self, dialog, response_id):
        self.dialog.destroy()

    def exit_shutdown(self):       
        for render_item in self.rendered_items:
            orig_clip, track, new_clip_path = render_item
            
            from_clip_id, to_clip_id, from_out, from_in, to_out, to_in, transition_type_index, \
            sorted_wipe_luma_index = orig_clip.creation_data
        
            clip_index = track.clips.index(orig_clip)
                        
    
            transition_clip = current_sequence().create_rendered_transition_clip(new_clip_path, transition_type_index)
            transition_clip.creation_data = orig_clip.creation_data
            transition_clip.clip_in = orig_clip.clip_in
            transition_clip.clip_out = orig_clip.clip_out

            data = {"track":track,
                    "transition_clip":transition_clip,
                    "transition_index":clip_index}

            GLib.idle_add(self._do_edit, data)
        
        GLib.idle_add(dialogutils.dialog_destroy, self.dialog, None)
        self.dialog = None

    def _update_text_label(self, info_text):
        if self.dialog != None:    
            self.text_label.set_text(info_text)

    def _update_progressbar(self, render_fraction):
        if self.dialog != None:  
            self.progress_bar.set_fraction(render_fraction)
            pros = int(render_fraction * 100)
            self.progress_bar.set_text(str(pros) + "%")

    def _do_edit(self, data):
        action = edit.replace_centered_transition_action(data)
        action.do_edit()
            

class ReRenderRunnerThread(threading.Thread):
    
    def __init__(self, rerender_window):
        self.rerender_window = rerender_window
        
        threading.Thread.__init__(self)

    def run(self):
        self.running = True
        while self.running:
            self.rerender_window.render_next()
            
            item_render_ongoing = True
            while item_render_ongoing:
                time.sleep(0.33)
                
                self.rerender_window.update_fraction()
                
                if self.rerender_window.renderer.stopped == True:
                    item_render_ongoing = False
                
            self.rerender_window.show_full_fraction()
            
            self.rerender_window.item_render_complete()
            if self.rerender_window.all_items_done() == True:
                self.running = False
            else:
                time.sleep(0.33)

        self.rerender_window.exit_shutdown()


# ------------------------------------------------------------------ dialogs
def transition_edit_dialog(callback, transition_data):
    dialog = Gtk.Dialog(_("Add Transition"),  gui.editor_window.window,
                        Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        (_("Cancel"), Gtk.ResponseType.REJECT,
                        _("Apply"), Gtk.ResponseType.ACCEPT))

    alignment, type_combo, length_entry, encodings_cb, quality_cb, wipe_luma_combo_box, steal_check, encodings = panels.get_transition_panel(transition_data)
    widgets = (type_combo, length_entry, encodings_cb, quality_cb, wipe_luma_combo_box, steal_check, encodings)
    dialog.connect('response', callback, widgets, transition_data)
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.set_default_behaviour(dialog)
    dialog.show_all()
    
def _no_creation_data_dialog():
    primary_txt = _("Can't rerender this fade / transition.")
    secondary_txt = _("This fade / transition was created with Flowblade <= 1.14 and does not have the necessary data embedded.\nRerendering works with fades/transitions created with Flowblade >= 1.16.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

def _source_clips_not_found_dialog():
    primary_txt = _("Can't rerender this fade / transition.")
    secondary_txt = _("The clip/s used to create this fade / transition are no longer available on the timeline.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)