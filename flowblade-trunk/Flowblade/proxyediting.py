

import gtk
import mlt
import os
import threading
import time

import app
import appconsts
import dialogs
import dialogutils
import editorpersistance
import editorstate
import gui
import guiutils
import persistance
import renderconsumer
import sequence
import utils


manager_window = None
progress_window = None
runner_thread = None
load_thread = None

# These correspond with size selector on manager window
PROXY_SIZE_FULL = 0
PROXY_SIZE_HALF = 1
PROXY_SIZE_QUARTER = 2


class ProjectProxyEditingData:
    
    def __init__(self):
        self.proxy_mode = appconsts.USE_ORIGINAL_MEDIA
        self.create_rules = None # not impl.
        self.encoding = 0 # default is first found encoding
        self.size = 1 # default is half project size


class ProxyRenderRunnerThread(threading.Thread):
    def __init__(self, proxy_profile, files_to_render):
        threading.Thread.__init__(self)
        self.proxy_profile = proxy_profile
        self.files_to_render = files_to_render
        self.aborted = False

    def run(self):        
        items = 1
        global progress_window
        start = time.time()
        elapsed = 0
        for media_file in self.files_to_render:
            if self.aborted == True:
                break

            # Create render objects
            proxy_file_path = media_file.create_proxy_path()
            consumer = renderconsumer.get_render_consumer_for_encoding(
                                                        proxy_file_path,
                                                        self.proxy_profile, 
                                                        get_proxy_encoding())
            #consumer.set("vb", "1000k")
            consumer.set("rescale", "nearest")

            file_producer = mlt.Producer(self.proxy_profile, str(media_file.path))
            #seq = sequence.Sequence(self.proxy_profile)
            #seq.create_default_tracks()
            #track = seq.tracks[seq.first_video_index]
            #track.append(file_producer, 0, file_producer.get_length() - 1)
            
            # Create and launch render thread
            global render_thread 
            render_thread = renderconsumer.FileRenderPlayer(None, file_producer, consumer, 0, file_producer.get_length() - 1)
            render_thread.start()

            # Render view update loop
            self.thread_running = True
            self.aborted = False
            while self.thread_running:
                if self.aborted == True:
                    break
                render_fraction = render_thread.get_render_fraction()
                now = time.time()
                elapsed = now - start
                progress_window.update_render_progress(render_fraction, media_file.name, items, len(self.files_to_render), elapsed)
                
                if render_thread.producer.get_speed() == 0: # Rendering has reached end or been aborted
                    self.thread_running = False
                    progress_window.render_progress_bar.set_fraction(1.0)
                    media_file.add_proxy_file(proxy_file_path)
                else:
                    time.sleep(0.1)
    
            if not self.aborted:
                items = items + 1
                progress_window.update_render_progress(0, media_file.name, items, len(self.files_to_render), elapsed)
            else:
                render_thread.shutdown()
                break
            render_thread.shutdown()
        
        _proxy_render_stopped()

    def abort(self):
        render_thread.shutdown()
        self.aborted = True
        self.thread_running = False


class ProxyManagerDialog:
    def __init__(self):
        self.dialog = gtk.Dialog(_("Proxy Manager"), None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (_("Close Manager").encode('utf-8'), gtk.RESPONSE_CLOSE))

        # Encoding
        self.enc_select = gtk.combo_box_new_text()
        encodings = renderconsumer.get_proxy_encodings()
        if len(encodings) < 1: # no encoding options available, system does not have right codecs
            # display info
            pass
        for encoption in encodings:
            self.enc_select.append_text(encoption.name)
            
        current_enc = editorstate.PROJECT().proxy_data.encoding
        if current_enc >= len(encodings): # current encoding selection not available
            current_enc = 0
            editorstate.PROJECT().proxy_data.encoding = 0
        self.enc_select.set_active(current_enc)
        self.enc_select.connect("changed", 
                                lambda w,e: self.encoding_changed(w.get_active()), 
                                None)
                            
        self.size_select = gtk.combo_box_new_text()
        self.size_select.append_text("Project Size")
        self.size_select.append_text("Half Project Size")
        self.size_select.append_text("Quarter Project Size")
        self.size_select.set_active(editorstate.PROJECT().proxy_data.size)
        self.size_select.connect("changed", 
                                lambda w,e: self.size_changed(w.get_active()), 
                                None)
                                
        row_enc = gtk.HBox(False, 2)
        row_enc.pack_start(gtk.Label(), True, True, 0)
        row_enc.pack_start(self.enc_select, False, False, 0)
        row_enc.pack_start(self.size_select, False, False, 0)
        row_enc.pack_start(gtk.Label(), True, True, 0)
        
        vbox_enc = gtk.VBox(False, 2)
        vbox_enc.pack_start(row_enc, False, False, 0)
        vbox_enc.pack_start(guiutils.pad_label(8, 12), False, False, 0)
        
        panel_encoding = guiutils.get_named_frame("Proxy Encoding", vbox_enc)

        # Mode
        media_files = editorstate.PROJECT().media_files
        video_files = 0
        proxy_files = 0
        for k, media_file in media_files.iteritems():
            if media_file.type == appconsts.VIDEO:
                video_files = video_files + 1
                if media_file.has_proxy_file == True or media_file.is_proxy_file == True:
                    proxy_files = proxy_files + 1
                    
        proxy_status_label = gtk.Label("Proxy Stats:")
        proxy_status_value = gtk.Label(str(proxy_files) + " proxy file(s) for " + str(video_files) + " video file(s)")
        row_proxy_status = guiutils.get_two_column_box_right_pad(proxy_status_label, proxy_status_value, 150, 150)

        proxy_mode_label = gtk.Label("Current Proxy Mode:")
        if editorstate.PROJECT().proxy_data.proxy_mode == appconsts.USE_PROXY_MEDIA:
            mode_str = "Using Proxy Media"
        else:
            mode_str = "Using Original Media"
        proxy_mode_value = gtk.Label(mode_str)
        row_proxy_mode = guiutils.get_two_column_box_right_pad(proxy_mode_label, proxy_mode_value, 150, 150)

        convert_progress_bar = gtk.ProgressBar()
        convert_progress_bar.set_text("Press Button to Change Mode")
            
        self.use_button = gtk.Button(_("Use Proxy Media"))
        self.dont_use_button = gtk.Button(_("Use Original Media"))
        self.set_convert_buttons_state()
        self.use_button.connect("clicked", lambda w: _convert_to_proxy_project(dialog))

        c_box_2 = gtk.HBox(True, 8)
        c_box_2.pack_start(self.use_button, True, True, 0)
        c_box_2.pack_start(self.dont_use_button, True, True, 0)

        row2_onoff = gtk.HBox(False, 2)
        row2_onoff.pack_start(gtk.Label(), True, True, 0)
        row2_onoff.pack_start(c_box_2, False, False, 0)
        row2_onoff.pack_start(gtk.Label(), True, True, 0)

        vbox_onoff = gtk.VBox(False, 2)
        vbox_onoff.pack_start(row_proxy_status, False, False, 0)
        vbox_onoff.pack_start(row_proxy_mode, False, False, 0)
        vbox_onoff.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        vbox_onoff.pack_start(convert_progress_bar, False, False, 0)
        vbox_onoff.pack_start(row2_onoff, False, False, 0)
        
        panel_onoff = guiutils.get_named_frame("Project Proxy Mode", vbox_onoff)

        # Pane
        vbox = gtk.VBox(False, 2)
        vbox.pack_start(panel_encoding, False, False, 0)
        vbox.pack_start(panel_onoff, False, False, 0)

        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(12, 12, 12, 12)
        alignment.add(vbox)

        self.dialog.vbox.pack_start(alignment, True, True, 0)
        dialogutils.default_behaviour(self.dialog)
        self.dialog.connect('response', dialogutils.dialog_destroy)
        self.dialog.show_all()

    def set_convert_buttons_state(self):
        proxy_mode = editorstate.PROJECT().proxy_data.proxy_mode
        if proxy_mode == appconsts.USE_PROXY_MEDIA:
            self.use_button.set_sensitive(False)
            self.dont_use_button.set_sensitive(True)
        else:
            self.use_button.set_sensitive(True)
            self.dont_use_button.set_sensitive(False)

    def encoding_changed(self, enc_index):
        editorstate.PROJECT().proxy_data.encoding = enc_index

    def size_changed(self, size_index):
        editorstate.PROJECT().proxy_data.size = size_index

class ProxyRenderProgressDialog:
    def __init__(self):
        self.dialog = gtk.Dialog(_("Creating Proxy Files"),
                                 gui.editor_window.window,
                                 gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                 (_("Stop").encode('utf-8'), gtk.RESPONSE_REJECT))
        
        self.render_progress_bar = gtk.ProgressBar()
        self.render_progress_bar.set_text("0 %")
        prog_align = gtk.Alignment(0.5, 0.5, 1.0, 0.0)
        prog_align.set_padding(0, 0, 0, 0)
        prog_align.add(self.render_progress_bar)
        prog_align.set_size_request(550, 30)
        
        self.elapsed_value = gtk.Label()
        self.current_render_value = gtk.Label()
        self.items_value = gtk.Label()
        
        est_label = guiutils.get_right_justified_box([guiutils.bold_label("Elapsed:")])
        current_label = guiutils.get_right_justified_box([guiutils.bold_label("Current Media File:")])
        items_label = guiutils.get_right_justified_box([guiutils.bold_label("Rendering Item:")])
        
        est_label.set_size_request(250, 20)
        current_label.set_size_request(250, 20)
        items_label.set_size_request(250, 20)

        info_vbox = gtk.VBox(False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([est_label, self.elapsed_value]), False, False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([current_label, self.current_render_value]), False, False, 0)
        info_vbox.pack_start(guiutils.get_left_justified_box([items_label, self.items_value]), False, False, 0)

        progress_vbox = gtk.VBox(False, 2)
        progress_vbox.pack_start(info_vbox, False, False, 0)
        progress_vbox.pack_start(guiutils.get_pad_label(10, 8), False, False, 0)
        progress_vbox.pack_start(prog_align, False, False, 0)

        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(12, 12, 12, 12)
        alignment.add(progress_vbox)
        alignment.show_all()

        self.dialog.vbox.pack_start(alignment, True, True, 0)
        self.dialog.set_has_separator(False)
        self.dialog.connect('response', self.stop_pressed)
        self.dialog.show()

    def update_render_progress(self, fraction, media_file_name, current_item, items, elapsed):
        elapsed_str= "  " + utils.get_time_str_for_sec_float(elapsed)
        self.elapsed_value .set_text(elapsed_str)
        self.current_render_value.set_text(" " + media_file_name)
        self.items_value.set_text( " " + str(current_item) + "/" + str(items))
        self.render_progress_bar.set_fraction(fraction)
        self.render_progress_bar.set_text(str(int(fraction * 100)) + " %")

    def stop_pressed(self, dialog, response_id):
        global runner_thread
        runner_thread.abort()


def _get_proxies_dir():
    return editorpersistance.prefs.render_folder + "/proxies"

def _get_proxy_encoding():
    return renderconsumer.get_proxy_encodings()[0]

def _get_proxy_dimensions(project_profile):
    # Get new dimension that are about half of previous and diviseble by eight
    old_width_half = int(project_profile.width() / 2)
    old_height_half = int(project_profile.height() / 2)
    new_width = old_width_half - old_width_half % 8
    new_height = old_height_half - old_height_half % 8
    return (new_width, new_height)

def _get_proxy_profile(project_profile):
    new_width, new_height = _get_proxy_dimensions(project_profile)
    
    file_contents = "description=" + "proxy render profile" + "\n"
    file_contents += "frame_rate_num=" + str(project_profile.frame_rate_num()) + "\n"
    file_contents += "frame_rate_den=" + str(project_profile.frame_rate_den()) + "\n"
    file_contents += "width=" + str(new_width) + "\n"
    file_contents += "height=" + str(new_height) + "\n"
    file_contents += "progressive=1" + "\n"
    file_contents += "sample_aspect_num=" + str(project_profile.sample_aspect_num()) + "\n"
    file_contents += "sample_aspect_den=" + str(project_profile.sample_aspect_den()) + "\n"
    file_contents += "display_aspect_num=" + str(project_profile.display_aspect_num()) + "\n"
    file_contents += "display_aspect_den=" + str(project_profile.display_aspect_den()) + "\n"

    proxy_profile_path = utils.get_hidden_user_dir_path() + "temp_proxy_profile"
    profile_file = open(proxy_profile_path, "w")
    profile_file.write(file_contents)
    profile_file.close()
    
    proxy_profile = mlt.Profile(proxy_profile_path)
    return proxy_profile

def show_proxy_manager_dialog():
    global manager_window
    manager_window = ProxyManagerDialog()

def create_proxy_files_pressed(retry_from_render_folder_select=False):
    if editorpersistance.prefs.render_folder == None:
        if retry_from_render_folder_select == True:
            return
        dialogs.select_rendred_clips_dir(_create_proxy_render_folder_select_callback, gui.editor_window.window, editorpersistance.prefs.render_folder)
        return

    proxies_dir = _get_proxies_dir()
    if not os.path.exists(proxies_dir):
        os.mkdir(proxies_dir)

    media_file_widgets = gui.media_list_view.get_selected_media_objects()
 
    # render only files that dont have proxy files already
    files_to_render = []
    for w in media_file_widgets:
        f = w.media_file
        if f.has_proxy_file == True:
            if os.path.exists(f.proxy_file_path):
                continue
        files_to_render.append(f)

    proxy_profile = _get_proxy_profile(editorstate.PROJECT().profile)
    
    global progress_window, runner_thread
    progress_window = ProxyRenderProgressDialog()
    runner_thread = ProxyRenderRunnerThread(proxy_profile, files_to_render)
    runner_thread.start()

def _proxy_render_stopped():
    global progress_window, runner_thread
    progress_window.dialog.destroy()
    gui.media_list_view.widget.queue_draw()
    progress_window = None
    runner_thread = None

def _create_proxy_render_folder_select_callback(dialog, response_id, file_select):
    try:
        folder = file_select.get_filenames()[0]
    except:
        dialog.destroy()
        return

    dialog.destroy()
    if response_id == gtk.RESPONSE_YES:
        if folder ==  os.path.expanduser("~"):
            dialogs.rendered_clips_no_home_folder_dialog()
        else:
            editorpersistance.prefs.render_folder = folder
            editorpersistance.save()
            create_proxy_files_pressed(True)
        

# --------------------------------------------------------- converting to and from proxy projects
def _convert_to_proxy_project(dialog):
    dialog.destroy()
    editorstate.PROJECT().proxy_data.proxy_mode = appconsts.CONVERTING_TO_USE_PROXY_MEDIA
    conv_temp_project_path = utils.get_hidden_user_dir_path() + "proxy_conv.flb"
    print conv_temp_project_path
    persistance.save_project(editorstate.PROJECT(), conv_temp_project_path)
    global load_thread
    load_thread = ProxyProjectLoadThread(conv_temp_project_path)
    load_thread.start()



class ProxyProjectLoadThread(threading.Thread):

    def __init__(self, proxy_project_path):
        threading.Thread.__init__(self)
        self.proxy_project_path = proxy_project_path

    def run(self): 
        persistance.show_messages = False
        try:
            print "2"
            project = persistance.load_project(self.proxy_project_path, False)
            print "3"
            sequence.set_track_counts(project)
            print "4"
        except persistance.FileProducerNotFoundError as e:
            print "did not find file:", e
            
        print "5"
        app.stop_autosave()
        app.open_project(project)
        project.proxy_data.proxy_mode = appconsts.USE_PROXY_MEDIA
        app.start_autosave()
        print "6"
        global load_thread
        load_thread = None
        persistance.show_messages = True
