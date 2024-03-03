import time
import numpy as np
import cv2
from picamera2 import Picamera2
#from picamera.array import PiRGBArray
#from picamera import PiCamera
from interfaces.LineAnalysisSharedIPC import LineAnalysisSharedIPC
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.Config import Config

class VisionLineAnalysisLava:

	def __init__(self, resolution, threshold, display, displayGrayscale, filename, blinkers, numSlices, framerate=30, ignoreTopSlices = 0, filterRatio=15, lookahead=0.8, saveRaw=True):
		self.threshold = threshold
		self.filename = filename
		self.display = display
		self.displayGrayscale = displayGrayscale
		self.blinkers = blinkers # pixels at either side of top
		self.ignoreTopSlices = ignoreTopSlices
		self.saveRaw = saveRaw
		
		# Create/overwrite
		self.results = LineAnalysisSharedIPC()
		self.results.create()
		
		# Define the analysis parameters
		self.radius = resolution[0]//filterRatio #31	# ensure radius is odd and slighly bigger than the white line
		self.numSlices = numSlices
		self.targetLookaheadRatio = lookahead # % of screen height that we attempt to head towards

		# initialize the camera and grab a reference to the raw camera capture
		# Legacy interface
		#self.camera = PiCamera()
		#self.camera.resolution = resolution
		self.resolution = resolution
		#self.camera.framerate = framerate
		#self.rawCapture = PiRGBArray(self.camera, size=self.resolution)
		self.picam2 = Picamera2()
		self.picam2.configure( self.picam2.create_preview_configuration(main={"format": 'RGB888', "size": (resolution[0], resolution[1])}))
		self.picam2.start()
		
		# Current Yaw reading
		self.sensors = SensorAccessFactory.getSingleton()
		self.yaw = self.sensors.yaw()
		
	def captureAndAssess(self):
		# File capture
		if self.filename != None:
			print(f"Saving to file: {self.filename}")
			# Define the codec and create VideoWriter object.
			self.captureFile = cv2.VideoWriter(self.filename, cv2.VideoWriter_fourcc(*'mp4v'), 10, (self.resolution[0], self.resolution[1]))
			
		# Start timer, so we know how long things took
		startTime = cv2.getTickCount()
		rateStartTime = startTime
		rate = 10.0

		# Blinkers polygons
		blinkerPolys = np.array([[[0,0], [self.blinkers, 0], [0, self.resolution[1]-1]],
								 [[self.resolution[0]-1, 0], [self.resolution[0]-1 - self.blinkers, 0], [self.resolution[0]-1, self.resolution[1]-1]]], np.int32)
		#print(f"blinkerPolys: {blinkerPolys}")
		
		angle = None
		count = 0
		
		# grab the next frame as a numpy array
		while True:
			#for frame in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True): #, resize = self.resolution):
			original = self.picam2.capture_array()
			
			count += 1
			
			# Get the current yaw value
			self.sensors.process()
			yaw = self.yaw.getValue()
			
			# grab the raw NumPy array representing the image, then initialize the timestamp
			# and occupied/unoccupied text
			#original = frame.array

			# Convert to greyscale and apply a Gaussian blur to the image in order 
			# to make more robust against noise and reflections
			gray = cv2.cvtColor(original.copy(), cv2.COLOR_BGR2GRAY)
			
			# Apply blinkers
			cv2.fillPoly(gray, blinkerPolys, 0)
			
			#gray = cv2.GaussianBlur(gray, (self.radius, self.radius), 0)
			gray = cv2.blur(gray, (self.radius, self.radius))

			# Chop the image into a number of horizontal slices
			slices = np.array_split(gray,self.numSlices)

			offset = 0
			points = []
			# For each slice, determine the brightest point
			for bit in range(len(slices)):
				if bit >= self.ignoreTopSlices:
					(minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(slices[bit])
					point = (maxLoc[0],maxLoc[1]+offset)
					offset += len(slices[bit])
					if maxVal < self.threshold:
						print(f"Ignoring point: {point}, value {maxVal}")
						pass
					else:
						print(f"Using point: {point}, value {maxVal}")
						points.append(point)
				else:
					offset += len(slices[bit])
		
			if len(points) < 5:
				print("Too few points - ignoring")
				hasResult = False
			else:
				# Fit a striaght line to the brightest point on each slice
				vx, vy, x0, y0 = cv2.fitLine(np.array(points), cv2.DIST_HUBER, 0, 0.1, 0.1)
				# Strip arrays
				vx = vx[0]
				vy = vy[0]
				x0 = x0[0]
				y0 = y0[0]
				# ensure the arrow is always pointing forwards (up the image)
				if vy > 0:
					vy = -vy
					vx = -vx
				#print(f"vx: {vx}, vy: {vy}, x0: {x0}, y0: {y0}")
				# Re-origin to stop some jitter
				#y0 = self.resolution[1]*(self.numSlices-1)//self.numSlices//2
				# scale the vector to approx screen size
				vx *= self.resolution[1]//2
				vy *= self.resolution[1]//2
				# Calculate an angle from where we are to approx mid point
				currentPosition = (self.resolution[0]//2, self.resolution[1])
				desiredPosition = (int(x0+vx*self.targetLookaheadRatio), int(y0+vy*self.targetLookaheadRatio))
				angle = np.arctan((currentPosition[0]-desiredPosition[0])/(currentPosition[1]-desiredPosition[1])) * 180.0/3.14159
				hasResult = True

			# Overall capture/analysis time
			endTime = cv2.getTickCount()
			time = (endTime - startTime) / cv2.getTickFrequency()

			if hasResult:	
				# Share the results
				yawAngle = yaw + angle 
				if yawAngle > 180.0:
					yawAngle -= 360.0
				elif yawAngle < -180.0:
					yawAngle += 360.0
				print(f"(vx, vy), (x0, y0): ({vx}, {vy}), ({x0} , {y0})")
				self.results.shareResults(startTime, time, angle, yawAngle, ((vx, vy), (x0, y0)), point)
			elif angle != None:
				# Ajust angle based on last successful analysis for display only
				angle += (lastYaw - yaw)
				if angle > 180.0:
					angle -= 360.0
				elif angle < -180.0:
					angle += 360.0
			lastYaw = yaw
				
			# clear the stream in preparation for the next frame
			#self.rawCapture.truncate(0)

			# display the results
			if self.display and angle != None:
				# Print the time taken
				print(f"Capture & analysis: {time:.3f}secs")
				# Create an overlayed image
				assessment = original.copy()
				for point in points:
					cv2.circle(assessment, point, 5, (0,0,255), 1)
				# Show blinkers
				cv2.polylines(assessment, blinkerPolys, 0, (0,0,0), thickness=2)
				# Draw an arrow representing the brightest points
				#print(f"values: {(int(x0-vx), int(y0-vy))}, {(int(x0+vx), int(y0+vy))}")
				cv2.arrowedLine(assessment, (int(x0-vx), int(y0-vy)), (int(x0+vx), int(y0+vy)), (255, 255, 0), 2)
				# Draw an angle from where we are to target
				#print(f"values: {currentPosition}, {desiredPosition}")
				cv2.arrowedLine(assessment, currentPosition, desiredPosition, (0, 255, 0), 3)
				# Overlay the angle calculated
				np.set_printoptions(precision=2)
				cv2.putText(assessment, f"{yaw:.2f}deg => {angle:+.2f}deg", (5, self.resolution[1]-4), cv2.FONT_HERSHEY_DUPLEX, 0.4, (0, 255, 0))
				cv2.putText(assessment, f"{rate:.0f}fps", (self.resolution[0]-40, self.resolution[1]-4), cv2.FONT_HERSHEY_DUPLEX, 0.4, (0, 255, 0))
				cv2.imshow(f"assessed direction", assessment)
				if self.displayGrayscale:
					cv2.imshow(f"grey", gray)
				
				if self.filename != None:
					# Write the next frame into the file
					if self.saveRaw:
						self.captureFile.write(original)
					else:
						self.captureFile.write(assessment)

			if angle != None:
				print(f"Assessed angle: {angle:.1f}")
				
			displayEndTime = cv2.getTickCount()
			overalltime = (displayEndTime - startTime) / cv2.getTickFrequency()
			print(f"Overall time:   {overalltime:.3f}secs, {rate:.1f}fps")

			key = cv2.waitKey(1) & 0xff
			if key == 27 or key == ord('q'):
				quit()
				
			startTime = cv2.getTickCount()
			
			if count % 10 == 0:
				frameTime = (startTime - rateStartTime) / cv2.getTickFrequency()
				rate = 10.0/frameTime
				rateStartTime = startTime

