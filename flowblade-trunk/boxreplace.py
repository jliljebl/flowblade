#!/usr/bin/env python3

import fnmatch
import glob
import os
import sys



# Get launch script dir
launch_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
src_dir = launch_dir + "/Flowblade"

line_count = 0
changed_files = []
for root, dirnames, filenames in os.walk(src_dir):
    for filename in filenames:
        
        if filename.endswith(".py") == False:
            continue
        
        file_path = os.path.join(root, filename)
        
        lines = None
        new_lines = []
        changed = False

        with open(file_path, "rt") as f:
          lines = f.readlines()

        for line in lines:
            
            replaced_line = line.replace(' Gtk.VBox', ' gtkbox.VBox')
            if line != replaced_line:
                print(filename, replaced_line)
                line_count += 1
                changed_files.append(file_path)
                line = replaced_line
                changed = True

            replaced_line = line.replace(' Gtk.HBox', ' gtkbox.HBox')
            if line != replaced_line:
                print(filename, replaced_line)
                line_count += 1
                changed_files.append(file_path)
                line = replaced_line
                changed = True

            new_lines.append(line)
        
        if changed == True:
            f = open(file_path, "a")
            f.writelines(new_lines)
            f.close()


changed_files = set(changed_files))

for cfile in changed_files:

    with open(cfile, "rt") as f:
      lines = f.readlines()

    for i in range(0, len(lines)):
        line = lines[i]
        if line.startswith("from gi.repository import") and ("Gtk" in line):
            lines.insert(i + 1, "import gtkbox")
            break
            
    f = open(cfile, "a")
    f.writelines(lines)
    f.close()


