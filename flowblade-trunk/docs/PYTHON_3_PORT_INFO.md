# PYTHON 3 STATUS OF DEPENDENCIES

tl;dr: All dependencies are Python 3 compatible although __python-mlt__ might not be adequately tested.

| **Ubuntu package name** | **Description** | **Python 3 available** |
|:-------------------------------|:----------------|:--------------|
| python-gi | GTK3 Python bindings | **YES, python3-gi**  |
| python-mlt | MLT python bindings, this pulls in MLT | **YES** |
| python-dbus | dbus python bindings | **YES, python3-dbus** |
| libmlt-data | Some image and text resources for MLT |**NOT PYTHON** |
| frei0r-plugins | Additional video filters | **NOT PYTHON** |
| swh-plugins | Additional audio filters | **NOT PYTHON**  |
| python-gi-cairo | Gi Cairo bindings | **YES, python3-gi-cairo** |
| python-numpy | Math and arrays library |  **YES** |
| python-pil | PIL image manipulation library | **YES, python-pil is Pillow fork and should work** |
| librsvg2-common | svg support | **NOT PYTHON**  |
| gmic | framework for image processing | **NOT PYTHON**  |
| gir1.2-glib-2.0 | Glib | **YES, this is same for Python 3 and used by python3-gi package**|
| gir1.2-gtk-3.0 | Gtk toolkit | **YES, this is same for Python 3 and used by python3-gi package** |
| gir1.2-pango-1.0 | Pango text lib | **YES, this is same for Python 3 and used by python3-gi package** |
| gir1.2-gdkpixbuf-2.0 | Image support | **YES, this is same for Python 3 and used by python3-gi package** |


# PYTHON 3 STATUS OF THIS REPO
[flake8](http://flake8.pycqa.org) flags 61 files as containing __E999 SyntaxError: invalid syntax__ (`flake8 . --select=E999`)
