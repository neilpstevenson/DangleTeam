import time
import numpy as np
import psutil
import sys
# Interfaces
from interfaces.SensorAccessFactory import SensorAccessFactory
from analysis.StepUpDownButtonValue import StepUpDownButtonValue
# Menu stuff
from display.menuPyGame import MenuDisplay
from display.welcome import showWelcomeSequence
from display.displayPosition import displayPosition
from display.displayText import displayText

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
		time.sleep(0.5)
	else:
		print(f"Already running: {actionParams}")
		display.message(f"Running\n{pythonName}")
		time.sleep(0.3)

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
					time.sleep(0.2)

def DisplayScreenSaver(selected, actionParams):
	stopButton = sensors.button(10)
	text = "Please connect\nController"
	display.message(text, True)
	# Wait for button
	while stopButton.getValue() == 0 and sensors.checkWatchdog() <= 0:
		time.sleep(0.2)
		display.processEvents()

def DisplayPositions(selected, actionParams):
	stopButton = sensors.button(10)
	#disp = displayPosition(display.getDevice(), stopButton)
	#disp.main()

def DisplayText(selected, actionParams):
	stopButton = sensors.button(10)
	text = actionParams[0]
	display.message(text, True)
	# Wait for button
	while stopButton.getValue() == 0 and sensors.checkWatchdog() > 0:
		time.sleep(0.2)
		display.processEvents()

	#disp = displayText(display.getDevice(), stopButton, text)
	#disp.main()

def GetSelection(selected):
	lastSelected = -1
	upDownButtons = StepUpDownButtonValue(sensors.button(14), sensors.button(13), min = 0, max = len(menus)-1, offset=selected, scaling = 1)
	selectButton = sensors.button(9)
	while True:
		if lastSelected != int(upDownButtons.getValue()):
			lastSelected = int(upDownButtons.getValue())
			display.select(lastSelected)
		else:
			display.processEvents()

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
	["Manual Control", [ 
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeManualSequence']],
			[Run, ['python3','displayStatus.py']],
			[DisplayPositions, []],
			[DisplayText, ['Manual Control']]  ]], 
	["Tidy up the Toys", [ 
			[Run, ['python3','TidyUpTheToysImageProcess.py']], 
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeTidyTheToys']],
			[Run, ['python3','displayStatus.py']],
			[DisplayText, ['Tidy up the\nToys']] ]], 
	["Up the\nGarden Path", [
			[Run, ['python3','VisionLineProcessor.py']], 
			[Run, ['python3','VoiceRecogniser.py']], 
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeUpTheGardenPath']],
			[Run, ['python3','displayStatus.py']],
			[DisplayText, ['Up the Garden\nPath']] ]], 
	["Feed the Fish", [
			[Run, ['python3','FeedFishImageProcess.py']], 
			[Run, ['python3','DangleRun.py', '--challenge', 'ChallengeFeedTheFish']],
			[Run, ['python3','displayStatus.py']],
			[DisplayText, ['Feed the Fish']] ]],
	["Stop all", [
			[StopAll, []] ]],
	["Quit", [
			[Quit, []] ]], 
	["Welcome", [
			[DisplayScreenSaver, []] ]]
	])

# Enable the menu selected via joystick
display = MenuDisplay(title, menus[:,0], 0, 3)

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
