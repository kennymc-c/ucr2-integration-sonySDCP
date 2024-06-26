#!/usr/bin/env python3

import asyncio
import logging

import ipaddress
import socket
import ucapi

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

    if msg.reconfigure and config.setup.get("setup_complete"):
        _LOG.info("Starting reconfiguration")
        config.setup.set("setup_reconfigure", True)

    ip = msg.setup_data["ip"]

    if ip != "":
        #Check if input is a valid ipv4 or ipv6 address
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            _LOG.error("The entered ip address \"" + ip + "\" is not valid")
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.NOT_FOUND)

        _LOG.info("Entered ip address: " + ip)

        #Check if SDCP/SDAP ports are open on the entered ip address
        _LOG.info("Check if SDCP Port " +  str(config.SDCP_PORT) + " is open")

        if not port_check(ip, config.SDCP_PORT):
            _LOG.error("Timeout while connecting to SDCP port " + str(config.SDCP_PORT) + " on " + ip)
            _LOG.info("Please check if you entered the correct ip of the projector and if SDCP/PJTalk is active and running on port " + str(config.SDCP_PORT))
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.CONNECTION_REFUSED)
        
        #TODO Modify port_check() to also work with UDP used for SDAP
    else:
        _LOG.info("No ip address entered. Using auto discovery mode")
    
    
    try:
        #Run blocking function set_entity_data which may need to run up to 30 seconds asynchronously in a separate thread to be able to still respond to the websocket server heartbeat ping messages in the meantime and prevent a disconnect from the websocket server
        await asyncio.gather(asyncio.to_thread(set_entity_data, ip), asyncio.sleep(1))
    except TimeoutError as t:
        _LOG.info("No response from the projector. Please check if SDAP advertisement is activated on the projector")
        _LOG.error(t)
        return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.TIMEOUT)
    except Exception as e:
        _LOG.error(e)
        return ucapi.SetupError()
    
    try:
        entity_id = config.setup.get("id")
        entity_name = config.setup.get("name")
    except Exception as e:
        _LOG.error(e)
        return ucapi.SetupError()

    _LOG.info("Add media player entity with id " + entity_id + " and name " + entity_name)
    await media_player.add_mp(entity_id, entity_name)

    if config.POLLER_INTERVAL == 0:
        _LOG.info("POLLER_INTERVAL set to " + str(config.POLLER_INTERVAL) + ". Skip creation of attributes poller task")
    else:
        driver.loop.create_task(driver.attributes_poller(config.setup.get("id"), config.POLLER_INTERVAL))
        _LOG.debug("Created attributes poller task with an interval of " + str(config.POLLER_INTERVAL) + " seconds")

    config.setup.set("setup_complete", True)
    _LOG.info("Setup complete")
    return ucapi.SetupComplete()
    


def set_entity_data(man_ip: str = None):
    _LOG.info("Query data from projector via SDAP advertisement service")
    _LOG.info("This may take up to 30 seconds depending on the advertisement interval setting of the projector")

    try:
        pjinfo = pysdcp.Projector(man_ip).get_pjinfo()
    except Exception as e:
        raise TimeoutError(e)
    
    if pjinfo != "":
        _LOG.info("Got data from projector")
        if "serial" and "model" and "ip" in pjinfo:
            if man_ip == "":
                if pjinfo["ip"] != "":
                    ip = pjinfo["ip"]
                    
                    _LOG.debug("Auto discovered IP: " + ip)
                else:
                    raise Exception("Got empty ip from projector")
            else:
                _LOG.debug("Manually entered IP: " + man_ip)
            
            if pjinfo["model"] or str(pjinfo["serial"]) != "":
                id = pjinfo["model"] + "-" + str(pjinfo["serial"])
                name= "Sony " + pjinfo["model"]

                _LOG.debug("Generated ID and name from serial and model")
                _LOG.debug("ID: " + id)
                _LOG.debug("Name: " + name)
            else:
                raise Exception("Got empty model and serial from projector")

            try:
                if man_ip == "":
                    config.setup.set("ip", ip)
                else:
                    config.setup.set("ip", man_ip)
                config.setup.set("id", id)
                config.setup.set("name", name)
            except Exception as e:
                raise Exception(e)
            
            return True

        else:
            raise Exception("Unknown values from projector: " + pjinfo)
    else:
        raise Exception("Got no data from projector")
    