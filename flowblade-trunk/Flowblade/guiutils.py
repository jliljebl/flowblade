"""
Module contains utility methods for creating GUI objects.
"""
import appconsts
import gtk
import respaths
import translations

TWO_COLUMN_BOX_HEIGHT = 20

def bold_label(str):
    label = gtk.Label(bold_text(str))
    label.set_use_markup(True)
    return label

def bold_text(str):
    return "<b>" + str + "</b>"

def get_left_justified_box(widgets):
    hbox = gtk.HBox()
    for widget in widgets:
        hbox.pack_start(widget, False, False, 0)
    hbox.pack_start(gtk.Label(), True, True, 0)
    return hbox

def get_right_justified_box(widgets):
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label(), True, True, 0)
    for widget in widgets:
        hbox.pack_start(widget, False, False, 0)
    return hbox

def get_two_column_box(widget1, widget2, left_width):
    hbox = gtk.HBox()
    left_box = get_left_justified_box([widget1])
    left_box.set_size_request(left_width, TWO_COLUMN_BOX_HEIGHT)
    hbox.pack_start(left_box, False, True, 0)
    hbox.pack_start(widget2, True, True, 0)
    return hbox

def get_two_row_box(widget1, widget2):
    # widget 1 is left justified
    top = get_left_justified_box([widget1])
    box = gtk.VBox(False, 2)
    box.pack_start(top, False, False, 4)
    box.pack_start(widget2, False, False, 0)
    return box

def get_image_button(img_file_name, width, height):
    button = gtk.Button()
    icon = gtk.image_new_from_file(respaths.IMAGE_PATH + img_file_name)        
    button_box = gtk.HBox()
    button_box.pack_start(icon, False, False, 0)
    button.add(button_box)
    button.set_size_request(width, height)
    return button
    
def get_pad_label(w, h):
    label = gtk.Label()
    label.set_size_request(w, h)
    return label

def get_multiplied_color(color, m):
    """
    Used to create lighter and darker hues of colors.
    """
    return (color[0] * m, color[1] * m, color[2] * m)

def get_slider_row(editable_property, listener, slider_name=None):
    adjustment = editable_property.get_input_range_adjustment()
    editable_property.value_changed_ID = adjustment.connect("value-changed", listener) # patching in to make available for disconnect
    editable_property.adjustment = adjustment # patching in to make available for disconnect

    hslider = gtk.HScale()
    hslider.set_adjustment(adjustment)
    hslider.set_draw_value(False)
    
    spin = gtk.SpinButton()
    spin.set_adjustment(adjustment)

    hbox = gtk.HBox(False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)
    
    if slider_name == None:
        name = editable_property.get_display_name()
    else:
        name = slider_name
    name = translations.get_param_name(name)
    return (get_two_column_editor_row(name, hbox), hslider)
    
def get_two_column_editor_row(name, editor_widget):
    label = gtk.Label(name + ":")

    label_box = gtk.HBox()
    label_box.pack_start(label, False, False, 0)
    label_box.pack_start(gtk.Label(), True, True, 0)
    label_box.set_size_request(appconsts.PROPERTY_NAME_WIDTH, appconsts.PROPERTY_ROW_HEIGHT)
    
    hbox = gtk.HBox(False, 2)
    hbox.pack_start(label_box, False, False, 4)
    hbox.pack_start(editor_widget, True, True, 0)
    return hbox
