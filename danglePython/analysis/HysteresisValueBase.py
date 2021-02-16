from abc import ABC, abstractmethod
from interfaces.SensorInterface import SensorInterface

class HysteresisValueBase(SensorInterface):
	""" Abstract class to get a value from a sensor and apply a "trigger" hysteresis to the
	the value.  
	Override trigger() to implement the trigger resultant action.
	"""
	
	def __init__(self, button, threshold, hysteresis, rising, triggeredValue, untriggeredValue):
		SensorInterface.__init__(self)
		self.button = button
		self.threshold = threshold
		self.hysteresis = hysteresis
		self.rising = rising
		self.triggeredValue = triggeredValue
		self.untriggeredValue = untriggeredValue
		self.lastButtonValue = 0.0
		self.currentValue = untriggeredValue
		
	@abstractmethod
	def trigger(self, rawValue):
		pass
		
	def getValue(self):
		rawValue = self.button.getValue()
		if self.rising:
			if rawValue >= self.threshold and self.lastButtonValue < self.threshold-self.hysteresis:
				# Trigger condition
				self.trigger(rawValue)
			elif rawValue < self.lastButtonValue:
				# Lowest point
				self.lastButtonValue = rawValue
		elif rawValue < self.lastButtonValue:
			if rawValue <= self.threshold and self.lastButtonValue > self.threshold+self.hysteresis:
				# Trigger condition
				self.trigger(rawValue)
			elif rawValue > self.lastButtonValue:
				# Highest point
				self.lastButtonValue = rawValue
		return self.currentValue

	def reset(self):
		self.currentValue = self.untriggeredValue
