# Interfaces
from interfaces.ChallengeInterface import ChallengeInterface
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
# Value combination helpers
from analysis.Scaler import Scaler
from analysis.ValueIntegrator import ValueIntegrator
# Control mediators
from challenge.SimpleControlMediator import SimpleControlMediator

class GrabberControl(ChallengeInterface):

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Grabber hand servo
		grabberServo = self.controls.servo(5)
		grabReleaseButtons = ValueIntegrator(self.sensors.upDownButton(1, 3), min = -0.8, max = 0.6, scaling = 0.2)
		grabber = SimpleControlMediator( grabReleaseButtons, grabberServo )
		medPriorityProcesses.append(grabber)
