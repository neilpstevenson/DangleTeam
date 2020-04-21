from simple_pid import PID
import time

# Interfaces
from interfaces.ChallengeInterface import ChallengeInterface
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.Config import Config
# Value providers
from analysis.SimplePIDErrorValue import SimplePIDErrorValue
from analysis.HeadingPIDErrorValue import HeadingPIDErrorValue
from analysis.OneShotButtonValue import OneShotButtonValue
from analysis.ToggleButtonValue import ToggleButtonValue
from analysis.TimedTriggerValue import TimedTriggerValue
from analysis.FixedValue import FixedValue
from analysis.StateMachine import StateMachine
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


class ChallengeManualControl(ChallengeInterface):

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		# Common controls
		self.grabberControl = GrabberControl()
		self.cameraLevellingControl = CameraLevellingControl()
		self.zGunControl = ZGunControl()
		# Get config
		config = Config()
		self.pidP = config.get("manual.pid.p", 0.015)
		self.pidI = config.get("manual.pid.i", 0.0) #0.001)
		self.pidD = config.get("manual.pid.d", 0.0012)
		self.proportionalOnMeasure = config.get("manual.pid.pom", False)
		self.maxForward = config.get("manual.forward.max", 1.0)
		self.maxManualTurn = config.get("manual.turn.max", -15.0)
		self.maxHeadingTurn = config.get("manual.headingturn.max", 0.6)
		self.maxSimpleTurn = config.get("manual.simpleturn.max", 0.4)
		self.cameraTilt = config.get("manual.camera.tilt", 0.15)
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
			self.stateMachine.changeState("SimpleManual")

	def simpleManualControl(self):
		# Simple remote control
		if self.motorEnable.getValue() > 0:
			# Just keep the heading ticking over
			self.headingError.setTarget(self.sensors.yaw().getValue())
		elif self.autoModeEnable.getValue() > 0:
			self.stateMachine.changeState("MPUAssistedManual")
		else:
			self.stateMachine.changeState("MotorsOff")
		
	def mpuAssistedControl(self):
		# MPU direction-assisted remote control
		if self.motorEnable.getValue() > 0:
			if self.left90.getValue() > 0:
				self.stateMachine.changeState("90Left")
			elif self.right90.getValue() > 0:
				self.stateMachine.changeState("90Right")
			elif self.joystickLeftRight.getValue() != 0.0:
				# Adjust heading from yaw reading
				self.headingError.setTarget(self.sensors.yaw().getValue() + self.joystickLeftRight.getValue() * self.maxManualTurn)
				#print(self.pidHeading.components)
		elif self.autoModeEnable.getValue() > 0:
			# Just keep the heading ticking over
			self.headingError.setTarget(self.sensors.yaw().getValue())
		else:
			self.stateMachine.changeState("MotorsOff")
		
	def turn90DegLeft(self):
		# MPU direction-assisted remote control - 90 degree turn left
		self.fastTurnTarget = self.sensors.yaw().getValue() + 90.0
		self.headingError.setTarget(self.fastTurnTarget)
			
	def turn90DegRight(self):
		# MPU direction-assisted remote control - 90 degree turn left
		self.fastTurnTarget = self.sensors.yaw().getValue() - 90.0
		self.headingError.setTarget(self.fastTurnTarget)
			
	def fastTurnState(self):
		if self.motorEnable.getValue() > 0 and self.joystickLeftRight.getValue() == 0.0:
			if self.left90.getValue() > 0:
				self.fastTurnTarget += 90.0
				self.headingError.setTarget(self.fastTurnTarget)
			elif self.right90.getValue() > 0:
				self.fastTurnTarget -= 90.0
				self.headingError.setTarget(self.fastTurnTarget)
		else:
			# Done
			self.stateMachine.changeState("MPUAssistedManual")
		
	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Set up the state machine
		self.stateMachine = StateMachine("MotorsOff")
		self.stateMachine.addState("MotorsOff", self.ControlOff, self.MotorsOffState, self.ControlOn)
		self.stateMachine.addState("SimpleManual", None, self.simpleManualControl, None)
		self.stateMachine.addState("MPUAssistedManual", None, self.mpuAssistedControl, None)
		self.stateMachine.addState("90Left", self.turn90DegLeft, self.fastTurnState, None)
		self.stateMachine.addState("90Right", self.turn90DegRight, self.fastTurnState, None)

		# Yaw control
		yaw = self.sensors.yaw()
		self.pidHeading = PID(self.pidP, self.pidI, self.pidD, sample_time=0.008, proportional_on_measurement=self.proportionalOnMeasure, output_limits=(-1.0, 1.0))
		self.headingError = HeadingPIDErrorValue(yaw, self.pidHeading, yaw.getValue())
		
		# Motors
		motorsStop = FixedValue(0.0)
		self.motorEnable = self.sensors.button(4)
		self.autoModeForwardSpeed = FixedValue(0.0)
		self.autoModeEnable = ToggleButtonValue(self.sensors.button(5))
		self.joystickForward = self.sensors.joystickAxis(1)
		self.joystickLeftRight = self.sensors.joystickAxis(3)
		self.left90 = OneShotButtonValue(self.sensors.button(3))
		self.right90 = OneShotButtonValue(self.sensors.button(1))
		self.motorLSimpleManualSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.joystickLeftRight, scaling = self.maxSimpleTurn))]
		self.motorRSimpleManualSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.joystickLeftRight, scaling = -self.maxSimpleTurn))]
		self.motorLMPUAssistedSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = -self.maxHeadingTurn))]
		self.motorRMPUAssistedSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.headingError, scaling = self.maxHeadingTurn))]
		self.motorsSpeedMode = ValueAdder([self.motorEnable, self.autoModeEnable], max=2) # 0=off, 1=manual/auto manual forward, 2=full auto
		# Switch motor speed calculation depending upone what buttons are pressed
		motorL = SwitchingControlMediator( [motorsStop, self.motorLSimpleManualSpeed, self.motorLMPUAssistedSpeed],
											self.controls.motor(2), self.motorsSpeedMode )
		highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [motorsStop, self.motorRSimpleManualSpeed, self.motorRMPUAssistedSpeed],
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
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.motorEnable, scaling=255), self.ledEyeLeft))
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.autoModeEnable, scaling=255), self.ledEyeRight))
		
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
		
