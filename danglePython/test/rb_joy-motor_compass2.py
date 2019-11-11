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

pygame.init()

#kit = MotorKit()
#kit.motor1.throttle = 0.0
#kit.motor2.throttle = 0.0
redboard.M1(0.0)
redboard.M2(0.0)
leftThrottle = 0.0
rightThrottle = 0.0
currentLeftSpeed = 0.0
currentRightSpeed = 0.0
button_rotate = 0.0
grabWidth = 0.0 # 0.0 = fully open, 1.0 = fully closed
joy_forward = 0.0

quaternion = Q.Quaternion_shared_helper()

pidLeft = PID(0.32, 0.8, 0.02, setpoint=0, sample_time=0.01, proportional_on_measurement=True)
pidLeft.output_limits = (-1.0, 1.0)
pidRight = PID(0.32, 0.8, 0.02, setpoint=0, sample_time=0.01, proportional_on_measurement=True)
pidRight.output_limits = (-1.0, 1.0)
pidHeading = PID(0.01, 0.003, 0.005, setpoint=0, sample_time=0.01, proportional_on_measurement=False)
pidHeading.output_limits = (-1.0, 1.0)

quaternion.updateReading()
target_heading = -quaternion.getYawDegrees()

# recommended for auto-disabling motors on shutdown!
def stop_all():
	#kit.motor1.throttle = 0.0
	#kit.motor2.throttle = 0.0
	#kit.motor3.throttle = 0.0
	#kit.motor4.throttle = 0.0
    redboard.led_off()
    redboard.Stop() # This destroys everying and stops the motors

atexit.register(stop_all)

joystick = None

def moveGrabber():
    redboard.servo5_P(680.0 + grabWidth*1500)

def normaliseHeading(heading):
    if heading > 180.0:
        return heading - 360.0
    elif heading < -180.0:
        return heading + 360.0
    return heading

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
        elif running and event.type == pygame.JOYBUTTONDOWN and joystick.get_button(15) == 1:
            button_rotate = -22.5
            print("Rotate -22.5 deg...")
        elif running and event.type == pygame.JOYBUTTONDOWN and joystick.get_button(16) == 1:
            button_rotate = 22.5
            print("Rotate +22.5 deg...")
        elif running and event.type == pygame.JOYBUTTONUP and joystick.get_button(4) == 0 and joystick.get_button(5) == 0:
            running = False
            pidHeading.auto_mode = False
            print("Motors off.")

    # Servo controls
    if joystick.get_button(1) == 1 and grabWidth <= 0.99:
        grabWidth += 0.01
        print("Grabbing...")
        moveGrabber()
    elif joystick.get_button(3) == 1 and grabWidth >= 0.01:
        grabWidth -= 0.01
        print("Releasing...")
        moveGrabber()

    quaternion.updateReading()
    heading = -quaternion.getYawDegrees()
    pitch = quaternion.getPitchDegrees()

 
    if running:
        redboard.red_on()
        redboard.green_off()
        
        # Use Joystick control
        #j0 = joystick.get_axis(0) # LEFT -1=left, +1=right
        # Limit the pitch 
        j1 = -joystick.get_axis(1) # LEFT -1=up, +1=down
        # Limit the max pitch of Dangle due to acceleration
        #if (pitch > -15.0 and j1 >= 0.0) or (pitch < 15.0 and j1 <= 0.0):
        joy_forward = j1
        #else:
        #    joy_forward = j1/2.0  # scale back 
        j2 = joystick.get_axis(3)  # RIGHT -1=left, +1=right
        #j3 = joystick.get_axis(4) # RIGHT-1=up, +1=down

        # clamp rotate to prevent sudden 180 degree changes
        new_heading = normaliseHeading(target_heading + button_rotate)
        diff_heading = normaliseHeading(heading - new_heading)
        if diff_heading < 100.0 and diff_heading > -100.0:
            target_heading = new_heading
        button_rotate = 0.0
            
        # Get the nearest delta angle to target
        joy_rotate = j2 * 1.0
        new_heading = normaliseHeading(target_heading + joy_rotate)
        diff_heading = normaliseHeading(heading - new_heading)
        if diff_heading < 100.0 and diff_heading > -100.0:
            target_heading = new_heading
        else:
            diff_heading = normaliseHeading(heading - target_heading)
            
        headingAdjustment = pidHeading(diff_heading)

        #print("j1: {0:4.3f}, j2: {1:4.3f}".format(j1,j2))
        print(pidHeading.components)
        print("target: {0:6.2f}, current: {1:6.2f}, diff: {2:6.2f}, headingAdjustment: {3:6.2f}".format(target_heading, heading, diff_heading, headingAdjustment))

        # Use compass heading to maintain position
        pidLeft.setpoint = max(min((-headingAdjustment+joy_forward),1.0),-1.0)
        pidRight.setpoint = max(min((headingAdjustment+joy_forward),1.0),-1.0)
    else:
        redboard.yellow_on()
        # Just idle to a standstill
        target_heading = heading # So doesn't spin when button is released
        pidLeft.setpoint = 0.0
        pidRight.setpoint = 0.0
        
    deltaLeft = pidLeft(currentLeftSpeed)
    deltaRight = pidRight(currentRightSpeed)
    leftThrottle = max(min((currentLeftSpeed + deltaLeft),1.0),-1.0)
    rightThrottle = max(min((currentRightSpeed + deltaRight),1.0),-1.0)
    print("pitch: {0:6.2f}, dl={1:6.2f}, dr={2:6.2f}, lt={3:6.2f}, rt={4:6.2f}".format(pitch, deltaLeft, deltaRight, leftThrottle, rightThrottle))
     # Update the motors
    redboard.M1(leftThrottle * 100)
    redboard.M2(-rightThrottle * 100)
    # Simulate a slight lag in the actual speed vs. requested speed
    currentLeftSpeed = max(min((currentLeftSpeed + 0.3*deltaLeft),1.0),-1.0)
    currentRightSpeed = max(min((currentRightSpeed + 0.3*deltaRight),1.0),-1.0)
        
    #    deltaLeft = pidLeft(leftThrottle)
    #    deltaRight = pidRight(rightThrottle)
    #    leftThrottle = max(min((leftThrottle + deltaLeft),1.0),-1.0)
    #    rightThrottle = max(min((rightThrottle + deltaRight),1.0),-1.0)
    #    redboard.M1(leftThrottle * 100.0)
    #    redboard.M2(rightThrottle * 100.0)
    #    #print("L: {0:6.3f}, R: {1:6.3f}".format(kit.motor1.throttle, kit.motor2.throttle))
    print("L: {0:6.3f} => {2:6.3f}, R: {1:6.3f} => {3:6.3f}".format(leftThrottle, rightThrottle, pidLeft.setpoint, pidRight.setpoint ))

    #time.sleep(0.1)
    pygame.time.wait(10) # mS
