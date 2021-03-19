import imutils
import numpy as np
import cv2

''' This class processes an OpenCV image and caclulates an estimated
	distance and bearing for the larges colour block found
'''
class ImageArucoRecogniser:
	def __init__(self, name, cameraCalibration, focalLength = 520, arucoSize = 100, arucoDictName = cv2.aruco.DICT_4X4_50):
		self.name = name
		self.arucoDict = cv2.aruco.Dictionary_get(arucoDictName)
		self.arucoParams = cv2.aruco.DetectorParameters_create()		
		self.arucoSize = arucoSize
		self.focalLength = focalLength

		# Camera calibration
		self.cameraNearestVisiblePixels, self.cameraFurthestVisiblePixel, self.cameraNearestVisibleDistance, self.cameraHeightDistance, self.angleAdjustment = cameraCalibration
		# Results
		self.hasResult = False
		self.markers  = None
	
	'''
	This takes a raw HSV image and generates the necessary base
	mask and contour features used by the rest of the analysis
	'''
	def processImage(self, image):
		# detect ArUco markers in the input frame
		(corners, ids, rejected) = cv2.aruco.detectMarkers(image, self.arucoDict, parameters=self.arucoParams)
		self.hasResult = len(corners) > 0
		#print(f"ids: {ids}")
		if self.hasResult:
			self.corners = corners
			self.ids = ids.flatten()
			self.imageShape = image.shape
		else:
			self.ids = []
			self.corners = None
			print(f"No markers found")
			
	'''
	Get the Ids of the identified blocks
	'''
	def getIds(self):
		return self.ids
		
	'''
	Calculate and return an estimated distance, bearing for the largest area identified
	Returns None if none identified
	'''		
	def calculateDistanceBearing(self, id):
		# Find the ID index
		index = np.where(self.ids == id)
		if len(index) < 1 or len(index[0]) < 1:
			return None
			
		# extract the marker corners (which are always returned
		# in top-left, top-right, bottom-right, and bottom-left
		# order)
		corners = self.corners[index[0][0]].reshape((4, 2)).astype(int)
		(topLeft, topRight, bottomRight, bottomLeft) = corners
		
		# Centre
		self.largestCenter = (int((topLeft[0] + bottomRight[0]) / 2.0), int((topLeft[1] + bottomRight[1]) / 2.0))
		
		# Assume roughly square pixels, calulate the size using the bottom edge of the marker
		#size = np.sqrt(((bottomRight[0] - bottomLeft[0])**2.0) + ((bottomRight[1] - bottomLeft[1])**2.0))
		
		# Calculate the angle from the bottom centre to the lowest point
		x = int((bottomLeft[0] + bottomRight[0]) / 2.0)
		y = int((bottomLeft[1] + bottomRight[1]) / 2.0)
		ourPosition = (self.imageShape[1]//2, self.imageShape[0] + self.cameraNearestVisiblePixels)
		angle_rads = np.arctan((ourPosition[0]-x)/(ourPosition[1]-y)) * self.angleAdjustment
		angle = angle_rads * 180.0/3.14159
		#print(f"{id} at x:{x}, y:{y}, ourPosition:{ourPosition}, angle:{angle}")
		
		# Distance approximation
		distance = self.arucoSize * self.focalLength / np.sqrt((bottomLeft[0]-bottomRight[0])**2 + (bottomLeft[1]-bottomRight[1])**2)# + self.cameraNearestVisibleDistance
		# Adjust for camera height
		distance = np.sqrt(distance**2 - self.cameraHeightDistance**2)
		# Adjust for distance to axis of rotation
		distance += 60
		# Adjust for angle
		distance = distance / np.cos(angle_rads)
		print(f"{id}: distance:{distance:.0f}mm, angle:{angle:.1f}deg")
		return corners, distance, angle
