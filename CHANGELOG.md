# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

*Changes in the next release*

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
