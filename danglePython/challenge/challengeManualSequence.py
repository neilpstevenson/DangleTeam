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
		pass

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

		# Nudge buttons
		#self.NudgeForward = OneShotButtonValue(self.sensors.button(2), triggeredValue = 300)
		#self.NudgeBackward = OneShotButtonValue(self.sensors.button(0), triggeredValue = 300)
