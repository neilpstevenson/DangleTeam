import time
# Basic motor control process, using IPC interface
from hardware.zgun import Zgun
from interfaces.MotorControlSharedIPC import MotorControlSharedIPC
from interfaces.ServoControlSharedIPC import ServoControlSharedIPC
from interfaces.SimpleControlSharedIPC import SimpleControlSharedIPC
import atexit

# recommended for auto-disabling motors on shutdown!
def stopAtExit():
	main.stopAll()
atexit.register(stopAtExit)

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
		self.currentServoValues = [0]*32
		self.zgun=Zgun()

	def stopAll(self):
		self.zgun.arm(False)
		
	def run(self):
		done = False
		running = False
		while not done:
			if running:
				# Adjust the elevation servo
				for servo in MotorControlProcess.managedServos:
					if self.servosIPC.getStatus(servo) > 0:
						# Active
						newPosition = int(self.servosIPC.getPosition(servo) * 500.0 + 1500.0) # 1000-2000 is allowed range
						if self.currentServoValues[servo] != newPosition:
							self.currentServoValues[servo] = newPosition
							self.zgun.setpos(newPosition)
					else:
						# Inactive
						pass
						
				
				# Trigger the motors to fire
				for motor in MotorControlProcess.managedMotors:
					if self.motorsIPC.getMode(motor) > 0:
						self.zgun.arm(True)
						torque = self.motorsIPC.getRequiredTorque(motor)
						if torque > 0.0:
							# Trigger
							print("Fire!")
							self.zgun.fire()
							# Clear the trigger status
							self.motorsIPC.setRequiredTorque(motor, 0.0)
						self.currentMotorValues[motor] = torque
					else:
						self.zgun.arm(False)
						
				# 20/s
				time.sleep(0.03)

			if self.motorsIPC.checkWatchdog() == 0:
				print("MotorControlProcess: Paused due to watchdog expiry")
				running = False
				for servo in MotorControlProcess.managedServos:
					pass
					#servo_off(servo)
				for motor in MotorControlProcess.managedMotors:
					self.motorsIPC.setRequiredTorque(motor, 0.0)
					#motor_off(motor)
				self.zgun.arm(False)
				time.sleep(1.0)
			else:
				running = True

main = MotorControlProcess()
main.run()
			
