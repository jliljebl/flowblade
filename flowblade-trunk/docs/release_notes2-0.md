

Flowblade 2.0 comes with the largest changes to workflow and UX since the very first releases.

Editing workflow has been made much more configurable, new tools have been added and GUI comes with new theme, new top row layout and modernized design language.


Workflow 2.0

The "insert editing" approach to video editing taken by previous versions of Flowblade has had the down side of being found by many users to be somewhat unintuitive. On the other hand many users have found it to be clean and efficient.

Flowblade 2.0 solves this issue by presenting a configurable workflow that enables users to make the application confirm to their mental model of editing workflow.



Toolset Configuration
   * User can select between 1 - 9 tools to be availabe via tool menu and shortcut keys 1-9
   * User can set the order in which the tools preseted and which shortcut keys they get
   * The *default tool* is first tool in tool menu with shortcut key 1. This the tool that is activated when for example exiting trims, this is settable by setting tool order



Timeline Behaviours
   * Drag'n'Drop behaviour, user can select wheather insert or blank overwrites are done on track V1 and others
   * Composiors autofollow, users can make compositors follow their origin clips automatically



Workflow presets
   To get things going the user is given option too choose between two Workflow Preset options application start or at anytime later.


	Standard
	--------
	Standard workflow has the <b>Move</b> tool as default tool and presents a workflow similar to most video editors.

	Tools: Move, Multitrim, Spacer, Insert, Cut, Keyframe

	Behaviours:Drag'n'Drop: 'Always Overwrite Blanks', Compositors Autofollow: Off


	Film Style
	---------
	Film Style workflow has the Insert tool as default tool and employs insert style editing. This was the workflow in previous versions of the application.

	Tools:Insert, Move,Trim, Roll, Slip,Spacer, Box

	Behaviours: Drag'n'Drop: 'Overwrite blanks on non-V1 tracks', Compositors Autofollow: Off



New Tools

Four new tools have been added to selection of tools that user has available when deciding on their preferred toolset.
    Keyframe tool enables eediting Volume and Brightness keyframes on the timeline with overlay curves editor.
    Multitrim tool combines Trim, Roll and Slip tool into a single tool that comminicates the available edit action with contaxt sensitive cursor changes.
    Cut Tool allow performing cuts with tool in addition to earlier method of cut action at playhead.
    Ripple Trim tool was earlier available as a mode of Trim tool but it is now a saparate tool.


Tools changes
    Overwrite Tool's name was changed to Move and it was made the default Tool inthe "Standard" workflow preset. New Move tool also has box selection and box move available as additional edit actions if user does a box selection starting from pressing on empty spot on timeline.






GUI updates

We made quite a few updates and changes to the user interface to clean up and modernize the design.

New Custom Theme was created and made the default theme for the application. It has become clear that video editors are the kinfd of applications that work best with a custom made dark theme and now that GTK3 has finally stabilized the theme CSS creating and maintaining a custom theme is now possible.

Earlier panel design with quite large buttons has been updated with a design employing more context and hamburger menus, and by making almost all toplevel item icons.

For systems with larger screen dimension the default top row layout has been changed to a 3 panel design instead of the earlier 2 panel design, earlier layout still being available as preference item.

    Tooltips coverage was extended largely and almost all top level items have individual tooltips, including all the middlebar buttons that had single tooltip for a group of buttons, mostly for texhical reasons.

Insert and Move(earlier Ovewrite) tools have new cursors.





Keyframe editing updates

In addition to new Keyframe tool many updates were made to keyframe editing.

    Slider to Keyframe editor functionality. Majority of filter parameters that earlier only had a slider editor available for setting a single unchanging value can now be eddited with a keyframe editor. There is a new keyframe icon in slider editors that turns slider editor into a keyframe editor when pressed. Kyrame editor can also be turned into back into a slider editor.


    Keyframe editors now have buttons that move keyframes 1 frame forward or backwards.

    Keyframe editor out-of-clip-range keyframes now have info on on them displayed and there are editing actions available for deleting and setting their values.

    Keyframe editors are also now updated on all mouse events making it more intuitive to know the value of a parameter in all keyframes.


    Compositor geometry editors now have numerical inputs making some more precise


    Shift + Arrow keys now change scale in Compositor geometry editors.



Compositors
    Add Transform compositor
    Add Alpha Combine Compositors


Edit
    Add Ripple delete Button, multitrack ripple 
    No more changing to default edit mode on media drop
    Make Shift + X cut all tracks on Playhead. (mutta toolissa on Control !?!)


Contributions
    Sequence Split functionality. It is now possible to split Sequence at playhead position to create a new Sequence from timeline contents after playhead, by Bene81
    Fix GTK version detection logic inversion problem, Issue #521 by Bene81
    Reducing video track count damages project Issue #486, fixed by Eliot Blennerhassett
    Change tracks dialog now gets current sequence track counts, not hard coded values by Eliot Blennerhassett
    Archlinux docs fix, depends sdl_image by Bernhard Landauer
    Make Flowblade exit cleanly if audio waveform rendering is still on,by Steven van de Beek,

    Peter Eszlari
	    Add appdata file used by e.g. GNOME Software or KDE Discover  Peter Eszlari <peter.eszlari@gmail.com>
	    Change icon path in setup.py to comply freedesktop spec, need for Flatpak
	    Fix mimetype data to be consistant.


Translations
    Update Czech translations by Pavel Fic and p-bo
    Add russian documentation translation an russian translation
    Polish translation....

Refactoring
    Refactor modes setting code from module editevent.py to modesetting.py
    Refactor and rename <X>Screen editors from module keyframeeditor.py to keyframeeditcanvas.py. 
    Remove unused imports using pyflakes.

Smaller fixes and features
    Add prefeference to not move to clip start on keyframe edit init
    Keep filter editors open on most edits #537
    More height for Compositor geometry editors on larger screens.
    Make clip editor next/prev buttons stay in edit range.
    768px height and some other screen sizes fixes can now full screen properly.
    fix track locking for multiple tools.
    Fix recent files bug.
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

