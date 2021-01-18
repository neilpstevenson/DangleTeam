import numpy as np
from collections import namedtuple

class VoiceRecognitionSharedIPC:
	# Structure of the voice recognition shared memory
	word_list_dt = np.dtype([
					('word', np.dtype('U32')),
					('confidence',np.float32),		# Recognition confidence 0 - 1.0
					('timestamp',np.uint64)
					])
	voice_recognition_shared_dt = np.dtype([
					('watchdog',np.uint16),
					('currentstatus', np.uint16),	# 0=no value, 1=provisional result, 2=full result
					('currentnumberwords',np.uint16),
					('currentwords',word_list_dt, (64)),
					('laststatus', np.uint16),	# 0=no value, 1=provisional result, 2=full result
					('lastnumberwords',np.uint16),
					('lastwords',word_list_dt, (64))])
	filename = '/dev/shm/voice_recognition.mmf'

	# Interface class to set the results array
	VoiceRecognitionResult = namedtuple('VoiceRecognitionResult', 'word confidence timestamp')
	
	def create(self):
		try:
			# Try existing file first
			self.data  = np.memmap(VoiceRecognitionSharedIPC.filename, offset=0, dtype=VoiceRecognitionSharedIPC.voice_recognition_shared_dt, mode='r+', shape=(1))
		except:
			# Create/overwrite
			self.data  = np.memmap(VoiceRecognitionSharedIPC.filename, offset=0, dtype=VoiceRecognitionSharedIPC.voice_recognition_shared_dt, mode='w+', shape=(1))
	
	def read(self):
		# Read only
		try:
			# Try existing file first
			self.data  = np.memmap(VoiceRecognitionSharedIPC.filename, offset=0, dtype=VoiceRecognitionSharedIPC.voice_recognition_shared_dt, mode='r')
		except:
			# Need to create first
			self.data  = np.memmap(VoiceRecognitionSharedIPC.filename, offset=0, dtype=VoiceRecognitionSharedIPC.voice_recognition_shared_dt, mode='w+', shape=(1))
			
	def shareResults(self, status, results):
		self.data[0]['currentstatus'] = status
		for result in range(len(results)):
			res = self.data[0]['currentwords'][result]
			res['word'] = results[result].word
			res['confidence'] = results[result].confidence
			res['timestamp'] = results[result].timestamp
		self.data[0]['currentnumberwords'] = len(results)

		# Invalidate the rest
		#for result in range(len(results), len(self.data[0]['currentwords'])):
		#	self.data[0]['currentwords'][result]['status'] = 0	# Invalid
			
		# Also copy to last if we have a non-null value
		if len(results) > 0:
			self.data[0]['laststatus'] = status
			self.data[0]['lastwords'] = self.data[0]['currentwords']
			self.data[0]['lastnumberwords'] = len(results)
		else:
			self.data[0]['currentstatus'] = 0
		self.resetWatchdog()
			
	def clearCurrentResults(self):
		self.data[0]['currentnumberwords'] = 0
		self.data[0]['currentnumberwords'] = 0
		self.data[0]['currentstatus'] = 0
		#for result in range(len(self.data[0]['words'])):
		#	self.data[0]['words'][result]['status'] = status	# Set Invalid
		self.resetWatchdog()

	def getCurrentResults(self):
		results = []
		for result in range(self.data[0]['currentnumberwords']):
			res = self.data[0]['currentwords'][result]
			results.append(
				VoiceRecognitionSharedIPC.VoiceRecognitionResult(
					name = res['word'].copy(),
					confidence = res['confidence'].copy(),
					timestamp = res['timestamp'].copy()))
		return self.data[0]['currentstatus'], results
			
	def getLastResults(self):
		results = []
		for result in range(self.data[0]['lastnumberwords']):
			res = self.data[0]['lastwords'][result]
			results.append(
				VoiceRecognitionSharedIPC.VoiceRecognitionResult(
					name = res['word'].copy(),
					confidence = res['confidence'].copy(),
					timestamp = res['timestamp'].copy()))
		return self.data[0]['currentstatus'], results
			
	def getStatus(self):
		return self.data[0]['currentstatus']
	
	def getWord(self, result):
		return self.data[0]['currentwords'][result]['word']

	def getCurrentWords(self):
		results = [self.data[0]['currentwords'][w]['word'].copy() for w in range(self.data[0]['currentnumberwords'])]
		return self.data[0]['currentstatus'], results
		
	def getLastWords(self):
		results = [self.data[0]['lastwords'][w]['word'].copy() for w in range(self.data[0]['lastnumberwords'])]
		return self.data[0]['laststatus'], results

	def findLastSpokenWord(self, searchWords):
		words = self.data[0]['lastwords']
		for w in reversed(range(self.data[0]['lastnumberwords'])):
			if words[w]['word'] in searchWords:
				return words[w]['word'].copy()
		return ""
		
	def getConfidence(self, result):
		return self.data[0]['currentwords'][result]['confidence']

	def getTimestamp(self, result):
		return self.data[0]['currentwords'][result]['timestamp']
	
	def checkWatchdog(self):
		if self.data[0]['watchdog'] > 0:
			# countdown
			self.data[0]['watchdog'] -= 1
		return self.data[0]['watchdog']
		
	def resetWatchdog(self, count = 100):
		self.data[0]['watchdog'] = count

