import sys, math, pygame
#from operator import itemgetter
# Factories
from interfaces.SensorAccessFactory import SensorAccessFactory

class Simulation:
	def __init__(self, win_width = 640, win_height = 480):
		pygame.init()
		self.width = win_width 
		self.height = win_height

		self.screen = pygame.display.set_mode((win_width, win_height))
		pygame.display.set_caption("ToF Viewer")
		
		self.clock = pygame.time.Clock()

		# Simple depiction of the robot as a rectangle
		#width = win_width/4.0
		#height = win_height / 2.0
		#topX = win_width / 2.0
		#topY = win_height * 0.33
		#self.robotVertices = [(topX-width*0.66,topY),(topX+width*0.66,topY),(topX+width,topY+height),(topX-width,topY+height),(topX-width*0.66,topY)]
		#self.robotColor = (255,64,64)
		# Robot image
		self.image = pygame.transform.scale(pygame.image.load("display/Dangle_IMG_1351-small.png").convert_alpha(), (320,320))
		self.imageRect = self.image.get_rect()
		
		self.lineColor = (255,255,255)
		self.labels = ["Left","Forward","Right"]
		self.sensors = []
		for s in [18,17,16]:
			self.sensors.append(SensorAccessFactory.getSingleton().analog(s))
		self.distances = [[40,50,60,70,50,40],[40,50,60,70,50,40],[40,50,60,70,50,40]]
		
	def run(self):
		font = pygame.font.SysFont('Arial', 12)
		timestampPrev = 0.0
		sampleNumberPrev = 0
		imagePos = (self.imageRect[0]+160,self.imageRect[1]+160)
		
		# Main Loop
		while 1:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()

			#self.clock.tick(30) #frames/sec
			pygame.time.wait(50)
			
			# Clear current image
			self.screen.fill((64,64,64))

			# Read the next position from input to front of list
			for s in range(len(self.sensors)):
				self.distances[s].insert(0, self.sensors[s].getValue())
				if len(self.distances[s]) > 100:
					self.distances[s].pop()
			
			# Draw the robot
			self.screen.blit(self.image, imagePos)
			#pygame.draw.polygon(self.screen, self.robotColor, self.robotVertices)
			
			# Label the sensors
			#self.screen.blit(font.render(self.labels[face_index], True, (255,255,255)), ((t[f[0]].x+t[f[1]].x+t[f[2]].x+t[f[3]].x)/4, (t[f[0]].y+t[f[1]].y+t[f[2]].y+t[f[3]].y)/4))

			# Draw the positions
			for s in [0]:
				pointlist = []
				for p in range(len(self.distances[s])):
					pointlist.append((self.distances[s][p]/2+440, p*4 + 100))
				pygame.draw.lines(self.screen, self.lineColor, False, pointlist, 2)
			for s in [2]:
				pointlist = []
				for p in range(len(self.distances[s])):
					pointlist.append((200-self.distances[s][p]/2, p*4 + 100))
				pygame.draw.lines(self.screen, self.lineColor, False, pointlist, 2)
			for s in [1]:
				for p in range(min(20,len(self.distances[s]))):
					pointlist = []
					pointlist.append((320-(220-p*10), 160 - self.distances[s][p]/2.0))
					pointlist.append((320+(220-p*10), 160 - self.distances[s][p]/2.0))
					pygame.draw.lines(self.screen, self.lineColor, False, pointlist, 2)

			# Show the basic info
			#if (sampleNumber - sampleNumberPrev) >= 100 and timestamp > timestampPrev:
			#	rate = float(sampleNumber - sampleNumberPrev) / (timestamp - timestampPrev)
			#	timestampPrev = timestamp
			#	sampleNumberPrev = sampleNumber
			#	
			#self.screen.blit(font.render("Elapsed: {:7.3f}s,  Rate: {:5.1f}/s, Yaw: {:5.1f},  Pitch: {:5.1f},  Roll: {:5.1f}".format(timestamp, rate, self.angleYaw,self.anglePitch,self.angleRoll), True, (255,255,255)), (150, 440))
				
			pygame.display.flip()
