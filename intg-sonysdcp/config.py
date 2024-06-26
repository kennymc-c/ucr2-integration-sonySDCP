import json
import os
import logging
import ucapi

_LOG = logging.getLogger(__name__)

#TODO Integrate SDCP and SDAP port and PJTalk community as variables into the command assigner to replace the pySDCP default values
#TODO Make poller interval, SDCP & SDAP ports and PJTalk community user configurable in an advanced setup option

SDCP_PORT = 53484 #Currently only used for port check during setup
SDAP_PORT = 53862 #Currently only used for port check during setup
POLLER_INTERVAL = 20 #Use to 0 to deactivate #TODO Deactivate by default once integrations can be uploaded to the remote to reduce power consumption #TODO Make configurable in setup flow
CFG_FILENAME = "config.json"



class mp_def:
    device_class = ucapi.media_player.DeviceClasses.TV
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
    attributes = {
        ucapi.media_player.Attributes.STATE: ucapi.media_player.States.UNKNOWN,
        ucapi.media_player.Attributes.MUTED: False,
        ucapi.media_player.Attributes.SOURCE: "",
        ucapi.media_player.Attributes.SOURCE_LIST: ["HDMI 1", "HDMI 2"]
        }
    options = {
        ucapi.media_player.Options.SIMPLE_COMMANDS: [
            "MODE_PRESET_REF",
            "MODE_PRESET_USER",
            "MODE_PRESET_TV",
            "MODE_PRESET_PHOTO",
            "MODE_PRESET_GAME",
            "MODE_PRESET_BRIGHT_CINEMA",
            "MODE_PRESET_BRIGHT_TV",
            "MODE_PRESET_CINEMA_FILM_1",
            "MODE_PRESET_CINEMA_FILM_2",
            "MODE_ASPECT_RATIO_NORMAL",
            "MODE_ASPECT_RATIO_ZOOM_1_85",
            "MODE_ASPECT_RATIO_ZOOM_2_35",
            "MODE_ASPECT_RATIO_V_STRETCH",
            "MODE_ASPECT_RATIO_SQUEEZE",
            "MODE_ASPECT_RATIO_STRETCH",
            "MODE_MOTIONFLOW_OFF",
            "MODE_MOTIONFLOW_SMOTH_HIGH",
            "MODE_MOTIONFLOW_SMOTH_LOW",
            "MODE_MOTIONFLOW_IMPULSE",
            "MODE_MOTIONFLOW_COMBINATION",
            "MODE_MOTIONFLOW_TRUE_CINEMA",
            "MODE_HDR_ON",
            "MODE_HDR_OFF",
            "MODE_HDR_AUTO",
            "MODE_2D_3D_SELECT_AUTO",
            "MODE_2D_3D_SELECT_3D",
            "MODE_2D_3D_SELECT_2D",
            "MODE_3D_FORMAT_SIMULATED_3D",
            "MODE_3D_FORMAT_SIDE_BY_SIDE",
            "MODE_3D_FORMAT_OVER_UNDER",
            "LAMP_CONTROL_LOW",
            "LAMP_CONTROL_HIGH",
            "INPUT_LAG_REDUCTION_ON",
            "INPUT_LAG_REDUCTION_OFF",
            "MENU_POSITION_BOTTOM_LEFT",
            "MENU_POSITION_CENTER",
            "LENS_SHIFT_UP",
            "LENS_SHIFT_DOWN",
            "LENS_SHIFT_LEFT",
            "LENS_SHIFT_RIGHT",
            "LENS_FOCUS_FAR",
            "LENS_FOCUS_NEAR",
            "LENS_ZOOM_LARGE",
            "LENS_ZOOM_SMALL",
            ]
        }



class setup:
    __conf = {
    "ip": "",
    "id": "",
    "name": "",
    "setup_complete": False,
    "setup_reconfigure": False,
    "standby": False
    }
    __setters = ["ip", "id", "name", "setup_complete", "setup_reconfigure", "standby"]
    __storers = ["setup_complete", "ip", "id", "name"] #Skip runtime only related values in config file


    @staticmethod
    def get(value):
        if setup.__conf[value] != "":
            return setup.__conf[value]
        else:
            _LOG.error("Got empty value from runtime storage")

    @staticmethod
    def set(key, value):

        if key in setup.__setters:
            if setup.__conf["setup_reconfigure"] == True and key == "setup_complete":
                _LOG.debug("Ignore setting and storing setup_complete flag during reconfiguration")
            else:
                setup.__conf[key] = value
                _LOG.debug("Stored " + key + ": " + str(value) + " into runtime storage")
            
                #Store key/value pair in config file
                if key in setup.__storers:
                    jsondata = {key: value}
                    if os.path.isfile(CFG_FILENAME):
                        try:
                            with open(CFG_FILENAME, "r+", encoding="utf-8") as f:
                                l = json.load(f)
                                l.update(jsondata)
                                f.seek(0)
                                f.truncate() #Needed when the new value has less characters than the old value (e.g. false to true)
                                json.dump(l, f)
                                _LOG.debug("Stored " + key + ": " + str(value) + " into " + CFG_FILENAME)
                        except:
                            raise Exception("Error while storing " + key + ": " + str(value) + " into " + CFG_FILENAME)

                    #Create config file first if it doesn't exists yet
                    else:
                        #Skip storing setup_complete if no config files exists
                        if key != "setup_complete":
                            try:
                                with open(CFG_FILENAME, "w", encoding="utf-8") as f:
                                    json.dump(jsondata, f)
                                _LOG.debug("Stored " + key + ": " + str(value) + " into " + CFG_FILENAME)
                            except OSError as o:
                                raise Exception(o)
                            except:
                                raise Exception("Error while storing " + key + ": " + str(value) + " into " + CFG_FILENAME)
                else:
                    _LOG.debug(key + " not found in __storers because it should not be stored in the config file")
        else:
            raise NameError(key + " not found in __setters because it should not be changed")

    @staticmethod
    def load():
        if os.path.isfile(CFG_FILENAME):

            try:
                with open(CFG_FILENAME, "r", encoding="utf-8") as f:
                    configfile = json.load(f)
            except:
                raise OSError("Error while reading " + CFG_FILENAME)
            if configfile == "":
                raise OSError("Error in " + CFG_FILENAME + ". No data")
            
            setup.__conf["setup_complete"] = configfile["setup_complete"]
            _LOG.debug("Loaded setup_complete: " + str(configfile["setup_complete"]) + " into runtime storage from " + CFG_FILENAME)

            if not setup.__conf["setup_complete"]:
                _LOG.warning("The setup was not completed the last time. Please restart the setup process")
            else:
                if "ip" in configfile:
                    setup.__conf["ip"] = configfile["ip"]
                    _LOG.debug("Loaded ip into runtime storage from " + CFG_FILENAME)
                else:
                    _LOG.debug("Skip loading ip as it's not yet stored in the config file")

                if "id" and "name" in configfile:
                    setup.__conf["id"] = configfile["id"]
                    setup.__conf["name"] = configfile["name"]
                    _LOG.debug("Loaded id and name into runtime storage from " + CFG_FILENAME)
                else:
                    _LOG.debug("Skip loading id and name as there are not yet stored in the config file")

        else:
            _LOG.info(CFG_FILENAME + " does not exist (yet). Please start the setup process")
