from interfaces.MotionSensorSharedIPC import MotionSensorSharedIPC
import pygame
from interfaces.JoystickAxis import JoystickAxis
from interfaces.Button import Button
from interfaces.UpDownButton import UpDownButton
from interfaces.Roll import Roll
from interfaces.Pitch import Pitch
from interfaces.Yaw import Yaw
from interfaces.SensorsSharedIPC import SensorsSharedIPC
from interfaces.CounterSensor import CounterSensor
from interfaces.CounterChangeSensor import CounterChangeSensor
from interfaces.AnalogSensor import AnalogSensor

class SensorAccessFactory:

	def __init__(self):
		# Initialise the IPC classes
		self.mpu = MotionSensorSharedIPC()
		self.sensorsIPC = SensorsSharedIPC()
		self.sensorsIPC.open()

	__instance = None
	@classmethod
	def getSingleton(cls):
		if cls.__instance == None:
			cls.__instance = SensorAccessFactory()
		return cls.__instance
		
	def process(self):
		# Do common processing of state
		for event in pygame.event.get():
			# Processes necessary events to update current joystick state
			pass
		self.mpu.updateReading()

	## Raw MPU accessor methods
	def getAcceleration(self):
		return self.mpu.get_accel()
	def getGyro(self):
		return self.mpu.get_gyro()
	def getMpuSampleNumber():
		return self.mpu.get_sample_number()
	def getMpuTimestampSeconds():
		return self.mpu.get_timestamp()
	# Compass reading - this is pretty unstable!
	def getMpuTimestampSeconds():
		return self.mpu.get_compassDegrees()
	# MPU tap and orientation detector
	def getTapCount():
		return self.mpu.get_tap_count(self)
	def getOrientation():
		return self.mpu.get_orientation()

	####################################################################
	# Factory methods to access the sensor interfacte
	# These are the primary methods used to access the sensor IPC values
	def joystickAxis(self, axis):
		return JoystickAxis(self.sensorsIPC, axis)
	def button(self, button):
		return Button(self.sensorsIPC, button)
	def upDownButton(self, buttonUp, buttonDown):
		return UpDownButton(self.sensorsIPC, buttonUp, buttonDown)
	def analog(self, sensor):
		return AnalogSensor(self.sensorsIPC, sensor)
	def counter(self, sensor):
		return CounterSensor(self.sensorsIPC, sensor)
	def rateCounter(self, sensor):
		return CounterChangeSensor(self.sensorsIPC, sensor)
		
	# Get current orientation positions as Euler angles
	def roll(self):
		return Roll(self.mpu)
	def pitch(self):
		return Pitch(self.mpu)
	def yaw(self):
		return Yaw(self.mpu)
