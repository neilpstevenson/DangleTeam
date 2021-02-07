from interfaces.ControlInterface import ControlInterface

class MotorPosition(ControlInterface):
	""" Class to set a value to a motor via the IPC provided
	"""
	
	def __init__(self, motorsIPC, motor):
		ControlInterface.__init__(self)
		self.motorsIPC = motorsIPC
		self.motor = motor
		
	def setValue(self, value):
		#print(f"MotorControl[{self.motor}]: {value}")
		self.motorsIPC.setCurrentPosition(self.motor, value)

	def getValue(self):
		print(f"MotorPosition[{self.motor}]: {self.motorsIPC.getCurrentPosition(self.motor)}")
		return self.motorsIPC.getCurrentPosition(self.motor)
	
