

import gtk
import pango
import pangocairo

from editorstate import PLAYER
import utils
import guiutils
import vieweditor
import vieweditorlayer

_titler = None
_titler_data = None

DEFAULT_FONT_SIZE = 25

FACE_REGULAR = "Regular"
FACE_BOLD = "Bold"
FACE_ITALIC = "Italic"
FACE_BOLD_ITALIC = "Bold Italic"

ALIGN_LEFT = 0
ALIGN_CENTER = 1
ALIGN_RIGHT = 2

def show_titler():
    global _titler_data
    _titler_data = TitlerData()
    
    global _titler
    _titler = Titler()
    _titler.show_current_frame()

# ------------------------------------------------------------- data
class TextLayer:
    """
    Data needed to create a pango text layout.
    """
    def __init__(self):
        self.text = "Text"
        self.font_desc = "Bitstream Vera Sans Mono Condensed 15"
        self.color_rgba = (1, 1, 1, 1) 
        self.alignment = ALIGN_LEFT
        self.pixel_size = (100, 100)

class TitlerData:
    """
    Data edited in titler editor
    """
    def __init__(self):
        self.layers = []
        self.add_layer()
        
    def add_layer(self):
        self.active_layer = TextLayer()
        self.layers.append(self.active_layer)
        
# ---------------------------------------------------------- editor
class Titler(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_title("Titler")

        self.block_updates = False
        
        self.active_layout = PangoTextLayout(_titler_data.active_layer)
        self.view_editor = vieweditor.ViewEditor(PLAYER().profile)
        edit_layer = vieweditorlayer.TextEditLayer(self.view_editor, self.active_layout)
        self.view_editor.edit_layers.append(edit_layer)
        self.view_editor.active_layer = edit_layer

        add_b = gtk.Button(_("Add"))
        del_b = gtk.Button(_("Delete"))
        add_b.connect("clicked", lambda w:self._add_layer_pressed())
        del_b.connect("clicked", lambda w:self._del_player_pressed())
        add_del_box = gtk.HBox()
        add_del_box = gtk.HBox(True,1)
        add_del_box.pack_start(add_b)
        add_del_box.pack_start(del_b)
        
        self.layer_list = TextLayerListView(self._layer_selection_changed)
        self.layer_list.set_size_request(300, 200)
    
        self.text_view = gtk.TextView()
        self.text_view.set_pixels_above_lines(2)
        self.text_view.set_left_margin(2)
        self.text_view.get_buffer().connect("changed", self._text_changed)

        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.sw.add(self.text_view)
        self.sw.set_size_request(300, 150)

        scroll_frame = gtk.Frame()
        scroll_frame.add(self.sw)
        
        font_map = pangocairo.cairo_font_map_get_default()
        unsorted_families = font_map.list_families()
        self.font_families = sorted(unsorted_families, key=lambda family: family.get_name())

        combo = gtk.combo_box_new_text()
        for family in self.font_families:
            combo.append_text(family.get_name())
        combo.set_active(0)
        self.font_select = combo
        self.font_select.connect("changed", self._edit_value_changed)
    
        adj = gtk.Adjustment(float(DEFAULT_FONT_SIZE), float(1), float(300), float(1))
        self.size_spin = gtk.SpinButton(adj)
        self.size_spin.connect("changed", self._edit_value_changed)
        self.size_spin.connect("activate", self._edit_value_changed)

        font_main_row = gtk.HBox()
        font_main_row.pack_start(self.font_select, True, True, 0)
        font_main_row.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        font_main_row.pack_start(self.size_spin, False, False, 0)

        self.bold_font = gtk.ToggleButton()
        self.italic_font = gtk.ToggleButton()
        bold_icon = gtk.image_new_from_stock(gtk.STOCK_BOLD, 
                                       gtk.ICON_SIZE_BUTTON)
        italic_icon = gtk.image_new_from_stock(gtk.STOCK_ITALIC, 
                                       gtk.ICON_SIZE_BUTTON)
        self.bold_font.set_image(bold_icon)
        self.italic_font.set_image(italic_icon)
        self.bold_font.connect("clicked", self._edit_value_changed)
        self.italic_font.connect("clicked", self._edit_value_changed)
        
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
        self.left_align.connect("clicked", self._edit_value_changed)
        self.center_align.connect("clicked", self._edit_value_changed)
        self.right_align.connect("clicked", self._edit_value_changed)
        
        self.color_button = gtk.ColorButton()
        self.color_button.connect("color-set", self._edit_value_changed)

        buttons_box = gtk.HBox()
        buttons_box.pack_start(gtk.Label(), True, True, 0)
        buttons_box.pack_start(self.bold_font, False, False, 0)
        buttons_box.pack_start(self.italic_font, False, False, 0)
        buttons_box.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        buttons_box.pack_start(self.left_align, False, False, 0)
        buttons_box.pack_start(self.center_align, False, False, 0)
        buttons_box.pack_start(self.right_align, False, False, 0)
        buttons_box.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        buttons_box.pack_start(self.color_button, False, False, 0)
        buttons_box.pack_start(gtk.Label(), True, True, 0)

        adj = gtk.Adjustment(float(0), float(1), float(3000), float(1))
        self.x_pos_spin = gtk.SpinButton(adj) 
        adj = gtk.Adjustment(float(0), float(1), float(3000), float(1))
        self.y_pos_spin = gtk.SpinButton(adj)
        adj = gtk.Adjustment(float(0), float(1), float(3000), float(1))
        self.rotation_spin = gtk.SpinButton(adj) 
        undo_pos = gtk.Button()
        undo_icon = gtk.image_new_from_stock(gtk.STOCK_UNDO, 
                                       gtk.ICON_SIZE_BUTTON)
        undo_pos.set_image(undo_icon)
        
        positions_box = gtk.HBox()
        positions_box.pack_start(gtk.Label(), True, True, 0)
        positions_box.pack_start(gtk.Label("X"), False, False, 0)
        positions_box.pack_start(self.x_pos_spin, False, False, 0)
        positions_box.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        positions_box.pack_start(gtk.Label("Y"), False, False, 0)
        positions_box.pack_start(self.y_pos_spin, False, False, 0)
        positions_box.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        positions_box.pack_start(gtk.Label(_("A")), False, False, 0)
        positions_box.pack_start(self.rotation_spin, False, False, 0)
        positions_box.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        positions_box.pack_start(undo_pos, False, False, 0)
        positions_box.pack_start(gtk.Label(), True, True, 0)

        adj = gtk.Adjustment(float(0), float(1), float(3000), float(1))
        self.intendent = gtk.SpinButton(adj)
        adj = gtk.Adjustment(float(0), float(1), float(3000), float(1))
        self.spacing = gtk.SpinButton(adj) 
        paragraph_box = gtk.HBox()
        paragraph_box.pack_start(gtk.Label(), True, True, 0)
        paragraph_box.pack_start(gtk.Label(_("Spacing")), False, False, 0)
        paragraph_box.pack_start(self.spacing, False, False, 0)
        paragraph_box.pack_start(guiutils.pad_label(5, 5), False, False, 0)
        paragraph_box.pack_start(gtk.Label(_("Indent")), False, False, 0)
        paragraph_box.pack_start(self.intendent, False, False, 0)
        paragraph_box.pack_start(gtk.Label(), True, True, 0)
        
        controls_panel_1 = gtk.VBox()
        controls_panel_1.pack_start(add_del_box, False, False, 0)
        controls_panel_1.pack_start(self.layer_list, False, False, 0)

        controls_panel_2 = gtk.VBox()
        controls_panel_2.pack_start(scroll_frame, False, False, 0)
        controls_panel_2.pack_start(font_main_row, False, False, 0)
        controls_panel_2.pack_start(buttons_box, False, False, 0)
        controls_panel_2.pack_start(positions_box, False, False, 0)
        controls_panel_2.pack_start(paragraph_box, False, False, 0)
        
        controls_panel = gtk.VBox()

        controls_panel.pack_start(guiutils.get_named_frame(_("Active Layer"),controls_panel_2), False, False, 0)
        controls_panel.pack_start(guiutils.get_named_frame(_("Layers"),controls_panel_1), False, False, 0)
        controls_panel.pack_start(gtk.Label(), True, True, 0)

        editor_row = gtk.HBox()
        editor_row.pack_start(controls_panel, False, False, 0)
        editor_row.pack_start(self.view_editor, False, False, 0)

        display_current_frame = gtk.Button("Load current frame")
        save_label = gtk.Label("Open Graphic In Bin")
        self.open_in_current_check = gtk.CheckButton()

        editor_buttons_row_upper = gtk.HBox()
        editor_buttons_row_upper.pack_start(gtk.Label(), True, True, 0)
        editor_buttons_row_upper.pack_start(vieweditor.ScaleSelector(self), False, False, 0)
        editor_buttons_row_upper.pack_start(display_current_frame, False, False, 0)
        editor_buttons_row_upper.pack_start(save_label, False, False, 0)
        editor_buttons_row_upper.pack_start(self.open_in_current_check , False, False, 0)

        exit_b = gtk.Button("Exit")
        save_titles_b = gtk.Button("Save Title")

        load_layers = gtk.Button("Load Layers")
        save_layers = gtk.Button("Save Layers")

        editor_buttons_row = gtk.HBox()
        editor_buttons_row.pack_start(load_layers, False, False, 0)
        editor_buttons_row.pack_start(save_layers, False, False, 0)
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

        self.layer_list.fill_data_model()
        self._update_gui_with_active_layer_data()
        self.show_all()

    def show_current_frame(self):
        rgbdata = PLAYER().seek_and_get_rgb_frame(PLAYER().current_frame())
        self.view_editor.set_screen_rgb_data(rgbdata)
        self.view_editor.edit_area.queue_draw()

    def scale_changed(self, new_scale):
        self.view_editor.set_scale_and_update(new_scale)
        self.view_editor.edit_area.queue_draw()

    def write_current_frame(self):
        self.view_editor.write_out_layers = True
        self.show_current_frame()

    def _add_layer_pressed(self):
        global _titler_data
        _titler_data.add_layer()
        self._update_gui_with_active_layer_data()
        self._update_active_layout()
        self.layer_list.fill_data_model()

    def _del_player_pressed(self):
        print "del"

    def _layer_selection_changed(self):
        print self.layer_list.get_selected_row()

    def _text_changed(self, widget):
        self._update_active_layer_rect()
        
    def _update_active_layer_rect(self):
        self.view_editor.active_layer.update_rect = True
        self._update_active_layout()

    def _edit_value_changed(self, widget):
        self._update_active_layout()

    def _update_active_layout(self):
        if self.block_updates:
            return

        global _titler_data
        buf = self.text_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), include_hidden_chars=True)
        if text != _titler_data.active_layer.text:
            update_layers_list = True
        else:
            update_layers_list = False

        _titler_data.active_layer.text = text
        
        family = self.font_families[self.font_select.get_active()]
        size = str(self.size_spin.get_value_as_int())
        face = FACE_REGULAR
        if self.bold_font.get_active() and self.italic_font.get_active():
            face = FACE_BOLD_ITALIC
        elif self.italic_font.get_active():
            face = FACE_ITALIC
        elif self.bold_font.get_active():
            face = FACE_BOLD
        desc_str = family.get_name() + " " + face + " " + size
        _titler_data.active_layer.font_desc = desc_str

        align = pango.ALIGN_LEFT
        if self.center_align.get_active():
            align = pango.ALIGN_CENTER
        elif  self.right_align.get_active():
             align = pango.ALIGN_RIGHT
        _titler_data.active_layer.alignment = align

        color = self.color_button.get_color()
        r, g, b = utils.hex_to_rgb(color.to_string())
        new_color = ( r/65535.0, g/65535.0, b/65535.0, 1.0)        
        _titler_data.active_layer.color_rgba = new_color

        self.active_layout.load_layer_data(_titler_data.active_layer)
        if update_layers_list:
            self.layer_list.fill_data_model()

        self.view_editor.edit_area.queue_draw()

    def _update_gui_with_active_layer_data(self):
        self.block_updates = True
        
        self.text_view.get_buffer().set_text(_titler_data.active_layer.text)
        r, g, b, a = _titler_data.active_layer.color_rgba
        button_color = gtk.gdk.Color(r * 65535.0, g * 65535.0, b * 65535.0)
        self.color_button.set_color(button_color)

        self.block_updates = False



# --------------------------------------------------------- layer/s representation
class PangoTextLayout:
    """
    Wrapper for drawing current active layer.
    
    We need this wrapper because we want to save titler data using simple pickle
    and therefore need to avoid using pango objects in layer data.
    """
    def __init__(self, layer):
        self.load_layer_data(layer)
        
    def load_layer_data(self, layer):    
        self.text = layer.text
        self.font_desc = pango.FontDescription(layer.font_desc)
        self.color_rgba = layer.color_rgba
        self.alignment = self._get_pango_alignment_for_layer(layer)
        self.pixel_size = layer.pixel_size
        
    def draw_layout(self, cr, x, y, rotation, xscale, yscale):
        cr.save()
        
        pango_context = pangocairo.CairoContext(cr)
        layout = pango_context.create_layout()
        layout.set_text(self.text)
        layout.set_font_description(self.font_desc)
        layout.set_alignment(self.alignment)
        self.pixel_size = layout.get_pixel_size()
        pango_context.set_source_rgba(*self.color_rgba)
        pango_context.move_to(x, y)
        pango_context.scale( xscale, yscale)
        pango_context.rotate(rotation)
        pango_context.update_layout(layout)
        pango_context.show_layout(layout)

        cr.restore()

    def _get_pango_alignment_for_layer(self, layer):
        if layer.alignment == ALIGN_LEFT:
            return pango.ALIGN_LEFT
        elif layer.alignment == ALIGN_CENTER:
            return pango.ALIGN_CENTER
        else:
            return pango.ALIGN_RIGHT


class TextLayerListView(gtk.VBox):

    def __init__(self, selection_changed_cb):
        gtk.VBox.__init__(self)

        style = self.get_style()
        bg_col = style.bg[gtk.STATE_NORMAL]
        
       # Datamodel: str
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
        tree_sel.connect("changed", lambda treeSel:selection_changed_cb())
            
        # Column view
        self.text_col_1 = gtk.TreeViewColumn("text1")

        # Cell renderers
        self.text_rend_1 = gtk.CellRendererText()
        self.text_rend_1.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.text_rend_1.set_fixed_height_from_font(1)

        # Build column views
        self.text_col_1.set_expand(True)
        self.text_col_1.set_spacing(5)
        self.text_col_1.set_sizing(gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.text_col_1.set_min_width(150)
        self.text_col_1.pack_start(self.text_rend_1)
        self.text_col_1.add_attribute(self.text_rend_1, "text", 0)

        # Add column views to view
        self.treeview.append_column(self.text_col_1)

        # Build widget graph and display
        self.scroll.add(self.treeview)
        self.pack_start(self.scroll)
        self.scroll.show_all()

    def get_selected_row(self):
        model, rows = self.treeview.get_selection().get_selected_rows()
        return max(rows)

    def fill_data_model(self):
        """
        Creates displayed data.
        Displays icon, sequence name and sequence length
        """
        self.storemodel.clear()
        for layer in _titler_data.layers:
            row_data = [layer.text]
            self.storemodel.append(row_data)
        
        self.scroll.queue_draw()
