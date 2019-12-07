import time
import pygame
import math
from simple_pid import PID
import atexit

from challenge.challengeBasicRemoteControl import ChallengeBasicRemoteControl
from interfaces.SensorAccessFactory import SensorAccessFactory

# Interfaces
from interfaces.ControlAccessFactory import ControlAccessFactory

MEDIUM_PRIORITY_FREQ = 10	# as proprotion of high priority

pygame.init()

# recommended for auto-disabling motors on shutdown!
def stopAtExit():
	ControlAccessFactory.getSingleton().emergencyStop() # This destroys everying and stops the motors
atexit.register(stopAtExit)

class DangleRun:

	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		self.highPriorityProcesses = []
		self.medPriorityProcesses = []
		self.counter = 0
		# Set up specific challenge instance
		self.challenge = ControlAccessFactory()

	def processAll(self, processes):
		[x.process() for x in processes]
	
	def run(self):
		# Get initial state
		self.sensors.process()

		# Set initial state of servos and motors
		self.controls.stopAllMotors()
	
		# Common controls
		self.highPriorityProcesses.append(self.controls)

		# Add challenge-specific controls
		self.challenge.createProcesses(self.highPriorityProcesses, self.medPriorityProcesses)

		# Set initial state of servos and motors
		self.processAll(self.highPriorityProcesses)
		self.processAll(self.medPriorityProcesses)
		
		# Loop until the user clicks the close button.
		done = False
		
		while not done:
			self.counter += 1
			
			# Get current sensor state
			self.sensors.process()
			
			#
			# EVENT PROCESSING STEP
			#
			for event in pygame.event.get(): # User did something.
				if event.type == pygame.QUIT: # If user clicked close.
					done = True # Flag that we are done so we exit this loop.

			self.challenge.move()
			
			# Update everything
			self.processAll(self.highPriorityProcesses)
			if self.counter % MEDIUM_PRIORITY_FREQ == 0:
				self.processAll(self.medPriorityProcesses)
			
			pygame.time.wait(10) # mS

			# Keep motors alive if sensors also alive
			if self.sensors.checkWatchdog() > 0:
				self.controls.resetWatchdog()
			else:
				motorEnable.setValue(0, status=0)
			
main = DangleRun()
main.run()
