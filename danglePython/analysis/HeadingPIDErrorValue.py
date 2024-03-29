from interfaces.SensorInterface import SensorInterface
import numpy as np

class HeadingPIDErrorValue(SensorInterface):
	""" Class to implement a simple PID control error calculation for heading values. It uses the supplied PID and either passes on 
	the returned error (e.g. for positioning via a motor), or an integrated form of the error up to a limit (e.g. for motor speed regulation)
	"""
	
	def __init__(self, currentHeading, pid, targetHeading, min = -1.0, max = 1.0, scaling = 1.0, integrate = False, clampIAt = None):
		SensorInterface.__init__(self)
		self.currentHeading = currentHeading
		self.pid = pid
		self.targetHeading = targetHeading
		self.min = min
		self.max = max
		self.scaling = scaling
		self.integrate = integrate
		self.integratedValue = 0.0
		self.clampIAt = clampIAt

	def normaliseHeading(self, heading):
		while heading > 180.0:
			heading -= 360.0
		while heading < -180.0:
			heading += 360.0
		return heading
		
	def getValue(self):
		current = self.currentHeading.getValue()
		headingDiff = self.normaliseHeading(current - self.targetHeading)
		# Clear the I term if we're a long way off, to prevent stability issues with large movements
		if self.clampIAt is not None:
			if headingDiff > self.clampIAt or headingDiff < -self.clampIAt:
				self.pid._integral = 0
				
		error = self.pid(headingDiff) * self.scaling
		#np.set_printoptions(precision=2)
		print(f"HeadingPIDErrorValue: targetHeading={self.targetHeading:4.2f}, current={current:4.2f}, headingDiff={headingDiff:4.2f}, error={error:4.2f}")
		if self.integrate:
			self.integratedValue += error
			if self.integratedValue > self.max:
				self.integratedValue = self.max 
			elif self.integratedValue < self.min:
				self.integratedValue = self.min
			print(self.integratedValue)
			return self.integratedValue
		else:
			if error > self.max:
				error = self.max
			elif error < self.min:
				error = self.min
			#print(f"capped error={error:4.2f}")
			return error

	def setTarget(self,targetHeading):
		self.targetHeading = self.normaliseHeading(targetHeading)

	def disable(self):
		self.pid.set_auto_mode(False)
		
	def enable(self):
		if not self.pid.auto_mode:
			self.setTarget(self.currentHeading.getValue())
			self.pid.set_auto_mode(True, last_output=0.0)
			self.getValue()

	def reset(self):
		self.pid.set_auto_mode(False)
		self.setTarget(self.currentHeading.getValue())
		self.pid.set_auto_mode(True, last_output=0.0)
		self.getValue()

