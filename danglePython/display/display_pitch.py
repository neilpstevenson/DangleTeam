import sys, math
import pygame
from interfaces.MotionSensorSharedIPC import MotionSensorSharedIPC

BLACK    = (   0,   0,   0)
WHITE    = ( 255, 255, 255)
GREY     = ( 192, 192, 192)
RED      = ( 192, 0, 0)


def main():
	pygame.init()
	size = [200, 350]
	screen = pygame.display.set_mode(size)
	pygame.display.set_caption("Pitch")
	bg_image = pygame.image.load("180rc-gauge350px.png").convert_alpha()
	needle = pygame.image.load("needle3.png").convert_alpha()
	needle_pivot = [26.0,bg_image.get_rect().center[1]+0.0]
	needle_offset = pygame.math.Vector2(needle.get_rect().center[0]-24.0,0.0)
	bg_img_rect = bg_image.get_rect()
	font = pygame.font.SysFont('Arial', 12)
	done = False
	quaternion = MotionSensorSharedIPC()

	while not done:
		for event in pygame.event.get(): 
			if event.type == pygame.QUIT:
				done = True 
		# Read the next position from input
		quaternion.updateReading()
		angle = quaternion.getPitchDegrees()
		warn = math.fabs(angle) > 80.0
		
		rot_needle = pygame.transform.rotate(needle, angle)
		rot_im_rect = rot_needle.get_rect(center = needle_pivot + needle_offset.rotate(-angle))
		if warn:
			screen.fill(RED)
		else:
			screen.fill(GREY)
		screen.blit(bg_image, (0,0))
		screen.blit(rot_needle, rot_im_rect)
		
		# Info pane
		screen.blit(font.render("Pitch: {:3.2f}".format(angle), True, (0,0,0)), (130, 330))

		pygame.display.flip()
		
		pygame.time.wait(50) # Milliseconds

	pygame.quit()
	sys.exit()

if __name__ == "__main__":
	main()
