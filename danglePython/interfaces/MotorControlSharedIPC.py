import numpy as np

class MotorControlSharedIPC:
	''' Share memory structure to reconrol the motor drivers.
		For speed and torgue: 1.0 = max forward, -1.0 = max backwards
		For position, it is a 64-bit pulse counter from nominal start position, i.e. depends on motors, wheel size etc.
		Watchdog will be decremented on each control loop and if reaches zero, the motors will be stopped.  Set to 100 for 1 second protection.
	'''
	motor_dt = np.dtype([
					('name', np.unicode_, (32)),
					('mode',np.uint16),		#0 = Off, 1 = Torque controlled, 2 = Speed controlled, 3 = Position controlled
					('reqtorque',np.float32),
					('acttorque',np.float32),
					('reqspeed',np.float32),
					('actspeed',np.float32),
					('reqposistion',np.int64),
					('actposistion',np.int64)])
	motors_shared_dt = np.dtype([
					('watchdog',np.uint16),
					('motors',motor_dt, (8))])
	filename = '/dev/shm/motor_control_shared.mmf'
	
	def create(self):
		try:
			self.open()
		except:
			# Create/overwrite
			self.data  = np.memmap(MotorControlSharedIPC.filename, offset=0, dtype=MotorControlSharedIPC.motors_shared_dt, mode='w+', shape=(1))
	
	def open(self):
		# Read/write (no create)
		self.data  = np.memmap(MotorControlSharedIPC.filename, offset=0, dtype=MotorControlSharedIPC.motors_shared_dt, mode='r+')

	def setName(self, motor, name):
		self.data[0]['motors'][motor]['name'] = name
	def setRequiredTorque(self, motor, value):
		self.data[0]['motors'][motor]['reqtorque'] = value
	def getRequiredTorque(self, motor):
		return self.data[0]['motors'][motor]['reqtorque'].copy()
	def setRequiredSpeed(self, motor, value):
		self.data[0]['motors'][motor]['reqspeed'] = value
	def getRequiredSpeed(self, motor):
		return self.data[0]['motors'][motor]['reqspeed'].copy()
	def setRequiredPosition(self, motor, value):
		self.data[0]['motors'][motor]['reqposistion'] = value
	def getRequiredPosition(self, motor):
		return self.data[0]['motors'][motor]['reqposistion'].copy()
	
	def getName(self, motor):
		return self.data[0]['motors'][motor]['name'].copy()
	def setCurrentTorque(self, motor, value):
		self.data[0]['motors'][motor]['acttorque'] = value
	def getCurrentTorque(self, motor):
		return self.data[0]['motors'][motor]['acttorque'].copy()
	def setCurrentSpeed(self, motor, value):
		self.data[0]['motors'][motor]['actspeed'] = value
	def getCurrentSpeed(self, motor):
		return self.data[0]['motors'][motor]['actspeed'].copy()
	def setCurrentPosition(self, motor, value):
		self.data[0]['motors'][motor]['actposistion'] = value
	def getCurrentPosition(self, motor):
		return self.data[0]['motors'][motor]['actposistion'].copy()
	def setMode(self, motor, mode):
		self.data[0]['motors'][motor]['mode'] = mode
	def getMode(self, motor):
		return self.data[0]['motors'][motor]['mode'].copy()
		
	def checkWatchdog(self):
		if self.data[0]['watchdog'] > 0:
			# countdown
			self.data[0]['watchdog'] -= 1
		return self.data[0]['watchdog']
	def resetWatchdog(self, count = 100):
		self.data[0]['watchdog'] = count
		

