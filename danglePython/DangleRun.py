import time
import math
import atexit
import argparse

# Challenge options
from challenge.challengeBasicRemoteControl import ChallengeBasicRemoteControl
from challenge.challengeHeadingRemoteControl import ChallengeHeadingRemoteControl
from challenge.challengeWallFollowControl import ChallengeWallFollowControl
from challenge.challengeMinesweeper import ChallengeMinesweeper
from challenge.challengeManualControl import ChallengeManualControl

# Factories
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.ControlAccessFactory import ControlAccessFactory

MEDIUM_PRIORITY_FREQ = 10	# as proprotion of high priority

# recommended for auto-disabling motors on shutdown!
def stopAtExit():
	ControlAccessFactory.getSingleton().emergencyStop() # This destroys everying and stops the motors
atexit.register(stopAtExit)

class DangleRun:

	def __init__(self):
		# Parse command-line options
		ap = argparse.ArgumentParser()
		ap.add_argument("-c", "--challenge", type=str, default="ChallengeWallFollowControl",
			help="clas name of the challenge processor")
		self.args = vars(ap.parse_args())
		# Factories
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		# Processing lists
		self.highPriorityProcesses = []
		self.medPriorityProcesses = []
		self.counter = 0
		# Run the challenge instance
		self.challenge = globals()[self.args["challenge"]]()
		
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

		# Start the challenge
		self.challenge.start()
		
		while not done:
			self.counter += 1
			
			# Get current sensor state
			self.sensors.process()
			
			# Calculate next move
			self.challenge.move()
			
			# Update everything
			self.processAll(self.highPriorityProcesses)
			if self.counter % MEDIUM_PRIORITY_FREQ == 0:
				self.processAll(self.medPriorityProcesses)
			
			time.sleep(0.01) # secs

			# Keep challenge alive if sensors also alive
			if self.sensors.checkWatchdog() > 0:
				self.controls.resetWatchdog()
			else:
				print("Sensor watchdog expired... stopping")
				self.challenge.stop()
				time.sleep(1.0)
			
main = DangleRun()
main.run()
