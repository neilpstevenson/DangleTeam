###import time
import numpy as np
import psutil
import sys
import json5
# Interfaces
from interfaces.SensorAccessFactory import SensorAccessFactory
from analysis.StepUpDownButtonValue import StepUpDownButtonValue
# Menu stuff
from display.menuPyGame import MenuDisplay
from display.welcome import showWelcomeSequence
from display.displayPosition import displayPosition
#from display.displayText import displayText	# For Dangle OLed display
from display.displayIndicatorEyes import displayIndicatorEyes

def Run(selected, actionParams):
	# Attempt to start the sub-process(es)
	name = menus[selected,0]
	print(f"Runing option {selected}: {name}")
	# Already running?
	alreadyRunning = False
	for process in psutil.process_iter():
		try:
			if process.cmdline() == actionParams:
				alreadyRunning = True
				break
		except psutil.NoSuchProcess:
			pass
			
	pythonName = actionParams[1]
	if not alreadyRunning:
		print(f"Starting: {actionParams}")
		display.message(f"Starting\n{pythonName}")
		psutil.Popen(actionParams)
		display.sleep(0.5)
	else:
		print(f"Already running: {actionParams}")
		display.message(f"Running\n{pythonName}")
		display.sleep(0.3)

def StopAll(selected, actionParams):
	# Kill any existing processes
	for options in menus[:,1]:
		for processCmd in options:
			print(f"Checking: {processCmd}")
			for process in psutil.process_iter():
				try:
					if processCmd[0] == Run and process.cmdline() == processCmd[1]:
						pythonName = processCmd[1][1]
						print(f"Stopping: {processCmd}")
						display.message(f"Stopping\n{pythonName}")
						process.kill()
						display.sleep(0.2)
				except psutil.NoSuchProcess:
					pass

def DisplayScreenSaver(selected, actionParams):
	stopButton = sensors.button(10)
	text = "Please connect\nController"
	display.message(text, True)
	# Wait for button
	eye = 0x01
	while stopButton.getValue() == 0 and sensors.checkWatchdog() <= 0:
		eyes.setEyes(eye, 0x040000,0, eye, 0x040000, 0)
		eye <<= 1
		if eye > 0x0080:
			eye = 0x01
		display.sleep(0.05)
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
		display.sleep(0.2)
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
			eyes.setEyes(*menus[lastSelected,2])
		else:
			display.processEvents()

		if selectButton.getValue() > 0:
			break
		display.sleep(0.05)
		
		# Display screensaver if sensors not running
		if sensors.checkWatchdog() <= 0:
			DisplayScreenSaver(lastSelected, None)
			display.select(lastSelected)
			eyes.setEyes(*menus[lastSelected,2])
	return lastSelected

def Quit(selected, actionParams):
	sys.exit()

sensors = SensorAccessFactory.getSingleton()

title = "Select Challenge"
# Load the menu definitions
menus = np.empty(shape=[0, 3], dtype=object)
with open("Menus.json", "r") as read_file:
	json_menu = json5.load(read_file)
	#print(json_menu)
# Convert to our runtime array
for menu_item in json_menu:
	name = menu_item["name"]
	indicators = menu_item["indicators"]
	actions = []
	for nextaction in menu_item["actions"]:
		action = nextaction["action"]
		params = nextaction["params"]
		if action == 'Run':
			actions = actions + [[Run, params]]
		elif action == 'DisplayText':
			actions = actions + [[DisplayText, params]]
		elif action == 'DisplayPositions':
			actions = actions + [[DisplayPositions, params]]
		elif action == 'StopAll':
			actions = actions + [[StopAll, params]]
		elif action == 'Quit':
			actions = actions + [[Quit, params]]
		elif action == 'DisplayScreenSaver':
			actions = actions + [[DisplayScreenSaver, params]]
		else:
			raise ValueError(f"Unknown action '{action}'") 
	nextmen = np.array([[name, actions, indicators]], dtype=object)
	menus = np.append(menus, nextmen, axis=0)
#print(f"results: {menus}")

# Enable the menu selected via joystick
display = MenuDisplay(title, menus[:,0], 0, 3)
# Eyes display
eyes = displayIndicatorEyes()

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
