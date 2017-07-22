#!/usr/bin/env python
'''
This script comunicated with the K40 Laser Cutter.

Copyright (C) 2017 Scorch www.scorchworks.com

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

import sys
import time
import os

import usb.core
import usb.util

from egv import egv
from crc8 import crc8

##############################################################################

class K40_CLASS:
    dev = None
    n_timeouts  = 10
    timeout = 200   # Time in milliseconds
    write_addr  = 0x2   # Write address
    read_addr   = 0x82  # Read address
    read_length  = 168

    packet_data_length = 30

    def __init__(self, verbose=False):
        self.dev = usb.core.find(
            idVendor=0x1a86,
            idProduct=0x5512
        )

        if self.dev is None:
            raise StandardError("Laser USB Device not found.")

        try:
            self.dev.set_configuration()
        except:
            raise StandardError("Unable to set USB Device configuration.")

        cfg = self.dev.get_active_configuration()

        ep = usb.util.find_descriptor(
            cfg[(0,0)],
            intf,
            # match the first OUT endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT
        )

        if ep == None:
            raise StandardError("Unable to match the USB 'OUT' endpoint.")

        ctrlxfer = self.dev.ctrl_transfer(         0x40,      177,   0x0102,        0,                      0, 2000)

        self._read_data()
        self._say_hello()

    def __del__(self):
        if self.dev:
            self.release()

    def unlock_rail(self):
        self._device_write(
            [73, 83, 50, 80]
        )
        self._say_hello()

    def emergency_stop(self):
        self._device_write(
            [73]
        )
        self._say_hello()

    def reset_usb(self):
        self.dev.reset()

    def release(self):
        usb.util.dispose_resources(self.dev)
        self.dev = None

    def home_position(self):
        self._device_write(
            [73, 80, 80]
        )
        self._say_hello()

    def send_data(self,data):
        self._device_write(data)

    def rapid_move(self,dxmils,dymils):
        data=[]
        egv_inst = egv(target=lambda s:data.append(s))
        egv_inst.make_move_data(dxmils,dymils)
        self.send_data(data)

    def _device_write(self, data):
        retries = 0
        for packet in self._data_to_packets(data):
            while True:
                try:
                    self.dev.write(
                        self.write_addr,
                        packet,
                        self.timeout
                    )
                    break
                except:
                    if retries < self.n_timeouts:
                        retires += 1
                    else:
                        raise StandardError('Too many timeouts')

    def _data_to_packets(self, data):
        for i in xrange(0, len(data), self.packet_data_length):
            yield _decorate_packet(
                    data[i:i + self.packet_data_length],
                )

    def _decorate_packet(self, data):
        fillup = self.packet_data_length - len(data)
        packet_data = data + [70] * fillup
        crc_sum = crc8(packet_data)
        packet = [166, 0] + packet_data + [166, crc_sum]
        return packet

    def _read_data(self):
        data = []
        while True:
            try:
                data.append(
                    self.dev.read(
                        self.read_addr,
                        self.read_length,
                        self.timeout
                    )
                )
            except:
                break
            return data

    def _say_hello(self):
        self._device_write(
            [160]
        )
        self._read_data()
