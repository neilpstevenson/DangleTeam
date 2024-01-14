import sys, math, pygame
import numpy as np
# Factories
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.VisionAccessFactory import VisionAccessFactory

class DisplayImageCapture:
	def __init__(self, win_width = 640, win_height = 480):
		pygame.init()
		self.width = win_width 
		self.height = win_height

		self.screen = pygame.display.set_mode((win_width, win_height))
		pygame.display.set_caption("Image Capture & Analysis Viewer")
		
		self.clock = pygame.time.Clock()

		self.sensors = SensorAccessFactory.getSingleton()
		self.imageAnalysisResult = VisionAccessFactory.getSingleton().getImageResult()
		
	def run(self):
		font = pygame.font.SysFont('Arial', 12)
		timestampPrev = 0.0
		sampleNumberPrev = 0
		
		# Name, Type, Colour
		imageNames = [("Green","Block","Green"), \
					  ("Red","Block", "Red"), \
					  ("Yellow","Block", "Yellow"), \
					  ("Blue","Block", "Blue"), \
					  ("12","ArUco", "Cyan"), \
					  ("24","ArUco", "Magenta"), \
					  ("48","ArUco", "White") ]

		# Main Loop
		while 1:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
			
			res, timestamp, elapsed = self.imageAnalysisResult.updateSnapshot()
			imageResults = []
			for i in imageNames:
				imageResult = self.imageAnalysisResult.getImageResultByNameAndType(i[0], i[1])
				if len(imageResult) > 0:
					for l in imageResult:
						imageResults += [[l, i[2]]]
			print(f"Showing: {imageResults}")
			
			# Clear current image
			self.screen.fill((64,64,64))

			self.screen.blit(font.render(f"Images: {len(imageResults)}", True, (255,255,255)), (32, 32))
			for result in range(len(imageResults)):
				print(f"result: {imageResults[result][0]}")
				self.screen.blit(font.render(f"{imageResults[result][0].typename}.{imageResults[result][0].name}: dist: {imageResults[result][0].distance:.0f}mm, angle: {imageResults[result][0].angle:.1f}", \
					True, (255,255,255)), (32, 48 + result*16))
			
				# Plot the found points
				dist = imageResults[result][0].distance
				#x = np.tan(imageResults[result][0].angle/180.0*3.14159) * dist
				x = np.sin(imageResults[result][0].angle/180.0*3.14159) * dist
				y= np.cos(imageResults[result][0].angle/180.0*3.14159) * dist
				try:
					colour = pygame.colordict.THECOLORS[imageResults[result][1].lower()]
				except:
					colour = (255,255,255)
				pygame.draw.circle(self.screen, colour, (self.width//2-int(x/1.5), self.height-int(y/2)), 20)
			
			# Show the new screen
			pygame.display.flip()
			
			# Limit update speed
			pygame.time.wait(50)
