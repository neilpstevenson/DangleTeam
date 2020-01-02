import time
# interfaces
from interfaces.SensorsSharedIPC import SensorsSharedIPC
# For quadrature encoder
import smbus2
import hardware.i2cEncoderLibV2 as i2cEncoderLibV2

class SensorsProcess:

	def __init__(self):
		# Initialise the IPC classes
		self.sensorsIPC = SensorsSharedIPC()
		self.sensorsIPC.create()
		
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
		return encoder
		
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
		
	def run(self):
		# Initialise the quadrature interface board
		self.encoderL = self.initialiseQuadratureCounters(0x45)
		lastQuadratureCountL = 0
		self.encoderR = self.initialiseQuadratureCounters(0x46)
		lastQuadratureCountR = 0
		
		done = False
		while not done:
			# Read the motor speed sensors
			newCount = self.getQuadratureCounter(self.encoderL, lastQuadratureCountL)
			timestamp = time.perf_counter()
			self.sensorsIPC.setCounterValue(0, newCount, timestamp=timestamp)
			lastQuadratureCountL = newCount
			#print(f"L: {newCount}")
			
			newCount = self.getQuadratureCounter(self.encoderR, lastQuadratureCountR)
			timestamp = time.perf_counter()
			self.sensorsIPC.setCounterValue(1, -newCount, timestamp=timestamp) # Inverted
			lastQuadratureCountR = newCount
			#print(f"R: {newCount}")
			
			# Report sensors alive
			#self.sensorsIPC.resetWatchdog()
			
			time.sleep(0.02) # seconds

main = SensorsProcess()
main.run()
			
