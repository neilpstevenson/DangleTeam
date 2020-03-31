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

class EcoDisasterImageCaptureAndAnalysis:
	
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
		blurred = cv2.GaussianBlur(frame, (self.blur_radius, self.blur_radius), 0)
		hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
		# construct a mask for the color range required, then perform
		# a series of dilations and erosions to remove any small
		# blobs left in the mask
		mask = cv2.inRange(hsv, (165,94,69), (180,255,255))
		mask = cv2.erode(mask, None, iterations=2)
		mask = cv2.dilate(mask, None, iterations=2)
		self.edgedRed = cv2.Canny(mask, 50, 150)
		
		mask = cv2.inRange(hsv, (40,63,27), (84,255,255))
		mask = cv2.erode(mask, None, iterations=2)
		mask = cv2.dilate(mask, None, iterations=2)
		self.edgedGreen = cv2.Canny(mask, 50, 150)

		# And simplier threshholds for the target regions
		mask = cv2.inRange(hsv, (112,58,54), (141,255,255))
		mask = cv2.erode(mask, None, iterations=2)
		self.maskedBlue = cv2.dilate(mask, None, iterations=2)
		
		mask = cv2.inRange(hsv, (7,53,138), (29,255,255))
		mask = cv2.erode(mask, None, iterations=2)
		self.maskedYellow = cv2.dilate(mask, None, iterations=2)
		
		self.timedCheckpoint("edges created")

	def analyseContours(self, cnts, frame, colour):
		count = 0
		for c in cnts:
			# approximate the contour
			peri = cv2.arcLength(c, True)
			approx = cv2.approxPolyDP(c, 0.01 * peri, True)

			# ensure that the approximated contour is "roughly" rectangular
			if len(approx) >= 4 and len(approx) <= 16:
				# compute the bounding box of the approximated contour and
				# use the bounding box to compute the aspect ratio
				(x, y, w, h) = cv2.boundingRect(approx)
				aspectRatio = w / float(h)
				#print(f"at: {(x,y)}, size: {(w,h)}, aspectRatio: {aspectRatio}, approx: {len(approx)}")

				# compute the solidity of the original contour
				#print(f"{c}")
				area = cv2.contourArea(c)
				hullArea = cv2.contourArea(cv2.convexHull(c))
				solidity = area / float(hullArea)

				# compute whether or not the width and height, solidity, and
				# aspect ratio of the contour falls within appropriate bounds
				keepDims = w > 15 and h > 25
				keepSolidity = solidity > 0.4 #0.8 #0.9
				#keepAspectRatio = aspectRatio >= 0.8 and aspectRatio <= 1.2
				keepAspectRatio = aspectRatio >= 0.3 and aspectRatio <= 0.8

				# ensure that the contour passes all our tests
				if keepDims and keepSolidity and keepAspectRatio:
					print(f"keep at: {(x,y)}: {len(approx)}, {keepDims}, {keepSolidity}({solidity:0.3f}), {keepAspectRatio}({aspectRatio:0.3f}), area: {area:0.3f}/{hullArea}")
					# draw an outline around the target and update the status
					# text
					cv2.drawContours(frame, [approx], -1, (0, 0, 255), 4)
					count += 1
					#print(f"at: {(x,y)}, size: {(w,h)}, aspectRatio: {aspectRatio}, approx: {len(approx)}")


					# compute the center of the contour region and draw the
					# crosshairs
					M = cv2.moments(approx)
					(cX, cY) = (int(M["m10"] // M["m00"]), int(M["m01"] // M["m00"]))
					(startX, endX) = (int(cX - (w * 0.15)), int(cX + (w * 0.15)))
					(startY, endY) = (int(cY - (h * 0.15)), int(cY + (h * 0.15)))
					# Put the count on the barrel
					cv2.putText(frame, f"{count}", (startX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
						(0, 0, 0), 2)
					#cv2.line(frame, (startX, cY), (endX, cY), (0, 0, 255), 3)
					#cv2.line(frame, (cX, startY), (cX, endY), (0, 0, 255), 3)
					
					# Calculate distance and angle to bottom of barrel
					self.calculateDistanceAngle(frame, x+w//2, y+h-1)
				
					# Add result to end list
					result = ImageAnalysisSharedIPC.ImageResult(
						 status = 1,
						 typename = 'Barrel',
						 name = colour,
						 confidence = 90.0,
						 distance = self.distance,
						 size = [0,0],
						 yaw = self.yawHeading,
						 angle = self.angle )
					self.results.append(result)
				else:
					print(f"reject at: {(x,y)}, {len(approx)}, {keepDims}, {keepSolidity}({solidity:0.3f}), {keepAspectRatio}({aspectRatio:0.3f}), area: {area:0.3f}/{hullArea}")
					# compute the center of the contour region and draw the
					# crosshairs
					cv2.drawContours(frame, [approx], -1, (0, 0, 0), 1)
					M = cv2.moments(approx)
					if M["m00"] != 0.0:
						(cX, cY) = (int(M["m10"] // M["m00"]), int(M["m01"] // M["m00"]))
						(startX, endX) = (int(cX - (w * 0.15)), int(cX + (w * 0.15)))
						(startY, endY) = (int(cY - (h * 0.15)), int(cY + (h * 0.15)))
						# Put the discount reason on the region
						if not keepDims:
							reason = "small"
						elif not keepSolidity:
							reason = "!solid"
						elif not keepAspectRatio:
							reason = "!rectangle"
						cv2.putText(frame, f"{reason}", (startX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
							(0, 0, 0), 2)
					
			else:
				print(f"reject cnts {len(approx)}")
		return count

	def calculateDistanceAngle(self, frame, x, y):
		# Calculate the angle from the bottom centre to the lowest point
		self.ourPosition = (frame.shape[1]//2, frame.shape[0] + self.cameraNearestVisiblePixels)
		self.angle = np.arctan((self.ourPosition[0]-x)/(self.ourPosition[1]-y)) * 180.0/3.14159 * self.angleAdjustment
		
		# Distance approximation
		dist_recip = self.cameraFurthestVisiblePixel - (frame.shape[0] - y)
		if dist_recip > 0:
			self.distance = ((((self.cameraFurthestVisiblePixel-1) / dist_recip) - 1) * self.cameraHeightAdjustment + 1) * self.cameraNearestVisibleDistance
		else:
			self.distance = 999

		self.yawHeading = self.yaw + self.angle 
		if self.yawHeading > 180.0:
			self.yawHeading -= 360.0
		elif self.yawHeading < -180.0:
			self.yawHeading += 360.0
		

	def analyseRegions(self, maskedFrame, colour):
		# find contours in the mask and initialize the current
		# (x, y) center of the ball
		cnts = cv2.findContours(maskedFrame, cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		cnts = imutils.grab_contours(cnts)
		self.center = None

		# only proceed if at least one contour was found
		self.hasResult = False
		if len(cnts) > 0:
			# find the largest contour in the mask, 
			c = max(cnts, key=cv2.contourArea)
			# find the best enclosing rectangle
			x, y, w, h = cv2.boundingRect(c)
			M = cv2.moments(c)
			self.center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
			self.displayContours = [c] # to display - for all, use: cnts largest:[c]
				
			# only proceed if the radius meets a minimum size
			if w >= self.minWidth and h >= self.minHeight:
				self.hasResult = True
				
				# Calculate the angle and distances
				self.calculateDistanceAngle(maskedFrame, x+w//2, y+h-1)
				
				# Add result to end list
				result = ImageAnalysisSharedIPC.ImageResult(
					 status = 1,
					 typename = 'Region',
					 name = colour,
					 confidence = 90.0,
					 distance = self.distance,
					 size = [0,0],
					 yaw = self.yawHeading,
					 angle = self.angle )
				self.results.append(result)
					
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
	# Analyse the filtered/masked frames to produce the required results
	#
	def analyseImage(self, frame):
		# find contours in the edge map
		cntsRed = cv2.findContours(self.edgedRed, cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		cntsRed = imutils.grab_contours(cntsRed)
		cntsGreen = cv2.findContours(self.edgedGreen, cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		cntsGreen = imutils.grab_contours(cntsGreen)
		
		# Overlay everything detected
		#cv2.polylines(frame, cnts,  True, (0, 255, 0), 2, 8)

		# loop over the contours
		counts = [0,0]
		colour = -1
		colours = ['Red','Green']
		for cnts in cntsRed,cntsGreen:
			colour += 1
			#sortedCnts = sorted(cnts, key=lambda x: -cv2.contourArea(x))
			# construct the list of bounding boxes and sort them from top to
			# bottom
			if len(cnts) > 1:
				boundingBoxes = [cv2.boundingRect(c) for c in cnts]
				(cnts, boundingBoxes) = zip(*sorted(zip(cnts, boundingBoxes),
					key=lambda b:b[1][1], reverse=True))

			counts[colour] = self.analyseContours(cnts, frame, colours[colour])
			
		if sum(counts) > 0:
			status = f"{counts[0]} Red Barrels Detected, {counts[1]} Green"
		else:
			status = "No barrels detected"
			
		# Work out the target regions
		self.analyseRegions(self.maskedBlue, 'Blue')
		if self.hasResult:
			# Show contours found
			cv2.polylines(frame, self.displayContours,  True, (255, 0, 0), 2, 8)		
			cv2.putText(frame, "Clean Target", self.center, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
		self.analyseRegions(self.maskedYellow, 'Yellow')
		if self.hasResult:
			# Show contours found
			cv2.polylines(frame, self.displayContours,  True, (0, 255, 255), 2, 8)
			cv2.putText(frame, "Dirty Target", self.center, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
				
		# draw the status text on the frame
		cv2.putText(frame, status, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
			(0, 0, 255), 2)
			
		# Overall time taken
		endTime = cv2.getTickCount()
		self.elapsed = (endTime - self.startTime) / cv2.getTickFrequency()

	#
	# Display an annotated image of the results
	#		
	def displayResults(self, frame):
		if self.fps != None:
			cv2.putText(frame, f"{self.fps}fps", (frame.shape[1]-60, frame.shape[0]-20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
		# show the frame to our screen
		cv2.imshow("Frame", frame)
		
		cv2.imshow("EdgedRed", self.edgedRed)
		cv2.imshow("EdgedGreen", self.edgedGreen)
		cv2.imshow("Blue", self.maskedBlue)
		cv2.imshow("Yellow", self.maskedYellow)
		
		# Print up the results found
		print(f"Total time taken {self.elapsed}")
		print(f"Result count {len(self.results)}")
		for result in self.results:
			print(f"{result.typename}.{result.name}")
			print(f"  d={result.distance:.0f}mm, size={result.size}, yaw={result.yaw:.1f}, angle={result.angle:.1f}")

	#
	# Share the results for robot code consumption
	#
	def publishResults(self):
		pass
		
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
			vs = VideoStream(src=0)
			vs.stream.stream.set( cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 7.5)
			vs.stream.stream.set( cv2.CAP_PROP_WHITE_BALANCE_RED_V, 7.5)
			vs.stream.stream.set( cv2.CAP_PROP_AUTO_WB, 0)
			vs.start()
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
			self.results = []
			
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
				self.analyseImage(frame)
				
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
