# Interfaces
from interfaces.ChallengeInterface import ChallengeInterface
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
# Value combination helpers
from analysis.Scaler import Scaler
from analysis.ValueIntegrator import ValueIntegrator
# Control mediators
from challenge.SimpleControlMediator import SimpleControlMediator

class CameraLevellingControl(ChallengeInterface):

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()

	def createProcesses(self, highPriorityProcesses, medPriorityProcesses, cameraTilt = 0.5, scaling = -0.015):

		# Camera angle servo
		cameraTiltServo = self.controls.servo(6)
		currentPitch = Scaler(self.sensors.pitch(), scaling = scaling)
		cameraUpDownButtons = ValueIntegrator(self.sensors.upDownButton(2, 0), scaling = -0.01, min=-0.85, max=0.85, offset = cameraTilt)
		cameraLeveller = SimpleControlMediator( Scaler([currentPitch, cameraUpDownButtons], min=-0.9, max=0.85 ), \
												cameraTiltServo )
		highPriorityProcesses.append(cameraLeveller)
	
