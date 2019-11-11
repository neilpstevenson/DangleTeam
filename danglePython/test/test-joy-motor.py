import time
from adafruit_motorkit import MotorKit
import pygame
import math

# Loop until the user clicks the close button.
done = False
running = False

pygame.init()

kit = MotorKit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

while not done:
    #
    # EVENT PROCESSING STEP
    #
    # Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
    # JOYBUTTONUP, JOYHATMOTION
    for event in pygame.event.get(): # User did something.
        if event.type == pygame.QUIT: # If user clicked close.
            done = True # Flag that we are done so we exit this loop.
        elif event.type == pygame.JOYBUTTONDOWN:
            running = True
            print("Joystick button pressed.")
        elif event.type == pygame.JOYBUTTONUP:
            running = False
        print("Joystick button released.")

    if running:
        j1 = joystick.get_axis(0) # -1=up, +1=down
        j2 = joystick.get_axis(1) # -1=left, +1=right
        kit.motor1.throttle = max(min((j1+j2),1.0),-1.0)
        kit.motor2.throttle = max(min((j1-j2),1.0),-1.0)
        print("L: {}, R: {}".format(kit.motor1.throttle,kit.motor2.throttle))
    else:
        kit.motor1.throttle = 0
        kit.motor2.throttle = 0

    time.sleep(0.1)
