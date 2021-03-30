# USAGE
# python3 FrindRedLight.py [--video recording.mp4]

# import the necessary packages
from collections import deque
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time
# Interfaces
from interfaces.ImageAnalysisSharedIPC import ImageAnalysisSharedIPC
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.Config import Config
# Analysis classes
from analysis.ElapsedTime import elapsedTime
from analysis.ImageColouredRegionAnalyser import ImageColouredRegionAnalyser

class TidyUpTheToysImageCaptureAndAnalysis:
	
	def __init__(self):
		# construct the argument parse and parse the arguments
		ap = argparse.ArgumentParser()
		ap.add_argument("-v", "--video",
			help="path to the (optional) video file")
		args = vars(ap.parse_args())
		self.recordedVideo = args.get("video", False)
		if self.recordedVideo:
			self.videoFilenanme = args["video"]

		# Get config
		config = Config()
		self.debugPrint = config.get("tidy.analysis.debugPrint", True)
		self.analysis_width = config.get("tidy.analysis.imagewidth", 480)
		self.blur_radius = config.get("tidy.analysis.burrradius", 11)
		#self.minSize = config.get("tidy.analysis.minsize", 10)
		self.minWidth = config.get("tidy.analysis.minWidth", 15)
		self.minHeight  = config.get("tidy.analysis.minHeight", 10)
		# Scale factors for real-world measures
		self.angleAdjustment = config.get("tidy.analysis.anglescale", 2.6)#1.3#0.55
		self.showImage = config.get("tidy.display.image", True)
		self.showMasks = config.get("tidy.display.masks", False)
		#self.trailSize = config.get("tidy.display.trail", 25)
		self.frameDelayMs = config.get("tidy.analysis.frameDelayMs", 20) # delay after each frame analysis
		self.filename = config.get("tidy.analysis.savefilename", "tidyupthetoys.mp4")
		self.saveFile = config.get("tidy.analysis.save", True)
		config.save()
		
		# Load calibration values
		configCal = Config("calibrationTidy.json")
		#if useCalibrationColours:
		#	self.colourTargetLower = tuple(configCal.get("tidy.analysis.colourTargetLower", None))
		#	self.colourTargetUpper = tuple(configCal.get("tidy.analysis.colourTargetUpper", None))
		self.cameraNearestVisibleDistance = configCal.get("distance.analysis.nearest", 130)
		self.cameraNearestVisiblePixels = int(self.cameraNearestVisibleDistance * 3.5) # Rough approximation equivallent!!
		self.cameraFurthestVisiblePixel = configCal.get("distance.analysis.horizon", 500)
		self.cameraHeightDistance = configCal.get("distance.analysis.cameraHeight", 170)
		calibrationResolution = configCal.get("distance.analysis.calibrationResolution", [480,640])
		# Adjust for the analysis picture resolution being different to the calibrator
		self.cameraFurthestVisiblePixel = self.cameraFurthestVisiblePixel * self.analysis_width // calibrationResolution[1]

		# Results IPC
		self.resultsIpc = ImageAnalysisSharedIPC()
		self.resultsIpc.create()
		
		# Yaw reading accessor
		self.sensors = SensorAccessFactory.getSingleton()
		self.yawAccessor = self.sensors.yaw()
		
		# Accessors for current wheel positions
		self.controls = ControlAccessFactory.getSingleton()
		self.positionL = self.controls.motorPosition(2)
		self.positionR = self.controls.motorPosition(1)
		
	#
	# Print a checkpoint time for an analysis stage
	#
	def timedCheckpoint(self, text):
		if self.debugPrint:
			print(f"{text} at: {self.overall():.3f}")
		
	#
	# Generate the filtered/masked frames that we are to analyse
	#
	def preprocessImage(self, frame):
		#blurred = cv2.GaussianBlur(frame, (self.blur_radius, self.blur_radius), 0)
		blurred = cv2.blur(frame, (self.blur_radius, self.blur_radius))

		hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)	
		
		#self.imageAnalysisRed = ImageColouredRegionAnalyser( "Red", ((0,141,148), (180,198,255)), 5, 5, None, \
		self.imageAnalysisRed = ImageColouredRegionAnalyser( "Red", [((155,94,69), (180,255,255)), ((0,94,69), (6,255,255))], 5, 5, None, \
			(self.minWidth, self.minHeight), \
			(self.cameraNearestVisiblePixels, self.cameraFurthestVisiblePixel, self.cameraNearestVisibleDistance, self.cameraHeightDistance, self.angleAdjustment))
		self.imageAnalysisRed.processImage(hsv)

		self.imageAnalysisGreen = ImageColouredRegionAnalyser( "Green", ((40,63,27), (84,255,255)), 5, 5, None, \
			(self.minWidth, self.minHeight), \
			(self.cameraNearestVisiblePixels, self.cameraFurthestVisiblePixel, self.cameraNearestVisibleDistance, self.cameraHeightDistance, self.angleAdjustment))
		self.imageAnalysisGreen.processImage(hsv)

		self.imageAnalysisBlue = ImageColouredRegionAnalyser( "Blue", ((96,101,60), (130,255,255)), 5, 5, None, \
			(self.minWidth, self.minHeight), \
			(self.cameraNearestVisiblePixels, self.cameraFurthestVisiblePixel, self.cameraNearestVisibleDistance, self.cameraHeightDistance, self.angleAdjustment))
		self.imageAnalysisBlue.processImage(hsv)

		self.imageAnalysisYellow = ImageColouredRegionAnalyser( "Yellow", ((3,100,86), (21,205,255)), 5, 5, None, \
			(self.minWidth, self.minHeight), \
			(self.cameraNearestVisiblePixels, self.cameraFurthestVisiblePixel, self.cameraNearestVisibleDistance, self.cameraHeightDistance, self.angleAdjustment))
		self.imageAnalysisYellow.processImage(hsv)
	
		self.timedCheckpoint("coloured masks created")


	#
	# Display an annotated image of the results
	#		
	def displayResults(self, frame):
		for analysis in [self.imageAnalysisRed, self.imageAnalysisGreen, self.imageAnalysisBlue, self.imageAnalysisYellow]:
			if analysis.hasResult:
				# Show the contours
				#print(f"displayResults: {analysis.largestContours}")
				cv2.polylines(frame, analysis.largestContours,  True, (128, 128, 128), 2, 8)		
				cv2.putText(frame, analysis.name, (analysis.largestCenter[0]-20,analysis.largestCenter[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
				distance, angle = analysis.calculateDistanceBearing()
				cv2.putText(frame, f"{distance:.0f}mm {angle:.1f}deg", (analysis.largestCenter[0]-65,analysis.largestCenter[1] - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
			if self.showMasks:
				cv2.imshow(analysis.name, analysis.maskedImage)
		
		if self.fps != None:
			cv2.putText(frame, f"{self.fps}fps", (frame.shape[1]-60, frame.shape[0]-20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

		cv2.imshow("Overview", frame)

		if self.saveFile:
			# Write the next frame into the file
			self.captureFile.write(frame)
		
		# Print up the results found
		print(f"Total time taken {self.elapsed}")
		#print(f"Result count {len(self.results)}")
		#for result in self.results:
		#	print(f"{result.typename}.{result.name}")
		#	print(f"  d={result.distance:.0f}mm, size={result.size}, yaw={result.yaw:.1f}, angle={result.angle:.1f}")

	#
	# Share the results for robot code consumption
	#
	def publishResults(self):
		for analysis in [self.imageAnalysisRed, self.imageAnalysisGreen, self.imageAnalysisBlue, self.imageAnalysisYellow]:
			if analysis.hasResult:
				distance, angle = analysis.calculateDistanceBearing()
				yawHeading = self.yaw + angle 
				if yawHeading > 180.0:
					yawHeading -= 360.0
				elif yawHeading < -180.0:
					yawHeading += 360.0
				# Add result to end list
				result = ImageAnalysisSharedIPC.ImageResult(
					 status = 1,
					 typename = 'Block',
					 name = analysis.name,
					 confidence = 90.0,
					 distance = distance,
					 size = [0,0],
					 yaw = yawHeading,
					 angle = angle,
					 motorpositions = self.currentMotorPositions )
				self.results.append(result)
				print(f"{result.typename}.{result.name}")
				print(f"  d={result.distance:.0f}mm, size={result.size}, yaw={result.yaw:.1f}, angle={result.angle:.1f}")

		self.resultsIpc.shareResults(self.startTime, self.elapsed, self.results )
		
	#
	# Debug stuff	
	#	
	def printDebugStats(self, count):
		if count % 10 == 0:
			fpsEnd = cv2.getTickCount() / cv2.getTickFrequency()
			self.fps = int(10 / (fpsEnd - self.fpsStart))
			self.fpsStart = fpsEnd
		if self.debugPrint and self.fps != None:
			print(f"{self.fps}fps")
	
	#
	# High-level method to continually capture, analyse and share the results
	#						
	def captureContinuous(self):
		# if a video path was not supplied, grab the reference
		# to the webcam
		frameRate = 25#30
		resolution = (640,480)
		if not self.recordedVideo:
			#vs = VideoStream(src=0)
			#vs.stream.stream.set( cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 7.5)
			#vs.stream.stream.set( cv2.CAP_PROP_WHITE_BALANCE_RED_V, 7.5)
			##vs.stream.stream.set( cv2.CAP_PROP_AUTO_WB, 0)
			#vs.start()
			vs = cv2.VideoCapture(0)
			vs.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
			vs.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
			vs.set(cv2.CAP_PROP_FPS, frameRate)
			vs.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 7.5)
			vs.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V, 7.5)
			vs.set(cv2.CAP_PROP_BUFFERSIZE, 1)	# Only interested in live data

		# otherwise, grab a reference to the video file
		else:
			vs = cv2.VideoCapture(self.videoFilenanme)

		# stats
		self.fpsStart = cv2.getTickCount() / cv2.getTickFrequency()
		self.fps = None
		
		# results
		self.angle = None
		self.ourPosition = None
		count = 0

		if self.saveFile:
			print(f"Saving to file: {self.filename}")
			# Define the codec and create VideoWriter object.
			self.captureFile = cv2.VideoWriter(self.filename, cv2.VideoWriter_fourcc(*'mp4v'), frameRate, (self.analysis_width, self.analysis_width*resolution[1]//resolution[0]))

		# keep looping
		while True:
			self.results = []
			
			with elapsedTime("Overall", printAtEnd = self.debugPrint) as self.overall:
				self.startTime = cv2.getTickCount()
				
				# grab the current frame
				ret, frame = vs.read()

				# handle the frame from VideoCapture or VideoStream
				frame = frame[1] if self.recordedVideo else frame

				# if we are viewing a video and we did not grab a frame,
				# then we have reached the end of the video
				if frame is None:
					break

				# Get the current yaw value
				self.sensors.process()
				self.yaw = self.yawAccessor.getValue()
				
				# Get the current motor positions
				self.currentMotorPositions = [self.positionL.getValue(), self.positionR.getValue()]
				
				# resize the frame
				frame = imutils.resize(frame, width=self.analysis_width, inter=cv2.INTER_NEAREST)
		
				# Do all necessary pre-processing, e.g. filtering and threholding
				self.preprocessImage(frame)
				
				# Analyse the frame for artifacts of interest
				#self.analyseImage(frame)
						
				endTime = cv2.getTickCount()
				self.elapsed = (endTime - self.startTime) / cv2.getTickFrequency()
				
				# Share the results
				self.publishResults()

				# Display the results		
				if self.showImage:
					self.displayResults(frame)
					
				# Stats
				self.printDebugStats(count)
				count += 1

				self.lastYaw = self.yaw
				
				# Display anything ready and delay a little
				key = cv2.waitKey(self.frameDelayMs) & 0xFF

				# if the 'q' key is pressed, stop the loop
				if key == ord("q"):
					break

		# if we are not using a video file, stop the camera video stream
		if not self.recordedVideo:
			pass
			#vs.stop() # for imutils version
		else:
			# otherwise, close the file
			vs.release()

		# close all windows
		cv2.destroyAllWindows()

if __name__ == "__main__":
	capture = FindRedLight()
	capture.captureContinuous()
