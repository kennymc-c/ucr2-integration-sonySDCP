#!/usr/bin/env python3

import asyncio
import logging

import ucapi
import json
import os
import ipaddress
import socket

import pysdcp

import config
import driver
import media_player

_LOG = logging.getLogger(__name__)



def port_check(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((ip, int(port)))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except:
        return False
    finally:
        s.close()



async def init():
    await driver.api.init("setup.json", driver_setup_handler)
    


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
    elif isinstance(msg, ucapi.AbortDriverSetup):
        _LOG.info("Setup was aborted with code: %s", msg.error)

    _LOG.error("Error during setup")
    config.setup.set("setup_complete", False)
    return ucapi.SetupError()



async def handle_driver_setup(msg: ucapi.DriverSetupRequest,) -> ucapi.SetupAction:
    """
    Start driver setup.

    Initiated by Remote Two to set up the driver.

    :param msg: value(s) of input fields in the first setup screen.
    :return: the setup action on how to continue
    """

    # if msg.reconfigure:
    #     _LOG.info("Ignoring driver reconfiguration request")

    ip = msg.setup_data["ip"]

    if ip == "":
        _LOG.error("No IP address has been entered")
        return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.NOT_FOUND)
    else:
        #Check if input is a valid ipv4 or ipv6 address
        try:
            ip_object = ipaddress.ip_address(ip)
        except ValueError:
            _LOG.error("The entered ip address \"" + ip + "\" is not valid")
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.NOT_FOUND)

        _LOG.info("Chosen ip address: " + ip)

        #Check if SDCP/SDAP ports are open on the entered ip address
        _LOG.info("Check if SDCP Port " +  str(config.SDCP_PORT) + " is open")

        if not port_check(ip, config.SDCP_PORT):
            _LOG.error("Timeout while connecting to SDCP port " + str(config.SDCP_PORT) + " on " + ip)
            _LOG.info("Please check if you entered the correct ip of the projector and if SDCP/PJTalk is active and running on port " + str(config.SDCP_PORT))
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.CONNECTION_REFUSED)
        
        #TODO Modify port_check() to also work with UDP used for SDAP
        # if not port_check(ip, config.SDAP_PORT):
        #     _LOG.error("Timeout while connecting to SDAP port " + str(config.SDAP_PORT) + " on " + ip)
        #     _LOG.info("Please check if you entered the correct ip of the projector and if SDAP advertisement is active and running on port " + str(config.SDAP_PORT))
        #     return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.CONNECTION_REFUSED)
        
        #Store ip in runtime and file storage
        try:
            config.setup.set("ip", ip)
        except Exception as e:
            _LOG.error(e)
            return ucapi.SetupError()

        #Get id and name from projector
        
        #TODO Run get_pjinfo as a coroutine in the background to avoid a websocket heartbeat pong timeout because of SDAP's 30 second default advertisement interval. Doesn't work...

        # cloop = asyncio.get_running_loop()
        # cloop.run_until_complete(get_pjinfo(ip))

        #Backup solution without a coroutine:
        #This requires the user to set the SDAP interval to a lower value than the default 30 seconds (e.g. the minimum value of 10 seconds) to not to interfere with the faster websockets heartbeat interval that will drop the connection before

        try:
            await get_pjinfo(ip)
        except TimeoutError as t:
            _LOG.info("Please check if SDAP advertisement is running on the projector")
            _LOG.error(t)
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.TIMEOUT)
        except Exception as e:
            _LOG.error(e)
            return ucapi.SetupError()
        
        
        id = config.setup.get("id")
        name = config.setup.get("name")

        _LOG.info("Add media player entity with id " + id + " and name " + name)
        await media_player.add_mp(id, name)

        config.setup.set("setup_complete", True)
        _LOG.info("Setup complete")
        return ucapi.SetupComplete()
    


async def get_pjinfo(ip: str):
    _LOG.info("Query serial number and model name from projector (" + ip + ") via SDAP advertisement service")
    _LOG.info("This may take up to 30 seconds depending on the interval setting of the projector")

    try: 
        pjinfo = pysdcp.Projector(ip).get_pjinfo()
    except Exception as e:
        raise TimeoutError(e)
    
    _LOG.debug("Got data from projector")
    if "serial" and "model" in pjinfo:
        if pjinfo["model"] or str(pjinfo["serial"]) != "":
            id = pjinfo["model"] + "-" + str(pjinfo["serial"])
            name= "Sony " + pjinfo["model"]
        else:
            raise Exception("Got empty id and name")

        _LOG.debug("Generated ID and name from serial and model")
        _LOG.debug("ID: " + id)
        _LOG.debug("Name: " + name)

        try:
            config.setup.set("id", id)
            config.setup.set("name", name)
        except Exception as e:
            raise Exception(e)

    else:
        raise Exception("Unknown values from projector: " + pjinfo)