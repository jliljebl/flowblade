"""
    Flowblade Movie Editor is a nonlinear video editor.
    Copyright 2022 Janne Liljeblad and contributors.

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
USB Human Interface Device Config File Support.

Finding, parsing, and making sense of USB HID config files.

"""

import os
import xml.dom.minidom

import appconsts
import respaths
import userfolders

def get_config(config_name):
    """
    Find and load a USB HID config, using a config name.

    Accepts a config name, which is a base name for an XML file, without the
    .xml extension, or any other path information.

    Finds and loads a config file matching this description, if one exists.

    Returns a populated UsbHidConfig object, or None if no config was found.

    """

    try:
        config_file = find_config_file_path_by_config_name(config_name)
        if config_file is not None:
            if os.path.exists(config_file):
                return load_config(config_file)
    except Exception as e:
        print("Error loading USB HID config: %s" % (str(e),))

    return None

def get_usb_hid_device_config_metadata_list():
    """
    Returns a list of UsbHidDeviceConfigMetadata entries detailing all
    of the devices that we can find configs for.

    This list is sorted, so that the GUI and editorpersistance.prefs
    can rely on pulling indexes out of the returned list if it is
    called twice in short succession. As long as the files don't get
    changed around on disk within the window of time between selecting
    a device in the preferences dialog and hitting OK, the index will
    stay the same.

    """

    # map of base config file name -> UsbHidDeviceConfigMetadata
    map = {}

    for base_dir in [respaths.USBHID_DRIVERS_PATH,
                     userfolders.get_data_dir() + "/" + appconsts.USER_USBHID_DIR]:
        for dirent in os.listdir(base_dir):
            config_file = os.path.join(base_dir, dirent)

            if os.path.isfile(config_file) and config_file.endswith(".xml"):
                (base_file, extension) = os.path.splitext(os.path.basename(config_file))

                try:
                    config = load_config(config_file)
                    config_metadata = UsbHidDeviceConfigMetadata(base_file, config.name)
                    map[base_file] = config_metadata
                except Exception as e:
                    # only show valid config files
                    print("Error loading USB HID config file %s: %s" % (config_file, str(e)))
                    continue

    # create a sorted list to return
    # the sorting is important, because far-flung parts of the code are
    # indexing into the returned list over multiple invocations
    config_metadata_list = []
    for key in sorted(map):
        config_metadata_list.append(map[key])

    return config_metadata_list

def find_config_file_path_by_config_name(config_name):
    """
    Find the most suitable USB HID device config file, given a config name
    (e.g. "contour_design_shuttlexpress").

    Return the path to the config file (e.g.
    "/path/to/contour_design_shuttlexpress.xml"), or None if no config
    file could be found.

    """

    filename = None

    for base_dir in [respaths.USBHID_DRIVERS_PATH,
                     userfolders.get_data_dir() + "/" + appconsts.USER_USBHID_DIR]:
        candidate_filename = os.path.join(base_dir, config_name + ".xml")
        if os.path.exists(candidate_filename):
            filename = candidate_filename

    return filename

def load_config(config_file):
    """
    Load and parse a USB HID XML config file, and return a populated
    UsbHidConfig object.

    All manner of XML exceptions might bubble up if anything goes wrong.

    """

    dom = xml.dom.minidom.parse(config_file)

    # required fields
    root = dom.getElementsByTagName("flowblade")[0]
    name = root.getElementsByTagName("name")[0].childNodes[0].data
    driver = root.getElementsByTagName("driver")[0].childNodes[0].data
    usb = root.getElementsByTagName("usb")[0]
    vendor_id_str = usb.getElementsByTagName("vendor_id")[0].childNodes[0].data
    product_id_str = usb.getElementsByTagName("product_id")[0].childNodes[0].data
    configuration_str = usb.getElementsByTagName("configuration")[0].childNodes[0].data
    interface_str = usb.getElementsByTagName("interface")[0].childNodes[0].data
    endpoint_in_str = usb.getElementsByTagName("endpoint_in")[0].childNodes[0].data

    # optional fields
    endpoint_out_str = None
    endpoint_out_tag = usb.getElementsByTagName("endpoint_out")
    if endpoint_out_tag:
        endpoint_out_str = endpoint_out_tag[0].childNodes[0].data

    # coerce strings into proper types
    usb_vendor_id  = int("0x" + vendor_id_str,  16)
    usb_product_id = int("0x" + product_id_str, 16)
    usb_configuration = int(configuration_str)
    usb_interface = int(interface_str)
    usb_endpoint_in = int("0x" + endpoint_in_str, 16)
    usb_endpoint_out = None
    if endpoint_out_str is not None:
        usb_endpoint_out = int("0x" + endpoint_out_str, 16)

    # create config object
    config = UsbHidConfig(driver=driver,
                          name=name,
                          usb_vendor_id=usb_vendor_id,
                          usb_product_id=usb_product_id,
                          usb_configuration=usb_configuration,
                          usb_interface=usb_interface,
                          usb_endpoint_in=usb_endpoint_in,
                          usb_endpoint_out=usb_endpoint_out)

    # go through keymap entries and assign actions in the config
    keymap = root.getElementsByTagName("keymap")[0]
    events = keymap.getElementsByTagName("event")
    for event in events:
        key = int(event.childNodes[0].data)
        handler = event.getAttribute("code")

        config.set_action(key, handler)

    return config

class UsbHidDeviceConfigMetadata:
    """
    High-level information about an available USB HID device config.

    Just enough to show up in GUI menus for selection, and to capture
    the device config name.

    """

    def __init__(self, device_config_name, name):
        """
        Constructor.

        Accepts device_config_name, and name.

        device_config_name is the base config name that represents the driver
        config (e.g. contour_design_shuttlexpress). It is the base name of
        an XML file, without any path information. This is used by
        usbhid.start_usb_hid_input() to find the config file by name and
        connect to the device.

        name is the human-readable name of the device (e.g. Contour Design
        ShuttleXpress).

        """

        self.device_config_name = device_config_name
        self.name = name


class UsbHidConfig:
    """
    Data structure class representing the contents of the config,
    but without being intertwined with the config file parsing itself.

    """

    def __init__(self,
                 driver,
                 name,
                 usb_vendor_id,
                 usb_product_id,
                 usb_configuration,
                 usb_interface,
                 usb_endpoint_in,
                 usb_endpoint_out):

        self.driver = driver
        self.name = name
        self.usb_vendor_id = usb_vendor_id
        self.usb_product_id = usb_product_id
        self.usb_configuration = usb_configuration
        self.usb_interface = usb_interface
        self.usb_endpoint_in = usb_endpoint_in
        self.usb_endpoint_out = usb_endpoint_out

        # map of int key numbers -> action strings
        # (e.g. 7 -> "play_pause")
        self.key_to_action = {}

    def set_action(self, key, action):
        """
        Map the given action to the specified key.

        Key is an integer, representing a button on the device.

        Action is a string corresponding to a named action available
        in the targetactions module.

        """

        self.key_to_action[key] = action

    def get_action(self, key):
        """
        Get the named action associated with the given key, or None
        if no action is mapped to this key.

        """

        if key in self.key_to_action:
            return self.key_to_action[key]

        return None

