from interfaces.SensorInterface import SensorInterface

class Button(SensorInterface):
	""" Class to get the binary state of a button state.  
	Buttons values returned are:
		0 = unpressed
		1 = pressed
	"""
	
	def __init__(self, sensorIPC, button):
		SensorInterface.__init__(self)
		self.sensorIPC = sensorIPC
		self.button = button
		
	def getValue(self):
		return self.sensorIPC.getDigitalValue(self.button)
		
	def setValue(self, value, status=1):
		self.sensorIPC.setDigitalValue(self.button, value, status=status)
	
