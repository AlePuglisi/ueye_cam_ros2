![Build Test (not for release)](https://github.com/anqixu/ueye_cam/workflows/Build%20Test%20(not%20for%20release)/badge.svg?branch=master&event=push)

# Camera Installation

## Camera setup (UI-3260CP-M-GL)

As of now (2025-07-22), drivers for this camera are provided [here](https://en.ids-imaging.com/download-details/AB00041.html?os=linux&version=&bus=64&floatca). You can install them with the following:

```sh
mkdir -p /tmp/ids
cd /tmp/ids
wget https://en.ids-imaging.com/files/downloads/ids-software-suite/software/linux-desktop/ids-software-suite-linux-64-4.96.1-debian.tgz
tar xzvf ids-software-suite-linux-64-4.96.1-debian.tgz
sudo apt install ./ueye*
```

You need to add the following to your `~/.bashrc` file:
```sh
echo "export PATH="$PATH:/opt/ids/ueye/bin" >> ~/.bashrc
source ~/.bashrc
```

Test with:

```sh
ueyedemo
```

You also need to install [IDS peak SDK](https://en.ids-imaging.com/download-peak.html?os=linux&version=&bus=64) >= 2.16.0:

```sh
wget https://en.ids-imaging.com/files/downloads/ids-peak/software/linux-desktop/ids-peak-with-ueyetl_2.16.0.0-457_amd64.deb
sudo apt instll ./ids-peak-with-ueyetl_2.16.0.0-457_amd64.deb
```

You can test it with:

```sh
ids_peak_cockpit
```

## UEye Cam Driver

1. Install [ROS2 jazzy](http://wiki.ros.org/ROS/Installation)
2. Install dependencies:
    ```sh
    sudo apt install ros-jazzy-ros2launch ros-jazzy-ros2param ros-jazzy-ros2run ros-jazzy-ros2topic ros-jazzy-rqt-image-view ros-jazzy-camera-info-manager ros-jazzy-cv-bridge ros-jazzy-ament-cmake ros-jazzy-ament-cmake-auto
    ```
2. Generate a ROS workspace

    `mkdir -p ros2_ws/src/`

3. Clone the repository

    ```
    cd ros2_ws/src/
    git clone https://github.com/arntanguy/ueye_cam.git -b jazzy 
    ```

4. Build the workspace

    ```sh
    cd ~/ros2_ws
    colcon build
    ```

4. Source the workspace

    ```sh
    source ~/ros2_ws/install/setup.bash
    ```

5. To get started, launch the standalone or component launcher. It is configured with a parameterisation that should enable connection to most IDS cameras.

```sh
# Uses ueye_cam/config/standalone.yaml
$ ros2 launch ueye_cam ids_ui_3260cp.launch.py 

# In a seperate shell, visualise the stream
$ ros2 run rqt_image_view rqt_image_view /ueye/ui_3260cp/image_raw

# Play around with parameters
$ ros2 param list
$ ros2 param set ueye auto_gain false
$ ros2 param describe ueye red_gain
$ ros2 param set ueye red_gain 100
```


# UEye Cam Driver (original documentation)

This software comes with a [BSD License](./LICENSE) and provides convenience APIs
(c++ and ROS) that facilitate access to UEye Cameras via the IDS Software Suite.

## Requirements

**Buildtime**

If you are just building the software, no IDS Software Suite installation is required.
This package will fetch headers and libraries on-the-fly to result in a successful build.
Note however, that these are not made available for a runtime environment. These headers
and libraries are not installed to the install space and you'll also need to install
the IDS discovery daemon.

**Runtime**

* [IDS uEye Software Suite](https://en.ids-imaging.com/downloads.html) >= 4.94 

The IDS Software Suite installs headers, libraries, documentation and a daemon used for
discovery of UEye cameras.

Start the discovery daemon for ethernet connected cameras:

```
$ sudo systemctl start ueyeethdrc
$ sudo /etc/init.d/ueyeethdrc start
```

To configure the cameras, do it via the `idscameramanager` graphical tool (should be reasonably
self-explanatory) or via the command line tools:

* Enumerate the network interfaces to be used for discovery (`/etc/ids/ueye/ueyeethd.conf`)
* Configure the camera ip addresses (`ueyesetip`)
* Configure the camera ids (`ueyesetid`)

## Usage

**Resources**

Default resource paths include:

* `~/.ros/camera_info/`:  camera calibration files (`.yaml`)
* `~/.ros/camera_conf/`:  IDS configuration files (`.ini`)

The camera calibration files are used to feed the ros2 [camera_calibration](https://github.com/ros-perception/image_pipeline/tree/ros2/camera_calibration) framework.

The IDS configuration files are the native format for configuring an IDS camera. In general, you do not need an IDS configuration file as the ROS wrapper exposes most of the configuration via dynamic ROS parameters, but an IDS configuration
file can be useful for parameters that it does not yet cover.

**Quick Start**

To get started, launch the standalone or component launcher. It is configured with a parameterisation that should enable connection to most IDS cameras.

```
# Install launcher / debugging / viz tools if you don't already have them
$ sudo apt install ros-foxy-ros2launch ros-foxy-ros2param ros-foxy-ros2run ros-foxy-ros2topic ros-foxy-rqt-image-view

# Uses ueye_cam/config/standalone.yaml
$ ros2 launch ueye_cam standalone.launch.py

# In a seperate shell, visualise the stream
$ ros2 run rqt_image_view rqt_image_view /ueye_cam/froody/image_raw

# Play around with parameters
$ ros2 param list
$ ros2 param set ueye_cam auto_gain false
$ ros2 param describe ueye_cam red_gain
$ ros2 param set ueye_cam red_gain 100
```

**Configuration**

In a typical launch, configuration can be traced to one or more sources, each with their own priority. Lower priorities can be overridden by higher priorities. From lowest, to highest:

* _Defaults_ : refer to `ueye_cam/node_parameters.hpp` and `ueye_cam/camera_parameters.hpp`
* _IDS_ : defined in `node_parameters.ids_configuration_filename`
    * If none is set, the default `~/.ros/camera_conf/<camera_name>.ini` is used
* _On-Launch_ : usually passed in via `.yaml` to the launcher / command line
* _Dynamic_ : modified on the fly at runtime

**Camera Calibration**

TODO

**IDS Camera Configuration Files (Optional)**

Using the ros2 node, along with ros2 parameters will serve most use cases. Making use of IDS camera configuration files however (e.g. `config/example_ids_configuration.ini`) is useful in some situations:

* If you want access to all parameters of the camera. This node only exposes the most common parameters for configuration as ROS2 parameters.
* If you want to absolutely ensure your cameras have a fully deterministic launch, these initialisation files are *complete*. On loading, they will overwrite any and all residual configuration left by the last user. The ROS2 configuration will also be as deterministic as possible, i.e. it will overwrite any and all residual configuration it knows about, but it will not be able to do so for parameters it is not aware of that may have been reconfigured via other means.

TODO - how to use the IDS gui, how to export and load the configuration files.
