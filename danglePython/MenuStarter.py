import time
import numpy as np
import psutil
import sys
# Interfaces
from interfaces.SensorAccessFactory import SensorAccessFactory
from analysis.StepUpDownButtonValue import StepUpDownButtonValue
# Menu stuff
from display.menu import MenuDisplay
from display.welcome import showWelcomeSequence
from display.displayPosition import displayPosition

def Run(selected, actionParams):
	# Attempt to start the sub-process(es)
	name = menus[selected,0]
	print(f"Runing option {selected}: {name}")
	# Already running?
	alreadyRunning = False
	for process in psutil.process_iter():
		if process.cmdline() == actionParams:
			alreadyRunning = True
			break
			
	pythonName = actionParams[1]
	if not alreadyRunning:
		print(f"Starting: {actionParams}")
		display.message(f"Starting\n{pythonName}")
		psutil.Popen(actionParams)
		time.sleep(1.5)
	else:
		print(f"Already running: {actionParams}")
		display.message(f"Running\n{pythonName}")
		time.sleep(0.5)

def StopAll(selected, actionParams):
	# Kill any existing processes
	for options in menus[:,1]:
		for processCmd in options:
			print(f"Checking: {processCmd}")
			for process in psutil.process_iter():
				if processCmd[0] == Run and process.cmdline() == processCmd[1]:
					pythonName = processCmd[1][1]
					print(f"Stopping: {processCmd}")
					display.message(f"Stopping\n{pythonName}")
					process.kill()
					time.sleep(1)

def DisplayScreenSaver(selected, actionParams):
	stopButton = sensors.button(10)
	showWelcomeSequence(display.getDevice(), stopButton)

def DisplayPositions(selected, actionParams):
	stopButton = sensors.button(10)
	disp = displayPosition(display.getDevice(), stopButton)
	disp.main()

def GetSelection(selected):
	lastSelected = -1
	upDownButtons = StepUpDownButtonValue(sensors.button(14), sensors.button(13), min = 0, max = len(menus)-1, offset=selected, scaling = 1)
	selectButton = sensors.button(9)
	while True:
		if lastSelected != upDownButtons.getValue():
			lastSelected = int(upDownButtons.getValue())
			display.select(lastSelected)
		if selectButton.getValue() > 0:
			break
		time.sleep(0.05)
		
		# Display screensaver if sensors not running
		if sensors.checkWatchdog() <= 0:
			DisplayScreenSaver(lastSelected, None)
			display.select(lastSelected)
	return lastSelected

def Quit(selected, actionParams):
	sys.exit()

sensors = SensorAccessFactory.getSingleton()
title = "Select Challenge"
menus = np.array([
	["Pi Noon", [ 
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeManualControl']],
			[DisplayPositions, []] ]], 
	["Escape Route", [ 
			[Run, ['python3','ToFSensorProcess.py']], 
			[Run, ['python3','displayToF.py']],
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeWallFollowControl']] ]], 
	["Lava Palava", [
			[Run, ['python3','VisionLineProcessor.py']], 
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeHeadingRemoteControl']] ]], 
	["Minesweeper", [
			[Run, ['python3','RedLightProcessor.py']], 
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeMinesweeper']] ]],
	["Eco-Disaster", [ 
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeManualControl']] ]], 
	["Zombie Apocalypse", [ 
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeManualControl']] ]], 
	["Temple of Doom", [ 
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeManualControl']] ]], 
	["Stop all", [
			[StopAll, []] ]],
	["Quit", [
			[Quit, []] ]], 
	["Welcome", [
			[DisplayScreenSaver, []] ]]
	])

# Enable the menu selected via joystick
display = MenuDisplay(title, menus[:,0], 0)

# Stop everything first
StopAll(-1, [])
lastSelected = 0
while True:
	# Present Menu
	selected = GetSelection(lastSelected)
	print(f"selected: {selected}")
	if lastSelected != selected:
		StopAll(-1, [])
	# Do selected acton(s)
	for action in menus[selected,1]:
		action[0](selected, action[1])
	lastSelected = selected
