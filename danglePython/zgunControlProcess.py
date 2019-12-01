# Basic motor control process, using IPC interface
import pygame
from hardware.zgun import Zgun
from interfaces.MotorControlSharedIPC import MotorControlSharedIPC
from interfaces.ServoControlSharedIPC import ServoControlSharedIPC
from interfaces.SimpleControlSharedIPC import SimpleControlSharedIPC
import atexit

pygame.init()

# recommended for auto-disabling motors on shutdown!
#atexit.register(redboard.Stop)

class MotorControlProcess:

	managedServos = [0]
	managedMotors = [0]
	
	def __init__(self):
		# Initialise the IPC classes
		self.motorsIPC = MotorControlSharedIPC()
		self.motorsIPC.create()
		self.currentMotorValues = [0.0]*3
		self.servosIPC = ServoControlSharedIPC()
		self.servosIPC.create()
		self.currentServoValues = [0.0]*32
		self.zgun=Zgun()

	def run(self):
		done = False
		running = False
		
		while not done:
			# Check for quit
			for event in pygame.event.get(): # User did something.
				if event.type == pygame.QUIT: # If user clicked close.
					done = True # Flag that we are done so we exit this loop.

			if running:
				# Adjust the elevation servo
				for servo in MotorControlProcess.managedServos:
					if self.servosIPC.getStatus(servo) > 0:
						# Active
						newPosition = self.servosIPC.getPosition(servo) * 500.0 + 1500.0 # 1000-2000 is allowed range
						if self.currentServoValues[servo] != newPosition:
							self.currentServoValues[servo] = newPosition
							self.zgun.setpos(newPosition)
					else:
						# Inactive
						pass
						
				
				# Trigger the motors to fire
				for motor in MotorControlProcess.managedMotors:
					torque = self.motorsIPC.getRequiredTorque(motor)
					if torque > 0.0:
						# Trigger
						print("Fire!")
						self.zgun.fire()
						# Clear the trigger status
						self.motorsIPC.setRequiredTorque(motor, 0.0)
					self.currentMotorValues[motor] = torque

			# This controller is not time-sensitive
			pygame.time.wait(50) # mS

			if self.motorsIPC.checkWatchdog() == 0:
				print("MotorControlProcess: Paused due to watchdog expiry")
				running = False
				for servo in MotorControlProcess.managedServos:
					pass
					#servo_off(servo)
				for motor in MotorControlProcess.managedMotors:
					self.motorsIPC.setRequiredTorque(motor, 0.0)
					#motor_off(motor)
				pygame.time.wait(1000) # mS
			else:
				running = True

main = MotorControlProcess()
main.run()
			
