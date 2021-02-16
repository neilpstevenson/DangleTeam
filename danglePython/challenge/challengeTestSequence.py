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
from analysis.StateMachine import StateMachine
# Common controls
from challenge.grabberControl import GrabberControl
from challenge.cameraLevellingControl import CameraLevellingControl
from challenge.zGunControl import ZGunControl


class ChallengeTestSequence(ChallengeInterface):

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

	def ControlOff(self):
		# Stop the motors
		self.autoModeForwardSpeed.setValue(0.0)
		# stop the PID controller
		#self.pidHeading.auto_mode = False
		self.autoModeEnable.reset()
		self.autoModeForwardSpeed.setValue(0.0)
			
	def MotorsOffState(self, data):
		# Check if entering remote control or auto mode
		if self.motorEnable.getValue() > 0 or self.autoModeEnable.getValue() > 0:
			self.stateMachine.changeState("Manual")

	def ControlOn(self, data):
		# reset the PID controller
		pass
		#self.pidHeading.set_auto_mode(True, last_output=0.0)
		#self.headingError.setTarget(self.sensors.yaw().getValue())
		#self.headingError.getValue()
				
	def ManualControl(self, data):
		# Simple remote control
		if self.motorEnable.getValue() > 0:
			# Manual turns
			pass #self.headingError.setTarget(self.sensors.yaw().getValue() + self.joystickLeftRight.getValue() * self.maxManualTurn)
		elif self.autoModeEnable.getValue() > 0:
			self.stateMachine.changeState("StartSequence")
		else:
			self.stateMachine.changeState("MotorsOff")

	def nextSequence(self):
		seq = [(1000,1000),(1000,0),(1000,1000),(1000,0),(1000,1000),(1000,0),(1000,1000),(1000,0)]
		for move in range(len(seq)):
			nudge  = seq[move]
			yield nudge 
			
	def StartSequence(self):
		self.nextSeq = self.nextSequence()
		
	def Sequence(self, data):
		self.stateMachine.changeState("MoveDistance")
		
	def StartMoveDistance(self):
		# Test state
		self.autoModeForwardSpeed.setValue(0.4)
		if not self.pidL.auto_mode:
			# Switch back on the PIDs
			self.pidL.auto_mode = True
			self.pidR.auto_mode = True
		try:
			nudge = next(self.nextSeq)
			print(f"nudge: {nudge}")
			self.targetPositionL += nudge[0]
			self.targetPositionR += nudge[1]
			self.motorPositionErrorL.setTarget(self.targetPositionL)
			self.motorPositionErrorR.setTarget(self.targetPositionR)
			data = (self.targetPositionL, self.targetPositionR)
			print(f"StartMoveDistance: {data}")
			return data
		except StopIteration:
			return None
		
	def MoveDistance(self, data):
		# End of sequence?
		if data is None:
			self.stateMachine.changeState("MotorsOff")
			return
		# Reached target?
		currentPositionL = self.positionL.getValue()
		currentPositionR = self.positionR.getValue()
		print(f"MoveDistance: {data}; current: {(currentPositionL, currentPositionR)}")
		if abs(data[0] - currentPositionL) < 100 and abs(data[1] - currentPositionR) < 100:
			self.stateMachine.changeState("NextSequence")

	def EndMoveDistance(self, data):
		pass
		#self.autoModeEnable.reset()
		#self.autoModeForwardSpeed.setValue(0.0)

	def StartRotateAngle(self):
		pass
		
	def RotateAngle(self, data):
		pass

	def EndRotateAngle(self, data):
		self.autoModeForwardSpeed.setValue(0.0)


	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		
		# Set up the state machine
		self.stateMachine = StateMachine("MotorsOff")
		self.stateMachine.addState("MotorsOff", self.ControlOff, self.MotorsOffState, self.ControlOn)
		self.stateMachine.addState("Manual", None, self.ManualControl, None)
		self.stateMachine.addState("StartSequence", self.StartSequence, self.Sequence, None)
		self.stateMachine.addState("NextSequence", None, self.Sequence, None)
		self.stateMachine.addState("MoveDistance", self.StartMoveDistance, self.MoveDistance, self.EndMoveDistance)
		self.stateMachine.addState("RotateAngle", self.StartRotateAngle, self.RotateAngle, self.EndRotateAngle)

		# Set up the PIDs for the two motors
		self.pidL = PID(self.pidConstants[0], self.pidConstants[1], self.pidConstants[2], sample_time=0.025, proportional_on_measurement=self.proportionalOnMeasure, output_limits=(-1.0, 1.0))
		self.motorL = self.controls.motor(2)
		self.positionL = self.controls.motorPosition(2)
		self.motorPositionErrorL = SimplePIDErrorValue(self.pidL, self.positionL)
		self.targetPositionL = self.positionL.getValue()
		self.motorPositionErrorL.setTarget(self.targetPositionL)
		self.motorPositionErrorL.getValue()
		
		self.pidR = PID(self.pidConstants[0], self.pidConstants[1], self.pidConstants[2], sample_time=0.025, proportional_on_measurement=self.proportionalOnMeasure, output_limits=(-1.0, 1.0))
		self.motorR = self.controls.motor(1)
		self.positionR = self.controls.motorPosition(1)
		self.motorPositionErrorR = SimplePIDErrorValue(self.pidR, self.positionR)
		self.targetPositionR = self.positionR.getValue()
		self.motorPositionErrorR.setTarget(self.targetPositionR)
		self.motorPositionErrorR.getValue()

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
		self.motorsSpeedMode = ValueAdder([self.motorEnable, self.autoModeEnable, self.autoSequenceRun], max=2)
		
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											self.motorLSimpleManualSpeed,  \
																						 # Choice 2 = Auto mode, but manual forward speed
											self.motorLSimplePositionSpeed  \
																						 # Choice 3 = Full Auto mode
											#[SpeedDirectionCombiner(fullAutoForwardSpeed, Scaler(self.motorPositionErrorL, scaling = -self.maxForward))]  \
										   ],
											self.controls.motor(2), \
											self.motorsSpeedMode )
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
											self.motorsSpeedMode )
		highPriorityProcesses.append(motorR)

		# LED display state
		self.ledIndicator = self.controls.led(0)
		medPriorityProcesses.append(SimpleControlMediator( Scaler(self.motorEnable, scaling=2, offset=2, max=4), self.ledIndicator))
		
		# Nudge buttons
		self.NudgeForward = OneShotButtonValue(self.sensors.button(2), triggeredValue = 300)
		self.NudgeBackward = OneShotButtonValue(self.sensors.button(0), triggeredValue = 300)

	def nextSequence(self):
		seq = [(300,300),(300,0),(300,300),(300,0),(300,300),(300,0),(300,300),(300,0)]
		for move in range(len(seq)):
			nudge  = seq[move]
			yield nudge 

	def move(self):
		self.stateMachine.process()
	
	def stop(self):
		''' Stop the challenge
		'''
		self.stateMachine.changeState("MotorsOff")
		self.motorEnable.setValue(0, status=0)


	def XXmove(self):
		if self.autoModeEnable.getValue() > 0:
			if not self.pidL.auto_mode:
				# Switch back on the PIDs
				self.pidL.auto_mode = True
				self.pidR.auto_mode = True
			# Update targets
			nudge = self.NudgeForward.getValue() - self.NudgeBackward.getValue() 
			self.targetPositionL += nudge
			self.targetPositionR += nudge
			self.motorPositionErrorL.setTarget(self.targetPositionL)
			self.motorPositionErrorR.setTarget(self.targetPositionR)
			self.startTime = 0
			self.nextSeq = self.nextSequence()
			
		elif self.autoSequenceRun.getValue() > 0:
			# Step the sequence
			self.startTime += 1
			if not self.pidL.auto_mode:
				# Switch back on the PIDs
				self.pidL.auto_mode = True
				self.pidR.auto_mode = True
			if self.startTime % 100 == 1:
				nudge = next(self.nextSeq)
				print(f"nudge: {nudge}")
				self.targetPositionL += nudge[0]
				self.targetPositionR += nudge[1]
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

