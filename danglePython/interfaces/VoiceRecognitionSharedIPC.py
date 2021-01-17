import numpy as np
from collections import namedtuple

class VoiceRecognitionSharedIPC:
	# Structure of the voice recognition shared memory
	word_list_dt = np.dtype([
					('status', np.uint16),	# 0=no value, 1=provisional result, 2=full result
					('word', np.dtype('U32')),
					('confidence',np.float32),		# Recognition confidence 0 - 1.0
					('timestamp',np.uint64)
					])
	voice_recognition_shared_dt = np.dtype([
					('watchdog',np.uint16),
					('numberwords',np.uint16),
					('words',word_list_dt, (64))])
	filename = '/dev/shm/voice_recognition.mmf'

	# Interface class to set the results array
	VoiceRecognitionResult = namedtuple('VoiceRecognitionResult', 'status word confidence timestamp')
	
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
			
	def shareResults(self, results):
		self.data[0]['numberwords'] = len(results)
		for result in range(len(results)):
			res = self.data[0]['words'][result]
			res['status'] = results[result].status
			res['word'] = results[result].word
			res['confidence'] = results[result].confidence
			res['timestamp'] = results[result].timestamp

		# Invalidate the rest
		for result in range(len(results), len(self.data[0]['words'])):
			self.data[0]['words'][result]['status'] = 0	# Invalid
			
	def noResults(self, status = 0):
		for result in range(len(self.data[0]['words'])):
			self.data[0]['words'][result]['status'] = status	# Set Invalid

	def getVoiceRecognitionResults(self):
		results = []
		for result in range(self.data[0]['numberwords']):
			res = self.data[0]['words'][result]
			results.append(
				VoiceRecognitionSharedIPC.VoiceRecognitionResult(
					status = res['status'].copy(),
					name = res['word'].copy(),
					confidence = res['confidence'].copy(),
					distance = res['timestamp'].copy()))
		return results
			
	def getStatus(self, result):
		return self.data[0]['words'][result]['status']
	
	def getWord(self, result):
		return self.data[0]['words'][result]['word']

	def getWords(self):
		results = []
		for result in range(self.data[0]['numberwords']):
			res = self.data[0]['words'][result]
			results.append(res['word'].copy())
		return self.getStatus(0), results
		
	def getConfidence(self, result):
		return self.data[0]['words'][result]['confidence']

	def getTimestamp(self, result):
		return self.data[0]['words'][result]['timestamp']
	
	def checkWatchdog(self):
		if self.data[0]['watchdog'] > 0:
			# countdown
			self.data[0]['watchdog'] -= 1
		return self.data[0]['watchdog']
	def resetWatchdog(self, count = 100):
		self.data[0]['watchdog'] = count

