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
#from challenge.grabberControl import GrabberControl
#from challenge.cameraLevellingControl import CameraLevellingControl
#from challenge.zGunControl import ZGunControl


class ChallengeTestSequence(ChallengeInterface):

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		self.vision = VisionAccessFactory.getSingleton()
		# Common controls
		#self.grabberControl = GrabberControl()
		#self.cameraLevellingControl = CameraLevellingControl()
		#self.zGunControl = ZGunControl()
		# Get config
		config = Config()
		self.pidConstants = config.get("motor.position.pid", [0.002, 0.0, 0.00008])	# Note: PID output is also limited to +/-1.0
		self.proportionalOnMeasure = config.get("motor.position.pid.pom", False)
		self.pidHeadingConstants = config.get("motor.heading.pid", [0.015, 0.001, 0.0012])	# Note: PID output is also limited to +/-1.0
		self.proportionalOnMeasureHeadiing = config.get("motor.heading.pid.pom", False)
		self.maxForward = config.get("motor.position.forward.max", 1.0)	# Joystick-controlled max speed
		self.maxManualTurn = config.get("lava.manualturn.max", -15.0) # Joystick-controlled max turn angle (mpu heading relative)
		self.maxPidForward = config.get("motor.position.pidforward.max", 0.4)	# PID-controlled max speed
		self.maxHeadingTurn = config.get("lava.headingturn.max", 0.6) # PID output scaling (manual mode)
		self.maxAutoTurn = config.get("lava.autoturn.max", 0.3) # PID output scaling (full auto mode)
		config.save()

	def ControlOff(self, data):
		# Stop the motors
		self.autoModeForwardSpeed.setValue(0.0)
		# stop any auto mode
		self.autoModeEnable.reset()
		self.motorsSpeedMode.setValue(0)
		# Disable the PID controls
		self.motorPositionErrorL.disable()
		self.motorPositionErrorR.disable()
		self.headingError.disable()
			
	def MotorsOffState(self, data):
		# Maintain current position
		self.targetPositionL = self.positionL.getValue()
		self.targetPositionR = self.positionR.getValue()
		#self.headingError.setTarget(self.visionTargetHeading.getValue())
		# Check if entering remote control or auto mode
		if self.motorEnable.getValue() > 0 or self.autoModeEnable.getValue() > 0:
			self.stateMachine.changeState("Manual")

	def StartManualControl(self, data):
		self.motorsSpeedMode.setValue(1)
				
	def ManualControl(self, data):
		# Simple remote control
		if self.motorEnable.getValue() > 0:
			# Manual turns
			pass #self.headingError.setTarget(self.sensors.yaw().getValue() + self.joystickLeftRight.getValue() * self.maxManualTurn)
		elif self.autoModeEnable.getValue() > 0:
			self.stateMachine.changeState("StartSequence")
		else:
			self.stateMachine.changeState("MotorsOff")

	def StartManualControlHeading(self, data):
		self.motorsSpeedMode.setValue(3)
		self.headingError.enable()
		self.headingError.reset()
				
	def ManualControlHeading(self, data):
		# Record position
		if self.resetLastPositionButton.getValue() > 0:
			self.lastPositionL = self.positionL.getValue()
			self.lastPositionR = self.positionR.getValue()
			self.pathRecord = []
		elif self.recordPositionButton.getValue() > 0:
			currentPositionL = self.positionL.getValue()
			currentPositionR = self.positionR.getValue()
			self.pathRecord.append(("MoveDistance",[int(currentPositionL-self.lastPositionL), int(currentPositionR-self.lastPositionR)]))
			self.lastPositionL = currentPositionL
			self.lastPositionR = currentPositionR
		elif self.savePositionsButton.getValue() > 0:
			pathFile = Config("recordedPath.json")
			pathFile.set("path", self.pathRecord)
			pathFile.save()
			#self.pathRecord = []

		# Simple remote control
		if self.motorEnable.getValue() > 0:
			# Manual turns
			if self.joystickLeftRight.getValue() != 0.0:
				self.headingError.setTarget(self.sensors.yaw().getValue() + self.joystickLeftRight.getValue() * self.maxManualTurn)
		elif self.autoModeEnable.getValue() > 0:
			self.stateMachine.changeState("StartSequence")
		else:
			self.stateMachine.changeState("MotorsOff")

	def EndManualControlHeading(self, data):
		# Disable the PID controls
		self.motorsSpeedMode.setValue(0)
		self.headingError.disable()
		
	def SetZeroHeading(self, data):
		# Just record the current heading, so everything else is then relative to this basline
		self.targetAngle = self.sensors.yaw().getValue()
		print(f"SetZeroHeading: {self.targetAngle}")
		self.stateMachine.changeState("NextSequence")


	def nextSequence(self):
		seq = [	("SetZeroHeading",None), \
				("MoveDistance",[300,300]), \
				("RotateAngle", 90), \
				("MoveDistance",[300,300]), \
				("RotateAngle", 90), \
				("MoveDistance",[300,300]), \
				("RotateAngle", 90), \
				("MoveDistance",[300,300]), \
				("RotateAngle", 90) \
			  ]
		# Use recorded path?
		pathFile = Config("recordedPath.json")
		seq = pathFile.get("path", seq)

		if len(self.pathRecord) > 0:
			seq = self.pathRecord
		for move in range(len(seq)):
			nudge  = seq[move]
			yield nudge 
			
	def StartSequence(self, data):
		self.nextSeq = self.nextSequence()
		
	def Sequence(self, data):
		# Check if we've been disabled
		if self.autoModeEnable.getValue() == 0:
			self.stateMachine.changeState("MotorsOff")
		else:
			# Process next move in sequence
			try:
				state, nudge = next(self.nextSeq)
				self.stateMachine.changeState(state, nudge)
			except StopIteration:
				# End of sequence?
				self.stateMachine.changeState("MotorsOff")
				
	def StartMoveDistance(self, data):
		# Ensure all is enabled
		self.autoModeForwardSpeed.setValue(self.maxPidForward)
		self.motorsSpeedMode.setValue(2)
		nudgeL, nudgeR = data
		print(f"nudge: {(nudgeL, nudgeR)}")
		self.motorPositionErrorL.enable()
		self.motorPositionErrorR.enable()
		self.targetPositionL += nudgeL
		self.motorPositionErrorL.setTarget(self.targetPositionL)
		self.targetPositionR += nudgeR
		self.motorPositionErrorR.setTarget(self.targetPositionR)
		# Remember the target positions as part of the state data
		stateData = (self.targetPositionL, self.targetPositionR)
		print(f"StartMoveDistance: {stateData}")
		return stateData

	def MoveDistance(self, data):
		# Reached target?
		currentPositionL = self.positionL.getValue()
		currentPositionR = self.positionR.getValue()
		targetPositionL, targetPositionR = data
		print(f"MoveDistance: {data}; current: {(currentPositionL, currentPositionR)}")
		# Continue until we're close to the target
		if abs(targetPositionL - currentPositionL) < 40 and abs(targetPositionR - currentPositionR) < 40 or self.autoModeEnable.getValue() == 0:
			self.stateMachine.changeState("NextSequence")

	def EndMoveDistance(self, data):
		# Disable the PID controls
		self.motorPositionErrorL.disable()
		self.motorPositionErrorR.disable()

	def StartRotateAngle(self, data):
		angle = data
		print(f"angle: {angle}")
		self.motorsSpeedMode.setValue(3)
		self.headingError.enable()
		self.targetAngle += angle
		self.headingError.setTarget(self.targetAngle)
		# Remember the target positions as part of the state data
		print(f"StartRotateAngle: {angle} => {self.targetAngle}")
		return self.targetAngle
		
	def RotateAngle(self, data):
		# Reached target?
		currentYaw = self.sensors.yaw().getValue()
		angle = data
		print(f"RotateAngle: {angle}; current: {currentYaw}")
		angleDiff = abs(angle - currentYaw)
		while angleDiff >= 360.0:
			angleDiff -= 360.0
		print(f"RotateAngle: {angle}; current: {currentYaw}; diff: {angleDiff}")
		# Continue until we're close to the target
		if angleDiff < 1.0 or self.autoModeEnable.getValue() == 0:
			self.stateMachine.changeState("NextSequence")

	def EndRotateAngle(self, data):
		# Disable the PID controls
		self.headingError.disable()
		# Reset position counters, as we've moved by an indeterminate angle
		self.targetPositionL = self.positionL.getValue()
		self.targetPositionR = self.positionR.getValue()


	def StartForward(self, data):
		distance = data
		print(f"distance: {distance}")
		self.motorsSpeedMode.setValue(4)
		self.autoModeForwardSpeed.setValue(self.maxPidForward if distance > 0.0 else -self.maxPidForward)
		self.headingError.enable()
		# Maintain current heading
		self.headingError.setTarget(self.targetAngle)
		# Remember the target distance as part of the state data
		self.targetPositionL += distance
		self.targetPositionR += distance
		stateData = (self.targetPositionL, self.targetPositionR)
		print(f"Forward:  {distance} => {stateData}")
		return stateData
		
	def Forward(self, data):
		# Reached target?
		currentPositionL = self.positionL.getValue()
		currentPositionR = self.positionR.getValue()
		targetPositionL, targetPositionR = data
		print(f"Forward: {data}; current: {(currentPositionL, currentPositionR)}")
		# Continue until we're close to the target
		if abs(targetPositionL - currentPositionL) < 40 or abs(targetPositionR - currentPositionR) < 40 or self.autoModeEnable.getValue() == 0:
			self.stateMachine.changeState("NextSequence")

	def EndForward(self, data):
		# Disable the PID controls
		self.headingError.disable()
		self.autoModeForwardSpeed.setValue(0.0)

	def StartServo(self, data):
		servoName, setpoint, timeout = data
		endtime = time.perf_counter() + timeout
		servo = self.servos[servoName]
		return (servo, setpoint, endtime)
		
	def Servo(self, data):
		servo, setpoint, endtime = data
		if time.perf_counter() >= endtime or self.autoModeEnable.getValue() == 0:
			self.stateMachine.changeState("NextSequence")
		else:
			servo.setValue(setpoint)

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		
		# Set up the state machine
		self.stateMachine = StateMachine("MotorsOff")
		self.stateMachine.addState("MotorsOff", self.ControlOff, self.MotorsOffState, None)
		self.stateMachine.addState("Manual", self.StartManualControlHeading, self.ManualControlHeading, self.EndManualControlHeading)
		self.stateMachine.addState("SetZeroHeading", None, self.SetZeroHeading, None)
		self.stateMachine.addState("StartSequence", self.StartSequence, self.Sequence, None)
		self.stateMachine.addState("NextSequence", None, self.Sequence, None)
		self.stateMachine.addState("MoveDistance", self.StartMoveDistance, self.MoveDistance, self.EndMoveDistance)
		self.stateMachine.addState("RotateAngle", self.StartRotateAngle, self.RotateAngle, self.EndRotateAngle)
		self.stateMachine.addState("Forward", self.StartForward, self.Forward, self.EndForward)
		self.stateMachine.addState("Servo", self.StartServo, self.Servo, None)

		# Set up the PIDs for the two motors
		self.pidL = PID(self.pidConstants[0], self.pidConstants[1], self.pidConstants[2], sample_time=0.025, proportional_on_measurement=self.proportionalOnMeasure, output_limits=(-1.0, 1.0))
		self.motorL = self.controls.motor(2)
		self.positionL = self.controls.motorPosition(2)
		self.motorPositionErrorL = SimplePIDErrorValue(self.pidL, self.positionL)
		self.targetPositionL = self.positionL.getValue()
		self.motorPositionErrorL.setTarget(self.targetPositionL)
		self.motorPositionErrorL.reset()
		
		self.pidR = PID(self.pidConstants[0], self.pidConstants[1], self.pidConstants[2], sample_time=0.025, proportional_on_measurement=self.proportionalOnMeasure, output_limits=(-1.0, 1.0))
		self.motorR = self.controls.motor(1)
		self.positionR = self.controls.motorPosition(1)
		self.motorPositionErrorR = SimplePIDErrorValue(self.pidR, self.positionR)
		self.targetPositionR = self.positionR.getValue()
		self.motorPositionErrorR.setTarget(self.targetPositionR)
		self.motorPositionErrorR.reset()

		# Setup the heading PID
		yaw = self.sensors.yaw()
		print(f"Heading PID: {self.pidHeadingConstants}")
		self.pidHeading = PID(self.pidHeadingConstants[0], self.pidHeadingConstants[1], self.pidHeadingConstants[2], sample_time=0.008, proportional_on_measurement=self.proportionalOnMeasureHeadiing, output_limits=(-1.0, 1.0))
		self.headingError = HeadingPIDErrorValue(yaw, self.pidHeading, yaw.getValue())
		# Initialise the PID
		self.headingError.reset()

		# Path recording
		self.pathRecord = []
		self.lastPositionL = self.targetPositionL
		self.lastPositionR = self.targetPositionR
		self.resetLastPositionButton = OneShotButtonValue(self.sensors.button(3))
		self.recordPositionButton = OneShotButtonValue(self.sensors.button(2))
		self.savePositionsButton = OneShotButtonValue(self.sensors.button(1))

		# Motor control - General
		motorsStop = FixedValue(0.0)
		self.autoModeForwardSpeed = FixedValue(0.0)
		self.motorEnable = self.sensors.button(4)
		self.autoModeEnable = ToggleButtonValue(self.sensors.button(5), triggeredValue = 2)
		self.autoSequenceRun = ToggleButtonValue(self.sensors.button(3), triggeredValue = 2)
		self.joystickForward = self.sensors.joystickAxis(1)
		self.joystickLeftRight = self.sensors.joystickAxis(3)

		self.motorLSimpleManualSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.joystickLeftRight, scaling = self.maxForward))]
		self.motorRSimpleManualSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxForward), Scaler(self.joystickLeftRight, scaling = -self.maxForward))]

		self.motorLSimplePositionSpeed = [Scaler([self.joystickForward, self.motorPositionErrorL], scaling = self.maxPidForward)]
		self.motorRSimplePositionSpeed = [Scaler([self.joystickForward, self.motorPositionErrorR], scaling = self.maxPidForward)]

		#self.motorLSimplePositionSpeed = [SpeedDirectionCombiner(Scaler([self.joystickForward,self.motorPositionErrorL], scaling = self.maxPidForward), Scaler([Scaler(self.motorPositionErrorR, scaling = -1.0),self.motorPositionErrorL], scaling = self.maxPidForward))]
		#self.motorRSimplePositionSpeed = [SpeedDirectionCombiner(Scaler([self.joystickForward,self.motorPositionErrorR], scaling = self.maxPidForward), Scaler([Scaler(self.motorPositionErrorL, scaling = -1.0),self.motorPositionErrorR], scaling = self.maxPidForward))]									
		self.motorLHeadingAutoSpeed = [SpeedDirectionCombiner(self.autoModeForwardSpeed, Scaler(self.headingError, scaling = -self.maxHeadingTurn))]
		self.motorRHeadingAutoSpeed = [SpeedDirectionCombiner(self.autoModeForwardSpeed, Scaler(self.headingError, scaling = self.maxHeadingTurn))]
		self.motorLHeadingJoystickSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxPidForward), Scaler(self.headingError, scaling = -self.maxHeadingTurn))]
		self.motorRHeadingJoystickSpeed = [SpeedDirectionCombiner(Scaler(self.joystickForward, scaling = self.maxPidForward), Scaler(self.headingError, scaling = self.maxHeadingTurn))]
		

		self.motorsSpeedMode = FixedValue(0) # 0=Stop, 1=Manual, 2=Position Control, 3=Heading (gyro yaw) Control
		#ValueAdder([self.motorEnable, self.autoModeEnable, self.autoSequenceRun], max=2)
		
		motorL = SwitchingControlMediator( [ motorsStop, 						# 0 = Stopped \
											self.motorLSimpleManualSpeed,  		# 1 = Simple joystick \
											self.motorLSimplePositionSpeed, 	# 2 = Joystick Forward + Position PIDs \
											self.motorLHeadingJoystickSpeed, 	# 3 = Joystick Forward + Heading PID \
											self.motorLHeadingAutoSpeed 		# 4 = Auto Forward + Heading PID \
										   ],
											self.controls.motor(2), self.motorsSpeedMode )
		highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [ motorsStop, 						# 0 = Stopped \
											self.motorRSimpleManualSpeed,  		# 1 = Simple joystick \
											self.motorRSimplePositionSpeed,  	# 2 = Joystick Forward + Position PIDs \
											self.motorRHeadingJoystickSpeed, 	# 3 = Joystick Forward + Heading PID \
											self.motorRHeadingAutoSpeed 		# 4 = Auto Forward + Heading PID \
										   ],
											self.controls.motor(1), self.motorsSpeedMode )
		highPriorityProcesses.append(motorR)

		# Servos used within the state machine
		grabberPosition = FixedValue(0.0)
		grabber = SimpleControlMediator( Scaler(grabberPosition, scaling=0.3, min=-1.0, max=1.0, offset=0.3), self.controls.servo(5) )
		grabber2 = SimpleControlMediator( Scaler(grabberPosition, scaling=-0.3, min=-1.0, max=1.0, offset=-0.1), self.controls.servo(6) )
		highPriorityProcesses.append(grabber)
		highPriorityProcesses.append(grabber2)
		grabberHeight = FixedValue(0.0)
		grabHeight = SimpleControlMediator( Scaler(grabberHeight, scaling=1.0, min=-1.0, max=1.1, offset=0.1), self.controls.servo(27) )
		highPriorityProcesses.append(grabHeight)
		self.servos = {
			"grabber" : grabberPosition,
			"grabheight" : grabberHeight
			}
			
		# LED display state
		self.ledIndicator = self.controls.led(0)
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.motorEnable, scaling=2, offset=2, max=4), self.ledIndicator))
		
		# Nudge buttons
		self.NudgeForward = OneShotButtonValue(self.sensors.button(2), triggeredValue = 300)
		self.NudgeBackward = OneShotButtonValue(self.sensors.button(0), triggeredValue = 300)

	def move(self):
		self.stateMachine.process()
	
	def stop(self):
		''' Stop the challenge
		'''
		self.stateMachine.changeState("MotorsOff")
		self.motorEnable.setValue(0, status=0)
