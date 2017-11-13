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
    print("Unable to load USB library (Sending data to Laser will not work.)")
import sys
import struct
import os
from shutil import copyfile
from egv import egv
import time
import traceback

##############################################################################

class K40_CLASS:
    def __init__(self):
        self.dev        = None
        self.n_timeouts = 10
        self.timeout    = 200   # Time in milliseconds
        self.write_addr = 0x2   # Write address
        self.read_addr  = 0x82  # Read address
        self.read_length= 168

        #### RESPONSE CODES ####
        self.OK          = 206
        self.BUFFER_FULL = 238
        self.CRC_ERROR   = 207
        self.UNKNOWN_1   = 236
        self.UNKNOWN_2   = 239 #after failed initialization followed by succesful initialization
        #######################
        self.hello   = [160]
        self.unlock  = [166,0,73,83,50,80,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,15]
        self.home    = [166,0,73,80,80,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,228]
        self.estop  =  [166,0,73,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,130]


    def say_hello(self):
        #255, 206, 111, 8, 19, 0
        cnt=0
        while cnt<self.n_timeouts:
            cnt=cnt+1
            try:
                self.send_packet(self.hello)
                break
            except:
                pass
        if cnt == self.n_timeouts:
            msg = "Too Many Transmission Errors (%d Status Timeouts)" %(cnt)
            raise StandardError(msg)
                
        response = None
        while response==None:
            try:
                response = self.dev.read(self.read_addr,self.read_length,self.timeout)
            except:
                response = None
        
        DEBUG = False
        if response != None:
            if DEBUG:
                if int(response[0]) != 255:
                    print "0: ", response[0]
                elif int(response[1]) != 206: 
                    print "1: ", response[1]
                elif int(response[2]) != 111:
                    print "2: ", response[2]
                elif int(response[3]) != 8:
                    print "3: ", response[3]
                elif int(response[4]) != 19: #Get a 3 if you try to initialize when already initialized
                    print "4: ", response[4]
                elif int(response[5]) != 0:
                    print "5: ", response[5]
                else:
                    print ".",
            
            if response[1]==self.OK          or \
               response[1]==self.BUFFER_FULL or \
               response[1]==self.CRC_ERROR   or \
               response[1]==self.UNKNOWN_1   or \
               response[1]==self.UNKNOWN_2:
                return response[1]
            else:
                return None
        else:
            return None

    
    def unlock_rail(self):
        self.send_packet(self.unlock)

    def e_stop(self):
        self.send_packet(self.estop)

    def home_position(self):
        self.send_packet(self.home)

    def reset_usb(self):
        self.dev.reset()

    def release_usb(self):
        usb.util.dispose_resources(self.dev)
        self.dev = None
    
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
    
    def send_data(self,data,update_gui=None,stop_calc=None,passes=1,preprocess_crc=True):
        if stop_calc == None:
            stop_calc=[]
            stop_calc.append(0)
        if update_gui == None:
            update_gui = self.none_function

        blank   = [166,0,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,70,166,0]
        packets = []
        packet  = blank[:]
        cnt=2
        len_data = len(data)
        for j in range(passes):
            if j == 0:
                istart = 0
            else:
                istart = 1
                data[-4]
            if passes > 1:
                if j == passes-1:
                    data[-4]=ord("F")
                else:
                    data[-4]=ord("@")
                
            for i in range(istart,len_data):
                if cnt > 31:
                    packet[-1] = self.OneWireCRC(packet[1:len(packet)-2])
                    if not preprocess_crc:
                        self.send_packet_w_error_checking(packet,update_gui,stop_calc)
                        update_gui("Sending Data to Laser = %.1f%%" %(100.0*float(i)/float(len_data)))
                    else:
                        packets.append(packet)
                        update_gui("Calculating CRC data and Generate Packets: %.1f%%" %(100.0*float(i)/float(len_data)))
                    packet = blank[:]
                    cnt = 2
                    
                    if stop_calc[0]==True:
                        raise StandardError("Action Stopped by User.")
                packet[cnt]=data[i]
                cnt=cnt+1
        packet[-1]=self.OneWireCRC(packet[1:len(packet)-2])
        if not preprocess_crc:
            self.send_packet_w_error_checking(packet,update_gui,stop_calc)
        else:
            packets.append(packet)
        packet_cnt = 0

        for line in packets:
            update_gui()
            self.send_packet_w_error_checking(line,update_gui,stop_calc)
            packet_cnt = packet_cnt+1.0
            update_gui( "Sending Data to Laser = %.1f%%" %( 100.0*packet_cnt/len(packets) ) )
        ##############################################################


    def send_packet_w_error_checking(self,line,update_gui=None,stop_calc=None):
        cnt=1
        while cnt < self.n_timeouts and True:
            try:
                self.send_packet(line)
            except:
                msg = "USB Timeout #%d" %(cnt)
                update_gui(msg)
                cnt=cnt+1
                continue
                
            ######################################
            response = self.say_hello()
            
            if response == self.BUFFER_FULL:
                while response == self.BUFFER_FULL:
                    response = self.say_hello()
                break #break and move on to next packet
            elif response == self.CRC_ERROR:
                msg = "Data transmission (CRC) error #%d" %(cnt)               
                update_gui(msg)
                cnt=cnt+1
                continue
            else: #response == self.OK:
                break #break and move on to next packet

            #elif response == self.UNKNOWN_1:
            #    msg = "Something UNKNOWN_1 happened: response=%s" %(response)
            #    break #break and move on to next packet
            #elif response == self.UNKNOWN_2:
            #    msg = "Something UNKNOWN_2 happened: response=%s" %(response)
            #    break #break and move on to next packet
            #else:
            #    msg = "Something Undefined happened: response=%s" %(response)
            #    break #break and move on to next packet
            
        if cnt == self.n_timeouts:
            msg = "Too Many Transmission Errors (%d)" %(cnt)
            update_gui(msg)
            raise StandardError(msg)
        if stop_calc[0]:
            msg="Action Stopped by User."
            update_gui(msg)
            raise StandardError(msg)
        

    def send_packet(self,line):
        self.dev.write(self.write_addr,line,self.timeout)

    def rapid_move(self,dxmils,dymils):
        data=[]
        egv_inst = egv(target=lambda s:data.append(s))
        egv_inst.make_move_data(dxmils,dymils)
        self.send_data(data)
    
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
            print("-------------- dev --------------")
            print(self.dev)
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
            print ("-------------- cfg --------------")
            print (cfg)
        intf = cfg[(0,0)]
        if verbose:
            print ("-------------- intf --------------")
            print (intf)
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
            print ("-------------- ep --------------")
            print (ep)
        #self.dev.clear_halt(ep)
        #print self.dev.get_active_configuration()
        #               dev.ctrl_transfer(bmRequestType, bRequest, wValue=0, wIndex=0, data_or_wLength = None, 2000)
        ctrlxfer = self.dev.ctrl_transfer(         0x40,      177,   0x0102,        0,                      0, 2000)
        if verbose:
            print ("---------- ctrlxfer ------------")
            print (ctrlxfer)

        #return True
        
    def hex2dec(self,hex_in):
        #format of "hex_in" is ["40","e7"]
        dec_out=[]
        for a in hex_in:
            dec_out.append(int(a,16))
        return dec_out
    

if __name__ == "__main__":
    k40=K40_CLASS()
    run_laser = False

    try:
        k40.initialize_device(verbose=True)
    # the following does not work for python 2.5
    except RuntimeError as e: #(RuntimeError, TypeError, NameError, StandardError):
        print(e)    
        print("Exiting...")
        os._exit(0) 

    #k40.initialize_device()
    print (k40.say_hello())
    #print k40.reset_position()
    #print k40.unlock_rail()
    print ("DONE")

    

    
