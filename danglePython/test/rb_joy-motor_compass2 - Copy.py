import time
#from adafruit_motorkit import MotorKit
import pygame
import math
import Quaternion_shared_helper as Q
from simple_pid import PID
import atexit
import redboard

# Loop until the user clicks the close button.
done = False
running = False
rotate = 0.0

pygame.init()

#kit = MotorKit()
#kit.motor1.throttle = 0.0
#kit.motor2.throttle = 0.0
redboard.M1(0.0)
redboard.M2(0.0)
leftThrottle = 0.0
rightThrottle = 0.0
grabWidth = 0.0 # 0.0 = fully open, 1.0 = fully closed

quaternion = Q.Quaternion_shared_helper()

pidLeft = PID(0.5, 0.02, 0.04, setpoint=0)
pidLeft.output_limits = (-1.0, 1.0)
pidRight = PID(0.5, 0.02, 0.04, setpoint=0)
pidRight.output_limits = (-1.0, 1.0)
pidHeading = PID(0.03, 0.0005, 0.01, setpoint=0)
pidHeading.output_limits = (-1.0, 1.0)

quaternion.updateReading()
target_heading = -quaternion.getYawDegrees()

# recommended for auto-disabling motors on shutdown!
def stop_all():
	#kit.motor1.throttle = 0.0
	#kit.motor2.throttle = 0.0
	#kit.motor3.throttle = 0.0
	#kit.motor4.throttle = 0.0
    redboard.Stop()
atexit.register(stop_all)

joystick = None

def moveGrabber():
    redboard.servo5_P(680.0 + grabWidth*1500)

# Set initial state of servos
moveGrabber()

while not done:
    if joystick is None or pygame.joystick.get_count() == 0:
        pygame.joystick.quit()
        pygame.joystick.init()
        while pygame.joystick.get_count() == 0:
            print("Please connect joystick...")
            pygame.time.wait(2000) # mS
            #time.sleep(2.0)
            # Re-initialise the joystick
            pygame.joystick.quit()
            pygame.joystick.init()
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

	    
    #
    # EVENT PROCESSING STEP
    #
    # Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
    # JOYBUTTONUP, JOYHATMOTION
    for event in pygame.event.get(): # User did something.
        print(event.type)
        if event.type == pygame.QUIT: # If user clicked close.
            done = True # Flag that we are done so we exit this loop.
        elif not running and event.type == pygame.JOYBUTTONDOWN and (joystick.get_button(4) == 1 or joystick.get_button(5) == 1):
            running = True
            pidHeading.auto_mode = True
            print("Motor Joystick enabled...")
        elif event.type == pygame.JOYBUTTONDOWN and joystick.get_button(15) == 1:
            rotate = -22.5
            print("Rotate -22.5 deg...")
        elif event.type == pygame.JOYBUTTONDOWN and joystick.get_button(16) == 1:
            rotate = 22.5
            print("Rotate +22.5 deg...")
        elif running and event.type == pygame.JOYBUTTONUP and joystick.get_button(4) == 0 and joystick.get_button(5) == 0:
            running = False
            pidHeading.auto_mode = False
            print("Motors off.")

    # Servo controls
    if joystick.get_button(1) == 1 and grabWidth <= 0.9:
        grabWidth += 0.1
        print("Grabbing...")
        moveGrabber()
    elif joystick.get_button(3) == 1 and grabWidth >= 0.1:
        grabWidth -= 0.1
        print("Releasing...")
        moveGrabber()

    target_heading = target_heading + rotate
    if target_heading > 180.0:
        target_heading = target_heading - 360.0
    elif target_heading < -180.0:
        target_heading = target_heading + 360.0
    rotate = 0.0
    
    quaternion.updateReading()
    heading = -quaternion.getYawDegrees()

    # simulate rotation alignment
    #target_heading = target_heading - (control*3.0)# / 10.0)

    if running:
        # Use Joystick control
        #j0 = joystick.get_axis(0) # LEFT -1=left, +1=right
        j1 = -joystick.get_axis(1) # LEFT -1=up, +1=down
        j2 = joystick.get_axis(3)  # RIGHT -1=left, +1=right
        #j3 = joystick.get_axis(4) # RIGHT-1=up, +1=down
        target_heading = target_heading + j2 * 10.0
	
        # Get the nearest delta angle to target
        diff_heading = heading - target_heading
        if diff_heading > 180.0:
            diff_heading = diff_heading - 360.0
        elif diff_heading < -180.0:
            diff_heading = diff_heading + 360.0
        headingAdjustment = pidHeading(diff_heading)

        #print("j1: {0:4.3f}, j2: {1:4.3f}".format(j1,j2))
        print(pidHeading.components)
        print("target: {0:6.2f}, current: {1:6.2f}, diff: {2:6.2f}, headingAdjustment: {3:6.2f}".format(target_heading, heading, diff_heading, headingAdjustment))

        # Use compass heading to maintain position
        pidLeft.setpoint = max(min((-headingAdjustment+j1),1.0),-1.0)
        pidRight.setpoint = max(min((-headingAdjustment-j1),1.0),-1.0)
        deltaLeft = pidLeft(leftThrottle)
        deltaRight = pidRight(rightThrottle)
        leftThrottle = max(min((leftThrottle + deltaLeft),1.0),-1.0)
        rightThrottle = max(min((rightThrottle + deltaRight),1.0),-1.0)
        redboard.M1(leftThrottle * 100)
        redboard.M2(rightThrottle * 100)
    else:
        # Just idle to a standstill
        target_heading = heading # So doesn't spin when button is released
        pidLeft.setpoint = 0.0
        pidRight.setpoint = 0.0
        deltaLeft = pidLeft(leftThrottle)
        deltaRight = pidRight(rightThrottle)
        leftThrottle = max(min((leftThrottle + deltaLeft),1.0),-1.0)
        rightThrottle = max(min((rightThrottle + deltaRight),1.0),-1.0)
        redboard.M1(leftThrottle * 100.0)
        redboard.M2(rightThrottle * 100.0)
        #print("L: {0:6.3f}, R: {1:6.3f}".format(kit.motor1.throttle, kit.motor2.throttle))
    print("L: {0:6.3f} => {2:6.3f}, R: {1:6.3f} => {3:6.3f}".format(leftThrottle, rightThrottle, pidLeft.setpoint, pidRight.setpoint ))

    #time.sleep(0.1)
    pygame.time.wait(100) # mS
