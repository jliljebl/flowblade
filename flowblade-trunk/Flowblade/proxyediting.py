

import gtk
import mlt
import os
import threading
import time

import dialogs
import dialogutils
import editorpersistance
import editorstate
import gui
import guiutils
import renderconsumer
import sequence
import utils

# proxy mode
USE_ORIGINAL_MEDIA = 0
USE_PROXY_MEDIA = 1

# create mode
PROXY_CREATE_MANUAL = 0
PROXY_CREATE_ALL_VIDEO_ON_OPEN = 1

progress_window = None
#render_queue = None
runner_thread = None

class ProjectProxyEditingData:
    
    def __init__(self):
        self.proxy_mode = USE_ORIGINAL_MEDIA
        self.create_mode = PROXY_CREATE_MANUAL
        self.create_rules = None # not impl.
        self.encoding = 0 # not impl.

        # List of (media file id,original media path,proxy file path) tuples 
        self.proxy_files = []

class ProxyRenderRunnerThread(threading.Thread):
    def __init__(self, proxy_profile, files_to_render):
        threading.Thread.__init__(self)
        self.proxy_profile = proxy_profile
        self.files_to_render = files_to_render
        self.aborted = False

    def run(self):        
        print "ee"
        print len(self.files_to_render)
        items = 1
        global progress_window
        for media_file in self.files_to_render:
            if self.aborted == True:
                break

            # Create render objects
            proxy_file_path = media_file.create_proxy_path()
            consumer = renderconsumer.get_render_consumer_for_encoding(
                                                        proxy_file_path,
                                                        self.proxy_profile, 
                                                        renderconsumer.get_proxy_encoding())

            file_producer = mlt.Producer(self.proxy_profile, str(media_file.path))
            seq = sequence.Sequence(self.proxy_profile)
            seq.create_default_tracks()
            track = seq.tracks[seq.first_video_index]
            track.append(file_producer, 0, file_producer.get_length() - 1)
            
            # Create and launch render thread
            global render_thread 
            render_thread = renderconsumer.FileRenderPlayer(None, seq.tractor, consumer, 0, file_producer.get_length() - 1)
            render_thread.start()

            # Render view update loop
            self.thread_running = True
            self.aborted = False
            while self.thread_running:
                if self.aborted == True:
                    break        
                render_fraction = render_thread.get_render_fraction()
                progress_window.update_render_progress(render_fraction, media_file.name, items, len(self.files_to_render))
                
                if render_thread.producer.get_speed() == 0: # Rendering has reached end or been aborted
                    self.thread_running = False
                    progress_window.render_progress_bar.set_fraction(1.0)
                    #render_item.render_completed()
                else:
                    time.sleep(0.1)
    
            if not self.aborted:
                items = items + 1
                progress_window.update_render_progress(0, media_file.name, items, len(self.files_to_render))
            else:
                if render_item != None:
                    render_item.render_aborted()
                    break
            render_thread.shutdown()
        

        progress_window.render_queue_stopped()

    def abort(self):
        render_thread.shutdown()
        self.aborted = True
        self.thread_running = False

class ProxyRenderProgressDialog:
    def __init__(self):
        self.dialog = gtk.Dialog(_("Proxy Render"),
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
        #self.dialog.connect('response', callback)
        self.dialog.show()

    def update_render_progress(self, fraction, media_file_name, current_item, items):
        self.current_render_value.set_text(" " + media_file_name)
        self.items_value.set_text( " " + str(current_item) + "/" + str(items))
        self.render_progress_bar.set_fraction(fraction)
        self.render_progress_bar.set_text(str(int(fraction * 100)) + " %")
        
def _get_proxies_dir():
    return editorpersistance.prefs.render_folder + "/proxies"
    
def _get_proxy_profile(project_profile):
    # Get new dimension that are about half of previous and diviseble by eight
    old_width_half = int(project_profile.width() / 2)
    old_height_half = int(project_profile.height() / 2)
    new_width = old_width_half - old_width_half % 8
    new_height = old_height_half - old_height_half % 8
    print "proxy dim:", new_width, new_height
    
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
    proxy_create_texts = [_("Manually Only"),_("All Video On Open")]
    dialog = gtk.Dialog(_("Proxy Manager"), None,
                        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                        (_("Close Manager").encode('utf-8'), gtk.RESPONSE_CLOSE))

    proxy_status_value = gtk.Label("There are 12 proxy file(s) for 32 video file(s)")
    row_proxy_status = guiutils.get_left_justified_box([proxy_status_value, gtk.Label()])
    
    # Create
    create_label = gtk.Label(_("Proxy Creation:") + " ")
    create_select = gtk.combo_box_new_text()
    create_select.append_text(proxy_create_texts[PROXY_CREATE_MANUAL])
    create_select.append_text(proxy_create_texts[PROXY_CREATE_ALL_VIDEO_ON_OPEN])
    create_select.set_active(0) 

    row_create1 = guiutils.get_left_justified_box([create_label, create_select])

    create_all_button = gtk.Button(_("Create Proxy Media For All Video"))
    delete_all_button = gtk.Button(_("Delete All Proxy Media For Project"))

    c_box = gtk.HBox(True, 8)
    c_box.pack_start(create_all_button, True, True, 0)
    c_box.pack_start(delete_all_button, True, True, 0)

    row_create2 = gtk.HBox(False, 2)
    row_create2.pack_start(gtk.Label(), True, True, 0)
    row_create2.pack_start(c_box, False, False, 0)
    row_create2.pack_start(gtk.Label(), True, True, 0)

    vbox_create = gtk.VBox(False, 2)
    vbox_create.pack_start(row_proxy_status, False, False, 0)
    vbox_create.pack_start(guiutils.pad_label(8, 4), False, False, 0)
    vbox_create.pack_start(row_create1, False, False, 0)
    vbox_create.pack_start(guiutils.pad_label(8, 12), False, False, 0)
    vbox_create.pack_start(row_create2, False, False, 0)
    vbox_create.pack_start(guiutils.pad_label(8, 12), False, False, 0)

    panel_create = guiutils.get_named_frame(_("Proxy Media"), vbox_create)

    # Use
    proxy_status_label = gtk.Label("Proxy Media Status:")

    use_button = gtk.Button(_("Use Proxy Media"))
    dont_use_button = gtk.Button(_("Use Original Media"))

    c_box_2 = gtk.HBox(True, 8)
    c_box_2.pack_start(use_button, True, True, 0)
    c_box_2.pack_start(dont_use_button, True, True, 0)

    row2_onoff = gtk.HBox(False, 2)
    row2_onoff.pack_start(gtk.Label(), True, True, 0)
    row2_onoff.pack_start(c_box_2, False, False, 0)
    row2_onoff.pack_start(gtk.Label(), True, True, 0)
    row2_onoff.set_size_request(470, 30)

    vbox_onoff = gtk.VBox(False, 2)
    vbox_onoff.pack_start(guiutils.pad_label(12, 4), False, False, 0)
    vbox_onoff.pack_start(row2_onoff, False, False, 0)
    
    panel_onoff = guiutils.get_named_frame("Project Proxy Mode", vbox_onoff)

    # Pane
    vbox = gtk.VBox(False, 2)
    vbox.pack_start(panel_create, False, False, 0)
    vbox.pack_start(panel_onoff, False, False, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.default_behaviour(dialog)
    dialog.connect('response', dialogutils.dialog_destroy)
    dialog.show_all()

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
        #if f.has_proxy_file == True:
        #    if os.path.exists(f.proxy_file_path):
        #        continue
        files_to_render.append(f)

    proxy_profile = _get_proxy_profile(editorstate.PROJECT().profile)
    
    global progress_window, runner_thread
    progress_window = ProxyRenderProgressDialog()
    runner_thread = ProxyRenderRunnerThread(proxy_profile, files_to_render)
    runner_thread.start()

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
        

        
