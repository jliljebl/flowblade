

![Flowblade](flowblade-trunk/Flowblade/res/darktheme/header_text.png "Flowblade")

1. [Introduction](https://github.com/jliljebl/flowblade#introduction)
2. [Features](https://github.com/jliljebl/flowblade#features)
3. [Releases](https://github.com/jliljebl/flowblade#releases)
4. [Installing Flowblade](https://github.com/jliljebl/flowblade#installing-flowblade)
5. [Docs](https://github.com/jliljebl/flowblade#docs)
6. [Screenshot](https://github.com/jliljebl/flowblade#screenshot)
7. [Webpage](https://github.com/jliljebl/flowblade#webpage)
8. [Contact](https://github.com/jliljebl/flowblade#contact)


**Due to moving the project is on a short break starting 3.10.24.** 

**After boxes are unpacked we are hoping to get going again by mid-October.**

---

**--- FIX FOR NON_WORKING VIDEO PREVIEW ISSUE ---**

**Start application from terminal with command:**

```
SDL12COMPAT_NO_QUIT_VIDEO=1 GDK_BACKEND=x11 SDL_VIDEODRIVER=x11  /usr/bin/flowblade 
```
**More info on Issue here: [Issue #1134](https://github.com/jliljebl/flowblade/issues/1134)**

**--- FIX FOR NON_WORKING VIDEO PREVIEW ISSUE ---**

# Introduction

Flowblade is a **multitrack non-linear video editor** for Linux released under **GPL 3 license**.

With Flowblade Movie Editor you can compose movies from video clips, audio clips and graphics files. Clips can be cut at the desired frames, filters can be added to clips, and you can create multilayer composite images using compositor objects.

# Features Overview

**Editing:**
* Toolset with 6 editing tools available
* 4 methods to insert / overwrite / append clips on the timeline
* Drag'n'Drop clips on the timeline from Clip monitor and media panel
* Clip parenting and audio synchronizing
* Max. 21 combined video and audio tracks available

**Image compositing:**
* Standard Track Compositing workflow 
    * Fades, transition and alpha channel manipulation achieved using with filters
    * Blend mode is settable per clip
* Compositor based workflow
    * Multiple compositors available. Mix, zoom, move and rotate source video with keyframed animation tools
    * 19 blends. Stardand image blend modes like Add, Hardlight and Overlay are available
* 40+ pattern wipes, user created patterns can be used also

**Image and audio filters:**
* 50+ image filters: color correction, image effects, distorts, alpha manipulation, blur, edge detection, motion effects, freeze frame, etc.
* 30+ audio filters: keyframed volume mixing, echo, reverb, distort, etc.

**Advanced features:**
* **Generators:** Powerful media generator plugin framework available to create e.g. animated texts and backgrounds.
* **Range Log:** Save and edit clip in/out ranges to easily utilize best parts of your material
* **G'Mic Tool:** Create media with beatiful, complex effects not available in any other editor
* **Text Tool:** Create text plates with a handy purpose build tool with large set of features like text shadow, outline etc.
* **Batch Encoding:** Render multiple output clips automatically 
* **Media re-linking:** Fix projects with missing media to be editable again.
* **USB Shuttle playback control:** Control playback with all the most popular USB Shuttle/Jog devices available on market.
  
**Supported editable media types:**
* Most common video and audio formats, depends on installed MLT/FFMPEG codecs
* JPEG, PNG, TGA, TIFF graphics file types
* SVG vector graphics
* Numbered frame sequences 

**Output encoding:**
* Most common video and audio formats, depends on installed MLT/FFMPEG codecs
* GPU Vaapi and NVENC encoders available
* User can define rendering by setting FFMpeg args individually

# Releases

**Latest release:** Flowblade Movie Editor 2.16 was released in May 2024.

# Installing Flowblade

Installing instructions are available [here](./flowblade-trunk/docs/INSTALLING.md).

# Docs

[FAQ](./flowblade-trunk/docs/FAQ.md)

[Known Issues](./flowblade-trunk/docs/KNOWN_ISSUES.md)

[Roadmap](./flowblade-trunk/docs/ROADMAP.md)

[Release notes](./flowblade-trunk/docs/RELEASE_NOTES.md)

[Creating a translation](./flowblade-trunk/docs/CREATING_TRANSLATION.md)

[Dependencies](./flowblade-trunk/docs/DEPENDENCIES.md)

[System Requirements](./flowblade-trunk/docs/SYSTEM_REQUIREMENTS.md)

# Screenshot
[Screenshot 2.10](./flowblade-trunk/docs/Screenshot-2-10.png)

# Webpage
[The project webpage is here](http://jliljebl.github.io/flowblade/). 

# Contact

Use the **Issues** tab to give bug reports or to make feature requests.

If needed, contact the project lead for additional information: janne.liljeblad@gmail.com
