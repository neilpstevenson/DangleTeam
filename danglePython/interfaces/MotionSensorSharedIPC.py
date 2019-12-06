import sys, math, numpy

class MotionSensorSharedIPC:
	def __init__(self):
		self.qw, self.qx, self.qy, self.qz = 0.0, 0.0, 0.0, 0.0
		self.sample_count = 0
		self.timeZero = 0		
		
		# From the generator process (in C):
		#struct shared_reading_struct {
		#	unsigned long timestamp;
		#	float accel[3];
		#	float gyro[3];
		#	float quaternion[4];
		#	unsigned long flags;
		#};
		#struct mmap_memory_struct {
		#	unsigned short oldest_sample;
		#	unsigned short latest_sample;
		#	unsigned short buffer_size;
		#	unsigned short dummy;
		#	struct shared_reading_struct shared_readings_buffer[SHARED_BUFFER_SIZE];
		#};
		shared_reading_dt = numpy.dtype([
								('timestamp',numpy.uint32),
								('accel',numpy.float32,(3,1)),
								('gyro',numpy.float32,(3,1)),
								('quaternion',numpy.float32,(4,1)),
								('flags',numpy.int32)])

		shared_dt = numpy.dtype([('sample_number',numpy.uint32),
								('oldest_sample',numpy.uint16),
								('latest_sample',numpy.uint16),
								('buffer_size',numpy.uint16),
								('orientation',numpy.uint8),
								('tap_count',numpy.uint8),
								('tap_direction',numpy.uint8),
								('dummy',numpy.uint8,(3,1)),
								('mag',numpy.float32,(3,1)),
								('shared_readings_buffer', shared_reading_dt, (1024,1))])
		#	('shared_readings_buffer', (('timestamp',numpy.uint32),('accel',numpy.float32,(3,1)),('gyro',numpy.float32,(3,1)),('quaternion',numpy.float32,(4,1)),('flags',numpy.int32)),(1,1024))])
		self.data  = numpy.memmap('/dev/shm/mpu_values_shared.mmf', offset=0, dtype=shared_dt, mode='r')

	def updateReading(self):
		self.sample_count += 1
		latest = self.data[0]['latest_sample']
		self.sample_number = self.data[0]['sample_number']
		latest_sample = self.data[0]['shared_readings_buffer'][latest][0]
		self.timestamp=latest_sample['timestamp'] # Sample number
		self.ax=latest_sample['accel'][0]	# Acceleromtere values
		self.ay=latest_sample['accel'][1]
		self.az=latest_sample['accel'][2]
		self.gx=latest_sample['gyro'][0] # Gyro values
		self.gy=latest_sample['gyro'][1]
		self.gz=latest_sample['gyro'][2]
		self.qw=latest_sample['quaternion'][0] # Quaternium values
		self.qx=latest_sample['quaternion'][1]
		self.qy=latest_sample['quaternion'][2]
		self.qz=latest_sample['quaternion'][3]
		self.flags=latest_sample['flags'] # Flags
		self.orientation = self.data[0]['orientation']
		self.tap_count = self.data[0]['tap_count']
		self.tap_direction = self.data[0]['tap_direction']
		self.mx = self.data[0]['mag'][0]
		self.my = self.data[0]['mag'][1]
		self.mz = self.data[0]['mag'][2]
		if self.timeZero == 0:
			self.timeZero = self.timestamp	# Baseline the time

	def updateBufferedReadings(self):
		# Simply take a copy of the readings
		latest = self.data[0]['latest_sample']
		oldest = self.data[0]['oldest_sample']
		tmp_readings_buffer = self.data[0]['shared_readings_buffer']
		if latest > oldest:
			# simple split
			self.readings_buffer = tmp_readings_buffer[oldest:latest]
		else:
			if latest == 0:
				# simple split
				self.readings_buffer = tmp_readings_buffer[1::oldest]
			else:
				self.readings_buffer = numpy.concatenate((tmp_readings_buffer[oldest:], tmp_readings_buffer[0:latest-1]))
	
	# Convert Quaternion to Euler angles helpers
	def getRollDegrees(self):
		# roll (x-axis rotation)
		sinr_cosp = +2.0 * (self.qw * self.qx + self.qy * self.qz)
		cosr_cosp = +1.0 - 2.0 * (self.qx * self.qx + self.qy * self.qy)
		return math.atan2(sinr_cosp, cosr_cosp) * 180.0/numpy.pi

#	def getPitchDegrees(self):
#		# pitch (y-axis rotation)
#		sinr_cosp = +2.0 * (self.qw * self.qy + self.qx * self.qz)
#		cosr_cosp = +1.0 - 2.0 * (self.qy * self.qy + self.qx * self.qx)
#		return math.atan2(sinr_cosp, cosr_cosp) * 180.0/numpy.pi


	def getPitchDegrees(self):
		# This is to cope with "gimbol lock"
		# pitch (y-axis rotation)
		sinp = +2.0 * (self.qw * self.qy - self.qz * self.qx)
		if (math.fabs(sinp) >= 1) :
			return math.copysign(numpy.pi / 2, sinp) * 180.0/numpy.pi # use 90 degrees if out of range
		else :
			return math.asin(sinp) * 180.0/numpy.pi

	def getYawDegrees(self):
		# yaw (z-axis rotation)
		siny_cosp = +2.0 * (self.qw * self.qz + self.qx * self.qy)
		cosy_cosp = +1.0 - 2.0 * (self.qy * self.qy + self.qz * self.qz)
		return math.atan2(siny_cosp, cosy_cosp) * 180.0/numpy.pi

	def get_quaternion(self):
		return (self.qw, self.qx, self.qy, self.qz)
		
	def get_accel(self):
		return (self.ax, self.ay, self.az)
		
	def get_gyro(self):
		return (self.gx, self.gy, self.gz)

	def get_flags(self):
		return self.flags

	def get_sample_count(self):
		return self.sample_count
		
	def get_sample_number(self):
		return self.sample_number
		
	def get_timestampMs(self):
		return self.timestamp-self.timeZero
	
	def get_timestamp(self):
		return float(self.get_timestampMs()) / 1000.0
	
	def get_pitchBufferedReadingsDegrees(self,sample_interval=1):
		out = []
		for reading in self.readings_buffer[::sample_interval]:
			 # Get the Quaternium values as "current"
			self.qw=reading[0]['quaternion'][0]
			self.qx=reading[0]['quaternion'][1]
			self.qy=reading[0]['quaternion'][2]
			self.qz=reading[0]['quaternion'][3]
			out.append(self.getPitchDegrees())
		return out
		
	def get_compassDegrees(self):
		return math.atan2(float(self.my), float(self.mx)) * 180.0/numpy.pi

	def get_tap_count(self):
		return self.tap_count
		
	def get_orientation(self):
		return self.orientation