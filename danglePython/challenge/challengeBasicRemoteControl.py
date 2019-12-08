# Interfaces
from interfaces.ChallengeInterface import ChallengeInterface
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
# Value providers
from analysis.SimplePIDErrorValue import SimplePIDErrorValue
from analysis.HeadingPIDErrorValue import HeadingPIDErrorValue
from analysis.OneShotButtonValue import OneShotButtonValue
from analysis.FixedValue import FixedValue
# Value combination helpers
from analysis.Scaler import Scaler
from analysis.ValueIntegrator import ValueIntegrator
from analysis.ValueAdder import ValueAdder
from analysis.ValueLambda import ValueLambda
# Control mediators
from challenge.SimpleControlMediator import SimpleControlMediator
from challenge.SwitchingControlMediator import SwitchingControlMediator
# Common controls
from challenge.grabberControl import GrabberControl
from challenge.cameraLevellingControl import CameraLevellingControl
from challenge.zGunControl import ZGunControl


class ChallengeBasicRemoteControl(ChallengeInterface):

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		# Common controls
		self.grabberControl = GrabberControl()
		self.cameraLevellingControl = CameraLevellingControl()
		self.zGunControl = ZGunControl()


	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Motors
		motorsStop = FixedValue(0.0)
		self.motorEnable = self.sensors.button(4)
		joystickForward = self.sensors.joystickAxis(1)
		joystickLeftRight = self.sensors.joystickAxis(3)
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											#[ValueLambda(Scaler(joystickForward, scaling =  0.9)), ValueLambda(Scaler(joystickLeftRight, scaling = -0.5))]	# Joystick  \
											[ValueLambda([Scaler(joystickForward, scaling =  0.9), Scaler(joystickLeftRight, scaling = -0.5)])]	# Joystick  \
										   ],
											self.controls.motor(2), \
											self.motorEnable )
		self.speedSensorL = self.sensors.counter(0)
		highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
																						 # Choice 1 = Controlled
											#[ValueLambda(Scaler(joystickForward, scaling = -0.9)), ValueLambda(Scaler(joystickLeftRight, scaling = -0.5))]  # Joystick \
											[ValueLambda([Scaler(joystickForward, scaling = -0.9), Scaler(joystickLeftRight, scaling = -0.5)])]	# Joystick  \
										   ],
											self.controls.motor(1), \
											self.motorEnable )
		highPriorityProcesses.append(motorR)

		# LED display state
		self.ledIndicator = self.controls.led(0)
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.motorEnable, scaling=2, offset=2, max=4), self.ledIndicator))
		
		# Common controls
		self.grabberControl.createProcesses(highPriorityProcesses, medPriorityProcesses)
		self.cameraLevellingControl.createProcesses(highPriorityProcesses, medPriorityProcesses)
		self.zGunControl.createProcesses(highPriorityProcesses, medPriorityProcesses)

		
	def stop(self):
		''' Stop the challenge
		'''
		self.motorEnable.setValue(0, status=0)
		