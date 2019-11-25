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
            self.pos=1000
            self.sb.write_byte_data(self.addr,0x01,0xff)
            self.setpos(self.pos)
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
        self.sb.write_byte_data(self.addr,0x03,0x01)

