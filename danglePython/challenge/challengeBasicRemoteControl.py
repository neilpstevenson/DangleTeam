# Interfaces
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

class ChallengeBasicRemoteControl:

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# LED display state
		self.ledIndicator = self.controls.led(0)
		medPriorityProcesses.append(Scaler(self.ledIndicator, scaling=2, offset=2))

		# Camera angle servo
		cameraTiltServo = self.controls.servo(6)
		currentPitch = Scaler(self.sensors.pitch(), scaling = -0.015)
		cameraUpDownButtons = ValueIntegrator(self.sensors.upDownButton(2, 0), scaling = -0.01, min=-0.85, max=0.85, offset = 0.5)
		cameraLeveller = SimpleControlMediator( Scaler([currentPitch, cameraUpDownButtons], min=-0.9, max=0.85 ), \
												cameraTiltServo )
		highPriorityProcesses.append(cameraLeveller)
		
		# Grabber hand servo
		grabberServo = self.controls.servo(5)
		grabReleaseButtons = ValueIntegrator(self.sensors.upDownButton(1, 3), min = -0.8, max = 0.6, scaling = 0.2)
		grabber = SimpleControlMediator( grabReleaseButtons, grabberServo )
		medPriorityProcesses.append(grabber)

		# Zgun
		zgunUpDownButtons = ValueIntegrator(self.sensors.upDownButton(13, 14), min = -1.0, max = 1.0, scaling = 0.005)
		zgunElevationServo = self.controls.servo(0)
		zgunElevation = SimpleControlMediator( zgunUpDownButtons, zgunElevationServo )
		highPriorityProcesses.append(zgunElevation)
		
		zgunTrigger = self.sensors.button(6)
		zgunFireMotor = self.controls.motor(0)
		zgunFire = SimpleControlMediator( zgunTrigger, zgunFireMotor )
		medPriorityProcesses.append(zgunFire)
		
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

		running = False
		
	def move(self):
		pass
		#	running = (self.motorEnable.getValue() > 0)
		#	if running:
		#		self.ledIndicator.setValue(0x04)
		#	else:
		#		self.ledIndicator.setValue(0x02)
