import imutils
import numpy as np
import cv2

''' This class processes an OpenCV image and caclulates an estimated
	distance and bearing for the larges colour block found
'''
class ImageArucoRecogniser:
	def __init__(self, name, cameraCalibration, arucoDictName = cv2.aruco.DICT_4X4_50):
		self.name = name
		self.arucoDict = cv2.aruco.Dictionary_get(arucoDictName)
		self.arucoParams = cv2.aruco.DetectorParameters_create()		
		
		# Camera calibration
		self.cameraNearestVisiblePixels, self.cameraFurthestVisiblePixel, self.cameraNearestVisibleDistance, self.cameraHeightDistance, self.angleAdjustment = cameraCalibration
		self.cameraHeightAdjustment = np.sqrt(self.cameraHeightDistance*self.cameraHeightDistance + self.cameraNearestVisibleDistance*self.cameraNearestVisibleDistance) / self.cameraNearestVisibleDistance
		# Results
		self.hasResult = False
		self.markers  = None
		self.largestContours = None
	
	'''
	This takes a raw HSV image and generates the necessary base
	mask and contour features used by the rest of the analysis
	'''
	def processImage(self, image):
		# detect ArUco markers in the input frame
		(corners, ids, rejected) = cv2.aruco.detectMarkers(image, self.arucoDict, parameters=self.arucoParams)
		self.hasResult = len(corners) > 0
		print(f"ids: {ids}")
		if self.hasResult:
			self.markers = zip(corners, ids.flatten())
			self.imageShape = image.shape
	
	'''
	Calculate and return an estimated distance, bearing for the largest area identified
	Returns None if none identified
	'''		
	def calculateDistanceBearing(self, id):
		if self.hasResult:
			# loop over the detected ArUCo corners
			for (markerCorner, markerID) in self.markers:
				# extract the marker corners (which are always returned
				# in top-left, top-right, bottom-right, and bottom-left
				# order)
				corners = markerCorner.reshape((4, 2)).astype(int)
				(topLeft, topRight, bottomRight, bottomLeft) = corners
				self.largestContours = corners
				
				# convert each of the (x, y)-coordinate pairs to integers
				topRight = (int(topRight[0]), int(topRight[1]))
				bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
				bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
				topLeft = (int(topLeft[0]), int(topLeft[1]))
				#Centre
				self.largestCenter = (int((topLeft[0] + bottomRight[0]) / 2.0), int((topLeft[1] + bottomRight[1]) / 2.0))
				# Assume roughly quare pixels, calulate the size using the bottom edge of the marker
				size = np.sqrt(((bottomRight[0] - bottomLeft[0])**2.0) + ((bottomRight[1] - bottomLeft[1])**2.0))
				
				#print(f"{markerID}: {corners}, size: {size}")

				# draw the bounding box of the ArUCo detection
				#cv2.line(frame, topLeft, topRight, (0, 255, 0), 2)
				#cv2.line(frame, topRight, bottomRight, (0, 255, 0), 2)
				#cv2.line(frame, bottomRight, bottomLeft, (0, 255, 0), 2)
				#cv2.line(frame, bottomLeft, topLeft, (0, 255, 0), 2)
				#
				## compute and draw the center (x, y)-coordinates of the
				## ArUco marker
				#cX = int((topLeft[0] + bottomRight[0]) / 2.0)
				#cY = int((topLeft[1] + bottomRight[1]) / 2.0)
				#cv2.circle(frame, (cX, cY), 4, (0, 0, 255), -1)
				#
				## draw the ArUco marker ID on the frame
				#cv2.putText(frame, str(markerID),
				#	(topLeft[0], topLeft[1] - 15),
				#	cv2.FONT_HERSHEY_SIMPLEX,
				#	0.5, (0, 255, 0), 2)
					
				# Calculate the angle from the bottom centre to the lowest point
				x = int((bottomLeft[0] + bottomRight[0]) / 2.0)
				y = int((bottomLeft[1] + bottomRight[1]) / 2.0)
				ourPosition = (self.imageShape[1]//2, self.imageShape[0] + self.cameraNearestVisiblePixels)
				angle_rads = np.arctan((ourPosition[0]-x)/(ourPosition[1]-y)) * self.angleAdjustment
				angle = angle_rads * 180.0/3.14159
				print(f"{markerID} at x:{x}, y:{y}, ourPosition:{ourPosition}, angle:{angle}")
				# Distance approximation
				ACURO_SIZE = 100 # mm
				FocalLength = 520
				distance = ACURO_SIZE * FocalLength / np.sqrt((bottomLeft[0]-bottomRight[0])**2 + (bottomLeft[1]-bottomRight[1])**2)# + self.cameraNearestVisibleDistance
				#dist_recip = self.cameraFurthestVisiblePixel - (self.imageShape[0] - y)
				#if dist_recip > 0:
				#	distance = ((((self.cameraFurthestVisiblePixel-1) / dist_recip) - 1) * self.cameraHeightAdjustment + 1) * self.cameraNearestVisibleDistance
				#	# Convert to actual distance
				#	distance = distance / np.cos(angle_rads)
				#else:
				#	distance = 999 # to infinity and beyond!
				# Adjust for camera height
				distance = np.sqrt(distance**2 - self.cameraHeightDistance**2)
				# Adjust for distance to axis of rotation
				distance += 60
				# Adjust for angle
				distance = distance / np.cos(angle_rads)
				print(f"dis:{distance}, angle:{angle}")
				return corners, distance, angle

		
		
		#if self.hasResult:
		#	# Calculate the angle from the bottom centre to the lowest point
		#	x = (self.largestBoundingRect[0] + self.largestBoundingRect[2]//2)
		#	y = (self.largestBoundingRect[1] + self.largestBoundingRect[3] - 1)
		#	ourPosition = (self.maskedImage.shape[1]//2, self.maskedImage.shape[0] + self.cameraNearestVisiblePixels)
		#	angle_rads = np.arctan((ourPosition[0]-x)/(ourPosition[1]-y)) * self.angleAdjustment
		#	angle = angle_rads * 180.0/3.14159
		#	#print(f"x:{x}, y:{y}, ourPosition:{ourPosition}, angle:{angle}")
		#	# Distance approximation
		#	dist_recip = self.cameraFurthestVisiblePixel - (self.maskedImage.shape[0] - y)
		#	if dist_recip > 0:
		#		distance = ((((self.cameraFurthestVisiblePixel-1) / dist_recip) - 1) * self.cameraHeightAdjustment + 1) * self.cameraNearestVisibleDistance
		#		# Convert to actual distance
		#		distance = distance / np.cos(angle_rads)
		#	else:
		#		distance = 999 # to infinity and beyond!
		#		
		#	return distance, angle

		return None
