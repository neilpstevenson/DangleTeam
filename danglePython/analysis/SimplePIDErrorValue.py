from interfaces.SensorInterface import SensorInterface

class SimplePIDErrorValue(SensorInterface):
	""" Class to implement a simple PID control error calculation, based on an input value. It uses the supplied PID and either passes on 
	the returned error (e.g. for positioning via a motor), or an integrated form of the error up to a limit (e.g. for motor speed regulation)
	"""
	
	def __init__(self, pid, current, min = -1.0, max = 1.0, scaling = 1.0, offset = 0.0, integrate = False):
		self.pid = pid
		self.current = current
		self.min = min
		self.max = max
		self.scaling = scaling
		self.offset = offset
		self.integrate = integrate
		self.integratedValue = 0.0

	def getValue(self):
		current = self.current.getValue()
		error = self.pid(float(current)) * self.scaling
		print(f"SimplePIDErrorValue: {current} ({self.pid.setpoint}) {error} = {self.pid.components} {self.pid.tunings}")
		if self.integrate:
			self.integratedValue += error
			if self.integratedValue + self.offset > self.max:
				self.integratedValue = self.max - self.offset
			elif self.integratedValue + self.offset < self.min:
				self.integratedValue = self.min - self.offset
			return self.integratedValue + self.offset
		else:
			if error + self.offset > self.max:
				error = self.max - self.offset
			elif error + self.offset < self.min:
				error = self.min - self.offset
			return error + self.offset

	def setTarget(self, value):
		self.pid.setpoint = float(value)
