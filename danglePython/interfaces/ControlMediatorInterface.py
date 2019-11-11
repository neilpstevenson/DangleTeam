from abc import ABC, abstractmethod

class ControlMediatorInterface:
	""" Class to get a value from a sensor and pass to a controller
	"""

	@abstractmethod
	def process(self):
		pass
