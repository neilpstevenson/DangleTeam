import numpy as np

class LineAnalysisSharedIPC:
	# Structure of the line analysis shared memory
	line_analysis_shared_dt = np.dtype([
					('status', np.uint16),	# 0=no value, 1=valid value
					('timestamp',np.uint64),
					('elapsed',np.float32),
					('angle',np.float32),	# Relative
					('yaw',np.float32),		# Absolute target at time of image capture
					('vector',np.float32,(2,2)),
					('numberpoints',np.uint32),
					('points',np.float32,(128,2))])
	filename = '/dev/shm/vision_line_shared.mmf'
	
	def create(self):
		try:
			# Try existing file first
			self.data  = np.memmap(LineAnalysisSharedIPC.filename, offset=0, dtype=LineAnalysisSharedIPC.line_analysis_shared_dt, mode='r+', shape=(1,1))
		except:
			# Create/overwrite
			self.data  = np.memmap(LineAnalysisSharedIPC.filename, offset=0, dtype=LineAnalysisSharedIPC.line_analysis_shared_dt, mode='w+', shape=(1,1))
	
	def read(self):
		# Read only
		try:
			# Try existing file first
			self.data  = np.memmap(LineAnalysisSharedIPC.filename, offset=0, dtype=LineAnalysisSharedIPC.line_analysis_shared_dt, mode='r')
		except:
			# Need to create first
			self.data  = np.memmap(LineAnalysisSharedIPC.filename, offset=0, dtype=LineAnalysisSharedIPC.line_analysis_shared_dt, mode='w+', shape=(1,1))
			
	def shareResults(self, timestamp, elapsed, angle, yaw, vector, points, status = 1):
		self.data[0]['status'] = status
		self.data[0]['timestamp'] = timestamp
		self.data[0]['elapsed'] = elapsed
		self.data[0]['angle'] = angle
		self.data[0]['yaw'] = yaw
		self.data[0]['vector'][0] = vector
		self.data[0]['numberpoints'] = len(points)
		for point in range(len(points)):
			self.data[0]['points'][0][point] = points[point]
			
	def noResults(self, status = 0):
		self.data[0]['status'] = status

	def getStatus(self):
		return self.data[0]['status']
	
	def getTimestamp(self):
		return self.data[0]['timestamp']
	
	def getElapsed(self):
		return self.data[0]['elapsed'] 
		
	def getAngle(self):
		return self.data[0]['angle']
		
	def getYaw(self):
		return self.data[0]['yaw']
		
	def getVector(self):
		return self.data[0]['vector'][0]
		
	def getPoints(self):
		numpoints = self.data[0]['numberpoints']
		return self.data[0]['points'][:numpoints]
	
