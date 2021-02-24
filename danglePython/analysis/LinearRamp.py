from interfaces.SensorInterface import SensorInterface

class LinearRamp(SensorInterface):
	""" Class to apply a scale/offset/limit to a value from a sensor
	"""
	
	def __init__(self, input, increment = 0.02, initialValue = 0.0):
		SensorInterface.__init__(self)
		self.input = input
		self.increment = increment
		self.currentValue = initialValue
		
	def getValue(self):
		return self.currentValue

	def process(self):
		if type(self.input) is list:
			targetValue = sum(map(lambda x: x.getValue(), self.input))
		else:
			targetValue = self.input.getValue()
		if targetValue > self.currentValue:
			self.currentValue = min(self.currentValue + self.increment, targetValue)
		elif targetValue < self.currentValue:
			self.currentValue = max(self.currentValue - self.increment, targetValue)
			
	def reset(self):
		# Set to current value
		if type(self.input) is list:
			self.currentValue = sum(map(lambda x: x.getValue(), self.input))
		else:
			self.currentValue = self.input.getValue()
		

