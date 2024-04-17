#!/usr/bin/env python3

import asyncio
import logging
from typing import Any

import ucapi
import pysdcp
from pysdcp.protocol import *

import driver
import setup

_LOG = logging.getLogger(__name__)


async def add_mp(ip: str, id: str, name: str):

    features = [
        ucapi.media_player.Features.ON_OFF, 
        ucapi.media_player.Features.TOGGLE, 
        ucapi.media_player.Features.MUTE,
        ucapi.media_player.Features.UNMUTE,
        ucapi.media_player.Features.MUTE_TOGGLE,
        ucapi.media_player.Features.DPAD, 
        ucapi.media_player.Features.HOME, 
        ucapi.media_player.Features.SELECT_SOURCE
        ]

    definition = ucapi.MediaPlayer(
        id, 
        name, 
        features, 
        attributes={
            ucapi.media_player.Attributes.STATE: ucapi.media_player.States.UNKNOWN, 
            ucapi.media_player.Attributes.MUTED: False,
            ucapi.media_player.Attributes.SOURCE: "", 
            ucapi.media_player.Attributes.SOURCE_LIST: ["HDMI 1", "HDMI 2"]
        },
        device_class=ucapi.media_player.DeviceClasses.TV, 
        options={
            ucapi.media_player.Options.SIMPLE_COMMANDS: [
                "MODE_PRESET_REF",
                "MODE_PRESET_USER",
                "MODE_PRESET_TV",
                "MODE_PRESET_PHOTO",
                "MODE_PRESET_GAME",
                "MODE_PRESET_BRIGHT_CINEMA",
                "MODE_PRESET_BRIGHT_TV",
                "MODE_PRESET_CINEMA_FILM_1",
                "MODE_PRESET_CINEMA_FILM_2",
                "MODE_ASPECT_RATIO_NORMAL",
                "MODE_ASPECT_RATIO_ZOOM_1_85",
                "MODE_ASPECT_RATIO_ZOOM_2_35",
                "MODE_ASPECT_RATIO_V_STRETCH",
                "MODE_ASPECT_RATIO_SQUEEZE",
                "MODE_ASPECT_RATIO_STRETCH",
                "LENS_SHIFT_UP",
                "LENS_SHIFT_DOWN",
                "LENS_SHIFT_LEFT",
                "LENS_SHIFT_RIGHT",
                "LENS_FOCUS_FAR",
                "LENS_FOCUS_NEAR",
                "LENS_ZOOM_LARGE",
                "LENS_ZOOM_SMALL",
            ]
        },
        cmd_handler=driver.mp_cmd_handler
    )

    _LOG.debug("Entity definition created")

    driver.api.available_entities.add(definition)

    _LOG.info("Added media player entity")



def mp_cmd_assigner(id: str, cmd_name: str, params: dict[str, Any] | None, ip: str):
    
    projector = pysdcp.Projector(ip)

    def cmd_error(msg: str = None):
        if msg == None:
            _LOG.error("Error while executing the command: " + cmd_name)
            return ucapi.StatusCodes.SERVER_ERROR
        else:
            _LOG.error(msg)
            return ucapi.StatusCodes.BAD_REQUEST

    #TODO Find a get command that shows the status of the current input signal to prevent errors for commands like aspect ratio and picture preset that don't work without a input signal. Probably better implement this in pySDC itself

    match cmd_name:

        case ucapi.media_player.Commands.ON:
            try:
                if projector.set_power(True):
                    driver.api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.ON})
                    return ucapi.StatusCodes.OK
                else:
                    return cmd_error()
            except Exception or ConnectionError as e:
                return cmd_error(e)
            
        case ucapi.media_player.Commands.OFF:
            try:
                if projector.set_power(False):
                    driver.api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF})
                    return ucapi.StatusCodes.OK
                else:
                    return cmd_error()
            except Exception or ConnectionError as e:
                return cmd_error(e)

        case ucapi.media_player.Commands.TOGGLE:
            try:
                if projector.get_power() == True:
                    if projector.set_power(False):
                        driver.api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF})
                        return ucapi.StatusCodes.OK
                    else:
                        return cmd_error()
                elif projector.get_power() == False:
                    if projector.set_power(True):
                        driver.api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.ON})
                        return ucapi.StatusCodes.OK
                    else:
                        return cmd_error()
                else:
                    return cmd_error()
            except Exception or ConnectionError as e:
                return cmd_error(e)

        case ucapi.media_player.Commands.MUTE_TOGGLE:
            try:
                if projector.get_muting() == True:
                    if projector.set_muting(False):
                        driver.api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.MUTED: False})
                        return ucapi.StatusCodes.OK
                    else:
                        return cmd_error()
                elif projector.get_muting() == False:
                    if projector.set_muting(True):
                        driver.api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.MUTED: True})
                        return ucapi.StatusCodes.OK
                    else:
                        return cmd_error()
                else:
                    return cmd_error()
            except Exception or ConnectionError as e:
                return cmd_error(e)

        case ucapi.media_player.Commands.MUTE:
            try:
                if projector.set_muting(True):
                    driver.api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.MUTED: True})
                    return ucapi.StatusCodes.OK
                else:
                    return cmd_error()
            except Exception or ConnectionError as e:
                return cmd_error(e)
        
        case ucapi.media_player.Commands.UNMUTE:
            try:
                if projector.set_muting(False):
                    driver.api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.MUTED: False})
                    return ucapi.StatusCodes.OK
                else:
                    return cmd_error()
            except Exception or ConnectionError as e:
                return cmd_error(e)
        
        case ucapi.media_player.Commands.HOME:
            try:
                projector._send_command(action=ACTIONS["SET"], command=COMMANDS_IR["MENU"])
                return ucapi.StatusCodes.OK
            except Exception or ConnectionError as e:
                return cmd_error(e)

        case ucapi.media_player.Commands.SELECT_SOURCE:
            source = params["source"]
            try:
                if source == "HDMI 1":
                    if projector.set_HDMI_input(1):
                        driver.api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.SOURCE: source})
                        return ucapi.StatusCodes.OK
                    else:
                        return cmd_error()
                elif source == "HDMI 2":
                    if projector.set_HDMI_input(2):
                        driver.api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.SOURCE: source})
                        return ucapi.StatusCodes.OK
                    else:
                        return cmd_error()
                else:
                    _LOG.error("Unknown source: " + source)
                    return ucapi.StatusCodes.BAD_REQUEST
            except Exception or ConnectionError as e:
                return cmd_error(e)

        case \
            "MODE_ASPECT_RATIO_NORMAL" | \
            "MODE_ASPECT_RATIO_V_STRETCH" | \
            "MODE_ASPECT_RATIO_ZOOM_1_85" | \
            "MODE_ASPECT_RATIO_ZOOM_2_35" | \
            "MODE_ASPECT_RATIO_STRETCH" | \
            "MODE_ASPECT_RATIO_SQUEEZE":
                aspect = cmd_name.replace("MODE_ASPECT_RATIO_", "")
                try:
                    if projector.set_aspect(aspect):
                        return ucapi.StatusCodes.OK
                    else:
                        return cmd_error()
                except Exception or ConnectionError as e:
                    return cmd_error(e)
                
        case \
                "MODE_PRESET_CINEMA_FILM_1" | \
                "MODE_PRESET_CINEMA_FILM_2" | \
                "MODE_PRESET_REF" | \
                "MODE_PRESET_TV" | \
                "MODE_PRESET_PHOTO" | \
                "MODE_PRESET_GAME" | \
                "MODE_PRESET_BRIGHT_CINEMA" | \
                "MODE_PRESET_BRIGHT_TV" | \
                "MODE_PRESET_USER":
                try:
                    preset = cmd_name.replace("MODE_PRESET_", "")
                    if projector.set_preset(preset):
                        return ucapi.StatusCodes.OK
                    else:
                        return cmd_error()
                except Exception or ConnectionError as e:
                    return cmd_error(e)

        case \
            ucapi.media_player.Commands.CURSOR_ENTER | \
            ucapi.media_player.Commands.CURSOR_UP | \
            ucapi.media_player.Commands.CURSOR_DOWN | \
            ucapi.media_player.Commands.CURSOR_LEFT | \
            ucapi.media_player.Commands.CURSOR_RIGHT | \
            "LENS_SHIFT_UP" | \
            "LENS_SHIFT_DOWN" | \
            "LENS_SHIFT_LEFT" | \
            "LENS_SHIFT_RIGHT" | \
            "LENS_FOCUS_FAR" | \
            "LENS_FOCUS_NEAR" | \
            "LENS_ZOOM_LARGE" | \
            "LENS_ZOOM_SMALL":
                try:
                    projector._send_command(action=ACTIONS["SET"], command=COMMANDS_IR[cmd_name.upper()])
                    return ucapi.StatusCodes.OK
                except Exception or ConnectionError as e:
                    return cmd_error(e)
        
        case _:
            _LOG.error("Command not implemented: " + cmd_name)
            return ucapi.StatusCodes.NOT_IMPLEMENTED