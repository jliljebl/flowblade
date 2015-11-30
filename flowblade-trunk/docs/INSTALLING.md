# Installing Flowblade #


### Installing using .deb package

**First download .deb file** for Flowblade 1.4 from <a href="https://www.dropbox.com/s/xe94cjwmf195de2/flowblade-1.4.0-1_all.deb?dl=0">here.</a>

<ul>
    <li>Double Click on the downloaded .deb file to install.</li>
    <li>On at least <b>Linux Mint 17</b> you will need to install dependencies separately with command:</li>
</ul>

```bash
sudo apt-get install -f
```

Release has been tested on: <b>Ubuntu 15.10, 14.10, and Debian 8</b>.

<b><i>Flowblade versions 1.2 and 1.4 are not supported for Ubuntu 14.04, Linux Mint 17.x,  Debian 7 or earlier systems.</i></b> Flowblade uses a GTK3 feature that is not available on those systems. Last GTK2 version 1.0 should work fine and it can be downloaded <a href="https://www.dropbox.com/s/9m2e9whcazjo1l8/flowblade-1.0.0-1_all.deb?dl=0">here.</a>

*Please note these issues with Dropbox download:*
<ul>
 <li> <i>The download button may appear grayed out and you have to press it twice.</i></li>
 <li> <i>A window may appear that asks you to create an account, but you can close it and press Download button again.</i></li> 
 <li> <i>The .deb file is in a Dropbox Public folder and may go over download limit, please contact Project Owner if this happens.</i></li>
</ul>

### Installing from your OS repository

The easiest way to install Flowblade is using the version in your OS repository. The downside is that **the version available may not be the current latest release**. Contact your OS to get latest Flowblade included in repositories if not already available.

#### Ubuntu, Debian and Linux Mint

```bash
sudo apt-get install flowblade
```
#### Archlinux

_Latest release_. Visit the <a href="https://aur.archlinux.org/packages/flowblade/">AUR</a> page or use terminal command:
```bash
yaourt -S flowblade
```

_Git version_. Visit the <a href="https://aur.archlinux.org/packages/flowblade-git/">AUR</a> page or use terminal command:
```bash
yaourt -S flowblade-git
```



### Installing Using Source Code Archive

Flowblade is currently a 100% script application, and all the dependencies should be available in popular distributions, so in most cases it should be possible to install and run Flowblade without compiling anything.

**First download 1.4 tar.gz** source archive file from <a href="https://www.dropbox.com/s/vmu12w36ov2aza8/flowblade-1.4.0.tar.gz?dl=0">here.</a> 

  * Extract archive into a folder of your choosing
  * Install dependencies. See [Dependencies](DEPENDENCIES.md) doc for more information.
  * If you have Flowblade installed in your system, you probably have the dependencies installed, unless some new ones have been added.
  * Launch by running script *.../flowblade-1.4.0/flowblade* that was created in the folder where archive was unpacked.
  * Note that if you have Flowblade installed you will need use full path to repository version or navigate to the folder containing launch script and use command "./flowblade" to launch repository version instead of installed version.

*Please note these issues with Dropbox download:*
<ul>
 <li> <i>The download button may appear grayed out and you have to press it twice.</i></li>
 <li> <i>A window may appear that asks you to create an account, but you can close it and press Download button again..</i></li> 
 <li> <i>The .deb file is in a Dropbox Public folder and may go over download limit, please contact Project Owner if this happens.</i></li>
</ul>

### Installing Using Development Repository Version

Flowblade is currently a 100% script application, and all the dependencies should be available in popular distributions, so in most cases it should be possible to install and run Flowblade without compiling anything.

Developer version may however be unstable or have new dependencies. If you fail to install developer version, please file a bug in Issues -tab.
  * Install Git in your system (Ubuntu command):
```bash
sudo apt-get install git
```
  * Use Git to download Flowblade into a folder of your choosing by using the git clone command in your terminal:
```bash
git clone https://github.com/jliljebl/flowblade.git
```
  * Install dependencies. See   [Dependencies](DEPENDENCIES.md) doc for more information.
  * If you have Flowblade installed in your system, you probably have the dependencies installed, unless some new ones have been added.
  * Launch by running script ``.../flowblade-trunk/flowblade`` that was created in the folder where clone command was done.
  * Note that if you have Flowblade installed you will need use full path to repository version or navigate to the folder containing launch script and use command "./flowblade" to launch repository version instead of installed version
 
*Please note: Using the available setup.py script will NOT result in a successful installation, even if dependencies are installed, and may actually break the .deb install if attempted. It is only there to help .deb packaging.* 
