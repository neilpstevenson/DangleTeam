import time
from adafruit_motorkit import MotorKit
import pygame
import math
import Quaternion_shared_helper as Q
from simple_pid import PID


# Loop until the user clicks the close button.
done = False
running = False
rotate = 0.0

pygame.init()

kit = MotorKit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

quaternion = Q.Quaternion_shared_helper()

pid = PID(0.05, 0.005, 0.01, setpoint=0)
pid.output_limits = (-1.0, 1.0)
quaternion.updateReading()
target_heading = -quaternion.getYawDegrees()

while not done:
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
            print("Motor Joystick enabled...")
        elif event.type == pygame.JOYBUTTONDOWN and joystick.get_button(15) == 1:
            rotate = -45.0
            print("Rotate -45 deg...")
        elif event.type == pygame.JOYBUTTONDOWN and joystick.get_button(16) == 1:
            rotate = 45.0
            print("Rotate +45 deg...")
        elif running and event.type == pygame.JOYBUTTONUP and joystick.get_button(4) == 0 and joystick.get_button(5) == 0:
            running = False
            print("Motors off.")

    target_heading = target_heading + rotate
    if target_heading > 180.0:
        target_heading = target_heading - 360.0
    elif target_heading < -180.0:
        target_heading = target_heading + 360.0
    rotate = 0.0
    
    quaternion.updateReading()
    heading = -quaternion.getYawDegrees()

    # Get the nearest delta angle to target
    diff_heading = heading - target_heading
    if diff_heading > 180.0:
        diff_heading = diff_heading - 360.0
    elif diff_heading < -180.0:
        diff_heading = diff_heading + 360.0
	
    control = pid(diff_heading)
    print("target: {0:6.2f}, current: {1:6.2f}, diff: {2:6.2f}, control: {3:6.2f}".format(target_heading, heading, diff_heading, control))
    # simulate
    target_heading = target_heading - (control*3.0)# / 10.0)

    if running:
        j1 = joystick.get_axis(0) # -1=up, +1=down
        j2 = joystick.get_axis(1) # -1=left, +1=right
        kit.motor1.throttle = max(min((j1+j2),1.0),-1.0)
        kit.motor2.throttle = max(min((j1-j2),1.0),-1.0)
        print("L: {}, R: {}".format(kit.motor1.throttle,kit.motor2.throttle))
    else:
        kit.motor1.throttle = -control #max(min((control),1.0),-1.0)
        kit.motor2.throttle = -control #max(min((control),1.0),-1.0)
        print("L: {}, R: {}".format(kit.motor1.throttle,kit.motor2.throttle))
#        kit.motor1.throttle = 0
#        kit.motor2.throttle = 0

    time.sleep(0.1)
