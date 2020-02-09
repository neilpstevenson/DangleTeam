# USAGE
# python drone.py --video FlightDemo.mp4

# import the necessary packages
import argparse
import imutils
from imutils.video import VideoStream
import cv2

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
args = vars(ap.parse_args())

# load the video
recordedVideo = args.get("video", False)
if recordedVideo:
	camera = cv2.VideoCapture(args["video"])
else:
	camera = VideoStream(src=0).start()

# keep looping
while True:
	# grab the current frame and initialize the status text
	if recordedVideo:
		(grabbed, frame) = camera.read()
		# check to see if we have reached the end of the
		# video
		if not grabbed:
			break
	else:
		frame = camera.read()
		
	status = "No Barrels"

	# convert the frame to grayscale, blur it, and detect edges
	#gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	#blurred = cv2.GaussianBlur(gray, (7, 7), 0)
	#edged = cv2.Canny(blurred, 50, 150)

	blurred = cv2.GaussianBlur(frame, (13, 13), 0)
	hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
	# construct a mask for the color range required, then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	maskRed = cv2.inRange(hsv, (165,94,69), (180,255,255))
	maskRed = cv2.erode(maskRed, None, iterations=2)
	maskRed = cv2.dilate(maskRed, None, iterations=2)
	edgedRed = cv2.Canny(maskRed, 50, 150)
	
	maskGreen = cv2.inRange(hsv, (47,74,114), (61,255,255))
	maskGreen = cv2.erode(maskGreen, None, iterations=2)
	maskGreen = cv2.dilate(maskGreen, None, iterations=2)
	edgedGreen = cv2.Canny(maskGreen, 50, 150)


	# find contours in the edge map
	cntsRed = cv2.findContours(edgedRed.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cntsRed = imutils.grab_contours(cntsRed)
	cntsGreen = cv2.findContours(maskGreen.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cntsGreen = imutils.grab_contours(cntsGreen)
	
	# Overlay everything detected
	#cv2.polylines(frame, cnts,  True, (0, 255, 0), 2, 8)

	# loop over the contours
	counts = [0,0]
	colour = -1
	for lists in cntsRed,cntsGreen:
		colour += 1
		for c in lists:
			# approximate the contour
			peri = cv2.arcLength(c, True)
			approx = cv2.approxPolyDP(c, 0.01 * peri, True)

			# ensure that the approximated contour is "roughly" rectangular
			if len(approx) >= 4 and len(approx) <= 16:
				# compute the bounding box of the approximated contour and
				# use the bounding box to compute the aspect ratio
				(x, y, w, h) = cv2.boundingRect(approx)
				aspectRatio = w / float(h)
				#print(f"at: {(x,y)}, size: {(w,h)}, aspectRatio: {aspectRatio}, approx: {len(approx)}")

				# compute the solidity of the original contour
				area = cv2.contourArea(c)
				hullArea = cv2.contourArea(cv2.convexHull(c))
				solidity = area / float(hullArea)

				# compute whether or not the width and height, solidity, and
				# aspect ratio of the contour falls within appropriate bounds
				keepDims = w > 25 and h > 25
				keepSolidity = solidity > 0.8 #0.9
				#keepAspectRatio = aspectRatio >= 0.8 and aspectRatio <= 1.2
				keepAspectRatio = aspectRatio >= 0.5 and aspectRatio <= 0.8
				print(f"keep: {keepDims}, {keepSolidity}({solidity}), {keepAspectRatio}({aspectRatio})")

				# ensure that the contour passes all our tests
				if keepDims and keepSolidity and keepAspectRatio:
					# draw an outline around the target and update the status
					# text
					cv2.drawContours(frame, [approx], -1, (0, 0, 255), 4)
					counts[colour] += 1
					print(f"at: {(x,y)}, size: {(w,h)}, aspectRatio: {aspectRatio}, approx: {len(approx)}")

					# compute the center of the contour region and draw the
					# crosshairs
					M = cv2.moments(approx)
					(cX, cY) = (int(M["m10"] // M["m00"]), int(M["m01"] // M["m00"]))
					(startX, endX) = (int(cX - (w * 0.15)), int(cX + (w * 0.15)))
					(startY, endY) = (int(cY - (h * 0.15)), int(cY + (h * 0.15)))
					cv2.line(frame, (startX, cY), (endX, cY), (0, 0, 255), 3)
					cv2.line(frame, (cX, startY), (cX, endY), (0, 0, 255), 3)

	if counts[0]+counts[1] > 0:
		status = f"{counts[0]} Red Barrels Detected, {counts[1]} Green"
		
	# draw the status text on the frame
	cv2.putText(frame, status, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
		(0, 0, 255), 2)

	# show the frame and record if a key is pressed
	cv2.imshow("Frame", frame)
	#cv2.imshow("Grey", gray)
	cv2.imshow("EdgedRed", edgedRed)
	cv2.imshow("EdgedGreen", edgedGreen)
	key = cv2.waitKey(1) & 0xFF

	# if the 'q' key is pressed, stop the loop
	if key == ord("q"):
		break

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
