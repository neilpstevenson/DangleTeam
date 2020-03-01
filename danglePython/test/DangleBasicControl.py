import time
import pygame
import math
from simple_pid import PID
import atexit

# Interfaces
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
# Value providers
from analysis.SimplePIDErrorValue import SimplePIDErrorValue
from analysis.HeadingPIDErrorValue import HeadingPIDErrorValue
from analysis.OneShotButtonValue import OneShotButtonValue
from analysis.FixedValue import FixedValue
# Value combination helpers
from analysis.Scaler import Scaler
from analysis.ValueIntegrator import ValueIntegrator
from analysis.ValueAdder import ValueAdder
from analysis.ValueLambda import ValueLambda
# Control mediators
from challenge.SimpleControlMediator import SimpleControlMediator
from challenge.SwitchingControlMediator import SwitchingControlMediator

# Direct hardware for the moment
#from hardware.zgun import Zgun

pygame.init()

# recommended for auto-disabling motors on shutdown!
def stopAtExit():
	ControlAccessFactory.getSingleton().emergencyStop() # This destroys everying and stops the motors
atexit.register(stopAtExit)

class DangleControl:

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		self.highPriorityProcesses = []
		self.medPriorityProcesses = []
		self.counter = 0

	def processAll(self, processes):
		[x.process() for x in processes]
	
	def run(self):
		# Get initial state
		self.sensors.process()
		#target_heading = -self.sensors.yaw().getValue()

		# Set initial state of servos and motors
		self.controls.stopAllMotors()
	
		# Common controls
		self.highPriorityProcesses.append(self.controls)
		
		# Camera angle servo
		cameraTiltServo = self.controls.servo(6)
		currentPitch = Scaler(self.sensors.pitch(), scaling = -0.015)
		cameraUpDownButtons = ValueIntegrator(self.sensors.upDownButton(2, 0), scaling = -0.01, min=-0.85, max=0.85, offset = 0.5)
		cameraLeveller = SimpleControlMediator( Scaler([currentPitch, cameraUpDownButtons], min=-0.9, max=0.85 ), \
												cameraTiltServo )
		self.highPriorityProcesses.append(cameraLeveller)
		
		# Grabber hand servo
		grabberServo = self.controls.servo(5)
		grabReleaseButtons = ValueIntegrator(self.sensors.upDownButton(1, 3), min = -0.8, max = 0.6, scaling = 0.2)
		grabber = SimpleControlMediator( grabReleaseButtons, grabberServo )
		self.medPriorityProcesses.append(grabber)

		# Zgun
		zgunUpDownButtons = ValueIntegrator(self.sensors.upDownButton(13, 14), min = -1.0, max = 1.0, scaling = 0.005)
		zgunElevationServo = self.controls.servo(0)
		zgunElevation = SimpleControlMediator( zgunUpDownButtons, zgunElevationServo )
		self.highPriorityProcesses.append(zgunElevation)
		
		zgunTrigger = self.sensors.button(6)
		zgunFireMotor = self.controls.motor(0)
		zgunFire = SimpleControlMediator( zgunTrigger, zgunFireMotor )
		self.medPriorityProcesses.append(zgunFire)
		
		# Motors
		motorsStop = FixedValue(0.0)
		motorEnable = self.sensors.button(4)
		joystickForward = self.sensors.joystickAxis(1)
		joystickLeftRight = self.sensors.joystickAxis(3)
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											[ValueLambda(Scaler(joystickForward, scaling =  0.9)), ValueLambda(Scaler(joystickLeftRight, scaling = 0.5))]	# Joystick  \
										   ],
											self.controls.motor(2), \
											motorEnable )
		self.speedSensorL = self.sensors.counter(0)
		self.highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
																						 # Choice 1 = Controlled
											[ValueLambda(Scaler(joystickForward, scaling = 0.9)), ValueLambda(Scaler(joystickLeftRight, scaling = -0.5))]  # Joystick \
										   ],
											self.controls.motor(1), \
											motorEnable )
		self.highPriorityProcesses.append(motorR)
		self.speedSensorR = self.sensors.counter(1)

		ledIndicator = self.controls.led(0)
		
		# Set initial state of servos and motors
		self.processAll(self.highPriorityProcesses)
		self.processAll(self.medPriorityProcesses)
		
		# Loop until the user clicks the close button.
		done = False
		running = False
		
		
		while not done:
			self.counter += 1
			
			# Get current sensor state
			self.sensors.process()
			
			#
			# EVENT PROCESSING STEP
			#
			for event in pygame.event.get(): # User did something.
				if event.type == pygame.QUIT: # If user clicked close.
					done = True # Flag that we are done so we exit this loop.

			running = (motorEnable.getValue() > 0)
			if running:
				ledIndicator.setValue(0x04)
			else:
				ledIndicator.setValue(0x02)

			# Update everything
			self.processAll(self.highPriorityProcesses)
			if self.counter % 10 == 0:
				self.processAll(self.medPriorityProcesses)
			
			speedSensorL = self.speedSensorL.getValue()
			rateOfChange = self.speedSensorL.getRateOfChange()
			print(f"speedSensorL: {speedSensorL}, speed: {rateOfChange}")
			
			#zgunElevation = zgunUpDownButtons.getValue()
			#print(f"zgunElevation: {zgunElevation}")
			zgunFireVal = zgunTrigger.getValue()
			print(f"zgunFireVal: {zgunFireVal}")
			
			pygame.time.wait(10) # mS

			# Keep motors alive if sensors also alive
			if self.sensors.checkWatchdog() > 0:
				self.controls.resetWatchdog()
			else:
				motorEnable.setValue(0, status=0)
			
main = DangleControl()
main.run()
