from interfaces.ControlInterface import ControlInterface

class MotorModeAccessor(ControlInterface):
	""" Class to control the mode of a motor via the IPC provided
	"""
	
	def __init__(self, motorsIPC, motor):
		ControlInterface.__init__(self)
		self.motorsIPC = motorsIPC
		self.motor = motor
		
	def setValue(self, value):
		#print(f"set MotorModeAccessor[{self.motor}]: {value}")
		self.motorsIPC.setMode(self.motor, value)

	def getValue(self):
		#print(f"get MotorModeAccessor[{self.motor}]: {self.motorsIPC.getMode(self.motor)}")
		return self.motorsIPC.getMode(self.motor)
	
