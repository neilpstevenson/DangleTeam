import numpy as np
from LineAnalysisSharedIPC import LineAnalysisSharedIPC

class LineAnalysisResult:
	def __init__(self):
		self.results = LineAnalysisSharedIPC()
		self.results.read()
		
	def getValue(self):
		# Get the latest angle
		return self.results.getAngle()
