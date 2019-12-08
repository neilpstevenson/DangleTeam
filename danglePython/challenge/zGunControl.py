# Interfaces
from interfaces.ChallengeInterface import ChallengeInterface
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
# Value combination helpers
from analysis.Scaler import Scaler
from analysis.ValueIntegrator import ValueIntegrator
# Control mediators
from challenge.SimpleControlMediator import SimpleControlMediator

class ZGunControl(ChallengeInterface):

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses):
		# Zgun elevation
		zgunUpDownButtons = ValueIntegrator(self.sensors.upDownButton(13, 14), min = -1.0, max = 1.0, scaling = 0.005)
		zgunElevationServo = self.controls.servo(0)
		zgunElevation = SimpleControlMediator( zgunUpDownButtons, zgunElevationServo )
		highPriorityProcesses.append(zgunElevation)
		# Fire button
		zgunTrigger = self.sensors.button(6)
		zgunFireMotor = self.controls.motor(0)
		zgunFire = SimpleControlMediator( zgunTrigger, zgunFireMotor )
		medPriorityProcesses.append(zgunFire)
		
