from interfaces.SensorInterface import SensorInterface
from interfaces.Config import Config

class SpeedDirectionCombiner(SensorInterface):
	""" Class to combine a speed with a direction adjustment in a non-linear fasion.  This
	is intended to compensate for real-world motors that won't accelerate from stationary easily
	and tend to coast once going.
	"""
	
	def __init__(self, forwardTorque, steerTorque, min = -1.0, max = 1.0, scaling = 1.0, offset = 0.0):
		SensorInterface.__init__(self)
		self.forwardTorque = forwardTorque
		self.steerTorque = steerTorque
		self.min = min
		self.max = max
		self.scaling = scaling
		self.offset = offset
		# Get config
		config = Config()
		self.speedSlow = config.get("speedsteer.slow", 0.1)
		self.speedSlowComp = config.get("speedsteer.slow.compensation", 2.0)
		self.speedMed = config.get("speedsteer.med", 0.8)
		self.speedMedComp = config.get("speedsteer.med.compensation", 1.0)
		self.speedHighComp = config.get("speedsteer.high.compensation", 2.0)
		self.speedHighThresh = config.get("speedsteer.high.decelthresh", 0.05)
		self.speedHighDecel = config.get("speedsteer.high.decel", 0.6)
		config.save()
	
	def nonLinearTransform(self, rawForwardTorque, rawSteerTorque):
		if (rawForwardTorque < self.speedSlow and rawForwardTorque > -self.speedSlow):
			# Slow speed or stationary - turn is emphasised
			combined = rawForwardTorque
			nominal = (combined*combined if combined>=0.0 else -combined*combined) + rawSteerTorque*self.speedSlowComp
			print(f"Slow: {rawForwardTorque}/{rawSteerTorque} => {nominal}")
			return nominal
		elif (rawForwardTorque < self.speedMed and rawForwardTorque > -self.speedMed):
			# Medium speed - turn has to be de-emphasised to stop spins
			combined = rawForwardTorque + rawSteerTorque*self.speedMedComp
			nominal = combined*combined if combined>=0.0 else -combined*combined
			print(f"Medium: {rawForwardTorque}/{rawSteerTorque} => {nominal}")
			return nominal
		elif (rawSteerTorque < self.speedHighThresh and rawSteerTorque > -self.speedHighThresh):
			# High speed - no much turn, let it rip
			combined = rawForwardTorque + rawSteerTorque*self.speedHighComp
			nominal = combined*combined if combined>=0.0 else -combined*combined
			print(f"High: {rawForwardTorque}/{rawSteerTorque} => {nominal}")
			return nominal
		else:
			# High speed - turn has to be re-emphasised otherwise it has little effect
			combined = rawForwardTorque*self.speedHighDecel + rawSteerTorque*self.speedHighComp
			nominal = combined*combined if combined>=0.0 else -combined*combined
			print(f"High Turn: {rawForwardTorque}/{rawSteerTorque} => {nominal}")
			return nominal
			
	def getValue(self):
		if type(self.forwardTorque) is list:
			rawForwardTorque = sum(map(lambda x: x.getValue(), self.forwardTorque))
		else:
			rawForwardTorque = self.forwardTorque.getValue()
		if type(self.steerTorque) is list:
			rawSteerTorque = sum(map(lambda x: x.getValue(), self.steerTorque))
		else:
			rawSteerTorque = self.steerTorque.getValue()	
		scaledValue = self.nonLinearTransform(rawForwardTorque, rawSteerTorque)*self.scaling + self.offset
		#print(f"forward: {rawForwardTorque:4.2f}, steer: {rawSteerTorque:4.2f}, result: {scaledValue:4.2f}")
		if scaledValue > self.max:
			return self.max
		elif scaledValue < self.min:
			return self.min
		return scaledValue
