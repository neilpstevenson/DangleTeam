from interfaces.SensorInterface import SensorInterface
from analysis.HysteresisValueBase import HysteresisValueBase

class ToggleButtonValue(HysteresisValueBase):
	""" Class to get a value from a sensor button and provide
		an on/off toggle when it crosses a value.  
	"""
	
	def __init__(self, button, threshold = 0.5, hysteresis = 0.0, rising=True, triggeredValue = 1.0, untriggeredValue = 0.0):
		HysteresisValueBase.__init__(self, button, threshold, hysteresis, rising, triggeredValue, untriggeredValue)
		
	def trigger(self, rawValue):
		self.lastButtonValue = rawValue
		self.currentValue = self.triggeredValue if self.currentValue == self.untriggeredValue else self.untriggeredValue
