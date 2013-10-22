

import gtk

import dialogutils
import editorstate
import guiutils

PROXY_CREATE_MANUAL = 0
PROXY_CREATE_ALL_VIDEO_ON_OPEN = 1
proxy_create_texts = None

def show_proxy_manager_dialog():
    global proxy_create_texts
    proxy_create_texts = [_("Manually Only"),_("All Video On Open")]
    dialog = gtk.Dialog(_("Sequence Watermark"), None,
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
    #vbox_onoff.pack_start(row1_onoff, False, False, 0)
    vbox_onoff.pack_start(guiutils.pad_label(12, 4), False, False, 0)
    vbox_onoff.pack_start(row2_onoff, False, False, 0)
    
    panel_onoff = guiutils.get_named_frame("Project Proxy Mode", vbox_onoff)

    #widgets = (add_button, remove_button, file_path_value_label)
    #add_button.connect("clicked", add_callback, widget s)
    #remove_button.connect("clicked", remove_callback, widgets)

    # Pane
    vbox = gtk.VBox(False, 2)
    #vbox.pack_start(row2, False, False, 0)
    #vbox.pack_start(guiutils.pad_label(12, 8), False, False, 0)
    vbox.pack_start(panel_create, False, False, 0)
    vbox.pack_start(panel_onoff, False, False, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(12, 12, 12, 12)
    alignment.add(vbox)

    dialog.vbox.pack_start(alignment, True, True, 0)
    dialogutils.default_behaviour(dialog)
    dialog.connect('response', dialogutils.dialog_destroy)
    dialog.show_all()


