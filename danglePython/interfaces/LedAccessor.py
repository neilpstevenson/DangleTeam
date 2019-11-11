from ControlInterface import ControlInterface

class LedAccessor(ControlInterface):
	""" Class to set a value to an LED or similar display via the IPC provided
	"""
	
	def __init__(self, simpleControlsIPC, led):
		ControlInterface.__init__(self)
		self.led = led
		self.simpleControlsIPC = simpleControlsIPC
		
	def setValue(self, value):
		self.simpleControlsIPC.setValue(self.led, value)
	