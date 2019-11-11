import hardware.redboard as redboard
import numpy

class Motor:
	def __init__(self, motor, max_torque = 1.0, delta_torque = 0.025):
		self.motor = motor
		self.max_torque = max_torque
		self.delta_torque = delta_torque
		self.requested_torque = 0.0
		self.current_torque = 0.0
		self.actual_speed = 0.0
	
	def updateMotor(self):
		if self.motor == 1:
			redboard.M1(self.current_torque * 100.0)
			print("motor 1: ", self.current_torque)
		elif self.motor == 2:
			redboard.M2(self.current_torque * 100.0)
			print("motor 2: ", self.current_torque)

	def updateTorque(self):
		# For the moment, assume torque==speed
		if self.requested_torque > self.current_torque:
			delta = numpy.minimum(self.requested_torque - self.current_torque, self.delta_torque)
			# Increase torque of motor
			if self.current_torque + delta < self.max_torque:
				self.current_torque += delta
			else:
				self.current_torque = self.max_torque
			self.updateMotor()
		elif self.requested_torque < self.current_torque:
			# Decrease torque of motor
			delta = numpy.minimum(self.current_torque - self.requested_torque, self.delta_torque)
			if self.current_torque - delta > -self.max_torque:
				self.current_torque -= delta
			else:
				self.current_torque = -self.max_torque
			self.updateMotor()
	
	def setTorque(self, torque):
		self.requested_torque = torque
		self.updateTorque()
		
