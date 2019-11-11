from SensorInterface import SensorInterface

class Roll(SensorInterface):
	""" Accessor to get the current roll (left/right) angle of the MPU sensor
	This is returned in degrees from the horizontal.
	"""
	
	def __init__(self, mpu):
		SensorInterface.__init__(self)
		self.mpu = mpu
		
	def getValue(self):
		return self.mpu.getRollDegrees()

	