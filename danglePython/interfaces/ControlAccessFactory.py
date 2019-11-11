# Direct access at the moment
#import redboard
from MotorAccessor import MotorAccessor
from ServoAccessor import ServoAccessor
from ServoControlSharedIPC import ServoControlSharedIPC
from SimpleControlSharedIPC import SimpleControlSharedIPC
from MotorControlSharedIPC import MotorControlSharedIPC
from LedAccessor import LedAccessor

class ControlAccessFactory:

	def __init__(self):
		# Initialise the IPC classes
		self.motorsIPC = MotorControlSharedIPC()
		self.motorsIPC.open()
		self.servosIPC = ServoControlSharedIPC()
		self.servosIPC.open()
		self.simpleControlsIPC = SimpleControlSharedIPC()
		self.simpleControlsIPC.open()

	__instance = None
	@classmethod
	def getSingleton(cls):
		if cls.__instance == None:
			cls.__instance = ControlIPC()
		return cls.__instance
		
	def process(self):
		# Do common processing of state
		pass
		
	def stopAllMotors(self):
		self.motorsIPC.resetWatchdog(0)
		self.servosIPC.resetWatchdog(0)
		#redboard.M1(0.0)
		#redboard.M2(0.0)

	def emergencyStop(self):
		self.stopAllMotors()
		#redboard.led_off()
		#redboard.Stop() # This destroys everying and stops the motors

	def resetWatchdog(self, count = 100):
		self.motorsIPC.resetWatchdog(count)
		self.servosIPC.resetWatchdog(count)
		
	####################################################################
	# Factory methods to access the control interfacte
	# These are the primary methods used to set the control IPC values
	def motor(self, motor):
		return MotorAccessor(self.motorsIPC, motor)
	def servo(self, servo):
		return ServoAccessor(self.servosIPC, servo)
	def led(self, led):
		return LedAccessor(self.simpleControlsIPC, led)
