import time
from adafruit_motorkit import MotorKit
import pygame
import math
import Quaternion_shared_helper as Q
from simple_pid import PID
import atexit

# Loop until the user clicks the close button.
done = False
running = False
rotate = 0.0

pygame.init()

kit = MotorKit()
kit.motor1.throttle = 0.0
kit.motor2.throttle = 0.0

quaternion = Q.Quaternion_shared_helper()

pidLeft = PID(0.5, 0.02, 0.04, setpoint=0)
pidLeft.output_limits = (-1.0, 1.0)
pidRight = PID(0.5, 0.02, 0.04, setpoint=0)
pidRight.output_limits = (-1.0, 1.0)
pidHeading = PID(0.02, 0.005, 0.005, setpoint=0)
pidHeading.output_limits = (-1.0, 1.0)

quaternion.updateReading()
target_heading = -quaternion.getYawDegrees()

# recommended for auto-disabling motors on shutdown!
def stop_all():
	kit.motor1.throttle = 0.0
	kit.motor2.throttle = 0.0
	kit.motor3.throttle = 0.0
	kit.motor4.throttle = 0.0
atexit.register(stop_all)

joystick = pygame.joystick.Joystick(0)
joystick.init()

while not done:
    if pygame.joystick.get_count() == 0:
        print("Please connect joystick...")
        while pygame.joystick.get_count() == 0:
            time.sleep(0.2)
	    
    #
    # EVENT PROCESSING STEP
    #
    # Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
    # JOYBUTTONUP, JOYHATMOTION
    for event in pygame.event.get(): # User did something.
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
        j1 = -joystick.get_axis(1) # -1=up, +1=down LEFT
        #j2 = joystick.get_axis(1) # -1=left, +1=right
        #j2 = joystick.get_axis(4) # -1=up, +1=down RIGHT
        j2 = joystick.get_axis(3) # -1=left, +1=right
        target_heading = target_heading + j2 * 10.0
	
        # Get the nearest delta angle to target
        diff_heading = heading - target_heading
        if diff_heading > 180.0:
            diff_heading = diff_heading - 360.0
        elif diff_heading < -180.0:
            diff_heading = diff_heading + 360.0
        control = pidHeading(diff_heading)

        print("j1: {0:4.3f}, j2: {1:4.3f}".format(j1,j2))
        print("target: {0:6.2f}, current: {1:6.2f}, diff: {2:6.2f}, control: {3:6.2f}".format(target_heading, heading, diff_heading, control))

        pidLeft.setpoint = max(min((control+j1),1.0),-1.0)
        pidRight.setpoint = max(min((control-j1),1.0),-1.0)
        deltaLeft = pidLeft(kit.motor1.throttle)
        deltaRight = pidRight(kit.motor2.throttle)
        kit.motor1.throttle = max(min((kit.motor1.throttle + deltaLeft),1.0),-1.0)
        kit.motor2.throttle = max(min((kit.motor2.throttle + deltaRight),1.0),-1.0)
    else:
        # Use compass heading to maintain position
        target_heading = heading # So doesn't spin when button is released
        pidLeft.setpoint = 0.0
        pidRight.setpoint = 0.0
        deltaLeft = pidLeft(kit.motor1.throttle)
        deltaRight = pidRight(kit.motor2.throttle)
        kit.motor1.throttle = max(min((kit.motor1.throttle + deltaLeft),1.0),-1.0)
        kit.motor2.throttle = max(min((kit.motor2.throttle + deltaRight),1.0),-1.0)
        #print("L: {0:6.3f}, R: {1:6.3f}".format(kit.motor1.throttle, kit.motor2.throttle))
    print("L: {0:6.3f} => {2:6.3f}, R: {1:6.3f} => {3:6.3f}".format(kit.motor1.throttle, kit.motor2.throttle, pidLeft.setpoint, pidRight.setpoint ))

    time.sleep(0.1)
