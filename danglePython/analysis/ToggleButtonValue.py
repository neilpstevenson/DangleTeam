from interfaces.SensorInterface import SensorInterface

class ToggleButtonValue(SensorInterface):
	""" Class to get a value from a sensor button and provide
		an on/off toggle when it crosses a value.  
	"""
	
	def __init__(self, button, threshold = 0.5, hysteresis = 0.0, rising=True, triggeredValue = 1.0, untriggeredValue = 0.0):
		SensorInterface.__init__(self)
		self.button = button
		self.threshold = threshold
		self.hysteresis = hysteresis
		self.rising = rising
		self.triggeredValue = triggeredValue
		self.untriggeredValue = untriggeredValue
		self.lastButtonValue = 0.0
		self.currentValue = untriggeredValue
		
	def getValue(self):
		rawValue = self.button.getValue()
		if self.rising:
			if rawValue >= self.threshold and self.lastButtonValue < self.threshold-self.hysteresis:
				# Trigger condition
				self.lastButtonValue = rawValue
				self.currentValue = self.triggeredValue if self.currentValue == self.untriggeredValue else self.untriggeredValue
				return self.currentValue
			elif rawValue < self.lastButtonValue:
				# Lowest point
				self.lastButtonValue = rawValue
		elif rawValue < self.lastButtonValue:
			if rawValue <= self.threshold and self.lastButtonValue > self.threshold+self.hysteresis:
				# Trigger condition
				self.lastButtonValue = rawValue
				self.currentValue = self.triggeredValue if self.currentValue == self.untriggeredValue else self.untriggeredValue
				return self.currentValue
			elif rawValue > self.lastButtonValue:
				# Highest point
				self.lastButtonValue = rawValue
		return self.currentValue

		

		
