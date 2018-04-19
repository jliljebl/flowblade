# Flowblade Package Dependencies #

| **Debian/Ubuntu package name** | **Description** | **Archlinux packages** |
|:-------------------------------|:----------------|:--------------|
| python-gi | GTK3 Python bindings | pygtk |
| python-mlt | MLT python bindings, this pulls in MLT | mlt-python-bindings |
| python-dbus | dbus python bindings | python2-dbus |
| libmlt-data | Some image and text resources for MLT | mlt, sdl_image |
| python 2.7 >=| Language and interpreter | python2 |
| frei0r-plugins | Additional video filters | movit, frei0r-plugins |
| swh-plugins | Additional audio filters | sox, swh-plugins |
| python-gi-cairo | Gi Cairo bindings | python2-gobject |
| python-numpy | Math and arrays library | python2-numpy |
| python-pil | PIL image manipulation library | python2-pillow |
| librsvg2-common | svg support | librsvg |
| gmic | framework for image processing | gmic |
| gir1.2-glib-2.0 | Glib | dbus-glib |
| gir1.2-gtk-3.0 | Gtk toolkit | gtk3 |
| gir1.2-pango-1.0 | Pango text lib | pango |
| gir1.2-gdkpixbuf-2.0 | Image support | gdk-pixbuf2 |

# Dropped  Dependencies #

| **Debian/Ubuntu package name** | **Introduced** | **Dropped** |
|:-------------------------------|:---------------|:------------|
| melt | 0.6  | 0.8 |
| fontconfig | 0.6  | 0.16 |
| python-gtk2 |  0.6   | 1.2 |
| gtk2-engines-pixbuf |  0.6   |  1.2 |
| python-gnome2 |  0.6   |  1.2 |
| python-gobject-2 |  0.6   |  1.2 |
| python-cairo |  0.6   |  1.6 |
