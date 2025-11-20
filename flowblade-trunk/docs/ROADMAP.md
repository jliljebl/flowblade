# FLOWBLADE ROADMAP

Last updated NOvember 20th 2025.

### Planned Features

- Improved UX interactivity for same Track Transitions, move to use Tractors instead of rendered clips.

- Audio autoducking.

- Project Info popover with list of all markers and with new Project and Media Item notes.

- Ingest feature with user selectable transcode or only copy.

- Auto proxy creation if requested.

- Unpacking MLT XML Compound clips to back to original source clips.

- 'Find Black Holes' and 'Find Flash Frames' feature for Timeline.

- Track Soloing,

- Add new  keyframe types for Fluxity media Plugins.

- Alpha Shape GUI editor update to allow for controlling shape dimensions. 

- Control key to toggle mouse zoom target between pointer / playhead.

- Drag and Drop from Timeline to Monitor.

- Mouse Scroll horizontal  speed preference.

### GPU utilization

* Enable GPU decoding for playback on AMD and later for NVidia cards.

### GTK 4 port

* Allmost of the work that can be done prior to commiting to doing the port is now done.
* GTK 4 does not support setting video display target widget window XID. This means that we need to decide if we only do Wayland version of GTK4 Flowblade or create a new X11 video display solution. We will likely target only Wayland systems at that point, but that pushes back the likely date to 2028 at the earliest, we want a clear majority of users on Wayland if we are to drop X11 support.

### Video display

- Video display was moved to use SDL 2 library.
- Next up is doing Wayland native video display.
