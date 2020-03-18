from simple_pid import PID
import time

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
from analysis.PeriodicWaveGenerator import PeriodicWaveGenerator
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


class ChallengeMinesweeper(ChallengeInterface):

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
		self.pidP = config.get("heading.pid.p", 0.06)
		self.pidI = config.get("heading.pid.i", 0.001)
		self.pidD = config.get("heading.pid.d", 0.004)
		self.proportionalOnMeasure = config.get("heading.pid.pom", False)
		self.maxForward = config.get("heading.forward.max", 1.0)
		self.maxManualTurn = config.get("heading.manualturn.max", -15.0)
		self.maxHeadingTurn = config.get("heading.headingturn.max", 0.5)
		
		self.maxFindLightTurn = config.get("minesweeper.findlightturn.max", -15.0)
		self.autoMaxSpeed = config.get("minesweeper.speed", 0.6)
		self.cameraTilt = config.get("minesweeper.camera.tilt", 0.22)
		self.achievedStopTime = config.get("minesweeper.achieved.stoptime", 5.0) # seconds
		self.minDistanceToStop = config.get("minesweeper.achieved.atdistance", 20.0)
		self.MoveTimeMin = config.get("minesweeper.movement.mintime", 1.0) # seconds
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
			self.stateMachine.changeState("FindLight")
		else:
			self.stateMachine.changeState("MotorsOff")
		
	def StopForward(self):
		self.autoModeForwardSpeed.setValue(0.0)
		
	def FindLight(self):
		if self.visionTargetHeading.getStatus() > 0:
			# Head towards it
			self.stateMachine.changeState("MoveToLight")
		elif self.autoModeEnable.getValue() > 0:
			# Find light by simple rotation on the spot
			self.headingError.setTarget(self.sensors.yaw().getValue() + self.maxFindLightTurn)
			#print(self.pidHeading.components)
		else:
			self.stateMachine.changeState("Manual")
		pass
	
	def FindLightAchieved(self):
		# Switch direction for next attempt.  Should stop us overshooting and going round in 
		# every faster circles
		self.maxFindLightTurn = -self.maxFindLightTurn
		
	def StartMoveToLight(self):
		self.autoModeForwardSpeed.setValue(self.autoMaxSpeed)
		self.moveToLightStart = time.perf_counter()
				
	def MoveToLight(self):
		# Nothing visible?
		if self.visionTargetHeading.getStatus() == 0 or self.visionTargetHeading.getDistance() < self.minDistanceToStop:
			if time.perf_counter() - self.moveToLightStart >= self.MoveTimeMin:
				# We've been moving for a bit, assume we've arrived if no longer can see target 
				self.stateMachine.changeState("Standstill")
			else:
				# Nothing in sight - find it
				self.stateMachine.changeState("FindLight")
		elif self.autoModeEnable.getValue() > 0:
			# Head towards indicated light target
			self.headingError.setTarget(self.visionTargetHeading.getValue())
			#print(self.pidHeading.components)
			print(f"Distance to target: {self.visionTargetHeading.getDistance()}")
		else:
			self.stateMachine.changeState("Manual")
			
	def StopToStandStill(self):
		# stop all motions
		print("StopToStandStill")
		self.headingError.setTarget(self.sensors.yaw().getValue())
		self.autoModeForwardSpeed.setValue(0.0)
		self.stateMachine.setTimeout(self.achievedStopTime, "FindLight")
		self.standStillStart = time.perf_counter()
		# reset the PID controller
		self.pidHeading.set_auto_mode(False)
		self.pidHeading.set_auto_mode(True, last_output=0.0)
		
	def StandStill(self):
		# stand still
		self.headingError.setTarget(self.sensors.yaw().getValue())

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Set up the state machine
		self.stateMachine = StateMachine("MotorsOff")
		self.stateMachine.addState("MotorsOff", self.ControlOff, self.MotorsOffState, self.ControlOn)
		self.stateMachine.addState("Manual", None, self.ManualControl, None)
		self.stateMachine.addState("FindLight", self.StopForward, self.FindLight, self.FindLightAchieved)
		self.stateMachine.addState("MoveToLight", self.StartMoveToLight, self.MoveToLight, self.StopForward)
		self.stateMachine.addState("Standstill", self.StopToStandStill, self.StandStill, None)

		# Yaw control
		yaw = self.sensors.yaw()
		self.pidHeading = PID(self.pidP, self.pidI, self.pidD, sample_time=0.008, proportional_on_measurement=self.proportionalOnMeasure)
		self.headingError = HeadingPIDErrorValue(yaw, self.pidHeading, yaw.getValue(), min = -1.0, max = 1.0, scaling=1.0)
		
		# Vision
		self.visionTargetHeading = self.vision.getImageResult()

		# Motors
		motorsStop = FixedValue(0.0)
		self.motorEnable = self.sensors.button(4)
		self.autoModeForwardSpeed = FixedValue(0.0)
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
		
		# LED eyes
		self.ledEyeLeft = self.controls.led(20)
		self.ledEyeRight = self.controls.led(21)
		#medPriorityProcesses.append(SimpleControlMediator( self.motorEnable, self.ledEyeLeft))
		medPriorityProcesses.append(SimpleControlMediator( PeriodicWaveGenerator(self.motorEnable, 0.2, 0.1), self.ledEyeLeft))
		medPriorityProcesses.append(SimpleControlMediator( self.autoModeEnable, self.ledEyeRight))
		
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
		
