import imutils
import numpy as np
import cv2

''' This class processes an OpenCV image and caclulates an estimated
	distance and bearing for the larges colour block found
'''
class ImageColouredRegionAnalyser:
	def __init__(self, name, colourRange, erodeCount, dilateCount, cannySize, minSize, cameraCalibration):
		self.name = name
		self.colourRange = colourRange
		self.minWidth, self.minHeight = minSize
		self.erodeCount = erodeCount
		self.dilateCount = dilateCount
		self.cannySize = cannySize
		# Camera calibration
		self.cameraNearestVisiblePixels, self.cameraFurthestVisiblePixel, self.cameraNearestVisibleDistance, self.cameraHeightDistance, self.angleAdjustment = cameraCalibration
		self.cameraHeightAdjustment = np.sqrt(self.cameraHeightDistance*self.cameraHeightDistance + self.cameraNearestVisibleDistance*self.cameraNearestVisibleDistance) / self.cameraNearestVisibleDistance
		# Results
		self.maskedImage = None
		self.hasResult = False
		self.contours = None
		self.largestCenter = None
		self.largestBoundingRect = None
		self.largestContours = None
		pass
	
	'''
	This takes a raw HSV image and generates the necessary base
	mask and contour features used by the rest of the analysis
	'''
	def processImage(self, image):
		if type(self.colourRange) is list:
			# Apply multiple mask colour ranges
			mask = None
			for cols in self.colourRange:
				if mask is None:
					mask = cv2.inRange(image, cols[0], cols[1])
				else:
					mask = cv2.bitwise_or(mask, cv2.inRange(image, cols[0], cols[1]))
		else:
			# Simple mask
			mask = cv2.inRange(image, self.colourRange[0], self.colourRange[1])
			
		mask = cv2.erode(mask, None, iterations = self.erodeCount)
		self.maskedImage = cv2.dilate(mask, None, iterations = self.dilateCount)
		if self.cannySize is not None:
			self.maskedImage = cv2.Canny(self.maskedImage, self.cannySize[0], self.cannySize[1])

		# find contours in the mask and initialize the current
		# (x, y) center of the ball
		self.contours = cv2.findContours(self.maskedImage, cv2.RETR_EXTERNAL,
			cv2.CHAIN_APPROX_SIMPLE)
		self.contours = imutils.grab_contours(self.contours)
		
		# only proceed if at least one contour was found
		self.hasResult = False
		if len(self.contours) > 0:
			# find the largest contour in the mask, 
			c = max(self.contours, key=cv2.contourArea)
			# find the best enclosing rectangle
			#x, y, w, h 
			self.largestBoundingRect = cv2.boundingRect(c)
			M = cv2.moments(c)
			if M["m00"] != 0.0 and M["m00"] != 0.0:
				self.largestCenter = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
				self.largestContours = [c]
				
				# only proceed if the radius meets a minimum size
				if self.largestBoundingRect[2] >= self.minWidth and self.largestBoundingRect[3] >= self.minHeight:
					self.hasResult = True
	
	'''
	Calculate and return an estimated distance, bearing for the largest area identified
	Returns None if none identified
	'''		
	def calculateDistanceBearing(self):
		if self.hasResult:
			# Calculate the angle from the bottom centre to the lowest point
			x = (self.largestBoundingRect[0] + self.largestBoundingRect[2]//2)
			y = (self.largestBoundingRect[1] + self.largestBoundingRect[3] - 1)
			ourPosition = (self.maskedImage.shape[1]//2, self.maskedImage.shape[0] + self.cameraNearestVisiblePixels)
			angle_rads = np.arctan((ourPosition[0]-x)/(ourPosition[1]-y)) * self.angleAdjustment
			angle = angle_rads * 180.0/3.14159
			#print(f"x:{x}, y:{y}, ourPosition:{ourPosition}, angle:{angle}")
			# Distance approximation
			dist_recip = self.cameraFurthestVisiblePixel - (self.maskedImage.shape[0] - y)
			if dist_recip > 0:
				distance = ((((self.cameraFurthestVisiblePixel-1) / dist_recip) - 1) * self.cameraHeightAdjustment + 1) * self.cameraNearestVisibleDistance
				# Convert to actual distance
				distance = distance / np.cos(angle_rads)
			else:
				distance = 999 # to infinity and beyond!
				
			return distance, angle

		return None
