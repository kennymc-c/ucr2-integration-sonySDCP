#!/usr/bin/env python3

"""Module that includes functions to add a remote entity with all available commands from the media player entity"""

import asyncio
import logging
from typing import Any
import time

import ucapi
import ucapi.ui
from pysdcp.protocol import *

import driver
import config
import projector

_LOG = logging.getLogger(__name__)



async def update_rt(entity_id: str, ip: str):
    """Retrieve input source, power state and muted state from the projector, compare them with the known state on the remote and update them if necessary"""

    try:
        state = projector.get_attr_power(ip)
    except Exception as e:
        _LOG.error(e)
        _LOG.warning("Can't get power status from projector. Set to Unavailable")
        state = {ucapi.remote.Attributes.STATE: ucapi.remote.States.UNAVAILABLE}

    try:
        api_update_attributes = driver.api.configured_entities.update_attributes(entity_id, state)
    except Exception as e:
        raise Exception("Error while updating state attribute for entity id " + entity_id) from e

    if not api_update_attributes:
        raise Exception("Entity " + entity_id + " not found. Please make sure it's added as a configured entity on the remote")
    else:
        _LOG.info("Updated remote entity state attribute to " + str(state) + " for " + entity_id)



async def remote_cmd_handler(
    entity: ucapi.Remote, cmd_id: str, params: dict[str, Any] | None
) -> ucapi.StatusCodes:
    """
    Remote command handler.

    Called by the integration-API if a command is sent to a configured remote-entity.

    :param entity: remote entity
    :param cmd_id: command
    :param params: optional command parameters
    :return: status of the command
    """

    if params is None:
        _LOG.info(f"Received {cmd_id} command for {entity.id}")
    else:
        _LOG.info(f"Received {cmd_id} command with parameter {params} for {entity.id}")
        repeat = params.get("repeat")
        delay = params.get("delay")
        hold = params.get("hold")

        if hold is None or hold == "":
            hold = 0
        if repeat is None:
            repeat = 1
        if delay is None:
            delay = 0
        else:
            delay = delay / 1000 #Convert milliseconds to seconds for sleep

        if repeat == 1 and delay != 0:
            _LOG.info(str(delay) + " seconds delay will be ignored as the command will not be repeated (repeat = 1)")
            delay = 0

    try:
        ip = config.Setup.get("ip")
    except ValueError as v:
        _LOG.error(v)
        return ucapi.StatusCodes.SERVER_ERROR

    match cmd_id:

        case \
            ucapi.remote.Commands.ON | \
            ucapi.remote.Commands.OFF | \
            ucapi.remote.Commands.TOGGLE:
            try:
                await projector.send_cmd(entity.id, ip, cmd_id)
            except Exception as e:
                if e is None:
                    return ucapi.StatusCodes.SERVER_ERROR
                return ucapi.StatusCodes.BAD_REQUEST
            return ucapi.StatusCodes.OK

        case \
            ucapi.remote.Commands.SEND_CMD:

            command = params.get("command")

            try:
                i = 0
                r = range(repeat)
                for i in r:
                    i = i+1
                    if repeat != 1:
                        _LOG.debug("Round " + str(i) + " for command " + command)
                    if hold != 0:
                        cmd_start = time.time()*1000
                        while time.time()*1000 - cmd_start < hold:
                            await projector.send_cmd(entity.id, ip, command)
                            await asyncio.sleep(0)
                    else:
                        await projector.send_cmd(entity.id, ip, command)
                        await asyncio.sleep(0)
                    await asyncio.sleep(delay)
            except Exception as e:
                if repeat != 1:
                    _LOG.warning("Execution of the command " + command + " failed. Remaining " + str(repeat-1) + " repetitions will no longer be executed")
                if e is None:
                    return ucapi.StatusCodes.SERVER_ERROR
                return ucapi.StatusCodes.BAD_REQUEST

            return ucapi.StatusCodes.OK

        case \
            ucapi.remote.Commands.SEND_CMD_SEQUENCE:

            sequence = params.get("sequence")

            _LOG.info(f"Command sequence: {sequence}")

            for command in sequence:
                _LOG.debug("Sending command: " + command)
                try:
                    i = 0
                    r = range(repeat)
                    for i in r:
                        i = i+1
                        if repeat != 1:
                            _LOG.debug("Round " + str(i) + " for command " + command)
                        if hold != 0:
                            cmd_start = time.time()*1000
                            while time.time()*1000 - cmd_start < hold:
                                await projector.send_cmd(entity.id, ip, command)
                                await asyncio.sleep(0)
                        else:
                            await projector.send_cmd(entity.id, ip, command)
                            await asyncio.sleep(0)
                        await asyncio.sleep(delay)
                except Exception as e:
                    if repeat != 1:
                        _LOG.warning("Execution of the command " + command + " failed. Remaining " + str(repeat-1) + " repetitions will no longer be executed")
                    if e is None:
                        return ucapi.StatusCodes.SERVER_ERROR
                    return ucapi.StatusCodes.BAD_REQUEST

            return ucapi.StatusCodes.OK

        case _:

            _LOG.info(f"Unsupported command: {cmd_id} for {entity.id}")
            return ucapi.StatusCodes.BAD_REQUEST



def create_button_mappings() -> list[ucapi.ui.DeviceButtonMapping | dict[str, Any]]:
    """Create the button mapping of the remote entity"""
    return [
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.BACK, "BACK"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.HOME, "MENU"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.VOICE, ucapi.remote.create_sequence_cmd(["MENU","CURSOR_UP"]), "MODE_HDR_TOGGLE"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.VOLUME_UP, "LENS_ZOOM_LARGE", "LENS_FOCUS_NEAR"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.VOLUME_DOWN, "LENS_ZOOM_SMALL", "LENS_FOCUS_FAR"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.MUTE, "PICTURE_MUTING_TOGGLE"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.DPAD_UP, "CURSOR_UP", "LENS_SHIFT_UP"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.DPAD_DOWN, "CURSOR_DOWN", "LENS_SHIFT_DOWN"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.DPAD_LEFT, "CURSOR_LEFT", "LENS_SHIFT_LEFT"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.DPAD_RIGHT, "CURSOR_RIGHT", "LENS_SHIFT_RIGHT"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.DPAD_MIDDLE, "CURSOR_ENTER"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.GREEN, "", "MODE_PRESET_CINEMA_FILM_1"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.YELLOW, "", "MODE_PRESET_CINEMA_FILM_2"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.RED, "", "MODE_PRESET_BRIGHT_TV"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.BLUE, "", "MODE_PRESET_BRIGHT_CINEMA"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.CHANNEL_DOWN, "INPUT_HDMI_1"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.CHANNEL_UP, "INPUT_HDMI_2"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.PREV, "MODE_PRESET_REF", "MODE_PRESET_PHOTO"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.PLAY, "MODE_PRESET_GAME"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.NEXT, "MODE_PRESET_USER", "MODE_PRESET_TV"),
        ucapi.ui.create_btn_mapping(ucapi.ui.Buttons.POWER, ucapi.remote.Commands.TOGGLE),
    ]



def create_ui_pages() -> list[ucapi.ui.UiPage | dict[str, Any]]:
    """Create a user interface with different pages that includes all commands"""

    ui_page1 = ucapi.ui.UiPage("page1", "Power, Inputs & HDR", grid=ucapi.ui.Size(6, 6))
    ui_page1.add(ucapi.ui.create_ui_text("On", 0, 0, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.Commands.ON))
    ui_page1.add(ucapi.ui.create_ui_text("Off", 2, 0, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.Commands.OFF))
    ui_page1.add(ucapi.ui.create_ui_icon("uc:button", 4, 0, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.Commands.TOGGLE))
    ui_page1.add(ucapi.ui.create_ui_icon("uc:info", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_sequence_cmd(["MENU","CURSOR_UP"])))
    ui_page1.add(ucapi.ui.create_ui_text("HDMI 1", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("INPUT_HDMI_1")))
    ui_page1.add(ucapi.ui.create_ui_text("HDMI 2", 4, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("INPUT_HDMI_2")))
    ui_page1.add(ucapi.ui.create_ui_text("-- HDR --", 0, 2, size=ucapi.ui.Size(6, 1)))
    ui_page1.add(ucapi.ui.create_ui_text("On", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_HDR_ON")))
    ui_page1.add(ucapi.ui.create_ui_text("Off", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_HDR_OFF")))
    ui_page1.add(ucapi.ui.create_ui_text("Auto", 4, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_HDR_AUTO")))

    ui_page2 = ucapi.ui.UiPage("page2", "Picture Modes")
    ui_page2.add(ucapi.ui.create_ui_text("-- Picture Modes --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page2.add(ucapi.ui.create_ui_text("Cinema Film 1", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_PRESET_CINEMA_FILM_1")))
    ui_page2.add(ucapi.ui.create_ui_text("Cinema Film 2", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_PRESET_CINEMA_FILM_1")))
    ui_page2.add(ucapi.ui.create_ui_text("Reference", 0, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_PRESET_REF")))
    ui_page2.add(ucapi.ui.create_ui_text("Game", 2, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_PRESET_GAME")))
    ui_page2.add(ucapi.ui.create_ui_text("TV", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_PRESET_TV")))
    ui_page2.add(ucapi.ui.create_ui_text("Bright TV", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_PRESET_BRIGHT_TV")))
    ui_page2.add(ucapi.ui.create_ui_text("Bright Cinema", 0, 4, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_PRESET_BRIGHT_CINEMA")))
    ui_page2.add(ucapi.ui.create_ui_text("Photo", 2, 4, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_PRESET_PHOTO")))
    ui_page2.add(ucapi.ui.create_ui_text("User", 1, 5, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_PRESET_USER")))

    ui_page3 = ucapi.ui.UiPage("page3", "Aspect Ratios")
    ui_page3.add(ucapi.ui.create_ui_text("-- Aspect Ratios --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page3.add(ucapi.ui.create_ui_text("Normal", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_ASPECT_RATIO_NORMAL")))
    ui_page3.add(ucapi.ui.create_ui_text("Squeeze", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_ASPECT_RATIO_SQUEEZE")))
    ui_page3.add(ucapi.ui.create_ui_text("Stretch", 0, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_ASPECT_RATIO_STRETCH")))
    ui_page3.add(ucapi.ui.create_ui_text("V Stretch", 2, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_ASPECT_RATIO_V_STRETCH")))
    ui_page3.add(ucapi.ui.create_ui_text("Zoom 1:85", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_ASPECT_RATIO_ZOOM_1_85")))
    ui_page3.add(ucapi.ui.create_ui_text("Zoom 2:35", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_ASPECT_RATIO_ZOOM_2_35")))

    ui_page4 = ucapi.ui.UiPage("page4", "Motionflow")
    ui_page4.add(ucapi.ui.create_ui_text("-- Motionflow --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page4.add(ucapi.ui.create_ui_text("Off", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_MOTIONFLOW_OFF")))
    ui_page4.add(ucapi.ui.create_ui_text("True Cinema", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_MOTIONFLOW_TRUE_CINEMA")))
    ui_page4.add(ucapi.ui.create_ui_text("Smoth High", 0, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_MOTIONFLOW_SMOTH_HIGH")))
    ui_page4.add(ucapi.ui.create_ui_text("Smoth Low", 2, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_MOTIONFLOW_SMOTH_LOW")))
    ui_page4.add(ucapi.ui.create_ui_text("Impulse", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_MOTIONFLOW_IMPULSE")))
    ui_page4.add(ucapi.ui.create_ui_text("Combination", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_MOTIONFLOW_COMBINATION")))

    ui_page5 = ucapi.ui.UiPage("page5", "2D / 3D", grid=ucapi.ui.Size(6, 6))
    ui_page5.add(ucapi.ui.create_ui_text("-- 2D/3D Display Select --", 0, 0, size=ucapi.ui.Size(6, 1)))
    ui_page5.add(ucapi.ui.create_ui_text("2D", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_2D_3D_SELECT_2D")))
    ui_page5.add(ucapi.ui.create_ui_text("3D", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_2D_3D_SELECT_3D")))
    ui_page5.add(ucapi.ui.create_ui_text("Auto", 4, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_2D_3D_SELECT_AUTO")))
    ui_page5.add(ucapi.ui.create_ui_text("-- 3D Format --", 0, 2, size=ucapi.ui.Size(6, 1)))
    ui_page5.add(ucapi.ui.create_ui_text("Simulated 3D", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_3D_FORMAT_SIMULATED_3D")))
    ui_page5.add(ucapi.ui.create_ui_text("Side-by-Side", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_3D_FORMAT_SIDE_BY_SIDE")))
    ui_page5.add(ucapi.ui.create_ui_text("Over-Under", 4, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MODE_3D_FORMAT_OVER_UNDER")))

    ui_page6 = ucapi.ui.UiPage("page6", "Lens Control", grid=ucapi.ui.Size(4, 7))
    ui_page6.add(ucapi.ui.create_ui_text("-- Lens Control --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page6.add(ucapi.ui.create_ui_text("-- Focus --", 0, 1, size=ucapi.ui.Size(2, 1)))
    ui_page6.add(ucapi.ui.create_ui_text("-- Zoom --", 2, 1, size=ucapi.ui.Size(2, 1)))
    ui_page6.add(ucapi.ui.create_ui_icon("uc:up-arrow", 0, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("LENS_FOCUS_NEAR")))
    ui_page6.add(ucapi.ui.create_ui_icon("uc:down-arrow", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("LENS_FOCUS_FAR")))
    ui_page6.add(ucapi.ui.create_ui_icon("uc:up-arrow-bold", 2, 2, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("LENS_ZOOM_LARGE")))
    ui_page6.add(ucapi.ui.create_ui_icon("uc:down-arrow-bold", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("LENS_ZOOM_SMALL")))
    ui_page6.add(ucapi.ui.create_ui_icon("uc:up-arrow-alt", 1, 4, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("LENS_SHIFT_UP")))
    ui_page6.add(ucapi.ui.create_ui_icon("uc:left-arrow-alt", 0, 5, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("LENS_SHIFT_LEFT")))
    ui_page6.add(ucapi.ui.create_ui_icon("uc:right-arrow-alt", 2, 5, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("LENS_SHIFT_RIGHT")))
    ui_page6.add(ucapi.ui.create_ui_icon("uc:down-arrow-alt", 1, 6, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("LENS_SHIFT_DOWN")))

    ui_page7 = ucapi.ui.UiPage("page7", "Miscellaneous")
    ui_page7.add(ucapi.ui.create_ui_text("-- Lamp Control --", 0, 0, size=ucapi.ui.Size(4, 1)))
    ui_page7.add(ucapi.ui.create_ui_text("High", 0, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("LAMP_CONTROL_HIGH")))
    ui_page7.add(ucapi.ui.create_ui_text("Low", 2, 1, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("LAMP_CONTROL_LOW")))
    ui_page7.add(ucapi.ui.create_ui_text("-- Input Lag Reduction --", 0, 2, size=ucapi.ui.Size(4, 1)))
    ui_page7.add(ucapi.ui.create_ui_text("On", 0, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("INPUT_LAG_REDUCTION_ON")))
    ui_page7.add(ucapi.ui.create_ui_text("Off", 2, 3, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("INPUT_LAG_REDUCTION_OFF")))
    ui_page7.add(ucapi.ui.create_ui_text("-- Menu Position --", 0, 4, size=ucapi.ui.Size(4, 1)))
    ui_page7.add(ucapi.ui.create_ui_text("Bottom Left", 0, 5, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MENU_POSITION_BOTTOM_LEFT")))
    ui_page7.add(ucapi.ui.create_ui_text("Center", 2, 5, size=ucapi.ui.Size(2, 1), cmd=ucapi.remote.create_send_cmd("MENU_POSITION_CENTER")))

    return [ui_page1, ui_page2, ui_page3, ui_page4, ui_page5, ui_page6, ui_page7]



async def add_remote(ent_id: str, name: str):
    """Function to add a remote entity"""

    _LOG.info("Add projector remote entity with id " + ent_id + " and name " + name)

    definition = ucapi.Remote(
        ent_id,
        name,
        features=config.RemoteDef.features,
        attributes=config.RemoteDef.attributes,
        simple_commands=config.RemoteDef.simple_commands,
        button_mapping=create_button_mappings(),
        ui_pages=create_ui_pages(),
        cmd_handler=remote_cmd_handler,
    )

    _LOG.debug("Projector remote entity definition created")

    driver.api.available_entities.add(definition)

    _LOG.info("Added projector remote entity")
