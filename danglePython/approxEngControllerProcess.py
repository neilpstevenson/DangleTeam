import time
from approxeng.input.selectbinder import ControllerResource
from interfaces.SensorsSharedIPC import SensorsSharedIPC

class SensorsProcess:

	# Mapping of ApproxEng named axes to PyGame equivalent
	axes = [("lx",0),("ly",1),("lt",2),("rx",3),("ry",4),("rt",5),("pitch",6),("roll",7)]
	# Buttons:
	buttons = [("cross",0),("circle",1),("triangle",2),("square",3),
		("l1",4),("r1",5),("l2",6),("r2",7),
		("select",8),("start",9),("home",10),("ls",11),("rs",12),
		("dup",13),("ddown",14),("dleft",15),("dright",16)]
	
	def __init__(self):
		# Initialise the IPC classes
		self.sensorsIPC = SensorsSharedIPC()
		self.sensorsIPC.create()

	def run(self):
		while True:
			try:
				with ControllerResource() as joystick:
					print('Found a joystick and connected')
					while joystick.connected:
						# Copy over axes values
						for axis in SensorsProcess.axes:
							axisValue = joystick[axis[0]]
							#print(f"axis: {axis} = {axisValue}")
							self.sensorsIPC.setAnalogValue(axis[1], axisValue)
						# Copy over the "held" status of buttons
						for button in SensorsProcess.buttons:
							held = joystick[button[0]]
							#print(f"button: {button} = {held}")
							self.sensorsIPC.setDigitalValue(button[1], 1.0 if (held is not None) else 0.0)
							
						# Report sensors alive
						self.sensorsIPC.resetWatchdog()
            
						# Poll delay
						time.sleep(0.05)
            
			except IOError:
				# No joystick found, wait for a bit before trying again
				print("Please connect joystick...")
				time.sleep(1.0)

main = SensorsProcess()
main.run()
			
