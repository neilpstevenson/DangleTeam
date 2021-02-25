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
		
		# Main Loop
		while 1:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
			
			imageResults, timestamp, elapsed = self.imageAnalysisResult.updateSnapshot()
			imageResults = self.imageAnalysisResult.getImageResultByNameAndType("Green","Block")
			imageResults += self.imageAnalysisResult.getImageResultByNameAndType("Red","Block")
			imageResults += self.imageAnalysisResult.getImageResultByNameAndType("Yellow","Block")
			imageResults += self.imageAnalysisResult.getImageResultByNameAndType("Blue","Block")
			
			# Clear current image
			self.screen.fill((64,64,64))

			self.screen.blit(font.render(f"Images: {len(imageResults)}", True, (255,255,255)), (32, 32))
			for result in range(len(imageResults)):
				self.screen.blit(font.render(f"{imageResults[result].typename}.{imageResults[result].name}: dist: {imageResults[result].distance:.0f}mm, angle: {imageResults[result].angle:.1f}", True, (255,255,255)), (32, 48 + result*16))
			
				# Plot the found points
				dist = imageResults[result].distance
				hpos = np.tan(imageResults[result].angle/180.0*3.14159) * dist
				colour = pygame.colordict.THECOLORS[imageResults[result].name.lower()]
				pygame.draw.circle(self.screen, colour, (self.width//3-int(hpos), self.height-int(dist/2.5)), 20)
			
			# Show the new screen
			pygame.display.flip()
			
			# Limit update speed
			pygame.time.wait(50)
