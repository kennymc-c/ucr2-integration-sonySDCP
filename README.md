# Sony Projector integration for Unfolded Circle Remote Devices <!-- omit in toc -->

## ⚠️ Disclaimer ⚠️ <!-- omit in toc -->

This software may contain bugs that could affect system stability. Please use it at your own risk!

Integration for Unfolded Circle Remote Devices running [Unfolded OS](https://www.unfoldedcircle.com/unfolded-os) (currently [Remote Two](https://www.unfoldedcircle.com/remote-two) and the upcoming [Remote 3](https://www.unfoldedcircle.com)) to control Sony projectors that support the SDCP/PJ Talk protocol.

Using [uc-integration-api](https://github.com/aitatoi/integration-python-library)
and a modified and extended version of [pySDCP](https://github.com/Galala7/pySDCP) that is included in this repository.

## Table of Contents <!-- omit in toc -->

- [Entities](#entities)
  - [Planned features](#planned-features)
- [Commands \& attributes](#commands--attributes)
  - [Supported media player commands](#supported-media-player-commands)
  - [Supported media player attributes](#supported-media-player-attributes)
  - [Supported simple commands (media player \& remote entity)](#supported-simple-commands-media-player--remote-entity)
  - [Supported remote entity commands](#supported-remote-entity-commands)
  - [Default remote entity button mappings](#default-remote-entity-button-mappings)
  - [Attributes poller](#attributes-poller)
    - [Media player](#media-player)
    - [Lamp timer sensor](#lamp-timer-sensor)
- [Usage](#usage)
  - [Limitations](#limitations)
  - [Known supported projectors](#known-supported-projectors)
  - [Projector Setup](#projector-setup)
    - [Activate SDCP/PJTalk](#activate-sdcppjtalk)
    - [Change SDAP Interval (optional)](#change-sdap-interval-optional)
  - [Manual advanced setup](#manual-advanced-setup)
- [Installation](#installation)
  - [Run on the remote as a custom integration driver](#run-on-the-remote-as-a-custom-integration-driver)
    - [Limitations / Disclaimer](#limitations--disclaimer)
      - [Missing firmware features](#missing-firmware-features)
    - [Download integration driver](#download-integration-driver)
    - [Install the custom integration driver on the remote](#install-the-custom-integration-driver-on-the-remote)
  - [Run on a separate device as an external integration](#run-on-a-separate-device-as-an-external-integration)
    - [Requirements](#requirements)
    - [Bare metal/VM](#bare-metalvm)
    - [Requirements](#requirements-1)
      - [Start the integration](#start-the-integration)
    - [Docker container](#docker-container)
- [Build](#build)
  - [Build distribution binary](#build-distribution-binary)
    - [x86-64 Linux](#x86-64-linux)
    - [aarch64 Linux / Mac](#aarch64-linux--mac)
  - [Create tar.gz archive](#create-targz-archive)
- [Versioning](#versioning)
- [Changelog](#changelog)
- [Contributions](#contributions)
- [License](#license)

## Entities

- Media player
  - Source select feature to choose the input from a list
- Remote
  - Pre-defined buttons mappings and ui pages with all available commands that can be customized in the web configurator
  - Use command sequences in the activity editor instead of creating a macro for each sequence. All command names have to be in upper case and separated by a comma
  - Support for repeat, delay and hold
    - Hold just repeats the command continuously for the given hold time. There is no native hold function for the SDCP protocol as with some ir devices to activate additional functions
- Sensor
  - Lamp timer
    - Lamp hours will be updated every time the projector is powered on or off by the remote and automatically every 30 minutes (can be changed in config.py) while the projector is powered on and the remote is not in sleep/standby mode or the integration is disconnected

### Planned features

- Picture position and advanced iris commands
  - Needs testers as I only own a VPL-VW-270 that doesn't support lens memory and iris control
- Power/error status sensor entity

Additional smaller planned improvements are labeled with #TODO in the code

## Commands & attributes

### Supported media player commands

- Turn On/Off/Toggle
- Mute/Unmute/Toggle
  - Used for picture muting
- Cursor Up/Down/Left/Right/Enter
  - The back command is also mapped to cursor left as there is no separate back command for the projector. Inside the setup menu cursor left has the same function as a typical back command.
- Home
  - Opens the setup menu. Used instead of the menu feature because of the hard mapped home button when opening the entity from a profile page
- Source Select
  - HDMI 1, HDMI 2

### Supported media player attributes

- State (On, Off, Unknown)
- Muted (True, False)
- Source
- Source List (HDMI 1, HDMI 2)

### Supported simple commands (media player & remote entity)

- Input HDMI 1 & 2
  - Intended for the remote entity in addition to the source select feature of the media player entity
- Calibration Presets*
  - Cinema Film 1, Cinema Film 2, Reference, TV, Photo, Game, Bright Cinema, Bright TV, User
- Aspect Ratios*
  - Normal, Squeeze, Stretch**, V Stretch, Zoom 1:85, Zoom 2:35
- Motionfow*
  - Off, Smoth High, Smoth Low, Impulse\*\*\*, Combination\***, True Cinema
- HDR*
  - On, Off, Auto, Toggle
- 2D/3D Display Select**
  - 2D, 3D, Auto
- 3D Format**
  - Simulated 3D, Side-by-Side, Over-Under
- Lamp Control*
  - High, Low
- Input Lag Reduction*
  - On, Off
- Menu Position
  - Bottom Left, Center
- Lens Control
  - Lens Shift Up/Down/Left/Right
  - Lens Focus Far/Near
  - Lens Zoom Large/Small

\* _Only works if a video signal is present at the input_ \
\** _May not work work with all video signals. Please refer to Sony's user manual_ \
\*** _May not work on certain projector models that do not support this mode/feature. Please refer to Sony's user manual_

If a command can't be processed or applied by the projector this will result in a bad request error on the remote. The response error message from the projector is shown in the integration log

### Supported remote entity commands

- On, Off, Toggle
- Send command
  - Command names have to be in upper case and separated by a comma
- Send command sequence
  - All command names have to be in upper case and separated by a comma

### Default remote entity button mappings

_The default button mappings and ui pages can be customized in the web configurator under Remotes/External._

| Button                  | Short Press command | Long Press command |
|-------------------------|---------------------|--------------------|
| BACK                    | Cursor Left | |
| HOME                    | Menu |         |
| VOICE                   | Projector Info (Menu+Cursor Up) | Toggle HDR On/Off |
| VOLUME_UP/DOWN          | Lens Zoom Large/Small | Lens Focus Far/Near |
| MUTE                    | Toggle Picture Muting |         |
| DPAD_UP/DOWN/LEFT/RIGHT | Cursor Up/Down/Left/Right | Lens Shift Up/Down/Left/Right |
| DPAD_MIDDLE             | Cursor Enter |         |
| GREEN                   |              | Mode Preset Cinema Film 1 |
| YELLOW                  |              | Mode Preset Cinema Film 2 |
| RED                     |              | Mode Preset Bright TV |
| BLUE                    |              | Mode Preset Bright Cinema |
| CHANNEL_UP/DOWN         | Input HDMI 1/2 |         |
| PREV                    | Mode Preset Ref | Mode Preset Photo |
| PLAY                    | Mode Preset Game |         |
| NEXT                    | Mode Preset User | Mode Preset TV |
| POWER                   | Power Toggle |         |

### Attributes poller

#### Media player

By default the integration checks the status of all media player entity attributes every 20 seconds while the remote is not in standby/sleep mode or disconnected from the integration. The interval can be changed in the manual advanced setup. Set it to 0 to deactivate this function. When running on the remote as a custom integration the interval will be automatically set to 0 to reduce battery consumption and save cpu/memory usage.

#### Lamp timer sensor

The sensor value will be updated every time the projector is powered on or off by the remote and automatically every 30 minutes by default while the projector is powered on and the remote is not in sleep/standby mode or the integration is disconnected. The interval can be changed in the manual advanced setup.

## Usage

### Limitations

This integration supports one projector per integration instance. Multi device support is currently not planned for this integration but you could run the integration multiple times using different und unique driver IDs.

### Known supported projectors

Usually all Sony projectors that support the PJTalk / SDCP protocol should be supported.

The following models have been tested with either pySDCP or this integration by personal testing:

- VPL-HW65ES
- VPL-VW100
- VPL-VW260
- VPL-VW270
- VPL-VW285
- VPL-VW315
- VPL-VW320
- VPL-VW328
- VPL-VW365
- VPL-VW515
- VPL-VW520
- VPL-VW528
- VPL-VW665

Please inform me if you have a projector that is not on this list and it works with pySDCP or this integration

### Projector Setup

#### Activate SDCP/PJTalk

Open the projectors web interface and go to _Setup/Advanced Menu (left menu)/PJTalk_, activate the _Start PJ Talk Service_ checkbox and click on _Apply_.

![webinterface](webinterface.png)

#### Change SDAP Interval (optional)

During the initial setup the integration tries to query data from the projector via the SDAP advertisement protocol to generate a unique entity id. The default SDAP interval is 30 seconds. You can shorten the interval to a minimum value of 10 seconds under _Setup/Advanced Menu/Advertisement/Interval_.

![advertisement](advertisement.png)

### Manual advanced setup

If you have set the projector to use different pj talk ports or community than the standard values, you need to use the manual advanced setup option. Here you can change the ip address, sdcp/sdap port, pj talk community and the interval of both poller intervals. Please note that when running this integration on the remote the power/mute/input poller interval is always set to 0 to deactivate this poller in order to reduce battery consumption and save cpu/memory usage.

## Installation

### Run on the remote as a custom integration driver

#### Limitations / Disclaimer

⚠️ This feature is currently only available in beta firmware releases and requires version 1.9.2 or newer. Please keep in mind that due to the beta status there are missing firmware features that require workarounds (see below) and that changes in future beta updates may temporarily or permanently break the functionality of this integration as a custom integration. Please wait until custom integrations are available in stable firmware releases if you don't want to take these risks.

##### Missing firmware features

- The configuration file of custom integrations are not included in backups.
- You currently can't update custom integrations. You need to delete the integration from the integrations menu first and then re-upload the new version. Do not edit any activity or macros that includes entities from this integration after you removed the integration and wait until the new version has been uploaded and installed. You also need to add re-add entities to the main pages after the update as they are automatically removed. An update function will probably be added once the custom integrations feature will be available in stable firmware releases.

#### Download integration driver

Download the uc-intg-sonysdcp-x.x.x-aarch64.tar.gz archive in the assets section from the [latest release](https://github.com/kennymc-c/ucr2-integration-sonySDCP/releases/latest)

#### Install the custom integration driver on the remote

The custom integration driver installation is currently only possible via the Core API.

```shell
curl --location 'http://$IP/api/intg/install' \
--user 'web-configurator:$PIN' \
--form 'file=@"uc-intg-sonysdcp-$VERSION-aarch64.tar.gz"'
```

There is also a Core API GUI available at https://_Remote-IP_/doc/core-rest. Click on Authorize to log in (username: web-configurator, password: your PIN), scroll down to POST intg/install, click on Try it out, choose a file and then click on Execute.

Alternatively you can also use the inofficial [UC Remote Toolkit](https://github.com/albaintor/UC-Remote-Two-Toolkit)

UC plans to integrate the upload function to the web configurator once they get enough positive feedback from developers (and users). The current status can be tracked in this issue: [#79](https://github.com/unfoldedcircle/feature-and-bug-tracker/issues/79).

### Run on a separate device as an external integration

#### Requirements

- Firmware 1.7.12 or newer to support simple commands and remote entities

#### Bare metal/VM

#### Requirements

- Python 3.11
- Install Libraries:  
  (using a [virtual environment](https://docs.python.org/3/library/venv.html) is highly recommended)

```shell
pip3 install -r requirements.txt
```

##### Start the integration

```shell
python3 intg-sonysdcp/driver.py
```

#### Docker container

For the mDNS advertisement to work correctly it's advised to start the integration in the host network (`--net=host`). You can also set the websocket listening port with the environment variable `UC_INTEGRATION_HTTP_PORT`, set the listening interface with `UC_INTEGRATION_INTERFACE` or change the default debug log level with `UC_LOG_LEVEL`. See available [environment variables](https://github.com/unfoldedcircle/integration-python-library#environment-variables)
in the Python integration library.

All data is mounted to `/usr/src/app`:

```shell
docker run --net=host -n 'ucr2-integration-sonysdcp' -v './ucr2-integration-sonySDCP':'/usr/src/app/':'rw' 'python:3.11' /usr/src/app/docker-entry.sh
```

## Build

Instead of downloading the integration driver archive from the release assets you can also build and create the needed distribution binary and tar.gz archive yourself.

For Python based integrations Unfolded Circle recommends to use `pyinstaller` to create a distribution binary that has everything in it, including the Python runtime and all required modules and native libraries.

### Build distribution binary

First we need to compile the driver on the target architecture because `pyinstaller` does not support cross compilation.

The `--onefile` option to create a one-file bundled executable should be avoided:

- Higher startup cost, since the wrapper binary must first extract the archive.
- Files are extracted to the /tmp directory on the device, which is an in-memory filesystem.  
  This will further reduce the available memory for the integration drivers!

We use the `--onedir` option instead.

#### x86-64 Linux

On x86-64 Linux we need Qemu to emulate the aarch64 target platform:

```bash
sudo apt install qemu binfmt-support qemu-user-static
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

Run pyinstaller:

```shell
docker run --rm --name builder \
    --platform=aarch64 \
    --user=$(id -u):$(id -g) \
    -v "$PWD":/workspace \
    docker.io/unfoldedcircle/r2-pyinstaller:3.11.6-0.2.0  \
    bash -c \
      "cd /workspace && \
      python -m pip install -r requirements.txt && \
      pyinstaller --clean --onedir --name int-sonysdcp intg-sonysdcp/driver.py"
```

#### aarch64 Linux / Mac

On an aarch64 host platform, the build image can be run directly (and much faster):

```shell
docker run --rm --name builder \
    --user=$(id -u):$(id -g) \
    -v "$PWD":/workspace \
    docker.io/unfoldedcircle/r2-pyinstaller:3.11.6-0.2.0  \
    bash -c \
      "cd /workspace && \
      python -m pip install -r requirements.txt && \
      pyinstaller --clean --onedir --name intg-sonysdcp intg-sonysdcp/driver.py"
```

### Create tar.gz archive

Now we need to create the tar.gz archive that can be installed on the remote and contains the driver.json metadata file and the driver distribution binary inside the bin directory

```shell
mkdir -p artifacts/bin
mv dist/intg-sonysdcp/* artifacts/bin
mv artifacts/bin/intg-sonysdcp artifacts/bin/driver
cp driver.json artifacts/
tar czvf uc-intg-sonysdcp-aarch64.tar.gz -C artifacts .
rm -r dist build artifacts intg-sonysdcp.spec
```

## Versioning

I use [SemVer](http://semver.org/) for versioning. For the versions available, see the
[tags and releases in this repository](https://github.com/kennymc-c/ucr2-integration-sonySDCP/releases).

## Changelog

The major changes found in each new release are listed in the [changelog](CHANGELOG.md)
and under the GitHub [releases](/releases).

## Contributions

Contributions to add new feature, implement #TODOs from the code or improve the code quality and stability are welcome! First check whether there are other branches in this repository that maybe already include your feature. If not, please fork this repository first and then create a pull request to merge your commits and explain what you want to change or add.

## License

This project is licensed under the [**GNU GENERAL PUBLIC LICENSE**](https://choosealicense.com/licenses/gpl-3.0/).
See the [LICENSE](LICENSE) file for details.
