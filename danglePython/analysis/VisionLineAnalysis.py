import numpy as np
import cv2
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
		self.blinkerWeight = 125
		self.ignoreTopSlices = ignoreTopSlices
		self.saveFile = (filename is not None)
		self.saveRaw = saveRaw
		self.blackLine = blackLine
		
		# Create/overwrite
		self.results = LineAnalysisSharedIPC()
		self.results.create()
		
		# Define the analysis parameters
		self.radius = resolution[0]//filterRatio #31	# ensure radius is odd and slighly bigger than the white line
		self.numSlices = numSlices
		self.minPoints = numSlices//5
		self.targetLookaheadRatio = lookahead # % of screen height that we attempt to head towards

		# initialize the camera and grab a reference to the raw camera capture
		self.cap = cv2.VideoCapture(0)
		self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])#320)
		self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])#240)
		self.cap.set(cv2.CAP_PROP_FPS, framerate)

		self.resolution = resolution
		self.framerate = framerate
		
		# Current Yaw reading
		self.sensors = SensorAccessFactory.getSingleton()
		self.yaw = self.sensors.yaw()
		
		# Voice command
		self.voice = VoiceRecognitionSharedIPC()
		self.voice.read()
		
		# Blinker masks
		slices = 10
		maxOpacity = self.blinkerWeight / slices
		# Create 3 version of the mask for preferred direction
		self.left_mask = np.zeros((self.resolution[1], self.resolution[0]), np.uint8)
		self.right_mask = np.zeros((self.resolution[1], self.resolution[0]), np.uint8)
		self.edge_mask = np.zeros((self.resolution[1], self.resolution[0]), np.uint8)
		for v in range(slices):
			# Left mask
			cv2.rectangle(self.left_mask, (self.blinkers*v*2//slices, 0), (self.blinkers*(v*2+2)//slices, self.resolution[1]-1), (slices-v)*maxOpacity, -1)
			# Right mask
			cv2.rectangle(self.right_mask, (self.resolution[0]-1-self.blinkers*v*2//slices, 0), (self.resolution[0]-1-self.blinkers*(v*2+2)//slices, self.resolution[1]-1), (slices-v)*maxOpacity, -1)
			# Edge mask
			cv2.rectangle(self.edge_mask, (self.blinkers*v//slices, 0), (self.blinkers*(v+1)//slices, self.resolution[1]-1), (slices-v)*maxOpacity, -1)
			cv2.rectangle(self.edge_mask, (self.resolution[0]-1-self.blinkers*v//slices, 0), (self.resolution[0]-1-self.blinkers*(v+1)//slices, self.resolution[1]-1), (slices-v)*maxOpacity, -1)

		
	def analyseImage(self, image):
		# Chop the image into a number of horizontal slices
		slices = np.array_split(image, self.numSlices)

		points = []
		# For each slice, determine the brightest point
		offset = 0
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
	
		if len(points) < self.minPoints:
			print("Too few points - ignoring")
			hasResult = False
			return hasResult, points, 0,0, 0,0
		else:
			# Add a few points where we are, to prevent the line going to extreme angles
			#for p in range(-4,5):
			#	point = (self.resolution[0]//2 + p * 20, self.resolution[1])
			#	points.append(point)
			
			# Alternative - simple average
			vx = sum([p[0] for p in points]) // len(points)
			vy = points[0][1] #len(points)-1][1]

			x0 = self.resolution[0]//2
			y0 = self.resolution[1]
			print(f"av = {(vx, vy)} {(x0,y0)}")
			hasResult = True
		return hasResult, points, vx, vy, x0, y0

	def displayResults(self, original, gray, points, angle, yaw, rate, assessedTopLeft, assessedBottomRight, currentPosition, desiredPosition, analysisTime):
		if self.display and angle != None:
			# Print the time taken
			print(f"Capture & analysis: {analysisTime:.3f}secs")
			# Create an overlayed image
			assessment = original.copy()
			for point in points:
				cv2.circle(assessment, point, 5, (0,0,255), 1)
			# Draw an arrow representing the brightest points
			cv2.arrowedLine(assessment, assessedTopLeft, assessedBottomRight, (255, 255, 0), 2)
			# Draw an angle from where we are to target
			cv2.arrowedLine(assessment, currentPosition, desiredPosition, (0, 255, 0), 3)
			# Overlay the angle calculated
			np.set_printoptions(precision=2)
			cv2.putText(assessment, f"{yaw:.2f}deg => {angle:+.2f}deg", (5, self.resolution[1]-4), cv2.FONT_HERSHEY_DUPLEX, 0.4, (0, 255, 0))
			cv2.putText(assessment, f"{rate:.0f}fps", (self.resolution[0]-40, self.resolution[1]-4), cv2.FONT_HERSHEY_DUPLEX, 0.4, (0, 255, 0))
			cv2.imshow(f"assessed direction", assessment)
			if self.displayGrayscale:
				cv2.imshow(f"grey", gray)
			
			if self.saveFile:
				# Write the next frame into the file
				if self.saveRaw:
					self.captureFile.write(original)
				else:
					self.captureFile.write(assessment)

		if angle != None:
			print(f"Assessed angle: {angle:.1f}")

	def applyDirectionHint(self, image):
		voiceCommand = self.voice.findLastSpokenWord(['left','right','go', 'fast', 'any'])
		print(f"voiceCommand: {voiceCommand}")
		if voiceCommand == 'right':
			self.lastMask = self.left_mask
		elif voiceCommand == 'left':
			self.lastMask = self.right_mask
		elif voiceCommand == 'go':
			self.lastMask = self.edge_mask
		elif voiceCommand == 'any':
			self.lastMask = None
		else:
			# No change
			pass
			
		if self.lastMask is not None:
			image = cv2.add(self.lastMask, image)
		return image

	def captureAndAssess(self):
		# File capture
		if self.filename != None:
			print(f"Saving to file: {self.filename}")
			# Define the codec and create VideoWriter object.
			self.captureFile = cv2.VideoWriter(self.filename, cv2.VideoWriter_fourcc(*'mp4v'), self.framerate, (self.resolution[0],self.resolution[1]))
			
		# Start timer, so we know how long things took
		startTime = cv2.getTickCount()
		rateStartTime = startTime
		
		rate = 10.0
		angle = None
		count = 0
		currentPosition = None
		desiredPosition = None
		self.lastMask = None
		
		while True:
			count += 1
			
			# Get the current yaw value
			self.sensors.process()
			yaw = self.yaw.getValue()
			
			# grab the raw NumPy array representing the image, then initialize the timestamp
			# and occupied/unoccupied text
			ret, original = self.cap.read()

			# Convert to greyscale and apply a Gaussian blur to the image in order 
			# to make more robust against noise and reflections
			gray = cv2.cvtColor(original.copy(), cv2.COLOR_BGR2GRAY)
			
			# Apply blinkers mask based on current command
			gray = self.applyDirectionHint(gray)
			
			# Quick blur
			gray = cv2.blur(gray, (self.radius, self.radius))

			# Analyse the image
			hasResult, points, vx, vy, x0, y0 = self.analyseImage(gray)
			if hasResult:
				currentPosition = (self.resolution[0]//2, self.resolution[1])
				desiredPosition = (int((vx-self.resolution[0]//2)*self.targetLookaheadRatio+self.resolution[0]//2), int(self.resolution[1]*(1-self.targetLookaheadRatio)))
				angle = np.arctan((currentPosition[0]-desiredPosition[0])/(currentPosition[1]-desiredPosition[1])) * 180.0/3.14159

			# Overall capture/analysis time
			endTime = cv2.getTickCount()
			analysisTime = (endTime - startTime) / cv2.getTickFrequency()

			if hasResult:	
				# Share the results
				yawAngle = yaw + angle 
				if yawAngle > 180.0:
					yawAngle -= 360.0
				elif yawAngle < -180.0:
					yawAngle += 360.0
				self.results.shareResults(startTime, analysisTime, angle, yawAngle, ((vx, vy), (x0, y0)), points)
			elif angle != None:
				# Ajust angle based on last successful analysis for display only
				angle += (lastYaw - yaw)
				if angle > 180.0:
					angle -= 360.0
				elif angle < -180.0:
					angle += 360.0
			lastYaw = yaw
				
			# display the results
			self.displayResults(original, gray, points, angle, yaw, rate, (x0, y0), (vx, vy), currentPosition, desiredPosition, analysisTime)
			
			# stats
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

