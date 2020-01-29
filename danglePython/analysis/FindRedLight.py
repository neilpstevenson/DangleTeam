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
from interfaces.LineAnalysisSharedIPC import LineAnalysisSharedIPC
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.Config import Config

class FindRedLight:
	
	def __init__(self):
		# construct the argument parse and parse the arguments
		ap = argparse.ArgumentParser()
		ap.add_argument("-v", "--video",
			help="path to the (optional) video file")
		ap.add_argument("-t", "--trail", type=int, default=25,
			help="max trail size")
		args = vars(ap.parse_args())
		self.recordedVideo = args.get("video", False)
		if self.recordedVideo:
			self.videoFilenanme = args["video"]

		# Scale factors for real-world measures
		self.angleAdjustment = 0.55
		self.distanceAdjustment = 0.0013
		self.distanceOffset = 300 # pixels

		# define the lower and upper boundaries of the target 
		# colour in the HSV color space, then initialize the
		# list of tracked points
		self.colourTargetLower = (160,128,24)#(29, 86, 6)
		self.colourTargetUpper = (180,255,255)#(64, 255, 255)
		self.trailSize = args["trail"]
		self.showImage = True
		
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

		# keep looping
		while True:
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
			frame = imutils.resize(frame, width=600)
			blurred = cv2.GaussianBlur(frame, (11, 11), 0)
			hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

			# construct a mask for the color range required, then perform
			# a series of dilations and erosions to remove any small
			# blobs left in the mask
			mask = cv2.inRange(hsv, self.colourTargetLower, self.colourTargetUpper)
			mask = cv2.erode(mask, None, iterations=2)
			mask = cv2.dilate(mask, None, iterations=2)

			# find contours in the mask and initialize the current
			# (x, y) center of the ball
			cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
				cv2.CHAIN_APPROX_SIMPLE)
			cnts = imutils.grab_contours(cnts)
			center = None

			# only proceed if at least one contour was found
			hasResult = False
			if len(cnts) > 0:
				# find the largest contour in the mask, then use
				# it to compute the minimum enclosing circle and
				# centroid
				c = max(cnts, key=cv2.contourArea)
				((x, y), radius) = cv2.minEnclosingCircle(c)
				M = cv2.moments(c)
				center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

				# only proceed if the radius meets a minimum size
				if radius > 10:
					count += 1
					hasResult = True
					# Show contours found
					#cv2.polylines(frame, cnts,  True, (0, 255, 0), 2, 8)
					cv2.polylines(frame, [c],  True, (0, 255, 0), 2, 8)
					
					# Calculate the angle from the bottom centre to the centre
					ourPosition = (hsv.shape[1]//2, hsv.shape[0])
					angle = np.arctan((ourPosition[0]-center[0])/(ourPosition[1]-center[1])) * 180.0/3.14159 * self.angleAdjustment
					#print(f"ourPosition: {ourPosition}, circlecentre: {(x, y)}, momentscentre: {center}")
					print(f"angle: {angle}")
					
					# Distance approximation
					distance = ((ourPosition[1]-center[1]) + self.distanceOffset) ** 2 * self.distanceAdjustment
					print(f"distance: {distance}mm")
					
					# Stats
					if count % 10 == 0:
						fpsEnd = cv2.getTickCount() / cv2.getTickFrequency()
						fps = int(10 / (fpsEnd - fpsStart))
						fpsStart = fpsEnd
					if fps != None:
						print(f"{fps}fps")

					if self.showImage:
						# Draw an angle from where we are to target
						cv2.arrowedLine(frame, ourPosition, center, (0, 255, 0), 3)
						# Overlay the angle calculated
						np.set_printoptions(precision=2)
						cv2.putText(frame, f"Heading {angle:+.1f}deg for {distance:.0f}mm", (5, hsv.shape[0]-20), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
						if fps != None:
							cv2.putText(frame, f"{fps}fps", (hsv.shape[1]-80, hsv.shape[0]-20), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0), 1, cv2.LINE_AA)
					
			# Share the results
			if hasResult:	
				# Overall capture/analysis time
				endTime = cv2.getTickCount()
				time = (endTime - startTime) / cv2.getTickFrequency()
				
				yawAngle = yaw + angle 
				if yawAngle > 180.0:
					yawAngle -= 360.0
				elif yawAngle < -180.0:
					yawAngle += 360.0
				self.results.shareResults(startTime, time, angle, yawAngle, ((0, 0), (0, 0)), center)
			elif angle != None:
				# Ajust angle based on last successful analysis for display only
				angle += (lastYaw - yaw)
				if angle > 180.0:
					angle -= 360.0
				elif angle < -180.0:
					angle += 360.0
			lastYaw = yaw
						
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

			key = cv2.waitKey(1) & 0xFF

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
