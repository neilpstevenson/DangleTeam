from __future__ import unicode_literals
import os
import sys
import time
from PIL import ImageFont

from hardware.demo_opts import get_device
from luma.core.render import canvas

class MenuDisplay:
	def __init__(self, title, menuItems, selected):
		self.titleFont = ImageFont.truetype("Piboto-Bold.ttf", 14)
		self.unselectedFont = ImageFont.truetype("Piboto-Regular.ttf", 10)
		self.selectedFont = ImageFont.truetype("Piboto-Bold.ttf", 20)
		self.title = title
		self.menuItems = menuItems
		self.selected = selected
		self.device = get_device()
	
	def show(self):
		top = 0
		with canvas(self.device) as draw:
			# Title - inverse text centered
			w, h = draw.textsize(text=self.title, font=self.titleFont)
			left = (self.device.width - w) / 2
			draw.rectangle(((0, top), (self.device.width, h)), fill="white")
			draw.text((left, top-2), text=self.title, font=self.titleFont, fill="black", spacing=-2)
			top += h-2
			# Unselected initial item
			if self.selected > 0:
				item = self.selected - 1
				w, h = draw.textsize(text=self.
				menuItems[item], font=self.unselectedFont)
				draw.text((10, top), text=self.menuItems[item], font=self.unselectedFont, fill="white", spacing=-2)
				top += h-4
			# Then the selected item
			w, h = draw.textsize(text=self.menuItems[self.selected], font=self.selectedFont)
			draw.text((0, top), text=self.menuItems[self.selected], font=self.selectedFont, fill="white", spacing=-2)
			top += h
			# Then the rest of the selected items while we have room
			for item in range(self.selected+1, len(self.menuItems)):
				if top < self.device.height:
					w, h = draw.textsize(text=self.menuItems[item], font=self.unselectedFont)
					draw.text((10, top), text=self.menuItems[item], font=self.unselectedFont, fill="white", spacing=-2)
					top += h

	def select(self, selected):
		self.selected = selected
		self.show()
		
if __name__ == "__main__":
	try:
		test = MenuDisplay("Test menu", ["Option A", "Second option", "Third", "Fourth options"], 0)
		for s in range(0,4):
			test.select(s)
			time.sleep(1.0)
	except KeyboardInterrupt:
		pass
