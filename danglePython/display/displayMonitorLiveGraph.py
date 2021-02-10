import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Interfaces
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
from interfaces.VisionAccessFactory import VisionAccessFactory
from interfaces.Config import Config
# Value providers
from analysis.SimplePIDErrorValue import SimplePIDErrorValue
from analysis.HeadingPIDErrorValue import HeadingPIDErrorValue
from analysis.OneShotButtonValue import OneShotButtonValue
from analysis.FixedValue import FixedValue
# Value combination helpers
from analysis.Scaler import Scaler

class MonitorDisplay:
	def __init__(self):
		self.controls = ControlAccessFactory.getSingleton()
		self.sensors = SensorAccessFactory.getSingleton()
		self.vision = VisionAccessFactory.getSingleton()
		# Get config
		config = Config()
		self.points = config.get("display.graph.numpoints", 500)
		config.save()
		
		self.fig, self.ax = plt.subplots()
		self.x = np.arange(0, self.points, 1)

		self.lines = \
			self.ax.plot(self.x, [0.0]*len(self.x), label="L motor")[0], \
			self.ax.plot(self.x, [0.0]*len(self.x), label="L position")[0], \
			self.ax.plot(self.x, [0.0]*len(self.x), label="R motor")[0], \
			self.ax.plot(self.x, [0.0]*len(self.x), label="R position")[0] 
			#self.ax.plot(self.x, [0.0]*len(self.x), label="F Joystick")[0], \
			#self.ax.plot(self.x, [0.0]*len(self.x), label="L speed")[0], \
			#self.ax.plot(self.x, [0.0]*len(self.x), label="R speed")[0], \
			#self.ax.plot(self.x, [0.0]*len(self.x), label="Heading")[0], \
			#self.ax.plot(self.x, [0.0]*len(self.x), label="Vision")[0]
		self.values = \
			Scaler(self.controls.motor(2), scaling=-1.0), \
			Scaler(self.controls.motorPosition(2), scaling=0.001), \
			Scaler(self.controls.motor(1), scaling=1.0), \
			Scaler(self.controls.motorPosition(1), scaling=0.001) 
			#Scaler(self.sensors.joystickAxis(1), scaling=1.0), \
			#Scaler(self.sensors.rateCounter(0), scaling=0.0012), \
			#Scaler(self.sensors.rateCounter(1), scaling=0.0012), \
			#Scaler(self.sensors.yaw(), scaling=1/180.0), \
			#Scaler(self.vision.getLineHeading(), scaling=1/180.0)
		plt.ylabel('value')
		plt.legend(loc=(0.01,0.75))

	def init(self):  # only required for blitting to give a clean slate.
		for line in self.lines:
			line.set_ydata([np.nan] * len(self.x))
		self.ax.set_ylim((-1.05,1.05))
		return self.lines

	def animate(self, i):
		# update readings
		self.sensors.process()
		#print(i) #len(pitch),pitch)
		for line, value in zip(self.lines, self.values):
			line.set_ydata(line.get_ydata()[1:]+[value.getValue()])
		#if i%100 == 0:
		#	ax.set_ylim(min(-1.05,min(line.get_ydata())-0.1),max(1.05,max(line.get_ydata())+0.1))
		#	plt.draw()
		print(f"{i}")
		return self.lines

	def show(self):
		self.ani = animation.FuncAnimation(
			self.fig, self.animate, init_func=self.init, interval=10, blit=True, save_count=5)
		plt.show()
	
	def save(self, filename):
		from matplotlib.animation import FFMpegWriter
		writer = FFMpegWriter(fps=15, metadata=dict(artist='Dangle'), bitrate=1800)
		self.ani.save(filename, writer=writer)
