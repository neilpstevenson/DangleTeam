from interfaces.SensorInterface import SensorInterface

class UpDownButton(SensorInterface):
	""" Class to get the tri-state value of a two-button up/down control.  
	Buttons values returned are:
		-1 = down button pressed
		 0 = both pressed or both unpressed
		 1 = up button pressed
	"""
	
	def __init__(self, sensorIPC, buttonUp, buttonDown):
		SensorInterface.__init__(self)
		self.sensorIPC = sensorIPC
		self.buttonUp = buttonUp
		self.buttonDown = buttonDown
		
	def getValue(self):
		up = self.sensorIPC.getDigitalValue(self.buttonUp)
		down = self.sensorIPC.getDigitalValue(self.buttonDown)
		return up - down
	