from interfaces.SensorInterface import SensorInterface

class IntegratingButtonValue(SensorInterface):
	""" Class to get a value from a sensor button and provide
	basic scaling and limits
	"""
	
	def __init__(self, buttonUp, buttonDown, min = -1.0, max = 1.0, scaling = 1.0, offset = 0.0):
		SensorInterface.__init__(self)
		self.buttonUp = buttonUp
		self.buttonDown = buttonDown
		self.min = min
		self.max = max
		self.scaling = scaling
		self.offset = offset
		self.currentValue = 0.0
		
	def getValue(self):
		rawValue = self.sensors.getButton(self.buttonUp) - self.sensors.getButton(self.buttonDown)
		self.currentValue += rawValue*self.scaling
		if self.currentValue + self.offset > self.max:
			self.currentValue = self.max - self.offset
		elif self.currentValue + self.offset < self.min:
			self.currentValue = self.min - self.offset
		return self.currentValue + self.offset
		

	