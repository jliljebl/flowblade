

import gtk
import os
import threading

import dialogs
import dialogutils
import editorpersistance
import editorstate
import gui
import guiutils
import renderconsumer

# proxy mode
USE_ORIGINAL_MEDIA = 0
USE_PROXY_MEDIA = 1

# create mode
PROXY_CREATE_MANUAL = 0
PROXY_CREATE_ALL_VIDEO_ON_OPEN = 1

progress_window = None

class ProjectProxyEditingData:
    
    def __init__(self):
        self.proxy_mode = USE_ORIGINAL_MEDIA
        self.create_mode = PROXY_CREATE_MANUAL
        self.create_rules = None # not impl.
        self.encoding = 0 # not impl.

        # List of (media file id,original media path,proxy file path) tuples 
        self.proxy_files = []

class ProxyRenderRunnerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    
    def run(self):        

        items = 0
        global render_queue, progress_window
        for render_item in render_queue:
            if self.aborted == False:
                break
            
            current_render_time = 0

            # Create render objects
            """
            consumer = renderconsumer.get_mlt_render_consumer(render_item.render_path, 
                                                              project.profile,
                                                              render_item.args_vals_list)
            """
            
            # Create and launch render thread
            global render_thread 
            render_thread = renderconsumer.FileRenderPlayer(None, producer, consumer, start_frame, end_frame) # None == file name not needed this time when using FileRenderPlayer because callsite keeps track of things
            render_thread.start()

            self.thread_running = True
            self.aborted = False
            while self.thread_running:
                if self.aborted == True:
                    break        
                render_fraction = render_thread.get_render_fraction()
                progress_window.update_render_progress(render_fraction, items, len(render_queue))
                
                if render_thread.producer.get_speed() == 0: # Rendering has reached end or been aborted
                    self.thread_running = False
                    progress_window.render_progress_bar.set_fraction(1.0)
                    #render_item.render_completed()
                else:
                    time.sleep(0.1)
            if not self.aborted:
                items = items + 1
                progress_window.update_render_progress(0, items, len(render_queue))
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

def _get_proxies_dir():
    return editorpersistance.prefs.render_folder + "/proxies"

def create_proxy_files_pressed(retry_from_render_folder_select=False):
    if editorpersistance.prefs.render_folder == None:
        if retry_from_render_folder_select == True:
            return
        dialogs.select_rendred_clips_dir(_create_proxy_render_folder_select_callback, gui.editor_window.window, editorpersistance.prefs.render_folder)
        return

    proxies_dir = _get_proxies_dir()
    if not os.path.exists(proxies_dir):
        os.mkdir(proxies_dir)
    
    global progress_window
    progress_window = ProxyRenderProgressDialog()

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
        

        
