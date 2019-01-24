# Flowblade Package Dependencies #

| **Debian/Ubuntu package name** | **Description** | **Archlinux packages** | **Solus packages** |
|:-------------------------------|:----------------|:--------------|:---------------|
| python-gi | GTK3 Python bindings | pygtk | ??? |
| mlt | | | (compile from source¹) |
| python-mlt | MLT python bindings, this pulls in MLT | mlt-python-bindings | (comes with mlt sources²) |
| python-dbus | dbus python bindings | python2-dbus | python-dbus |
| libmlt-data | Some image and text resources for MLT | mlt, sdl_image | mlt, sdl1-image |
| python >= 2.7 < 3 | Language and interpreter | python2 | python |
| frei0r-plugins | Additional video filters | movit, frei0r-plugins | movit, frei0r |
| swh-plugins | Additional audio filters | sox, swh-plugins | sox, swh-plugins |
| python-gi-cairo | Gi Cairo bindings | python2-gobject | python-gobject |
| python-numpy | Math and arrays library | python2-numpy | numpy |
| python-pil | PIL image manipulation library | python2-pillow | python-pillow |
| librsvg2-common | svg support | librsvg | librsvg |
| gmic | framework for image processing | gmic | gmic |
| gir1.2-glib-2.0 | Glib | dbus-glib | dbus-glib |
| gir1.2-gtk-3.0 | Gtk toolkit | gtk3 | libgtk-3 |
| gir1.2-pango-1.0 | Pango text lib | pango | pango |
| gir1.2-gdkpixbuf-2.0 | Image support | gdk-pixbuf2 | gdk-pixbuf |
| | | | cairo |

¹ Version supplied by package manager lacks python bindings. Needs `{sox,frei0r,libexif,movit,sdl1,sdl1-image,alsa-lib,pulseaudio}-devel` to build.
² Patch `src/swig/python/build` to use `python2` instead of `python`, then run `configure` with `--swig-languages=python`. Before running `make install`, add `cp python/_mlt.so python/mlt.py python/mlt_wrap.o '$(prefix)/lib/python2.7/'` to `src/swig/Makefile`'s `install` rule.

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
.
