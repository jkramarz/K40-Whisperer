#!/usr/bin/python
"""
    K40 Whisperer

    Copyright (C) <2017-2019>  <Scorch>
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
version = '0.29'
title_text = "K40 Whisperer V"+version

import sys
from math import *
from egv import egv
from nano_library import K40_CLASS
from dxf import DXF_CLASS
from svg_reader import SVG_READER
from svg_reader import SVG_TEXT_EXCEPTION
from g_code_library import G_Code_Rip
from interpolate import interpolate
from ecoords import ECoord

import inkex
import simplestyle
import simpletransform
import cubicsuperpath
import cspsubdiv
import traceback
import struct

DEBUG = False

VERSION = sys.version_info[0]
LOAD_MSG = ""

if VERSION == 3:
    from tkinter import *
    from tkinter.filedialog import *
    import tkinter.messagebox
    MAXINT = sys.maxsize
    
else:
    from Tkinter import *
    from tkFileDialog import *
    import tkMessageBox
    MAXINT = sys.maxint

if VERSION < 3 and sys.version_info[1] < 6:
    def next(item):
        #return item.next()
        return item.__next__()
    
try:
    import psyco
    psyco.full()
    LOAD_MSG = LOAD_MSG+"\nPsyco Loaded\n"
except:
    pass

import math
from time import time
import os
import re
import binascii
import getopt
import operator
import webbrowser
from PIL import Image
from PIL import ImageOps
try:
    Image.warnings.simplefilter('ignore', Image.DecompressionBombWarning)
except:
    pass
try:
    from PIL import ImageTk
    from PIL import _imaging
except:
    pass #Don't worry everything will still work

QUIET = False


    
    
################################################################################
class Application(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.w = 780
        self.h = 490
        frame = Frame(master, width= self.w, height=self.h)
        self.master = master
        self.x = -1
        self.y = -1
        self.createWidgets()

    def resetPath(self):
        self.RengData  = ECoord()
        self.VengData  = ECoord()
        self.VcutData  = ECoord()
        self.GcodeData = ECoord()
        self.SCALE = 1
        self.Design_bounds = (0,0,0,0)
        self.UI_image = None
        #if self.HomeUR.get():
        self.move_head_window_temporary([0.0,0.0])
        #else:
        #    self.move_head_window_temporary([0.0,0.0])
            
        self.pos_offset=[0.0,0.0]
        
    def createWidgets(self):
        self.initComplete = 0
        self.stop=[]
        self.stop.append(False)
        
        self.k40 = None
        
        self.master.bind("<Configure>", self.Master_Configure)
        self.master.bind('<Enter>', self.bindConfigure)
        self.master.bind('<F1>', self.KEY_F1)
        self.master.bind('<F2>', self.KEY_F2)
        self.master.bind('<F3>', self.KEY_F3)
        self.master.bind('<F4>', self.KEY_F4)
        self.master.bind('<F5>', self.KEY_F5)
        self.master.bind('<Home>', self.Home)
        

        self.master.bind('<Control-Left>' , self.Move_Left)
        self.master.bind('<Control-Right>', self.Move_Right)
        self.master.bind('<Control-Up>'   , self.Move_Up)
        self.master.bind('<Control-Down>' , self.Move_Down)

        self.master.bind('<Alt-Control-Left>' , self.Move_Arb_Left)
        self.master.bind('<Alt-Control-Right>', self.Move_Arb_Right)
        self.master.bind('<Alt-Control-Up>'   , self.Move_Arb_Up)
        self.master.bind('<Alt-Control-Down>' , self.Move_Arb_Down)

        self.master.bind('<Control-i>' , self.Initialize_Laser)
        self.master.bind('<Control-o>' , self.menu_File_Open_Design)
        self.master.bind('<Control-l>' , self.menu_Reload_Design)
        self.master.bind('<Control-h>' , self.Home)
        self.master.bind('<Control-u>' , self.Unlock)
        self.master.bind('<Escape>'    , self.Stop)

        self.include_Reng = BooleanVar()
        self.include_Rpth = BooleanVar()
        self.include_Veng = BooleanVar()
        self.include_Vcut = BooleanVar()
        self.include_Gcde = BooleanVar()
        self.include_Time = BooleanVar()

        self.advanced = BooleanVar()
        
        self.halftone     = BooleanVar()
        self.mirror       = BooleanVar()
        self.rotate       = BooleanVar()
        self.negate       = BooleanVar()
        self.inputCSYS    = BooleanVar()
        self.HomeUR       = BooleanVar()
        self.engraveUP    = BooleanVar()
        self.init_home    = BooleanVar()
        self.pre_pr_crc   = BooleanVar()
        self.inside_first = BooleanVar()

        self.ht_size    = StringVar()
        self.Reng_feed  = StringVar()
        self.Veng_feed  = StringVar()
        self.Vcut_feed  = StringVar()

        self.Reng_passes = StringVar()
        self.Veng_passes = StringVar()
        self.Vcut_passes = StringVar()
        self.Gcde_passes = StringVar()
        
        
        self.board_name = StringVar()
        self.units      = StringVar()
        self.jog_step   = StringVar()
        self.rast_step  = StringVar()
        self.funits     = StringVar()
        

        self.bezier_M1     = StringVar()
        self.bezier_M2     = StringVar()
        self.bezier_weight = StringVar()

        self.LaserXsize = StringVar()
        self.LaserYsize = StringVar()

        self.LaserXscale = StringVar()
        self.LaserYscale = StringVar()

        self.gotoX = StringVar()
        self.gotoY = StringVar()

        self.n_egv_passes = StringVar()

        self.inkscape_path = StringVar()
        self.t_timeout  = StringVar()
        self.n_timeouts  = StringVar()
        
        self.Reng_time = StringVar()
        self.Veng_time = StringVar()
        self.Vcut_time = StringVar()
        self.Gcde_time = StringVar()

        self.comb_engrave = BooleanVar()
        self.comb_vector  = BooleanVar()
        self.zoom2image   = BooleanVar()

        
        ###########################################################################
        #                         INITILIZE VARIABLES                             #
        #    if you want to change a default setting this is the place to do it   #
        ###########################################################################
        self.include_Reng.set(1)
        self.include_Rpth.set(0)
        self.include_Veng.set(1)
        self.include_Vcut.set(1)
        self.include_Gcde.set(1)
        self.include_Time.set(0)
        self.advanced.set(0)
        
        self.halftone.set(1)
        self.mirror.set(0)
        self.rotate.set(0)
        self.negate.set(0)
        self.inputCSYS.set(0)
        self.HomeUR.set(0)
        self.engraveUP.set(0)
        self.init_home.set(1)
        self.pre_pr_crc.set(1)
        self.inside_first.set(1)
        
        self.ht_size.set(500)

        self.Reng_feed.set("100")
        self.Veng_feed.set("20")
        self.Vcut_feed.set("10")
        self.Reng_passes.set("1")
        self.Veng_passes.set("1")
        self.Vcut_passes.set("1")
        self.Gcde_passes.set("1")
        
        
        self.jog_step.set("10.0")
        self.rast_step.set("0.002")
        
        self.bezier_weight.set("3.5")
        self.bezier_M1.set("2.5")
        self.bezier_M2.set("0.50")

        self.bezier_weight_default = float(self.bezier_weight.get())
        self.bezier_M1_default     = float(self.bezier_M1.get())
        self.bezier_M2_default     = float(self.bezier_M2.get())
        
                                        
        self.board_name.set("LASER-M2") # Options are
                                        #    "LASER-M2",
                                        #    "LASER-M1",
                                        #    "LASER-M",
                                        #    "LASER-B2",
                                        #    "LASER-B1",
                                        #    "LASER-B",
                                        #    "LASER-A"


        self.units.set("mm")            # Options are "in" and "mm"
        self.t_timeout.set("200")   
        self.n_timeouts.set("30")

        self.HOME_DIR    = os.path.expanduser("~")
        
        if not os.path.isdir(self.HOME_DIR):
            self.HOME_DIR = ""

        self.DESIGN_FILE = (self.HOME_DIR+"/None")
        self.EGV_FILE    = None
        
        self.aspect_ratio =  0
        self.segID   = []
        
        self.LaserXsize.set("325")
        self.LaserYsize.set("220")
        
        self.LaserXscale.set("1.000")
        self.LaserYscale.set("1.000")

        self.gotoX.set("0.0")
        self.gotoY.set("0.0")

        self.n_egv_passes.set("1")

        self.comb_engrave.set(0)
        self.comb_vector.set(0)
        self.zoom2image.set(0)

        
        self.laserX    = 0.0
        self.laserY    = 0.0
        self.PlotScale = 1.0

        # PAN and ZOOM STUFF
        self.panx = 0
        self.panx = 0
        self.lastx = 0
        self.lasty = 0
        self.move_start_x = 0
        self.move_start_y = 0

        
        self.RengData  = ECoord()
        self.VengData  = ECoord()
        self.VcutData  = ECoord()
        self.GcodeData = ECoord()
        self.SCALE = 1
        self.Design_bounds = (0,0,0,0)
        self.UI_image = None
        self.pos_offset=[0.0,0.0]

        
        # Derived variables
        if self.units.get() == 'in':
            self.funits.set('in/min')
            self.units_scale = 1.0
        else:
            self.units.set('mm')
            self.funits.set('mm/s')
            self.units_scale = 25.4
        
        self.statusMessage = StringVar()
        self.statusMessage.set("Welcome to K40 Whisperer")
        
        
        self.Reng_time.set("0")
        self.Veng_time.set("0")
        self.Vcut_time.set("0")
        self.Gcde_time.set("0")
        
        ##########################################################################
        ###                     END INITILIZING VARIABLES                      ###
        ##########################################################################

        # make a Status Bar
        self.statusbar = Label(self.master, textvariable=self.statusMessage, \
                                   bd=1, relief=SUNKEN , height=1)
        self.statusbar.pack(anchor=SW, fill=X, side=BOTTOM)
        

        # Canvas
        lbframe = Frame( self.master )
        self.PreviewCanvas_frame = lbframe
        self.PreviewCanvas = Canvas(lbframe, width=self.w-(220+20), height=self.h-200, background="grey75")
        self.PreviewCanvas.pack(side=LEFT, fill=BOTH, expand=1)
        self.PreviewCanvas_frame.place(x=230, y=10)

        self.PreviewCanvas.tag_bind('LaserTag',"<1>"              , self.mousePanStart)
        self.PreviewCanvas.tag_bind('LaserTag',"<B1-Motion>"      , self.mousePan)
        self.PreviewCanvas.tag_bind('LaserTag',"<ButtonRelease-1>", self.mousePanStop)

        self.PreviewCanvas.tag_bind('LaserDot',"<3>"              , self.right_mousePanStart)
        self.PreviewCanvas.tag_bind('LaserDot',"<B3-Motion>"      , self.right_mousePan)
        self.PreviewCanvas.tag_bind('LaserDot',"<ButtonRelease-3>", self.right_mousePanStop)

        # Left Column #
        self.separator1 = Frame(self.master, height=2, bd=1, relief=SUNKEN)
        self.separator2 = Frame(self.master, height=2, bd=1, relief=SUNKEN)
        self.separator3 = Frame(self.master, height=2, bd=1, relief=SUNKEN)
        self.separator4 = Frame(self.master, height=2, bd=1, relief=SUNKEN)
        
        self.Label_Reng_feed_u = Label(self.master,textvariable=self.funits, anchor=W)
        self.Entry_Reng_feed   = Entry(self.master,width="15")
        self.Entry_Reng_feed.configure(textvariable=self.Reng_feed,justify='center',fg="black")
        self.Reng_feed.trace_variable("w", self.Entry_Reng_feed_Callback)
        self.NormalColor =  self.Entry_Reng_feed.cget('bg')

        self.Label_Veng_feed_u = Label(self.master,textvariable=self.funits, anchor=W)
        self.Entry_Veng_feed   = Entry(self.master,width="15")
        self.Entry_Veng_feed.configure(textvariable=self.Veng_feed,justify='center',fg="blue")
        self.Veng_feed.trace_variable("w", self.Entry_Veng_feed_Callback)
        self.NormalColor =  self.Entry_Veng_feed.cget('bg')

        self.Label_Vcut_feed_u = Label(self.master,textvariable=self.funits, anchor=W)
        self.Entry_Vcut_feed   = Entry(self.master,width="15")
        self.Entry_Vcut_feed.configure(textvariable=self.Vcut_feed,justify='center',fg="red")
        self.Vcut_feed.trace_variable("w", self.Entry_Vcut_feed_Callback)
        self.NormalColor =  self.Entry_Vcut_feed.cget('bg')

        # Buttons
        self.Reng_Button  = Button(self.master,text="Raster Engrave", command=self.Raster_Eng)
        self.Veng_Button  = Button(self.master,text="Vector Engrave", command=self.Vector_Eng)
        self.Vcut_Button  = Button(self.master,text="Vector Cut"    , command=self.Vector_Cut)
        self.Grun_Button  = Button(self.master,text="Run G-Code"    , command=self.Gcode_Cut)


        self.Reng_Veng_Button      = Button(self.master,text="Raster and\nVector Engrave", command=self.Raster_Vector_Eng)
        self.Veng_Vcut_Button      = Button(self.master,text="Vector Engrave\nand Cut", command=self.Vector_Eng_Cut)
        self.Reng_Veng_Vcut_Button = Button(self.master,text="Raster Engrave\nVector Engrave\nand\nVector Cut", command=self.Raster_Vector_Cut)
        
        self.Label_Position_Control = Label(self.master,text="Position Controls:", anchor=W)
        
        self.Initialize_Button = Button(self.master,text="Initialize Laser Cutter", command=self.Initialize_Laser)

        self.Open_Button       = Button(self.master,text="Open\nDesign File",   command=self.menu_File_Open_Design)
        self.Reload_Button     = Button(self.master,text="Reload\nDesign File", command=self.menu_Reload_Design)
        
        self.Home_Button       = Button(self.master,text="Home",             command=self.Home)
        self.UnLock_Button     = Button(self.master,text="Unlock Rail",     command=self.Unlock)
        self.Stop_Button       = Button(self.master,text="Stop",             command=self.Stop)

        try:
            self.left_image  = self.Imaging_Free(Image.open("left.png"),bg=None)
            self.right_image = self.Imaging_Free(Image.open("right.png"),bg=None)
            self.up_image    = self.Imaging_Free(Image.open("up.png"),bg=None)
            self.down_image  = self.Imaging_Free(Image.open("down.png"),bg=None)
            
            self.Right_Button   = Button(self.master,image=self.right_image, command=self.Move_Right)
            self.Left_Button    = Button(self.master,image=self.left_image,  command=self.Move_Left)
            self.Up_Button      = Button(self.master,image=self.up_image,    command=self.Move_Up)
            self.Down_Button    = Button(self.master,image=self.down_image,  command=self.Move_Down)

            self.UL_image  = self.Imaging_Free(Image.open("UL.png"),bg=None)
            self.UR_image  = self.Imaging_Free(Image.open("UR.png"),bg=None)
            self.LR_image  = self.Imaging_Free(Image.open("LR.png"),bg=None)
            self.LL_image  = self.Imaging_Free(Image.open("LL.png"),bg=None)
            self.CC_image  = self.Imaging_Free(Image.open("CC.png"),bg=None)
            
            self.UL_Button = Button(self.master,image=self.UL_image, command=self.Move_UL)
            self.UR_Button = Button(self.master,image=self.UR_image, command=self.Move_UR)
            self.LR_Button = Button(self.master,image=self.LR_image, command=self.Move_LR)
            self.LL_Button = Button(self.master,image=self.LL_image, command=self.Move_LL)
            self.CC_Button = Button(self.master,image=self.CC_image, command=self.Move_CC)
            
        except:
            self.Right_Button   = Button(self.master,text=">",          command=self.Move_Right)
            self.Left_Button    = Button(self.master,text="<",          command=self.Move_Left)
            self.Up_Button      = Button(self.master,text="^",          command=self.Move_Up)
            self.Down_Button    = Button(self.master,text="v",          command=self.Move_Down)

            self.UL_Button = Button(self.master,text=" ", command=self.Move_UL)
            self.UR_Button = Button(self.master,text=" ", command=self.Move_UR)
            self.LR_Button = Button(self.master,text=" ", command=self.Move_LR)
            self.LL_Button = Button(self.master,text=" ", command=self.Move_LL)
            self.CC_Button = Button(self.master,text=" ", command=self.Move_CC)

        self.Label_Step   = Label(self.master,text="Jog Step", anchor=CENTER )
        self.Label_Step_u = Label(self.master,textvariable=self.units, anchor=W)
        self.Entry_Step   = Entry(self.master,width="15")
        self.Entry_Step.configure(textvariable=self.jog_step, justify='center')
        self.jog_step.trace_variable("w", self.Entry_Step_Callback)

        ###########################################################################
        self.GoTo_Button    = Button(self.master,text="Move To", command=self.GoTo)
        
        self.Entry_GoToX   = Entry(self.master,width="15",justify='center')
        self.Entry_GoToX.configure(textvariable=self.gotoX)
        self.gotoX.trace_variable("w", self.Entry_GoToX_Callback)
        self.Entry_GoToY   = Entry(self.master,width="15",justify='center')
        self.Entry_GoToY.configure(textvariable=self.gotoY)
        self.gotoY.trace_variable("w", self.Entry_GoToY_Callback)
        
        self.Label_GoToX   = Label(self.master,text="X", anchor=CENTER )
        self.Label_GoToY   = Label(self.master,text="Y", anchor=CENTER )
        ###########################################################################
        # End Left Column #

        # Advanced Column     #
        self.separator_vert = Frame(self.master, height=2, bd=1, relief=SUNKEN)
        self.Label_Advanced_column = Label(self.master,text="Advanced Settings",anchor=CENTER)
        self.separator_adv = Frame(self.master, height=2, bd=1, relief=SUNKEN)       

        self.Label_Halftone_adv = Label(self.master,text="Halftone (Dither)")
        self.Checkbutton_Halftone_adv = Checkbutton(self.master,text=" ", anchor=W)
        self.Checkbutton_Halftone_adv.configure(variable=self.halftone)
        self.halftone.trace_variable("w", self.menu_View_Refresh_Callback)

        self.Label_Negate_adv = Label(self.master,text="Invert Raster Color")
        self.Checkbutton_Negate_adv = Checkbutton(self.master,text=" ", anchor=W)
        self.Checkbutton_Negate_adv.configure(variable=self.negate)
        self.negate.trace_variable("w", self.menu_View_Mirror_Refresh_Callback)

        self.Label_Mirror_adv = Label(self.master,text="Mirror Design")
        self.Checkbutton_Mirror_adv = Checkbutton(self.master,text=" ", anchor=W)
        self.Checkbutton_Mirror_adv.configure(variable=self.mirror)
        self.mirror.trace_variable("w", self.menu_View_Mirror_Refresh_Callback)

        self.Label_Rotate_adv = Label(self.master,text="Rotate Design")
        self.Checkbutton_Rotate_adv = Checkbutton(self.master,text=" ", anchor=W)
        self.Checkbutton_Rotate_adv.configure(variable=self.rotate)
        self.rotate.trace_variable("w", self.menu_View_Mirror_Refresh_Callback)
    
        self.Label_inputCSYS_adv = Label(self.master,text="Use Input CSYS")
        self.Checkbutton_inputCSYS_adv = Checkbutton(self.master,text=" ", anchor=W)
        self.Checkbutton_inputCSYS_adv.configure(variable=self.inputCSYS)
        self.inputCSYS.trace_variable("w", self.menu_View_inputCSYS_Refresh_Callback)

        self.Label_Inside_First_adv = Label(self.master,text="Cut Inside First")
        self.Checkbutton_Inside_First_adv = Checkbutton(self.master,text=" ", anchor=W)
        self.Checkbutton_Inside_First_adv.configure(variable=self.inside_first)
        self.inside_first.trace_variable("w", self.menu_Inside_First_Callback)

        #####
        self.separator_comb = Frame(self.master, height=2, bd=1, relief=SUNKEN)  

        self.Label_Comb_Engrave_adv = Label(self.master,text="Group Engrave Tasks")
        self.Checkbutton_Comb_Engrave_adv = Checkbutton(self.master,text=" ", anchor=W)
        self.Checkbutton_Comb_Engrave_adv.configure(variable=self.comb_engrave)
        self.comb_engrave.trace_variable("w", self.menu_View_Refresh_Callback)

        self.Label_Comb_Vector_adv = Label(self.master,text="Group Vector Tasks")
        self.Checkbutton_Comb_Vector_adv = Checkbutton(self.master,text=" ", anchor=W)
        self.Checkbutton_Comb_Vector_adv.configure(variable=self.comb_vector)
        self.comb_vector.trace_variable("w", self.menu_View_Refresh_Callback) 
        #####
        
        self.Label_Reng_passes = Label(self.master,text="Raster Eng. Passes")
        self.Entry_Reng_passes   = Entry(self.master,width="15")
        self.Entry_Reng_passes.configure(textvariable=self.Reng_passes,justify='center',fg="black")
        self.Reng_passes.trace_variable("w", self.Entry_Reng_passes_Callback)
        self.NormalColor =  self.Entry_Reng_passes.cget('bg')

        self.Label_Veng_passes = Label(self.master,text="Vector Eng. Passes")
        self.Entry_Veng_passes   = Entry(self.master,width="15")
        self.Entry_Veng_passes.configure(textvariable=self.Veng_passes,justify='center',fg="blue")
        self.Veng_passes.trace_variable("w", self.Entry_Veng_passes_Callback)
        self.NormalColor =  self.Entry_Veng_passes.cget('bg')

        self.Label_Vcut_passes = Label(self.master,text="Vector Cut Passes")
        self.Entry_Vcut_passes   = Entry(self.master,width="15")
        self.Entry_Vcut_passes.configure(textvariable=self.Vcut_passes,justify='center',fg="red")
        self.Vcut_passes.trace_variable("w", self.Entry_Vcut_passes_Callback)
        self.NormalColor =  self.Entry_Vcut_passes.cget('bg')

        self.Label_Gcde_passes = Label(self.master,text="G-Code Passes")
        self.Entry_Gcde_passes   = Entry(self.master,width="15")
        self.Entry_Gcde_passes.configure(textvariable=self.Gcde_passes,justify='center',fg="black")
        self.Gcde_passes.trace_variable("w", self.Entry_Gcde_passes_Callback)
        self.NormalColor =  self.Entry_Gcde_passes.cget('bg')

        
        self.Hide_Adv_Button = Button(self.master,text="Hide Advanced", command=self.Hide_Advanced)
        
        # End Right Column #

        #GEN Setting Window Entry initializations
        self.Entry_Sspeed    = Entry()
        self.Entry_BoxGap    = Entry()
        self.Entry_ContAngle = Entry()

        # Make Menu Bar
        self.menuBar = Menu(self.master, relief = "raised", bd=2)

        


        top_File = Menu(self.menuBar, tearoff=0)
        top_File.add("command", label = "Save Settings File", command = self.menu_File_Save)
        top_File.add("command", label = "Read Settings File", command = self.menu_File_Open_Settings_File)

        top_File.add_separator()
        top_File.add("command", label = "Open Design (SVG/DXF/G-Code)"  , command = self.menu_File_Open_Design)
        top_File.add("command", label = "Reload Design"          , command = self.menu_Reload_Design)

        top_File.add_separator()    
        top_File.add("command", label = "Send EGV File to Laser"             , command = self.menu_File_Open_EGV)

        SaveEGVmenu = Menu(self.master, relief = "raised", bd=2, tearoff=0)
        top_File.add_cascade(label="Save EGV File", menu=SaveEGVmenu)        
        SaveEGVmenu.add("command", label = "Raster Engrave"     , command = self.menu_File_Raster_Engrave)
        SaveEGVmenu.add("command", label = "Vector Engrave"     , command = self.menu_File_Vector_Engrave)
        SaveEGVmenu.add("command", label = "Vector Cut"         , command = self.menu_File_Vector_Cut)
        SaveEGVmenu.add("command", label = "G-Code Operations"  , command = self.menu_File_G_Code)
        SaveEGVmenu.add_separator()   
        SaveEGVmenu.add("command", label = "Raster and Vector Engrave"             , command = self.menu_File_Raster_Vector_Engrave)
        SaveEGVmenu.add("command", label = "Vector Engrave and Cut"                , command = self.menu_File_Vector_Engrave_Cut)
        SaveEGVmenu.add("command", label = "Raster, Vector Engrave and Vector Cut" , command = self.menu_File_Raster_Vector_Cut)
        
    
        top_File.add_separator()
        top_File.add("command", label = "Exit"              , command = self.menu_File_Quit)
        
        self.menuBar.add("cascade", label="File", menu=top_File)

        #top_Edit = Menu(self.menuBar, tearoff=0)
        #self.menuBar.add("cascade", label="Edit", menu=top_Edit)

        top_View = Menu(self.menuBar, tearoff=0)
        top_View.add("command", label = "Refresh   <F5>", command = self.menu_View_Refresh)
        top_View.add_separator()
        top_View.add_checkbutton(label = "Show Raster Image"  ,  variable=self.include_Reng ,command= self.menu_View_Refresh)
        if DEBUG:
            top_View.add_checkbutton(label = "Show Raster Paths" ,variable=self.include_Rpth ,command= self.menu_View_Refresh)
        top_View.add_checkbutton(label = "Show Vector Engrave",   variable=self.include_Veng ,command= self.menu_View_Refresh)
        top_View.add_checkbutton(label = "Show Vector Cut"    ,   variable=self.include_Vcut ,command= self.menu_View_Refresh)
        top_View.add_checkbutton(label = "Show G-Code Paths"  ,   variable=self.include_Gcde ,command= self.menu_View_Refresh)
        top_View.add_checkbutton(label = "Show Time Estimates",   variable=self.include_Time ,command= self.menu_View_Refresh)
        top_View.add_checkbutton(label = "Zoom to Design Size",   variable=self.zoom2image   ,command= self.menu_View_Refresh)

        #top_View.add_separator()
        #top_View.add("command", label = "computeAccurateReng",command= self.computeAccurateReng)
        #top_View.add("command", label = "computeAccurateVeng",command= self.computeAccurateVeng)
        #top_View.add("command", label = "computeAccurateVcut",command= self.computeAccurateVcut)

        self.menuBar.add("cascade", label="View", menu=top_View)


        top_USB = Menu(self.menuBar, tearoff=0)
        top_USB.add("command", label = "Reset USB", command = self.Reset)
        top_USB.add("command", label = "Release USB", command = self.Release_USB)
        top_USB.add("command", label = "Initialize Laser", command = self.Initialize_Laser)
        self.menuBar.add("cascade", label="USB", menu=top_USB)
        

        top_Settings = Menu(self.menuBar, tearoff=0)
        top_Settings.add("command", label = "General Settings", command = self.GEN_Settings_Window)
        top_Settings.add("command", label = "Raster Settings",  command = self.RASTER_Settings_Window)
        top_Settings.add_separator()
        top_Settings.add_checkbutton(label = "Advanced Settings", variable=self.advanced ,command= self.menu_View_Refresh)
        
        self.menuBar.add("cascade", label="Settings", menu=top_Settings)
        
        top_Help = Menu(self.menuBar, tearoff=0)
        top_Help.add("command", label = "About (e-mail)", command = self.menu_Help_About)
        top_Help.add("command", label = "K40 Whisperer Web Page", command = self.menu_Help_Web)
        top_Help.add("command", label = "Manual (Web Page)", command = self.menu_Help_Manual)
        self.menuBar.add("cascade", label="Help", menu=top_Help)

        self.master.config(menu=self.menuBar)

        ##########################################################################
        #                  Config File and command line options                  #
        ##########################################################################
        config_file = "k40_whisperer.txt"
        home_config1 = self.HOME_DIR + "/" + config_file
        if ( os.path.isfile(config_file) ):
            self.Open_Settings_File(config_file)
        elif ( os.path.isfile(home_config1) ):
            self.Open_Settings_File(home_config1)

        opts, args = None, None
        try:
            opts, args = getopt.getopt(sys.argv[1:], "ho:",["help", "other_option"])
        except:
            debug_message('Unable interpret command line options')
            sys.exit()
##        for option, value in opts:
##            if option in ('-h','--help'):
##                fmessage(' ')
##                fmessage('Usage: python .py [-g file]')
##                fmessage('-o    : unknown other option (also --other_option)')
##                fmessage('-h    : print this help (also --help)\n')
##                sys.exit()
##            if option in ('-o','--other_option'):
##                pass

        ##########################################################################

################################################################################
    def entry_set(self, val2, calc_flag=0, new=0):
        if calc_flag == 0 and new==0:
            try:
                self.statusbar.configure( bg = 'yellow' )
                val2.configure( bg = 'yellow' )
                self.statusMessage.set(" Recalculation required.")
            except:
                pass
        elif calc_flag == 3:
            try:
                val2.configure( bg = 'red' )
                self.statusbar.configure( bg = 'red' )
                self.statusMessage.set(" Value should be a number. ")
            except:
                pass
        elif calc_flag == 2:
            try:
                self.statusbar.configure( bg = 'red' )
                val2.configure( bg = 'red' )
            except:
                pass
        elif (calc_flag == 0 or calc_flag == 1) and new==1 :
            try:
                self.statusbar.configure( bg = 'white' )
                self.statusMessage.set(" ")
                val2.configure( bg = 'white' )
            except:
                pass
        elif (calc_flag == 1) and new==0 :
            try:
                self.statusbar.configure( bg = 'white' )
                self.statusMessage.set(" ")
                val2.configure( bg = 'white' )
            except:
                pass

        elif (calc_flag == 0 or calc_flag == 1) and new==2:
            return 0
        return 1

################################################################################
    def Write_Config_File(self, event):
        config_data = self.WriteConfig()
        config_file = "k40_whisperer.txt"
        configname_full = self.HOME_DIR + "/" + config_file

        win_id=self.grab_current()
        if ( os.path.isfile(configname_full) ):
            if not message_ask_ok_cancel("Replace", "Replace Exiting Configuration File?\n"+configname_full):
                try:
                    win_id.withdraw()
                    win_id.deiconify()
                except:
                    pass
                return
        try:
            fout = open(configname_full,'w')
        except:
            self.statusMessage.set("Unable to open file for writing: %s" %(configname_full))
            self.statusbar.configure( bg = 'red' )
            return
        for line in config_data:
            try:
                fout.write(line+'\n')
            except:
                fout.write('(skipping line)\n')
        fout.close
        self.statusMessage.set("Configuration File Saved: %s" %(configname_full))
        self.statusbar.configure( bg = 'white' )
        try:
            win_id.withdraw()
            win_id.deiconify()
        except:
            pass

    ################################################################################
    def WriteConfig(self):
        global Zero
        header = []
        header.append('( K40 Whisperer Settings: '+version+' )')
        header.append('( by Scorch - 2019 )')
        header.append("(=========================================================)")
        # BOOL
        header.append('(k40_whisperer_set include_Reng  %s )'  %( int(self.include_Reng.get())  ))
        header.append('(k40_whisperer_set include_Veng  %s )'  %( int(self.include_Veng.get())  ))
        header.append('(k40_whisperer_set include_Vcut  %s )'  %( int(self.include_Vcut.get())  ))
        header.append('(k40_whisperer_set include_Gcde  %s )'  %( int(self.include_Gcde.get())  ))
        header.append('(k40_whisperer_set include_Time  %s )'  %( int(self.include_Time.get())  ))
        
        header.append('(k40_whisperer_set halftone      %s )'  %( int(self.halftone.get())      ))
        header.append('(k40_whisperer_set HomeUR        %s )'  %( int(self.HomeUR.get())        ))
        header.append('(k40_whisperer_set inputCSYS     %s )'  %( int(self.inputCSYS.get())     ))
        header.append('(k40_whisperer_set advanced      %s )'  %( int(self.advanced.get())      ))
        header.append('(k40_whisperer_set mirror        %s )'  %( int(self.mirror.get())        ))
        header.append('(k40_whisperer_set rotate        %s )'  %( int(self.rotate.get())        ))
        header.append('(k40_whisperer_set negate        %s )'  %( int(self.negate.get())        ))
        
        header.append('(k40_whisperer_set engraveUP     %s )'  %( int(self.engraveUP.get())     ))
        header.append('(k40_whisperer_set init_home     %s )'  %( int(self.init_home.get())     ))
        header.append('(k40_whisperer_set pre_pr_crc    %s )'  %( int(self.pre_pr_crc.get())    ))
        header.append('(k40_whisperer_set inside_first  %s )'  %( int(self.inside_first.get())  ))

        header.append('(k40_whisperer_set comb_engrave  %s )'  %( int(self.comb_engrave.get())  ))
        header.append('(k40_whisperer_set comb_vector   %s )'  %( int(self.comb_vector.get())   ))
        header.append('(k40_whisperer_set zoom2image    %s )'  %( int(self.zoom2image.get())   ))

        # STRING.get()
        header.append('(k40_whisperer_set board_name    %s )'  %( self.board_name.get()     ))
        header.append('(k40_whisperer_set units         %s )'  %( self.units.get()          ))
        header.append('(k40_whisperer_set Reng_feed     %s )'  %( self.Reng_feed.get()      ))
        header.append('(k40_whisperer_set Veng_feed     %s )'  %( self.Veng_feed.get()      ))
        header.append('(k40_whisperer_set Vcut_feed     %s )'  %( self.Vcut_feed.get()      ))
        header.append('(k40_whisperer_set jog_step      %s )'  %( self.jog_step.get()       ))

        header.append('(k40_whisperer_set Reng_passes   %s )'  %( self.Reng_passes.get()    ))
        header.append('(k40_whisperer_set Veng_passes   %s )'  %( self.Veng_passes.get()    ))
        header.append('(k40_whisperer_set Vcut_passes   %s )'  %( self.Vcut_passes.get()    ))
        header.append('(k40_whisperer_set Gcde_passes   %s )'  %( self.Gcde_passes.get()    ))

        header.append('(k40_whisperer_set rast_step     %s )'  %( self.rast_step.get()      ))
        header.append('(k40_whisperer_set ht_size       %s )'  %( self.ht_size.get()        ))
        
        header.append('(k40_whisperer_set LaserXsize    %s )'  %( self.LaserXsize.get()     ))
        header.append('(k40_whisperer_set LaserYsize    %s )'  %( self.LaserYsize.get()     ))
        header.append('(k40_whisperer_set LaserXscale   %s )'  %( self.LaserXscale.get()    ))
        header.append('(k40_whisperer_set LaserYscale   %s )'  %( self.LaserYscale.get()    ))
        header.append('(k40_whisperer_set gotoX         %s )'  %( self.gotoX.get()          ))
        header.append('(k40_whisperer_set gotoY         %s )'  %( self.gotoY.get()          ))

        header.append('(k40_whisperer_set bezier_M1     %s )'  %( self.bezier_M1.get()      ))
        header.append('(k40_whisperer_set bezier_M2     %s )'  %( self.bezier_M2.get()      ))
        
        header.append('(k40_whisperer_set bezier_weight %s )'  %( self.bezier_weight.get()  ))

        header.append('(k40_whisperer_set t_timeout     %s )'  %( self.t_timeout.get()      ))
        header.append('(k40_whisperer_set n_timeouts    %s )'  %( self.n_timeouts.get()     ))
        
        header.append('(k40_whisperer_set designfile    \042%s\042 )' %( self.DESIGN_FILE   ))
        header.append('(k40_whisperer_set inkscape_path \042%s\042 )' %( self.inkscape_path.get() ))


        self.jog_step
        header.append("(=========================================================)")

        return header
        ######################################################

    def Quit_Click(self, event):
        self.statusMessage.set("Exiting!")
        self.Release_USB
        root.destroy()

    def mousePanStart(self,event):
        self.panx = event.x
        self.pany = event.y
        self.move_start_x = event.x
        self.move_start_y = event.y
        
    def mousePan(self,event):
        all = self.PreviewCanvas.find_all()
        dx = event.x-self.panx
        dy = event.y-self.pany

        self.PreviewCanvas.move('LaserTag', dx, dy)
        self.lastx = self.lastx + dx
        self.lasty = self.lasty + dy
        self.panx = event.x
        self.pany = event.y
        
    def mousePanStop(self,event):
        Xold = round(self.laserX,3)
        Yold = round(self.laserY,3)

        can_dx = event.x-self.move_start_x
        can_dy = -(event.y-self.move_start_y)
        
        dx = can_dx*self.PlotScale
        dy = can_dy*self.PlotScale
        if self.HomeUR.get():
            dx = -dx
        self.laserX,self.laserY = self.XY_in_bounds(dx,dy)
        DXmils = round((self.laserX - Xold)*1000.0,0)
        DYmils = round((self.laserY - Yold)*1000.0,0)
        
        if self.Send_Rapid_Move(DXmils,DYmils):
            self.menu_View_Refresh()

    def right_mousePanStart(self,event):
        self.s_panx = event.x
        self.s_pany = event.y
        self.s_move_start_x = event.x
        self.s_move_start_y = event.y
        
    def right_mousePan(self,event):
        all = self.PreviewCanvas.find_all()
        dx = event.x-self.s_panx
        dy = event.y-self.s_pany

        self.PreviewCanvas.move('LaserDot', dx, dy)
        self.s_lastx = self.lastx + dx
        self.s_lasty = self.lasty + dy
        self.s_panx = event.x
        self.s_pany = event.y
        
    def right_mousePanStop(self,event):
        Xold = round(self.laserX,3)
        Yold = round(self.laserY,3)
        can_dx =   event.x-self.s_move_start_x
        can_dy = -(event.y-self.s_move_start_y)
        
        dx = can_dx*self.PlotScale
        dy = can_dy*self.PlotScale
        if self.HomeUR.get():
            dx = -dx
            
        DX =  round(dx*1000)
        DY =  round(dy*1000)
        self.Move_Arbitrary(DX,DY)
        self.menu_View_Refresh()

    def LASER_Size(self):
        MINX = 0.0
        MAXY = 0.0
        if self.units.get()=="in":
            MAXX =  float(self.LaserXsize.get())
            MINY = -float(self.LaserYsize.get())
        else:
            MAXX =  float(self.LaserXsize.get())/25.4
            MINY = -float(self.LaserYsize.get())/25.4

        return (MAXX-MINX,MAXY-MINY)


    def XY_in_bounds(self,dx_inches,dy_inches, no_size=False):
        MINX = 0.0
        MAXY = 0.0
        if self.units.get()=="in":
            MAXX =  float(self.LaserXsize.get())
            MINY = -float(self.LaserYsize.get())
        else:
            MAXX =  float(self.LaserXsize.get())/25.4
            MINY = -float(self.LaserYsize.get())/25.4

        if (self.inputCSYS.get() and self.RengData.image == None) or no_size:
            xmin,xmax,ymin,ymax = 0.0,0.0,0.0,0.0
        else:
            xmin,xmax,ymin,ymax = self.Get_Design_Bounds()
        
        X = self.laserX + dx_inches
        Y = self.laserY + dy_inches
        ################
        dx=xmax-xmin
        dy=ymax-ymin
        if X < MINX:
            X = MINX
        if X+dx > MAXX:
            X = MAXX-dx
            
        if Y-dy < MINY:
            Y = MINY+dy
        if Y > MAXY:
            Y = MAXY
        ################
        if not no_size:
            XOFF = self.pos_offset[0]/1000.0
            YOFF = self.pos_offset[1]/1000.0
            if X+XOFF < MINX:
                X= X +(MINX-(X+XOFF))
            if X+XOFF > MAXX:
                X= X -((X+XOFF)-MAXX)
            if Y+YOFF < MINY:
                Y= Y + (MINY-(Y+YOFF))
            if Y+YOFF > MAXY:
                Y= Y -((Y+YOFF)-MAXY)
        ################
        X = round(X,3)
        Y = round(Y,3)
        return X,Y

##    def computeAccurateVeng(self):
##        self.update_gui("Optimize vector engrave.") 
##        self.VengData.set_ecoords(self.optimize_paths(self.VengData.ecoords),data_sorted=True)
##        self.refreshTime()
##            
##    def computeAccurateVcut(self):
##        self.update_gui("Optimize vector cut.") 
##        self.VcutData.set_ecoords(self.optimize_paths(self.VcutData.ecoords),data_sorted=True)
##        self.refreshTime()
##
##    def computeAccurateReng(self):
##        self.update_gui("Calculating Raster engrave.")
##        if self.RengData.image != None:        
##            if self.RengData.ecoords == []:
##                self.make_raster_coords()
##        self.RengData.sorted = True 
##        self.refreshTime()


    def format_time(self,time_in_seconds):
        # format the duration from seconds to something human readable
        if time_in_seconds >=0 :
            s = round(time_in_seconds)
            m,s=divmod(s,60)
            h,m=divmod(m,60)
            res = ""
            if h > 0:
                res =  "%dh " %(h)
            if m > 0:
                res += "%dm " %(m)
            if h == 0: 
                res += "%ds " %(s)
            #L=len(res)
            #for i in range(L,8):
            #    res =  res+" "
            return res
        else :
            return "?" 

    def refreshTime(self):
        if not self.include_Time.get():
            return
        if self.units.get() == 'in':
            factor =  60.0
        else : 
            factor = 25.4

        Raster_eng_feed = float(self.Reng_feed.get()) / factor
        Vector_eng_feed = float(self.Veng_feed.get()) / factor
        Vector_cut_feed = float(self.Vcut_feed.get()) / factor
        
        Raster_eng_passes = float(self.Reng_passes.get())
        Vector_eng_passes = float(self.Veng_passes.get())
        Vector_cut_passes = float(self.Vcut_passes.get())
        Gcode_passes      = float(self.Gcde_passes.get())

        rapid_feed = 100.0 / 25.4   # 100 mm/s move feed to be confirmed

        
        #if self.RengData.sorted:
        #    wim, him = self.RengData.image.size
        #    Reng_time  =  ( (self.RengData.len)/Raster_eng_feed + (him/self.input_dpi)/rapid_feed) * Raster_eng_passes
        #else:
        try:
            wim, him = self.RengData.image.size
            Reng_time  =   ((wim/self.input_dpi * him/self.input_dpi)/ float(self.rast_step.get()) ) / Raster_eng_feed*Raster_eng_passes
        except:
            Reng_time = 0

        Veng_time  =  (self.VengData.len / Vector_eng_feed + self.VengData.move / rapid_feed) * Vector_eng_passes
        Vcut_time  =  (self.VcutData.len / Vector_cut_feed + self.VcutData.move / rapid_feed) * Vector_cut_passes
        Gcode_time =  self.GcodeData.gcode_time * Gcode_passes
                
        self.Reng_time.set("Raster Engrave: %s" %(self.format_time(Reng_time)))
        self.Veng_time.set("Vector Engrave: %s" %(self.format_time(Veng_time)))
        self.Vcut_time.set("    Vector Cut: %s" %(self.format_time(Vcut_time)))
        self.Gcde_time.set("         Gcode: %s" %(self.format_time(Gcode_time)))
        
        ##########################################
        cszw = int(self.PreviewCanvas.cget("width"))
        cszh = int(self.PreviewCanvas.cget("height"))
        HUD_vspace = 15
        HUD_X = cszw-5
        HUD_Y = cszh-5
        self.PreviewCanvas.delete("HUD")
        if self.GcodeData.ecoords == []:
            self.PreviewCanvas.create_text(HUD_X, HUD_Y             , fill = "red"  ,text =self.Vcut_time.get(), anchor="se",tags="HUD")
            self.PreviewCanvas.create_text(HUD_X, HUD_Y-HUD_vspace  , fill = "blue" ,text =self.Veng_time.get(), anchor="se",tags="HUD")
            self.PreviewCanvas.create_text(HUD_X, HUD_Y-HUD_vspace*2, fill = "black",text =self.Reng_time.get(), anchor="se",tags="HUD")
        else:
            self.PreviewCanvas.create_text(HUD_X, HUD_Y, fill = "black",text =self.Gcde_time.get(), anchor="se",tags="HUD")
        ##########################################


    def Settings_ReLoad_Click(self, event):
        win_id=self.grab_current()

    def Close_Current_Window_Click(self):
        win_id=self.grab_current()
        win_id.destroy()
        
    # Left Column #
    #############################
    def Entry_Reng_feed_Check(self):
        try:
            value = float(self.Reng_feed.get())
            if  value <= 0.0:
                self.statusMessage.set(" Feed Rate should be greater than 0.0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        self.refreshTime()
        return 0         # Value is a valid number
    def Entry_Reng_feed_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Reng_feed, self.Entry_Reng_feed_Check(), new=1)        
    #############################
    def Entry_Veng_feed_Check(self):
        try:
            value = float(self.Veng_feed.get())
            if  value <= 0.0:
                self.statusMessage.set(" Feed Rate should be greater than 0.0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        self.refreshTime()
        return 0         # Value is a valid number
    def Entry_Veng_feed_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Veng_feed, self.Entry_Veng_feed_Check(), new=1)
    #############################
    def Entry_Vcut_feed_Check(self):
        try:
            value = float(self.Vcut_feed.get())
            if  value <= 0.0:
                self.statusMessage.set(" Feed Rate should be greater than 0.0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        self.refreshTime()
        return 0         # Value is a valid number
    def Entry_Vcut_feed_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Vcut_feed, self.Entry_Vcut_feed_Check(), new=1)
        
    #############################
    def Entry_Step_Check(self):
        try:
            value = float(self.jog_step.get())
            if  value <= 0.0:
                self.statusMessage.set(" Step should be greater than 0.0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_Step_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Step, self.Entry_Step_Check(), new=1)


    #############################
    def Entry_GoToX_Check(self):
        try:
            value = float(self.gotoX.get())
            if  (value < 0.0) and (not self.HomeUR.get()):
                self.statusMessage.set(" Value should be greater than 0.0 ")
                return 2 # Value is invalid number
            elif (value > 0.0) and self.HomeUR.get():
                self.statusMessage.set(" Value should be less than 0.0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_GoToX_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_GoToX, self.Entry_GoToX_Check(), new=1)

    #############################
    def Entry_GoToY_Check(self):
        try:
            value = float(self.gotoY.get())
            if  value > 0.0:
                self.statusMessage.set(" Value should be less than 0.0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_GoToY_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_GoToY, self.Entry_GoToY_Check(), new=1)
        
    #############################
    def Entry_Rstep_Check(self):
        try:
            value = self.get_raster_step_1000in()
            if  value <= 0 or value > 63:
                self.statusMessage.set(" Step should be between 0.001 and 0.063 in")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_Rstep_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Rstep, self.Entry_Rstep_Check(), new=1)
 
    #############################
    # End Left Column #
    #############################
    def bezier_weight_Callback(self, varName=None, index=None, mode=None):
        self.bezier_plot()
        
    def bezier_M1_Callback(self, varName=None, index=None, mode=None):
        self.bezier_plot()

    def bezier_M2_Callback(self, varName=None, index=None, mode=None):
        self.bezier_plot()

    def bezier_plot(self):
        self.BezierCanvas.delete('bez')

        #self.BezierCanvas.create_line( 5,260-0,260,260-255,fill="black", capstyle="round", width = 2, tags='bez')
        M1 = float(self.bezier_M1.get())
        M2 = float(self.bezier_M2.get())
        w  = float(self.bezier_weight.get())
        num = 10
        x,y = self.generate_bezier(M1,M2,w,n=num)
        for i in range(0,num):
            self.BezierCanvas.create_line( 5+x[i],260-y[i],5+x[i+1],260-y[i+1],fill="black", \
                                           capstyle="round", width = 2, tags='bez')
        self.BezierCanvas.create_text(128, 0, text="Output Level vs. Input Level",anchor="n", tags='bez')
            
    #############################
    def Entry_Timeout_Check(self):
        try:
            value = float(self.t_timeout.get())
            if  value <= 0.0:
                self.statusMessage.set(" Timeout should be greater than 0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_Timeout_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Timeout,self.Entry_Timeout_Check(), new=1)

    #############################
    def Entry_N_Timeouts_Check(self):
        try:
            value = float(self.n_timeouts.get())
            if  value <= 0.0:
                self.statusMessage.set(" N_Timeouts should be greater than 0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_N_Timeouts_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_N_Timeouts,self.Entry_N_Timeouts_Check(), new=1)

    #############################
    def Entry_N_EGV_Passes_Check(self):
        try:
            value = int(self.n_egv_passes.get())
            if  value < 1:
                self.statusMessage.set(" EGV passes should be 1 or higher")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_N_EGV_Passes_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_N_EGV_Passes,self.Entry_N_EGV_Passes_Check(), new=1)
        
    #############################
    def Entry_Laser_Area_Width_Check(self):
        try:
            value = float(self.LaserXsize.get())
            if  value <= 0.0:
                self.statusMessage.set(" Width should be greater than 0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_Laser_Area_Width_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Laser_Area_Width,self.Entry_Laser_Area_Width_Check(), new=1)

    #############################
    def Entry_Laser_Area_Height_Check(self):
        try:
            value = float(self.LaserYsize.get())
            if  value <= 0.0:
                self.statusMessage.set(" Height should be greater than 0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_Laser_Area_Height_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Laser_Area_Height,self.Entry_Laser_Area_Height_Check(), new=1)


    #############################
    def Entry_Laser_X_Scale_Check(self):
        try:
            value = float(self.LaserXscale.get())
            if  value <= 0.0:
                self.statusMessage.set(" Scale should be greater than 0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_Laser_X_Scale_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Laser_X_Scale,self.Entry_Laser_X_Scale_Check(), new=1)
    #############################
    def Entry_Laser_Y_Scale_Check(self):
        try:
            value = float(self.LaserYscale.get())
            if  value <= 0.0:
                self.statusMessage.set(" Height should be greater than 0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_Laser_Y_Scale_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Laser_Y_Scale,self.Entry_Laser_Y_Scale_Check(), new=1)

    # Advanced Column #
    #############################
    def Entry_Reng_passes_Check(self):
        try:
            value = int(self.Reng_passes.get())
            if  value < 1:
                self.statusMessage.set(" Number of passes should be greater than 0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        self.refreshTime()
        return 0         # Value is a valid number
    def Entry_Reng_passes_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Reng_passes, self.Entry_Reng_passes_Check(), new=1)        
    #############################
    def Entry_Veng_passes_Check(self):
        try:
            value = int(self.Veng_passes.get())
            if  value < 1:
                self.statusMessage.set(" Number of passes should be greater than 0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        self.refreshTime()
        return 0         # Value is a valid number
    def Entry_Veng_passes_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Veng_passes, self.Entry_Veng_passes_Check(), new=1)
    #############################
    def Entry_Vcut_passes_Check(self):
        try:
            value = int(self.Vcut_passes.get())
            if  value < 1:
                self.statusMessage.set(" Number of passes should be greater than 0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        self.refreshTime()
        return 0         # Value is a valid number
    def Entry_Vcut_passes_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Vcut_passes, self.Entry_Vcut_passes_Check(), new=1)
        
    #############################
    def Entry_Gcde_passes_Check(self):
        try:
            value = int(self.Gcde_passes.get())
            if  value < 1:
                self.statusMessage.set(" Number of passes should be greater than 0 ")
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number
    def Entry_Gcde_passes_Callback(self, varName, index, mode):
        self.entry_set(self.Entry_Gcde_passes, self.Entry_Gcde_passes_Check(), new=1)
        
    #############################





    ##########################################################################
    ##########################################################################
    def Check_All_Variables(self):
        return 0
##        MAIN_error_cnt= \
##        self.entry_set(self.Entry_Yscale, self.Entry_Yscale_Check()    ,2) +\
##        self.entry_set(self.Entry_Toptol, self.Entry_Toptol_Check()    ,2) 
##
##        GEN_error_cnt= \
##        self.entry_set(self.Entry_ContAngle,self.Entry_ContAngle_Check(),2)

##        ERROR_cnt = MAIN_error_cnt + GEN_error_cnt
##
##        if (ERROR_cnt > 0):
##            self.statusbar.configure( bg = 'red' )
##        if (GEN_error_cnt > 0):
##            self.statusMessage.set(\
##                " Entry Error Detected: Check Entry Values in General Settings Window ")
##        if (MAIN_error_cnt > 0):
##            self.statusMessage.set(\
##                " Entry Error Detected: Check Entry Values in Main Window ")
##
##        return ERROR_cnt



    #############################
    def Inkscape_Path_Click(self, event):
        win_id=self.grab_current()
        newfontdir = askopenfilename(filetypes=[("Executable Files",("inkscape.exe","*inkscape*")),\
                                                ("All Files","*")],\
                                                 initialdir=self.inkscape_path.get())
        if newfontdir != "" and newfontdir != ():
            self.inkscape_path.set(newfontdir.encode("utf-8"))
        try:
            win_id.withdraw()
            win_id.deiconify()
        except:
            pass


    def Entry_units_var_Callback(self):
        if (self.units.get() == 'in') and (self.funits.get()=='mm/s'):
            self.funits.set('in/min')
            self.Scale_Linear_Inputs('in')
        elif (self.units.get() == 'mm') and (self.funits.get()=='in/min'):
            self.funits.set('mm/s')
            self.Scale_Linear_Inputs('mm')
            
    def Scale_Linear_Inputs(self, new_units=None):
        if new_units=='in':
            self.units_scale = 1.0
            factor  = 1/25.4
            vfactor = 60.0/25.4
        elif new_units=='mm':
            factor  = 25.4
            vfactor = 25.4/60.0
            self.units_scale = 25.4
        else:
            return
        self.LaserXsize.set( self.Scale_Text_Value('%.2f',self.LaserXsize.get(),factor) )
        self.LaserYsize.set( self.Scale_Text_Value('%.2f',self.LaserYsize.get(),factor) )
        self.jog_step.set  ( self.Scale_Text_Value('%.3f',self.jog_step.get()  ,factor) )
        self.gotoX.set     ( self.Scale_Text_Value('%.3f',self.gotoX.get()     ,factor) )
        self.gotoY.set     ( self.Scale_Text_Value('%.3f',self.gotoY.get()     ,factor) )
        self.Reng_feed.set ( self.Scale_Text_Value('%.1f',self.Reng_feed.get() ,vfactor) )
        self.Veng_feed.set ( self.Scale_Text_Value('%.1f',self.Veng_feed.get() ,vfactor) )
        self.Vcut_feed.set ( self.Scale_Text_Value('%.1f',self.Vcut_feed.get() ,vfactor) )

    def Scale_Text_Value(self,format_txt,Text_Value,factor):
        try:
            return format_txt %(float(Text_Value)*factor )
        except:
            return ''

    def menu_File_Open_Settings_File(self,event=None):
        init_dir = os.path.dirname(self.DESIGN_FILE)
        if ( not os.path.isdir(init_dir) ):
            init_dir = self.HOME_DIR
        fileselect = askopenfilename(filetypes=[("Settings Files","*.txt"),\
                                                ("All Files","*")],\
                                                 initialdir=init_dir)
        if fileselect != '' and fileselect != ():
            self.Open_Settings_File(fileselect)


    def menu_Reload_Design(self,event=None):
        file_full = self.DESIGN_FILE
        file_name = os.path.basename(file_full)
        if ( os.path.isfile(file_full) ):
            filename = file_full
        elif ( os.path.isfile( file_name ) ):
            filename = file_name
        elif ( os.path.isfile( self.HOME_DIR+"/"+file_name ) ):
            filename = self.HOME_DIR+"/"+file_name
        else:
            self.statusMessage.set("file not found: %s" %(os.path.basename(file_full)) )
            self.statusbar.configure( bg = 'red' ) 
            return
        
        Name, fileExtension = os.path.splitext(filename)
        TYPE=fileExtension.upper()
        if TYPE=='.DXF':
            self.Open_DXF(filename)
        elif TYPE=='.SVG':
            self.Open_SVG(filename)
        elif TYPE=='.EGV':
            self.EGV_Send_Window(filename)
        else:
            self.Open_G_Code(filename)
        self.menu_View_Refresh()
        

    def menu_File_Open_Design(self,event=None):
        init_dir = os.path.dirname(self.DESIGN_FILE)
        if ( not os.path.isdir(init_dir) ):
            init_dir = self.HOME_DIR

        fileselect = askopenfilename(filetypes=[("Design Files", ("*.svg","*.dxf")),
                                            ("G-Code Files", ("*.ngc","*.gcode","*.g","*.tap")),\
                                            ("DXF Files","*.dxf"),\
                                            ("SVG Files","*.svg"),\
                                            ("All Files","*"),\
                                            ("Design Files ", ("*.svg","*.dxf"))],\
                                            initialdir=init_dir)

        if fileselect == () or (not os.path.isfile(fileselect)):
            return
            
        Name, fileExtension = os.path.splitext(fileselect)
        self.update_gui("Opening '%s'" % fileselect )
        TYPE=fileExtension.upper()
        if TYPE=='.DXF':
            self.Open_DXF(fileselect)
        elif TYPE=='.SVG':
            self.Open_SVG(fileselect)
        else:
            self.Open_G_Code(fileselect)

            
        self.DESIGN_FILE = fileselect
        self.menu_View_Refresh()
        
    def menu_File_Raster_Engrave(self):
        self.menu_File_save_EGV(operation_type="Raster_Eng")
        
    def menu_File_Vector_Engrave(self):
        self.menu_File_save_EGV(operation_type="Vector_Eng")
        
    def menu_File_Vector_Cut(self):
        self.menu_File_save_EGV(operation_type="Vector_Cut")
        
    def menu_File_G_Code(self):
        self.menu_File_save_EGV(operation_type="Gcode_Cut")
        
    def menu_File_Raster_Vector_Engrave(self):
        self.menu_File_save_EGV(operation_type="Raster_Eng-Vector_Eng")

    def menu_File_Vector_Engrave_Cut(self):
        self.menu_File_save_EGV(operation_type="Vector_Eng-Vector_Cut")

    def menu_File_Raster_Vector_Cut(self):
        self.menu_File_save_EGV(operation_type="Raster_Eng-Vector_Eng-Vector_Cut")


    def menu_File_save_EGV(self,operation_type=None,default_name="out.EGV"):
        if DEBUG:
            start=time()
        fileName, fileExtension = os.path.splitext(self.DESIGN_FILE)
        init_file=os.path.basename(fileName)
        default_name = init_file+"_"+operation_type
        
        if self.EGV_FILE != None:
            init_dir = os.path.dirname(self.EGV_FILE)
        else:
            init_dir = os.path.dirname(self.DESIGN_FILE)
            
        if ( not os.path.isdir(init_dir) ):
            init_dir = self.HOME_DIR
            
        fileName, fileExtension = os.path.splitext(default_name)
        init_file=os.path.basename(fileName)

        filename = asksaveasfilename(defaultextension='.EGV', \
                                     filetypes=[("EGV File","*.EGV")],\
                                     initialdir=init_dir,\
                                     initialfile= init_file )
        
        if filename != '' and filename != ():

            if operation_type.find("Raster_Eng") > -1:
                self.make_raster_coords()
            else:
                self.statusbar.configure( bg = 'yellow' )
                self.statusMessage.set("No raster data to engrave")
                
            self.send_data(operation_type=operation_type, output_filename=filename)
            self.EGV_FILE = filename
        if DEBUG:
            print("time = %d seconds" %(int(time()-start)))
        


    def menu_File_Open_EGV(self):
        init_dir = os.path.dirname(self.DESIGN_FILE)
        if ( not os.path.isdir(init_dir) ):
            init_dir = self.HOME_DIR
        fileselect = askopenfilename(filetypes=[("Engraver Files", ("*.egv","*.EGV")),\
                                                    ("All Files","*")],\
                                                     initialdir=init_dir)
        if fileselect != '' and fileselect != ():
            self.resetPath()
            self.DESIGN_FILE = fileselect
            self.EGV_Send_Window(fileselect)

            
    def Open_EGV(self,filemname,n_passes=1):
        pass
        EGV_data=[]
        value1 = ""
        value2 = ""
        value3 = ""
        value4 = ""
        data=""
        #value1 and value2 are the absolute y and x starting positions
        #value3 and value4 are the absolute y and x end positions
        with open(filemname) as f:
            while True:
                ## Skip header
                c = f.read(1)
                while c!="%" and c:
                    c = f.read(1)
                ## Read 1st Value
                c = f.read(1)
                while c!="%" and c:
                    value1 = value1 + c
                    c = f.read(1)
                y_start_mils = int(value1) 
                ## Read 2nd Value
                c = f.read(1)
                while c!="%" and c:
                    value2 = value2 + c
                    c = f.read(1)
                x_start_mils = int(value2)   
                ## Read 3rd Value
                c = f.read(1)
                while c!="%" and c:
                    value3 = value3 + c
                    c = f.read(1)
                y_end_mils = int(value3)
                ## Read 4th Value
                c = f.read(1)
                while c!="%" and c:
                    value4 = value4 + c
                    c = f.read(1)
                x_end_mils = int(value4)
                break

            ## Read Data
            while True:
                c = f.read(1)
                if not c:
                    break
                if c=='\n' or c==' ' or c=='\r':
                    pass
                else:
                    data=data+"%c" %c
                    EGV_data.append(ord(c))
                    
        if ( (x_end_mils != 0) or (y_end_mils != 0) ):
            n_passes=1
        else:
            x_start_mils = 0
            y_start_mils = 0

        try:
            self.send_egv_data(EGV_data,n_passes)
        except MemoryError as e:
            #raise StandardError("Memory Error:  Out of Memory.")
            raise Exception("Memory Error:  Out of Memory.")
            debug_message(traceback.format_exc())
        #except StandardError as e:
        except Exception as e:
            msg1 = "Sending Data Stopped: "
            msg2 = "%s" %(e)
            if msg2 == "":
                formatted_lines = traceback.format_exc().splitlines()
            self.statusMessage.set((msg1+msg2).split("\n")[0] )
            self.statusbar.configure( bg = 'red' )
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())

        #rapid move back to starting position
        dxmils = -(x_end_mils - x_start_mils)
        dymils =   y_end_mils - y_start_mils
        self.Send_Rapid_Move(dxmils,dxmils)

        
    def Open_SVG(self,filemname):
        self.resetPath()
               
        self.SVG_FILE = filemname
        svg_reader =  SVG_READER()
        svg_reader.set_inkscape_path(self.inkscape_path.get())
        self.input_dpi = 1000
        svg_reader.image_dpi = self.input_dpi
        try:
            try:
                svg_reader.parse(self.SVG_FILE)
                svg_reader.make_paths()
            except SVG_TEXT_EXCEPTION as e:
                svg_reader = SVG_READER()
                svg_reader.set_inkscape_path(self.inkscape_path.get())
                self.statusMessage.set("Converting TEXT to PATHS.")
                self.master.update()
                svg_reader.parse(self.SVG_FILE)
                svg_reader.make_paths(txt2paths=True)
                
        except Exception as e:
            msg1 = "SVG file load failed: "
            msg2 = "%s" %(e)
            self.statusMessage.set((msg1+msg2).split("\n")[0] )
            self.statusbar.configure( bg = 'red' )
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())
            return
        except:
            self.statusMessage.set("Unable To open SVG File: %s" %(filemname))
            debug_message(traceback.format_exc())
            return
        xmax = svg_reader.Xsize/25.4
        ymax = svg_reader.Ysize/25.4
        xmin = 0
        ymin = 0

        self.Design_bounds = (xmin,xmax,ymin,ymax)
        
        ##########################
        ###   Create ECOORDS   ###
        ##########################
        self.VcutData.make_ecoords(svg_reader.cut_lines,scale=1/25.4)
        self.VengData.make_ecoords(svg_reader.eng_lines,scale=1/25.4)

        ##########################
        ###   Load Image       ###
        ##########################
        self.RengData.set_image(svg_reader.raster_PIL)
        
        if (self.RengData.image != None):
            self.wim, self.him = self.RengData.image.size
            self.aspect_ratio =  float(self.wim-1) / float(self.him-1)
            #self.make_raster_coords()
        self.refreshTime()

    def make_ecoords(self,coords,scale=1):
        xmax, ymax = -1e10, -1e10
        xmin, ymin =  1e10,  1e10
        ecoords=[]
        Acc=.001
        oldx = oldy = -99990.0
        first_stroke = True
        loop=0
        for line in coords:
            XY = line
            x1 = XY[0]*scale
            y1 = XY[1]*scale
            x2 = XY[2]*scale
            y2 = XY[3]*scale
            dx = oldx - x1
            dy = oldy - y1
            dist = sqrt(dx*dx + dy*dy)
            # check and see if we need to move to a new discontinuous start point
            if (dist > Acc) or first_stroke:
                loop = loop+1
                first_stroke = False
                ecoords.append([x1,y1,loop])
            ecoords.append([x2,y2,loop])
            oldx, oldy = x2, y2
            xmax=max(xmax,x1,x2)
            ymax=max(ymax,y1,y2)
            xmin=min(xmin,x1,x2)
            ymin=min(ymin,y1,y2)
        bounds = (xmin,xmax,ymin,ymax)
        return ecoords,bounds

##    def convert_greyscale(self,image):
##        image = image.convert('RGB')
##        x_lim, y_lim = image.size
##        grey = Image.new("L", image.size, color=255)
##        
##        pixel = image.load()
##        grey_pixel = grey.load()
##        
##        for y in range(1, y_lim):
##            self.statusMessage.set("Converting to greyscale: %.1f %%" %( (100.0*y)/y_lim ) )
##            self.master.update()
##            for x in range(1, x_lim):
##                value = pixel[x, y]
##                grey_pixel[x,y] = int( value[0]*.333 + value[1]*.333 +value[2]*.333 )
##                #grey_pixel[x,y] = int( value[0]*.210 + value[1]*.720 +value[2]*.007 )
##                grey_pixel[x,y] = int( value[0]*.299 + value[1]*.587 +value[2]*.114 )
##
##        grey.save("adjusted_grey.png","PNG")
##        return grey

    
    #####################################################################
    def make_raster_coords(self):
            ecoords=[]
            if (self.RengData.image != None):
                cutoff=128
                image_temp = self.RengData.image.convert("L")

                if self.negate.get():
                    image_temp = ImageOps.invert(image_temp)
                    
                if self.mirror.get():
                    image_temp = ImageOps.mirror(image_temp)

                if self.rotate.get():
                    #image_temp = image_temp.rotate(90,expand=True)
                    image_temp = self.rotate_raster(image_temp)

                Xscale = float(self.LaserXscale.get())
                Yscale = float(self.LaserYscale.get())
                if Xscale != 1.0 or Yscale != 1.0:
                    wim,him = image_temp.size
                    nw = int(wim*Xscale)
                    nh = int(him*Yscale)
                    image_temp = image_temp.resize((nw,nh))

                    
                if self.halftone.get():
                    #start = time()
                    ht_size_mils =  round( 1000.0 / float(self.ht_size.get()) ,1)
                    npixels = int( round(ht_size_mils,1) )
                    if npixels == 0:
                        return
                    wim,him = image_temp.size
                    # Convert to Halftoning and save
                    nw=int(wim / npixels)
                    nh=int(him / npixels)
                    image_temp = image_temp.resize((nw,nh))
                    
                    image_temp = self.convert_halftoning(image_temp)
                    image_temp = image_temp.resize((wim,him))
                    #print time()-start
                    
                if DEBUG:
                    image_name = os.path.expanduser("~")+"/IMAGE.png"
                    image_temp.save(image_name,"PNG")

                Reng_np = image_temp.load()
                wim,him = image_temp.size
                #######################################
                x=0
                y=0
                loop=1
                
                Raster_step = self.get_raster_step_1000in()
                timestamp=0
                for i in range(0,him,Raster_step):
                    stamp=int(3*time()) #update every 1/3 of a second
                    if (stamp != timestamp):
                        timestamp=stamp #interlock
                        self.statusMessage.set("Raster Engraving: Creating Scan Lines: %.1f %%" %( (100.0*i)/him ) )
                        self.master.update()
                    if self.stop[0]==True:
                        raise Exception("Action stopped by User.")
                    line = []
                    cnt=1
                    for j in range(1,wim):
                        if (Reng_np[j,i] == Reng_np[j-1,i]):
                            cnt = cnt+1
                        else:
                            laser = "U" if Reng_np[j-1,i] > cutoff else "D"
                            line.append((cnt,laser))
                            cnt=1
                    laser = "U" if Reng_np[j-1,i] > cutoff else "D"
                    line.append((cnt,laser))
                    
                    y=(him-i)/1000.0
                    x=0
                    #rng = range(0,len(line),1)
                    rng = list(range(0,len(line),1))
                        
                    for i in rng:
                        seg = line[i]
                        delta = seg[0]/1000.0
                        if seg[1]=="D":
                            loop=loop+1
                            ecoords.append([x      ,y,loop])
                            ecoords.append([x+delta,y,loop])
                        x = x + delta
                        
            if ecoords!=[]:
                self.RengData.set_ecoords(ecoords,data_sorted=True)
    #######################################################################


    def rotate_raster(self,image_in):
        wim,him = image_in.size
        im_rotated = Image.new("L", (him, wim), "white")

        image_in_np   = image_in.load()
        im_rotated_np = im_rotated.load()
        
        for i in range(1,him):
            for j in range(1,wim):
                im_rotated_np[i,wim-j] = image_in_np[j,i]
        return im_rotated
    
    def get_raster_step_1000in(self):
        val_in = float(self.rast_step.get())
        value = int(round(val_in*1000.0,1))
        return value


    def generate_bezier(self,M1,M2,w,n=100):
        if (M1==M2):
            x1=0
            y1=0
        else:
            x1 = 255*(1-M2)/(M1-M2)
            y1 = M1*x1
        x=[]
        y=[]
        # Calculate Bezier Curve
        for step in range(0,n+1):
            t    = float(step)/float(n)
            Ct   = 1 / ( pow(1-t,2)+2*(1-t)*t*w+pow(t,2) )
            x.append( Ct*( 2*(1-t)*t*w*x1+pow(t,2)*255) )
            y.append( Ct*( 2*(1-t)*t*w*y1+pow(t,2)*255) )
        return x,y

    '''This Example opens an Image and transform the image into halftone.  -Isai B. Cicourel'''
    # Create a Half-tone version of the image
    def convert_halftoning(self,image):
        image = image.convert('L')
        x_lim, y_lim = image.size
        pixel = image.load()
        
        M1 = float(self.bezier_M1.get())
        M2 = float(self.bezier_M2.get())
        w  = float(self.bezier_weight.get())
        
        if w > 0:
            x,y = self.generate_bezier(M1,M2,w)
            
            interp = interpolate(x, y) # Set up interpolate class
            val_map=[]
            # Map Bezier Curve to values between 0 and 255
            for val in range(0,256):
                val_out = int(round(interp[val])) # Get the interpolated value at each value
                val_map.append(val_out)
            # Adjust image
            timestamp=0
            for y in range(1, y_lim):
                stamp=int(3*time()) #update every 1/3 of a second
                if (stamp != timestamp):
                    timestamp=stamp #interlock
                    self.statusMessage.set("Raster Engraving: Adjusting Image Darkness: %.1f %%" %( (100.0*y)/y_lim ) )
                    self.master.update()
                for x in range(1, x_lim):
                    pixel[x, y] = val_map[ pixel[x, y] ]

        self.statusMessage.set("Raster Engraving: Creating Halftone Image." )
        self.master.update()
        image = image.convert('1')
        return image

    #######################################################################

    def Open_G_Code(self,filename):
        self.resetPath()
        
        g_rip = G_Code_Rip()
        try:
            MSG = g_rip.Read_G_Code(filename, XYarc2line = True, arc_angle=2, units="in", Accuracy="")
            Error_Text = ""
            if MSG!=[]:
                for line in MSG:
                    Error_Text = Error_Text + line + "\n"
                    message_box("G-Code Messages", Error_Text)
        #except StandardError as e:
        except Exception as e:
            msg1 = "G-Code Load Failed:  "
            msg2 = "Filename: %s" %(filename)
            msg3 = "%s" %(e)
            self.statusMessage.set((msg1+msg3).split("\n")[0] )
            self.statusbar.configure( bg = 'red' )
            message_box(msg1, "%s\n%s" %(msg2,msg3))
            debug_message(traceback.format_exc())

            
        ecoords= g_rip.generate_laser_paths(g_rip.g_code_data)
        self.GcodeData.set_ecoords(ecoords,data_sorted=True)
        self.Design_bounds = self.GcodeData.bounds

        
    def Open_DXF(self,filemname):
        self.resetPath()
        
        self.DXF_FILE = filemname
        dxf_import=DXF_CLASS()
        tolerance = .0005
        try:
            fd = open(self.DXF_FILE)
            dxf_import.GET_DXF_DATA(fd,lin_tol = tolerance,get_units=True,units=None)
            fd.seek(0)
            
            dxf_units = dxf_import.units
            if dxf_units=="Unitless":
                d = UnitsDialog(root)
                dxf_units = d.result
            if dxf_units=="Inches":
                dxf_scale = 1.0
            elif dxf_units=="Feet":
                dxf_scale = 12.0
            elif dxf_units=="Miles":
                dxf_scale = 5280.0*12.0
            elif dxf_units=="Millimeters":
                dxf_scale = 1.0/25.4
            elif dxf_units=="Centimeters":
                dxf_scale = 1.0/2.54
            elif dxf_units=="Meters":
                dxf_scale = 1.0/254.0
            elif dxf_units=="Kilometers":
                dxf_scale = 1.0/254000.0
            elif dxf_units=="Microinches":
                dxf_scale = 1.0/1000000.0
            elif dxf_units=="Mils":
                dxf_scale = 1.0/1000.0
            else:
                return    

            lin_tol = tolerance / dxf_scale
            dxf_import.GET_DXF_DATA(fd,lin_tol=lin_tol,get_units=False,units=None)
            fd.close()
        #except StandardError as e:
        except Exception as e:
            msg1 = "DXF Load Failed:"
            msg2 = "%s" %(e)
            self.statusMessage.set((msg1+msg2).split("\n")[0] )
            self.statusbar.configure( bg = 'red' )
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())
        except:
            fmessage("Unable To open Drawing Exchange File (DXF) file.")
            debug_message(traceback.format_exc())
            return
        
        new_origin=False
        dxf_engrave_coords = dxf_import.DXF_COORDS_GET_TYPE(engrave=True, new_origin=False)
        dxf_cut_coords     = dxf_import.DXF_COORDS_GET_TYPE(engrave=False,new_origin=False)
##        if DEBUG:
##            dxf_code = dxf_import.WriteDXF(close_loops=False)
##            fout = open('Z:\\out.dxf','w')
##            for line in dxf_code:
##                fout.write(line+'\n')
##            fout.close
        
        if dxf_import.dxf_messages != "":
            msg_split=dxf_import.dxf_messages.split("\n")
            msg_split.sort()
            msg_split.append("")
            mcnt=1
            msg_out = ""
            for i in range(1,len(msg_split)):
                if msg_split[i-1]==msg_split[i]:
                    mcnt=mcnt+1
                else:
                    if msg_split[i-1]!="":
                        msg_line = "%s (%d places)\n" %(msg_split[i-1],mcnt)
                        msg_out = msg_out + msg_line
                    mcnt=1
            message_box("DXF Import:",msg_out)
                    
        ##########################
        ###   Create ECOORDS   ###
        ##########################
        self.VcutData.make_ecoords(dxf_cut_coords    ,scale=dxf_scale)
        self.VengData.make_ecoords(dxf_engrave_coords,scale=dxf_scale)

        xmin = min(self.VcutData.bounds[0],self.VengData.bounds[0])
        xmax = max(self.VcutData.bounds[1],self.VengData.bounds[1])
        ymin = min(self.VcutData.bounds[2],self.VengData.bounds[2])
        ymax = max(self.VcutData.bounds[3],self.VengData.bounds[3])
        self.Design_bounds = (xmin,xmax,ymin,ymax)


    def Open_Settings_File(self,filename):
        try:
            fin = open(filename,'r')
        except:
            fmessage("Unable to open file: %s" %(filename))
            return
        
        text_codes=[]
        ident = "k40_whisperer_set"
        for line in fin:
            if ident in line:
                # BOOL
                if "include_Reng"  in line:
                    self.include_Reng.set(line[line.find("include_Reng"):].split()[1])
                elif "include_Veng"  in line:
                    self.include_Veng.set(line[line.find("include_Veng"):].split()[1])
                elif "include_Vcut"  in line:
                    self.include_Vcut.set(line[line.find("include_Vcut"):].split()[1])
                elif "include_Gcde"  in line:
                    self.include_Gcde.set(line[line.find("include_Gcde"):].split()[1])
                elif "include_Time"  in line:
                    self.include_Time.set(line[line.find("include_Time"):].split()[1])
                elif "halftone"  in line:
                    self.halftone.set(line[line.find("halftone"):].split()[1])
                elif "negate"  in line:
                    self.negate.set(line[line.find("negate"):].split()[1])
                elif "HomeUR"  in line:
                    self.HomeUR.set(line[line.find("HomeUR"):].split()[1])                    
                elif "inputCSYS"  in line:
                    self.inputCSYS.set(line[line.find("inputCSYS"):].split()[1])
                elif "advanced"  in line:
                    self.advanced.set(line[line.find("advanced"):].split()[1])
                elif "mirror"  in line:
                    self.mirror.set(line[line.find("mirror"):].split()[1])
                elif "rotate"  in line:
                    self.rotate.set(line[line.find("rotate"):].split()[1])
                elif "engraveUP"  in line:
                    self.engraveUP.set(line[line.find("engraveUP"):].split()[1])
                elif "init_home"  in line:
                    self.init_home.set(line[line.find("init_home"):].split()[1])
                elif "pre_pr_crc"  in line:
                    self.pre_pr_crc.set(line[line.find("pre_pr_crc"):].split()[1])
                elif "inside_first"  in line:
                    self.inside_first.set(line[line.find("inside_first"):].split()[1])
                elif "comb_engrave"  in line:
                    self.comb_engrave.set(line[line.find("comb_engrave"):].split()[1])
                elif "comb_vector"  in line:
                    self.comb_vector.set(line[line.find("comb_vector"):].split()[1])
                elif "zoom2image"  in line:
                    self.zoom2image.set(line[line.find("zoom2image"):].split()[1])
        
                # STRING.set()
                elif "board_name" in line:
                    self.board_name.set(line[line.find("board_name"):].split()[1])
                elif "units"    in line:
                    self.units.set(line[line.find("units"):].split()[1])
                elif "Reng_feed"    in line:
                     self.Reng_feed .set(line[line.find("Reng_feed"):].split()[1])
                elif "Veng_feed"    in line:
                     self.Veng_feed .set(line[line.find("Veng_feed"):].split()[1])  
                elif "Vcut_feed"    in line:
                     self.Vcut_feed.set(line[line.find("Vcut_feed"):].split()[1])
                elif "jog_step"    in line:
                     self.jog_step.set(line[line.find("jog_step"):].split()[1])
                     
                elif "Reng_passes"    in line:
                     self.Reng_passes.set(line[line.find("Reng_passes"):].split()[1])
                elif "Veng_passes"    in line:
                     self.Veng_passes.set(line[line.find("Veng_passes"):].split()[1])
                elif "Vcut_passes"    in line:
                     self.Vcut_passes.set(line[line.find("Vcut_passes"):].split()[1])
                elif "Gcde_passes"    in line:
                     self.Gcde_passes.set(line[line.find("Gcde_passes"):].split()[1])

                elif "rast_step"    in line:
                     self.rast_step.set(line[line.find("rast_step"):].split()[1])
                elif "ht_size"    in line:
                     self.ht_size.set(line[line.find("ht_size"):].split()[1])

                elif "LaserXsize"    in line:
                     self.LaserXsize.set(line[line.find("LaserXsize"):].split()[1])
                elif "LaserYsize"    in line:
                     self.LaserYsize.set(line[line.find("LaserYsize"):].split()[1])
                elif "LaserXscale"    in line:
                     self.LaserXscale.set(line[line.find("LaserXscale"):].split()[1])
                elif "LaserYscale"    in line:
                     self.LaserYscale.set(line[line.find("LaserYscale"):].split()[1])
                     
                elif "gotoX"    in line:
                     self.gotoX.set(line[line.find("gotoX"):].split()[1])
                elif "gotoY"    in line:
                     self.gotoY.set(line[line.find("gotoY"):].split()[1])

                elif "bezier_M1"    in line:
                     self.bezier_M1.set(line[line.find("bezier_M1"):].split()[1])
                elif "bezier_M2"    in line:
                     self.bezier_M2.set(line[line.find("bezier_M2"):].split()[1])
                elif "bezier_weight"    in line:
                     self.bezier_weight.set(line[line.find("bezier_weight"):].split()[1])
        
                elif "t_timeout"    in line:
                     self.t_timeout.set(line[line.find("t_timeout"):].split()[1])
                elif "n_timeouts"    in line:
                     self.n_timeouts.set(line[line.find("n_timeouts"):].split()[1]) 

                elif "designfile"    in line:
                       self.DESIGN_FILE=(line[line.find("designfile"):].split("\042")[1])
                elif "inkscape_path"    in line:
                     self.inkscape_path.set(line[line.find("inkscape_path"):].split("\042")[1])
                     
        fin.close()

        fileName, fileExtension = os.path.splitext(self.DESIGN_FILE)
        init_file=os.path.basename(fileName)
        
        if init_file != "None":
            if ( os.path.isfile(self.DESIGN_FILE) ):
                pass
            else:
                self.statusMessage.set("Image file not found: %s " %(self.DESIGN_FILE))

        if self.units.get() == 'in':
            self.funits.set('in/min')
            self.units_scale = 1.0
        else:
            self.units.set('mm')
            self.funits.set('mm/s')
            self.units_scale = 25.4

        temp_name, fileExtension = os.path.splitext(filename)
        file_base=os.path.basename(temp_name)
            
        if self.initComplete == 1:
            self.menu_Mode_Change()
            self.DESIGN_FILE = filename
            
    ##########################################################################
    ##########################################################################
    def menu_File_Save(self):
        #if (self.Check_All_Variables() > 0):
        #    return

        settings_data = self.WriteConfig()
        init_dir = os.path.dirname(self.DESIGN_FILE)
        if ( not os.path.isdir(init_dir) ):
            init_dir = self.HOME_DIR
            
        fileName, fileExtension = os.path.splitext(self.DESIGN_FILE)
        init_file=os.path.basename(fileName)

        filename = asksaveasfilename(defaultextension='.txt', \
                                     filetypes=[("Text File","*.txt")],\
                                     initialdir=init_dir,\
                                     initialfile= init_file )

        if filename != '' and filename != ():
            try:
                fout = open(filename,'w')
            except:
                self.statusMessage.set("Unable to open file for writing: %s" %(filename))
                self.statusbar.configure( bg = 'red' )
                return

            for line in settings_data:
                try:
                    fout.write(line+'\n')
                except:
                    fout.write('(skipping line)\n')
                    debug_message(traceback.format_exc())
            fout.close
            self.statusMessage.set("File Saved: %s" %(filename))
            self.statusbar.configure( bg = 'white' )
        
    def Get_Design_Bounds(self):
        if self.rotate.get():
            ymin =  self.Design_bounds[0]
            ymax =  self.Design_bounds[1]
            xmin = -self.Design_bounds[3]
            xmax = -self.Design_bounds[2]
        else:
            xmin,xmax,ymin,ymax = self.Design_bounds
        return (xmin,xmax,ymin,ymax)
    
    def Move_UL(self,dummy=None):
        xmin,xmax,ymin,ymax = self.Get_Design_Bounds()
        if self.HomeUR.get():
            Xnew = self.laserX + (xmax-xmin)
            DX = round((xmax-xmin)*1000.0)
        else:
            Xnew = self.laserX
            DX = 0
            
        (Xsize,Ysize)=self.LASER_Size()
        if Xnew <= Xsize+.001:
            self.move_head_window_temporary([DX,0.0])
        else:
            pass

    def Move_UR(self,dummy=None):
        xmin,xmax,ymin,ymax = self.Get_Design_Bounds()
        if self.HomeUR.get():
            Xnew = self.laserX
            DX = 0
        else:
            Xnew = self.laserX + (xmax-xmin) 
            DX = round((xmax-xmin)*1000.0)

        (Xsize,Ysize)=self.LASER_Size()
        if Xnew <= Xsize+.001:
            self.move_head_window_temporary([DX,0.0])
        else:
            pass
    
    def Move_LR(self,dummy=None):
        xmin,xmax,ymin,ymax = self.Get_Design_Bounds()
        if self.HomeUR.get():
            Xnew = self.laserX
            DX = 0
        else:
            Xnew = self.laserX + (xmax-xmin) 
            DX = round((xmax-xmin)*1000.0)
            
        Ynew = self.laserY - (ymax-ymin)
        (Xsize,Ysize)=self.LASER_Size()
        if Xnew <= Xsize+.001 and Ynew >= -Ysize-.001:
            DY = round((ymax-ymin)*1000.0)
            self.move_head_window_temporary([DX,-DY])
        else:
            pass
    
    def Move_LL(self,dummy=None):
        xmin,xmax,ymin,ymax = self.Get_Design_Bounds()
        if self.HomeUR.get():
            Xnew = self.laserX + (xmax-xmin)
            DX = round((xmax-xmin)*1000.0)
        else:
            Xnew = self.laserX
            DX = 0
            
        Ynew = self.laserY - (ymax-ymin)
        (Xsize,Ysize)=self.LASER_Size()
        if Xnew <= Xsize+.001 and Ynew >= -Ysize-.001:
            DY = round((ymax-ymin)*1000.0)
            self.move_head_window_temporary([DX,-DY])
        else:
            pass

    def Move_CC(self,dummy=None):
        xmin,xmax,ymin,ymax = self.Get_Design_Bounds()
        if self.HomeUR.get():
            Xnew = self.laserX + (xmax-xmin)/2.0 
            DX = round((xmax-xmin)/2.0*1000.0)
        else:
            Xnew = self.laserX + (xmax-xmin)/2.0 
            DX = round((xmax-xmin)/2.0*1000.0)

            
        Ynew = self.laserY - (ymax-ymin)/2.0
        (Xsize,Ysize)=self.LASER_Size()
        if Xnew <= Xsize+.001 and Ynew >= -Ysize-.001: 
            DY = round((ymax-ymin)/2.0*1000.0)
            self.move_head_window_temporary([DX,-DY])
        else:
            pass

    def Move_Arbitrary(self,MoveX,MoveY,dummy=None):
        if self.HomeUR.get():
            DX = -MoveX
        else:
            DX = MoveX
        DY = MoveY
        NewXpos = self.pos_offset[0]+DX
        NewYpos = self.pos_offset[1]+DY
        self.move_head_window_temporary([NewXpos,NewYpos])

    def Move_Arb_Step(self,dx,dy):
        if self.units.get()=="in":
            dx_inches = round(dx*1000)
            dy_inches = round(dy*1000)
        else:
            dx_inches = round(dx/25.4*1000)
            dy_inches = round(dy/25.4*1000)
        self.Move_Arbitrary( dx_inches,dy_inches )

    def Move_Arb_Right(self,dummy=None):
        JOG_STEP = float( self.jog_step.get() )
        self.Move_Arb_Step( JOG_STEP,0 )

    def Move_Arb_Left(self,dummy=None):
        JOG_STEP = float( self.jog_step.get() )
        self.Move_Arb_Step( -JOG_STEP,0 )

    def Move_Arb_Up(self,dummy=None):
        JOG_STEP = float( self.jog_step.get() )
        self.Move_Arb_Step( 0,JOG_STEP )

    def Move_Arb_Down(self,dummy=None):
        JOG_STEP = float( self.jog_step.get() )
        self.Move_Arb_Step( 0,-JOG_STEP )

    ####################################################

    def Move_Right(self,dummy=None):
        JOG_STEP = float( self.jog_step.get() )
        self.Rapid_Move( JOG_STEP,0 )

    def Move_Left(self,dummy=None):
        JOG_STEP = float( self.jog_step.get() )
        self.Rapid_Move( -JOG_STEP,0 )

    def Move_Up(self,dummy=None):
        JOG_STEP = float( self.jog_step.get() )
        self.Rapid_Move( 0,JOG_STEP )

    def Move_Down(self,dummy=None):
        JOG_STEP = float( self.jog_step.get() )
        self.Rapid_Move( 0,-JOG_STEP )

    def Rapid_Move(self,dx,dy):
        if self.units.get()=="in":
            dx_inches = round(dx,3)
            dy_inches = round(dy,3)
        else:
            dx_inches = round(dx/25.4,3)
            dy_inches = round(dy/25.4,3)

        if (self.HomeUR.get()):
            dx_inches = -dx_inches

        Xnew,Ynew = self.XY_in_bounds(dx_inches,dy_inches)
        dxmils = (Xnew - self.laserX)*1000.0
        dymils = (Ynew - self.laserY)*1000.0

        if self.k40 == None:
            self.laserX  = Xnew
            self.laserY  = Ynew
            self.menu_View_Refresh()
        elif self.Send_Rapid_Move(dxmils,dymils):
            self.laserX  = Xnew
            self.laserY  = Ynew
            self.menu_View_Refresh()
        

    def Send_Rapid_Move(self,dxmils,dymils):
        try:
            if self.k40 != None:
                if float(self.LaserXscale.get()) != 1.0 or float(self.LaserYscale.get()) != 1.0:
                    dxmils = int(round(dxmils *float(self.LaserXscale.get())))
                    dymils = int(round(dymils *float(self.LaserYscale.get())))
                self.k40.n_timeouts = 10
                self.k40.rapid_move(dxmils,dymils)
                return True
            else:
                return True
        #except StandardError as e:
        except Exception as e:
            msg1 = "Rapid Move Failed: "
            msg2 = "%s" %(e)
            if msg2 == "":
                formatted_lines = traceback.format_exc().splitlines()
            self.statusMessage.set((msg1+msg2).split("\n")[0] )
            self.statusbar.configure( bg = 'red' )
            debug_message(traceback.format_exc())
            return False       

    def update_gui(self, message=None, bgcolor='white'):
        if message!=None:
            self.statusMessage.set(message)
            self.statusbar.configure( bg = bgcolor )
        self.master.update()
        return True

    def set_gui(self,new_state="normal"):
        self.menuBar.entryconfigure("File"    , state=new_state)
        self.menuBar.entryconfigure("View"    , state=new_state)
        self.menuBar.entryconfigure("USB"     , state=new_state)
        self.menuBar.entryconfigure("Settings", state=new_state)
        self.menuBar.entryconfigure("Help"    , state=new_state)
        self.PreviewCanvas.configure(state=new_state)
        
        for w in self.master.winfo_children():
            try:
                w.configure(state=new_state)
            except:
                pass
        self.Stop_Button.configure(state="normal")
        self.statusbar.configure(state="normal")
        self.master.update()

    def Vector_Cut(self, output_filename=None):
        self.stop[0]=False
        self.set_gui("disabled")
        self.statusbar.configure( bg = 'green' )
        self.statusMessage.set("Vector Cut: Processing Vector Data.")
        self.master.update()
        if self.VcutData.ecoords!=[]:
            self.send_data("Vector_Cut", output_filename)
        else:
            self.statusbar.configure( bg = 'yellow' )
            self.statusMessage.set("No vector data to cut")
        self.set_gui("normal")
        
    def Vector_Eng(self, output_filename=None):
        self.stop[0]=False
        self.set_gui("disabled")
        self.statusbar.configure( bg = 'green' )
        self.statusMessage.set("Vector Engrave: Processing Vector Data.")
        self.master.update()
        if self.VengData.ecoords!=[]:
            self.send_data("Vector_Eng", output_filename)
        else:
            self.statusbar.configure( bg = 'yellow' )
            self.statusMessage.set("No vector data to engrave")
        self.set_gui("normal")

    def Raster_Eng(self, output_filename=None):
        self.stop[0]=False
        self.set_gui("disabled")
        self.statusbar.configure( bg = 'green' )
        self.statusMessage.set("Raster Engraving: Processing Image Data.")
        self.master.update()
        try:
            self.make_raster_coords()
            if self.RengData.ecoords!=[]:
                self.send_data("Raster_Eng", output_filename)
            else:
                self.statusbar.configure( bg = 'yellow' )
                self.statusMessage.set("No raster data to engrave")
        except Exception as e:
            msg1 = "Making Raster Data Stopped: "
            msg2 = "%s" %(e)
            self.statusMessage.set((msg1+msg2).split("\n")[0] )
            self.statusbar.configure( bg = 'red' )
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())
        self.set_gui("normal")

    def Raster_Vector_Eng(self, output_filename=None):
        self.stop[0]=False
        self.set_gui("disabled")
        self.statusbar.configure( bg = 'green' )
        self.statusMessage.set("Raster Engraving: Processing Image and Vector Data.")
        self.master.update()
        try:
            self.make_raster_coords()
            if self.RengData.ecoords!=[] or self.VengData.ecoords!=[]:
                self.send_data("Raster_Eng+Vector_Eng", output_filename)
            else:
                self.statusbar.configure( bg = 'yellow' )
                self.statusMessage.set("No data to engrave")
        except Exception as e:
            msg1 = "Preparing Data Stopped: "
            msg2 = "%s" %(e)
            self.statusMessage.set((msg1+msg2).split("\n")[0] )
            self.statusbar.configure( bg = 'red' )
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())
        self.set_gui("normal")


    def Vector_Eng_Cut(self, output_filename=None):
        self.stop[0]=False
        self.set_gui("disabled")
        self.statusbar.configure( bg = 'green' )
        self.statusMessage.set("Vector Cut: Processing Vector Data.")
        self.master.update()
        if self.VcutData.ecoords!=[] or self.VengData.ecoords!=[]:
            self.send_data("Vector_Eng+Vector_Cut", output_filename)
        else:
            self.statusbar.configure( bg = 'yellow' )
            self.statusMessage.set("No vector data.")
        self.set_gui("normal")

        
    def Raster_Vector_Cut(self, output_filename=None):
        self.stop[0]=False
        self.set_gui("disabled")
        self.statusbar.configure( bg = 'green' )
        self.statusMessage.set("Raster Engraving: Processing Image and Vector Data.")
        self.master.update()
        try:
            self.make_raster_coords()
            if self.RengData.ecoords!=[] or self.VengData.ecoords!=[] or self.VcutData.ecoords!=[]:
                self.send_data("Raster_Eng+Vector_Eng+Vector_Cut", output_filename)
            else:
                self.statusbar.configure( bg = 'yellow' )
                self.statusMessage.set("No data to engrave/cut")
        except Exception as e:
            msg1 = "Preparing Data Stopped: "
            msg2 = "%s" %(e)
            self.statusMessage.set((msg1+msg2).split("\n")[0] )
            self.statusbar.configure( bg = 'red' )
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())
        self.set_gui("normal")
        
        
    def Gcode_Cut(self, output_filename=None):
        self.stop[0]=False
        self.set_gui("disabled")
        self.statusbar.configure( bg = 'green' )
        self.statusMessage.set("G Code Cutting.")
        self.master.update()
        if self.GcodeData.ecoords!=[]:
            self.send_data("Gcode_Cut", output_filename)
        else:
            self.statusbar.configure( bg = 'yellow' )
            self.statusMessage.set("No g-code data to cut")
        self.set_gui("normal")


    ################################################################################
    def Sort_Paths(self,ecoords,i_loop=2):
        ##########################
        ###   find loop ends   ###
        ##########################
        Lbeg=[]
        Lend=[]
        if len(ecoords)>0:
            Lbeg.append(0)
            loop_old=ecoords[0][i_loop]
            for i in range(1,len(ecoords)):
                loop = ecoords[i][i_loop]
                if loop != loop_old:
                    Lbeg.append(i)
                    Lend.append(i-1)
                loop_old=loop
            Lend.append(i)

        #######################################################
        # Find new order based on distance to next beg or end #
        #######################################################
        order_out = []
        use_beg=0
        if len(ecoords)>0:
            order_out.append([Lbeg[0],Lend[0]])
        inext = 0
        total=len(Lbeg)
        for i in range(total-1):
            if use_beg==1:
                ii=Lbeg.pop(inext)
                Lend.pop(inext)
            else:
                ii=Lend.pop(inext)
                Lbeg.pop(inext)

            Xcur = ecoords[ii][0]
            Ycur = ecoords[ii][1]

            dx = Xcur - ecoords[ Lbeg[0] ][0]
            dy = Ycur - ecoords[ Lbeg[0] ][1]
            min_dist = dx*dx + dy*dy

            dxe = Xcur - ecoords[ Lend[0] ][0]
            dye = Ycur - ecoords[ Lend[0] ][1]
            min_diste = dxe*dxe + dye*dye

            inext=0
            inexte=0
            for j in range(1,len(Lbeg)):
                dx = Xcur - ecoords[ Lbeg[j] ][0]
                dy = Ycur - ecoords[ Lbeg[j] ][1]
                dist = dx*dx + dy*dy
                if dist < min_dist:
                    min_dist=dist
                    inext=j
                ###
                dxe = Xcur - ecoords[ Lend[j] ][0]
                dye = Ycur - ecoords[ Lend[j] ][1]
                diste = dxe*dxe + dye*dye
                if diste < min_diste:
                    min_diste=diste
                    inexte=j
                ###
            if min_diste < min_dist:
                inext=inexte
                order_out.append([Lend[inexte],Lbeg[inexte]])
                use_beg=1
            else:
                order_out.append([Lbeg[inext],Lend[inext]])
                use_beg=0
        ###########################################################
        return order_out
    
    #####################################################
    # determine if a point is inside a given polygon or not
    # Polygon is a list of (x,y) pairs.
    # http://www.ariel.com.au/a/python-point-int-poly.html
    #####################################################
    def point_inside_polygon(self,x,y,poly):
        n = len(poly)
        inside = -1
        p1x = poly[0][0]
        p1y = poly[0][1]
        for i in range(n+1):
            p2x = poly[i%n][0]
            p2y = poly[i%n][1]
            if y > min(p1y,p2y):
                if y <= max(p1y,p2y):
                    if x <= max(p1x,p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = inside * -1
            p1x,p1y = p2x,p2y

        return inside

    def optimize_paths(self,ecoords):
        order_out = self.Sort_Paths(ecoords)
        lastx=-999
        lasty=-999
        Acc=0.004
        cuts=[]

        for line in order_out:
            temp=line
            if temp[0] > temp[1]:
                step = -1
            else:
                step = 1

            loop_old = -1
            
            for i in range(temp[0],temp[1]+step,step):
                x1   = ecoords[i][0]
                y1   = ecoords[i][1]
                loop = ecoords[i][2]
                # check and see if we need to move to a new discontinuous start point
                if (loop != loop_old):
                    dx = x1-lastx
                    dy = y1-lasty
                    dist = sqrt(dx*dx + dy*dy)
                    if dist > Acc:
                        cuts.append([[x1,y1]])
                    else:
                        cuts[-1].append([x1,y1])
                else:
                    cuts[-1].append([x1,y1])
                lastx = x1
                lasty = y1
                loop_old = loop
        #####################################################
        # For each loop determine if other loops are inside #
        #####################################################
        Nloops=len(cuts)
        self.LoopTree=[]
        for iloop in range(Nloops):
            self.LoopTree.append([])
##            CUR_PCT=float(iloop)/Nloops*100.0
##            if (not self.batch.get()):
##                self.statusMessage.set('Determining Which Side of Loop to Cut: %d of %d' %(iloop+1,Nloops))
##                self.master.update()
            ipoly = cuts[iloop]
            ## Check points in other loops (could just check one) ##
            if ipoly != []:
                for jloop in range(Nloops):
                    if jloop != iloop:
                        inside = 0
                        inside = inside + self.point_inside_polygon(cuts[jloop][0][0],cuts[jloop][0][1],ipoly)
                        if inside > 0:
                            self.LoopTree[iloop].append(jloop)
        #####################################################
        for i in range(Nloops):
            lns=[]
            lns.append(i)
            self.remove_self_references(lns,self.LoopTree[i])

        self.order=[]
        self.loops = list(range(Nloops))
        for i in range(Nloops):
            if self.LoopTree[i]!=[]:
                self.addlist(self.LoopTree[i])
                self.LoopTree[i]=[]
            if self.loops[i]!=[]:
                self.order.append(self.loops[i])
                self.loops[i]=[]
        ecoords_out = []
        for i in self.order:
            line = cuts[i]
            for coord in line:
                ecoords_out.append([coord[0],coord[1],i])
        return ecoords_out
            
    def remove_self_references(self,loop_numbers,loops):
        for i in range(0,len(loops)):
            for j in range(0,len(loop_numbers)):
                if loops[i]==loop_numbers[j]:
                    loops.pop(i)
                    return
            if self.LoopTree[loops[i]]!=[]:
                loop_numbers.append(loops[i])
                self.remove_self_references(loop_numbers,self.LoopTree[loops[i]])

    def addlist(self,list):
        for i in list:
            try: #this try/except is a bad hack fix to a recursion error. It should be fixed properly later.
                if self.LoopTree[i]!=[]:
                    self.addlist(self.LoopTree[i]) #too many recursions here causes cmp error
                    self.LoopTree[i]=[]
            except:
                pass
            if self.loops[i]!=[]:
                self.order.append(self.loops[i])
                self.loops[i]=[]


    def mirror_rotate_vector_coords(self,coords):
        xmin = self.Design_bounds[0]
        xmax = self.Design_bounds[1]
        coords_rotate_mirror=[]
        
        for i in range(len(coords)):
            coords_rotate_mirror.append(coords[i][:])
            if self.mirror.get():
                coords_rotate_mirror[i][0]=xmin+xmax-coords_rotate_mirror[i][0]
            if self.rotate.get():
                x = coords_rotate_mirror[i][0]
                y = coords_rotate_mirror[i][1]
                coords_rotate_mirror[i][0] = -y
                coords_rotate_mirror[i][1] =  x
                
        return coords_rotate_mirror

    def scale_vector_coords(self,coords,startx,starty):
        Xscale = float(self.LaserXscale.get())
        Yscale = float(self.LaserYscale.get())
        coords_scale=[]
        if Xscale != 1.0 or Yscale != 1.0:
            for i in range(len(coords)):
                coords_scale.append(coords[i][:])
                x = coords_scale[i][0]
                y = coords_scale[i][1]
                coords_scale[i][0] = x*Xscale
                coords_scale[i][1] = y*Yscale
            scaled_startx = startx*Xscale
            scaled_starty = starty*Yscale
        else:
            coords_scale = coords
            scaled_startx = startx
            scaled_starty = starty

        return coords_scale,scaled_startx,scaled_starty
  
    def send_data(self,operation_type=None, output_filename=None):
        num_passes=0
        if self.k40 == None and output_filename == None:
            self.statusMessage.set("Laser Cutter is not Initialized...")
            self.statusbar.configure( bg = 'red' ) 
            return
        try:
            if self.units.get()=='in':
                feed_factor = 25.4/60.0
            else:
                feed_factor = 1.0
                
            if self.inputCSYS.get() and self.RengData.image == None:
                xmin,xmax,ymin,ymax = 0.0,0.0,0.0,0.0
            else:
                xmin,xmax,ymin,ymax = self.Get_Design_Bounds()
                
            self.move_head_window_temporary([0,0])
                        
            startx = xmin
            starty = ymax

            if self.HomeUR.get():
                FlipXoffset = abs(xmax-xmin)
                if self.rotate.get():
                    startx = -xmin
            else:
                FlipXoffset = 0

            
            Raster_Eng_data=[]
            Vector_Eng_data=[]
            Vector_Cut_data=[]
            G_code_Cut_data=[]
                        
            if (operation_type.find("Vector_Cut") > -1) and  (self.VcutData.ecoords!=[]):
                Feed_Rate = float(self.Vcut_feed.get())*feed_factor
                self.statusMessage.set("Vector Cut: Determining Cut Order....")
                self.master.update()
                if not self.VcutData.sorted and self.inside_first.get():
                    self.VcutData.set_ecoords(self.optimize_paths(self.VcutData.ecoords),data_sorted=True)
                self.statusMessage.set("Generating EGV data...")
                self.master.update()

                Vcut_coords = self.VcutData.ecoords
                if self.mirror.get() or self.rotate.get():
                    Vcut_coords = self.mirror_rotate_vector_coords(Vcut_coords)

                Vcut_coords,startx,starty = self.scale_vector_coords(Vcut_coords,startx,starty)
                Vector_Cut_egv_inst = egv(target=lambda s:Vector_Cut_data.append(s))   
                Vector_Cut_egv_inst.make_egv_data(
                                                Vcut_coords,                      \
                                                startX=startx,                    \
                                                startY=starty,                    \
                                                Feed = Feed_Rate,                 \
                                                board_name=self.board_name.get(), \
                                                Raster_step = 0,                  \
                                                update_gui=self.update_gui,       \
                                                stop_calc=self.stop,              \
                                                FlipXoffset=FlipXoffset
                                                )

            if (operation_type.find("Vector_Eng") > -1) and  (self.VengData.ecoords!=[]):
                Feed_Rate = float(self.Veng_feed.get())*feed_factor
                self.statusMessage.set("Vector Engrave: Determining Cut Order....")
                self.master.update()
                if not self.VengData.sorted and self.inside_first.get():
                    self.VengData.set_ecoords(self.optimize_paths(self.VengData.ecoords),data_sorted=True)
                self.statusMessage.set("Generating EGV data...")
                self.master.update()

                Veng_coords = self.VengData.ecoords
                if self.mirror.get() or self.rotate.get():
                    Veng_coords = self.mirror_rotate_vector_coords(Veng_coords)

                Veng_coords,startx,starty = self.scale_vector_coords(Veng_coords,startx,starty)
                Vector_Eng_egv_inst = egv(target=lambda s:Vector_Eng_data.append(s))
                Vector_Eng_egv_inst.make_egv_data(
                                                Veng_coords,                      \
                                                startX=startx,                    \
                                                startY=starty,                    \
                                                Feed = Feed_Rate,                 \
                                                board_name=self.board_name.get(), \
                                                Raster_step = 0,                  \
                                                update_gui=self.update_gui,       \
                                                stop_calc=self.stop,              \
                                                FlipXoffset=FlipXoffset
                                                )
                
            if (operation_type.find("Raster_Eng") > -1) and  (self.RengData.ecoords!=[]):
                Feed_Rate = float(self.Reng_feed.get())*feed_factor
                Raster_step = self.get_raster_step_1000in()
                if not self.engraveUP.get():
                    Raster_step = -Raster_step
                    
                raster_startx = 0
                raster_starty = float(self.LaserYscale.get())*starty

                self.statusMessage.set("Generating EGV data...")
                self.master.update()
                Raster_Eng_egv_inst = egv(target=lambda s:Raster_Eng_data.append(s))
                Raster_Eng_egv_inst.make_egv_data(
                                                self.RengData.ecoords,            \
                                                startX=raster_startx,             \
                                                startY=raster_starty,             \
                                                Feed = Feed_Rate,                 \
                                                board_name=self.board_name.get(), \
                                                Raster_step = Raster_step,        \
                                                update_gui=self.update_gui,       \
                                                stop_calc=self.stop,              \
                                                FlipXoffset=FlipXoffset
                                                )
                
                self.Reng=[]

            if (operation_type.find("Gcode_Cut") > -1) and (self.GcodeData.ecoords!=[]):
                self.statusMessage.set("Generating EGV data...")
                self.master.update()
                Gcode_coords = self.GcodeData.ecoords
                if self.mirror.get() or self.rotate.get():
                    Gcode_coords = self.mirror_rotate_vector_coords(Gcode_coords)

                Gcode_coords,startx,starty = self.scale_vector_coords(Gcode_coords,startx,starty)
                G_code_Cut_egv_inst = egv(target=lambda s:G_code_Cut_data.append(s))
                G_code_Cut_egv_inst.make_egv_data(
                                                Gcode_coords,                     \
                                                startX=startx,                    \
                                                startY=starty,                    \
                                                Feed = None,                      \
                                                board_name=self.board_name.get(), \
                                                Raster_step = 0,                  \
                                                update_gui=self.update_gui,       \
                                                stop_calc=self.stop,              \
                                                FlipXoffset=FlipXoffset
                                                )
                
            ### Join Resulting Data together ###
            data=[]
            data.append(ord("I"))
            if Raster_Eng_data!=[]:
                num_passes = int(self.Reng_passes.get())
                for k in range(num_passes):
                    if len(data)> 4:
                        data[-4]=ord("@")
                    data.extend(Raster_Eng_data)
            if Vector_Eng_data!=[]:
                num_passes = int(self.Veng_passes.get())
                for k in range(num_passes):
                    if len(data)> 4:
                        data[-4]=ord("@")
                    data.extend(Vector_Eng_data)
            if Vector_Cut_data!=[]:
                num_passes = int(self.Vcut_passes.get())
                for k in range(num_passes):
                    if len(data)> 4:
                        data[-4]=ord("@")
                    data.extend(Vector_Cut_data)
            if G_code_Cut_data!=[]:
                num_passes = int(self.Gcde_passes.get())
                for k in range(num_passes):
                    if len(data)> 4:
                        data[-4]=ord("@")
                    data.extend(G_code_Cut_data)
            if len(data)< 4:
                raise Exception("No laser data was generated.")    
                
            self.master.update()
            if output_filename != None:
                self.write_egv_to_file(data,output_filename)
            else:
                self.send_egv_data(data, 1, output_filename)
                self.menu_View_Refresh()
                
        except MemoryError as e:
            raise Exception("Memory Error:  Out of Memory.")
            debug_message(traceback.format_exc())
        
        except Exception as e:
            msg1 = "Sending Data Stopped: "
            msg2 = "%s" %(e)
            if msg2 == "":
                formatted_lines = traceback.format_exc().splitlines()
            self.statusMessage.set((msg1+msg2).split("\n")[0] )
            self.statusbar.configure( bg = 'red' )
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())

    def send_egv_data(self,data,num_passes=1,output_filename=None):        
        pre_process_CRC        = self.pre_pr_crc.get()
        if self.k40 != None:
            self.k40.timeout       = int(self.t_timeout.get())   
            self.k40.n_timeouts    = int(self.n_timeouts.get())
            if DEBUG:
                time_start = time()
            self.k40.send_data(data,self.update_gui,self.stop,num_passes,pre_process_CRC, wait_for_laser=True)
            if DEBUG:
                print(("Elapsed Time: %.2f" %(time()-time_start)))
        else:
            self.statusMessage.set("Laser is not initialized.")
            self.statusbar.configure( bg = 'yellow' )
            return
        self.menu_View_Refresh()
        
    ##########################################################################
    ##########################################################################
    def write_egv_to_file(self,data,fname):
        if len(data) == 0:
            raise Exception("No data available to write to file.")
        try:
            fout = open(fname,'w')
        except:
            raise Exception("Unable to open file ( %s ) for writing." %(fname))
        fout.write("Document type : LHYMICRO-GL file\n")
        fout.write("Creator-Software: K40 Whisperer\n")
        
        fout.write("\n")
        fout.write("%0%0%0%0%")
        for char_val in data:
            char = chr(char_val)
            fout.write("%s" %(char))
            
        #fout.write("\n")
        fout.close
        self.menu_View_Refresh()
        self.statusMessage.set("Data saved to: %s" %(fname))
        
    def Home(self, event=None):
        if self.k40 != None:
            self.k40.home_position()
        self.laserX  = 0.0
        self.laserY  = 0.0
        self.pos_offset = [0.0,0.0]
        self.menu_View_Refresh()

    def GoTo(self):
        xpos = float(self.gotoX.get())
        ypos = float(self.gotoY.get())
        if self.k40 != None:
            self.k40.home_position()
        self.laserX  = 0.0
        self.laserY  = 0.0
        self.Rapid_Move(xpos,ypos)
        self.menu_View_Refresh()  
        
    def Reset(self):
        if self.k40 != None:
            try:
                self.k40.reset_usb()
                self.statusMessage.set("USB Reset Succeeded")
            except:
                debug_message(traceback.format_exc())
                pass
            
    def Stop(self,event=None):
        line1 = "The K40 Whisperer is currently Paused."
        line2 = "Press \"OK\" to stop current action."
        line3 = "Press \"Cancel\" to resume."
        if message_ask_ok_cancel("Stop Laser Job.", "%s\n\n%s\n%s" %(line1,line2,line3)):
            self.stop[0]=True

    def Hide_Advanced(self,event=None):
        self.advanced.set(0)
        self.menu_View_Refresh()

    def Release_USB(self):
        if self.k40 != None:
            try:
                self.k40.release_usb()
                self.statusMessage.set("USB Release Succeeded")
            except:
                debug_message(traceback.format_exc())
                pass
            self.k40=None
        
    def Initialize_Laser(self,event=None):
        self.stop[0]=False
        self.Release_USB()
        self.k40=None
        self.move_head_window_temporary([0.0,0.0])      
        self.k40=K40_CLASS()
        try:
            self.k40.initialize_device()
            self.k40.say_hello()
            if self.init_home.get():
                self.Home()
            else:
                self.Unlock()
            
        #except StandardError as e:
        except Exception as e:
            error_text = "%s" %(e)
            if "BACKEND" in error_text.upper():
                error_text = error_text + " (libUSB driver not installed)"
            self.statusMessage.set("USB Error: %s" %(error_text))
            self.statusbar.configure( bg = 'red' )
            self.k40=None
            debug_message(traceback.format_exc())

        except:
            self.statusMessage.set("Unknown USB Error")
            self.statusbar.configure( bg = 'red' )
            self.k40=None
            debug_message(traceback.format_exc())
            
    def Unlock(self,event=None):
        if self.k40 != None:
            try:
                self.k40.unlock_rail()
                self.statusMessage.set("Rail Unlock Succeeded")
                self.statusbar.configure( bg = 'white' )
            except:
                self.statusMessage.set("Rail Unlock Failed.")
                self.statusbar.configure( bg = 'red' )
                debug_message(traceback.format_exc())
                pass
    
    ##########################################################################
    ##########################################################################
            
    def menu_File_Quit(self):
        if message_ask_ok_cancel("Exit", "Exiting...."):
            self.Quit_Click(None)

    def menu_View_Mirror_Refresh_Callback(self, varName, index, mode):
        self.RengData.reset_path()
        self.SCALE = 0
        self.menu_View_Refresh()

    def menu_View_inputCSYS_Refresh_Callback(self, varName, index, mode):
        self.move_head_window_temporary([0.0,0.0])
        self.SCALE = 0
        self.menu_View_Refresh()

    def menu_View_Refresh_Callback(self, varName, index, mode):
        self.SCALE = 0
        self.menu_View_Refresh()

    def menu_View_Refresh(self):
        try:
            app.master.title(title_text+"   "+ self.DESIGN_FILE)
        except:
            pass
        dummy_event = Event()
        dummy_event.widget=self.master
        self.Master_Configure(dummy_event,1)
        self.Plot_Data()
        xmin,xmax,ymin,ymax = self.Get_Design_Bounds()
        W = xmax-xmin
        H = ymax-ymin

        if self.units.get()=="in":
            X_display = self.laserX + self.pos_offset[0]/1000.0
            Y_display = self.laserY + self.pos_offset[1]/1000.0
            W_display = W
            H_display = H
            U_display = self.units.get()
        else:
            X_display = (self.laserX + self.pos_offset[0]/1000.0)*self.units_scale
            Y_display = (self.laserY + self.pos_offset[1]/1000.0)*self.units_scale
            W_display = W*self.units_scale
            H_display = H*self.units_scale
            U_display = self.units.get()
        if self.HomeUR.get():
            X_display = -X_display

        self.statusMessage.set(" Current Position: X=%.3f Y=%.3f    ( W X H )=( %.3f%s X %.3f%s ) "
                                %(X_display,
                                  Y_display,
                                  W_display,
                                  U_display,
                                  H_display,
                                  U_display))

        self.statusbar.configure( bg = 'white' )
        
    def menu_Mode_Change_Callback(self, varName, index, mode):
        self.menu_View_Refresh()

    def menu_Inside_First_Callback(self, varName, index, mode):
        if self.GcodeData.ecoords != []:
            if self.VcutData.sorted == True:
                self.menu_Reload_Design()
            elif self.VengData.sorted == True:
                self.menu_Reload_Design()
        

    def menu_Mode_Change(self):
        dummy_event = Event()
        dummy_event.widget=self.master
        self.Master_Configure(dummy_event,1)

    def menu_View_Recalculate(self):
        pass

    def menu_Help_About(self):
        
        about = "K40 Whisperer by Scorch.\n"
        about = about + "\163\143\157\162\143\150\100\163\143\157\162"
        about = about + "\143\150\167\157\162\153\163\056\143\157\155\n"
        about = about + "http://www.scorchworks.com/\n\n"
        try:
            version = "%d.%d.%d" %(sys.version_info.major,sys.version_info.minor,sys.version_info.micro)
        except:
            version = ""
        about = about + "Python "+version+" (%d bit)" %(struct.calcsize("P") * 8)
        message_box("About k40_whisperer",about)

    def menu_Help_Web(self):
        webbrowser.open_new(r"http://www.scorchworks.com/K40whisperer/k40whisperer.html")

    def menu_Help_Manual(self):
        webbrowser.open_new(r"http://www.scorchworks.com/K40whisperer/k40w_manual.html")

    def KEY_F1(self, event):
        self.menu_Help_About()

    def KEY_F2(self, event):
        self.GEN_Settings_Window()

    def KEY_F3(self, event):
        self.RASTER_Settings_Window()

    def KEY_F4(self, event):
        self.advanced.set(not self.advanced.get())
        self.menu_View_Refresh()

    def KEY_F5(self, event):
        self.menu_View_Refresh()

    def bindConfigure(self, event):
        if not self.initComplete:
            self.initComplete = 1
            self.menu_Mode_Change()

    def Master_Configure(self, event, update=0):
        if event.widget != self.master:
            return
        x = int(self.master.winfo_x())
        y = int(self.master.winfo_y())
        w = int(self.master.winfo_width())
        h = int(self.master.winfo_height())
        if (self.x, self.y) == (-1,-1):
            self.x, self.y = x,y
        if abs(self.w-w)>10 or abs(self.h-h)>10 or update==1:
            ###################################################
            #  Form changed Size (resized) adjust as required #
            ###################################################
            self.w=w
            self.h=h

            if True:                
                # Left Column #
                w_label=90
                w_entry=48
                w_units=52

                x_label_L=10
                x_entry_L=x_label_L+w_label+20-5
                x_units_L=x_entry_L+w_entry+2

                Yloc=15
                self.Initialize_Button.place (x=12, y=Yloc, width=100*2, height=23)
                Yloc=Yloc+33

                self.Open_Button.place (x=12, y=Yloc, width=100, height=40)
                self.Reload_Button.place(x=12+100, y=Yloc, width=100, height=40)                

                Yloc=Yloc+50
                self.separator1.place(x=x_label_L, y=Yloc,width=w_label+75+40, height=2)
                Yloc=Yloc+6
                self.Label_Position_Control.place(x=x_label_L, y=Yloc, width=w_label*2, height=21)

                Yloc=Yloc+25
                self.Home_Button.place (x=12, y=Yloc, width=100, height=23)
                self.UnLock_Button.place(x=12+100, y=Yloc, width=100, height=23)

                Yloc=Yloc+33
                self.Label_Step.place(x=x_label_L, y=Yloc, width=w_label, height=21)
                self.Label_Step_u.place(x=x_units_L, y=Yloc, width=w_units, height=21)
                self.Entry_Step.place(x=x_entry_L, y=Yloc, width=w_entry, height=23)

                ###########################################################################
                Yloc=Yloc+30
                bsz=40
                xoffst=35
                self.UL_Button.place    (x=xoffst+12      ,  y=Yloc, width=bsz, height=bsz)
                self.Up_Button.place    (x=xoffst+12+bsz  ,  y=Yloc, width=bsz, height=bsz)
                self.UR_Button.place    (x=xoffst+12+bsz*2,  y=Yloc, width=bsz, height=bsz)
                Yloc=Yloc+bsz
                self.Left_Button.place  (x=xoffst+12      ,y=Yloc, width=bsz, height=bsz)
                self.CC_Button.place    (x=xoffst+12+bsz  ,y=Yloc, width=bsz, height=bsz)
                self.Right_Button.place (x=xoffst+12+bsz*2,y=Yloc, width=bsz, height=bsz)
                Yloc=Yloc+bsz
                self.LL_Button.place    (x=xoffst+12      ,  y=Yloc, width=bsz, height=bsz)
                self.Down_Button.place  (x=xoffst+12+bsz  ,  y=Yloc, width=bsz, height=bsz)
                self.LR_Button.place    (x=xoffst+12+bsz*2,  y=Yloc, width=bsz, height=bsz)
            
                
                Yloc=Yloc+bsz
                ###########################################################################
                self.Label_GoToX.place(x=x_entry_L, y=Yloc, width=w_entry, height=23)
                self.Label_GoToY.place(x=x_units_L, y=Yloc, width=w_entry, height=23)
                Yloc=Yloc+25
                self.GoTo_Button.place (x=12, y=Yloc, width=100, height=23)
                self.Entry_GoToX.place(x=x_entry_L, y=Yloc, width=w_entry, height=23)
                self.Entry_GoToY.place(x=x_units_L, y=Yloc, width=w_entry, height=23)
                ###########################################################################
                            

                #From Bottom up
                BUinit = self.h-70
                Yloc = BUinit
                self.Stop_Button.place (x=12, y=Yloc, width=100*2, height=30)
                
                self.Stop_Button.configure(bg='light coral')
                Yloc=Yloc-10

                wadv       = 220 #200
                wadv_use   = wadv-20
                Xvert_sep  = 220
                Xadvanced  = Xvert_sep+10
                w_label_adv= wadv-80 #  110 w_entry

                if self.GcodeData.ecoords == []:
                    self.Grun_Button.place_forget()
                    self.Reng_Veng_Vcut_Button.place_forget()
                    self.Reng_Veng_Button.place_forget()
                    self.Veng_Vcut_Button.place_forget()

                    Yloc=Yloc-30
                    self.Vcut_Button.place      (x=12, y=Yloc, width=100, height=23)
                    self.Entry_Vcut_feed.place  (x=x_entry_L, y=Yloc, width=w_entry, height=23)
                    self.Label_Vcut_feed_u.place(x=x_units_L, y=Yloc, width=w_units, height=23)
                    Y_Vcut=Yloc

                    Yloc=Yloc-30
                    self.Veng_Button.place  (x=12, y=Yloc, width=100, height=23)
                    self.Entry_Veng_feed.place(  x=x_entry_L, y=Yloc, width=w_entry, height=23)
                    self.Label_Veng_feed_u.place(x=x_units_L, y=Yloc, width=w_units, height=23)
                    Y_Veng=Yloc
                    
                    Yloc=Yloc-30
                    self.Reng_Button.place  (x=12, y=Yloc, width=100, height=23)
                    self.Entry_Reng_feed.place(  x=x_entry_L, y=Yloc, width=w_entry, height=23)
                    self.Label_Reng_feed_u.place(x=x_units_L, y=Yloc, width=w_units, height=23)
                    Y_Reng=Yloc
                    
                    if self.comb_vector.get() or self.comb_engrave.get():
                        if self.comb_engrave.get():
                            self.Veng_Button.place_forget()                    
                            self.Reng_Button.place_forget()
                        if self.comb_vector.get():
                            self.Vcut_Button.place_forget()
                            self.Veng_Button.place_forget() 
                            
                        if self.comb_engrave.get():
                            if self.comb_vector.get():
                                self.Reng_Veng_Vcut_Button.place(x=12, y=Y_Reng, width=100, height=23*3+14)
                            else:
                                self.Reng_Veng_Button.place(x=12, y=Y_Reng, width=100, height=23*2+7)
                        elif self.comb_vector.get():
                            self.Veng_Vcut_Button.place(x=12, y=Y_Veng, width=100, height=23*2+7)
                   
                    
                else:
                    self.Vcut_Button.place_forget()
                    self.Entry_Vcut_feed.place_forget()
                    self.Label_Vcut_feed_u.place_forget()
                    
                    self.Veng_Button.place_forget()
                    self.Entry_Veng_feed.place_forget()
                    self.Label_Veng_feed_u.place_forget()
                    
                    self.Reng_Button.place_forget()
                    self.Entry_Reng_feed.place_forget()
                    self.Label_Reng_feed_u.place_forget()

                    self.Reng_Veng_Vcut_Button.place_forget()
                    self.Reng_Veng_Button.place_forget()
                    self.Veng_Vcut_Button.place_forget()
                    
                    Yloc=Yloc-30
                    self.Grun_Button.place  (x=12, y=Yloc, width=100*2, height=23)
                    
                
                Yloc=Yloc-15
                self.separator2.place(x=x_label_L, y=Yloc,width=w_label+75+40, height=2)
                # End Left Column #

                if self.advanced.get():
                   
                    self.PreviewCanvas.configure( width = self.w-240-wadv, height = self.h-50 )
                    self.PreviewCanvas_frame.place(x=220+wadv, y=10)
                    self.separator_vert.place(x=220, y=10,width=2, height=self.h-50)

                    adv_Yloc=15
                    self.Label_Advanced_column.place(x=Xadvanced, y=adv_Yloc, width=wadv_use, height=21)
                    adv_Yloc=adv_Yloc+25
                    self.separator_adv.place(x=Xadvanced, y=adv_Yloc,width=wadv_use, height=2)

                    adv_Yloc=adv_Yloc+15
                    self.Label_Halftone_adv.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                    self.Checkbutton_Halftone_adv.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=25, height=23)
                    
                    adv_Yloc=adv_Yloc+25
                    self.Label_Negate_adv.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                    self.Checkbutton_Negate_adv.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=25, height=23)

                    adv_Yloc=adv_Yloc+25
                    self.Label_Mirror_adv.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                    self.Checkbutton_Mirror_adv.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=25, height=23)

                    adv_Yloc=adv_Yloc+25
                    self.Label_Rotate_adv.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                    self.Checkbutton_Rotate_adv.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=25, height=23)

                    adv_Yloc=adv_Yloc+25
                    self.Label_inputCSYS_adv.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                    self.Checkbutton_inputCSYS_adv.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=25, height=23)

                    adv_Yloc=adv_Yloc+25
                    self.Label_Inside_First_adv.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                    self.Checkbutton_Inside_First_adv.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=25, height=23)
                   

                    adv_Yloc = BUinit
                    self.Hide_Adv_Button.place (x=Xadvanced, y=adv_Yloc, width=wadv_use, height=30)

                    if self.RengData.image != None:
                        self.Label_inputCSYS_adv.configure(state="disabled")
                        self.Checkbutton_inputCSYS_adv.place_forget()              
                    else:
                        self.Label_inputCSYS_adv.configure(state="normal")
                        
                    if self.GcodeData.ecoords == []:
                        adv_Yloc = adv_Yloc-40
                        self.Label_Vcut_passes.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                        self.Entry_Vcut_passes.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=w_entry, height=23)

                        adv_Yloc=adv_Yloc-30
                        self.Label_Veng_passes.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                        self.Entry_Veng_passes.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=w_entry, height=23)

                        adv_Yloc=adv_Yloc-30
                        self.Label_Reng_passes.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                        self.Entry_Reng_passes.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=w_entry, height=23)
                        self.Label_Gcde_passes.place_forget()
                        self.Entry_Gcde_passes.place_forget()


                       ####
                        adv_Yloc=adv_Yloc-15
                        self.separator_comb.place(x=Xadvanced-1, y=adv_Yloc, width=wadv_use, height=2)

                        adv_Yloc=adv_Yloc-25
                        self.Label_Comb_Vector_adv.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                        self.Checkbutton_Comb_Vector_adv.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=25, height=23)
                        
                        adv_Yloc=adv_Yloc-25
                        self.Label_Comb_Engrave_adv.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                        self.Checkbutton_Comb_Engrave_adv.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=25, height=23)
                        ####
                        
                    else:
                        adv_Yloc=adv_Yloc-40
                        self.Label_Gcde_passes.place(x=Xadvanced, y=adv_Yloc, width=w_label_adv, height=21)
                        self.Entry_Gcde_passes.place(x=Xadvanced+w_label_adv+2, y=adv_Yloc, width=w_entry, height=23)
                        self.Label_Vcut_passes.place_forget()
                        self.Entry_Vcut_passes.place_forget()
                        self.Label_Veng_passes.place_forget()
                        self.Entry_Veng_passes.place_forget()
                        self.Label_Reng_passes.place_forget()
                        self.Entry_Reng_passes.place_forget()

                else:
                    self.PreviewCanvas_frame.place_forget()
                    self.separator_vert.place_forget()
                    self.Label_Advanced_column.place_forget()
                    self.separator_adv.place_forget() 
                    self.Label_Halftone_adv.place_forget()
                    self.Checkbutton_Halftone_adv.place_forget()
                    self.Label_Mirror_adv.place_forget()
                    self.Checkbutton_Mirror_adv.place_forget()
                    self.Label_Rotate_adv.place_forget()
                    self.Label_Negate_adv.place_forget()
                    self.Checkbutton_Negate_adv.place_forget()
                    self.Checkbutton_Rotate_adv.place_forget()
                    self.Label_inputCSYS_adv.place_forget()
                    self.Checkbutton_inputCSYS_adv.place_forget()
                    self.Label_Inside_First_adv.place_forget()
                    self.Checkbutton_Inside_First_adv.place_forget()


 
                    self.separator_comb.place_forget()
                    self.Label_Comb_Engrave_adv.place_forget()
                    self.Checkbutton_Comb_Engrave_adv.place_forget()
                    self.Label_Comb_Vector_adv.place_forget()
                    self.Checkbutton_Comb_Vector_adv.place_forget()


                    self.Entry_Vcut_passes.place_forget()
                    self.Label_Vcut_passes.place_forget()
                    self.Entry_Veng_passes.place_forget()
                    self.Label_Veng_passes.place_forget()
                    self.Entry_Reng_passes.place_forget()
                    self.Label_Reng_passes.place_forget()
                    self.Label_Gcde_passes.place_forget()
                    self.Entry_Gcde_passes.place_forget()
                    self.Hide_Adv_Button.place_forget()
                    
                    self.PreviewCanvas.configure( width = self.w-240, height = self.h-50 )
                    self.PreviewCanvas_frame.place(x=Xvert_sep, y=10)
                    self.separator_vert.place_forget()

                self.Set_Input_States()
                
            self.Plot_Data()
            
    def Recalculate_RQD_Click(self, event):
        self.menu_View_Refresh()

    def Set_Input_States(self):
        pass
            
    def Set_Input_States_Event(self,event):
        self.Set_Input_States()

    def Set_Input_States_RASTER(self):
        if self.halftone.get():
            self.Label_Halftone_DPI.configure(state="normal")
            self.Halftone_DPI_OptionMenu.configure(state="normal")
            self.Label_Halftone_u.configure(state="normal")
            self.Label_bezier_M1.configure(state="normal")
            self.bezier_M1_Slider.configure(state="normal")
            self.Label_bezier_M2.configure(state="normal")
            self.bezier_M2_Slider.configure(state="normal")
            self.Label_bezier_weight.configure(state="normal")
            self.bezier_weight_Slider.configure(state="normal")
        else:
            self.Label_Halftone_DPI.configure(state="disabled")
            self.Halftone_DPI_OptionMenu.configure(state="disabled")
            self.Label_Halftone_u.configure(state="disabled")
            self.Label_bezier_M1.configure(state="disabled")
            self.bezier_M1_Slider.configure(state="disabled")
            self.Label_bezier_M2.configure(state="disabled")
            self.bezier_M2_Slider.configure(state="disabled")
            self.Label_bezier_weight.configure(state="disabled")
            self.bezier_weight_Slider.configure(state="disabled")

            
    def Set_Input_States_RASTER_Event(self,event):
        self.Set_Input_States_RASTER()

    def Imaging_Free(self,image_in,bg="#ffffff"):
        image_in = image_in.convert('L')
        wim,him = image_in.size
        image_out=PhotoImage(width=wim,height=him)
        pixel=image_in.load()
        if bg!=None:
            image_out.put(bg, to=(0,0,wim,him))
        for y in range(0,him):
            for x in range(0,wim):
                val=pixel[x,y]
                if val!=255:
                    image_out.put("#%02x%02x%02x" %(val,val,val),(x,y))
        return image_out

    ##########################################
    #        CANVAS PLOTTING STUFF           #
    ##########################################
    def Plot_Data(self):
        self.PreviewCanvas.delete(ALL)
        if (self.Check_All_Variables() > 0):
            return

        for seg in self.segID:
            self.PreviewCanvas.delete(seg)
        self.segID = []
        
        cszw = int(self.PreviewCanvas.cget("width"))
        cszh = int(self.PreviewCanvas.cget("height"))
        buff=10
        wc = float(cszw/2)
        hc = float(cszh/2)        
        
        maxx = float(self.LaserXsize.get()) / self.units_scale
        minx = 0.0
        maxy = 0.0
        miny = -float(self.LaserYsize.get()) / self.units_scale
        midx=(maxx+minx)/2
        midy=(maxy+miny)/2
        
                
        if self.inputCSYS.get() and self.RengData.image == None:
            xmin,xmax,ymin,ymax = 0.0,0.0,0.0,0.0
        else:
            xmin,xmax,ymin,ymax = self.Get_Design_Bounds()           
                
        if (self.HomeUR.get()):
            XlineShift = maxx - self.laserX - (xmax-xmin)
        else:
            XlineShift = self.laserX
        YlineShift = self.laserY    

        if min((xmax-xmin),(ymax-ymin)) > 0 and self.zoom2image.get():
            self.PlotScale = max((xmax-xmin)/(cszw-buff), (ymax-ymin)/(cszh-buff))
            x_lft =  minx / self.PlotScale - self.laserX / self.PlotScale + (cszw-(xmax-xmin)/self.PlotScale)/2
            x_rgt =  maxx / self.PlotScale - self.laserX / self.PlotScale + (cszw-(xmax-xmin)/self.PlotScale)/2
            y_bot = -miny / self.PlotScale + self.laserY / self.PlotScale + (cszh-(ymax-ymin)/self.PlotScale)/2
            y_top = -maxy / self.PlotScale + self.laserY / self.PlotScale + (cszh-(ymax-ymin)/self.PlotScale)/2
            self.segID.append( self.PreviewCanvas.create_rectangle(
                            x_lft, y_bot, x_rgt, y_top, fill="gray80", outline="gray80", width = 0) )
        else:
            self.PlotScale = max((maxx-minx)/(cszw-buff), (maxy-miny)/(cszh-buff))
            x_lft = cszw/2 + (minx-midx) / self.PlotScale
            x_rgt = cszw/2 + (maxx-midx) / self.PlotScale
            y_bot = cszh/2 + (maxy-midy) / self.PlotScale
            y_top = cszh/2 + (miny-midy) / self.PlotScale
            self.segID.append( self.PreviewCanvas.create_rectangle(
                            x_lft, y_bot, x_rgt, y_top, fill="gray80", outline="gray80", width = 0) )


        ######################################
        ###       Plot Raster Image        ###
        ######################################
        if self.RengData.image != None:
            if self.include_Reng.get():   
                try:
                    new_SCALE = (1.0/self.PlotScale)/self.input_dpi
                    if new_SCALE != self.SCALE:
                        self.SCALE = new_SCALE
                        nw=int(self.SCALE*self.wim)
                        nh=int(self.SCALE*self.him)
                        plot_im = self.RengData.image.convert("L")
                        
                        if self.negate.get():
                            plot_im = ImageOps.invert(plot_im)

                        if self.halftone.get() == False:
                            plot_im = plot_im.point(lambda x: 0 if x<128 else 255, '1')
                            plot_im = plot_im.convert("L")

                        if self.mirror.get():
                            plot_im = ImageOps.mirror(plot_im)

                        if self.rotate.get():
                            plot_im = plot_im.rotate(90,expand=True)
                            nh=int(self.SCALE*self.wim)
                            nw=int(self.SCALE*self.him)
                            
                        try:
                            self.UI_image = ImageTk.PhotoImage(plot_im.resize((nw,nh), Image.ANTIALIAS))
                        except:
                            debug_message("Imaging_Free Used.")
                            self.UI_image = self.Imaging_Free(plot_im.resize((nw,nh), Image.ANTIALIAS))
                except:
                    self.SCALE = 1
                    debug_message(traceback.format_exc())
                    
                self.Plot_Raster(self.laserX, self.laserY-.0005, x_lft,y_top,self.PlotScale,im=self.UI_image)
        else:
            self.UI_image = None


        ######################################
        ###       Plot Reng Coords         ###
        ######################################
        if self.include_Rpth.get() and self.RengData.ecoords!=[]:
            loop_old = -1
            scale = 1

            for line in self.RengData.ecoords:
                XY    = line
                x1    = (XY[0]-xmin)*scale
                y1    = (XY[1]-ymax)*scale

                loop  = XY[2]
                color = "black"
                # check and see if we need to move to a new discontinuous start point
                if (loop == loop_old):
                    self.Plot_Line(xold, yold, x1, y1, x_lft, y_top, XlineShift, YlineShift, self.PlotScale, color)
                loop_old = loop
                xold=x1
                yold=y1

            
        ######################################
        ###       Plot Veng Coords         ###
        ######################################
        if self.include_Veng.get():
            loop_old = -1
            scale=1

            plot_coords = self.VengData.ecoords
            if self.mirror.get() or self.rotate.get():
                plot_coords = self.mirror_rotate_vector_coords(plot_coords)
                
            for line in plot_coords:
                XY    = line
                x1    = (XY[0]-xmin)*scale
                y1    = (XY[1]-ymax)*scale
                loop  = XY[2]
                # check and see if we need to move to a new discontinuous start point
                if (loop == loop_old):
                    self.Plot_Line(xold, yold, x1, y1, x_lft, y_top, XlineShift, YlineShift, self.PlotScale, "blue")
                loop_old = loop
                xold=x1
                yold=y1

        ######################################
        ###       Plot Vcut Coords         ###
        ######################################
        if self.include_Vcut.get():
            loop_old = -1
            scale=1

            plot_coords = self.VcutData.ecoords
            if self.mirror.get() or self.rotate.get():
                    plot_coords = self.mirror_rotate_vector_coords(plot_coords)
                
            for line in plot_coords:
                XY    = line
                x1    = (XY[0]-xmin)*scale
                y1    = (XY[1]-ymax)*scale

                loop  = XY[2]
                # check and see if we need to move to a new discontinuous start point
                if (loop == loop_old):
                    self.Plot_Line(xold, yold, x1, y1, x_lft, y_top, XlineShift, YlineShift, self.PlotScale, "red")
                        
                    
                loop_old = loop
                xold=x1
                yold=y1

        ######################################
        ###       Plot Gcode Coords        ###
        ######################################
        if self.include_Gcde.get():  
            loop_old = -1
            scale=1

            plot_coords = self.GcodeData.ecoords
            if self.mirror.get() or self.rotate.get():
                    plot_coords = self.mirror_rotate_vector_coords(plot_coords)
                
            for line in plot_coords:
                XY    = line
                x1    = (XY[0]-xmin)*scale
                y1    = (XY[1]-ymax)*scale

                loop  = XY[2]
                # check and see if we need to move to a new discontinuous start point
                if (loop == loop_old):
                    self.Plot_Line(xold, yold, x1, y1, x_lft, y_top, XlineShift, YlineShift, self.PlotScale, "white")
                loop_old = loop
                xold=x1
                yold=y1
                


        ######################################            
        self.refreshTime()
        dot_col = "grey50"
        xoff = self.pos_offset[0]/1000.0
        yoff = self.pos_offset[1]/1000.0

        if abs(self.pos_offset[0])+abs(self.pos_offset[1]) > 0:
            head_offset=True
        else:
            head_offset=False
        
        self.Plot_circle(self.laserX+xoff,self.laserY+yoff,x_lft,y_top,self.PlotScale,dot_col,radius=5,cross_hair=head_offset)
        
    def Plot_Raster(self, XX, YY, Xleft, Ytop, PlotScale, im):
        if (self.HomeUR.get()):
            maxx = float(self.LaserXsize.get()) / self.units_scale
            xmin,xmax,ymin,ymax = self.Get_Design_Bounds()
            xplt = Xleft + ( maxx-XX-(xmax-xmin) )/PlotScale
        else:
            xplt = Xleft +  XX/PlotScale
            
        yplt = Ytop  - YY/PlotScale
        self.segID.append(
            self.PreviewCanvas.create_image(xplt, yplt, anchor=NW, image=self.UI_image,tags='LaserTag')
            )
        
    def Plot_circle(self, XX, YY, Xleft, Ytop, PlotScale, col, radius=0, cross_hair=False):
        circle_tags = ('LaserTag','LaserDot')
        if (self.HomeUR.get()):
            maxx = float(self.LaserXsize.get()) / self.units_scale
            xplt = Xleft + maxx/PlotScale - XX/PlotScale
        else:
            xplt = Xleft + XX/PlotScale
        yplt = Ytop  - YY/PlotScale


        if cross_hair:
            radius=radius*2
            leg = int(radius*.707)
            self.segID.append(
                self.PreviewCanvas.create_polygon(
                                                xplt-radius,
                                                yplt,
                                                xplt-leg,
                                                yplt+leg,
                                                xplt,
                                                yplt+radius,
                                                xplt+leg,
                                                yplt+leg,
                                                xplt+radius,
                                                yplt,
                                                xplt+leg,
                                                yplt-leg,
                                                xplt,
                                                yplt-radius,
                                                xplt-leg,
                                                yplt-leg,
                                                fill=col,  outline=col, width = 1, stipple='gray12',tags=circle_tags ))
           
            self.segID.append(
                self.PreviewCanvas.create_line( xplt-radius,
                                                yplt,
                                                xplt+radius,
                                                yplt,
                                                fill=col, capstyle="round", width = 1, tags=circle_tags ))
            self.segID.append(
                self.PreviewCanvas.create_line( xplt,
                                                yplt-radius,
                                                xplt,
                                                yplt+radius,
                                                fill=col, capstyle="round", width = 1, tags=circle_tags ))
        else:
            self.segID.append(
                self.PreviewCanvas.create_oval(
                                                xplt-radius,
                                                yplt-radius,
                                                xplt+radius,
                                                yplt+radius,
                                                fill=col,  outline=col, width = 0, stipple='gray50',tags=circle_tags ))


    def Plot_Line(self, XX1, YY1, XX2, YY2, Xleft, Ytop, XlineShift, YlineShift, PlotScale, col, thick=0):
        xplt1 = Xleft + (XX1 + XlineShift )/PlotScale 
        xplt2 = Xleft + (XX2 + XlineShift )/PlotScale
        yplt1 = Ytop  - (YY1 + YlineShift )/PlotScale
        yplt2 = Ytop  - (YY2 + YlineShift )/PlotScale
        
        self.segID.append(
            self.PreviewCanvas.create_line( xplt1,
                                            yplt1,
                                            xplt2,
                                            yplt2,
                                            fill=col, capstyle="round", width = thick, tags='LaserTag') )
        
    ################################################################################
    #                         Temporary Move Window                                #
    ################################################################################
    def move_head_window_temporary(self,new_pos_offset):
        dx_inches = round(new_pos_offset[0]/1000.0,3)
        dy_inches = round(new_pos_offset[1]/1000.0,3)
        Xnew,Ynew = self.XY_in_bounds(dx_inches,dy_inches,no_size=True)

        pos_offset_X = round((Xnew-self.laserX)*1000.0)
        pos_offset_Y = round((Ynew-self.laserY)*1000.0)
        new_pos_offset = [pos_offset_X,pos_offset_Y]        
        
        if self.inputCSYS.get() and self.RengData.image == None:
            new_pos_offset = [0,0]
            xdist = -self.pos_offset[0]
            ydist = -self.pos_offset[1]
        else:
            xdist = -self.pos_offset[0] + new_pos_offset[0]
            ydist = -self.pos_offset[1] + new_pos_offset[1]
            
        if self.k40 != None:
            if self.Send_Rapid_Move( xdist,ydist ):
                self.pos_offset = new_pos_offset
                self.menu_View_Refresh()
        else:      
            self.pos_offset = new_pos_offset
            self.menu_View_Refresh()
    
    ################################################################################
    #                         General Settings Window                              #
    ################################################################################
    def GEN_Settings_Window(self):
        gen_settings = Toplevel(width=560, height=460)
        gen_settings.grab_set() # Use grab_set to prevent user input in the main window
        gen_settings.focus_set()
        gen_settings.resizable(0,0)
        gen_settings.title('Settings')
        gen_settings.iconname("Settings")

        try:
            gen_settings.iconbitmap(bitmap="@emblem64")
        except:
            debug_message(traceback.format_exc())
            pass

        D_Yloc  = 6
        D_dY = 26
        xd_label_L = 12

        w_label=150
        w_entry=40
        w_units=35
        xd_entry_L=xd_label_L+w_label+10
        xd_units_L=xd_entry_L+w_entry+5

        #Radio Button
        D_Yloc=D_Yloc+D_dY
        self.Label_Units = Label(gen_settings,text="Units")
        self.Label_Units.place(x=xd_label_L, y=D_Yloc, width=113, height=21)
        self.Radio_Units_IN = Radiobutton(gen_settings,text="inch", value="in",
                                         width="100", anchor=W)
        self.Radio_Units_IN.place(x=w_label+22, y=D_Yloc, width=75, height=23)
        self.Radio_Units_IN.configure(variable=self.units, command=self.Entry_units_var_Callback )
        self.Radio_Units_MM = Radiobutton(gen_settings,text="mm", value="mm",
                                         width="100", anchor=W)
        self.Radio_Units_MM.place(x=w_label+110, y=D_Yloc, width=75, height=23)
        self.Radio_Units_MM.configure(variable=self.units, command=self.Entry_units_var_Callback )

        D_Yloc=D_Yloc+D_dY
        self.Label_init_home = Label(gen_settings,text="Home Upon Initialize")
        self.Label_init_home.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Checkbutton_init_home = Checkbutton(gen_settings,text="", anchor=W)
        self.Checkbutton_init_home.place(x=xd_entry_L, y=D_Yloc, width=75, height=23)
        self.Checkbutton_init_home.configure(variable=self.init_home)

        D_Yloc=D_Yloc+D_dY
        self.Label_Preprocess_CRC = Label(gen_settings,text="Preprocess CRC Data")
        self.Label_Preprocess_CRC.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Checkbutton_Preprocess_CRC = Checkbutton(gen_settings,text="", anchor=W)
        self.Checkbutton_Preprocess_CRC.place(x=xd_entry_L, y=D_Yloc, width=75, height=23)
        self.Checkbutton_Preprocess_CRC.configure(variable=self.pre_pr_crc)


        D_Yloc=D_Yloc+D_dY
        self.Label_Timeout = Label(gen_settings,text="USB Timeout")
        self.Label_Timeout.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Label_Timeout_u = Label(gen_settings,text="ms", anchor=W)
        self.Label_Timeout_u.place(x=xd_units_L, y=D_Yloc, width=w_units, height=21)
        self.Entry_Timeout = Entry(gen_settings,width="15")
        self.Entry_Timeout.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        self.Entry_Timeout.configure(textvariable=self.t_timeout)
        self.t_timeout.trace_variable("w", self.Entry_Timeout_Callback)
        self.entry_set(self.Entry_Timeout,self.Entry_Timeout_Check(),2)

        D_Yloc=D_Yloc+D_dY
        self.Label_N_Timeouts = Label(gen_settings,text="Number of Timeouts")
        self.Label_N_Timeouts.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Entry_N_Timeouts = Entry(gen_settings,width="15")
        self.Entry_N_Timeouts.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        self.Entry_N_Timeouts.configure(textvariable=self.n_timeouts)
        self.n_timeouts.trace_variable("w", self.Entry_N_Timeouts_Callback)
        self.entry_set(self.Entry_N_Timeouts,self.Entry_N_Timeouts_Check(),2)

        D_Yloc=D_Yloc+D_dY
        font_entry_width=215
        self.Label_Inkscape_Path = Label(gen_settings,text="Inkscape Executable")
        self.Label_Inkscape_Path.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Entry_Inkscape_Path = Entry(gen_settings,width="15")
        self.Entry_Inkscape_Path.place(x=xd_entry_L, y=D_Yloc, width=font_entry_width, height=23)
        self.Entry_Inkscape_Path.configure(textvariable=self.inkscape_path)
        self.Inkscape_Path = Button(gen_settings,text="Find Inkscape")
        self.Inkscape_Path.place(x=xd_entry_L+font_entry_width+10, y=D_Yloc, width=110, height=23)
        self.Inkscape_Path.bind("<ButtonRelease-1>", self.Inkscape_Path_Click)

        D_Yloc=D_Yloc+D_dY
        self.Label_no_com = Label(gen_settings,text="Home in Upper Right")
        self.Label_no_com.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Checkbutton_no_com = Checkbutton(gen_settings,text="", anchor=W)
        self.Checkbutton_no_com.place(x=xd_entry_L, y=D_Yloc, width=75, height=23)
        self.Checkbutton_no_com.configure(variable=self.HomeUR)
        self.HomeUR.trace_variable("w",self.menu_View_Refresh_Callback)        

        D_Yloc=D_Yloc+D_dY 
        self.Label_Board_Name      = Label(gen_settings,text="Board Name", anchor=CENTER )
        self.Board_Name_OptionMenu = OptionMenu(gen_settings, self.board_name,
                                            "LASER-M2",
                                            "LASER-M1",
                                            "LASER-M",
                                            "LASER-B2",
                                            "LASER-B1",
                                            "LASER-B",
                                            "LASER-A")
        self.Label_Board_Name.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Board_Name_OptionMenu.place(x=xd_entry_L, y=D_Yloc, width=w_entry*3, height=23)

        D_Yloc=D_Yloc+D_dY
        self.Label_Laser_Area_Width = Label(gen_settings,text="Laser Area Width")
        self.Label_Laser_Area_Width.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Label_Laser_Area_Width_u = Label(gen_settings,textvariable=self.units, anchor=W)
        self.Label_Laser_Area_Width_u.place(x=xd_units_L, y=D_Yloc, width=w_units, height=21)
        self.Entry_Laser_Area_Width = Entry(gen_settings,width="15")
        self.Entry_Laser_Area_Width.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        self.Entry_Laser_Area_Width.configure(textvariable=self.LaserXsize)
        self.LaserXsize.trace_variable("w", self.Entry_Laser_Area_Width_Callback)
        self.entry_set(self.Entry_Laser_Area_Width,self.Entry_Laser_Area_Width_Check(),2)

        D_Yloc=D_Yloc+D_dY
        self.Label_Laser_Area_Height = Label(gen_settings,text="Laser Area Height")
        self.Label_Laser_Area_Height.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Label_Laser_Area_Height_u = Label(gen_settings,textvariable=self.units, anchor=W)
        self.Label_Laser_Area_Height_u.place(x=xd_units_L, y=D_Yloc, width=w_units, height=21)
        self.Entry_Laser_Area_Height = Entry(gen_settings,width="15")
        self.Entry_Laser_Area_Height.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        self.Entry_Laser_Area_Height.configure(textvariable=self.LaserYsize)
        self.LaserYsize.trace_variable("w", self.Entry_Laser_Area_Height_Callback)
        self.entry_set(self.Entry_Laser_Area_Height,self.Entry_Laser_Area_Height_Check(),2)

        D_Yloc=D_Yloc+D_dY
        self.Label_Laser_X_Scale = Label(gen_settings,text="X Scale Factor")
        self.Label_Laser_X_Scale.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Entry_Laser_X_Scale = Entry(gen_settings,width="15")
        self.Entry_Laser_X_Scale.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        self.Entry_Laser_X_Scale.configure(textvariable=self.LaserXscale)
        self.LaserXscale.trace_variable("w", self.Entry_Laser_X_Scale_Callback)
        self.entry_set(self.Entry_Laser_X_Scale,self.Entry_Laser_X_Scale_Check(),2)

        D_Yloc=D_Yloc+D_dY
        self.Label_Laser_Y_Scale = Label(gen_settings,text="Y Scale Factor")
        self.Label_Laser_Y_Scale.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Entry_Laser_Y_Scale = Entry(gen_settings,width="15")
        self.Entry_Laser_Y_Scale.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        self.Entry_Laser_Y_Scale.configure(textvariable=self.LaserYscale)
        self.LaserYscale.trace_variable("w", self.Entry_Laser_Y_Scale_Callback)
        self.entry_set(self.Entry_Laser_Y_Scale,self.Entry_Laser_Y_Scale_Check(),2)
        

        D_Yloc=D_Yloc+D_dY+10
        self.Label_SaveConfig = Label(gen_settings,text="Configuration File")
        self.Label_SaveConfig.place(x=xd_label_L, y=D_Yloc, width=113, height=21)

        self.GEN_SaveConfig = Button(gen_settings,text="Save")
        self.GEN_SaveConfig.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=21, anchor="nw")
        self.GEN_SaveConfig.bind("<ButtonRelease-1>", self.Write_Config_File)
        
        ## Buttons ##
        gen_settings.update_idletasks()
        Ybut=int(gen_settings.winfo_height())-30
        Xbut=int(gen_settings.winfo_width()/2)

        self.GEN_Close = Button(gen_settings,text="Close",command=self.Close_Current_Window_Click)
        self.GEN_Close.place(x=Xbut, y=Ybut, width=130, height=30, anchor="center")

    ################################################################################
    #                          Raster Settings Window                              #
    ################################################################################
    def RASTER_Settings_Window(self):
        Wset=425+280
        Hset=330 #260
        raster_settings = Toplevel(width=Wset, height=Hset)
        raster_settings.grab_set() # Use grab_set to prevent user input in the main window
        raster_settings.focus_set()
        raster_settings.resizable(0,0)
        raster_settings.title('Raster Settings')
        raster_settings.iconname("Raster Settings")

        try:
            raster_settings.iconbitmap(bitmap="@emblem64")
        except:
            debug_message(traceback.format_exc())
            pass

        D_Yloc  = 6
        D_dY = 24
        xd_label_L = 12

        w_label=155
        w_entry=60
        w_units=35
        xd_entry_L=xd_label_L+w_label+10
        xd_units_L=xd_entry_L+w_entry+5



        D_Yloc=D_Yloc+D_dY
        self.Label_Rstep   = Label(raster_settings,text="Scanline Step", anchor=CENTER )
        self.Label_Rstep.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Label_Rstep_u = Label(raster_settings,text="in", anchor=W)
        self.Label_Rstep_u.place(x=xd_units_L, y=D_Yloc, width=w_units, height=21)
        self.Entry_Rstep   = Entry(raster_settings,width="15")
        self.Entry_Rstep.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        self.Entry_Rstep.configure(textvariable=self.rast_step)
        self.rast_step.trace_variable("w", self.Entry_Rstep_Callback)

        D_Yloc=D_Yloc+D_dY
        self.Label_EngraveUP = Label(raster_settings,text="Engrave Bottom Up")
        self.Checkbutton_EngraveUP = Checkbutton(raster_settings,text=" ", anchor=W)
        self.Checkbutton_EngraveUP.configure(variable=self.engraveUP)
        self.Label_EngraveUP.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Checkbutton_EngraveUP.place(x=w_label+22, y=D_Yloc, width=75, height=23)
        
        D_Yloc=D_Yloc+D_dY
        self.Label_Halftone = Label(raster_settings,text="Halftone (Dither)")
        self.Label_Halftone.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Checkbutton_Halftone = Checkbutton(raster_settings,text=" ", anchor=W, command=self.Set_Input_States_RASTER)
        self.Checkbutton_Halftone.place(x=w_label+22, y=D_Yloc, width=75, height=23)
        self.Checkbutton_Halftone.configure(variable=self.halftone)
        self.halftone.trace_variable("w", self.menu_View_Refresh_Callback)

        ############
        D_Yloc=D_Yloc+D_dY 
        self.Label_Halftone_DPI      = Label(raster_settings,text="Halftone Resolution", anchor=CENTER )
        self.Halftone_DPI_OptionMenu = OptionMenu(raster_settings, self.ht_size,
                                            "1000",
                                            "500",
                                            "333",
                                            "250",
                                            "200",
                                            "167",
                                            "143",
                                            "125")
        self.Label_Halftone_DPI.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Halftone_DPI_OptionMenu.place(x=xd_entry_L, y=D_Yloc, width=w_entry+30, height=23)


        self.Label_Halftone_u = Label(raster_settings,text="dpi", anchor=W)
        self.Label_Halftone_u.place(x=xd_units_L+30, y=D_Yloc, width=w_units, height=21)

        ############
        D_Yloc=D_Yloc+D_dY+5
        self.Label_bezier_M1  = Label(raster_settings,
                                text="Slope, Black (%.1f)"%(self.bezier_M1_default),
                                anchor=CENTER )
        self.bezier_M1_Slider = Scale(raster_settings, from_=1, to=50, resolution=0.1, \
                                orient=HORIZONTAL, variable=self.bezier_M1)
        self.bezier_M1_Slider.place(x=xd_entry_L, y=D_Yloc, width=(Wset-xd_entry_L-25-280 ))
        D_Yloc=D_Yloc+21
        self.Label_bezier_M1.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.bezier_M1.trace_variable("w", self.bezier_M1_Callback)
        
        D_Yloc=D_Yloc+D_dY-8
        self.Label_bezier_M2  = Label(raster_settings,
                                text="Slope, White (%.2f)"%(self.bezier_M2_default),
                                anchor=CENTER )
        self.bezier_M2_Slider = Scale(raster_settings, from_=0.0, to=1, \
                                orient=HORIZONTAL,resolution=0.01, variable=self.bezier_M2)
        self.bezier_M2_Slider.place(x=xd_entry_L, y=D_Yloc, width=(Wset-xd_entry_L-25-280 ))
        D_Yloc=D_Yloc+21
        self.Label_bezier_M2.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.bezier_M2.trace_variable("w", self.bezier_M2_Callback)

        D_Yloc=D_Yloc+D_dY-8
        self.Label_bezier_weight   = Label(raster_settings,
                                     text="Transition (%.1f)"%(self.bezier_M1_default),
                                     anchor=CENTER )
        self.bezier_weight_Slider = Scale(raster_settings, from_=0, to=10, resolution=0.1, \
                                    orient=HORIZONTAL, variable=self.bezier_weight)
        self.bezier_weight_Slider.place(x=xd_entry_L, y=D_Yloc, width=(Wset-xd_entry_L-25-280 ))
        D_Yloc=D_Yloc+21
        self.Label_bezier_weight.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.bezier_weight.trace_variable("w", self.bezier_weight_Callback)


        # Bezier Canvas
        self.Bezier_frame = Frame(raster_settings, bd=1, relief=SUNKEN)
        self.Bezier_frame.place(x=Wset-280, y=10, height=265, width=265)
        self.BezierCanvas = Canvas(self.Bezier_frame, background="white")
        self.BezierCanvas.pack(side=LEFT, fill=BOTH, expand=1)
        self.BezierCanvas.create_line( 5,260-0,260,260-255,fill="grey75", capstyle="round", width = 2, tags='perm')


        M1 = self.bezier_M1_default
        M2 = self.bezier_M2_default
        w  = self.bezier_weight_default
        num = 10
        x,y = self.generate_bezier(M1,M2,w,n=num)
        for i in range(0,num):
            self.BezierCanvas.create_line( 5+x[i],260-y[i],5+x[i+1],260-y[i+1],fill="grey85", stipple='gray25',\
                                           capstyle="round", width = 2, tags='perm')
        

        ## Buttons ##
        raster_settings.update_idletasks()
        Ybut=int(raster_settings.winfo_height())-30
        Xbut=int(raster_settings.winfo_width()/2)

        self.RASTER_Close = Button(raster_settings,text="Close",command=self.Close_Current_Window_Click)
        self.RASTER_Close.place(x=Xbut, y=Ybut, width=130, height=30, anchor="center")

        self.bezier_M1_Callback()
        self.Set_Input_States_RASTER()




    ################################################################################
    #                            EGV Send Window                                   #
    ################################################################################
    def EGV_Send_Window(self,EGV_filename):
        
        egv_send = Toplevel(width=400, height=180)
        egv_send.grab_set() # Use grab_set to prevent user input in the main window during calculations
        egv_send.resizable(0,0)
        egv_send.title('EGV Send')
        egv_send.iconname("EGV Send")
        try:
            egv_send.iconbitmap(bitmap="@emblem64")
        except:
            debug_message(traceback.format_exc())
            pass

        D_Yloc  = 0
        D_dY = 28
        xd_label_L = 12

        w_label=150
        w_entry=40
        w_units=35
        xd_entry_L=xd_label_L+w_label+10
        xd_units_L=xd_entry_L+w_entry+5

        D_Yloc=D_Yloc+D_dY
        self.Label_Preprocess_CRC = Label(egv_send,text="Preprocess CRC Data")
        self.Label_Preprocess_CRC.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Checkbutton_Preprocess_CRC = Checkbutton(egv_send,text="", anchor=W)
        self.Checkbutton_Preprocess_CRC.place(x=xd_entry_L, y=D_Yloc, width=75, height=23)
        self.Checkbutton_Preprocess_CRC.configure(variable=self.pre_pr_crc)

        D_Yloc=D_Yloc+D_dY
        self.Label_N_EGV_Passes = Label(egv_send,text="Number of EGV Passes")
        self.Label_N_EGV_Passes.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.Entry_N_EGV_Passes = Entry(egv_send,width="15")
        self.Entry_N_EGV_Passes.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        self.Entry_N_EGV_Passes.configure(textvariable=self.n_egv_passes)
        self.n_egv_passes.trace_variable("w", self.Entry_N_EGV_Passes_Callback)
        self.entry_set(self.Entry_N_EGV_Passes,self.Entry_N_EGV_Passes_Check(),2)

        D_Yloc=D_Yloc+D_dY
        font_entry_width=215
        self.Label_Inkscape_Path = Label(egv_send,text="EGV File:")
        self.Label_Inkscape_Path.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)

        EGV_Name = os.path.basename(EGV_filename)
        self.Label_Inkscape_Path = Label(egv_send,text=EGV_Name,anchor="w") #,bg="yellow")
        self.Label_Inkscape_Path.place(x=xd_entry_L, y=D_Yloc, width=200, height=21,anchor="nw")
        
        ## Buttons ##
        egv_send.update_idletasks()
        Ybut=int(egv_send.winfo_height())-30
        Xbut=int(egv_send.winfo_width()/2)

        self.EGV_Close = Button(egv_send,text="Cancel",command=self.Close_Current_Window_Click)
        self.EGV_Close.place(x=Xbut, y=Ybut, width=130, height=30, anchor="e")


        def Close_and_Send_Click():
            win_id=self.grab_current()
            win_id.destroy()
            self.Open_EGV(EGV_filename, n_passes=int(self.n_egv_passes.get()) )
            
        self.EGV_Send = Button(egv_send,text="Send EGV Data",command=Close_and_Send_Click)
        self.EGV_Send.place(x=Xbut, y=Ybut, width=130, height=30, anchor="w")
        ################################################################################
        
        
################################################################################
#             Function for outputting messages to different locations          #
#            depending on what options are enabled                             #
################################################################################
def fmessage(text,newline=True):
    global QUIET
    if (not QUIET):
        if newline==True:
            try:
                sys.stdout.write(text)
                sys.stdout.write("\n")
                debug_message(traceback.format_exc())
            except:
                debug_message(traceback.format_exc())
                pass
        else:
            try:
                sys.stdout.write(text)
                debug_message(traceback.format_exc())
            except:
                debug_message(traceback.format_exc())
                pass

################################################################################
#                               Message Box                                    #
################################################################################
def message_box(title,message):
    title = "%s (K40 Whisperer V%s)" %(title,version)
    if VERSION == 3:
        tkinter.messagebox.showinfo(title,message)
    else:
        tkMessageBox.showinfo(title,message)
        pass

################################################################################
#                          Message Box ask OK/Cancel                           #
################################################################################
def message_ask_ok_cancel(title, mess):
    if VERSION == 3:
        result=tkinter.messagebox.askokcancel(title, mess)
    else:
        result=tkMessageBox.askokcancel(title, mess)
    return result

################################################################################
#                         Debug Message Box                                    #
################################################################################
def debug_message(message):
    global DEBUG
    title = "Debug Message"
    if DEBUG:
        if VERSION == 3:
            tkinter.messagebox.showinfo(title,message)
        else:
            tkMessageBox.showinfo(title,message)
            pass

################################################################################
#                         Choose Units Dialog                                  #
################################################################################
if VERSION < 3:
    import tkSimpleDialog
else:
    import tkinter.simpledialog as tkSimpleDialog

class UnitsDialog(tkSimpleDialog.Dialog):
    def body(self, master):
        self.resizable(0,0)
        self.title('Units')
        self.iconname("Units")

        try:
            self.iconbitmap(bitmap="@emblem64")
        except:
            pass
        
        self.uom = StringVar()
        self.uom.set("Millimeters")

        Label(master, text="Select DXF Import Units:").grid(row=0)
        Radio_Units_IN = Radiobutton(master,text="Inches",        value="Inches")
        Radio_Units_MM = Radiobutton(master,text="Millimeters",   value="Millimeters")
        Radio_Units_CM = Radiobutton(master,text="Centimeters",   value="Centimeters")
        
        Radio_Units_IN.grid(row=1, sticky=W)
        Radio_Units_MM.grid(row=2, sticky=W)
        Radio_Units_CM.grid(row=3, sticky=W)

        Radio_Units_IN.configure(variable=self.uom)
        Radio_Units_MM.configure(variable=self.uom)
        Radio_Units_CM.configure(variable=self.uom)

    def apply(self):
        self.result = self.uom.get()
        return 



################################################################################
#                          Startup Application                                 #
################################################################################
    
root = Tk()
app = Application(root)
app.master.title(title_text)
app.master.iconname("K40")
app.master.minsize(800,560) #800x600 min

try:
    try:
        app.master.iconbitmap(r'emblem')
    except:
        app.master.iconbitmap(bitmap="@emblem64")
except:
    pass

if LOAD_MSG != "":
    message_box("K40 Whisperer",LOAD_MSG)
debug_message("Debuging is turned on.")

root.mainloop()
