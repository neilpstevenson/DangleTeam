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


class ChallengeLavaPalava(ChallengeInterface):

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
		self.pidP = config.get("lava.pid.p", 0.015)	# Note: PID output is also limited ot +/-1.0
		self.pidI = config.get("lava.pid.i", 0.0) #0.001)
		self.pidD = config.get("lava.pid.d", 0.0012)
		self.proportionalOnMeasure = config.get("lava.pid.pom", False)
		self.maxForward = config.get("lava.forward.max", 1.0)	# Joystick-controlled max speed
		self.maxManualTurn = config.get("lava.manualturn.max", -15.0) # Joystick-controlled max turn angle (mpu heading relative)
		self.maxHeadingTurn = config.get("lava.headingturn.max", 0.6) # PID output scaling (manual mode)
		self.maxAutoTurn = config.get("lava.autoturn.max", 0.3) # PID output scaling (full auto mode)
		self.constantSpeed = config.get("lava.speed", 0.6) # Speed in full auto mode
		self.cameraTilt = config.get("lava.camera.tilt", 0.5)
		config.save()

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Yaw control
		yaw = self.sensors.yaw()
		self.pidHeading = PID(self.pidP, self.pidI, self.pidD, sample_time=0.008, proportional_on_measurement=self.proportionalOnMeasure, output_limits=(-1.0, 1.0))
		self.headingError = HeadingPIDErrorValue(yaw, self.pidHeading, yaw.getValue())
		# Initialise the PID
		self.headingError.getValue()
		
		# Vision
		self.visionTargetHeading = self.vision.getLineHeading()

		# Motors
		motorsStop = FixedValue(0.0)
		fullAutoForwardSpeed = FixedValue(self.constantSpeed)
		self.motorEnable = self.sensors.button(4)
		self.fullAutoEnable = ToggleButtonValue(self.sensors.button(5), triggeredValue = 2)
		self.joystickForward = self.sensors.joystickAxis(1)
		self.joystickLeftRight = self.sensors.joystickAxis(3)
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											[SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = -self.maxHeadingTurn))],  \
																						 # Choice 2 = Auto mode, but manual forward speed
											[SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = -self.maxAutoTurn))],  \
																						 # Choice 3 = Full Auto mode
											[SpeedDirectionCombiner(fullAutoForwardSpeed, Scaler(self.headingError, scaling = -self.maxAutoTurn))]  \
										   ],
											self.controls.motor(2), \
											ValueAdder([self.motorEnable,self.fullAutoEnable], max=3) )
		self.speedSensorL = self.sensors.counter(0)
		highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
																						 # Choice 1 = Manual Controlled only
											[Scaler(SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = self.maxHeadingTurn)), scaling = 1.0)],  \
																						 # Choice 2 = Auto mode, but manual forward speed
											[Scaler(SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = self.maxAutoTurn)), scaling = 1.0)],  \
																						 # Choice 3 = Full Auto mode
											[SpeedDirectionCombiner(fullAutoForwardSpeed, Scaler(self.headingError, scaling = self.maxAutoTurn), scaling = 1.0)]  \
										   ],
											self.controls.motor(1), \
											ValueAdder([self.motorEnable,self.fullAutoEnable], max=3) )
		highPriorityProcesses.append(motorR)

		# LED display state
		self.ledIndicator = self.controls.led(0)
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.motorEnable, scaling=2, offset=2, max=4), self.ledIndicator))
		
		# LED eyes
		self.ledEyeLeft = self.controls.led(20)
		self.ledEyeRight = self.controls.led(21)
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.motorEnable, scaling=255), self.ledEyeLeft))
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.fullAutoEnable, scaling=255), self.ledEyeRight))
		
		# Common controls
		self.grabberControl.createProcesses(highPriorityProcesses, medPriorityProcesses)
		self.cameraLevellingControl.createProcesses(highPriorityProcesses, medPriorityProcesses, self.cameraTilt)
		self.zGunControl.createProcesses(highPriorityProcesses, medPriorityProcesses)

	def move(self):
		if self.fullAutoEnable.getValue() > 0:
			if not self.pidHeading.auto_mode:
				self.pidHeading.auto_mode = True
			# Vision turns
			self.headingError.setTarget(self.visionTargetHeading.getValue())
			print(self.pidHeading.components)
		elif self.motorEnable.getValue() > 0:
			if not self.pidHeading.auto_mode:
				self.pidHeading.auto_mode = True
			# Manual turns
			if self.joystickLeftRight.getValue() != 0.0:
				self.headingError.setTarget(self.sensors.yaw().getValue() + self.joystickLeftRight.getValue() * self.maxManualTurn)
			print(f"Err: {self.headingError.getValue()}")
			print(self.pidHeading.components)
		else:
			# No change in position
			self.pidHeading.auto_mode = False
			self.headingError.setTarget(self.sensors.yaw().getValue())
	
	def stop(self):
		''' Stop the challenge
		'''
		self.motorEnable.setValue(0, status=0)
		
