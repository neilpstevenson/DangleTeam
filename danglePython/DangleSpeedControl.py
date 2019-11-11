import time
import pygame
import math
from simple_pid import PID
import atexit

# Interfaces
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
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
		grabber = SimpleControlMediator( grabReleaseButtons, \
										 grabberServo )
		self.medPriorityProcesses.append(grabber)
		
		# Motors
		motorsStop = FixedValue(0.0)
		motorEnable = self.sensors.button(4)
		joystickForward = self.sensors.joystickAxis(1)
		joystickLeftRight = self.sensors.joystickAxis(3)
		
		# Speed PID controller
		speedSensorL = self.sensors.rateCounter(0)
		speedRequestL = Scaler([Scaler(joystickForward, scaling = 0.8), Scaler(joystickLeftRight, scaling = -0.5)], scaling = 1.0)
		pidL = PID(0.5,0.1,0.05, proportional_on_measurement = False)
		pidTorqueErrorL = SimplePIDErrorValue(pidL, Scaler(speedSensorL, scaling = 0.0008)) # Full speed => 0.8 ish
		torqueLprev = FixedValue(0.0)
		torqueL = Scaler([speedRequestL, pidTorqueErrorL])
		motorL = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
											  											 # Choice 1 = Controlled
											[torqueL]	# Speed control via PID  \
										   ],
											self.controls.motor(2), \
											motorEnable )
		self.highPriorityProcesses.append(motorL)
		
		speedSensorR = self.sensors.rateCounter(1)
		speedRequestR = Scaler([Scaler(joystickForward, scaling = 0.8), Scaler(joystickLeftRight, scaling = 0.5)], scaling = -1.0)
		pidR = PID(0.5,0.1,0.05, proportional_on_measurement = False)
		pidTorqueErrorR = SimplePIDErrorValue(pidR, Scaler(speedSensorR, scaling = -0.0008)) # Full speed => 0.8 ish
		torqueRprev = FixedValue(0.0)
		torqueR = Scaler([speedRequestR, pidTorqueErrorR])
		motorR = SwitchingControlMediator( [ motorsStop, 								 # Choice 0 = Stopped \
																						 # Choice 1 = Controlled
											[torqueR]	# Speed control via PID  \
										   ],
											self.controls.motor(1), \
											motorEnable )
		self.highPriorityProcesses.append(motorR)

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
				targetL = speedRequestL.getValue()
				print(f"targetL: {targetL}")
				pidTorqueErrorL.setTarget(targetL)
				if not pidL.auto_mode:
					pidL.auto_mode = True
				targetR = speedRequestR.getValue()
				print(f"targetR: {targetR}")
				pidTorqueErrorR.setTarget(targetR)
				if not pidR.auto_mode:
					pidR.auto_mode = True
			else:
				ledIndicator.setValue(0x02)
				pidTorqueErrorL.setTarget(0.0)
				pidL.auto_mode = False
				pidTorqueErrorR.setTarget(0.0)
				pidR.auto_mode = False
				

			# Update everything
			self.processAll(self.highPriorityProcesses)
			if self.counter % 10 == 0:
				self.processAll(self.medPriorityProcesses)
			
			speedSensorValL = speedSensorL.getCounter()
			rateOfChangeL = speedSensorL.getValue()
			print(f"speedSensorValL: {speedSensorValL}, speed: {rateOfChangeL}")
			speedSensorValR = speedSensorR.getCounter()
			rateOfChangeR = speedSensorR.getValue()
			print(f"speedSensorValR: {speedSensorValR}, speed: {rateOfChangeR}")
			
			if running:
				currentTorqueL = torqueL.getValue()
				torqueLprev.setValue(currentTorqueL)
				currentTorqueR = torqueR.getValue()
				torqueRprev.setValue(currentTorqueR)
			else:
				torqueLprev.setValue(0.0)
				torqueRprev.setValue(0.0)
			
			pygame.time.wait(10) # mS

			# Keep motors alive
			self.controls.resetWatchdog()
			
main = DangleControl()
main.run()
