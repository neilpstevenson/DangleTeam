import time
import numpy as np
import psutil
#from subprocess import Popen

# Interfaces
from interfaces.SensorAccessFactory import SensorAccessFactory
from analysis.StepUpDownButtonValue import StepUpDownButtonValue
# Menu stuff
from display.menu import MenuDisplay

sensors = SensorAccessFactory.getSingleton()
title = "Select Challenge"
menus = np.array([
	["Maze (r-wall)", [['python3','ToFSensorProcess.py'], ['python3','DangleRun.py']]], 
	["Lava Palaver", [['python3','VisionLineProcessor.py'], ['python3','DangleRun-lava.py']]], 
	["Third", []],
	["Fourth options", []]])

# Kill any existing processes
for options in menus[:,1]:
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

# Enable the menu selected via joystick
selected = StepUpDownButtonValue(sensors.button(0), sensors.button(2), min = 0, max = len(menus)-1, scaling = 1)
display = MenuDisplay(title, menus[:,0], 0)
lastSelected = -1
selectButton = sensors.button(5)
while True:
	if lastSelected != selected.getValue():
		lastSelected = int(selected.getValue())
		display.select(lastSelected)
	if selectButton.getValue() > 0:
		break
	time.sleep(0.05)

name = menus[lastSelected,0]
requiredProcesses = menus[lastSelected,1]

print(f"Selected option: {name} ({lastSelected})")

# Attempt to start the sub-process(es)
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
