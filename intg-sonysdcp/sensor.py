#!/usr/bin/env python3

"""Module that includes functions to add a lamp timer sensor entity and to poll the sensor data"""

import logging

import ucapi
import pysdcp
from pysdcp.protocol import *

import config
import driver

_LOG = logging.getLogger(__name__)



async def add_lt_sensor(ent_id: str, name: str):
    """Function to add a lamp timer sensor entity with the config.sensorDef class definition and get current lamp hours"""

    definition = ucapi.Sensor(
        ent_id,
        name,
        features=None, #Mandatory although sensor entities have no features
        attributes=config.LTSensorDef.attributes,
        device_class=config.LTSensorDef.device_class,
        options=config.LTSensorDef.options
    )

    _LOG.debug("Projector lamp timer sensor entity definition created")

    driver.api.available_entities.add(definition)

    _LOG.info("Added projector lamp timer sensor entity")



async def create_lt_poller(ent_id: str, ip: str):
    """Creates a lamp timer poller task"""

    lt_poller_interval = config.Setup.get("lt_poller_interval")
    driver.loop.create_task(lt_poller(ent_id, lt_poller_interval, ip), name="lt_poller")
    _LOG.debug("Started lamp timer poller task with an interval of " + str(lt_poller_interval) + " seconds")



async def lt_poller(entity_id: str, interval: int, ip: str) -> None:
    """Projector lamp timer poller task. Runs only when the projector is powered on"""
    while True:
        await driver.asyncio.sleep(interval)
        #TODO Implement check if there are too many timeouts to the projector and automatically deactivate poller and set entity status to unknown
        #TODO #WAIT Check if there are configured entities using the get_configured_entities api request once the UC Python library supports this
        if config.Setup.get("standby"):
            continue
        try:
            projector = pysdcp.Projector(ip)
            if not projector.get_power():
                _LOG.debug("Skip updating lamp timer. Projector is powered off")
                continue
        except ConnectionError:
            _LOG.warning("Could not check projector power status. Connection refused")
            continue
        try:
            #TODO Add check if network and remote is reachable
            await update_lt(entity_id, ip)
        except Exception as e:
            _LOG.warning(e)



def get_lamp_hours(ip: str):
    """Get the lamp hours from the projector"""
    projector = pysdcp.Projector(ip)
    try:
        hours = projector.get_lamp_hours()
        return hours
    except (Exception, ConnectionError) as e:
        _LOG.error(e)



async def update_lt(entity_id: str, ip: str):
    """Update lamp timer sensor. Compare retrieved lamp hours with the last sensor value from the remote and update it if necessary"""

    try:
        #TODO #WAIT Remove h string from value when the remote ui actually shows the unit
        current_value = get_lamp_hours(ip)+" h"
    except Exception as e:
        _LOG.warning("Can't get lamp hours from projector. Use empty sensor value")
        current_value = ""
        raise Exception(e) from e

    try:
        #TODO #WAIT Change to configured_entities once the UC Python library supports this
        stored_states = await driver.api.available_entities.get_states()
    except Exception as e:
        raise Exception(e) from e

    if stored_states != []:
        attributes_stored = stored_states[1]["attributes"] # [1] = 2nd entity that has been added
    else:
        raise Exception("Got empty states from remote. Please make sure to add configured entities")

    try:
        stored_value = attributes_stored["value"]
    except KeyError as e:
        _LOG.info("Lamp timer sensor value has not been set yet")
        stored_value = "0"

    if current_value == "":
        _LOG.warning("Couldn't get lamp hours from projector. Set state to Unknown")
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.UNKNOWN, ucapi.sensor.Attributes.VALUE: current_value, ucapi.sensor.Attributes.UNIT: "h"}
    else:
        attributes_to_send = {ucapi.sensor.Attributes.STATE: ucapi.sensor.States.ON, ucapi.sensor.Attributes.VALUE: current_value, ucapi.sensor.Attributes.UNIT: "h"}

    if stored_value == current_value:
        _LOG.debug("Lamp hours have not changed since the last update. Skipping update process")
    else:
        try:
            api_update_attributes = driver.api.configured_entities.update_attributes(entity_id, attributes_to_send)
        except Exception as e:
            _LOG.error(e)
            raise Exception("Error while updating sensor value for entity id " + entity_id) from e

        if not api_update_attributes:
            raise Exception("Sensor entity " + entity_id + " not found. Please make sure it's added as a configured entity on the remote")
      
        _LOG.info("Updated lamp timer sensor value to " + current_value)
