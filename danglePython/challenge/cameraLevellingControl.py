# Interfaces
from interfaces.ChallengeInterface import ChallengeInterface
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.Config import Config
# Value combination helpers
from analysis.Scaler import Scaler
from analysis.ValueIntegrator import ValueIntegrator
# Control mediators
from challenge.SimpleControlMediator import SimpleControlMediator

class CameraLevellingControl(ChallengeInterface):

	def __init__(self, configPrefix = "camera"):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		# Get config
		config = Config()
		self.scaling = config.get(f"{configPrefix}.leveling.scaling", 0.012)
		config.save()

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses, cameraTilt = 0.5):

		# Camera angle servo
		cameraTiltServo = self.controls.servo(6)
		currentPitch = Scaler(self.sensors.pitch(), scaling = self.scaling)
		cameraUpDownButtons = ValueIntegrator(self.sensors.upDownButton(2, 0), scaling = 0.01, min=-0.70, max=0.90, offset = cameraTilt)
		cameraLeveller = SimpleControlMediator( Scaler([currentPitch, cameraUpDownButtons], min=-0.75, max=0.90 ), \
												cameraTiltServo )
		highPriorityProcesses.append(cameraLeveller)
	
