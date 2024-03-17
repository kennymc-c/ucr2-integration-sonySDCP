#!/usr/bin/env python3
import asyncio
import logging
from typing import Any

import ucapi
import json
import time

import pysdcp
from pysdcp.protocol import *

# import os
# os.environ["UC_INTEGRATION_INTERFACE"] = "192.168.1.101"

loop = asyncio.get_event_loop()
api = ucapi.IntegrationAPI(loop)

CFG_FILENAME = "config.json"



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
    
    # if isinstance(msg, ucapi.UserDataResponse):
    #    print("return handle_user_data_response")
    #    return await handle_user_data_response(msg)

    # user confirmation not used in our demo setup process
    # if isinstance(msg, UserConfirmationResponse):
    #     return handle_user_confirmation(msg)

    print("Error during setup")
    return ucapi.SetupError()



async def handle_driver_setup(msg: ucapi.DriverSetupRequest,) -> ucapi.SetupAction:
    """
    Start driver setup.

    Initiated by Remote Two to set up the driver.

    :param msg: value(s) of input fields in the first setup screen.
    :return: the setup action on how to continue
    """
    # No support for reconfiguration :-)
    if msg.reconfigure:
        print("Ignoring driver reconfiguration request")

    # For our demo we simply clear everything!
    # A real driver might have to handle this differently
    print("Clear all available and configured entities")
    api.available_entities.clear()
    api.configured_entities.clear()

    print("Check if ip address has been entered")
    if msg.setup_data["ip"] != "":

        print(f"Chosen ip: " + msg.setup_data["ip"])
  
        #Create Python dictionary for ip address
        ip = {"ip": msg.setup_data["ip"]}

        #Convert and store into Json config file
        with open(CFG_FILENAME, "w") as f:
            json.dump(ip, f)

        print("IP address stored in " + CFG_FILENAME)

        #Add entities with their corresponding command handler
        menu_button = ucapi.Button("menu", "Menu", cmd_handler=cmd_handler)

        print(f"Add new entities")
        api.available_entities.add(menu_button)

        print(f"Setup complete")
        return ucapi.SetupComplete()

    print("Error: No ip address has been entered")
    return ucapi.SetupError()


async def cmd_handler(
    entity: ucapi.Button, cmd_id: str, _params: dict[str, Any] | None) -> ucapi.StatusCodes:
    """
    Push button command handler.

    Called by the integration-API if a command is sent to a configured button-entity.

    :param entity: button entity
    :param cmd_id: command
    :param _params: optional command parameters
    :return: status of the command
    """

    print(f"Got {entity.id} command request: {cmd_id}")

    #print("Load ip address from config json file")
    with open(CFG_FILENAME, "r") as f:
        config = json.load(f)
    
    if config["ip"] != "":
        #Define projector object with chosen ip address
        projector = pysdcp.Projector(config["ip"])

        try:
            projector._send_command(action=ACTIONS["SET"], command=COMMANDS_IR["MENU"])
            return ucapi.StatusCodes.OK
        except:
            print("Error while executing the command")
            return ucapi.StatusCodes.SERVER_ERROR


        # attempts = 3

        # for i in range(attempts+1):
        #     try:
        #         projector._send_command(action=ACTIONS["SET"], command=COMMANDS_IR["MENU"])
        #         return ucapi.StatusCodes.OK
        #     except:
        #         print("Error while executing the command. Attempt " + str(i+1) + " of " + str(attempts))
        #         if i+1 == attempts:
        #             print("Error while executing the command. All " + str(attempts) + " attemps have failed. Please check your network")
        #             return ucapi.StatusCodes.SERVER_ERROR
        #         i = i+1
        #         time.sleep(3)
                
    else:
        print("Error in " + CFG_FILENAME + ". No ip address found")
        return ucapi.StatusCodes.CONFLICT



@api.listens_to(ucapi.Events.CONNECT)
async def on_connect() -> None:
    # When the remote connects, we just set the device state. We are ready all the time!
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)



@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """

    for entity_id in entity_ids:
        print("Subscribe entities event: " + entity_id)
        api.configured_entities.update_attributes(entity_id, {ucapi.button.Attributes.STATE: ucapi.button.States.AVAILABLE})



if __name__ == "__main__":
    logging.basicConfig()

    #Add entities with their corresponding command handler
    menu_button = ucapi.Button("menu", "Menu", cmd_handler=cmd_handler)
    print(f"Add all available entities")
    api.available_entities.add(menu_button)

    loop.run_until_complete(api.init("setup.json", driver_setup_handler))
    loop.run_forever()