#!/usr/bin/env python 
'''
Copyright (C) 2018 Scorch www.scorchworks.com
Derived from dxf_outlines.py by Aaron Spike and Alvin Penner

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

# standard library
import math
import tempfile, os, sys, shutil

import zipfile
import re
# local library
import inkex
import simplestyle
import simpletransform
import cubicsuperpath
import cspsubdiv
import traceback

from PIL import Image
Image.MAX_IMAGE_PIXELS = None

from lxml import etree

try:
    inkex.localize()
except:
    print("localize failed")
    pass

#### Subprocess timout stuff ######
from subprocess import Popen, PIPE
from threading import Timer
def run_external(cmd, timeout_sec):
    FLAG=[True]
    try:
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    except Exception as e:
        raise Exception("\n%s\n\nExecutable Path:\n%s" %(e,cmd[0]))
    kill_proc = lambda p: kill_sub_process(p,timeout_sec, FLAG)
    timer = Timer(timeout_sec, kill_proc, [proc])
    try:
        timer.start()
        stdout,stderr = proc.communicate()
    finally:
        timer.cancel()
    if not FLAG[0]:
        raise Exception("\nInkscape sub-process terminated after %d seconds." %(timeout_sec))
        
def kill_sub_process(p,timeout_sec, FLAG):
    FLAG[0]=False
    p.kill()

##################################
class SVG_TEXT_EXCEPTION(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class CSS_value_class():
    def __init__(self,type_name,value):
        type_name_list = type_name.split('.')
        try:
            self.object_type = type_name_list[0]
        except:
            self.object_type = ""

        try:
            self.value_name  = type_name_list[1]
        except:
            self.value_name  = ""
        self.data_string = value


class CSS_values_class():
    def __init__(self):
        self.CSS_value_list = []

    def add(self,type_name,value):
        self.CSS_value_list.append(CSS_value_class(type_name,value))

    def get_css_value(self,tag_type,class_val):
        value = ""
        for entry in self.CSS_value_list:
            if entry.object_type == "":
                if entry.value_name  == class_val:
                    value = entry.data_string
            if entry.object_type == tag_type:
                if entry.value_name  == class_val:
                    value = entry.data_string
                    break
        return value


class SVG_READER(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.flatness = 0.01
        self.image_dpi = 1000
        self.inscape_exe_list = []
        self.inscape_exe_list.append("C:\\Program Files\\Inkscape\\inkscape.exe")
        self.inscape_exe_list.append("C:\\Program Files (x86)\\Inkscape\\inkscape.exe")
        self.inscape_exe_list.append("/usr/bin/inkscape")
        self.inscape_exe_list.append("/usr/local/bin/inkscape")
        self.inscape_exe_list.append("/Applications/Inkscape.app/Contents/Resources/bin/inkscape")
        self.inscape_exe = None
        self.lines =[]
        self.Cut_Type = {}
        self.Xsize=40
        self.Ysize=40
        self.raster   = True

        self.raster_PIL = None
        self.cut_lines = []
        self.eng_lines = []
        self.id_cnt = 0
        
        self.png_area = "--export-area-page"
        self.timout = 180 #timeout time for external calls to Inkscape in seconds 
              
        self.layers = ['0']
        self.layer = '0'
        self.layernames = []
        self.txt2paths = False
        self.CSS_values = CSS_values_class()
        
    def set_inkscape_path(self,PATH):
        if PATH!=None:
            self.inscape_exe_list.insert(0,PATH)
        for location in self.inscape_exe_list:
            if ( os.path.isfile( location ) ):
                self.inscape_exe=location
                break
        
    def colmod(self,r,g,b,path_id):
        changed=False
        delta = 10
        # Check if the color is Red (or close to it)
        if (r >= 255-delta) and (g <= delta) and (b <= delta):
            self.Cut_Type[path_id]="cut"
            (r,g,b) = (255,255,255)
            changed=True
        # Check if the color is Blue (or close to it)
        elif (r <= delta) and (g <= delta) and (b >= 255-delta):
            self.Cut_Type[path_id]="engrave"
            (r,g,b) = (255,255,255)
            changed=True
        else:
            self.Cut_Type[path_id]="raster"
            changed=False
        color_out = '#%02x%02x%02x' %(r,g,b)
        return (color_out, changed)
        

    def process_shape(self, node, mat, group_stroke = None):
        #################################
        ### Determine the shape type  ###
        #################################
        try:
            i = node.tag.find('}')
            if i >= 0:
                tag_type = node.tag[i+1:]
        except:
            tag_type=""
        
        ##############################################
        ### Set a unique identifier for each shape ###
        ##############################################
        self.id_cnt=self.id_cnt+1
        path_id = "ID%d"%(self.id_cnt)
        sw_flag = False
        changed = False
        #######################################
        ### Handle references to CSS data   ###
        #######################################
        class_val = node.get('class')
        if class_val:
            css_data = ""
            for cv in class_val.split(' '):
                if css_data!="":
                    css_data = self.CSS_values.get_css_value(tag_type,cv)+";"+css_data
                else:
                    css_data = self.CSS_values.get_css_value(tag_type,cv)
                
            # Remove the reference to the CSS data 
            del node.attrib['class']

            # Check if a style entry already exists. If it does
            # append the the existing style data to the CSS data
            # otherwise create a new style entry.
            if node.get('style'):
                if css_data!="":
                    css_data = css_data + ";" + node.get('style')
                    node.set('style', css_data)
            else:
                node.set('style', css_data)

        style   = node.get('style')
        self.Cut_Type[path_id]="raster" # Set default type to raster

        text_message_warning = "SVG File with Color Coded Text Outlines Found: (i.e. Blue: engrave/ Red: cut)"
        line1 = "SVG File with color coded text outlines found (i.e. Blue: engrave/ Red: cut)."
        line2 = "Automatic conversion to paths failed: Try upgrading to Inkscape .90 or later"
        line3 = "To convert manually in Inkscape: select the text then select \"Path\"-\"Object to Path\" in the menu bar."
        text_message_fatal  = "%s\n\n%s\n\n%s" %(line1,line2,line3)
        
        ##############################################
        ### Handle 'style' data outside of style   ###
        ##############################################
        stroke_outside = node.get('stroke')
        if not stroke_outside:
            stroke_outside = group_stroke
        if stroke_outside:
            stroke_width_outside = node.get('stroke-width')
            
            col = stroke_outside
            col= col.strip()
            if simplestyle.isColor(col):
                c=simplestyle.parseColor(col)
                (new_val,changed)=self.colmod(c[0],c[1],c[2],path_id)
            else:
                new_val = col
            if changed:
                node.set('stroke',new_val)
                node.set('stroke-width',"0.0")
                sw_flag = True

            if sw_flag == True:
                if node.tag == inkex.addNS('text','svg') or node.tag == inkex.addNS('flowRoot','svg'):
                    if (self.txt2paths==False):
                        raise SVG_TEXT_EXCEPTION(text_message_warning)
                    else:
                        raise Exception(text_message_fatal)

        ##############################################
        ### Handle 'style' data                    ###
        ##############################################
        if style:
            declarations = style.split(';')
            i_sw = -1
            
            sw_prop = 'stroke-width'
            for i,decl in enumerate(declarations):
                parts = decl.split(':', 2)
                if len(parts) == 2:
                    (prop, col) = parts
                    prop = prop.strip().lower()
                    #if prop in color_props:
                    if prop == sw_prop:
                        i_sw = i
                    if prop == 'stroke':
                        col= col.strip()
                        if simplestyle.isColor(col):
                            c=simplestyle.parseColor(col)
                            (new_val,changed)=self.colmod(c[0],c[1],c[2],path_id)
                        else:
                            new_val = col
                        if changed:
                            declarations[i] = prop + ':' + new_val
                            sw_flag = True
            if sw_flag == True:
                if node.tag == inkex.addNS('text','svg') or node.tag == inkex.addNS('flowRoot','svg'):
                    if (self.txt2paths==False):
                        raise SVG_TEXT_EXCEPTION(text_message_warning)
                    else:
                        raise Exception(text_message_fatal)

                if i_sw != -1:
                    declarations[i_sw] = sw_prop + ':' + "0.0"
                else:
                    declarations.append(sw_prop + ':' + "0.0")
            node.set('style', ';'.join(declarations))
        ##############################################

        #####################################################
        ### If vector data was found save the path data   ###
        #####################################################
        if changed:
            if node.tag == inkex.addNS('path','svg'):
                d = node.get('d')
                if not d:
                    return
                p = cubicsuperpath.parsePath(d)
            elif node.tag == inkex.addNS('rect','svg'):
                x = float(node.get('x'))
                y = float(node.get('y'))
                width = float(node.get('width'))
                height = float(node.get('height'))
                rx = 0.0
                ry = 0.0
                if node.get('rx'):
                    rx=float(node.get('rx'))
                if node.get('ry'):
                    ry=float(node.get('ry'))
                    
                if max(rx,ry) > 0.0:
                    if rx==0.0 or ry==0.0:
                        rx = max(rx,ry)
                        ry = rx
                    Rxmax = abs(width)/2.0
                    Rymax = abs(height)/2.0
                    rx = min(rx,Rxmax)
                    ry = min(ry,Rymax)
                    L1 = "M %f,%f %f,%f "      %(x+rx       , y          , x+width-rx , y          )
                    C1 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x+width    , y+ry       )
                    L2 = "M %f,%f %f,%f "      %(x+width    , y+ry       , x+width    , y+height-ry)
                    C2 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x+width-rx , y+height   )
                    L3 = "M %f,%f %f,%f "      %(x+width-rx , y+height   , x+rx       , y+height   )
                    C3 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x          , y+height-ry)
                    L4 = "M %f,%f %f,%f "      %(x          , y+height-ry, x          , y+ry       )
                    C4 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x+rx       , y          )
                    d =  L1 + C1 + L2 + C2 + L3 + C3 + L4 + C4    
                else:
                    d = "M %f,%f %f,%f %f,%f %f,%f Z" %(x,y, x+width,y,  x+width,y+height, x,y+height) 
                p = cubicsuperpath.parsePath(d)
                
            elif node.tag == inkex.addNS('circle','svg'):
                cx = float(node.get('cx') )
                cy = float(node.get('cy'))
                r  = float(node.get('r'))
                d  = "M %f,%f A   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f Z" %(cx+r,cy, r,r,cx,cy+r,  r,r,cx-r,cy,  r,r,cx,cy-r, r,r,cx+r,cy)
                p = cubicsuperpath.parsePath(d)
            
            elif node.tag == inkex.addNS('ellipse','svg'):
                cx = float(node.get('cx')) 
                cy = float(node.get('cy'))
                rx = float(node.get('rx'))
                ry = float(node.get('ry'))
                d  = "M %f,%f A   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f Z" %(cx+rx,cy, rx,ry,cx,cy+ry,  rx,ry,cx-rx,cy,  rx,ry,cx,cy-ry, rx,ry,cx+rx,cy)
                p = cubicsuperpath.parsePath(d)
                
            elif (node.tag == inkex.addNS('polygon','svg')) or (node.tag == inkex.addNS('polyline','svg')):
                points = node.get('points')
                if not points:
                    return
               
                points = points.replace(',', ' ')
                while points.find('  ') > -1:
                    points = points.replace('  ', ' ')
                    
                points = points.strip().split(" ")
                d = "M "
                for i in range(0,len(points),2):
                    x = float(points[i])
                    y = float(points[i+1])
                    d = d + "%f,%f " %(x,y)

                #Close the loop if it is a ploygon
                if node.tag == inkex.addNS('polygon','svg'):
                    d = d + "Z"
                p = cubicsuperpath.parsePath(d)

            elif node.tag == inkex.addNS('line','svg'):
                x1 = float(node.get('x1')) 
                y1 = float(node.get('y1'))
                x2 = float(node.get('x2'))
                y2 = float(node.get('y2'))
                d = "M "
                d = "M %f,%f %f,%f" %(x1,y1,x2,y2)
                p = cubicsuperpath.parsePath(d)          
            else:
                #print("something was ignored")
                #print(node.tag)
                return
            
            trans = node.get('transform')
            if trans:
                mat = simpletransform.composeTransform(mat, simpletransform.parseTransform(trans))
            simpletransform.applyTransformToPath(mat, p)
            
            ##########################################
            ## Break Curves down into small lines  ###
            ##########################################
            f = self.flatness
            is_flat = 0
            while is_flat < 1:
                try:
                    cspsubdiv.cspsubdiv(p, f)
                    is_flat = 1
                except IndexError:
                    break
                except:
                    f += 0.1
                    if f>2 :
                      break
                      #something has gone very wrong.
            ##########################################
            rgb=(0,0,0)
            for sub in p:
                for i in range(len(sub)-1):
                    x1 = sub[i][1][0]
                    y1 = sub[i][1][1]
                    x2 = sub[i+1][1][0]
                    y2 = sub[i+1][1][1]
                    self.lines.append([x1,y1,x2,y2,rgb,path_id])
        #####################################################
        ### End of saving the vector path data            ###
        #####################################################
                
        
    def process_clone(self, node):
        trans = node.get('transform')
        x = node.get('x')
        y = node.get('y')
        mat = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        if trans:
            mat = simpletransform.composeTransform(mat, simpletransform.parseTransform(trans))
        if x:
            mat = simpletransform.composeTransform(mat, [[1.0, 0.0, float(x)], [0.0, 1.0, 0.0]])
        if y:
            mat = simpletransform.composeTransform(mat, [[1.0, 0.0, 0.0], [0.0, 1.0, float(y)]])
        # push transform
        if trans or x or y:
            self.groupmat.append(simpletransform.composeTransform(self.groupmat[-1], mat))
        # get referenced node
        refid = node.get(inkex.addNS('href','xlink'))
        refnode = self.getElementById(refid[1:])
        if refnode is not None:
            if refnode.tag == inkex.addNS('g','svg') or refnode.tag == inkex.addNS('switch','svg'):
                self.process_group(refnode)
            elif refnode.tag == inkex.addNS('use', 'svg'):
                self.process_clone(refnode)
            else:
                self.process_shape(refnode, self.groupmat[-1])
        # pop transform
        if trans or x or y:
            self.groupmat.pop()

    def process_group(self, group):
        ##############################################
        ### Get color set at group level
        stroke_group = group.get('stroke')
        ##############################################
        ### Handle 'style' data                   
        style = group.get('style')
        if style:
            declarations = style.split(';')
            for i,decl in enumerate(declarations):
                parts = decl.split(':', 2)
                if len(parts) == 2:
                    (prop, col) = parts
                    prop = prop.strip().lower()
                    if prop == 'stroke':
                        stroke_group = col.strip()
        ##############################################
        
        if group.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
            style = group.get('style')
            if style:
                style = simplestyle.parseStyle(style)
                if 'display' in style:   
                    if style['display'] == 'none':
                        return
            layer = group.get(inkex.addNS('label', 'inkscape'))
              
            layer = layer.replace(' ', '_')
            if layer in self.layers:
                self.layer = layer
        trans = group.get('transform')
        if trans:
            self.groupmat.append(simpletransform.composeTransform(self.groupmat[-1], simpletransform.parseTransform(trans)))
        for node in group:
            if node.tag == inkex.addNS('g','svg') or  node.tag == inkex.addNS('switch','svg'):
                self.process_group(node)
            elif node.tag == inkex.addNS('use', 'svg'):
                self.process_clone(node)
            elif node.tag == inkex.addNS('defs', 'svg'):
                for sub in node:
                    if sub.tag == inkex.addNS('style','svg'):
                        self.parse_css(sub.text)
            else:
                self.process_shape(node, self.groupmat[-1], group_stroke = stroke_group)
        if trans:
            self.groupmat.pop()

    def parse_css(self,css_string):
        name_list=[]
        value_list=[]
        name=""
        value=""
        i=0
        while i < len(css_string):
            c=css_string[i]
            if c=="{":
                i=i+1
                while i < len(css_string):
                    c=css_string[i]
                    i=i+1
                    if c=="}":
                        break
                    else:
                        value = value+c
                name_list.append(name)
                value_list.append(value)
                name=""
                value=""
                continue
            name=name+c
            i=i+1
        for i in range(len(name_list)):
            name_list[i]=" ".join(name_list[i].split())
            self.CSS_values.add(name_list[i],value_list[i])

            
    def unit2mm(self, string):
        # Returns mm given a string representation of units in another system
        # a dictionary of unit to user unit conversion factors
        uuconv = {'in': 25.4,
                  'pt': 25.4/72.0,
                  #'px': 25.4/self.inkscape_dpi,
                  'mm': 1.0,
                  'cm': 10.0,
                  'm' : 1000.0,
                  'km': 1000.0*1000.0,
                  'pc': 25.4/6.0,
                  'yd': 25.4*12*3,
                  'ft': 25.4*12}
  
        unit = re.compile('(%s)$' % '|'.join(uuconv.keys()))
        param = re.compile(r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')
 
        p = param.match(string)
        u = unit.search(string)
        if p:
            retval = float(p.string[p.start():p.end()])
        else:
            inkex.errormsg(_("Size was not determined returning zero value"))
            retval = 0.0
        if u:
            retunit = u.string[u.start():u.end()]
        else:
            raise Exception
            
        try:
            return retval * uuconv[retunit]
        except KeyError:
            return retval

    def Make_PNG(self):
        #create OS temp folder
        tmp_dir = tempfile.mkdtemp()
        
        if self.inscape_exe != None:
            try:
                svg_temp_file = os.path.join(tmp_dir, "k40w_temp.svg")
                png_temp_file = os.path.join(tmp_dir, "k40w_image.png")
                dpi = "%d" %(self.image_dpi)           
                self.document.write(svg_temp_file)
                cmd = [ self.inscape_exe, self.png_area, "--export-dpi", dpi, \
                        "--export-background","rgb(255, 255, 255)","--export-background-opacity", \
                        "255" ,"--export-png", png_temp_file, svg_temp_file ]
                run_external(cmd, self.timout)
                self.raster_PIL = Image.open(png_temp_file)
                self.raster_PIL = self.raster_PIL.convert("L")
            except Exception as e:
                error_text = "%s" %(e)
                raise Exception("Inkscape Execution Failed (while making raster data).\n%s" %(error_text))
        else:
            raise Exception("Inkscape Not found.")
        try:
            shutil.rmtree(tmp_dir) 
        except:
            raise Exception("Temp dir failed to delete:\n%s" %(tmp_dir) )


    def convert_text2paths(self):
        #create OS temp folder
        tmp_dir = tempfile.mkdtemp()
        if self.inscape_exe != None:
            try:
                svg_temp_file = os.path.join(tmp_dir, "k40w_temp.svg")
                txt2path_file = os.path.join(tmp_dir, "txt2path.svg")         
                self.document.write(svg_temp_file)
                cmd = [ self.inscape_exe, "--export-text-to-path","--export-plain-svg",txt2path_file, svg_temp_file ]
                run_external(cmd, self.timout)
                p = etree.XMLParser(huge_tree=True, recover=True)
                self.document.parse(txt2path_file, parser=p)
            except Exception as e:
                raise Exception("Inkscape Execution Failed (while converting text to paths).\n\n"+str(e))
        else:
            raise Exception("Inkscape Not found.")
        try:
            shutil.rmtree(tmp_dir) 
        except:
            raise Exception("Temp dir failed to delete:\n%s" %(tmp_dir) )
    
    def make_paths(self, txt2paths=False ):
        self.txt2paths = txt2paths
        msg               = ""
        
##        self.inkscape_dpi = None
##        try:
##            Inkscape_Version = self.document.getroot().xpath('@inkscape:version', namespaces=inkex.NSS)[0].split(" ")[0]
##        except:
##            Inkscape_Version = None
##
##        if Inkscape_Version <= .91:
##            self.inkscape_dpi = 90.0
##        else:
##            self.inkscape_dpi = 96.0

      
        if (self.txt2paths):
            self.convert_text2paths()
            
        try:
            h_mm = self.unit2mm(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0])
            w_mm = self.unit2mm(self.document.getroot().xpath('@width', namespaces=inkex.NSS)[0])
        except:
            line1 = "Units not set in SVG File.\n"
            line2 = "Inkscape v0.90 or higher makes SVG files with units data.\n"
            line3 = "1.) In Inkscape (v0.90 or higher) select 'File'-'Document Properties'."
            line4 = "2.) In the 'Custom Size' region on the 'Page' tab set the 'Units' to 'mm' or 'in'."
            raise Exception("%s\n%s\n%s\n%s" %(line1,line2,line3,line4))
        
        try:
            view_box_str = self.document.getroot().xpath('@viewBox', namespaces=inkex.NSS)[0]
            view_box_list = view_box_str.split(' ')
            Wpix = float(view_box_list[2])
            Hpix = float(view_box_list[3])
            scale_h = h_mm/Hpix
            scale_w = w_mm/Wpix
            Dx = float(view_box_list[0]) * scale_w
            Dy = float(view_box_list[1]) * scale_h
        except:
            line1 = "Cannot determine SVG scale (SVG Viewox Missing).\n"
            line2 = "In Inkscape (v0.92) select 'File'-'Document Properties'."
            line3 = "In the 'Scale' region on the 'Page' tab change the 'Scale x:' value"
            line4 = "and press enter. Changing the value will add the Viewbox attribute."
            line5 = "The 'Scale x:' can then be changed back to the original value."
            ##if self.inkscape_dpi==None:
            raise Exception("%s\n%s\n%s\n%s\n%s" %(line1,line2,line3,line4,line5))

##            print "Using guessed dpi value of: ",self.inkscape_dpi
##            scale_h = 25.4/self.inkscape_dpi
##            scale_w = 25.4/self.inkscape_dpi
##            Dx = 0
##            Dy = 0
        
        if abs(1.0-scale_h/scale_w) > .01:
            line1 ="SVG Files with different scales in X and Y are not supported.\n"
            line2 ="In Inkscape (v0.92): 'File'-'Document Properties'"
            line3 ="on the 'Page' tab adjust 'Scale x:' in the 'Scale' section"
            raise Exception("%s\n%s\n%s" %(line1,line2,line3))
        
        for node in self.document.getroot().xpath('//svg:g', namespaces=inkex.NSS):
            if node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
                layer = node.get(inkex.addNS('label', 'inkscape'))
                self.layernames.append(layer.lower())
                layer = layer.replace(' ', '_')
                if layer and not layer in self.layers:
                    self.layers.append(layer)

        self.groupmat = [[[scale_w,    0.0,  0.0-Dx],
                          [0.0  , -scale_h, h_mm+Dy]]]

        self.process_group(self.document.getroot())

        
        #################################################
        #msg = msg + "Height(mm)= %f\n" %(h_mm)
        #msg = msg + "Width (mm)= %f\n" %(w_mm)
        #inkex.errormsg(_(msg))
        
##        if not self.raster: 
##            xmin= self.lines[0][0]+0.0
##            xmax= self.lines[0][0]+0.0
##            ymin= self.lines[0][1]+0.0
##            ymax= self.lines[0][1]+0.0
##            for line in self.lines:
##                x1= line[0]
##                y1= line[1]
##                x2= line[2]
##                y2= line[3]
##                xmin = min(min(xmin,x1),x2)
##                ymin = min(min(ymin,y1),y2)
##                xmax = max(max(xmax,x1),x2)
##                ymax = max(max(ymax,y1),y2)
##        else:
        xmin= 0.0
        xmax=  w_mm 
        ymin= -h_mm 
        ymax= 0.0
        self.Make_PNG()
        
        self.Xsize=xmax-xmin
        self.Ysize=ymax-ymin
        Xcorner=xmin
        Ycorner=ymax
        for ii in range(len(self.lines)):
            self.lines[ii][0] = self.lines[ii][0]-Xcorner
            self.lines[ii][1] = self.lines[ii][1]-Ycorner
            self.lines[ii][2] = self.lines[ii][2]-Xcorner
            self.lines[ii][3] = self.lines[ii][3]-Ycorner

        self.cut_lines = []
        self.eng_lines = []
        for line in self.lines:
            ID=line[5]
            if (self.Cut_Type[ID]=="engrave"):
                self.eng_lines.append([line[0],line[1],line[2],line[3]])
            elif (self.Cut_Type[ID]=="cut"):
                self.cut_lines.append([line[0],line[1],line[2],line[3]])
            else:
                pass
                
if __name__ == '__main__':
    svg_reader =  SVG_READER()
    svg_reader.parse("test.svg")
    svg_reader.make_paths()
