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
USB Human Interface Device Drivers.

This module contains device drivers for various jog/shuttle devices.

Low-level connections to the USB devices themselves happen in the usbhid
module. The focus here is on providing drivers for individual devices,
so that the usbhid module can look them up by name, read bytes from them
in an undifferentiated fashion, and call handler methods on the individual
drivers here.

"""

import usbhid
import usbhidconfig


targetactions_get_handler_by_name_func = None
targetactions_move_player_position_func = None
targetactions_variable_speed_playback_func = None


def get_usb_driver(config_name):
    """
    Maps Flowblade USB HID driver names to the instantiation of Python
    classes that implement the necessary methods to act as a USB HID driver.

    Accepts a device config name (e.g. "contour_design_shuttlexpress").

    Returns a valid device driver instance, or raises a usbhid.UsbHidError
    if the driver does not exist.

    """

    # load the config
    config = usbhidconfig.get_config(config_name)

    # if we have a config, instantiate the right driver for it,
    # and pass the config into the driver to let it figure out the rest
    if config:
        try:
            if config.driver == "contour_design_shuttle":
                return ContourDesignShuttle(config)
        except Exception as e:
            raise usbhid.UsbHidError(
                "Error loading USB HID driver %s using config %s: %s" % \
                (config.driver, config_name, str(e)))

    raise usbhid.UsbHidError("Could not find USB HID config: %s" % (str(config_name),))

class Jog:
    """
    Represents a jog wheel, using an 8 bit rotary encoder.

    Triggers prev/next frame actions when the wheel is rotated.

    """

    def __init__(self):
        self.prev_value = None

    def set_encoder(self, value):
        """
        Handler method to accept the current jog encoder value,
        and trigger the appropriate action.

        """

        # the first time we get any input whatsoever from the device,
        # we have no idea which of the 256 encoder values the jog might
        # be starting from. therefore, we can only detect jog wheel
        # movement once we have two values to compare
        if self.prev_value is not None:
            # if the jog wheel has moved, figure out which direction,
            # and trigger the appropriate action
            if value != self.prev_value:
                # common case: figure out how far the jog encoder wheel moved,
                # and in which direction
                delta = value - self.prev_value

                # the jog encoder wheel is a uint8, and it can wrap around
                # detect the wrap around and set the delta accordingly

                # we're moving left, and wrapped around
                if (value > 200) and (self.prev_value < 50):
                    delta = value - 256 - self.prev_value

                # we're moving right, and wrapped around
                elif (value < 50) and (self.prev_value > 200):
                    delta = value + 256 - self.prev_value

                # move the player position by the requested number of frames,
                # and in the appropriate direction
                targetactions_move_player_position_func(delta)

        # remember the previous value to detect state transitions next time
        self.prev_value = value


class Shuttle:
    """
    Represents a shuttle, using an 8 bit rotary encoder.

    """

    def __init__(self, stop_encoder_value, encoder_value_playback_speed_map):
        """
        Constructor.

        Accepts a stop_encoder_value, which is the value of the shuttle encoder
        corresponding to the center or stop position.

        Accepts an encoder_value_playback_speed_map, which is a map of all
        possible shuttle encoder values as keys, with floating point variable
        playback speeds as values. When the shuttle rotary encoder is turned
        to the value matching the key, variable speed playback is set to the
        corresponding value in the map.

        """

        self.prev_value = stop_encoder_value
        self.encoder_value_playback_speed_map = encoder_value_playback_speed_map

    def set_encoder(self, value):
        """
        Handler method to accept the current shuttle encoder value,
        and trigger the appropriate action.

        """

        # if the shuttle value has changed
        if value != self.prev_value:
            # figure out which speed we should use based on shuttle position
            speed = self.encoder_value_playback_speed_map[value]

            # trigger variable speed playback
            targetactions_variable_speed_playback_func(speed)

        # remember the previous value to detect state transitions next time
        self.prev_value = value


class Key:
    """
    Represents a key, or button, that can be pressed on a USB HID device.

    Detects key presses, and can trigger a handler function accordingly.

    """

    def __init__(self, on_press_handler):
        """
        Constructor.

        Accepts an on_press_handler, which is a reference to a function
        that should be executed when a key press event is detected.
        If no handler is defined, then None should be pass in as an
        argument instead.

        """

        self.on_press_handler = on_press_handler
        self.prev_pressed = False

    def set_pressed(self, pressed):
        """
        Handler method to accept the current key press state as a boolean.

        If the key has an on_press_handler, and a key press is detected,
        the handler is executed.

        """

        if self.on_press_handler is not None:
            if pressed and not self.prev_pressed:
                self.on_press_handler()

        self.prev_pressed = pressed


class UsbHidDriver:
    """
    Base class for all USB HID drivers.

    """

    def __init__(self, config):
        """
        Base class constructor.

        Accepts a usbhidconfig.UsbHidConfig instance.

        """

        # usbhidconfig.UsbHidConfig
        self.config = config

        # human-readable name of the device (e.g. Contour Design ShuttleXpress)
        self.name = config.name

        # USB vendor ID / product ID
        self.usb_vendor_id = config.usb_vendor_id
        self.usb_product_id = config.usb_product_id

        # zero-based indexes to traverse down the USB tree and find the
        # endpoints on the device.
        # usb_endpoint_out is optional, and can be None
        self.usb_configuration = config.usb_configuration
        self.usb_interface = config.usb_interface
        self.usb_endpoint_in = config.usb_endpoint_in
        self.usb_endpoint_out = config.usb_endpoint_out

    def get_name(self):
        """
        Get the human-readable name of the device.

        """

        return self.name

    def get_usb_vendor_id(self):
        """
        Get the USB vendor ID for the device.

        """

        return self.usb_vendor_id

    def get_usb_product_id(self):
        """
        Get the USB product ID for the device.

        """

        return self.usb_product_id

    def get_usb_configuration(self):
        """
        Get the USB configuration index (zero-based).

        """

        return self.usb_configuration

    def get_usb_interface(self):
        """
        Get the USB interface index (zero-based) under the configuration.

        """

        return self.usb_interface

    def get_usb_endpoint_in(self):
        """
        Get the USB in endpoint index (zero-based) under the interface.

        """

        return self.usb_endpoint_in

    def get_usb_endpoint_out(self):
        """
        Get the USB out endpoint index (zero-based) under the interface.

        """

        return self.usb_endpoint_out

    def handle_connect(self):
        """
        Handle the initial connection to the device.

        The ByteReader and ByteWriter can optionally be used here to perform
        any sort of initialization or startup procedure necessary to get the
        device ready.

        The low-level connection has already been established in usbhid by
        this time. This method is limited to reading and writing bytes from
        endpoint(s) that have already been established.

        """

        # default implementation does nothing
        pass

    def handle_disconnect(self):
        """
        Handle disconnection from the device.

        The ByteReader and ByteWriter can optionally be used here to perform
        any sort of clean shutdown procedure that might be necessary to
        release the device.

        The low-level connection has already been established in usbhid by
        this time. This method is limited to reading and writing bytes from
        endpoint(s) that have already been established.

        """

        # default implementation does nothing
        pass

    def handle_input(self, usb_data):
        """
        USB data input handler method, which is called every time new USB
        data is read in from the device.

        Accepts an array of raw USB input data (array of uint8).

        Decodes the data, and triggers whatever actions are necessary.

        This method needs to be overridden by each subclass implementing
        driver support for a device.

        """

        raise usbhid.UsbHidError(
            "not implemented, method must be implemented in subclass")

    def _get_key_handler(self, key):
        """
        Private convenience method for driver subclass constructors.

        Get a zero-argument target action function reference that corresponds to
        a particular numbered key from the device config.

        Accepts a key number.

        Returns a function reference, or None if no handler was found.

        """

        # get the name of the action that the given key is configured to perform
        action_string = self.config.get_action(key)

        # get a zero-argument function reference based on the name of the action
        function_reference = targetactions_get_handler_by_name_func(action_string)

        # return the function reference
        return function_reference


class ContourDesignShuttle(UsbHidDriver):
    """
    USB HID Driver for the Contour Design family of jog/shuttle devices.

    https://www.contourdesign.com/product/shuttle/

    """

    def __init__(self, config):
        # call superconstructor in parent class
        super().__init__(config)

        # map of shuttle encoder values -> variable playback speeds
        shuttle_encoder_value_playback_speed_map = {
            249: -32.0,
            250: -16.0,
            251:  -8.0,
            252:  -5.0,
            253:  -3.0,
            254:  -1.8,
            255:  -1.0,
              0:   0,
              1:   1.0,
              2:   1.8,
              3:   3.0,
              4:   5.0,
              5:   8.0,
              6:  16.0,
              7:  32.0,
        }

        # jog
        self.jog = Jog()

        # shuttle
        self.shuttle = Shuttle(0, shuttle_encoder_value_playback_speed_map)

        # keys
        self.k1  = Key(self._get_key_handler(1))
        self.k2  = Key(self._get_key_handler(2))
        self.k3  = Key(self._get_key_handler(3))
        self.k4  = Key(self._get_key_handler(4))
        self.k5  = Key(self._get_key_handler(5))
        self.k6  = Key(self._get_key_handler(6))
        self.k7  = Key(self._get_key_handler(7))
        self.k8  = Key(self._get_key_handler(8))
        self.k9  = Key(self._get_key_handler(9))
        self.k10 = Key(self._get_key_handler(10))
        self.k11 = Key(self._get_key_handler(11))
        self.k12 = Key(self._get_key_handler(12))
        self.k13 = Key(self._get_key_handler(13))
        self.k14 = Key(self._get_key_handler(14))
        self.k15 = Key(self._get_key_handler(15))

    def handle_input(self, usb_data):
        if len(usb_data) != 5:
            return

        # extract USB data into raw variables
        usb_shuttle     = usb_data[0]
        usb_jog         = usb_data[1]
        usb_key_field_1 = usb_data[3]
        usb_key_field_2 = usb_data[4]

        # jog
        self.jog.set_encoder(usb_jog)

        # shuttle
        self.shuttle.set_encoder(usb_shuttle)

        # keys
        self.k1.set_pressed( bool(usb_key_field_1 &   1))
        self.k2.set_pressed( bool(usb_key_field_1 &   2))
        self.k3.set_pressed( bool(usb_key_field_1 &   4))
        self.k4.set_pressed( bool(usb_key_field_1 &   8))
        self.k5.set_pressed( bool(usb_key_field_1 &  16))
        self.k6.set_pressed( bool(usb_key_field_1 &  32))
        self.k7.set_pressed( bool(usb_key_field_1 &  64))
        self.k8.set_pressed( bool(usb_key_field_1 & 128))
        self.k9.set_pressed( bool(usb_key_field_2 &   1))
        self.k10.set_pressed(bool(usb_key_field_2 &   2))
        self.k11.set_pressed(bool(usb_key_field_2 &   4))
        self.k12.set_pressed(bool(usb_key_field_2 &   8))
        self.k13.set_pressed(bool(usb_key_field_2 &  16))
        self.k14.set_pressed(bool(usb_key_field_2 &  32))
        self.k15.set_pressed(bool(usb_key_field_2 &  64))

