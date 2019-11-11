import time
import pygame
import redboard
from SensorsShared import SensorsShared
# For quadrature encoder
import smbus2
import i2cEncoderLibV2

pygame.init()

class SensorsProcess:

	def __init__(self):
		# Initialise the IPC classes
		self.sensorsIPC = SensorsShared()
		self.sensorsIPC.create()
		self.joystick = None
		
	def initialiseQuadratureCounters(self):
		# Set up quadrature interface board
		i2cBus=smbus2.SMBus(1)
		self.encoder = i2cEncoderLibV2.i2cEncoderLibV2(i2cBus,0x45)
		encconfig=(i2cEncoderLibV2.INT_DATA | i2cEncoderLibV2.WRAP_ENABLE | i2cEncoderLibV2.DIRE_RIGHT | i2cEncoderLibV2.IPUP_ENABLE | i2cEncoderLibV2.RMOD_X1 | i2cEncoderLibV2.RGB_ENCODER)
		self.encoder.begin(encconfig)
		self.encoder.writeCounter(0)
		self.encoder.writeMax(32767)
		self.encoder.writeMin(-32767)
		self.encoder.writeStep(1)
		self.encoder.writeInterruptConfig(0xff)
		self.lastQuadratureCount = 0
		
	def getQuadratureCounter(self):
		self.encoder.updateStatus()
		if self.encoder.readStatus(i2cEncoderLibV2.RINC) == True :
			#last = encoder.readCounter32()
			count = self.encoder.readCounter16()
			print ('Increment: %8d=0x%08x %8d' % (count, count&0xffffffff, count-self.lastQuadratureCount)) 
		elif self.encoder.readStatus(i2cEncoderLibV2.RDEC) == True :
			#last = encoder.readCounter32()
			count = self.encoder.readCounter16()
			print ('Decrement:  %8d=0x%08x %8d' % (count, count&0xffffffff, count-self.lastQuadratureCount))
		else:
			count = self.lastQuadratureCount
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
		self.initialiseQuadratureCounters()
		
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
			newCount = self.getQuadratureCounter()
			timestamp = time.perf_counter()
			self.sensorsIPC.setCounterValue(0, newCount, timestamp=timestamp)
			self.lastQuadratureCount = newCount
			
			pygame.time.wait(50) # mS

main = SensorsProcess()
main.run()
			
