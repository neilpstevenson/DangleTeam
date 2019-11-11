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
# Vision
from LineFollowerImageProcessor import LineFollowerImageProcessor

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
		
		# Vision
		visionHeadingError = LineFollowerImageProcessor()

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
		
		# Motors
		motorsStop = FixedValue(0.0)
		motorEnable = self.sensors.button(4)
		joystickForward = self.sensors.joystickAxis(1)
		joystickLeftRight = self.sensors.joystickAxis(3)
		visionHeadingLeftRight = Scaler(visionHeadingError, max=0.7, min=-0.7, scaling = 0.003)
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											[Scaler(joystickForward, scaling = 0.8), Scaler(joystickLeftRight, scaling = -0.5), visionHeadingLeftRight]	# Joystick  \
										   ],
											self.controls.motor(2), \
											motorEnable )
		self.highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
																						 # Choice 1 = Controlled
											[Scaler(joystickForward, scaling = -0.8), Scaler(joystickLeftRight, scaling = -0.5), visionHeadingLeftRight]  # Joystick \
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
			
			#angle = visionHeadingLeftRight.getValue()
			#print(f"visionHeadingLeftRight={angle}")

			running = (motorEnable.getValue() > 0)
			if running:
				self.controls.setLightState(0, 1)
			else:
				self.controls.setLightState(0, 0)

			# Update everything
			self.processAll(self.highPriorityProcesses)
			if self.counter % 10 == 0:
				self.processAll(self.medPriorityProcesses)
			
			pygame.time.wait(10) # mS

main = DangleControl()
main.run()













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

	def normaliseHeading(self, heading):
		if heading > 180.0:
			return heading - 360.0
		elif heading < -180.0:
			return heading + 360.0
		return heading

	def processAll(self, processes):
		[x.process() for x in processes]
	
	def run(self):
		# Get initial state
		self.sensors.process()
		#target_heading = -self.sensors.yaw().getValue()

		# Set initial state of servos and motors
		self.controls.stopAllMotors()
	
		
		#pidLeft = PID(0.4, 0.8, 0.02, setpoint=0, sample_time=0.01, proportional_on_measurement=True)
		#pidLeft.output_limits = (-1.0, 1.0)
		#pidRight = PID(0.4, 0.8, 0.02, setpoint=0, sample_time=0.01, proportional_on_measurement=True)
		#pidRight.output_limits = (-1.0, 1.0)
		pidHeadingL = PID(0.1, 0.000, 0.003, setpoint=0, sample_time=0.01, proportional_on_measurement=False, output_limits = (-1.0, 1.0))
		pidHeadingR = PID(0.1, 0.000, 0.003, setpoint=0, sample_time=0.01, proportional_on_measurement=False, output_limits = (-1.0, 1.0))

		# Value generatators for speed control based on heading direction
		headingErrorValueL = HeadingPIDErrorValue(self.sensors.yaw(), pidHeadingL, 0.0)
		headingErrorValueR = HeadingPIDErrorValue(self.sensors.yaw(), pidHeadingR, 0.0, scaling=-1.0)
		
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
		
		# Motors
		motorsStop = FixedValue(0.0)
		motorEnable = self.sensors.button(4)
		joystickForward = self.sensors.joystickAxis(1)
		joystickLeftRight = self.sensors.joystickAxis(3)
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											[Scaler(joystickForward, scaling = 0.8), Scaler(joystickLeftRight, scaling = -0.5)]	# Joystick  \
										   ],
											self.controls.motor(2), \
											motorEnable )
		self.highPriorityProcesses.append(motorL)
		motorR = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
																						 # Choice 1 = Controlled
											[Scaler(joystickForward, scaling = -0.8), Scaler(joystickLeftRight, scaling = -0.5)]  # Joystick \
										   ],
											self.controls.motor(1), \
											motorEnable )
		self.highPriorityProcesses.append(motorR)

		# Vision
		imageProcessor = LineFollowerImageProcessor()
		
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

			heading = -self.sensors.yaw().getValue()
			button_rotate = rotateLeft.getValue() - rotateRight.getValue()
			
			running = (motorEnable.getValue() > 0)
			if running:
				self.controls.setLightState(0, 1)
				pidHeadingL.auto_mode = True
				pidHeadingR.auto_mode = True
				# Get the offset for the white line
				#_,lineAngle = imageProcessor.captureAndAssess()
				lineAngle = imageProcessor.getValue()
				# clamp rotate to prevent sudden changes
				if lineAngle > 10.0:
					lineAngle = 10.0
				elif lineAngle < -10.0:
					lineAngle = -10.0
				target_heading = self.normaliseHeading(heading - lineAngle)
				print(f"White line indicate rotate from {heading} to {target_heading}")
				target_heading = self.normaliseHeading(target_heading + button_rotate)
				headingErrorValueL.setTarget(target_heading)
				headingErrorValueR.setTarget(target_heading)

			else:
				self.controls.setLightState(0, 0)
				# Just idle to a standstill
				pidHeadingL.auto_mode = False
				pidHeadingR.auto_mode = False
				#target_heading = heading # So doesn't spin when button is released
				headingErrorValueL.setTarget(heading)
				headingErrorValueR.setTarget(heading)
				
			#print("L: {0:6.3f} => {2:6.3f}, R: {1:6.3f} => {3:6.3f}".format(leftThrottle, rightThrottle, pidLeft.setpoint, pidRight.setpoint ))

			# Update everything
			self.processAll(self.highPriorityProcesses)
			if self.counter % 10 == 0:
				self.processAll(self.medPriorityProcesses)
			
			#imageProcessor.captureAndDisplay()
			
			#time.sleep(0.1)
			pygame.time.wait(10) # mS

main = DangleControl()
main.run()
