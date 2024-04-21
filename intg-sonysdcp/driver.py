#!/usr/bin/env python3

import asyncio
import logging
from typing import Any

import ucapi
import os

from pysdcp.protocol import *

import config
import setup
import media_player

# os.environ["UC_INTEGRATION_INTERFACE"] = ""

_LOG = logging.getLogger("driver")  # avoid having __main__ in log messages

loop = asyncio.get_event_loop()
api = ucapi.IntegrationAPI(loop)



async def startcheck():
    #Load config into runtime storage
    try:
        config.setup.load()
    except OSError as o:
        _LOG.critical(o)
        return False

    if config.setup.get("setup_complete"):
        id = config.setup.get("id")
        name = config.setup.get("name")

        if api.available_entities.contains(id):
            _LOG.debug("Entity with id " + id + " is already in storage as available entity")
        else:
            _LOG.info("Add entity with id " + id + " and name " + name + " as available entity")
            await media_player.add_mp(id, name)

            

async def attributes_poller(interval: int) -> None:
    """Projector data poller."""
    while True:
            await asyncio.sleep(interval)
            if config.setup.get("setup_complete"):
                if config.setup.get("standby"):
                    continue
                try:
                    await media_player.update_attributes()
                except Exception as e:
                    _LOG.warning(e)



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

    ip = config.setup.get("ip")
    
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

    Set config.R2_IN_STANDBY to True and show a debug log message as there is no permanent connection to the projector that needs to be closed.
    """
    _LOG.info("Received enter standby event message from remote")

    _LOG.debug("Set config.R2_IN_STANDBY to True")
    config.setup.set("standby", True)
    


@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote Two.

    Just show a debug log message as there is no permanent connection to the projector that needs to be re-established.
    """
    _LOG.info("Received exit standby event message from remote")

    _LOG.debug("Set config.R2_IN_STANDBY to False")
    config.setup.set("standby", False)



@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    _LOG.info("Received subscribe entities event for entity ids: " + str(entity_ids))

    config.setup.set("standby", False)

    for entity_id in entity_ids:
        try:
            await media_player.update_attributes(entity_id)
        except OSError as o:
            _LOG.critical(o)
        except Exception as e:
            _LOG.warning(e)



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
    logging.getLogger("config").setLevel(level)

    _LOG.debug("Starting driver")

    if config.POLLER_INTERVAL == 0:
        _LOG.info("POLLER_INTERVAL is " + str(config.POLLER_INTERVAL) + ". Skip creation of attributes puller task")
    else:
        loop.create_task(attributes_poller(config.POLLER_INTERVAL))
    
    await setup.init()
    await startcheck()



if __name__ == "__main__":
    loop.run_until_complete(main())
    loop.run_forever()