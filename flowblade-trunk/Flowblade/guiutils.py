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

import time
import threading

from gi.repository import Gtk, Gdk
from gi.repository import GdkPixbuf

import appconsts
import respaths
import translations

TWO_COLUMN_BOX_HEIGHT = 20

def bold_label(str):
    label = Gtk.Label(label=bold_text(str))
    label.set_use_markup(True)
    return label

def bold_text(str):
    return "<b>" + str + "</b>"

def get_left_justified_box(widgets):
    hbox = Gtk.HBox()
    for widget in widgets:
        hbox.pack_start(widget, False, False, 0)
    hbox.pack_start(Gtk.Label(), True, True, 0)
    return hbox

def get_right_justified_box(widgets):
    hbox = Gtk.HBox()
    hbox.pack_start(Gtk.Label(), True, True, 0)
    for widget in widgets:
        hbox.pack_start(widget, False, False, 0)
    return hbox

def get_sides_justified_box(widgets, count_of_widgets_on_the_left=1):
    hbox = Gtk.HBox()
    wgets_added = 0
    for widget in widgets:
        hbox.pack_start(widget, False, False, 0)
        wgets_added +=1
        if wgets_added == count_of_widgets_on_the_left:
            hbox.pack_start(Gtk.Label(), True, True, 0)
    return hbox

def get_centered_box(widgets):
    hbox = Gtk.HBox()
    hbox.pack_start(Gtk.Label(), True, True, 0)
    for widget in widgets:
        hbox.pack_start(widget, False, False, 0)
    hbox.pack_start(Gtk.Label(), True, True, 0)
    return hbox

def get_vbox(widgets, add_pad_label=True, padding=2):
    vbox = Gtk.VBox(False, padding)
    for widget in widgets:
        vbox.pack_start(widget, False, False, 0)
    if add_pad_label:
        vbox.pack_start(Gtk.Label(), True, True, 0)
    return vbox

def get_single_column_box(widgets):
    vbox = Gtk.VBox()
    for widget in widgets:
        vbox.pack_start(get_left_justified_box([widget]), False, False, 0)
    vbox.pack_start(Gtk.Label(), True, True, 0)
    return vbox
    
def get_two_column_box(widget1, widget2, left_width):
    hbox = Gtk.HBox()
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
    right_box = Gtk.HBox()
    right_box.pack_start(right_widget_box, True, True, 0)
    right_box.pack_start(pad_label, False, False, 0)
    
    hbox = Gtk.HBox()
    hbox.pack_start(left_box, False, True, 0)
    hbox.pack_start(right_box, True, True, 0)
    return hbox

def get_checkbox_row_box(checkbox, widget2):
    hbox = Gtk.HBox()
    hbox.pack_start(checkbox, False, False, 0)
    hbox.pack_start(get_pad_label(4, 1), False, False, 0)
    hbox.pack_start(widget2, False, False, 0)
    hbox.pack_start(Gtk.Label(), True, True, 0)
    return hbox

def get_two_row_box(widget1, widget2):
    # widget 1 is left justified
    top = get_left_justified_box([widget1])
    box = Gtk.VBox(False, 2)
    box.pack_start(top, False, False, 4)
    box.pack_start(widget2, False, False, 0)
    return box
    
def get_image_button(img_file_name, width, height):
    button = Gtk.Button()
    icon = Gtk.Image.new_from_file(respaths.IMAGE_PATH + img_file_name)        
    button_box = Gtk.HBox()
    button_box.pack_start(icon, False, False, 0)
    button.add(button_box)
    button.set_size_request(width, height)
    return button
    
def get_pad_label(w, h):
    label = Gtk.Label()
    label.set_size_request(w, h)
    return label

def get_multiplied_color(color, m):
    """
    Used to create lighter and darker hues of colors.
    """
    return (color[0] * m, color[1] * m, color[2] * m)

def get_slider_row(editable_property, listener, slider_name=None):
    adjustment = editable_property.get_input_range_adjustment()
    editable_property.adjustment = adjustment # patching in to make available for disconnect

    hslider = Gtk.HScale()
    hslider.set_adjustment(adjustment)
    hslider.set_draw_value(False)
    
    spin = Gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)

    hbox = Gtk.HBox(False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)
    
    if slider_name == None:
        name = editable_property.get_display_name()
    else:
        name = slider_name
    name = translations.get_param_name(name)
    
    editable_property.value_changed_ID = adjustment.connect("value-changed", listener) # saving ID to make it available for disconnect
                                                                                       # This also needs to be after adjustment is set to not loose exiting value for build dummy value 
        
    return (get_two_column_editor_row(name, hbox), hslider)

def get_slider_row_and_spin_widget(editable_property, listener, slider_name=None):
    adjustment = editable_property.get_input_range_adjustment()
    editable_property.adjustment = adjustment # patching in to make available for disconnect

    hslider = Gtk.HScale()
    hslider.set_adjustment(adjustment)
    hslider.set_draw_value(False)
    
    spin = Gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)

    hbox = Gtk.HBox(False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)
    
    if slider_name == None:
        name = editable_property.get_display_name()
    else:
        name = slider_name
    name = translations.get_param_name(name)
    
    editable_property.value_changed_ID = adjustment.connect("value-changed", listener) # saving ID to make it available for disconnect
                                                                                       # This also needs to be available after adjustment is set to not lose exiting value for build dummy value 
        
    return (get_two_column_editor_row(name, hbox), hslider, spin)
    
def get_non_property_slider_row(lower, upper, step, value=0, listener=None):
    hslider = Gtk.HScale()
    hslider.set_draw_value(False)

    adjustment = hslider.get_adjustment()
    adjustment.set_lower(lower)
    adjustment.set_upper(upper)
    adjustment.set_step_increment(step)
    adjustment.set_value(value)

    if listener != None:
        adjustment.connect("value-changed", listener) # patching in to make available for disconnect
    
    spin = Gtk.SpinButton()
    spin.set_numeric(True)
    spin.set_adjustment(adjustment)

    hbox = Gtk.HBox(False, 4)
    hbox.pack_start(hslider, True, True, 0)
    hbox.pack_start(spin, False, False, 4)

    return (hbox, hslider)
    
def get_two_column_editor_row(name, editor_widget):
    label = Gtk.Label(label=name + ":")

    label_box = Gtk.HBox()
    label_box.pack_start(label, False, False, 0)
    label_box.pack_start(Gtk.Label(), True, True, 0)
    label_box.set_size_request(appconsts.PROPERTY_NAME_WIDTH, appconsts.PROPERTY_ROW_HEIGHT)
    
    hbox = Gtk.HBox(False, 2)
    hbox.pack_start(label_box, False, False, 4)
    hbox.pack_start(editor_widget, True, True, 0)
    return hbox

def get_no_pad_named_frame(name, panel):
    return get_named_frame(name, panel, 0, 0, 0)

def get_named_frame_with_vbox(name, widgets, left_padding=12, right_padding=6, right_out_padding=4):
    vbox = Gtk.VBox()
    for widget in widgets:
        vbox.pack_start(widget, False, False, 0)

    return get_named_frame(name, vbox, left_padding, right_padding, right_out_padding)
    
def get_named_frame(name, widget, left_padding=12, right_padding=6, right_out_padding=4):
    """
    Gnome style named panel
    """
    if name != None:
        label = bold_label(name)
        label.set_justify(Gtk.Justification.LEFT)
        
        label_box = Gtk.HBox()
        label_box.pack_start(label, False, False, 0)
        label_box.pack_start(Gtk.Label(), True, True, 0)

    alignment = set_margins(widget, right_padding, 0, left_padding, 0)

    frame = Gtk.VBox()
    if name != None:
        frame.pack_start(label_box, False, False, 0)
    frame.pack_start(alignment, True, True, 0)
    
    out_align = set_margins(frame, 4, 4, 0, right_out_padding)
    
    return out_align

def get_in_centering_alignment(widget, xsc=0.0, ysc=0.0):
    align = Gtk.HBox(False, 0)
    align.pack_start(Gtk.Label(), True, True, 0)
    align.pack_start(widget, False, False, 0)
    align.pack_start(Gtk.Label(), True, True, 0)

    return align

def pad_label(w, h):
    pad_label = Gtk.Label()
    pad_label.set_size_request(w, h)
    return pad_label

def get_sized_button(lable, w, h, clicked_listener=None):
    b = Gtk.Button(lable)
    if clicked_listener != None:
        b.connect("clicked", lambda w,e: clicked_listener())
    b.set_size_request(w, h)
    return b  

def get_render_button():
    render_button = Gtk.Button()
    render_icon = Gtk.Image.new_from_stock(Gtk.STOCK_MEDIA_RECORD, 
                                           Gtk.IconSize.BUTTON)
    render_button_box = Gtk.HBox()
    render_button_box.pack_start(get_pad_label(10, 10), False, False, 0)
    render_button_box.pack_start(render_icon, False, False, 0)
    render_button_box.pack_start(get_pad_label(5, 10), False, False, 0)
    render_button_box.pack_start(Gtk.Label(label=_("Render")), False, False, 0)
    render_button_box.pack_start(get_pad_label(10, 10), False, False, 0)
    render_button.add(render_button_box)
    return render_button

def get_menu_item(text, callback, data, sensitive=True):
    item = Gtk.MenuItem(text)
    item.connect("activate", callback, data)
    item.show()
    item.set_sensitive(sensitive)
    return item

def get_radio_menu_items_group(menu, labels, msgs, callback, active_index):
    first_item = Gtk.RadioMenuItem()
    first_item.set_label(labels[0])
    first_item.show()
    menu.append(first_item)
    if active_index == 0:
        first_item.set_active(True)
    first_item.connect("activate", callback, msgs[0])
    
    for i in range(1, len(labels)):
        radio_item = Gtk.RadioMenuItem.new_with_label([first_item], labels[i])
        menu.append(radio_item)
        radio_item.show()
        if active_index == i:
            radio_item.set_active(True)
        radio_item.connect("activate", callback, msgs[i])
        
def add_separetor(menu):
    sep = Gtk.SeparatorMenuItem()
    sep.show()
    menu.add(sep)

def get_gtk_image_from_file(source_path, image_height):
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(source_path)
    icon_width = int((float(pixbuf.get_width()) / float(pixbuf.get_height())) * image_height)
    s_pbuf = pixbuf.scale_simple(icon_width, image_height, GdkPixbuf.InterpType.BILINEAR)
    img = Gtk.Image.new_from_pixbuf(s_pbuf)
    return img

def set_margins(widget, t, b, l, r):
    widget.set_margin_top(t)
    widget.set_margin_left(l)
    widget.set_margin_bottom(b)
    widget.set_margin_right(r)
    
    return widget

def get_theme_bg_color():
    return (242.0/255.0, 241.0/ 255.0, 240.0/255.0)

def remove_children(container):
    children = container.get_children()
    for child in children:
        container.remove(child)

class PulseThread(threading.Thread):
    def __init__(self, proress_bar):
        threading.Thread.__init__(self)
        self.proress_bar = proress_bar

    def run(self):
        self.exited = False
        self.running = True
        while self.running:
            Gdk.threads_enter()
            self.proress_bar.pulse()
            Gdk.threads_leave()
            time.sleep(0.1)
        self.exited = True
