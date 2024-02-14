import numpy as np

class IndicatorControlSharedIPC:
	''' Shared memory structure to control indicator outputs, such as short NeoPixel rings or LEDs.
		Values provided are groups of up to 32 LED values using a common colour, e.g.
			Colour - 16-bit RGB - R=0x04, G=0x02, B=0x01
			Bits for up to 32 LEDs to illuminate, e.g. 0x0001 for first LED, 0x0002 for second etc.
		May be extended further to provide auto-colour effects 
	'''
	control_dt = np.dtype([
					('type', np.uint8), 		# 0 = not in use, 1 = simple valued, 2 = tbc
					('offColour', np.uint32),	# As packed WRGB bytes
					('onColour', np.uint32),
					('ledBits', np.uint32)])
	controls_shared_dt = np.dtype([
					('controls', control_dt, (32))])
	filename = '/dev/shm/indicator_control_shared.mmf'
	
	def create(self):
		try:
			# Try existing file first
			self.data  = np.memmap(IndicatorControlSharedIPC.filename, offset=0, dtype=IndicatorControlSharedIPC.controls_shared_dt, mode='r+', shape=(1))
		except:
			# Create/overwrite
			self.data  = np.memmap(IndicatorControlSharedIPC.filename, offset=0, dtype=IndicatorControlSharedIPC.controls_shared_dt, mode='w+', shape=(1))
	
	def open(self):
		# Read only
		try:
			# Try existing file first
			self.data  = np.memmap(IndicatorControlSharedIPC.filename, offset=0, dtype=IndicatorControlSharedIPC.controls_shared_dt, mode='r')
		except:
			# Need to create first
			self.data  = np.memmap(IndicatorControlSharedIPC.filename, offset=0, dtype=IndicatorControlSharedIPC.controls_shared_dt, mode='w+', shape=(1))

	def setIndicator(self, id, ledBits, onColour, offColour = 0, type = 1):
		self.data[0]['controls'][id]['ledBits'] = ledBits
		self.data[0]['controls'][id]['onColour'] = onColour
		self.data[0]['controls'][id]['offColour'] = offColour
		self.data[0]['controls'][id]['type'] = type
	def getIndicator(self, id):
		return (self.data[0]['controls'][id]['ledBits'].item(), self.data[0]['controls'][id]['onColour'].item(), self.data[0]['controls'][id]['offColour'].item())
	def getType(self, id):
		return self.data[0]['controls'][id]['type'].item()
		

