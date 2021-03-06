import sys, math, pygame
from interfaces.MotionSensorSharedIPC import MotionSensorSharedIPC
from operator import itemgetter

class Point3D:
	def __init__(self, x = 0, y = 0, z = 0):
		self.x, self.y, self.z = float(x), float(y), float(z)
 
	def rotateX(self, angle):
		""" Rotates the point around the X axis by the given angle in degrees. """
		rad = angle * math.pi / 180
		cosa = math.cos(rad)
		sina = math.sin(rad)
		y = self.y * cosa - self.z * sina
		z = self.y * sina + self.z * cosa
		return Point3D(self.x, y, z)
 
	def rotateY(self, angle):
		""" Rotates the point around the Y axis by the given angle in degrees. """
		rad = angle * math.pi / 180
		cosa = math.cos(rad)
		sina = math.sin(rad)
		z = self.z * cosa - self.x * sina
		x = self.z * sina + self.x * cosa
		return Point3D(x, self.y, z)
 
	def rotateZ(self, angle):
		""" Rotates the point around the Z axis by the given angle in degrees. """
		rad = angle * math.pi / 180
		cosa = math.cos(rad)
		sina = math.sin(rad)
		x = self.x * cosa - self.y * sina
		y = self.x * sina + self.y * cosa
		return Point3D(x, y, self.z)
 
	def project(self, win_width, win_height, fov, viewer_distance):
		""" Transforms this 3D point to 2D using a perspective projection. """
		factor = fov / (viewer_distance + self.z)
		x = self.x * factor + win_width / 2
		y = -self.y * factor + win_height / 2
		return Point3D(x, y, self.z)

class Simulation:
	def __init__(self, win_width = 640, win_height = 480):
		pygame.init()

		self.screen = pygame.display.set_mode((win_width, win_height))
		pygame.display.set_caption("Gyro/Accelerometer Positioning Viewer")
		
		self.clock = pygame.time.Clock()

		self.vertices = [
			Point3D(-1,1,-1),
			Point3D(1,1,-1),
			Point3D(1,-1,-1),
			Point3D(-1,-1,-1),
			Point3D(-1,1,1),
			Point3D(1,1,1),
			Point3D(1,-1,1),
			Point3D(-1,-1,1)
		]

		# Define the vertices that compose each of the 6 faces. These numbers are
		# indices to the vertices list defined above.
		self.faces  = [(0,1,2,3),(1,5,6,2),(5,4,7,6),(4,0,3,7),(0,4,5,1),(3,2,6,7)]

		# Define colors for each face
		self.colors = [(255,0,255),(255,0,0),(0,255,0),(0,0,255),(128,128,128),(255,128,0)]
		self.labels = ["Rear","Right","Front","Left","Top","Bottom"]

		self.anglePitch = 0
		self.angleYaw = 0
		self.angleRoll = 0
		self.anglePitchOffset = 0
		self.angleYawOffset = 0
		self.angleRollOffset = 0
		
	def run(self):
		font = pygame.font.SysFont('Arial', 12)
		timestampPrev = 0.0
		sampleNumberPrev = 0
		rate = 0.0
		quaternion = MotionSensorSharedIPC()
		
		""" Main Loop """
		while 1:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()

			#self.clock.tick(30) #frames/sec
			pygame.time.wait(50)
			
			# Read the next position from input
			quaternion.updateReading()
			self.angleRoll = quaternion.getRollDegrees()
			self.anglePitch = quaternion.getPitchDegrees()
			self.angleYaw = quaternion.getYawDegrees()
			timestamp = quaternion.get_timestamp()
			sampleCount = quaternion.get_sample_count()
			sampleNumber = quaternion.get_sample_number()
			
			if sampleNumberPrev == 0:
				sampleNumberPrev = sampleNumber	# Set initial number
				timestampPrev = timestamp
			
			#self.angleYaw,self.anglePitch,self.angleRoll = list(map(float, input().split()))
			
			# Auto-calibrate after appox 15secs
			if(timestamp >= 14.9 and timestamp <= 15.0):
				# Reset the offsets
				self.anglePitchOffset = self.anglePitch
				self.angleYawOffset = self.angleYaw
				self.angleRollOffset = self.angleRoll

			# Apply offsets
			self.anglePitch -= self.anglePitchOffset
			self.angleYaw -= self.angleYawOffset
			self.angleRoll -= self.angleRollOffset
				 
			self.screen.fill((64,64,64))

			# It will hold transformed vertices.
			t = []
			
			for v in self.vertices:
				# Rotate the point around X axis, then around Y axis, and finally around Z axis.
				r = v.rotateY(-self.angleYaw).rotateX(-self.anglePitch).rotateZ(self.angleRoll)
				# Transform the point from 3D to 2D
				p = r.project(self.screen.get_width(), self.screen.get_height(), 640, 6)
				# Put the point in the list of transformed vertices
				t.append(p)

			# Calculate the average Z values of each face.
			avg_z = []
			i = 0
			for f in self.faces:
				z = (t[f[0]].z + t[f[1]].z + t[f[2]].z + t[f[3]].z) / 4.0
				avg_z.append([i,z])
				i = i + 1

			# Draw the faces using the Painter's algorithm:
			# Distant faces are drawn before the closer ones.
			for tmp in sorted(avg_z,key=itemgetter(1),reverse=True):
				face_index = tmp[0]
				f = self.faces[face_index]
				pointlist = [(t[f[0]].x, t[f[0]].y), (t[f[1]].x, t[f[1]].y),
							 (t[f[1]].x, t[f[1]].y), (t[f[2]].x, t[f[2]].y),
							 (t[f[2]].x, t[f[2]].y), (t[f[3]].x, t[f[3]].y),
							 (t[f[3]].x, t[f[3]].y), (t[f[0]].x, t[f[0]].y)]
				pygame.draw.polygon(self.screen,self.colors[face_index],pointlist)
				# Label the faces
				self.screen.blit(font.render(self.labels[face_index], True, (255,255,255)), ((t[f[0]].x+t[f[1]].x+t[f[2]].x+t[f[3]].x)/4, (t[f[0]].y+t[f[1]].y+t[f[2]].y+t[f[3]].y)/4))
				#print((t[f[0]].x+t[f[1]].x+t[f[2]].x+t[f[3]].x)/4, (t[f[0]].y+t[f[1]].y+t[f[2]].y+t[f[3]].y)/4)

			# Show the basic info
			if (sampleNumber - sampleNumberPrev) >= 100 and timestamp > timestampPrev:
				rate = float(sampleNumber - sampleNumberPrev) / (timestamp - timestampPrev)
				timestampPrev = timestamp
				sampleNumberPrev = sampleNumber
				
			self.screen.blit(font.render("Elapsed: {:7.3f}s,  Rate: {:5.1f}/s, Yaw: {:5.1f},  Pitch: {:5.1f},  Roll: {:5.1f}".format(timestamp, rate, self.angleYaw,self.anglePitch,self.angleRoll), True, (255,255,255)), (150, 440))
				
 #           self.angleYaw += 1
			
			pygame.display.flip()

if __name__ == "__main__":
	Simulation().run()
