from interfaces.SensorInterface import SensorInterface

class ImageResult(SensorInterface):
	""" Class to get the resuts of a vision-based heading analysis.  
	"""
	
	def __init__(self, visionIPC):
		SensorInterface.__init__(self)
		self.visionIPC = visionIPC
		
	def getValue(self):
		#print(f"yaw: {self.visionIPC.getYaw(0)}")
		return self.visionIPC.getYaw(0)
			
	def getStatus(self):
		#print(f"{self.visionIPC.getTypeName(0)}:{self.visionIPC.getName(0)}: status: {self.visionIPC.getStatus(0)}")
		return self.visionIPC.getStatus(0)
			
	def getDistance(self):
		#print(f"distance: {self.visionIPC.getDistance(0)}")
		return self.visionIPC.getDistance(0)
			
