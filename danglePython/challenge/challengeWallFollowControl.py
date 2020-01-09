from simple_pid import PID

# Interfaces
from interfaces.ChallengeInterface import ChallengeInterface
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
#from interfaces.VisionAccessFactory import VisionAccessFactory
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


class ChallengeWallFollowControl(ChallengeInterface):

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		#self.vision = VisionAccessFactory.getSingleton()
		# Common controls
		self.grabberControl = GrabberControl()
		self.cameraLevellingControl = CameraLevellingControl()
		self.zGunControl = ZGunControl()
		# Get config
		config = Config()
		self.pidP = config.get("heading.pid.p", 0.06)
		self.pidI = config.get("heading.pid.i", 0.001)
		self.pidD = config.get("heading.pid.d", 0.004)
		self.proportionalOnMeasure = config.get("heading.pid.pom", False)
		self.maxForward = config.get("heading.forward.max", 1.0)
		self.maxManualTurn = config.get("heading.manualturn.max", -15.0)
		self.maxHeadingTurn = config.get("heading.headingturn.max", 0.5)
		self.constantSpeed = config.get("lava.speed", 0.7)
		self.cameraTilt = config.get("lava.camera.tilt", 0.5)
		config.save()
		# define the state machine to control our behaviour
		self.states = { 0: self.moveManual,
						1: self.moveFindWall,
						2: self.moveFollowWall,
						3: self.moveTurnLeft,
						4: self.moveTurnRight }
		self.currentState = 1

	def moveManual(self, leftDist, forwardDist, rightDist):
		pass
		
	def moveFindWall(self, leftDist, forwardDist, rightDist):
		print(f"moveFindWall: {rightDist}")
		# drift right
		self.motorConstant.setValue(self.constantSpeed)
		self.headingError.setTarget(self.sensors.yaw().getValue() - 15.0)
		
	def moveFollowWall(self, leftDist, forwardDist, rightDist):
		print(f"moveFollowWall: {rightDist}")
		self.motorConstant.setValue(self.constantSpeed)
		if rightDist > 240:
			# Move nearer right wall
			self.headingError.setTarget(self.sensors.yaw().getValue() - 5.0)
		elif rightDist < 100:
			# Move away from right wall quickly
			self.headingError.setTarget(self.sensors.yaw().getValue() + 10.0)
		elif rightDist < 160:
			# Move away from right wall
			self.headingError.setTarget(self.sensors.yaw().getValue() + 5.0)
		else:
			# Maintain heading
			self.headingError.setTarget(self.sensors.yaw().getValue())
		
	def moveTurnLeft(self, leftDist, forwardDist, rightDist):
		self.motorConstant.setValue(0.1)
		self.headingError.setTarget(self.sensors.yaw().getValue() + 20.0)
		
	def moveTurnRight(self, leftDist, forwardDist, rightDist):
		self.motorConstant.setValue(0.1)
		self.headingError.setTarget(self.sensors.yaw().getValue() - 20.0)
	
		
	def updateState(self, left, forward, right):
		if forward > 350 and left > 350 and right > 350:
			# Nothing in view, find a wall
			self.currentState = 1
		elif forward <= 350 and left > 350 and right > 350:
			# Blocked ahead, turn left and this should become a wall
			self.currentState = 3
		elif forward > 350 and left <= 350 and right > 350:
			# Too far from wall, find it
			self.currentState = 1
		elif forward > 350 and left > 350 and right <= 350:
			# Near wall, follow it
			self.currentState = 2
		elif forward > 350 and left <= 350 and right <= 350:
			# Ahead ok, follow wall
			self.currentState = 2
		elif forward <= 350 and left <= 350 and right > 350:
			# Too far from wall but ahead blocked, turn right (WILL OSCILLATE?)
			self.currentState = 4
		elif forward <= 350 and left > 350 and right <= 350:
			# Only left free, avoid
			self.currentState = 3
		elif forward <= 350 and left <= 350 and right <= 350:
			# Dead end, about turn
			self.currentState = 3
		print(f"New state: {self.currentState}")
	
	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Yaw control
		yaw = self.sensors.yaw()
		self.pidHeading = PID(self.pidP, self.pidI, self.pidD, sample_time=0.008, proportional_on_measurement=self.proportionalOnMeasure)
		self.headingError = HeadingPIDErrorValue(yaw, self.pidHeading, yaw.getValue(), min = -1.0, max = 1.0, scaling=1.0)
		# Initialise the PID
		self.headingError.getValue()
		
		# Vision
		#self.visionTargetHeading = self.vision.getLineHeading()

		# Motors
		motorsStop = FixedValue(0.0)
		self.motorConstant = FixedValue(self.constantSpeed)
		self.motorEnable = self.sensors.button(4)
		self.constantEnable = ToggleButtonValue(self.sensors.button(5))
		#self.constantEnable = TimedTriggerValue(self.sensors.button(5), 1.0, retriggerable = True)
		self.joystickForward = self.sensors.joystickAxis(1)
		self.joystickLeftRight = self.sensors.joystickAxis(3)
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											#[ValueLambda(Scaler(self.joystickForward, scaling =  0.9)), ValueLambda(Scaler(self.joystickLeftRight, scaling = -0.5))]	# Joystick  \
											#[ValueLambda([Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.joystickLeftRight, scaling = -self.maxManualTurn), Scaler(self.headingError, scaling = -self.maxHeadingTurn)])]	# Joystick  \
											#[ValueLambda([Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = -self.maxHeadingTurn)])]	# Joystick  \
											#[ValueLambda([Scaler(self.joystickForward, scaling = self.maxForward)]), Scaler(self.headingError, scaling = -self.maxHeadingTurn)]	# Joystick  \
											[SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = -self.maxHeadingTurn))],  \
											[SpeedDirectionCombiner(self.motorConstant, Scaler(self.headingError, scaling = -self.maxHeadingTurn))]  \
										   ],
											self.controls.motor(2), \
											ValueAdder([self.motorEnable,self.constantEnable], max=2) )
		self.speedSensorL = self.sensors.counter(0)
		highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
																						 # Choice 1 = Controlled
											#[ValueLambda(Scaler(self.joystickForward, scaling = -0.9)), ValueLambda(Scaler(self.joystickLeftRight, scaling = -0.5))]  # Joystick \
											#[ValueLambda([Scaler(self.joystickForward, scaling = -self.maxForward), Scaler(self.joystickLeftRight, scaling = -self.maxManualTurn), Scaler(self.headingError, scaling = -self.maxHeadingTurn)])]	# Joystick  \
											#[ValueLambda([Scaler(self.joystickForward, scaling = -self.maxForward), Scaler(self.headingError, scaling = -self.maxHeadingTurn)])]	# Joystick  \
											#[ValueLambda([Scaler(self.joystickForward, scaling = -self.maxForward)]), Scaler(self.headingError, scaling = -self.maxHeadingTurn)]	# Joystick  \
											[Scaler(SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = self.maxHeadingTurn)), scaling = 1.0)],  \
											[SpeedDirectionCombiner(self.motorConstant, Scaler(self.headingError, scaling = self.maxHeadingTurn), scaling = 1.0)]  \
										   ],
											self.controls.motor(1), \
											ValueAdder([self.motorEnable,self.constantEnable], max=2) )
		highPriorityProcesses.append(motorR)

		# LED display state
		self.ledIndicator = self.controls.led(0)
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.motorEnable, scaling=2, offset=2, max=4), self.ledIndicator))
		
		# ToF Sensors
		self.tofLeft = self.sensors.analog(16)
		self.tofForward = self.sensors.analog(17)
		self.tofRight = self.sensors.analog(18)
		
		# LED eyes
		self.ledEyeLeft = self.controls.led(20)
		self.ledEyeRight = self.controls.led(21)
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.tofLeft, scaling=-1.0, min=0.0, max=1.0, offset=200), self.ledEyeLeft))
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.tofRight, scaling=-1.0, min=0.0, max=1.0, offset=200), self.ledEyeRight))
		
		# Common controls
		self.grabberControl.createProcesses(highPriorityProcesses, medPriorityProcesses)
		self.cameraLevellingControl.createProcesses(highPriorityProcesses, medPriorityProcesses, self.cameraTilt)
		self.zGunControl.createProcesses(highPriorityProcesses, medPriorityProcesses)

	def move(self):
		if self.constantEnable.getValue() > 0:
			if not self.pidHeading.auto_mode:
				self.pidHeading.auto_mode = True
			# ToF turns
			leftDist = self.tofLeft.getValue()
			rightDist = self.tofRight.getValue()
			forwardDist = self.tofForward.getValue()
			# Update and execute state determined
			self.updateState(leftDist, forwardDist, rightDist)
			self.states[self.currentState](leftDist, forwardDist, rightDist)
			
			#rightDist = self.tofRight.getValue()
			#print(f"rightDist: {rightDist}")
			#if rightDist > 350:
			#	# Move nearer right wall
			#	self.headingError.setTarget(self.sensors.yaw().getValue() - 10.0)
			#elif rightDist < 250:
			#	# Move away from right wall
			#	self.headingError.setTarget(self.sensors.yaw().getValue() + 10.0)
			#else:
			#	# Maintain heading
			#	self.headingError.setTarget(self.sensors.yaw().getValue())
		elif self.motorEnable.getValue() > 0:
			if not self.pidHeading.auto_mode:
				self.pidHeading.auto_mode = True
			# Manual turns
			if self.joystickLeftRight.getValue() != 0.0:
				self.headingError.setTarget(self.sensors.yaw().getValue() + self.joystickLeftRight.getValue() * self.maxManualTurn)
			print(self.pidHeading.components)
		else:
			# No change in position
			self.pidHeading.auto_mode = False
			self.headingError.setTarget(self.sensors.yaw().getValue())
	
	def stop(self):
		''' Stop the challenge
		'''
		self.motorEnable.setValue(0, status=0)
		
