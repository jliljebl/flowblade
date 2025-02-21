
## Building Python 3 bindings to use with repo installation

This is a rough guide on how install and run self created MLT bindinds with Flowblade install from repository.

Please create pull request against this document if you have corrections or additions to improve this guide.

### Install Flowblade from OS repository
See [here](./INSTALLING.md). This installs the runtime dependencies to run Flowblade and use MLT. *(Note that Flatpak install does not work here because dependencies when installed by Flatpak will not be available to the local install of MLT we are creating)*

### Install MLT build dependencies
Here is list of Ubuntu build dependencies. There could be some omissions, please file a pull request to update the list if something is found to be missing.

```bash
sudo apt-get install git swig python3-dev python3-numpy libxml2-dev libsdl-dev libavdevice-dev libswscale-dev libvorbis-dev libsamplerate-dev frei0r-plugins-dev libdv-dev libavformat-dev libquicktime-dev libsox-dev libjack-dev ladspa-sdk libopencv-dev librubberband-dev libvidstab-dev
```

### Create work directory 

Let's call this directory **\<ROOT_DIR\>**. Open terminal in this directory.

### Clone MLT repository
```bash
git clone https://github.com/mltframework/mlt.git
```

### Create bindings with CMAKE

Since 2023, MLT only builds with CMAKE.

#### Configure and build
With terminal still open in **\<ROOT_DIR\>**.
```bash
cmake -DCMAKE_BUILD_TYPE=Release -DSWIG_PYTHON=ON -DMOD_GLAXNIMATE_QT6=OFF -DMOD_GLAXNIMATE=OFF -DMOD_QT=OFF -DMOD_QT6=OFF -DMOD_MOVIT=OFF -DMOD_OPENCV=ON -S ./mlt -B ./build

cmake --build ./build --config Release
```

#### Create a local install
```bash
mkdir install

cmake --install ./build --prefix ./install
```

### Set up bindings

1. Copy *mlt7.py* and *_mlt7.so* from  *\<ROOT_DIR\>/install/lib/python3.\<current_version\>/dist-packages* into  *../flowblade-trunk* where your repository version Flowblade is installed.
1. Create a launch script in to set up MLT variables correctly on launch.

 ```bash
#!/bin/sh

# Set MLT environment variables to point
# where you have the binaries and libraries
# so MLT finds them runtime.
ROOT_DIR=<ROOT_DIR\>

INSTALL_DIR=$ROOT_DIR/install
export PATH=$INSTALL_DIR/bin:$PATH

export MLT_REPOSITORY=$INSTALL_DIR/lib/mlt-7
export MLT_DATA=$INSTALL_DIR/share/mlt-7
export MLT_PROFILES_PATH=$INSTALL_DIR/share/mlt-7/profiles
export LD_LIBRARY_PATH=$INSTALL_DIR/lib:$LD_LIBRARY_PATH

# Launch repository Flowblade
/home/path/to/flowblade/repo/install/flowblade-trunk/flowblade
``` 

Launch Flowblade with the script above.
