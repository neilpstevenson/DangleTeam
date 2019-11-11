from interfaces.SensorInterface import SensorInterface

class JoystickAxis(SensorInterface):
	""" Accessor to get a value of an analog joystick axis.  
	These always return a value from -1.0 to 1.0
	"""
	
	def __init__(self, sensorIPC, axis):
		SensorInterface.__init__(self)
		self.sensorIPC = sensorIPC
		self.axis = axis
		
	def getValue(self):
		return self.sensorIPC.getAnalogValue(self.axis) 
	