from interfaces.ControlInterface import ControlInterface

class MotorSpeed(ControlInterface):
	""" Class to set a value to a motor via the IPC provided
	"""
	
	def __init__(self, motorsIPC, motor):
		ControlInterface.__init__(self)
		self.motorsIPC = motorsIPC
		self.motor = motor
		
	def setValue(self, value):
		print(f"MotorControl[{self.motor}]: {value}")
		self.motorsIPC.setRequiredSpeed(self.motor, value)

	def getValue(self):
		return self.motorsIPC.getCurrentSpeed(self.motor)
	
