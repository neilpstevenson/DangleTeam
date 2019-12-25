from interfaces.LineAnalysisSharedIPC import LineAnalysisSharedIPC
from interfaces.Config import Config
from analysis.VisionLineAnalysis import VisionLineAnalysis

class VisionLineProcessor:

	def __init__(self):
		# Get config
		config = Config()
		self.resolution = config.get("lava.vision.resolution", (320, 240))
		self.display = config.get("lava.vision.displayresult", True)
		self.displayGrey = config.get("lava.vision.displaygrey", False)
		self.threshold = config.get("lava.vision.threshold", 128)
		self.savefilename = config.get("lava.vision.filename", 'visionCapture.mp4')
		config.save()
		
	def run(self):
		analyser = VisionLineAnalysis(self.resolution, self.threshold, self.display, self.displayGrey, self.savefilename) 
		analyser.captureAndAssess()

processor = VisionLineProcessor()
processor.run()
