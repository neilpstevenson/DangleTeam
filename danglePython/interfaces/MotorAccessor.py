from interfaces.ControlInterface import ControlInterface

class MotorAccessor(ControlInterface):
	""" Class to set a value to a motor via the IPC provided
	"""
	
	def __init__(self, motorsIPC, motor):
		ControlInterface.__init__(self)
		self.motorsIPC = motorsIPC
		self.motor = motor
		
	def setValue(self, value):
		#print(f"MotorAccessor[{self.motor}]: {value}")
		self.motorsIPC.setRequiredTorque(self.motor, value)

	def getValue(self):
		return self.motorsIPC.getRequiredTorque(self.motor)
	
