import gtk
import pango

import guiutils


def display_linker():
    window = MediaLinkerWindow()


class MediaLinkerWindow(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)

        load_button = gtk.Button(_("Load Project For Relinking"))
        project_label = gtk.Label(_("<no project loaded>"))
        
        project_row = gtk.HBox(False, 2)
        project_row.pack_start(load_button, False, False, 0)
        project_row.pack_start(guiutils.pad_label(4, 12), False, False, 0)
        project_row.pack_start(project_label, False, False, 0)
        project_row.pack_start(gtk.Label(), True, True, 0)

        relink_list = MediaRelinkListView()

        find_button = gtk.Button(_("Set Asset Relink"))
        delete_button = gtk.Button(_("Delete Asset Relink"))
        auto_locate_check = gtk.CheckButton()
        auto_label = gtk.Label(_("Autorelink other assests"))
        working_check = gtk.CheckButton()
        working_label = gtk.Label(_("Display Working Assests"))

        buttons_row = gtk.HBox(False, 2)
        buttons_row.pack_start(working_check, False, False, 0)
        buttons_row.pack_start(working_label, False, False, 0)
        buttons_row.pack_start(gtk.Label(), True, True, 0)
        buttons_row.pack_start(delete_button, False, False, 0)
        buttons_row.pack_start(guiutils.pad_label(12, 12), False, False, 0)
        buttons_row.pack_start(auto_locate_check, False, False, 0)
        buttons_row.pack_start(auto_label, False, False, 0)
        buttons_row.pack_start(guiutils.pad_label(4, 4), False, False, 0)
        buttons_row.pack_start(find_button, False, False, 0)

        save_button = gtk.Button(_("Overwrite With Relinks"))
        cancel_button = gtk.Button(_("Cancel"))
        dialog_buttons_box = gtk.HBox(True, 2)
        dialog_buttons_box.pack_start(cancel_button, True, True, 0)
        dialog_buttons_box.pack_start(save_button, False, False, 0)
        
        dialog_buttons_row = gtk.HBox(False, 2)
        dialog_buttons_row.pack_start(gtk.Label(), True, True, 0)
        dialog_buttons_row.pack_start(dialog_buttons_box, False, False, 0)

        pane = gtk.VBox(False, 2)
        pane.pack_start(project_row, False, False, 0)
        pane.pack_start(guiutils.pad_label(24, 12), False, False, 0)
        pane.pack_start(relink_list, False, False, 0)
        pane.pack_start(buttons_row, False, False, 0)
        pane.pack_start(guiutils.pad_label(24, 24), False, False, 0)
        pane.pack_start(dialog_buttons_row, False, False, 0)
        
        align = gtk.Alignment()
        align.set_padding(12, 12, 12, 12)
        align.add(pane)

        # Set pane and show window
        self.add(align)
        self.set_title(_("Media Relinker"))
        self.show_all()
        self.set_resizable(False)
        self.set_keep_above(True) # Perhaps configurable later


class MediaRelinkListView(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)
        
       # Datamodel: icon, text, text
        self.storemodel = gtk.ListStore(str, str)
 
        # Scroll container
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # View
        self.treeview = gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(True)
        tree_sel = self.treeview.get_selection()

        # Column views
        self.text_col_1 = gtk.TreeViewColumn("text1")
        self.text_col_1.set_title(_("Missing Asset Path"))
        self.text_col_2 = gtk.TreeViewColumn("text2")
        self.text_col_2.set_title(_("Asset Relink Path"))
        
        # Cell renderers
        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_START)

        self.text_rend_2 = gtk.CellRendererText()
        self.text_rend_2.set_property("ellipsize", pango.ELLIPSIZE_START)
        self.text_rend_2.set_property("yalign", 0.0)

        # Build column views
        self.text_col_1.set_expand(True)
        self.text_col_1.pack_start(self.text_rend_1)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 0)
    
        self.text_col_2.set_expand(True)
        self.text_col_2.pack_start(self.text_rend_2)
        self.text_col_2.add_attribute(self.text_rend_2, "text", 1)

        # Add column views to view
        self.treeview.append_column(self.text_col_1)
        self.treeview.append_column(self.text_col_2)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
        self.scroll.show_all()
        self.set_size_request(1000, 400)

    def fill_data_model(self):
        """
        self.storemodel.clear()
        star_icon_path = respaths.IMAGE_PATH + "star.png"
        no_star_icon_path = respaths.IMAGE_PATH + "star_not_active.png"

        log_events = get_current_filtered_events()
        for log_event in log_events:
            if log_event.starred == True:
                icon = gtk.gdk.pixbuf_new_from_file(star_icon_path)
            else:
                icon =  gtk.gdk.pixbuf_new_from_file(no_star_icon_path)
            row_data = [icon, 
                        log_event.comment,
                        log_event.name,
                        log_event.get_mark_in_str(),
                        log_event.get_mark_out_str(),
                        log_event.get_date_str()]
            self.storemodel.append(row_data)
        """
        self.scroll.queue_draw()

    def get_selected_rows_list(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return rows
