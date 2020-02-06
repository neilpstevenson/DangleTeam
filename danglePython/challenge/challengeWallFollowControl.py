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
from analysis.StateMachine import StateMachine
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
		
		self.maxHeadingTurn = config.get("wall.headingturn.max", 0.7)
		self.autoMaxSpeed = config.get("wall.speed", 0.6)
		self.cameraTilt = config.get("wall.camera.tilt", 0.3)
		self.leftRightMaxDist = config.get("wall.leftright.maxdist", 350)
		self.forwardMaxDist = config.get("wall.forward.maxdist", 350)
		self.wallDistTarget = config.get("wall.targetdist", 200)
		self.wallDistLeeway = config.get("wall.leewaydist", 40)
		self.wallDistMin = config.get("wall.mindist", 100)
		self.wallDriftAngle = config.get("wall.move.driftangle", 15)
		self.wallTurnAngle = config.get("wall.move.turnangle", 20)
		self.wallTurnSpeed = config.get("wall.move.turnspeed", 0.1)
		self.wallFollowAngleMin = config.get("wall.move.followanglemin", 5)
		self.wallFollowAngleMax = config.get("wall.move.followanglemax", 10)
		config.save()

	def ControlOff(self):
		# Stop the motors
		self.autoModeForwardSpeed.setValue(0.0)
		# stop the PID controller
		self.pidHeading.auto_mode = False
			
	def ControlOn(self):
		# reset the PID controller
		self.pidHeading.set_auto_mode(True, last_output=0.0)
		self.headingError.setTarget(self.sensors.yaw().getValue())
		self.headingError.getValue()
				
	def MotorsOffState(self):
		# Check if entering remote control or auto mode
		if self.motorEnable.getValue() > 0 or self.autoModeEnable.getValue() > 0:
			self.stateMachine.changeState("Manual")
			
	def ManualControl(self):
		# Simple remote control
		if self.motorEnable.getValue() > 0:
			# Manual turns
			self.headingError.setTarget(self.sensors.yaw().getValue() + self.joystickLeftRight.getValue() * self.maxManualTurn)
		elif self.autoModeEnable.getValue() > 0:
			self.stateMachine.changeState("moveFindWall")
		else:
			self.stateMachine.changeState("MotorsOff")
	
	def getCurrentTofReadings(self):
		dists = (self.tofLeft.getValue(), self.tofRight.getValue(), self.tofForward.getValue())
		print(f"getCurrentTofReadings: {dists}")
		return dists
		
	def startFindWall(self):
		self.autoModeForwardSpeed.setValue(self.autoMaxSpeed)
		
	def moveFindWall(self):
		leftDist, rightDist, forwardDist = self.getCurrentTofReadings()
		if self.autoModeEnable.getValue() == 0:
			self.stateMachine.changeState("Manual")
		elif forwardDist <= self.forwardMaxDist and rightDist > self.leftRightMaxDist:
			# Blocked ahead, turn right to re-aquire the wall (probably just gone around corner)
			self.stateMachine.changeState("moveTurnRight")
		elif forwardDist > self.forwardMaxDist and rightDist <= self.leftRightMaxDist:
			# Near wall, follow it
			self.stateMachine.changeState("moveFollowWall")
		elif forwardDist <= self.forwardMaxDist and rightDist <= self.leftRightMaxDist:
			# Near wall, but in a corner, turn away to find ahead wall
			self.stateMachine.changeState("moveTurnLeft")
		else:
			# Nothing in view, continue to find a wall by drifting right
			self.headingError.setTarget(self.sensors.yaw().getValue() - self.wallDriftAngle)
		
	def startFollowWall(self):
		self.autoModeForwardSpeed.setValue(self.autoMaxSpeed)
		
	def moveFollowWall(self):
		leftDist, rightDist, forwardDist = self.getCurrentTofReadings()
		if self.autoModeEnable.getValue() == 0:
			self.stateMachine.changeState("Manual")
		elif forwardDist <= self.forwardMaxDist and rightDist > self.leftRightMaxDist:
			# Blocked ahead, turn right to re-aquire the wall (probably just gone around corner)
			self.stateMachine.changeState("moveTurnRight")
		elif forwardDist <= self.forwardMaxDist and rightDist <= self.leftRightMaxDist:
			# Near wall, but in a corner, turn away to find ahead wall
			self.stateMachine.changeState("moveTurnLeft")
		elif rightDist > self.wallDistTarget + self.wallDistLeeway:
			# Move nearer right wall
			self.headingError.setTarget(self.sensors.yaw().getValue() - self.wallFollowAngleMin)
		elif rightDist < self.wallDistMin:
			# Move away from right wall quickly
			self.headingError.setTarget(self.sensors.yaw().getValue() + self.wallFollowAngleMax)
		elif rightDist < self.wallDistTarget - self.wallDistLeeway:
			# Move away from right wall
			self.headingError.setTarget(self.sensors.yaw().getValue() + self.wallFollowAngleMin)
		else:
			# Maintain heading
			self.headingError.setTarget(self.sensors.yaw().getValue())
		
	def startTurnLeft(self):
		self.autoModeForwardSpeed.setValue(self.wallTurnSpeed)
		self.turnAngle = self.wallTurnAngle
		
	def startTurnRight(self):
		self.autoModeForwardSpeed.setValue(self.wallTurnSpeed)
		self.turnAngle = -self.wallTurnAngle
		
	def moveTurn(self):
		leftDist, rightDist, forwardDist = self.getCurrentTofReadings()
		if self.autoModeEnable.getValue() == 0:
			self.stateMachine.changeState("Manual")
		elif forwardDist > self.forwardMaxDist:
			# Now free ahead, try to re-aquire the wall
			self.stateMachine.changeState("moveFindWall")
		else:
			# Keep turning
			self.headingError.setTarget(self.sensors.yaw().getValue() + self.turnAngle)
		
		
	#def updateState(self, left, forward, right):
	#	if forward > self.forwardMaxDist and left > self.leftRightMaxDist and right > self.leftRightMaxDist:
	#		# Nothing in view, find a wall
	#		self.currentState = 1
	#	elif forward <= self.forwardMaxDist and left > self.leftRightMaxDist and right > self.leftRightMaxDist:
	#		# Blocked ahead, turn right to re-aquire the wall (probably just gone around corner)
	#		self.currentState = 4
	#	elif forward > self.forwardMaxDist and left <= self.leftRightMaxDist and right > self.leftRightMaxDist:
	#		# Too far from wall, find it
	#		self.currentState = 1
	#	elif forward > self.forwardMaxDist and left > self.leftRightMaxDist and right <= self.leftRightMaxDist:
	#		# Near wall, follow it
	#		self.currentState = 2
	#	elif forward > self.forwardMaxDist and left <= self.leftRightMaxDist and right <= self.leftRightMaxDist:
	#		# Ahead ok, follow wall
	#		self.currentState = 2
	#	elif forward <= self.forwardMaxDist and left <= self.leftRightMaxDist and right > self.leftRightMaxDist:
	#		# Too far from wall but ahead blocked, turn right (WILL OSCILLATE?)
	#		self.currentState = 4
	#	elif forward <= self.forwardMaxDist and left > self.leftRightMaxDist and right <= self.leftRightMaxDist:
	#		# Only left free, avoid
	#		self.currentState = 3
	#	elif forward <= self.forwardMaxDist and left <= self.leftRightMaxDist and right <= self.leftRightMaxDist:
	#		# Dead end, about turn
	#		self.currentState = 3
	#	print(f"New state: {self.currentState}")
	
	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Set up the state machine
		self.stateMachine = StateMachine("MotorsOff")
		self.stateMachine.addState("MotorsOff", self.ControlOff, self.MotorsOffState, self.ControlOn)
		self.stateMachine.addState("Manual", None, self.ManualControl, None)
		self.stateMachine.addState("moveFindWall", self.startFindWall, self.moveFindWall, None)
		self.stateMachine.addState("moveFollowWall", self.startFollowWall, self.moveFollowWall, None)
		self.stateMachine.addState("moveTurnLeft", self.startTurnLeft, self.moveTurn, None)
		self.stateMachine.addState("moveTurnRight", self.startTurnRight, self.moveTurn, None)

		# Yaw control
		yaw = self.sensors.yaw()
		self.pidHeading = PID(self.pidP, self.pidI, self.pidD, sample_time=0.008, proportional_on_measurement=self.proportionalOnMeasure)
		self.headingError = HeadingPIDErrorValue(yaw, self.pidHeading, yaw.getValue(), min = -1.0, max = 1.0, scaling=1.0)
		
		# Motors
		motorsStop = FixedValue(0.0)
		self.autoModeForwardSpeed = FixedValue(0.0)
		self.motorEnable = self.sensors.button(4)
		self.autoModeEnable = ToggleButtonValue(self.sensors.button(5))
		self.joystickForward = self.sensors.joystickAxis(1)
		self.joystickLeftRight = self.sensors.joystickAxis(3)
		self.motorLManualSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = -self.maxHeadingTurn))]
		self.motorRManualSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = self.maxHeadingTurn))]
		self.motorLAutoSpeed = [SpeedDirectionCombiner(self.autoModeForwardSpeed, Scaler(self.headingError, scaling = -self.maxHeadingTurn))]
		self.motorRAutoSpeed = [SpeedDirectionCombiner(self.autoModeForwardSpeed, Scaler(self.headingError, scaling = self.maxHeadingTurn))]
		self.motorsSpeedMode = ValueAdder([self.motorEnable, self.autoModeEnable], max=2) # 0=off, 1=manual/auto manual forward, 2=full auto
		# Switch motor speed calculation depending upone what buttons are pressed
		motorL = SwitchingControlMediator( [motorsStop, self.motorLManualSpeed, self.motorLAutoSpeed],
											self.controls.motor(2), self.motorsSpeedMode )
		highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [motorsStop, self.motorRManualSpeed, self.motorRAutoSpeed],
											self.controls.motor(1), self.motorsSpeedMode )
		highPriorityProcesses.append(motorR)

		#self.speedSensorL = self.sensors.counter(0)
		#self.speedSensorR = self.sensors.counter(1)

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
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.tofLeft, scaling=-1.0, min=0.0, max=1.0, offset=self.forwardMaxDist), self.ledEyeLeft))
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.tofRight, scaling=-1.0, min=0.0, max=1.0, offset=self.forwardMaxDist), self.ledEyeRight))
		
		# Common controls
		self.grabberControl.createProcesses(highPriorityProcesses, medPriorityProcesses)
		self.cameraLevellingControl.createProcesses(highPriorityProcesses, medPriorityProcesses, self.cameraTilt)
		self.zGunControl.createProcesses(highPriorityProcesses, medPriorityProcesses)

	#def move(self):
	#	if self.autoModeEnable.getValue() > 0:
	#		# Wall Following using ToF Distances
	#		if not self.pidHeading.auto_mode:
	#			self.pidHeading.auto_mode = True
	#		leftDist = self.tofLeft.getValue()
	#		rightDist = self.tofRight.getValue()
	#		forwardDist = self.tofForward.getValue()
	#		# Update and execute state determined
	#		self.updateState(leftDist, forwardDist, rightDist)
	#		self.states[self.currentState](leftDist, forwardDist, rightDist)
	#	elif self.motorEnable.getValue() > 0:
	#		# Manual control
	#		if not self.pidHeading.auto_mode:
	#			self.pidHeading.auto_mode = True
	#		if self.joystickLeftRight.getValue() != 0.0:
	#			self.headingError.setTarget(self.sensors.yaw().getValue() + self.joystickLeftRight.getValue() * self.maxManualTurn)
	#		print(self.pidHeading.components)
	#	else:
	#		# Still - no change in direction
	#		self.pidHeading.auto_mode = False
	#		self.headingError.setTarget(self.sensors.yaw().getValue())
	
	def move(self):
		self.stateMachine.process()
	
	def stop(self):
		''' Stop the challenge
		'''
		self.stateMachine.changeState("MotorsOff")
		self.motorEnable.setValue(0, status=0)
		
		
