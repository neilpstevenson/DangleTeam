# Basic motor control process, using IPC interface
import pygame
import redboard
from Motor import Motor
from MotorControlShared import MotorControlShared
from ServoControlShared import ServoControlShared
from SimpleControlShared import SimpleControlShared
import atexit

pygame.init()

# recommended for auto-disabling motors on shutdown!
atexit.register(redboard.Stop)

class MotorControlProcess:

	managedServos = (5,6,13,27,20,21,22)
	
	def __init__(self):
		# Initialise the IPC classes
		self.motorsIPC = MotorControlShared()
		self.motorsIPC.create()
		self.currentMotorValues = [0.0]*3
		self.servosIPC = ServoControlShared()
		self.servosIPC.create()
		self.currentServoValues = [0.0]*32
		self.simpleControlsIPC = SimpleControlShared()
		self.simpleControlsIPC.create()
		self.currentSimpleValues = [0]*32
		
	def run(self):
		done = False
		running = False
		motorL = Motor(2)
		motorR = Motor(1)
		
		while not done:
			# Check for quit
			for event in pygame.event.get(): # User did something.
				if event.type == pygame.QUIT: # If user clicked close.
					done = True # Flag that we are done so we exit this loop.

			if running:
				# Adjust torque
				torqueL = self.motorsIPC.getRequiredTorque(2)
				torqueR = self.motorsIPC.getRequiredTorque(1)
				if torqueL != self.currentMotorValues[2] or torqueR != self.currentMotorValues[1]:
					self.currentMotorValues[2] = torqueL
					self.currentMotorValues[1] = torqueR
					print(f"Left: {torqueL}, Right {torqueR}")
				motorL.setTorque(torqueL)
				motorR.setTorque(torqueR)
				#redboard.M2(torqueL*100.0)
				#redboard.M1(torqueR*100.0)
					
				# Also copy over all of the servo values
				for servo in MotorControlProcess.managedServos:
					if self.servosIPC.getStatus(servo) > 0:
						newPosition = self.servosIPC.getPosition(servo) * 1000.0 + 1500.0 # 500-2500 is allowed range
						if newPosition != self.currentServoValues[servo]:
							self.currentServoValues[servo] = newPosition
							redboard.servo_P(servo, newPosition)
					elif self.currentServoValues[servo] != 0.0:
						self.currentServoValues[servo] = 0.0
						redboard.servo_off(servo)
						
				# Simple control #0 is the colour LED control
				if self.simpleControlsIPC.getType(0) > 0:
					led = self.simpleControlsIPC.getValue(0)
					if led != self.currentSimpleValues[0]: 
						self.currentSimpleValues[0] = led
						if led & 0x04:
							redboard.red_on()
						else:
							redboard.red_off()
						if led & 0x02:
							redboard.green_on()
						else:
							redboard.green_off()
						if led & 0x01:
							redboard.blue_on()
						else:
							redboard.blue_off()

			pygame.time.wait(10) # mS

			if self.motorsIPC.checkWatchdog() == 0:
				print("MotorControlProcess: Paused due to watchdog expiry")
				running = False
				#redboard.M2(0.0)
				#redboard.M1(0.0)
				for servo in MotorControlProcess.managedServos:
					redboard.servo_off(servo)
				for i in range(100):
					# Allow the motors to return to idle normally
					motorL.setTorque(0.0)
					motorR.setTorque(0.0)
					pygame.time.wait(10) # mS
			else:
				running = True

main = MotorControlProcess()
main.run()
			