from interfaces.LineAnalysisSharedIPC import LineAnalysisSharedIPC
from interfaces.Config import Config
from analysis.VisionLineAnalysisLava import VisionLineAnalysisLava

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
		self.savefilename = config.get("lava.vision.filename", 'video-lavaVisionProc')
		self.filterRatio = config.get("lava.vision.filterRatio", 15)
		self.lookahead = config.get("lava.vision.lookahead", 0.8)
		self.saveRaw = config.get("lava.vision.saveRaw", False)
		self.saveRunNumber = config.get("lava.vision.runNumber", 1)
		config.set("lava.vision.runNumber", self.saveRunNumber + 1)
		config.save()
		
		if self.savefilename is not None:
			# Add run number and extension
			self.savefilename += str(self.saveRunNumber) + ".avi"
		
	def run(self):
		analyser = VisionLineAnalysisLava(self.resolution, self.threshold, self.display, 
						self.displayGrey, self.savefilename, self.blinkers, self.numSlices, self.framerate, self.ignoreTopSlices, self.filterRatio, self.lookahead, self.saveRaw) 
		analyser.captureAndAssess()

processor = VisionLineProcessor()
processor.run()
