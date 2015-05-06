**Flowblade Movie Editor Reference Guide**


![http://sites.google.com/site/phantom2dsite/Home/flowblade.png](http://sites.google.com/site/phantom2dsite/Home/flowblade.png)

**Updated last 17.6.2014 for version 0.14**




---

# Introduction #

Flowblade Movie Editor is a **multitrack non-linear video editor** for Linux.

With Flowblade Movie Editor you can compose movies from video clips, audio clips and graphics files. Clips can be cut at the desired frames, filters can be added to clips, and you can create multilayer composite images using compositor objects.

In Flowblade  clips are usually automatically placed tightly after the previous clip - or between two existing clips - when they
are inserted on the timeline. Edits are fine tuned by trimming in and out points of clips, or by cutting and deleting parts of clips.



![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---

# Basic Editing #

This section describes the minimal workflow for making a movie using only a single track. Full editing workflow is described in detail in the later sections.


## Creating a New Project ##
  * Menu: Select **File -> New** from menu.
  * Keyboard Shortcut: Press **Control+N**.

Flowblade Movie Editor saves work in project files.
A project contains one or more Sequences of edited media and a collection of Media Files stored in Bins.

There are two parameters that can be selected for a new project:

  1. **Project Profile** Project Profile determines frame rate per second, image size in pixels and pixel aspect ratio.
  1. **Tracks count** Select the number of video and audio tracks that are used in the project. This can be changed later, but the operation destroys the Undo / Redo stack and all the Timeline Clips that do not fit in the newly created version of the Sequence.

Video material is internally scaled to profile dimensions, so selecting Project Profile with smaller pixel dimensions than the rendered output leads to decreased quality.

Flowblade Movie Editor handles image data internally as YUV420 frames, so the encoding associated with a given profile has no affect on quality before rendering.

For **best possible quality** the **input material, Project Profile and Rendering Profile** should **all have the same pixel dimensions** and pixel aspect ratio**.**

## Adding and removing new Sequences ##
A Project contains one or more Sequences. Use **Add** and **Delete** buttons in the **Project** tab **Sequences** panel. All Sequences use the same Profile.

When creating a new Sequence, you can choose the number of Tracks in the Sequence. This can be changed later, but the operation destroys the Undo / Redo stack and all the Timeline Clips that do not fit in the newly created version of the Sequence.


## Working with Media Files ##

Flowblade Movie Editor holds files in **Media** tab. Files are listed in unnamed table that displays contents of the currently selected Bin. Bins are listed in the **Bins** table.

**Opening Media Files**
  * Press **Add** button above the unnamed Bin contents table in the **Media** tab.
  * Use dialog to find and select files.
  * Files are displayed in untitled contents table with thumbnails.
  * Note that creating thumbnails for many simultaneously opened files will take some time.


## Project Media: Absolute and relative paths ##



  * Flowblade **saves references** to media files used in a project as **absolute paths**.
  * If a media is **not found on load**, Flowblade attempts to find a media file **with the same name in subfolders relative to project file.**
  * **If all media used by a project is saved in subfolders** relative to project file, **project file and media can moved as a unit** and the project will load successfully after data is copied to a different place
  * **Rendered files** like transitions **are saved by default in a hidden folder**. Render target folder needs to be set in a project files subfolder when working if these are desired to be movable also.
  * Menu item **File->Save Backup Snapshot...** saves project file, all media and rendered files in a single folder that can saved as unit and and project can always be loaded using this data
  * **Load order** between absolute and relative paths can be set in preferences window
  * **Media Relinker** tool can be used to fix problems that may occur

_**NOTE:** Information given here only applies to version 0.18 and above._

## Working with Bins ##
**Adding a Bin**: Press **Add** button above Bins table.

**Deleting a Bin**: Press **Delete** button in above Bins table.
Bin must be empty before removing. A project must always have at least one Bin.

**Renaming a Bin**: Double click on the Bin name.

**Moving files to another Bin**: Select one or more files in the unnamed table. While holding down the **Left mouse** button after last selection drag files on
top of a Bin in the Bins table.


## Using Timeline ##

**Scrolling Timeline**:
  * Press and Drag **Scrollbar** below Timeline
  * Scroll **Mouse Middle** button + **CTRL** key while on top of Timeline

**Zooming Timeline**:
  * Click **Zoom In**, **Zoom Out** or **Zoom Length** buttons.
  * Scroll **Mouse Middle** button on top of Timeline

**Changing Current Frame**:
  * Drag with **Right Mouse** button starting from  an empty space in the Timeline.
  * Drag with **Left Mouse** button on the Frame Scale.
  * Drag with **Left Mouse** on the Monitor Position Bar.
  * Click **Left Arrow** key or **Right Arrow** key to move to next or previous frame.
  * Click **Up Arrow** key or **Down Arrow** key to move to next or previous cut on topmost active track.
  * Click **Next** or **Prev** button in Monitor Buttons area to move to next or previous frame.

**Changing Current Frame when Clip is displayed on Monitor**:
  * Drag with **Left Mouse** on the Monitor Position Bar.
  * Click **Left Arrow** key or **Right Arrow** key to move to next or previous frame.
  * Click **Up Arrow** key or **Down Arrow** key to move to next or previous of the following: Mark In/Mark Out/Start/End
  * Click **Next** or **Prev** button in Monitor Buttons area to move to next or previous frame.

**Switching between Timeline and Clip Display**:
  * Click **Timeline/Clip** button in Monitor Buttons area.
  * Drag Media File on top of **Monitor** to display Clip.

_**Track switches**_

![http://sites.google.com/site/phantom2dsite/Home/tracks_column.png](http://sites.google.com/site/phantom2dsite/Home/tracks_column.png)

**Setting Active Tracks**:
  * Click **Track Active Switch** on the right side of Tracks Column area.

**Effects of Track Active State**;
  * Cuts are only performed on active Tracks.
  * Inserting Media File that is currently displayed in Monitor using **Insert From Monitor, Append From Monitor** or **3-Point Ovewrite** buttons places clip on the top most active Track indicated by arrow icon.

**Selecting single clip**:
  * Click on a clip with **Left Mouse** button.

**Selecting multiple clips on the same track**:
  * Click on a clip with **Left Mouse** button.
  * Click on another clip on the same track with **Control + Left Mouse** button.
  * All clips between clicked clips will be selected.
  * **There is no box selection or any other means of selecting clips from different Tracks at the same time.**

**De-selecting all clips**
  * Click on Timeline area background.

## Adding clips to Sequence ##

**Drag'n'Drop**
  * Press on a Media File in **Media** tab and drag it on top of the track you want to place it on.
  * Clip will be inserted on the track at the nearest cut.

**From Monitor**
  1. Open clip in Monitor by either:
    * double clicking on thumbnail icon,
    * dragging Media File on top of Monitor or
    * selecting **Open in Clip Monitor** item from **Right Mouse** context menu.
  1. Select insert range
    * Use **Mark In** and **Mark Out** buttons to select range.
    * Use **I** an **O** keys to set to select range.
    * If range is not set, then the full clip length will be inserted.
  1. Press **Insert From Monitor** button
    * Clip will be inserted on the first active track at the cut nearest of the currently displayed frame. First active track is marked by down arrow in the track Active Switch.


## Editing Clips on Timeline ##
Once you have placed clips on the Timeline to form a Sequence, you will probably need to refine the cuts between clips.

**Trimming Clips**
Use [Trim Tool](FlowbladeReference#Trim_Tool.md), [Roll Tool](FlowbladeReference#Roll_Tool.md) or  [Slip Tool](FlowbladeReference#Slip_Tool.md)


**Moving Clips**
Use [Insert Tool](FlowbladeReference#Insert_Tool.md) or [Overwrite Tool](FlowbladeReference#Overwrite_Tool.md)

**Cutting Clips**
  1. Select cut frame
    * Cut is always made before currently displayed frame on all active tracks.
    * If you wish to cut off piece from start of the clip, drag Current Frame Pointer to the first frame you wish to have displayed after cut clip piece is removed.
    * If you wish to cut off piece from end of the clip, drag Current Frame Pointer to the last frame you wish to have displayed, and then move one frame forward.
  1. Cut clip
    * Press **Cut** button or press **X** on the keyboard.
  1. Select and delete cut clip piece
    * Click on the cut clip piece and either press **Delete** key or **Splice Out** button of **Lift** button.

**Use Keyboard Shortcuts!** It is much faster to use **X** key to cut clips and **Delete** key to splice out clips than it is to use buttons for the same operations.

## Rendering Movie ##

### Selecting Parameters ###
  * **Folder File Select** button will select folder to place the output file in.
  * **Name** entry widget provides means to set the name of the output file.
  * Use **Encoding Format** and untitled **Quality** drop down menus make to select the type of file to be rendered.

### Rendering output ###
  1. Press **Render** Button to begin rendering.
  1. A Render Window will open displaying information on file path of render file, estimated time left, render time and a Progress bar widget.
  1. After rendering is complete, Render Window will close automatically.

![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---

# Edit Tools #

Flowblade Movie Editor has **five edit tools**, **two move tools** and **three trim tools**.

## Insert Tool ##

**Splice out one or more clips and insert them at desired cut on any track.**

  1. Pick 'Insert' tool
    * Use **Tool Switcher** button drop menu or press **1** key.
  1. Select clip
    * Click **Left Mouse** on a clip.
  1. Select other end of clip range if moving multiple clips
    * Click **CTRL+Left Mouse** on the clip you wish to be the other end of move clip range.
  1. Drag Clip(s) to new position
    * Press **Left Mouse** on a selecetd clip and drag clip/s to a new position.
    * Yellow arrow displays insert point.
    * You can also move clips to a different track.

## Overwrite Tool ##

**Lift out one or more clips and insert them at any point to overwrite on any track.**

  1. Pick 'Overwrite' tool
    * Use **Tool Switcher** button drop menu or press **2** key.
  1. Select clip
    * Click **Left Mouse** on a clip.
    * Select other end of clip range if moving multiple clips. Click **CTRL+Left Mouse** on the clip you wish to be the other end of move clip range.
  1. Drag Clip(s) to new position
    * Press **Left Mouse** on a selecetd clip and drag clip/s to a new position.
    * Red shadow clips show overwrite area.
    * You can also move clips to a different track.

## Trim Tool ##

**Make clip longer or shorter from either clip's end or from clip's beginning.**
  1. Pick 'Trim' tool
    * Use **Tool Switcher** button drop menu or press **3** key.
  1. Select trimmed cut and select new in or out frame
    * Press with **Left Mouse** on a clip near the side you wish to trim
    * Continue on to **Left drag** on clip to select new in or out frame
  1. View trimmed cut
    * Press **Play Loop** button to view edit.
  1. Select new trim from another clip
    * Click with **Left Mouse** on another clip near the side you wish to trim
  1. Select other end of same clip to trim
    * Click on empty space on the Timeline
    * Click with **Left Mouse** on the original clip near the side you wish to trim

## Roll Tool ##

**Move edit point between two clips so that their combined length stays the same.**

  1. Pick 'Roll' tool
    * Use **Tool Switcher** button drop menu or press **4** key.
  1. Select trimmed cut and select new in or out frames
    * Press with **Left Mouse** on a clip near the cut you wish to trim on the side you wish to view while trimming
    * Continue on to **Left drag** on the two selected clips to select in or out frames for both clips
  1. View trimmed cut
    * Press **Play Loop** button to view edit.
  1. Select new trim from another clip
    * Click on empty space on the Timeline
    * Click with **Left Mouse** near the cut you wish to trim

## Slip Tool ##

**Change the displayed area of media in a clip while keeping the clip unchanged on the timeline.**

  1. Pick 'Slip' tool
    * Use **Tool Switcher** button drop menu or press **5** key.
  1. Select trimmed clip and change displayed media
    * Press with **Left Mouse** on a clip you wish to slip trim
    * Continue on to **Left drag** from clip area to display different area of media
  1. Select new trim from another clip
    * Click on empty space on the Timeline
    * Click with **Left Mouse** on the clip you wish to trim

## Spacer Tool ##

**Move all Timeline items on all tracks or on a single track**

  1. Pick 'Spacer' tool
    * Use **Tool Switcher** button drop menu or press **6** key.
  1. Select a clip on Timeline and move it and all items to the right of it
    * Press **Left Mouse** on a clip.
    * Continue on to **Left drag** clip and all clips and compositors to right of it to a new position
    * It is not possible to move items on top of clips. Items can only be moved on top of empty space
  1. Use **Control** button to only affect items on a single track
    * Press **Control** and use **Left Mouse** to move all items on single track to the right of the selected clip

![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---

# Creating Composited Images #

Flowblade Movie Editor uses Compositors to mix images from two different tracks.
By combining multiple tracks and multiple Compositors complex composite images can be achieved.

Compositors have a Source track and a Destination track. On the Timeline Compositor is displayed as a dark rectangular object that is displayed on top of two tracks. Source track is always the one above Compositor, but Destination track may be any of the tracks below it.

Parameters defining the resulting composite are edited in the **Compositors** tab.

There is a subtype of Compositors called Blenders.
Blenders do the standard blends like Add, Softlight and Darken,
but offer no transformations, nor any method to control the amount of blend.

## Compositor Workflow ##
  1. Creating a Compositor
    * Click **Right Mouse** on any clip on tracks from V5 to V2 and select for example **Add Compositor -> Dissolve** or **Add Blender -> Softlight** from popupmenu to create a new Compositor.
  1. Trimmimg or Moving a Compositor
    * To trim Compositor start and end points: Press and drag **Left Mouse** near either end of Compositor on Timeline.
    * To move Compositor: Press and drag **Left Mouse** in the middle of Compositor on Timeline.
  1. Editing Compositor Parameters in Compositors Tab
    * Double click Compositor with **Left Mouse**.
    * Click **Right Mouse** on any Compositor and select Open In Compositor Editor
    * Edit parameters using value editors.
  1. Deleting Compositor
    * Click **Left Mouse** on any Compositor to select it and press **Delete** key.

## Compositor are executed from top to bottom ##
In Flowblade Movie Editor **the order of rendering is top-to-bottom**,
instead of bottom-to-top like in Gimp or Photoshop.

When attempting certain type of multilayer composites this yields results that seem unintuitive,
unless the user is aware of rendering order of Compositors.

### Rendering A Composited Frame ###
  1. For each frame it is checked if there is a Compositor covering this frame that has track V5 as Source track.
  1. If such Compositor is found, do composite on Destination track.
  1. If next track is Source of Compositor covering this frame, that Compositor is rendered.
  1. This is done until there is track that isn't a Source track of any Compositor. That frame on last this track may already been a Destination of a Compositor.

## EXAMPLE: Creating a 3-layer composite ##
In this example we demonstrate how top-to-bottom Compositor
order affects compositing. We are trying to make word 'GO' apperar on top of 2-color
background made by combining red and blue Color Clips using 'Free Stripes' wipe.

To make alpha transparency work the GO.PNG graphic has to composited using 'Dissolve'.

_**clips: RED and BLUE Color Clips and GO.PNG graphic with alpha transparency**_

![http://sites.google.com/site/phantom2dsite/Home/comp_clips.png](http://sites.google.com/site/phantom2dsite/Home/comp_clips.png)

_**Desired result**_

![http://sites.google.com/site/phantom2dsite/Home/correct_comp.png](http://sites.google.com/site/phantom2dsite/Home/correct_comp.png)

### Gimp/Photoshop style layer order yields wrong result ###
Here we have arranged clips on the tracks as we would arrange layers in Gimp.

_**Gimp style layer order**_

![http://sites.google.com/site/phantom2dsite/Home/wrong_timeline.png](http://sites.google.com/site/phantom2dsite/Home/wrong_timeline.png)

What happens here is that first 'GO.PNG' is composited on 'RED' Color Clip, and the resulting image is composited using 'Free Stripes' wipe on top of 'BLUE' Color Clip. We get the wrong result.

_**Wrong result**_

![http://sites.google.com/site/phantom2dsite/Home/wrong_comp.png](http://sites.google.com/site/phantom2dsite/Home/wrong_comp.png)

### Correct layer order when compositing order is top-to-bottom ###

Here we have arranged clips in correct order for the desired result.

_**Correct layer order**_

![http://sites.google.com/site/phantom2dsite/Home/correct_timeline.png](http://sites.google.com/site/phantom2dsite/Home/correct_timeline.png)

Here 'RED' Color Clip  is first composited using 'Free Stripes' wipe on 'BLUE' Color Clip. After that 'GO.PNG' is composited on top of the resulting image (that is already rendered on track V1) using 'Dissolve' to get final output image.

_**Destination track in 'Region' Compositor is V1, Source track is V3**_

![http://sites.google.com/site/phantom2dsite/Home/correct_dest.png](http://sites.google.com/site/phantom2dsite/Home/correct_dest.png)

_**Correct result**_

![http://sites.google.com/site/phantom2dsite/Home/correct_comp.png](http://sites.google.com/site/phantom2dsite/Home/correct_comp.png)

## TABLE: Compositors ##
| **Compositor** | **Description** |
|:---------------|:----------------|
|Affine|Does affine transform (move-rotate-skew) before compositing. Has keyframed mix, position and rotation, and non-keyframed skew.|
|Affine Blend|Does affine transform (move-rotate) before compositing in any blend mode. Has keyframed mix, position and rotation.|
|Blend|Does keyframed mix in any blend mode.|
|Dissolve|Does keyframed mix.|
|Picture in Picture|Does picture in picture composite with keyframed mix and transform.|
|Region|Does picture in picture composite with keyframed mix, wipe and transform.|
|Wipe|Does a non-keyframed full wipe that has the same duration as the clip.|

## TABLE: Blenders ##
| **Blend Mode** | **Description** |
|:---------------|:----------------|
|Add|This blend mode simply adds pixel values of one layer with the other. In case of values above 255 (in the case of RGB), white is displayed.|
|Burn|The Burn mode divides the inverted bottom layer by the top layer, and then inverts the result.|
|Color Only|Color blend mode preserves the luma of the bottom layer, while adopting the hue and chroma of the top layer.|
|Darken|Darken takes the darkest value for each pixel from each layer.|
|Difference|Difference subtracts the top layer from the bottom layer or the other way round, to always get a positive value. Blending with black produces no change, as values for all colours are 0. (The RGB value for black is 0,0,0). Blending with white inverts the picture.One of the main utilities for this is during the editing process, when it can be used to verify alignment of pictures with similar content|
|Divide|This blend mode simply divides pixel values of one layer with the other.|
|Dodge|Dodge blend mode divides the bottom layer by the inverted top layer. This decreases the contrast to make the bottom layer reflect the top layer: the brighter the top layer, the more its colour affects the bottom layer.|
|Grain Extract| - |
|Grain Merge| - |
|Hardlight|Hard Light combines Multiply and Screen blend modes. As opposed to Overlay, the contrast is also increased.|
|Hue|Hue blend mode preserves the luma and chroma of the bottom layer, while adopting the hue of the top layer.|
|Lighten|Lighten takes the lightest pixel from each layer.|
|Multiply|Multiply blend mode multiplies the numbers for each pixel of the top layer with the corresponding pixel for the bottom layer. As a simple multiplication for 8-bit/channel can get values as high as 65025 (255\*255), which is far higher than the maximum allowed value, 255, the result is divided by 255.|
|Overlay|Overlay combines Multiply and Screen blend modes. Light parts of the picture become lighter and dark parts become darker. An overlay with the same picture looks like an S-curve.|
|Saturation|Saturation blend mode preserves the luma and hue of the bottom layer, while adopting the chroma of the top layer.|
|Screen|With Screen blend mode the values of the pixels in the two layers are negated, multiplied, and then negated again. This is in some way the opposite of multiply. The result is a brighter picture.|
|Softlight|This is a softer version of Overlay. Applying pure black or white does not result in pure black or white.|
|Subtract|This blend mode simply subtracts pixel values of one layer with the other. In case of negative values, black is displayed.|
|Value|Value blend mode preserves the hue and chroma of the bottom layer, while adopting the luma of the top layer.|

_Blend descriptions are from Wikipedia and are under Creative Commons Attribution-ShareAlike License._

![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---

# Adding Filters #

In Flowblade Movie Editor you can add a Filters to all clips to modify output image and audio.

Parameters defing output are edited in the Filters tab. Clips will display small filter icon if a filter has been added to them. To have any effect, the filters that modify alpha channel have to be mixed with images from other clips using Compositors.

## Filter Workflow ##

  1. Adding Filter
    * Click **Right Mouse** on any clip and select for example **Add Filter -> Blur -> Pixelize** from popup menu.
    * In **Filters** tab: double click on a filter in the currently displayed filters group.
    * In **Filters** tab: drag a filter from the currently displayed filters group to the Filters Stack table below.
  1. Opening Filter for Editing in **Filters** tab
    * Click **Right Mouse** on any clip and select
    * Open in Filters Editor from popup menu.
    * **Double click** on any clip.
  1. Cloning Filters from other Clips
    * Click **Right Mouse** on any clip and select **Clone Filters -> From Next Clip** or **Clone Filters -> From Previous Clip** from popup menu.
  1. Deleting Filters from Clips
    * Select filter in Filters Stack table and click **Delete** button above.
    * Select filter in Filters Stack table and press **Delete** key.
    * Select clip or range of clips in Timeline and select **Clear Filters** from application menu.

![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---

# Range Log #

Flowblade provides functionality save, name and manage in-point to out point ranges on media items.

This useful then there are media items that contain multiple areas of interest or if the user wants to save in and out points of an edit for later use.

A typical example use case for the feature would be:
  * user has a long clip of a speech delivered at some social function
  * user wants to mark and name the interesting parts of the speech

## Creating Range Log Items ##
  * **With Clip Monitor**
    1. Add Media Item to Clip Monitor
    1. Set Mark In and Mark Out points
    1. Press 'Log Current marked Range' -button on the bottom left in the Range Log panel
  * **Drag'n'Drop from Timeline**
    1. Drag a Clip from Timeline on top of Items list view in the Range Log panel


## Adding Range Log items to Timeline ##
  * **With buttons**
    * Press 'Append displayed..." -button on the bottom right corner to append all Items as Clips on active Track
    * Press 'Insert selected..." -button next to bottom right corner button to insert all selected Items on active track at nearest cut from the currently displayed Timeline position
  * **Drag'n'Drop into Timeline**
    * Select a Range Log item and drag it into the desired position on Timeline

## Managing Range Log Items ##
  * Use top row drop down menu to select the displayed Items Group
  * Use the top left corner button drop down menu to create, rename and delete Items Groups

![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---

# Clip Syncing and Audio Split Editing #

In Flowblade Movie Editor you can **set a clip's positions to follow another clip's positions** on request.

This is done by **setting clip to be a Sync Child Clip** clips by selecting a
clip on track V1 as its Sync Parent Clip.

**Only clips on track V1 can be Sync Parent Clips**. This is done to encourage edit style in which the main body of the Sequence is on track V1 and composites and audio split edits are done relative to the clip sequence on track V1.

**Sync feature helps preserve earlier work** an multitrack composites and audio split edits when clips are no longer in correct positions relative to each other, because of edits elsewhere on the Sequence.

**Resyncs are only done on request** to avoid jumping of clips on the timeline while editing. Explicit resyncs are also better from the point of view of avoiding side effects when doing edits.

## Setting Sync Parent ##
  1. Click **Right Mouse** on clip and select Select Sync Parent Clip... on any clip NOT on track V1.
  1. Cursor turns into a Target Cross. Click on clip on track V1 to select it as Sync Parent Clip.
  1. Sync Relation is established between the two clips. Cursor turns back into a default pointer.
  1. Sync State Stripe appers on the Sync Child Clip. Sync State Indicator Stripes on Clips:
    * Green means that clip is in sync with parent.
    * Red means that clip is NOT in sync with parent.
    * Gray means that Sync Parent Clip is no longer on track V1.

## Resyncing Sync Child Clips ##
  * Select **Edit -> Resync All to resync** from application menu all Sync Child Clips.
  * Select **Edit - >Resync Selected to resync** from application menu selected Sync Child Clips.
  * Click **Right Mouse** on Sync Child Clip and select **Resync** from popoup menu to resync single clip.
  * Press **Resync Selected** Bbtton to resync selected Sync Child Clips.

## Clearing Sync Parent Relations ##
  * Click **Right Mouse** on Sync Child Clip and select Clear Sync Relation.

## Syncing Composited Clips ##
  * If appropriate set all clips that are part of a multitrack composite synched to the same clip.

## Audio Split Syncing ##
  * Click **Right Mouse** on clip in track V1 and select Split Audio Synched.
  * Edit audio split using Two Roll Trim mode to maintain sync with parent clip.
  * Resync Audio as needed.

![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---

# Slow / Fast Motion #

In Flowblade motion effects are achived by **rendering slow / fast motion versions of video clips** and placing those on the timeline.

## Creating Motion Clips ##
  1. Right click on a Media File and select **Render Slow / Fast Motion File** from menu
  1. Edit parameters for the new motion Clip
    * Set speed
    * Give name and location for motion Clip
    * Select rendering parameters for motion Clip. It is probably a good idea to use a **lossless format** here to avoid any generational quality losses.
    * Select render range, either:
      * Full Source Clip
      * From Source Clip Mark In to Mark Out
  1. Click **Render** button to create a new motion Clip

![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---


# Proxy Editing #

Proxy editing is a method of editing in which original media clips are presented on timeline by proxy clips. Proxy clips usually have smaller data rate and less CPU intensive decoding.

There are two main reasons to use proxy editing to create programs:
  * Original media from which the program is edited makes too high demands for either disk bandwidth or CPU processing power for decoding to enable responsive editing
  * Original is kept on network server, slow external disk or other media with restricted access and does not provide responsice editing if accessed directly.

## Generic Proxy Editing workflow ##

All proxy editing workflows have the same phases:
  1. Render proxy media from original media
  1. Replace original media with proxy media
  1. Edit using proxy media
  1. Replace proxy media with original media
  1. Render final program using original media

## Flowblade proxy editing ##
  1. Creating Proxy Media
    * Select **Project->Proxy Manager** in menu and set proxy file settings in **Proxy Encoding** area
    * Select Video Media files in **'Media'** Panel
    * Press button with proxy file icon next Delete button in 'Media' Panel
    * If Project is already in **'Using Proxy Media'** proxy mode, timeline clips with original media that had proxy media rendered to will be replaced with proxy media immediately
  1. Converting to use Proxy media
    * Select **Project->Proxy Manager** to open Proxy Manager
    * Press **Use Proxy Media** button
  1. Editing with proxy media
    * Clips that use proxy media have a blue stripe indicating that status
    * A proxy editing indicator icon is displayed at left bottom corner
    * If new proxy media is rendered timeline clips using the original media in question will be replaced with proxy media immediately
    * Project can be saved normally and converted after load to use original media
  1. Converting to use Original Media
    * Select **Project->Proxy Manager** to open Proxy Manager
    * Press **Use Original Media** button

## Important notes about Flowblade proxy editing ##

Flowblade uses a programming techique that changes the paths used by media and clips to point either to proxy media or original media. Changing from one to another is implemented by writing a project file to disk and replacing paths when project is read back. This has important implications on how proxy editing works in Flowblade:

**IMPORTANT**
  * **It is only possible to use all proxy media and clips or all original media**
  * **DESTROYING ANY MEDIA while doing proxy editing WILL PREVENT CONVERTING BACK TO USING ORIGINAL MEDIA**


![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---


# Rendering #

## Rendering Movie ##

### Selecting Parameters ###
  * **Folder File Select** button will select folder to place the output file in.
  * **Name** entry widget provides means to set the name of the output file.
  * Use **Encoding Format** and untitled **Quality** drop down menus make to select the type of file to be rendered.

### Rendering output ###
  1. Press **Render** Button to begin rendering.
  1. A Render Window will open displaying information on file path of render file, estimated time left, render time and a Progress bar widget.
  1. After rendering is complete, Render Window will close automatically.


## Batch Render Queue ##

**Feature will be available on 0.12 release**

Flowblade offers a dedicated Batch Render Queue application. Batch Render Queue is a separate application to Flowblade and runs on different process, so it is possible to close Flowblade without affecting ongoing renders.

Render queue is a persistent data structure of render items on disk. Each item consists of a Project file and saved render parameters. Users can add render items to render queue and then render the whole queue without any further user input.

**Adding Items to Batch Render Queue**

  * Press **To Queue** button in **Render** tab.
  * Select **Render->Add to Batch Render Queue...** item from menu

**Using Batch Render Queue application**

  * Open Batch Render Queue application by selecting **Render->Batch Render Queue** from menu.
  * Press **Reload Queue** button to display render items that have been added to render queue since it was opened.
  * Use **Delete Selected** and **Delete Finished** buttons to remove items from queue.
  * Use checkbox widget in the Render column to select which items will be rendered.
  * Press **Render** button to begin rendering.
  * **Right Mouse Click** render item to show render item context menu.
    * **Save Item Project As...** allows th user to save the Project file of the render item into same other location
    * **Render Properties** displays the render properties that were set when the item was added to render queue.
    * **Delete** deletes the item from queue

## Rendering behind the scenes: MLT and libavformat(FFMpeg) ##

Flowblade Movie Editor is a Python application interfacing to MLT multitrack media framework.
Other video editing applications build on top of MLT include OpenShot and Kdenlive.

MLT uses C-library libavformat(FFMpeg) to render output files, and rendering is defined by setting FFMpeg encoding parameters.
These parameters are delivered from Flowblade Movie Editor to MLT by creating a "avformat" Consumer object for
a  given Render Profile, and then setting its Rendering Args.
These latter arguments are exactly the same which are used when using FFmpeg to encode video files.

Rendering arguments for encoding different types of video files are pre-packed and can be selected using
Encocing / Format and Quality Drop Down Menus. Arguments can be refined
by checking Render with args Checkbox and changing args values and/or adding/removing args.

Any kind of video files supported by the installed version of MLT can be encoded by creating a user defined
Render Profile and setting its Rendering Args. Google for FFMpeg encoding to find Args combinations for different video files.

Search web for information on encoding files with FFMpeg to get examples of Rendering Args that can be used.

## Flowblade rendering pipeline ##

![http://sites.google.com/site/phantom2dsite/Home/encoding.png](http://sites.google.com/site/phantom2dsite/Home/encoding.png)

![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---

# Tools #

## Titler ##
  * Add and remove layers in Layers area
  * Edit layer properties and text in Active Layer area
  * Set text position by dragging the active layer around in the view editor
  * Set background image from Timeline to position texts appropriately by dragging frame pointer in the Position Bar
  * Load and Save layers data in Layers Area

## Audio Mixer ##
  * Monitor audio levels on VU meters during playback
  * Use sliders to set volume for tracks or Master Out
  * Click **Pan** button to activate pannig slider and use it to pan audio

## Media Relinker ##
  * **Media Relinker** is a standalone application running in its own process and does not affect the project that is open in Flowblade
  * Start by pressing **Load Project For Relinking** button and select the project you wish to relink
  * Select the media file you wish to replace with some other media file. Press **Set File Relink Path** button or press **Right Mouse** on item to start selecting the new file. Clips and wipes in the project are linked to this new media file.
  * Use drop down menu at bottom left to display either missing or found media files
  * Press **Save Relinked Project As...** button to save the relinked version of the project
  * Open the relinked project in Flowblade and continue working with it
  * When relinking a project you have open in Flowblade at the same time **make sure that do not overwrite the relinked version of project when saving the project you have open in Flowblade**

![http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png](http://sites.google.com/site/phantom2dsite/Home/flowbladeappicon.png)

---
