from ../interfaces/SensorInterface import SensorInterface

class FixedValue(SensorInterface):
	""" Class to get a value from a sensor and provide
	basic scaling and limits
	"""
	
	def __init__(self, value):
		SensorInterface.__init__(self)
		self.value = value
		
	def getValue(self):
		return self.value
		
	def setValue(self, value):
		self.value = value
		