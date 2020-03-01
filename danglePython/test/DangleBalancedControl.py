import time
import pygame
import math
from simple_pid import PID
import atexit

# Interfaces
from ControlIPC import ControlIPC
from SensorIPC import SensorIPC
# Value providers
from Scaler import Scaler
from SimplePIDErrorValue import SimplePIDErrorValue
from HeadingPIDErrorValue import HeadingPIDErrorValue
from OneShotButtonValue import OneShotButtonValue
from FixedValue import FixedValue
# Value combination helpers
from ValueIntegrator import ValueIntegrator
from ValueAdder import ValueAdder
# Control mediators
from SimpleControlMediator import SimpleControlMediator
from SwitchingControlMediator import SwitchingControlMediator

pygame.init()

# recommended for auto-disabling motors on shutdown!
def stopAtExit():
	ControlIPC.getSingleton().emergencyStop() # This destroys everying and stops the motors
atexit.register(stopAtExit)

class DangleControl:

	def __init__(self):
		self.controls = ControlIPC.getSingleton()
		self.sensors = SensorIPC.getSingleton()
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
		currentPitch = Scaler(self.sensors.pitch(), scaling = -0.0075)
		cameraUpDownButtons = ValueIntegrator(self.sensors.upDownButton(2, 0), scaling = -0.005, min=0.1, max=0.85, offset = 0.725)
		cameraLeveller = SimpleControlMediator( Scaler([currentPitch, cameraUpDownButtons], min=0.05, max=0.9 ), \
												cameraTiltServo )
		self.highPriorityProcesses.append(cameraLeveller)
		
		# Grabber hand servo
		grabberServo = self.controls.servo(5)
		grabReleaseButtons = ValueIntegrator(self.sensors.upDownButton(1, 3), min = 0.1, max = 0.8, scaling = 0.1)
		grabber = SimpleControlMediator( grabReleaseButtons, \
										 grabberServo )
		self.medPriorityProcesses.append(grabber)
		
		# Balance
		pidL = PID(0.02,0.001,0.01, proportional_on_measurement = False)
		pidR = PID(0.02,0.001,0.01, proportional_on_measurement = False)
		pitchBalanceL = SimplePIDErrorValue(pidL, self.sensors.pitch())
		pitchBalanceR = SimplePIDErrorValue(pidR, self.sensors.pitch(), scaling = -1.0)
		
		# Motors
		motorsStop = FixedValue(0.0)
		motorEnable = self.sensors.button(4)
		joystickForward = self.sensors.joystickAxis(1)
		joystickLeftRight = self.sensors.joystickAxis(3)
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											[pitchBalanceL, Scaler(joystickForward, scaling = 0.8), Scaler(joystickLeftRight, scaling = -0.4)]	# Joystick  \
										   ],
											self.controls.motor(2), \
											motorEnable )
		self.highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
																						 # Choice 1 = Controlled
											[pitchBalanceR, Scaler(joystickForward, scaling = -0.8), Scaler(joystickLeftRight, scaling = -0.4)]  # Joystick \
										   ],
											self.controls.motor(1), \
											motorEnable )
		self.highPriorityProcesses.append(motorR)

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
				self.controls.setLightState(0, 1)
				pidL.auto_mode = True
				pidR.auto_mode = True
			else:
				self.controls.setLightState(0, 0)
				# Reset balance state
				pidL.setpoint = pidR.setpoint = self.sensors.pitch().getValue()
				pidL.auto_mode = False
				pidR.auto_mode = False

			# Update everything
			self.processAll(self.highPriorityProcesses)
			if self.counter % 10 == 0:
				self.processAll(self.medPriorityProcesses)
			
			pygame.time.wait(10) # mS

main = DangleControl()
main.run()
