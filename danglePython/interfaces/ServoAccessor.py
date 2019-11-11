from interfaces.ControlInterface import ControlInterface

class ServoAccessor(ControlInterface):
	""" Class to set a value to a servo to a fixed position
		-1.0 = Clockwise extreme
		1.0 = Anticlockwise extreme
	"""
	
	def __init__(self, servosIPC, servo):
		ControlInterface.__init__(self)
		self.servo = servo
		self.servosIPC = servosIPC
		
	def setValue(self, value):
		if value < -1.0:
			value = -1.0
		elif value > 1.0:
			value = 1.0
		self.servosIPC.setPosition(self.servo, value)
