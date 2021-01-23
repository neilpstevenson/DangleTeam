# Basic motor control process, using IPC interface
import time
import hardware.redboard as redboard
import ioexpander as pioe
from simple_pid import PID
from hardware.Motor import Motor
from interfaces.MotorControlSharedIPC import MotorControlSharedIPC
from interfaces.ServoControlSharedIPC import ServoControlSharedIPC
from interfaces.SimpleControlSharedIPC import SimpleControlSharedIPC
from interfaces.Config import Config
import atexit

# recommended for auto-disabling motors on shutdown!
atexit.register(redboard.Stop)

class MotorControlProcess:

	managedServos = (5,6,27,20,21,22) #13,
	
	def __init__(self):
		# Initialise the IPC classes
		self.motorsIPC = MotorControlSharedIPC()
		self.motorsIPC.create()
		self.currentMotorValues = [0.0]*3
		self.servosIPC = ServoControlSharedIPC()
		self.servosIPC.create()
		self.currentServoValues = [0.0]*32
		self.simpleControlsIPC = SimpleControlSharedIPC()
		self.simpleControlsIPC.create()
		self.currentSimpleValues = [0]*32
		# Config
		config = Config()
		self.pollrate = (1.0 / config.get("redboard.motor.pollrate", 100))
		self.delta_torque = self.pollrate * config.get("redboard.motor.accelmax", 4.0)
		self.readEncoders = config.get("motors.encoders.fromioexpander", True)
		self.pidSpeedControl = config.get("motors.speedmode.pidenabled", True)
		self.pidValues = config.get("motors.speedmode.pidconstants", (0.001, 0.0001, 0.001))
		
		config.save()

		# Pimoroni IO Expander config
		self.pioe_I2C_ADDR = 0x18  # 0x18 for IO Expander, 0x0F for the encoder breakout
		# Pins, left motor
		self.pioe_leftA = 13
		self.pioe_leftB = 11
		# Pins, right motor
		self.pioe_rightA = 14
		self.pioe_rightB = 12

	def run(self):
		done = False
		running = False
		motorL = Motor(2, redboard.M2, delta_torque = self.delta_torque)
		motorR = Motor(1, redboard.M1, delta_torque = self.delta_torque)
		
		if self.pidSpeedControl:
			pidL = PID(self.pidValues[0], self.pidValues[1], self.pidValues[2], sample_time=0.1)
			pidR = PID(self.pidValues[0], self.pidValues[1], self.pidValues[2], sample_time=0.1)

		if self.readEncoders:
			ioe = pioe.IOE(i2c_addr=self.pioe_I2C_ADDR)
			ioe.setup_rotary_encoder(1, self.pioe_leftA, self.pioe_leftB)
			ioe.setup_rotary_encoder(2, self.pioe_rightA, self.pioe_rightB)
			lastEncoderPositionL = ioe.read_rotary_encoder(1)
			lastEncoderPositionR = ioe.read_rotary_encoder(2)
			speedL = 0
			speedR = 0
			
		# Set names
		self.motorsIPC.setName(2, "Left Motor")
		self.motorsIPC.setName(1, "Right Motor")
		print(f"2: {self.motorsIPC.getName(2)}")
		print(f"1: {self.motorsIPC.getName(1)}")
		startTime = time.perf_counter()

		while not done:
			if running:
				# Adjust torque
				torqueL = -self.motorsIPC.getRequiredTorque(2)
				torqueR = self.motorsIPC.getRequiredTorque(1)
				if torqueL != self.currentMotorValues[2] or torqueR != self.currentMotorValues[1]:
					self.currentMotorValues[2] = torqueL
					self.currentMotorValues[1] = torqueR
					#print(f"Left: {torqueL}, Right {torqueR}")
				if self.pidSpeedControl:
					pidL.setpoint = torqueL
					pidR.setpoint = torqueR
				motorL.setTorque(torqueL)
				motorR.setTorque(torqueR)
				
				# Read the motor encoders
				if self.readEncoders:
					encoderPositionL = ioe.read_rotary_encoder(1)
					encoderPositionR = ioe.read_rotary_encoder(2)
					self.motorsIPC.setCurrentPosition(2, encoderPositionL)
					self.motorsIPC.setCurrentPosition(1, encoderPositionR)
					print(f"encoders: {encoderPositionL} {encoderPositionR}, speeds: {speedL} {speedR}")
					# Calculate speeds
					nowTime = time.perf_counter()
					deltaT = nowTime - startTime
					if deltaT > 0.1:
						speedL = (encoderPositionL - lastEncoderPositionL) // deltaT
						lastEncoderPositionL = encoderPositionL
						self.motorsIPC.setCurrentSpeed(2, speedL)
						speedR = (encoderPositionR - lastEncoderPositionR) // deltaT
						lastEncoderPositionR = encoderPositionR
						self.motorsIPC.setCurrentSpeed(1, speedR)
						startTime = nowTime
						if self.pidSpeedControl:
							errorL = pidL(speedL)
							errorR = pidR(speedR)
							print(f"pid errors: {errorL:.2f} {errorR:.2f}")

					
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
				# GPIO 20/21 as simple binary values
				for gpio in [20,21]:
					if self.simpleControlsIPC.getType(gpio) > 0:
						redboard.setPin(gpio, 1 if self.simpleControlsIPC.getValue(gpio) > 0.5 else 0)

			time.sleep(self.pollrate)

			if self.motorsIPC.checkWatchdog() == 0:
				print("MotorControlProcess: Paused due to watchdog expiry")
				running = False
				for servo in MotorControlProcess.managedServos:
					redboard.servo_off(servo)
				for i in range(int(1/self.delta_torque)+1):
					# Allow the motors to return to idle normally
					motorL.setTorque(0.0)
					motorR.setTorque(0.0)
					time.sleep(self.pollrate)
				redboard.red_off()
				redboard.green_off()
				redboard.blue_off()
				time.sleep(1.0)
			else:
				running = True

main = MotorControlProcess()
main.run()
			
