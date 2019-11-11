import numpy as np

class LineAnalysisSharedIPC:
	# Structure of the line analysis shared memory
	line_analysis_shared_dt = np.dtype([
					('timestamp',np.uint64),
					('elapsed',np.float32),
					('angle',np.float32),
					('vector',np.float32,(2,2)),
					('numberpoints',np.uint32),
					('points',np.float32,(2,32))])
	filename = '/dev/shm/vision_line_shared.mmf'
	
	def create(self):
		# Create/overwrite
		self.data  = np.memmap(LineAnalysisSharedIPC.filename, offset=0, dtype=LineAnalysisSharedIPC.line_analysis_shared_dt, mode='w+', shape=(1,1))
	
	def read(self):
		# Read only
		self.data  = np.memmap(LineAnalysisSharedIPC.filename, offset=0, dtype=LineAnalysisSharedIPC.line_analysis_shared_dt, mode='r')
		
	def shareResults(self, timestamp, elapsed, angle, vector, points):
		self.data[0]['timestamp'] = timestamp
		self.data[0]['elapsed'] = elapsed
		self.data[0]['angle'] = angle
		self.data[0]['vector'][0] = vector
		self.data[0]['numberpoints'] = len(points)
		for point in range(len(points)):
			self.data[0]['points'][0][point] = points[point]

	def getTimestamp(self):
		return self.data[0]['timestamp']
	
	def getElapsed(self):
		return self.data[0]['elapsed'] 
		
	def getAngle(self):
		return self.data[0]['angle']
		
	def getVector(self):
		return self.data[0]['vector'][0]
		
	def getPoints(self):
		numpoints = self.data[0]['numberpoints']
		return self.data[0]['points'][0][:numpoints]
	