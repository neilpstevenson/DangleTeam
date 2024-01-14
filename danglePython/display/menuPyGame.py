import sys
import time
from PIL import ImageFont
# Interfaces
from interfaces.Config import Config
import pygame
import textwrap
import pygame.freetype


class MenuDisplay:
	
	def __init__(self, title, menuItems, selected, scale = 1):
		self.titleFont = ImageFont.truetype("FreeSans.ttf", 14*scale)
		self.unselectedFont = ImageFont.truetype("Piboto-Regular.ttf", 10*scale)
		self.selectedFont = ImageFont.truetype("FreeSansBold.ttf", 20*scale)
		self.title = title
		self.menuItems = menuItems
		self.selected = selected
		# Config
		#config = Config()
		#displayDef = config.get("display.config", MenuDisplay.defaultDisplayConfig)
		#config.save()
		# create device
		pygame.display.init()
		pygame.freetype.init()
		windowInfo = pygame.display.Info()
		self.width = min(1024,windowInfo.current_w)
		self.height = min(800,windowInfo.current_h)
		self.title_font = pygame.freetype.SysFont('Verdana', self.width/8)
		self.subTitle_font = pygame.freetype.SysFont('Verdana', self.width/16)
		self.additional_font = pygame.freetype.SysFont('Verdana', self.width/24)
		self.clock = pygame.time.Clock()
		 # Setup window
		self.screen = pygame.display.set_mode((self.width, self.height))#, pygame.FULLSCREEN)
		pygame.display.set_caption(self.title)


	def processEvents(self):
		# Process PyGame events
		for event in pygame.event.get():
			if event.type == pygame.QUIT or \
				(event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_q)):
				# If pressed key is ESC or q, quit program
				sys.exit()
		
	def show(self):
		# Display the status
		self.screen.fill((255, 255, 255))
		pos = (0,20)
		for item in range(len(self.menuItems)):
			for text in self.menuItems[item].split("\n"):
				if item == self.selected:
					# Draw in big font
					text_rendered,rect = self.title_font.render(text, fgcolor=(0,0,0))
				else:
					# Draw in medium font
					text_rendered,rect = self.subTitle_font.render(text, fgcolor=(0,0,0))
				self.screen.blit(text_rendered, (self.width//2 - (rect[2]-rect[0])//2, pos[1]))
				pos = (pos[0],pos[1] + rect[1] * 7 // 5)

		pygame.display.flip()
		self.processEvents()
					
	def message(self, msg, bigFont=False):
		self.screen.fill((255, 255, 255))
		pos = (0,200)
		for text in msg.split("\n"):
			if bigFont:
				# Draw in big font
				text_rendered,rect = self.title_font.render(text, fgcolor=(0,0,0))
			else:
				# Draw in medium font
				text_rendered,rect = self.subTitle_font.render(text, fgcolor=(0,0,0))
			self.screen.blit(text_rendered, (self.width//2 - (rect[2]-rect[0])//2, pos[1]))
			pos = (pos[0],pos[1] + rect[1] * 7 // 5)

		pygame.display.flip()
		self.processEvents()

		#top = 0
		#with canvas(self.device) as draw:
		#	# Title - inverse text centered
		#	w, h = draw.textsize(text=self.title, font=self.titleFont)
		#	left = (self.device.width - w) / 2
		#	draw.rectangle(((0, top), (self.device.width, h-2)), fill="white")
		#	draw.text((left, top-2), text=self.title, font=self.titleFont, fill="black", spacing=-2)
		#	top += h
		#	# Message
		#	w, h = draw.textsize(text=msg, font=self.selectedFont)
		#	draw.text((0, top), text=msg, font=self.selectedFont, fill="white", spacing=-2)
		#	top += h

	def select(self, selected):
		self.selected = selected
		self.show()
	
	def getDevice(self):
		return self.device
		
if __name__ == "__main__":
	try:
		test = MenuDisplay("Test menu", ["Option A", "Second option", "Third", "Fourth options"], 0)
		for s in range(0,4):
			test.select(s)
			time.sleep(1.0)
	except KeyboardInterrupt:
		pass
