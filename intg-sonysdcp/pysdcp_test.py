import pysdcp
from pysdcp.protocol import *

SonyVW270 = pysdcp.Projector('192.168.1.107')

#IR Befehl
#command=SonyVW270._send_command(action=ACTIONS["SET"], command=COMMANDS_IR["MENU"])
command=print(SonyVW270.get_power())
#command=SonyVW270._send_command(action=ACTIONS["SET"], command=COMMANDS["STATUS"], data=STATUS["ON"])

try:
    command
    print('Alles OK')
except:
    print('Fehler')