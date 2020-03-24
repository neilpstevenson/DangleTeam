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
from interfaces.Config import Config
# Analysis classes
from analysis.ElapsedTime import elapsedTime

class FindRedLight:
	
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
		self.debugPrint = config.get("minesweeper.analysis.debugPrint", False)
		self.analysis_width = config.get("minesweeper.analysis.imagewidth", 480)
		self.blur_radius = config.get("minesweeper.analysis.burrradius", 11)
		#self.minSize = config.get("minesweeper.analysis.minsize", 10)
		self.minWidth = config.get("minesweeper.analysis.minWidth", 15)
		self.minHeight  = config.get("minesweeper.analysis.minHeight", 10)
		# Scale factors for real-world measures
		self.angleAdjustment = config.get("minesweeper.analysis.anglescale", 2.6)#1.3#0.55
		
		# define the lower and upper boundaries of the target 
		# colour in the HSV color space, then initialize the
		useCalibrationColours = config.get("minesweeper.analysis.useCalibrationColours", True)
		if not useCalibrationColours:
			useLEDColours = config.get("minesweeper.analysis.useLEDColours", False)
			if useLEDColours:
				# For LED:
				self.colourTargetLower = tuple(config.get("minesweeper.analysis.colourTargetLowerLED", [155,24,200]))#(165,90,100)#(158,60,90) #(160,128,24)
				self.colourTargetUpper = tuple(config.get("minesweeper.analysis.colourTargetUpperLED", [175,255,255]))#(175,255,255) #(180,255,255)
			else:
				# For test biscuit tin lid
				self.colourTargetLower = tuple(config.get("minesweeper.analysis.colourTargetLowerTest", [165,94,69]))
				self.colourTargetUpper = tuple(config.get("minesweeper.analysis.colourTargetUpperTest", [180,255,255]))
		
		self.showImage = config.get("minesweeper.display.image", True)
		self.trailSize = config.get("minesweeper.display.trail", 25)
		self.frameDelayMs = config.get("minesweeper.analysis.frameDelayMs", 20) # delay after each frame analysis
		config.save()
		
		# Load calibration values
		configCal = Config("calibrationMinesweeper.json")
		if useCalibrationColours:
			self.colourTargetLower = tuple(configCal.get("minesweeper.analysis.colourTargetLower", None))
			self.colourTargetUpper = tuple(configCal.get("minesweeper.analysis.colourTargetUpper", None))
		self.cameraNearestVisibleDistance = configCal.get("distance.analysis.nearest", 130)
		self.cameraNearestVisiblePixels = int(self.cameraNearestVisibleDistance * 3.5) # Rough approximation equivallent!!
		self.cameraFurthestVisiblePixel = configCal.get("distance.analysis.horizon", 500)
		self.cameraHeightDistance = configCal.get("distance.analysis.cameraHeight", 170)
		calibrationResolution = configCal.get("distance.analysis.calibrationResolution", [480,640])
		self.cameraHeightAdjustment = np.sqrt(self.cameraHeightDistance*self.cameraHeightDistance + self.cameraNearestVisibleDistance*self.cameraNearestVisibleDistance) / self.cameraNearestVisibleDistance
		# Adjust for the analysis picture resolution being different to the calibrator
		self.cameraFurthestVisiblePixel = self.cameraFurthestVisiblePixel * self.analysis_width // calibrationResolution[1]

		# Results IPC
		self.results = ImageAnalysisSharedIPC()
		self.results.create()
		
		# Yaw reading accessor
		self.sensors = SensorAccessFactory.getSingleton()
		self.yawAccessor = self.sensors.yaw()
		
		# list of tracked points
		self.trail = deque(maxlen=self.trailSize)

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
		# Blur the frame to get rid of some noise, and convert it to the HSV
		# color space
		blurred = cv2.blur(frame, (self.blur_radius, self.blur_radius))
		hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
		self.timedCheckpoint("blur")

		# construct a mask for the color range required, then perform
		# a series of dilations and erosions to remove any small
		# blobs left in the mask
		self.maskedFrame = cv2.inRange(hsv, self.colourTargetLower, self.colourTargetUpper)
		self.maskedFrame = cv2.erode(self.maskedFrame, None, iterations=2)
		self.maskedFrame = cv2.dilate(self.maskedFrame, None, iterations=2)
		self.timedCheckpoint("mask created")

	#
	# Analyse the filtered/masked frames to produce the required results
	#
	def analyseImage(self):
		# find contours in the mask and initialize the current
		# (x, y) center of the ball
		cnts = cv2.findContours(self.maskedFrame, cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		self.center = None

		# only proceed if at least one contour was found
		self.hasResult = False
		if len(cnts) > 0:
			# find the largest contour in the mask, 
			c = max(cnts, key=cv2.contourArea)
			# find the best minimum enclosing circle and centroid
			#((x, y), radius) = cv2.minEnclosingCircle(c)
			# find the best enclosing rectangle
			x, y, w, h = cv2.boundingRect(c)
			M = cv2.moments(c)
			self.center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
			self.displayContours = cnts # to display only - for all, use: [c]
				
			# only proceed if the radius meets a minimum size
			if w >= self.minWidth and h >= self.minHeight:
				self.hasResult = True
				
				# Calculate the angle from the bottom centre to the centre
				self.ourPosition = (self.maskedFrame.shape[1]//2, self.maskedFrame.shape[0] + self.cameraNearestVisiblePixels)
				self.angle = np.arctan((self.ourPosition[0]-self.center[0])/(self.ourPosition[1]-self.center[1])) * 180.0/3.14159 * self.angleAdjustment
				
				# Distance approximation
				dist_recip = self.cameraFurthestVisiblePixel - (self.maskedFrame.shape[0] - self.center[1])
				if dist_recip > 0:
					self.distance = ((((self.cameraFurthestVisiblePixel-1) / dist_recip) - 1) * self.cameraHeightAdjustment + 1) * self.cameraNearestVisibleDistance
				else:
					dself.istance = 999
					
		# Debug output	
		if self.debugPrint:
			#	print(f"mid point HSV: {hsv[self.center[1], self.center[0]]}")
			#	print(f"20 above mid point HSV: {hsv[self.center[1]-20, self.center[0]]}")
			if len(cnts) > 0:
				print(f"best area width: {w}, height: {h}, center: {self.center}")
			if self.hasResult:
				print(f"distance: {self.distance}mm, angle: {self.angle}, center: {self.center}")
			else:
				print(f"no result")

	#
	# Display an annotated image of the results
	#		
	def displayResults(self, frame):
		# Draw an angle from where we are to target
		if self.hasResult:
			cv2.arrowedLine(frame, self.ourPosition, self.center, (0, 255, 0), 3)
		# Display the results as text overlay
		if self.ourPosition != None:
			# Overlay the angle calculated
			np.set_printoptions(precision=2)
			cv2.putText(frame, f"Head {self.angle:+.1f}deg for {self.distance:.0f}mm", (5, frame.shape[0]-20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
		if self.fps != None:
			cv2.putText(frame, f"{self.fps}fps", (frame.shape[1]-60, frame.shape[0]-20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
		# Show a trail of recent points
		if self.hasResult:
			self.trail.appendleft(self.center)
		elif len(self.trail) > 0:
			self.trail.pop()
		for i in range(1, len(self.trail)):
			# if either of the tracked points are None, ignore
			# them
			if self.trail[i - 1] is None or self.trail[i] is None:
				continue
			# Recent lines thicker than older lines
			thickness = int(np.sqrt(self.trailSize / float(i + 1)) * 2.0)
			cv2.line(frame, self.trail[i - 1], self.trail[i], (0, 0, 255), thickness)
			
		if self.hasResult:
			# Show contours found
			cv2.polylines(frame, self.displayContours,  True, (0, 255, 0), 2, 8)
			
		# show the frame to our screen
		cv2.imshow("Frame", frame)

	#
	# Share the results for robot code consumption
	#
	def publishResults(self):
		if self.hasResult:	
			# self.overall capture/analysis time
			endTime = cv2.getTickCount()
			timestamp = (endTime - self.startTime) / cv2.getTickFrequency()
			
			yawHeading = self.yaw + self.angle 
			if yawHeading > 180.0:
				yawHeading -= 360.0
			elif yawHeading < -180.0:
				yawHeading += 360.0
			result0 = ImageAnalysisSharedIPC.ImageResult(
			 status = 1,
			 typename = 'Area',
			 name = 'Red',
			 confidence = 90.0,
			 distance = self.distance,
			 size = [0,0],
			 yaw = yawHeading,
			 angle = self.angle )
			self.results.shareResults(self.startTime, timestamp, [result0] )
		elif self.angle != None:
			# Ajust angle based on last successful analysis for display only
			self.angle += (self.lastYaw - self.yaw)
			if self.angle > 180.0:
				self.angle -= 360.0
			elif self.angle < -180.0:
				self.angle += 360.0
			# Inform receiver we had no results
			self.results.noResults()

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
			vs = VideoStream(src=0).start()
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
		
		# keep looping
		while True:
			with elapsedTime("Overall", printAtEnd = self.debugPrint) as self.overall:
				self.startTime = cv2.getTickCount()
				
				# grab the current frame
				frame = vs.read()

				# handle the frame from VideoCapture or VideoStream
				frame = frame[1] if self.recordedVideo else frame

				# if we are viewing a video and we did not grab a frame,
				# then we have reached the end of the video
				if frame is None:
					break

				# Get the current yaw value
				self.sensors.process()
				self.yaw = self.yawAccessor.getValue()
				
				# resize the frame
				frame = imutils.resize(frame, width=self.analysis_width, inter=cv2.INTER_NEAREST)
		
				# Do all necessary pre-processing, e.g. filtering and threholding
				self.preprocessImage(frame)
				
				# Analyse the frame for artifacts of interest
				self.analyseImage()
				
				# Display the results		
				if self.showImage:
					self.displayResults(frame)
					
				# Share the results
				self.publishResults()

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
			vs.stop()
		else:
			# otherwise, close the file
			vs.release()

		# close all windows
		cv2.destroyAllWindows()

if __name__ == "__main__":
	capture = FindRedLight()
	capture.captureContinuous()
