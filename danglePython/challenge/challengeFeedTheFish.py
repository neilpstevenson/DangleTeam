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

class ChallengeFeedTheFish(ChallengeSequenceBase):

	def __init__(self):
		super().__init__()
		# Get config
		#config = Config()
		#self.maxAutoHeadingTurn = config.get("tidy.autoheadingturn.max", 0.3) # PID output scaling (full auto mode)
		#config.save()
		# Challenge Sequence
		self.sequenceDefFilename = "feedTheFishSequence.json"
		pass

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Set up the state machine and base behaviours
		super().createProcesses(highPriorityProcesses, medPriorityProcesses)
		
		##
		## Additional Controls
		##
		
		# Flinger fire button
		flingerFire = ToggleButtonValue(self.sensors.button(2))
		flinger = SimpleControlMediator( Scaler(flingerFire, min=-0.2, max=0.3, offset=-0.2), self.controls.servo(20) )
		medPriorityProcesses.append(flinger)
		
		# Servos used within the state machine
		self.servos = {
			"fire" : flingerFire
			}
			
		# Image analysis
		self.imageAnalysisResult = VisionAccessFactory.getSingleton().getImageResult()

		# Nudge buttons
		#self.NudgeForward = OneShotButtonValue(self.sensors.button(2), triggeredValue = 300)
		#self.NudgeBackward = OneShotButtonValue(self.sensors.button(0), triggeredValue = 300)
