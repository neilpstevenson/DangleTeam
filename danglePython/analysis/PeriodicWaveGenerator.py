from interfaces.SensorInterface import SensorInterface
from analysis.HysteresisValueBase import HysteresisValueBase
import time

class PeriodicWaveGenerator:
	""" Class to get a value from a sensor button and provide
		an periodic wave output while it is above a threshold.
		If truncate=False, then the high time will run to completion, 
		otherwise it stops immediately.  
		The low phase can always be truncated.
		Always start in the high state.
	"""
	
	def __init__(self, button, highTime, lowTime, truncate = False, threshold = 0.5, highValue = 1.0, lowValue = 0.0):
		self.button = button
		self.highTime = highTime
		self.lowTime = lowTime
		self.truncate = truncate
		self.threshold = threshold
		self.highValue = highValue
		self.lowValue = lowValue
		self.currentValue = lowValue
		self.triggeredTime = None
		
	def updateOutputState(self):
		if self.triggeredTime != None:
			now = time.perf_counter()
			if self.currentValue == self.lowValue and (now - self.triggeredTime) >= self.lowTime:
				# End of low period
				self.triggeredTime = now
				self.currentValue = self.highValue
			elif self.currentValue == self.highValue and (now - self.triggeredTime) >= self.highTime:
				# End of high period
				self.triggeredTime = now
				self.currentValue = self.lowValue
		
	def getValue(self):
		self.updateOutputState()
		# Update the value based on the input
		rawValue = self.button.getValue()
		if rawValue >= self.threshold:
			if self.triggeredTime == None:
				# Start the output
				self.triggeredTime = time.perf_counter()
				self.currentValue = self.highValue
		elif self.triggeredTime != None:
			# Stop the output now or defer?
			if self.truncate or self.currentValue == self.lowValue:
				# Stop the output 
				self.triggeredTime = None
				self.currentValue = self.lowValue
		#print(f"returning {self.currentValue}")
		return self.currentValue
