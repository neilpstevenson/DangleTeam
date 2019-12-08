from abc import ABC, abstractmethod

class ChallengeInterface:
	""" Interface that all challenge classes should adhere to
	"""

	@abstractmethod
	def createProcesses(self):
		pass

	def start(self):
		''' Start the challenge
		'''
		pass
		
	def move(self):
		''' Calculate the next move in the challenge
		'''
		pass

	def pause(self):
		''' Pause the challenge
		'''
		pass

	def resume(self):
		''' Resume  the challenge
		'''
		pass
		
	def stop(self):
		''' Stop the challenge
		'''
		pass
