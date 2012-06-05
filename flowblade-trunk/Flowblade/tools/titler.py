

import gtk
import pango
import pangocairo

from editorstate import PLAYER
import utils
import guiutils
import vieweditor
import vieweditorlayer

_titler = None

def show_titler():
    global _titler
    _titler = Titler()

class Titler(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_title("Titler")
        
        self.active_layout = PangoTextLayout()
        self.view_editor = vieweditor.ViewEditor(PLAYER().profile)
        edit_layer = vieweditorlayer.TextEditLayer(self.view_editor, self.active_layout)
        self.view_editor.edit_layers.append(edit_layer)
        self.view_editor.active_layer = edit_layer

        add_b = gtk.Button(_("Add"))
        del_b = gtk.Button(_("Delete"))
        add_b.connect("clicked", self._add_layer_pressed, None)
        del_b.connect("clicked", self._del_player_pressed, None)
        add_del_box = gtk.HBox()
        add_del_box = gtk.HBox(True,1)
        add_del_box.pack_start(add_b)
        add_del_box.pack_start(del_b)
        
        self.layer_list = TextLayerListView()
        self.layer_list.set_size_request(300, 100)
    
        self.text_view = gtk.TextView()
        self.text_view.set_pixels_above_lines(2)
        self.text_view.set_left_margin(2)
        self.text_view.get_buffer().connect("changed", self._edit_value_changed)

        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.sw.add(self.text_view)
        self.sw.set_size_request(300, 150)

        scroll_frame = gtk.Frame()
        scroll_frame.add(self.sw)
        
        font_map = pangocairo.cairo_font_map_get_default()
        unsorted_families = font_map.list_families()
        self.font_families = sorted(unsorted_families, key=lambda family: family.get_name())

        self.font_select = self._create_font_combo()
        self.font_select.connect("changed", self._edit_value_changed)
        self.font_face_box = gtk.HBox()
        self.font_face_bin = gtk.HBox() # we're using it as bin
        self.font_face_bin.add(self.font_face_box)
        self._fill_font_face_box()

        self.left_align = gtk.RadioButton()
        self.center_align = gtk.RadioButton(self.left_align)
        self.right_align = gtk.RadioButton(self.left_align)
        left_icon = gtk.image_new_from_stock(gtk.STOCK_JUSTIFY_LEFT, 
                                       gtk.ICON_SIZE_BUTTON)
        center_icon = gtk.image_new_from_stock(gtk.STOCK_JUSTIFY_CENTER, 
                                       gtk.ICON_SIZE_BUTTON)
        right_icon = gtk.image_new_from_stock(gtk.STOCK_JUSTIFY_RIGHT, 
                                       gtk.ICON_SIZE_BUTTON)
        self.left_align.set_image(left_icon)
        self.center_align.set_image(center_icon)
        self.right_align.set_image(right_icon)
        self.left_align.set_mode(False)
        self.center_align.set_mode(False)
        self.right_align.set_mode(False)

        self.color_button = gtk.ColorButton()
        self.color_button.connect("color-set", self._edit_value_changed)

        buttons_box = gtk.HBox()
        buttons_box.pack_start(self.left_align, False, False, 0)
        buttons_box.pack_start(self.center_align, False, False, 0)
        buttons_box.pack_start(self.right_align, False, False, 0)
        buttons_box.pack_start(self.color_button, False, False, 0)
        buttons_box.pack_start(gtk.Label(), True, True, 0)

        adj = gtk.Adjustment(float(0), float(1), float(3000), float(1))
        self.x_pos_spin = gtk.SpinButton(adj) 
        adj = gtk.Adjustment(float(0), float(1), float(3000), float(1))
        self.y_pos_spin = gtk.SpinButton(adj) 
        adj = gtk.Adjustment(float(0), float(1), float(3000), float(1))
        self.rotation_spin = gtk.SpinButton(adj) 

        positions_box = gtk.HBox()
        positions_box.pack_start(gtk.Label("X:"), False, False, 0)
        positions_box.pack_start(self.x_pos_spin, False, False, 0)
        positions_box.pack_start(gtk.Label("Y:"), False, False, 0)
        positions_box.pack_start(self.y_pos_spin, False, False, 0)
        positions_box.pack_start(gtk.Label(_("Rot:")), False, False, 0)
        positions_box.pack_start(self.rotation_spin, False, False, 0)

        controls_panel_1 = gtk.VBox()
        controls_panel_1.pack_start(add_del_box, False, False, 0)
        controls_panel_1.pack_start(self.layer_list, False, False, 0)

        controls_panel_2 = gtk.VBox()
        controls_panel_2.pack_start(scroll_frame, False, False, 0)
        controls_panel_2.pack_start(self.font_select, False, False, 0)
        controls_panel_2.pack_start(self.font_face_bin, False, False, 0)
        controls_panel_2.pack_start(buttons_box, False, False, 0)
        controls_panel_2.pack_start(positions_box, False, False, 0)
        
        controls_panel = gtk.VBox()
        controls_panel.pack_start(guiutils.get_named_frame(_("Layers"),controls_panel_1), False, False, 0)
        controls_panel.pack_start(guiutils.get_named_frame(_("Layer Properties"),controls_panel_2), False, False, 0)
        controls_panel.pack_start(gtk.Label(), True, True, 0)

        editor_row = gtk.HBox()
        editor_row.pack_start(controls_panel, False, False, 0)
        editor_row.pack_start(self.view_editor, False, False, 0)

        display_current_frame = gtk.Button("Load current frame")
        save_label = gtk.Label("Open Graphic In Bin")
        self.open_in_current_check = gtk.CheckButton()

        editor_buttons_row_upper = gtk.HBox()
        editor_buttons_row_upper.pack_start(gtk.Label(), True, True, 0)
        editor_buttons_row_upper.pack_start(display_current_frame, False, False, 0)
        editor_buttons_row_upper.pack_start(save_label, False, False, 0)
        editor_buttons_row_upper.pack_start(self.open_in_current_check , False, False, 0)

        exit_b = gtk.Button("Exit")
        save_titles_b = gtk.Button("Save Title")

        editor_buttons_row = gtk.HBox()
        editor_buttons_row.pack_start(gtk.Label(), True, True, 0)
        editor_buttons_row.pack_start(save_titles_b, False, False, 0)
        editor_buttons_row.pack_start(exit_b, False, False, 0)

        titler_pane = gtk.VBox()
        titler_pane.pack_start(editor_row, False, False, 0)
        titler_pane.pack_start(editor_buttons_row_upper, False, False, 0)
        titler_pane.pack_start(editor_buttons_row, False, False, 0)

        alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        alignment.set_padding(8,8, 8, 8)
        alignment.add(titler_pane)
    
        self.add(alignment)
        self.show_all()

    def _create_font_combo(self):
        combo = gtk.combo_box_new_text()
        for family in self.font_families:
            combo.append_text(family.get_name())
        combo.set_active(0)
        return combo

    def _fill_font_face_box(self):
        current_family = self.font_families[self.font_select.get_active()]

        faces = current_family.list_faces()
        self.face_combo = gtk.combo_box_new_text()
        self.faces = []
        for face in faces:
            self.face_combo.append_text(face.get_face_name())
            self.faces.append(face.get_face_name())
        self.face_combo.set_active(0)
        self.face_combo.connect("changed", self._edit_value_changed)
        adj = gtk.Adjustment(float(18), float(1), float(300), float(1))
        self.size_spin = gtk.SpinButton(adj)
        self.size_spin.connect("changed", self._edit_value_changed)
        self.size_spin.connect("activate", self._edit_value_changed)

        new_box = gtk.HBox()
        new_box.pack_start(self.face_combo, False, False, 0)
        new_box.pack_start(self.size_spin, False, False, 0)

        self.font_face_bin.remove(self.font_face_box)
        self.font_face_box = new_box
        self.font_face_bin.add(self.font_face_box)

    def show_current_frame(self):
        rgbdata = PLAYER().seek_and_get_rgb_frame(PLAYER().current_frame())
        self.view_editor.set_screen_rgb_data(rgbdata)
        self.view_editor.set_scale_and_update(0.75)
        self.view_editor.edit_area.queue_draw()

    def write_current_frame(self):
        self.view_editor.write_out_layers = True
        self.show_current_frame()

    def _add_layer_pressed(self, button):
        print "ad"

    def _del_player_pressed(self, button):
        print "del"

    def _edit_value_changed(self, widget):
        self._update_active_layout()

    def _update_active_layout(self):
        buf =  self.text_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), include_hidden_chars=True)
        self.active_layout.text = text
        
        family = self.font_families[self.font_select.get_active()]
        size = str(self.size_spin.get_value_as_int())
        face = self.faces[self.face_combo.get_active()]
        desc_str = family.get_name() + " " + face + " " + size
        self.active_layout.font_desc = pango.FontDescription(desc_str)
        
        color = self.color_button.get_color()
        r, g, b = utils.hex_to_rgb(color.to_string())
        new_color = ( r/65535.0, g/65535.0, b/65535.0, 1.0)
        self.active_layout.color_rgba = new_color
        self.view_editor.edit_area.queue_draw()
         
class PangoTextLayout:
    """
    Data needed to create a pango text layout.
    """
    def __init__(self):
        self.text = "Text"
        self.font_desc = pango.FontDescription("Bitstream Vera Sans Mono Condensed 15")
        self.color_rgba = (1, 1, 1, 1) 
        self.alignment = pango.ALIGN_LEFT
        
    def draw_layout(self, cr, x, y, rotation):
        pango_context = pangocairo.CairoContext(cr)
        layout = pango_context.create_layout()
        layout.set_text(self.text)
        layout.set_font_description(self.font_desc)

        pango_context.set_source_rgba(*self.color_rgba)
        pango_context.move_to(x, y)
        pango_context.rotate(rotation)
        pango_context.update_layout(layout)
        pango_context.show_layout(layout)

# ------------------------------------------------- item lists 
class TextLayerListView(gtk.VBox):

    def __init__(self):
        gtk.VBox.__init__(self)

        style = self.get_style()
        bg_col = style.bg[gtk.STATE_NORMAL]
        
       # Datamodel: icon, text, text
        self.storemodel = gtk.ListStore(str)
 
        # Scroll container
        self.scroll = gtk.ScrolledWindow()
        self.scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.scroll.set_shadow_type(gtk.SHADOW_ETCHED_IN)

        # View
        self.treeview = gtk.TreeView(self.storemodel)
        self.treeview.set_property("rules_hint", True)
        self.treeview.set_headers_visible(False)
        tree_sel = self.treeview.get_selection()
        tree_sel.set_mode(gtk.SELECTION_SINGLE)

        # Column view
        self.text_col_1 = gtk.TreeViewColumn("text1")

        # Cell renderers
        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_END)

        # Build column views
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 1)
        
        # Add column views to view
        self.treeview.append_column(self.text_col_1)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
        self.scroll.show_all()

    def get_selected_row(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return max(rows)
