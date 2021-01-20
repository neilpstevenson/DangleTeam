import time as t
import numpy as np
import cv2
#from picamera.array import PiRGBArray
#from picamera import PiCamera
from interfaces.LineAnalysisSharedIPC import LineAnalysisSharedIPC
from interfaces.VoiceRecognitionSharedIPC import VoiceRecognitionSharedIPC
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.Config import Config

class VisionLineAnalysis:

	def __init__(self, resolution, threshold, display, displayGrayscale, filename, blinkers, numSlices, framerate=30, ignoreTopSlices = 0, filterRatio=15, lookahead=0.8, saveRaw=True, blackLine=True):
		self.threshold = threshold
		self.filename = filename
		self.display = display
		self.displayGrayscale = displayGrayscale
		self.blinkers = blinkers # pixels at either side of top
		self.blinkerWeight = 25
		self.ignoreTopSlices = ignoreTopSlices
		self.saveRaw = saveRaw
		self.blackLine = blackLine
		
		# Create/overwrite
		self.results = LineAnalysisSharedIPC()
		self.results.create()
		
		# Define the analysis parameters
		self.radius = resolution[0]//filterRatio #31	# ensure radius is odd and slighly bigger than the white line
		self.numSlices = numSlices
		self.targetLookaheadRatio = lookahead # % of screen height that we attempt to head towards

		# initialize the camera and grab a reference to the raw camera capture
		#self.camera = PiCamera()
		#self.camera.resolution = resolution
		self.cap = cv2.VideoCapture(0)
		self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])#320)
		self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])#240)
		self.cap.set(cv2.CAP_PROP_FPS, framerate)

		self.resolution = resolution
		#self.camera.framerate = framerate
		#self.rawCapture = PiRGBArray(self.camera, size=self.resolution)
		
		# Current Yaw reading
		self.sensors = SensorAccessFactory.getSingleton()
		self.yaw = self.sensors.yaw()
		
		# Voice command
		self.voice = VoiceRecognitionSharedIPC()
		self.voice.read()
		
		
	def captureAndAssess(self):
		# File capture
		if self.filename != None:
			print(f"Saving to file: {self.filename}")
			# Define the codec and create VideoWriter object.
			self.captureFile = cv2.VideoWriter(self.filename, cv2.VideoWriter_fourcc(*'mp4v'), 10, self.resolution[0])
			
		# Start timer, so we know how long things took
		startTime = cv2.getTickCount()
		rateStartTime = startTime
		rate = 10.0

		# Blinkers polygons
		blinkerPolys = np.array([[[0,0], [self.blinkers, 0], [0, self.resolution[1]-1]],
								 [[self.resolution[0]-1, 0], [self.resolution[0]-1 - self.blinkers, 0], [self.resolution[0]-1, self.resolution[1]-1]]], np.int32)
		#print(f"blinkerPolys: {blinkerPolys}")
		# Create 3 version of the mask for preferred direction
		left_mask = np.zeros((self.resolution[1], self.resolution[0]), np.uint8)
		right_mask = np.zeros((self.resolution[1], self.resolution[0]), np.uint8)
		edge_mask = np.zeros((self.resolution[1], self.resolution[0]), np.uint8)
		for v in range(5):
			# Left mask
			cv2.rectangle(left_mask, (self.blinkers*v*2//5, 0), (self.blinkers*(v*2+2)//5, self.resolution[1]-1), (5-v)*self.blinkerWeight, -1)
			# Right mask
			cv2.rectangle(right_mask, (self.resolution[0]-1-self.blinkers*v*2//5, 0), (self.resolution[0]-1-self.blinkers*(v*2+2)//5, self.resolution[1]-1), (5-v)*self.blinkerWeight, -1)
			# Edge mask
			cv2.rectangle(edge_mask, (self.blinkers*v//5, 0), (self.blinkers*(v+1)//5, self.resolution[1]-1), (5-v)*self.blinkerWeight, -1)
			cv2.rectangle(edge_mask, (self.resolution[0]-1-self.blinkers*v//5, 0), (self.resolution[0]-1-self.blinkers*(v+1)//5, self.resolution[1]-1), (5-v)*self.blinkerWeight, -1)
		
		angle = None
		count = 0
		
		# grab the next frame as a numpy array
		#stream = self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True) #, resize = self.resolution)
		#t.sleep(2.0)
		#for frame in stream:
		while True:
			count += 1
			
			# Get the current yaw value
			self.sensors.process()
			yaw = self.yaw.getValue()
			
			# grab the raw NumPy array representing the image, then initialize the timestamp
			# and occupied/unoccupied text
			#original = frame.array
			ret, original = self.cap.read()

			# Convert to greyscale and apply a Gaussian blur to the image in order 
			# to make more robust against noise and reflections
			gray = cv2.cvtColor(original.copy(), cv2.COLOR_BGR2GRAY)
			
			# Apply blinkers
			if self.blackLine:
				#overlay = gray.copy()
				#cv2.fillPoly(overlay, blinkerPolys, 255)
				# Draw 5 vertical stripes for increasing whiteness
				print(f"{self.resolution} {gray.shape}")
				#overlay = np.zeros(gray.shape, np.uint8)
				
				voiceCommand = self.voice.findLastSpokenWord(['left','right','go'])
				print(f"voiceCommand: {voiceCommand}")
				if voiceCommand == 'right':
					# Left mask
					gray = cv2.add(left_mask, gray)
				elif voiceCommand == 'left':
					# Right mask
					gray = cv2.add(right_mask, gray)
				else:
					# Edge mask
					gray = cv2.add(edge_mask, gray)
			else:
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
					offset += len(slices[bit])
					
					if self.blackLine:
						if minVal > self.threshold:
							point = (minLoc[0],minLoc[1]+offset)
							print(f"Ignoring point: {point}, min value {minVal}")
							pass
						else:
							point = (minLoc[0],minLoc[1]+offset)
							print(f"Using point: {point}, value {minVal}")
							points.append(point)
					else:
						if maxVal < self.threshold:
							point = (minLoc[0],minLoc[1]+offset)
							print(f"Ignoring point: {point}, max value {maxVal}")
							pass
						else:
							point = (maxLoc[0],maxLoc[1]+offset)
							print(f"Using point: {point}, value {maxVal}")
							points.append(point)
				else:
					offset += len(slices[bit])
		
			if len(points) < 5:
				print("Too few points - ignoring")
				hasResult = False
			else:
				# Add a few points where we are, to prevent the line going to extreme angles
				for p in range(-4,5):
					point = (self.resolution[0]//2 + p * 20, self.resolution[1])
					points.append(point)
				
				# Fit a striaght line to the brightest point on each slice
				vx, vy, x0, y0 = cv2.fitLine(np.array(points), cv2.DIST_HUBER, 0, 0.1, 0.1)
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
				# Draw an arrow representing the brightest points
				cv2.arrowedLine(assessment, (x0-vx, y0-vy), (x0+vx, y0+vy), (255, 255, 0), 2)
				# Draw an angle from where we are to target
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

			key = cv2.waitKey(1)
			if key == 27 or key == 'q':
				quit()
				
			startTime = cv2.getTickCount()
			
			if count % 10 == 0:
				frameTime = (startTime - rateStartTime) / cv2.getTickFrequency()
				rate = 10.0/frameTime
				rateStartTime = startTime

