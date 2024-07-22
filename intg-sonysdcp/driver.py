#!/usr/bin/env python3

"""Main driver file. Run this module to start the integration driver"""

import sys
import asyncio
import logging
from typing import Any

import os
import ucapi

from pysdcp.protocol import *

import config
import setup
import media_player

_LOG = logging.getLogger("driver")  # avoid having __main__ in log messages

loop = asyncio.get_event_loop()
api = ucapi.IntegrationAPI(loop)



async def startcheck():
    """
    Called at the start of the integration driver to load the config file into the runtime storage, add a media player entity and start the attributes poller task
    """
    try:
        config.Setup.load()
    except OSError as o:
        _LOG.critical(o)
        _LOG.critical("Stopping integration driver")
        raise SystemExit(0) from o

    if config.Setup.get("setup_complete"):
        entity_id = config.Setup.get("id")
        entity_name = config.Setup.get("name")

        if api.available_entities.contains(entity_id):
            _LOG.debug("Entity with id " + entity_id + " is already in storage as available entity")
        else:
            _LOG.info("Add entity with id " + entity_id + " and name " + entity_name + " as available entity")

        await media_player.add_mp(entity_id, entity_name)

        poller_interval = config.Setup.get("poller_interval")
        if poller_interval == 0:
            _LOG.info("Attributes poller interval set to " + str(poller_interval) + ". Skip creation of attributes poller task")
        else:
            loop.create_task(attributes_poller(entity_id, poller_interval))
            _LOG.debug("Created attributes poller task with an interval of " + str(poller_interval) + " seconds")



async def attributes_poller(entity_id: str, interval: int) -> None:
    """Projector data poller."""
    while True:
        await asyncio.sleep(interval)
        #TODO #WAIT Uncomment when (get_)configured_entities are implemented in the remote core
        #https://studio.asyncapi.com/?url=https://raw.githubusercontent.com/unfoldedcircle/core-api/main/integration-api/asyncapi.yaml#message-get_configured_entities
        # if api.configured_entities.contains(id):
        if config.Setup.get("standby"):
            continue
        try:
            #TODO Add check if network and remote is reachable
            await media_player.update_attributes(entity_id)
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

    if _params is None:
        _LOG.info(f"Received {cmd_id} command for {entity.id}")
    else:
        _LOG.info(f"Received {cmd_id} command with parameter {_params} for {entity.id}")

    try:
        ip = config.Setup.get("ip")
    except ValueError as v:
        _LOG.error(v)
        return ucapi.StatusCodes.SERVER_ERROR

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
    config.Setup.set("standby", True)



@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote Two.

    Just show a debug log message as there is no permanent connection to the projector that needs to be re-established.
    """
    _LOG.info("Received exit standby event message from remote")

    _LOG.debug("Set config.R2_IN_STANDBY to False")
    config.Setup.set("standby", False)



@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    _LOG.info("Received subscribe entities event for entity ids: " + str(entity_ids))

    config.Setup.set("standby", False)

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



def getLogger():
    """Get logger from all modules"""

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("ucapi.api").setLevel(level)
    logging.getLogger("ucapi.entities").setLevel(level)
    logging.getLogger("ucapi.entity").setLevel(level)
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    logging.getLogger("setup").setLevel(level)
    logging.getLogger("config").setLevel(level)



async def main():
    """Main function that gets logging from all sub modules and starts the driver"""

    #Check if integration runs in a PyInstaller bundle on the remote and adjust the logging format, config file path and attributes poller interval
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):

        logging.basicConfig(format="%(name)-14s | %(message)s")
        getLogger()

        _LOG.info("This integration is running in a PyInstaller bundle. Probably on the remote hardware")
        config.Setup.set("bundle_mode", True)

        cfg_path = os.environ["UC_CONFIG_HOME"] + "/config.json"
        config.Setup.set("cfg_path", cfg_path)
        _LOG.debug("Store configuration in " + cfg_path)

        _LOG.info("Deactivating attributes poller to reduce battery consumption when running on the remote")
        config.Setup.set("poller_interval", 0)
    else:
        logging.basicConfig(format="%(asctime)s | %(levelname)-8s | %(name)-14s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        getLogger()

    _LOG.debug("Starting driver")

    #TODO #WAIT Remove all pySDCP files and add pySDCP to requirements.txt when upstream PR has been merged:
    #https://github.com/Galala7/pySDCP/pull/5

    await setup.init()
    await startcheck()



if __name__ == "__main__":
    loop.run_until_complete(main())
    loop.run_forever()
