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

            replaced_line = line.replace(' Gtk.HBox', ' gtkbox.HBox')
            if line != replaced_line:
                print(filename, replaced_line)
                line_count += 1
                changed_files.append(file_path)
                line = replaced_line

            new_lines.append(line)

        f = open(file_path, "a")
        f.writelines(new_lines)
        f.close()

print(line_count)
print(set(changed_files))


