import time
#import board
#import neopixel
from interfaces.IndicatorControlSharedIPC import IndicatorControlSharedIPC

# Hardware GPIO line 
#pixel_pin = board.D12

# Two eyes of 8 pixels each
#num_pixels_per_eye = 8
#num_eyes = 2

# The order of the pixel colors
#ORDER = neopixel.GRB

eyes = IndicatorControlSharedIPC()
eyes.create()

#pixels = neopixel.NeoPixel( pixel_pin, num_pixels_per_eye * num_eyes, brightness=1.0, auto_write=False, pixel_order=ORDER )

RED =   0x00040000
GREEN = 0x00000200
BLUE =  0x00000004
WHITE = 0x00040404


while True:
	for left in (0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0xff,0x00):
		eyes.setIndicator(0, left, RED, BLUE)
		time.sleep(0.2)
	for right in (0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0xff,0x00):
		eyes.setIndicator(1, right, GREEN, WHITE)
		time.sleep(0.2)
	


#while True:
#	leftLeds, leftOnColour, leftOffColour = eyes.getIndicator(0)
#	rightLeds, rightOnColour, rightOffColour = eyes.getIndicator(1)
#	
#	#print(f"Left: {hex(leftLeds)}/{hex(leftOnColour)}/{hex(leftOffColour)}, Right: {hex(rightLeds)}/{hex(rightOnColour)}/{hex(rightOffColour)}")
#	
#	# Fill pixel arrays
#	for led in range(num_pixels_per_eye):
#		pixels[led] = rightOnColour if (rightLeds & 0x0001) == 1 else rightOffColour
#		rightLeds >>= 1
#	for led in range(num_pixels_per_eye, 2*num_pixels_per_eye):
#		pixels[led] = leftOnColour if (leftLeds & 0x0001) == 1 else leftOffColour
#		leftLeds >>= 1
#		
#	pixels.show()
#	
#	time.sleep(0.2)
