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
from interfaces.LineAnalysisSharedIPC import LineAnalysisSharedIPC
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
		self.analysis_width = config.get("minesweeper.analysis.imagewidth", 480)
		self.blur_radius = config.get("minesweeper.analysis.burrradius", 11)
		#self.minSize = config.get("minesweeper.analysis.minsize", 10)
		self.minWidth = config.get("minesweeper.analysis.minWidth", 15)
		self.minHeight  = config.get("minesweeper.analysis.minHeight", 10)
		# Scale factors for real-world measures
		self.angleAdjustment = config.get("minesweeper.analysis.anglescale", 2.6)#1.3#0.55
		self.distanceAdjustment = config.get("minesweeper.analysis.distancescale", 0.00005)#0.0007#0.0013
		self.distanceOffset = int(self.analysis_width * config.get("minesweeper.analysis.distanceoffset", 1.75)) # relative to width
		
		# define the lower and upper boundaries of the target 
		# colour in the HSV color space, then initialize the
		# list of tracked points
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
		
		# Results IPC
		self.results = LineAnalysisSharedIPC()
		self.results.create()
		
		# Current Yaw reading
		self.sensors = SensorAccessFactory.getSingleton()
		self.yaw = self.sensors.yaw()

	def capture(self):
		# if a video path was not supplied, grab the reference
		# to the webcam
		if not self.recordedVideo:
			vs = VideoStream(src=0).start()
		# otherwise, grab a reference to the video file
		else:
			vs = cv2.VideoCapture(self.videoFilenanme)

		trail = deque(maxlen=self.trailSize)

		# allow the camera or video file to warm up ???
		#time.sleep(2.0)

		# stats
		fpsStart = cv2.getTickCount() / cv2.getTickFrequency()
		fps = None
		count = 0
		angle = None

		# keep looping
		while True:
			with elapsedTime("overall") as overall:
				startTime = cv2.getTickCount()
				
				# grab the current frame
				frame = vs.read()

				# Get the current yaw value
				self.sensors.process()
				yaw = self.yaw.getValue()

				# handle the frame from VideoCapture or VideoStream
				frame = frame[1] if self.recordedVideo else frame

				# if we are viewing a video and we did not grab a frame,
				# then we have reached the end of the video
				if frame is None:
					break

				# resize the frame, blur it, and convert it to the HSV
				# color space
				frame = imutils.resize(frame, width=self.analysis_width, inter=cv2.INTER_NEAREST)
				blurred = cv2.blur(frame, (self.blur_radius, self.blur_radius))
				#blurred = cv2.GaussianBlur(frame, (self.blur_radius, self.blur_radius), 0)
				hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

				print(f"blur at: {overall():.3f}")

				# construct a mask for the color range required, then perform
				# a series of dilations and erosions to remove any small
				# blobs left in the mask
				mask = cv2.inRange(hsv, self.colourTargetLower, self.colourTargetUpper)
				mask = cv2.erode(mask, None, iterations=2)
				mask = cv2.dilate(mask, None, iterations=2)

				print(f"masked at: {overall():.3f}")

				# find contours in the mask and initialize the current
				# (x, y) center of the ball
				cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
					cv2.CHAIN_APPROX_SIMPLE)
				cnts = imutils.grab_contours(cnts)
				center = None

				# only proceed if at least one contour was found
				hasResult = False
				if len(cnts) > 0:
					# find the largest contour in the mask, 
					c = max(cnts, key=cv2.contourArea)
					# then use it to compute the minimum enclosing circle and
					# centroid
					#((x, y), radius) = cv2.minEnclosingCircle(c)
					# find the best enclosing rectangle
					x, y, w, h = cv2.boundingRect(c)
					M = cv2.moments(c)
					center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
					#print(f"radius: {radius}, center: {center}")
					print(f"width: {w}, height: {h}, center: {center}")
					
					if self.showImage:
						# Show contours found
						cv2.polylines(frame, cnts,  True, (0, 255, 0), 2, 8)
						#cv2.polylines(frame, [c],  True, (0, 255, 0), 2, 8)

					print(f"mid point HSV: {hsv[center[1],center[0]]}")
					print(f"20 above mid point HSV: {hsv[center[1]-20,center[0]]}")
						
					# only proceed if the radius meets a minimum size
					if w >= self.minWidth and h >= self.minHeight:
						hasResult = True
						
						# Calculate the angle from the bottom centre to the centre
						ourPosition = (hsv.shape[1]//2, hsv.shape[0] + self.distanceOffset)
						angle = np.arctan((ourPosition[0]-center[0])/(ourPosition[1]-center[1])) * 180.0/3.14159 * self.angleAdjustment
						#print(f"ourPosition: {ourPosition}, circlecentre: {(x, y)}, momentscentre: {center}")
						print(f"angle: {angle}, center: {center}")
						# Distance approximation
						distance = (ourPosition[1]-center[1]) ** 2 * self.distanceAdjustment
						print(f"distance: {distance}mm")
						
						if self.showImage:
							# Draw an angle from where we are to target
							cv2.arrowedLine(frame, ourPosition, center, (0, 255, 0), 3)
							# Overlay the angle calculated
							np.set_printoptions(precision=2)
							cv2.putText(frame, f"Head {angle:+.1f}deg for {distance:.0f}mm", (5, hsv.shape[0]-20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
						
						
				if self.showImage and fps != None:
					cv2.putText(frame, f"{fps}fps", (hsv.shape[1]-60, hsv.shape[0]-20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

				# Share the results
				if hasResult:	
					# Overall capture/analysis time
					endTime = cv2.getTickCount()
					timestamp = (endTime - startTime) / cv2.getTickFrequency()
					
					yawAngle = yaw + angle 
					if yawAngle > 180.0:
						yawAngle -= 360.0
					elif yawAngle < -180.0:
						yawAngle += 360.0
					self.results.shareResults(startTime, timestamp, angle, yawAngle, (ourPosition, center), (0,distance) )
				elif angle != None:
					# Ajust angle based on last successful analysis for display only
					angle += (lastYaw - yaw)
					if angle > 180.0:
						angle -= 360.0
					elif angle < -180.0:
						angle += 360.0
					# Inform receiver we had no results
					self.results.noResults()
				lastYaw = yaw

				# Stats
				count += 1
				if count % 10 == 0:
					fpsEnd = cv2.getTickCount() / cv2.getTickFrequency()
					fps = int(10 / (fpsEnd - fpsStart))
					fpsStart = fpsEnd
				if fps != None:
					print(f"{fps}fps")
							
				if self.showImage:
					# update the points queue
					trail.appendleft(center)

					# loop over the set of tracked points
					for i in range(1, len(trail)):
						# if either of the tracked points are None, ignore
						# them
						if trail[i - 1] is None or trail[i] is None:
							continue
						# Recent lines thicker than older lines
						thickness = int(np.sqrt(self.trailSize / float(i + 1)) * 2.0)
						cv2.line(frame, trail[i - 1], trail[i], (0, 0, 255), thickness)

					# show the frame to our screen
					cv2.imshow("Frame", frame)
					#cv2.imshow("HSV", hsv)
					#cv2.imshow("mask", mask)

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
	capture.capture()
