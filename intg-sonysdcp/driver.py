#!/usr/bin/env python3

import asyncio
import logging
from typing import Any

import ucapi
import json
import os
import ipaddress

import pysdcp
from pysdcp.protocol import *

# os.environ["UC_INTEGRATION_INTERFACE"] = ""
CFG_FILENAME = "config-test.json"
ID_DEFAULT = "sony-projector"
NAME_DEFAULT = {"en": "Sony Projector", "de": "Sony Projektor"}

loop = asyncio.get_event_loop()
api = ucapi.IntegrationAPI(loop)
        
#TODO Split up driver.py into separate files



def get_ip():
    #Check if config json file exists
    if os.path.isfile(CFG_FILENAME):

        #Load ip address from config json file
        with open(CFG_FILENAME, "r") as f:
            config = json.load(f)
        
        if config["ip"] != "":
            return config["ip"]
        else:
            print("Error in " + CFG_FILENAME + ". No ip address found")
    else:
        print(CFG_FILENAME + " not found. Please start the setup process")


def setup_complete(value: bool):
    if value == True:
        flag = {"setup_complete": True}
    else:
        flag = {"setup_complete": False}
    try:
        with open(CFG_FILENAME, "r+") as f:
            l = json.load(f)
            l.update(flag)
            f.seek(0)
            json.dump(l, f)
    except:
        raise Exception("Error while storing setup_complete flag")



def get_setup_complete():
    if os.path.isfile(CFG_FILENAME):
        try:
            with open(CFG_FILENAME, "r") as f:
                l = json.load(f)
                flag = l["setup_complete"]
                if flag == True:
                    return True
                elif flag == False:
                    return False
        except KeyError:
            print("Setup has not been completed yet")
            return False
        except:
            raise Exception("Error while reading setup_complete flag from " + CFG_FILENAME)
    else:
        print(CFG_FILENAME + " does not exist (yet)")
        return False
        



def get_pjinfo(ip: str):

    def load_pjinfo():
        #Load entity id and name from config json file
        with open(CFG_FILENAME, "r") as f:
            config = json.load(f)  

        if "id" and "name" in config:
            print("Loaded id and name from " + CFG_FILENAME)
            return config
        else:
            return False
        
    def store_pjinfo(data):
        print("Append serial number as id and model as name into " + CFG_FILENAME)
        try:
            with open(CFG_FILENAME, "r+") as f:
                l = json.load(f)
                l.update(data)
                f.seek(0)
                json.dump(l, f)
        except:
            print("Error while storing projector data")
            return False
            
    
    #Check if config files exists and load id and name instead of query them every time
    if os.path.isfile(CFG_FILENAME):
        config = load_pjinfo()

        if config == False:
            projector = pysdcp.Projector(ip)
            
            print("Query serial number and model name from projector (" + ip + ") via SDAP advertisement service. This may take up to 30 seconds")
            #TODO Also mention this in the setup dialog when entering the ip
            pjinfo = projector.get_pjinfo()

            if pjinfo != False:

                serial = str(pjinfo["serial"])
                model = "Sony " + pjinfo["model"]

                jsondata={"id": serial, "name": model}

                store_pjinfo(jsondata)

                config = load_pjinfo()
            
                return config
            else:
                print("Query failed. Please check if the projector is connected to the same network as the integration and the SDAP advertisement service is turned on")
                print("Using default values instead: ID: " + ID_DEFAULT + ", Name: " + str(NAME_DEFAULT))
                jsondata={"id": ID_DEFAULT, "name": NAME_DEFAULT}

                store_pjinfo(jsondata)

                config = load_pjinfo()
            
                return config
                
        else:
            return config
            
    else:
        print(CFG_FILENAME + " not found. Please start the setup process")
        return False



def add_media_player(ip: str):
    
    info = get_pjinfo(ip)
    if info == False:
        return False
    else:
        id = info["id"]
        name = info["name"]

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

    media_player = ucapi.MediaPlayer(
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
                "MODE_PRESET_TV",
                "MODE_PRESET_PHOTO",
                "MODE_PRESET_GAME",
                "MODE_PRESET_BRIGHT_CINEMA",
                "MODE_PRESET_BRIGHT_TV",
                "MODE_PRESET_USER",
                "MODE_ASPECT_RATIO_NORMAL",
                "MODE_ASPECT_RATIO_V_STRETCH",
                "MODE_ASPECT_RATIO_ZOOM_1_85",
                "MODE_ASPECT_RATIO_ZOOM_2_35",
                "MODE_ASPECT_RATIO_STRETCH",
                "MODE_ASPECT_RATIO_SQUEEZE",
                "MODE_PRESET_CINEMA_FILM_1",
                "MODE_PRESET_CINEMA_FILM_2",
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
        cmd_handler=mp_cmd_handler
    )

    api.available_entities.add(media_player)
    print("Added media player entity")



async def driver_setup_handler(msg: ucapi.SetupDriver) -> ucapi.SetupAction:
    """
    Dispatch driver setup requests to corresponding handlers.

    Either start the setup process or handle the provided user input data.

    :param msg: the setup driver request object, either DriverSetupRequest,
                UserDataResponse or UserConfirmationResponse
    :return: the setup action on how to continue
    """
    if isinstance(msg, ucapi.DriverSetupRequest):
        return await handle_driver_setup(msg)

    print("Error during setup")
    return ucapi.SetupError()



async def handle_driver_setup(msg: ucapi.DriverSetupRequest,) -> ucapi.SetupAction:
    """
    Start driver setup.

    Initiated by Remote Two to set up the driver.

    :param msg: value(s) of input fields in the first setup screen.
    :return: the setup action on how to continue
    """

    # if msg.reconfigure:
    #     print("Ignoring driver reconfiguration request")

    # print("Clear all available and configured entities")
    # api.available_entities.clear()
    # api.configured_entities.clear()

    #Check if ip address has been entered
    if msg.setup_data["ip"] != "":

        #Check if input is a valid ipv4 or ipv6 address
        try:
            ip_object = ipaddress.ip_address(msg.setup_data["ip"])
        except ValueError:
            print("The entered ip address \"" + msg.setup_data["ip"] + "\" is not valid")
            return ucapi.SetupError()

        print(f"Chosen ip address: " + msg.setup_data["ip"])

        #Create Python dictionary for ip address
        ip = msg.setup_data["ip"]
        ip_json = {"ip": msg.setup_data["ip"]}

        #Convert and store ip address into Json config file
        with open(CFG_FILENAME, "w") as f:
            json.dump(ip_json, f)

        print("IP address stored in " + CFG_FILENAME)

        #Add entities with their corresponding command handler
        print("Add media player entity from ip " + ip)

        add_media_player(ip)
        print("Setup complete")
        setup_complete(True)
        return ucapi.SetupComplete()
    
    else:
        print("No IP address has been entered")
        return ucapi.SetupError()



async def mp_cmd_handler(entity: ucapi.MediaPlayer, cmd_id: str, _params: dict[str, Any] | None) -> ucapi.StatusCodes:
    """
    Media Player command handler.

    Called by the integration-API if a command is sent to a configured media_player-entity.

    :param entity: media_player entity
    :param cmd_id: command
    :param _params: optional command parameters
    :return: status of the command
    """

    print(f"Received {cmd_id} command for {entity.id}. Optional parameter: {_params}")
    
    try:
        ip = get_ip()
    except:
        print("Could not load ip address from config json file")
        return ucapi.StatusCodes.CONFLICT
    
    return mp_cmd_assigner(entity.id, cmd_id, _params, ip)



def mp_cmd_assigner(id: str, cmd_name: str, params: dict[str, Any] | None, ip: str):

    projector = pysdcp.Projector(ip)

    def cmd_error():
        print("Error while executing the command: " + cmd_name)
        return ucapi.StatusCodes.SERVER_ERROR

    #TODO Separate error messages for timeouts
    #TODO Show the exception message from pySDCP in the integration log and also send a response code to the api
    #TODO Find a get command that shows the status of the current input signal to prevent errors for commands like aspect ratio and picture preset that don't work without a input signal. Probably better implement this in pySDC itself

    match cmd_name:

        case ucapi.media_player.Commands.ON:
            if projector.set_power(True):
                api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.ON})
                return ucapi.StatusCodes.OK
            else:
                return cmd_error()
            
        case ucapi.media_player.Commands.OFF:
            if projector.set_power(False):
                api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF})
                return ucapi.StatusCodes.OK
            else:
                return cmd_error()

        case ucapi.media_player.Commands.TOGGLE:
            if projector.get_power() == True:
                if projector.set_power(False):
                    api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.OFF})
                    return ucapi.StatusCodes.OK
                else:
                    return cmd_error()
            elif projector.get_power() == False:
                if projector.set_power(True):
                    api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.ON})
                    return ucapi.StatusCodes.OK
                else:
                    return cmd_error()
            else:
                return cmd_error()

        case ucapi.media_player.Commands.MUTE_TOGGLE:
            if projector.get_muting() == True:
                if projector.set_muting(False):
                    api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.MUTED: False})
                    return ucapi.StatusCodes.OK
                else:
                    return cmd_error()
            elif projector.get_muting() == False:
                if projector.set_muting(True):
                    api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.MUTED: True})
                    return ucapi.StatusCodes.OK
                else:
                    return cmd_error()
            else:
                return cmd_error()

        case ucapi.media_player.Commands.MUTE:
            if projector.set_muting(True):
                api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.MUTED: True})
                return ucapi.StatusCodes.OK
            else:
                return cmd_error()
        
        case ucapi.media_player.Commands.UNMUTE:
            if projector.set_muting(False):
                api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.MUTED: False})
                return ucapi.StatusCodes.OK
            else:
                return cmd_error()
        
        case ucapi.media_player.Commands.HOME:
            try:
                projector._send_command(action=ACTIONS["SET"], command=COMMANDS_IR["MENU"])
                return ucapi.StatusCodes.OK
            except:
                return cmd_error()

        case ucapi.media_player.Commands.SELECT_SOURCE:
            source = params["source"]
            if source == "HDMI 1":
                if projector.set_HDMI_input(1):
                    api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.SOURCE: source})
                    return ucapi.StatusCodes.OK
                else:
                    return cmd_error()
            elif source == "HDMI 2":
                if projector.set_HDMI_input(2):
                    api.configured_entities.update_attributes(id, {ucapi.media_player.Attributes.SOURCE: source})
                    return ucapi.StatusCodes.OK
                else:
                    return cmd_error()
            else:
                print("Unknown source: " + source)
                return cmd_error()

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
                except:
                    return cmd_error()
                
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
                    if projector.set_preset(preset):
                        return ucapi.StatusCodes.OK
                    else:
                        return cmd_error()
                except:
                    return cmd_error()

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
                except:
                    return cmd_error()
        
        case _:
            print("Command not implemented: " + cmd_name)
            return ucapi.StatusCodes.NOT_IMPLEMENTED




@api.listens_to(ucapi.Events.CONNECT)
async def on_r2_connect() -> None:
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)


@api.listens_to(ucapi.Events.DISCONNECT)
#TODO Find out how to prevent the remote from constantly reconnecting when the integration is not running without deleting the integration configuration on the remote every time
async def on_r2_disconnect() -> None:
    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)


@api.listens_to(ucapi.Events.ENTER_STANDBY)
async def on_r2_enter_standby() -> None:
    """
    Enter standby notification from Remote Two.

    Disconnect every projector instances.
    """
    print("Enter standby")


@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote Two.

    Connect all projector instances.
    """
    print("Exit standby")


@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    
    projector = pysdcp.Projector(get_ip())


    def get_attribute_power():
        try:
            if projector.get_power() == True:
                return ucapi.media_player.States.ON
            else:
                return ucapi.media_player.States.OFF
        except:
            print("Can't get power status from projector. Set to Unknown")
            return ucapi.media_player.States.UNKNOWN
        
    def get_attribute_muted():
        try:
            if projector.get_muting() == True:
                return True
            else:
                return False
        except:
            print("Can't get mute status from projector. Set to False")
            return False
        
    def get_attribute_source():
        try:
            return projector.get_input()
        except:
            print("Can't get input from projector. Set to None")
            return None


    for entity_id in entity_ids:
        print("Subscribe entities event: " + entity_id)

        state = get_attribute_power()
        muted = get_attribute_muted()
        source = get_attribute_source()

        api.configured_entities.update_attributes(entity_id, {
            ucapi.media_player.Attributes.STATE: state,
            ucapi.media_player.Attributes.MUTED: muted,
            ucapi.media_player.Attributes.SOURCE: source,
            ucapi.media_player.Attributes.SOURCE_LIST: ["HDMI 1", "HDMI 2"]
        })


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """On unsubscribe, we disconnect the objects and remove listeners for events."""
    print("Unsubscribe entities event: %s", entity_ids)



if __name__ == "__main__":
    logging.basicConfig()

    #TODO Use logging function instead of print()
    #FIXME WS connection closed and not reestablish after remote reboot due to a system freeze. Can not be reproduced with a manual reboot
    #FIXME .local domainname changed after system freeze and the remote could not reconnect to the driver. Had to manually change the driver url to the new url. The domain didn't changed after a manual container restart. Why? Docker problem?

    print("Starting driver")

    #TODO First check if there are any configured entities on the remote and then check if config file exists

    if get_setup_complete():

        #Check if configuration file has already been created and add all entities
        if os.path.isfile(CFG_FILENAME):

            print(CFG_FILENAME + " found")

            info = get_pjinfo(get_ip())
            id = info["id"]

            if api.available_entities.contains(id):
                print("Entity with id " + id + " is already in storage")
            else:
                print("Add entity with id " + id)
                add_media_player(get_ip())

        else:
            print(CFG_FILENAME + " not found. Please restart the setup process")
    else:
        print("Driver setup not complete. Please start the setup process")


    loop.run_until_complete(api.init("setup.json", driver_setup_handler))
    loop.run_forever()