from interfaces.ControlMediatorInterface import ControlMediatorInterface

class SwitchingControlMediator(ControlMediatorInterface):
	""" Class to simply copy one or more sensor values to a controller, e.g. joystick axis to motor
		but dependent on another input for the source
	"""
	
	def __init__(self, inputChoices, control, choice):
		self.inputChoices = inputChoices
		self.control = control
		self.choice = choice
		
	def process(self):
		input = self.inputChoices[self.choice.getValue()]
		if type(input) is list:
			self.control.setValue( sum(map(lambda x: x.getValue(), input)) )
		else:
			self.control.setValue( input.getValue() )
	