import time
from display.demo_opts import get_device
from luma.core.render import canvas
from luma.core import cmdline, error
from interfaces.SensorAccessFactory import SensorAccessFactory

class displayPosition:
	def __init__(self, device, stopButton):
		self.count = 0
		self.device = device
		self.stopButton = stopButton
		# Current Yaw reading
		self.sensors = SensorAccessFactory.getSingleton()
		self.yaw = self.sensors.yaw()
		self.pitch = self.sensors.pitch()
		
	def showPosition(self, draw):
		padding = 2
		shape_width = 20
		top = padding
		msg = f"Yaw: {self.yaw.getValue():.1f}"
		draw.text((padding, top + 4), 'Current Positions', fill="white")
		draw.text((padding, top + 16), msg, fill="white")
		msg = f"Pitch: {self.pitch.getValue():.1f}"
		draw.text((padding, top + 28), msg, fill="white")
		self.count += 1

	def main(self):
		while True:
			self.sensors.process()
			with canvas(self.device) as draw:
				self.showPosition(draw)
			if self.stopButton.getValue() > 0:
				return
			time.sleep(0.05)

class testGetValue:
	def getValue(self):
		return False			

if __name__ == "__main__":
	try:
		defaultDisplayConfig = ["--display=ssd1309", "--interface=spi", "--width=128", "--height=64", "--spi-bus-speed=8000000", "--gpio-reset=4", "--gpio-data-command=9"]
		displayDef = defaultDisplayConfig
		parser = cmdline.create_parser(description='luma arguments')
		displayArgs = parser.parse_args(displayDef)		
		try:
			device = cmdline.create_device(displayArgs)
		except error.Error as e:
			parser.error(e)

		disp = displayPosition(device, testGetValue())
		disp.main()
	except KeyboardInterrupt:
		pass

