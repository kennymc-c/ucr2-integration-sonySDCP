#!/usr/bin/env python3

import asyncio
import logging

import ucapi
import json
import os
import ipaddress
import socket

import pysdcp

import driver
import media_player

CFG_FILENAME = driver.CFG_FILENAME
id = ""
name = ""

_LOG = logging.getLogger(__name__)



async def init():
    await driver.api.init("setup.json", driver_setup_handler)



def setup_complete(value: bool):
    if value == True:
        flag = {"setup_complete": True}
        _LOG.debug("Set setup_complete flag to True")
    else:
        flag = {"setup_complete": False}
        _LOG.debug("Set setup_complete flag to False")
    if os.path.isfile(CFG_FILENAME):
        try:
            with open(CFG_FILENAME, "r+") as f:
                l = json.load(f)
                l.update(flag)
                f.seek(0)
                json.dump(l, f)
        except:
            raise Exception("Error while storing setup_complete flag")
    else:
        _LOG.error(CFG_FILENAME + " does not exist (yet)")
    


def get_setup_complete():
    if os.path.isfile(CFG_FILENAME):
        try:
            with open(CFG_FILENAME, "r") as f:
                l = json.load(f)
                flag = l["setup_complete"]
                id = l["id"]

                if flag:
                    return True
                elif not flag:
                    _LOG.warning("Last setup process was not successful")
                    return False
                # elif flag == True:
                #     if driver.api.configured_entities.contains(id):
                #         _LOG.debug("Found " + id + " in configured entities")
                #         return True
                #     elif driver.api.available_entities.contains(id):
                #         _LOG.debug("Found " + id + " in available entities")
                #         return True
                #     else:
                #         _LOG.debug("Couldn't find " + id + " in configured or available entities")
                #         _LOG.error("Setup complete flag is true but the remote returned no available or configured entities from the config file")
                #         _LOG.info("Has the integration been removed manually from the remote?")
                #         _LOG.warning("Please restart the setup process")
                #         setup_complete(False)
                #         return False
        except KeyError:
            _LOG.debug("No setup_complete flag found in " + CFG_FILENAME)
            return False
        except:
            raise Exception("Error while reading setup_complete flag from " + CFG_FILENAME)
    else:
        _LOG.info(CFG_FILENAME + " does not exist (yet). Please start the setup process")
        return False
    


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
        _LOG.debug("Setup was aborted with code: %s", msg.error)

    _LOG.error("Error during setup")
    setup_complete(False)
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

    #Check if ip address has been entered
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

        _LOG.info(f"Chosen ip address: " + ip)

        #Create Python dictionary for ip address
        ip_json = {"ip": msg.setup_data["ip"]}

        #Convert and store ip address into Json config file
        with open(CFG_FILENAME, "w") as f:
            json.dump(ip_json, f)

        _LOG.debug("IP address stored in " + CFG_FILENAME)

        #Check if SDCP Port is open
        SDCP_TCP_PORT = 53484
        _LOG.info("Check if SDCP Port " +  str(SDCP_TCP_PORT) + " is open")

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

        if not port_check(ip, SDCP_TCP_PORT):
            _LOG.error("Timeout while connecting to SDCP port " + str(SDCP_TCP_PORT) + " on " + ip)
            _LOG.info("Please check if you entered the correct ip and if SDCP/PJTalk is active and running on port " + str(SDCP_TCP_PORT))
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.CONNECTION_REFUSED)

        #Get id and name from projector
        
        #TODO Running get_pjinfo() in background doesn't work in this form
        #Preferred solution: Run get_pjinfo as a coroutine in the background to avoid a websocket heartbeat pong timeout because of SDAP's 30 second default advertisement interval

        # import nest_asyncio #Haven't found a way to prevent the loop is already running error without using this module
        # projector_data = {}

        # async def request_projector_info(ip: str):
        #   global projector_data
        #   projector_data = get_pjinfo(ip)
        #   await projector_data
        
        # global projector_data
        # nest_asyncio.apply() # Should also work with asyncio.get_running_loop() but this still results in a loop is already running error
        # loop.run_until_complete(request_projector_info(ip))


        #Backup solution without a coroutine.
        #This requires the user to set the SDAP interval to a lower value than the default 30 seconds (e.g. the minimum value of 10 seconds) to not to interfere with the faster websockets heartbeat interval that will drop the connection before
        try:
            await get_pjinfo(ip)
        except TimeoutError as t:
            _LOG.error(t)
            _LOG.info("Please check if the SDAP advertisement service is turned on")
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.TIMEOUT)
        except Exception as e:
            _LOG.error(e)
            return ucapi.SetupError()

        global id
        global name

        if id and name == "":
            _LOG.error("Got empty id and name variables")
            return ucapi.SetupError()
        elif id and name != "":
            _LOG.info("Add media player entity from ip " + ip + ", id " + id + " and name " + name)
            await media_player.add_mp(ip, id, name)

            setup_complete(True)
            _LOG.info("Setup complete")
            return ucapi.SetupComplete()



async def get_pjinfo(ip: str):

    global id
    global name

    def load_pjinfo():
        global id
        global name
        #Load entity id and name from config json file
        with open(CFG_FILENAME, "r") as f:
            config = json.load(f)  

        if "id" and "name" in config:
            _LOG.debug("Loaded id and name from " + CFG_FILENAME)
            id = config["id"]
            name = config["name"]
        else:
            return False
        
    def store_pjinfo(data):
        _LOG.debug("Append id and name into " + CFG_FILENAME)
        try:
            with open(CFG_FILENAME, "r+") as f:
                l = json.load(f)
                l.update(data)
                f.seek(0)
                json.dump(l, f)
        except:
            raise Exception("Error while storing name and id into " + CFG_FILENAME)
            
    
    #Check if config files exists and load id and name instead of query them every time
    if os.path.isfile(CFG_FILENAME):
        config = load_pjinfo()

        if config == False:
            
            _LOG.info("Query serial number and model name from projector (" + ip + ") via SDAP advertisement service")
            _LOG.info("This may take up to 30 seconds depending on the interval setting of the projector")

            try: 
                pjinfo = pysdcp.Projector(ip).get_pjinfo()
            except Exception as e:
                raise TimeoutError(e)
            
            _LOG.debug("Got data from projector")
            if "serial" and "model" in pjinfo:
                _LOG.debug("Generate ID and name from serial and model")
                id = pjinfo["model"] + "-" + str(pjinfo["serial"])
                name = "Sony " + pjinfo["model"]

                _LOG.debug("ID: " + id)
                _LOG.debug("Name: " + name)

                jsondata={"id": id, "name": name}

                store_pjinfo(jsondata)

                return True
            else:
                raise Exception("Unknown values from projector: " + pjinfo)
                
        else:
            id = config["id"]
            name = config["name"]
            return True
            
    else:
        raise Exception(CFG_FILENAME + " not found. Please restart the setup process")