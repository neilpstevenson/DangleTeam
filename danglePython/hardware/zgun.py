#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  servo.py
#  
#  Copyright 2019  <pi@RoboTank>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
import logging
logging.basicConfig
logger=logging.getLogger(__name__)
import time
from smbus import SMBus

MIN=900
MAX=2000

class Zgun(object):
    def __init__(self,addr=0x10):
        self.addr=addr
        try:
            self.sb=SMBus(1)
            self.pos=1500
            self.sb.write_byte_data(self.addr,0x01,0xff) #motor speed Max
            self.sb.write_byte_data(self.addr,0x00,0xff) #Laser Max
            self.sb.write_byte_data(self.addr,0x02,0x00) #Motor off
            self.sb.write_byte_data(self.addr,0x03,0x00)
            self.motor=False
            self.setpos(self.pos)
            high,low=divmod(50,256)
            self.sb.write_byte_data(self.addr,6,high)
            self.sb.write_byte_data(self.addr,7,low)
        except OSError:
            pass
            
    def down(self,step=1):
        self.pos -= step
        self.setpos(self.pos)
        time.sleep(.01)
        
    def up(self,step=1):
        self.pos += step
        self.setpos(self.pos)
        time.sleep(.01)
        
    def setpos(self,pos):
        if pos>MAX:
            pos=MAX
        if pos<MIN:
            pos=MIN
        self.pos=pos
        high,low=divmod(int(pos),256)
        print(high,low)
        self.sb.write_byte_data(self.addr,4,high)
        self.sb.write_byte_data(self.addr,5,low)
        
    def fire(self):
        if self.motor:
            high,low=divmod(3000,256)
            print (high,low)
            self.sb.write_byte_data(self.addr,6,high)
            self.sb.write_byte_data(self.addr,7,low)
            time.sleep(1)
            high,low=divmod(10,256)
            self.sb.write_byte_data(self.addr,6,high)
            self.sb.write_byte_data(self.addr,7,low)
            
            time.sleep(.5)
        
    def arm(self,state):
        '''switch on targeting laser & activate Nerf Mechanism'''
        self.sb.write_byte_data(self.addr,0,0xff) # Max intensity
        if state:
            self.sb.write_byte_data(self.addr,2,1) #laser on
            self.sb.write_byte_data(self.addr,0x03,0x01) #motors on
            self.motor=True
        else:
            self.sb.write_byte_data(self.addr,2,0) #laser off
            self.sb.write_byte_data(self.addr,0x03,0x0) #motors off
            self.motor=False

def main(args):
    zgun=Zgun()
    while True:
    
        zgun.fire()
        time.sleep(2)
#            print ('IO Error!')
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
