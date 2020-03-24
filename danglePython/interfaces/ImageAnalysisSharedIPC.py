import numpy as np
from collections import namedtuple

class ImageAnalysisSharedIPC:
	# Structure of the image analysis shared memory
	image_analysis_dt = np.dtype([
					('status', np.uint16),	# 0=no value, 1=valid value
					('typename', np.dtype('U32')),	# E.g. "Person"
					('name', np.dtype('U32')),		# E.g. "Fred bloggs"
					('confidence',np.float32),		# Match confidence 1-100%
					('distance',np.float32),# Estimated distance to nearest point of object (in mm)
					('size',np.float32,(2)),# Estimated size of bounding rectangle of object (in mm)
					('yaw',np.float32),		# Absolute yaw to centre of object at time of image capture
					('angle',np.float32)	# Relative angle to centre of object
					])
	image_analysis_shared_dt = np.dtype([
					('timestamp',np.uint64),
					('elapsed',np.float32),	# Time taken to do the analysis
					('watchdog',np.uint16),
					('numberimages',np.uint16),
					('images',image_analysis_dt, (64))])
	filename = '/dev/shm/image_analysis_shared.mmf'

	# Interface class to set the results array
	ImageResult = namedtuple('ImageResult', 'status typename name confidence distance size yaw angle')
	
	def create(self):
		try:
			# Try existing file first
			self.data  = np.memmap(ImageAnalysisSharedIPC.filename, offset=0, dtype=ImageAnalysisSharedIPC.image_analysis_shared_dt, mode='r+', shape=(1))
		except:
			# Create/overwrite
			self.data  = np.memmap(ImageAnalysisSharedIPC.filename, offset=0, dtype=ImageAnalysisSharedIPC.image_analysis_shared_dt, mode='w+', shape=(1))
	
	def read(self):
		# Read only
		try:
			# Try existing file first
			self.data  = np.memmap(ImageAnalysisSharedIPC.filename, offset=0, dtype=ImageAnalysisSharedIPC.image_analysis_shared_dt, mode='r')
		except:
			# Need to create first
			self.data  = np.memmap(ImageAnalysisSharedIPC.filename, offset=0, dtype=ImageAnalysisSharedIPC.image_analysis_shared_dt, mode='w+', shape=(1))
			
	def shareResults(self, timestamp, elapsed, results):
		self.data[0]['timestamp'] = timestamp
		self.data[0]['elapsed'] = elapsed
		self.data[0]['numberimages'] = len(results)
		for result in range(len(results)):
			res = self.data[0]['images'][result]
			res['status'] = 1	# Valid
			res['typename'] = results[result].typename
			res['name'] = results[result].name
			res['confidence'] = results[result].confidence
			res['distance'] = results[result].distance
			res['size'] = results[result].size
			res['yaw'] = results[result].yaw
			res['angle'] = results[result].angle
		# Invalidate the rest
		for result in range(len(results), len(self.data[0]['images'])):
			self.data[0]['images'][result]['status'] = 0	# Invalid
			
	def noResults(self, status = 0):
		for result in range(len(self.data[0]['images'])):
			self.data[0]['images'][result]['status'] = status	# Invalid

	def getTimestamp(self):
		return self.data[0]['timestamp']
	
	def getElapsed(self):
		return self.data[0]['elapsed'] 
		
	def getStatus(self, result):
		return self.data[0]['images'][result]['status']
	
	def getTypeName(self, result):
		return self.data[0]['images'][result]['typename']
		
	def getName(self, result):
		return self.data[0]['images'][result]['name']
		
	def getYaw(self, result):
		return self.data[0]['images'][result]['yaw']
		
	def getAngle(self, result):
		return self.data[0]['images'][result]['angle']
		
	def getDistance(self, result):
		return self.data[0]['images'][result]['distance']
		
	def getSize(self, result):
		return self.data[0]['images'][result]['size']

	def getConfidence(self, result):
		return self.data[0]['images'][result]['confidence']

	def checkWatchdog(self):
		if self.data[0]['watchdog'] > 0:
			# countdown
			self.data[0]['watchdog'] -= 1
		return self.data[0]['watchdog']
	def resetWatchdog(self, count = 100):
		self.data[0]['watchdog'] = count

