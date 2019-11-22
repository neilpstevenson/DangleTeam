import numpy as np

class SensorsSharedIPC:
	''' Shared memory structure to return simple sensor data.
		Three types of sensors are currently supported:
			Analog - These include Distance sensors, ADCs and Joystick axes.  Where a finite range is produced, 
					 they return a value between -1.0 to and +1.0.  Distance sensors produce a real-world value in metres.
			and take a value
			Digital - Generally 0 or 1 for on/off, such as switches.  Some may be tri-state or multi-state values -32768 to 32767.
			Counters - These are integer-based, and generally increase or decrease in response to external stimuli, such 
			as quadature encoders.  It also returns a rate-of-change in counts/second (note: only really valid for rapid 
			changing sensors)
		Watchdog should be decremented on each read in any control loop and if reaches zero, the sensor values should be treated as 
		unreliable (probably crashed) and set motors etc. into safe mode.  Set to 100 for 1 second protection.
	'''
	sensor_analog_dt = np.dtype([
					('status', np.uint16),	# 0=no value, 1=valid value
					('timestamp', np.float64 ),
					('value', np.float32)])
	sensor_digital_dt = np.dtype([
					('status', np.uint16),	# 0=no value, 1=valid value
					('timestamp', np.float64 ),
					('value', np.int16)])
	sensor_counter_dt = np.dtype([
					('status', np.uint16),	# 0=no value, 1=valid value
					('timestamp', np.float64 ),
					('value', np.int64),
					('rateOfChange', np.float32)])
	servos_shared_dt = np.dtype([
					('watchdog', np.uint16),
					('analog', sensor_analog_dt, (32)),
					('digital', sensor_digital_dt, (32)),
					('counter', sensor_counter_dt, (32))])
	filename = '/dev/shm/sensors_shared.mmf'
	
	def create(self):
		# Create/overwrite
		self.data  = np.memmap(SensorsSharedIPC.filename, offset=0, dtype=SensorsSharedIPC.servos_shared_dt, mode='w+', shape=(1))
	
	def open(self):
		# Read/write (no create)
		self.data  = np.memmap(SensorsSharedIPC.filename, offset=0, dtype=SensorsSharedIPC.servos_shared_dt, mode='r+')

	def checkWatchdog(self):
		if self.data[0]['watchdog'] > 0:
			# countdown
			self.data[0]['watchdog'] -= 1
		return self.data[0]['watchdog']
	def resetWatchdog(self, count = 100):
		self.data[0]['watchdog'] = count
		
	def setAnalogValue(self, sensor, value, status=1, timestamp = 0):
		self.data[0]['analog'][sensor]['value'] = value
		self.data[0]['analog'][sensor]['status'] = status
		self.data[0]['analog'][sensor]['timestamp'] = timestamp
	def getAnalogValue(self, sensor):
		return self.data[0]['analog'][sensor]['value'].copy()
	def getAnalogStatus(self, sensor):
		return self.data[0]['analog'][sensor]['status'].copy()
	def getAnalogTimestamp(self, sensor):
		return self.data[0]['analog'][sensor]['timestamp'].copy()

	def setDigitalValue(self, sensor, value, status=1, timestamp = 0):
		self.data[0]['digital'][sensor]['value'] = value
		self.data[0]['digital'][sensor]['status'] = status
		self.data[0]['digital'][sensor]['timestamp'] = timestamp
	def getDigitalValue(self, sensor):
		return self.data[0]['digital'][sensor]['value'].copy()
	def getDigitalStatus(self, sensor):
		return self.data[0]['digital'][sensor]['status'].copy()
	def getDigitalTimestamp(self, sensor):
		return self.data[0]['digital'][sensor]['timestamp'].copy()
		
	def setCounterValue(self, sensor, value, status=1, timestamp = 0):
		# Work out rate of change
		if timestamp == 0:
			# No timestamps
			self.data[0]['counter'][sensor]['value'] = value
			self.data[0]['counter'][sensor]['status'] = status
			self.data[0]['counter'][sensor]['timestamp'] = 0
			self.data[0]['counter'][sensor]['rateOfChange'] = 0
		elif timestamp != self.data[0]['counter'][sensor]['timestamp']:
			self.data[0]['counter'][sensor]['rateOfChange'] = (value-self.data[0]['counter'][sensor]['value']) / (timestamp - self.data[0]['counter'][sensor]['timestamp'])
			self.data[0]['counter'][sensor]['value'] = value
			self.data[0]['counter'][sensor]['status'] = status
			self.data[0]['counter'][sensor]['timestamp'] = timestamp
	def getCounterValue(self, sensor):
		return self.data[0]['counter'][sensor]['value'].copy()
	def getCounterStatus(self, sensor):
		return self.data[0]['counter'][sensor]['status'].copy()
	def getCounterTimestamp(self, sensor):
		return self.data[0]['counter'][sensor]['timestamp'].copy()
	def getCounterRateOfChange(self, sensor):
		return self.data[0]['counter'][sensor]['rateOfChange'].copy()
		
		
