from ../interfaces/SensorInterface import SensorInterface

class Scaler(SensorInterface):
	""" Class to apply a scale/offset/limit to a value from a sensor
	"""
	
	def __init__(self, input, min = -1.0, max = 1.0, scaling = 1.0, offset = 0.0):
		SensorInterface.__init__(self)
		self.input = input
		self.min = min
		self.max = max
		self.scaling = scaling
		self.offset = offset
		
	def getValue(self):
		if type(self.input) is list:
			rawValue = sum(map(lambda x: x.getValue(), self.input))
		else:
			rawValue = self.input.getValue()
		scaledValue = rawValue*self.scaling + self.offset
		if scaledValue > self.max:
			return self.max
		elif scaledValue < self.min:
			return self.min
		return scaledValue

	