import time
import pygame
import math
import atexit

# Interfaces
from ControlIPC import ControlIPC
from SensorIPC import SensorIPC
# Value providers
from Scaler import Scaler
from SimplePIDErrorValue import SimplePIDErrorValue
from HeadingPIDErrorValue import HeadingPIDErrorValue
from OneShotButtonValue import OneShotButtonValue
from FixedValue import FixedValue
# Value combination helpers
from ValueIntegrator import ValueIntegrator
from ValueAdder import ValueAdder
# Control mediators
from SimpleControlMediator import SimpleControlMediator
from SwitchingControlMediator import SwitchingControlMediator

pygame.init()

# recommended for auto-disabling motors on shutdown!
def stopAtExit():
	ControlIPC.getSingleton().emergencyStop() # This destroys everying and stops the motors
atexit.register(stopAtExit)

class DangleControl:

	def __init__(self):
		self.controls = ControlIPC.getSingleton()
		#self.sensors = SensorIPC.getSingleton()
		self.highPriorityProcesses = []
		self.medPriorityProcesses = []
		self.counter = 0

	def processAll(self, processes):
		[x.process() for x in processes]
	
	def run(self):
		# Get initial state
		#self.sensors.process()
		
		# Set initial state of servos and motors
		self.controls.stopAllMotors()
	
		# Common controls
		self.highPriorityProcesses.append(self.controls)

		# Motor controller
		motorL = self.controls.motor(2)
		motorR = self.controls.motor(1)
		
		# Motors
		motorTorqueL = FixedValue(0.0)
		motorMediatorL = SimpleControlMediator(motorTorqueL, motorL)
		self.highPriorityProcesses.append(motorMediatorL)
		
		motorTorqueR = FixedValue(0.0)
		motorMediatorR = SimpleControlMediator(motorTorqueR, motorR)
		self.highPriorityProcesses.append(motorMediatorR)

		# Set initial state of servos and motors
		self.processAll(self.highPriorityProcesses)
		self.processAll(self.medPriorityProcesses)
		
		# Loop until the user clicks the close button.
		done = False
		running = False
		
		
		while not done:
			self.counter += 1
			
			# Get current sensor state
			#self.sensors.process()
			
			#
			# EVENT PROCESSING STEP
			#
			for event in pygame.event.get(): # User did something.
				if event.type == pygame.QUIT: # If user clicked close.
					done = True # Flag that we are done so we exit this loop.
			# Adjust torque
			if self.counter % 10000 < 5000:
				motorTorqueL.setValue( motorTorqueL.getValue() + 0.0002 )
			else:
				motorTorqueL.setValue( motorTorqueL.getValue() - 0.0002 )
			# Adjust torque
			#if self.counter % 1000 < 500:
			#	motorTorqueR.setValue( motorTorqueR.getValue() + 0.002 )
			#else:
			#	motorTorqueR.setValue( motorTorqueR.getValue() - 0.002 )


			# Update everything
			self.processAll(self.highPriorityProcesses)
			if self.counter % 10 == 0:
				self.processAll(self.medPriorityProcesses)
			
			pygame.time.wait(10) # mS

main = DangleControl()
main.run()
