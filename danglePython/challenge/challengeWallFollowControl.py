from simple_pid import PID
import numpy as np
import time

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
		self.pidP = config.get("wall.pid.p", 0.015)
		self.pidI = config.get("wall.pid.i", 0.0) #0.001)
		self.pidD = config.get("wall.pid.d", 0.0012)
		self.proportionalOnMeasure = config.get("wall.pid.pom", False)
		self.maxForward = config.get("wall.forward.max", 1.0)
		self.maxManualTurn = config.get("wall.manualturn.max", -15.0)
		
		self.maxHeadingTurn = config.get("wall.headingturn.max", 0.5)
		self.autoMaxSpeed = config.get("wall.speed", 0.6)
		self.cameraTilt = config.get("wall.camera.tilt", -0.4)
		self.leftRightMaxDist = config.get("wall.leftright.maxdist", 600)
		self.forwardTurnDist = config.get("wall.forward.maxdist", 450)
		self.wallDistTarget = config.get("wall.targetdist", 305) # 305 ~= 210mm clearance each side
		self.wallFollowAdjustmentRate = config.get("wall.move.followfactor", 300.0)
		self.wallFollowMaxAngle = config.get("wall.move.maxfollowangle", 15.0)
		self.turnAllowedTime = config.get("wall.move.turnspeed", 1.0)
		self.turnAheadSpeed = config.get("wall.move.turnaheadspeed", 0.4)
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
		self.stateMachine.changeState("moveFollowWall")
		#leftDist, rightDist, forwardDist = self.getCurrentTofReadings()
		#if self.autoModeEnable.getValue() == 0:
		#	self.stateMachine.changeState("Manual")
		#elif forwardDist <= self.forwardMaxDist and rightDist > self.leftRightMaxDist:
		#	# Blocked ahead, turn right to re-aquire the wall (probably just gone around corner)
		#	self.stateMachine.changeState("moveTurnRight")
		#elif forwardDist > self.forwardMaxDist and rightDist <= self.leftRightMaxDist:
		#	# Near wall, follow it
		#	self.stateMachine.changeState("moveFollowWall")
		#elif forwardDist <= self.forwardMaxDist and rightDist <= self.leftRightMaxDist:
		#	# Near wall, but in a corner, turn away to find ahead wall
		#	self.stateMachine.changeState("moveTurnLeft")
		#else:
		#	# Nothing in view, continue to find a wall by drifting right
		#	self.headingError.setTarget(self.sensors.yaw().getValue() - self.wallDriftAngle)
		
	def startFollowWall(self):
		self.autoModeForwardSpeed.setValue(self.autoMaxSpeed)
		# Get the nominal ahead direction and use this as a basis for corrections
		self.nominalAheadDirection = self.sensors.yaw().getValue()
		
	def moveFollowWall(self):
		leftDist, rightDist, forwardDist = self.getCurrentTofReadings()
		if self.autoModeEnable.getValue() == 0:
			self.stateMachine.changeState("Manual")
		elif self.motorEnable.getValue() > 0 and forwardDist <= self.forwardTurnDist and rightDist > self.leftRightMaxDist:
			# Blocked ahead, turn right to re-aquire the wall (probably just gone around corner)
			self.stateMachine.changeState("90Right")
		elif self.motorEnable.getValue() > 0 and forwardDist <= self.forwardTurnDist:
			# Near wall, but in a corner, turn away to find ahead wall
			self.stateMachine.changeState("90Left")
		elif rightDist > self.leftRightMaxDist and leftDist > self.leftRightMaxDist:
			# Found a gap - continue straight for the moment
			pass
		else:
			# We're ok ahead, continue to follow wall
			# Use the nearesr wall to follow
			if rightDist < leftDist:
				error = self.wallDistTarget - rightDist
			else:
				error = leftDist - self.wallDistTarget
			adjustmentAngle = np.arctan((error) / self.wallFollowAdjustmentRate) * 180.0/3.14159
			# Limit angle
			adjustmentAngle = min(self.wallFollowMaxAngle, max(-self.wallFollowMaxAngle, adjustmentAngle))
			self.headingError.setTarget(self.nominalAheadDirection + adjustmentAngle)
			print(f"Yaw: {self.sensors.yaw().getValue():0.1f}, error: {error:0.1f}, adjustment: {adjustmentAngle:0.1f}")
			
	def turn90DegLeft(self):
		# Stop the motors
		self.autoModeForwardSpeed.setValue(self.turnAheadSpeed)
		# MPU direction-assisted remote control - 90 degree turn left
		self.fastTurnTarget = self.sensors.yaw().getValue() + 90.0
		self.headingError.setTarget(self.fastTurnTarget)
		self.turnStartTime = time.perf_counter()
			
	def turn90DegRight(self):
		# Stop the motors
		self.autoModeForwardSpeed.setValue(self.turnAheadSpeed)
		# MPU direction-assisted remote control - 90 degree turn left
		self.fastTurnTarget = self.sensors.yaw().getValue() - 90.0
		self.headingError.setTarget(self.fastTurnTarget)
		self.turnStartTime = time.perf_counter()
			
	def fastTurnState(self):
		if self.motorEnable.getValue() > 0:
			# Turn for set period
			if time.perf_counter() - self.turnStartTime >= self.turnAllowedTime:
				# Continue the maze
				self.stateMachine.changeState("moveFollowWall")
		else:
			# Done
			self.stateMachine.changeState("Manual")
	
	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Set up the state machine
		self.stateMachine = StateMachine("MotorsOff")
		self.stateMachine.addState("MotorsOff", self.ControlOff, self.MotorsOffState, self.ControlOn)
		self.stateMachine.addState("Manual", None, self.ManualControl, None)
		self.stateMachine.addState("moveFindWall", self.startFindWall, self.moveFindWall, None)
		self.stateMachine.addState("moveFollowWall", self.startFollowWall, self.moveFollowWall, None)
		self.stateMachine.addState("90Left", self.turn90DegLeft, self.fastTurnState, None)
		self.stateMachine.addState("90Right", self.turn90DegRight, self.fastTurnState, None)

		# Yaw control
		yaw = self.sensors.yaw()
		self.pidHeading = PID(self.pidP, self.pidI, self.pidD, sample_time=0.008, proportional_on_measurement=self.proportionalOnMeasure, output_limits=(-1.0, 1.0))
		self.headingError = HeadingPIDErrorValue(yaw, self.pidHeading, yaw.getValue())
		
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
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.tofLeft, scaling=-1.0, min=0.0, max=1.0, offset=self.leftRightMaxDist), self.ledEyeLeft))
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.tofRight, scaling=-1.0, min=0.0, max=1.0, offset=self.leftRightMaxDist), self.ledEyeRight))
		
		# Common controls
		self.grabberControl.createProcesses(highPriorityProcesses, medPriorityProcesses)
		self.cameraLevellingControl.createProcesses(highPriorityProcesses, medPriorityProcesses, self.cameraTilt)
		self.zGunControl.createProcesses(highPriorityProcesses, medPriorityProcesses)

	def move(self):
		self.stateMachine.process()
	
	def stop(self):
		''' Stop the challenge
		'''
		self.stateMachine.changeState("MotorsOff")
		self.motorEnable.setValue(0, status=0)
		
		
