# Jog / Shuttle Support

  * [Overview](./JOG_SHUTTLE.md#overview)
  * [Supported Devices](./JOG_SHUTTLE.md#supported-devices)
  * [Enabling Jog/Shuttle Support](./JOG_SHUTTLE.md#enabling-jog--shuttle-support)
  * [Enable Device Permissions](./JOG_SHUTTLE.md#enable-device-permissions)
  * [Custom Key Mappings](./JOG_SHUTTLE.md#custom-key-mappings)
  * [Available Target Actions](./JOG_SHUTTLE.md#available-target-actions)

### Overview

Flowblade has a USB Human Input Device subsystem, which is capable of
supporting selected USB jog/shuttle devices.

A jog/shuttle gives you an additional way to navigate through your timeline
using a dedicated hardware control interface, in addition to the keyboard and
mouse. Playback at various speeds, in both forward and reverse, and navigating
frame by frame are right at your fingertips.

Turning the jog wheel to the right and left moves the playback location forward
and backward, one frame at a time, respectively.

Turning the shuttle ring to the right starts out with playback in the forward
direction, with increasingly faster speeds the farther you turn the shuttle.

Turning the shuttle ring to the left starts out with playback in the reverse
direction, with increasingly faster speeds the farther you turn the shuttle.

Additionally, most jog/shuttle devices have keys which can be mapped to
various actions within the program. Each supported device has default key
mappings, which can also be customized.

### Supported Devices

Manufacturer Device Name           | Flowblade Device Name        | Config File
-----------------------------------|------------------------------|---------------------------------
Contour Design ShuttlePRO v2       | Contour Design ShuttlePRO v2 | contour_design_shuttlepro_v2.xml
Contour Design ShuttleXpress       | Contour Design ShuttleXpress | contour_design_shuttlexpress.xml
Contour A/V Solutions SpaceShuttle | Contour Design ShuttleXpress | contour_design_shuttlexpress.xml

### Enabling Jog / Shuttle Support

Jog/shuttle support is not on by default in Flowblade, and must be enabled.

Additionally, Flowblade will not be able to access the USB device without
a small amount of operating system configuration to grant permissions so that
Flowblade is allowed to use the device.

#### Enable Device Permissions

In order for Flowblade to be able to read from the USB device, it is
necessary to tell your operating system to grant permissions on the device
to non-root users.

On Linux, this is done by adding a udev rules configuration file that
instructs the udev subsystem to enable additional access to your device.

Become the root user, and create a new text file at
`/etc/udev/rules.d/90-flowblade` with the following contents:

```
#
# Grant unprivileged users access to USB HID jog/shuttle devices
#

# Contour ShuttleXpress
# Contour A/V Solutions SpaceShuttle
ATTRS{idVendor}=="0b33", ATTRS{idProduct}=="0020", MODE="0644"

# Contour ShuttlePRO v2
ATTRS{idVendor}=="0b33", ATTRS{idProduct}=="0030", MODE="0644"
```

It may be necessary to reboot your computer after this step. This only
needs to be done once. It is also possible to tell the udev subsystem
to reload the config file instead of rebooting, but this is left as an
exercise for the reader.

<b>Don't forget to drop your root privileges after this step, before starting
Flowblade! Do not run Flowblade as root!</b>

#### Tell Flowblade to Use the Device

The next step is opening Flowblade, and enabling your device.

Go to the <b>Edit</b> menu, select <b>Preferences</b>, and then navigate over
to the <b>Jog/Shuttle</b> tab.

Check the <b>USB Jog/Shuttle Enabled</b> checkbox.

In the <b>Device</b> pull down menu, select the device driver that you wish to
use. The entries in this menu correspond to the <b>Flowblade Device Name</b> in
the <b>Supported Devices</b> section above.

Close the <b>Preferences</b> window.

After this, it will be necessary to exit Flowblade and restart it.

At this point, the USB jog/shuttle configuration is part of your saved
Flowblade preferences. You will now be able to use the program with or
without the jog/shuttle, without any further configuration necessary.

### Custom Key Mappings

Flowblade ships with XML config files that provide default key mappings
between the keys on your USB jog/shuttle device, and various actions in
Flowblade. It is possible to customize these mappings, by copying the
appropriate file into the correct user preferences directory, and modifying
the local copy.

The precise location of these config files can vary depending on how you
have installed Flowblade. You want to find the <b>res/usbhid</b> directory
under the Flowblade installation. From there, you will want to copy the config
file for your particular USB jog/shuttle device, and copy it to a location in
your local user preferences directory.

For example, if you installed Flowblade on Ubuntu using the OS packaging
system, and you have a Contour Design ShuttleXpress, then you would want to
copy the
`/usr/share/flowblade/Flowblade/res/usbhid/contour_design_shuttlexpress.xml`
file into
`.local/share/flowblade/user_usbhid/contour_design_shuttlexpress.xml` under
your home directory.

Open up the new local copy of the file under your home directory in a text
editor. You will see more information in the comments of the file about how
the keys are laid out on your particular device. Under the _keymap_ section
of the config file, you can edit the _code_ settings to point to different
_target actions_ that Flowblade can perform, for each of the keys on the
device.

Once your file is complete, save and close the file, and start Flowblade.
Now your new custom key mappings will be in effect every time you run the
program.

Take care not to introduce any XML errors into the file, or Flowblade will
not be able to process it correctly.

See the next section for all of the target actions that can be mapped to
the keys on your device.

#### Available Target Actions

Target Action               | Description
----------------------------|---------------------------------------
3_point_overwrite           | Three Point Overwrite
add_marker                  | Add Marker
append                      | Append
append_from_bin             | Append Selected Media From Bin
clear_io_marks              | Clear In/Out Marks
clear_mark_in               | Clear Mark In
clear_mark_out              | Clear Mark Out
cut                         | Cut Active Tracks
cut_all                     | Cut All Tracks
delete                      | Delete
display_clip_in_monitor     | Display Media Item In Monitor
display_sequence_in_monitor | Display Current Sequence In Monitor
enter_edit                  | Enter Editing Mode
faster                      | Faster
insert                      | Insert
lift                        | Lift
log_range                   | Log Range
mark_in                     | Mark In
mark_out                    | Mark Out
next_cut                    | Go To Next Cut
next_frame                  | Go To Next Frame
nudge_back                  | Nudge Move Selection Back 1 Frame
nudge_back_10               | Nudge Move Selection Back 10 Frames
nudge_forward               | Nudge Move Selection Forward 1 Frame
nudge_forward_10            | Nudge Move Selection Forward 10 Frames
open_next                   | Open Next Media Item In Monitor
open_prev                   | Open Previous Media Item In Monitor
overwrite_range             | Overwrite Range
play                        | Play
play_pause                  | Play / Pause
play_pause_loop_marks       | Play / Pause Mark In to Mark Out Loop
prev_cut                    | Go To Previous Cut
prev_frame                  | Go To Previous Frame
resync                      | Resynchronization
select_next                 | Open Next Clip In Filter Editor
select_prev                 | Open Previous Clip In Filter Editor
sequence_split              | Sequence Split
slower                      | Slower
stop                        | Stop
switch_monitor              | Switch Monitor Display
to_end                      | Go To End
toggle_ripple               | Toggle Ripple
to_mark_in                  | Go To Mark In
to_mark_out                 | Go To Mark Out
to_start                    | Go To Start
trim_end                    | Trim Clip End To Playhead
trim_start                  | Trim Clip Start To Playhead
zoom_in                     | Zoom In
zoom_out                    | Zoom Out

