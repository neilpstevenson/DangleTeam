from __future__ import print_function
import cv2 as cv
import numpy as np
import argparse
from interfaces.Config import Config

# Get the last known config
config = Config("calibrationDistance.json")
nearest = config.get("distance.analysis.nearest", 130)
horizon = config.get("distance.analysis.horizon", 500)
cameraHeight = config.get("distance.analysis.cameraHeight", 170)
#cameraF = config.get("distance.analysis.camera_f", 1.4)

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

    
    cameraF = np.sqrt(cameraHeight*cameraHeight + nearest*nearest) / nearest
    centreX = frame.shape[1] // 2
    # Draw the graticule
    for y in range(0, horizon, 30):
        #calc_dist = ((((horizon-1) / ((horizon - y))) - 1) * cameraF + 1) * nearest#effectiveNearestPont
        calc_dist = (horizon-1)
        calc_dist /= (horizon - y)
        calc_dist -= 1
        calc_dist *= cameraF
        calc_dist += 1
        calc_dist *= nearest
        #y2 = horizon - (horizon-1) / (((calc_dist / nearest - 1) / cameraF) + 1)
        #print(f"({y} => {y2}")
        cv.line(frame_annotated, (centreX,frame.shape[0]-y-1), (centreX+20,frame.shape[0]-y-1), (0,0,0), 1)
        cv.putText(frame_annotated, f"{calc_dist:.0f}mm", (centreX+30,frame.shape[0]-y), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0))
    # Also based on a fixed set of points
    for dist in (250.0,300.0,400.0,500.0,750.0,1000.0,1250.0,1500.0,2000.0,3000.0):
        if dist > nearest and nearest > 0 and horizon > 0:
            #print(f"{horizon} {dist} {nearest} {cameraF}")
            y = int(horizon - (horizon-1) / (((dist / nearest - 1) / cameraF) + 1))
            cv.line(frame_annotated, (centreX-20,frame.shape[0]-y-1), (centreX,frame.shape[0]-y-1), (0,0,0), 1)
            cv.putText(frame_annotated, f"{dist:.0f}mm", (centreX-100,frame.shape[0]-y), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0))
    cv.line(frame_annotated, (centreX-100,frame.shape[0]-horizon-1), (centreX+100,frame.shape[0]-horizon-1), (0,0,0), 2)
    cv.putText(frame_annotated, f"inf", (centreX+120,frame.shape[0]-horizon), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0))

        
    #cv.imshow(window_capture_name, frame)
    cv.imshow(window_detection_name, frame_annotated)
    
    key = cv.waitKey(30)
    if key == ord('s'):
        config.set("distance.analysis.nearest", nearest)
        config.set("distance.analysis.horizon", horizon)
        config.set("distance.analysis.cameraHeight", cameraHeight)
        config.save()
        # flash to confirm
        cv.putText(frame_annotated, f"Saved", (frame_annotated.shape[0]*2//5, frame_annotated.shape[1]*2//6), cv.FONT_HERSHEY_DUPLEX, 2, (255, 255, 255))
        cv.imshow(window_detection_name, frame_annotated)
        key = cv.waitKey(500)
    elif key == ord('m'):
        configM = Config("calibrationMinesweeper.json")
        configM.set("distance.analysis.nearest", nearest)
        configM.set("distance.analysis.horizon", horizon)
        configM.set("distance.analysis.cameraHeight", cameraHeight)
        configM.set("distance.analysis.calibrationResolution", frame_annotated.shape)
        configM.save()
        # flash to confirm
        cv.putText(frame_annotated, f"Saved to Minesweeper", (frame_annotated.shape[0]*1//10, frame_annotated.shape[1]*2//6), cv.FONT_HERSHEY_DUPLEX, 1.5, (255, 255, 255))
        cv.imshow(window_detection_name, frame_annotated)
        key = cv.waitKey(500)
        
    if key == ord('q') or key == 27:
        break
