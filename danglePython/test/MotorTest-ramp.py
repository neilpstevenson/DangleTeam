import time
import pygame
import atexit
from redboard import *

pygame.init()

# recommended for auto-disabling motors on shutdown!
atexit.register(Stop)

class DangleControl:

	def run(self):
		counter = 0
		torgueL = 0.0
		torgueR = 0.0
		done = False
		
		while not done:
			counter += 1
			
			#
			# EVENT PROCESSING STEP
			#
			for event in pygame.event.get(): # User did something.
				if event.type == pygame.QUIT: # If user clicked close.
					done = True # Flag that we are done so we exit this loop.

			# Adjust torque
			if counter % 10000 < 2500 or counter % 10000 >= 7500:
				torgueL += 0.0002
			else:
				torgueL -= 0.0002
			M2(torgueL*100.0)
			if counter % 1200 < 300 or counter % 1200 >= 900:
				torgueR += 0.002
			else:
				torgueR -= 0.002
			M1(torgueR*100.0)

			pygame.time.wait(10) # mS

main = DangleControl()
main.run()
