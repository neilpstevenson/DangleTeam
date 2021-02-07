from simple_pid import PID

# Interfaces
from interfaces.ChallengeInterface import ChallengeInterface
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.VisionAccessFactory import VisionAccessFactory
from interfaces.Config import Config
# Value providers
from analysis.SimplePIDErrorValue import SimplePIDErrorValue
from analysis.HeadingPIDErrorValue import HeadingPIDErrorValue
from analysis.OneShotButtonValue import OneShotButtonValue
from analysis.ToggleButtonValue import ToggleButtonValue
from analysis.TimedTriggerValue import TimedTriggerValue
from analysis.FixedValue import FixedValue
# Value combination helpers
from analysis.Scaler import Scaler
from analysis.ValueIntegrator import ValueIntegrator
from analysis.ValueAdder import ValueAdder
from analysis.ValueLambda import ValueLambda
from analysis.SpeedDirectionCombiner import SpeedDirectionCombiner
# Control mediators
from challenge.SimpleControlMediator import SimpleControlMediator
from challenge.SwitchingControlMediator import SwitchingControlMediator
# Common controls
from challenge.grabberControl import GrabberControl
from challenge.cameraLevellingControl import CameraLevellingControl
from challenge.zGunControl import ZGunControl


class ChallengeTestAbsolute(ChallengeInterface):

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		self.vision = VisionAccessFactory.getSingleton()
		# Common controls
		self.grabberControl = GrabberControl()
		self.cameraLevellingControl = CameraLevellingControl()
		self.zGunControl = ZGunControl()
		# Get config
		config = Config()
		self.pidConstants = config.get("motor.position.pid", [0.001, 0.0, 0.001])	# Note: PID output is also limited to +/-1.0
		self.proportionalOnMeasure = config.get("motor.position.pid.pom", False)
		self.maxForward = config.get("motor.position.forward.max", 1.0)	# Joystick-controlled max speed
		self.maxPidForward = config.get("motor.position.pidforward.max", 0.4)	# PID-controlled max speed
		config.save()

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		
		# Set up the PIDs for the two motors
		self.pidL = PID(self.pidConstants[0], self.pidConstants[1], self.pidConstants[2], sample_time=0.05, proportional_on_measurement=self.proportionalOnMeasure, output_limits=(-1.0, 1.0))
		self.motorL = self.controls.motor(2)
		self.positionL = self.controls.motorPosition(2)
		self.motorPositionErrorL = SimplePIDErrorValue(self.pidL, self.positionL)
		self.targetPositionL = self.positionL.getValue()
		self.motorPositionErrorL.setTarget(self.targetPositionL)
		self.motorPositionErrorL.getValue()
		
		self.pidR = PID(self.pidConstants[0], self.pidConstants[1], self.pidConstants[2], sample_time=0.05, proportional_on_measurement=self.proportionalOnMeasure, output_limits=(-1.0, 1.0))
		self.motorR = self.controls.motor(1)
		self.positionR = self.controls.motorPosition(1)
		self.motorPositionErrorR = SimplePIDErrorValue(self.pidR, self.positionR)
		self.targetPositionR = self.positionR.getValue()
		self.motorPositionErrorR.setTarget(self.targetPositionR)
		self.motorPositionErrorR.getValue()

		# Motor control - General
		motorsStop = FixedValue(0.0)
		self.motorEnable = self.sensors.button(4)
		self.fullAutoEnable = ToggleButtonValue(self.sensors.button(5), triggeredValue = 2)
		self.joystickForward = self.sensors.joystickAxis(1)
		self.joystickLeftRight = self.sensors.joystickAxis(3)

		self.motorLSimpleManualSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.joystickLeftRight, scaling = self.maxForward))]
		self.motorRSimpleManualSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.joystickLeftRight, scaling = -self.maxForward))]
		
		self.motorLSimplePositionSpeed = [SpeedDirectionCombiner(Scaler([self.joystickForward,self.motorPositionErrorL], scaling = self.maxForward), Scaler([Scaler(self.motorPositionErrorR, scaling = -1.0),self.motorPositionErrorL], scaling = self.maxPidForward))]
		self.motorRSimplePositionSpeed = [SpeedDirectionCombiner(Scaler([self.joystickForward,self.motorPositionErrorR], scaling = self.maxForward), Scaler([Scaler(self.motorPositionErrorL, scaling = -1.0),self.motorPositionErrorR], scaling = self.maxPidForward))]									
		
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											self.motorLSimpleManualSpeed,  \
																						 # Choice 2 = Auto mode, but manual forward speed
											self.motorLSimplePositionSpeed  \
																						 # Choice 3 = Full Auto mode
											#[SpeedDirectionCombiner(fullAutoForwardSpeed, Scaler(self.motorPositionErrorL, scaling = -self.maxForward))]  \
										   ],
											self.controls.motor(2), \
											ValueAdder([self.motorEnable,self.fullAutoEnable], max=2) )
		#self.speedSensorL = self.sensors.counter(0)
		highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
																						 # Choice 1 = Manual Controlled only
											self.motorRSimpleManualSpeed,  \
																						 # Choice 2 = Auto mode, but manual forward speed
											self.motorRSimplePositionSpeed \
																						 # Choice 3 = Full Auto mode
											#[SpeedDirectionCombiner(fullAutoForwardSpeed, Scaler(self.motorPositionErrorR, scaling = self.maxAutoTurn), scaling = 1.0)]  \
										   ],
											self.controls.motor(1), \
											ValueAdder([self.motorEnable,self.fullAutoEnable], max=2) )
		highPriorityProcesses.append(motorR)

		# LED display state
		self.ledIndicator = self.controls.led(0)
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.motorEnable, scaling=2, offset=2, max=4), self.ledIndicator))
		
	def move(self):
		if self.fullAutoEnable.getValue() > 0:
			if not self.pidL.auto_mode:
				# Switch back on the PIDs
				self.pidL.auto_mode = True
				self.pidR.auto_mode = True
			# Update targets
			self.motorPositionErrorL.setTarget(self.targetPositionL)
			self.motorPositionErrorR.setTarget(self.targetPositionR)
		else:
			# Switch off the PIDs - No change in position
			self.pidL.auto_mode = False
			self.targetPositionL = self.positionL.getValue()
			self.motorPositionErrorL.setTarget(self.targetPositionL)
			self.pidR.auto_mode = False
			self.targetPositionR = self.positionR.getValue()
			self.motorPositionErrorR.setTarget(self.targetPositionR)

	def stop(self):
		''' Stop the challenge
		'''
		self.motorEnable.setValue(0, status=0)
		
