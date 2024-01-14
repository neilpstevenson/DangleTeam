import numpy as np
from collections import namedtuple

class StatusSharedIPC:
	# Structure of the status shared memory
	status_dt = np.dtype([
					('title', np.dtype('U80')),
					('subtitle',np.dtype('U80')),
					('additional',np.dtype('U160'))
					])
	filename = '/dev/shm/status_info.mmf'

	def create(self):
		try:
			# Try existing file first
			self.data  = np.memmap(StatusSharedIPC.filename, offset=0, dtype=StatusSharedIPC.status_dt, mode='r+', shape=(1))
		except:
			# Create/overwrite
			self.data  = np.memmap(StatusSharedIPC.filename, offset=0, dtype=StatusSharedIPC.status_dt, mode='w+', shape=(1))
	
	def read(self):
		# Read only
		try:
			# Try existing file first
			self.data  = np.memmap(StatusSharedIPC.filename, offset=0, dtype=StatusSharedIPC.status_dt, mode='r')
		except:
			# Need to create first
			self.data  = np.memmap(StatusSharedIPC.filename, offset=0, dtype=StatusSharedIPC.status_dt, mode='w+', shape=(1))
			
	def setStatus(self, title, subtitle = "", parameters = None):
		self.data[0]['title'] = title
		self.data[0]['subtitle'] = subtitle
		self.data[0]['additional'] = "" if parameters is None else f"{parameters}"
			
	def clear(self):
		self.data[0]['title'] = ""
		self.data[0]['subtitle'] = ""
		self.data[0]['additional'] = ""

	def getTitle(self):
		return self.data[0]['title']
	def getSubtitle(self):
		return self.data[0]['subtitle']
	def getAdditional(self):
		return self.data[0]['additional']
