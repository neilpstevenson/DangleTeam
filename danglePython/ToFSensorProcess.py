import time
# interfaces
from interfaces.SensorsSharedIPC import SensorsSharedIPC
# For VL53L0X ToF sensors (AdaFruit hardware mux interface)
from hardware.VL53L0X import *

class SensorsProcess:

	def __init__(self):
		# Initialise the IPC classes
		self.sensorsIPC = SensorsSharedIPC()
		self.sensorsIPC.create()
		
	def initialiseVL53L0XSensors(self, muxAddress):
		# Create a VL53L0X object for device on TCA9548A bus 1
		self.tof1 = VL53L0X(TCA9548A_Num=1, TCA9548A_Addr=muxAddress)
		# Create a VL53L0X object for device on TCA9548A bus 4
		self.tof2 = VL53L0X(TCA9548A_Num=4, TCA9548A_Addr=muxAddress)
		# Create a VL53L0X object for device on TCA9548A bus 7
		self.tof3 = VL53L0X(TCA9548A_Num=7, TCA9548A_Addr=muxAddress)

		# Start ranging on TCA9548A bus 1
		self.tof1.start_ranging(VL53L0X_GOOD_ACCURACY_MODE) #VL53L0X_HIGH_SPEED_MODE
		# Start ranging on TCA9548A bus 4
		self.tof2.start_ranging(VL53L0X_GOOD_ACCURACY_MODE)
		# Start ranging on TCA9548A bus 7
		self.tof3.start_ranging(VL53L0X_GOOD_ACCURACY_MODE)

		# Work out how fast to poll
		self.timing = self.tof1.get_timing()/1000000.00
		if (self.timing < 0.02):
			self.timing = 0.02
		print ("Poll rate: %.3fs" % self.timing)
		
	def run(self):
		# Initialise the sensors
		self.initialiseVL53L0XSensors(0x70)
		count = 0
		
		while True:
			# Left
			distance = self.tof1.get_distance()
			if (distance > 0):
				print (f"{count} Left(1): {distance}mm")
				timestamp = time.perf_counter()
				self.sensorsIPC.setAnalogValue(16, distance, timestamp=timestamp)
			else:
				self.sensorsIPC.setAnalogValue(16, -1, status = 0)
			# Front
			distance = self.tof2.get_distance()
			if (distance > 0):
				print (f"{count} Front(4): {distance}mm")
				timestamp = time.perf_counter()
				self.sensorsIPC.setAnalogValue(17, distance, timestamp=timestamp)
			else:
				self.sensorsIPC.setAnalogValue(17, -1, status = 0)
			# Right
			distance = self.tof3.get_distance()
			if (distance > 0):
				print (f"{count} Right(7): {distance}mm")
				timestamp = time.perf_counter()
				self.sensorsIPC.setAnalogValue(18, distance, timestamp=timestamp)
			else:
				self.sensorsIPC.setAnalogValue(18, -1, status = 0)

			count += 1
			time.sleep(self.timing)

main = SensorsProcess()
main.run()
			
