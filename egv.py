#!/usr/bin/env python 
'''
This script reads/writes egv format

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
import struct
import os
from shutil import copyfile
from math import *

##############################################################################

class egv:
    #def __init__(self):
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

        
        # % Yxtart % Xstart % Yend % Xend % I % C VXXXXXXX CUT_TYPE R YYY B XXX

        # %Ystart_pos %Xstart_pos %Yend_pos %Xend_pos  (start pos is the location of the head before the code is run)
        # value = 39.37 * position in mm (at least for 10mm)
        
        # X/Y Start/End are the position in mm * 39.37
        # I is always I ?
        # C is C for cutting or Marking otherwise it is omitted
        # V is the start of 7 digits indicating the feed rate 255 255 1
        # CUT_TYPE cutting/marking, Engraving=G002
        # YYY is the position of the start of the first cut position in mm * 39.6
        # XXX is the position of the start of the first cut position in mm * 39.6

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
            #print "dist_mils = ",dist_mils
            raise StandardError('Distance values should be integer value (inches*1000)')
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
            raise StandardError("Error in EGV make_distance_in(): dist_milsA=",dist_milsA)
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
            
    
    def make_cut_line(self,dxmils,dymils):
        XCODE = self.RIGHT
        if dxmils < 0.0:
            XCODE = self.LEFT
        YCODE = self.UP
        if dymils < 0.0:
            YCODE = self.DOWN
            
        if abs(dxmils-round(dxmils,0)) > 0.0 or abs(dymils-round(dymils,0)) > 0.0:
            raise StandardError('Distance values should be integer value (inches*1000)')

        adx = abs(dxmils/1000.0)
        ady = abs(dymils/1000.0)

        if dxmils == 0:
            self.move(YCODE,abs(dymils),laser_on=True)
        elif dymils == 0:
            self.move(XCODE,abs(dxmils),laser_on=True)      
        elif dxmils==dymils:
            self.move(self.ANGLE,abs(dxmils),laser_on=True,angle_dirs=[XCODE,YCODE])
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
                        self.move(self.ANGLE,d2,laser_on=True,angle_dirs=[XCODE,YCODE])
                        d2cnt=d2cnt+d2
                        d2=0.0
                else:
                    d2=d2+1
                    if d1>0.0:
                        self.move(CODE,d1,laser_on=True)
                        d1cnt=d1cnt+d1
                        d1=0.0
                Lh=h[i]

            if d1>0.0:
                self.move(CODE,d1,laser_on=True)
                d1cnt=d1cnt+d1
                d1=0.0
            if d2>0.0:
                self.move(self.ANGLE,d2,laser_on=True,angle_dirs=[XCODE,YCODE])
                d2cnt=d2cnt+d2
                d2=0.0

        
            DX = d2cnt
            DY = (d1cnt+d2cnt)
            if adx < ady:
                error = max(DX-abs(dxmils),DY-abs(dymils))
            else:
                error = max(DY-abs(dxmils),DX-abs(dymils))
            if error > 0:
                raise StandardError("egv.py: Error delta =%f" %(error))
        #out_str=""
        #for c in cdata:
        #    out_str =out_str+"%s" %chr(c)
        #print out_str
        #print "error = ",error
        #return str #,DX,DY,error

        #return cdata

        
    def make_speed(self,Feed=None,speed_text=None,Raster_step=0):
        #speed_text = "CV1752241021000191"
        speed=[]
        if speed_text==None:
            if Feed < 7:
                B = 255.97
                M = 100.21
            else:
                B = 236
                M = 1202.5
            V  = B-M/Feed
            C1 = floor(V)
            C2 = floor((V-C1)*255)
            if Raster_step==0:
                speed_text = "CV%03d%03d%d000000000" %(C1,C2,1)
                #speed_text = "CV1752241021000191"
            else:
                speed_text =  "V%03d%03d%dG%03d" %(C1,C2,1,Raster_step)
            if Feed < 7:
                speed_text = speed_text + "C"
            
        for c in speed_text:
            speed.append(ord(c))
        return speed


    def make_move_data(self,dxmils,dymils):
        if (abs(dxmils)+abs(dymils)) > 0:
            self.write(73) # I
            self.make_dir_dist(dxmils,dymils)
            self.flush()
            self.write(83)
            self.write(49)
            self.write(80)

    #######################################################################
    def none_function(self,dummy=None):
        #Don't delete this function (used in make_egv_data)
        pass
    
    def make_egv_data(self, ecoords_in,
                            startX=0,
                            startY=0,
                            units = 'in',
                            Feed = None,
                            speed_text="V1752241021000191",
                            Raster_step=0,
                            update_gui=None,
                            stop_calc=None):
        ########################################################
        if stop_calc == None:
            stop_calc=[]
            stop_calc.append(0)
        if update_gui == None:
            update_gui = self.none_function
        ########################################################
        if units == 'in':
            scale = 1000.0
        if units == 'mm':
            scale = 1000.0/25.4;
        ecoords=[]
        for i in range(len(ecoords_in)):
            e0 = int(round(ecoords_in[i][0]*scale,0))
            e1 = int(round(ecoords_in[i][1]*scale,0))
            e2 = ecoords_in[i][2]
            ecoords.append([e0,e1,e2])
        startX = int(round(startX*scale,0))
        startY = int(round(startY*scale,0))

        ########################################################
        if Feed==None:
            speed = self.make_speed(Feed,speed_text=speed_text)
        else:
            speed = self.make_speed(Feed,Raster_step=Raster_step)
            
        self.write(ord("I"))
        for code in speed:
            self.write(code)
        
        lastx     = ecoords[0][0]
        lasty     = ecoords[0][1]
        loop_last = ecoords[0][2]
                
        if Raster_step==0:
            self.make_dir_dist(lastx-startX,lasty-startY)
            self.flush(laser_on=False)
            self.write(ord("N"))
            self.write(ord("R"))
            self.write(ord("B"))
            # Insert "SIE"
            self.write(ord("S"))
            self.write(ord("1"))
            self.write(ord("E"))
            ###########################################################
            laser   = False
            for i in range(1,len(ecoords)):
                update_gui("Generating EGV Data: %.1f%%" %(100.0*float(i)/float(len(ecoords))))
                if stop_calc[0]==True:
                    raise StandardError("Action Stoped by User.")
            
                if (ecoords[i][2] == ecoords[i-1][2]) and (not laser):
                    laser = True
                elif (ecoords[i][2] != ecoords[i-1][2]) and (laser):
                    laser = False
                dx = ecoords[i][0] - lastx
                dy = ecoords[i][1] - lasty

                min_rapid = 5
                if (abs(dx)+abs(dy))>0:
                    if laser:
                        self.make_cut_line(dx,dy)
                    else:
                        #print dx,dy,min_rapid
                        if ((abs(dx) < min_rapid) and (abs(dy) < min_rapid)):
                            self.rapid_move_slow(dx,dy)
                        else:
                            self.rapid_move_fast(dx,dy)
                        
                lastx   = ecoords[i][0]
                lasty   = ecoords[i][1]
 
            if laser:
                laser = False
                
            self.make_dir_dist(startX-lastx,startY-lasty)
              ###########################################################
        else: # Raster
              ###########################################################
            Rapid_flag=True
            ###################################################
            scanline = []
            scanline_y = None
            for i in range(len(ecoords)):
                y    = ecoords[i][1]
                if y != scanline_y:
                    scanline.append([ecoords[i]])
                    scanline_y = y
                else:
                    scanline[-1].append(ecoords[i])
            ###################################################
                
            lastx     = ecoords[0][0]
            lasty     = ecoords[0][1]
        
            DXstart = lastx-startX
            DYstart = lasty-startY
            self.make_dir_dist(DXstart,DYstart)
            #insert "NRB"
            self.flush(laser_on=False)
            self.write(ord("N"))
            self.write(ord("R"))
            self.write(ord("B"))
            # Insert "S1E"
            self.write(ord("S"))
            self.write(ord("1"))
            self.write(ord("E"))
            dx_last   = 0

            sign = -1
            cnt = 1
            for scan in scanline:
                update_gui("Generating EGV Data: %.1f%%" %(100.0*float(cnt)/float(len(scanline))))
                if stop_calc[0]==True:
                    raise StandardError("Action Stoped by User.")
                cnt = cnt+1
                #self.write(ord(" "))
                ######################################
                ## Flip direction and reset loop    ##
                ######################################
                sign      = -sign
                loop_last =  None
                y         =  scan[0][1]
                dy        =  y-lasty
                ###
                if sign == 1:
                    xr = scan[0][0]
                else:
                    xr = scan[-1][0]
                dxr = xr - lastx
                ######################################
                ## Make Rapid move if needed        ##
                ######################################
                if dy < -Raster_step:
                    if dxr*sign < 0:
                        yoffset = Raster_step*3
                    else:
                        yoffset = Raster_step
                    
                    if (dy+yoffset) < 0:
                        self.flush(laser_on=False)
                        self.write(ord("N"))
                        self.make_dir_dist(0,dy+yoffset)
                        self.flush(laser_on=False)
                        self.write(ord("S"))
                        self.write(ord("E"))
                        Rapid_flag=True
                    else:
                        adj_steps = -dy/Raster_step
                        #print "Raster_step = ",Raster_step
                        #print "dy = "         ,dy
                        #print "adj_steps = "  ,adj_steps
                        
                        for stp in range(1,adj_steps):
                            #print "stp= ",stp
                            adj_dist=5
                            self.make_dir_dist(sign*adj_dist,0)
                            lastx = lastx + sign*adj_dist
                            ##
                            sign  = -sign
                            if sign == 1:
                                xr = scan[0][0]
                            else:
                                xr = scan[-1][0]
                            dxr = xr - lastx
                            ##
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
                    if loop==loop_last:
                        self.make_cut_line(dx,0)
                    else:
                        if dx*sign > 0.0:
                            self.make_dir_dist(dx,0)
                    lastx = x
                    loop_last=loop
                lasty = y
            
            # Make final move to ensure last move is to the right 
            self.make_dir_dist(pad,0)
            lastx = lastx + pad
            # If sign is negative the final move will have incremented the
            # "y" position so adjust the lasty to acoomodate
            if sign < 0:
                lasty = lasty - Raster_step

            self.flush(laser_on=False)
            
            self.write(ord("N"))
            dx_final = (startX - lastx)
            dy_final = (startY - lasty) - Raster_step
            self.make_dir_dist(dx_final,dy_final)
            self.flush(laser_on=False)
            self.write(ord("S"))
            self.write(ord("E"))
            ###########################################################
                        
        # Append Footer
        self.flush(laser_on=False)
        self.write(ord("F"))
        self.write(ord("N"))
        self.write(ord("S"))
        self.write(ord("E"))
        return

    def rapid_move_slow(self,dx,dy):
        #self.make_cut_line(dx,dy)
        self.make_dir_dist(dx,dy)

    def rapid_move_fast(self,dx,dy):
        pad = 3
        #self.flush(laser_on=False)
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

    def rapid_move_fast_old(self,dx,dy):
        self.flush(laser_on=False)
        self.write(ord("N"))
        self.make_dir_dist(dx,dy)
        #self.make_dir_dist(dx-copysign(131,dx),dy-copysign(131,dx))
        self.flush(laser_on=False)
        self.write(ord("S"))
        self.write(ord("E"))
        if dy>0:
            self.write(self.UP)
        else:
            self.write(self.DOWN)
        if dx<0:
            self.write(self.LEFT)
        else:
            self.write(self.RIGHT)
                            
    def test_move_calc(self):
        vals = [0.0033,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.1,0.11,0.12,0.13,0.14,0.15,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1,6.48,6.5,6.6,6.7,6.8,6.9,7,7.1,7.2,7.3,7.4,7.5,7.6,7.7,7.71,7.72,7.73,7.74,7.75,7.76,7.77,7.775,7.775,7.776,7.777,7.778,7.779,7.779,7.78,7.79,7.8,7.825,7.85,7.875,7.9,8,8.1,8.2,8.3,8.4,8.5,8.6,8.7,8.8,8.9,9,10,10.1,10.2,10.3,10.4,10.5,10.6,10.7,10.8,10.9,11,11.1,11.2,11.3,11.4,11.5,11.6,11.7,11.8,11.9,12,12.1,12.2,12.3,12.4,12.5,12.6,12.7,12.8,12.9,13,14,15,16,17,18,19,20,30,40,50,60,70,80,90,100]
        for i in vals:
            #code_mm  = self.make_distance(i)
            code_in  = self.make_distance(round(i/25.4*1000.0,0))
            print round(i/25.4*1000.0,0),":",
            for j in range(len(code_in)): #,len(code_mm))):
                print code_in[j],
            print ""
    
    def open_egv_file_print_feed(self,filename):
        #print "Opening file: ",filename
        try:
            fin = open(filename,'r')
        except:
            print("Unable to open file: %s" %(filename))
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
        #print "Opening file: ",filename
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

        header_pct = ""
        while c!="I":
            header_pct=header_pct+c
            c = fin.read(1)

        cut_code1 = ""
        while c!="V":
            cut_code1 = cut_code1+c
            c = fin.read(1)


        #feed_rate = ""
        #for i in range(0,8):
        #    feed_rate=feed_rate+c
        #    c = fin.read(1)

        feed_rate = ""
        while c!="R" and c!="B" and c!="N" :
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
            

        #print "%-20s  " %(header_pct),"%-3s" %(cut_code1),feed_rate, "%-10s" %(cut_code2), cur
        
        #print "%-20s  " %(header_pct),
        #print "%-3s"    %(cut_code1),
        #print "%-10s"   %(feed_rate),
        #print feed_rate[0],feed_rate[1:4],feed_rate[4:7],feed_rate[7],feed_rate[8:11],feed_rate[11:14], feed_rate[14:17],
        #if len(feed_rate) > 17:
        #    print feed_rate[-1],
        #else:
        #    print " ",
        #print cur,

        #print feed_rate[1:4],feed_rate[4:7],feed_rate[7],feed_rate[8:11],feed_rate[11:14], feed_rate[14:17],
        print "%4d,%4d,%4d,%4d,%4d,%4d ])" %(
                int(feed_rate[1:4]),
                int(feed_rate[4:7]),
                int(feed_rate[7]),
                int(feed_rate[8:11]),
                int(feed_rate[11:14]),
                int(feed_rate[14:17])),
        print "  ",feed_rate,
        print ""

    
    def test_make_feed(self):
        data = []
        data.append([5.00,  235, 238,   1,   6,   0, 223 ]) 
        data.append([6.00,  239,  69,   1,   7,   0, 159 ]) 
        data.append([6.40,  240,  80,   1,   7,   0, 149 ]) 
        data.append([6.50,  240, 142,   1,   7,   0, 147 ]) 
        data.append([6.60,  240, 202,   1,   7,   0, 145 ]) 
        data.append([6.70,  241,   4,   1,   7,   0, 143 ]) 
        data.append([6.80,  241,  60,   1,   7,   0, 140 ]) 
        data.append([6.90,  241, 115,   1,   7,   0, 138 ]) 
        data.append([6.95,  241, 141,   1,   7,   0, 137 ]) 
        data.append([6.99,  241, 162,   1,   7,   0, 136 ]) 
        data.append([7.00,   64,  54,   1,   8,   5, 155 ]) 
        data.append([7.01,   64, 117,   1,   8,   5, 153 ]) 
        data.append([7.02,   64, 180,   1,   8,   5, 151 ]) 
        data.append([7.03,   64, 242,   1,   8,   5, 149 ]) 
        data.append([7.04,   65,  48,   1,   8,   5, 147 ]) 
        data.append([7.05,   65, 110,   1,   8,   5, 145 ]) 
        data.append([7.10,   66, 162,   1,   8,   5, 135 ]) 
        data.append([8.00,   85, 175,   1,   9,   4,  92 ]) 
        data.append([9.00,  102,  99,   1,  10,   3, 125 ]) 
        data.append([10.00,  115, 192,   1,  11,   2, 219 ]) 
        data.append([15.00,  155, 213,   1,  16,   1,  79 ]) 
        data.append([20.00,  175, 224,   1,  21,   0, 191 ]) 
        data.append([21.00,  178, 189,   1,  22,   0, 174 ]) 
        data.append([22.00,  181,  87,   1,  23,   0, 158 ]) 
        data.append([25.40,  188, 168,   1,  26,   0, 121 ]) 
        data.append([30.00,  195, 235,   2,  31,   0,  86 ]) 
        data.append([40.00,  205, 240,   2,  41,   0,  49 ]) 
        data.append([40.05,  205, 250,   2,  41,   0,  48 ]) 
        data.append([40.06,  205, 252,   2,  41,   0,  48 ]) 
        data.append([40.07,  205, 254,   2,  41,   0,  48 ]) 
        data.append([40.08,  206,   0,   2,  41,   0,  48 ]) 
        data.append([40.10,  206,   3,   2,  41,   0,  48 ]) 
        data.append([40.33,  206,  47,   2,  41,   0,  48 ]) 
        data.append([41.00,  206, 172,   2,  42,   0,  46 ]) 
        data.append([42.00,  207,  95,   2,  43,   0,  44 ]) 
        data.append([55.50,  214,  86,   2,  56,   0,  25 ]) 
        data.append([70.00,  216, 211,   3,  71,   0,  16 ]) 
        data.append([100.00,  221, 250,   3, 101,   0,   7 ]) 
        data.append([105.00,  222, 141,   3, 106,   0,   7 ]) 
        data.append([110.00,  223,  18,   3, 111,   0,   6 ]) 
        data.append([195.00,  225, 214,   4, 128,   0,   3 ]) 
        data.append([200.00,  225, 253,   4, 128,   0,   3 ]) 
        data.append([254.00,  172, 224,   1,  20,   0, 211 ]) 
        data.append([255.00,  172, 224,   1,  20,   0, 211 ]) 
        data.append([300.00,  172, 224,   1,  20,   0, 211 ]) 
        data.append([350.00,  172, 224,   1,  20,   0, 211 ]) 
        data.append([400.00,  172, 224,   1,  20,   0, 211 ]) 
        data.append([500.00,  172, 224,   1,  20,   0, 211 ]) 

        for line in data:
            print "%8.3f " %(line[0]),
            print "%03d "   %(line[1]),
            print "%03d "   %(line[2]),
            print "%d "   %(line[3]),
            print "%03d "   %(line[4]),
            print "%03d "   %(line[5]),
            print "%03d"    %(line[6]),
            print " :: ",
            feed = self.make_speed(line[0])
            print feed
            #print "%5.2f %5.2f" %(feed[0], line[1]-feed)

            
if __name__ == "__main__":

    EGV=egv()
    folder = "../"
    egv_files = []
    #files=os.listdir("../EGV_FILES/")
    files=os.listdir(folder)
    files.sort()
    name_len = 0
    for name in files:
        name_len = max(name_len,len(name))
    FORMAT = '%%%ds' %(-name_len)
    #self.gcode.append(FORMAT %(SafeZ))
    #except:
    #    egv_files=" "

    test_files = False
    if test_files:
        for name in files:
            if str.find(name.upper(),'.EGV') != -1:
                egv_files.append(name)
                #print FORMAT %(name)+":",
                rate = name.split('.')[0].replace('_','.')
                print "data.append([%3.2f," %float(rate),
                #print FORMAT %name.split('.')[0]+":",
                EGV.open_egv_file_print_data(folder+name)


    #EGV.test_move_calc()

    for i in range(1,258,1):
        print i,":",
        for n in EGV.make_distance(i):
            print chr(n),
        print ""

    
    #EGV.test_make_feed()
    print "DONE"
    print EGV.make_distance(round(131,0))
