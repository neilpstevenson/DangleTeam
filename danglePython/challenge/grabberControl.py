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

class GrabberControl(ChallengeInterface):

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		config = Config()
		self.min = config.get("grabber.open", -0.75)
		self.max = config.get("grabber.closed", 0.25)
		self.speed = config.get("grabber.speed", 0.2)
		config.save()

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Grabber hand servo
		grabberServo = self.controls.servo(5)
		grabReleaseButtons = ValueIntegrator(self.sensors.upDownButton(16, 15), min = self.min, max = self.max, scaling = self.speed)
		grabber = SimpleControlMediator( grabReleaseButtons, grabberServo )
		medPriorityProcesses.append(grabber)
