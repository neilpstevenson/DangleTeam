import time
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera

resolution = (1280,720) #(320,240)
camera = PiCamera(resolution=resolution, framerate=90)
#camera.resolution = resolution
#camera.framerate = 90 #30
rawCapture = PiRGBArray(camera, size=resolution)
		
startTime = cv2.getTickCount()
rateStartTime = startTime
rate = 10.0
count = 0

stream = camera.capture_continuous(rawCapture, format="bgr", use_video_port=True) #, resize = resolution)
time.sleep(2.0)
for frame in stream:
	#original = frame.array
	#exposure = camera.exposure_speed
	#ag = 0#camera.analog_gain
	#dg = 0#camera.digital_gain
	rawCapture.truncate(0)
	count += 1

	#time.sleep(0.023)
	#cv2.imshow(f"live", original)
					
	if count % 10 == 0:
		endTime = cv2.getTickCount()
		overalltime = (endTime - startTime) / cv2.getTickFrequency()
		rate = 	10.0 / ((endTime - rateStartTime) / cv2.getTickFrequency())
		rateStartTime = endTime
	
		print(f"Overall time:   {overalltime:.3f}secs, {rate:.1f}fps")
		startTime = endTime

	#cv2.waitKey(1)
