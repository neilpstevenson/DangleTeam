from interfaces.LineAnalysisSharedIPC import LineAnalysisSharedIPC
from interfaces.LineHeading import LineHeading

class VisionAccessFactory:

	def __init__(self):
		# Initialise the IPC classes
		self.lineIPC = LineAnalysisSharedIPC()
		self.lineIPC.read()

	__instance = None
	@classmethod
	def getSingleton(cls):
		if cls.__instance == None:
			cls.__instance = VisionAccessFactory()
		return cls.__instance
		
	def process(self):
		# Do common processing of state
		pass
		
	####################################################################
	# Factory methods to access the Vision results interface
	# These are the primary methods used to access the IPC values
	def getLineHeading(self):
		return LineHeading(self.lineIPC)
