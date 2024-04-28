#! py3
'''
https://github.com/Galala7/pySDCP

MIT License

Copyright (c) 2017 Guy Shapira 

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import socket
from collections import namedtuple
from struct import *

from pysdcp.protocol import *

Header = namedtuple("Header", ['version', 'category', 'community'])
ProjInfo = namedtuple("ProjInfo", ['id', 'product_name', 'serial_number', 'power_state', 'location'])


def create_command_buffer(header: Header, action, command, data=None):
    # create bytearray in the right size
    if data is not None:
        my_buf = bytearray(12)
    else:
        my_buf = bytearray(10)
    # header
    my_buf[0] = 2  # only works with version 2, don't know why
    my_buf[1] = header.category
    # community
    my_buf[2] = ord(header.community[0])
    my_buf[3] = ord(header.community[1])
    my_buf[4] = ord(header.community[2])
    my_buf[5] = ord(header.community[3])
    # command
    my_buf[6] = action
    pack_into(">H", my_buf, 7, command)
    if data is not None:
        # add data len
        my_buf[9] = 2  # Data is always 2 bytes
        # add data
        pack_into(">H", my_buf, 10, data)
    else:
        my_buf[9] = 0
    return my_buf


def process_command_response(msgBuf):
    my_header = Header(
        version=int(msgBuf[0]),
        category=int(msgBuf[1]),
        community=decode_text_field(msgBuf[2:6]))
    is_success = bool(msgBuf[6])
    command = unpack(">H", msgBuf[7:9])[0]
    data_len = int(msgBuf[9])
    if data_len != 0:
        data = unpack(">H", msgBuf[10:10 + data_len])[0]
    else:
        data = None
    return my_header, is_success, command, data


def process_SDAP(SDAP_buffer) -> (Header, ProjInfo):
    try:
        my_header = Header(
            version=int(SDAP_buffer[2]),
            category=int(SDAP_buffer[3]),
            community=decode_text_field(SDAP_buffer[4:8]))
        my_info = ProjInfo(
            id=SDAP_buffer[0:2].decode(),
            product_name=decode_text_field(SDAP_buffer[8:20]),
            serial_number=unpack('>I', SDAP_buffer[20:24])[0],
            power_state=unpack('>H', SDAP_buffer[24:26])[0],
            location=decode_text_field(SDAP_buffer[26:]))
    except Exception as e:
        print("Error parsing SDAP packet: {}".format(e))
        raise
    return my_header, my_info


def decode_text_field(buf):
    """
    Convert char[] string in buffer to python str object
    :param buf: bytearray with array of chars
    :return: string
    """
    return buf.decode().strip(b'\x00'.decode())


class Projector:
    def __init__(self, ip: str = None):
        """
        Base class for projector communication. 
        Enables communication with Projector, Sending commands and Querying Power State
         
        :param ip: str, IP address for projector. if given, will create a projector with default values to communicate
            with projector on the given ip.  i.e. "10.0.0.5"
        """
        self.info = ProjInfo(
            product_name=None,
            serial_number=None,
            power_state=None,
            location=None,
            id=None)
        if ip is None:
            # Create empty Projector object
            self.ip = None
            self.header = Header(version=None, category=None, community=None)
            self.is_init = False
        else:
            # Create projector from known ip
            # Set default values to enable immediately communication with known project (ip)
            self.ip = ip
            self.header = Header(category=10, version=2, community="SONY")
            self.is_init = True

        # Default ports
        self.UDP_IP = ""
        self.UDP_PORT = 53862
        self.TCP_PORT = 53484
        self.TCP_TIMEOUT = 2
        self.UDP_TIMEOUT = 31

        # Valid settings
        self.SCREEN_SETTINGS = {
            "ASPECT_RATIO": ASPECT_RATIOS,
            "PICTURE_POSITION": PICTURE_POSITIONS,
            }

    def __eq__(self, other):
        return self.info.serial_number == other.info.serial_number

    def _send_command(self, action, command, data=None, timeout=None):
        timeout = timeout if timeout is not None else self.TCP_TIMEOUT
        if not self.is_init:
            self.find_projector()
        if not self.is_init:
            raise Exception("No projector found and / or specified")

        my_buf = create_command_buffer(self.header, action, command, data)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((self.ip, self.TCP_PORT))
            sent = sock.send(my_buf)
        except socket.timeout as e:
            raise Exception("Timeout while trying to send command {}".format(command)) from e

        if len(my_buf) != sent:
           raise ConnectionError(
              "Failed sending entire buffer to projector. Sent {} out of {} !".format(sent, len(my_buf)))

        #Check if command is an simulated ir command without a response from the projector and always return true to avoid a timeout
        if data is None and str(hex(command)).startswith(("0x17", "0x19", "0x1B")):
            sock.close()

            return True
        else:
            response_buf = sock.recv(1024)

            sock.close()

            _, is_success, _, data = process_command_response(response_buf)

            if not is_success:
                command = "{:x}".format(command)
                try:
                    error_msg = RESPONSE_ERRORS[data]
                except KeyError:
                    error_code = "{:x}".format(data)
                    error_msg = "Unknown error code: " + error_code
                raise Exception("Received failed status from projector while sending command 0x" + command + ". " + error_msg)
            
            return data

    def find_projector(self, udp_ip: str = None, udp_port: int = None, timeout=None):

        self.UDP_PORT = udp_port if udp_port is not None else self.UDP_PORT
        self.UDP_IP = udp_ip if udp_ip is not None else self.UDP_IP
        timeout = timeout if timeout is not None else self.UDP_TIMEOUT

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        sock.bind((self.UDP_IP, self.UDP_PORT))

        sock.settimeout(timeout)
        try:
            SDAP_buffer, addr = sock.recvfrom(1028)
        except socket.timeout as e:
            return False

        self.header, self.info = process_SDAP(SDAP_buffer)
        self.ip = addr[0]
        self.is_init = True

    def get_pjinfo(self, udp_ip: str = None, udp_port: int = None, timeout=None):
        '''
        Returns ip, serial and model name from projector via SDAP advertisement service as a dictionary. Can take up to 30 seconds.
        '''
        self.UDP_PORT = udp_port if udp_port is not None else self.UDP_PORT
        self.UDP_IP = udp_ip if udp_ip is not None else self.UDP_IP
        timeout = timeout if timeout is not None else self.UDP_TIMEOUT

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        sock.bind((self.UDP_IP, self.UDP_PORT))

        sock.settimeout(timeout)
        try:
            SDAP_buffer, addr = sock.recvfrom(1028)
        except socket.timeout:
            raise Exception("Timeout while waiting for data from projector")
        
        serial = unpack('>I', SDAP_buffer[20:24])[0]
        model = decode_text_field(SDAP_buffer[8:20])
        ip = addr[0]

        result = {"model":model, "serial":serial, "ip":ip}

        return result

    def set_power(self, on=True):
        self._send_command(action=ACTIONS["SET"], command=COMMANDS["SET_POWER"],
                           data=POWER_STATUS["START_UP"] if on else POWER_STATUS["STANDBY"])
        return True

    def set_HDMI_input(self, hdmi_num: int):
        self._send_command(action=ACTIONS["SET"], command=COMMANDS["INPUT"],
                           data=INPUTS["HDMI1"] if hdmi_num == 1 else INPUTS["HDMI2"])
        return True
    
    def get_input(self):
        data = self._send_command(action=ACTIONS["GET"], command=COMMANDS["INPUT"])
        if data == INPUTS["HDMI1"]:
            return "HDMI 1"
        elif data == INPUTS["HDMI2"]:
            return "HDMI 2"

    def set_screen(self, command: str, value: str):
        valid_values = self.SCREEN_SETTINGS.get(command)
        if valid_values is None:
            raise Exception("Invalid screen setting {}".format(command))

        if value not in valid_values:
            raise Exception("Invalid parameter: {}. Expected one of: {}".format(value, valid_values.keys()))

        self._send_command(action=ACTIONS["SET"], command=COMMANDS[command],
                           data=valid_values[value])
        return True

    def get_power(self):
        data = self._send_command(action=ACTIONS["GET"], command=COMMANDS["GET_STATUS_POWER"])
        if data == POWER_STATUS["STANDBY"] or data == POWER_STATUS["COOLING"] or data == POWER_STATUS["COOLING2"]:
            return False
        else:
            return True
        
    def get_muting(self):
        data = self._send_command(action=ACTIONS["GET"], command=COMMANDS["PICTURE_MUTING"])
        if data == PICTURE_MUTING["OFF"]:
            return False
        else:
            return True
        
    def set_muting(self, on=True):
        self._send_command(action=ACTIONS["SET"], command=COMMANDS["PICTURE_MUTING"],
                           data=PICTURE_MUTING["ON"] if on else PICTURE_MUTING["OFF"])
        return True
    
    def set_aspect(self, aspect):
        self._send_command(action=ACTIONS["SET"], command=COMMANDS["ASPECT_RATIO"],
                           data=ASPECT_RATIOS[aspect])
        return True
    
    def set_preset(self, preset):
        self._send_command(action=ACTIONS["SET"], command=COMMANDS["CALIBRATION_PRESET"],
                           data=CALIBRATION_PRESETS[preset])
        return True


if __name__ == '__main__':
    # b = Projector()
    # b.find_projector(timeout=1)
    # # print(b.get_power())
    # # b = Projector("10.0.0.139")
    # # #
    # print(b.get_power())
    # print(b.set_power(False))
    # # import time
    # # time.sleep(7)
    # print (b.set_HDMI_input(1))
    # # time.sleep(7)
    # # print (b.set_HDMI_input(2))
    pass
