import sys, math
import pygame
from interfaces.MotionSensorSharedIPC import MotionSensorSharedIPC

BLACK    = (   0,   0,   0)
WHITE    = ( 255, 255, 255)
GREY     = ( 192, 192, 192)
RED      = ( 192, 0, 0)


def main():
	pygame.init()
	size = [700, 700]
	screen = pygame.display.set_mode(size)
	pygame.display.set_caption("RPi Orientation")
	# Set required frame rate
	#pygame.time.Clock().tick(40)
	image = pygame.image.load("compass1.png").convert_alpha()
	img_rect = image.get_rect()
	angle = 0
	done = False
	quaternion = MotionSensorSharedIPC()

	while not done:
		for event in pygame.event.get(): 
			if event.type == pygame.QUIT:
				done = True 
		# Read the next position from input
		quaternion.updateReading()
		angle = -quaternion.getYawDegrees()
		warn = math.fabs(quaternion.getPitchDegrees()) > 80.0
		
		rot_image = pygame.transform.rotate(image, angle)
		rot_im_rect = rot_image.get_rect()
		rot_im_rect.center = img_rect.center
		if warn:
			screen.fill(RED)
		else:
			screen.fill(GREY)
		screen.blit(rot_image, rot_im_rect)
		pygame.display.flip()
		
		pygame.time.wait(50) # Milliseconds

	pygame.quit()
	sys.exit()

if __name__ == "__main__":
	main()
