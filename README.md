# Rock Cam

MJPEG camera streaming server for Radxa Rock 4 using GStreamer

# Installation

## Clone directory to `/opt`
```
cd /opt
git clone <repository_url>
```

## System requirements

### Radxa CLI images
The Radxa CLI images does not install the required RockChip vendor packages, so additional setup is required

#### Create `/etc/apt/sources.list.d/radxa-rockchip.list` 
```
deb [signed-by=/usr/share/keyrings/radxa-archive-keyring.gpg] https://radxa-repo.github.io/bullseye rockchip-bullseye main
```
#### Create `/etc/apt/preferences.d/radxa-rockchip`
```
Package: *
Pin: release a=rockchip-bullseye
Pin-Priority: 1001
```
#### Blacklist `panfrost` driver, create `/etc/modprobe.d/panfrost.conf`
```
# settings for panfrost

# Disable panfrost driver by default to perfer mali driver
# This is due to Rockchip version of graphical stack does
# not support panfrost, and will use sofware rendering instead
blacklist       panfrost

# Uncomment the following line and comment above lines
# to use panfrost driver for GPU instead
# You will have to install desktop without vendor repo
#blacklist   mali
#blacklist   bifrost_kbase
#blacklist   midgard_kbase
```


#### Install drivers
A reboot is needed after installing the packages
```
apt install task-rockchip-mpp task-rk3399-camera rockchip-udev gstreamer1.0-plugins-good
```


### Install packages required for running the server
```
apt install python3-aiohttp python3-setproctitle python3-gst-1.0
```


