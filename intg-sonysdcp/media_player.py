#!/usr/bin/env python3

import asyncio
import logging
from typing import Any
import json

import ucapi
import pysdcp
from pysdcp.protocol import *

import config
import driver
import setup

_LOG = logging.getLogger(__name__)


def get_attr_power(ip: str):
    projector = pysdcp.Projector(ip)
    try:
        if projector.get_power() == True:
            return ucapi.media_player.States.ON
        else:
            return ucapi.media_player.States.OFF
    except Exception or ConnectionError as e:
        _LOG.error(e)
        _LOG.warning("Can't get power status from projector. Set to Unknown")
        return ucapi.media_player.States.UNKNOWN
    
def get_attr_muted(ip: str):
    projector = pysdcp.Projector(ip)
    try:
        if projector.get_muting() == True:
            return True
        else:
            return False
    except Exception or ConnectionError as e:
        _LOG.error(e)
        _LOG.warning("Can't get mute status from projector. Set to False")
        return False
    
def get_attr_source(ip: str):
    projector = pysdcp.Projector(ip)
    try:
        return projector.get_input()
    except Exception or ConnectionError as e:
        _LOG.error(e)
        _LOG.warning("Can't get input from projector. Set to None")
        return None
    


async def update_attributes(id: str):

    ip = config.setup.get("ip")

    try:
        state = get_attr_power(ip)
        muted = get_attr_muted(ip)
        source = get_attr_source(ip)
    except Exception as e:
        raise Exception(e)
    
    stored_states = await driver.api.configured_entities.get_states()
    for entity in stored_states:
        attributes_stored = entity["attributes"]

    stored_attributes = {"state": attributes_stored["state"], "muted": attributes_stored["muted"], "source": attributes_stored["source"]}
    current_attributes = {"state": state, "muted": muted, "source": source}

    attributes_to_check = ["state", "muted", "source"]
    attributes_to_update = []
    attributes_to_skip = []

    for attribute in attributes_to_check:
        if current_attributes[attribute] != stored_attributes[attribute]:
            attributes_to_update.append(attribute)
        else:
            attributes_to_skip.append(attribute)

    if attributes_to_skip != []:
        _LOG.debug("Entity attributes for " + str(attributes_to_skip) + " have not changed since the last update")

    if attributes_to_update != []:
        attributes_to_send = {}
        if "state" in attributes_to_update:
            attributes_to_send.update({ucapi.media_player.Attributes.STATE: state})
        if "muted" in attributes_to_update:
            attributes_to_send.update({ucapi.media_player.Attributes.MUTED: muted})
        if "source" in attributes_to_update:
            attributes_to_send.update({ucapi.media_player.Attributes.SOURCE: source})

        try:
            driver.api.configured_entities.update_attributes(id, attributes_to_send)
            _LOG.info("Updated entity attributes " + str(attributes_to_update) + " for " + id)
        except:
            raise Exception("Error while updating attributes for entity id " + id)
    else:
        _LOG.info("No entity attributes to update")
    


async def add_mp(id: str, name: str):

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
                "MODE_MOTIONFLOW_OFF",
                "MODE_MOTIONFLOW_SMOTH_HIGH",
                "MODE_MOTIONFLOW_SMOTH_LOW",
                "MODE_MOTIONFLOW_IMPULSE",
                "MODE_MOTIONFLOW_COMBINATION",
                "MODE_MOTIONFLOW_TRUE_CINEMA",
                "MODE_HDR_ON",
                "MODE_HDR_OFF",
                "MODE_HDR_AUTO",
                "MODE_2D_3D_SELECT_AUTO",
                "MODE_2D_3D_SELECT_3D",
                "MODE_2D_3D_SELECT_2D",
                "MODE_3D_FORMAT_SIMULATED_3D",
                "MODE_3D_FORMAT_SIDE_BY_SIDE",
                "MODE_3D_FORMAT_OVER_UNDER",
                "LAMP_CONTROL_LOW",
                "LAMP_CONTROL_HIGH",
                "INPUT_LAG_REDUCTION_ON",
                "INPUT_LAG_REDUCTION_OFF",
                "MENU_POSITION_BOTTOM_LEFT",
                "MENU_POSITION_CENTER",
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

    #TODO If all commands from protocol.py have been implemented into pySDCP as separate commands create a upstream pull request and remove pySDCP files when it has been merged

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
            
        case \
            ucapi.media_player.Commands.BACK:
                try:
                    projector._send_command(action=ACTIONS["SET"], command=COMMANDS_IR["CURSOR_LEFT"])
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
                    projector._send_command(action=ACTIONS["SET"], command=COMMANDS["ASPECT_RATIO"], data=ASPECT_RATIOS[aspect])
                except Exception or ConnectionError as e:
                    return cmd_error(e)
                return ucapi.StatusCodes.OK
                
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
            preset = cmd_name.replace("MODE_PRESET_", "")
            try:
                projector._send_command(action=ACTIONS["SET"], command=COMMANDS["CALIBRATION_PRESET"], data=CALIBRATION_PRESETS[preset])
            except Exception or ConnectionError as e:
                return cmd_error(e)
            return ucapi.StatusCodes.OK
        
        case \
            "MODE_MOTIONFLOW_OFF" | \
            "MODE_MOTIONFLOW_SMOTH_HIGH" | \
            "MODE_MOTIONFLOW_SMOTH_LOW" | \
            "MODE_MOTIONFLOW_IMPULSE" | \
            "MODE_MOTIONFLOW_COMBINATION" | \
            "MODE_MOTIONFLOW_TRUE_CINEMA":
            preset = cmd_name.replace("MODE_MOTIONFLOW_", "")
            try:
                projector._send_command(action=ACTIONS["SET"], command=COMMANDS["MOTIONFLOW"], data=MOTIONFLOW[preset])
            except Exception or ConnectionError as e:
                return cmd_error(e)
            return ucapi.StatusCodes.OK
        
        case \
            "MODE_HDR_ON" | \
            "MODE_HDR_OFF" | \
            "MODE_HDR_AUTO":
            preset = cmd_name.replace("MODE_HDR_", "")
            try:
                projector._send_command(action=ACTIONS["SET"], command=COMMANDS["HDR"], data=HDR[preset])
            except Exception or ConnectionError as e:
                return cmd_error(e)
            return ucapi.StatusCodes.OK
        
        case \
            "MODE_2D_3D_SELECT_AUTO" | \
            "MODE_2D_3D_SELECT_3D" | \
            "MODE_2D_3D_SELECT_2D":
            preset = cmd_name.replace("MODE_2D_3D_SELECT_", "")
            try:
                projector._send_command(action=ACTIONS["SET"], command=COMMANDS["2D_3D_DISPLAY_SELECT"], data=TWO_D_THREE_D_SELECT[preset])
            except Exception or ConnectionError as e:
                return cmd_error(e)
            return ucapi.StatusCodes.OK

        case \
            "MODE_3D_FORMAT_SIMULATED_3D" | \
            "MODE_3D_FORMAT_SIDE_BY_SIDE" | \
            "MODE_3D_FORMAT_OVER_UNDER":
            preset = cmd_name.replace("MODE_3D_FORMAT_", "")
            try:
                projector._send_command(action=ACTIONS["SET"], command=COMMANDS["3D_FORMAT"], data=THREE_D_FORMATS[preset])
            except Exception or ConnectionError as e:
                return cmd_error(e)
            return ucapi.StatusCodes.OK
        
        
        case \
            "LAMP_CONTROL_LOW" | \
            "LAMP_CONTROL_HIGH":
            preset = cmd_name.replace("LAMP_CONTROL_", "")
            try:
                projector._send_command(action=ACTIONS["SET"], command=COMMANDS["LAMP_CONTROL"], data=LAMP_CONTROL[preset])
            except Exception or ConnectionError as e:
                return cmd_error(e)
            return ucapi.StatusCodes.OK

        case \
            "INPUT_LAG_REDUCTION_ON" | \
            "INPUT_LAG_REDUCTION_OFF":
            preset = cmd_name.replace("INPUT_LAG_REDUCTION_", "")
            try:
                projector._send_command(action=ACTIONS["SET"], command=COMMANDS["INPUT_LAG_REDUCTION"], data=INPUT_LAG_REDUCTION[preset])
            except Exception or ConnectionError as e:
                return cmd_error(e)
            return ucapi.StatusCodes.OK
        
        case \
            "MENU_POSITION_BOTTOM_LEFT" | \
            "MENU_POSITION_CENTER":
            preset = cmd_name.replace("MENU_POSITION_", "")
            try:
                projector._send_command(action=ACTIONS["SET"], command=COMMANDS["MENU_POSITION"], data=MENU_POSITIONS[preset])
            except Exception or ConnectionError as e:
                return cmd_error(e)
            return ucapi.StatusCodes.OK

        #TODO Beneficial for a DIY lens memory function: Lens shift up/down/left/right max + lens zoom large/small max simple commands to move lens faster than with slower remote command repeat function on the remote

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