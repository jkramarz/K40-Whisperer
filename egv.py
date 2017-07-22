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

    def make_egv_data(self, ecoords_in,
                            startX=0,
                            startY=0,
                            units = 'in',
                            Feed = None,
                            speed_text="V1752241021000191",
                            Raster_step=0):
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

        self._write_string("I")
        for code in speed:
            self.write(code)

        lastx     = ecoords[0][0]
        lasty     = ecoords[0][1]
        loop_last = ecoords[0][2]

        if Raster_step==0:
            self.make_dir_dist(lastx-startX,lasty-startY)
            self.flush(laser_on=False)
            self._write_string("NRBS1E")
            ###########################################################
            laser   = False
            for i in range(1,len(ecoords)):
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
            self.flush(laser_on=False)
            self._write_string("NRBS1E")
            dx_last   = 0

            sign = -1
            for scan in scanline:
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
                    self.flush(laser_on=False)
                    self._write_string("N")
                    self.make_dir_dist(0,dy+yoffset)
                    self.flush(laser_on=False)
                    self._write_string("SE")
                    Rapid_flag=True
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
                        #print dxr,sign
                        #self.write(ord("_"))
                        #self.make_dir_dist(-sign*2    ,0)
                        #self.make_dir_dist( sign*2+dxr,0)
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

            sself._write_string("N")
            dx_final = (startX - lastx)
            dy_final = (startY - lasty) - Raster_step
            self.make_dir_dist(dx_final,dy_final)
            self.flush(laser_on=False)
            self._write_string("SE")
            ###########################################################

        # Append Footer
        self.flush(laser_on=False)
        self._write_string("FNSE")

        return



##################################

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

    def make_distance(self, points):
        distance = int(points)
        full_range = 255
        full_range_code = 122 # ASCII "z"
        full_ranges = distance / full_range
        code = [full_range_code] * full_ranges
        remainder = distance % full_range

        if remainder == 0:
            return code
        elif remainder < 26: # encodes to ASCII range "a" to "y"
            return code + [96 + remainder]
        elif remainder < 52: # encodes to ASCII range "a" to "y", prefixed with "|"
            return code + [124, 96 + remainder - 25]
        else: # or zero-padded string
            return code +  map(
                ord,
                list("%03d" % remainder)
            )


    def make_dir_dist(self,dxmils,dymils,laser_on=False):
        ady = abs(dymils)
        if ady > 0:
            self.move(
                self.UP if dymils > 0 else self.DOWN,
                ady,
                laser_on
            )

        adx = abs(dxmils)
        if adx > 0:
            self.move(
                self.RIGHT if dymils > 0 else self.LEFT,
                adx,
                laser_on
            )

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
                print "egv.py: Error delta =", error
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

        print "speed_text=",speed_text
        for c in speed_text:
            speed.append(ord(c))
        return speed

    def make_move_data(self,dxmils,dymils):
        if (abs(dxmils)+abs(dymils)) > 0:
            self.write(73) # I
            self.make_dir_dist(dxmils,dymils)
            self.flush()
            self._write_string("S1P")


    def rapid_move_slow(self,dx,dy):
        self.make_dir_dist(dx,dy)

    def rapid_move_fast(self,dx,dy):
        pad = 3
        #self.flush(laser_on=False)
        self.make_dir_dist(-pad, 0  ) #add "T" move
        self.make_dir_dist(   0, pad) #add "L" move
        self.flush(laser_on=False)

        if dx+pad < 0.0:
            self._write_string("BN")
        else:
            self._write_string("TN")

        self.make_dir_dist(dx+pad,dy-pad)
        self.flush(laser_on=False)

        self._write_string("SE")


    def _write_string(self, data):
        for byte in map(
            list(data),
            ord
        ):
            self.write(byte)
