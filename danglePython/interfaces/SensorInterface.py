from abc import ABC, abstractmethod

class SensorInterface:
	""" Interface that all sensors classes should ahhere to
	"""

	@abstractmethod
	def getValue(self):
		pass
