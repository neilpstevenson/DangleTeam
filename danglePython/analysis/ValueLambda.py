from interfaces.SensorInterface import SensorInterface

class ValueLambda(SensorInterface):
	""" Class to apply an arbitrary lambda function to the imput value(s).
		Default is a value squared function
	"""
	
	def __init__(self, input, function = lambda x:x*x, min = -1.0, max = 1.0, scaling = 1.0, offset = 0.0):
		SensorInterface.__init__(self)
		self.input = input
		self.function = function
		self.min = min
		self.max = max
		self.scaling = scaling
		self.offset = offset
		
	def getValue(self):
		if type(self.input) is list:
			rawValue = sum(map(lambda x: x.getValue(), self.input))
		else:
			rawValue = self.input.getValue()
		scaledValue = self.function(rawValue)*self.scaling + self.offset
		# Preserve sign
		if rawValue < 0.0 and scaledValue > 0.0:
			scaledValue = -scaledValue
		if scaledValue > self.max:
			return self.max
		elif scaledValue < self.min:
			return self.min
		return scaledValue
