from interfaces.SensorInterface import SensorInterface

class Yaw(SensorInterface):
	""" Accessor to get the current yaw (heading) angle of the MPU sensor
	This is returned in degrees from the nominal North.
	"""
	
	def __init__(self, mpu):
		SensorInterface.__init__(self)
		self.mpu = mpu
		
	def getValue(self):
		return self.mpu.getYawDegrees()

	