import numpy as np

class ServoControlSharedIPC:
	''' Shared memory structure to control the servo drivers.
		Servo positions are defined as: -1.0 extreme anticlockwise, +1.0 extreme clockwise
		Watchdog will be decremented on each control loop and if reaches zero, the motors will be stopped.  Set to 100 for 1 second protection.
	'''
	servo_dt = np.dtype([
					('status', np.uint16),	# 0=off, 1=driven
					('position', np.float32)])
	servos_shared_dt = np.dtype([
					('watchdog', np.uint16),
					('servos', servo_dt, (32))])
	filename = '/dev/shm/servo_control_shared.mmf'
	
	def create(self):
		try:
			self.open()
		except:
			# Create/overwrite
			self.data  = np.memmap(ServoControlSharedIPC.filename, offset=0, dtype=ServoControlSharedIPC.servos_shared_dt, mode='w+', shape=(1))
	
	def open(self):
		# Read/write (no create)
		self.data  = np.memmap(ServoControlSharedIPC.filename, offset=0, dtype=ServoControlSharedIPC.servos_shared_dt, mode='r+')

	def setPosition(self, servo, value, status=1):
		self.data[0]['servos'][servo]['position'] = value
		self.data[0]['servos'][servo]['status'] = status
	def getPosition(self, servo):
		return self.data[0]['servos'][servo]['position'].copy()
	def getStatus(self, servo):
		return self.data[0]['servos'][servo]['status'].copy()
		
	def checkWatchdog(self):
		if self.data[0]['watchdog'] > 0:
			# countdown
			self.data[0]['watchdog'] -= 1
		return self.data[0]['watchdog']
	def resetWatchdog(self, count = 100):
		self.data[0]['watchdog'] = count
		

