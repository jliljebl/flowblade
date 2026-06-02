"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2026 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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

from gi.repository import Gtk, GLib

import hashlib
import os
import threading
import time

import appconsts
import dialogutils
import edit
import editorstate
from editorstate import current_sequence
from editorstate import PROJECT
import gui
import guiutils
import mlttransitions
import panels
import renderconsumer
import respaths
import userfolders


def show_no_handles_dialog(from_req, from_handle, to_req, to_handle, length):
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

    label1 = Gtk.Label(label=_("Current situation, not enough media overlap:"))
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
        self.write_file = folder + file_name + file_ext
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

    alignment, type_combo, length_entry, encodings_cb, quality_cb, wipe_luma_combo_box, encodings = panels.get_transition_panel(transition_data)
    widgets = (type_combo, length_entry, encodings_cb, quality_cb, wipe_luma_combo_box, encodings)
    dialog.connect('response', callback, widgets, transition_data)
    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.set_outer_margins(dialog.vbox)
    dialogutils.set_default_behaviour(dialog)
    dialog.show_all()

def no_creation_data_dialog():
    primary_txt = _("Can't rerender this fade / transition.")
    secondary_txt = _("This fade / transition was created with Flowblade <= 1.14 and does not have the necessary data embedded.\nRerendering works with fades/transitions created with Flowblade >= 1.16.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)

def source_clips_not_found_dialog():
    primary_txt = _("Can't rerender this fade / transition.")
    secondary_txt = _("The clip/s used to create this fade / transition are no longer available on the timeline.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)
    
def no_audio_tracks_mixing_info():
    primary_txt = _("Rendered transitions cannot be used on audio tracks.")
    secondary_txt = _("This feature only works on video tracks.")
    dialogutils.info_message(primary_txt, secondary_txt, gui.editor_window.window)


