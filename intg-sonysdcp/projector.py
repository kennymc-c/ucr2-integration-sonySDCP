#!/usr/bin/env python3

"""Module that includes functions to execute pySDCP commands"""

import logging

import ucapi
import pysdcp
from pysdcp.protocol import *

import config
import driver
import sensor

_LOG = logging.getLogger(__name__)



def get_attr_power(ip: str):
    """Get the current power state from the projector and return the corresponding ucapi power state attribute"""
    projector = pysdcp.Projector(ip)

    try:
        if projector.get_power():
            return {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.ON}
        return {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF}
    except (Exception, ConnectionError) as e:
        raise Exception(e) from e

def get_attr_muted(ip: str):
    """Get the current muted state from the projector and return either False or True"""
    projector = pysdcp.Projector(ip)
    try:
        if projector.get_muting():
            return True
        else:
            return False
    except (Exception, ConnectionError) as e:
        raise Exception(e) from e

def get_attr_source(ip: str):
    """Get the current input source from the projector and return it as a string"""
    projector = pysdcp.Projector(ip)
    try:
        return projector.get_input()
    except (Exception, ConnectionError) as e:
        raise Exception(e) from e



async def send_cmd(entity_id: str, ip: str, cmd_name:str, params = None):
    """Send a command to the projector and raise an exception if it fails"""

    projector_pysdcp = pysdcp.Projector(ip)
    mp_id = config.Setup.get("id")
    rt_id = config.Setup.get("rt-id")
    lt_id = config.Setup.get("lt-id")

    def cmd_error(msg:str = None):
        if msg is None:
            _LOG.error("Error while executing the command: " + cmd_name)
            raise Exception(msg)
        _LOG.error(msg)
        raise Exception(msg)

    match cmd_name:

        case ucapi.media_player.Commands.ON:
            try:
                if projector_pysdcp.set_power(True):
                    driver.api.configured_entities.update_attributes(entity_id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.ON})
                    driver.api.configured_entities.update_attributes(rt_id, {ucapi.remote.Attributes.STATE: ucapi.remote.States.ON})
                    sensor.update_lt(lt_id, ip)
                else:
                    cmd_error()
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case ucapi.media_player.Commands.OFF:
            try:
                if projector_pysdcp.set_power(False):
                    driver.api.configured_entities.update_attributes(entity_id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF})
                    driver.api.configured_entities.update_attributes(rt_id, {ucapi.remote.Attributes.STATE: ucapi.remote.States.OFF})
                    sensor.update_lt(lt_id, ip)
                else:
                    cmd_error()
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case ucapi.media_player.Commands.TOGGLE:
            try:
                if projector_pysdcp.get_power():
                    if projector_pysdcp.set_power(False):
                        driver.api.configured_entities.update_attributes(entity_id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF})
                        driver.api.configured_entities.update_attributes(rt_id, {ucapi.remote.Attributes.STATE: ucapi.remote.States.OFF})
                    else:
                        cmd_error()
                elif not projector_pysdcp.get_power():
                    if projector_pysdcp.set_power(True):
                        driver.api.configured_entities.update_attributes(entity_id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.ON})
                        driver.api.configured_entities.update_attributes(rt_id, {ucapi.remote.Attributes.STATE: ucapi.remote.States.ON})
                    else:
                        cmd_error()
                else:
                    cmd_error()
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            ucapi.media_player.Commands.MUTE_TOGGLE | \
            "PICTURE_MUTING_TOGGLE":
            try:
                if projector_pysdcp.get_muting():
                    if projector_pysdcp.set_muting(False):
                        driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.MUTED: False})
                    else:
                        cmd_error()
                elif not projector_pysdcp.get_muting():
                    if projector_pysdcp.set_muting(True):
                        driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.MUTED: True})
                    else:
                        cmd_error()
                else:
                    cmd_error()
            except (Exception, ConnectionError) as e:
                return cmd_error(e)

        case \
            ucapi.media_player.Commands.MUTE | \
            "MUTE":
            try:
                if projector_pysdcp.set_muting(True):
                    driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.MUTED: True})
                else:
                    cmd_error()
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            ucapi.media_player.Commands.UNMUTE | \
            "UNMUTE":
            try:
                if projector_pysdcp.set_muting(False):
                    driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.MUTED: False})
                else:
                    cmd_error()
            except (Exception, ConnectionError) as e:
                return cmd_error(e)

        case \
            ucapi.media_player.Commands.SELECT_SOURCE | \
            "INPUT_HDMI_1" | \
            "INPUT_HDMI_2":
            if params:
                source = params["source"]
            else:
                source = cmd_name.replace("INPUT_", "").replace("_", " ")

            try:
                if source == "HDMI 1":
                    if projector_pysdcp.set_HDMI_input(1):
                        driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.SOURCE: source})
                    else:
                        cmd_error()
                elif source == "HDMI 2":
                    if projector_pysdcp.set_HDMI_input(2):
                        driver.api.configured_entities.update_attributes(mp_id, {ucapi.media_player.Attributes.SOURCE: source})
                    else:
                        cmd_error()
                else:
                    cmd_error("Unknown source: " + source)
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            ucapi.media_player.Commands.HOME | \
            "HOME" | \
            "MENU":
            try:
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS_IR["MENU"])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            ucapi.media_player.Commands.BACK | \
            "BACK":
            try:
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS_IR["CURSOR_LEFT"])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            ucapi.media_player.Commands.CURSOR_ENTER | \
            ucapi.media_player.Commands.CURSOR_UP | \
            ucapi.media_player.Commands.CURSOR_DOWN | \
            ucapi.media_player.Commands.CURSOR_LEFT | \
            ucapi.media_player.Commands.CURSOR_RIGHT | \
            "CURSOR_ENTER" | \
            "CURSOR_UP" | \
            "CURSOR_DOWN" | \
            "CURSOR_LEFT" | \
            "CURSOR_RIGHT" | \
            "LENS_SHIFT_UP" | \
            "LENS_SHIFT_DOWN" | \
            "LENS_SHIFT_LEFT" | \
            "LENS_SHIFT_RIGHT" | \
            "LENS_FOCUS_FAR" | \
            "LENS_FOCUS_NEAR" | \
            "LENS_ZOOM_LARGE" | \
            "LENS_ZOOM_SMALL":
            try:
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS_IR[cmd_name.upper()])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            "MODE_ASPECT_RATIO_NORMAL" | \
            "MODE_ASPECT_RATIO_V_STRETCH" | \
            "MODE_ASPECT_RATIO_ZOOM_1_85" | \
            "MODE_ASPECT_RATIO_ZOOM_2_35" | \
            "MODE_ASPECT_RATIO_STRETCH" | \
            "MODE_ASPECT_RATIO_SQUEEZE":
            aspect = cmd_name.replace("MODE_ASPECT_RATIO_", "")
            try:
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["ASPECT_RATIO"], data=ASPECT_RATIOS[aspect])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

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
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["CALIBRATION_PRESET"], data=CALIBRATION_PRESETS[preset])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            "MODE_MOTIONFLOW_OFF" | \
            "MODE_MOTIONFLOW_SMOTH_HIGH" | \
            "MODE_MOTIONFLOW_SMOTH_LOW" | \
            "MODE_MOTIONFLOW_IMPULSE" | \
            "MODE_MOTIONFLOW_COMBINATION" | \
            "MODE_MOTIONFLOW_TRUE_CINEMA":
            preset = cmd_name.replace("MODE_MOTIONFLOW_", "")
            try:
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["MOTIONFLOW"], data=MOTIONFLOW[preset])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            "MODE_HDR_ON" | \
            "MODE_HDR_OFF" | \
            "MODE_HDR_AUTO" | \
            "MODE_HDR_TOGGLE":
            preset = cmd_name.replace("MODE_HDR_", "")
            if preset != "TOGGLE":
                try:
                    projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["HDR"], data=HDR[preset])
                except (Exception, ConnectionError) as e:
                    cmd_error(e)
            if preset == "TOGGLE":
                try:
                    data = projector_pysdcp._send_command(action=ACTIONS["GET"], command=COMMANDS["HDR"])
                except (Exception, ConnectionError) as e:
                    cmd_error(e)
                if data == HDR["ON"] or data == HDR["AUTO"]:
                    try:
                        _LOG.info("Turn HDR off")
                        projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["HDR"], data=HDR["OFF"])
                    except (Exception, ConnectionError) as e:
                        cmd_error(e)
                else:
                    try:
                        _LOG.info("Turn HDR on")
                        projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["HDR"], data=HDR["ON"])
                    except (Exception, ConnectionError) as e:
                        cmd_error(e)

        case \
            "MODE_2D_3D_SELECT_AUTO" | \
            "MODE_2D_3D_SELECT_3D" | \
            "MODE_2D_3D_SELECT_2D":
            preset = cmd_name.replace("MODE_2D_3D_SELECT_", "")
            try:
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["2D_3D_DISPLAY_SELECT"], data=TWO_D_THREE_D_SELECT[preset])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            "MODE_3D_FORMAT_SIMULATED_3D" | \
            "MODE_3D_FORMAT_SIDE_BY_SIDE" | \
            "MODE_3D_FORMAT_OVER_UNDER":
            preset = cmd_name.replace("MODE_3D_FORMAT_", "")
            try:
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["3D_FORMAT"], data=THREE_D_FORMATS[preset])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            "LAMP_CONTROL_LOW" | \
            "LAMP_CONTROL_HIGH":
            preset = cmd_name.replace("LAMP_CONTROL_", "")
            try:
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["LAMP_CONTROL"], data=LAMP_CONTROL[preset])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            "INPUT_LAG_REDUCTION_ON" | \
            "INPUT_LAG_REDUCTION_OFF":
            preset = cmd_name.replace("INPUT_LAG_REDUCTION_", "")
            try:
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["INPUT_LAG_REDUCTION"], data=INPUT_LAG_REDUCTION[preset])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case \
            "MENU_POSITION_BOTTOM_LEFT" | \
            "MENU_POSITION_CENTER":
            preset = cmd_name.replace("MENU_POSITION_", "")
            try:
                projector_pysdcp._send_command(action=ACTIONS["SET"], command=COMMANDS["MENU_POSITION"], data=MENU_POSITIONS[preset])
            except (Exception, ConnectionError) as e:
                cmd_error(e)

        case _:
            cmd_error("Command not found or unsupported: " + cmd_name)
