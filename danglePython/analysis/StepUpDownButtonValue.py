from interfaces.SensorInterface import SensorInterface

class StepUpDownButtonValue(SensorInterface):
	""" Class to get a value from a sensor button and provide
	basic step up/down control with scaling and limits.  
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
		self.currentButtonState = 0.0
		
	def getValue(self):
		up = self.buttonUp.getValue()
		down = self.buttonDown.getValue()
		rawValue = up - down
		if rawValue != self.currentButtonState:
			self.currentButtonState = rawValue
			self.currentValue += rawValue*self.scaling
			if self.currentValue + self.offset > self.max:
				self.currentValue = self.max - self.offset
			elif self.currentValue + self.offset < self.min:
				self.currentValue = self.min - self.offset
		return self.currentValue + self.offset
		

		
