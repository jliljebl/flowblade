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
USB Human Interface Device support.

Top-level USB HID interface for the main program to deal with.

This module deals with setting up, tearing down, and communicating with a USB
device at a low level. Raw USB communications happen here. Decoding of the
input from the device and triggering action happens in the individual USB HID
drivers in the usbhiddrivers module.

"""

from gi.repository import GObject

import usb.core
import usb.util

import usbhidconfig
import usbhiddrivers

# how often should the USB input handler function be called?
# set this too high, and there will be noticable latency in processing input
# set this too low, and performance of everything else will suffer
HANDLER_FREQUENCY_MSEC = 5

# selected usb.core.USBError.errno values we care about
USB_CODE_NO_SUCH_DEVICE = 19
USB_CODE_TIMEOUT = 110

# this is our reference to the GTK timeout handler
usb_hid_input_id = -1

# USB device and driver references
usb_device = None
usb_read_endpoint = None
usb_write_endpoint = None
usb_driver = None

# should we try to re-attach a kernel driver for the interface(s) on the
# selected USB device when we detach our userspace driver from it?
__reattach_kernel_driver_interfaces = []

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

    This function is a pass-through so that the top parts of the program
    can just import usbhid, and not all the other modules.

    """

    return usbhidconfig.get_usb_hid_device_config_metadata_list()


def start_usb_hid_input(device_config_name):
    """
    Connect to the specified USB HID device by name, and start allowing it
    to control the program.

    Accepts a Flowblade USB HID device config name
    (e.g. "contour_design_shuttle").

    Raises a UsbHidError if an error occurs connecting to the device.

    """

    global usb_hid_input_id

    # if a device is already up and running with a timeout handler function,
    # don't add another one
    if usb_hid_input_id != -1:
        raise UsbHidError("USB HID device already in use")

    # connect to the USB device
    _attach_device(device_config_name)

    # set a recurring timeout to call our input handler function
    usb_hid_input_id = GObject.timeout_add(HANDLER_FREQUENCY_MSEC,
                                           __handle_usb_input)

def stop_usb_hid_input():
    """
    Disconnect from any USB HID device that we may be connected to.

    This function is idempotent, and it is safe to call whether or not a
    USB HID device is currently connected or not.

    """

    global usb_hid_input_id

    # if no device is in use, just return
    if usb_hid_input_id == -1:
        return

    # stop the input handler timeout function calls
    GObject.source_remove(usb_hid_input_id)
    usb_hid_input_id = -1

    # disconnect from the USB device
    _detach_current_device()

# these are internal private helper functions that other modules in the
# program should not connect to.

def _attach_device(config_name):
    """
    Initialize the USB HID device by config name.

    Accepts a Flowblade USB HID device config name.

    Finds and connects to the specified device.

    Sets usb_* global variables that allow other functions to communicate
    with the device in the future.

    Raises a UsbHidError if there is a problem connecting to the device.

    """

    global usb_device
    global usb_read_endpoint
    global usb_write_endpoint
    global usb_driver
    global __reattach_kernel_driver_interfaces

    # get the Flowblade USB HID device driver by name
    usb_driver = usbhiddrivers.get_usb_driver(config_name)

    # get the USB configuration/interface/alternate/endpoint from the driver
    # these numbers define which part of the USB device tree we'll read from
    usb_vendor_id = usb_driver.get_usb_vendor_id()
    usb_product_id = usb_driver.get_usb_product_id()
    usb_configuration = usb_driver.get_usb_configuration()
    usb_interface = usb_driver.get_usb_interface()
    usb_alternate = usb_driver.get_usb_alternate()
    usb_endpoint_in = usb_driver.get_usb_endpoint_in()
    usb_endpoint_out = usb_driver.get_usb_endpoint_out()

    # find the USB device
    usb_device = usb.core.find(idVendor=usb_vendor_id,
                               idProduct=usb_product_id)

    if usb_device is None:
        err = "USB HID device config '%s' not found" % (config_name)
        print(err)
        raise UsbHidError(err)

    # detach the kernel driver for each interface, if necessary,
    # so we can control the device. to be nice, we will also remember if
    # we detached a kernel driver for each interface, so we can try to
    # set things back the way they were when the program closes
    try:
        for usb_config in usb_device:
            for interface_index in range(usb_config.bNumInterfaces):
                if usb_device.is_kernel_driver_active(interface_index):
                    usb_device.detach_kernel_driver(interface_index)
                    __reattach_kernel_driver_interfaces.append(interface_index)
    except usb.core.USBError as e:
        raise UsbHidError(
            "Kernel won't allow USB HID driver to be detached for %s: %s" % \
            (usb_driver.get_name(), str(e)))

    # initialize the configuration of the USB device
    try:
        usb_device.set_configuration()
    except usb.core.USBError as e:
        raise UsbHidError("Can not configure USB device: '%s'" % (str(e),))

    # reset the USB device (just in case)
    try:
        usb_device.reset()
    except usb.core.USBError as e:
        raise UsbHidError("Can not reset USB device: '%s'" % (str(e),))

    # lsusb -v
    # https://beyondlogic.org/usbnutshell/usb5.shtml
    #
    #usb_device               <class 'usb.core.Device'>
    #usb_device[0]            <class 'usb.core.Configuration'>
    #usb_device[0][(0,0)]     <class 'usb.core.Interface'>
    #usb_device[0][(0,0)][0]  <class 'usb.core.Endpoint'>

    # get the endpoint within the device that we want to read from
    usb_read_endpoint = usb_device[usb_configuration][(usb_interface,usb_alternate)][usb_endpoint_in]

    # make a ByteReader with the IN endpoint available to the driver
    # (ByteReader references global usb_read_endpoint so it can be invalidated in one place)
    usb_driver.set_byte_reader(ByteReader())

    # if we have an out endpoint, connect to it as well
    if usb_endpoint_out is not None:
        usb_write_endpoint = usb_device[usb_configuration][(usb_interface,usb_alternate)][usb_endpoint_out]

        # make a ByteWriter with the OUT endpoint available to the driver
        # (ByteWriter references global usb_write_endpoint so it can be invalidated in one place)
        usb_driver.set_byte_writer(ByteWriter())

    print("Found USB HID device: %s" % (usb_driver.get_name()))

    # run the handle connect phase of driver initialization
    try:
        usb_driver.handle_connect()
    except Exception as e:
        raise UsbHidError("Error during USB HID driver initialization: %s" % (str(e),))

def _detach_current_device():
    """
    Detach from the currently attached USB HID device (if one is attached).

    Sets the same usb_* global variables that _attach_current_device()
    originally set back to None.

    Raises a UsbHidError if there is a problem disconnecting from the device.

    """

    global usb_device
    global usb_read_endpoint
    global usb_driver
    global __reattach_kernel_driver_interfaces

    if not usb_driver:
        return

    if not usb_device:
        return

    # run the handle disconnect phase of driver initialization
    try:
        usb_driver.handle_disconnect()
    except Exception as e:
        # best effort
        print("Error during USB HID driver disconnection: %s" % (str(e),))
        pass

    # defensive copy global reattach kernel driver interfaces list,
    # and consume it. if we fail this time, it's not likely to work next
    # time either.
    interface_indexes = []
    for interface_index in __reattach_kernel_driver_interfaces:
        interface_indexes.append(interface_index)
    __reattach_kernel_driver_interfaces = []

    try:
        for interface_index in interface_indexes:
            usb_device.attach_kernel_driver(interface_index)
    except usb.core.USBError as e:
        # best effort
        print("Error detaching USB device: %s" % (str(e),))
        pass

    usb_device = None
    usb_read_endpoint = None
    usb_write_endpoint = None
    usb_driver = None

def _handle_usb_read_error(e):
    """
    Handles usb.core.USBError exceptions within other exception handling
    blocks.

    Ignores timeout errors.

    If the device has gone missing, it tries to shut down the connection
    cleanly.

    All other errors are raised as usbhid.UsbHidError exceptions.

    """

    # ignore USB timeouts
    if USB_CODE_TIMEOUT == e.errno:
        pass

    # the USB device has probably been disconnected, try to clean up
    elif USB_CODE_NO_SUCH_DEVICE == e.errno:
        if usb_driver:
            print("USB HID device disconnected: %s" % (usb_driver.get_name()))
        else:
            print("USB HID device disconnected")

        # tear down any remaining references to the disconnected device
        stop_usb_hid_input()

    # unknown error
    else:
        raise UsbHidError("Error reading from USB device: '%s'" % (str(e),))

def _handle_usb_write_error(e):
    """
    Handles usb.core.USBError exceptions within other exception handling
    blocks.

    If the device has gone missing, it tries to shut down the connection
    cleanly.

    All other errors are raised as usbhid.UsbHidError exceptions.

    """

    # the USB device has probably been disconnected, try to clean up
    if USB_CODE_NO_SUCH_DEVICE == e.errno:
        if usb_driver:
            print("USB HID device disconnected: %s" % (usb_driver.get_name()))
        else:
            print("USB HID device disconnected")

        # tear down any remaining references to the disconnected device
        stop_usb_hid_input()

    # unknown error
    else:
        raise UsbHidError("Error writing to USB device: '%s'" % (str(e),))

def __handle_usb_input():
    """
    USB handler function. This gets called multiple times per second directly
    from a GObject timeout handler, once we attach to a USB HID device.

    This is the place where we read USB HID input data, and pass it off to the
    device drivers.

    """

    global usb_device
    global usb_read_endpoint
    global usb_driver

    try:
        # read raw data from the USB device
        # this will either return an array of byte values, or None
        data = usb_read_endpoint.read(usb_read_endpoint.wMaxPacketSize,
                                      timeout=1)

        # send raw input data into the driver
        if data is not None:
            usb_driver.handle_input(data)

    except usb.core.USBError as e:
        _handle_usb_read_error(e)

    return True


class UsbHidError(Exception):
    """
    Represents a USB HID error.

    """

    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class ByteReader:
    """
    Wrapper around low-level USB in endpoint.

    This class handles the direct connection with the USB libraries, and
    allows the individual drivers to just think in terms of reading bytes.

    Note that most reads of bytes are passed into the drivers using their
    handle_input() methods. This is for other reads, such as during
    the initial connection to the device.

    """

    def read(self):
        """
        Read bytes from the USB device.

        Returns the bytes read, or None if no bytes were available.

        """

        global usb_read_endpoint
        global _handle_usb_read_error

        if usb_read_endpoint is None:
            return None

        try:
            data = usb_read_endpoint.read(usb_read_endpoint.wMaxPacketSize,
                                          timeout=1)

            return data

        except usb.core.USBError as e:
            _handle_usb_read_error(e)

        return None


class ByteWriter:
    """
    Wrapper around low-level USB out endpoint.

    This class handles the direct connection with the USB libraries, and
    allows the individual drivers to just think in terms of writing bytes.

    """

    def write(self, byte_array):
        """
        Write bytes to the USB device.

        Accepts an array of bytes.

        Raises a usbhid.UsbHidError if the write can not be completed.

        """

        global usb_write_endpoint
        global _handle_usb_write_error

        if usb_write_endpoint is None:
            raise UsbHidError("USB write endpoint is not connected")

        try:
            usb_write_endpoint.write(byte_array)
        except usb.core.USBError as e:
            _handle_usb_write_error(e)

