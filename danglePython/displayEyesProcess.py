import time
import board
import neopixel
from interfaces.IndicatorControlSharedIPC import IndicatorControlSharedIPC

# Hardware GPIO line 
pixel_pin = board.D12

# Two eyes of 8 pixels each
num_pixels_per_eye = 8
num_eyes = 2

# The order of the pixel colors
ORDER = neopixel.GRB

eyes = IndicatorControlSharedIPC()
eyes.open()

pixels = neopixel.NeoPixel( pixel_pin, num_pixels_per_eye * num_eyes, brightness=1.0, auto_write=False, pixel_order=ORDER )

lastLeftLeds = lastLeftOnColour = lastLeftOffColour = 0xffffffff
lastRightLeds = lastRightOnColour = lastRightOffColour = 0xffffffff

while True:
	leftLeds, leftOnColour, leftOffColour = eyes.getIndicator(0)
	rightLeds, rightOnColour, rightOffColour = eyes.getIndicator(1)

	if lastLeftLeds != leftLeds or lastLeftOnColour != leftOnColour or lastLeftOffColour != leftOffColour or \
		lastrightLeds != rightLeds or lastrightOnColour != rightOnColour or lastrightOffColour != rightOffColour:

		lastLeftLeds = leftLeds
		lastLeftOnColour = leftOnColour
		lastLeftOffColour = leftOffColour
		lastrightLeds = rightLeds
		lastrightOnColour = rightOnColour
		lastrightOffColour = rightOffColour
		
		print(f"Left: {hex(leftLeds)}/{hex(leftOnColour)}/{hex(leftOffColour)}, Right: {hex(rightLeds)}/{hex(rightOnColour)}/{hex(rightOffColour)}")

		# Fill pixel arrays
		for led in range(num_pixels_per_eye):
			pixels[led] = rightOnColour if (rightLeds & 0x0001) == 1 else rightOffColour
			rightLeds >>= 1
		for led in range(num_pixels_per_eye, 2*num_pixels_per_eye):
			pixels[led] = leftOnColour if (leftLeds & 0x0001) == 1 else leftOffColour
			leftLeds >>= 1
			
		pixels.show()

	time.sleep(0.05)
