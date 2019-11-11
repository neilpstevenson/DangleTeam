from interfaces.SensorInterface import SensorInterface

class Pitch(SensorInterface):
	""" Accessor to get the current pitch (nose-up) angle of the MPU sensor
	This is returned in degrees from the horizontal.
	"""
	
	def __init__(self, mpu):
		SensorInterface.__init__(self)
		self.mpu = mpu
		
	def getValue(self):
		return self.mpu.getPitchDegrees()

	