# RUNNING FLOWBLADE 2.4

## MLT 6.18 REQUIRED

Flowblade 2.4 is running in Python 3 and requires MLT version that supports Python 3 bindigs. MLT 6.18 is the first version that fully supports all features required by Flowblade.

(MLT 6.16 does provide Python 3 bindings but does not support one part of API needed to run Flowblade successfully)

## PYTHON 3.7 OR HIGHER RECOMMENDED

Python 3 port of Flowblade was developed and tested on Python version 3.7. 

During development it was discovered that Python 3.6 required some Gtk objects to be instantiated with using only named parameters in constructors. We fixed all cases that were shown to cause problems but did not try to fix every possible instance of Gtk object being created in the codebase.

Therefore we recommend Python versions 3.7 or later for running Flowblade.


