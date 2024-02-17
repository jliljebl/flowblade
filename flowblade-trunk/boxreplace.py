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
        
        print(file_path)
        
        lines = None
        new_lines = []
        changed = False

        with open(file_path, "rt") as f:
            lines = f.readlines()

        for line in lines:
            
            replaced_line = line.replace(' Gtk.VBox', ' gtkbox.VBox')
            if line != replaced_line:
                #print(filename, replaced_line)
                line_count += 1
                changed_files.append(file_path)
                line = replaced_line
                changed = True

            replaced_line = line.replace(' Gtk.HBox', ' gtkbox.HBox')
            if line != replaced_line:
                #print(filename, replaced_line)
                line_count += 1
                changed_files.append(file_path)
                line = replaced_line
                changed = True

            new_lines.append(line)
        
        if changed == True:
            with open(file_path, "w") as f:
                f.writelines(new_lines)  




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

        print(file_path)
        
        changed = False
        for line in lines:
            new_lines.append(line)
            if line.startswith("from gi.repository import") and changed == False:
                print(line)
                if "Gtk" in line:
                    print("line has Gtk import")
                    new_lines.append("import gtkbox\n")
                    changed = True

        if changed == True:
            with open(file_path, "w") as f:
                print("Witing lines")
                f.writelines(new_lines)  



