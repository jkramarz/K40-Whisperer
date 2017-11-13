#!/usr/bin/python
"""
    g_code_library
    Copyright (C) <2017>  <Scorch>
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys
from math import *
import os
import re
import binascii
import getopt
import webbrowser


#################
### START LIB ###
#################
############################################################################
class G_Code_Rip:
    def __init__(self):
        self.Zero      = 0.0000001
        self.g_code_data  = []
        self.scaled_trans = []
        self.right_side   = []
        self.left_side    = []
        self.probe_gcode  = []
        self.probe_coords = []
        self.arc_angle    = 2
        self.accuracy     = .001
        self.units        = "in"

    ################################################################################
    #             Function for outputting messages to different locations          #
    #            depending on what options are enabled                             #
    ################################################################################
    def fmessage(self,text,newline=True):
        if newline==True:
            try:
                sys.stdout.write(text)
                sys.stdout.write("\n")
            except:
                pass
        else:
            try:
                sys.stdout.write(text)
            except:
                pass

    def Read_G_Code(self,filename, XYarc2line = False, arc_angle=2, units="in", Accuracy=""):
        self.g_code_data  = []
        self.scaled_trans = []
        self.right_side   = []
        self.left_side    = []
        self.probe_gcode  = []
        self.probe_coords = []
        self.arc_angle    = arc_angle
        self.units        = units
        if Accuracy == "":
            if units == "in":
                self.accuracy = .001
            else:
                self.accuracy = .025
        else:
            self.accuracy = float(Accuracy)
        
        READ_MSG = []

        # Try to open file for reading
        try:
            fin = open(filename,'r')
        except:
            READ_MSG.append("Unable to open file: %s" %(filename))
            return READ_MSG

        scale = 1
        variables = []
        line_number = 0

        xind=0
        yind=1
        zind=2

        mode_arc  = "incremental" # "absolute"
        mode_pos = "absolute"    # "incremental"

        mvtype = 1  # G0 (Rapid), G1 (linear), G2 (clockwise arc) or G3 (counterclockwise arc). 
        plane  = "17" # G17 (Z-axis, XY-plane), G18 (Y-axis, XZ-plane), or G19 (X-axis, YZ-plane)
        pos     =['','','']
        pos_last=['','','']
        POS     =[complex(0,1),complex(0,1),complex(0,1)]
        feed = 0
        spindle = 0
        
        #########################
        for line in fin:
            line_number = line_number + 1
            #print line_number
            line = line.replace("\n","")
            line = line.replace("\r","")
            code_line=[]
            
            #####################
            ### FIND COMMENTS ###
            #####################
            if line.find("(") != -1:
                s = line.find("(")
                while s != -1:
                    e = line.find(")")
                    code_line.append([ ";", line[s:e+1] ])
                    line = self.rm_text(line,s,e)
                    s = line.find("(")
            
            if line.find(";") != -1:
                s = line.find(";")
                e = len(line)
                code_line.append([ ";", line[s:e] ])
                line = self.rm_text(line,s,e)
            # If comment exists write it to output 
            if code_line!= []: 
                for comment in code_line:
                    self.g_code_data.append(comment)
                code_line=[]

            # Switch remaining non comment data to upper case
            # and remove spaces
            line = line.upper()
            line = line.replace(" ","")

            
            #####################################################
            # Find # chars and check for a variable definition  #
            #####################################################
            if line.find("#") != -1:
                s = line.rfind("#")
                while s != -1:
                    if line[s+1] == '<':
                        e = s+2
                        while line[e] != '>' and e <= len(line):
                            e = e+1
                        e = e+1
                        vname = line[s:e].lower()
                    else:
                        vname = re.findall(r'[-+]?\d+',line[s:])[0]	
                        e = s + 1 + len(vname)
                        vname = line[s:e]

                    DEFINE = False
                    if e < len(line):
                        if line[e]=="=":
                            DEFINE = True
                    if DEFINE:
                        try:
                            vval = "%.4f" %(float(line[e+1:]))
                            line = ''
                        except:
                            try:
                                vval = self.EXPRESSION_EVAL(line[e+1:])
                                line = ''
                            except:
                                READ_MSG.append(str(sys.exc_info()[1]))
                                return READ_MSG
                            
                        variables.append([vname,vval])
                        line  = self.rm_text(line,s,e-1)
                    else:
                        line = self.rm_text(line,s,e-1)
                        VALUE = ''
                        for V in variables:
                            if V[0] == vname:
                                VALUE = V[1]
                                
                        line = self.insert_text(line,VALUE,s)
                        
                    s = line.rfind("#")

            #########################
            ### FIND MATH REGIONS ###
            #########################
            if line.find("[") != -1 and line.find("[") != 0:
                ############################
                s = line.find("[")
                while s != -1:
                    e = s + 1
                    val = 1
                    while val > 0:
                        if e >= len(line):
                            MSG = "ERROR: Unable to evaluate expression: G-Code Line %d" %(line_number)
                            raise ValueError(MSG)
                        if line[e]=="[":
                            val = val + 1
                        elif line[e] == "]":
                            val = val - 1
                        e = e + 1
                        
                    new_val = self.EXPRESSION_EVAL(line[s:e])
                    
                    line = self.rm_text(line,s,e-1)
                    line = self.insert_text(line,new_val,s)
                    s = line.find("[")
                #############################


            ####################################
            ### FIND FULLY UNSUPPORTED CODES ###
            ####################################
            # D Tool radius compensation number
            # E ...
            # L ...
            # O ... Subroutines
            # Q Feed increment in G73, G83 canned cycles
            # A A axis of machine
            # B B axis of machine
            # C C axis of machine
            # U U axis of machine
            # V V axis of machine
            # W W axis of machine

            UCODES = ("A","B","C","D","E","L","O","Q","U","V","W")
            skip = False
            for code in UCODES:
                if line.find(code) != -1:
                    READ_MSG.append("Warning: %s Codes are not supported ( G-Code File Line: %d )" %(code,line_number))
                    skip = True
            if skip:
                continue
                    

            ##############################
            ###    FIND ALL CODES      ###
            ##############################
            # F Feed rate
            # G General function
            # I X offset for arcs and G87 canned cycles
            # J Y offset for arcs and G87 canned cycles
            # K Z offset for arcs and G87 canned cycles. Spindle-Motion Ratio for G33 synchronized movements.
            # M Miscellaneous function (See table Modal Groups)
            # P Dwell time in canned cycles and with G4. Key used with G10. Used with G2/G3.
            # R Arc radius or canned cycle plane
            # S Spindle speed
            # T Tool selection
            # X X axis of machine
            # Y Y axis of machine
            # Z Z axis of machine
            
            ALL = ("A","B","C","D","E","F","G","H","I","J",\
                   "K","L","M","N","O","P","Q","R","S","T",\
                   "U","V","W","X","Y","Z","#","=")
            temp = []
            line = line.replace(" ","")
            for code in ALL:
                index=-1
                index = line.find(code,index+1)
                while index != -1:
                    temp.append([code,index])
                    index = line.find(code,index+1)
            temp.sort(key=lambda a:a[1])

            code_line=[]
            if temp != []:
                x = 0
                while x <= len(temp)-1:
                    s = temp[x][1]+1
                    if x == len(temp)-1:
                        e = len(line)
                    else:    
                        e = temp[x+1][1]
                    
                    CODE  = temp[x][0]
                    VALUE = line[s:e]
                    code_line.append([ CODE, VALUE ])
                    x = x + 1

            #################################
                    
            mv_flag   = 0
            POS_LAST = POS[:]
            #CENTER  = ['','','']
            CENTER   = POS_LAST[:]
            passthru = ""
            for com in code_line:
                if com[0] == "G":
                    Gnum = "%g" %(float(com[1]))
                    if Gnum == "0" or Gnum == "1":
                        mvtype = int(Gnum)
                    elif Gnum == "2" or Gnum == "3":
                        mvtype = int(Gnum)
                        #CENTER = POS_LAST[:]
                    elif Gnum == "17":
                        plane = Gnum
                    elif Gnum == "18":
                        plane = Gnum
                    elif Gnum == "19":
                        plane = Gnum
                    elif Gnum == "20":
                        if units == "in":
                            scale = 1
                        else:
                            scale = 25.4
                    elif Gnum == "21":
                        if units == "mm":
                            scale = 1
                        else:
                            scale = 1.0/25.4
                    elif Gnum == "81":
                        READ_MSG.append("Warning: G%s Codes are not supported ( G-Code File Line: %d )" %(Gnum,line_number))
                    elif Gnum == "90.1":
                        mode_arc = "absolute"
                        
                    elif Gnum == "90":
                        mode_pos = "absolute"

                    elif Gnum == "91":
                        mode_pos = "incremental"
                    
                    elif Gnum == "91.1":
                        mode_arc = "incremental"

                    elif Gnum == "92":
                        #READ_MSG.append("Aborting G-Code Reading: G%s Codes are not supported" %(Gnum))
                        READ_MSG.append("Warning: G%s Codes are not supported ( G-Code File Line: %d )" %(Gnum,line_number))
                        #return READ_MSG
                        
                    elif Gnum == "38.2":
                        READ_MSG.append("Warning: G%s Codes are not supported ( G-Code File Line: %d )" %(Gnum,line_number))
                        #READ_MSG.append("Aborting G-Code Reading: G%s Codes are not supported" %(Gnum))
                        #return READ_MSG
                    
                    else:
                        passthru = passthru +  "%s%s " %(com[0],com[1])
                
                elif com[0] == "X":
                    if mode_pos == "absolute":
                        POS[xind] = float(com[1])*scale
                    else:
                        POS[xind] = float(com[1])*scale + POS_LAST[xind]
                    mv_flag = 1

                elif com[0] == "Y":
                    if mode_pos == "absolute":
                        POS[yind] = float(com[1])*scale
                    else:
                        POS[yind] = float(com[1])*scale + POS_LAST[yind]
                    mv_flag = 1

                elif com[0] == "Z":
                    if mode_pos == "absolute":
                        POS[zind] = float(com[1])*scale
                    else:
                        POS[zind] = float(com[1])*scale + POS_LAST[zind]
                    mv_flag = 1

                ###################
                elif com[0] == "I":
                    if mode_arc == "absolute":
                        CENTER[xind] = float(com[1])*scale
                    else:
                        CENTER[xind] = float(com[1])*scale + POS_LAST[xind]
                    if (mvtype==2 or mvtype==3):
                        mv_flag = 1
                    
                elif com[0] == "J":
                    if mode_arc == "absolute":
                        CENTER[yind] = float(com[1])*scale
                    else:
                        CENTER[yind] = float(com[1])*scale + POS_LAST[yind]
                    if (mvtype==2 or mvtype==3):
                        mv_flag = 1
                elif com[0] == "K":
                    if mode_arc == "absolute":
                        CENTER[zind] = float(com[1])*scale
                    else:
                        CENTER[zind] = float(com[1])*scale + POS_LAST[zind]
                    if (mvtype==2 or mvtype==3):
                        mv_flag = 1

                elif com[0] == "R":
                    Rin= float(com[1])*scale
                    CENTER = self.get_center(POS,POS_LAST,Rin,mvtype,plane)
                        
                ###################
                elif com[0] == "F":
                    feed = float(com[1]) * scale
                    
                elif com[0] == "S":
                    spindle = float(com[1])

                elif com[0] == ";":
                    passthru = passthru + "%s " %(com[1])

                elif com[0] == "P" and mv_flag == 1 and mvtype > 1:
                    READ_MSG.append("Aborting G-Code Reading: P word specifying the number of full or partial turns of arc are not supported")
                    return READ_MSG

                elif com[0] == "M":
                    Mnum = "%g" %(float(com[1]))
                    if Mnum == "2":
                        self.g_code_data.append([ "M2", "(END PROGRAM)" ])
                    passthru = passthru + "%s%s " %(com[0],com[1])

                elif com[0] == "N":
                    pass
                    #print "Ignoring Line Number %g" %(float(com[1]))
                    
                else:
                    passthru = passthru + "%s%s " %(com[0],com[1])

            pos      = POS[:]
            pos_last = POS_LAST[:]
            center = CENTER[:]
 
            # Most command on a line are executed prior to a move so 
            # we will write the passthru commands on the line before we found them
            # only "M0, M1, M2, M30 and M60" are executed after the move commands
            # there is a risk that one of these commands could stop the program before
            # the move is completed

            if passthru != '':
                self.g_code_data.append("%s" %(passthru))


            ###############################################################################
            if mv_flag == 1:
                if mvtype == 0:
                    self.g_code_data.append([mvtype,pos_last[:],pos[:]])
                if mvtype == 1:
                    self.g_code_data.append([mvtype,pos_last[:],pos[:],feed,spindle])
                if mvtype == 2 or mvtype == 3:
                    if plane == "17":
                        if XYarc2line == False:
                            self.g_code_data.append([mvtype,pos_last[:],pos[:],center[:],feed,spindle])
                        else:
                            data = self.arc2lines(pos_last[:],pos[:],center[:], mvtype, plane)
                            
                            for line in data:
                                XY=line
                                self.g_code_data.append([1,XY[:3],XY[3:],feed,spindle])
                                
                    elif plane == "18":
                        data = self.arc2lines(pos_last[:],pos[:],center[:], mvtype, plane)
                        for line in data:
                            XY=line
                            self.g_code_data.append([1,XY[:3],XY[3:],feed,spindle])
                            
                    elif plane == "19":
                        data = self.arc2lines(pos_last[:],pos[:],center[:], mvtype, plane)
                        for line in data:
                            XY=line
                            self.g_code_data.append([1,XY[:3],XY[3:],feed,spindle])
            ###############################################################################
            #################################
        fin.close()
                    
        ## Post process the g-code data to remove complex numbers
        cnt = 0
        firstx = complex(0,1)
        firsty = complex(0,1)
        firstz = complex(0,1)
        first_sum = firstx + firsty + firstz
        while ((cnt < len(self.g_code_data)) and (isinstance(first_sum, complex))):
            line = self.g_code_data[cnt]
            if line[0] == 0 or line[0] == 1 or line[0] == 2 or line[0] == 3:
                if (isinstance(firstx, complex)): firstx = line[2][0]
                if (isinstance(firsty, complex)): firsty = line[2][1]
                if (isinstance(firstz, complex)): firstz = line[2][2]
            cnt=cnt+1
            first_sum = firstx + firsty + firstz
        max_cnt = cnt
        cnt = 0
        ambiguousX = False
        ambiguousY = False
        ambiguousZ = False
        while (cnt < max_cnt):
            line = self.g_code_data[cnt]
            if line[0] == 1 or line[0] == 2 or line[0] == 3:
                # X Values
                if (isinstance(line[1][0], complex)):
                    line[1][0] = firstx
                    ambiguousX = True
                if (isinstance(line[2][0], complex)):
                    line[2][0] = firstx
                    ambiguousX = True
                # Y values
                if (isinstance(line[1][1], complex)):
                    line[1][1] = firsty
                    ambiguousY = True
                if (isinstance(line[2][1], complex)):
                    line[2][1] = firsty
                    ambiguousY = True
                # Z values
                if (isinstance(line[1][2], complex)):
                    line[1][2] = firstz
                    ambiguousZ = True
                if (isinstance(line[2][2], complex)):
                    line[2][2] = firstz
                    ambiguousZ = True
            cnt=cnt+1
        #if (ambiguousX or ambiguousY or ambiguousZ):
        #    MSG = "Ambiguous G-Code start location:\n"
        #    if (ambiguousX):  MSG = MSG + "X position is not set by a G0(rapid) move prior to a G1,G2 or G3 move.\n"
        #    if (ambiguousY):  MSG = MSG + "Y position is not set by a G0(rapid) move prior to a G1,G2 or G3 move.\n"
        #    if (ambiguousZ):  MSG = MSG + "Z position is not set by a G0(rapid) move prior to a G1,G2 or G3 move.\n"
        #    MSG = MSG + "!! Review output files carefully !!"
        #    READ_MSG.append(MSG)
        
        return READ_MSG

    def get_center(self,POS,POS_LAST,Rin,mvtype,plane="17"):
        if   plane == "18":
            xind=2
            yind=0
            zind=1
        elif plane == "19":
            xind=1
            yind=2
            zind=0
        elif plane == "17":
            xind=0
            yind=1
            zind=2

        CENTER=["","",""]
        cord = sqrt( (POS[xind]-POS_LAST[xind])**2 + (POS[yind]-POS_LAST[yind])**2 )
        v1 = cord/2.0
        
        #print "rin=%f v1=%f (Rin**2 - v1**2)=%f" %(Rin,v1,(Rin**2 - v1**2))
        v2_sq = Rin**2 - v1**2
        if v2_sq<0.0:
            v2_sq = 0.0
        v2 = sqrt( v2_sq )

        theta = self.Get_Angle2(POS[xind]-POS_LAST[xind],POS[yind]-POS_LAST[yind])

        if mvtype == 3:
            dxc,dyc = self.Transform(-v2,v1,radians(theta-90))
        elif mvtype == 2:
            dxc,dyc = self.Transform(v2,v1,radians(theta-90))
        else:
            return "Center Error"

        xcenter = POS_LAST[xind] + dxc
        ycenter = POS_LAST[yind] + dyc

        CENTER[xind] = xcenter
        CENTER[yind] = ycenter
        CENTER[zind] = POS_LAST[zind]

        return CENTER

    #######################################
    def split_code(self,code2split,shift=[0,0,0],angle=0.0):
        xsplit=0.0
        mvtype = -1  # G0 (Rapid), G1 (linear), G2 (clockwise arc) or G3 (counterclockwise arc).

        passthru = ""
        POS     =[0,0,0]
        feed = 0
        spindle = 0
        self.right_side = []
        self.left_side  = []

        L = 0
        R = 1
        for line in code2split:
            if line[0] == 1:
                mvtype   = line[0]
                POS_LAST = line[1][:]
                POS      = line[2][:]
                CENTER   = ['','','']
                feed     = line[3]
                spindle  = line[4] 

            elif line[0] == 3 or line[0] == 2:
                mvtype   = line[0]
                POS_LAST = line[1][:]
                POS      = line[2][:]
                CENTER   = line[3][:]
                feed     = line[4]
                spindle  = line[5]

            else:
                mvtype  = -1
                passthru = line
                
            ###############################################################################
            if mvtype >= 1 and mvtype <= 3:
                pos      = self.coordop(POS,shift,angle)
                pos_last = self.coordop(POS_LAST,shift,angle)

                if CENTER[0]!='' and CENTER[1]!='':
                    center = self.coordop(CENTER,shift,angle)
                else:
                    center = CENTER

                this=""
                other=""
                
                if pos_last[0] > xsplit+self.Zero:
                    flag_side = R
                elif pos_last[0] < xsplit-self.Zero:
                    flag_side = L
                else:
                    if mvtype == 1:
                        if pos[0] >= xsplit:
                            flag_side = R
                        else:
                            flag_side = L
                            
                    elif mvtype == 2:
                        
                        if abs(pos_last[1]-center[1]) < self.Zero:
                            if center[0] > xsplit:
                                flag_side = R
                            else:
                                flag_side = L
                        else:
                            if   pos_last[1] >= center[1]:
                                flag_side = R
                            else:
                                flag_side = L
                                
                    else: #(mvtype == 3)
                        if abs(pos_last[1]-center[1]) < self.Zero:
                            if center[0] > xsplit:
                                flag_side = R
                            else:
                                flag_side = L
                        else:
                            if   pos_last[1] >= center[1]:
                                flag_side = L
                            else:
                                flag_side = R

                if flag_side == R:
                    this  = 1
                    other = 0
                else:
                    this  = 0
                    other = 1
                    
                app=[self.apright, self.apleft]
                
                #############################
                if mvtype == 0:
                    pass

                if mvtype == 1:
                    A  = self.coordunop(pos_last[:],shift,angle)
                    C  = self.coordunop(pos[:]     ,shift,angle)
                    cross = self.get_line_intersect(pos_last, pos, xsplit)

                    if len(cross) > 0: ### Line crosses boundary ###
                        B  = self.coordunop(cross[0]   ,shift,angle)
                        app[this] ( [mvtype,A,B,feed,spindle] )
                        app[other]( [mvtype,B,C,feed,spindle] )
                    else:
                        app[this] ( [mvtype,A,C,feed,spindle] )

                if mvtype == 2 or mvtype == 3:
                    A  = self.coordunop(pos_last[:],shift,angle)
                    C  = self.coordunop(pos[:]     ,shift,angle)
                    D  = self.coordunop(center     ,shift,angle)
                    cross = self.get_arc_intersects(pos_last[:], pos[:], xsplit, center[:], "G%d" %(mvtype))

                    if len(cross) > 0: ### Arc crosses boundary at least once ###
                        B  = self.coordunop(cross[0]   ,shift,angle)
                        #Check length of arc before writing
                        if sqrt((A[0]-B[0])**2 + (A[1]-B[1])**2) > self.accuracy:
                            app[this]( [mvtype,A,B,D,feed,spindle])
                            
                        if len(cross) == 1: ### Arc crosses boundary only once ###
                            #Check length of arc before writing
                            if sqrt((B[0]-C[0])**2 + (B[1]-C[1])**2) > self.accuracy:
                                app[other]([ mvtype,B,C,D, feed,spindle] )
                        if len(cross) == 2: ### Arc crosses boundary twice ###
                            E  = self.coordunop(cross[1],shift,angle)
                            #Check length of arc before writing
                            if sqrt((B[0]-E[0])**2 + (B[1]-E[1])**2) > self.accuracy:
                                app[other]([ mvtype,B,E,D, feed,spindle] )
                            #Check length of arc before writing
                            if sqrt((E[0]-C[0])**2 + (E[1]-C[1])**2) > self.accuracy:
                                app[this] ([ mvtype,E,C,D, feed,spindle] )
                    else: ### Arc does not cross boundary ###
                        app[this]([ mvtype,A,C,D, feed,spindle])

            ###############################################################################
            else:
                if passthru != '':
                    self.apboth(passthru)

    #######################################
    def probe_code(self,code2probe,nX,nY,probe_istep,minx,miny,xPartitionLength,yPartitionLength): #,Xoffset,Yoffset):
    #def probe_code(self,code2probe,nX,nY,probe_istep,minx,miny,xPartitionLength,yPartitionLength,Xoffset,Yoffset,Zoffset):
        #print "nX,nY =",nX,nY 
        probe_coords = []
        BPN=500
        POINT_LIST = [False for i in range(int((nY)*(nX)))]
        
        if code2probe == []:
            return 
        
        mvtype = -1  # G0 (Rapid), G1 (linear), G2 (clockwise arc) or G3 (counterclockwise arc).
        passthru = ""
        POS      = [0,0,0]
        feed     = 0
        spindle  = 0
        out      = []

        min_length = min(xPartitionLength,yPartitionLength) / probe_istep
        if (min_length < self.Zero):
            min_length = max(xPartitionLength,yPartitionLength) / probe_istep
        if (min_length < self.Zero):
            min_length = 1

        for line in code2probe:
            if line[0] == 0  or line[0] == 1:
                mvtype   = line[0]
                POS_LAST = line[1][:]
                POS      = line[2][:]
                CENTER   = ['','','']
                if line[0] == 1:
                    feed     = line[3]
                    spindle  = line[4]

            elif line[0] == 3 or line[0] == 2:
                mvtype   = line[0]
                POS_LAST = line[1][:]
                POS      = line[2][:]
                CENTER   = line[3][:]
                feed     = line[4]
                spindle  = line[5]
            else:
                mvtype  = -1
                passthru = line

            ###############################################################################
            if mvtype >= 0 and mvtype <=3:
                pos = POS[:]
                pos_last = POS_LAST[:]
                center = CENTER[:]
                
                #############################
                if mvtype == 0:
                    out.append( [mvtype,pos_last,pos] )
                    
                if mvtype == 1:
                    dx = pos[0]-pos_last[0]
                    dy = pos[1]-pos_last[1]
                    dz = pos[2]-pos_last[2]
                    length = sqrt(dx*dx + dy*dy)
                    if (length <= min_length):
                        out.append( [mvtype,pos_last,pos,feed,spindle] )
                    else:
                        Lsteps = max(2,int(ceil(length / min_length)))
                        xstp0 = float(pos_last[0])
                        ystp0 = float(pos_last[1])
                        zstp0 = float(pos_last[2])
                        for n in range(1,Lsteps+1):
                            xstp1 = n/float(Lsteps)*dx + pos_last[0] 
                            ystp1 = n/float(Lsteps)*dy + pos_last[1]
                            zstp1 = n/float(Lsteps)*dz + pos_last[2]
                            out.append( [mvtype,[xstp0,ystp0,zstp0],[xstp1,ystp1,zstp1],feed,spindle] )
                            xstp0 = float(xstp1)
                            ystp0 = float(ystp1)
                            zstp0 = float(zstp1)
                            
                if mvtype == 2 or mvtype == 3:
                    out.append( [ mvtype,pos_last,pos,center, feed,spindle] )                    
            ###############################################################################
            else:
                if passthru != '':
                    out.append(passthru)

        ################################
        ##  Loop through output to    ##
        ##  find needed probe points  ##
        ################################
        for i in range(len(out)):
            line = out[i]
            if line[0] == 0  or line[0] == 1:
                mvtype   = line[0]
                POS_LAST = line[1][:]
                POS      = line[2][:]
                CENTER   = ['','','']
                if line[0] == 1:
                    feed = line[3]
                    spindle = line[4]

            elif line[0] == 3 or line[0] == 2:
                mvtype   = line[0]
                POS_LAST = line[1][:]
                POS      = line[2][:]
                CENTER   = line[3][:]
                feed     = line[4]
                spindle  = line[5]
            else:
                mvtype  = -1
                passthru = line

            if mvtype >= 1 and mvtype <=3:
                pos = POS[:]
                pos_last = POS_LAST[:]
                center = CENTER[:]


                #### ADD ADDITIONAL DATA TO POS_LAST DATA ####
                i_x,i_y = self.get_ix_iy((pos_last[0]-minx),(pos_last[1]-miny),xPartitionLength,yPartitionLength)
                #i_x = i_x+Xoffset
                #i_y = i_y+Yoffset
                if i_x < 0:
                    i_x=0
                if i_y < 0:
                    i_y=0
                if (i_x+1 >= nX):
                    i_x = nX-2
                    #i_x = i_x-1 #commented 02/22
                    #print "adjust i_x POS_LAST"
                i_x2 = i_x+1
                if (i_y+1 >= nY):
                    i_y = nY-2
                    #i_y = i_y-1  #commented 02/22
                    #print "adjust i_y POS_LAST"
                i_y2 = i_y+1
                
                p_index_A =  int(i_y* nX + i_x )
                p_index_B =  int(i_y2*nX + i_x )
                p_index_C =  int(i_y *nX + i_x2)
                p_index_D =  int(i_y2*nX + i_x2)                    
                
                Xfraction=((pos_last[0]-minx)-(i_x*xPartitionLength))/xPartitionLength
                Yfraction=((pos_last[1]-miny)-(i_y*yPartitionLength))/yPartitionLength

                if Xfraction>1.0:
                    #print "ERROR POS_LAST: Xfraction = ", Xfraction
                    Xfraction = 1.0
                if Xfraction <0.0:
                    #print "ERROR POS_LAST: Xfraction = ", Xfraction
                    Xfraction = 0.0
                if Yfraction > 1.0:
                    #print "ERROR POS_LAST: Yfraction = ", Yfraction
                    Yfraction = 1.0
                if Yfraction<0.0:
                    #print "ERROR POS_LAST: Yfraction = ", Yfraction
                    Yfraction = 0.0

                BPN=500
                out[i][1].append(p_index_A+BPN)
                out[i][1].append(p_index_B+BPN)
                out[i][1].append(p_index_C+BPN)
                out[i][1].append(p_index_D+BPN)
                out[i][1].append(Xfraction)
                out[i][1].append(Yfraction)

                try:
                    POINT_LIST[p_index_A ] = True
                    POINT_LIST[p_index_B ] = True
                    POINT_LIST[p_index_C ] = True
                    POINT_LIST[p_index_D ] = True
                except:
                    pass 
                #### ADD ADDITIONAL DATA TO POS_LAST DATA ####
                i_x,i_y = self.get_ix_iy((pos[0]-minx),(pos[1]-miny),xPartitionLength,yPartitionLength)
                #i_x = i_x+Xoffset
                #i_y = i_y+Yoffset
                if i_x < 0:
                    i_x=0
                if i_y < 0:
                    i_y=0
                if (i_x+1 >= nX):
                    i_x = nX-2
                    #i_x = i_x-1 #commented 02/22
                    #print "adjust i_x POS"
                i_x2 = i_x+1
                if (i_y+1 >= nY):
                    i_y = nY-2
                    #i_y = i_y-1#commented 02/22
                    #print "adjust i_y POS"
                i_y2 = i_y+1
                
                p_index_A =  int(i_y* nX + i_x )
                p_index_B =  int(i_y2*nX + i_x )
                p_index_C =  int(i_y *nX + i_x2)
                p_index_D =  int(i_y2*nX + i_x2)
                Xfraction=((pos[0]-minx)-(i_x*xPartitionLength))/xPartitionLength
                Yfraction=((pos[1]-miny)-(i_y*yPartitionLength))/yPartitionLength
                
                if Xfraction>1.0:
                    Xfraction = 1.0
                    #print "ERROR POS: Xfraction = ", Xfraction
                if Xfraction <0.0:
                    Xfraction = 0.0
                    #print "ERROR POS: Xfraction = ", Xfraction
                if Yfraction > 1.0:
                    Yfraction = 1.0
                    #print "ERROR POS: Yfraction = ", Yfraction
                if Yfraction<0.0:
                    Yfraction = 0.0
                    #print "ERROR POS: Yfraction = ", Yfraction
                    
                out[i][2].append(p_index_A+BPN)
                out[i][2].append(p_index_B+BPN)
                out[i][2].append(p_index_C+BPN)
                out[i][2].append(p_index_D+BPN)
                out[i][2].append(Xfraction)
                out[i][2].append(Yfraction)
                try:
                    POINT_LIST[p_index_A ] = True
                    POINT_LIST[p_index_B ] = True
                    POINT_LIST[p_index_C ] = True
                    POINT_LIST[p_index_D ] = True
                except:
                    pass
        self.probe_gcode = out
        #for line in out:
        #    print line
        
        ################################
        ##  Generate Probing Code     ##
        ##  For needed points         ##
        ################################

        for i in range(len(POINT_LIST)):
            i_x = i % nX
            i_y = int(i / nX)
            xp  = i_x * xPartitionLength + minx
            yp  = i_y * yPartitionLength + miny
            probe_coords.append([POINT_LIST[i],i+BPN,xp,yp])

        self.probe_coords = probe_coords
        return

    def get_ix_iy(self,x,y,xPartitionLength,yPartitionLength):
        i_x=int(x/xPartitionLength)
        i_y=int(y/yPartitionLength)
        return i_x,i_y

    ####################################### 
    def scale_rotate_code(self,code2scale,scale=[1.0,1.0,1.0,1.0],angle=0.0):
        if code2scale == []:
            return code2scale,0,0,0,0,0,0
        minx =  99999
        maxx = -99999
        miny =  99999
        maxy = -99999
        minz =  99999
        maxz = -99999
        mvtype = -1  # G0 (Rapid), G1 (linear), G2 (clockwise arc) or G3 (counterclockwise arc).

        passthru = ""
        POS     =[0,0,0]
        feed = 0
        spindle = 0
        out = []

        L = 0
        R = 1
        flag_side = 1  

        for line in code2scale:
            if line[0] == 0  or line[0] == 1:
                mvtype   = line[0]
                POS_LAST = line[1][:]
                POS      = line[2][:]
                CENTER   = ['','','']
                if line[0] == 1:
                    feed     = line[3] * scale[3]
                    spindle   = line[4]

            elif line[0] == 3 or line[0] == 2:
                mvtype   = line[0]
                POS_LAST = line[1][:]
                POS      = line[2][:]
                CENTER   = line[3][:]
                feed     = line[4] * scale[3]
                spindle   = line[5]
            else:
                mvtype  = -1
                passthru = line

            ###############################################################################
            if mvtype >= 0 and mvtype <=3:

                pos      = self.scale_rot_coords(POS,scale,angle)
                pos_last = self.scale_rot_coords(POS_LAST,scale,angle)


                if CENTER[0]!='' and CENTER[1]!='':
                    center = self.scale_rot_coords(CENTER,scale,angle)
                else:
                    center = CENTER
                 
                #############################
                try:
                    minx = min( minx, min(pos[0],pos_last[0]) ) 
                    maxx = max( maxx, max(pos[0],pos_last[0]) )
                except:
                    pass
                try:
                    miny = min( miny, min(pos[1],pos_last[1]) ) 
                    maxy = max( maxy, max(pos[1],pos_last[1]) )
                except:
                    pass
                try:
                    minz = min( minz, min(pos[2],pos_last[2]) ) 
                    maxz = max( maxz, max(pos[2],pos_last[2]) )
                except:
                    pass

                if mvtype == 0:
                    out.append( [mvtype,pos_last,pos] )
                
                if mvtype == 1:
                    out.append( [mvtype,pos_last,pos,feed, spindle] )

                if mvtype == 2 or mvtype == 3:
                    out.append( [ mvtype,pos_last,pos,center, feed, spindle] )
                    
                    if mvtype == 3:
                        ang1 = self.Get_Angle2(pos_last[0]-center[0],pos_last[1]-center[1])
                        xtmp,ytmp = self.Transform(pos[0]-center[0],pos[1]-center[1],radians(-ang1))
                        ang2 = self.Get_Angle2(xtmp,ytmp)

                    else:
                        ang1 = self.Get_Angle2(pos[0]-center[0],pos[1]-center[1])
                        xtmp,ytmp = self.Transform(pos_last[0]-center[0],pos_last[1]-center[1],radians(-ang1))
                        ang2 = self.Get_Angle2(xtmp,ytmp)
                        
                    if ang2 == 0:
                        ang2=359.999
                        
                    Radius = sqrt( (pos[0]-center[0])**2 +(pos[1]-center[1])**2 )
                            
                    if ang1 > 270:
                        da = 270
                    elif ang1 > 180:
                        da = 180
                    elif ang1 > 90:
                        da = 90
                    else:
                        da = 0
                    for side in [90,180,270,360]:
                        spd = side + da
                        if ang2 > (spd-ang1):
                            if spd > 360:
                                spd=spd-360
                            if spd==90:
                                maxy = max( maxy, center[1]+Radius )
                            if spd==180:
                                minx = min( minx, center[0]-Radius)
                            if spd==270:
                                miny = min( miny, center[1]-Radius )
                            if spd==360:
                                maxx = max( maxx, center[0]+Radius )           
            ###############################################################################
            else:
                if passthru != '':
                    out.append(passthru)
                    
        return out,minx,maxx,miny,maxy,minz,maxz


    #######################################
    def scale_translate(self,code2translate,translate=[0.0,0.0,0.0]):
        
        if translate[0]==0 and translate[1]==0 and translate[2]==0:
            return code2translate
        
        mvtype = -1  # G0 (Rapid), G1 (linear), G2 (clockwise arc) or G3 (counterclockwise arc).
        passthru = ""
        POS     =[0,0,0]
        pos     =[0,0,0]
        pos_last=[0,0,0]
        feed = 0
        spindle = 0
        out = []

        L = 0
        R = 1
        flag_side = 1  

        for line in code2translate:
            if line[0] == 1 or line[0] == 0:
                mvtype   = line[0]
                POS_LAST = line[1][:]
                POS      = line[2][:]
                CENTER   = ['','','']
                if line[0] == 1:
                    feed     = line[3]
                    spindle  = line[4]

            elif line[0] == 3 or line[0] == 2:
                mvtype   = line[0]
                POS_LAST = line[1][:]
                POS      = line[2][:]
                CENTER   = line[3][:]
                feed     = line[4]
                spindle  = line[5]
            else:
                mvtype  = -1
                passthru = line

            ###############################################################################
            if mvtype >= 0 and mvtype <=3:
                pos      = self.scale_trans_coords(POS,translate)
                pos_last      = self.scale_trans_coords(POS_LAST,translate)
                if CENTER[0]!='' and CENTER[1]!='':
                    center      = self.scale_trans_coords(CENTER,translate)
                else:
                    center = CENTER[:]
                 
                #############################
                if mvtype == 0:
                    out.append( [mvtype,pos_last,pos] )
                
                if mvtype == 1:
                    out.append( [mvtype,pos_last,pos,feed,spindle] )

                if mvtype == 2 or mvtype == 3:
                    out.append( [ mvtype,pos_last,pos,center, feed,spindle] )
            ###############################################################################
            else:
                if passthru != '':
                    out.append(passthru)
        return out

    def scale_trans_coords(self,coords,trans):
        x = coords[0] - trans[0]
        y = coords[1] - trans[1]
        z = coords[2] - trans[2]
        return [x,y,z]

    def scale_rot_coords(self,coords,scale,rot):
        x = coords[0] * scale[0]
        y = coords[1] * scale[1]
        z = coords[2] * scale[2]

        x,y = self.Transform(x,y, radians(rot) )
        return [x,y,z]

    def generategcode(self,side,z_safe=.5,
                      plunge_feed=10.0,
                      no_variables=False,
                      Rstock=0.0,
                      Wrap="XYZ",
                      preamble="",
                      postamble="",
                      gen_rapids=False,
                      PLACES_L=4,
                      PLACES_R=3,
                      PLACES_F=1,
                      WriteAll=False,
                      FSCALE="Scale-Rotary",
                      Reverse_Rotary = False,
                      NoComments=False):

        g_code = []

        sign = 1
        if Reverse_Rotary:
            sign = -1

        self.MODAL_VAL={'X':" ", 'Y':" ", 'Z':" ", 'F':" ", 'A':" ", 'B':" ", 'I':" ", 'J':" "}
        LASTX = 0
        LASTY = 0
        LASTZ = z_safe

        g_code.append("( G-Code Modified by G-Code Ripper                        )")
        g_code.append("( by Scorch - 2017 www.scorchworks.com                    )")
        if Wrap == "XYZ":
            AXIS=["X"     , "Y"     , "Z"     ]
            DECP=[PLACES_L, PLACES_L, PLACES_L]  
        elif Wrap == "Y2A":
            AXIS=["X"     , "A"     , "Z"     ]
            DECP=[PLACES_L, PLACES_R, PLACES_L]
            WriteAll=False
            g_code.append("(G-Code Ripper has mapped the Y-Axis to the A-Axis      )")
        elif Wrap == "X2B":
            AXIS=["B"     , "Y"     , "Z"     ]
            DECP=[PLACES_R, PLACES_L, PLACES_L]
            WriteAll=False
            g_code.append("(G-Code Ripper has mapped the X-Axis to the B-Axis      )")
        elif Wrap == "Y2B":
            AXIS=["X"     , "B"     , "Z"     ]
            DECP=[PLACES_L, PLACES_R, PLACES_L]
            WriteAll=False
            g_code.append("(G-Code Ripper has mapped the Y-Axis to the B-Axis      )")
        elif Wrap == "X2A":
            AXIS=["A"     , "Y"     , "Z"     ]
            DECP=[PLACES_R, PLACES_L, PLACES_L]
            WriteAll=False
            g_code.append("(G-Code Ripper has mapped the X-Axis to the A-Axis      )")
            
        if Wrap != "XYZ":
            g_code.append("(A nominal stock radius of %f was used.             )" %(Rstock))
            g_code.append("(Z-axis zero position is the surface of the round stock.  )")
            g_code.append("(---------------------------------------------------------)")
            
        g_code.append("G90   (set absolute distance mode)")
        g_code.append("G90.1 (set absolute distance mode for arc centers)")
        g_code.append("G17   (set active plane to XY)")
        
        if self.units == "in":
            g_code.append("G20   (set units to inches)")
        else:
            g_code.append("G21   (set units to mm)")
            
        if no_variables==False:
            g_code.append("#<z_safe> = % 5.3f " %(z_safe))
            g_code.append("#<plunge_feed> = % 5.0f " %(plunge_feed))
            
        for line in preamble.split('|'):
            g_code.append(line)

        g_code.append("(---------------------------------------------------------)")
        ###################
        ## GCODE WRITING ##
        ###################
        for line in side:
            if line[0] == 1 or line[0] == 2 or line[0] == 3 or (line[0] == 0 and gen_rapids == False):
                D0 = line[2][0]-line[1][0] 
                D1 = line[2][1]-line[1][1] 
                D2 = line[2][2]-line[1][2]
                D012 = sqrt((D0+0j).real**2+(D1+0j).real**2+(D2+0j).real**2)
                
                coordA=[ line[1][0], line[1][1], line[1][2] ]
                coordB=[ line[2][0], line[2][1], line[2][2] ]
                if Wrap == "Y2A" or Wrap == "Y2B":
                    #if line[1][1].imag == 0:
                    if (not isinstance(line[1][1], complex)):
                        coordA[1]=sign*degrees(line[1][1]/Rstock)
                    #if line[2][1].imag == 0:
                    if (not isinstance(line[2][1], complex)):
                        coordB[1]=sign*degrees(line[2][1]/Rstock)
                elif Wrap == "X2B" or Wrap == "X2A":
                    #if line[1][0].imag == 0:
                    if (not isinstance(line[1][0], complex)):
                        coordA[0]=sign*degrees(line[1][0]/Rstock)
                    #if line[2][0].imag == 0:
                    if (not isinstance(line[2][0], complex)):
                        coordB[0]=sign*degrees(line[2][0]/Rstock)

                dx = coordA[0]-LASTX
                dy = coordA[1]-LASTY
                dz = coordA[2]-LASTZ

                # Check if next point is coincident with the
                # current point withing the set accuracy
                if sqrt((dx+0j).real**2 + (dy+0j).real**2 + (dz+0j).real**2) > self.accuracy and gen_rapids == True:
                    ### Move tool to safe height (z_safe) ###
                    if no_variables==False:
                        g_code.append("G0 %c #<z_safe> " %(AXIS[2]) )
                        self.MODAL_VAL[AXIS[2]] = z_safe
                    else:
                        LINE = "G0"
                        LINE = self.app_gcode_line(LINE,AXIS[2],z_safe,DECP[2],WriteAll)
                        if len(LINE) > 2: g_code.append(LINE)
                    
                    ### Move tool to coordinates of next cut ###
                    LINE = "G0"
                    LINE = self.app_gcode_line(LINE,AXIS[0],coordA[0],DECP[0],WriteAll)
                    LINE = self.app_gcode_line(LINE,AXIS[1],coordA[1],DECP[1],WriteAll)
                    if len(LINE) > 2: g_code.append(LINE)

                    if float(coordA[2]) < float(z_safe):
                        if no_variables==False:
                            LINE = "G1"
                            LINE = self.app_gcode_line(LINE,AXIS[2],coordA[2],DECP[2],WriteAll)
                            LINE = LINE + " F #<plunge_feed>"
                            self.MODAL_VAL["F"] = plunge_feed
                            if len(LINE) > 2: g_code.append(LINE)                 
                        else:
                            LINE = "G1"
                            LINE = self.app_gcode_line(LINE,AXIS[2],coordA[2]  ,DECP[2]  , WriteAll)
                            LINE = self.app_gcode_line(LINE,"F"    ,plunge_feed,PLACES_F, WriteAll)
                            if len(LINE) > 2: g_code.append(LINE)

                LASTX = coordB[0]
                LASTY = coordB[1]
                LASTZ = coordB[2]

            if (line[0] == 1) or (line[0] == 2) or (line[0] == 3) or (line[0] == 0 and (gen_rapids == False)):
                try:    LAST0 = float(self.MODAL_VAL[AXIS[0]])
                except: LAST0 = coordB[0]
                try:    LAST1 = float(self.MODAL_VAL[AXIS[1]])
                except: LAST1 = coordB[1]
                try:    LAST2 = float(self.MODAL_VAL[AXIS[2]])
                except: LAST2 = coordB[2]
                
                LINE = "G%d" %(line[0])
                LINE = self.app_gcode_line(LINE,AXIS[0],coordB[0],DECP[0],WriteAll)
                LINE = self.app_gcode_line(LINE,AXIS[1],coordB[1],DECP[1],WriteAll)
                LINE = self.app_gcode_line(LINE,AXIS[2],coordB[2],DECP[2],WriteAll)
                if (line[0] == 1):
                    if ((LINE.find("A") > -1) or (LINE.find("B") > -1)) and (FSCALE == "Scale-Rotary") and (D012>self.Zero):
                        if (LINE.find("X") > -1) or (LINE.find("Y") > -1) or (LINE.find("Z") > -1):
                            if Wrap == "Y2A" or Wrap == "Y2B":
                                Df = sqrt(D0**2 + D2**2)
                            elif Wrap == "X2B" or Wrap == "X2A":
                                Df = sqrt(D1**2 + D2**2)
                            Feed_adj = abs(Df / (D012/line[3]))
                        else:
                            if Wrap == "Y2A" or Wrap == "Y2B":
                                DAf = coordB[1]-LAST1
                                Feed_adj = abs(DAf / (D012/line[3]))
                            elif Wrap == "X2B" or Wrap == "X2A":
                                DAf = coordB[0]-LAST0
                                Feed_adj = abs(DAf / (D012/line[3]))
                    else:
                        Feed_adj = line[3]
                    LINE = self.app_gcode_line(LINE,"F",Feed_adj  ,PLACES_F,WriteAll)
                    
                elif (line[0] == 2) or (line[0] == 3):
                    LINE = self.app_gcode_line(LINE,"I",line[3][0],DECP[0]  ,WriteAll)
                    LINE = self.app_gcode_line(LINE,"J",line[3][1],DECP[1]  ,WriteAll)
                    LINE = self.app_gcode_line(LINE,"F",Feed_adj  ,PLACES_F,WriteAll)
                if len(LINE) > 2: g_code.append(LINE)

            elif (line[0] == 0 and gen_rapids == True):
                pass

            elif line[0] == ";":
                if not NoComments:
                    g_code.append("%s" %(line[1]))
                
            elif line[0] == "M2":
                if gen_rapids == True:
                    if no_variables==False:
                        g_code.append("G0 %c #<z_safe> " %(AXIS[2]) )
                        self.MODAL_VAL[AXIS[2]] = z_safe
                    else:
                        LINE = "G0"
                        LINE = self.app_gcode_line(LINE,AXIS[2],z_safe,DECP[2],WriteAll)
                        g_code.append(LINE)
                        
                for entry in postamble.split('|'):
                    g_code.append(entry)
                #g_code.append(line[0])
            else:
                g_code.append(line)
        ########################
        ## END G-CODE WRITING ##
        ########################
        return g_code


    def app_gcode_line(self,LINE,CODE,VALUE,PLACES,WriteAll):
        if isinstance(VALUE, complex):
            return LINE
        #if VALUE.imag != 0:
        #    return LINE

        if CODE == "F":
            if (VALUE*10**PLACES) < 1:
                # Fix Zero feed rate
                VALUE = 1.0/(10**PLACES)

        if PLACES > 0:
            FORMAT="%% .%df" %(PLACES)
        else:
            FORMAT="%d"
        VAL = FORMAT %(VALUE)

        if ( VAL != self.MODAL_VAL[CODE] )\
            or ( CODE=="I" ) \
            or ( CODE=="J" ) \
            or  (WriteAll):
            LINE = LINE +  " %s%s" %(CODE, VAL)
            self.MODAL_VAL[CODE] = VAL

        return LINE

    def get_arc_intersects(self, p1, p2, xsplit, cent, code):
        xcross1= xsplit
        xcross2= xsplit
     
        R = sqrt( (cent[0]-p1[0])**2 + (cent[1]-p1[1])**2 )
        Rt= sqrt( (cent[0]-p2[0])**2 + (cent[1]-p2[1])**2 )
        if abs(R-Rt) > self.accuracy:  self.fmessage("Radius Warning: R1=%f R2=%f"%(R,Rt))

        val =  R**2 - (xsplit - cent[0])**2
        if val >= 0.0:
            root = sqrt( val )
            ycross1 = cent[1] - root
            ycross2 = cent[1] + root
        else:
            return []

        theta = self.Get_Angle2(p1[0]-cent[0],p1[1]-cent[1])

        xbeta,ybeta = self.Transform(p2[0]-cent[0],p2[1]-cent[1],radians(-theta))
        beta  = self.Get_Angle2(xbeta,ybeta,code)

        if abs(beta) <= self.Zero: beta = 360.0

        xt,yt = self.Transform(xsplit-cent[0],ycross1-cent[1],radians(-theta))
        gt1 = self.Get_Angle2(xt,yt,code)

        xt,yt = self.Transform(xsplit-cent[0],ycross2-cent[1],radians(-theta))
        gt2 = self.Get_Angle2(xt,yt,code)
 
        if gt1 < gt2:
           gamma1 = gt1
           gamma2 = gt2
        else:
           gamma1 = gt2
           gamma2 = gt1
           temp = ycross1
           ycross1 = ycross2
           ycross2 = temp

        dz = p2[2] - p1[2]    
        da = beta
        mz = dz/da
        zcross1 = p1[2] + gamma1 * mz
        zcross2 = p1[2] + gamma2 * mz

        output=[]
        if gamma1 < beta and gamma1 > self.Zero and gamma1 < beta-self.Zero:
            output.append([xcross1,ycross1,zcross1])
        if gamma2 < beta and gamma1 > self.Zero and gamma2 < beta-self.Zero:
            output.append([xcross2,ycross2,zcross2])
        
        #print(" start: x1 =%5.2f y1=%5.2f z1=%5.2f" %(p1[0],     p1[1],     p1[2]))
        #print("   end: x2 =%5.2f y2=%5.2f z2=%5.2f" %(p2[0],     p2[1],     p2[2]))
        #print("center: xc =%5.2f yc=%5.2f xsplit=%5.2f code=%s" %(cent[0],cent[1],xsplit,code))
        #print("R = %f" %(R))
        #print("theta =%5.2f" %(theta))
        #print("beta  =%5.2f gamma1=%5.2f gamma2=%5.2f\n" %(beta,gamma1,gamma2))
        #cnt=0
        #for line in output:
        #    cnt=cnt+1
        #    print("arc cross%d: %5.2f, %5.2f, %5.2f" %(cnt, line[0], line[1], line[2]))
        #print(output)
        #print("----------------------------------------------\n")

        return output

    def arc2lines(self, p1, p2, cent, code, plane="17"):
        if   plane == "18":
            xind=2
            yind=0
            zind=1
        elif plane == "19":
            xind=1
            yind=2
            zind=0
        elif plane == "17":
            xind=0
            yind=1
            zind=2
        
        R = sqrt( (cent[xind]-p1[xind])**2 + (cent[yind]-p1[yind])**2 )
        Rt= sqrt( (cent[xind]-p2[xind])**2 + (cent[yind]-p2[yind])**2 )
        if abs(R-Rt) > self.accuracy:  self.fmessage("Radius Warning: R1=%f R2=%f "%(R,Rt))

        if code == 3:
            theta = self.Get_Angle2(p1[xind]-cent[xind],p1[yind]-cent[yind])
            xbeta,ybeta = self.Transform(p2[xind]-cent[xind],p2[yind]-cent[yind],radians(-theta))
            X1 = p1[xind]
            Y1 = p1[yind]
            Z1 = p1[zind]
            zstart = Z1
            zend   = p2[zind]
        if code == 2:
            theta = self.Get_Angle2(p2[xind]-cent[xind],p2[yind]-cent[yind])
            xbeta,ybeta = self.Transform(p1[xind]-cent[xind],p1[yind]-cent[yind],radians(-theta))
            X1 = p2[xind]
            Y1 = p2[yind]
            Z1 = p2[zind]
            zstart = Z1
            zend   = p1[zind]
            
        beta  = self.Get_Angle2(xbeta,ybeta) #,code)
        
        if abs(beta) <= self.Zero: beta = 360.0
        ##########################################
        arc_step=self.arc_angle
        
        my_range=[]
        
        at=arc_step
        while at < beta:
            my_range.append(at)
            at = at+arc_step
        my_range.append(beta)

        

        new_lines=[]
        for at in my_range:
            xt,yt = self.Transform(R,0,radians(theta+at))

            X2 = cent[xind] + xt
            Y2 = cent[yind] + yt
            #Z2 = p1[zind] + at*(p2[zind]-p1[zind])/beta
            Z2 = zstart + at*(zend-zstart)/beta
            data = ["","","","","",""]


            if code == 3:
                data[xind]=X1
                data[yind]=Y1
                data[zind]=Z1
                data[3+xind]=X2
                data[3+yind]=Y2
                data[3+zind]=Z2
                new_lines.append(data)
            else:
                data[xind]=X2
                data[yind]=Y2
                data[zind]=Z2
                data[3+xind]=X1
                data[3+yind]=Y1
                data[3+zind]=Z1
                new_lines.insert(0, data)
        
            X1=X2
            Y1=Y2
            Z1=Z2
            at = at+arc_step

        return new_lines
    
    def get_line_intersect(self,p1, p2, xsplit):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dz = p2[2] - p1[2]
        
        xcross = xsplit 
        try:
            my = dy/dx
            by = p1[1] - my * p1[0]
            ycross = my*xsplit + by
        except:
            ycross = p1[1]
        try:
            mz = dz/dx
            bz = p1[2] - mz * p1[0]
            zcross = mz*xsplit + bz
        except:
            zcross = p1[2]

        output=[]
        if xcross > min(p1[0],p2[0])+self.Zero and xcross < max(p1[0],p2[0])-self.Zero:
            output.append([xcross,ycross,zcross])            
        return output


    def apleft(self, gtext):
        self.left_side.append(gtext)


    def apright(self, gtext):
        self.right_side.append(gtext)


    def apboth(self, gtext):
        self.left_side.append(gtext)
        self.right_side.append(gtext)


    def rm_text(self,line,s,e):
        if e == -1:
            e = len(line)
        temp1 = line[0:s]
        temp2 = line[e+1:len(line)]
        return temp1+temp2


    def insert_text(self,line,itext,s):
        temp1 = line[0:s]
        temp2 = line[s:len(line)]
        return temp1+itext+temp2


    def coordop(self,coords,offset,rot):
        x = coords[0]
        y = coords[1] 
        z = coords[2]
        x = x - offset[0]
        y = y - offset[1]
        z = z - offset[2] 
        x,y = self.Transform(x,y, radians(rot) )
        return [x,y,z]


    def coordunop(self,coords,offset,rot):
        x = coords[0]
        y = coords[1] 
        z = coords[2]
        x,y = self.Transform(x,y, radians(-rot) )
        x = x + offset[0]
        y = y + offset[1]
        z = z + offset[2] 
        return [x,y,z]

    #######################################    #######################################
    #######################################    #######################################
    #######################################    #######################################
    #######################################    #######################################

    def FUNCTION_EVAL(self,list):
        #list consists of [name,val1,val2]
        name = list[0]
        val1 = float(list[1])
        fval = float(val1)
        #############################################
        ########### G-CODE FUNCTIONS ################
        #############################################
        # ATAN[Y]/[X] Four quadrant inverse tangent #
        # ABS[arg]    Absolute value                #
        # ACOS[arg]   Inverse cosine                #
        # ASIN[arg]   Inverse sine                  #
        # COS[arg]    Cosine                        #
        # EXP[arg]    e raised to the given power   #
        # FIX[arg]    Round down to integer         #
        # FUP[arg]    Round up to integer           #
        # ROUND[arg]  Round to nearest integer      #
        # LN[arg]     Base-e logarithm              #
        # SIN[arg]    Sine                          #
        # SQRT[arg]   Square Root                   #
        # TAN[arg]    Tangent                       #
        # EXISTS[arg]	Check named Parameter   #
        #############################################
        if name == "ATAN":
            fval2 = float(list[2])
            atan2(fval1,fval2)
        if name == "ABS":
            return abs(fval)
        if name == "ACOS":
            return degrees(acos(fval))
        if name == "ASIN":
            return degrees(asin(fval))
        if name == "COS":
            return cos(radians(fval))
        if name == "EXP":
            return exp(fval)
        if name == "FIX":
            return floor(fval)
        if name == "FUP":
            return ceil(fval)
        if name == "ROUND":
            return round(fval)
        if name == "LN":
            return log(fval)
        if name == "SIN":
            return sin(radians(fval))
        if name == "SQRT":
            return sqrt(fval)
        if name == "TAN":
            return tan(radians(fval))
        if name == "EXISTS":
            pass
        
    def EXPRESSION_EVAL(self,line):
        ###################################################
        ###          EVALUATE MATH IN REGION            ###
        ###################################################
        line_in = line
        P = 0
        if P==1: self.fmessage("line=%s" %(line))

        if len(line)<2:
            MSG = "ERROR EXP-1: Unable to evaluate expression: %s\n" %(line_in)
            raise ValueError(MSG)
        
        
        line = line.replace(" ","")
        
        #################################################
        ###           G-CODE OPPERATORS               ###
        ###          In Precedence Order              ###
        #################################################
        ##    **                                        #
        ##    * / MOD                                   #
        ##    + -                                       #
        ##    EQ NE GT GE LT LE                         #
        ##    AND OR XOR                                #
        #################################################

        #################################################
        ### Replace multiple +/- with single operator ###
        #################################################
        cnt = 1
        while cnt > 0:
            if (not self.cmp_new(line[cnt],'+')) or (not self.cmp_new(line[cnt],'-')):
                sign = 1
                span = 0
                FLAG = True
                while FLAG:
                    if not self.cmp_new(line[cnt+span],'+'):
                        span = span + 1
                    elif not self.cmp_new(line[cnt+span],'-'):
                        sign = -sign
                        span = span + 1
                    else:
                        FLAG = False
                tmp1=line[:(cnt)]
                tmp2=line[(cnt+span):]
                if sign > 0:
                    line = tmp1+'+'+tmp2
                else:
                    line = tmp1+'-'+tmp2    
            cnt=cnt + 1
            if cnt >= len(line):
                cnt = -1
                
        #########################################
        ### Replace multi-character operators ###
        ### with single character identifiers ###
        #########################################
        line = line.replace("XOR","|")
        line = line.replace("AND","&")
        line = line.replace("LE","l")
        line = line.replace("LT","<")
        line = line.replace("GE","g")
        line = line.replace("GT",">")
        line = line.replace("NE","!")
        line = line.replace("EQ","=")
        line = line.replace("**","^")

        #########################################
        ###     Split the text into a list    ###
        #########################################
        line = re.split( "([\[,\],\^,\*,\/,\%,\+,\-,\|  ,\&  ,\l ,\< ,\g ,\> ,\! ,\= ])", line)
        
        #########################################
        ### Remove empty items from the list  ###
        #########################################
        for i in range(line.count('')): line.remove('')
        
        #########################################
        ###   Find the last "[" in the list   ###
        #########################################
        s=-1
        for cnt in range(s+1,len(line)):
            if line[cnt] == '[':
                s = cnt
        if s == -1:
            MSG = "ERROR EXP-2: Unable to evaluate expression: %s" %(line_in)
            #self.fmessage(MSG)
            raise ValueError(MSG)
        
        #################################################################    
        ###  While there are still brackets "[...]" keep processing   ###
        #################################################################
        while s != -1:
            ##############################################################
            ### Find the first occurance of "]" after the current "["  ###
            ##############################################################
            e=-1
            for cnt in range(len(line)-1,s,-1):
                if line[cnt] == ']':
                    e = cnt
                    
            #############################################
            ###  Find the items between the brackets  ###
            #############################################
            temp = line[s+1:e]
            
            ##############################################################
            ###  Fix Some Special Cases                                ###
            ##############################################################
            ### **-  *-  MOD-                                          ###
            ##############################################################
            for cnt in range(0,len(temp)):
                if (not self.cmp_new(temp[cnt],'^')) or \
                   (not self.cmp_new(temp[cnt],'*')) or \
                   (not self.cmp_new(temp[cnt],'%')):
                    if not self.cmp_new(temp[cnt+1],'-'):
                        temp[cnt+1]=''
                        temp[cnt+2]= -float(temp[cnt+2])
                    elif not self.cmp_new(temp[cnt+1],'+'):
                        temp[cnt+1]=''
                        temp[cnt+2]= float(temp[cnt+2])
            for i in range(temp.count('')): temp.remove('')

            #####################################
            XOR_operation = self.list_split(temp,"|") #XOR
            for iXOR in range(0,len(XOR_operation)):
                #####################################
                AND_operation = self.list_split(XOR_operation[iXOR],"&") #AND
                for iAND in range(0,len(AND_operation)):
                    #####################################
                    LE_operation = self.list_split(AND_operation[iAND],"l") #LE
                    for iLE in range(0,len(LE_operation)):
                        #####################################
                        LT_operation = self.list_split(LE_operation[iLE],"<") #LT
                        for iLT in range(0,len(LT_operation)):
                            #####################################
                            GE_operation = self.list_split(LT_operation[iLT],"g") #GE
                            for iGE in range(0,len(GE_operation)):
                                #####################################
                                GT_operation = self.list_split(GE_operation[iGE],">") #GT
                                for iGT in range(0,len(GT_operation)):
                                    #####################################
                                    NE_operation = self.list_split(GT_operation[iGT],"!") #NE
                                    for iNE in range(0,len(NE_operation)):
                                        #####################################
                                        EQ_operation = self.list_split(NE_operation[iNE],"=") #EQ
                                        for iEQ in range(0,len(EQ_operation)):
                                            #####################################
                                            add = self.list_split(EQ_operation[iEQ],"+")
                                            for cnt in range(1,len(add)):
                                                if add[cnt-1]==[]:
                                                    add[cnt-1]  = ''
                                            for i in range(add.count('')): add.remove('')      
                                            for iadd in range(0,len(add)):
                                                #####################################
                                                subtract = self.list_split(add[iadd],"-")         
                                                for cnt in range(1,len(subtract)):
                                                    if subtract[cnt-1]==[]:
                                                        subtract[cnt-1]  = ''
                                                        subtract[cnt][0] = -float(subtract[cnt][0])
                                                for i in range(subtract.count('')): subtract.remove('')
                                                for isub in range(0,len(subtract)):
                                                    #####################################
                                                    multiply = self.list_split(subtract[isub],"*")
                                                    for imult in range(0,len(multiply)):
                                                        #####################################
                                                        divide = self.list_split(multiply[imult],"/")
                                                        for idiv in range(0,len(divide)):
                                                            #####################################
                                                            mod = self.list_split(divide[idiv],"%")
                                                            for imod in range(0,len(mod)):
                                                                #####################################
                                                                power = self.list_split(mod[imod],"^")
                                                                for ipow in range(0,len(power)):
                                                                    if power[ipow]==[]:
                                                                        MSG = "ERROR EXP-3: Unable to evaluate expression: %s" %(line_in)
                                                                        raise ValueError(MSG)
                                                                    
                                                                    if type(power[0]) is list:
                                                                        power_len = len(power[0])
                                                                    else:
                                                                        power_len = 1
                                                                    if power_len > 1:
                                                                        power[ipow] = self.FUNCTION_EVAL(power[0])
                                                                    else:
                                                                        power[ipow] = float(power[ipow][0])
                                                                #####################################
                                                                res_power=power[0]
                                                                for k in range(1,len(power)):
                                                                    res_power = res_power**power[k]
                                                                    if P==True: self.fmessage("  POWER"+str(power)+"="+str(res_power))
                                                                mod[imod]=res_power
                                                            #####################################
                                                            #REVERSE MOD
                                                            res_mod=mod[len(mod)-1]
                                                            for k in range(len(mod),1,-1):
                                                                res_mod = mod[k-2]%res_mod
                                                                self.fmessage("     MOD"+str(mod)+"="+str(res_mod))
                                                            divide[idiv]=res_mod
                                                        #####################################
                                                        res_divide=divide[0]
                                                        for k in range(1,len(divide),1):
                                                            res_divide = res_divide/divide[k]
                                                            if P==True: self.fmessage("  DIVIDE"+str(divide)+"="+str(res_divide))
                                                        multiply[imult]=res_divide
                                                    #####################################
                                                    res_multiply=multiply[0]
                                                    for k in range(1,len(multiply)):
                                                        res_multiply = res_multiply*multiply[k]
                                                        if P==True: self.fmessage("MULTIPLY"+str(multiply)+"="+str(res_multiply))         
                                                    subtract[isub]=res_multiply
                                                #####################################
                                                res_subtract=subtract[0]
                                                for k in range(1,len(subtract)):
                                                    res_subtract = res_subtract-subtract[k]
                                                    if P==True: self.fmessage("SUBTRACT"+str(subtract)+"="+str(res_subtract))
                                                add[iadd]=res_subtract
                                            #####################################
                                            res_add=add[len(add)-1]
                                            for k in range(len(add),1,-1):
                                                res_add = add[k-2]+res_add
                                                if P==True: self.fmessage("     ADD"+str(add)+"="+str(res_add))
                                            EQ_operation[iEQ]=res_add
                                        #####################
                                        res_EQ=EQ_operation[0]
                                        for k in range(1,len(EQ_operation),1):
                                            if res_EQ == EQ_operation[k]:
                                                res_EQ = 1
                                            else:
                                                res_EQ = 0
                                            if P==True: self.fmessage("      EQ"+str(EQ_operation)+"="+str(res_EQ))
                                        NE_operation[iNE]=res_EQ
                                    #####################
                                    res_NE=NE_operation[0]
                                    for k in range(1,len(NE_operation),1):
                                        if res_NE != NE_operation[k]:
                                            res_NE = 1
                                        else:
                                            res_NE = 0
                                        if P==True: self.fmessage("      NE"+str(NE_operation)+"="+str(res_NE))
                                    GT_operation[iGT]=res_NE
                                #####################
                                res_GT=GT_operation[0]
                                for k in range(1,len(GT_operation),1):
                                    if res_GT > GT_operation[k]:
                                        res_GT = 1
                                    else:
                                        res_GT = 0
                                    if P==True: self.fmessage("      GT"+str(GT_operation),"="+str(res_GT))
                                GE_operation[iGE]=res_GT
                            #####################
                            res_GE=GE_operation[0]
                            for k in range(1,len(GE_operation),1):
                                if res_GE >= GE_operation[k]:
                                    res_GE = 1
                                else:
                                    res_GE = 0
                                if P==True: self.fmessage("      GE"+str(GE_operation)+"="+str(res_GE))
                            LT_operation[iLT]=res_GE
                        #####################
                        res_LT=LT_operation[0]
                        for k in range(1,len(LT_operation),1):
                            if res_LT < LT_operation[k]:
                                res_LT = 1
                            else:
                                res_LT = 0
                            if P==True: self.fmessage("      LT"+str(LT_operation)+"="+str(res_LT))
                        LE_operation[iLE]=res_LT
                    #####################
                    res_LE=LE_operation[0]
                    for k in range(1,len(LE_operation),1):
                        if res_LE <= LE_operation[k]:
                            res_LE = 1
                        else:
                            res_LE = 0
                        if P==True: self.fmessage("      LE"+str(LE_operation)+"="+str(res_LE))
                    AND_operation[iAND]=res_LE
                #####################
                res_AND=AND_operation[0]
                for k in range(1,len(AND_operation),1):
                    if res_AND and AND_operation[k]:
                        res_AND = 1
                    else:
                        res_AND = 0
                    if P==True: self.fmessage("      AND"+str(AND_operation)+"="+str(res_AND))
                XOR_operation[iXOR]=res_AND
            #####################
            res_XOR=XOR_operation[0]
            for k in range(1,len(XOR_operation),1):
                if bool(res_XOR) ^ bool(XOR_operation[k]):
                    res_XOR = 1
                else:
                    res_XOR = 0
                if P==True: self.fmessage("      XOR"+str(XOR_operation)+"="+str(res_XOR))

            #####################################
            ### Return NEW VALUE to the list  ###
            #####################################
            for i in range(e,s-1,-1): line.pop(i)
            line.insert(int(s),res_XOR)

            #############################
            # Find Last "[" in the list #
            #############################
            s=-1
            for cnt in range(s+1,len(line)):
                if line[cnt] == '[':
                    s = cnt
        #################################################################    
        ###  END of While there are still brackets "[...]"            ###
        #################################################################
        
        if len(line) > 1:
            MSG = "ERROR EXP-5: Unable to evaluate expression: %s" %(line_in)
            raise ValueError(MSG)
        return "%.4f" %(line[0])


    def list_split(self,lst,obj):
        loc=[]
        index = -1
        for cnt in range(0,len(lst)):
            if not self.cmp_new(lst[cnt],obj):
                loc.append( lst[index+1:cnt] )
                index=cnt
        loc.append( lst[index+1:len(lst)])
        return loc


    #Define self.cmp_new, cmp replacement for Python 3 compatability
    def cmp_new(self,A,B):
        if A==B:
            return False
        else:
            return True

    ############################################################################
    # routine takes an x and a y coords and does a cordinate transformation    #
    # to a new coordinate system at angle from the initial coordinate system   #
    # Returns new x,y tuple                                                    #
    ############################################################################
    def Transform(self,x,y,angle):
        newx = x * cos(angle) - y * sin(angle)
        newy = x * sin(angle) + y * cos(angle)
        return newx,newy

    ############################################################################
    # routine takes an sin and cos and returnss the angle (between 0 and 360)  #
    ############################################################################
    def Get_Angle2(self,x,y,code=""):
        angle = 90.0-degrees(atan2(x,y))
        if angle < 0:
            angle = 360 + angle
        if code == "G2":
            return (360.0 - angle)
        else:
            return angle


    ##################################################
    ###  Generate paths for Laser cutter           ###
    ##################################################
    def generate_laser_paths(self,side,Rapids=True):
        ecoords = []
        #################################
        xlast = -99999
        ylast = -99999
        loop = 1
        for line in side:
            #print line
            if line[0] == 1:
                feed    = line[3]
                spindle = line[4]
                x1=(line[1][0]+0j).real
                y1=(line[1][1]+0j).real
                z1=(line[1][2]+0j).real

                x2=(line[2][0]+0j).real
                y2=(line[2][1]+0j).real
                z2=(line[2][2]+0j).real
    
                if xlast!=x1 or ylast!=y1:
                    loop = loop+1
                    ecoords.append([x1,y1,loop,feed,spindle])
                    
                if x2!=x1 or y2!=y1:
                    ecoords.append([x2,y2,loop,feed,spindle])

                xlast = x2
                ylast = y2
        ######################################
        return ecoords
    ##################################################
    ###    End Generate paths for Laser cutter     ###
    ##################################################



if __name__ == "__main__":
    g_rip = G_Code_Rip()
    filename="Z:\\text.ngc"
    MSG = g_rip.Read_G_Code(filename, XYarc2line = True, arc_angle=2, units="in", Accuracy="")
    print MSG
    ecoords = g_rip.generate_laser_paths(g_rip.g_code_data)
    for line in ecoords:
        print line
