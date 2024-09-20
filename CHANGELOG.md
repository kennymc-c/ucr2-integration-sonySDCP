# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

*Changes in the next release*

## [0.7.0-beta] - 2024-09-20

### Breaking changes
- **🎉 This integration can now also run on the remote as a custom integration driver. From now on each release will have a tar.gz file attached that can be installed on the remote** (see [Run on the remote](/README.md#Run-on-the-remote-as-a-custom-integration-driver))
  - ⚠️ Running custom integrations on the remote is currently only available in beta firmware releases and requires version 1.9.2 or newer. Please keep in mind that due to the beta status there are missing firmware features that require workarounds (see link above) and that changes in future beta updates may temporarily or permanently break the functionality of this integration as a custom integration. Please wait until custom integrations are available in stable firmware releases if you don't want to take these risks.
- When running as an external integration driver the working directory when starting driver.py should now be the root of the repository. The path in docker-entry.sh has been adjusted. The configuration json file is therefore now created in the root of the integration directory. Existing users have to move config.json from the intg-sonysdcp directory
 
### Added
- Add build.yml Github action to automatically build a self-contained binary of the integration and create a release draft with the current driver version as a tag/name

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
