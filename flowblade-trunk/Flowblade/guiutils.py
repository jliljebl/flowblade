"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2012 Janne Liljeblad.

    This file is part of Flowblade Movie Editor <https://github.com/jliljebl/flowblade/>.

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
import cairo
import time
import threading

from gi.repository import Gtk, Gdk, GLib
from gi.repository import GdkPixbuf

import appconsts
import editorpersistance
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

def get_two_column_box_fixed(widget1, widget2, left_width, right_width, margin):
    hbox = Gtk.HBox()
    left_box = get_left_justified_box([widget1])
    left_box.set_size_request(left_width, TWO_COLUMN_BOX_HEIGHT)
    right_box = get_left_justified_box([widget2])
    right_box.set_size_request(right_width, TWO_COLUMN_BOX_HEIGHT)
    right_box.set_margin_start(margin)
    hbox.pack_start(left_box, False, False, 0)
    hbox.pack_start(right_box, False, False, 0)
    return hbox
    
def get_three_column_box(widget1, widget2, widget3, left_width, right_width):
    hbox = Gtk.HBox()
    left_box = get_left_justified_box([widget1])
    left_box.set_size_request(left_width, TWO_COLUMN_BOX_HEIGHT)
    right_box = get_right_justified_box([widget3])
    right_box.set_size_request(right_width, TWO_COLUMN_BOX_HEIGHT)
    hbox.pack_start(left_box, False, True, 0)
    hbox.pack_start(widget2, True, True, 0)
    hbox.pack_start(right_box, True, True, 0)
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

def get_right_expand_box(widget1, widget2, center_pad=False):
    hbox = Gtk.HBox()
    hbox.pack_start(widget1, False, True, 0)
    if center_pad:
        hbox.pack_start(pad_label(4,4), False, True, 0)
    hbox.pack_start(widget2, True, True, 0)
    return hbox

# Aug-2019 - SvdB - BB
def get_image_name(img_name, suffix = ".png", double_height = False):
    button_size_text = ""
    if double_height:
       button_size_text = "@2"    
    img_name = img_name+button_size_text+suffix
    return img_name

# Aug-2019 - SvdB - BB
def get_image(img_name, suffix = ".png", force = None):
    # Use parameter force as True or False to force the track height no matter what the preferences setting
    if force == None:
        force = (editorpersistance.prefs.icons_scale == appconsts.ICONS_SCALE_DOUBLE)
    if force:
        new_name = img_name + "@2"
    else:
        new_name = img_name
    try:
        img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + new_name + suffix)
    except:
        img = Gtk.Image.new_from_file(respaths.IMAGE_PATH + img_name + suffix)
    return img
    

# Aug-2019 - SvdB - BB
def get_cairo_image(img_name, suffix = ".png", force = None):
    # Apr-2020 - SvdB - Make it sturdier in case a @2 image is missing. Just display the original image.
    # Use parameter force as True or False to force the track height no matter what the preferences setting
    if force == None:
        force = (editorpersistance.prefs.icons_scale == appconsts.ICONS_SCALE_DOUBLE)
    if force:
        new_name = img_name + "@2"
    else:
        new_name = img_name

    try:
        img = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + new_name + suffix)
    except:
        # Colorized icons
        if img_name[-6:] == "_color":  #editorpersistance.prefs.colorized_icons is True:
            try:
                img = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + img_name + "_color" + suffix)
            except:
                img = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + img_name[:-6] + suffix)
        else:
            img = cairo.ImageSurface.create_from_png(respaths.IMAGE_PATH + img_name + suffix)
        # End of Colorized icons
    return img

def get_double_scaled_cairo_image(icon_name):
    img_path = respaths.IMAGE_PATH + icon_name
    
    icon = cairo.ImageSurface.create_from_png(img_path)
    if (editorpersistance.prefs.icons_scale != appconsts.ICONS_SCALE_DOUBLE):
        return icon
    
    surface_pattern = cairo.SurfacePattern(icon)
    surface_pattern.set_filter(cairo.Filter.NEAREST)
    
    scaled_icon = cairo.ImageSurface(cairo.FORMAT_ARGB32, icon.get_width() * 2, icon.get_height() * 2)
    cr = cairo.Context(scaled_icon)
    cr.scale(2.0, 2.0)
    cr.set_source(surface_pattern)
    cr.paint()

    return scaled_icon
        
# Aug-2019 - SvdB - BB
def get_image_button(img_file_name, width, height):
    button = Gtk.Button()
    icon = get_image(img_file_name)        
    size_adj = 1
    if (editorpersistance.prefs.icons_scale == appconsts.ICONS_SCALE_DOUBLE):
        size_adj = 2
    button_box = Gtk.HBox()
    button_box.pack_start(icon, False, False, 0)
    button.add(button_box)
    button.set_size_request(width*size_adj, height*size_adj)
    return button

def double_icon_size():
    if (editorpersistance.prefs.icons_scale == appconsts.ICONS_SCALE_DOUBLE):
        return True
    else:
        return False

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
    
def get_non_property_slider_row(lower, upper, step, value=0, listener=None, scale_digits=0):
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

    hslider.set_digits(scale_digits)
    spin.set_digits(scale_digits)
    
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
    
def get_named_frame(name, widget, left_padding=12, right_padding=6, right_out_padding=4, tooltip_txt=None):
    """
    Gnome style named panel
    """
    if name != None:
        label = bold_label(name)
        label.set_justify(Gtk.Justification.LEFT)
        
        label_box = Gtk.HBox()
        label_box.pack_start(label, False, False, 0)
        label_box.pack_start(Gtk.Label(), True, True, 0)
        if tooltip_txt != None:        
            label.set_tooltip_markup(tooltip_txt)
    else:
        label = Gtk.Label()

    alignment = set_margins(widget, right_padding, 0, left_padding, 0)

    frame = Gtk.VBox()
    if name != None:
        frame.pack_start(label_box, False, False, 0)
    frame.pack_start(alignment, True, True, 0)
    
    frame.name_label = label
    
    out_align = set_margins(frame, 4, 4, 0, right_out_padding)
    
    return out_align

def get_panel_etched_frame(panel):
    frame = Gtk.Frame()
    frame.add(panel)
    set_margins(frame, 0, 0, 1, 0)
    return frame

def get_empty_panel_etched_frame():
    frame = Gtk.Frame()
    set_margins(frame, 0, 0, 1, 0)
    return frame
    
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

def get_sized_button(button_label, w, h, clicked_listener=None):
    b = Gtk.Button(label=button_label)
    if clicked_listener != None:
        b.connect("clicked", lambda w,e: clicked_listener())
    b.set_size_request(w, h)
    return b  

def get_render_button():
    render_button = Gtk.Button()
    render_icon = Gtk.Image.new_from_icon_name( "media-record", 
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
    widget.set_margin_start(l)
    widget.set_margin_bottom(b)
    widget.set_margin_end(r)
    
    return widget

def get_theme_bg_color():
    return (242.0/255.0, 241.0/ 255.0, 240.0/255.0)

def remove_children(container):
    children = container.get_children()
    for child in children:
        container.remove(child)

class PulseEvent:
    def __init__(self, proress_bar):
        self.proress_bar = proress_bar
        self.exited = False
        self.running = True
        
        Gdk.threads_add_timeout(GLib.PRIORITY_HIGH_IDLE, 100, self._do_pulse)
                
    def _do_pulse(self):
        if self.running:
            self.proress_bar.pulse()
            return True
        else:
            self.exited = True
            return False


def update_text_idle(text_widget, msg):
    GLib.idle_add(_do_update_text, text_widget, msg)

def _do_update_text(text_widget, msg):
    text_widget.set_text(msg)


class ProgressWindowThread(threading.Thread):
    def __init__(self, dialog, progress_bar, clip_renderer, callback):
        self.dialog = dialog
        self.progress_bar = progress_bar
        self.clip_renderer = clip_renderer
        self.callback = callback
        threading.Thread.__init__(self)
    
    def run(self):        
        self.running = True
        
        while self.running:         

            GLib.idle_add(self._update_progress_bar)

            if self.clip_renderer.stopped == True:
                self.running = False
                GLib.idle_add(self._render_complete)

            time.sleep(0.33)
    
    def _update_progress_bar(self):
        render_fraction = self.clip_renderer.get_render_fraction()
        self.progress_bar.set_fraction(render_fraction)
        pros = int(render_fraction * 100)
        self.progress_bar.set_text(str(pros) + "%")
    
    def _render_complete(self):
        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text("Render Complete!")
        self.callback(self.dialog, 0)
    
