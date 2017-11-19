#!/usr/bin/python
"""
    DXF Utilities

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
from math import *
Zero       = 0.00001

####################################################
##     PointClass from dxf2gcode_b02_point.py     ##
####################################################
class PointClass:
    def __init__(self,x=0,y=0):
        self.x=x
        self.y=y
    def __str__(self):
        return ('X ->%6.3f  Y ->%6.3f' %(self.x,self.y))

####################################################
##  Begin Excerpts from dxf2gcode_b02_nurbs_calc  ##
####################################################
class NURBSClass:
    def __init__(self,degree=0,Knots=[],Weights=None,CPoints=None):
        self.degree=degree              #Spline degree
        self.Knots=Knots                #Knot Vector
        self.CPoints=CPoints            #Control points of splines [2D]
        self.Weights=Weights            #Weighting of the individual points

        #Initializing calculated variables
        self.HCPts=[]                   #Homogeneous points vectors [3D]

        #Convert Points in Homogeneous points
        self.CPts_2_HCPts()

        #Creating the BSplineKlasse to calculate the homogeneous points
        self.BSpline=BSplineClass(degree=self.degree,\
                                  Knots=self.Knots,\
                                  CPts=self.HCPts)

    #Calculate a number of evenly distributed points
    def calc_curve_old(self,n=0, cpts_nr=20):
        #Initial values for step and u
        u=0; Points=[]
        step=self.Knots[-1]/(cpts_nr-1)
        while u<=self.Knots[-1]:
            Pt=self.NURBS_evaluate(n=n,u=u)
            Points.append(Pt)
            u+=step
        return Points


    #Calculate a number points using error limiting
    def calc_curve(self,n=0, tol_deg=5):
        #Initial values for step and u
        u=0; Points=[]

        tol = radians(tol_deg)
        i=1
        while self.Knots[i]==0:
            i=i+1
        step=self.Knots[i]/3

        Pt1=self.NURBS_evaluate(n=n,u=0.0)
        Points.append(Pt1)
        while u<self.Knots[-1]:
            if (u+step > self.Knots[-1]):
                step = self.Knots[-1]-u

            Pt2=self.NURBS_evaluate(n=n,u=u+step)
            Pt_test=self.NURBS_evaluate(n=n,u=u + step/2)

            ###
            DX = Pt2.x-Pt1.x
            DY = Pt2.y-Pt1.y
            cord = sqrt(DX*DX + DY*DY)
            DXtest = Pt_test.x-(Pt1.x+Pt2.x)/2.0
            DYtest = Pt_test.y-(Pt1.y+Pt2.y)/2.0
            t = sqrt(DXtest*DXtest + DYtest*DYtest)
            if (abs(t) > Zero):
                R = (cord*cord/4.0 + t*t)/(2.0*t)
            else:
                R = 0.0

            dx1 = (Pt_test.x - Pt1.x)
            dy1 = (Pt_test.y - Pt1.y)
            L1 = sqrt(dx1*dx1 + dy1*dy1)

            dx2 = (Pt2.x - Pt_test.x)
            dy2 = (Pt2.y - Pt_test.y)
            L2 = sqrt(dx2*dx2 + dy2*dy2)

            if L1 > Zero and L2 > Zero and R > Zero:
                sin_ratio = (cord/2)/R
                if abs(sin_ratio) > 1.0:
                    sin_ratio = round(sin_ratio,0)
                angle = 2 * asin(sin_ratio)
            else:
                angle=0.0

            if angle > tol:
                step = step/2
            else:
                u+=step
                Points.append(Pt2)
                step = step*2
                Pt1=Pt2
        return Points


    #Calculate a point of NURBS
    def NURBS_evaluate(self,n=0,u=0):

        #Calculate the homogeneous points to the n th derivative
        HPt=self.BSpline.bspline_ders_evaluate(n=n,u=u)

        #Point back to normal coordinates transform
        Point=self.HPt_2_Pt(HPt[0])
        return Point

    #Convert the NURBS control points and weight in a homogeneous vector
    def CPts_2_HCPts(self):
        for P_nr in range(len(self.CPoints)):
            HCPtVec=[self.CPoints[P_nr].x*self.Weights[P_nr],\
                       self.CPoints[P_nr].y*self.Weights[P_nr],\
                       self.Weights[P_nr]]
            self.HCPts.append(HCPtVec[:])

    #Convert a homogeneous vector point in a point
    def HPt_2_Pt(self,HPt):
        return PointClass(x=HPt[0]/HPt[-1],y=HPt[1]/HPt[-1])

class BSplineClass:
    def __init__(self,degree=0,Knots=[],CPts=[]):
        self.degree=degree
        self.Knots=Knots
        self.CPts=CPts

        self.Knots_len=len(self.Knots)
        self.CPt_len=len(self.CPts[0])
        self.CPts_len=len(self.CPts)

        # Incoming inspection, fit the upper node number, etc.
        if  self.Knots_len< self.degree+1:
            raise StandardError("SPLINE: degree greater than number of control points.")
        if self.Knots_len != (self.CPts_len + self.degree+1):
            raise StandardError("SPLINE: Knot/Control Point/degree number error.")

    #Modified Version of Algorithm A3.2 from "THE NURBS BOOK" pg.93
    def bspline_ders_evaluate(self,n=0,u=0):
        #Calculating the position of the node vector
        span=self.findspan(u)

        #Compute the basis function up to the n th derivative at the point u
        dN=self.ders_basis_functions(span,u,n)

        p=self.degree
        du=min(n,p)

        CK=[]
        dPts=[]
        for i in range(self.CPt_len):
            dPts.append(0.0)
        for k in range(n+1):
            CK.append(dPts[:])

        for k in range(du+1):
            for j in range(p+1):
                for i in range(self.CPt_len):
                    CK[k][i]+=dN[k][j]*self.CPts[span-p+j][i]
        return CK

    #Algorithm A2.1 from "THE NURBS BOOK" pg.68
    def findspan(self,u):
        #Special case when the value is == Endpoint
        if(u==self.Knots[-1]):
            return self.Knots_len-self.degree-2

        # Binary search
        # (The interval from high to low is always halved by
        # [mid: mi +1] value lies between the interval of Knots)
        low=self.degree
        high=self.Knots_len
        mid=int((low+high)/2)
        while ((u<self.Knots[mid])or(u>=self.Knots[mid+1])):
            if (u<self.Knots[mid]):
                high=mid
            else:
                low=mid
            mid=int((low+high)/2)
            if low==high: #new
                break     #new
        return mid

    #Algorithm A2.3 from "THE NURBS BOOK" pg.72
    def ders_basis_functions(self,span,u,n):
        d=self.degree

        #Initialize the a matrix
        a=[]
        zeile=[]
        for j in range(d+1):
            zeile.append(0.0)
        a.append(zeile[:]); a.append(zeile[:])

        #Initialize the ndu matrix
        ndu=[]
        zeile=[]
        for i in range(d+1):
            zeile.append(0.0)
        for j in range(d+1):
            ndu.append(zeile[:])

        #Initialize the ders matrix
        ders=[]
        zeile=[]
        for i in range(d+1):
            zeile.append(0.0)
        for j in range(n+1):
            ders.append(zeile[:])

        ndu[0][0]=1.0
        left=[0]
        right=[0]

        for j in range(1,d+1):
            left.append(u-self.Knots[span+1-j])
            right.append(self.Knots[span+j]-u)
            saved=0.0
            for r in range(j):
                #Lower Triangle
                ndu[j][r]=right[r+1]+left[j-r]
                temp=ndu[r][j-1]/ndu[j][r]
                #Upper Triangle
                ndu[r][j]=saved+right[r+1]*temp
                saved=left[j-r]*temp
            ndu[j][j]=saved

        #Load the basis functions
        for j in range(d+1):
            ders[0][j]=ndu[j][d]

        #This section computes the derivatives (Eq. [2.9])
        for r in range(d+1): #Loop over function index
            s1=0; s2=1  #Alternate rows in array a
            a[0][0]=1.0
            for k in range(1,n+1):
                der=0.0
                rk=r-k; pk=d-k
                if(r>=k):
                    a[s2][0]=a[s1][0]/ndu[pk+1][rk]
                    der=a[s2][0]*ndu[rk][pk]
                if (rk>=-1):
                    j1=1
                else:
                    j1=-rk
                if (r-1<=pk):
                    j2=k-1
                else:
                    j2=d-r

                #Here he is not in the first derivative of pure
                for j in range(j1,j2+1):
                    a[s2][j]=(a[s1][j]-a[s1][j-1])/ndu[pk+1][rk+j]
                    der+=a[s2][j]*ndu[rk+j][pk]

                if(r<=pk):
                    a[s2][k]=-a[s1][k-1]/ndu[pk+1][r]
                    der+=a[s2][k]*ndu[r][pk]

                ders[k][r]=der
                j=s1; s1=s2; s2=j #Switch rows

        #Multiply through by the the correct factors
        r=d
        for k in range(1,n+1):
            for j in range(d+1):
                ders[k][j] *=r
            r*=(d-k)
        return ders

####################################################
##  End Excerpts from dxf2gcode_b02_nurbs_calc.py ##
####################################################

class Header:
    def __init__(self):
        self.variables = dict()
        self.last_var = None
    def new_var(self, kw):
        self.variables.update({kw: dict()})
        self.last_var = self.variables[kw]
    def new_val(self, val):
        self.last_var.update({ str(val[0]) : val[1] })

class Entity:
    def __init__(self, _type):
        self.type = _type
        self.data = dict()
    def update(self, value):
        key = str(value[0])
        val = value[1]
        if key in self.data:
            if type(self.data[key]) != list:
                self.data[key] = [self.data[key]]
            self.data[key].append(val)
        else:
            self.data.update({key:val})

class Entities:
    def __init__(self):
        self.entities = []
        self.last = None
    def new_entity(self, _type):
        e = Entity(_type)
        self.entities.append(e)
        self.last = e
    def update(self, value):
        self.last.update(value)

class Layer:
    def __init__(self):
        self.data = dict()
    def update(self, value):
        key = str(value[0])
        val = value[1]
        if key in self.data:
            if type(self.data[key]) != list:
                self.data[key] = [self.data[key]]
            self.data[key].append(val)
        else:
            self.data.update({key:val})

class Layers:
    def __init__(self):
        self.layers = []
        self.last = None
    def new_layer(self):
        e = Layer()
        self.layers.append(e)
        self.last = e
    def update(self, value):
        self.last.update(value)

class Block:
    def __init__(self, master):
        self.master = master
        self.data = dict()
        self.entities = []
        self.le = None
    def new_entity(self, value):
        self.le = Entity(value)
        self.entities.append(self.le)
    def update(self, value):
        if self.le == None:
            val = str(value[0])
            self.data.update({val:value[1]})
            if val == "2":
                self.master.blocks[value[1]] = self
        else:
            self.le.update(value)

class Blocks:
    def __init__(self):
        self.blocks = dict()
        self.last_var = None
    def new_block(self):
        b = Block(self)
        self.last_block = b
        self.last_var = b
    def new_entity(self, value):
        self.last_block.new_entity(value)
    def update(self, value):
        self.last_block.update(value)

class DXF_CLASS:
    def __init__(self):
        self.units = 0
        self.dxf_messages = ""
        self.coords = []
        self.cut_coords = []
        self.eng_coords = []
        strings = []
        floats = []
        ints = []
        self.layer_color=dict()

        strings += list(range(0, 10))     #String (255 characters maximum; less for Unicode strings)
        floats += list(range(10, 60))     #Double precision 3D point
        ints += list(range(60, 80))       #16-bit integer value
        ints += list(range(90,100))       #32-bit integer value
        strings += [100]                  #String (255 characters maximum; less for Unicode strings)
        strings += [102]                  #String (255 characters maximum; less for Unicode strings
        strings += [105]                  #String representing hexadecimal (hex) handle value
        floats += list(range(140, 148))   #Double precision scalar floating-point value
        ints += list(range(170, 176))     #16-bit integer value
        ints += list(range(280, 290))     #8-bit integer value
        strings += list(range(300, 310))  #Arbitrary text string
        strings += list(range(310, 320))  #String representing hex value of binary chunk
        strings += list(range(320, 330))  #String representing hex handle value
        strings += list(range(330, 369))  #String representing hex object IDs
        strings += [999]                  #Comment (string)
        strings += list(range(1000, 1010))#String (255 characters maximum; less for Unicode strings)
        floats += list(range(1010, 1060)) #Floating-point value
        ints += list(range(1060, 1071))   #16-bit integer value
        ints += [1071]                    #32-bit integer value


        self.funs = []
        for i in range(0,1072):
            self.funs.append(self.read_none)

        for i in strings:
            self.funs[i] = self.read_string

        for i in floats:
            self.funs[i] = self.read_float

        for i in ints:
            self.funs[i] = self.read_int

        self.unit_vals = ["Unitless",
                     "Inches",
                     "Feet",
                     "Miles",
                     "Millimeters",
                     "Centimeters",
                     "Meters",
                     "Kilometers",
                     "Microinches",
                     "Mils"]
        self.POLY_FLAG   = None
        self.POLY_CLOSED = None

    def dxf_message(self,text):
        self.dxf_messages = self.dxf_messages + "\n" + text
        
    def read_int(self,data):
        return int(float(data))

    def read_float(self,data):
        return float(data)

    def read_string(self,data):
        return str(data)

    def read_none(self,data):
        return None

###    def read_dxf_file(self, name, data):
###        fd = file(name)
###        Skip = True
###        for line in fd:
###            group_code = int(line)
###
###            value = fd.next().replace('\r', '')
###            value = value.replace('\n', '')
###            value = value.lstrip(' ')
###            value = value.rstrip(' ')
###            value = self.funs[group_code](value)
###            if (value != "SECTION") and Skip:
###                continue
###            else:
###                Skip = False
###            data.append((group_code, value))
###        fd.close()

    def read_dxf_data(self, fd, data):
        self.comment="None"
        Skip = True
        fd_iter = iter(fd)
        for line in fd_iter:
            try:
                group_code = int(line)
                value = next(fd_iter).replace('\r', '')
                value = value.replace('\n', '')
                value = value.lstrip(' ')
                value = value.rstrip(' ')
                value = self.funs[group_code](value)
                if (value != "SECTION") and Skip:
                    if group_code==999:
                        self.comment=value
                    continue
                else:
                    Skip = False
                data.append((group_code, value))
            except:
                pass

    ##########################################################################
    # routine takes an sin and cos and returns the angle (between 0 and 360) #
    ##########################################################################
    def Get_Angle(self,y,x):
        angle = 90.0-degrees(atan2(x,y))
        if angle < 0:
            angle = 360 + angle
        return angle

    ############################################################################
    # routine takes an x and a y coords and does a coordinate transformation   #
    # to a new coordinate system at angle from the initial coordinate system   #
    # Returns new x,y tuple                                                    #
    ############################################################################
    def Transform(self,x,y,angle):
        newx = x * cos(angle) - y * sin(angle)
        newy = x * sin(angle) + y * cos(angle)
        return newx,newy

    def bulge_coords(self,x0,y0,x1,y1,bulge,tol_deg=5):
        global Zero
        bcoords=[]
        if bulge < 0.0:
            sign = 1
            bulge=abs(bulge)
        else:
            sign = -1

        dx      = x1-x0
        dy      = y1-y0
        c       = sqrt(dx**2 + dy**2)
        alpha   = 2.0 * (atan(bulge))
        R       = c / (2*sin(alpha))
        L       = R * cos(alpha)
        steps   = ceil(2*alpha / radians(tol_deg))

        if abs(c) < Zero:
            phi = 0
            bcoords.append([x0,y0,x1,y1])
            return bcoords

        seg_sin =  dy/c
        seg_cos =  dx/c
        phi = self.Get_Angle(seg_sin,seg_cos)

        d_theta = 2*alpha / steps
        theta = alpha - d_theta

        xa = x0
        ya = y0
        for i in range(1,int(steps)):
            xp = c/2 - R*sin(theta)
            yp = R*cos(theta) - L
            xb,yb = self.Transform(xp,yp*sign,radians(phi))
            xb=xb+x0
            yb=yb+y0

            bcoords.append([xa,ya,xb,yb])
            xa = xb
            ya = yb
            theta = theta -d_theta
        bcoords.append([xa,ya,x1,y1])
        return bcoords

    def add_coords(self,line,offset,scale,rotate,color=None,layer=None):

        if color == None:
            if layer in self.layer_color:
                color = self.layer_color[layer]
            else:
                color = 0

        x0s = line[0]*scale[0]
        y0s = line[1]*scale[1]
        x1s = line[2]*scale[0]
        y1s = line[3]*scale[1]

        if abs(rotate) > Zero:
            rad = radians(rotate)
            x0r = x0s*cos(rad) - y0s*sin(rad)
            y0r = x0s*sin(rad) + y0s*cos(rad)
            x1r = x1s*cos(rad) - y1s*sin(rad)
            y1r = x1s*sin(rad) + y1s*cos(rad)
        else:
            x0r = x0s
            y0r = y0s
            x1r = x1s
            y1r = y1s

        x0 = x0r + offset[0]
        y0 = y0r + offset[1]
        x1 = x1r + offset[0]
        y1 = y1r + offset[1]

        # Check if line is blue
        Color_Blue    = (color == 5) or (color >= 140 and color <=180)
        try:
            Layer_Engrave = str.find(layer.upper(),'ENGRAVE') != -1
        except:
            Layer_Engrave = False
            try:
                for lay in layer:
                    Layer_Engrave = (str.find(lay.upper(),'ENGRAVE') != -1) or Layer_Engrave
            except:
                pass
            
        if Color_Blue or Layer_Engrave:
            self.eng_coords.append([x0,y0,x1,y1])
        else: #if (color >= 10 and color <=28) or (color >= 230 and color <=249): #red
            self.cut_coords.append([x0,y0,x1,y1])
            
        self.coords.append([x0,y0,x1,y1])

    def eval_entity(self,e,bl,tol_deg=5,offset=[0,0],scale=[1,1],rotate=0):
        try:
            color = e.data["62"]
        except:
            color = None
        try:
            layer = e.data["8"]
        except:
            layer = 0

        ############# LINE ############
        if e.type == "LINE":
            x0 = e.data["10"]
            y0 = e.data["20"]
            x1 = e.data["11"]
            y1 = e.data["21"]
            self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)
        ############# ARC #############
        elif e.type == "ARC":
            x     = e.data["10"]
            y     = e.data["20"]
            r     = e.data["40"]
            start = e.data["50"]
            end   = e.data["51"]

            if end < start:
                end=end+360.0
            delta  = end-start
            angle_steps = max(floor(delta/tol_deg),2)

            start_r = radians(start)
            end_r   = radians(end)

            step_phi = radians( delta/angle_steps )
            x0 = x + r * cos(start_r)
            y0 = y + r * sin(start_r)
            pcnt = 1
            while pcnt < angle_steps+1:
                phi = start_r + pcnt*step_phi
                x1 = x + r * cos(phi)
                y1 = y + r * sin(phi)
                self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)
                x0=x1
                y0=y1
                pcnt += 1

        ######### LWPOLYLINE ##########
        elif e.type == "LWPOLYLINE":
            flag=0
            lpcnt=-1
            for x,y in zip(e.data["10"], e.data["20"]):
                x1 = x
                y1 = y
                lpcnt=lpcnt+1
                try:
                    bulge1 = e.data["42"][lpcnt]
                except:
                    bulge1 = 0

                if flag==0:
                    x0=x1
                    y0=y1
                    bulge0=bulge1
                    flag=1
                else:
                    if bulge0 != 0:
                        bcoords = self.bulge_coords(x0,y0,x1,y1,bulge0,tol_deg)
                        for line in bcoords:
                            self.add_coords(line,offset,scale,rotate,color,layer)
                    else:
                        self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)
                    x0     = x1
                    y0     = y1
                    bulge0 = bulge1

            if (e.data["70"]!=0):
                x1 = e.data["10"][0]
                y1 = e.data["20"][0]
                if bulge0 != 0:
                    bcoords = self.bulge_coords(x0,y0,x1,y1,bulge1,tol_deg)
                    for line in bcoords:
                        self.add_coords(line,offset,scale,rotate,color,layer)
                else:
                    self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)
        ########### CIRCLE ############
        elif e.type == "CIRCLE":
            x = e.data["10"]
            y = e.data["20"]
            r = e.data["40"]

            start = 0
            end   = 360
            if end < start:
                end=end+360.0
            delta  = end-start
            angle_steps = max(floor(delta)/tol_deg,2)

            start_r = radians( start )
            end_r   = radians( end )

            step_phi = radians( delta/angle_steps)
            x0 = x + r * cos(start_r)
            y0 = y + r * sin(start_r)
            pcnt = 1
            while pcnt < angle_steps+1:
                phi = start_r + pcnt*step_phi
                x1 = x + r * cos(phi)
                y1 = y + r * sin(phi)
                self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)
                x0=x1
                y0=y1
                pcnt += 1

        ############ SPLINE ###########
        elif e.type == "SPLINE":
            self.Spline_flag=[]
            self.degree=1
            self.Knots=[]
            self.Weights=[]
            self.CPoints=[]

            self.Spline_flag = int(e.data["70"])
            self.degree      = int(e.data["71"])
            self.Knots       =     e.data["40"]
            try:
                self.Weights = e.data["41"]
            except:
                for K in self.Knots:
                    self.Weights.append(1)
                pass

            kmin = min(self.Knots)
            kmax = max(self.Knots)
            for i in range(len(self.Knots)):
                self.Knots[i] = (self.Knots[i]-kmin)/(kmax-kmin)

            for x,y in zip(e.data["10"], e.data["20"]):
                self.CPoints.append(PointClass(float(x), float(y)))

            self.MYNURBS=NURBSClass(degree=self.degree, \
                                     Knots=self.Knots,  \
                                   Weights=self.Weights,\
                                   CPoints=self.CPoints)

            mypoints=self.MYNURBS.calc_curve(n=0, tol_deg=tol_deg)
            flag = 0
            for XY in mypoints:
                x1 = XY.x
                y1 = XY.y
                if flag==0:
                    x0=x1
                    y0=y1
                    flag=1
                else:
                    self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)
                    x0=x1
                    y0=y1

        ########### ELLIPSE ###########
        elif e.type == "ELLIPSE":
            #X and Y center points
            xcp = e.data["10"]
            ycp = e.data["20"]

            #X and Y of major axis end point
            xma = e.data["11"]
            yma = e.data["21"]

            #Ratio of minor axis to major axis
            ratio = e.data["40"]

            #Start and end angles (in radians 0 and 2pi for full ellipse)
            start = degrees( e.data["41"] )
            end   = degrees( e.data["42"] )

            rotation = atan2(yma, xma)
            a = sqrt(xma**2 + yma**2)
            b = a * ratio

            ##################
            if end < start:
                end=end+360.0
            delta  = end-start


            start_r = radians( start )
            end_r   = radians( end )

            tol = radians( tol_deg )

            phi = start_r
            x1 = xcp + ( a*cos(phi) * cos(rotation) - b*sin(phi) * sin(rotation) );
            y1 = ycp + ( a*cos(phi) * sin(rotation) + b*sin(phi) * cos(rotation) );
            step=tol
            while phi < end_r:
                if (phi+step > end_r):
                    step = end_r-phi

                x2 = xcp + ( a*cos(phi+step) * cos(rotation) - b*sin(phi+step) * sin(rotation) );
                y2 = ycp + ( a*cos(phi+step) * sin(rotation) + b*sin(phi+step) * cos(rotation) );

                x_test = xcp + ( a*cos(phi+step/2) * cos(rotation) - b*sin(phi+step/2) * sin(rotation) );
                y_test = ycp + ( a*cos(phi+step/2) * sin(rotation) + b*sin(phi+step/2) * cos(rotation) );

                dx1 = (x_test - x1)
                dy1 = (y_test - y1)
                L1 = sqrt(dx1*dx1 + dy1*dy1)

                dx2 = (x2 - x_test)
                dy2 = (y2 - y_test)
                L2 = sqrt(dx2*dx2 + dy2*dy2)

                angle=acos( dx1/L1 * dx2/L2 + dy1/L1 * dy2/L2)

                if angle > tol:
                    step = step/2
                else:
                    phi+=step
                    self.add_coords([x1,y1,x2,y2],offset,scale,rotate,color,layer)
                    step = step*2
                    x1=x2
                    y1=y2
        ########### ELLIPSE ###########
        elif e.type == "OLD_ELLIPSE":
            #X and Y center points
            xcp = e.data["10"]
            ycp = e.data["20"]
            #X and Y of major axis end point
            xma = e.data["11"]
            yma = e.data["21"]
            #Ratio of minor axis to major axis
            ratio = e.data["40"]
            #Start and end angles (in radians 0 and 2pi for full ellipse)
            start = degrees( e.data["41"] )
            end   = degrees( e.data["42"] )

            rotation = atan2(yma, xma)
            a = sqrt(xma**2 + yma**2)
            b = a * ratio

            ##################
            if end < start:
                end=end+360.0
            delta  = end-start
            angle_steps = max(floor(delta/tol_deg),2)

            start_r = radians( start )
            end_r   = radians( end )

            step_phi = radians( delta/angle_steps )
            x0 = xcp + ( a*cos(start_r) * cos(rotation) - b*sin(start_r) * sin(rotation) );
            y0 = ycp + ( a*cos(start_r) * sin(rotation) + b*sin(start_r) * cos(rotation) );
            pcnt = 1
            while pcnt < angle_steps+1:
                phi = start_r + pcnt*step_phi
                x1 = xcp + ( a*cos(phi) * cos(rotation) - b*sin(phi) * sin(rotation) );
                y1 = ycp + ( a*cos(phi) * sin(rotation) + b*sin(phi) * cos(rotation) );
                self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)
                x0=x1
                y0=y1
                pcnt += 1

        ########### LEADER ###########
        elif e.type == "LEADER":
            flag=0
            for x,y in zip(e.data["10"], e.data["20"]):
                x1 = x
                y1 = y
                if flag==0:
                    x0=x1
                    y0=y1
                    flag=1
                else:
                    self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)
                    x0=x1
                    y0=y1

        ########### POLYLINE ###########
        elif e.type == "POLYLINE":
            self.POLY_CLOSED =  0
            self.POLY_FLAG   = -1
            try:
                TYPE=e.data["70"]
                if (TYPE==0 or TYPE==8):
                    pass
                elif (TYPE==1):
                    self.POLY_CLOSED=1
                else:
                    self.dxf_message("DXF Import Ignored: - %s - Entity" %(e.type))
                    self.POLY_FLAG = 0
            except:
                pass

        ########### SEQEND ###########
        elif e.type == "SEQEND":
            if (self.POLY_FLAG != 0):
                self.POLY_FLAG=0
                if (self.POLY_CLOSED==1):
                    self.POLY_CLOSED==0
                    x0 = self.PX
                    y0 = self.PY
                    x1 = self.PX0
                    y1 = self.PY0

                    if self.bulge != 0:
                        bcoords = self.bulge_coords(x0,y0,x1,y1,self.bulge,tol_deg)
                        for line in bcoords:
                            self.add_coords(line,offset,scale,rotate,color,layer)
                    else:
                        self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)

            else:
                self.dxf_message("DXF Import Ignored: - %s - Entity" %(e.type))

        ########### VERTEX ###########
        elif e.type == "VERTEX":

            if (self.POLY_FLAG==-1):
                self.PX  = e.data["10"]
                self.PY  = e.data["20"]
                self.PX0 = self.PX
                self.PY0 = self.PY
                try:
                    self.bulge = e.data["42"]
                except:
                    self.bulge = 0

                self.POLY_FLAG = 1
            elif (self.POLY_FLAG == 1):
                x0 = self.PX
                y0 = self.PY
                x1 = e.data["10"]
                y1 = e.data["20"]
                self.PX=x1
                self.PY=y1

                if self.bulge != 0:
                    bcoords = self.bulge_coords(x0,y0,x1,y1,self.bulge,tol_deg)
                    for line in bcoords:
                        self.add_coords(line,offset,scale,rotate,color,layer)
                else:
                    self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)

                try:
                    self.bulge = e.data["42"]
                except:
                    self.bulge = 0
            else:
                self.dxf_message("DXF Import Ignored: - %s - Entity" %(e.type))
                pass
        ########### END VERTEX ###########
        ########### INSERT ###########
        elif e.type == "INSERT":
            key = e.data["2"]
            xoff = e.data["10"]+offset[0]
            yoff = e.data["20"]+offset[1]

            try:
                xscale = e.data["41"]
            except:
                xscale = 1
            try:
                yscale = e.data["42"]
            except:
                yscale = 1
            try:
                rotate = e.data["50"]
            except:
                rotate = 0

            try:
                x_block_ref = bl.blocks[key].data.get("10")
                y_block_ref = bl.blocks[key].data.get("20")
            except:
                x_block_ref = 0
                y_block_ref = 0

            xoff = xoff - x_block_ref
            yoff = yoff - y_block_ref
            
            for e in bl.blocks[key].entities:
                self.eval_entity(e,bl,tol_deg,offset=[xoff,yoff],scale=[xscale,yscale],rotate=rotate)

        ########### END INSERT ###########

        elif e.type == "SOLID":
            x0 = e.data["10"]
            y0 = e.data["20"]
            x1 = e.data["11"]
            y1 = e.data["21"]
            x2 = e.data["12"]
            y2 = e.data["22"]
            try:
                x3 = e.data["13"]
                y3 = e.data["23"]
            except:
                x3 = x2
                y3 = y2
            self.add_coords([x0,y0,x1,y1],offset,scale,rotate,color,layer)
            self.add_coords([x1,y1,x3,y3],offset,scale,rotate,color,layer)
            self.add_coords([x3,y3,x2,y2],offset,scale,rotate,color,layer)
            self.add_coords([x2,y2,x0,y0],offset,scale,rotate,color,layer)

        elif e.type == "HATCH":
            #quietly ignore HATCH
            pass
        else:
            self.dxf_message("DXF Import Ignored: %s Entity" %(e.type))
            pass



    def GET_DXF_DATA(self,fd, tol_deg=5):
        data = []
        try:
            self.read_dxf_data(fd, data)
        except:
            self.dxf_message("\nUnable to read input DXF data!")
            return 1
        data = iter(data)
        g_code, value = None, None
        sections = dict()

        he = Header()
        bl = Blocks()
        la = Layers()
        while value != "EOF":
            g_code, value = next(data)
            if value == "SECTION":
                g_code, value = next(data)
                sections[value] = []

                while value != "ENDSEC":


                    if value == "HEADER":
                        while True:
                            g_code, value = next(data)
                            if value == "ENDSEC":
                                break
                            elif g_code == 9:
                                he.new_var(value)
                            else:
                                he.new_val((g_code, value))

                    elif value == "BLOCKS":
                        while True:
                            g_code, value = next(data)
                            if value == "ENDSEC":
                                break
                            elif value == "ENDBLK":
                                continue
                            elif value == "BLOCK":
                                bl.new_block()
                            elif g_code == 0 and value != "BLOCK":
                                bl.new_entity(value)
                            else:
                                bl.update((g_code, value))

                    elif value == "ENTITIES":
                        TYPE=""
                        en = Entities()
                        while True:
                            g_code, value = next(data)

                            ###################################
                            if g_code==0:
                                TYPE = value
                            if TYPE == "LWPOLYLINE" and g_code==10 and g_code_last==20:
                                # Add missing code 42
                                en.update((42, 0.0))
                            g_code_last = g_code
                            ###################################

                            if value == "ENDSEC":
                                break
                            elif g_code == 0 and value != "ENDSEC":
                                en.new_entity(value)
                            else:
                                en.update((g_code, value))
                                
                    #------------------------------------------------------------------
                    elif value == "TABLE":
                        while True:
                            g_code, value = next(data)
                            if value == "AcDbLayerTableRecord":
                                la.new_layer()
                                while True:
                                    g_code, value = next(data)
                                    if g_code==0:
                                        break
                                    la.update((g_code, value))
                            if value == "ENDTAB":
                                break
                    #------------------------------------------------------------------
                                
                    try:
                        g_code, value = next(data)
                    except:
                        break

        #Process Units
        try:
            unit_val = he.variables.get("$INSUNITS").get("70")
            self.units = self.unit_vals[int(unit_val)]
        except:
            self.units = self.unit_vals[0]

        #Process Layers
        for l in la.layers:
            try:
                color = l.data["62"]
            except:
                color = None
            try:
                name = l.data["2"]
            except:
                name = None
            self.layer_color[name]=color

        #Process Entities
        for e in en.entities:
            self.eval_entity(e,bl,tol_deg)


    def DXF_COORDS_GET(self,new_origin=True):
        if (new_origin==True):
            ymin=99999
            xmin=99999
            for line in self.coords:
                XY=line
                if XY[0] < xmin:
                        xmin = XY[0]
                if XY[1] < ymin:
                        ymin = XY[1]
                if XY[2] < xmin:
                        xmin = XY[2]
                if XY[3] < ymin:
                        ymin = XY[3]
        else:
            xmin=0
            ymin=0

        coords_out=[]
        for line in self.coords:
            XY=line
            coords_out.append([XY[0]-xmin, XY[1]-ymin, XY[2]-xmin, XY[3]-ymin])
        return coords_out


    def DXF_COORDS_GET_TYPE(self,engrave=True,new_origin=True):
        if engrave==True:
            coords = self.eng_coords
        else:
            coords = self.cut_coords
        
        if (new_origin==True):
            ymin=99999
            xmin=99999
            for line in coords:
                XY=line
                if XY[0] < xmin:
                        xmin = XY[0]
                if XY[1] < ymin:
                        ymin = XY[1]
                if XY[2] < xmin:
                        xmin = XY[2]
                if XY[3] < ymin:
                        ymin = XY[3]
        else:
            xmin=0
            ymin=0

        coords_out=[]
        for line in coords:
            XY=line
            coords_out.append([XY[0]-xmin, XY[1]-ymin, XY[2]-xmin, XY[3]-ymin])
        return coords_out



    ##################################################
    ###  Begin Dxf_Write G-Code Writing Function   ###
    ##################################################
    def WriteDXF(self,close_loops=False):

        if close_loops:
            self.V_Carve_It(clean_flag=0,DXF_FLAG = close_loops)
        
        dxf_code = []
        # Create a header section just in case the reading software needs it
        dxf_code.append("999")
        dxf_code.append("DXF created by dxf library <by Scorch, www.scorchworks.com>")
        
        dxf_code.append("0")
        dxf_code.append("SECTION")
        dxf_code.append("2")
        dxf_code.append("HEADER")
        dxf_code.append("0")
        dxf_code.append("ENDSEC")
        #         
        #Tables Section
        #These can be used to specify predefined constants, line styles, text styles, view 
        #tables, user coordinate systems, etc. We will only use tables to define some layers 
        #for use later on. Note: not all programs that support DXF import will support 
        #layers and those that do usually insist on the layers being defined before use
        #
        # The following will initialise layers 1 and 2 for use with moves and rapid moves.
        dxf_code.append("0")
        dxf_code.append("SECTION")
        dxf_code.append("2")
        dxf_code.append("TABLES")
        dxf_code.append("0")
        dxf_code.append("TABLE")
        dxf_code.append("2")
        dxf_code.append("LTYPE")
        dxf_code.append("70")
        dxf_code.append("1")
        dxf_code.append("0")
        dxf_code.append("LTYPE")
        dxf_code.append("2")
        dxf_code.append("CONTINUOUS")
        dxf_code.append("70")
        dxf_code.append("64")
        dxf_code.append("3")
        dxf_code.append("Solid line")
        dxf_code.append("72")
        dxf_code.append("65")
        dxf_code.append("73")
        dxf_code.append("0")
        dxf_code.append("40")
        dxf_code.append("0.000000")
        dxf_code.append("0")
        dxf_code.append("ENDTAB")
        dxf_code.append("0")
        dxf_code.append("TABLE")
        dxf_code.append("2")
        dxf_code.append("LAYER")
        dxf_code.append("70")
        dxf_code.append("6")
        dxf_code.append("0")
        dxf_code.append("LAYER")
        dxf_code.append("2")
        dxf_code.append("1")
        dxf_code.append("70")
        dxf_code.append("64")
        dxf_code.append("62")
        dxf_code.append("7")
        dxf_code.append("6")
        dxf_code.append("CONTINUOUS")
        dxf_code.append("0")
        dxf_code.append("LAYER")
        dxf_code.append("2")
        dxf_code.append("2")
        dxf_code.append("70")
        dxf_code.append("64")
        dxf_code.append("62")
        dxf_code.append("7")
        dxf_code.append("6")
        dxf_code.append("CONTINUOUS")
        dxf_code.append("0")
        dxf_code.append("ENDTAB")
        dxf_code.append("0")
        dxf_code.append("TABLE")
        dxf_code.append("2")
        dxf_code.append("STYLE")
        dxf_code.append("70")
        dxf_code.append("0")
        dxf_code.append("0")
        dxf_code.append("ENDTAB")
        dxf_code.append("0")
        dxf_code.append("ENDSEC")
        
        #This block section is not necessary but apperantly it's good form to include one anyway.
        #The following is an empty block section.
        dxf_code.append("0")
        dxf_code.append("SECTION")
        dxf_code.append("2")
        dxf_code.append("BLOCKS")
        dxf_code.append("0")
        dxf_code.append("ENDSEC")

        # Start entities section
        dxf_code.append("0")
        dxf_code.append("SECTION")
        dxf_code.append("2")
        dxf_code.append("ENTITIES")
        dxf_code.append("  0")

        #################################
        ## GCODE WRITING for Dxf_Write ##
        #################################
        #for line in side:
        for line in self.coords:
            XY = line
            
            #if line[0] == 1 or (line[0] == 0 and Rapids):
            dxf_code.append("LINE")
            dxf_code.append("  5")
            dxf_code.append("30")
            dxf_code.append("100")
            dxf_code.append("AcDbEntity")
            dxf_code.append("  8") #layer Code #dxf_code.append("0")

            ##########################
            #if line[0] == 1:
            #    dxf_code.append("1")
            #else:
            #    dxf_code.append("2")    
            #dxf_code.append(" 62") #color code
            #if line[0] == 1:
            #    dxf_code.append("10")
            #else:
            #    dxf_code.append("150")
            dxf_code.append("1")
            dxf_code.append(" 62") #color code
            dxf_code.append("150")
            ###########################
            
            dxf_code.append("100")
            dxf_code.append("AcDbLine")
            dxf_code.append(" 10")
            dxf_code.append("%.4f" %(line[0])) #x1 coord
            dxf_code.append(" 20")
            dxf_code.append("%.4f" %(line[1])) #y1 coord
            dxf_code.append(" 30")
            dxf_code.append("%.4f" %(0))       #z1 coord
            dxf_code.append(" 11")
            dxf_code.append("%.4f" %(line[2])) #x2 coord
            dxf_code.append(" 21")
            dxf_code.append("%.4f" %(line[3])) #y2 coord
            dxf_code.append(" 31")
            dxf_code.append("%.4f" %(0))       #z2 coord
            dxf_code.append("  0")

        dxf_code.append("ENDSEC")
        dxf_code.append("0")
        dxf_code.append("EOF")
        ######################################
        ## END G-CODE WRITING for Dxf_Write ##
        ######################################
        return dxf_code

