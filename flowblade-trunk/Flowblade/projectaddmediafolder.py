from gi.repository import Gtk, GObject, GLib, Gdk

import fnmatch
import os

import dialogutils
import gui
import guiutils
import editorpersistance
import projectaction
import utils

_add_media_window = None
_add_files_set = None

# ----------------------------------- open close
def show_add_media_folder_dialog():
    global _add_media_window
    _add_media_window = AddMediaWindow()

def _close_window():
    global _add_media_window
    _add_media_window.set_visible(False)
    _add_media_window.destroy()

def _close_clicked():
    _close_window()

# ------------------------------------- window
class AddMediaWindow(Gtk.Window):
    def __init__(self):
        GObject.GObject.__init__(self)
        self.set_modal(True)
        self.set_transient_for(gui.editor_window.window)
        self.set_title(_("Add Media From Folder"))
        self.connect("delete-event", lambda w, e:_close_window())
        
        file_chooser = Gtk.FileChooserButton(_("Select Folder"))
        file_chooser.set_size_request(250, 25)
        if ((editorpersistance.prefs.open_in_last_opended_media_dir == True)
            and (editorpersistance.prefs.last_opened_media_dir != None)):
            file_chooser.set_current_folder(editorpersistance.prefs.last_opened_media_dir)
        else:
            file_chooser.set_current_folder(os.path.expanduser("~") + "/")
        file_chooser.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.file_chooser = file_chooser
        row1 = guiutils.get_two_column_box(Gtk.Label(label=_("Add Media from Folder:")), file_chooser, 220)

        recursively_checkbox = Gtk.CheckButton()
        recursively_checkbox.set_active(False)
        recursively_label = Gtk.Label(label=_("Search subfolders"))
        self.recursively_checkbox = recursively_checkbox
        row3 = guiutils.get_checkbox_row_box(recursively_checkbox, recursively_label)

        action_select = Gtk.ComboBoxText()
        action_select.append_text(_("All Media Files"))
        action_select.append_text(_("Video Files"))
        action_select.append_text(_("Audio Files"))
        action_select.append_text(_("Image Files"))
        action_select.set_active(0)
        self.action_select = action_select
        action_label = Gtk.Label(label=_("File types to add:"))
        row4 = guiutils.get_two_column_box(action_label, action_select, 220)

        use_extension_checkbox = Gtk.CheckButton()
        use_extension_checkbox.set_active(False)
        self.use_extension_checkbox = use_extension_checkbox
        use_extension_label = Gtk.Label(label=_("Filter by file extension"))
        row5 = guiutils.get_checkbox_row_box(use_extension_checkbox, use_extension_label)

        extension_entry = Gtk.Entry.new()
        extension_entry.set_max_width_chars(6)
        extension_entry_box = Gtk.HBox(False, 0)
        extension_entry_box.pack_start(extension_entry, False, False, 0)
        extension_entry_box.pack_start(guiutils.pad_label(200,10), True, True, 0)
        self.extension_entry = extension_entry
        extension_label = Gtk.Label(label=_("File extension:"))
        extension_entry.set_sensitive(False)
        extension_label.set_sensitive(False)
        row6 = guiutils.get_two_column_box(extension_label, extension_entry_box, 100)

        self.files_view = Gtk.TextView()
        self.files_view.set_sensitive(False)
        self.files_view.set_pixels_above_lines(2)
        self.files_view.set_left_margin(2)
        self.files_view.set_sensitive(False)
        self.files_view.set_editable(False)

        text_buffer = Gtk.TextBuffer()
        text_buffer.set_text(_("No files loaded."))
        self.files_view.set_buffer(text_buffer)
        self.files_view.set_sensitive(False)
        
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.add(self.files_view)
        sw.set_size_request(500, 200) # 500 here sets window width.

        scroll_frame = Gtk.Frame()
        scroll_frame.add(sw)

        load_button = Gtk.Button(_("Load Add Files Set"))
        load_button.connect("clicked", lambda w: _load_add_files_clicked())
        self.load_info = Gtk.Label(_("Files to load: ") + _("Not Set"))
        row9 = Gtk.HBox(False, 0)
        row9.pack_start(self.load_info, False, False, 0)
        row9.pack_start(Gtk.Label(), True, True, 0)
        row9.pack_start(load_button, False, False, 0)
        guiutils.set_margins(row9, 4, 24, 0, 0)
        
        close_button = Gtk.Button(_("Close"))
        close_button.connect("clicked", lambda w: _close_clicked())
        self.add_button = Gtk.Button(_("Add Media"))
        self.add_button.connect("clicked", lambda w: _do_folder_media_import())
        self.add_button.set_sensitive(False)
        self.load_info_2 = Gtk.Label() 
        row8 = Gtk.HBox(False, 0)
        row8.pack_start(self.load_info_2, False, False, 0)
        row8.pack_start(Gtk.Label(), True, True, 0)
        row8.pack_start(close_button, False, False, 0)
        row8.pack_start(self.add_button, False, False, 0)
        
        maximum_select = Gtk.ComboBoxText()
        maximum_select.append_text(_("29"))
        maximum_select.append_text(_("49"))
        maximum_select.append_text(_("99"))
        maximum_select.append_text(_("199"))
        maximum_select.set_active(0)
        self.maximum_select = maximum_select
        maximum_label = Gtk.Label(label=_("Max. number of files to import:"))
        row7 = guiutils.get_two_column_box(maximum_label, maximum_select, 220)
        guiutils.set_margins(row7, 0, 12, 0, 0)
        
        activateble_widgets = (action_label, action_select, extension_label, extension_entry)
        use_extension_checkbox.connect("toggled", _use_extension_toggled, activateble_widgets)
        
        vbox = Gtk.VBox(False, 2)
        vbox.pack_start(row1, False, False, 0)
        vbox.pack_start(guiutils.pad_label(12, 24), False, False, 0)
        vbox.pack_start(row3, False, False, 0)
        vbox.pack_start(guiutils.pad_label(12, 8), False, False, 0)
        vbox.pack_start(row4, False, False, 0)
        vbox.pack_start(row5, False, False, 0)
        vbox.pack_start(row6, False, False, 0)
        vbox.pack_start(row7, False, False, 0)
        vbox.pack_start(scroll_frame, False, False, 0)
        vbox.pack_start(row9, False, False, 0)
        vbox.pack_start(row8, False, False, 0)
        
        alignment = guiutils.set_margins(vbox, 8, 8, 12, 12)

        self.add(alignment)
        self.set_position(Gtk.WindowPosition.CENTER)  
        self.show_all()

# --------------------------------------------------- functionality 
def _load_add_files_clicked():
    _add_media_window.load_info.set_text(_("Searching..."))
    Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, _do_add_files_search, None)

def _do_add_files_search(data):
    add_folder = _add_media_window.file_chooser.get_filenames()[0]
    load_action = _add_media_window.action_select.get_active()
    search_recursively = _add_media_window.recursively_checkbox.get_active()
    use_extension = _add_media_window.use_extension_checkbox.get_active()
    user_extensions = _add_media_window.extension_entry.get_text()
    maximum_file_option = _add_media_window.maximum_select.get_active()

    if add_folder == None:
        return
    
    if search_recursively == True:
        candidate_files = []
        for root, dirnames, filenames in os.walk(add_folder):
            for filename in filenames:
                candidate_files.append(os.path.join(root, filename))
    else:
        candidate_files = []
        for filename in os.listdir(add_folder):
            candidate_files.append(add_folder + "/" + filename)

    if use_extension == False:
        if load_action == 0: # "All Files", see dialogs.py
            filtered_files = candidate_files
        else:
            filtered_files = []
            for cand_file in candidate_files:
                file_type = utils.get_file_type(cand_file)
                if load_action == 1 and file_type == "video": # 1 = "Video Files", see dialogs.py
                    filtered_files.append(cand_file)
                elif load_action == 2 and file_type == "audio": # 2 = "Audio Files", see dialogs.py
                    filtered_files.append(cand_file)
                elif load_action == 3 and file_type == "image": # 3 = "Image Files", see dialogs.py
                    filtered_files.append(cand_file)
    else:
        # Try to accept spaces, commas and periods between extensions.
        stage1 = user_extensions.replace(",", " ")
        stage2 = stage1.replace(".", " ")
        exts = stage2.split()

        filtered_files = []
        for ext in exts:
            for cand_file in candidate_files:
                if fnmatch.fnmatch(cand_file, "*." + ext):
                    filtered_files.append(cand_file)
    
    # This is recursive, we need upper limit always
    max_files = 29
    if maximum_file_option == 1:
        max_files = 49 # see dialogs.py 
    elif maximum_file_option == 2:
        max_files = 99 # see dialogs.py
    elif maximum_file_option == 3:
        max_files = 199 # see dialogs.py
        
    filtered_amount = len(filtered_files)
    if filtered_amount > max_files:
        filtered_files = filtered_files[0:max_files]
    
    global _add_files_set
    _add_files_set = filtered_files

    files_text = ""
    for f in filtered_files:
        files_text += f + "\n"
     
    text_buffer = Gtk.TextBuffer()
    text_buffer.set_text(files_text)
    _add_media_window.files_view.set_buffer(text_buffer)
    
    info_text = _("Files to load: ") + str(len(filtered_files))
    _add_media_window.load_info.set_text(info_text)

    if filtered_amount > max_files:
        _add_media_window.load_info_2.set_text(str(filtered_amount - max_files) + " / " + str(filtered_amount) + _(" of found files will not be loaded."))       
    else:
        _add_media_window.load_info_2.set_text("")

    if len(filtered_files) > 0:
        _add_media_window.add_button.set_sensitive(True)
    else:
        _add_files_set = None
        _add_media_window.add_button.set_sensitive(False)
    
def _use_extension_toggled(checkbutton, widgets):
    action_label, action_select, extension_label, extension_entry = widgets
    if checkbutton.get_active() == True:
        action_label.set_sensitive(False)
        action_select.set_sensitive(False)
        extension_label.set_sensitive(True)
        extension_entry.set_sensitive(True)
    else:
        action_label.set_sensitive(True)
        action_select.set_sensitive(True)
        extension_label.set_sensitive(False)
        extension_entry.set_sensitive(False)

def _do_folder_media_import():
    _close_window()
    Gdk.threads_add_idle(GLib.PRIORITY_DEFAULT_IDLE, _do_folder_media_import_on_idle, None) # Let's kill window first

def _do_folder_media_import_on_idle(data):
    if _add_files_set != None:
        projectaction.open_file_names(_add_files_set)
