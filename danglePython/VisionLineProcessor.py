from interfaces.LineAnalysisSharedIPC import LineAnalysisSharedIPC
from interfaces.Config import Config
from analysis.VisionLineAnalysis import VisionLineAnalysis

class VisionLineProcessor:

	def __init__(self):
		# Get config
		config = Config()
		self.resolution = config.get("lava.vision.resolution", (320, 240))
		self.framerate = config.get("lava.vision.framerate", 30)
		self.numSlices = config.get("lava.vision.slices", 40)
		self.ignoreTopSlices = config.get("lava.vision.ignoreTopSlices", 10)
		self.display = config.get("lava.vision.displayresult", True)
		self.displayGrey = config.get("lava.vision.displaygrey", False)
		self.threshold = config.get("lava.vision.threshold", 128)
		self.blinkers = config.get("lava.vision.blinkers", 30) # pixels at either side of top
		self.savefilename = config.get("lava.vision.filename", 'visionCapture.avi')
		self.filterRatio = config.get("lava.vision.filterRatio", 15)
		self.lookahead = config.get("lava.vision.lookahead", 0.8)
		self.saveRaw = config.get("lava.vision.saveRaw", False)
		config.save()
		
	def run(self):
		analyser = VisionLineAnalysis(self.resolution, self.threshold, self.display, 
						self.displayGrey, self.savefilename, self.blinkers, self.numSlices, self.framerate, self.ignoreTopSlices, self.filterRatio, self.lookahead, self.saveRaw) 
		analyser.captureAndAssess()

processor = VisionLineProcessor()
processor.run()
