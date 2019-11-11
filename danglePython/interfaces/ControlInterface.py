from abc import ABC, abstractmethod

class ControlInterface:
	""" Interface that all control classes should ahhere to
	"""

	@abstractmethod
	def setValue(self, value):
		pass
