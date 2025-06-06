# Release Notes



## FLOWBLADE 2.22
Date: June 6, 2025

### New Keyframe Interpolation Types

We added 32 new keyframes types to give users more options and control over animated images and filter values. New keyframe types are presented in two categories:

**Smooth Extented:** *Smooth Natural, Smooth Tight, Quadratic In, Quadratic Out, Quadratic In Out, Cubic In, Cubic Out, Cubic In Out, Quatic In, Quatic Out, Quatic In Out, Quintic In, Quintic Out, Quintic In Out, Exponenetial In, Exponenetial Out, Exponenetial In Out, Circular In, Circular Out, Circular In Out*

**Effect:** *Sinusoidal In, Sinusoidal Out, Sinusoidal In Out, Back In, Back Out, Back In Out, Elastic In, Elastic Out, Elastic In Out, Bounce In, Bounce Out, Bounce In Out*

### New GUI editors for Filters

Previously some filters only provided sliders to edit properties that were clearly geometric in nature. For this release we added mouse operated GUI editors for filters **Alpha Shape, Crop** and **Gradient Tint** to improve editing of these geometric properties.

### Top level UX updates

- Timecode Display was moved from Middlebar to below video monitor to improve locality of displayed image its position on Timeline or Clip. Timecode position in Middlebar is no longer configurable because Timecode is not in Middlebar anymore.
  
- Video source information locality was additionally improved by moving monitor source label to the left side in the topbar, next to *In/Out/Source Length* displays.
  
- *Tool* launcher icons were moved to Middlebar.
  
- Tracks can now be labeled with text that is displayed as a semitransparent overlay next to Track Head Column.
  
- Tracks Head Column mute icons were redsigned to be bigger and easier to hit.
  
- Custom expander widget was created for filter editing panel to regain vertical space lost to Trash and Up/Down icons.
  
- Splash screen was droppped. This was never really needed because Flowblade starts up quite quickly and the current implementation does not work with Wayland or Gtk4.
  

### Edit workflow

- Added *Box Selection* multitrack sync setting feature.
  
- New keyboard shortcuts for actions **Set Clip Sync Relation, Clear Clip Sync Relation, Toggle Clip Audio Mute, Set Clip Length.**
  
- Made *Distort* property editable for **Position Scale** and **Position Scale Rotate** filter.
  

### Contributions

Typo fixes from user *luzpaz* were contributed.

### Small updates and bug fixes

- Move Edit submenu first in Clip menu edit section.
  Add Sync section to keyboard shortcuts list.
  
- Fix keyframe editors menu copy/paste issues.
  
- Removed deprecated playback preferences.
  
- GUI tweak for Bins and Sequences panels.
  
- Delete unused resource images.
  
- Code reafactor to use AnimatedValue class to get intepolated values for properties.
  
- Clip end drag overwrite bug fix.

## FLOWBLADE 2.20
Date: March 25, 2025

We have now moved to SDL2 video playback for Flatpak and all systems with MLT 7.30 or higher. 

Video playback for native Wayland without XWayland or for Gtk 4 (that does not support the per widget Xwindow paradigm) does not currently seem possible with SDL. Moving forward we will develop some alternative video display approach. 

### Sync editing improvements

A large number of changes were made to improve Flowblade sync editing worflow:

* New track sync actions:
  
  * **Sync All Clips Action...** sets all clips in Track to be parented to closest clip on target Track. Target Track is remembered to enable single action update feature, see below.
  * **Update Sync to Clips' Positions** updates parenting sync to current positions to relative to Track that was previous selected as parenting target Track.

* Sync parent clips can now be on any track, not just V1. Track V1 can now also contain child clips.

* Clips can now be automatically audio sync split when added to user defined set of Tracks.

* Audio splits can be set to go on mirrored tracks instead of always going on track A1

* Clip multiselection popup offers now *Resync*, *Clear Sync* or *Set Parent Clip* actions.

* New delete edits:
  
  * Box selection delete and lift.
  * Single and  multiselection Ripple Delete Range action.

* Clip end trims can now be done in *overwrite* mode which help maintaining sync between tracks. 

### Sequence Link Container Clips

New **Sequence Link Container Clips** feature streamlines workflow where *Sequences* are used as parts of another *Sequence*. **Sequence Link Container Clips** can be updated to display changed contents of another *Sequence* without having to manually create a new clip and replace old clip on *Timeline*.

### Preset keyframe animations

Filters **Position Scale** and **Position Scale Rotate** have a new feature making it possible to add some frequently needed animations such as slide-ins and zooms in a single action.

Feature is available in keyframe editor hamburger menu when selecting item **Add Preset Keyframed Movement...**.

#### Monitor player buttons Row UX update

Though perfectly functional, the monitor player buttons row was always visually a bit rough. We did a visual and functional update in this area, switched to a using single centered Play/Stop button, moved marks buttons to the side and made larger the visual difference between displaying Timeline and Clips in the monitor. 

In a related update the timecode displays were made to display the active part of timecode in a brighter color to improve readability.   

### New features

* Rendered **Stabilized Media Item** creation is now possible.
* **Duplicate Sequence** feature allows creating copies of *Sequences*.
* **Generator Templates** feature makes possible to create **Generators** with user set properties to avoid having to set properties multiple times when creating **Generators**.

### Double sized icons deprecated

Double sized icons preference was removed. The results were always visually unsatisfactory. Tracks scaling preference remains, and when used in combination with scaling options provided by desktop environments it be possible to always achieve good results.

### Contributions

* **luzpaz** contributed a patch fixing large number of typos.

### New small features and bug fixes

* Zoom and shakiness parameters were activated for Stabilization filter.
* Add multi-item popup menu to Media Panel.
* Add 'Delete' item to Media Panel hamburger menu.
* Add feature to open keyframe editor params parameter in Keyframe Tool.
* Add Open in Edit Panel feature to Keyframe Tool.
* Add disable clip end drags when selected feature to improve targeting small clips.
* Add wide Slip trim activation area preference.
* Feature to delete motion tracking data to make motion tracking more manageable.
* Fix off by one issue with track syncs.
* Make Media Items grab keyboard focus when selected with hamburger menu.
* Add pixel format and colorspace info to file properties dialog.
* Clone sync data for cut clip clones.
* Fix Credit Scroll typo.
* Drop cyan color from box selection display.
* Updated create bindings documentation.
* Make second window part of applica too to fix non-working menu actions.
* Replace Pattern Producer file filering item with Container option.
* Process shutdown fixes.
* Show consumer type in env dialog.
* Delete consumer start/stop hack.
* Fix media item gmic icon bug.
* Fix paste append off by one and multitrack bugs.
* Add Filter Stack move arrows.
* Fix Filter editing file select button replacement.
* Add default container encoding options feature.
* Fix Container Clips losing sync on render.

## FLOWBLADE 2.18.1
Date: February 17, 2025

Flatpak fix for Credit Scroll generator.

## FLOWBLADE 2.18
Date: December 18, 2024

With this release we worked on gradual improvement on features, correctness and code structure. We had some great progress in moving forward from SDL 1 video display, but there were still some issues, so that was postponed for now.


### Timeline Clip slowmotion

Previously Flowblade only offered workflow in which slowmotion needed to be created by adding new rendered Media Items.

With this release Timeline Clips can be directly turned into slowmotion or reversed clips, a more interactive and responsive workflow requested by users.

### Generator work

- **Credits Scroll Generator** With this new generator scrolled or paged credit sequences can be created easily and with great amount of control over presentation. Text presentation and layout changes are controlled using a bit of MarkDown inspired markup, see documentation. Users can set initial layout parameters with GUI editors.

**Other improvements:**

- Upgrade **Hex Colors** generator to do boxes and triangles too, changed generator name to **Color Polygons**.
  
- Added **From Left Solid** and **From Right Solid** background types to **Multiline Animation** generator.
  
- Made generators use appropriate video clip default renders instead of frame sequences. This provided a nice performance for text animation generators.
  
- Made new HTML Link Button editor available to be used with generator to link to outside resources for e.g. added documentation.
  

### Alpha video rendering

Support for rendering VP9 WebM videos with alpha channel included was added.

### Gtk 4 work

Object creation for quite many often used widgets is subtly different between Gtk3 and Gtk4.

We added a builder module so that when we make the eventual switch we can only edit a few tens of lines of code instead of hundrends code points at widget creation sites.

Work was started by porting Gtk.HPaned / Vpaned and Gtk.FileChooserButton widgets to use the new module, and for the next few cycles will work to include all possible widgets.

### GUI / UX updates

- Add new Project Info and Data -dialog
  
- Move to 3-column view for Jobs whendisplayed in left column panel
  
- Make Media panel minimum size configurable
  
- Display Project Profile in topbar
  
- Add box selection functionality to Insert tool
  
- Add mute and unmute actions to multiclip popup
  
- Add keyboard shortcuts for showing vector scope and rgbparade
  
- Improve filter edit panels expanded states initialization after moves or mask adds
  

### Contributions

- Updated Polish translation by Stanisław Polak, who also provided a lot of valuable help in finding and fixing some missing translations.
  
- Typo fix from user Surfoo.
  
- Spanish translation update by David Gámiz Jiménez.
  

### Bug fixes, UX updates and other work

- Fix motion several tracking bugs
  
- Fix non-updating numerical entry values when swicthing keyframes in GUI canvas editors
  
- Fix save bug when image sequence being displayed on monitor
  
- Fix cloning to default XDG Data Store
  
- Fix project Data Store clone selection combo creation bug
  
- Fix default renders for generator clones
  
- Fix media item popover initialization
  
- Fix mouse scrolling for GeometryNoKeyframes editor
  
- Fix multiclip menu delete action
  
- Fix multiclip menu add filter action
  
- Fix SyntaxWarnings for regexes
  
- Fix G'Mic launch visual glitch
  
- Fix G'Mic containers
  
- Update Compositing chapter in docs
  
- Create shortcutsdialog.py module
  
- Add arg to launch all tools
  
- Code cleanups, move monkeypatches to dedicated bridge modules
  
- Add kf copy from next/prev menu items to kf popovers
  
- Update kf editor hamburger menu
  
- Make file name and path ellipsized in File Properties dialog
  
- Fix media item popovers
  
- Make GUI box editor handles bigger
  
- Update tc mark in / mark out icons
  
- Send arrow key events to focused editor component in GeometryEditor
  
- Send arrow key events to focused editor component in FilterRectGeometryEditor
  
- Correct mouse side scroll speed for sequence length
  
- Add filters copy/paste as popover menu items
  
- Add clone kf value functionality to RotatingGeometryEditor

## FLOWBLADE 2.16.3
Fixes G'Mic tool visual glitch and media items popover regression.

## FLOWBLADE 2.16.2

Hotfix release, fixes motion tracking bug.

## FLOWBLADE 2.16.1

Skip this one, metadata was not correct.

## FLOWBLADE 2.16

This was one of the shortest development cycles we've had. We had some interesting stuff ready, and with summer coming along a meaninfully larger feature set would have pushed the release past August, so we decided to go with what we have now.

### MOTION TRACKING

Motion tracking is now available. The feature was implemented using 3 different filters: one filter to produce motion tracking data, one filter to apply that data as motion of other image element and one filter that provides means to create filter masks to e.g. blur a person's face in a shot. More info [here](http://jliljebl.github.io/flowblade/webhelp/advanced.html#6._Motion_Tracking).

### STABILIZING

Stabilizing was implemented using a single filter and a user initiated rendering task to create the needed stabilizing data file. More info [here](http://jliljebl.github.io/flowblade/webhelp/advanced.html#8._Stabilizing).

### NEW FILTERS AND FILTER MASKS

- Four new *Filter Masks* are available: **Alpha Shape Motion Tracked**, **Image Alpha**, **Image Luma** or **Color Select**. **Alpha Shape Motion Tracked** is used to implement the motion tracked filter mask feature.
  
- New **Rubberband Octave Shift** audio filter.
  
- New **Rubberband Pitch Scale** audio filter. These filters provide slightly differing means of adjusting the audio pitch using the Rubberband library.
  

### MEDIA MANAGEMENT

We added two new features to make managing media more powerful and efficient:

- **Media Item rating feature**. Users can now rate every Media Item as either **Favorite, Unreated** or **Bad** and display only media items with desired ratings.
- **Move selected Media Items feature** It is now possible to re-arrange Media Items in Bins.

### OTHER NEW FEATURES

- **Slowmo playback at +-0.35 speed with USB shuttle devices**.
  
- **Slowmo at +-0.35 speed with JKL playback**.
  
- **Keyboard Shortcuts dialog UX update** with improved categorizing of shortcuts.
  
- **Move multiple keyframes** feature in *Keyframe Tool* with *SHIFT + Left Mouse*.
  
- **Move multiple keyframes** feature with in keyframe editors *SHIFT + Left Mouse*.
  

### CONTRIBUTIONS

- Stanisław Polak provided update for Polish translation.

### GTK 4 PORT WORK

- Drop *Gdk.Color* usage.
  
- Stop using 'clicked' -signal with checkbuttons.
  
- Remove *set_keep_above()*, it is not respected in Wayland.
  
- Port Edit Tool menu to popovers.
  

### BUG FIXES AND SMALL ENHANCEMENTS

- Fix setting sync parent
  
- Fix filter kf geom editors delete and next/prev buttons bugs
  
- Fix clip paste bug
  
- Add Paste filters shortcut into Keyboard Shortcuts dialog
  
- Update DEPENDENCIES.md, filters list doc, keyboard shortcuts doc and several chapters in docs
  
- Fix kb shortcuts dialog info
  
- Remove dead GUI colors code
  
- Fix tool dock colors
  
- Fix tools data users bugs
  
- Fix combined monitors size detection for vertical dimension
  
- Fix KeyFrameFilterRotatingProperty bug
  
- Fix geom kb shortcuts for GeometryNoKeyframes editor
  
- Fix filter geom editor shape move keyboard shortcuts
  
- Fix filter mask menu warnings
  
- Filter Mask UX updates


## FLOWBLADE 2.14.0.2
Fix Color Adjustment filter regression.

## FLOWBLADE 2.14.0.1
Fix monitors size detection for multiple monitors.

## FLOWBLADE 2.14
Date: March 29, 2024

Flewblade 2.14 comes with many long asked for features such as editable titles and slowmo playback, and with the largest single contribution in project history enabling using USB shuttle devices. 

### USB JOG/SHUTTLE SUPPORT

After some delay we merged **Usb jog/shuttle** feature developed by **Nathan Rosenquist**. This was a major contribution with about 2K lines of code needed to get things going. Intially we have support for three devices available, **Contour Design ShuttlePRO v2, Contour Design ShuttleXpress, Contour A/V Solutions SpaceShuttle**.

Documentation on activating the feature and adding support for new devices here: http://jliljebl.github.io/flowblade/webhelp/advanced.html#6._Jog_/_Shuttle_Support

Distro packagers, please see info on the needed configuration file addition (*/etc/udev/rules.d/90-flowblade.rules*) described in the link to docs above.

### EDITABLE TITLE CLIPS

The **Titler** tool now creates **Title Media Items**. Clips on timeline created from **Title Media Items** can edited with **Titler**, text and all its properties can changed as wished.

### OTHER NEW FEATURES

- **Switch to do clip paste on playhead position.** Previous we did paste on the nearest cut on target track, but doing paste as insert exactly on plyhead position is the established action pattern on popular video editors and we now do that as well.
  
- **Graphics clips can now be dragged to be arbitrarily long**. The previous underlying restrictions on doing this were no longer in place.
  
- **Slowmo playback is now available**. *CTRL + Left/Right Arrow* keys when held down now do forward/back playback at 10fps.
  

### FILTERS UPDATES

- Added **Position Scale Rotate** filter with a GUI editor.
  
- Added new **Elastic** distort filter.
  
- Added new **Compressor** audio filter
  
- **Waves** filter was updated with effect animation now available.
  
- Slider values can now be edited with mouse over scrolling. Relevant code provided by **schauveau**.
  
- Add *'sense'* property to avfilter.perspective.
  
- Fixed value replace for SCREENSIZE_WIDTH and SCREENSIZE_HEIGHT when used as range limits for editors.
  
- Fixed reset for filters the to do a value replace when initializing.
  
- Added a link to some editors providing additional information on their usage.
  

### OTHER CONTRIBUTIONS

- **schauveau** did some exellent research and provided a solution for Issue #1134 with failing playback on many latest systems.

### GTK4 WORK

We have removed almost all instances of *Gtk.Menu*. We spend some time to do a mostly scripted test conversion to fully explore the needed changes. The required work seems quite doable, and we will be able to do large parts of conversion work with scripts, but there were some show stoppers that need to be addressed relating to the fact that GTK4 no longer has per widget XWindows. Currently it is looking that GTK4 port will land sometime in 2025.

### SMALL FEATURES AND BUG FIXES

- Make Filter Select panel width configurable via a preference.
  
- Switch to keyboard shortcut *Alt + A* for appending selected media on timeline.
  
- Add reverse Media Items order in a Bin feature.
  
- Add a default graphics length per Bin feature.
  
- Add one more zoom step to make working with single frame clips easier.
  
- Fix GPU rendering with hevc_nvenc encoding to keep working with ffmpeg >= 6.0.
  
- Fix scripttool for new fluxity API.
  
- Fix generator validation render bug.
  
- Fix single track transition re-render.
  
- Fix layout for 768px height screens.
  
- Fix selectable clip colors and their gradients and selection colors.
  
- Fix gpu test render log names.
  
- Fix for start side trim view post-release display.
  
- Fix audio levels rendering for old datalayout projects
  
- Fix Projects data layouts after using close
  
- Fix CTRL + S saving for old data layout projects
  
- Add infotip for filter Perspective

**Hotfix releases since 2.12 initial release:**

## Flowblade 2.12.0.2 
Fix Generators rendering Issue (NOTE: 2.12.0.1 release had an issue and was removed)

## FLOWBLADE 2.12




Date: November 29, 2023

With Flowblade 2.12 we are getting a couple of important structural updates such as Data Stores feature and the possiblity to use up to 21 tracks in a Sequence. 

## DATA STORES

Users can now decide where project data such as proxie clips, container clip renders, thumbnails and audio levels is stored. Data location can be selected for each project individually, and project data can also be destroyd per project so that other projects are not affected. See documentation for more info.

## MAXIMUM NUMBER OF TRACKS INCREASED TO 21

Flowblade has always avoided UX with free scrolling of Timeline in 2 dimensions. The rationale has been that this provides a more stable and maximally controllable view of the Timeline. This in turn has necessitated having a maximum a track count of 9.

For 2.12 we added a paged and auto centered view of Timeline in the vertical dimension. This provides most of the stable view advantages of the previous approach, while simultaniously making it possible to increase the maximum number of tracks available to the user. 

## FASTER PROXY RENDERING

It was pointed out that creating proxy files with the FFMPEG CLI application GPU rendering was much faster then Flowblade proxy rendering, even if GPU was used for rendering by Flowblade. The reason for this speed difference is the additional overhead necessery to support multitrack playback with arbitrary filtering and image and audio mixing that is required for video editor rendering.

Proxies can now be rendered using FFMPEG CLI app if system supports GPU encoding. On testing we were getting 4-10x speed improvements with this approach. 

## TOOLS AND CONFIGURATION REMOVAL

Flowblade no longer offers user configurable toolset for Timeline editing. The use cases of additional available tools are well covered with the default toolset and user configurable ordering of tools was longer considered an important feature.

## OTHER NEW FEATURES

* New filters **Unpremultiply**, **Grayscale Luminance**, **Copy Channel** and **Fade To Black In/Out**
* Track output On/Off toggle keyboard shortcut.
* **Replace Media in Project** functionality.
* **Zoom to mouse position** feature

## CONTRIBUTIONS

* Translations update from **albanobattistella**

* Documentation and copyrights texts update from **Disaster2life**

*  Arch docs update by **Felix Yan**

## WORK ON GTK 4 PORT

A considerable portion of available development time was spend on moving to using Gtk.Popover widgets instead of Gtk.Menu widgets. Unfortunately GTK 4 deprecates a large amount of widgets and patterns used by Flowblade, and it will take some time and effort to get everything ready to even consider attempting a port.

## Small features, changes, removals and bugfixes

* Replace distutils with setuptools in setup.py
* Remove deprecated Gtk.main_iteration()
* Use GtkTicker for mltplayer updates and remove dead rendering code
* Refactor tool cursors handling to new module tlinecursors.py
* Flake8 fixes
* Make Add Plugin window resizable
* Fix few translations typos
* Fix MLT/ffmpeg complaint when rendering thumbnails
* Deprecate show_tool_tooltips pref
* Clone filters from prev/next non-blank clip
* Refuse to load files with fps_den == 0
* Add diagonal mirroring options
* Move 'Noise Gate' filter to group 'Audio'
* Remove dead timeline render code
* Remove dead theming code
* Fix on XML rendering calling player ticker
* Remove calling deleted method is_rendering()
* Remove Blender related code
* Remove light theme icons
* Fix editing for API version 1 fluxity plugins
* Add translations for plugin editor groups
* Make TextArea editor take all possible space for text widget and increase margins
* Display fluxity editor groups as notebooks
* Add to Fluxity API method add_editor_group() done
* Add Fluxity API method required_api_version()
* Port main app to Gtk.Application
* Change Add Plugin window to use pos bar for preview position selection
* Remove unneeded icons
* Add round caps and lighter bg to posbar
* Icons touch-up
* Remove detailed profile description info from top level at larger screensizes
* Remove colorized icons
* Remove Edge filter group and moved filters to group Artistic
* Remove tline match frame feature
* Remove all rules-hint properties
* Remove all frame ahdow types
* Remove deprecated CSS -gtk-icon-effect 
* Replace depracated Gdk.Cursor.new constructors
* Replace deprecated add_with_viewport method calls
* Replace deprecated Gtk.TreeView.get_vadjustment methods calls
* Change depracated new_from_stock to new_from_icon_name methods
* Change instance of modify_font to override_font
* Change instance of set_margin_left to set_margin_start
* Add Fade To Black filter Janne Liljeblad
* Add NVENC HEVC non-HDR render option
* Rename NVENC HEVC Main10 Profile as NVENC HEVC HDR
* Fix crash when dragging pattern producer into monitor
* Replace Batch Render dbus usage with polling solution
* Show info dialog when user tries to log Timeline range
* Fix for MLT 7.20 requiring profile when creating mlt.Playlist
* Fix 2 window monitor window top row layout TC and widgets touch-up


**Hotfix releases since 2.10 initial release:**

## Flowblade 2.10.0.4 
Fix issue with audio scrubbing repeating noise on pause.

## Flowblade 2.10.0.3
Remove dead Compositors and fix loading if they are used.

## Flowblade 2.10.0.2
Fix Issue #1095.

## Flowblade 2.10.0.1
Fix installdata.

## FLOWBLADE 2.10

This release took a long time to get done, but it is finally here. On the other hand, this release has the most ever new and interesting features for a single release, so it was worth taking the time to get everything in.

Going forward the project is in a quite good place now, and we have a clear path of incremental improvents ahead. We will return to 2-3 releases per year schedule.

### FULL TRACK COMPOSITING IS THE NEW DEFAULT

Compositing mode **Standard Full Track** is the now default compositing mode. Previous default compositing mode **Top Down Free Move** remains available via application menu and bottom left corner selector.

Compositing now works by default similarly to all other video editors on the market. This change should make the application more apprachable for new users.

### GENERATORS

Version 2.10 replaces *Pattern Producers* with a new *Generators* feature created using *Fluxity Plugin API* (see below).

*Generators* are media items with editable parameters that create rendered media when placed on timeline.

In this first release we provide 6 *Generators* that provide functionality in the following categories:

- Animated texts
- Animated backgrounds
- Overlay transitions

A demo video showing new plugins in action here: [Generators Demo on Vimeo](https://vimeo.com/838654406)

### FLUXITY PLUGIN API

*Fluxity Plugin API* is Python scripting solution targeted at providing means to create media generators with editable parameters.

API documentation is available here: [fluxity API documentation](http://jliljebl.github.io/flowblade/webhelp/fluxity.html)

We had several compelling reasons for creating a plugins framework to add to the functionality provided by MLT.

- Functionality such as animated texts can be created much more easily using Python and rendered media.
- Some MLT functionality is unavailable for Flowblade because QT based MLT services crash the application.
- Contributing threshold for creating new *Generators* should be very low for since only a single self contained file is needed to do a meaningful contribution.

### NEW KEYFRAME INTERPOLATION MODES

Previously we only provided ***Linear*** value interpolations between keyframes, but with this release we make ***Smooth*** and ***Discrete*** keyframe interpolations available too.

### GPU RENDERING

We now have GPU encoding available for some formats:

- AMD/Intel cards - VAAPI h264 encoding
- NVidia cards - NVENC HEVC encoding, NVENC h264 encoding

Options will be available in **Render** panel if test renders on start-up complete successfully.

### NEW DEFAULT THEME

We have a new dark default theme. The previous default theme and the other available themes were removed. System dark and light themes were also removed because the new Gnome global dark preference setting caused application window to become invsible in some cases.

  
### CONTRIBUTIONS

- **jep-fa: Keyframe Tool keyframe level editing feature.** *Control +Left Mouse* press and drag between two keyframes sets same value to both. This likely going to be very handy when e-g- working with audio levels.
- **Ümit Solmaz** provided new turkish language support.
- **jep-fa: Creating missing files in Media Relinker feature.** When using Media Relinker to fix projects with missing media user can now create place holder files directly with Media Relinker dialog.
- **Albano Battistella** updated italian translation.
- **Pavel Fric** updated czech translation.
- **Martin A. Wielebinski** updated german translation.
- **Николай Смольянинов** updated the Russian translation
- **jep-fa** Titler : remove spaces and new line characters at start of the name of the layer

  
### GUI UPDATES

- New **Edit** panel. Dedicated edit panels for *Filters* and *Compositors* have been combined into single *'Edit'* panel. *Generator* properties are also edited in this panel.
  
- **New Encoding Options selector** Encoding options are now presented using a categorised combo box allowing e.g. more clearly differentiating the new GPU rendering options.
  
- **New Profile selector** Project Profile options are now presented using a categorised combo box.
  
- **Move Tools buttons to top bar** Buttons for launching *G'Mic editor*, *Audio Monitor* etc. have been moved from Middlebar to top menu bar.
  
- **Mouse prelight** Pressable icons now prelight under mouse improving UI interactivity.
  
- **Preset Layouts** There are now preset layouts avaialeble from a button in top menu bar.
  
- **Combine freebar and layouts functionality** Middlebar buttons editing and layout selections functionality have been combined.
  
- **Multiclip selection pop-up menu** A new menu with actions that can be applied to multiple clips is presented when multiple clips are selected on timeline and a context menu is opened with mouse right click.
  
- **Keyframe editor hamburger menus** Keyframe editors now have a hamburger menus adding new functionality and replacing old menus accessed via keyframe icons on sides.
  
- **Keyframe Interpolation right click menu** Keyframes now have right click context menus with options to set keyframe interpolation.

  

### Other new features

- **Quick Filter Keyboard Shortcuts** Keyboard Shortcuts dialog now provides possibility to set up to 12 Quick Filters available using **Control + F(1-12)** key combo.
  
- **Add Media Folder** feature allows user to import multiple media items from a folder in a single action. User can control file type and maximum numbers of files to be added.
  
- **Blend Mode filters** When using the new default compositing mode *'Standard Full Track'* compositing mode is now controlled by adding a new Blend Mode filter.
  
- **New Filters:** Trails, Glitch, Choppy, RGB Shift.
  
- **Add markers during playback using** feature.
  
- **Q and W keyboard shortcuts** for quick trimming clip ends.
  
- **Save/Load Effect Stack** functionality has been added.
  
- **Looping playback** Looping range is set by setting Mark In and Mark Out on timeline.
  

### UX Papercuts

- Support CTRL+X for media files and timeline clips.
  
- Autoexpand track on first added clip.
  
- Keep timeline centered on zoom if possible.
  
- Allow box selection from blank clip with Move tool.
  
- Make mouse wheel sideways scroll step zoom level dependent.
  
- Make Move tool box selection snap too.
  
- Add Resync Track -edit action and keyboard shortcut for it.
  
- Make split and sync split edits for clip ranges consolidated and available from multiselection pop-up.
  
- Auto seek to clip first frame on clip opened in filter editor.
  
- Auto expand latest added filter when clip opened in filter editor.
  
- Exit other then default tools on empty click.
  
- Make clip ends snap correctly.
  
- Multiple menu updates including main menu and clip context menu.
  
- Move playhead to clip start when clip opened in editor.
  
- Make Move tool box selection on empty press behaviour always on, update tooltip.
  
- Turn single track box selection into range selection.
  
- Add drag'n'drop filter on all selected clips if dropped on selected range.
  
- Make Media Panel Shift + Mouse selection work in standard way.
  
### Removed features

Quite a few features were removed to tighten up the design and codebase. Some may be later re-introduced if there is singficant demand.

- Drop Blue and Grey themes.
  
- Remove rendered fade and color dip functionalities.
  
- Drop Blender containers.
  
- Removed Autofollow composition mode.
  
- Removed feature to display audio levels only on single clips.
  
- Removed fade compositors.
  
- Dropped film emulation LUTs from G'Mic tool
  
- Drop Pattern Producers, replaced by Generators.
  

These two we hope to bring back later:

- Dropped timeline rendering feature.
  
- Dropped Save Snapshot... feature.
  

#### Small features, changes and updates

- Use outline to indicate media item selection
- Add copy/paste items to keyframe editor menus
- Marks GUI update
- Improve sync info GUI on clips
- Monitor area layout change
- Pos bar look update
- Clips colors update
- Tighten up slider editor GUI
- Enable markers for audio clips
- Zoom to project length and pos 0 on sequence open
- Enable drag'n'drop for range log items into monitor
- Add feature to show Range Log items in monitor with range marked
- Add keyboard shortcut for rendering timeline ranges
- Make many processes use mltinit.py
- Clear GLib dependency from renderconsumer
- Delete unncessery imports from mltenv.py
- Port everything except main app to Gtk.Application
- Remove Gdk.Screen usage
- Use GLib.timeout_add instead of Gdk.threads_add_timeout
- Remove audiowaveform.py module
- Audio mime type fixes
- Remove Gtk, Gdk dependency from utils.py
- Remove threads enter/leave from everything except main app
- Add 'Center' action for geometry editors
- Add clone filters feature for audio clips
- Remove imgseq ?begin version

- Change defaults to favor showing playhead on stop
- Change Image Clip Color on default theme.
- Jobs info texts update
- Make Runtime dialog bigger and resizable
- More HiDPI work, @2 buttons work, add some @2 icons for buttons
- Keyframe Tool GUI and menu updates
- Show info dialog when creating too large custom layouts
- Drop force_small_midbar pref and fix midbar to always work with w >= 1280 screens
- Add filter add menu to Effects editor panel
- Don't display project name in top level project panel
- Fix themes having tabs properties bleeding from system theme
- Fullscreen button functionality
- Display info on modified audio levels in Tracks column
- Tighten multiple GUI elements
- Clone only active filter with copy/paste
- Add Recreate Icon feature for Media Items
- Do not accept non-seekable video files
- Make render with args work with values containing equals sign
- Do not open non-seekable audio files
- Refuse to load files with non-media extensions.
- Drop Pattern Producers
- Add 10% view size into geometry editors
- Make Range Log text column wider and ellipsized
- Add drag'n'drop filter on all selected clips if dropped on selected range
- Optimize Dark Theme colors for Yaru and Adwaita instead of Arc-Dark
- Make Ubuntu theme selected color work with Yaru
- select-next - prev clip, select-next - forward
- Make load dialog more interactive
- Thin edit panels 40px
- Import mlt7 as mlt if the available mlt is presented as mlt7
- flake8 fixes
- Use Icon to mark active Sequence
- cairoarea: replace deprecated Gdk.EventMask.POINTER_MOTION_HINT_MASK with Gdk.EventMask.POINTER_MOTION_MASK, fixes GMicButtons issue
- Timeline waveform display touch-ups
- Add snapping to playhead

#### BUG FIXES

- Clear keyframe editors on clear_clip() to avoid failing callbacks on discarded editors
- Fix CairoColorProperty
- Don't crash if setting dark theme preference fails.
- Fix media timline drag'n'drop when starting from multiple selection
- Panel positioning fixes for two windows mode
- Clear keyframes editors update list when initing Keyframe Tool
- Fix updating custom shortcuts files
- Fix media bin multi dnd (?) onko uusi regressio tässä cyclessä
- Fix Keyframe Tool draw off-by-one bug
- Fix removed monitor start-up crash
- Fix image sequence Container Clip loading
- Keep names same for rendered Container Clips
- Fix Issue #870 with Home and End keys
- Make images and color clips respect Mark In and Mark Out when dropping on timeline
- Fix numerical entry issues with geometry editors
- Fix issue in forum question 110
- Fix updating tooldock when tool selection changes
- Stop container clips from being able to prevent loading media files because of duplicate check
- Remove profile selection from container clips rendering, always use project profile.
- Fix issue #990 by adding missing tabs position default value
- Fix adding named Sequence
- Fix G'Mic video render stopping bug
- Fix loading User profiles
- Update edited sequence name in top row
- Fixes on profiles widgets after profile changes by user
- Fix ESC updating for tool dock
- Fix selection clip creation GUI update bug

- Fix monitor media drag
- Fix bins update after adding pattern producer
- Make clip end drags respect track locking
- Fix clip drag out of tline bug when range panel missed
- Fix project load in systems with 'import mlt7' if project data saved in system with
- import mlt' Janne Liljeblad
- Remove mlt.mlt_image_rgb24a definition from monitorwidget.py
- Fix setting audio levels to 0 in audiomonitoring.py
- Fix ToolSelector re-init after middlebar configuration
- Fix multitrim overlay bug when entered with key press
- Fix re-render rendered transitions
- Fix rendered transitions
- Fix kfeditors for clip end drags
- Fix filter undo/redo edit panel updates
- Fix effect drop on range
- Fix compositor and generator edit panels visibility through edits
- Set Save menu item sensitivity always correctly after first video load

## FLOWBLADE 2.8

Date: February 9, 2021

In this development cycle we focused on making the application more configurable. Among other new features we made panels layout, keyboard shortcuts and middlebar customizable.

### CONFIGURABLE PANEL POSITIONING

For the first time it is now possible to change the layout of the application by moving panels to different positions using **View->Panel Placement** submenu. Currently the feature is only available for screens with resolution of 1680 x 1050 and up. 

### NEW THEMES

Application look'n'feel was updated by adding two new custom themes. 

* **Flowblade Neutral** is a dark theme with equal RGB values for all hues providing a neutral background. [Screenshot](https://github.com/jliljebl/flowblade/blob/master/flowblade-trunk/docs/Screenshot_THEME_FLOWBLADE_NEUTRAL.png)  

* **Flowblade Gray** is a dark theme with very light blue tint. [Screenshot](https://github.com/jliljebl/flowblade/blob/master/flowblade-trunk/docs/Screenshot_THEME_FLOWBLADE_GRAY.png)  

* Previous default theme remains available as **Flowblade Blue**.

### FREEBAR

**jep-fa** provided a feature allowing users to select which items in Middlebar are displayed and in which order. Feature is available by selecting **View->Middlebar layout->Free Bar** and then **View->Middlebar layout->Configure Free Bar...**. 

### CONFIGURABLE KEYBOARD SHORTCUTS

A subset of keyboard shortcuts can now be changed. From the hamburger menu in **Keyboard Shortcuts** dialog select **Add Custom Shortcuts Group** and click on gear icons to set shortcuts.

### TOOLDOCK

User can now optionally use Tool Dock widget to select Timeline Edit Tools instead of the middlebar drop down menu.

### FILTER EDIT PANEL UPDATE

Filter panel was updated. The previous left side **Filter Stack** and **Filter Selection** list boxes were removed in favor of the more common approach of having **Filter Edit Panels** themselves being arranged in stack.

### NEW FILTER SELECT PANEL

**Filter Selection** panel was moved to right side of the Timeline. User can add filters by double clicking on filter items or by doing a drag-and-drop on top of Timeline Clips.

### COLOR ICONS

**jep-fa** provided a set colored of icons to be optionally used in the Middlebar with **Николай Смольянинов** providing some additional contributions. The feature provides a differentiated, bright and colorful look for users who prefer it.

### OTHER CONTRIBUTIONS

* **Relink a directory** feature for **Media Relinker** contributed by **jep-fa**
* GitHub Actions build workflow contributed by **Dan Dennedy**.
* Fix broken 'ui' object references in editorwindow.py **Nathan Rosenquist**.
* startup: support usr-merge by **sgn**.
* Don't use legacy directory for Appstream metadata **City-busz**.

### NEW FRENCH USER MANUAL

**jep-fa** created a new French language user manual with large amount of up-to-date screenshots and icons shown and explained. The manual is substantially longer and more detailed then the current user manual and it might very well be worth the effort to translate this to English to use it as the new project official user guide.

### TRANSLATIONS UPDATES

* **Николай Смольянинов** updated the Russian translation

* **jep-fa** updated the French translation

* **micitabesh** updated the Ukrainian translation

* **Stanisław Polak** updated the Polish translation

### OTHER CHANGES

* MultipartFilterObject filters were decracated and replaced with standard filters.

* Cutting clips now keep filters and mute state of original clips on both new clips. 

* Gradient and Shadow blur features were added into Titler.

* Color Picker feature for selecting colors from monitor was added into color selection widgets.


### NEXT CYCLE PLANS

In next cycle we plan among other things to improve the current rendering functionality and create a new scripting tool for creating custom effects, transitions and rendered backgrounds.


### BUG FIXES AND OTHER CHANGES

* Fix Issue #969 with non-updating LADSPA filters
* Fix problems with using Range Log in Proxy Mode
* Fix Issue #960 with Range Log treeview failing to hold scroll position after adding item
* Load project even if container clip fails to make media item icon, Issue #919
* Drop support for G'Mic version 1, fixes Issue #900
* Drop word 'Pan' from Audio Mixer and use icon instead
* Fix FilterRectGeometryEditor mouse scroll zoom
* Fix Range Log Delete key action
* Don't draw out of clip range clip markers
* Make Titler layer list treeview selection follow state
* Drop H.264 for single track rendered fades/transitions
* Fix trim view second image
* Change Titler to use left side checkboxes
* Change top level checkboxes to be on left
* 900px height screen render panel GUI fix
* Refuse to open animated GIF files
* Fix Issue #941 with crashing renders when using H.264 and timeline having blanks
* Make possible to change aspect ratio with Position Scale filter
* Fix X and Y scale in Rotate and Shear filters, Issue #943
* Add module persistancecompat.py and refactor compatibility code into it
* Add code to try to open moved proxy projects
* mime: add icon, fixes #905 eszlari
* Remove deprecated getiterator() method
* Keep Titler open but re-init for screensize on project load
* Add offline docs as .pdf and .docx files
* Make second window fullscreen with F11 if it has toplevel focus
* Fix intro dialog typo, Issue #921

## Flowblade 2.6.3

Date: October 27, 2020

This is a bug fix release.
 * fixes Color Clip load crash regression in 2.6.1

## Flowblade 2.6.1

Date: October 14, 2020

This is a bug fix release.

* Flatpak: Fix broken Jobs rendering - Proxy, SlowMotion, Reverse, Container Clips
* Fix autosave bug #891 with Control + S saves going into old autosave file
* hfiguiere and eszlari: Flatpak - Remove deprecated non-unified plugins 
* Make Delete Editor activate Save button too on Blender program editor
* Use self.render_player.wait_for_producer_end_stop = True for G'Mic video rendering
* Switch tlinerender to use Flatpak app-id dbus names
* Make unused missing asset launch relinker too
* Николай Смольянинов: UpdateRussian translations
* Mark Mandel:  Add Paste Filter shortcut (in docs)
* Balló György:  Install subdirectories of help
* Fix bug in simpleexitors.py

## Flowblade 2.6

Date: July 5, 2020

This is the second Python 3 release of the application. This time we introduced a quite large amount of new functionality like Container Clips and async rendering of resources using Jobs panel.

### TECHNICAL ISSUES

* MLT 6.18 or higher is now required.

* Application requires XDG user folder information to run, using dot folders as backup is no longer supported

* Flatpak does not support all features, Batch Rendering and Blender Container Clips are currently not available in Flowblade Flatpak. We aim to do a point release in August addressing these issues.

### COMPOSITING CHANGES

In 2.4 for we added the concept of Compositing Modes enabling user to select between different ways of creating composited images. In this release we complete the approach by adding a new Compositing Mode Standard Full Track.

#### Standard Full Track Compositing Mode - no Compositors needed

The shortest way to describe this compositing mode is *"What everyone else does"*. No Compositors are needed to create composited images in this Compositing mode.

We made a tutorial video explaining using Compositing Modes [here.](https://vimeo.com/427093600)

User documentation on Compositing Modes is [here.](http://jliljebl.github.io/flowblade/webhelp/compositor.html)

#### Other Composing Mode changes

* **Top Down Auto Follow** Compositing Mode was  removed. This mode did not offer any sufficiently differetiated functionality to justify additional complexity.

* Compositing Mode can now be selected from a menu in the bottom left corner.

#### Making Standard Full Track the default Compositing Mode in the future

We are considering making the new Compositing Mode Standard Full Track the default for new projects, anyone having an opinion on this can comment [here.](https://github.com/jliljebl/flowblade/issues/876)

### CONTAINER CLIPS

We introduced a new Media and Timeline object called a Container Clip.

There is a lengthy explanation on the rationale and usage of Container Clips in user documentation [here.](http://jliljebl.github.io/flowblade/webhelp/container_clips.html)

This is only the first iteration on the idea to get things going. Later we will be adding at least a Python based scripting tool and Natron project file Container Clips.

For 2.8 we will introduce a central repository where users can contribute and share Container Clip resources.

#### Compound Clips are now Selection Container Clips

Clips made from selections were previously called Compound Clips. Now they are one type of Container Clips and Compound Clips naming is no longer used.

## TIMELINE RENDERING

We now offer a functionality to render one or more parts of timeline in case there are performance problems in some areas. Related user documentation is [here.](http://jliljebl.github.io/flowblade/webhelp/advanced.html#5._Timeline_Rendering)

## JOBS PANEL

Adding Container Clips necessitated proving a way to launch, observe and abort asynchronous renders other then the existing Batch Rendering functionality.

Proxy Clip rendering and rendering of Motion/Reverse clips are now asynchronous jobs instead of the previous approach where they were modal renders.

Functionality is provided in a new **Jobs** panel.

## CONTRIBUTIONS

**Albano Battistella** 

* updated italian translation

**驿窗**

* updated Chinese translation

**micitabesh**

* updated Ukrainian translations

**Николай Смольянинов**

- Updated Russian translation
- Fixed "start key" to "home key"

**jep-fa** 

* Add a list of the unused files as a new Media Panel view category.

* New optional playback buttons To Start/To End to go to start or end of timeline.

* 75 pixels high tracks option. These larger tracks can look nicer and clearer in many situations.

**Pascal de Bruijn**

* add **Lines** filter

* add **Dust** filter

* move **Grain** from group Blur to Artistic

* libmp3lame over ffmpeg's aac 

* renderencoding: minor consistency changes

**dvdlvr**

* Add sturdier code for missing @2 icons

* Added compositor_icon@2

**imaami**

* Fix crash on loading a project with color clips

## OTHER NEW FEATURES

* Partial filter application with filter masks.

* Clips can reload clip media from disk now.

* Steal frames for rendered transitions feature.

* No confirm dialog asked on project exit if nothing has been changed.

* Rotomask Curve/Line type selection is now a persistent property.

* New keyboard shrtcuts:
  
  * Alt + R is shortcut for Resync now, S no longer works for this.
  
  * Clear Filters was changed to Alt + C.
  
  * Alt + K for clear Mark In/Out.
  
  * Alt + I/O is now Display going to mark in/out for all usecases, Shift + Shift + I/O still works users who prefer .

* Position bar now shows timeline markers.

* Disk cache size warning. If Flowblade takes over 500MB space on disk user will be informed.

* Range Overwrite edit action now works when only Timeline Mark Out defined.

* It is now possible to change render path of a render item in  Batch Render window.

## FOCUS AREAS FOR NEXT DEVELOPMENT CYCLE

* We are moving to feature branch development model so master can have quite long pauses before new work appears there.

* Work on SDL 1.2 replacement. We got SDL 2 software rendering video display working but the performance was much worse then what we have now. Next we will look to develop  SDL2/OpenGL based solution 

* Improved GUI configuration. Now that we have made editing tool set, workflow and compositing model user configurable we will continue to make keyboard shortcuts, middlebar contents and window layout configurable. 

* Container Clips work with Natron and Python script tool features planned.

* Work on Issue list.

* There will no summer shutdown this year, we will remain active on PRs and Issue list, but on July there will probably be relatively few new patches.

## BUG FIXES AND SMALL CHANGES

* Fix issues with deleting and moving media items  in media Panel views.

* Make out-of-range keyframes menu do write out correctly for all edit actions.

* Fix slight GUI shaking in Keyframe Editor.

* Make $HOME default folder for "Save As..." when no good last save data exists.

* Drop 96 kHz audio sample rate option.

* Fix rendered Fade out video position.

* Fix rendered fades delete actions.

* Fix rendered transitions Issue #836.

* Make fade editors position update with timeline.

* Titler: Fix layers load GUI inconsistency with layer visibility.

* Escape G'Mic render paths spaces.

* Make fade buttons default lengths configurable.

* Player buttons tooltips fixes.

* Fix double .xml in selection Container Clips.S

* Autocreate user defined render folder if deleted.

* Position Scale filter: Make keyframe copy paste work
  Position Scale filter: Make menu actions work 
  Position Scale filter: Set initial value to 0,0
  Position Scale filter: Fix numerical inputs

* Add Default Keyboard Shortcuts list is Docs.

* Fix missing proxy dir on launch.

* Make NO_DECORATIONS default button style.

* Remove test.py module, it is not used.

* Drop presets from G'Mic tool rendering options.

* Add action to render proxyfiles for all project media.

* Make sure there is always space displayed in GUI after sequence end.

* Make dark theme timeline marker yellow to pop better.

* Position bar markesrs display bug fix.

* Implement default render folder feature.

* Replace deprecated time.clock() with time.monotonic.

* Implement quieting output prints with commandline switch --quiet.

* Fix Issue #801 with unexpected save behaviour with moved project files.

* Try to use original media when proxy media missing on load and project is in proxy mode.

* Make proxies destroyable with cache management UI.

## Flowblade 2.4

Date: December 12, 2019

**Flowblade 2.4** is the first version of the application running on Python 3.

We also got interesting contributions in this development cycle and made some quite large changes on how Compositing works.

With the Python 3 conversion now behind us, we have plenty of interesting ideas for the next development cycle and will also start working towards getting video display moved on from SDL 1.2.

## PYTHON 3 PORT

**All distributions are encouraged to update to Flowblade 2.4 and MLT 6.18**

Flowblade was ported to Python 3. The process went without major gliches and we only needed to do one single patch upstream to maintain functionality.

The change however represents a discontinuity point in the development of the application, 
e.g. we do not offer **.deb** package for this release. It is also possible that we didn't catch all regressions, but we expect to get back on track towards continual quality improvement very quickly.

Going forward we hope that the Python project focuses on improving its existing strenghs in a backward compatible way. The decade long transition into Python 3 should be considered as proof that further compatibility breaking changes will only hurt all stakeholders in the platform.

## ARDOUR EXPORT

**Nathan Rosenquist** contributed functionality to export Sequence audio as an Ardour project.

This contribution is an important step towards more professional workflows where audio is worked on a dedicated application after the image edit is completed.

Advantages of editing audio in Adrour include cutting audio with single sample accuracy (Flowblade generally allows cutting at every 44100th sample), unlimited tracks, more and better audio filtering options and much more.

## NEW COMPOSITING MODE 'STANDARD AUTO'

Previously we had a **Compositor Auto Follow** mode that changed the way compositors behaved.

In this release we are moving to present that previous functionality as a **Compositor Mode** and also we added a new Compositor Mode **Standard Auto Follow**.

**Standard Auto Follow** mode is the most simple and easiest to use Compositing Mode. 

In **Standard Auto Follow** mode Compositors follow their origin clips automatically and users can only add one compositor per clip. Compositors select their destination tracks automatically and it is not possible to create node tree compositions.

This mode works most similarly to way that compositing works in most other video editors.

User can set Compositing Mode for each Sequence by selecting it from *Sequence -> Compositing Mode* sub menu.

## COMPOSITOR CHANGES

We made some changes here to improve image quality and approachability when working with compositors.

* **Dropped Dissolve and Picture-in-Picture from compositors  selection**, these use cases are better covered by Blend and Affine Blend that have more functionality and better quality when compositing with alpha channel.

* **Renamed Region to Wipe/Translate** and moved it into new group Wipe with Wipe Clip Length Compositor.

* **Renamed Alpha Combiners compositor group Alpha** and moved LumaToAlpha compositor in it.

* **Dropped Dodge blender and Cairo blending mode "Saturate"** because these were not functioning properly.

* **Added 'Delete Compositors' menu action** in clip context menu.

## TRANSFORM FILTERS UPDATES

* **Filter selection was updated** New available filters transform are **Position Scale, Rotate and Shear**.

* **Position Scale** filter now has GUI editor.

* All filter values can now be edited with keyframes.

## CONTRIBUTIONS

#### Pascal de Bruijn

New defishor type filter and improved defaults - Changed Default new Project Profile to: HD 1080p 30 fps -  Change mp2 audio encoder to libtwolame - Change H.264 video to use with AAC audio - drop mp3 codec audio bitrate to real available maximum - Change WebM to use xiph's libvorbis - make Ogg Theora video have Ogg Vorbis audio - Mention VP8 video for WebM container - Mention Ogg container for Theora video - Make h.264 as first option Encoding selection. - Proxy Editing:fix h.264 proxy format audio description (ref: dc13921e), reduce alignment to 2, this gets rid of the black bars , sensibly match audio codec to their (proxy) video codec - Flowblade CSS Theme: unset all properties so the system theme doesn't bleed through - keep assets sources local - GUI Keyframededitor colors update to better match Flowblade theme colors - Remove duplicates of profiles atsc_720p_25, atsc_720p_2997, atsc_720p_50, atsc_720p_5994

#### Steven van de Beek

* Fixed big buttons for HiDPI screens with new cdoe and new icons provided 
* fixed autosave interval selection to work.

#### Nathan Rosenqvist

Fix atomic file for Python3 - update Lossless HuffYUV and Apple ProRes render Profiles to use 24bit audio - add numpy dependency to python3 doc.

**cclauss** IconSize.DND -> Gtk.IconSize.DND

**Alex Myczko** Rename flowblade..po to flowblade.po

## TRANSLATIONS

Chinese zh_CN translation update by **驿窗**

Czech translation update by **Pavel Fric**

Russian translation update for application and help docs **Николай Смольянинов.**

## FEATURE ADDITIONS AND BUG FIXES

* Fix sequence combining bugs

* Add audio_match property to all shape filters to fix audio level bug

* Fix audio monitoring for all sequences

* Fix Issue #443 with media loading and bins

* Add Wipe alpha filter

* Change Paster Filters -> Paste Filters / Properties

* Allow opening MLT XML files with exactly matching profiles

* Make Proxy mode info available for Render Queue items

* Drop LensCorrectionAV filter

* Make possible to select the monitor used to decide window layout

* Fix box move bug

* Make possible to copy paste clip ranges with blanks in them

* Project events are now displayed on modal window on all screen sizes

* Fix Render panel GUI for 900px height screens

* JKL playback new speed 1.8x, GUI fix

* Geometry editors GUI update

* Keyframe values can now be copy pasted

* Created Sequence menu to simplify Edit and Project menus

* Batch render window GUI touchup

* Make possible to render a compound clip from non-active sequence

* Media icons GUI update

* Middlebar GUI update

* Make monitor timecode infos pop better

* Created document helpng to create MLT bindigs to run Flowblade

## Flowblade 2.2

Date: August 26, 2019

**Flowblade 2.2** is the first new version after 2.0 brought large changes the editing workflow and application layout. This time the main focus was on improving Flowblade's compositing capabilities with a dedicated tool for editing animated masks being most important new functionality.

There was also a lot of other new functionality and fixes, including G'Mic update, support for XDG user folders and many Issues fixed from Github Issue list.

### Compositing Improvements

For the purpose of improving compositing we added 2 new filters and 1 new compositor. Together these will enable doing much more complex compositing work.

There is a tutorial video for the new compositioning features: https://vimeo.com/355860509.

#### RotoMask Filter

RotoMask filter enables creating animated line or curve masks which will either affect the alpha channel or RGB data. Masks are edited with a GUI editor created especially for this filter, editor also comes with complete keyframe editing functionality.

#### LumaToAlpha Compositor

This compositor uses luma values from source track and writes them into alpha channel of target track.

#### FileLumaToAlpha Filter

This filter uses luma values from source media and writes them into alpha channel of video or image clip.

### User data moved into XDG folders

We have moved user data from directory */home/USERFOLDER/.flowblade* into XDG folders specified in the user system. Data will be copied automatically on first launch of this version.

**NOTE: Thumbnail and Render directories are not user settable anymore since we decided to support XDG user data spec.**

**NOTE: Application DOES NOT delete existing data in .flowblade folder, so if you have large amount of data there you will probably want to delete folder */home/USERFOLDER/.flowblade* manually to free disk space.**

### New Filters

We added 3 new filters: **Vignette Advanced, Normalize** and **Gradient Tint**.

### Keyframe Edit Tool update

* Tool colors got an update.
* All keyframable params can now be edited with the tool.
* Value snapping options for steps 2 and 5 were added.

### Tools updates

#### G'MIC

* We added 20 new filters for systems G'MIC 2+: **YAG Effect, Delaunay, Difference of Gaussians, Dices, Boost Chroma, Threshold, Etch, Bokeh, Make Squiggly, Dream Smooth, Graphic Novel, Rodilius, Aurora, Grid Hexagonal, Anguish, Blockism, Cut Out, Wiremap, Fraeky BW, Warhol, Grid Triangular**
* Gmic tool no longer does audio scrubbing
* Some GUI fixes

#### Titler

* Layout update
* New layers now use current selected font properties

## Contributions

**Николай Смольянинов** did a overhaul of wipe luma files with some new ones added and some existing improved.

**rtomj** fixed issue #660 caused by move to XDG folders.

**Alex Myczko** Updated INSTALLING.md with new information.

**jorgenatz** Change launch script for variant install locations

**cclauss** provided a batch of correctness fixes improving code base quality and helping towards Python 3 transition.

## Going forward

The next thing in line is the Python 3 conversion.

Things are looking good on this front and hopefully there will be no major setbacks. We may do a release that does just the conversion or perhaps do a longer release cycle with some new features added too. In any case there will be at least one more release this year to move Flowblade to Python 3.

## Translations updates

* Czech translation update by Peter Frei
* Italy translation update by Enrico Bella
* Ukrainian translation update by Slava Manoilo
* Russian translation update by Николай Смольянинов

## New small features

* Move fade buttons under Opacity slider in Compositors
* Add keep existing workflow item to new version first run workflow menu
* Removed Finnish translation
* Add Alt+S as keyboard shortcut for Sync All Compositors
* Make Control + Delete do Lift
* Make timeline auto expand if possible when making track heights larger
* Make Multitrim tool exit on empty click like other trims
* Add pref to loop clips in monitor, #623
* Make R do Overwrite Range and change Toggle Ripple to Alt + R
* Make track scrubbing action selection persistent
* Make Keyboard Shortcuts dialog non-modal
* Make mouse double click on track head toggle track height
* Show pulse progress bar when doing clapperless compare
* Make ALT + N open next media item in monitor
* Make , and . nudge selected clips on timeline
* Audio media items icon update
* Fix #529, more complete render settings saving
* Fix tool shortcuts display in Keyboard Shortcuts dialog
* Add append media from Bin to timeline feature, Issue #605
* Make audio scrubbing user settable
* Make Master Audio meter resizable
* Make possible to render speedup video with 601-2900% speedup, Issue #648
* Make possible to forca any language in any language OS
* Added Operation combobox for two alpha filters
* MLT profiles were updated

## Bug fixes

* Fix tracks resize to fit  failure bug
* Fix Issue #661 with no update on loaded filter data
* Fix Issue #659 with bad UI for buttons in custom theme
* Handle missing LADSPA filters in audio clip context menus
* Fix add fade in case kfs exist after fade length
* Update some MLT profiles
* Fix extra blank appearing when adding new video tracks
* Make recents list update for all saves
* Keep source bin open when doing drag'n'drop to another bin
* Fix reverted filter stack move menu items, #641
* Fix no drag for keyframe on first press when initializing Keyframe Tool from pop-up menu
* Fix value updates when going from Keyframe editor to slider
* Add missing keyframe editor updates in clipeffectseditor.py
* Fix cut tool playback bug
* Fix compositor end drag snap frame
* Fix Issue #640 with hite frames + static added to end of file when rendering fixed range
* Fix Media Relinker and Keyboard shortcuts dialog (nää ei ollut dynaamiset)
* Fix timeline track column repaint bug
* Fix args rendering on small screens when args window never opened
* Fix missing c_seq on load error
* Fix colors for visibility in workflow dialog, Issue #622
* Don't match profiles with more then 2x size difference to media even if fps matches, Issue #517
* Fix keyframe delete not registering when done as last edit

## Flowblade 2.0

Date: February 4, 2019

**Flowblade 2.0** comes with the largest changes to workflow and UX since the very first releases.

Timeline editing workflow has been made much more configurable, new tools have been added and GUI comes with a new custom theme (for Gtk+ versions >= 3.22), new top row layout and modernized design language.

### Workflow 2.0

The *insert editing* approach to video editing taken by previous versions of Flowblade has had the down side of being found by some users to be somewhat unintuitive. On the other hand many users have found it to be clean and efficient.

Flowblade 2.0 solves this issue by presenting a configurable workflow that enables users to make the application better confirm to their mental model of editing workflow.

#### Toolset Configuration

* User can select between 1 - 9 tools to be available via tool menu and shortcut keys 1-9
* User can set the order in which the tools presented and which shortcut keys they get.
* The *default tool* is the first tool in the tool menu with shortcut key **1**. This is the tool that is activated when for example exiting trims, this is settable by selecting the tool order

#### Configurable Timeline Behaviours

* Drag'n'Drop behaviour, user can select whether insert or blank overwrites are done on track V1 and others
* Composiors autofollow, users can make compositors follow their origin clips automatically

#### Workflow presets

   To get things going the user is given option too choose between two *Workflow Preset* options application start or at anytime later.

**STANDARD  WORKFLOW** has the **Move** tool as default tool and presents a workflow similar to most video editors.
**Tools:** Move, Multitrim, Spacer, Insert, Cut, Keyframe
**Behaviours:** Drag'n'Drop: 'Always Overwrite Blanks', Compositors Autofollow: Off

**FILM STYLE WORKFLOW** has the Insert tool as the default tool and employs insert style editing. This was the workflow in previous versions of the application.
**Tools:** Insert, Move, Trim, Roll, Slip,Spacer, Box
**Behaviours:** Drag'n'Drop: 'Overwrite blanks on non-V1 tracks', Compositors Autofollow: Off

#### New Tools

Four new tools have been added to selection of tools that user has available when deciding on their preferred toolset.

* **Keyframe tool** enables editing Volume and Brightness keyframes on the timeline with overlay curves editor.

* **Multitrim** tool combines Trim, Roll and Slip tool into a single tool that comminicates the available edit action with context sensitive cursor changes.

* **Cut** Tool allow performing cuts with tool in addition to earlier method of cut action at playhead.

* **Ripple Trim** tool was earlier available as a mode of Trim tool but it is now a separate tool.

#### Tools changes

 **Overwrite tool's name was changed to Move** and it was made the default Tool in the "Standard" workflow preset. New Move tool also has box selection and box move available as additional edit actions if user does a box selection starting from pressing on empty spot on timeline.

### GUI updates

We made quite a few updates and changes to the user interface to clean up and modernize the design.

**New Custom Theme** was created and made the default theme for the application. It has become clear that video editors are the kind of applications that work best with a custom made dark theme, the generic dark themes are too light for current established look of video editors. Now that GTK3 has finally stabilized the theme CSS, creating and maintaining a custom theme is now possible.

Earlier **panel design** with quite large buttons **has been updated** with a design employing more context and hamburger menus and by making almost all toplevel items icons.

For systems with larger screen dimension the **default top row layout has been changed to a 3 panel design** instead of the earlier 2 panel design, earlier layout still being available via user preference item.

**Tooltips coverage was extended** and almost all top level items now have individual tooltips..

Insert and Move (earlier Overwrite) tools have new cursors.

### Keyframe editing updates

In addition to new Keyframe tool many updates were made to keyframe editing.

**Slider to Keyframe editor functionality.** Majority of filter parameters that earlier only had a slider editor available for setting a single unchanging value can now be eddited with a keyframe editor. There is a new keyframe icon in slider editors that turns slider editor into a keyframe editor when pressed. Kyrame editor can also be turned back into a slider editor.

Keyframe editors now have buttons that **move keyframes 1 frame forward or backwards.**

Keyframe editor **out-of-clip-range keyframes now have info** on on them displayed and there are editing actions available for deleting and setting their values.

Keyframe editors are also now updated on all mouse events making it more intuitive to know the value of a parameter in all keyframes.

**Compositor geometry editors now have numerical inputs**.

**Shift + Arrow keys now change scale** in Compositor geometry editors.

### Compositors

* **Transform Compositor** was added. This provides some transformations like rotations that previously were not available.
* **AlphaXOR, Alpha Out and Alpha In Compositors** were added that provide additional ways of combining images using  alpha channel data.

### Edit Action updates

**Ripple delete Button**, that does multitrack ripple to maintain sync between tracks if overwrites can be avoided.

**Shift + X cuts all tracks on Playhead.**

### Contributions

**Sequence Split functionality.** It is now possible to split Sequence at playhead position to create a new Sequence from timeline contents after playhead, by **Bene81**.

Fix GTK version detection logic inversion problem, Issue #521, **by Bene81.**

Reducing video track count damages project Issue #486, fixed by **Eliot Blennerhassett.**

Change tracks dialog now gets current sequence track counts, not hard coded values by **Eliot Blennerhassett.**

Some wipe luma files for wide screen do not work correctly, Issue #572, fixed by **Николай Смольянинов** who also provided very helpful release QA.

Make Flowblade exit cleanly if audio waveform rendering is still on, by **Steven van de Beek.**

Add appdata file used by e.g. GNOME Software or KDE Discover  by **Peter Eszlari**.

Change icon path in setup.py to comply freedesktop with spec, fix mimetype data to be consistent, by **Peter Eszlari**.

Archlinux docs fix, depends sdl_image by **Bernhard Landauer.**

### New translations

Steve Nian contributed Traditional Chinese translation. 
Slava Manoilo contributed Urkrainian translation. 

### Help docs in Russian

**Николай Смольянинов** created the first full translation of help documentation, docs are now available in  Russian too.  **Andrey Grigoriev** provided some additional scripts to display correct helps in all systems.

### Translations updates

Czech translations updates by **Pavel Fic and p-bo.**

Russian translation update **Николай Смольянинов.**

Polish translation update by **Stanisław Polak.**

German translation update by **Martin Gansser.**

### Refactoring

Some worst modules were cut in half and object naming was somewhat improved.
Modes setting code was moved from module *editevent.py - > modesetting.py.*
Screen editors code was renamed and moved from module *keyframeeditor.py -> keyframeeditcanvas.py.*
Unused imports were removed using pyflakes analysis.

## Future directions

This release took longer then would have been liked for various reasons, but mainly because the feature set was larger then usually and getting a release out of at least reasonable quality took some effort.

We will be doing 2 more releases this year with feature sets that will be adjusted to make sure that we have some nice incremental steps forward. There is an updated roadmap for larger development directions thought to be important right now and Issues list has quite a few items that need addressing. 

### Smaller fixes and features

Add prefeference to not move to clip start on keyframe edit init

Keep filter editors open on most edits #537

More height for Compositor geometry editors on larger screens.

Make clip editor next/prev buttons stay in edit range.

768px height and some other screen sizes fixes can now full screen properly.

fix track locking for multiple tools.

Fix recent files bug.

No more changing to default edit mode on media drop

Add follow tline range in playback option, Issue #503.

Offer preference to switch mouse horizontal scroll direction, #499.

Fix Issue #532 by removing lossless mpeg2 rendering.

Make G'Mic tool monitors bigger for bigger screens.

Fix "Blend" Compositor

Remove some less useful preferences.

Fix trim info dialog texts.

Fix Issue #558 with setting user lumas.

Make possible to start playback with Space after loading clip in monitor with double click.

Support Shift range selection in media panel.

Fix Issue #497 with timeline mouse events on load.

Make possible to move Bins up/down in GUI.

Make hard coded paths work with flatpack.

Add Keyframe Editor editor buttons tooltips.

Fix Keyframe Editor icon positions for Flowblade/arc theme.

Fix MLT version filters dropping.

Fix crash by banning Qt producers to keep using Gtk producers after Qt ones were made default in MLT.

## Flowblade 1.16

Date: March 31, 2018

**Flowblade 1.16** is the sixteenth release of Flowblade. This cycle we mostly had improvements, refinements and bug fixes building on existing features. A lot of time was spend on developing new video display code, but we didn't get any results there yet. Work on that front will continue, we have some issues that need to resolved eventually and the currently used technology is slowly on its way out.

### Tool cursor timeline sensitivity

This is the biggest user visible change. Previously tool cursors didn't react in any way to the timeline contents, now they change appearance on appropriate positions to signal that some different edit actions are available.

* With **Insert tool** and **Overwrite tool** the cursor now changes on clip and Compositor ends to indicate that the user can drag the ends to lengthen or shorten the clips or Compositors. On top of Compositors cursor changes to indicate that Compositor can be dragged to a new position.
* **Trim tool** now changes appearance to indicate which end of clip will be trimmed if Mouse Left is pressed and held.
* **Box tool** now changes when entering selected box to indicate that box contents can be dragged sideways.

This feature was so far avoided by design based on the fact that it requires quite precise mouse positioning to initiate desired edits and larger target areas are easier and quicker to hit.

However, it has become clear that users prefer context sensitive tool cursors, the main evidence being that almost every other edit program has them, so this was now added to Flowblade. This will probably help beginner users more easily to get going with Flowblade.

The feature in on by default, but can be disabled to return to previous behaviour.

### Tool cursors GUI update

Tool cursors appearance got an update as part of the timeline sensitivity work. The biggest change was to Overwrite tool cursor, it is now otherwise the same as the Insert cursor, except that it is red.

### Compositor auto follow

It is now possible to set Compositors to automatically to follow their origin clips as clips are moved or trimmed. It is possible to set individual clips to remain manually editable even if auto follow is set on. This feature can flexibly offer good sides of both clip embedded Compositors and free flowing Compositors.

This mode is off by default and needs to activated from track popup menu.

### Re-rendering rendered transitions

Rendered transitions can now be re-rendered e.g. when the clips that were used to render the transition have had new filters added. 

It is also possible to batch re-render all rendered transitions. This is useful e.g. after leaving proxy mode before doing final render as in proxymode rendered transitions are rendered from proxy clips, and therefore are of worse quality then rendered transitions created from original media.

### Clip markers

Users can now add markers to clips, before markers could only be added to timeline positions.

### Some notable updates

**Luma Wipe** can now be made to run in reverse directions, earlier it could only be made alpha inverted.

**A 'Playback' panel** was added to Preferences dialog keep item count per panel low enough for quick discovery.

**G'MIC Effects tool** now works with G'MIC version 2.

**Timewarp producer** is used if available to **have sound on forward slow/fast motion clips.**

**Compositors and Effects** can now save and load their parameter values.

### Flatpak

Github user *eszlari* created a Flowblade 1.14 Flatpak which is already available on Flathub. Version 1.16 is coming there too in the coming weeks. We will post info on Google+ on that when it is done.

### Contributions

*atomicfile.py* module was added by *Nathan Rosenquist* to make saving data more robust.

Николай Смольянинов provided a series of reports on missing translations strings, the coverage should now be close to 100%.

### Future directions

The focus areas of next release will be animations, masks and compositing. So far the focus has squarly been on Flowblade as an editing tool, but now we will look for ways to expand application's feature set in this direction.

There are a number of approaches that can be tried here, and it is difficult beforehand to predict which will work out, so we will basically try everything and see how things turn out. The translations workflow update will definitely come too.

We will keep the 6 month release cycle, so next release will be sometime in the autumn.

### Other bugfixes and improvements

* Remove all prints with possible non-latin characters from save/load
* Fix Issue #478, crash on small screens
* Add info on rerendering proxies when in proxy mode telling user to change to original mode, issue #435
* Show some info on alpha filters add to help users understand that they need to add compositor too
* Make some missing blend modes available for translation, fix #461
* Fix Issue #465, rendering frame sequences with PNG codec
* Fix crash on media item double click, Issue #466
* Fix small screen regression caused by new fade buttons, Issue #467
* Fix Issue #436 with ruler marks in 23.98 and fractional framerates
* Fix Issue #456 with batchrendering and unicode
* Add audio sync error infos to translations
* Fix #483, frames per image in image sequences
* Fix audio muting bug #362
* Make selected blanks stand out better
* Make active keyframes stand out better
* Remove all prints with possible non-latin characters from save/load to fix possible issues

## Flowblade 1.14

Date: October 4, 2017

**Flowblade 1.14** is the fifteenth release of Flowblade. This release had probably more new features then any release  since the initial release 0.6. New functionality like sequence combining, compound clips and audio syncing take the application to the next level as a complete editing solution.

Especially sequence combining feature together with existing features like *Range Log* make Flowblade easily the most advanced and featureful FLOSS tool for projects with long complex edits and large amounts of media.

Improved user feedback has also made possible to refine many areas of functionality beoynd original design. 

### Audio Syncing

Python module *clapperless.py* by *Martin Schitter* and *Benjamin M. Schwartz* has made it possible to offer functionality that syncs media items based on their audio data. We have two new features offering Audio Syncing functionality.

* **Timeline Audio Syncing** Now you can select  two clips on timeline and request one of them to be moved so that clips' audio is synced on timeline. This makes it possible to do multicamera editing on timeline, one needs to manually set video mute on/off on tracks to see all tracks, but the workflow is possible now.

* **Audio Synced Compound Clips** User can select a video and audio clip and create an audio synced compound clip media item from them. This is useful e.g. when audio is recorded separately and video clip only has some help audio.

### Combining Sequences

It is possible to import full contents of another Sequence into the Sequence currently being edited. There are two ways provided to combine sequences:

* Imported sequence can be **appended at the end of current sequence**.
* Imported sequence can be **spliced in at the playhead position**.

This long overdue feature will make having multiple sequences per project a much more useful and flexible tool when building complex programs from smaller parts.

### Compound Clips

A **Compound Clip** is a single clip created by combining multiple clips and compositors in to a single media item. Compound Clips are useful when some complex sequence is more conveniently handled as a single unit.

* **Compound Clip from Selection** feature creates a Compound Clip from currently selected clips into a Compound Clip.
* **Compound Clip from Sequence** feature creates a Compound Clip from current full contents of the timeline.
* **Audio Synced Compound Clip**, see above.

### Fade in/out

We have two new features addressing user requests for speeding up the process of creating fade in and fade out transitions.

* **Fade Compositors** These are special new compositors that will automatically on creation place themselves at the beginning or end of clips and do not need any keyframe manipulation; lengths of fades are changed by changing the lengths of compositors.
* **Add Fade buttons** *Compositors* panel now has **Add Fade In** and **Add Fade Out** buttons that will create keyframes that define a fade of desired length in a single click.

### User Selectable Keyboard shortcuts

**Steven van de Beek** contributed code that makes it possible to have user defined keyboard shortcuts. In this release we offer a possibility to select between two predefined sets of shortcuts, and fully configurable keyboard shortcuts will be made available in the future.

### Tools development

#### Reverse clips tool

We now offer a new tool to create reverse clips of user selectable speed from media items.

#### Titler

Titler got two new features:

* Text drop shadow 
* Text outline

#### Disk cache management

Disk cache management window provides GUI tool for deleting saved hidden files that could eventually consume noticeable amounts of disk space.

### Translations

We got a new new Cantonese translation by 老吴的BOX.

We got fully up to date translations for 1.14 in Russian, Polish and Czezh by Николай Смольянинов, Stanisław Polak and Pavel Fric respectively.

### Future directions

During next cycle work continues roughly as outlined in road map and Issues list at Github. 

Translations workflow update is definitely in the plans. The current workflow is difficult and outdated when there are several web solutions that are likely preferable to all translations contributors.

Next cycle will also see move to spending more development time on some upstream issues that can take a bit of time to come through as available features in the application, especially on installationss from distro repositories.

We will probably continue with the 6 month release cycle, but a shorter one is possible if certain planned improvements come together quickly enough.

### Other new Features

* Import media items from another project.
* Support for manually entered time codes/frame values on clicked time code display  in **by Bene81**.
* Timeline edit move delta info overlay.
* Save render settings for proxy conversions.
* Add Lossless FFv1 profile **by lsde**.
* Fix timelineline zoom issue causing problems with scrolling.
* About menu visually improved **by Mostafa Ahangarha**.
* Allow user preferences for Fast Forward / Reverse speeds **by Steven van de Beek**.
* Allow shrinking timeline vertically when fewer than maximum tracks used tracks.
* Make Range Overwrite 3 point edit work with only In set on Timeline.
* Enable Volume filter to  bring volume up > 100%

### Feature Removals

* Dropped **Zoom Pan filter** because it does not work on all files.

### Other bugfixes and improvements

* Double track heights for HiDPI screens.
* Fix frame sequence render issue.
* Fix wrong FPS on import for certain clips.
* Fix Slip tool bug for clips with index 0.
* Fix keyboard focus handling for 2 window layout.
* Add guide lines for shift down edits in geometry editors.
* Fix double click on blank crash.
* Fix trim view handling for roll and slide with TRIM_VIEW_SINGLE.
* Fix change profile unicode bug.
* Get confirmation when rendering from proxy media.
* Make default rate 8000kB for rendered transitions.
* Get overwrite confirmation when rendering.
* Disable cut action when it might interfere with ongoing edits.
* Fix titler for 1.13 numpy.
* Save mark in/out for proxy conversions.
* Make keypad 1-7 change tools too.
* Fix issue with Volume filter spin inputs.
* Fix keyframe drag to last frame bug.
* Fix not updating TC display after layout change.
* Fix unicode marker names.
* Add Clip Edit menu.
* Reverse order of SCOPE_MIX_VALUES.
* Add Window mode menu item.
* Fix duplicate profiles.

## Flowblade 1.12

Date: March 18, 2017

**Flowblade 1.12** is the fourteenth release of Flowblade.

In this cycle the main developments were the adding of new tools for the first time since 0.14, and the increased level contributions the project received.

Much time was spend on creating an AppImage for the project but unfortunately no satisfactory end result was reached, so there will not be an AppImage with latest dependencies available for Flowblade yet.

Even with this and some redesign related delays we were able to advance the project at a reasonably pace.

### Box tool

New Box tool is provided to help with the use case of moving a range containing media on multiple tracks to another point in the sequence. This has previously required multiple edit steps to achieve. The Box tool will reduce the number of required edit actions.

The main intended use case is probably best explained with a video: https://vimeo.com/207310517

### Trim tool Ripple mode

Every use of Trim tool will cause the edited track to lose sync with other tracks after the trim point. The Ripple mode enables in most cases doing trims while maintaining sync with other tracks. Some points on Trim Ripple mode:

- Sync is maintained by changing the lengths of the closest blanks on other tracks. This might not produce the edit you wish to achieve, in that case you will need to use Trim tool in default mode and do the edit in multiple steps.
- No overwrites are allowed to happen so the available trim length is constrained by blank lengths on other tracks.
- This tool is not provided as a separate tool and it is not given a GUI top level representation because it became clear that the resulting multitrack edit can be found confusing by many users
- The tool can be accessed by toggling the Trim tool mode using 'R' key when timeline has keyboard focus.

### Contributions

We added a new category 'Developers' in the About dialog for contributors producing multiple patches and taking part in development discussions. The first developers that were added to this category were Steven van de Beek and Nathan Rosenquist.

*Steven van de Beek*

- Fix loading of projects with unicode names.
- Fix "Size/height" for multiple filters in "Transform" group
- Fix Render Folder from Preferences not being copied to Render panel
- Change .xml file to associate Flowblade logo to .flb files.
- Optionally Show Full Filenames in Media items
- Render with multiple threads and allow drop frames in playback.

*Nathan Rosenquist*

- Add option to hide file extensions during import for cleaner media names
- Round FPS to whole numbers for NTSC time code to get NTSC timocode correct
- Fix updating bin file count after deleting files
- Make 'End' key and move playhead to the end of sequence.
- Explain video gamma problem on certain systems.

### AVFilters

MLT 6.2.0 added AVFilters support. Flowblade now offers additional filters if you have MLT > 6.2.0 with AVFilters module installed.

- *Lut3D* This makes possible to add similar film emulation filters that are available in G'Mic by using **.cube** files. 
- *Zoom/Pan* Similar functionality current "Affine" filter but the performance is much better
- *Color Channels Mixer* This makes possible to use color data of one channel to determine color output of another channel. Basic example would be making green shirt blue by using green color data to display blue color.
- *Perspective* Stretch image in way that can enable changing perspective.
- *Lens correction AV* Filter that corrects typical lens errors.

### Translations

We got a new Russian translation by Nikolai Smoljaninov. There are over 100 million Russian spekers in the world and most use localised applications, so this widens the potential user base  in a big way.

Hungarian and German translations got updates by Péter Gábor and Mario Dejanovic.

### Future directions

*Move to 2 releases per year instead of 3.* The release overhead and associated project slowdown has been getting bigger lately and with container formats possibly added to release requirements it is better to make the development cycles a bit longer to get overall better development throughput. 

*Container formats and Wayland support* These technologies are still being developed and adopted. Solutions here are worked on will be made available when ready.

*Focus areas for next cycle include* continued work on Issue list and Roadmap, Clip Compositors that automatically follow clips even across tracks will be attempted, tool integration hopefully gets a bit of attention, small website update and more tutorial videos will be done.

### Other bugfixes and improvements

- Fix extraraeditors.py translation problems (Péter Gábor)
- Add missing params for translations (Péter Gábor)
- Fix trim view for blank match frames
- Set insert tool active after project load
- Make marker graphic a bit more visible in dark theme
- Make Trin and Roll edits snap
- Make Spacer tool snap
- Add higher bitrates for h264 and Theora codes for 4K encoding
- Add 4K profiles for projects and rendering
- Makes tracks number selection free with max. 9 tracks available
- Add center playhead on arrow move preference
- Make Control key keep aspect ratio when scaling with Affine Blend GUI editor
- Fix adding graphics default length in and out to Image Sequences media
- Add Compositor values copy-paste feature
- Make Control key move image 10px for every arrow key press in Geometry editors
- Make Mouse scroll zoom/scroll by selecting a preference.

## Flowblade 1.10

Date: December 13, 2016

**Flowblade 1.10** is the thirteenth release of Flowblade.

This cycle was a nice change in the sense that not much time was needed on project structural issues such as porting to GTK3 or creating a website.

The main feature in this release is the new Trim View, with the additional features being focused on editing and some GUI updates.

Next release cycle will focus on improved tool integration with the goal of providing more convenient and efficient ways to manipulate and create media within Flowblade in concert with other existing FLOSS tools. Some new editing tools and options will also be worked on, as well as bug fixes and feature requests in the Issues list.

Appimage for this will release will become available in January and for all subsequent releases it will be available at release date.

### Trim View

Trim View is feature available in most commercial packages and now also in Flowblade, probably as the first FLOSS video editor. It is maybe best described just by a [screenshot.](https://raw.githubusercontent.com/jliljebl/flowblade/master/flowblade-trunk/docs/1-10_trimview.jpg). The advantages are clear: user is provided with more information when doing a trim and is thus able to better assess the correct cut frame within a single edit action.

Points on Trim View performance

- for "Trim" tool the trim tool should mostly work quite well
- for "Roll" and "Slip" tools there is no getting around the fact that two video streams need to be displayed in real time. The following performance considerations apply:
  - SSDs perform better the spinning hard disks
  - faster processors improve playback
  - video streams like image sequences consisting fully of I-frames perform better than streams with a lot of B- and P-frames

For these reasons the **Trim View is off by default and needs to activated from menu below the monitor**. Users are advised to assess for themselves if performance is satisfactory for system and media they are working on

### Frame Matching

Trim view layout also addresses a fundamental restriction of a single monitor layout: user is unable to compare video material to other material when deciding on a clip to add to a sequence. We now provide two mechanisms to help with this use case:

- monitor frame matching, shown [here.](https://raw.githubusercontent.com/jliljebl/flowblade/master/flowblade-trunk/docs/1-10_monitor_match_frame.jpg)
- timeline frame matching, shown [here.](https://raw.githubusercontent.com/jliljebl/flowblade/master/flowblade-trunk/docs/1-10-timeline_match_frame.jpg)

### Editing Improvements

- a "Delete Range" button is now provided to cut and lift material inside selected range on all tracks
- Filters in filter stack can now be rearranged
- Spacer tool got some bug fixes improving its usabily
- User can now select all clips before or after a clip on timeline using a popup menu option.

### xport from timeline to tools

- timeline clips can be now exported with frame range preserved to G'MIX Effects Tool, Slow/Fast Motion renderer and Natron if it is installed in the system.

### Dual monitor and small screens improvements

- dual monitor support has been improved by providing a to window layout shown [here.](https://raw.githubusercontent.com/jliljebl/flowblade/master/flowblade-trunk/docs/1-10_dual_monitor.jpg)
- small screen sizes support has been updated with multiple bug fixes and feature additions.

### GUI updates

- Monitor area layout was updated with the main goal of providing clearer visual cues whether Timeline or Clip is displayed in the monitor by making the selection buttons much bigger.
- Middlebar got some minor visual updates

### German translation update

- German translation received an update from Mario Dejanovic.

### Other bugfixes and improvements

- Make render args available for small screen heights
- Make Master Audio Meter available for small screen heights 
- Fix displayed media lengths for old and changed profile projects
- Ask for exit confirmation when opening non-empty projects from recents list
- Add 7/2 and 2/7 track configurations whencreating new projects
- Trim init optimization
- Fix adding watermark dialog freeze
- Show file name in media item tooltip
- Add track active set actions to all tracks menu
- Make Media Relinker remember last folder
- Make Media Icons display length at bottom and range at top
- Remember fade/transition lengths between dialog invocations
- Make holding down Shift key snap to X or Y in compositor editors
- Update track lock icon
- Menu actions to turn all filters in timeline on/off
- Make Home key move to timeline start

## Flowblade 1.8

**Date: September 19, 2016**

**Flowblade 1.8** is the twelfth release of Flowblade. 

During this cycle a lot of time was spend on creating a website for the project and on bringing a node compositor tool to Flowblade. Website was successfully deployed, but the node compositor tool was dropped in final stages of development.

The node compositor was dropped when I realized that it does not serve any user group particularly well.

Casual users will find difficult to use node compositors effectively as any non-trivial composition requires creating complex node graphs. On the other hand adcanced users already have alternative FLOSS solutions like Natron and Blender available, and are unlikely to adopt this tool in meaningful numbers.

Once it became clear that it would require postponing this release quite a bit to do the remaining bugfixing and creating documentation, I decided that the project is best served by allocating resources to other areas of development.

We did get some good stuff in, and with the next cycle we can hopefully get moving with improved speed of feature development.

Particular attention will given to the current *Issues* list, with some of the other focus areas being improving integration between tools and timeline, and an attempt to make nested clips available.

### Flowblade Main Features

* **Keyboard trimming with arrow keys** Trim positions can now be moved using arrow keys and trim edit confirmed with pressing Enter key. This is often more convenient and precise then always working with a mouse
* **Clip Snapping** Clips and compositors will now snap to clip ends on adjacent tracks when clips or compositors are moved or their ends dragged. 
* **Clips display media thumbnails** This helps differentiating clips from each other on timeline.
* **EDL export** is now available. Thanks to Github user *tin2tin* for extensive testing on software not available on my system. Unfortunately it became clear that Blender EDL import is buggy.

### G'MIC Film Emulation Filters

G'MIC Effects tool got an important capability update with the addition of film emulation filters.

G'MIC Film Emulation Filters change the tones and gamma of the image to resemble different film stocks. Where as other color correction filters available in Flowblade work with luma or R,G,B LUTs, film emulation filters employ much bigger LUTs which are applied to the 3D color space of the image, and can achieve more detailed changes. 

The results have been quite nice during testing; it is often possible to achieve subtle effects that greatly improve the look of the material.

### Contributions

In this cycle we got the largest amount of contributions per cycle so far.

* **Hungarian translation** was provided by Péter Gábor. These take a big amount work and we're always happy to receive a new one.
* **Play/pause toggle with single button** functionality was provided by Github user *dvdlvr*. This has been asked before so a portion of users probably likes it better like. The new behaviour needs to be activated from *Preferences*
* **Titler remembers last save directory** patch by Martin Mois. Before the user needed to always navigate away from the default folder when saving titles.
* **New anti-aliased the monitor control icons and modified the clear marks icon** by Github user *bergamote* improve visuals on that part of the GUI.

### Bugfixes and enhancements

* "Change Project" functionality fixed, and works much better now 
* If first loaded media does not match current project profile, user is informed and given option to switch to matching profile.
* Fix assoc file launch from e.g. Nautilus
* Improve missing rendered transition media overlap info
* Compositors can now move by dragging from middle too, not just edges
* Do gi.require() for Gtk and PangoCairo to silence warnings and specify Gtk+ 3
* Make MLT version detection work for two digit version number parts
* Fix adding media while in proxy mode
* Check and give info on IO errors when saving in main app and relinker
* Add keyboard shortcut 'R' for resyncing selected clip or compositor
* Display image sizes for graphics files in info dialogs
* Make CTRL + Mouse toggle media items selection state, not just add to selection
* Make KeyFrameEditor prev button update keuframes info
* Fix updating non-existing clip in effects editor after delete
* Make Compositor GUI edit update keyframe count display
* Add user selectable scope overlay opacity
* Add timeline start indicator triangles
* Remove non-existing files from recents list
* Fix launching uninited renders
* Fix too long filename layout bug in filter editor
* Fix unicode project name bug
* Display warning icons for non-profile-matching video media
* Reset titler for new project

## Flowblade 1.6

**Date: March 2, 2016**

**Flowblade 1.6** is the eleventh release of Flowblade. The main feature of this release is the new G'MIC Effects tool.

### G'MIC effects tool

G'MIC is a full-featured open-source framework for image processing developed by french research scientist David Tschumperlé and others. Its main strength is that it enables creating complex new image filters without writing any compiled code.

For applications such as Flowblade this makes it possible to offer a wide range of image filtering capabilities using a relatively small amount of managed code.

A [demo video](https://vimeo.com/157364651) of some features available in the first release is available at Vimeo. This is just the first step, many more filters will come in the future.

### Other main features in this release

* **Changing project profile is now possible.** This is a feature that was requested by users who felt uneasy about having to commit to a profile at the beginning of the project.

* **Drag'n'drop of media files from other applications** is a standard feature that has so far been missing from Flowblade.

* **Middlebar was updated** on wider screens as G'MIC, Batch Render Queue and Split Audio buttons were added.

* **'Sync All Compositors' functionality was added** This can be very useful in situations where a track as a whole is moved in relation to other media.

For the next release cycle the focus will be on integrating existing technologies to improve Flowblade's capabilities in doing motion graphics. The Natron compositor project offers a lot of promise here, and the existing node compositor by myself will be made available in some form.

Also a project website will be developed during this cycle. The first version is to be made available in a week or two.

The next cycle will be the longest since 0.16 because of the amount of coding and research needed. The target release date for 1.8 is September 2016.

#### Bugfixes and enhancements

* Fix set parent clip functionality
* Fix translation scripts (apienk)
* Re-create all media icons always when requested
* Fix dark theme monitor indicator icon
* Fix change to first bin after media load bug
* Remove alpha mode functionality from compositors
* Fix batch render to respect profile selection
* Fix single render to respect changed profile
* Open missing asset project directly from info dialog into Media Relinker on request
* Add Mark In and Mark Out data to clip info dialog
* Remove write env data functionality
* Fix dark theme mute video icon
* Add transition button to TC Middle layout and combine it with edit buttons group
* Fix filter cloning for filters with non-mlt properties
* Make Titler work better with non-square pixel formats
* Add HD 1080p 60fps profile
* Range Log sorting upgrade and gmic encode view update
* New undo-redo icons (bergamote)
* Render slowmo files from original when using proxy files
* Make possible to render slowmo file from a Range Log item
* RHEL7/CentOS compatibility patch (Martin A. Wielebinski)
* Fix file info fps display
* Make relinker and batchrender use dark theme
* Make single render use dark theme and add percentage display
* New in/out markers (bergamote)

## Flowblade 1.4

**Date: November 24, 2015**

**Flowblade 1.4** is the tenth release of Flowblade and the first release after the GTK3 port.

Most main features in this release are changes to editing model that were designed to make editing more approachable and quicker. It is also notable that a large part of the main features were based on user requests, a first for the project.

In the next release cycle features that will be attempted include a G'MIC effects scripting tool, a node compositor tool using an existing code base, a first launch tips window for new users, and a clip snapping feature.

In 2016 there will probably be 3-4 releases, and the next release 1.6 is targeted for March. There will be some reports on progress in the Flowblade Google+ group.

### Main Features in this release

* **Fade/Transition cover delete feature was added.** Selecting a single rendered fade/transition clip and pressing delete will cause the deleted area to be covered using material from adjacent clips if such material is available. This makes working with single track transitions/fades faster. Previous behaviour can be restored using a preference option.

* **Clip ends drag with Control + Right mouse.** When a move tool - <i>Insert, Overwrite or Spacer</i> - is selected clip's ends can now be dragged to change clip's length. This is useful when for example a clip in a multitrack composition needs to be made longer to cover a clip on a track below. Clips end drags perform overwrite on empty/blank regions and insert on media regions of timeline.

* **Drag'n'drop overwrite action on non-V1 tracks** has been added. Dropping clip on track V1 works like before, but on non-V1 tracks:
  
  * clip will be inserted if dropped on a clip 
  * clip will overwrite available blank and empty space and will perform insert for the length of media frames that would be overwritten.
  
  This makes creating multitrack compositions faster. Previous drag'n'drop behaviour can be restored using a preference option.

* **Always on audio levels display** functionality was added. Before the audio levels could only be displayed on request, but now it possible to have audio levels rendered on background and displayed as soon as they are available 

* **Filters can now be copy/pasted from one clip to another**. It has been possible to copy paste clips on timeline for quite a while, but now this feature was made more discovarable by adding menu items for the functionality.  

#### Other features and enhancements

* Fix media relinking for projects with SAVEFILE_VERSION < 4
* Add 1080p 50fps profile
* Fix keys 1-6 stopping working after tool selection
* Fix snapshot save same basename bug
* Add fullscreen view
* Begin work on add xdg-app support 
* Fix color clips backwards compatibility for some old projects
* Add info text active keyframe and number of keyframes to keyframe editors
* Make 'Control + Left/Right arrow' move 10 frames at a time
* Add 'Clear Filters' item to clip pop-up menu
* Make effects editor keyframe editors listen for space key play/stop
* Fix crashing keyframe editor for multitrack moves
* Make compositor editors zoom with mouse scroll
* Make Space for play/stop work then focus on keyframe editor
* Make Affine Blend editable with arrows keys
* Make keyframeeditor.RotatingGeometryEditor receive keyframe updates

## Flowblade 1.2

**Date: September 9, 2015**

**Flowblade 1.2** is the ninth release of Flowblade.

Flowblade has now been ported to GTK3.

* **The process was not as straight forward as one might think** but eventually everything worked out. There always seemed to be just one more little change in API that required all instances to be fixed by hand. Luckily there was a conversion script available that did most of the grunt work to get things going.
* **We did get something in return**. A small but percipteble responsiveness improvement was gained probably because GTK3 provides a Cairo widget for creating custom widgets that is now used instead of the project specific Cairo widget that was used before. GTK3 also seems to render widgets a bit crispier.
* **I really hope that major API breaking version jumps for widget toolkits are avoided as much as possible**. Projects with large interface and small man power can really suffer here. 

There were some other major developments during the cycle too:

* **All rendering was moved out of process** as the in-process rendering was found to not work correctly in some cases.
* **Dark theme support was improved**. It is now possible to use a dark theme just by setting a preference if the GTK3 theme used has a dark variant available.
* **Small screen support has been upgraded**. The application now works better on 768px height screens.

There has also been more contributors then ever, so the move to Github seems to have a positive effect on the project visibility and participation.

After bug fix release 1.0 and GTK3 port release 1.2, the next cycle will be about getting back on track with steady improvement in features and stabilization.

The 1.4 will also be the first "real" release of the 1.x series. In the 1.x series all changes to project format, editing paradigm and fundamental technical structure are avoided in favor of creating a solid application that reaches its full potential within the chosen tech/design path. The 1.x series will probably last for about two years, after which further fundamental change will be considered.

#### Other bug fixes and enhancements

* Add preference to always use English on a localized OS
* Make audio sample rate user selectable for rendering
* Drop support for creating new 'Affine' compositors. 'Affine' didn't work properly.
* Make color clips use hidden pngs instead of mlt producer to fix compositing crashes.
* Fix MPEG - 4 / .mp4 rendering to always respect source image shape 
* Fix transform filters by removing non-persitant scaling properties
* Fix clip audio sample frequency and channels info display
* Use translations at /usr/share/locale if available
* Fix preset encodings batch rendering 
* Make image sequence open dialog use the last opened media directory
* Make out-of-process tools write log files

## Flowblade 1.0

**Date: June 15, 2015**

**Flowblade 1.0** is the eighth release of Flowblade. It turns out that you *can* write a video editor with those Python bindings to MLT.

This release focused almost entirely on bugfixes to ensure maximum quality of existing features for 1.0 release. This was probably a good decision as quite a few bugs were found and fixed.

Quite a bit of time was spend moving the project from Google Code project hosting to Github. After a short time here it's quite clear that Github is a superior platform, so it was all for the better.

Next release cycle will be devoted to the GTK3 port. Hopefully everything goes according to plan, and we can get back to adding new exiting features to the application.

#### Bug fixes and enhancements

* Make range item delete work logically
* Fix Range log group functionality
* Media files pop-ups only display usable items for media type
* Fix Media Relinker to work with image sequences correctly
* Make backup snapshot have .flb ext no matter what user enters
* Fix snapshot saving for image sequences
* Add missing image sequence proxy render functionality
* Fix snapshot relative paths lookup for image sequences
* Update project event time display text
* New fallback thumbnail icon
* Fix MLT version comparison 
* Brightness Keyframed bug fixed
* Moved help files from Google Code to HTML resource files
* Remove panel frame shadows for cleaner look

## Flowblade 0.18

**Date: March 19, 2015**

**Flowblade 0.18** is the seventh release of Flowblade and the last one before 1.0.

Features in this release concentrated on media management, as that was thought to be the last under developed area that needed to be addressed before 1.0.

This cycle was a bit difficult as considerable work was done on features that were then abandoned because satisfactory functionality could not be achieved at this time. Also, the features that were released went through a redesign forcing a full  code rewrite and the quick and easy release cycle turned into major undertaking.

Through all this it became clear that the time for Gtk3 port is now. Next release will be 1.0 and only bug fixes and some minor editing work flow features will be added. 1.0 will also be the last Gtk2 release of Flowblade.

### Main Features in this release

* **Relative paths for media assets** are now supported. If media file is not found using the saved absolute path, a file with same name is searched from subfolders relative to project file directory.
* **Save backup Snapshot** functionality saves project file and all media used by project in selected folder for convenient backup.
* **Media Relinker** tool makes replacing missing media files easy.
* **Image Sequence Rendering** for exporting project as a file sequence is now available.

#### Other features and enhancements

* Current Frame export
* Fix Batch render track mute bug
* Color Pulse and Ising pattern producers added
* Fix Titler closing and saving bugs
* Color Lift Gain Gamma filter added

---

## Flowblade 0.16

**Date: December 2, 2014**

**Flowblade 0.16** is the sixth release of Flowblade.

This release has only one major new feature, and marks a change in the approach until the 1.0 release is done.

The next 2-3 releases will contain at most 1 new major feature along with smaller enhancements and bug fixes. The releases will also come quicker, once every 3-4 months.

The previous release completed the editing concept and feature list needed for 1.0. The 1.0 release will be made before the end of 2015, after which the focus will shift immediately to the porting of the application to gtk3.

The code base refactoring has come to a conclusion with this release, and the focus when improving code readability will now shift to adding and improving comments.

### Main Features in this release

* **Audio Master Meter** has been added to top level GUI to help working with audio.
* New **Chroma Key** filter works better on blue and green screen keying than the existing Color Select filter
* **Luma Key** enables keying based on image luma values
* **Batch Rendering** was changed to use dbus instead of PID files and should now  actually work

#### Other features and enhancements

* Add German translation
* Add Italian translation
* Fix Quick Enter and Quick Exit trim white blank display bug
* Final round of refactoring before 1.0
* Fix start-up problem from missing threads\_enter() - Louis C. Villa
* Require pygtk 2.0 to fix start-up on some systems - Louis C. Villa
* Update timeline tools overlay GUI
* Make Clip Monitor remember displayed frame
* Fix flashing black around monitor bug
* Add keyboard shortcuts ALT + I and ALT + O to move to in and out points
* View selector for media panel to display all or only certain types of files
* Add info on duplicate media items on load
* Refactor and fix audio monitoring display update and exit

---

## Flowblade 0.14

**Date: June 18, 2014**

**Flowblade 0.14** is the fifth release of Flowblade.

This release has some good new features and improvements, see below for more info. It also seems clear that the "release every 6 months" schedule suits the project well at this stage, and it will be kept for the future.

In the next release cycle attention  will be paid to rendering output files and media and project management.

New features for the next release have not been decided on yet, but MLT webFX module will be looked at, and there are some other services available that are not yet utilized by Flowblade.

### Main Features in this release

* **Color Correction improvements** in this release take a major step forward.
  * New 3 band color correcting filter **Color Grading** makes professional level color manipulation possible on Flowblade
  * Industry standard Catmull-Rom based **Curves** filter (other FLOSS video editors use Bezier based implementations, which in my opinion are inferior)
  * RGB Adjustment filter is equipped with a new and much more intuitive editor and renamed as **Color Adjustment**.

Unfortunately the first two require repository version of **MLT (=>0.9.1)** which is not available on any distributions yet (Arch may have it).

* **Spacer tool** makes it possible to move all timeline items on all the tracks as a single unit. If Control button is pressed all items on a single track can be moved. This makes it much quicker to restore relative positions of clips after edits that change positions between clips on different tracks.
* **Audio levels** displayed on clips are now rendered much quicker and some earlier bugs were fixed.
* **Range Log** functionality has been upgraded.
  * Range Log items can now be dragged onto Timeline
  * Timeline Clips can dragged to create Range Log items
  * Range Log items can be arranged into groups
  * ...and some other minor improvements and bug fixes
* **Quick Enter and Quick Exit for trim tools** make editing more fluid. When using Trim, Roll and Slip -tools the edit now begins immediately on click. The old behaviour can be restored by setting a preference.

#### Other features and enhancements

* Give info on a too long Fade for Clip
* Improve Transition handles and error info.
* Automatically create hidden folder for rendered clips
* Automatically create hidden folder for thumbnails
* Spanish translation
* Make possible use wipe luma files from file system
* Display media items as they are loaded
* Add all filters on/off button
* Add preference that sets last render directory as default on project open
* Add warning if Render Profile fps different from Project Profile fps
* Make track mute icons clickable for video/audio muting
* Enable dragging clip from monitor to Timeline
* CTRL + A support for media panel
* Make mouse middle click zoom to sequence length on Timeline
* Make Monitor playback interpolation user selectable
* Fix hidden blank after sequence end bug
* Fix render bug when minimizing windows
* Fix Audio Mixer crash on exit
* Fix 0.8 Project files forwards compatibility
* Fix Titler crash on exit
* Fix Filters editor delete out of index bug
* Fix Quick Transition alignment bug
* Fix Quick Transition undo bug
* Fix window panels resize bug
* Fix clip effects editor drag'n'drop bug
* **GUI updates:** Render time value display before estimated time - speaker icon change sensitivity state - clip rects back into trim overlays - trim overlays GUI update - Image Sequence indicator - Graphics indicator - Render Proxy File menu item - selected compositor color to blue - Timeline overlay update - rendered clip length display in slo-mo dialog - vcodec and acodec info in clip info - audio icon update - artistic filter icon update

---

## Flowblade 0.12

**Date: January 14, 2014**

**Flowblade 0.12** is the fourth release of Flowblade.

This release was about gradual improvements on features, correctness and stability. The new features in this release may not be useful to all users, but are very much needed by small subsets of users, and make the application useful for wider variety of editing needs.

The continued refactoring and improving of the code base has made it more clear that no major rewrites are needed, and Flowblade can be developed in a gradual and predictable way in the future.

### In this release

* **Slip tool** allows changing the media displayed in a clip in a single edit action without changing the position and length of the clip
* **Proxy editing workflow** can be used to edit material that makes the editing experience unacceptably unresponsive because the material places too high demands on the system
* **Batch rendering application** makes it possible to render multiple programs in the background
* **Dark Theme support** optimizes icons and GUI colours for dark themes
* **Copy Pasting clips** on the timeline is now possible

#### Other features and enhancements

* Watermarks
* Rendering stopping bugs fixed, incl Motion Clip render bug
* French and Czech translations
* Playback frame positioning bug fixed
* Icons and Tool cursors update
* Simplify Tool names
* Fix .mp4 files rendering bug
* Fix wrong FPS value in File properties window
* Change Theora render file extension to .ogv
* Fix Image Sequence import bug on some numbering styles
* Remove gnomevfs dependency
* Add indicator to timeline clip being edited in effects editor
* Make all thread GUI updates acquire gtk lock
* Fix SpinButtons value display bug
* Make Titler layer visibility togglable
* Make possible to turn off safe and overlay displays in Titler
* Make Titler window resizable
* Add entry box to give file extension when rendering with args
* Improve SVG handling
* Fix saving bug caused by MLT types SWIG names
* Fix Redo keyboard shortcut bug
* Fix Range Log comment editing bug

---

## Flowblade 0.10

**Date: September 13, 2013**

**Flowblade 0.10** is the third release of Flowblade.

This release has a lot of new features and enhancements. The development cycle was longer than the planned 6 months, mainly because of the summer break and a cascade of interconnected changes that all needed to be completed before doing a release.

In future we will hold strictly to a maximum 6 months between releases, and will opt to postpone features in favour of a more reliable release schedule.

### In this release

* **Tools** metaphor is used for editing instead of **Edit Modes** like before
* **Audio Mixer** window with VU meter + gain and pan controls for all tracks and master out (**Requires MLT 0.8.8**)
* **Affine Blend** compositor provides single point of control to create keyframed composites with both opacity and affine transform and all the standard blend modes (**Requires Frei0r 1.4**, which isn't widely in repos)
* **Image sequences** of numbered frames can be imported now as media
* **Preset rendering options** for commonly used file types are made available to the user
* **Range Log** panel enables user to save and name Mark In/Out ranges on media files. This is very useful when working with long files that have many areas of interest.
* **Marks** can now be placed to identify positions on the timeline.
* **Single track rendered transitions** for quick dissolves and wipes
* **Auto consolidate blanks**, no more multiple blanks between clips after some edits
* **GUI Look'n'Feel** was updated with over 20 new icons and new custom buttons

#### Other features and enhancements

* Updated application menu
* Configurable Tabs position
* Configurable Timecode display position
* Keyboard shortcuts list window
* "Centring" action for Compositor editors
* TAB key switches between Timeline/Clip display on monitor
* Keyboard shortcut CTRL+L for logging clip ranges
* Arrow keys move source image in Compositor editors
* Project events panel and persistent project events data
* 8 video/1 audio and 1 video/8 audio track layoutsn for sequences
* Media objects are now displayed using large thumbnails with information overlays
* Noise and EBUBars image producers
* Bin panel is now resizable
* Colgate white balance plugin
* Tracks menu
* Support for Copy/Paste in Title Editor
* Runtime environment data can be saved into a file
* Rename and Clip Color features added to Clip context menus
* Make cut action available when working with trim edit tools
* Image Grid filter
* Audio information for clip is displayed with level data instead of waveform
* Panel sizes are now persistent
* UP/DOWN arrows move position to In/Out Marks and clip ends on Clip Monitor display
* HOME/END keys move position to timeline start/end
* Sync Parent feature GUI update
* Timeline focus fixes to make keyboard shortcuts available better
* M keyboard shortcut for adding markers
* Sync frame offsets visible
* Display selected range on timeline frame widget
* Display selected range length for Clips under monitor

---

## Flowblade 0.8

**Date: December 4, 2012**

**Flowblade 0.8** is the second release of Flowblade, and the first one to take advantage of bug reports and feature requests from users.

Although a few important new features were added, much of the effort after **0.6** was spend creating new Frei0r plugins, total of 14 were contributed by the author, 10 of which are available in Flowblade **0.8**. Good new Fre0r plugins were contributed by other people too, so it may be worth while to install Frei0r from source code. See wiki: InstallingFrei0rPluginsFromSource.

### New Features

* Titler
* Slow/Fast motion clips
* Flowblade now runs on screens with height of 768 pixels
* Creating Sequences with different number of tracks is now possible
* Ability to change Track count of Sequence
* T, Y and U keyboard shortcuts for insert events
* J, K, L keyboard playback control
* Default length of Drag'N'Drop for graphics is configurable
* 18 new filters added (latest Frei0r needed)
* Environment information is made available to users

#### Major Bugfixes

* Localisation bug causing non-working compositors fixed
* Environment detection method changed to direct MLT for better results

---

## Flowblade 0.6

**Date: May 7, 2012**

Initial release.

### Features

* Film style insert/trim editing paradigm
* 2 move modes and 2 trim modes
* Image compositing with transformations, blend modes and pattern wipes
* Close to 100 image and audio filters
* Supports most common video and audio formats
* JPEG, PNG, BMP, TGA, TIFF, GIF images and SVG vector graphics
* Output encoding to multiple formats
