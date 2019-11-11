import time
import numpy as np
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
from LineAnalysisSharedResult import LineAnalysisSharedResult

class VisionLineProcessor:

	def __init__(self):
		
		# Create/overwrite
		self.results = LineAnalysisSharedResult()
		self.results.create()
		
		# Define the analysis parameters
		self.radius = 31	# ensure radius is odd and slighly bigger than the white line
		self.numSlices = 20

		# initialize the camera and grab a reference to the raw camera capture
		self.camera = PiCamera()
		self.camera.resolution = (320, 240)
		self.camera.framerate = 30
		self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
		
	def captureAndAssess(self, display):
		# Start timer, so we know how long things took
		startTime = cv2.getTickCount()
		
		# grab the next frame as a numpy array
		for frame in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):
			
			# grab the raw NumPy array representing the image, then initialize the timestamp
			# and occupied/unoccupied text
			original = frame.array

			# Convert to greyscale and apply a Gaussian blur to the image in order 
			# to make more robust against noise and reflections
			gray = cv2.cvtColor(original.copy(), cv2.COLOR_BGR2GRAY)
			cv2.GaussianBlur(gray, (self.radius, self.radius), 0)

			# Chop the image into a number of horizontal slices
			slices = np.array_split(gray,self.numSlices)

			offset = 0
			points = []
			# For each slice, determine the brightest point
			for bit in range(len(slices)):
				(minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(slices[bit])
				point = (maxLoc[0],maxLoc[1]+offset)
				offset += len(slices[bit])
				points.append(point)
				
			# Fit a striaght line to the brightest point on each slice
			vx, vy, x0, y0 = cv2.fitLine(np.array(points), cv2.DIST_HUBER, 0, 0.1, 0.1)
			# ensure the arrow is always pointing forwards (up the image)
			if vy > 0:
				vy = -vy
				vx = -vx
			# Calculate an angle from where we are to approx mid point
			currentPosition = (self.camera.resolution[0]//2, self.camera.resolution[1])
			desiredPosition = (x0,y0)
			angle = np.arctan((currentPosition[0]-desiredPosition[0])/(currentPosition[1]-desiredPosition[1])) * 180.0/3.14159

			endTime = cv2.getTickCount()
			time = (endTime - startTime) / cv2.getTickFrequency()
			
			# Share the results
			self.results.shareResults(startTime, time, angle, ((vx, vy), (x0, y0)), point)
			
			# clear the stream in preparation for the next frame
			self.rawCapture.truncate(0)
			
			# display the results
			if display:
				# Print the time taken
				print(f"Took {time:.3f}secs")
				# Create an overlayed image
				assessment = original.copy()
				for point in points:
					#cv2.circle(assessment, point, self.radius, (255, 0, 0), 1)
					cv2.circle(assessment, point, 5, (0,0,255), 1)
				# scale the vector to approx screen size
				vx *= self.camera.resolution[0]//3
				vy *= self.camera.resolution[0]//3
				# Draw an arrow representing the brightest points
				cv2.arrowedLine(assessment, (x0-vx, y0-vy), (x0+vx, y0+vy), (255, 255, 0), 2)
				# Calculate an angle from where we are to approx mid point
				currentPosition = (self.camera.resolution[0]//2, self.camera.resolution[1])
				desiredPosition = (x0,y0)
				angle = np.arctan((currentPosition[0]-desiredPosition[0])/(currentPosition[1]-desiredPosition[1])) * 180.0/3.14159
				cv2.arrowedLine(assessment, currentPosition, desiredPosition, (0, 255, 0), 3)
				# Overlay the angle calculated
				cv2.putText(assessment, f"{angle} degrees", (5, self.camera.resolution[1]-4), cv2.FONT_HERSHEY_DUPLEX, 0.4, (0, 255, 0))
				cv2.imshow(f"assessed direction", assessment)
				
				displayEndTime = cv2.getTickCount()
				overalltime = (displayEndTime - startTime) / cv2.getTickFrequency()
				print(f"Overall {overalltime:.3f}secs")
				
			print(f"Assessed angle: {angle}")

			cv2.waitKey(1)
			startTime = cv2.getTickCount()
				
processor = VisionLineProcessor()
processor.captureAndAssess(True)
