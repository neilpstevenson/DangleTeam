from interfaces.LineAnalysisSharedIPC import LineAnalysisSharedIPC
from interfaces.ImageAnalysisSharedIPC import ImageAnalysisSharedIPC
from interfaces.LineHeading import LineHeading
from interfaces.ImageResult import ImageResult

class VisionAccessFactory:

	def __init__(self):
		# Initialise the IPC classes
		self.lineIPC = LineAnalysisSharedIPC()
		self.lineIPC.read()
		self.imageIPC = ImageAnalysisSharedIPC()
		self.imageIPC.read()

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

	def getImageResult(self):
		return ImageResult(self.imageIPC)
