from __future__ import print_function
import cv2 as cv
import argparse
from interfaces.Config import Config

# Get the last known config
config = Config("calibrationDistance.json")
nearest = config.get("distance.analysis.nearest", 20)
horizon = config.get("distance.analysis.horizon", 300)

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
cv.createTrackbar(nearest_name, window_detection_name , nearest, 200, on_nearest_trackbar)
cv.createTrackbar(horizon_name, window_detection_name , horizon, max_value_horizon, on_horizon_trackbar)

while True:
    
    ret, frame = cap.read()
    if frame is None:
        break
        
    frame_annotated = frame.copy()
    
    # Draw the graticule
    for height in range(0, horizon, 30):
        calc_dist = horizon/(horizon - height) * nearest
        cv.line(frame_annotated, (300,frame.shape[0]-height-1), (320,frame.shape[0]-height-1), (255,255,255), 2)
        cv.putText(frame_annotated, f"{calc_dist:.0f}mm", (330,frame.shape[0]-height), cv.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255))
    cv.line(frame_annotated, (300,frame.shape[0]-horizon-1), (420,frame.shape[0]-horizon-1), (255,255,255), 2)
    cv.putText(frame_annotated, f"inf", (430,frame.shape[0]-horizon), cv.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255))
   
    #cv.imshow(window_capture_name, frame)
    cv.imshow(window_detection_name, frame_annotated)
    
    key = cv.waitKey(30)
    if key == ord('s'):
        config.save()
        # flash to confirm
        cv.putText(frame_annotated, f"Saved", (frame_masked.shape[0]*2//5, frame_masked.shape[1]*2//6), cv.FONT_HERSHEY_DUPLEX, 2, (255, 255, 255))
        cv.imshow(window_detection_name, frame_masked)
        key = cv.waitKey(250)
        
    if key == ord('q') or key == 27:
        break
