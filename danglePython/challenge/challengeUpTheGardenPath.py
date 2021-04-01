from simple_pid import PID

# Interfaces
from interfaces.ChallengeInterface import ChallengeInterface
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.VisionAccessFactory import VisionAccessFactory
from interfaces.VoiceRecognitionSharedIPC import VoiceRecognitionSharedIPC
from interfaces.StatusSharedIPC import StatusSharedIPC
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

class ChallengeUpTheGardenPath(ChallengeInterface):

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		self.vision = VisionAccessFactory.getSingleton()
		# Voice command
		self.voice = VoiceRecognitionSharedIPC()
		self.voice.read()
		# Status shared memory
		self.status = StatusSharedIPC()
		self.status.create()
		# Get config
		config = Config()
		self.pidP , self.pidI, self.pidD = config.get("garden.pid.p", (0.015, 0.0, 0.0012))	# Note: PID output is also limited ot +/-1.0
		self.proportionalOnMeasure = config.get("garden.pid.pom", False)
		self.maxForward = config.get("garden.forward.max", 0.5)	# Joystick-controlled max speed
		self.maxManualTurn = config.get("garden.manualturn.max", -15.0) # Joystick-controlled max turn angle (mpu heading relative)
		self.maxHeadingTurn = config.get("garden.headingturn.max", 0.7) # PID output scaling (manual mode)
		self.maxAutoTurn = config.get("garden.autoturn.max", 0.7) # PID output scaling (full auto mode)
		self.constantSpeed = config.get("garden.speed", 0.3) # Speed in full auto mode
		self.constantSpeedFast = config.get("garden.speedfast", 0.5) # Speed "fast" in full auto mode
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
		self.fullAutoForwardSpeed = FixedValue(0.0)
		self.motorEnable = self.sensors.button(4)
		self.fullAutoEnable = ToggleButtonValue(self.sensors.button(5), triggeredValue = 3)
		self.joystickForward = self.sensors.joystickAxis(1)
		self.joystickLeftRight = self.sensors.joystickAxis(3)
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											[SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = -self.maxHeadingTurn))],  \
																						 # Choice 2 = Auto mode, but manual forward speed
											[SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = -self.maxAutoTurn))],  \
																						 # Choice 3 = Full Auto mode
											[SpeedDirectionCombiner(self.fullAutoForwardSpeed, Scaler(self.headingError, scaling = -self.maxAutoTurn))]  \
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
											[SpeedDirectionCombiner(self.fullAutoForwardSpeed, Scaler(self.headingError, scaling = self.maxAutoTurn), scaling = 1.0)]  \
										   ],
											self.controls.motor(1), \
											ValueAdder([self.motorEnable,self.fullAutoEnable], max=3) )
		highPriorityProcesses.append(motorR)

		# LED display state
		self.ledIndicator = self.controls.led(0)
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.motorEnable, scaling=2, offset=2, max=4), self.ledIndicator))

		# Initial status
		self.status.setStatus(f"Up the", "Garden Path", "Ready")

	def move(self):
		if self.fullAutoEnable.getValue() > 0:
			if not self.pidHeading.auto_mode:
				self.pidHeading.auto_mode = True
			# Voice commands
			voiceCommand = self.voice.findLastSpokenWord(['left','right','go', 'fast', 'any', 'stop'])
			print(f"voiceCommand: {voiceCommand}")
			if voiceCommand == 'right' or voiceCommand == 'left' or voiceCommand == 'go' or voiceCommand == 'any':
				self.fullAutoForwardSpeed.setValue(self.constantSpeed)
			elif voiceCommand == 'fast':
				self.fullAutoForwardSpeed.setValue(self.constantSpeedFast)
			elif voiceCommand == 'stop':
				self.fullAutoForwardSpeed.setValue(0.0)
				self.fullAutoEnable.reset()
				# Maintain position
				self.pidHeading.auto_mode = False
				self.headingError.setTarget(self.sensors.yaw().getValue())
			if voiceCommand is not None and voiceCommand != "":
				self.status.setStatus(voiceCommand)
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
			# Maintain position
			self.pidHeading.auto_mode = False
			self.headingError.setTarget(self.sensors.yaw().getValue())
	
	def stop(self):
		''' Stop the challenge
		'''
		self.motorEnable.setValue(0, status=0)
		
