import hardware.redboard as redboard
import time

class Motor:
	def __init__(self, motor, max_torque = 1.0, delta_torque = 0.025):
		self.motor = motor
		self.max_torque = max_torque
		self.delta_torque = delta_torque
		self.requested_torque = 0.0
		self.current_torque = 0.0
		self.actual_speed = 0.0
		self.pwmCount = 0
		self.last_speed = 999
		if self.motor == 1:
			self.redboardM = redboard.M1
		elif self.motor == 2:
			self.redboardM = redboard.M2
	
	def updateMotor(self):
		required_torque = self.current_torque * 100.0
		# Do high-level PWM control
		#self.pwmCount = (self.pwmCount + 1) % 10
		#if required_torque > 5 and self.pwmCount < required_torque/10:
		#	required_torque *= 10
		#elif required_torque < -5 and self.pwmCount < -required_torque/10:
		#	required_torque *= 10
		if required_torque != self.last_speed:
			print(f"{time.time():.4f}: {self.motor}: {self.last_speed:.1f} -> {required_torque:.1f}")
			self.redboardM(required_torque)
			self.last_speed = required_torque
		#print(f"{time.time()}:{self.pwmCount} motor {self.motor}: {self.current_torque} -> {required_torque}")

	def updateTorque(self):
		# For the moment, assume torque==speed
		if self.requested_torque > self.current_torque:
			delta = min(self.requested_torque - self.current_torque, self.delta_torque)
			# Increase torque of motor
			if self.current_torque + delta < self.max_torque:
				self.current_torque += delta
			else:
				self.current_torque = self.max_torque
			self.updateMotor()
		elif self.requested_torque < self.current_torque:
			# Decrease torque of motor
			delta = min(self.current_torque - self.requested_torque, self.delta_torque)
			if self.current_torque - delta > -self.max_torque:
				self.current_torque -= delta
			else:
				self.current_torque = -self.max_torque
			self.updateMotor()
		else:
			self.updateMotor()
	
	def setTorque(self, torque):
		self.requested_torque = torque
		self.updateTorque()
		
