from ../interfaces/SensorInterface import SensorInterface

class ValueAdder(SensorInterface):
	""" Class to sum a set of sensor values, returning
		as a derived sensor value
	"""
	
	def __init__(self, sensors, min = -1.0, max = 1.0, scaling = 1.0, offset = 0.0):
		SensorInterface.__init__(self)
		self.sensors = sensors
		self.min = min
		self.max = max
		self.scaling = scaling
		self.offset = offset
		
	def getValue(self):
		rawValue = sum(map(lambda x: x.getValue(), self.sensors))
		scaledValue = rawValue*self.scaling
		if scaledValue + self.offset > self.max:
			return self.max
		elif scaledValue + self.offset < self.min:
			return self.min
		return scaledValue + self.offset
		

	