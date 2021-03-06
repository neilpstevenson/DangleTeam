from __future__ import print_function
import cv2 as cv
import argparse
from interfaces.Config import Config

# Get the last known config
config = Config("calibrationHSV.json")
low_H, low_S, low_V = config.get("minesweeper.analysis.colourTargetLowerTest", [165,94,69])
high_H, high_S, high_V = config.get("minesweeper.analysis.colourTargetUpperTest", [180,255,255])

max_value = 255
max_value_H = 360//2
#low_H = 0
#low_S = 0
#low_V = 0
#high_H = max_value_H
#high_S = max_value
#high_V = max_value
window_capture_name = 'Video Capture'
window_detection_name = 'Object Detection'
low_H_name = 'Low H'
low_S_name = 'Low S'
low_V_name = 'Low V'
high_H_name = 'High H'
high_S_name = 'High S'
high_V_name = 'High V'
def on_low_H_thresh_trackbar(val):
    global low_H
    global high_H
    low_H = val
    low_H = min(high_H-1, low_H)
    cv.setTrackbarPos(low_H_name, window_detection_name, low_H)
def on_high_H_thresh_trackbar(val):
    global low_H
    global high_H
    high_H = val
    high_H = max(high_H, low_H+1)
    cv.setTrackbarPos(high_H_name, window_detection_name, high_H)
def on_low_S_thresh_trackbar(val):
    global low_S
    global high_S
    low_S = val
    low_S = min(high_S-1, low_S)
    cv.setTrackbarPos(low_S_name, window_detection_name, low_S)
def on_high_S_thresh_trackbar(val):
    global low_S
    global high_S
    high_S = val
    high_S = max(high_S, low_S+1)
    cv.setTrackbarPos(high_S_name, window_detection_name, high_S)
def on_low_V_thresh_trackbar(val):
    global low_V
    global high_V
    low_V = val
    low_V = min(high_V-1, low_V)
    cv.setTrackbarPos(low_V_name, window_detection_name, low_V)
def on_high_V_thresh_trackbar(val):
    global low_V
    global high_V
    high_V = val
    high_V = max(high_V, low_V+1)
    cv.setTrackbarPos(high_V_name, window_detection_name, high_V)
    
parser = argparse.ArgumentParser(description='Code for Thresholding Operations using inRange tutorial.')
parser.add_argument('--camera', help='Camera divide number.', default=0, type=int)
args = parser.parse_args()
cap = cv.VideoCapture(args.camera)
cv.namedWindow(window_capture_name)
cv.namedWindow(window_detection_name)
cv.createTrackbar(low_H_name, window_detection_name , low_H, max_value_H, on_low_H_thresh_trackbar)
cv.createTrackbar(high_H_name, window_detection_name , high_H, max_value_H, on_high_H_thresh_trackbar)
cv.createTrackbar(low_S_name, window_detection_name , low_S, max_value, on_low_S_thresh_trackbar)
cv.createTrackbar(high_S_name, window_detection_name , high_S, max_value, on_high_S_thresh_trackbar)
cv.createTrackbar(low_V_name, window_detection_name , low_V, max_value, on_low_V_thresh_trackbar)
cv.createTrackbar(high_V_name, window_detection_name , high_V, max_value, on_high_V_thresh_trackbar)
while True:
    
    ret, frame = cap.read()
    if frame is None:
        break
    frame_HSV = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    frame_threshold = cv.inRange(frame_HSV, (low_H, low_S, low_V), (high_H, high_S, high_V))
    frame_masked = cv.bitwise_and(frame,frame,mask = frame_threshold)    
    
    cv.imshow(window_capture_name, frame)
    #cv.imshow(window_detection_name, frame_threshold)
    cv.imshow(window_detection_name, frame_masked)
    
    key = cv.waitKey(30)
    if key == ord('s'):
        config.set("minesweeper.analysis.colourTargetLowerTest", [low_H, low_S, low_V])
        config.set("minesweeper.analysis.colourTargetUpperTest", [high_H, high_S, high_V])
        config.save()
        # flash to confirm
        cv.putText(frame_masked, f"Saved", (frame_masked.shape[0]*2//5, frame_masked.shape[1]*2//6), cv.FONT_HERSHEY_DUPLEX, 2, (255, 255, 255))
        cv.imshow(window_detection_name, frame_masked)
        key = cv.waitKey(500)
    elif key == ord('m'):
        configM = Config("calibrationMinesweeper.json")
        configM.set("minesweeper.analysis.colourTargetLower", [low_H, low_S, low_V])
        configM.set("minesweeper.analysis.colourTargetUpper", [high_H, high_S, high_V])
        configM.save()
        # flash to confirm
        cv.putText(frame_masked, f"Saved to Minesweeper", (frame_masked.shape[0]*1//10, frame_masked.shape[1]*2//6), cv.FONT_HERSHEY_DUPLEX, 1.5, (255, 255, 255))
        cv.imshow(window_detection_name, frame_masked)
        key = cv.waitKey(500)
        
    if key == ord('q') or key == 27:
        break
