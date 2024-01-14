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
			[(self.ax.plot(self.x, [0.0]*len(self.x), label="L motor")[0], 	 Scaler(self.controls.motor(2), scaling=-1.0)), \
			(self.ax.plot(self.x, [0.0]*len(self.x), label="L position")[0], Scaler(self.controls.motorPosition(2), scaling=0.001)), \
			(self.ax.plot(self.x, [0.0]*len(self.x), label="L speed")[0],    Scaler(self.controls.motorSpeed(2), scaling=-1.0/1500)), \
			(self.ax.plot(self.x, [0.0]*len(self.x), label="R motor")[0],    Scaler(self.controls.motor(1), scaling=1.0)), \
			(self.ax.plot(self.x, [0.0]*len(self.x), label="R position")[0], Scaler(self.controls.motorPosition(1), scaling=0.001)), \
			(self.ax.plot(self.x, [0.0]*len(self.x), label="R speed")[0],    Scaler(self.controls.motorSpeed(1), scaling=1.0/1500)) ]
			#(self.ax.plot(self.x, [0.0]*len(self.x), label="F Joystick")[0], Scaler(self.sensors.joystickAxis(1), scaling=1.0), \
			#(self.ax.plot(self.x, [0.0]*len(self.x), label="Heading")[0],    Scaler(self.sensors.yaw(), scaling=1/180.0), \
			#(self.ax.plot(self.x, [0.0]*len(self.x), label="Vision")[0],     Scaler(self.vision.getLineHeading(), scaling=1/180.0)
		plt.ylabel('value')
		plt.legend(loc=(0.01, 1.0 - 0.04*len(self.lines)))
		
		self.pause = False
		#self.fig.canvas.mpl_connect('button_press_event', self.onClick)
		self.fig.canvas.mpl_connect('key_press_event', self.onClick)
		
	def onClick(self, event):
		if event.key == 'p':
			self.pause ^= True
			self.ani._blit = not self.pause
			for line, valueprovider in self.lines:
				line.set_animated(not self.pause)
			#if self.pause:
			#	self.ani.event_source.stop()
			#else:
			#	self.ani.event_source.start()
			print(f"onClick: {self.pause }")
		elif event.key == 'S':
			print(f"onClick: Save")
			self.save("monitor.mp4")
			
	def init(self):  # only required for blitting to give a clean slate.
		for line, valueprovider in self.lines:
			line.set_ydata([np.nan] * len(self.x))
		self.ax.set_ylim((-1.05,1.05))
		return [row[0] for row in self.lines]

	def animate(self, i):
		# update readings
		self.sensors.process()
		#print(i) #len(pitch),pitch)
		#self.ani._blit_cache.clear()
		if not self.pause:
			for line, valueprovider in self.lines:
				newline = line.get_ydata()
				newline.pop(0)
				newline.append(valueprovider.getValue())
				#print(f"{newline}")
				line.set_ydata(newline)
				#line.set_data(range(len(newline)),newline)
		#if i%100 == 0:
		#	ax.set_ylim(min(-1.05,min(line.get_ydata())-0.1),max(1.05,max(line.get_ydata())+0.1))
		#	plt.draw()
		#print(f"{i}")
		return [row[0] for row in self.lines]

	def show(self):
		self.ani = animation.FuncAnimation(
			self.fig, self.animate, init_func=self.init, interval=10, blit=True, save_count=500)
		#self.ax.callbacks.connect('xlim_changed', lambda event: self.ani._blit_cache.clear())
		#self.ax.callbacks.connect('ylim_changed', lambda event: self.ani._blit_cache.clear())
		#self.fig.canvas.mpl_connect('button_press_event', lambda event: self.ani._blit_cache.clear())
		plt.show()
	
	def save(self, filename):
		from matplotlib.animation import FFMpegWriter
		writer = FFMpegWriter(fps=15, metadata=dict(artist='Chameleon'), bitrate=1800)
		self.ani.save(filename, writer=writer)
		writer.finish()
