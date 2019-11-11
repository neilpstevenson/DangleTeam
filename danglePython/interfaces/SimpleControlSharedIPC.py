import numpy as np

class SimpleControlSharedIPC:
	''' Shared memory structure to control simple outputs, such as LEDs, solenoids and activators.
		Values provided are 0-255 with interpretation being output-specific, e.g.
			Simple RGB LED - R=0x04, G=0x02, B=0x01
			Brightness controlled LED - 0=off, 255=Full on
			Solenoid/activator - 0 = off, 255 = fully activated
		Watchdog will be decremented on each control loop and if reaches zero, the device-specific "safe" action is taken.  Set to 100 for 1 second protection.
	'''
	control_dt = np.dtype([
					('type', np.uint8), 	# 0 = not in use, 1 = simple valued, 2 = one-shot (reset to zero after activating)
					('value', np.uint8)])
	controls_shared_dt = np.dtype([
					('watchdog', np.uint16),
					('controls', control_dt, (32))])
	filename = '/dev/shm/simple_control_shared.mmf'
	
	def create(self):
		# Create/overwrite
		self.data  = np.memmap(SimpleControlSharedIPC.filename, offset=0, dtype=SimpleControlSharedIPC.controls_shared_dt, mode='w+', shape=(1))
	
	def open(self):
		# Read/write (no create)
		self.data  = np.memmap(SimpleControlSharedIPC.filename, offset=0, dtype=SimpleControlSharedIPC.controls_shared_dt, mode='r+')

	def setValue(self, control, value, type = 1):
		self.data[0]['controls'][control]['value'] = value
		self.data[0]['controls'][control]['type'] = type
	def getValue(self, control):
		return self.data[0]['controls'][control]['value'].copy()
	def getType(self, control):
		return self.data[0]['controls'][control]['type'].copy()
		
	def checkWatchdog(self):
		if self.data[0]['watchdog'] > 0:
			# countdown
			self.data[0]['watchdog'] -= 1
		return self.data[0]['watchdog']
	def resetWatchdog(self, count = 100):
		self.data[0]['watchdog'] = count
		

