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

import usb1

import time

import usbhidconfig
import usbhiddrivers

# how often should the USB input handler function be called?
# set this too high, and there will be noticable latency in processing input
# set this too low, and performance of everything else will suffer
HANDLER_FREQUENCY_MSEC = 10

# number of USB transfers in flight
USB_TRANSFERS_IN_FLIGHT = 10

# USB HID driver context reference
usb_driver_ctx = None

# This is our reference to the GTK timeout handler
usb_hid_input_id = -1

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

    global usb_driver_ctx
    global usb_hid_input_id

    if usb_driver_ctx is not None:
        raise UsbHidError("USB HID device already in use")

    if usb_hid_input_id != -1:
        raise UsbHidError("USB HID device already in use")

    # create the USB HID driver context
    try:
        usb_driver_ctx = UsbHidDriverContext(device_config_name)
    except UsbHidError as e:
        raise e
    except Exception as e:
        raise UsbHidError("Error connecting to USB HID device: %s" % \
                          (str(e),)) from e

    # set a recurring timeout to call our input handler function
    usb_hid_input_id = GObject.timeout_add(HANDLER_FREQUENCY_MSEC,
                                           __gtk_usb_driver_handler)

def stop_usb_hid_input():
    """
    Disconnect from any USB HID device that we may be connected to.

    This function is idempotent, and it is safe to call whether or not a
    USB HID device is currently connected or not.

    """

    global usb_driver_ctx
    global usb_hid_input_id

    # if no device is in use, just return
    if usb_driver_ctx is None:
        return
    if usb_hid_input_id == -1:
        return

    GObject.source_remove(usb_hid_input_id)
    usb_hid_input_id = -1

    # disconnect from the USB device
    try:
        usb_driver_ctx.disconnect()
    except Exception as e:
        # best effort
        print("Error disconnecting from USB HID device: %s" % (str(e),))

    usb_driver_ctx = None

def _handle_usb_transfer(usb_transfer):
    """
    USB transfer handler.

    This is the handler function that is repeatedly called once we're up and
    running, to read input from the USB device, and dispatch it to the driver.

    It's a free function outside of the UsbHidDriverContext class, because
    the usb1 module API requires a callback function that accepts one
    argument to be passed into it.

    Accepts a usb1.USBTransfer instance as an argument (which is required
    by the callback API).

    Does not return a value.

    Examines the USB transfer status, and takes appropriate action, which
    can include handing off data to the device driver, or handling errors.

    Resubmits the transfer again (to continue the request/response cycle) in
    most cases, unless there is some sort of error that we can't recover from.

    """

    global usb_driver_ctx

    # transfer status
    #
    # corresponds to the libusb_transfer_status enum in libusb.h,
    # and top-level constants in the usb1 module.
    #
    # this handler function uses the numbers directly, rather than the
    # symbols, because in practice it seems to be possible for the
    # usb1.TRANSFER_* symbols to be undefined in this function when
    # the program is on its way down.
    #
    # possible values:
    #
    # TRANSFER_COMPLETED = 0
    # TRANSFER_ERROR = 1
    # TRANSFER_TIMED_OUT = 2
    # TRANSFER_CANCELLED = 3
    # TRANSFER_STALL = 4
    # TRANSFER_NO_DEVICE = 5
    # TRANSFER_OVERFLOW = 6
    #
    status = usb_transfer.getStatus()

    if usb_driver_ctx is None:
        return

    # we read some data
    if status == 0:
        # get a reference to the contents of the buffer
        buffer = usb_transfer.getBuffer()

        # get the number of bytes that we actually received
        length = usb_transfer.getActualLength()

        # the data we actually got might be a subset of what's in the buffer
        data = buffer[:length]

        # pass the data that we read off to the driver
        try:
            usb_driver_ctx.driver.handle_input(data)
        except Exception as e:
            print("USB HID driver input handler error: %s" % (str(e),))

        # resubmit transfer
        usb_transfer.submit()
        return

    # timeout
    elif status == 2:
        # resubmit transfer
        usb_transfer.submit()
        return

    # transfer cancelled
    elif status == 3:
        # this is the normal clean shutdown condition
        # don't retry or log errors
        return

    # all other unexpected errors
    else:
        # transfer error
        if status == 1:
            print("USB transfer error")

        # transfer stall
        elif status == 4:
            print("USB transfer stall")

        # no device
        elif status == 5:
            print("USB HID device not found")

        # overflow
        elif status == 6:
            print("USB transfer overflow")

        # try to shut down the USB HID subsystem cleanly
        stop_usb_hid_input()

        return

def __gtk_usb_driver_handler():
    """
    GTK handler function to read new USB HID input and map it to actions.

    Accepts no arguments.

    Called by GTK periodically once the driver is set up and running.

    Returns True to let GTK know that it should reschedule this same
    handler function to run again at the next interval.

    """

    global usb_driver_ctx

    usb_driver_ctx.handle_input()

    return True

class UsbHidError(Exception):
    """
    Represents a USB HID error.

    """

    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class UsbHidDriverContext:
    """
    USB HID Driver Context

    This class represents the context of a connection to a USB HID device.

    """

    def __init__(self, device_config_name):
        """
        Constructor.

        Accepts a device config name (e.g. contour_design_shuttlexpress).

        Finds and loads the driver configuration, and connects to the specified
        device.

        Raises a UsbHidError exception if an error occurs.

        """

        # device config name and associated driver
        self.device_config_name = device_config_name
        self.driver = None

        # device metadata extracted from the device config
        self.vendor_id = None
        self.product_id = None
        self.configuration = None
        self.interface = None
        self.endpoint_in = None
        self.endpoint_out = None

        # usb1.USBContext (top-level entry point into libusb)
        self.usb_ctx = usb1.USBContext()
        # usb1.USBDeviceHandle (reference to the device we want to read from)
        self.usb_device_handle = None
        # list of integers representing USB interfaces to reattach on shutdown
        self.reattach_kernel_interfaces = []
        # list of USBTransfer instances in flight
        self.transfers = []

        # load the driver based on the config name
        self.__load_driver()

        # connect to the USB device
        self.__connect()

    def __load_driver(self):
        # find the driver based on the device config name
        self.driver = usbhiddrivers.get_usb_driver(self.device_config_name)

        # get the USB configuration/interface/endpoints from the driver
        # these numbers define which part of the USB device tree we'll read from
        self.vendor_id = self.driver.get_usb_vendor_id()
        self.product_id = self.driver.get_usb_product_id()
        self.configuration = self.driver.get_usb_configuration()
        self.interface = self.driver.get_usb_interface()
        self.endpoint_in = self.driver.get_usb_endpoint_in()
        self.endpoint_out = self.driver.get_usb_endpoint_out()

        print("Initializing USB HID driver: %s" % (self.driver.get_name()))

    def __get_endpoint_max_packet_size(self, endpoint_address):
        # traverse through the USB device hierarchy to find the max packet size
        # for the given endpoint address on our device

        max_packet_size = None

        # go through every USB device on the system that we can see
        for usb_device in self.usb_ctx.getDeviceIterator(skip_on_error=True):
            # if we find the device that we're trying to talk to,
            # by vendor_id / product_id...
            if (self.vendor_id == usb_device.getVendorID()):
                if (self.product_id == usb_device.getProductID()):

                    # go through each configuration on the device
                    configuration_number = 0
                    for usb_configuration in usb_device:
                        # if this is the configuration we are interested in
                        if self.configuration == configuration_number:
                            # go through each interface on the configuration
                            interface_number = 0
                            for usb_interface in usb_configuration:
                                # if this is the interface we are interested in
                                if self.interface == interface_number:
                                    # go through each setting on the interface
                                    for usb_interface_setting in usb_interface:
                                        # go through each endpoint on the setting
                                        for usb_endpoint in usb_interface_setting:
                                            # if this is the endpoint address we are searching for
                                            if endpoint_address == usb_endpoint.getAddress():
                                                max_packet_size = usb_endpoint.getMaxPacketSize()

                            interface_number += 1

                        configuration_number += 1

        return max_packet_size

    def __detach_kernel_drivers(self):
        # go through every USB device on the system that we can see
        for usb_device in self.usb_ctx.getDeviceIterator(skip_on_error=True):
            # if we find the device that we're trying to talk to,
            # by vendor_id / product_id...
            if (self.vendor_id == usb_device.getVendorID()):
                if (self.product_id == usb_device.getProductID()):

                    # go through each configuration on the device
                    configuration_number = 0
                    for usb_configuration in usb_device:
                        # if this is the configuration we are interested in
                        if self.configuration == configuration_number:
                            # go through each interface on the configuration
                            interface_number = 0
                            for usb_interface in usb_configuration:
                                # detach kernel driver, if necessary, and remember it for later
                                if self.usb_device_handle.kernelDriverActive(interface_number):
                                    self.usb_device_handle.detachKernelDriver(interface_number)
                                    self.reattach_kernel_interfaces.append(interface_number)

                                interface_number += 1

                        configuration_number += 1

    def __reattach_kernel_drivers(self):
        # go through every interface that we detached from its pre-existing
        # kernel driver and reattach them
        for interface_number in self.reattach_kernel_interfaces:
            self.usb_device_handle.attachKernelDriver(interface_number)

    def __connect(self):
        global USB_TRANSFERS_IN_FLIGHT
        global _handle_usb_tranfer

        # get endpoint in max packet size
        endpoint_in_max_packet_size = \
            self.__get_endpoint_max_packet_size(self.endpoint_in)

        # the endpoint in max packet size is determined by reading metadata
        # from the device, so if it's not available, the device isn't here
        if endpoint_in_max_packet_size is None:
            raise UsbHidError("USB HID device not found")

        # USBDeviceHandle
        self.usb_device_handle = \
            self.usb_ctx.openByVendorIDAndProductID(self.vendor_id,
                                                    self.product_id,
                                                    skip_on_error=True)

        if self.usb_device_handle is None:
            raise UsbHidError("Can not open USB HID device")

        # detach kernel driver for each interface, etc.
        self.__detach_kernel_drivers()

        # claim exclusive access to the configured interface number
        self.usb_device_handle.claimInterface(self.interface)

        # set up a number of USB transfers to keep in-flight
        for _ in range(USB_TRANSFERS_IN_FLIGHT):
            # USBTransfer
            transfer = self.usb_device_handle.getTransfer()

            # set up transfer for interrupt use
            transfer.setInterrupt(self.endpoint_in,
                                  endpoint_in_max_packet_size,
                                  _handle_usb_transfer)

            # submit the transfer
            transfer.submit()

            # keep a reference to the transfer so we can refer to it later
            self.transfers.append(transfer)

    def disconnect(self):
        """
        Disconnect from the USB HID device.

        """

        # cancel all transfers
        for transfer in self.transfers:
            transfer.cancel()

        # wait for a while for the transfers to be fully cancelled,
        # but don't block indefinitely. this is expected to break early
        # most of the time, but we don't want to hang the program on the
        # way down if there is some sort of unexpected issue.
        for _ in range(100):
            all_cancelled = True
            for transfer in self.transfers:
                if transfer.isSubmitted():
                    self.usb_ctx.handleEventsTimeout(0)
                    if transfer.getStatus() != usb1.TRANSFER_CANCELLED:
                        all_cancelled = False

            if all_cancelled == True:
                break

            time.sleep(0.05)

        # reset the device
        self.usb_device_handle.resetDevice()

        # relinquish access to the configured interface number
        self.usb_device_handle.releaseInterface(self.interface)

        # reattach any kernel drivers that were detached when we connected
        self.__reattach_kernel_drivers()

        # close the device handle
        self.usb_device_handle.close()

        # Close the USB context
        self.usb_ctx.close()

    def handle_input(self):
        """
        Handle any pending input that might be waiting for us to read.

        Examines all of the USB transfers, and checks to see if any of
        them are ready to read. If so, it triggers the event handler
        function for any of the transfers that are ready.

        This function is non-blocking.

        """

        for transfer in self.transfers:
            try:
                if transfer.isSubmitted():
                    # handle any pending transfer events
                    # (non-blocking, no timeout, returns instantly)
                    self.usb_ctx.handleEventsTimeout(0)

            except usb1.USBErrorInterrupted as e:
                pass

