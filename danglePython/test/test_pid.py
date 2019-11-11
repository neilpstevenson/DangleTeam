#!/usr/bin/python3
from simple_pid import PID
import time
import matplotlib.pyplot as plt
import sys
import math
import numpy as np

class TestPid:
	def __init__(self):
		self.pid = PID(0.4, 0.8, 0.02, setpoint=0, sample_time=0.01)
		#self.pid = PID(0.32, 0.8, 0.02, setpoint=0, sample_time=0.01)
		self.pid.output_limits = (-1.0,1.0)
		self.pid.proportional_on_measurement = True	
		# Set the target position
		print("PID: ", self.pid.tunings)

		# Current forward speed of motors
		self.current_speed = 0.0

		# points to plot
		self.setpoint = []
		self.speed = []
		self.PIDctrls = []
		self.PIDerror = []
		
	def speedFn(self, error):
		return self.current_speed + 0.3*error

		
	def setpointFn(self, point):
		if point < 20: 
			return 0.0
		elif point < 500:
			return 1.0
		elif point < 800:
			return 0.5
		else:
			return -1.0
		
	def simulate(self):
		for point in range(1000):
		
			setpoint = self.setpointFn(point)
			self.pid.setpoint = setpoint
			error = self.pid(self.current_speed)
			
			# Save the results
			self.setpoint.append(setpoint)
			self.speed.append(self.current_speed)
			self.PIDerror.append(error)
			self.PIDctrls.append(self.pid.components)

			# Update the motor feedback
			self.current_speed = self.speedFn(error)
			
			print(point, ":  new speed: ", self.current_speed, ", error ", error, ", setpoint: ", setpoint)
			time.sleep(0.01)

	def plot(self):
		#Plot the results
		plt.clf()
		
		p_val, i_val, d_val = zip(*self.PIDctrls)
		pid_colors_and_labels = (
			(p_val, 'green', 'p'),
			(i_val, 'grey', 'i'),
			(d_val, 'orange', 'd'),
		)
		for val, color, label in pid_colors_and_labels:
			plt.plot(val, color=color, label=label)
			
		plt.plot(self.PIDerror, 'r', label="err")
		plt.plot(self.speed, 'b', label="speed")
		plt.plot(self.setpoint, 'k', label="set point")

		plt.ylabel('speed')
		#plt.ylim((-35.0,35.0))	# Switch off auto-scale
		plt.legend()
		plt.show() #show(block=False)

def main():
	test = TestPid()
	test.simulate()
	test.plot()

if __name__ == "__main__":
	main()
