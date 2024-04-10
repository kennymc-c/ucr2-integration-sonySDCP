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

import setup
import media_player

_LOG = logging.getLogger("driver")  # avoid having __main__ in log messages

# os.environ["UC_INTEGRATION_INTERFACE"] = ""
CFG_FILENAME = "config-test.json"
id = ""
name = ""

loop = asyncio.get_event_loop()
api = ucapi.IntegrationAPI(loop)



async def startcheck():
    if setup.get_setup_complete():

        _LOG.debug(CFG_FILENAME + " found")

        with open(CFG_FILENAME, "r") as f:
            config = json.load(f)  

        if "id" and "name" in config:
            id = config["id"]
            name = config["name"]
            if api.available_entities.contains(id):
                _LOG.debug("Entity with id " + id + " is already in storage as available entity")
            else:
                _LOG.info("Add entity with id " + id + " as available entity")
                await media_player.add_mp(get_ip(), id, name)
        else:
            _LOG.error("Error in " + CFG_FILENAME + ". ID and name not found")



def get_ip():
    #Check if config json file exists
    if os.path.isfile(CFG_FILENAME):

        #Load ip address from config json file
        with open(CFG_FILENAME, "r") as f:
            config = json.load(f)
        
        if config["ip"] != "":
            return config["ip"]
        else:
            _LOG.error("Error in " + CFG_FILENAME + ". No ip address found")
    else:
        _LOG.warning(CFG_FILENAME + " not found. Please start the setup process")



async def mp_cmd_handler(entity: ucapi.MediaPlayer, cmd_id: str, _params: dict[str, Any] | None) -> ucapi.StatusCodes:
    """
    Media Player command handler.

    Called by the integration-API if a command is sent to a configured media_player-entity.

    :param entity: media_player entity
    :param cmd_id: command
    :param _params: optional command parameters
    :return: status of the command
    """

    if _params == None:
        _LOG.info(f"Received {cmd_id} command for {entity.id}")
    else:
        _LOG.info(f"Received {cmd_id} command with parameter {_params} for {entity.id}")
    
    try:
        ip = get_ip()
    except:
        _LOG.error("Could not load ip address from config json file")
        return ucapi.StatusCodes.CONFLICT
    
    return media_player.mp_cmd_assigner(entity.id, cmd_id, _params, ip)



@api.listens_to(ucapi.Events.CONNECT)
async def on_r2_connect() -> None:
    """
    Connect notification from Remote Two.

    Just reply with connected as there is no permanent connection to the projector that needs to be re-established
    """
    _LOG.info("Received connect event message from remote")
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)



@api.listens_to(ucapi.Events.DISCONNECT)
#TODO Find out how to prevent the remote from constantly reconnecting when the integration is not running without deleting the integration configuration on the remote every time
async def on_r2_disconnect() -> None:
    """
    Disconnect notification from the remote Two.

    Just reply with disconnected as there is no permanent connection to the projector that needs to be closed
    """
    _LOG.info("Received disconnect event message from remote")
    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)



@api.listens_to(ucapi.Events.ENTER_STANDBY)
async def on_r2_enter_standby() -> None:
    """
    Enter standby notification from Remote Two.

    Just show a debug log message as there is no permanent connection to the projector that needs to be closed.
    """
    _LOG.info("Received enter standby event message from remote")



@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote Two.

    Just show a debug log message as there is no permanent connection to the projector that needs to be re-established.
    """
    _LOG.info("Received exit standby event message from remote")



@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    _LOG.info("Received subscribe entities event for: %s", entity_ids)

    projector = pysdcp.Projector(get_ip())

    def get_attribute_power():
        try:
            if projector.get_power() == True:
                return ucapi.media_player.States.ON
            else:
                return ucapi.media_player.States.OFF
        except:
            _LOG.warning("Can't get power status from projector. Set to Unknown")
            return ucapi.media_player.States.UNKNOWN
        
    def get_attribute_muted():
        try:
            if projector.get_muting() == True:
                return True
            else:
                return False
        except:
            _LOG.warning("Can't get mute status from projector. Set to False")
            return False
        
    def get_attribute_source():
        try:
            return projector.get_input()
        except:
            _LOG.warning("Can't get input from projector. Set to None")
            return None


    for entity_id in entity_ids:
        _LOG.info("Set entity attributes for: " + entity_id)

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
    """
    Unsubscribe to given entities.

    Just show a debug log message as there is no permanent connection to the projector or clients that needs to be closed or removed.
    """
    _LOG.info("Unsubscribe entities event for: %s", entity_ids)



async def main():
    #Bugs
    #FIXME WS connection closed and not reestablish after remote reboot due to a system freeze. Can not be reproduced with a manual reboot
    #FIXME .local domainname changed after system freeze and the remote could not reconnect to the driver. Had to manually change the driver url to the new url. The domain didn't changed after a manual container restart. Why? Docker problem?

    logging.basicConfig(format='%(asctime)s | %(levelname)-8s | %(name)-14s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    logging.getLogger("setup").setLevel(level)

    _LOG.debug("Starting driver")

    #TODO Create attributes puller function

    await setup.init()
    await startcheck()



if __name__ == "__main__":
    loop.run_until_complete(main())
    loop.run_forever()