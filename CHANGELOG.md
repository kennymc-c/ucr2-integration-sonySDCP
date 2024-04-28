# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

*Changes in the next release*

### Added
- Added attributes puller function that checks all available integration attributes of the projector every 20 seconds by default. The interval can be changed in config.py. Set to 0 to deactivate this function.
- Added runtime storage to reduce config file access load
- Added missing SDCP error response messages in protocol.py


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
