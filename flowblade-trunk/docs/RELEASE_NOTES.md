# Release Notes #

## Flowblade 2.2 ##

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
* Don't match profiles with more then 2x size diffence to media even if fps matches, Issue #517
* Fix keyframe delete not registering when done as last edit

## Flowblade 2.0

Date: February 4, 2019

**Flowblade 2.0** comes with the largest changes to workflow and UX since the very first releases.

Timeline editing workflow has been made much more configurable, new tools have been added and GUI comes with a new custom theme (for Gtk+ versions >= 3.22), new top row layout and modernized design language.


### Workflow 2.0 ###

The *insert editing* approach to video editing taken by previous versions of Flowblade has had the down side of being found by some users to be somewhat unintuitive. On the other hand many users have found it to be clean and efficient.

Flowblade 2.0 solves this issue by presenting a configurable workflow that enables users to make the application better confirm to their mental model of editing workflow.



#### Toolset Configuration
   * User can select between 1 - 9 tools to be availabe via tool menu and shortcut keys 1-9
   * User can set the order in which the tools presented and which shortcut keys they get.
   * The *default tool* is the first tool in the tool menu with shortcut key **1**. This is the tool that is activated when for example exiting trims, this is settable by selecting the tool order



#### Configurable Timeline Behaviours
   * Drag'n'Drop behaviour, user can select wheather insert or blank overwrites are done on track V1 and others
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

Insert and Move (earlier Ovewrite) tools have new cursors.


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

Change icon path in setup.py to comply freedesktop with spec, fix mimetype data to be consistant, by **Peter Eszlari**.

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


## Flowblade 1.16 ##

Date: March 31, 2018

**Flowblade 1.16** is the sixteenth release of Flowblade. This cycle we mostly had improvements, refinements and bug fixes building on existing features. A lot of time was spend on developing new video display code, but we didn't get any results there yet. Work on that front will continue, we have some issues that need to resolved eventually and the currently used technology is slowly on its way out.

### Tool cursor timeline sensitivity ### 

This is the biggest user visible change. Previously tool cursors didn't react in any way to the timeline contents, now they change appearence on appropriate positions to signal that some different edit actions are available.

  * With **Insert tool** and **Overwite tool** the cursor now changes on clip and Compositor ends to indicate that the user can drag the ends to lengthen or shorten the clips or Compositors. On top of Compositors cursor changes to indicate that Compositor can be dragged to a new position.
  * **Trim tool** now changes appearance to indicate which end of clip will be trimmed if Mouse Left is pressed and held.
  * **Box tool** now changes when entering selected box to indicate that box contents can be dragged sideways.

This feature was so far avoided by design based on the fact that it requires quite precise mouse positioning to initiate desired edits and larger target areas are easier and quicker to hit.

However, it has become clear that users prefer context sensitive tool cursors, the main evidence being that almost every other edit program has them, so this was now added to Flowblade. This will probably help beginner users more easily to get going with Flowblade.

The feature in on by default, but can be disabled to return to previous behaviour.

### Tool cursors GUI update ###
Tool cursors appearance got an update as part of the timeline sensitivity work. The biggest change was to Overwrite tool cursor, it is now otherwise the same as the Insert cursor, except that it is red.

### Compositor auto follow ###
It is now possible to set Compositors to automatically to follow their origin clips as clips are moved or trimmed. It is possible to set individual clips to remain manually editable even if auto follow is set on. This feature can flexibly offer good sides of both clip embedded Compositors and free flowing Compositors.

This mode is off by default and needs to activated from track popup menu.

### Re-rendering rendered transitions ###
Rendered transitions can now be re-rendered e.g. when the clips that were used to render the transition have had new filters added. 

It is also possible to batch re-render all rendered transitions. This is useful e.g. after leaving proxy mode before doing final render as in proxymode rendered transitions are rendered from proxy clips, and therefore are of worse quality then rendered transitions created from original media.

### Clip markers ###
Users can now add markers to clips, before markers could only be added to timeline positions.

### Some notable updates ###
**Luma Wipe** can now be made to run in reverse directions, earlier it could only be made alpha inverted.

**A 'Playback' panel** was added to Preferences dialog keep item count per panel low enough for quick discovery.

**G'MIC Effects tool** now works with G'MIC version 2.

**Timewarp producer** is used if available to **have sound on forward slow/fast motion clips.**

**Compositors and Effects** can now save and load their parameter values.

### Flatpak ###
Github user *eszlari* created a Flowblade 1.14 Flatpak which is already available on Flathub. Version 1.16 is coming there too in the coming weeks. We will post info on Google+ on that when it is done.

### Contributions ###

*atomicfile.py* module was added by *Nathan Rosenquist* to make saving data more robust.

Николай Смольянинов provided a series of reports on missing translations strings, the coverage should now be close to 100%.

### Future directions ###
The focus areas of next release will be animations, masks and compositing. So far the focus has squarly been on Flowblade as an editing tool, but now we will look for ways to expand application's feature set in this direction.

There are a number of approaches that can be tried here, and it is difficult beforehand to predict which will work out, so we will basically try everything and see how things turn out. The translations workflow update will definately come too.

We will keep the 6 month release cycle, so next release will be sometime in the autumn.


### Other bugfixes and improvements ###

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
  
## Flowblade 1.14 ##

Date: October 4, 2017

**Flowblade 1.14** is the fifteenth release of Flowblade. This release had probably more new features then any release  since the initial release 0.6. New functionality like sequence combining, compound clips and audio syncing take the application to the next level as a complete editing solution.

Especially sequence combining feature together with existing features like *Range Log* make Flowblade easily the most advanced and featureful FLOSS tool for projects with long complex edits and large amounts of media.

Improved user feedback has also made possible to refine many areas of functionality beoynd original design. 

### Audio Syncing ###

Python module *clapperless.py* by *Martin Schitter* and *Benjamin M. Schwartz* has made it possible to offer functionality that syncs media items based on their audio data. We have two new features offering Audio Syncing functionality.

  * **Timeline Audio Syncing** Now you can select  two clips on timeline and request one of them to be moved so that clips' audio is synced on timeline. This makes it possible to do multicamera editing on timeline, one needs to manually set video mute on/off on tracks to see all tracks, but the workflow is possible now.

* **Audio Synced Compound Clips** User can select a video and audio clip and create an audio synced compound clip media item from them. This is useful e.g. when audio is recorded separately and video clip only has some help audio.

### Combining Sequences ###

It is possible to import full contents of another Sequence into the Sequence currently being edited. There are two ways provided to combine sequences:
  * Imported sequence can be **appended at the end of current sequence**.
  * Imported sequence can be **spliced in at the playhead position**.

This long overdue feature will make having multiple sequences per project a much more useful and flexible tool when building complex programs from smaller parts.

### Compound Clips ###

A **Compound Clip** is a single clip created by combining multiple clips and compositors in to a single media item. Compound Clips are useful when some complex sequence is more conveniently handled as a single unit.
  * **Compound Clip from Selection** feature creates a Compound Clip from currently selected clips into a Compound Clip.
  * **Compound Clip from Sequence** feature creates a Compound Clip from current full contents of the timeline.
  * **Audio Synced Compound Clip**, see above.
  
### Fade in/out ###
We have two new features addressing user requests for speeding up the process of creating fade in and fade out transitions.
  * **Fade Compositors** These are special new compositors that will automatically on creation place themselves at the beginning or end of clips and do not need any keyframe manipulation; lengths of fades are changed by changing the lengths of compositors.
  * **Add Fade buttons** *Compositors* panel now has **Add Fade In** and **Add Fade Out** buttons that will create keyframes that define a fade of desired length in a single click.

### User Selectable Keyboard shortcuts ###

**Steven van de Beek** contributed code that makes it possible to have user defined keyboard shortcuts. In this release we offer a possibility to select between two predefined sets of shortcuts, and fully configurable keyboard shortcuts will be made available in the future.

### Tools development ###

#### Reverse clips tool ####
We now offer a new tool to create reverse clips of user selectable speed from media items.

#### Titler ####

Titler got two new features:

  * Text drop shadow 
  * Text outline

#### Disk cache management ####
Disk cache management window provides GUI tool for deleting saved hidden files that could eventually consume noticable amounts of disk space.

### Translations ###

We got a new new Cantonese translation by 老吴的BOX.

We got fully up to date translations for 1.14 in Russian, Polish and Czezh by Николай Смольянинов, Stanisław Polak and Pavel Fric respectively.

### Future directions ###

During next cycle work continues roughly as outlined in road map and Issues list at Github. 

Translations workflow update is definately in the plans. The current workflow is difficult and outdated when there are several web solutions that are likely preferable to all translations contributors.

Next cycle will also see move to spending more development time on some upstream issues that can take a bit of time to come through as available features in the application, expecially on installationss from distro repositories.

We will probably continue with the 6 month release cycle, but a shorter one is possible if certain planned improvements come together quickly enough.

### Other new Features ###
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

### Feature Removals ###
  * Dropped **Zoom Pan filter** because it does not work on all files.

### Other bugfixes and improvements ###
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

## Flowblade 1.12 ##

Date: March 18, 2017

**Flowblade 1.12** is the fourteenth release of Flowblade.

In this cycle the main developments were the adding of new tools for the first time since 0.14, and the increased level contributions the project received.

Much time was spend on creating an AppImage for the project but unfortunately no satisfactory end result was reached, so there will not be an AppImage with latest dependencies available for Flowblade yet.

Even with this and some redesign related delays we were able to advance the project at a reasonably pace.

### Box tool ###

New Box tool is provided to help with the use case of moving a range containing media on multiple tracks to another point in the sequence. This has previously required multiple edit steps to achieve. The Box tool will reduce the number of required edit actions.

The main intended use case is probably best explained with a video: https://vimeo.com/207310517

### Trim tool Ripple mode ###

Every use of Trim tool will cause the edited track to lose sync with other tracks after the trim point. The Ripple mode enables in most cases doing trims while maintaining sync with other tracks. Some points on Trim Ripple mode:
- Sync is maintained by changing the lengths of the closest blanks on other tracks. This might not produce the edit you wish to achieve, in that case you will need to use Trim tool in default mode and do the edit in multiple steps.
- No overwrites are allowed to happen so the available trim length is constrained by blank lengths on other tracks.
- This tool is not provided as a separate tool and it is not given a GUI top level representation because it became clear that the resulting multitrack edit can be found confusing by many users
- The tool can be accessed by toggling the Trim tool mode using 'R' key when timeline has keyboard focus.


### Contributions ###

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



### AVFilters ###
MLT 6.2.0 added AVFilters support. Flowblade now offers additional filters if you have MLT > 6.2.0 with AVFilters module installed.
- *Lut3D* This makes possible to add similar film emulation filters that are available in G'Mic by using **.cube** files. 
- *Zoom/Pan* Similar functionality current "Affine" filter but the performance is much better
- *Color Channels Mixer* This makes possible to use color data of one chanel to determine color output of another channel. Basic exmple would be making green shirt blue by using green color data to display blue color.
- *Perspective* Strech image in way that can enable changing perspective.
- *Lens correction AV* Filter that corrects typical lens errors.


### Translations ###

We got a new Russian translation by Nikolai Smoljaninov. There are over 100 million Russian spekers in the world and most use localised applications, so this widens the potential user base  in a big way.

Hungarian and German translations got updates by Péter Gábor and Mario Dejanovic.

### Future directions ###
*Move to 2 releases per year instead of 3.* The release overhead and assosiated project slowdown has been getting bigger lately and with container formats possibly added to release requirements it is better to make the development cycles a bit longer to get overall better development throughput. 

*Container formats and Wayland support* These technologies are still being developed and adopted. Solutions here are worked on will be made available when ready.

*Focus areas for next cycle include* continued work on Issue list and Roadmap, Clip Compositors that automatically follow clips even across tracks will be attempted, tool integration hopefully gets a bit of attention, small website update and more tutorial videos will be done.

### Other bugfixes and improvements ###
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

## Flowblade 1.10 ##

Date: December 13, 2016

**Flowblade 1.10** is the thirteenth release of Flowblade.

This cycle was a nice change in the sense that not much time was needed on project structural issues such as porting to GTK3 or creating a website.

The main feature in this release is the new Trim View, with the additional features being focused on editing and some GUI updates.

Next release cycle will focus on improved tool integration with the goal of providing more convenient and efficient ways to manipulate and create media within Flowblade in concert with other existing FLOSS tools. Some new editing tools and options will also be worked on, as well as bug fixes and feature requests in the Issues list.

Appimage for this will release will become available in January and for all subsequent releases it will be available at release date.

### Trim View ###

Trim View is feature available in most commercial packages and now also in Flowblade, probably as the first FLOSS video editor. It is maybe best described just by a [screenshot.](https://raw.githubusercontent.com/jliljebl/flowblade/master/flowblade-trunk/docs/1-10_trimview.jpg). The advantages are clear: user is provided with more information when doing a trim and is thus able to better assess the correct cut frame within a single edit action.

Points on Trim View performance
- for "Trim" tool the trim tool should mostly work quite well
- for "Roll" and "Slip" tools there is no getting around the fact that two video streams need to be displayed in real time. The following performance considerations apply:
    - SSDs perform better the spinning hard disks
    - faster processors improve playback
    - video streams like image sequences consisting fully of I-frames perform better than streams with a lot of B- and P-frames

For these reasons the **Trim View is off by default and needs to activated from menu below the monitor**. Users are advised to assess for themselves if performance is satisfactory for system and media they are working on

### Frame Matching ###

Trim view layout also addresses a fundamental restriction of a single monitor layout: user is unable to compare video material to other material when deciding on a clip to add to a sequence. We now provide two mechanisms to help with this use case:
- monitor frame matching, shown [here.](https://raw.githubusercontent.com/jliljebl/flowblade/master/flowblade-trunk/docs/1-10_monitor_match_frame.jpg)
- timeline frame matching, shown [here.](https://raw.githubusercontent.com/jliljebl/flowblade/master/flowblade-trunk/docs/1-10-timeline_match_frame.jpg)

### Editing Improvements ###

- a "Delete Range" button is now provided to cut and lift material inside selected range on all tracks
- Filters in filter stack can now be rearranged
- Spacer tool got some bug fixes improving its usabily
- User can now select all clips before or after a clip on timeline using a popup menu option.


### xport from timeline to tools ###
- timeline clips can be now exported with frame range preserved to G'MIX Effects Tool, Slow/Fast Motion renderer and Natron if it is installed in the system.

### Dual monitor and small screens improvements ###
- dual monitor support has been improved by providing a to window layout shown [here.](https://raw.githubusercontent.com/jliljebl/flowblade/master/flowblade-trunk/docs/1-10_dual_monitor.jpg)
- small screen sizes support has been updated with multiple bug fixes and feature additions.

### GUI updates ###
- Monitor area layout was updated with the main goal of providing clearer visual cues wheather Timeline or Clip is displayed in the monitor by making the selection buttons much bigger.
- Middlebar got some minor visual updates

### German translation update ###
- German translation received an update from Mario Dejanovic.

### Other bugfixes and improvements ###
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


## Flowblade 1.8 ##

**Date: September 19, 2016**

**Flowblade 1.8** is the twelth release of Flowblade. 

During this cycle a lot of time was spend on creating a website for the project and on bringing a node compositor tool to Flowblade. Website was succesfully deployed, but the node compositor tool was dropped in final stages of development.

The node compositor was dropped when I realized that it does not serve any user group particularly well.

Casual users will find difficult to use node compositors effectively as any non-trivial composition requires creating complex node graphs. On the other hand adcanced users already have alternative FLOSS solutions like Natron and Blender available, and are unlikely to adopt this tool in meaningful numbers.

Once it became clear that it would require postponing this release quite a bit to do the remaining bugfixing and creating documentation, I decided that the project is best served by allocating resources to other areas of development.

We did get some good stuff in, and with the next cycle we can hopefully get moving with improved speed of feature development.

Particular attention will given to the current *Issues* list, with some of the other focus areas being improving integration between tools and timeline, and an attempt to make nested clips available.

### Flowblade Main Features ###

* **Keybord trimming with arrow keys** Trim positions can now be moved using arrow keys and trim edit confirmed with pressing Enter key. This is often more convenient and precise then always working with a mouse
* **Clip Snapping** Clips and compositors will now snap to clip ends on adjacent tracks when clips or compositors are moved or their ends dragged. 
* **Clips display media thumbnails** This helps differentiating clips from each other on timeline.
* **EDL export** is now available. Thanks to Github user *tin2tin* for extensive testing on software not available on my system. Unfortunately it became clear that Blender EDL import is buggy.

### G'MIC Film Emulation Filters ###

G'MIC Effects tool got an important capability update with the addition of film emulation filters.

G'MIC Film Emulation Filters change the tones and gamma of the image to resemble different film stocks. Where as other color correction filters available in Flowblade work with luma or R,G,B LUTs, film emulation filters employ much bigger LUTs which are applied to the 3D color space of the image, and can achieve more detailed changes. 

The results have been quite nice during testing; it is often possible to achive subtle effects that greatly improve the look of the material.


### Contributions ###

In this cycle we got the largest amount of contributions per cycle so far.

* **Hungarian translation** was provided by Péter Gábor. These take a big amount work and we're always happy to receive a new one.
* **Play/pause toggle with single button** functionality was provided by Github user *dvdlvr*. This has been asked before so a portion of users probably likes it better like. The new behaviour needs to be activated from *Preferences*
* **Titler remembers last save directory** patch by Martin Mois. Before the user needed to always navigate away from the default folder when saving titles.
* **New anti-aliased the monitor control icons and modified the clear marks icon** by Github user *bergamote* improve visuals on that part of the GUI.


###  Bugfixes and enhancements ###
* "Change Project" functionality fixed, and works much better now 
* If first loaded media does not match current project profile, user is informed and given option to switch to matching profile.
* Fix assoc file launch from e.g. Nautilus
* Improve missing rendered transition media overlap info
* Compositors can now move by dragging from middle too, not just edges
* Do gi.require() for Gtk and PangoCairo to silence warnings and specify Gtk+ 3
* Make MLT version detection work for two digit version number parts
* Fix adding media while in proxy mode
* Check and give info on IO errors when saving in main app and relinker
* Add keyboard shorcut 'R' for resyncing selected clip or compositor
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



## Flowblade 1.6 ##

**Date: March 2, 2016**

**Flowblade 1.6** is the eleventh release of Flowblade. The main feature of this release is the new G'MIC Effects tool.

### G'MIC effects tool ###

G'MIC is a full-featured open-source framework for image processing developed by french research scientist David Tschumperlé and others. Its main strength is that it enables creating complex new image filters without writing any compiled code.

For applications such as Flowblade this makes it possible to offer a wide range of image filtering capabilities using a relatively small amount of managed code.

A [demo video](https://vimeo.com/157364651) of some features available in the first release is available at Vimeo. This is just the first step, many more filters will come in the future.

### Other main features in this release ###

* **Changing project profile is now possible.** This is a feature that was requested by users who felt uneasy about having to commit to a profile at the beginning of the project.

* **Drag'n'drop of media files from other applications** is a standard feature that has so far been missing from Flowblade.
 
* **Middlebar was updated** on wider screens as G'MIC, Batch Render Queue and Split Audio buttons were added.

* **'Sync All Compositors' functionality was added** This can be very useful in situations where a track as a whole is moved in relation to other media.

For the next release cycle the focus will be on integrating existing technologies to improve Flowblade's capabilites in doing motion graphics. The Natron compositor project offers a lot of promise here, and the exisiting node compositor by myself will be made available in some form.

Also a project website will be developed during this cycle. The first version is to be made available in a week or two.

The next cycle will be the longest since 0.16 because of the amount of coding and research needed. The target release date for 1.8 is September 2016.

#### Bugfixes and enhancements ####
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
* Fix filter cloning for filters witn non-mlt properties
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


## Flowblade 1.4 ##

**Date: November 24, 2015**

**Flowblade 1.4** is the tenth release of Flowblade and the first release after the GTK3 port.

Most main features in this release are changes to editing model that were designed to make editing more approachable and quicker. It is also notable that a large part of the main features were based on user requests, a first for the project.

In the next release cycle features that will be attempted include a G'MIC effects scripting tool, a node compositor tool using an existing code base, a first launch tips window for new users, and a clip snapping feature.

In 2016 there will probably be 3-4 releases, and the next release 1.6 is targeted for March. There will be some reports on progress in the Flowblade Google+ group.

### Main Features in this release ###

* **Fade/Transition cover delete feature was added.** Selecting a single rendered fade/transition clip and pressing delete will cause the deleted area to be covered using material from adjacent clips if such material is available. This makes working with single track transitions/fades faster. Previous behaviour can be restored using a preference option.

* **Clip ends drag with Control + Right mouse.** When a move tool - <i>Insert, Overwrite or Spacer</i> - is selected clip's ends can now be dragged to change clip's length. This is useful when for example a clip in a multitrack composition needs to be made longer to cover a clip on a track below. Clips end drags perform overwrite on empty/blank regions and insert on media regions of timeline.

* **Drag'n'drop overwrite action on non-V1 tracks** has been added. Dropping clip on track V1 works like before, but on non-V1 tracks:
  * clip will be inserted if dropped on a clip 
  * clip will overwrite available blank and empty space and will perform insert for the length of media frames that would be overwritten.
 
 This makes creating multitrack compositions faster. Previous drag'n'drop behaviour can be restored using a preference option.

* **Always on audio levels display** functionality was added. Before the audio levels could only be displayd on request, but now it possible to have audio levels rendered on background and displayed as soon as they are available 

* **Filters can now be copy/pasted from one clip to another**. It has been possible to copy paste clips on timeline for quite a while, but now this feature was made more discovarable by adding menu items for the functionality.  


#### Other features and enhancements ####
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


## Flowblade 1.2 ##
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

#### Other bug fixes and enhancements ####

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
    
## Flowblade 1.0 ##
**Date: June 15, 2015**

**Flowblade 1.0** is the eighth release of Flowblade. It turns out that you *can* write a video editor with those Python bindings to MLT.

This release focused almost entirely on bugfixes to ensure maximum quality of existing features for 1.0 release. This was probably a good decision as quite a few bugs were found and fixed.

Quite a bit of time was spend moving the project from Google Code project hosting to Github. After a short time here it's quite clear that Github is a superior platform, so it was all for the better.

Next release cycle will be devoted to the GTK3 port. Hopefully everything goes according to plan, and we can get back to adding new exiting features to the application.

#### Bug fixes and enhancements ####
  * Make range item delete work logically
  * Fix Range log group functionality
  * Media files pop-ups only display usable items for media type
  * Fix Media Relinker to work with image sequences correctly
  * Make backup snapshot have .flb ext no matter what user enters
  * Fix snapshot saving for image sequences
  * Add missing image sequence proxy render functionality
  * Fix snapshot relative paths lookup for image sequences
  * Update project event time display text
  *  New fallback thumbnail icon
  * Fix MLT version comparison 
  * Brightness Keyframed bug fixed
  * Moved help files from Google Code to HTML resource files
  * Remove panel frame shadows for cleaner look


## Flowblade 0.18 ##
**Date: March 19, 2015**

**Flowblade 0.18** is the seventh release of Flowblade and the last one before 1.0.

Features in this release concentrated on media management, as that was thought to be the last under developed area that needed to be addressed before 1.0.

This cycle was a bit difficult as considerable work was done on features that were then abandoned because satisfactory functionality could not be achieved at this time. Also, the features that were released went through a redesign forcing a full  code rewrite and the quick and easy release cycle turned into major undertaking.

Through all this it became clear that the time for Gtk3 port is now. Next release will be 1.0 and only bug fixes and some minor editing work flow features will be added. 1.0 will also be the last Gtk2 release of Flowblade.

### Main Features in this release ###
  * **Relative paths for media assets** are now supported. If media file is not found using the saved absolute path, a file with same name is searched from subfolders relative to project file directory.
  * **Save backup Snapshot** functionality saves project file and all media used by project in selected folder for convenient backup.
  * **Media Relinker** tool makes replacing missing media files easy.
  * **Image Sequence Rendering** for exporting project as a file sequence is now available.

#### Other features and enhancements ####
  * Current Frame export
  * Fix Batch render track mute bug
  * Color Pulse and Ising pattern producers added
  * Fix Titler closing and saving bugs
  * Color Lift Gain Gamma filter added

---

## Flowblade 0.16 ##
**Date: December 2, 2014**

**Flowblade 0.16** is the sixth release of Flowblade.

This release has only one major new feature, and marks a change in the approach until the 1.0 release is done.

The next 2-3 releases will contain at most 1 new major feature along with smaller enhancements and bug fixes. The releases will also come quicker, once every 3-4 months.

The previous release completed the editing concept and feature list needed for 1.0. The 1.0 release will be made before the end of 2015, after which the focus will shift immediately to the porting of the application to gtk3.

The code base refactoring has come to a conclusion with this release, and the focus when improving code readability will now shift to adding and improving comments.

### Main Features in this release ###
  * **Audio Master Meter** has been added to top level GUI to help working with audio.
  * New **Chroma Key** filter works better on blue and green screen keying than the existing Color Select filter
  * **Luma Key** enables keying based on image luma values
  * **Batch Rendering** was changed to use dbus instead of PID files and should now  actually work

#### Other features and enhancements ####
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
  * View selector for media panel to display all or anly certain types of files
  * Add info on duplicate media items on load
  * Refactor and fix audio monitoring display update and exit

---

## Flowblade 0.14 ##
**Date: June 18, 2014**

**Flowblade 0.14** is the fifth release of Flowblade.

This release has some good new features and improvements, see below for more info. It also seems clear that the "release every 6 months" schedule suits the project well at this stage, and it will be kept for the future.

In the next release cycle attention  will be paid to rendering output files and media and project management.

New features for the next release have not been decided on yet, but MLT webFX module will be looked at, and there are some other services available that are not yet utilized by Flowblade.

### Main Features in this release ###
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

#### Other features and enhancements ####
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

## Flowblade 0.12 ##
**Date: January 14, 2014**

**Flowblade 0.12** is the fourth release of Flowblade.

This release was about gradual improvements on features, correctness and stability. The new features in this release may not be useful to all users, but are very much needed by small subsets of users, and make the application useful for wider variety of editing needs.

The continued refactoring and improving of the code base has made it more clear that no major rewrites are needed, and Flowblade can be developed in a gradual and predictable way in the future.

### In this release ###
  * **Slip tool** allows changing the media displayed in a clip in a single edit action without changing the position and length of the clip
  * **Proxy editing workflow** can be used to edit material that makes the editing experience unacceptably unresponsive because the material places too high demands on the system
  * **Batch rendering application** makes it possible to render multiple programs in the background
  * **Dark Theme support** optimizes icons and GUI colours for dark themes
  * **Copy Pasting clips** on the timeline is now possible

#### Other features and enhancements ####
  * Watermarks
  * Rendering stopping bugs fixed, incl Motion Clip render bug
  * French and Czech translations
  * Playback frame positioning bug fixed
  * Icons and Tool cursors update
  * Simplify Tool names
  * Fix .mp4 files rendering bug
  * Fix wrong FPS value in File properties window
  * Change Theora rende file extension to .ogv
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

## Flowblade 0.10 ##
**Date: September 13, 2013**

**Flowblade 0.10** is the third release of Flowblade.

This release has a lot of new features and enhancements. The development cycle was longer than the planned 6 months, mainly because of the summer break and a cascade of interconnected changes that all needed to be completed before doing a release.

In future we will hold strictly to a maximum 6 months between releases, and will opt to postpone features in favour of a more reliable release schedule.

### In this release ###
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

#### Other features and enhancements ####
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

## Flowblade 0.8 ##
**Date: December 4, 2012**

**Flowblade 0.8** is the second release of Flowblade, and the first one to take advantage of bug reports and feature requests from users.

Although a few important new features were added, much of the effort after **0.6** was spend creating new Frei0r plugins, total of 14 were contributed by the author, 10 of which are available in Flowblade **0.8**. Good new Fre0r plugins were contributed by other people too, so it may be worth while to install Frei0r from source code. See wiki: InstallingFrei0rPluginsFromSource.

### New Features ###

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

#### Major Bugfixes ####
  * Localisation bug causing non-working compositors fixed
  * Environment detection method changed to direct MLT for better results

---

## Flowblade 0.6 ##
**Date: May 7, 2012**

Initial release.

### Features ###
  * Film style insert/trim editing paradigm
  * 2 move modes and 2 trim modes
  * Image compositing with transformations, blend modes and pattern wipes
  * Close to 100 image and audio filters
  * Supports most common video and audio formats
  * JPEG, PNG, BMP, TGA, TIFF, GIF images and SVG vector graphics
  * Output encoding to multiple formats
