"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <http://code.google.com/p/flowblade>.

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

"""
Module contains utility methods for creating GUI objects.
"""
import pygtk
pygtk.require('2.0');
import gtk

import time
import threading

import appconsts
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

def get_sides_justified_box(widgets, count_of_widgets_on_the_left=1):
    hbox = gtk.HBox()
    wgets_added = 0
    for widget in widgets:
        hbox.pack_start(widget, False, False, 0)
        wgets_added +=1
        if wgets_added == count_of_widgets_on_the_left:
            hbox.pack_start(gtk.Label(), True, True, 0)
    return hbox

def get_centered_box(widgets):
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label(), True, True, 0)
    for widget in widgets:
        hbox.pack_start(widget, False, False, 0)
    hbox.pack_start(gtk.Label(), True, True, 0)
    return hbox

def get_single_column_box(widgets):
    vbox = gtk.VBox()
    for widget in widgets:
        vbox.pack_start(get_left_justified_box([widget]), False, False, 0)
    vbox.pack_start(gtk.Label(), True, True, 0)
    return vbox
    
def get_two_column_box(widget1, widget2, left_width):
    hbox = gtk.HBox()
    left_box = get_left_justified_box([widget1])
    left_box.set_size_request(left_width, TWO_COLUMN_BOX_HEIGHT)
    hbox.pack_start(left_box, False, True, 0)
    hbox.pack_start(widget2, True, True, 0)
    return hbox

def get_two_column_box_right_pad(widget1, widget2, left_width, right_pad):
    left_box = get_left_justified_box([widget1])
    left_box.set_size_request(left_width, TWO_COLUMN_BOX_HEIGHT)
    
    right_widget_box = get_left_justified_box([widget2])
    pad_label = get_pad_label(right_pad, 5)
    right_box = gtk.HBox()
    right_box.pack_start(right_widget_box, True, True, 0)
    right_box.pack_start(pad_label, False, False, 0)
    
    hbox = gtk.HBox()
    hbox.pack_start(left_box, False, True, 0)
    hbox.pack_start(right_box, True, True, 0)
    return hbox

def get_checkbox_row_box(checkbox, widget2):
    hbox = gtk.HBox()
    hbox.pack_start(checkbox, False, False, 0)
    hbox.pack_start(widget2, False, False, 0)
    hbox.pack_start(gtk.Label(), True, True, 0)
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
    spin.set_numeric(True)
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

def get_non_property_slider_row(lower, upper, step, value=0, listener=None):
    hslider = gtk.HScale()
    hslider.set_draw_value(False)

    adjustment = hslider.get_adjustment()
    adjustment.set_lower(lower)
    adjustment.set_upper(upper)
    adjustment.set_step_increment(step)
    adjustment.set_value(value)

    if listener != None:
        adjustment.connect("value-changed", listener) # patching in to make available for disconnect
    
    spin = gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)

    hbox = gtk.HBox(False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)

    return (hbox, hslider)
    
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

def get_no_pad_named_frame(name, panel):
    return get_named_frame(name, panel, 0, 0, 0)

def get_named_frame_with_vbox(name, widgets, left_padding=12, right_padding=6, right_out_padding=4):
    vbox = gtk.VBox()
    for widget in widgets:
        vbox.pack_start(widget, False, False, 0)

    return get_named_frame(name, vbox, left_padding, right_padding, right_out_padding)
    
def get_named_frame(name, widget, left_padding=12, right_padding=6, right_out_padding=4):
    """
    Gnome style named panel
    """
    if name != None:
        label = bold_label(name)
        label.set_justify(gtk.JUSTIFY_LEFT)
        
        label_box = gtk.HBox()
        label_box.pack_start(label, False, False, 0)
        label_box.pack_start(gtk.Label(), True, True, 0)

    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(right_padding, 0, left_padding, 0)
    alignment.add(widget)
    
    frame = gtk.VBox()
    if name != None:
        frame.pack_start(label_box, False, False, 0)
    frame.pack_start(alignment, True, True, 0)
    
    out_align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    out_align.set_padding(4, 4, 0, right_out_padding)
    out_align.add(frame)
    
    return out_align

def get_in_centering_alignment(widget, xsc=0.0, ysc=0.0):
    align = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=xsc, yscale=ysc)
    align.add(widget)
    return align

def pad_label(w, h):
    pad_label = gtk.Label()
    pad_label.set_size_request(w, h)
    return pad_label

def get_sized_button(lable, w, h, clicked_listener=None):
    b = gtk.Button(lable)
    if clicked_listener != None:
        b.connect("clicked", lambda w,e: clicked_listener())
    b.set_size_request(w, h)
    return b  

def get_render_button():
    render_button = gtk.Button()
    render_icon = gtk.image_new_from_stock(gtk.STOCK_MEDIA_RECORD, 
                                           gtk.ICON_SIZE_BUTTON)
    render_button_box = gtk.HBox()
    render_button_box.pack_start(get_pad_label(10, 10), False, False, 0)
    render_button_box.pack_start(render_icon, False, False, 0)
    render_button_box.pack_start(get_pad_label(5, 10), False, False, 0)
    render_button_box.pack_start(gtk.Label(_("Render")), False, False, 0)
    render_button_box.pack_start(get_pad_label(10, 10), False, False, 0)
    render_button.add(render_button_box)
    return render_button

def get_menu_item(text, callback, data, sensitive=True):
    item = gtk.MenuItem(text)
    item.connect("activate", callback, data)
    item.show()
    item.set_sensitive(sensitive)
    return item

def add_separetor(menu):
    sep = gtk.SeparatorMenuItem()
    sep.show()
    menu.add(sep)

def get_gtk_image_from_file(source_path, image_height):
    img = gtk.Image()
    p_map = get_pixmap_from_file(source_path, image_height)
    img.set_from_pixmap(p_map, None)
    return img

def get_pixmap_from_file(source_path, image_height):
    pixbuf = gtk.gdk.pixbuf_new_from_file(source_path)
    icon_width = int((float(pixbuf.get_width()) / float(pixbuf.get_height())) * image_height)
    s_pbuf = pixbuf.scale_simple(icon_width, image_height, gtk.gdk.INTERP_BILINEAR)
    p_map, mask = s_pbuf.render_pixmap_and_mask()
    return p_map

class PulseThread(threading.Thread):
    def __init__(self, proress_bar):
        threading.Thread.__init__(self)
        self.proress_bar = proress_bar

    def run(self):
        self.exited = False
        self.running = True
        while self.running:
            gtk.gdk.threads_enter()
            self.proress_bar.pulse()
            gtk.gdk.threads_leave()
            time.sleep(0.1)
        self.exited = True
