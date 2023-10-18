# Installing Flowblade

*NOTE: Since version 2.10 we no longer provide .deb packages for the application. The recommended way of installing the latest version if it is not available in your OS repository is to install Floablade Flatpak*

  * [Installing Flatpak from Flathub](./INSTALLING.md#installing-flatpak-from-flathub)
  * [Installing Flatpak from Flathub with commandline](./INSTALLING.md#installing-flatpak-from-flathub-with-commandline)
  * [Installing using your OS appstore GUI application](./INSTALLING.md#installing-using-your-os-appstore-gui-application)
  * [Installing from your OS repository using commandline](./INSTALLING.md#installing-from-your-os-repository-using-commandline)
  * [Installing using Development Repository Version](./INSTALLING.md#installing-using-development-repository-version)
    
## Installing Flatpak from Flathub


Setup Flathub for your distro, there is an official guide here: https://flatpak.org/setup/ .

Go to Flathub <a href="https://flathub.org/apps/io.github.jliljebl.Flowblade">Flowblade page</a> and install from there. 

##  Installing Flatpak from Flathub with commandline

Go to Flatub <a href="https://flathub.org/apps/io.github.jliljebl.Flowblade">Flowblade page</a> and see the *Manual Install* area at the bottom of the page.

Give the commands given the in a terminal application.

## Installing using your OS appstore GUI application

Most Linux distributions provide GUI appstore application and Flowblade should generally be installable using those.

**NOTE: Sometimes version in appstore is older then the latest version, which is always available areFlathub.**

## Installing from your OS repository using commandline

**NOTE: The version available may not be the current latest release**. Contact your OS to get latest Flowblade included in repositories if not already available.
    
#### Ubuntu, Debian and Linux Mint

```bash
sudo apt-get install flowblade
```

#### Archlinux

_Latest release_. Visit the <a href="https://archlinux.org/packages/community/any/flowblade/">AUR</a> page or use terminal command:

```bash
yaourt -S flowblade
```

_Git version_. Visit the <a href="https://aur.archlinux.org/packages/flowblade-git/">AUR</a> page or use terminal command:

```bash
yaourt -S flowblade-git
```

## Installing using Development Repository Version

Flowblade 2.10 has been developed with MLT 7.12 or higher.

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
