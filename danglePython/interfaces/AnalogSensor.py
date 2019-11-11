from interfaces.SensorInterface import SensorInterface

class AnalogSensor(SensorInterface):
	""" Class to get an analog sensor reading. 
	"""
	
	def __init__(self, sensorIPC, sensor):
		SensorInterface.__init__(self)
		self.sensorIPC = sensorIPC
		self.sensor = sensor
		
	def getValue(self):
		return self.sensorIPC.getAnalogValue(self.sensor)
	