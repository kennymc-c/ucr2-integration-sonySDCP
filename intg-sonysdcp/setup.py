#!/usr/bin/env python3

"""Module that includes all functions needed for the setup and reconfiguration process"""

import asyncio
import logging

from ipaddress import ip_address
import socket
import ucapi

import config
import driver
import projector
import media_player
import sensor
import remote

_LOG = logging.getLogger(__name__)



async def init():
    """Advertises the driver metadata and first setup page to the remote using driver.json"""
    await driver.api.init("driver.json", driver_setup_handler)



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
    if isinstance(msg, ucapi.UserDataResponse):
        return await handle_user_data_response(msg)
    elif isinstance(msg, ucapi.AbortDriverSetup):
        _LOG.info("Setup was aborted with code: %s", msg.error)

    _LOG.error("Error during setup")
    config.Setup.set("setup_complete", False)
    return ucapi.SetupError()



async def handle_driver_setup(msg: ucapi.DriverSetupRequest,) -> ucapi.SetupAction:
    """
    Start driver setup.

    Initiated by Remote Two to set up the driver.

    :param msg: value(s) of input fields in the first setup screen.
    :return: the setup action on how to continue
    """

    if msg.reconfigure and config.Setup.get("setup_complete"):
        _LOG.info("Starting reconfiguration")
        config.Setup.set("setup_reconfigure", True)

    if msg.setup_data["advanced_settings"] == "true":
        _LOG.info("Entering advanced setup settings")

        try:
            try:
                ip = config.Setup.get("ip")
            except ValueError:
                ip = ""
            sdcp_port = config.Setup.get("sdcp_port")
            sdap_port = config.Setup.get("sdap_port")
            pjtalk_community = config.Setup.get("pjtalk_community")
            mp_poller_interval = config.Setup.get("mp_poller_interval")
            lt_poller_interval = config.Setup.get("lt_poller_interval")
        except ValueError as v:
            _LOG.error(v)

        return ucapi.RequestUserInput(
            {
                "en": "Advanced Configuration",
                "de": "Erweiterte Konfiguration"
            },
            [
                {
                  "id": "ip",
                  "label": {
                            "en": "Projector IP (leave empty to use auto discovery):",
                            "de": "Projektor-IP (leer lassen zur automatischen Erkennung):"
                            },
                   "field": {"text": {
                                    "value": ip
                                    }
                            }
                },
                {
                  "id": "sdcp_port",
                  "label": {
                            "en": "SDCP control port (TCP):",
                            "de": "SDCP Steuerungs-Port (TCP):"
                            },
                   "field": {"number": {
                                    "value": sdcp_port,
                                    "decimals": 1
                                        }
                            }
                },
                {
                  "id": "sdap_port",
                  "label": {
                            "en": "SDAP advertisement port (UDP):",
                            "de": "SDAP Ankündigungs-Port (UDP):"
                            },
                   "field": {"number": {
                                    "value": sdap_port,
                                    "decimals": 1
                                        }
                            }
                },
                {
                  "id": "pjtalk_community",
                  "label": {
                            "en": "PJ Talk community:",
                            "de": "PJ Talk Community:"
                            },
                   "field": {"text": {
                                    "value": pjtalk_community
                                        }
                            }
                },
                {
                    "id": "note",
                    "label": {"en": "Poller intervals", "de": "Poller-Intervalle"},
                    "field": { "label": { "value": {
                        "en":
                            "When running this integration as a custom integration on the remote itself it is best not to change these intervals or \
                            set them as high as possible to reduce battery consumption and save cpu/memory usage. \
                            An interval set to high can lead to unstable system performance.",
                        "de":
                            "Wenn du diese Integration als Custom Integration auf der Remote selbst laufen lässt, ändere diese Intervalle am Besten nicht oder \
                            setzte sie möglichst hoch, um den Batterieverbrauch zu reduzieren und die CPU-/Arbeitsspeichernutzung zu verringern. \
                            Ein zu hoher Intervall kann zu einem instabilen System führen."
                        } }
                    }
                },
                {
                  "id": "mp_poller_interval",
                  "label": {
                            "en": "Projector power/mute/input poller interval (in seconds, 0 to deactivate):",
                            "de": "Projektor Power/Mute/Eingang Poller-Interval (in Sekunden, 0 zum Deaktivieren):"
                            },
                   "field": {"number": {
                                    "value": mp_poller_interval,
                                    "decimals": 1
                                        }
                            }
                },
                {
                  "id": "lt_poller_interval",
                  "label": {
                            "en": "Lamp timer poller interval (in seconds, 0 to deactivate):",
                            "de": "Lampen-Timer Poller-Interval (in Sekunden, 0 zum Deaktivieren):"
                            },
                   "field": {"number": {
                                    "value": lt_poller_interval,
                                    "decimals": 1
                                        }
                            }
                }
            ]
        )
    else:
        _LOG.info("Using full auto discovery mode")

        #Resetting potential previously manually entered ip, ports and community when using full auto discovery mode
        if config.Setup.get("setup_reconfigure"):
            if config.Setup.get("ip") != "":
                _LOG.info("Use empty ip value")
            if config.Setup.get("sdcp_port") != 53484:
                _LOG.info("Reset sdcp port to the default of 53484")
                config.Setup.set("sdcp_port", 53484)
            if config.Setup.get("sdap_port") != 53862:
                _LOG.info("Reset sdap port to the default of 53862")
                config.Setup.set("sdap_port", 53862)
            if config.Setup.get("pjtalk_community") != "SONY":
                _LOG.info("Reset pj talk community to the default \"SONY\"")
                config.Setup.set("pjtalk_community", "SONY")


    try:
        await setup_projector()
    except ConnectionRefusedError:
        return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.CONNECTION_REFUSED)
    except TimeoutError:
        return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.TIMEOUT)
    except Exception:
        return ucapi.SetupError()

    try:
        mp_entity_id = config.Setup.get("id")
        mp_entity_name = config.Setup.get("name")
        rt_entity_id = "remote-"+mp_entity_id
        config.Setup.set("rt-id", rt_entity_id)
        rt_entity_name = mp_entity_name
        config.Setup.set_lt_name_id(mp_entity_id, mp_entity_name)
        lt_entity_id = config.Setup.get("lt-id")
        lt_entity_name = config.Setup.get("lt-name")
    except ValueError as v:
        _LOG.error(v)
        return ucapi.SetupError()

    await media_player.add_mp(mp_entity_id, mp_entity_name)
    await remote.add_remote(rt_entity_id, rt_entity_name)
    await sensor.add_lt_sensor(lt_entity_id, lt_entity_name)

    _LOG.info("Setup complete")
    config.Setup.set("setup_complete", True)
    return ucapi.SetupComplete()



async def  handle_user_data_response(msg: ucapi.UserDataResponse) -> ucapi.SetupAction:
    """
    Process user data response in a setup process.

    Driver setup callback to provide requested user data during the setup process.

    :param msg: response data from the requested user data
    :return: the setup action on how to continue: SetupComplete if finished.
    """

    ip = msg.input_values["ip"]
    sdcp_port = int(msg.input_values["sdcp_port"])
    sdap_port = int(msg.input_values["sdap_port"])
    pjtalk_community = msg.input_values["pjtalk_community"]
    mp_poller_interval = int(msg.input_values["mp_poller_interval"])
    lt_poller_interval = int(msg.input_values["lt_poller_interval"])
    skip_entities = False
    skip_mp_poller = False
    skip_lt_poller = False

    if config.Setup.get("setup_reconfigure") and ip == config.Setup.get("ip"):
        _LOG.info("The ip address has not been changed")

        if sdcp_port == config.Setup.get("sdcp_port") and sdap_port == config.Setup.get("sdap_port") and pjtalk_community == config.Setup.get("pjtalk_community"):
            _LOG.info("No PJ talk related values have been changed. Skipping entity setup and creation.")
            skip_entities = True
    else:
        if ip != "":
            #Check if input is a valid ipv4 or ipv6 address
            try:
                ip_address(ip)
            except ValueError:
                _LOG.error("The entered ip address \"" + ip + "\" is not valid")
                return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.NOT_FOUND)
            _LOG.info("Entered ip address: " + ip)
        else:
            _LOG.info("No ip address entered. Using auto discovery mode")

    if config.Setup.get("setup_reconfigure") and mp_poller_interval == config.Setup.get("mp_poller_interval"):
        skip_mp_poller = True
    if config.Setup.get("setup_reconfigure") and lt_poller_interval == config.Setup.get("lt_poller_interval"):
        skip_lt_poller = True

    try:
        config.Setup.set("sdcp_port", sdcp_port)
        config.Setup.set("sdap_port", sdap_port)
        config.Setup.set("pjtalk_community", pjtalk_community)
        config.Setup.set("mp_poller_interval", mp_poller_interval)
        config.Setup.set("lt_poller_interval", lt_poller_interval)
    except ValueError as v:
        _LOG.error(v)
        return ucapi.SetupError()

    if not skip_entities:
        try:
            await setup_projector(ip)
        except ConnectionRefusedError:
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.CONNECTION_REFUSED)
        except TimeoutError:
            return ucapi.SetupError(error_type=ucapi.IntegrationSetupError.TIMEOUT)
        except Exception:
            return ucapi.SetupError()

        try:
            mp_entity_id = config.Setup.get("id")
            mp_entity_name = config.Setup.get("name")
            rt_entity_id = "remote-"+mp_entity_id
            config.Setup.set("rt-id", rt_entity_id)
            rt_entity_name = mp_entity_name
            config.Setup.set_lt_name_id(mp_entity_id, mp_entity_name)
            lt_entity_id = config.Setup.get("lt-id")
            lt_entity_name = config.Setup.get("lt-name")
        except ValueError as v:
            _LOG.error(v)
            return ucapi.SetupError()

        await media_player.add_mp(mp_entity_id, mp_entity_name)
        await remote.add_remote(rt_entity_id, rt_entity_name)
        await sensor.add_lt_sensor(lt_entity_id, lt_entity_name)

    if not skip_mp_poller:
        mp_entity_id = config.Setup.get("id")
        await media_player.MpPollerController.start(mp_entity_id, ip)
    if not skip_lt_poller:
        lt_entity_id = config.Setup.get("lt-id")
        await sensor.LtPollerController.start(lt_entity_id, ip)

    config.Setup.set("setup_complete", True)
    _LOG.info("Setup complete")
    return ucapi.SetupComplete()



async def setup_projector(ip:str = ""):
    """Discovery protector ip if empty. Check if sdcp port is open and trigger a test command to check if the pj talk community is correct.
    Add all entities to the remote and create poller tasks"""

    try:
        #Run blocking function set_entity_data which may need to run up to 30 seconds asynchronously in a separate thread
        #to be able to still respond to the websocket server heartbeat ping messages in the meantime and prevent a disconnect from the websocket server
        await asyncio.gather(asyncio.to_thread(set_entity_data, ip), asyncio.sleep(1))
    except TimeoutError as t:
        _LOG.info("No response from the projector. Please check if SDAP advertisement is activated on the projector")
        _LOG.error(t)
        raise TimeoutError from t
    except ConnectionRefusedError as r:
        _LOG.error(r)
        raise ConnectionRefusedError from r
    except Exception as e:
        _LOG.error(e)
        raise Exception from e

    sdcp_port = config.Setup.get("sdcp_port")
    #Use discovered ip if ip value was empty before
    if ip == "":
        ip = config.Setup.get("ip")

    #Check if sdcp port is open
    if not port_check(ip, sdcp_port):
        _LOG.error("Timeout while connecting to SDCP port " + str(sdcp_port) + " on " + ip)
        _LOG.info("Please check if you entered the correct ip of the projector and if SDCP/PJTalk is active and running on port " + str(sdcp_port))
        raise ConnectionRefusedError

    #After ip has been discovered check if PJ talk community is correct
    try:
        projector.get_lamp_hours(ip)
    except Exception as e:
        _LOG.error(e)
        _LOG.error("Test command failed. Please check if the entered PJ talk community \"" + config.Setup.get("pjtalk_community") + "\" is correct")
        raise ConnectionRefusedError from e



def set_entity_data(man_ip: str = None):
    """Retrieves data from the projector (ip, serial number, model name) via the SDAP protocol
    which can take up to 30 seconds depending on the advertisement interval setting of the projector
    
    Afterwards this data will be used to generate the entity id and name and sets and stores them to the runtime storage and config file

    :man_ip: If empty the ip retrieved from the projector data will be used
    """
    _LOG.info("Query data from projector via SDAP advertisement service")
    _LOG.info("This may take up to 30 seconds depending on the advertisement interval setting of the projector")

    try:
        pjinfo = projector.get_pjinfo(man_ip)
    except Exception as e:
        raise TimeoutError(e) from e

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
                entity_id = pjinfo["model"] + "-" + str(pjinfo["serial"])
                entity_name= "Sony " + pjinfo["model"]

                _LOG.debug("Generated entity ID and name from serial number and model name")
                _LOG.debug("ID: " + entity_id)
                _LOG.debug("Name: " + entity_name)
            else:
                raise Exception("Got empty model and serial from projector")

            try:
                if man_ip == "":
                    config.Setup.set("ip", ip)
                else:
                    config.Setup.set("ip", man_ip)
                config.Setup.set("id", entity_id)
                config.Setup.set("name", entity_name)
            except Exception as e:
                raise Exception(e) from e

            return True

        else:
            raise Exception("Unknown values from projector: " + pjinfo)
    else:
        raise Exception("Got no data from projector")



def port_check(ip, port):
    """Function to check if a specified port from a specified ip is open"""

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((ip, int(port)))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except Exception:
        return False
    finally:
        s.close()
    