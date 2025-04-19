# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-04-19

### Breaking Changes

#### ⚠️ Important: This is the final release of this integration and it is now deprecated

**Development will continue in form of the new [Sony ADCP integration](https://github.com/kennymc-c/ucr-integration-sonyADCP).**

- This integration is based on the more advanced ADCP protocol which supports more features and is easier to implement. The ADCP protocol is supported by most Sony home cinema projectors that were released since 2016
- It's advised to switch to this new integration as many things in the background have been improved in comparison to this integration.
- It also supports to control multiple devices at the same time and send native ADCP commands e.g. to send commands that are not exposed as simple commands or set a specific value for a setting.

### Added

- Added simple commands for advanced iris (lamp models) resp. dynamic control (laser models) and picture positions. These function are only supported by certain models and not all picture positions are supported by all models with this feature

### Fixed

- Removed "h" unit from the lamp sensor value string because previous firmware versions did't add the separate unit string in the remote ui. This has been fixed by UC as of firmware 2.2.2

### Changed

- The poller tasks will not be started if the media player and/or lamp timer are not a configured entity
- Changed the default integration icon from uc:camera to uc:projection. This new icon is only available from firmware 2.2.0 or newer

## [0.9.0] - 2024-12-11

### Breaking changes

- All modified pySDCP files have been moved to a separate python package called [pySDCP-extended](https://pypi.org/project/pysdcp-extended/)
  - Existing users running as an external integration need to update their requirements: ```pip3 install -r requirements.txt```

### Added

- Added a manual advanced setup option to change SDCP/SDAP ports, the PJ talk community and both poller intervals

## [0.8.0] - 2024-11-03

### Added

- Added a lamp timer sensor entity
  - The sensor value will be updated every time the projector is powered on or off by the remote and automatically every 30 minutes by default while the projector is powered on and the remote is not in sleep/standby mode or the integration is disconnected
- Added a remote entity
  - Advanced button mappings compared to the media player entity (see [Default remote entity button mappings](/README.md#default-remote-entity-button-mappings)) and remote ui pages with all available commands. Both can be customized in the web configurator under Remotes/External
  - Use command sequences in the activity editor instead of creating a macro for each sequence and map it to a button or add it to the ui grid i. All command names have to be in upper case and separated by a comma
  - Support for repeat, delay and hold
    - Hold just repeats the command continuously for the given hold time. There is no native hold function for the SDCP protocol as with some ir devices to activate additional functions
- Added 3 new simple commands:
  - INPUT_HDMI_1
  - INPUT_HDMI_2
  - MODE_HDR_TOGGLE (toggles between On and Off)

## [0.7.0] - 2024-09-20

### Breaking changes

- **🎉 This integration can now also run on the remote as a custom integration driver. From now on each release will have a tar.gz file attached that can be installed on the remote** (see [Run on the remote](/README.md#Run-on-the-remote-as-a-custom-integration-driver))
  - ⚠️ Running custom integrations on the remote is currently only available in beta firmware releases and requires version 1.9.2 or newer. Please keep in mind that due to the beta status there are missing firmware features that require workarounds (see link above) and that changes in future beta updates may temporarily or permanently break the functionality of this integration as a custom integration. Please wait until custom integrations are available in stable firmware releases if you don't want to take these risks.
- When running as an external integration driver the working directory when starting driver.py should now be the root of the repository. The path in docker-entry.sh has been adjusted. The configuration json file is therefore now created in the root of the integration directory. Existing users have to move config.json from the intg-sonysdcp directory

### Added

- Added build.yml Github action to automatically build a self-contained binary of the integration and create a release draft with the current driver version as a tag/name

### Changed

- Deactivate the attributes poller task when the integration runs on the remote as a custom integration driver.
  - The reason for this is to reduce battery consumption and save cpu/memory usage. Also this function is just needed if you control the projector alternating with a second device. In a future release this setting may also be adjustable in the integration setup.
- Due to the custom integration upload feature setup.json has been renamed to driver.json and moved to the root of the repository
- Corrected the semantic version scheme in driver.json (x.x to x.x.x)

## [0.6-beta] - 2024-05-11

### Added

- Added IP auto discovery. Just leave the ip text field empty in the setup process

### Changed

- No need to change the default SDAP advertisement interval anymore on the projector as the query function is now running asynchronously in a separate thread
  
### Fixed

- Replaced a variable reference log warning message with a clearer error description. This message appears if attributes of an entity should be updated that the remote has not yet subscribed to, e.g. shortly after the integration setup has been completed or if the integration configuration has been deleted just on the remote side.

## [0.5-beta] - 2024-05-05

### Changed

- Only update attribute if it differs from the value stored on the remote

### Fixed

- Fixed attributes poller not running due to a check against an API function that has not been implemented in the remote core (get_configured_entities)

## [0.4-beta] - 2024-05-03

### Added

- Added new simple commands for Motionflow, HDR, 2D/3D conversion & format, lamp control, input lag reduction & menu position
- Added attributes poller function that checks all available integration attributes of the projector every 20 seconds by default. The interval can be changed in config.py. Set to 0 to deactivate this function.
- Added runtime storage to reduce config file access load
- Added missing SDCP error response messages in protocol.py
  
### Changed

- The CURSOR_LEFT command has been mapped to the back command on the remote as in most cases this has the same function as a typical back command that the projector doesn't have

## [0.3-beta] - 2024-04-17

### Added

- Show pySDCP exception messages in log
- Show SDCP error response message according to Sony's documentation instead of just the error code

### Changed

- Split up setup flow and media player into separate files
- Optimize SDAP setup flow

## [0.2-beta] - 2024-04-04

### Breaking Changes

- Generate entity name from projector model name and entity id from model and serial number.
  - **This requires existing users to remove the integration on the remote, restart the integration and then run the setup process again. In existing activities/macros the old entity has to be removed and replaced by the new entity. Button mappings and on/off sequences have to be updated as well**
  - Note: The projector sends data only **every 30 seconds** by default and the interval should therefore be shortened to a minimum of 10 seconds in the web interface of the projector under _Setup/Advanced Menu/Advertisement/Interval_ to avoid timeouts to the remote and the integration. Otherwise the websocket connection to the remote could be reset if data is returned to slow to the integration which results in a spinning wheel in the setup flow.

### Added

- Optimize setup workflow and add a setup complete flag to config.json
- Use logging module instead of print()

### Fixed

- Added a missing comma that was causing two simple commands to show as a single command
- Fixed a naming problem for picture presets
- Corrected minimum WS Core API version in setup.json to 0.24.3. Previous version was a REST API version number

## [0.1-beta] - 2024-03-24

### Added

- Added Media Player entity
  - Features:
    - ON_OFF, TOGGLE, MUTE, UNMUTE, MUTE_TOGGLE, DPAD, HOME, SELECT_SOURCE
  - Attributes:
    - STATE, MUTED, SOURCE, SOURCE_LIST
  - Options:
    - SIMPLE_COMMANDS
      - LENS_SHIFT_UP, LENS_SHIFT_DOWN, LENS_SHIFT_LEFT, LENS_SHIFT_RIGHT, LENS_FOCUS_FAR, LENS_FOCUS_NEAR, LENS_ZOOM_LARGE, LENS_ZOOM_SMALL
      - MODE_ASPECT_RATIO_NORMAL, MODE_ASPECT_RATIO_V_STRETCH, MODE_ASPECT_RATIO_ZOOM_1_85, MODE_ASPECT_RATIO_ZOOM_2_35, MODE_ASPECT_RATIO_STRETCH, MODE_ASPECT_RATIO_SQUEEZE
      - MODE_PRESET_CINEMA_FILM_1, MODE_PRESET_CINEMA_FILM_2, MODE_PRESET_REF, MODE_PRESET_TV, MODE_PRESET_PHOTO, MODE_PRESET_GAME, MODE_PRESET_RIGHT_CINEMA, MODE_PRESET_BRIGHT_TV, MODE_PRESET_USER
- Added subscribe/unsubscribe, connect/disconnect and enter/exit standby event handlers
- Added infos to README.md
- Added requirements.txt and CHANGELOG.md

### Removed

- Removed alpha test button entity

### Changed

- Changed the minimum api version to 0.31.3 in setup.json to make sure that simple commands will work

## [0.0.1-alpha] - 2024-03-05

### Added

- First pre-release that only includes a button entity to open the projector menu
