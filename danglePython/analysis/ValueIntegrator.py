from ../interfaces/SensorInterface import SensorInterface

class ValueIntegrator(SensorInterface):
	""" Class to get a value from a sensor and integrate its value, returning
		as a derived sensor value
	"""
	
	def __init__(self, input, min = -1.0, max = 1.0, scaling = 1.0, offset = 0.0):
		SensorInterface.__init__(self)
		self.input = input
		self.min = min
		self.max = max
		self.scaling = scaling
		self.offset = offset
		self.currentValue = 0.0
		
	def getValue(self):
		if type(self.input) is list:
			rawValue = sum(map(lambda x: x.getValue(), self.input))
		else:
			rawValue = self.input.getValue()
		self.currentValue += rawValue*self.scaling
		if self.currentValue + self.offset > self.max:
			self.currentValue = self.max - self.offset
		elif self.currentValue + self.offset < self.min:
			self.currentValue = self.min - self.offset
		return self.currentValue + self.offset
		

	