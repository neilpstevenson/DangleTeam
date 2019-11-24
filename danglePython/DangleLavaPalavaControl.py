import time
import pygame
import math
from simple_pid import PID
import atexit

# Interfaces
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.VisionAccessFactory import VisionAccessFactory
# Value providers
from analysis.Scaler import Scaler
from analysis.SimplePIDErrorValue import SimplePIDErrorValue
from analysis.HeadingPIDErrorValue import HeadingPIDErrorValue
from analysis.OneShotButtonValue import OneShotButtonValue
from analysis.FixedValue import FixedValue
# Value combination helpers
from analysis.ValueIntegrator import ValueIntegrator
from analysis.ValueAdder import ValueAdder
# Control mediators
from challenge.SimpleControlMediator import SimpleControlMediator
from challenge.SwitchingControlMediator import SwitchingControlMediator

pygame.init()

# recommended for auto-disabling motors on shutdown!
def stopAtExit():
	ControlAccessFactory.getSingleton().emergencyStop() # This destroys everying and stops the motors
atexit.register(stopAtExit)

class DangleControl:

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		self.vision = VisionAccessFactory.getSingleton()
		self.highPriorityProcesses = []
		self.medPriorityProcesses = []
		self.counter = 0

	def processAll(self, processes):
		[x.process() for x in processes]
	
	def run(self):
		# Get initial state
		self.sensors.process()

		# Set initial state of servos and motors
		self.controls.stopAllMotors()

		# Yaw control
		yaw = self.sensors.yaw()
		targetLineHeading = self.vision.getLineHeading()
		pidHeading = PID(0.3,0.003,0.05, sample_time=0.05)
		target_heading = HeadingPIDErrorValue(yaw, pidHeading, yaw.getValue(), min = -0.2, max = 0.2, scaling=0.04)
		# Initialise the PID
		target_heading.getValue()
		
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
		grabber = SimpleControlMediator( grabReleaseButtons, \
										 grabberServo )
		self.medPriorityProcesses.append(grabber)
		
		# Motors
		motorsStop = FixedValue(0.0)
		motorsForward = FixedValue(-0.2)
		motorEnable = self.sensors.button(4)
		joystickForward = self.sensors.joystickAxis(1)
		joystickLeftRight = self.sensors.joystickAxis(3)
		
		# Speed PID controller
		## LEFT
		speedSensorL = self.sensors.rateCounter(0) # Raw speed
		speedSensorScaledL = Scaler(speedSensorL, scaling = 0.0005) # Roughly +/-1000 => +/1.0 max speed
		speedRequestL = ValueAdder([motorsForward, Scaler(joystickForward, scaling = 0.5), Scaler(joystickLeftRight, scaling = -0.2), Scaler(target_heading, scaling = -1.0)])
		#pidL = PID(2.0,0.0,0.05, sample_time=0.05, output_limits=(-1.0, 1.0), proportional_on_measurement = False)
		pidL = PID(0.3,0.3,0.05, sample_time=0.05, output_limits=(-1.0, 1.0), proportional_on_measurement = True)
		torqueErrorL = SimplePIDErrorValue(pidL, Scaler(speedSensorScaledL, scaling = -1.0))
		#torqueL = ValueAdder([speedRequestL, torqueErrorL])
		torqueL = speedRequestL
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											[torqueL]	# Speed control via PID  \
										   ],
											self.controls.motor(2), \
											motorEnable )
		self.highPriorityProcesses.append(motorL)
		## RIGHT
		speedSensorR = self.sensors.rateCounter(1) # Raw speed
		speedSensorScaledR = Scaler(speedSensorR, scaling = -0.0005) # Roughly +/-1000 => +/1.0 max speed
		speedRequestR = ValueAdder([motorsForward, Scaler(joystickForward, scaling = 0.5), Scaler(joystickLeftRight, scaling = 0.2), Scaler(target_heading, scaling = 1.0)])
		#pidL = PID(2.0,0.0,0.05, sample_time=0.05, output_limits=(-1.0, 1.0), proportional_on_measurement = False)
		pidR = PID(0.3,0.3,0.05, sample_time=0.05, output_limits=(-1.0, 1.0), proportional_on_measurement = True)
		torqueErrorR = SimplePIDErrorValue(pidR, Scaler(speedSensorScaledR, scaling = -1.0))
		#torqueR = ValueAdder([speedRequestR, torqueErrorR], scaling=-1.0)
		torqueR = ValueAdder([speedRequestR], scaling=-1.0)
		motorR = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											[torqueR]	# Speed control via PID  \
										   ],
											self.controls.motor(1), \
											motorEnable )
		self.highPriorityProcesses.append(motorR)

		# Led Status
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
				if not pidHeading.auto_mode:
					pidHeading.auto_mode = True
				target_heading.setTarget(targetLineHeading.getValue())
				targetL = speedRequestL.getValue()
				print(f"targetL: {targetL}")
				torqueErrorL.setTarget(targetL)
				if not pidL.auto_mode:
					pidL.auto_mode = True
				targetR = speedRequestR.getValue()
				#print(f"targetR: {targetR}")
				torqueErrorR.setTarget(targetR)
				if not pidR.auto_mode:
					pidR.auto_mode = True
			else:
				ledIndicator.setValue(0x02)
				torqueErrorL.setTarget(0.0)
				pidL.auto_mode = False
				torqueErrorR.setTarget(0.0)
				pidR.auto_mode = False
				target_heading.setTarget(yaw.getValue())
				pidHeading.auto_mode = False
				

			# Update everything
			self.processAll(self.highPriorityProcesses)
			if self.counter % 10 == 0:
				self.processAll(self.medPriorityProcesses)
			
			#speedSensorValL = speedSensorL.getCounter()
			rateOfChangeL = speedSensorL.getValue()
			speedL = speedSensorScaledL.getValue()
			print(f"scaled speedL: {speedL}, speed: {rateOfChangeL}")
			pidLcomponents = pidL.components
			print(f"pidL: {pidLcomponents}")
			#speedSensorValR = speedSensorR.getCounter()
			#rateOfChangeR = speedSensorR.getValue()
			#print(f"speedSensorValR: {speedSensorValR}, speed: {rateOfChangeR}")
			
			#if running:
			#	currentTorqueL = torqueL.getValue()
			#	torqueLprev.setValue(currentTorqueL)
			#	currentTorqueR = torqueR.getValue()
			#	torqueRprev.setValue(currentTorqueR)
			#else:
			#	torqueLprev.setValue(0.0)
			#	torqueRprev.setValue(0.0)
			
			pygame.time.wait(10) # mS

			# Keep motors alive if sensors also alive
			if self.sensors.checkWatchdog() > 0:
				self.controls.resetWatchdog()
			else:
				motorEnable.setValue(0, status=0)
			
main = DangleControl()
main.run()
