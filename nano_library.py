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
try:
    import usb.core
    import usb.util
except:
    print "Unable to load USB library (Sending data to Laser will not work.)"
import sys
import time

import struct
import os
#from time import time
from shutil import copyfile
from egv import egv

##############################################################################

class K40_CLASS:
    def __init__(self):
        self.dev        = None
        self.n_timeouts = 10
        self.timeout    = 200   # Time in milliseconds
        self.write_addr = 0x2   # Write address
        self.read_addr  = 0x82  # Read address
        self.read_length= 168
        
        self.hello   = [160]
        self.unlock  = [166,0,73,83,50,80,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,15]
        self.home    = [166,0,73,80,80,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,228]
        self.estop  =  [166,0,73,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,130]
        
    def say_hello(self):
        self.dev.write(self.write_addr,self.hello,self.timeout)
        return self.read_data()

    def send_array(self,array):
        self.dev.write(self.write_addr,array,self.timeout)
        self.read_data()
    
    def unlock_rail(self):
        self.dev.write(self.write_addr,self.unlock,self.timeout)
        return self.say_hello()

    def e_stop(self):
        self.dev.write(self.write_addr,self.estop,self.timeout)
        return self.say_hello()

    def reset_usb(self):
        self.dev.reset()

    def release_usb(self):
        usb.util.dispose_resources(self.dev)
        self.dev = None

    def home_position(self):
        self.dev.write(self.write_addr,self.home,self.timeout)
        self.say_hello()
        return self.say_hello()
    
    #######################################################################
    #  The one wire CRC algorithm is derived from the OneWire.cpp Library
    #  The latest version of this library may be found at:
    #  http://www.pjrc.com/teensy/td_libs_OneWire.html
    #######################################################################
    def OneWireCRC(self,line):
        crc=0
        for i in range(len(line)):
            inbyte=line[i]
            for j in range(8):
                mix = (crc ^ inbyte) & 0x01
                crc >>= 1
                if (mix):
                    crc ^= 0x8C
                inbyte >>= 1
        return crc
    #######################################################################
    def none_function(self,dummy=None):
        #Don't delete this function (used in send_data)
        pass
    
    def send_data(self,data,update_gui=None,stop_calc=None):
        if stop_calc == None:
            stop_calc=[]
            stop_calc.append(0)
        if update_gui == None:
            update_gui = self.none_function

        blank   = [166,0,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,0]
        packets = []
        packet  = blank[:]
        cnt=2
        #for d in data:
        len_data = len(data)
        for i in range(len_data):
            if cnt > 31:
                packet[-1] = self.OneWireCRC(packet[1:len(packet)-2])
                packets.append(packet)
                packet = blank[:]
                cnt = 2
                update_gui("Calculating CRC data and Generate Packets: %.1f%%" %(100.0*float(i)/float(len_data)))
                if stop_calc[0]==True:
                    raise StandardError("Action Stoped by User.")
            packet[cnt]=data[i]
            cnt=cnt+1
        packet[-1]=self.OneWireCRC(packet[1:len(packet)-2])
        packets.append(packet)
        packet_cnt = 0

        update_gui("Sending Data to Laser...")
        for line in packets:
            update_gui()
            cnt=1
            while cnt < self.n_timeouts and True:
                try:
                    self.dev.write(self.write_addr,line,self.timeout)
                    packet_cnt = packet_cnt+1.0
                    break #break and move on to next packet
                except:
                    cnt=cnt+1
                    update_gui("Timeout #%d, packet number %d of %d" %(cnt,packet_cnt,len(packets)))
            if cnt == self.n_timeouts:
                update_gui("Too Many Timeouts(%d) Quiting..." %(cnt))
                break
            if stop_calc[0]:
                update_gui("User Commanded Stop")
                return
            update_gui( "Sending Data to Laser = %.1f%%" %( 100.0*packet_cnt/len(packets) ) )
        ##############################################################
        update_gui( "Packets sent = %d of %d" %( packet_cnt, len(packets) ) )
        
    def rapid_move(self,dxmils,dymils):
        data=[]
        egv_inst = egv(target=lambda s:data.append(s))
        egv_inst.make_move_data(dxmils,dymils)
        self.send_data(data)

    def read_data(self):
        data = []
        while True:
            try:
                data.append(self.dev.read(self.read_addr,self.read_length,self.timeout))
            except:
                break
            return data
    
    def initialize_device(self,verbose=False):
        try:
            self.release_usb()
        except:
            pass
        # find the device
        self.dev = usb.core.find(idVendor=0x1a86, idProduct=0x5512)
        if self.dev is None:
            raise StandardError("Laser USB Device not found.")
            #return "Laser USB Device not found."

        if verbose:
            print "-------------- dev --------------"
            print self.dev
        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        try:
            self.dev.set_configuration()
        except:
            #return "Unable to set USB Device configuration."
            raise StandardError("Unable to set USB Device configuration.")

        # get an endpoint instance
        cfg = self.dev.get_active_configuration()
        if verbose:
            print "-------------- cfg --------------"
            print cfg
        intf = cfg[(0,0)]
        if verbose:
            print "-------------- intf --------------"
            print intf
        ep = usb.util.find_descriptor(
            intf,
            # match the first OUT endpoint
            custom_match = \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
        if ep == None:
            raise StandardError("Unable to match the USB 'OUT' endpoint.")
        if verbose:
            print "-------------- ep --------------"
            print ep
        #self.dev.clear_halt(ep)
        #print self.dev.get_active_configuration()
        #               dev.ctrl_transfer(bmRequestType, bRequest, wValue=0, wIndex=0, data_or_wLength = None, 2000)
        ctrlxfer = self.dev.ctrl_transfer(         0x40,      177,   0x0102,        0,                      0, 2000)
        if verbose:
            print "---------- ctrlxfer ------------"
            print ctrlxfer

        #return True
        
    def hex2dec(self,hex_in):
        #format of "hex_in" is ["40","e7"]
        dec_out=[]
        for a in hex_in:
            dec_out.append(int(a,16))
        return dec_out
    
    def open_egv_file_print_feed(self,filename):
        try:
            fin = open(filename,'r')
        except:
            print "Unable to open file: %s" %(filename)
            return

        cur = ""
        data = []
        c = True
        while c:
            c = fin.read(1)
            if c=="%" or c=="G":
                data.append(cur)
                cur=""
            cur = cur+c
            last = c
            
        data.append(cur)
        print data[6]


    def open_egv_file_print_data(self,filename):
        try:
            fin = open(filename,'r')
        except:
            print "Unable to open file: %s" %(filename)
            return

        header=""
        c = fin.read(1)
        while c!="%":
            header = header+c
            c = fin.read(1)


        # %Ystart_pos %Xstart_pos %Yend_pos %Xend_pos  (start pos is the location of the head before the coade is run)
        # value = 39.4 * position in mm (at least for 10mm)
        
        header_pct = ""
        while c!="V":
            header_pct=header_pct+c
            c = fin.read(1)

        feed_rate = ""
        for i in range(0,8):
            feed_rate=feed_rate+c
            c = fin.read(1)

        cur = ""
        while c:
            if c=="F":
                Fpos =  fin.tell()
                NSE = fin.read(3)
                if NSE=="NSE":
                    cur=cur+" FNSE"
                    c=" "
                    
            if c=="R" or c=="B" or c=="N":
                cur=cur+" "+c+" "
            else:
                cur=cur+c
            c = fin.read(1)
            

        print "%-20s  " %(header_pct),feed_rate,cur
if __name__ == "__main__":

    k40=K40_CLASS()
    run_laser = False

    try:
        k40.initialize_device(verbose=True)
    # the following does not work for python 2.5
    except StandardError as e: #(RuntimeError, TypeError, NameError, StandardError):
        print e    
        print "Exiting..."
        os._exit(0) 

    #k40.initialize_device()
    print k40.read_data()
    print k40.say_hello()
    #print k40.reset_position()
    #print k40.unlock_rail()
    print "DONE"

    

    
