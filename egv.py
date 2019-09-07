#!/usr/bin/env python 
'''
This script reads/writes egv format

Copyright (C) 2017-2019 Scorch www.scorchworks.com

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
import struct
import os
from shutil import copyfile
from math import *
from interpolate import interpolate
from time import time
from LaserSpeed import LaserSpeed

##############################################################################
class egv:
    def __init__(self, target=lambda s: sys.stdout.write(s)):
        self.write = target
        self.Modal_dir  = 0
        self.Modal_dist = 0
        self.Modal_on   = False
        self.Modal_AX   = 0
        self.Modal_AY   = 0

        self.RIGHT = 66 #ord("B")=66
        self.LEFT  = 84 #ord("T")=84
        self.UP    = 76 #ord("L")=76
        self.DOWN  = 82 #ord("R")=82
        self.ANGLE = 77 #ord("M")=77
        self.ON    = 68 #ord("D")=68
        self.OFF   = 85 #ord("U")=85
        
        # % Yxtart % Xstart % Yend % Xend % I % C VXXXXXXX CUT_TYPE
        #
        # %Ystart_pos %Xstart_pos %Yend_pos %Xend_pos  (start pos is the location of the head before the code is run)
        # I is always I ?
        # C is C for cutting or Marking otherwise it is omitted
        # V is the start of 7 digits indicating the feed rate 255 255 1
        # CUT_TYPE cutting/marking, Engraving=G followed by the raster step in thousandths of an inch 

    def move(self,direction,distance,laser_on=False,angle_dirs=None):

        if angle_dirs==None:
            angle_dirs = [self.Modal_AX,self.Modal_AY]
            
        if direction == self.Modal_dir         \
            and laser_on == self.Modal_on      \
            and angle_dirs[0] == self.Modal_AX \
            and angle_dirs[1] == self.Modal_AY:
            self.Modal_dist = self.Modal_dist + distance

        else:
            self.flush()
            if laser_on != self.Modal_on:
                if laser_on:
                    self.write(self.ON)
                else:
                    self.write(self.OFF)
                self.Modal_on = laser_on
                    
            if direction == self.ANGLE:
                if angle_dirs[0]!=self.Modal_AX:
                    self.write(angle_dirs[0])
                    self.Modal_AX = angle_dirs[0]
                if angle_dirs[1]!=self.Modal_AY:
                    self.write(angle_dirs[1])
                    self.Modal_AY = angle_dirs[1]
                
            self.Modal_dir  = direction
            self.Modal_dist = distance

            if direction == self.RIGHT or direction == self.LEFT:
                self.Modal_AX = direction
            if direction == self.UP or direction == self.DOWN:
                self.Modal_AY = direction
                
        
    def flush(self,laser_on=None):
        if self.Modal_dist > 0:
            self.write(self.Modal_dir)
            for code in self.make_distance(self.Modal_dist):
                self.write(code)
        if (laser_on!=None) and (laser_on!=self.Modal_on):
            if laser_on:
                self.write(self.ON)
            else:
                self.write(self.OFF)
            self.Modal_on   = laser_on
        self.Modal_dist = 0

        
    #  The one wire CRC algorithm is derived from the OneWire.cpp Library
    #  The library location: http://www.pjrc.com/teensy/td_libs_OneWire.html
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
        return crcS


    def make_distance(self,dist_mils):
        dist_mils=float(dist_mils)
        if abs(dist_mils-round(dist_mils,0)) > 0.000001:
            raise Exception('Distance values should be integer value (inches*1000)')
        DIST=0.0
        code = []
        v122 = 255
        dist_milsA = int(dist_mils)
        
        for i in range(0,int(floor(dist_mils/v122))):
            code.append(122)
            dist_milsA = dist_milsA-v122
            DIST = DIST+v122
        if dist_milsA==0:
            pass
        elif dist_milsA < 26:  # codes  "a" through  "y"
            code.append(96+dist_milsA)
        elif dist_milsA < 52:  # codes "|a" through "|z"
            code.append(124)
            code.append(96+dist_milsA-25)
        elif dist_milsA < 255:
            num_str =  "%03d" %(int(round(dist_milsA)))
            code.append(ord(num_str[0]))
            code.append(ord(num_str[1]))
            code.append(ord(num_str[2]))
        else:
            raise Exception("Error in EGV make_distance_in(): dist_milsA=",dist_milsA)
        return code
    
    def make_dir_dist(self,dxmils,dymils,laser_on=False):
        adx = abs(dxmils)
        ady = abs(dymils)
        if adx > 0 or ady > 0:
            if ady > 0:
                if dymils > 0:
                    self.move(self.UP  ,ady,laser_on)
                else:
                    self.move(self.DOWN,ady,laser_on)
            if adx > 0:
                if dxmils > 0:
                    self.move(self.RIGHT,adx,laser_on)
                else:
                    self.move(self.LEFT ,adx,laser_on)
            
    def make_cut_line(self,dxmils,dymils,Spindle):
        XCODE = self.RIGHT
        if dxmils < 0.0:
            XCODE = self.LEFT
        YCODE = self.UP
        if dymils < 0.0:
            YCODE = self.DOWN
            
        if abs(dxmils-round(dxmils,0)) > 0.0 or abs(dymils-round(dymils,0)) > 0.0:
            raise Exception('Distance values should be integer value (inches*1000)')

        adx = abs(dxmils/1000.0)
        ady = abs(dymils/1000.0)

        if dxmils == 0:
            self.move(YCODE,abs(dymils),laser_on=Spindle)
        elif dymils == 0:
            self.move(XCODE,abs(dxmils),laser_on=Spindle)      
        elif dxmils==dymils:
            self.move(self.ANGLE,abs(dxmils),laser_on=Spindle,angle_dirs=[XCODE,YCODE])
        else:
            h=[]
            if adx > ady:
                slope = ady/adx
                n = int(abs(dxmils))
                CODE  = XCODE
                CODE1 = YCODE
            else:
                slope = adx/ady
                n = int(abs(dymils))
                CODE  = YCODE
                CODE1 = XCODE

            for i in range(1,n+1):
                h.append(round(i*slope,0))

            Lh=0.0
            d1=0.0
            d2=0.0
            d1cnt=0.0
            d2cnt=0.0
            for i in range(len(h)):
                if h[i]==Lh:
                    d1=d1+1
                    if d2>0.0:
                        self.move(self.ANGLE,d2,laser_on=Spindle,angle_dirs=[XCODE,YCODE])
                        d2cnt=d2cnt+d2
                        d2=0.0
                else:
                    d2=d2+1
                    if d1>0.0:
                        self.move(CODE,d1,laser_on=Spindle)
                        d1cnt=d1cnt+d1
                        d1=0.0
                Lh=h[i]

            if d1>0.0:
                self.move(CODE,d1,laser_on=Spindle)
                d1cnt=d1cnt+d1
                d1=0.0
            if d2>0.0:
                self.move(self.ANGLE,d2,laser_on=Spindle,angle_dirs=[XCODE,YCODE])
                d2cnt=d2cnt+d2
                d2=0.0

        
            DX = d2cnt
            DY = (d1cnt+d2cnt)
            if adx < ady:
                error = max(DX-abs(dxmils),DY-abs(dymils))
            else:
                error = max(DY-abs(dxmils),DX-abs(dymils))
            if error > 0:
                raise Exception("egv.py: Error delta =%f" %(error))


    def make_speed(self,Feed=None,board_name="LASER-M2",Raster_step=0):
        board_code = board_name.split('-')[1]
        speed_text = LaserSpeed.get_code_from_speed(Feed, abs(Raster_step), board=board_code)
        
        speed=[]
        for c in speed_text:
            speed.append(ord(c))
        return speed


    def make_move_data(self,dxmils,dymils):
        if (abs(dxmils)+abs(dymils)) > 0:
            self.write(73) # I
            self.make_dir_dist(dxmils,dymils)
            self.flush()
            self.write(83) #S
            self.write(49) #1 (one)
            self.write(80) #P

    #######################################################################
    def none_function(self,dummy=None):
        #Don't delete this function (used in make_egv_data)
        pass

    def ecoord_adj(self,ecoords_adj_in,scale,FlipXoffset):
        if FlipXoffset > 0:
            e0 = int(round((FlipXoffset-ecoords_adj_in[0])*scale,0))
        else:
            e0 = int(round(ecoords_adj_in[0]*scale,0))
        e1 = int(round(ecoords_adj_in[1]*scale,0))
        e2 = ecoords_adj_in[2]
        return e0,e1,e2


    def make_egv_data(self, ecoords_in,
                            startX=0,
                            startY=0,
                            units = 'in',
                            Feed = None,
                            board_name="LASER-M2",
                            Raster_step=0,
                            update_gui=None,
                            stop_calc=None,
                            FlipXoffset=0,
                            Rapid_Feed_Rate=0):

        #print("make_egv_data",Rapid_Feed_Rate,len(ecoords_in))
        #print("Rapid_Feed_Rate=",Rapid_Feed_Rate)
        ########################################################
        if stop_calc == None:
            stop_calc=[]
            stop_calc.append(0)
        if update_gui == None:
            update_gui = self.none_function
        ########################################################
        if units == 'in':
            scale      = 1000.0
        if units == 'mm':
            scale = 1000.0/25.4;

        startX = int(round(startX*scale,0))
        startY = int(round(startY*scale,0))

        ########################################################
        variable_feed_scale=None
        Spindle = True
        if Feed==None:
            variable_feed_scale = 25.4/60.0
            Feed = round(ecoords_in[0][3]*variable_feed_scale,2)
            Spindle = False
            
        speed = self.make_speed(Feed,board_name=board_name,Raster_step=Raster_step)
        
        ##self.write(ord("I"))
        #for code in speed:
        #    self.write(code)
        
        if Raster_step==0:
            #self.write(ord("I"))
            for code in speed:
                self.write(code)

            lastx,lasty,last_loop = self.ecoord_adj(ecoords_in[0],scale,FlipXoffset)
            if not Rapid_Feed_Rate:
                self.make_dir_dist(lastx-startX,lasty-startY)
            self.flush(laser_on=False)
            self.write(ord("N"))
            self.write(ord("R"))
            self.write(ord("B"))
            # Insert "S1E"
            self.write(ord("S"))
            self.write(ord("1"))
            self.write(ord("E"))
            ###########################################################
            laser   = False
            
            if Rapid_Feed_Rate:
                self.rapid_move_slow(lastx-startX,lasty-startY,Rapid_Feed_Rate,Feed,board_name)
            timestamp=0
            for i in range(1,len(ecoords_in)):
                e0,e1,e2                = self.ecoord_adj(ecoords_in[i]  ,scale,FlipXoffset)
                stamp=int(3*time()) #update every 1/3 of a second
                if (stamp != timestamp):
                    timestamp=stamp #interlock        
                    update_gui("Generating EGV Data: %.1f%%" %(100.0*float(i)/float(len(ecoords_in))))
                    if stop_calc[0]==True:
                        raise Exception("Action Stopped by User.")
            
                if ( e2  == last_loop) and (not laser):
                    laser = True
                elif ( e2  != last_loop) and (laser):
                    laser = False
                dx = e0 - lastx
                dy = e1 - lasty

                min_rapid = 5
                if (abs(dx)+abs(dy))>0:
                    if laser:
                        if variable_feed_scale!=None:
                            Feed_current    = round(ecoords_in[i][3]*variable_feed_scale,2)
                            Spindle = ecoords_in[i][4] > 0
                            if Feed != Feed_current:
                                Feed = Feed_current
                                self.flush()
                                self.change_speed(Feed,board_name,laser_on=Spindle)
                        self.make_cut_line(dx,dy,Spindle)
                    else:
                        if ((abs(dx) < min_rapid) and (abs(dy) < min_rapid)) or Rapid_Feed_Rate:
                            self.rapid_move_slow(dx,dy,Rapid_Feed_Rate,Feed,board_name)
                        else:
                            self.rapid_move_fast(dx,dy)
                        
                lastx     = e0
                lasty     = e1
                last_loop = e2
 
            if laser:
                laser = False
                
            dx = startX-lastx
            dy = startY-lasty
            if ((abs(dx) < min_rapid) and (abs(dy) < min_rapid)) or Rapid_Feed_Rate:
                self.rapid_move_slow(dx,dy,Rapid_Feed_Rate,Feed,board_name)
            else:
                self.rapid_move_fast(dx,dy)

              ###########################################################
        else: # Raster
              ###########################################################
            Rapid_flag=True
            ###################################################
            scanline = []
            scanline_y = None
            if Raster_step < 0.0:
                irange = range(len(ecoords_in))
            else:
                irange = range(len(ecoords_in)-1,-1,-1)
            timestamp=0
            for i in irange:
                #if i%1000 == 0:
                stamp=int(3*time()) #update every 1/3 of a second
                if (stamp != timestamp):
                    timestamp=stamp #interlock
                    update_gui("Preprocessing Raster Data: %.1f%%" %(100.0*float(i)/float(len(ecoords_in))))
                y    = ecoords_in[i][1]
                if y != scanline_y:
                    scanline.append([ecoords_in[i]])
                    scanline_y = y
                else:
                    if bool(FlipXoffset) ^ bool(Raster_step > 0.0): # ^ is bitwise XOR
                        scanline[-1].insert(0,ecoords_in[i])
                    else:
                        scanline[-1].append(ecoords_in[i])
            update_gui("Raster Data Ready")
            ###################################################
            lastx,lasty,last_loop = self.ecoord_adj(scanline[0][0],scale,FlipXoffset)
            
            DXstart = lastx-startX
            DYstart = lasty-startY

            if Rapid_Feed_Rate:
                self.make_egv_rapid(DXstart,DYstart,Rapid_Feed_Rate,board_name,finish=False)

            ##self.write(ord("I"))
            for code in speed:
                self.write(code)

            if not Rapid_Feed_Rate:
                self.make_dir_dist(DXstart,DYstart)

            #insert "NRB"
            self.flush(laser_on=False)
            self.write(ord("N"))
            if (Raster_step < 0.0):
                self.write(ord("R"))
            else:
                self.write(ord("L"))
            self.write(ord("B"))
            # Insert "S1E"
            self.write(ord("S"))
            self.write(ord("1"))
            self.write(ord("E"))
            dx_last   = 0

            sign = -1
            cnt = 1
            timestamp=0
            for scan_raw in scanline:
                scan = []
                for point in scan_raw:
                    e0,e1,e2 = self.ecoord_adj(point,scale,FlipXoffset)
                    scan.append([e0,e1,e2])
                stamp=int(3*time()) #update every 1/3 of a second
                if (stamp != timestamp):
                    timestamp=stamp #interlock
                    update_gui("Generating EGV Data: %.1f%%" %(100.0*float(cnt)/float(len(scanline))))
                    if stop_calc[0]==True:
                        raise Exception("Action Stopped by User.")
                cnt = cnt+1
                ######################################
                ## Flip direction and reset loop    ##
                ######################################
                sign      = -sign
                last_loop =  None
                y         =  scan[0][1]
                dy        =  y-lasty
                if sign == 1:
                    xr = scan[0][0]
                else:
                    xr = scan[-1][0]
                dxr = xr - lastx
                ######################################
                ## Make Rapid move if needed        ##
                ######################################
                if abs(dy-Raster_step) != 0 and not Rapid_flag: 
                    
                    if dxr*sign < 0:
                        yoffset = -Raster_step*3
                    else:
                        yoffset = -Raster_step
                        
                    if (dy+yoffset)*(abs(yoffset)/yoffset) < 0:
                        self.flush(laser_on=False)

                        if not Rapid_Feed_Rate:
                            self.write(ord("N"))
                            self.make_dir_dist(0,dy+yoffset)
                            self.flush(laser_on=False)
                            self.write(ord("S"))
                            self.write(ord("E"))
                        else:
                            DX=0
                            DY=dy+yoffset
                            self.raster_rapid_move_slow(DX,DY,Raster_step,Rapid_Feed_Rate,Feed,board_name)

                        Rapid_flag=True
                    else:
                        adj_steps = int(dy/Raster_step)
                        for stp in range(1,adj_steps):
                            
                            adj_dist=5
                            self.make_dir_dist(sign*adj_dist,0)
                            lastx = lastx + sign*adj_dist

                            sign  = -sign
                            if sign == 1:
                                xr = scan[0][0]
                            else:
                                xr = scan[-1][0]
                            dxr = xr - lastx
                    lasty = y

                        
                ######################################
                if sign == 1:
                    rng = range(0,len(scan),1)
                else:
                    rng = range(len(scan)-1,-1,-1)
                ######################################
                ## Pad row end if needed ##
                ###########################
                pad = 2
                if (dxr*sign <= 0.0):
                    if (Rapid_flag == False):
                        self.make_dir_dist(-sign*pad,0)
                        self.make_dir_dist( dxr,0)
                        self.make_dir_dist( sign*pad,0)
                    else:
                        self.make_dir_dist( dxr,0)
                    lastx = lastx+dxr
                    
                Rapid_flag=False
                ######################################   
                for j in rng:
                    x  = scan[j][0]
                    dx = x - lastx
                    ##################################
                    loop = scan[j][2]
                    if loop==last_loop:
                        self.make_cut_line(dx,0,True)
                    else:
                        if dx*sign > 0.0:
                            self.make_dir_dist(dx,0)
                    lastx     = x
                    last_loop = loop
                lasty = y
            
            # Make final move to ensure last move is to the right 
            self.make_dir_dist(pad,0)
            lastx = lastx + pad
            # If sign is negative the final move will have incremented the
            # "y" position so adjust the lasty to acoomodate
            if sign < 0:
                lasty = lasty + Raster_step

            self.flush(laser_on=False)


            dx_final = (startX - lastx)
            if Raster_step < 0:
                dy_final = (startY - lasty) + Raster_step
            else:
                dy_final = (startY - lasty) - Raster_step
           
            ##############################################################
            max_return_feed = 50.0
            final_feed = 0
            if Rapid_Feed_Rate:
                final_feed = Rapid_Feed_Rate
            elif Feed > max_return_feed:
                final_feed = max_return_feed

            if final_feed:
                self.change_speed(final_feed,board_name,laser_on=False,pad=False)
                dy_final = dy_final + abs(Raster_step)
                self.make_dir_dist(dx_final,dy_final)
            else:
                self.write(ord("N"))
                self.make_dir_dist(dx_final,dy_final)
                self.flush(laser_on=False)
                self.write(ord("S"))
                self.write(ord("E"))
            ##############################################################
            
           
        # Append Footer
        self.flush(laser_on=False)
        self.write(ord("F"))
        self.write(ord("N"))
        self.write(ord("S"))
        self.write(ord("E"))
        update_gui("EGV Data Complete")
        return

    def make_egv_rapid(self, DX,DY,Feed = None,board_name="LASER-M2",finish=True):
        speed = self.make_speed(Feed,board_name=board_name,Raster_step=0)
        if finish:
            self.write(ord("I"))
        for code in speed:
            self.write(code)
        self.flush(laser_on=False)
        self.write(ord("N"))
        self.write(ord("R"))
        self.write(ord("B"))
        # Insert "S1E"
        self.write(ord("S"))
        self.write(ord("1"))
        self.write(ord("E"))
        ###########################################################
        # Move Distance
        self.make_cut_line(DX,DY,Spindle=0)
        ###########################################################   
        # Append Footer
        self.flush(laser_on=False)
        if finish:
            self.write(ord("F"))
        else:
            self.write(ord("@"))
        self.write(ord("N"))
        self.write(ord("S"))
        self.write(ord("E"))
        return

    def rapid_move_slow(self,dx,dy,Rapid_Feed_Rate,Feed,board_name):
        if Rapid_Feed_Rate:
            self.change_speed(Rapid_Feed_Rate,board_name,laser_on=False)
            self.make_dir_dist(dx,dy)
            self.change_speed(Feed,board_name,laser_on=False)
        else:
            self.make_dir_dist(dx,dy)

    def raster_rapid_move_slow(self,DX,DY,Raster_step,Rapid_Feed_Rate,Feed,board_name):
        tiny_step = Raster_step/abs(Raster_step)
        self.change_speed(Rapid_Feed_Rate,board_name,laser_on=False,pad=False)
        self.make_dir_dist(DX,DY-tiny_step)
        self.flush(laser_on=False)
        self.change_speed(Feed,board_name,laser_on=False,Raster_step=Raster_step,pad=False)
        #Tiny Rapid
        self.write(ord("N"))
        self.make_dir_dist(0,tiny_step)
        self.flush(laser_on=False)
        self.write(ord("S"))
        self.write(ord("E"))


    def rapid_move_fast(self,dx,dy):
        pad = 3
        if pad == -dx:
            pad = pad+3
        self.make_dir_dist(-pad, 0  ) #add "T" move
        self.make_dir_dist(   0, pad) #add "L" move
        self.flush(laser_on=False)

        if dx+pad < 0.0:
            self.write(ord("B"))
        else:
            self.write(ord("T"))
        self.write(ord("N"))
        self.make_dir_dist(dx+pad,dy-pad)
        self.flush(laser_on=False)
        self.write(ord("S"))
        self.write(ord("E"))


    def change_speed(self,Feed,board_name,laser_on=False,Raster_step=0,pad=True):
        cspad = 5
        if laser_on:
            self.write(self.OFF)

        if pad:
            self.make_dir_dist(-cspad,-cspad)
        self.flush(laser_on=False)
        
        self.write(ord("@"))
        self.write(ord("N"))
        self.write(ord("S"))
        self.write(ord("E"))
        speed = self.make_speed(Feed,board_name,Raster_step=Raster_step)
        #print Feed,speed
        for code in speed:
            self.write(code)
        self.write(ord("N"))
        self.write(ord("R"))
        self.write(ord("B"))
        ## Insert "SIE"
        self.write(ord("S"))
        self.write(ord("1"))
        self.write(ord("E"))

        if pad:
            self.make_dir_dist(cspad,cspad)
        self.flush(laser_on=False)
        
        if laser_on:    
            self.write(self.ON)
            
        
if __name__ == "__main__":
    EGV=egv()
    bname = "LASER-M2"
    values  = [.1,.2,.3,.4,.5,.6,.7,.8,.9,1,2,3,4,5,6,7,8,9,10,20,30,40,50,70,90,100]
    step=2
    for value_in in values:
        #print ("% 8.2f" %(value_in),": ",end='')
        val=EGV.make_speed(value_in,board_name=bname,Raster_step=step)
        txt=""
        for c in val:
            txt=txt+chr(c)
        print(txt)
    print("DONE")





    
