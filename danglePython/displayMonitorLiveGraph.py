#!/usr/bin/python3
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Interfaces
from interfaces.ControlAccessFactory import ControlAccessFactory
from interfaces.SensorAccessFactory import SensorAccessFactory
# Value providers
from analysis.SimplePIDErrorValue import SimplePIDErrorValue
from analysis.HeadingPIDErrorValue import HeadingPIDErrorValue
from analysis.OneShotButtonValue import OneShotButtonValue
from analysis.FixedValue import FixedValue
# Value combination helpers
from analysis.Scaler import Scaler

fig, ax = plt.subplots()

x = np.arange(0, 500, 1)
line, = ax.plot(x, [0.0]*len(x), label="F Joystick")
line2, = ax.plot(x, [0.0]*len(x), label="R motor")
line3, = ax.plot(x, [0.0]*len(x), label="R speed")
plt.ylabel('value')
plt.legend(loc=(0.01,0.85))

controls = ControlAccessFactory.getSingleton()
sensors = SensorAccessFactory.getSingleton()
lineValue1 = Scaler(sensors.joystickAxis(1), scaling=0.8)
lineValue2 = Scaler(controls.motor(1), scaling=-1.0)
lineValue3 = Scaler(sensors.rateCounter(1), scaling=0.0012)
		


def init():  # only required for blitting to give a clean slate.
	line.set_ydata([np.nan] * len(x))
	line2.set_ydata([np.nan] * len(x))
	line3.set_ydata([np.nan] * len(x))
	ax.set_ylim((-1.05,1.05))
	return line,line2,line3,


def animate(i):
	# update readings
	sensors.process()
	print(i) #len(pitch),pitch)
	line.set_ydata(line.get_ydata()[1:]+[lineValue1.getValue()])
	line2.set_ydata(line2.get_ydata()[1:]+[lineValue2.getValue()])
	line3.set_ydata(line3.get_ydata()[1:]+[lineValue3.getValue()])
	#if i%100 == 0:
	#	ax.set_ylim(min(-1.05,min(line.get_ydata())-0.1),max(1.05,max(line.get_ydata())+0.1))
	#	plt.draw()
	return line,line2,line3


ani = animation.FuncAnimation(
	fig, animate, init_func=init, interval=20, blit=True, save_count=1)

# To save the animation, use e.g.
#
# ani.save("movie.mp4")
#
# or
#
# from matplotlib.animation import FFMpegWriter
# writer = FFMpegWriter(fps=15, metadata=dict(artist='Me'), bitrate=1800)
# ani.save("movie.mp4", writer=writer)

plt.show()
