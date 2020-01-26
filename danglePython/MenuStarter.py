import time
import numpy as np
import psutil
import sys
#from subprocess import Popen

# Interfaces
from interfaces.SensorAccessFactory import SensorAccessFactory
from analysis.StepUpDownButtonValue import StepUpDownButtonValue
# Menu stuff
from display.menu import MenuDisplay
from display.welcome import showWelcomeSequence

def Run(selected):
	# Attempt to start the sub-process(es)
	name = menus[selected,0]
	requiredProcesses = menus[selected,2]
	print(f"Runing option {selected}: {name}")
	for processCmd in requiredProcesses:
		alreadyRunning = False
		for process in psutil.process_iter():
			if process.cmdline() == processCmd:
				alreadyRunning = True
				break
				
		pythonName = processCmd[1]
		if not alreadyRunning:
			print(f"Starting: {processCmd}")
			display = MenuDisplay(title, [f"Starting\n{pythonName}"], 0)
			display.show()
			psutil.Popen(processCmd)
			time.sleep(1)
		else:
			print(f"Already running: {processCmd}")
			display = MenuDisplay(title, [f"Running\n{pythonName}"], 0)
			display.show()
			time.sleep(1)

def StopAll(selected):
	# Kill any existing processes
	for options in menus[:,2]:
		for processCmd in options:
			print(f"Checking: {processCmd}")
			for process in psutil.process_iter():
				if process.cmdline() == processCmd:
					pythonName = processCmd[1]
					print(f"Stopping: {processCmd}")
					display = MenuDisplay(title, [f"Stopping\n{pythonName}"], 0)
					display.show()
					process.kill()
					time.sleep(1)

def Display(selected):
	stopButton = sensors.button(10)
	showWelcomeSequence(display.getDevice(), stopButton)

def GetSelection():
	lastSelected = -1
	upDownButtons = StepUpDownButtonValue(sensors.button(14), sensors.button(13), min = 0, max = len(menus)-1, scaling = 1)
	selectButton = sensors.button(9)
	while True:
		if lastSelected != upDownButtons.getValue():
			lastSelected = int(upDownButtons.getValue())
			display.select(lastSelected)
		if selectButton.getValue() > 0:
			break
		time.sleep(0.05)
	return lastSelected

def Quit(selected):
	sys.exit()

sensors = SensorAccessFactory.getSingleton()
title = "Select Challenge"
menus = np.array([
	["Maze (r-wall)", Run, [['python3','ToFSensorProcess.py'], ['python3','DangleRun.py']]], 
	["Lava Palaver", Run, [['python3','VisionLineProcessor.py'], ['python3','DangleRun-lava.py']]], 
	["Welcome", Display, [['python3', 'display/welcome.py', '--config', 'hardware/ssd1309.conf']]],
	["Stop", StopAll, []],
	["Quit", Quit, []]
	])

# Enable the menu selected via joystick
display = MenuDisplay(title, menus[:,0], 0)

# Stop everything first
StopAll(-1)
while True:
	# Present Menu
	selected = GetSelection()
	# Do selected acton
	menus[selected,1](selected)
