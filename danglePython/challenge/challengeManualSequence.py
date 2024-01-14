import time
from challenge.challengeSequenceBase import ChallengeSequenceBase

# Interfaces
#from interfaces.ChallengeInterface import ChallengeInterface
#from interfaces.ControlAccessFactory import ControlAccessFactory
#from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.VisionAccessFactory import VisionAccessFactory
from interfaces.Config import Config
# Value providers
from analysis.SimplePIDErrorValue import SimplePIDErrorValue
from analysis.HeadingPIDErrorValue import HeadingPIDErrorValue
from analysis.OneShotButtonValue import OneShotButtonValue
from analysis.ToggleButtonValue import ToggleButtonValue
from analysis.TimedTriggerValue import TimedTriggerValue
from analysis.FixedValue import FixedValue
from analysis.LinearRamp import LinearRamp
# Value combination helpers
from analysis.Scaler import Scaler
from analysis.ValueIntegrator import ValueIntegrator
from analysis.ValueAdder import ValueAdder
from analysis.ValueLambda import ValueLambda
from analysis.SpeedDirectionCombiner import SpeedDirectionCombiner
# Control mediators
from challenge.SimpleControlMediator import SimpleControlMediator
#from challenge.SwitchingControlMediator import SwitchingControlMediator
#from analysis.StateMachine import StateMachine

class ChallengeManualSequence(ChallengeSequenceBase):

	def __init__(self):
		super().__init__()
		# Get config
		config = Config()
		self.servoRampSpeed = config.get("tidy.servo.rampspeed", 0.1)
		config.save()
		# Challenge Sequence
		self.sequenceDefFilename = "manualSequence.json"
		self.sequenceDefUpButtonFilename = "upSequence.json"
		self.sequenceDefDownButtonFilename = "downSequence.json"
		self.sequenceDefLeftButtonFilename = "leftSequence.json"
		self.sequenceDefRightButtonFilename = "rightSequence.json"
		self.sequenceDefSquareButtonFilename = "squareSequence.json"
		self.sequenceDefCrossButtonFilename = "crossSequence.json"
		self.sequenceDefTriangleButtonFilename = "triangleSequence.json"
		self.sequenceDefCircleButtonFilename = "circleSequence.json"

	# Override the Manual Control to enable initiation of sequences with that state
	def ManualControlHeading(self, data):
		# Record position
		#if self.resetLastPositionButton.getValue() > 0:
		#	self.lastPositionL = self.positionL.getValue()
		#	self.lastPositionR = self.positionR.getValue()
		#	self.pathRecord = []
		#elif self.recordPositionButton.getValue() > 0:
		#	currentPositionL = self.positionL.getValue()
		#	currentPositionR = self.positionR.getValue()
		#	self.pathRecord.append(("MoveDistance",[int(currentPositionL-self.lastPositionL), int(currentPositionR-self.lastPositionR)]))
		#	self.lastPositionL = currentPositionL
		#	self.lastPositionR = currentPositionR
		#elif self.savePositionsButton.getValue() > 0:
		#	pathFile = Config("recordedPath.json")
		#	pathFile.set("path", self.pathRecord)
		#	pathFile.save()
		#	#self.pathRecord = []

		# Simple remote control
		if self.motorEnable.getValue() > 0 :
			# Special buttons
			if self.runTestSequence1.getValue() > 0:
				self.autoModeEnable.setValue(1)
				self.stateMachine.changeState("StartSequence", self.sequenceDefUpButtonFilename)
			elif self.runTestSequence2.getValue() > 0:
				self.autoModeEnable.setValue(1)
				self.stateMachine.changeState("StartSequence", self.sequenceDefDownButtonFilename)
			elif self.runTestSequence3.getValue() > 0:
				self.autoModeEnable.setValue(1)
				self.stateMachine.changeState("StartSequence", self.sequenceDefLeftButtonFilename)
			elif self.runTestSequence4.getValue() > 0:
				self.autoModeEnable.setValue(1)
				self.stateMachine.changeState("StartSequence", self.sequenceDefRightButtonFilename)
			elif self.runTestSequenceSq.getValue() > 0:
				self.autoModeEnable.setValue(1)
				self.stateMachine.changeState("StartSequence", self.sequenceDefSquareButtonFilename)
			elif self.runTestSequenceCr.getValue() > 0:
				self.autoModeEnable.setValue(1)
				self.stateMachine.changeState("StartSequence", self.sequenceDefCrossButtonFilename)
			elif self.runTestSequenceTr.getValue() > 0:
				self.autoModeEnable.setValue(1)
				self.stateMachine.changeState("StartSequence", self.sequenceDefTriangleButtonFilename)
			elif self.runTestSequenceCi.getValue() > 0:
				self.autoModeEnable.setValue(1)
				self.stateMachine.changeState("StartSequence", self.sequenceDefCircleButtonFilename)
			# Manual turns
			elif self.joystickLeftRight.getValue() != 0.0:
				self.headingError.setTarget(self.sensors.yaw().getValue() + self.joystickLeftRight.getValue() * self.maxManualTurn)
		else:
			self.stateMachine.changeState("MotorsOff")


	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Set up the state machine and base behaviours
		super().createProcesses(highPriorityProcesses, medPriorityProcesses)
		
		##
		## Additional Controls
		##
		
		# Servos used within the state machine
		grabberPosition = FixedValue(0.0)
		grabberPositionRamp = LinearRamp(grabberPosition, increment=self.servoRampSpeed)
		grabber = SimpleControlMediator( Scaler(grabberPositionRamp, scaling=0.3, min=-1.0, max=1.0, offset=0.3), self.controls.servo(5) )
		grabber2 = SimpleControlMediator( Scaler(grabberPositionRamp, scaling=-0.3, min=-1.0, max=1.0, offset=-0.1), self.controls.servo(6) )
		highPriorityProcesses.append(grabber)
		highPriorityProcesses.append(grabber2)
		grabberHeight = FixedValue(0.0)
		grabHeight = SimpleControlMediator( Scaler(grabberHeight, scaling=1.0, min=-1.0, max=1.1, offset=0.1), self.controls.servo(27) )
		highPriorityProcesses.append(grabHeight)
		highPriorityProcesses.append(grabberPositionRamp)
		self.servos = {
			"grabber" : grabberPosition,
			"grabheight" : grabberHeight
			}
			
		# Image analysis
		self.imageAnalysisResult = VisionAccessFactory.getSingleton().getImageResult()

		# Further buttons
		self.runTestSequenceSq = self.sensors.button(3)
		self.runTestSequenceCr = self.sensors.button(0)
		self.runTestSequenceTr = self.sensors.button(2)
		self.runTestSequenceCi = self.sensors.button(1)

		# Nudge buttons
		#self.NudgeForward = OneShotButtonValue(self.sensors.button(2), triggeredValue = 300)
		#self.NudgeBackward = OneShotButtonValue(self.sensors.button(0), triggeredValue = 300)
