import os
import time
from luma.core.render import canvas
from PIL import ImageFont
# Interfaces
from interfaces.SensorAccessFactory import SensorAccessFactory

class displayText:
	def __init__(self, device, stopButton, text):
		self.count = 0
		self.device = device
		self.stopButton = stopButton
		self.text = text
		
	def make_font(self, name, size):
		font_path = os.path.abspath(os.path.join(
			os.path.dirname(__file__), 'fonts', name))
		return ImageFont.truetype(font_path, size)
	
	def show(self, draw):
		fonts = [self.make_font("code2000.ttf", sz) for sz in range(36, 8, -2)]
		# Try in reducing font size until we find one where the width fits
		for font in fonts:
			size = draw.multiline_textsize(self.text, font)
			if size[0] <= self.device.width and size[1] <= self.device.height:
				 break
		# Render in the center
		left = (self.device.width - size[0]) // 2
		top = (self.device.height - size[1]) // 2
		draw.multiline_text((left, top), self.text, font=font, fill="white", align="center")

	def main(self):	
		with canvas(self.device) as draw:
			self.show(draw)
		while True:
			if self.stopButton.getValue() > 0 or SensorAccessFactory.getSingleton().checkWatchdog() <= 0:
				return
			time.sleep(0.2)
