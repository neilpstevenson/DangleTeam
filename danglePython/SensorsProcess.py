import time
import pygame
from interfaces.SensorsSharedIPC import SensorsSharedIPC
# For quadrature encoder
import smbus2
import hardware.i2cEncoderLibV2 as i2cEncoderLibV2

pygame.init()

class SensorsProcess:

	def __init__(self):
		# Initialise the IPC classes
		self.sensorsIPC = SensorsSharedIPC()
		self.sensorsIPC.create()
		self.joystick = None
		
	def initialiseQuadratureCounters(self, address):
		# Set up quadrature interface board
		i2cBus=smbus2.SMBus(1)
		encoder = i2cEncoderLibV2.i2cEncoderLibV2(i2cBus,address)
		encconfig=(i2cEncoderLibV2.INT_DATA | i2cEncoderLibV2.WRAP_ENABLE | i2cEncoderLibV2.DIRE_RIGHT | i2cEncoderLibV2.IPUP_ENABLE | i2cEncoderLibV2.RMOD_X1 | i2cEncoderLibV2.RGB_ENCODER)
		encoder.begin(encconfig)
		encoder.writeCounter(0)
		encoder.writeMax(32767)
		encoder.writeMin(-32767)
		encoder.writeStep(1)
		encoder.writeInterruptConfig(0xff)
		
	def getQuadratureCounter(self, encoder, lastQuadratureCount):
		encoder.updateStatus()
		if encoder.readStatus(i2cEncoderLibV2.RINC) == True :
			#last = encoder.readCounter32()
			count = encoder.readCounter16()
			print ('Increment: %8d=0x%08x %8d' % (count, count&0xffffffff, count-lastQuadratureCount)) 
		elif encoder.readStatus(i2cEncoderLibV2.RDEC) == True :
			#last = encoder.readCounter32()
			count = encoder.readCounter16()
			print ('Decrement:  %8d=0x%08x %8d' % (count, count&0xffffffff, count-lastQuadratureCount))
		else:
			count = lastQuadratureCount
		return count
		
	def initialiseJoystick(self):
		# Ensure we have a joystick connection
		if self.joystick is None or pygame.joystick.get_count() == 0:
			pygame.joystick.quit()
			pygame.joystick.init()
			while pygame.joystick.get_count() == 0:
				print("Please connect joystick...")
				pygame.time.wait(500) # mS
				#time.sleep(2.0)
				# Re-initialise the joystick
				pygame.joystick.quit()
				pygame.joystick.init()
			self.joystick = pygame.joystick.Joystick(0)
			self.joystick.init()
			
		
	def run(self):
		# Initialise the Joystick connection
		self.initialiseJoystick()
		# Initialise the quadrature interface board
		self.encoderL = self.initialiseQuadratureCounters(0x45)
		lastQuadratureCountL = 0
		self.encoderR = self.initialiseQuadratureCounters(0x46)
		lastQuadratureCountR = 0
		
		done = False
		while not done:
			# Check for quit
			for event in pygame.event.get(): # User did something.
				if event.type == pygame.QUIT: # If user clicked close.
					done = True # Flag that we are done so we exit this loop.

			# Get the Joystick axes
			for axis in range(6):
				axisValue = self.joystick.get_axis(axis)
				self.sensorsIPC.setAnalogValue(axis, axisValue)
			
			# Get the Joystick buttons
			for button in range(17):
				buttonValue = self.joystick.get_button(button)
				self.sensorsIPC.setDigitalValue(button, buttonValue)
			
			# Read the motor speed sensors
			newCount = self.getQuadratureCounter(self.encoderL, lastQuadratureCountL)
			timestamp = time.perf_counter()
			self.sensorsIPC.setCounterValue(0, newCount, timestamp=timestamp)
			lastQuadratureCountL = newCount
			
			newCount = self.getQuadratureCounter(self.encoderR, lastQuadratureCountR)
			timestamp = time.perf_counter()
			self.sensorsIPC.setCounterValue(1, newCount, timestamp=timestamp)
			lastQuadratureCountR = newCount
			
			pygame.time.wait(50) # mS

main = SensorsProcess()
main.run()
			
