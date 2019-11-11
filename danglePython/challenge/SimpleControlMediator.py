from ../interfaces/ControlMediatorInterface import ControlMediatorInterface

class SimpleControlMediator(ControlMediatorInterface):
	""" Class to simply copy one or more sensor values to a controller, e.g. joystick axis to motor
	"""
	
	def __init__(self, input, control):
		self.input = input
		self.control = control
		
	def process(self):
		if type(self.input) is list:
			self.control.setValue( sum(map(lambda x: x.getValue(), self.input)) )
		else:
			self.control.setValue( self.input.getValue() )
	