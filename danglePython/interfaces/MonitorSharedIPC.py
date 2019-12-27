import numpy as np

class MonitorSharedIPC:
	# Structure of the line analysis shared memory
	monitor_dt = np.dtype([
					('status', np.uint16),	# 0=no value, 1=valid value
					('timestamp', np.float64 ),
					('value', np.float32)])
	monitor_shared_dt = np.dtype([
					('values', monitor_dt, (64))])
	filename = '/dev/shm/monitor_shared.mmf'
	
	def create(self):
		try:
			# Try using existing file first
			self.data  = np.memmap(MonitorSharedIPC.filename, offset=0, dtype=MonitorSharedIPC.monitor_shared_dt, mode='r+', shape=(1,1))
		except:
			# Create/overwrite
			self.data  = np.memmap(MonitorSharedIPC.filename, offset=0, dtype=MonitorSharedIPC.monitor_shared_dt, mode='w+', shape=(1,1))
	
	def read(self):
		# Read only
		self.data  = np.memmap(MonitorSharedIPC.filename, offset=0, dtype=MonitorSharedIPC.monitor_shared_dt, mode='r')
		
	def getValue(self, id):
		return self.data[0]['values'][id]['value']
	
	def setValue(self, id, value, status=1, timestamp = 0):
		self.data[0]['analog'][id]['status'] = status
		self.data[0]['analog'][id]['timestamp'] = timestamp
		self.data[0]['values'][id]['value'] = value
