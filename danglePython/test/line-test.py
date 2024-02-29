"""
@file hough_lines.py
@brief This program demonstrates line finding with the Hough transform
"""
import sys
import math
import cv2 as cv
import numpy as np
from picamera2 import Picamera2

def main(argv):
    picam2 = Picamera2()
    picam2.configure( picam2.create_preview_configuration(main={"format": 'RGB888', "size": (640, 480)}))
    picam2.start()
    
    while True:
        #default_file = 'sudoku.png'
        #filename = argv[0] if len(argv) > 0 else default_file
        ## Loads an image
        #src = cv.imread(cv.samples.findFile(filename), cv.IMREAD_GRAYSCALE)
        ## Check if image is loaded fine
        #if src is None:
        #    print ('Error opening image!')
        #    print ('Usage: hough_lines.py [image_name -- default ' + default_file + '] \n')
        #    return -1
        src = picam2.capture_array()
        
        dst = cv.Canny(src, \
            50, # threshold1 \
            200, # threshold2 \
            None, #  ?? \
            3) # aperture size 3-7
        
        # Copy edges to the images that will display the results in BGR
        cdst = cv.cvtColor(dst, cv.COLOR_GRAY2BGR)
        cdstP = np.copy(cdst)
        """
        lines = cv.HoughLines(dst, 1, np.pi / 180, 150, None, 0, 0)
        
        if lines is not None:
            for i in range(0, len(lines)):
                rho = lines[i][0][0]
                theta = lines[i][0][1]
                a = math.cos(theta)
                b = math.sin(theta)
                x0 = a * rho
                y0 = b * rho
                pt1 = (int(x0 + 1000*(-b)), int(y0 + 1000*(a)))
                pt2 = (int(x0 - 1000*(-b)), int(y0 - 1000*(a)))
                cv.line(cdst, pt1, pt2, (0,0,255), 3, cv.LINE_AA)
        """
        
        linesP = cv.HoughLinesP(dst, 1, \
            3 * np.pi / 180, # deviation angle\
            50, \
            None, \
            50, # min length \
            10) # min gap
        
        if linesP is not None:
            for i in range(0, len(linesP)):
                l = linesP[i][0]
                cv.line(cdstP, (l[0], l[1]), (l[2], l[3]), (255,0,0), 3, cv.LINE_AA)
        
        cv.imshow("Source", src)
        #cv.imshow("Detected Lines (in red) - Standard Hough Line Transform", cdst)
        cv.imshow("Canny edges", dst)
        cv.imshow("Detected Lines (in blue) - Probabilistic Line Transform", cdstP)
    
        key = cv.waitKey(25) & 0xff
        if key == 27 or key == ord('q'):
            quit()
        
    cv.waitKey()
    return 0
    
if __name__ == "__main__":
    main(sys.argv[1:])
