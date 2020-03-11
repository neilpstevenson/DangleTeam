from __future__ import print_function
import cv2 as cv
import numpy as np
import argparse
from interfaces.Config import Config

# Get the last known config
config = Config("calibrationDistance.json")
nearest = config.get("distance.analysis.nearest", 20)
horizon = config.get("distance.analysis.horizon", 300)
#cameraHeight = config.get("distance.analysis.cameraHeight", 170)
cameraF = config.get("distance.analysis.camera_f", 1.4)

max_value_horizon = 640
window_capture_name = 'Video Capture'
window_detection_name = 'Calibration'
nearest_name = 'nearest'
horizon_name = 'horizon'

def on_nearest_trackbar(val):
    global nearest_name
    global nearest
    nearest = val
    cv.setTrackbarPos(nearest_name, window_detection_name, nearest)
def on_horizon_trackbar(val):
    global horizon
    global horizon_name
    global max_value_horizon
    horizon = val
    horizon = min(horizon, max_value_horizon-1)
    cv.setTrackbarPos(horizon_name, window_detection_name, horizon)
    
parser = argparse.ArgumentParser(description='Distinace calibration tool')
parser.add_argument('--camera', help='Camera divide number.', default=0, type=int)
args = parser.parse_args()
cap = cv.VideoCapture(args.camera)
cv.namedWindow(window_detection_name)
cv.createTrackbar(nearest_name, window_detection_name , nearest, 500, on_nearest_trackbar)
cv.createTrackbar(horizon_name, window_detection_name , horizon, max_value_horizon, on_horizon_trackbar)


while True:
    
    ret, frame = cap.read()
    if frame is None:
        break
        
    frame_annotated = frame.copy()

    
    #effectiveNearestPont = np.sqrt(cameraHeight*cameraHeight + nearest*nearest)
    
    # Draw the graticule
    for height in range(0, horizon, 30):
        calc_dist = ((((horizon-1) / ((horizon - height))) - 1) * cameraF + 1) * nearest#effectiveNearestPont
        #calc_dist = (np.log2(calc_dist) + 1) * nearest
        # Compensate for heigh of camera
        #calc_dist = calc_dist * cameraF + nearest
        #calc_dist = np.sqrt(calc_dist*calc_dist - cameraHeight*cameraHeight)
        cv.line(frame_annotated, (300,frame.shape[0]-height-1), (320,frame.shape[0]-height-1), (0,0,0), 2)
        cv.putText(frame_annotated, f"{calc_dist:.0f}mm", (330,frame.shape[0]-height), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0))
    cv.line(frame_annotated, (300,frame.shape[0]-horizon-1), (420,frame.shape[0]-horizon-1), (0,0,0), 2)
    cv.putText(frame_annotated, f"inf", (430,frame.shape[0]-horizon), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0))
   
    #cv.imshow(window_capture_name, frame)
    cv.imshow(window_detection_name, frame_annotated)
    
    key = cv.waitKey(30)
    if key == ord('s'):
        config.set("distance.analysis.camera_f", cameraF)
        config.set("distance.analysis.nearest", nearest)
        config.set("distance.analysis.horizon", horizon)
        config.save()
        # flash to confirm
        cv.putText(frame_annotated, f"Saved", (frame_annotated.shape[0]*2//5, frame_annotated.shape[1]*2//6), cv.FONT_HERSHEY_DUPLEX, 2, (255, 255, 255))
        cv.imshow(window_detection_name, frame_annotated)
        key = cv.waitKey(250)
        
    if key == ord('q') or key == 27:
        break
