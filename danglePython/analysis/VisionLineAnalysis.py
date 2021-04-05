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
		self.maxAngle = 25.0	# Cap any calulated angle to this
		
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
		#slices = np.array_split(image, self.numSlices)
		total_height = len(image)
		total_width = len(image[0])
		slice_size = total_height // self.numSlices
		
		points = []
		# For each slice, determine the brightest point
		#offset = 0
		for bit in range(self.ignoreTopSlices, self.numSlices):
			slice_top = bit * slice_size
			slice_bottom = (bit+1) * slice_size - 1
			(minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(image[slice_top:slice_bottom,:])
			#offset += len(slices[bit])
			
			# Ignore any at extreme edges, as these are likely to be contrast-related artefacts
			if self.blackLine:
				if minVal > self.threshold or minLoc[0] < self.radius or minLoc[0] > (total_width - self.radius):
					point = (minLoc[0],minLoc[1]+slice_top)
					print(f"Ignoring point: {point}, min value {minVal}")
					pass
				else:
					point = (minLoc[0],minLoc[1]+slice_top)
					print(f"Using point: {point}, value {minVal}")
					points.append(point)
			else:
				if maxVal < self.threshold or minLoc[0] < self.radius or minLoc[0] > (total_width - self.radius):
					point = (minLoc[0],minLoc[1]+slice_top)
					print(f"Ignoring point: {point}, max value {maxVal}")
					pass
				else:
					point = (maxLoc[0],maxLoc[1]+slice_top)
					print(f"Using point: {point}, value {maxVal}")
					points.append(point)
					
		# And the same as vertical slices
		#if self.voiceCommand == "left":
		#	first_slice = 0
		#	last_slice = self.numSlices//2
		#elif self.voiceCommand == "right":
		#	first_slice = self.numSlices//2
		#	last_slice = self.numSlices
		#elif self.voiceCommand == "any":
		first_slice = 0
		last_slice = self.numSlices
		#else:
		#	first_slice = 0
		#	last_slice = 0
		slice_v_size = total_width // self.numSlices
		slice_top = self.ignoreTopSlices * slice_v_size
		slice_width = total_width // self.numSlices
		slice_bottom = (self.numSlices - self.ignoreTopSlices) * slice_size
		#print(f"slice_v_size:{slice_v_size}, slice_bottom:{slice_bottom}, {self.numSlices}-{self.ignoreTopSlices}")
		for bit in range(first_slice, last_slice):
			slice_left = bit * slice_width
			slice_right = (bit+1) * slice_width - 1
			(minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(image[slice_top:, slice_left:slice_right])
			#offset += len(slices[bit])
			
			# Ignore any at extreme edges, as these are likely to be contrast-related artefacts
			if self.blackLine:
				#print(f"minLoc: {minLoc}, min y: {slice_bottom - 2*self.radius}")
				if minVal > self.threshold or minLoc[1] > (slice_bottom - self.radius):
					point = (minLoc[0] + slice_left, minLoc[1]+slice_top)
					print(f"Ignoring V point: {point}, min value {minVal}")
					pass
				else:
					point = (minLoc[0] + slice_left, minLoc[1]+slice_top)
					print(f"Using V point: {point}, value {minVal}")
					points.append(point)
			else:
				if maxVal < self.threshold or minLoc[1] > (slice_bottom - self.radius):
					point = (minLoc[0] + slice_left, minLoc[1]+slice_top)
					print(f"Ignoring V point: {point}, max value {maxVal}")
					pass
				else:
					point = (maxLoc[0] + slice_left, maxLoc[1]+slice_top)
					print(f"Using point: {point}, value {maxVal}")
					points.append(point)
	
		if len(points) < self.minPoints:
			print("Too few points - ignoring")
			hasResult = False
			return hasResult, points, 0,0, 0,0
		else:
			# Sort the point top left to right
			point_lr = sorted(points, key=lambda k: k[0])
			#print(f"point_lr: {point_lr}")
			if self.voiceCommand == "left":
				first_slice = 0
				last_slice = len(point_lr)//3
			elif self.voiceCommand == "right":
				first_slice = len(point_lr)*2//3
				last_slice = len(point_lr)
			elif self.voiceCommand == "ahead" or self.voiceCommand == "stop":
				# centre region of interest
				first_slice = len(point_lr)//3
				last_slice = len(point_lr)*2//3
			else:
				# use full image
				first_slice = 0
				last_slice = len(point_lr)
			points = point_lr[first_slice:last_slice]
			#print(f"points: {points}")

			# Now discard the edge points that aren't in our desired direction
			
			# Add a few points where we are, to prevent the line going to extreme angles
			#for p in range(-4,5):
			#	point = (self.resolution[0]//2 + p * 20, self.resolution[1])
			#	points.append(point)
			
			# Alternative - simple average
			vx = sum([p[0] for p in points]) // len(points)
			vy = min(points, key=lambda k: k[1])[1] # points[0][1] #len(points)-1][1]

			x0 = self.resolution[0]//2
			y0 = self.resolution[1]
			print(f"av = {(vx, vy)} {(x0,y0)}")
			hasResult = True
		return hasResult, points, vx, vy, x0, y0

	def displayResults(self, original, gray, points, hasResult, angle, yaw, rate, assessedTopLeft, assessedBottomRight, analysisTime):
		currentPosition = (self.resolution[0]//2, self.resolution[1])
		if self.display:
			# Create an overlayed image
			assessment = original.copy()

			if angle != None:
				desiredPosition =  (int(currentPosition[0] - self.resolution[0]*np.sin(angle*3.142/180)//2), \
									int(self.resolution[1] - self.resolution[1]*0.75*np.cos(angle*3.142/180)) )
				# Print the time taken
				print(f"Capture & analysis: {analysisTime:.3f}secs {desiredPosition}")
				# Show the points
				for point in points:
					cv2.circle(assessment, point, 5, (0,0,255), 1)
				# Draw an arrow representing the brightest points
				cv2.arrowedLine(assessment, assessedTopLeft, assessedBottomRight, (255, 255, 0), 2)
				# Draw an angle from where we are to target
				if hasResult:
					cv2.arrowedLine(assessment, currentPosition, desiredPosition, (0, 255, 0), 3)
				else:
					cv2.arrowedLine(assessment, currentPosition, desiredPosition, (200, 200, 200), 3)
					
				# Overlay the angle calculated
				np.set_printoptions(precision=2)
				cv2.putText(assessment, f"{yaw:.1f}deg {angle:+.1f}deg", (5, self.resolution[1]-4), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 25, 0))
				cv2.putText(assessment, f"{rate:.0f}fps", (self.resolution[0]-40, self.resolution[1]-4), cv2.FONT_HERSHEY_DUPLEX, 0.4, (0, 25, 0))
				cv2.putText(assessment, self.voiceCommand, (self.resolution[0]//2 + 45, self.resolution[1]-4), cv2.FONT_HERSHEY_DUPLEX, 0.4, (0, 25, 0))
			
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
		voiceCommand = self.voice.findLastSpokenWord(['left','right','go', 'fast', 'ahead', 'head', 'stop'])
		print(f"voiceCommand: {voiceCommand}")
		if voiceCommand == 'right':
			#self.lastMask = self.left_mask
			self.voiceCommand = voiceCommand
		elif voiceCommand == 'left':
			#self.lastMask = self.right_mask
			self.voiceCommand = voiceCommand
		elif voiceCommand == 'go' or voiceCommand == 'fast':
			#self.lastMask = self.edge_mask
			self.voiceCommand = voiceCommand
		elif voiceCommand == 'ahead' or  voiceCommand == 'head':
			#self.lastMask = None
			self.voiceCommand = 'ahead'
		elif voiceCommand == 'stop':
			#self.lastMask = None
			self.voiceCommand = voiceCommand
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
		desiredPosition = None
		self.lastMask = None
		self.voiceCommand = "ready"

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

			# Overall capture/analysis time
			endTime = cv2.getTickCount()
			analysisTime = (endTime - startTime) / cv2.getTickFrequency()

			if hasResult:	
				# Share the results
				currentPosition = (self.resolution[0]//2, self.resolution[1])
				desiredPosition = (int((vx-self.resolution[0]//2)*self.targetLookaheadRatio+self.resolution[0]//2), vy) #int(self.resolution[1]*(1-self.targetLookaheadRatio)))
				angle = np.arctan((currentPosition[0]-desiredPosition[0])/(currentPosition[1]-desiredPosition[1])) * 180.0/3.14159
				# cap max angle retuned
				angle /= 2.0
				if angle > self.maxAngle:
					yawAngle = yaw + self.maxAngle 
				elif angle < -self.maxAngle:
					yawAngle = yaw - self.maxAngle
				else:
					yawAngle = yaw + angle 
				if yawAngle > 180.0:
					yawAngle -= 360.0
				elif yawAngle < -180.0:
					yawAngle += 360.0
				self.results.shareResults(startTime, analysisTime, angle, yawAngle, ((vx, vy), (x0, y0)), points)
			elif angle != None:
				# Ajust angle based on last successful analysis for display only
				#angle += (lastYaw - yaw)
				#if angle > 180.0:
				#	angle -= 360.0
				#elif angle < -180.0:
				#	angle += 360.0
				# Repeat using the last known angle, hopefuly this will re-gain image analysis if we keep rotating
				if angle > self.maxAngle:
					yawAngle = yaw + self.maxAngle 
				elif angle < -self.maxAngle:
					yawAngle = yaw - self.maxAngle
				else:
					yawAngle = yaw + angle 
				if yawAngle > 180.0:
					yawAngle -= 360.0
				elif yawAngle < -180.0:
					yawAngle += 360.0
				self.results.shareResults(startTime, analysisTime, angle, yawAngle, ((vx, vy), (x0, y0)), points)
			lastYaw = yaw
				
			# display the results
			self.displayResults(original, gray, points, hasResult, angle, yaw, rate, (x0, y0), (vx, vy), analysisTime)
			
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

