from interfaces.SensorInterface import SensorInterface
from analysis.HysteresisValueBase import HysteresisValueBase
import time

class TimedTriggerValue(HysteresisValueBase):
	""" Class to get a value from a sensor button and provide
		an timed pulse as a result when it crosses a value.  
	"""
	
	def __init__(self, button, pulseTime, retriggerable = False, threshold = 0.5, hysteresis = 0.0, rising=True, triggeredValue = 1.0, untriggeredValue = 0.0):
		HysteresisValueBase.__init__(self, button, threshold, hysteresis, rising, triggeredValue, untriggeredValue)
		self.pulseTime = pulseTime
		self.retriggerable = retriggerable
		self.triggeredTime = None
		
	def trigger(self, rawValue):
		self.lastButtonValue = rawValue
		if self.currentValue == self.untriggeredValue:
			# Trigger a new timed pulse
			self.currentValue = self.triggeredValue
			self.triggeredTime = time.perf_counter()		
		elif self.retriggerable:
			self.triggeredTime = time.perf_counter()		

	def getValue(self):
		# Check for expired timer
		if self.triggeredTime != None:
			if (time.perf_counter() - self.triggeredTime) >= self.pulseTime:
				self.currentValue = self.untriggeredValue
				self.triggeredTime = None
		return HysteresisValueBase.getValue(self)
				
