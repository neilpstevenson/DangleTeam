# Interfaces
from interfaces.IndicatorControlSharedIPC import IndicatorControlSharedIPC

class displayIndicatorEyes:
	def __init__(self):
		self.eyes = IndicatorControlSharedIPC()
		self.eyes.create()

	def setEyes(self, leftLeds, leftOnColour, leftOffColour, rightLeds, rightOnColour, rightOffColour):
		self.eyes.setIndicator(0, leftLeds, leftOnColour, leftOffColour)
		self.eyes.setIndicator(1, rightLeds, rightOnColour, rightOffColour)
