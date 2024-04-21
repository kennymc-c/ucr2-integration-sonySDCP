import json
import os
import logging

_LOG = logging.getLogger(__name__)

CFG_FILENAME = "config.json"
SDCP_PORT = 53484 #Currently only used for port check during setup
SDAP_PORT = 53862 #Currently only used for port check during setup
POLLER_INTERVAL = 20 #Set to 0 to deactivate

#TODO Integrate SDCP and SDAP port and PJTalk community as variables into the command assigner to replace the pySDCP variables



class setup:
    __conf = {
    "ip": "",
    "id": "",
    "name": "",
    "setup_complete": False,
    "standby": False
    }
    __setters = ["ip", "id", "name", "setup_complete", "standby"]

    @staticmethod
    def get(value):
        if setup.__conf[value] != "":
            return setup.__conf[value]
        else:
            _LOG.error("Got empty value from runtime storage")

    @staticmethod
    def set(key, value):
        if key in setup.__setters:

            #Store runtime config
            setup.__conf[key] = value
            _LOG.debug("Stored " + key + ": " + str(value) + " into runtime storage")
            
            #Store key/value pair in config file except standby flag

            if key != "standby":
                jsondata = {key: value}
                if os.path.isfile(CFG_FILENAME):
                    try:
                        with open(CFG_FILENAME, "r+") as f:
                            l = json.load(f)
                            l.update(jsondata)
                            f.seek(0)
                            json.dump(l, f)
                    except:
                        raise Exception("Error while storing " + key + ": " + str(value) + " into " + CFG_FILENAME)
                    
                    _LOG.debug("Stored " + key + ": " + str(value) + " into " + CFG_FILENAME)

                #Create config file first if it doesn't exists yet
                else:
                    #Skip storing setup_complete if no ip has ben set before
                    if key != "setup_complete" and setup.__conf["ip"] != "":
                        try:
                            with open(CFG_FILENAME, "w") as f:
                                json.dump(jsondata, f)
                        except:
                            raise Exception("Error while storing " + key + ": " + str(value) + " into " + CFG_FILENAME)
                        _LOG.debug("Stored " + key + ": " + str(value) + " into " + CFG_FILENAME)
        
        else:
            raise NameError("Name not accepted in set() method")
        
    @staticmethod
    def load():
        if os.path.isfile(CFG_FILENAME):

            try:
                with open(CFG_FILENAME, "r") as f:
                    configfile = json.load(f)
            except:
                raise OSError("Error while reading " + CFG_FILENAME)
            if configfile == "":
                raise OSError("Error in " + CFG_FILENAME + ". No data")
            
            setup.__conf["setup_complete"] = configfile["setup_complete"]
            _LOG.debug("Loaded setup_complete into runtime storage from " + CFG_FILENAME)

            if not setup.__conf["setup_complete"]:
                _LOG.warning("The setup was not completed the last time. Please restart the setup process")

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