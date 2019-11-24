from interfaces.SensorInterface import SensorInterface

class LineHeading(SensorInterface):
	""" Class to get the resuts of a vision-based heading analysis.  
	"""
	
	def __init__(self, visionIPC):
		SensorInterface.__init__(self)
		self.visionIPC = visionIPC
		
	def getValue(self):
		return self.visionIPC.getYaw()
			
