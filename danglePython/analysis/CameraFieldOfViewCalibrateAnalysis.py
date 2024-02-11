# USAGE
# python3 FrindRedLight.py [--video recording.mp4]

# import the necessary packages
from collections import deque
from imutils.video import VideoStream
from picamera2 import Picamera2
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
#from analysis.ImageColouredRegionAnalyser import ImageColouredRegionAnalyser
from analysis.ImageArucoRecogniser import ImageArucoRecogniser

class CameraFieldOfViewCalibrateAnalysis:
	
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
		self.debugPrint = config.get("fish.analysis.debugPrint", True)
		# Scale factors for real-world measures
		self.angleAdjustment = config.get("fish.analysis.anglescale", 2.1)
		self.showImage = config.get("fish.display.image", True)
		self.frameDelayMs = config.get("fish.analysis.frameDelayMs", 1) # delay after each frame analysis
		self.filename = config.get("fish.analysis.savefilename", "feedthefish.mp4")
		self.saveFile = config.get("fish.analysis.save", True)
		self.frameRate = config.get("fish.camera.framerate", 25)
		self.resolution = config.get("fish.camera.resolution", (640,480))
		self.arucoDictName = config.get("fish.camera.arucodictname", cv2.aruco.DICT_4X4_50)
		self.arucoSize = config.get("fish.camera.arucosize", 100) # mm

		config.save()
		
		# Load calibration values
		configCal = Config("calibrationFish.json")
		self.cameraNearestVisibleDistance = configCal.get("distance.analysis.nearest", 130)
		self.cameraNearestVisiblePixels = int(self.cameraNearestVisibleDistance * 3.5) # Rough approximation equivallent!!
		self.cameraFurthestVisiblePixel = configCal.get("distance.analysis.horizon", 500)
		self.cameraHeightDistance = configCal.get("distance.analysis.cameraHeight", 170)
		self.focalLength = configCal.get("camera.focallength", 520)
		calibrationResolution = configCal.get("distance.analysis.calibrationResolution", [480,640])
		# Adjust for the analysis picture resolution being different to the calibrator
		self.cameraFurthestVisiblePixel = self.cameraFurthestVisiblePixel * self.resolution[0] // calibrationResolution[1]

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
		self.imageAnalysisFishTankAruco = ImageArucoRecogniser("ArUco", \
			(self.cameraNearestVisiblePixels, self.cameraFurthestVisiblePixel, self.cameraNearestVisibleDistance, self.cameraHeightDistance, self.angleAdjustment), \
			self.focalLength, self.arucoSize, self.arucoDictName)
		self.imageAnalysisFishTankAruco.processImage(frame)

		self.timedCheckpoint("aruco image analysed")

	#
	# Display an annotated image of the results
	#		
	def displayResults(self, frame):
		for analysis in [self.imageAnalysisFishTankAruco]:
			if analysis.hasResult:
				for id in analysis.getIds():
					# Get the results
					corners, distance, angle = analysis.calculateDistanceBearing(id)
					# Show the contours
					corners = corners.reshape((-1,1,2))
					#print(f"displayResults: {corners}")
					cv2.polylines(frame, [corners],  True, (0, 255, 0), 2, 8)		
					cv2.putText(frame, f"{id} : {analysis.name}", (corners[0][0][0], corners[0][0][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
					cv2.putText(frame, f"{distance:.0f}mm {angle:.1f}deg", (analysis.largestCenter[0]-65,analysis.largestCenter[1] - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
		
		if self.fps != None:
			cv2.putText(frame, f"{self.fps}fps", (frame.shape[1]-60, frame.shape[0]-20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

		cv2.imshow("Feed the Fish - ArUco markers", frame)

		if self.saveFile:
			# Write the next frame into the file
			self.captureFile.write(frame)
		
		# Print up the results found
		if self.debugPrint:
			print(f"Total time taken {self.elapsed}")
		#print(f"Result count {len(self.results)}")
		#for result in self.results:
		#	print(f"{result.typename}.{result.name}")
		#	print(f"  d={result.distance:.0f}mm, size={result.size}, yaw={result.yaw:.1f}, angle={result.angle:.1f}")

	#
	# Share the results for robot code consumption
	#
	def publishResults(self):
		for analysis in [self.imageAnalysisFishTankAruco]:
			if analysis.hasResult:
				for id in analysis.getIds():
					# Get the results
					corners, distance, angle = analysis.calculateDistanceBearing(id)
					yawHeading = self.yaw + angle 
					if yawHeading > 180.0:
						yawHeading -= 360.0
					elif yawHeading < -180.0:
						yawHeading += 360.0
					# Add result to end list
					result = ImageAnalysisSharedIPC.ImageResult(
						 status = 1,
						 typename = analysis.name,
						 name = id,
						 confidence = 90.0,
						 distance = distance,
						 size = [0,0],
						 yaw = yawHeading,
						 angle = angle,
						 motorpositions = self.currentMotorPositions )
					self.results.append(result)
					if self.debugPrint:
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
		if not self.recordedVideo:
			picam2 = Picamera2()
			picam2.configure( picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (self.resolution[0], self.resolution[1])}))
			picam2.start()
			#vs = cv2.VideoCapture(0)
			#vs.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
			#vs.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
			#vs.set(cv2.CAP_PROP_FPS, self.frameRate)
			#vs.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 7.5)
			#vs.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V, 7.5)
			#vs.set(cv2.CAP_PROP_BUFFERSIZE, 1)	# Only interested in live data

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
			self.captureFile = cv2.VideoWriter(self.filename, cv2.VideoWriter_fourcc(*'mp4v'), self.frameRate, (self.resolution[0], self.resolution[1]))
		
		# keep looping
		while True:
			self.results = []
			
			with elapsedTime("Overall", printAtEnd = self.debugPrint) as self.overall:
				self.startTime = cv2.getTickCount()
				
				# grab the current frame
				if self.recordedVideo:
					ret, frame = vs.read()
					frame = frame[1]
				else:
					original = picam2.capture_array()
					frame = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

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
				#frame = imutils.resize(frame, width=self.analysis_width, inter=cv2.INTER_NEAREST)
		
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

