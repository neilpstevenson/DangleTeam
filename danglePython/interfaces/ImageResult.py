from interfaces.SensorInterface import SensorInterface

class ImageResult(SensorInterface):
	""" Class to get the resuts of a vision-based image analysis.  
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
		
	def updateSnapshot(self):
		self.imageResults = self.visionIPC.getImageResults()
		self.timestamp = self.visionIPC.getTimestamp()
		self.elapsed = self.visionIPC.getElapsed()
		return self.imageResults,self.timestamp,self.elapsed
	
	# These methods work on the last snapshot taken
	def getImageResults(self):
		return self.imageResults

	def getImageResultByType(self, typeName):
		return list(filter(lambda i: i.typename == typeName, self.imageResults))
				
	def getImageResultByNameAndType(self, name, typeName):
		return list(filter(lambda i: i.name == name and i.typename == typeName, self.imageResults))
		
	def getTimestamp(self):
		return self.timestamp
		
	def getElapsed(self):
		return self.elapsed
		
